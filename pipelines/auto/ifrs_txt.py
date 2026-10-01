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
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

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


# ---------------------------------------------------------------------------
# Fecha de «actualizado» del índice
# ---------------------------------------------------------------------------
# El índice (`estadisticas_ifrs.php`) muestra, junto a cada archivo, cuándo lo actualizó la CMF:
#     Diciembre 2025   (actualizado: 26/08/2026 22:01)
#     2024             (actualizado: 31/03/2025)
# La CMF reedita cierres antiguos (en 2026 tocó dic-2025 y los tres primeros trimestres de 2025
# mucho después de su cierre). Quien solo relee los trimestres «abiertos» no se entera, así que
# los extractores usan esta fecha para decidir si un trimestre ya cerrado hay que volver a bajarlo.

ZONA_CMF = "America/Santiago"
MESES_CIERRE = ("03", "06", "09", "12")
_ACTUALIZADO = re.compile(
    r"actualizado\s*:?\s*(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+(\d{1,2}):(\d{2}))?", re.IGNORECASE)
_ENLACE_ARCHIVO = re.compile(r"ver_archivo\.php\?(?:[^#]*?&)?inicio=(\d{6})&termino=(\d{6})")


def _zona_cmf():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(ZONA_CMF)
    except Exception:  # noqa: BLE001 - sin base de zonas horarias en el sistema
        return None


def fecha_actualizado(texto: str) -> datetime | None:
    """«(actualizado: 30/09/2026 23:59)» → instante en UTC; sin texto o fecha imposible, `None`.

    La hora es la de Chile. Si el índice solo trae el día, se toma el final de ese día: para
    decidir una relectura es la lectura prudente (a lo sumo se baja una vez de más).
    """
    m = _ACTUALIZADO.search(texto or "")
    if not m:
        return None
    dia, mes, anio, hora, minuto = m.groups()
    try:
        local = datetime(int(anio), int(mes), int(dia), int(hora) if hora else 23,
                         int(minuto) if minuto else 59, 0 if hora else 59)
    except ValueError:
        return None
    zona = _zona_cmf()
    if zona is not None:
        # fold=1: ante una hora repetida por el cambio de horario, la lectura posterior.
        return local.replace(tzinfo=zona, fold=1).astimezone(timezone.utc)
    return (local + timedelta(hours=4)).replace(tzinfo=timezone.utc)  # peor caso: UTC-4


class _EnlacesConFecha(HTMLParser):
    """Junta, para cada enlace a un archivo, el texto que le sigue hasta el enlace siguiente."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.entradas: list[tuple[str, str, list[str]]] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        m = _ENLACE_ARCHIVO.search((dict(attrs).get("href") or "").replace("&amp;", "&"))
        if m:
            self.entradas.append((m.group(1), m.group(2), []))

    def handle_data(self, data):
        if self.entradas:
            self.entradas[-1][2].append(data)


def actualizaciones_indice(raw: bytes) -> dict[str, datetime]:
    """Trimestre (AAAAMM) → cuándo dice la CMF que actualizó el archivo que lo contiene.

    Un enlace anual (`inicio=202403&termino=202412`) vale para sus cuatro trimestres. Si el
    índice no trae fechas —o cambia de forma—, devuelve `{}` y los extractores se comportan
    como siempre: nada se relee por reedición.
    """
    if not raw:
        return {}
    parser = _EnlacesConFecha()
    try:
        parser.feed(raw.decode("utf-8", errors="replace"))
        parser.close()
    except Exception:  # noqa: BLE001 - un HTML roto no debe tirar la corrida
        return {}
    por_enlace: dict[tuple[str, str], datetime] = {}
    for inicio, fin, trozos in parser.entradas:
        fecha = fecha_actualizado(" ".join(trozos))
        if fecha is not None and fecha > por_enlace.get((inicio, fin), fecha - timedelta(seconds=1)):
            por_enlace[(inicio, fin)] = fecha
    por_trimestre: dict[str, datetime] = {}
    for (inicio, fin), fecha in por_enlace.items():
        if inicio > fin or inicio[4:] not in MESES_CIERRE or fin[4:] not in MESES_CIERRE:
            continue
        anio, mes = int(inicio[:4]), int(inicio[4:])
        while f"{anio:04d}{mes:02d}" <= fin:
            clave = f"{anio:04d}{mes:02d}"
            if fecha > por_trimestre.get(clave, fecha - timedelta(seconds=1)):
                por_trimestre[clave] = fecha
            mes += 3
            if mes > 12:
                anio, mes = anio + 1, 3
    return por_trimestre


def reeditado_despues(leido_utc: str | None, actualizado: datetime | None) -> bool:
    """¿La CMF actualizó el archivo después de la última lectura? Sin uno de los datos, no."""
    if actualizado is None or not leido_utc:
        return False
    try:
        leido = datetime.fromisoformat(str(leido_utc))
    except ValueError:
        return False
    if leido.tzinfo is None:
        leido = leido.replace(tzinfo=timezone.utc)
    return actualizado > leido
