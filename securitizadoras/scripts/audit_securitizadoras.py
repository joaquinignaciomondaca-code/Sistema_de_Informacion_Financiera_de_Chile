#!/usr/bin/env python3
"""
audit_securitizadoras.py
Suite integral de auditoría y verificación de calidad y consistencia contable para:
  1. securitizadoras_maestro (parquet/json)
  2. securitizadoras_balance (particiones anuales, TXT IFRS CMF)
  3. patrimonios_separados_maestro (parquet/json)
  4. patrimonios_separados_balance (parquet)
"""

import json
import os
import unicodedata

import pandas as pd


CLAVES_BALANCE = ["periodo", "rut", "tipo_balance", "estado_financiero"]
TOLERANCIA_CUADRE = 1000
CUENTAS_ACTIVOS_TOTAL = {"total de activos", "activos total"}
CUENTAS_PATRIMONIO_PASIVOS_TOTAL = {
    "total de patrimonio y pasivos",
    "patrimonio neto y pasivos total",
}


def normalizar_cuenta(cuenta: str) -> str:
    """Normaliza acentos y puntuación menor de una glosa contable."""
    texto = unicodedata.normalize("NFKD", str(cuenta or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().replace(",", " ").replace(".", " ").split())


def _coalescer_aliases(totales: pd.DataFrame, nombres: set[str]) -> tuple[pd.Series, pd.Series]:
    """Unifica glosas equivalentes y marca grupos con alias de valores distintos."""
    resultado = pd.Series(float("nan"), index=totales.index, dtype="float64")
    conflictos = pd.Series(False, index=totales.index, dtype=bool)
    for columna in totales.columns:
        if normalizar_cuenta(columna) not in nombres:
            continue
        candidato = pd.to_numeric(totales[columna], errors="coerce")
        conflictos |= resultado.notna() & candidato.notna() & resultado.ne(candidato)
        resultado = resultado.fillna(candidato)
    return resultado, conflictos


def resumir_cuadre_balance(df_b: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una fila por balance, conservando también los que no se pueden cotejar."""
    seleccion = df_b[df_b["repeticion"] == 1]
    grupos = pd.MultiIndex.from_frame(seleccion[CLAVES_BALANCE].drop_duplicates())
    totales = seleccion.pivot_table(
        index=CLAVES_BALANCE, columns="cuenta", values="valor", aggfunc="first"
    ).reindex(grupos)
    activos, conflictos_activos = _coalescer_aliases(totales, CUENTAS_ACTIVOS_TOTAL)
    pasivos_patrimonio, conflictos_pasivos = _coalescer_aliases(
        totales, CUENTAS_PATRIMONIO_PASIVOS_TOTAL
    )
    conflicto = conflictos_activos | conflictos_pasivos
    verificable = activos.notna() & pasivos_patrimonio.notna() & ~conflicto
    return pd.DataFrame({
        "activos": activos,
        "patrimonio_y_pasivos": pasivos_patrimonio,
        "diferencia": (activos - pasivos_patrimonio).abs(),
        "conflicto": conflicto,
        "verificable": verificable,
    }, index=totales.index)


def calcular_dv(rut_str: str) -> str:
    rut = str(rut_str).strip().replace(".", "").replace("-", "")
    if not rut.isdigit():
        return ""
    suma = 0
    multiplicador = 2
    for c in reversed(rut):
        suma += int(c) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    elif resto == 10:
        return "K"
    else:
        return str(resto)

def main():
    print("=" * 75)
    print("AUDITORIA INTEGRAL: SECURITIZADORAS Y PATRIMONIOS SEPARADOS (CMF CHILE)")
    print("=" * 75)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "outputs", "securitizadoras"))
    errores = []

    # 1. Maestro Securitizadoras
    print("\n--- 1. AUDITORIA: securitizadoras_maestro ---")
    maestro_pq = os.path.join(base_dir, "securitizadoras_maestro.parquet")
    maestro_js = os.path.join(base_dir, "securitizadoras_maestro.json")
    if not os.path.exists(maestro_pq) or not os.path.exists(maestro_js):
        errores.append("Archivos de securitizadoras_maestro faltantes.")
        df_m = pd.DataFrame()
    else:
        df_m = pd.read_parquet(maestro_pq)
        with open(maestro_js, "r", encoding="utf-8") as f:
            js_m = json.load(f)
        
        print(f"Total entidades registradas: {len(df_m)} | Parquet=JSON: {len(df_m) == len(js_m)}")
        if len(df_m) != len(js_m):
            errores.append(f"Discrepancia filas Parquet ({len(df_m)}) vs JSON ({len(js_m)})")

        dups_rut = df_m["rut"].duplicated().sum()
        print(f"RUT duplicados: {dups_rut}")
        if dups_rut > 0:
            errores.append(f"Existen {dups_rut} RUT duplicados en maestro.")

        dv_errors = 0
        for _, row in df_m.iterrows():
            dv_calc = calcular_dv(row["rut"])
            if dv_calc != str(row["dv"]).upper():
                dv_errors += 1
        print(f"Validacion Modulo 11 (RUT): {len(df_m) - dv_errors}/{len(df_m)} validos")
        if dv_errors > 0:
            errores.append(f"Fallaron {dv_errors} digitos verificadores Modulo 11.")

        vigentes = (df_m["estado_vigencia"] == "VIGENTE").sum()
        print(f"Distribucion vigencia: {vigentes} VIGENTES | {len(df_m) - vigentes} NO VIGENTES / LIQUIDACION")

    ruts_maestro_completos = set(df_m["rut_completo"]) if not df_m.empty else set()

    # 2. Balance IFRS de las securitizadoras (TXT trimestral CMF, pipelines/ifrs_sectores)
    print("\n--- 2. AUDITORIA: securitizadoras_balance ---")
    import glob
    archivos = sorted(glob.glob(os.path.join(base_dir, "securitizadoras_balance", "*.parquet")))
    if not archivos:
        errores.append("Faltan las particiones de securitizadoras_balance.")
    else:
        df_b = pd.concat([pd.read_parquet(a) for a in archivos], ignore_index=True)
        resumen = resumir_cuadre_balance(df_b)
        if resumen.empty:
            errores.append("No se encontraron balances con repeticion=1 en securitizadoras_balance.")
        verificables = resumen["verificable"]
        dentro_tolerancia = verificables & (resumen["diferencia"] <= TOLERANCIA_CUADRE)
        descuadrados = verificables & (resumen["diferencia"] > TOLERANCIA_CUADRE)
        conflictos = resumen["conflicto"]
        no_verificables = ~verificables
        print(
            f"Balances: {len(resumen)} | dentro de tolerancia (≤ {TOLERANCIA_CUADRE}): "
            f"{int(dentro_tolerancia.sum())}/{len(resumen)}"
        )
        if no_verificables.any():
            errores.append(
                f"{int(no_verificables.sum())} balances no se pudieron verificar: "
                "faltan totales o hay glosas equivalentes con valores contradictorios"
            )
            for clave in resumen.index[no_verificables][:5]:
                print(f"  [NO VERIFICABLE] {clave}")
        if conflictos.any():
            errores.append(
                f"{int(conflictos.sum())} balances tienen glosas alias con valores contradictorios"
            )
        if descuadrados.any():
            errores.append(
                f"{int(descuadrados.sum())} balances de securitizadoras no cuadran "
                "(activos vs patrimonio y pasivos)"
            )

    # 3. Maestro Patrimonios Separados (Programas y Lineas)
    print("\n--- 3. AUDITORIA: patrimonios_separados_maestro ---")
    ps_pq = os.path.join(base_dir, "patrimonios_separados_maestro.parquet")
    ps_js = os.path.join(base_dir, "patrimonios_separados_maestro.json")
    if not os.path.exists(ps_pq) or not os.path.exists(ps_js):
        errores.append("Archivos de patrimonios_separados_maestro faltantes.")
    else:
        df_ps = pd.read_parquet(ps_pq)
        with open(ps_js, "r", encoding="utf-8") as f:
            js_ps = json.load(f)
        print(f"Total lineas de emision: {len(df_ps)} | Parquet=JSON: {len(df_ps) == len(js_ps)}")
        if len(df_ps) != len(js_ps):
            errores.append("Discrepancia Parquet vs JSON en patrimonios_separados_maestro")

    # 4. Balance de patrimonios separados (05_publicar_balance_patrimonios.py)
    print("\n--- 4. AUDITORIA: patrimonios_separados_balance ---")
    bal_pq = os.path.join(base_dir, "patrimonios_separados_balance.parquet")
    if not os.path.exists(bal_pq):
        errores.append("Falta patrimonios_separados_balance.parquet")
    else:
        cta = pd.read_parquet(bal_pq)
        t = cta.pivot_table(index="archivo", columns="categoria", values="monto_m_clp", aggfunc="sum").fillna(0)
        print(f"Cuentas: {len(cta)} | Balances: {len(t)} | Cierres: {cta['periodo'].nunique()} "
              f"({cta['periodo'].min()}–{cta['periodo'].max()})")
        if cta.duplicated(["archivo", "orden_en_balance"]).any():
            errores.append("balance: (archivo, orden_en_balance) duplicado")
        if cta.drop_duplicates("archivo").duplicated(["rut_administradora", "codigo_patrimonio", "periodo"]).any():
            errores.append("balance: patrimonio y cierre repetidos en documentos distintos")
        gap = (t["Total Activos"] - t["Total Pasivo Circulante"] - t["Total Pasivo No Circulante"]
               - t["Total Patrimonio (Excedente Acumulado)"]).abs()
        print(f"Cuadre activos = pasivos + patrimonio: {int((gap <= 2).sum())}/{len(t)}")
        if (gap > 2).any():
            errores.append(f"balance: {int((gap > 2).sum())} balances no cuadran")
        for det in ["Activo Circulante", "Activo No Circulante", "Pasivo Circulante", "Pasivo No Circulante",
                    "Patrimonio (Excedente Acumulado)"]:
            if det in t and ((t[det] - t[f"Total {det}"]).abs() > 2).any():
                errores.append(f"balance: las cuentas de '{det}' no suman su total")
        if "df_m" in locals():
            sin_gestora = set(cta["rut_administradora"]) - set(df_m["rut"].astype(str))
            print(f"RUT sin gestora en securitizadoras_maestro: {sorted(sin_gestora) or 'ninguno'}")
            if sin_gestora:
                errores.append(f"balance: RUT sin gestora {sorted(sin_gestora)}")

    print("\n" + "=" * 75)
    if not errores:
        print("RESULTADO DE AUDITORIA: 100% EXITOSA - 4 DATASETS VERIFICADOS")
        print("=" * 75)
        return 0
    else:
        print(f"RESULTADO DE AUDITORIA: FALLIDA CON {len(errores)} ERRORES:")
        for err in errores:
            print(f"  - ERROR: {err}")
        print("=" * 75)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
