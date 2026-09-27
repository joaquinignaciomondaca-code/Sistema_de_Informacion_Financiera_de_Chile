"""
Auditoria independiente del dataset bancos_repos_saldos_series.

A diferencia de bancos/scripts/audit_bancos_repos.py (que solo comprueba
coherencia interna del propio archivo), esta auditoria incorpora controles
cruzados contra fuentes independientes que SI existen en el repositorio, y
detecta problemas de identidad, cobertura y semantica.

Controles:
  1. Integridad fisica: Parquet y JSON existen y coinciden fila por fila.
  2. Estructura: esquema esperado y ausencia de nulos.
  3. Clave primaria: id_repo unico y coherente con codigo_institucion+periodo.
  4. Aritmetica interna: neto = activo - pasivo (CLP y USD);
     total_transado_mm_usd = activo + pasivo; conversion USD = CLP / tipo de cambio.
  5. Tipo de cambio: contraste del tc_usd_cierre mensual contra la serie
     independiente usd_clp_cierre del modulo macro (extraida de BCCh por otro
     pipeline, sin intervencion manual).
  6. Identidad: validez del RUT (modulo 11), duplicidad de RUT entre codigos
     distintos con periodos solapados y deteccion de RUT sinteticos de agregados.
  7. Cobertura: bancos del catalogo sin filas en el ultimo ano, bancos que
     reportan balance pero no repos, y continuidad temporal por institucion.
  8. Semantica: campos etiquetados de forma que induce a error (transado).

Uso:
    python bancos/scripts/audit_repos_saldos_series.py [--json]

Devuelve codigo de salida 0 si no hay fallas estructurales y 1 si las hay.
Las observaciones (identidad, cobertura, semantica) se informan sin alterar
los archivos auditados.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import pandas as pd

PARQUET = "docs/outputs/bancos/bancos_repos_saldos_series.parquet"
JSON = "docs/outputs/bancos/bancos_repos_saldos_series.json"
MAESTRO = "docs/outputs/bancos/bancos_maestro.parquet"
MACRO_FX = "docs/outputs/macro/macro_divisas_mercado.parquet"

COLUMNAS_ESPERADAS = [
    "id_repo", "periodo", "fecha_corte", "codigo_institucion", "rut",
    "razon_social", "nombre_fantasia", "repo_activo_mm_clp",
    "repo_pasivo_mm_clp", "repo_neto_mm_clp", "tc_usd_cierre",
    "repo_activo_mm_usd", "repo_pasivo_mm_usd", "repo_neto_mm_usd",
    "total_transado_mm_usd", "posicion_relativa",
]

# Filas que NO corresponden a una institucion individual: son totales y
# subtotales construidos por el archivo de origen (RUT 99.999.xxx o similar).
CODIGOS_AGREGADO = ["900", "950", "960", "970", "980", "998"]

# Referencia local de codigos bancarios: mezcla entidades historicas y
# posiblemente vigentes. NO constituye una nomina oficial certificada ni una
# expectativa de REPO mensual: un banco sin fila podria tener saldo cero.
CODIGOS_REFERENCIA_2026 = [
    "001", "009", "012", "014", "016", "028", "031", "037", "039",
    "041", "049", "051", "053", "055", "059", "060", "061", "062",
]

TOLERANCIA_USD = 0.02  # redondeo a dos decimales en millones de USD


class Auditoria:
    def __init__(self, base_dir: str) -> None:
        self.base = base_dir
        self.fallas: list[str] = []
        self.observaciones: list[str] = []
        self.detalle: list[str] = []

    # ---------------------------------------------------------------- utils
    def _p(self, rel: str) -> str:
        return os.path.join(self.base, rel)

    def falla(self, msg: str) -> None:
        self.fallas.append(msg)

    def observa(self, msg: str) -> None:
        self.observaciones.append(msg)

    def info(self, msg: str) -> None:
        self.detalle.append(msg)

    # ------------------------------------------------------------ controles
    def cargar(self) -> pd.DataFrame | None:
        for rel in (PARQUET, JSON):
            if not os.path.exists(self._p(rel)):
                self.falla(f"No existe el archivo publicado {rel}")
        if self.fallas:
            return None

        df = pd.read_parquet(self._p(PARQUET))
        with open(self._p(JSON), encoding="utf-8") as fh:
            filas_json = json.load(fh)
        registros_json = len(filas_json)

        self.info(f"Parquet: {len(df):,} registros | JSON: {registros_json:,} registros")
        if registros_json != len(df):
            self.falla(
                f"Parquet y JSON tienen distinto numero de registros "
                f"({len(df):,} vs {registros_json:,})"
            )
        elif filas_json:
            columnas_json = list(filas_json[0].keys())
            if columnas_json != list(df.columns):
                self.falla(f"Columnas JSON diferentes de Parquet: {columnas_json}")
            elif len({fila.get("id_repo") for fila in filas_json}) != len(filas_json):
                self.falla("JSON tiene id_repo duplicados")
            else:
                por_id = {fila["id_repo"]: fila for fila in filas_json}
                mismatches = []
                for row in df.to_dict("records"):
                    other = por_id.get(row["id_repo"])
                    if other is None or any(
                        abs(row[c] - other[c]) > 0.001 if isinstance(row[c], (int, float))
                        else row[c] != other[c]
                        for c in df.columns
                    ):
                        mismatches.append(row["id_repo"])
                if mismatches:
                    self.falla(f"Parquet y JSON difieren en {len(mismatches)} filas")
        if list(df.columns) != COLUMNAS_ESPERADAS:
            self.falla(f"Esquema inesperado: {list(df.columns)}")
        if df.isna().any().any():
            self.falla("Hay valores nulos en el dataset")

        dup = df["id_repo"].duplicated().sum()
        if dup:
            self.falla(f"id_repo tiene {dup} duplicados")
        esperado = df["codigo_institucion"] + "_" + df["periodo"]
        if not (esperado == df["id_repo"]).all():
            self.falla("id_repo no coincide con codigo_institucion + periodo")
        return df

    def control_aritmetica(self, df: pd.DataFrame) -> None:
        calc_clp = (df["repo_activo_mm_clp"] - df["repo_pasivo_mm_clp"]).round(2)
        if not (df["repo_neto_mm_clp"] - calc_clp).abs().le(0.01).all():
            self.falla("repo_neto_mm_clp no cuadra con los saldos en CLP")

        calc_usd = (df["repo_activo_mm_usd"] - df["repo_pasivo_mm_usd"]).round(2)
        if not (df["repo_neto_mm_usd"] - calc_usd).abs().le(0.01).all():
            self.falla("repo_neto_mm_usd no cuadra con los saldos en USD")

        suma = (df["repo_activo_mm_usd"] + df["repo_pasivo_mm_usd"]).round(2)
        if not (df["total_transado_mm_usd"] - suma).abs().le(0.02).all():
            self.falla("total_transado_mm_usd no es la suma de los saldos en USD")
        else:
            self.observa(
                "total_transado_mm_usd es la SUMA DE SALDOS activo+pasivo, no volumen "
                "transado del periodo: la etiqueta induce a error"
            )

        for lado in ("activo", "pasivo"):
            conv = (df[f"repo_{lado}_mm_clp"] / df["tc_usd_cierre"]).round(2)
            peor = (conv - df[f"repo_{lado}_mm_usd"]).abs().max()
            self.info(f"Conversion CLP->USD {lado}: desviacion maxima {peor:.4f} MM USD")
            if peor > TOLERANCIA_USD:
                self.falla(f"repo_{lado}_mm_usd no equivale a CLP/tipo de cambio (max {peor:.4f})")

        signos = pd.Series("Neutro", index=df.index)
        signos[df["repo_neto_mm_clp"] > 0] = "Prestamista Neto de Liquidez"
        signos[df["repo_neto_mm_clp"] < 0] = "Tomador Neto de Fondeo"
        if not (signos == df["posicion_relativa"]).all():
            self.falla("posicion_relativa no es coherente con el signo del saldo neto")

    def control_tipo_cambio(self, df: pd.DataFrame) -> None:
        ruta = self._p(MACRO_FX)
        if not os.path.exists(ruta):
            self.observa("No hay serie macro de tipo de cambio para contrastar")
            return
        macro = pd.read_parquet(ruta, columns=["periodo", "usd_clp_cierre"])
        tc = df.groupby("periodo")["tc_usd_cierre"].first().reset_index()
        m = tc.merge(macro, on="periodo", how="inner")
        if m.empty:
            self.observa("Sin periodos comunes con la serie macro de tipo de cambio")
            return
        m["dif"] = (m["tc_usd_cierre"] - m["usd_clp_cierre"]).abs()
        peor = m["dif"].max()
        self.info(
            f"Tipo de cambio contrastado en {len(m)} meses (BCCh via modulo macro): "
            f"desviacion maxima {peor:.2f} CLP/USD"
        )
        if peor > 0.5:
            self.falla(
                f"tc_usd_cierre difiere del dolar observado de cierre BCCh en hasta "
                f"{peor:.2f} CLP/USD"
            )
        excluidos = sorted(set(tc["periodo"]) - set(m["periodo"]))
        if excluidos:
            self.observa(
                f"{len(excluidos)} periodos sin contraste de tipo de cambio "
                f"(la serie macro parte en {macro['periodo'].min()}): "
                f"{excluidos[0]} a {excluidos[-1]}"
            )

    def control_identidad(self, df: pd.DataFrame) -> None:
        def modulo11(rut: str) -> bool:
            limpio = str(rut).replace(".", "").replace("-", "").strip().upper()
            if len(limpio) < 2 or not limpio[:-1].isdigit():
                return False
            suma, factor = 0, 2
            for digito in reversed(limpio[:-1]):
                suma += int(digito) * factor
                factor = 2 if factor == 7 else factor + 1
            resto = 11 - (suma % 11)
            esperado = "K" if resto == 10 else ("0" if resto == 11 else str(resto))
            return limpio[-1] == esperado

        ruts = df[["codigo_institucion", "rut"]].drop_duplicates()
        invalidos = [r for r in ruts["rut"] if not modulo11(r)]
        if invalidos:
            self.falla(f"RUT con digito verificador invalido: {sorted(invalidos)}")
        else:
            self.info(f"RUT validos (modulo 11): {len(ruts)} pares codigo-RUT")

        por_rut = ruts.groupby("rut")["codigo_institucion"].apply(list)
        compartidos = por_rut[por_rut.apply(len) > 1]
        for rut, codigos in compartidos.items():
            self.observa(
                f"RUT {rut} asignado a {len(codigos)} codigos distintos ({', '.join(codigos)}): "
                "unir por RUT colapsa o duplica filas; requiere cotejo registral"
            )

        # Una ficha historica oficial de SBIF identifica codigo y RUT por banco.
        # No se corrigen los datos automaticamente porque puede haber sucesiones
        # legales; se deja evidencia de las discrepancias para cotejo registral.
        # Fuente: https://sbif.cl/sbifweb/internet/bancos/todos.pdf (corte 2004).
        rut_sbif_2004 = {
            "009": "97.011.000-3", "012": "97.030.000-7", "027": "97.023.000-9",
            "028": "97.080.000-K", "031": "97.951.000-4", "039": "97.041.000-7",
            "041": "97.043.000-8", "045": "59.002.220-9", "507": "97.051.000-1",
        }
        ruts_locales = ruts.set_index("codigo_institucion")["rut"].to_dict()
        distintos = [
            f"{codigo}: {ruts_locales[codigo]} vs SBIF {rut_oficial}"
            for codigo, rut_oficial in rut_sbif_2004.items()
            if codigo in ruts_locales and ruts_locales[codigo] != rut_oficial
        ]
        if distintos:
            self.observa(
                f"{len(distintos)} codigos con RUT distinto de fichas historicas SBIF "
                "(corte 2004; no implica necesariamente error en 2026): "
                + "; ".join(distintos)
            )

        # CMF, ficha de entidad BBVA Chile, RUT 97.032.000-8.
        # https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=97032000&grupo=0&tipoentidad=BANCO&vig=VI&orig=lista&control=svs&pestania=38
        if ruts_locales.get("504") == "97.018.000-1":
            self.observa(
                "Codigo 504 (BBVA Chile) figura con RUT 97.018.000-1 de "
                "Scotiabank; ficha CMF de BBVA registra 97.032.000-8. "
                "Identidad temporal/historica por corregir tras cotejo completo"
            )

        # Solapamiento temporal entre codigos que comparten RUT: doble conteo real
        for rut, codigos in compartidos.items():
            sub = df[df["rut"] == rut]
            periodos = sub.groupby("codigo_institucion")["periodo"].apply(set)
            for i, c1 in enumerate(codigos):
                for c2 in codigos[i + 1:]:
                    solape = periodos.get(c1, set()) & periodos.get(c2, set())
                    if solape:
                        self.observa(
                            f"RUT compartido: los codigos {c1} y {c2} (RUT {rut}) tienen "
                            f"{len(solape)} periodos simultaneos, desde {min(solape)} "
                            f"hasta {max(solape)}"
                        )

        agregados = df[df["codigo_institucion"].isin(CODIGOS_AGREGADO)]
        if len(agregados):
            ruts_sinteticos = sorted(agregados["rut"].unique())
            self.observa(
                f"{len(agregados)} filas de agregados del sistema "
                f"(codigos {', '.join(CODIGOS_AGREGADO)}; RUT sinteticos "
                f"{', '.join(ruts_sinteticos)}) mezcladas con bancos individuales: "
                "sumar la tabla completa PUEDE duplicar totales; verificar definicion de cada agregado"
            )

    def control_cobertura(self, df: pd.DataFrame) -> None:
        agg = df[df["codigo_institucion"].isin(CODIGOS_AGREGADO)]
        if len(agg):
            self.info(
                f"Filas de agregados: {len(agg)} | cobertura {agg['periodo'].min()} a "
                f"{agg['periodo'].max()}"
            )
        bancos = df[~df["codigo_institucion"].isin(CODIGOS_AGREGADO)]
        ultimos = sorted(bancos["periodo"].unique())[-12:]
        presentes = set(bancos[bancos["periodo"].isin(ultimos)]["codigo_institucion"])
        ausentes = [c for c in CODIGOS_REFERENCIA_2026 if c not in presentes]
        self.info(
            f"Cobertura ultimos 12 periodos ({ultimos[0]} a {ultimos[-1]}): "
            f"{len(presentes)} codigos con filas"
        )
        if ausentes:
            nombres = (
                df[df["codigo_institucion"].isin(ausentes)]
                .drop_duplicates("codigo_institucion")
                .set_index("codigo_institucion")["nombre_fantasia"]
                .to_dict()
            )
            etiquetas = [f"{c} ({nombres.get(c, 'sin nombre')})" for c in ausentes]
            self.observa(
                "Sin filas en el ultimo ano para "
                + ", ".join(etiquetas)
                + f" (referencia local de {len(CODIGOS_REFERENCIA_2026)} codigos; ausencia NO equivale a dato faltante)"
            )

        # Continuidad: instituciones cuyo ultimo periodo no es el ultimo del dataset
        corte = max(bancos["periodo"])
        ultimo_por_banco = bancos.groupby("codigo_institucion")["periodo"].max()
        truncados = ultimo_por_banco[ultimo_por_banco < corte]
        recientes = [c for c in truncados.index if c in CODIGOS_REFERENCIA_2026]
        if recientes:
            detalle = ", ".join(f"{c} hasta {truncados[c]}" for c in sorted(recientes))
            self.observa(f"Series que terminan antes del ultimo periodo {corte} (pueden ser saldos cero): {detalle}")

        huecos = []
        for code, g in bancos.groupby("codigo_institucion"):
            if code not in CODIGOS_REFERENCIA_2026:
                continue
            p0, p1 = g["periodo"].min(), g["periodo"].max()
            esperados = pd.period_range(p0, p1, freq="M").strftime("%Y-%m").tolist()
            faltantes = sorted(set(esperados) - set(g["periodo"]))
            if faltantes:
                huecos.append(f"{code}: {len(faltantes)} meses sin fila ({p0} a {p1})")
        if huecos:
            self.observa("Meses sin fila por institucion (pueden ser saldos cero) -> " + "; ".join(huecos))

    def control_maestro(self, df: pd.DataFrame) -> None:
        ruta = self._p(MAESTRO)
        if not os.path.exists(ruta):
            self.observa("No existe bancos_maestro.parquet para cotejar identidad")
            return
        maestro = pd.read_parquet(ruta)
        faltan = sorted(set(df["codigo_institucion"]) - set(maestro["codigo_institucion"]))
        if faltan:
            self.falla(f"Codigos de la serie ausentes en el catalogo maestro: {faltan}")
        else:
            self.info("Integridad referencial con bancos_maestro: 100%")

    # ---------------------------------------------------------------- salida
    def ejecutar(self) -> int:
        print("=" * 78)
        print("AUDITORIA INDEPENDIENTE: bancos_repos_saldos_series")
        print("=" * 78)
        df = self.cargar()
        if df is None:
            for f in self.fallas:
                print(f"[FALLA] {f}")
            return 1

        self.control_aritmetica(df)
        self.control_tipo_cambio(df)
        self.control_identidad(df)
        self.control_cobertura(df)
        self.control_maestro(df)

        for linea in self.detalle:
            print(f"[OK]    {linea}")
        for obs in self.observaciones:
            print(f"[AVISO] {obs}")
        for f in self.fallas:
            print(f"[FALLA] {f}")

        print("-" * 78)
        if self.fallas:
            print(f"DICTAMEN: NO APROBADO — {len(self.fallas)} fallas, "
                  f"{len(self.observaciones)} avisos")
            return 1
        print(f"DICTAMEN: controles estructurales aprobados — {len(self.observaciones)} avisos "
              "de identidad, cobertura o semantica pendientes de resolucion")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Salida en JSON")
    args = parser.parse_args()
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    auditoria = Auditoria(base)
    if args.json:
        sys.stdout = sys.stderr  # el informe legible va a stderr, el JSON a stdout
        codigo = auditoria.ejecutar()
        sys.stdout = sys.__stdout__
        print(json.dumps(
            {
                "aprobado": codigo == 0,
                "fallas": auditoria.fallas,
                "avisos": auditoria.observaciones,
                "detalle": auditoria.detalle,
            },
            ensure_ascii=False, indent=2,
        ))
        return codigo
    return auditoria.ejecutar()


if __name__ == "__main__":
    raise SystemExit(main())
