"""Protección de identificadores en la capa pública de datos.

El sistema publica información que la CMF ya divulga, pero no todo lo que es
público en un portal regulatorio conviene republicarlo como base descargable:
un portal se consulta registro a registro, mientras que un Parquet permite
cruzar, filtrar y explotar millones de filas de una sola vez. Dos identificadores
concentraban ese riesgo y este módulo los trata:

1. `fi.cartera_nacional.rut_emisor`
   El emisor de un instrumento puede ser una empresa o una **persona natural**
   (mutuos hipotecarios, pagarés y otros instrumentos de deuda donde el deudor
   es alguien con nombre y apellido). Se suprime el RUT cuando probablemente
   corresponde a una persona natural y se agrega `emisor_tipo` para que quede
   registrado el criterio aplicado.

   Criterio (reproducible y documentado, no una lista negra artesanal):
     * el cuerpo numérico del RUT es **menor a 50.000.000** — rango que el SII
       asigna mayoritariamente a personas naturales — **y**
     * el RUT **no** aparece en los registros de entidades que el propio sistema
       publica (fondos de inversión, fondos mutuos, aseguradoras y listas de
       entidades). Esos registros son los que explican los RUT "cortos" que
       parecen de persona pero son de fondos.

   Se prefirió el falso positivo (suprimir el RUT de una empresa chica) al falso
   negativo (publicar el RUT de una persona). La regla se aplica a toda la tabla,
   sin excepciones por fondo o por periodo.

2. `fintech.rpsf_maestro.email_contacto`
   El Registro de Prestadores de Servicios Financieros identifica al prestador
   por RUT y razón social; el correo no es un dato registral y sí permite
   contactar a la persona. 46 de los 264 correos publicados eran de dominios
   personales (gmail, hotmail, outlook, yahoo) y 36 filas corresponden a
   personas naturales. Se retira la columna completa en vez de enmascararla:
   enmascarar deja la ilusión de que el dato se publica y no reduce el riesgo.

3. `seguros.bienes_raices`: dirección exacta y rol
   La dirección y el rol tributario de un inmueble permiten ubicar una propiedad
   y, con ella, a sus ocupantes. No se publican. Se conservan `comuna` y `ciudad`
   (el nivel geográfico con valor analítico) y se agrega `property_id`, un
   seudónimo estable que permite seguir el mismo bien raíz entre meses sin
   revelar su dirección. Ojo con el nombre de la columna: la CMF la llama
   `ubicacion` en el formato vigente desde 2024-12 y `direccion` en los archivos
   anteriores, así que se retiran las dos.

Qué **no** es esto: no es anonimización con garantía formal (k-anonimato,
privacidad diferencial). Es reducción deliberada del riesgo de reidentificación
en la versión pública y académica, manteniendo la utilidad analítica y la
referencia a la fuente CMF, que se conserva en todos los casos.

Uso típico:
    from pipelines.auto import privacidad
    entidades = privacidad.cargar_entidades_conocidas()
    df["rut_emisor"], df["emisor_tipo"] = privacidad.enmascarar_columna(df["rut_emisor"], entidades)
    df = privacidad.proteger_bienes_raices(df)
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

# RUT bajo este valor: rango asignado mayoritariamente a personas naturales.
UMBRAL_PERSONA_NATURAL = 50_000_000

# Registros publicados que permiten reconocer entidades jurídicas con RUT corto.
# (archivo relativo a docs/outputs, columnas donde buscar el RUT)
REGISTROS_ENTIDADES = (
    ("fi/maestro_fondos_inversion.parquet", ("run_fondo", "rut_fondo_dv")),
    ("ffmm/ffmm_registro_fondos_universo.parquet", ("run_fondo", "rut_fondo_completo")),
    ("ffmm/maestro_fondos_mutuos.parquet", ("run_fondo",)),
    ("seguros/aseguradoras.parquet", ("rut_aseguradora", "rut")),
)

TIPO_JURIDICA = "persona_juridica"
TIPO_NATURAL = "persona_natural_probable"
TIPO_SIN_RUT = "sin_rut_informado"

# Bienes raíces: la dirección se llama «ubicacion» en el formato CMF vigente
# desde 2024-12 y «direccion» en los archivos anteriores. El rol, igual en ambos.
COLUMNAS_DIRECCION = ("ubicacion", "direccion", "domicilio")
COLUMNAS_RETIRADAS = ("rol",) + COLUMNAS_DIRECCION

# Columnas de contacto personal que no se publican en ninguna tabla. El correo
# institucional de una entidad no es un dato registral y, cuando el titular es
# una persona natural, es dato personal sin finalidad analítica.
COLUMNAS_CONTACTO = (
    "email_contacto",
    "correo_contacto",
    "email",
    "telefono_contacto",
    "celular",
)


# ---------------------------------------------------------------------------
# RUT
# ---------------------------------------------------------------------------
def cuerpo_rut(valor) -> str | None:
    """Cuerpo numérico del RUT sin puntos ni dígito verificador ("97004000")."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    texto = texto.split("-")[0].replace(".", "").strip()
    if not texto.isdigit():
        return None
    return texto.lstrip("0") or "0"


