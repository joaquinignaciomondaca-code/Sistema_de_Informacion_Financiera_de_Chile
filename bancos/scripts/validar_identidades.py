#!/usr/bin/env python3
"""Coteja el maestro de bancos contra el registro BANCO de la CMF.

`bancos/AUDITORIA_MAESTRO_IDENTIDADES.md` dejó el maestro «pendiente de
validación» después de cotejar 4 de 40 RUT a mano. Esta compuerta hace el cotejo
completo contra la misma fuente que usa `pipelines/entidades/actualizar_listas.py`
para dar de alta bancos nuevos: el registro BANCO de la CMF, listas de vigentes
(`VI`) y no vigentes (`NV`).

Qué comprueba, para cada fila del maestro:

  * **Agregados sectoriales** (`Total Bancos`, `Total Sistema Financiero`…): no
    son entidades de la CMF, así que no se cotejan; se declaran.
  * **Filiales en el exterior y entidades históricas**: están declaradas en
    `EXCEPCIONES` con su motivo. No aparecen en el registro porque no son bancos
    establecidos en Chile (o porque la CMF ya sólo publica el nombre sucesor).
  * **El resto**: su RUT tiene que estar en el registro, en la lista que
    corresponde a su `estado` (`Activo` → VI; `Cerrado`/`Fusionado` → NV). Si no
    está, el script busca el registro cuya razón social se parece y lo propone:
    es el caso de los RUT que se completaron a mano y no existen en la CMF.

Resultado por fila en `docs/outputs/bancos/identidades_cmf.json`, con la fecha,
las URL consultadas y el resumen. Sin red, el cotejo se hace contra ese mismo
archivo (`--check`), que es lo que corre la integración.

    python3 bancos/scripts/validar_identidades.py --descargar   # refresca y coteja
    python3 bancos/scripts/validar_identidades.py --check       # sin red (CI)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

BANCOS = ROOT / "docs" / "outputs" / "bancos"
MAESTRO = BANCOS / "bancos_maestro.json"
REGISTRO = BANCOS / "registro_cmf_banco.json"
COTEJO = BANCOS / "identidades_cmf.json"
REGISTRO_URL = "https://www.cmfchile.cl/institucional/mercados/consulta.php" \
               "?mercado=B&entidad=BANCO"

# Filas que no se pueden cotejar contra el registro y por qué. Se declaran una
# por una: si aparece una nueva, la compuerta falla en vez de darla por buena.
EXCEPCIONES = {
    "027": "CorpBanca: absorbido por Banco Itaú Chile (97023000-9); la CMF ya no "
           "publica su RUT y el código 027 sigue en los archivos históricos.",
    "816": "BCI Financial Group Inc and Subsidiaries: filial en el exterior; el "
           "registro BANCO sólo lista bancos establecidos en Chile.",
    "916": "City National Bank of Florida: filial en el exterior; el registro "
           "BANCO sólo lista bancos establecidos en Chile.",
    "927": "CorpBanca Colombia: filial en el exterior; el registro BANCO sólo "
           "lista bancos establecidos en Chile.",
}

# Estados del maestro que exigen estar en la lista de no vigentes.
NO_VIGENTES = {"Cerrado", "Fusionado"}

RUIDO = re.compile(r"\b(S\.?A\.?|LTDA|LIMITADA|CHILE|BANCO|COMPANIA|COMPAÑIA)\b")


def normalizar(texto: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", str(texto))
                         if unicodedata.category(c) != "Mn")
    limpio = re.sub(r"[^A-Z0-9 ]+", " ", sin_tildes.upper())
    palabras = [p for p in limpio.split() if p and not RUIDO.fullmatch(p)]
    return " ".join(palabras)


def parecido(a: str, b: str) -> float:
    """Jaccard de palabras: cuánto se parecen dos razones sociales."""
    pa, pb = set(normalizar(a).split()), set(normalizar(b).split())
    if not pa or not pb:
        return 0.0
    return len(pa & pb) / len(pa | pb)


def descargar() -> dict:
    """Baja las dos listas y escribe el snapshot que usa `--check`.

    El lector del registro vive en `pipelines/entidades/actualizar_listas.py` y
    arrastra pandas; se importa solo aquí, para que `--check` corra sin él.
    """
    from pipelines.entidades.actualizar_listas import registro

    entidades = []
    for estado, vigencia in (("VI", "Vigente"), ("NV", "No Vigente")):
        for cuerpo, (dv, nombre) in sorted(registro("B", "BANCO", estado).items()):
            entidades.append({"rut": f"{cuerpo}-{dv}", "razon_social_cmf": nombre,
                              "vigencia": vigencia})
    if len(entidades) < 20:
        raise SystemExit(f"El registro BANCO trajo {len(entidades)} entidades: "
                         "se aborta para no publicar un cotejo incompleto")
    return {
        "fecha": date.today().isoformat(),
        "fuente": "CMF — registro BANCO (consulta de entidades fiscalizadas)",
        "url": REGISTRO_URL,
        "entidades": entidades,
    }


def comparar(maestro: list[dict], snapshot: dict) -> list[dict]:
    por_rut = {e["rut"].upper(): e for e in snapshot["entidades"]}
    resultados = []
    for fila in maestro:
        codigo = str(fila["codigo_institucion"])
        # El maestro publica el RUT completo sin puntos (`rut_dv`, cuerpo-DV) y el
        # registro de la CMF usa la misma forma; se canonicaliza igual por si
        # aparece una copia antigua con puntos, que `corregir_identidades.py`
        # marca como formato inconsistente.
        rut = re.sub(r"[.\s]", "", str(fila["rut_dv"])).upper()
        estado = str(fila.get("estado") or "")
        registro_cmf = por_rut.get(rut)
        resultado = {
            "codigo_institucion": codigo,
            "rut": rut,
            "razon_social": fila["razon_social"],
            "estado": estado,
        }
        if str(fila.get("tipo_licencia")) == "Agregado Sectorial":
            resultado["cotejo"] = "agregado_sectorial"
            resultado["detalle"] = "No es una entidad de la CMF: total publicado por la fuente."
        elif registro_cmf:
            esperado = "No Vigente" if estado in NO_VIGENTES else "Vigente"
            resultado["cotejo"] = "cotejado" if registro_cmf["vigencia"] == esperado else "vigencia_distinta"
            resultado["razon_social_cmf"] = registro_cmf["razon_social_cmf"]
            resultado["vigencia_cmf"] = registro_cmf["vigencia"]
            resultado["detalle"] = ("RUT y vigencia coinciden con el registro." if resultado["cotejo"] == "cotejado"
                                    else f"El maestro dice «{estado}» y la CMF lo lista como «{registro_cmf['vigencia']}».")
        elif codigo in EXCEPCIONES:
            resultado["cotejo"] = "declarado"
            resultado["detalle"] = EXCEPCIONES[codigo]
        else:
            candidato = max(snapshot["entidades"],
                            key=lambda e: parecido(fila["razon_social"], e["razon_social_cmf"]),
                            default=None)
            resultado["cotejo"] = "no_en_registro"
            if candidato and parecido(fila["razon_social"], candidato["razon_social_cmf"]) >= 0.5:
                resultado["sugerencia"] = {"rut": candidato["rut"],
                                           "razon_social_cmf": candidato["razon_social_cmf"],
                                           "vigencia": candidato["vigencia"]}
                resultado["detalle"] = ("El RUT del maestro no está en el registro; la razón social "
                                        "se parece a la de la sugerencia.")
            else:
                resultado["detalle"] = "El RUT del maestro no está en el registro y no hay una entidad parecida."
        resultados.append(resultado)
    return resultados


def resumir(resultados: list[dict]) -> dict:
    cuenta: dict[str, int] = {}
    for r in resultados:
        cuenta[r["cotejo"]] = cuenta.get(r["cotejo"], 0) + 1
    return {"filas": len(resultados), "por_cotejo": dict(sorted(cuenta.items()))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--descargar", action="store_true", help="baja el registro CMF y reescribe el cotejo")
    ap.add_argument("--check", action="store_true", help="no escribe: falla si el cotejo publicado está incompleto")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    if not MAESTRO.exists():
        raise SystemExit(f"Falta el maestro: {MAESTRO.relative_to(ROOT)}")
    maestro = json.loads(MAESTRO.read_text(encoding="utf-8"))

    if args.descargar:
        snapshot = descargar()
    else:
        if not REGISTRO.exists():
            raise SystemExit(f"Falta el registro cotejado: {REGISTRO.relative_to(ROOT)}. "
                             "Corre con --descargar donde haya red.")
        snapshot = json.loads(REGISTRO.read_text(encoding="utf-8"))

    resultados = comparar(maestro, snapshot)
    resumen = resumir(resultados)
    pendientes = [r for r in resultados if r["cotejo"] in ("no_en_registro", "vigencia_distinta")]

    if args.verbose or not args.check:
        for r in resultados:
            if r["cotejo"] != "cotejado" or args.verbose:
                print(f"  {r['cotejo']:<17} {r['codigo_institucion']:>4}  {r['rut']:<12} {r['razon_social']}")
                if r.get("sugerencia"):
                    print(f"      CMF propone: {r['sugerencia']['rut']} · {r['sugerencia']['razon_social_cmf']}")
                elif r["cotejo"] != "cotejado":
                    print(f"      {r['detalle']}")
    print(json.dumps({**resumen, "fecha_cotejo": snapshot["fecha"]}, ensure_ascii=False, indent=1))

    if not args.check:
        if args.descargar:
            REGISTRO.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        payload = {"fecha": snapshot["fecha"], "fuente": snapshot["fuente"], "url": snapshot["url"],
                   "resumen": resumen, "filas": resultados}
        COTEJO.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"Cotejo escrito en {COTEJO.relative_to(ROOT)}")

    if pendientes:
        print(f"BANCA: {len(pendientes)} fila(s) del maestro no coinciden con el registro CMF")
        return 1
    if args.check:
        publicado = json.loads(COTEJO.read_text(encoding="utf-8"))
        if publicado.get("resumen", {}).get("por_cotejo") != resumen["por_cotejo"]:
            print("BANCA: el cotejo publicado no coincide con el maestro actual; vuelve a correr --descargar")
            return 1
    print("BANCA: las 41 filas están cotejadas o declaradas (agregados, filiales y entidad histórica)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
