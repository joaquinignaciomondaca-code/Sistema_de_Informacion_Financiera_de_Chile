#!/usr/bin/env python3
"""Comprueba que el sitio siga siendo usable en un teléfono.

El entorno de integración no tiene navegador, así que esta compuerta no mide
pixeles: comprueba las decisiones de diseño que hacen usable la interfaz en una
pantalla de 360–430 px y que se pueden afirmar leyendo el CSS, el marcado y los
eventos. Es la lista de la ruta (`docs/notas/ruta_movil_2026-10-22.md`)
convertida en reglas para que no se pierdan en el siguiente rediseño.

Qué comprueba:

   1. La etiqueta `viewport` declara `viewport-fit=cover` y el teclado no tapa
      el campo activo (`interactive-widget`).
   2. El alto se mide con `100dvh`, no con `100vh` a secas, y el layout no
      descuenta un alto de cabecera fijo.
   3. Por debajo de 900 px el explorador es un cajón superpuesto, no una columna.
   4. Existen fondo, cierre por toque, cierre por Escape y cierre al elegir.
   5. Las pestañas alcanzan 44 px y se deslizan.
   6. Los campos de texto usan 16 px: por debajo, iOS amplía la página al enfocar.
   7. La tabla de la Guía se convierte en tarjetas con etiqueta por celda.
   8. El modal de guardadas y los avisos caben en el ancho y respetan el área
      segura del teléfono.
   9. Con puntero grueso hay objetivos táctiles mínimos.
  10. El mapa relacional escucha Pointer Events y acepta pellizco.
  11. La cabecera publica su altura real en `--sif-header-h`.
  12. Elegir una tabla cierra el cajón.
  13. El aviso de «esto se ve mejor en un computador» existe, se cierra y sólo
      aparece en pantalla pequeña.

Uso:
    python3 scripts/audit_movil.py                 # informe y código de salida
    python3 scripts/audit_movil.py --verbose       # con el resumen por regla
    python3 scripts/audit_movil.py --autoprueba    # comprueba que las reglas fallan
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CSS = RAIZ / "docs" / "css" / "app.css"
HTML = RAIZ / "docs" / "index.html"
ERD = RAIZ / "docs" / "js" / "erd_graph.js"
SIDEBAR = RAIZ / "docs" / "js" / "sidebar.js"
SHELL = RAIZ / "docs" / "js" / "ux_shell.js"

TOTAL = 13


# ---------------------------------------------------------------------------
# Lector de CSS: devuelve (condición, selector, propiedad, valor)
# ---------------------------------------------------------------------------
def _sin_comentarios(texto: str) -> str:
    return re.sub(r"/\*.*?\*/", "", texto, flags=re.S)


def reglas(css: str):
    """Recorre el CSS y emite cada declaración con su condición de media.

    No es un parser completo: alcanza para hojas propias sin at-rules anidados
    más allá de `@media`, que es lo que usa este archivo. Cualquier regla con
    otra forma se ignora en silencio, nunca se inventa.
    """
    css = _sin_comentarios(css)
    i, n = 0, len(css)
    pila: list[tuple[str, str]] = []
    prelude = ""
    while i < n:
        c = css[i]
        if c == "{":
            prelude = prelude.strip()
            if prelude.startswith("@media"):
                pila.append(("media", prelude[len("@media"):].strip()))
                prelude = ""
            elif prelude.startswith("@"):
                pila.append(("at", prelude))
                prelude = ""
            else:
                j = css.find("}", i)
                if j == -1:
                    break
                cuerpo = css[i + 1:j]
                condicion = " ".join(cond for tipo, cond in pila if tipo == "media")
                # Un prelude puede agrupar varios selectores: se emiten por
                # separado para no depender de cómo estén escritos.
                for selector in (s.strip() for s in prelude.split(",")):
                    if not selector:
                        continue
                    for decl in cuerpo.split(";"):
                        if ":" not in decl:
                            continue
                        prop, _, valor = decl.partition(":")
                        yield condicion, selector, prop.strip().lower(), valor.strip()
                i = j + 1
                prelude = ""
                continue
            i += 1
        elif c == "}":
            if pila:
                pila.pop()
            i += 1
            prelude = ""
        else:
            prelude += c
            i += 1


def ancho_max(condicion: str) -> int | None:
    m = re.search(r"max-width:\s*(\d+)px", condicion)
    return int(m.group(1)) if m else None


def cumple(condicion: str, *maximos: int) -> bool:
    """True si la condición aplica en un ancho dado (o en cualquiera)."""
    if not condicion:
        return True
    ancho = ancho_max(condicion)
    return ancho is not None and ancho <= max(maximos)


def valor_final(lista, selector: str, prop: str, condicion_max: int | None = None) -> str | None:
    """El valor que gana: la última declaración en el orden del archivo."""
    elegido = None
    for cond, sel, p, v in lista:
        if sel != selector or p != prop:
            continue
        if condicion_max is not None and not cumple(cond, condicion_max):
            continue
        elegido = v
    return elegido


def px(valor: str | None) -> float | None:
    if not valor:
        return None
    m = re.match(r"(-?\d+(?:\.\d+)?)px$", valor.strip())
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Reglas
# ---------------------------------------------------------------------------
def comprobar(css_texto: str, html_texto: str, erd_texto: str,
              sidebar_texto: str, shell_texto: str) -> tuple[list[str], list[str]]:
    fallos: list[str] = []
    avisos: list[str] = []
    lista = list(reglas(css_texto))

    # 1 · viewport
    viewport = re.search(r'<meta\s+name="viewport"\s+content="([^"]+)"', html_texto)
    contenido = viewport.group(1) if viewport else ""
    faltan = [x for x in ("width=device-width", "initial-scale=1", "viewport-fit=cover",
                          "interactive-widget=resizes-content") if x not in contenido]
    if faltan:
        fallos.append(f"1 viewport: falta {', '.join(faltan)}")

    # 2 · alto real: gana la última declaración, como en el navegador
    alto_body = valor_final(lista, "body", "height")
    if alto_body != "100dvh":
        fallos.append(f"2 alto: body termina en height: {alto_body}; se espera 100dvh")
    alto_layout = valor_final(lista, ".app-layout", "height")
    if alto_layout and "calc(100vh" in alto_layout:
        fallos.append("2 alto: el layout sigue descontando un alto fijo con calc(100vh - …)")

    # 3 · cajón del explorador
    cajon = [v for cond, sel, p, v in lista
             if sel == ".sidebar" and p == "position" and cumple(cond, 900)]
    if "fixed" not in cajon:
        fallos.append("3 explorador: por debajo de 900 px la barra lateral no es un cajón (position: fixed)")

    # 4 · fondo y cierres
    if 'id="sidebar-backdrop"' not in html_texto:
        fallos.append("4 cajón: falta el fondo que cierra el explorador al tocarlo")
    if "sidebar-backdrop" not in sidebar_texto or "cerrarCajon" not in sidebar_texto:
        fallos.append("4 cajón: el JS no cierra el explorador al tocarlo")
    if not re.search(r'key === "Escape"', sidebar_texto):
        fallos.append("4 cajón: Escape no cierra el explorador")

    # 5 · pestañas
    alturas = [px(v) for cond, sel, p, v in lista
               if sel == ".panel-tab-btn" and p == "min-height" and cumple(cond, 900)]
    if not alturas or max(a for a in alturas if a) < 44:
        fallos.append("5 pestañas: no hay min-height de 44 px; quedan por debajo del objetivo táctil")
    if not any(sel == ".panel-tabs" and p == "overflow-x" and cumple(cond, 900)
               for cond, sel, p, v in lista):
        fallos.append("5 pestañas: no se deslizan en horizontal")

    # 6 · campos a 16 px
    campos = {sel for cond, sel, p, v in lista
              if p == "font-size" and v == "16px" and cumple(cond, 900)}
    if not campos:
        fallos.append("6 campos: ningún selector usa 16 px; iOS amplía la página al enfocar")
    else:
        for requerido in ("#chat-input", ".sidebar-search-box input", ".dict-search-input"):
            if requerido not in campos:
                fallos.append(f"6 campos: {requerido} no está a 16 px en pantalla pequeña")

    # 7 · tabla de la Guía
    thead = [v for cond, sel, p, v in lista
             if sel == ".uso-tabla thead" and p == "display" and cumple(cond, 560)]
    if "none" not in thead:
        fallos.append("7 tabla: la tabla de la Guía no se convierte en tarjetas")
    if html_texto.count("data-label=") < 2:
        fallos.append("7 tabla: las celdas no llevan la etiqueta de su columna")

    # 8 · modal, avisos y área segura
    if not re.search(r"width:\s*min\(360px,\s*calc\(100vw", css_texto):
        fallos.append("8 modal: el de consultas guardadas no se adapta al ancho del teléfono")
    if "env(safe-area-inset-bottom" not in css_texto:
        fallos.append("8 área segura: ningún elemento respeta el borde inferior del iPhone")

    # 9 · puntero grueso
    grueso = [r for r in lista if "pointer: coarse" in r[0]]
    if not grueso:
        fallos.append("9 táctil: no hay reglas para puntero grueso")
    else:
        altos = [px(v) for cond, sel, p, v in grueso if p == "min-height"]
        if not altos or max(a for a in altos if a) < 44:
            fallos.append("9 táctil: ningún objetivo llega a 44 px con el dedo")
        if not any(v == "none" for cond, sel, p, v in grueso if p == "transform"):
            avisos.append("9 táctil: no se anula ningún efecto :hover al tocar")

    # 10 · mapa táctil
    if 'addEventListener("pointerdown"' not in erd_texto:
        fallos.append("10 mapa: el lienzo no escucha pointerdown; el dedo no puede arrastrarlo")
    if 'addEventListener("mousedown"' in erd_texto:
        fallos.append("10 mapa: quedan manejadores de ratón en el lienzo")
    if "pellizco" not in erd_texto:
        fallos.append("10 mapa: no hay pellizco de dos dedos")
    if "none" not in (valor_final(lista, "#erd-canvas", "touch-action") or ""):
        fallos.append("10 mapa: falta touch-action: none, el navegador interpreta el arrastre como scroll")

    # 11 · cabecera medible (de ahí cuelga el cajón)
    if "--sif-header-h" not in shell_texto:
        fallos.append("11 cabecera: el JS no publica su altura real en --sif-header-h")
    if not any("--sif-header-h" in v for _, _, _, v in lista):
        fallos.append("11 cabecera: el CSS no usa --sif-header-h")

    # 12 · cierre del cajón al elegir tabla
    if "if (this.esMovil()) this.cerrarCajon();" not in sidebar_texto:
        fallos.append("12 cajón: elegir una tabla no lo cierra")

    # 13 · aviso de teléfono
    if 'id="aviso-movil"' not in html_texto:
        fallos.append("13 aviso: falta el aviso que recomienda usar un computador")
    elif 'id="aviso-movil-cerrar"' not in html_texto:
        fallos.append("13 aviso: no se puede cerrar")
    if "aviso-movil" not in shell_texto or "initAvisoMovil" not in shell_texto:
        fallos.append("13 aviso: el JS no lo muestra ni recuerda el descarte")
    if "sif-aviso-movil-cerrado" not in shell_texto:
        fallos.append("13 aviso: el descarte no se guarda en el navegador")
    # El valor base es el de fuera de todo media query, no el último del archivo.
    oculto_base = None
    for cond, sel, prop, v in lista:
        if sel == ".aviso-movil" and prop == "display" and not cond:
            oculto_base = v
    if oculto_base != "none":
        fallos.append("13 aviso: se muestra también en escritorio; el estilo base debe ocultarlo")
    visible = [v for cond, sel, p, v in lista
               if sel == ".aviso-movil" and p == "display" and cumple(cond, 900)]
    if "flex" not in visible:
        fallos.append("13 aviso: no aparece en pantalla pequeña")

    return fallos, avisos


# ---------------------------------------------------------------------------
# Autoprueba: cada regla tiene que romperse cuando se rompe el diseño
# ---------------------------------------------------------------------------
def autoprueba(textos: dict[str, str]) -> int:
    caso = textos["css"]
    mutaciones = [
        ("1 viewport", {"html": textos["html"].replace(", viewport-fit=cover", "")}),
        ("2 alto", {"css": caso.replace("height: 100dvh;", "height: 101vh;")}),
        ("3 explorador", {"css": caso.replace("    position: fixed;\n    top: var(--sif-header-h", "    position: relative;\n    top: var(--sif-header-h")}),
        ("4 cajón", {"sidebar": textos["sidebar"].replace('key === "Escape"', 'key === "Esc"')}),
        ("5 pestañas", {"css": caso.replace("""  .panel-tab-btn {
    min-height: 44px;""", """  .panel-tab-btn {
    min-height: 22px;""")}),
        ("6 campos", {"css": caso.replace("  #chat-input {\n    font-size: 16px;\n  }", "  #chat-input {\n    font-size: 12px;\n  }")}),
        ("7 tabla", {"html": re.sub(r' data-label="[^"]*"', "", textos["html"])}),
        ("9 táctil", {"css": caso.replace("@media (pointer: coarse)", "@media (pointer: none)")}),
        ("10 mapa", {"erd": textos["erd"].replace('addEventListener("pointerdown"', 'addEventListener("mousedown"')}),
        ("13 aviso", {"html": textos["html"].replace('id="aviso-movil-cerrar"', 'id="aviso-movil-ok"')}),
    ]
    fallos_prueba = []
    for esperada, cambio in mutaciones:
        textos_mutados = dict(textos, **cambio)
        fallos, avisos = comprobar(textos_mutados["css"], textos_mutados["html"],
                                   textos_mutados["erd"], textos_mutados["sidebar"],
                                   textos_mutados["shell"])
        if not any(f.startswith(esperada.split()[0] + " ") for f in fallos):
            fallos_prueba.append(f"la regla «{esperada}» no se rompe al romper el diseño")

    print(f"Autoprueba: {len(mutaciones)} mutaciones")
    for f in fallos_prueba:
        print(f"[FALLA] {f}")
    if fallos_prueba:
        print(f"\nAUTOPRUEBA: {len(fallos_prueba)} regla(s) no detectan su avería")
        return 1
    print("AUTOPRUEBA: todas las reglas detectan su avería")
    return 0


def main() -> int:
    textos = {
        "css": CSS.read_text(encoding="utf-8"),
        "html": HTML.read_text(encoding="utf-8"),
        "erd": ERD.read_text(encoding="utf-8"),
        "sidebar": SIDEBAR.read_text(encoding="utf-8"),
        "shell": SHELL.read_text(encoding="utf-8"),
    }
    if "--autoprueba" in sys.argv:
        return autoprueba(textos)

    fallos, avisos = comprobar(textos["css"], textos["html"], textos["erd"],
                               textos["sidebar"], textos["shell"])

    print("Móvil: comprobaciones de interfaz en pantalla pequeña")
    for linea in fallos:
        print(f"[FALLA] {linea}")
    for linea in avisos:
        print(f"[AVISO] {linea}")
    if not fallos and not avisos:
        print(f"  {TOTAL} reglas en verde")
    con_fallo = len({f.split(":")[0].split()[0] for f in fallos})
    if fallos:
        print(f"\nRESULTADO: {len(fallos)} fallo(s) en {con_fallo} regla(s) de móvil")
        return 1
    print(f"\nRESULTADO: interfaz utilizable en pantalla pequeña ({TOTAL}/{TOTAL} reglas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
