"""Publica de punta a punta los siete registros incorporados por el formato 2024.

No hay muestras reales de estas fichas en el repositorio, así que se arman líneas sintéticas
con posiciones y PICTURE del anexo oficial. Se comprueban largos, lectura, conversiones de
campos, cuadratura y escritura Parquet de B.6, B.9–B.14.

  python -m seguros.tests.test_registros_2024
"""
import io
import tempfile
import zipfile
from pathlib import Path

from seguros.scripts import actualizar_carteras as ac
from seguros.scripts import ficha_1835
from seguros.scripts.formato_1835 import LARGO

PERIODO = "2024-12"
RUT = "076543210"        # 9 dígitos: el lector agrega el dígito verificador
NOMBRE = "COMPANIA DE PRUEBA S A"
NUEVAS = {"o": "otras_inversiones", "d": "tablas_descriptores",
          "t": "tablas_desarrollo", "e": "flujos_activos_elegibles",
          "r": "prestamos", "v": "bienes_raices_arriendo_morosidad",
          "g": "garantias_derivados"}
TIPO6 = {"e": "B.11", "g": "B.14"}


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
    # Casos de privacidad: un deudor/arrendatario y una contraparte persona natural.
    if letra == "r" and tipo == "2":
        relleno[30] = "N"                 # TIPO_DEUDOR
        relleno[40:49] = list("012345678") # RUT_DEUDOR, cuerpo bajo el umbral de persona jurídica
        relleno[49] = "5"                  # VER_DEUDOR
        relleno[50:59] = list("PERSONA  ")
        relleno[150:158] = list("NOMBRE  ")
    elif letra == "v" and tipo == "2":
        relleno[11:22] = list("ROL-001-002")
        relleno[33:41] = list("PERSONA ")
        relleno[93:102] = list("012345678")
        relleno[102] = "5"
    elif letra == "g" and tipo == "2":
        relleno[1:10] = list("012345678")
        relleno[10] = "5"
        relleno[31:39] = list("PERSONA ")
    return "".join(relleno)


def encabezado(letra: str) -> str:
    total = LARGO["v2024"][letra]
    return (f"1{RUT}5{NOMBRE[:60]:<60}{PERIODO.replace('-', '')}" + " " * total)[:total]


def totales(letra: str, cuantas: int) -> str:
    total = LARGO["v2024"][letra]
    return (f"3{cuantas:06d}" + " " * total)[:total]


def zip_mes() -> bytes:
    archivos = {}
    # B.1 y B.8 son obligatorios para que el mes se publique; se prueba además B.6 y B.9–B.14.
    for letra, tipo in (("i", "2"), ("c", "2")) + tuple((l, "2") for l in NUEVAS):
        cuerpo = [linea(letra, tipo), linea(letra, tipo)]
        if letra in TIPO6:
            cuerpo.append("6" + "Z" * (LARGO["v2024"][letra] - 1))
        lineas = [encabezado(letra)] + cuerpo + [totales(letra, len(cuerpo) + 2)]
        archivos[f"{letra}202501.v.{RUT}"] = "\r\n".join(lineas) + "\r\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for nombre, contenido in archivos.items():
            z.writestr(nombre, contenido.encode("latin-1"))
    return buf.getvalue()


