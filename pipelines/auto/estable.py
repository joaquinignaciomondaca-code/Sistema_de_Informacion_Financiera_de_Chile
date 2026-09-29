"""Escritura de manifiestos que no cambia el archivo si solo cambió la hora.

Los extractores estampaban `updated_at` (y `leido_utc`, `ultima_consulta_utc`…) en cada corrida,
aunque la CMF no hubiera publicado nada nuevo. Resultado: cada ejecución programada dejaba un
commit con solo marcas de tiempo, regeneraba el data_manifest y el catálogo de descargas, y dejaba
un historial donde es imposible ver cuándo entraron datos de verdad.

`escribir_json` compara el contenido nuevo con el que ya está en disco ignorando los campos
volátiles; si no hay diferencias, no toca el archivo. Consecuencias deliberadas:

  * `updated_at` / `ultima_actualizacion` significan «última vez que cambió algo», no «última vez
    que corrió el workflow»; la frescura de los workflows se mide con las corridas de Actions
    (scripts/audit_automatizacion.py --frescura), no con estos campos.
  * Cuando sí hay cambios reales, se escribe el objeto completo con las marcas nuevas.
"""
from __future__ import annotations

import json
from pathlib import Path

VOLATILES = frozenset({"updated_at", "ultima_actualizacion", "leido_utc", "ultima_consulta_utc",
                       "ultima_revision_utc"})


def sin_volatiles(obj):
    if isinstance(obj, dict):
        return {k: sin_volatiles(v) for k, v in obj.items() if k not in VOLATILES}
    if isinstance(obj, list):
        return [sin_volatiles(v) for v in obj]
    return obj


def escribir_json(ruta: Path, obj, indent: int = 2) -> bool:
    """Escribe `obj` como JSON. Devuelve False (sin tocar el archivo) si solo difieren las marcas de tiempo."""
    texto = json.dumps(obj, ensure_ascii=False, indent=indent) + "\n"
    ruta = Path(ruta)
    if ruta.exists():
        try:
            previo = json.loads(ruta.read_text(encoding="utf-8"))
            if sin_volatiles(previo) == sin_volatiles(json.loads(texto)):
                return False
        except ValueError:
            pass  # archivo previo ilegible: se reescribe
    ruta.write_text(texto, encoding="utf-8")
    return True
