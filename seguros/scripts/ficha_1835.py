"""Lector de las fichas técnicas de la Circular 1835 (CMF).

Convierte el texto oficial de las fichas (``seguros/fuentes/fichas_tecnicas_1835/``)
en una lista ordenada de campos con su posición, largo, tipo y descripción, tal
como los define la CMF. Sirve para construir y para auditar el inventario de
campos publicados: si la CMF cambia la ficha, este lector lo detecta.

Las fichas son texto plano con sus propias mañas, y este módulo las resuelve:

  - saltos de página (``\\f``) que parten un nombre en dos renglones
    (``CODIGO_`` / ``OPERACIÓN``) o un paréntesis (``POSICIÓN_CORTA_(no`` /
    ``mbre)``);
  - nombres separados por espacios (``VALOR RAZONABLE``);
  - anotaciones de unidad (``(M$)``, ``(UM)``, ``($)``) y calificadores
    (``PRIMA_DE_LA_OPCION (monto)`` y ``(moneda)``);
  - PICTURE impreso con espacios (``X (05)``, ``-9(03) V9 (04)``) y a veces un
    renglón antes del nombre;
  - subcampos escritos como etiqueta (``Local: Se indicará si es un local.``),
    que se publican con el prefijo del grupo al que pertenecen;
  - referencias cruzadas del tipo "B.1, el cual deberá...", que no son títulos
    de sección.

Posiciones: se acumulan en el orden en que la ficha las lista. Que cada registro
sume exactamente el largo real del archivo (p. ej. 930 caracteres en renta fija
hasta 2024-11) es la validación más fuerte de que el orden es el correcto.

Uso:
  python -m seguros.scripts.ficha_1835 --listar --formato v2024
  python -m seguros.scripts.ficha_1835 --archivo i --tipo 2 --formato v2016
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FUENTES = RAIZ / "seguros" / "fuentes" / "fichas_tecnicas_1835"

# Ficha vigente hasta 2024-11 y Anexo Técnico vigente desde 2024-12 (Circular 2354).
FICHA = {
    "v2016": {
        "i": "B.1_Instrumentos_de_Renta_Fija.txt",
        "a": "B.2_Acciones_S.A._abiertas_Acc_S.A_cerradas_y_cuotas_FFII.txt",
        "f": "B.3_Cuotas_de_Fondos_Mutuos.txt",
        "b": "B.4_Bienes_Raices.txt",
        "x": "B.5_Inversiones_en_el_Extranjero.txt",
        "p": "B.7_Inversiones_e_Instrumentos_derivados_y_pactos.txt",
        "c": "B.8_Informacion_de_Control.txt",
    },
    "v2024": {letra: "Anexos_Tecnicos_Circular_N1835.txt" for letra in "iafbxpc"},
}

# Letra del archivo según el título de la sección en la ficha.
LETRA = {"1": "i", "2": "a", "3": "f", "4": "b", "5": "x", "7": "p", "8": "c"}

# La ficha no es uniforme con los PICTURE: a veces los imprime con espacios
# ("X (05)", "-9(03) V9 (04)"). Sin aceptarlos, campos como COBERTURA,
# CRITERIO_VALORIZACION, ACTIVO_CALCE o TIR_COMPRA quedaban fuera del inventario
# y todas las posiciones siguientes quedaban corridas.
_PICT = r"(?:S|-)?9\s*\(\s*\d+\s*\)\s*(?:V9\s*\(\s*\d+\s*\))?|X\s*\(\s*\d+\s*\)"
_PICT_FIN = re.compile(r"\s(" + _PICT + r")\s*$")
_ENCABEZADO = re.compile(r"^\s*CAMPO\s+DESCRIP", re.I)
_SECCION = re.compile(r"^\s*B\.(\d+)\s+([A-ZÁÉÍÓÚÑ0-9°º.,\- ]{3,140})\s*$")
_REGISTRO = re.compile(r"Registro tipo\s+(\d+)", re.I)
_TOKEN_NOMBRE = re.compile(r"^[A-Z0-9ÁÉÍÓÚÑ_.$()+]+$")
# Una o varias palabras en mayúsculas al principio del renglón (trozo de nombre).
_PALABRA = r"[A-Z0-9ÁÉÍÓÚÑ_.$()+]{2,}"
_FRAGMENTO = re.compile(r"^\s{0,14}((?:" + _PALABRA + r"\s+){0,3}" + _PALABRA + r")(?:\s+|$)(.*)$")
_SOLO_MAYUSCULAS = re.compile(r"^[^a-z]*$")
_REFERENCIA = re.compile(r"^B\.\d+$")

# Anotaciones de unidad que la ficha escribe al lado del nombre. Se guardan aparte
# y se agregan al nombre normalizado (un M$ y un $ son mil veces distintos).
UNIDADES = ("(M$)", "(UM)", "($)", "(US$)", "(UF)", "(U.F.)")
SUFIJO_UNIDAD = {"(M$)": "M_CLP", "(UM)": "UM", "($)": "CLP", "(US$)": "USD", "(UF)": "UF",
                 "(U.F.)": "UF"}


_UNIDAD_TEXTO = (
    (re.compile(r"miles de pesos|\(M\$\)|\bM\$", re.I), "(M$)"),
    (re.compile(r"\ben UF\b|expresad[oa]s? en UF|\(UF\)", re.I), "(UF)"),
    (re.compile(r"\ben pesos\b|\(\$\)", re.I), "($)"),
    (re.compile(r"unidad de reajustabilidad|unidades monetarias|unidad monetaria|\(UM\)", re.I), "(UM)"),
    (re.compile(r"\ben d[oó]lares\b|\(US\$\)", re.I), "(US$)"),
)


def unidad_del_texto(texto: str) -> str | None:
    """Unidad declarada en la descripción ("expresarse en pesos ($)", "en miles de pesos")."""
    for patron, unidad in _UNIDAD_TEXTO:
        if patron.search(texto or ""):
            return unidad
    return None


@dataclass
class Campo:
    """Un campo del registro, con la posición que le da la ficha."""

    nombre: str                    # nombre normalizado (el que se publica)
    nombre_ficha: str              # nombre tal cual sale en la ficha
    picture: str
    largo: int
    inicio: int
    tipo: str                      # t texto · n número · f fecha AAAAMMDD · r RUT · x relleno
    decimales: int = 0
    con_signo: bool = False
    unidad: str | None = None
    grupo: str | None = None
    descripcion: str = ""
    renglon: int = 0
    ficha: str = ""


@dataclass
class Registro:
    """Un tipo de registro de un archivo (p. ej. archivo i, registro tipo 2)."""

    letra: str
    tipo: str
    formato: str = ""
    campos: list[Campo] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(c.largo for c in self.campos)

    def busca(self, nombre: str) -> Campo | None:
        for c in self.campos:
            if c.nombre == nombre:
                return c
        return None


# ---------------------------------------------------------------------------
# Lectura del texto
# ---------------------------------------------------------------------------
def _leer(ruta: Path) -> list[str]:
    """Lee la ficha y junta los renglones que la maquetación partió a medias.

    Se juntan los renglones que dejan un paréntesis sin cerrar (``POSICIÓN_CORTA_(no``
    + ``mbre)``), que es como la ficha parte los nombres largos al pasar de página.
    """
    texto = ruta.read_text(encoding="utf-8", errors="replace").replace("\f", "\n")
    salida: list[str] = []
    for linea in texto.split("\n"):
        while (
            salida
            and salida[-1].count("(") > salida[-1].count(")")
            and not _PICT_FIN.search(salida[-1])
            and linea.strip()
        ):
            salida[-1] = f"{salida[-1].rstrip()} {linea.strip()}"
            linea = ""
        if linea or not salida:
            salida.append(linea)
    return salida


def _picture(picture: str) -> tuple[int, str, int, bool]:
    """Largo, tipo, decimales y si lleva signo, según el PICTURE de la ficha."""
    p = re.sub(r"\s+", "", picture)
    m = re.fullmatch(r"(S|-)?9\((\d+)\)(?:V9\((\d+)\))?", p)
    if m:
        signo = bool(m.group(1))
        return (1 if signo else 0) + int(m.group(2)) + int(m.group(3) or 0), "n", int(m.group(3) or 0), signo
    m = re.fullmatch(r"X\((\d+)\)", p)
    if not m:  # pragma: no cover - la ficha no usa otros PICTURE
        raise ValueError(f"PICTURE no reconocido: {picture!r}")
    return int(m.group(1)), "t", 0, False


def _es_campo(linea: str) -> bool:
    return bool(_PICT_FIN.search(linea)) and not _ENCABEZADO.match(linea)


def normalizar(nombre: str) -> str:
    """Nombre de columna: mayúsculas, sin acentos, espacios y guiones como "_"."""
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", nombre) if not unicodedata.combining(c)
    )
    limpio = re.sub(r"[^A-Za-z0-9]+", "_", sin_acentos).strip("_")
    return limpio.upper()


# ---------------------------------------------------------------------------
# Nombres
# ---------------------------------------------------------------------------
def _nombre(linea: str) -> tuple[str, str | None, str, int, bool] | None:
    """Saca (nombre, unidad, resto, sangría, incompleto) si la línea trae un nombre.

    El nombre se arma con la seguidilla de tokens en mayúsculas del principio de
    la línea; se detiene en el primero que lleva minúsculas, que ya es descripción.
    ``incompleto`` indica que terminaba en "_" (la cola viene en otro renglón).
    """
    m = re.match(r"^(\s{0,14})(\S+)(\s+|$)(.*)$", linea.rstrip())
    if not m:
        return None
    sangria, token, _, resto = m.groups()
    if not _TOKEN_NOMBRE.match(token) or not _SOLO_MAYUSCULAS.match(token):
        return None
    if token.endswith(":"):  # es una etiqueta de subcampo ("Local: Se indicará...")
        return None
    partes = [token]
    unidad: str | None = None
    while True:
        m2 = re.match(r"^(\S+)(\s+|$)(.*)$", resto)
        if not m2:
            break
        tok, _, cola = m2.groups()
        if tok in UNIDADES:
            unidad = tok
            resto = cola
            continue
        if _REFERENCIA.match(tok):  # "B.1" al lado del nombre: referencia, no nombre
            resto = cola
            continue
        if re.fullmatch(r"\([a-záéíóúñ ]+\)", tok):  # calificador: "(monto)", "(moneda)"
            partes.append(tok.strip("()"))
            resto = cola
            continue
        if tok.startswith("("):  # paréntesis partido: se descarta la cola
            tok = tok.split("(")[0]
            if not tok:
                break
        # Calificador pegado al token: "POSICIÓN_CORTA_(nombre)".
        cabeza_tok = tok
        calificador = ""
        if "(" in tok:
            cabeza_tok, _, cola_tok = tok.partition("(")
            calificador = cola_tok
        if not (_TOKEN_NOMBRE.match(cabeza_tok) and _SOLO_MAYUSCULAS.match(cabeza_tok)):
            break
        partes.append(cabeza_tok)
        if calificador and re.fullmatch(r"[A-Za-záéíóúñ0-9_.+ ]+\)?", calificador):
            partes.append(re.sub(r"[^A-Za-z0-9]+", "_", calificador.rstrip(")")).strip("_"))
        resto = cola
    incompleto = partes[-1].endswith("_")
    nombre = "_".join(p.strip("_") for p in partes if p.strip("_"))
    return nombre, unidad, resto.strip(), len(sangria), incompleto


def _seguir(lineas: list[str], i: int, nombre: str, unidad: str | None, descripcion: str,
            incompleto: bool | None = None, usados: set[int] | None = None) -> tuple[str, str | None, str, int]:
    """Une la cola de un nombre repartido en varios renglones ("VALOR_DE_" + "MERCADO_A_LA_")."""
    if incompleto is None:
        incompleto = nombre.endswith("_")
    saltos = 0
    if not incompleto:  # nombre completo seguido de otro trozo ("PLAZO_AL" + "VENCIMIENTO")
        incompleto = _sigue_en(lineas, i + 1)
    while (incompleto or saltos) and saltos < 5:
        cola = _busca_cola(lineas, i + 1, i + 8, usados=usados)
        if not cola:
            break
        i, parte, resto, unidad_cola, parte_abierta = cola
        if usados is not None:
            usados.add(i)
        nombre = re.sub("_{2,}", "_", f"{nombre}_{parte}")
        descripcion = f"{descripcion} {resto}".strip()
        unidad = unidad or unidad_cola
        incompleto = parte_abierta
        saltos += 1
        if not (incompleto or _sigue_en(lineas, i + 1)):
            break
    return nombre.rstrip("_"), unidad, descripcion, i


def _fragmento(linea: str) -> str | None:
    """Primer token de ``linea`` si la línea trae un trozo de nombre y nada más."""
    if _es_campo(linea):
        return None
    m = re.match(r"^(\s{0,14})(\S+)(?:\s+|$)(.*)$", linea.rstrip())
    if not m:
        return None
    frag, resto = m.group(2), m.group(3).strip()
    if not (_TOKEN_NOMBRE.match(frag) and _SOLO_MAYUSCULAS.match(frag)) or len(frag) < 3:
        return None
    return frag


def _sigue_en(lineas: list[str], j: int) -> bool:
    """True si el renglón ``j`` sigue el nombre: "_FECHA_DE_LA_" o "SOCIEDAD FILIAL  la filial...".

    En las fichas el nombre se imprime en una columna angosta, así que sus trozos caen
    en renglones distintos y a veces se cortan por la mitad ("VALORIZACION_DE_PACTO_A_LA_FEC"
    + "HA_DE_" + "CIERRE").  El trozo son una o pocas palabras en mayúsculas seguidas de
    texto en minúsculas (la descripción) o de nada: así se descartan las listas de códigos
    ("RE : Relacionado", "S : Si").
    """
    if j >= len(lineas) or _es_campo(lineas[j]):
        return False
    m = _FRAGMENTO.match(lineas[j].rstrip())
    if not m:
        return False
    resto = m.group(2).strip()
    return not resto or resto[:1].islower()


def _busca_cola(lineas: list[str], desde: int, hasta: int, minimo: int = 2,
                usados: set[int] | None = None) -> tuple[int, str, str, str | None, bool] | None:
    """Busca la cola de un nombre partido (o perdido) en los renglones siguientes.

    Se detiene en el primer renglón con PICTURE: ése ya es otro campo. Descarta
    las listas de códigos ("S : Si") y los nombres de una sola letra.
    """
    for j in range(desde, min(hasta, len(lineas))):
        linea = lineas[j]
        if not linea.strip():
            continue
        if usados is not None and j in usados:  # ya es parte de otro campo
            continue
        if _es_campo(linea):
            return None
        nm = _nombre(linea)
        if not nm or not nm[0] or nm[3] > 14:
            continue
        if len(nm[0]) < minimo or re.match(r"^\s*[:.]", nm[2]):
            continue
        return j, nm[0], nm[2], nm[1], nm[4]
    return None


_SUBCAMPO = re.compile(r"^\s*(?P<nombre>[A-ZÁÉÍÓÚÑ][^:]{2,44}):\s+(?P<desc>\S.*\S)\s*$")
_NO_SUBCAMPO = {"S", "N", "SI", "NO", "EJEMPLOS", "EJEMPLO", "NOTA", "CAMPO"}


def _subcampo(cabeza: str) -> tuple[str, str] | None:
    """Subcampo escrito como etiqueta: "Local: Se indicará si es un local.".

    Aparecen en bienes raíces (CASA, OFICINA, BODEGA…) y en las inversiones en el
    extranjero; el grupo al que pertenecen se agrega después como prefijo.
    """
    m = _SUBCAMPO.match(cabeza)
    if not m:
        return None
    nombre = m.group("nombre").strip()
    desc = m.group("desc").strip()
    if nombre.upper() in _NO_SUBCAMPO or len(nombre.split()) > 5 or len(desc.split()) < 2:
        return None
    return nombre, desc


def _descripcion(lineas: list[str], desde: int, inicial: str, tope: int = 14) -> str:
    """Junta la descripción: los renglones con sangría hasta el campo siguiente."""
    partes = [inicial] if inicial else []
    blancos = 0
    for j in range(desde, min(desde + tope, len(lineas))):
        linea = lineas[j]
        if _es_campo(linea):
            break
        if not linea.strip():
            blancos += 1
            if blancos > 2:
                break
            continue
        blancos = 0
        if len(linea) - len(linea.lstrip()) < 12:  # empieza otra sección o campo
            break
        partes.append(linea.strip())
    return re.sub(r"\s+", " ", " ".join(partes)).strip(" .;")


# ---------------------------------------------------------------------------
# Parseo
# ---------------------------------------------------------------------------
def parsear(ruta: Path, letras: set[str] | None = None) -> dict[tuple[str, str], Registro]:
    """Lee una ficha y devuelve {(letra, tipo_registro): Registro} con posiciones."""
    lineas = _leer(ruta)
    letra: str | None = None
    tipo: str | None = None
    grupo: str | None = None
    registros: dict[tuple[str, str], Registro] = {}
    usados: set[int] = set()  # renglones que ya aportaron al nombre de un campo
    i = 0
    while i < len(lineas):
        linea = lineas[i].rstrip()
        sec = _SECCION.match(linea)
        if sec:
            letra = LETRA.get(sec.group(1))
            grupo = None
        reg = _REGISTRO.search(linea)
        if reg:
            tipo = reg.group(1)
        m = _es_campo(linea) and _PICT_FIN.search(linea)
        if not m:
            # Encabezado de grupo (nombre sin PICTURE): da prefijo a sus subcampos.
            cab = _nombre(linea)
            if cab and cab[0] and cab[3] <= 14 and len(cab[0]) >= 5 and cab[2][:1:].isupper():
                grupo = cab[0]
                if cab[4]:
                    cola = _busca_cola(lineas, i + 1, i + 4, usados=usados)
                    if cola:
                        grupo = f"{grupo}_{cola[1]}"
                        usados.add(cola[0])
            i += 1
            continue

        picture = re.sub(r"\s+", "", m.group(1))
        renglon = i  # se conserva: las búsquedas de nombre pueden adelantar ``i``
        cabeza = linea[: m.start()].rstrip()
        nombre: str | None = None
        unidad: str | None = None
        descripcion = cabeza.strip()
        nombre_grupo: str | None = None

        cab = _nombre(cabeza)
        if cab and cab[0]:
            nombre, unidad, descripcion, _, incompleto = cab
            nombre, unidad, descripcion, i = _seguir(
                lineas, i, nombre, unidad, descripcion, incompleto=incompleto, usados=usados
            )
        if nombre is None:
            sub = _subcampo(cabeza)
            if sub:
                nombre, descripcion = sub
                nombre_grupo = grupo
        if nombre is None:  # el PICTURE se imprimió antes del nombre
            perdido = _busca_cola(lineas, i + 1, i + 4, minimo=3, usados=usados)
            if perdido:
                i, nombre, resto, unidad, _ = perdido
                usados.add(i)
                descripcion = f"{descripcion} {resto}".strip()
                # El nombre puede estar partido alrededor del renglón del PICTURE
                # ("IDENTIFICADOR_GARA" + PICTURE + "NTIA"): se rescata hacia arriba.
                k = renglon
                while k >= 1 and renglon - k < 3 and (k - 1) not in usados:
                    frag = _fragmento(lineas[k - 1])
                    if frag is None:
                        break
                    usados.add(k - 1)
                    nombre = re.sub("_{2,}", "_", frag + nombre)
                    k -= 1
                nombre, unidad, descripcion, i = _seguir(
                    lineas, i, nombre, unidad, descripcion, incompleto=nombre.endswith("_"),
                    usados=usados,
                )
        if nombre is None:
            nombre = "SIN_NOMBRE"

        if letra is None or tipo is None or (letras and letra not in letras):
            i += 1
            continue
        largo, tipo_campo, dec, signo = _picture(picture)
        clave = (letra, tipo)
        registro = registros.setdefault(clave, Registro(letra, tipo))
        if nombre_grupo:
            nombre = f"{nombre_grupo}_{nombre}"
        registro.campos.append(
            Campo(
                nombre=normalizar(nombre),
                nombre_ficha=nombre,
                picture=picture,
                largo=largo,
                inicio=registro.total,
                tipo=tipo_campo,
                decimales=dec,
                con_signo=signo,
                unidad=unidad,
                grupo=nombre_grupo,
                descripcion=_descripcion(lineas, i + 1, descripcion),
                renglon=i + 1,
                ficha=ruta.name,
            )
        )
        i += 1
    return registros


def registros(formato: str, letras: set[str] | None = None) -> dict[tuple[str, str], Registro]:
    """Registros de un formato, leyendo la ficha que corresponde."""
    salida: dict[tuple[str, str], Registro] = {}
    for letra, nombre in FICHA[formato].items():
        if letras and letra not in letras:
            continue
        for clave, registro in parsear(FUENTES / nombre, letras={letra}).items():
            registro.formato = formato
            salida[clave] = registro
    return salida


def principal(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lee las fichas técnicas de la Circular 1835")
    ap.add_argument("--formato", choices=("v2016", "v2024"), default="v2016")
    ap.add_argument("--archivo", help="letra del archivo (i, a, f, b, x, p, c)")
    ap.add_argument("--tipo", help="tipo de registro (1, 2, 3...)")
    ap.add_argument("--listar", action="store_true", help="resumen de largos por registro")
    args = ap.parse_args(argv)
    letras = {args.archivo} if args.archivo else None
    regs = registros(args.formato, letras)
    if args.listar or not (args.archivo and args.tipo):
        for clave in sorted(regs):
            r = regs[clave]
            print(f"{r.letra} tipo {r.tipo}: {len(r.campos)} campos · {r.total} caracteres")
        return 0
    r = regs.get((args.archivo, args.tipo))
    if r is None:
        print(f"No existe el registro {args.archivo} tipo {args.tipo} en la ficha {args.formato}")
        return 1
    print(f"{'ini':>4} {'lar':>3} {'PICTURE':14} {'nombre':44} descripción")
    for c in r.campos:
        print(f"{c.inicio:4d} {c.largo:3d} {c.picture:14} {c.nombre[:44]:44} {c.descripcion[:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