def cargar_entidades_conocidas(raiz: str | os.PathLike | None = None) -> set[str]:
    """RUT (cuerpo) de todas las entidades jurídicas que el sistema ya publica.

    Sin `pyarrow` devuelve un conjunto vacío: la regla se vuelve conservadora y
    enmascara todo RUT bajo el umbral, que es el sentido en que debe fallar.
    """
    entidades: set[str] = set()
    try:
        import pyarrow.parquet as pq
    except Exception:
        return entidades

    base = Path(raiz) if raiz else Path(__file__).resolve().parents[2] / "docs" / "outputs"
    if not base.exists():
        return entidades

    def tomar(ruta: Path, columnas) -> None:
        try:
            tabla = pq.read_table(ruta)
        except Exception:
            return
        nombres = tabla.column_names
        objetivo = [c for c in columnas if c in nombres] if columnas else [c for c in nombres if c.startswith(("rut", "run"))]
        for col in objetivo:
            for valor in tabla.column(col).to_pylist():
                cuerpo = cuerpo_rut(valor)
                if cuerpo:
                    entidades.add(cuerpo)

    for relativo, columnas in REGISTROS_ENTIDADES:
        ruta = base / relativo
        if ruta.exists():
            tomar(ruta, columnas)

    # Listas de entidades (bancos, AFP, cooperativas, corredoras, etc.).
    for directorio in (base / "entidades", base):
        if not directorio.is_dir():
            continue
        for ruta in sorted(directorio.glob("*.parquet")):
            tomar(ruta, None)
    for ruta in sorted(base.glob("*/*lista_entidades*.parquet")):
        tomar(ruta, None)
    return entidades


def es_probable_persona_natural(valor, entidades=frozenset()) -> bool:
    """True si el RUT probablemente es de una persona natural (ver docstring)."""
    cuerpo = cuerpo_rut(valor)
    if cuerpo is None:
        return False
    try:
        numero = int(cuerpo)
    except ValueError:
        return False
    if numero >= UMBRAL_PERSONA_NATURAL:
        return False
    return cuerpo not in entidades


def tipo_emisor(valor, entidades=frozenset()) -> str:
    """Etiqueta del criterio aplicado, para que quede auditado en la tabla."""
    cuerpo = cuerpo_rut(valor)
    if cuerpo is None:
        return TIPO_SIN_RUT
    return TIPO_NATURAL if es_probable_persona_natural(cuerpo, entidades) else TIPO_JURIDICA


