"""Parseo compartido del TXT trimestral de estados financieros IFRS de la CMF.

Dos extractores leen el mismo archivo —`pipelines/ifrs_sectores/actualizar.py` (AGF,
securitizadoras y cajas de compensación) y `factoring_leasing/scripts/backfill_ifrs.py`—
y durante un tiempo cada uno interpretó el TXT por su cuenta: distinta forma de contar la
posición de una cuenta dentro del estado, distinto criterio para un importe no entero,
distinta traducción del tipo de balance. Publicaban el mismo dato con semánticas que no
eran la misma, que es la peor forma de divergir: las dos tablas se ven iguales.

Este módulo es la parte compartida. Lo que aquí vive es lo que cuesta acertar:

  * reconocer el archivo de verdad (la CMF responde HTML cuando algo falla);
  * decidir a qué tabla va cada línea según el código de estado (`ESF*` balance, `ER*`
    resultados, el resto —flujos de efectivo— no se publica);
  * tratar el importe: entero literal o nada, nunca un cero inventado ni un separador
    decimal adivinado;
  * contar el `orden` y la `repeticion`, que es lo que permite reconstruir el estado tal
    como lo presenta la sociedad y saber cuándo una cuenta aparece dos veces.

Cada extractor arma su propia fila (publican esquemas distintos, y cambiar el esquema
publicado rompe las consultas de quien ya las guardó), pero los dos pasan por aquí.

Formato del archivo (`ver_archivo.php?inicio=AAAAMM&termino=AAAAMM`), separado por `;`:
    periodo;rut;nombre;I|C;moneda;cuenta;valor;taxonomia;estado
"""
from __future__ import annotations

import io
import re
import unicodedata

from pipelines.auto.rut import dv  # noqa: F401  (reexportado: los extractores lo usaban local)

ENTEROS = re.compile(r"-?\d+")
TAMANO_MAXIMO_TEXTO = 200

# Letra del archivo -> valor publicado.
TIPO_BALANCE = {"I": "individual", "C": "consolidado"}

# Prefijo del código de estado -> tabla publicada. Los flujos de efectivo (EFMD/EFMI)
# y cualquier estado nuevo que no sea balance ni resultados quedan fuera.
TABLAS = {"balance": "ESF", "resultados": "ER"}


def es_txt(raw: bytes) -> bool:
    """¿La descarga es el TXT y no una página de error de la CMF?"""
    if not raw:
        return False
    cabecera = raw[:2000].lower()
    return (b"<html" not in cabecera and b"<!doctype" not in cabecera
            and b"accion no permitida" not in cabecera)


def decodificar(raw: bytes) -> str:
    """El archivo viene en UTF-8; algunos años vienen con caracteres latin-1 sueltos."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def normalizar(s: str) -> str:
    """Mayúsculas, sin acentos y con espacios colapsados: para comparar nombres de sociedad."""
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s or "").upper())
                if not unicodedata.combining(c))
    return " ".join(s.split())


def lineas(raw: bytes):
    """Itera las celdas del archivo (separador «;»), descartando líneas vacías.

    Devuelve `(numero, celdas)` para que el aviso de una línea rara diga dónde.
    """
    import csv
    for n, c in enumerate(csv.reader(io.StringIO(decodificar(raw)), delimiter=";"), start=1):
        if not c or all(not x.strip() for x in c):
            continue
        yield n, [x.strip() for x in c]


def tabla_de(estado: str) -> str | None:
    """'balance' para ESF*, 'resultados' para ER*, None para lo que no se publica."""
    estado = (estado or "").strip()
    return next((t for t, prefijo in TABLAS.items() if estado.startswith(prefijo)), None)


def valor_y_texto(texto: str) -> tuple[int | None, str | None]:
    """Importe del archivo: entero literal, o nulo con el texto original a salvo.

    Nunca se redondea, nunca se interpreta una coma decimal y nunca se devuelve 0 por
    un valor que no se entendió: si no es un entero, `valor` queda nulo y el texto va a
    `valor_no_numerico` / `valor_texto_original`.
    """
    t = (texto or "").strip()
    if ENTEROS.fullmatch(t):
        return int(t), None
    return None, t[:TAMANO_MAXIMO_TEXTO]


class Contextos:
    """Cuenta la posición de cada cuenta en su estado y las veces que se repite.

    Un mismo estado puede traer dos veces la misma glosa (por ejemplo «Ganancia
    (pérdida)», que aparece como resultado del ejercicio y otra vez en su atribución).
    Sin este ordinal, quien sume por nombre de cuenta cuenta esa cifra dos veces.

    `orden` se cuenta por (sociedad, tipo de balance, moneda, taxonomía y estado): la
    taxonomía entra en la llave para que dos taxonomías del mismo estado no intercalen
    sus cuentas. `repeticion` añade la cuenta, así que marca la enésima vez que ESA
    cuenta aparece en el mismo contexto.
    """

    def __init__(self):
        self._orden: dict[tuple, int] = {}
        self._repeticion: dict[tuple, int] = {}

    def agregar(self, clave_estado: tuple, cuenta: str) -> tuple[int, int]:
        self._orden[clave_estado] = self._orden.get(clave_estado, 0) + 1
        clave_cuenta = clave_estado + (cuenta,)
        self._repeticion[clave_cuenta] = self._repeticion.get(clave_cuenta, 0) + 1
        return self._orden[clave_estado], self._repeticion[clave_cuenta]

    def clave_estado(self, periodo, rut, tipo, moneda, taxonomia, estado) -> tuple:
        return (periodo, rut, tipo, moneda, taxonomia, estado)