def main() -> int:
    fallas = 0
    from seguros.scripts.vistas_1835 import RESUMENES_RELEVANTES
    ac._ESQUEMAS.clear()
    for base, (resumen, _titulo, columnas) in RESUMENES_RELEVANTES.items():
        nombres = ac.esquema(resumen).names
        if nombres != list(columnas):
            print(f"FALLA {resumen}: esquema distinto de la proyección declarada")
            fallas += 1
        if len(nombres) >= len(ac.esquema(base).names):
            print(f"FALLA {resumen}: no reduce columnas respecto de {base}")
            fallas += 1
    filas, companias, avisos, excluidos = ac.leer_zip(zip_mes(), PERIODO, "vida")
    if excluidos or not companias:
        print("FALLA: archivos excluidos:", excluidos)
        return 1
    for letra, tabla in NUEVAS.items():
        if len(filas[tabla]) != 2:
            print(f"FALLA {tabla}: {len(filas[tabla])} filas, se esperaban 2")
            fallas += 1
    registros_6 = filas["registros_tipo6"]
    if len(registros_6) != 2:
        print(f"FALLA registros_tipo6: {len(registros_6)} filas, se esperaban 2")
        fallas += 1
    else:
        for fila in registros_6:
            letra = "e" if fila["tipo_archivo"] == "B.11" else "g"
            if (fila["tipo_registro"] != "6" or fila["largo_registro"] != LARGO["v2024"][letra]
                    or fila["registro_original"] != "6" + "Z" * (LARGO["v2024"][letra] - 1)):
                print(f"FALLA: registro original tipo 6 no conservado ({fila['tipo_archivo']})")
                fallas += 1
    esperado = {
        "otras_inversiones": ("codigo_o_nombre_de_la_inversion", "X" * 20),
        "tablas_descriptores": ("codigo_nemotecnico", "X" * 30),
        "tablas_desarrollo": ("nro_cupon", 7),
        "flujos_activos_elegibles": ("circular_aplicada", 7),
        "prestamos": ("codigo_prestamo", 7),
        "bienes_raices_arriendo_morosidad": ("tipo_instrumento", "X" * 10),
        "garantias_derivados": ("identificador_garantia", "X" * 14),
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
        for tabla in [*NUEVAS.values(), "registros_tipo6"]:
            ruta = ac.ruta_particion(tabla, PERIODO)
            if not ruta.exists():
                print(f"FALLA {tabla}: no se escribió {ruta.name}")
                fallas += 1
                continue
            import pyarrow.parquet as pq
            schema = pq.read_schema(ruta)
            if "periodo" not in schema.names or schema.names[0] != "periodo":
                print(f"FALLA {tabla}: esquema inesperado {schema.names[:4]}")
                fallas += 1
            if pq.ParquetFile(ruta).metadata.num_rows != 2:
                print(f"FALLA {tabla}: el Parquet no tiene las 2 filas")
                fallas += 1
        # También se generan las dos vistas simplificadas cuyo registro completo está en este ZIP.
        for tabla in ("renta_fija_relevante", "prestamos_relevantes",
                      "bienes_raices_arriendo_morosidad_relevantes"):
            ruta = ac.ruta_particion(tabla, PERIODO)
            if not ruta.exists():
                print(f"FALLA {tabla}: no se escribió la vista de campos relevantes")
                fallas += 1
                continue
            import pyarrow.parquet as pq
            schema = pq.read_schema(ruta)
            from seguros.scripts.vistas_1835 import RESUMENES_RELEVANTES
            source = next(base for base, cfg in RESUMENES_RELEVANTES.items() if cfg[0] == tabla)
            if len(schema) >= len(ac.esquema(source)) or len(schema) < 10:
                print(f"FALLA {tabla}: proyección de columnas no simplificada ({len(schema)})")
                fallas += 1
            if pq.ParquetFile(ruta).metadata.num_rows != 2:
                print(f"FALLA {tabla}: el resumen no conservó las dos filas")
                fallas += 1
        import pyarrow.parquet as pq
        prestamos = pq.read_table(ac.ruta_particion("prestamos", PERIODO)).to_pandas()
        if not prestamos["rut_deudor"].isna().all() or not prestamos["nombre_deudor"].isna().all():
            print("FALLA privacidad B.12: quedó identidad de deudor natural")
            fallas += 1
        arriendos = pq.read_table(ac.ruta_particion("bienes_raices_arriendo_morosidad", PERIODO)).to_pandas()
        if not arriendos["rol"].isna().all() or not arriendos["rut_arrendatario_deudor"].isna().all():
            print("FALLA privacidad B.13: quedó rol o RUT de arrendatario natural")
            fallas += 1
        if not arriendos["property_id"].astype(str).str.startswith("BIEN-").all():
            print("FALLA privacidad B.13: no se generó property_id longitudinal")
            fallas += 1
        garantias = pq.read_table(ac.ruta_particion("garantias_derivados", PERIODO)).to_pandas()
        if not garantias["rut_contraparte_nacional"].isna().all() or not garantias["nombre_contraparte_garantia"].isna().all():
            print("FALLA privacidad B.14: quedó identidad de contraparte natural")
            fallas += 1
        if not garantias["contraparte_tipo"].eq("persona_natural_probable").all():
            print("FALLA privacidad B.14: no se clasificó contraparte natural")
            fallas += 1
        if any(tabla not in ac.TABLAS for tabla in [*NUEVAS.values(), "registros_tipo6"]):
            print("FALLA: el publicador no incluye todos los registros nuevos")
            fallas += 1

    print(f"avisos de lectura: {len(avisos)}")
    print(f"tablas publicadas: {len(tablas)} · nuevas: {len(NUEVAS)}")
    print("OK" if not fallas else f"{fallas} fallas")
    return 1 if fallas else 0


if __name__ == "__main__":
    raise SystemExit(main())