def enmascarar_rut_emisor(valor, entidades=frozenset()):
    """Devuelve (rut_publicable, emisor_tipo): None si probablemente es persona.

    Un valor ausente (None, cadena vacía o NaN de pandas) se publica como nulo:
    nunca como el texto «nan», que ensuciaría la columna y los cruces por RUT.
    """
    tipo = tipo_emisor(valor, entidades)
    if tipo == TIPO_NATURAL:
        return None, tipo
    if valor is None or cuerpo_rut(valor) is None:
        return None, TIPO_SIN_RUT
    return str(valor).strip(), tipo


def enmascarar_columna(valores, entidades=frozenset()):
    """Aplica la regla a una columna (lista, Series o iterable) de RUT.

    Devuelve (valores_enmascarados, tipos) en el mismo orden.
    """
    enmascarados, tipos = [], []
    for valor in valores:
        nuevo, tipo = enmascarar_rut_emisor(valor, entidades)
        enmascarados.append(nuevo)
        tipos.append(tipo)
    return enmascarados, tipos


# ---------------------------------------------------------------------------
# Bienes raíces (seguros)
# ---------------------------------------------------------------------------
def normalizar_rol(valor) -> str:
    """Rol sin espacios ni ceros a la izquierda del bloque, para el seudónimo."""
    if valor is None:
        return ""
    return " ".join(str(valor).split()).strip().upper()


def property_id(rut_aseguradora, rol, sal: str = "") -> str | None:
    """Seudónimo estable de un bien raíz, derivado de su rol.

    Permite seguir el mismo inmueble entre meses sin publicar ni la dirección
    ni el rol. No es un secreto: con una `sal` vacía (por omisión) el cálculo es
    determinista y cualquiera puede reproducirlo, porque el espacio de roles es
    acotado y un atacante decidido podría probar combinaciones. Para la versión
    académica se recomienda fijar `SIF_PRIV_SALT` con un valor que no se
    publique: el id deja de ser reproducible, pero deja de ser un punto débil.
    """
    rol_normal = normalizar_rol(rol)
    if not rol_normal:
        return None
    cuerpo = cuerpo_rut(rut_aseguradora) or str(rut_aseguradora or "").strip()
    if not cuerpo:
        return None
    base = f"{sal}|{cuerpo}|{rol_normal}".encode("utf-8")
    return "BIEN-" + hashlib.sha256(base).hexdigest()[:12]


def sal_privada() -> str:
    """Sal opcional para los seudónimos (variable de entorno SIF_PRIV_SALT)."""
    return os.environ.get("SIF_PRIV_SALT", "")


# ---------------------------------------------------------------------------
# Contacto: minimización
# ---------------------------------------------------------------------------
def retirar_contacto(df, columnas=COLUMNAS_CONTACTO):
    """Quita del DataFrame las columnas de contacto personal.

    Se aplica antes de publicar. Devuelve el mismo DataFrame sin cambios si no
    hay ninguna de esas columnas, para que la regla sea idempotente y no obligue
    a tocar los publicadores que no manejan contacto.
    """
    presentes = [c for c in columnas if c in getattr(df, "columns", [])]
    if not presentes:
        return df
    return df.drop(columns=presentes)


# ---------------------------------------------------------------------------
# Helpers sobre DataFrames (pandas es opcional: se importa al usarlos)
# ---------------------------------------------------------------------------
def proteger_cartera_nacional(df, entidades=frozenset(), columna: str = "rut_emisor"):
    """Suprime el RUT del emisor y agrega `emisor_tipo` a un DataFrame."""
    if columna not in getattr(df, "columns", []):
        return df
    enmascarados, tipos = enmascarar_columna(df[columna].tolist(), entidades)
    df = df.copy()
    df[columna] = enmascarados
    df["emisor_tipo"] = tipos
    return df


