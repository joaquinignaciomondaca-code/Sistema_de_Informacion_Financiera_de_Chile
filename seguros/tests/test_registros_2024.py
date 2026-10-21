"""Publica de punta a punta los registros que el anexo 2024 agregó (B.6 y B.9–B.11).

No hay muestras reales de esos archivos en el repositorio (la CMF no los publica hasta
2024-12 y el sandbox no llega a cmfchile.cl), así que esta prueba arma líneas sintéticas con
la posición y el PICTURE de la ficha: si el inventario estuviera corrido, las líneas no
medirían lo que mide el archivo y `leer_zip` las rechazaría.

Se comprueba: largo de cada línea, que las cuatro tablas nuevas se publiquen, que una columna
conocida de cada una traiga el valor sintético, y que el Parquet se escriba con su esquema.

  python -m seguros.tests.test_registros_2024
"""
import io
import tempfile
import zipfile
from pathlib import Path

from seguros.scripts import actualizar_carteras as ac
from seguros.scripts import ficha_1835
from seguros.scripts.formato_1835 import LARGO

PERIODO = "2025-01"
RUT = "076543210"        # 9 dígitos: el lector agrega el dígito verificador
NOMBRE = "COMPANIA DE PRUEBA S A"
NUEVAS = {"o": "otras_inversiones", "d": "tablas_descriptores",
          "t": "tablas_desarrollo", "e": "flujos_activos_elegibles"}


def linea(letra: str, tipo: str) -> str:
    """Una línea de detalle con el largo exacto del archivo, según la ficha."""
    camp = ficha_1835.registros("v2024")[(letra, tipo)]
    total = LARGO["v2024"][letra]
    relleno = [" "] * total
    for campo in camp.campos:
        nombre, inicio, largo, t, dec = campo.nombre, campo.inicio, campo.largo, campo.tipo, campo.decimales
        if inicio == 0:      # TIPO: el carácter que dice qué registro es
            relleno[0] = tipo
            continue
        if largo == 1 and t == "t" and nombre.startswith(("VERIFICADOR", "DV", "DIG", "VER_")):
            valor = "5"                      # dígito verificador del RUT
        elif t == "f":
            valor = "20240131"
        elif t == "r":
            valor = RUT + "5"
        elif t == "n" and largo == 9 and nombre.startswith(("RUT", "NRO_RUT", "RUN")):
            valor = RUT                      # el dígito verificador va en el campo siguiente
        elif t == "n":
            valor = "0" * (largo - dec - 1) + "7" + "7" * dec
        else:                                # texto (incluidos los rellenos)
            valor = "X" * largo
        relleno[inicio:inicio + largo] = list(valor[:largo])
    return "".join(relleno)


def encabezado(letra: str) -> str:
    total = LARGO["v2024"][letra]
    return (f"1{RUT}5{NOMBRE[:60]:<60}{PERIODO.replace('-', '')}" + " " * total)[:total]


def totales(letra: str, cuantas: int) -> str:
    total = LARGO["v2024"][letra]
    return (f"3{cuantas:06d}" + " " * total)[:total]


def zip_mes() -> bytes:
    archivos = {}
    # B.1 y B.8 son obligatorios para que el mes se publique; el resto es lo que se prueba.
    for letra, tipo in (("i", "2"), ("c", "2")) + tuple((l, "2") for l in NUEVAS):
        cuerpo = [linea(letra, tipo), linea(letra, tipo)]
        lineas = [encabezado(letra)] + cuerpo + [totales(letra, len(cuerpo) + 2)]
        archivos[f"{letra}202501.v.{RUT}"] = "\r\n".join(lineas) + "\r\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for nombre, contenido in archivos.items():
            z.writestr(nombre, contenido.encode("latin-1"))
    return buf.getvalue()


def main() -> int:
    fallas = 0
    filas, companias, avisos, excluidos = ac.leer_zip(zip_mes(), PERIODO, "vida")
    if excluidos or not companias:
        print("FALLA: archivos excluidos:", excluidos)
        return 1
    for letra, tabla in NUEVAS.items():
        if len(filas[tabla]) != 2:
            print(f"FALLA {tabla}: {len(filas[tabla])} filas, se esperaban 2")
            fallas += 1
    esperado = {
        "otras_inversiones": ("codigo_o_nombre_de_la_inversion", "X" * 20),
        "tablas_descriptores": ("codigo_nemotecnico", "X" * 30),
        "tablas_desarrollo": ("nro_cupon", 7),
        "flujos_activos_elegibles": ("circular_aplicada", 7),
    }
    for tabla, (columna, valor) in esperado.items():
        fila = filas[tabla][0] if filas[tabla] else {}
        if fila.get(columna) != valor:
            print(f"FALLA {tabla}.{columna}: {fila.get(columna)!r} != {valor!r}")
            fallas += 1
    if filas["tablas_descriptores"] and filas["tablas_descriptores"][0].get("rut_del_emisor") != "76543210-5":
        print("FALLA descriptores.rut_del_emisor:", filas["tablas_descriptores"][0].get("rut_del_emisor"))
        fallas += 1
    if filas["flujos_activos_elegibles"] and filas["flujos_activos_elegibles"][0].get("tramo_10_uf") != 7.777:
        print("FALLA flujos.tramo_10_uf:", filas["flujos_activos_elegibles"][0].get("tramo_10_uf"))
        fallas += 1

    # Escritura: cada tabla nueva deja su Parquet y su manifiesto.
    with tempfile.TemporaryDirectory() as tmp:
        ac.SALIDA = Path(tmp)
        ac._ESQUEMAS.clear()
        tablas = ac.tablas_de(PERIODO)
        ac.escribir_periodo(PERIODO, filas, tablas)
        for tabla in NUEVAS.values():
            ruta = ac.ruta_particion(tabla, PERIODO)
            if not ruta.exists():
                print(f"FALLA {tabla}: no se escribió {ruta.name}")
                fallas += 1
                continue
            import pyarrow.parquet as pq
            esquema = pq.read_schema(ruta)
            if "periodo" not in esquema.names or esquema.names[0] != "periodo":
                print(f"FALLA {tabla}: esquema inesperado {esquema.names[:4]}")
                fallas += 1
            if pq.ParquetFile(ruta).metadata.num_rows != 2:
                print(f"FALLA {tabla}: el Parquet no tiene las 2 filas")
                fallas += 1
        if "otras_inversiones" not in ac.TABLAS or "flujos_activos_elegibles" not in ac.TABLAS:
            print("FALLA: el publicador no incluye las tablas nuevas")
            fallas += 1

    print(f"avisos de lectura: {len(avisos)}")
    print(f"tablas publicadas: {len(tablas)} · nuevas: {len(NUEVAS)}")
    print("OK" if not fallas else f"{fallas} fallas")
    return 1 if fallas else 0


if __name__ == "__main__":
    raise SystemExit(main())
