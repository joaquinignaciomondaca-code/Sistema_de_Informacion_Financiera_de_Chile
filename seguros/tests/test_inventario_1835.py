"""Contrasta la ficha técnica con lo que publica el inventario (sin pandas ni pyarrow).

Tres comprobaciones, todas contra el anexo 2024 (`Anexos_Tecnicos_Circular_N1835.txt`):

1. **Campos por registro.** El número de campos de cada registro de detalle coincide con la
   tabla de campos que publica la CMF en el anexo (que no cuenta los `FILLER`).
2. **Largo del registro.** La suma de los largos de los campos es exactamente el largo del
   registro tipo 1 del mismo archivo: si un campo falta o sobra, la suma deja de cuadrar.
3. **Cobertura publicada.** Las columnas publicadas (que unen el RUT con su dígito verificador
   y omiten `TIPO`, `FILLER`) cubren el registro sin huecos ni solapes, de la posición 1 al
   último carácter.

  python -m seguros.tests.test_inventario_1835
"""
from seguros.scripts import ficha_1835
from seguros.scripts.formato_1835 import LARGO, TIPO_TOTAL
from seguros.scripts.inventario_1835 import DESTINO, NOMBRES_POSICION, inventario

# Campos por registro de detalle según la tabla de la CMF (sin contar FILLER).
CAMPOS_CMF = {
    ("i", "2"): 107, ("a", "2"): 56, ("f", "2"): 34, ("b", "2"): 53,
    ("x", "2"): 50, ("x", "3"): 54, ("x", "4"): 41, ("x", "5"): 15,
    ("o", "2"): 31, ("r", "2"): 78, ("v", "2"): 39, ("g", "2"): 22,
    ("p", "2"): 41, ("p", "3"): 44, ("p", "4"): 42, ("p", "5"): 49, ("p", "6"): 28,
    ("c", "2"): 12, ("d", "2"): 18, ("t", "2"): 9, ("e", "2"): 14,
}

# Registro tipo 1 de cada archivo: el largo que debe sumar el registro de detalle.
LARGO_ARCHIVO = {"i": 970, "a": 572, "f": 361, "b": 506, "x": 611, "o": 510,
                 "p": 587, "c": 138, "d": 108, "t": 80, "e": 178,
                 "r": 658, "v": 443, "g": 300}


def main() -> int:
    regs = ficha_1835.registros("v2024")
    fallas = 0

    # 1 y 2: campos y largo, contra la tabla de la CMF y el registro de identificación.
    for clave, esperados in sorted(CAMPOS_CMF.items()):
        registro = regs.get(clave)
        if registro is None:
            print(f"FALLA {clave}: el anexo no trae el registro")
            fallas += 1
            continue
        reales = sum(1 for c in registro.campos if c.nombre != "FILLER")
        if reales != esperados:
            print(f"FALLA {clave}: {reales} campos, la tabla de la CMF dice {esperados}")
            fallas += 1
        for tipo in ("1", "3"):
            ident = regs.get((clave[0], tipo))
            if ident is not None and ident.total != registro.total:
                print(f"FALLA {clave}: el detalle suma {registro.total} y el registro {tipo} "
                      f"declara {ident.total}")
                fallas += 1
        if registro.total != LARGO_ARCHIVO[clave[0]]:
            print(f"FALLA {clave}: suma {registro.total}, el archivo mide {LARGO_ARCHIVO[clave[0]]}")
            fallas += 1
        if LARGO["v2024"][clave[0]] != LARGO_ARCHIVO[clave[0]]:
            print(f"FALLA {clave[0]}: formato_1835.LARGO dice {LARGO['v2024'][clave[0]]}")
            fallas += 1

    # Ningún campo puede quedar sin nombre ni con una letra suelta (síntoma de una ficha
    # mal convertida: el nombre se imprime en otra columna).
    for clave, registro in sorted(regs.items()):
        malos = [c for c in registro.campos
                 if (c.nombre == "SIN_NOMBRE" or len(c.nombre) <= 2)
                 and (clave[0], clave[1], c.inicio) not in NOMBRES_POSICION]
        if malos:
            print(f"FALLA {clave}: {len(malos)} campos sin nombre reparable ({malos[0].inicio})")
            fallas += 1
    for (letra, tipo), columnas in inventario("v2024").items():
        for campo in columnas:
            if "sin_nombre" in campo["columna"]:
                print(f"FALLA {(letra, tipo)}: columna publicada sin nombre oficial ({campo['inicio']})")
                fallas += 1

    # 3: las columnas publicadas cubren el registro de punta a punta.
    for clave, columnas in sorted(inventario("v2024").items()):
        registro = regs[clave]
        orden = sorted(columnas, key=lambda c: c["inicio"])
        tope = 1  # el registro tipo 2 arranca con TIPO, que no se publica
        for columna in orden:
            if columna["inicio"] != tope:
                print(f"FALLA {clave}: hueco o solape en {columna['columna']} "
                      f"(inicio {columna['inicio']}, se esperaba {tope})")
                fallas += 1
                break
            tope = columna["inicio"] + columna["largo"]
        # El relleno final (FILLER) no se publica: la cobertura termina donde empieza.
        esperado = registro.total - sum(c.largo for c in registro.campos if c.nombre == "FILLER")
        if tope != esperado:
            print(f"FALLA {clave}: las columnas cubren hasta {tope} de {esperado}")
            fallas += 1
        columnas_repetidas = {c["columna"] for c in columnas if
                              [x["columna"] for x in columnas].count(c["columna"]) > 1}
        if columnas_repetidas:
            print(f"FALLA {clave}: columnas repetidas {sorted(columnas_repetidas)}")
            fallas += 1

    # Los registros de otros archivos también tienen que estar mapeados a una tabla.
    for letra in LARGO_ARCHIVO:
        if (letra, "2") not in DESTINO:
            print(f"FALLA {letra}: el registro de detalle no tiene tabla destino")
            fallas += 1
        if letra in TIPO_TOTAL and not regs.get((letra, TIPO_TOTAL[letra])):
            print(f"FALLA {letra}: el anexo no trae el registro de totales ({TIPO_TOTAL[letra]})")
            fallas += 1

    publicadas = {t for (_, _), (t, _) in DESTINO.items()}
    print(f"{len(regs)} registros leídos · {len(publicadas)} tablas de detalle cubiertas")
    print("OK" if not fallas else f"{fallas} fallas")
    return 1 if fallas else 0


if __name__ == "__main__":
    raise SystemExit(main())