def proteger_bienes_raices(df, sal: str | None = None):
    """Quita dirección y rol; deja comuna, ciudad y un `property_id` estable."""
    columnas = set(getattr(df, "columns", []))
    if not columnas:
        return df
    sal = sal_privada() if sal is None else sal
    df = df.copy()
    roles = df["rol"].tolist() if "rol" in columnas else [None] * len(df)
    aseguradoras = df["rut_aseguradora"].tolist() if "rut_aseguradora" in columnas else [None] * len(df)
    df["property_id"] = [property_id(rut, rol, sal) for rut, rol in zip(aseguradoras, roles)]
    for columna in COLUMNAS_RETIRADAS:
        if columna in columnas:
            df[columna] = [None] * len(df)
    return df


def proteger_prestamos(df, entidades=frozenset()):
    """Conserva las columnas B.12, pero suprime identidad de deudores personas naturales."""
    columnas = set(getattr(df, "columns", []))
    if not columnas or "rut_deudor" not in columnas:
        return df
    df = df.copy()
    ruts = df["rut_deudor"].tolist()
    tipos = df["tipo_deudor"].tolist() if "tipo_deudor" in columnas else [None] * len(df)
    naturales = [str(t or "").strip().upper() == "N" or cuerpo_rut(rut) is None or
                 es_probable_persona_natural(rut, entidades) for rut, t in zip(ruts, tipos)]
    for nombre in ("rut_deudor", "ver_deudor", "razon_social_deudor", "nombre_deudor",
                   "primer_apellido_deudor", "segundo_apellido_deudor"):
        if nombre in columnas:
            df[nombre] = [None if n else v for n, v in zip(naturales, df[nombre].tolist())]
    return df


def proteger_bienes_raices_arriendo(df, sal: str | None = None, entidades=frozenset()):
    """Suprime rol y datos de arrendatarios personas, y agrega un id longitudinal del inmueble."""
    columnas = set(getattr(df, "columns", []))
    if not columnas:
        return df
    sal = sal_privada() if sal is None else sal
    df = df.copy()
    roles = df["rol"].tolist() if "rol" in columnas else [None] * len(df)
    aseguradoras = df["rut_aseguradora"].tolist() if "rut_aseguradora" in columnas else [None] * len(df)
    df["property_id"] = [property_id(rut, rol, sal) for rut, rol in zip(aseguradoras, roles)]
    if "rol" in columnas:
        df["rol"] = [None] * len(df)
    if "rut_arrendatario_deudor" in columnas:
        ruts = df["rut_arrendatario_deudor"].tolist()
        personas = [cuerpo_rut(rut) is None or es_probable_persona_natural(rut, entidades) for rut in ruts]
        df["rut_arrendatario_deudor"] = [None if p else rut for p, rut in zip(personas, ruts)]
        if "nombre_arrendatario_deudor" in columnas:
            nombres = df["nombre_arrendatario_deudor"].tolist()
            df["nombre_arrendatario_deudor"] = [None if p else n for p, n in zip(personas, nombres)]
    return df


def proteger_contrapartes(df, entidades=frozenset()):
    """Protege contrapartes naturales de B.14 sin afectar contrapartes jurídicas."""
    columnas = set(getattr(df, "columns", []))
    if not columnas or "rut_contraparte_nacional" not in columnas:
        return df
    df = df.copy()
    ruts = df["rut_contraparte_nacional"].tolist()
    naturales = [cuerpo_rut(rut) is not None and es_probable_persona_natural(rut, entidades)
                 for rut in ruts]
    df["contraparte_tipo"] = [TIPO_NATURAL if n else (TIPO_JURIDICA if cuerpo_rut(rut) else TIPO_SIN_RUT)
                               for n, rut in zip(naturales, ruts)]
    df["rut_contraparte_nacional"] = [None if n else rut for n, rut in zip(naturales, ruts)]
    if "nombre_contraparte_garantia" in columnas:
        df["nombre_contraparte_garantia"] = [None if n else nombre
                                              for n, nombre in zip(naturales, df["nombre_contraparte_garantia"].tolist())]
    return df
