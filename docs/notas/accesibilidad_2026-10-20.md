# Revisión de accesibilidad — 2026-10-20 (punto 11)

## Qué se revisó y cómo

- **HTML estático** (`docs/index.html`) con axe-core 4 sobre jsdom, con la regla `color-contrast` desactivada (jsdom no calcula estilos reales).
  - Antes: 1 violación (`region`, moderada): el contenedor principal era un `div`.
  - Después: 0 violaciones. El contenedor es ahora `<main class="main-container">`, con cierre emparejado. Sus hijos son los mismos que en la versión original (solo `div.top-panel`).
- **Idioma**: `<html lang="es">` presente.
- **Campos de búsqueda sin nombre accesible** (solo placeholder): corregidos con `aria-label` en:
  - `#sidebar-search` (`docs/index.html`),
  - `#dict-search-input` (`docs/js/data_dictionary.js`),
  - `#dv-filter-input` (`docs/js/data_viewer.js`),
  - `#normativa-search` (`docs/js/normativa_monitor.js`).
- **Checkbox de recorte por años** (`docs/js/downloads_panel.js`): ya está dentro de un `<label>`; sin cambios.
- **Foco visible**: 10 reglas quitan el contorno nativo (`outline: none`). La regla global `:focus-visible` de `docs/css/app.css` (línea ~4035) usa un contorno de 2 px en color de acento y va después de esas reglas, así que la queda como sustituto. Los campos de texto cambian además el color del borde al enfocarse.
- **Contraste de texto secundario** (`--text-muted`), calculado sobre los valores literales de `docs/css/app.css`:

| Tema | Antes (sobre fondo principal / secundario) | Después |
|---|---|---|
| Por defecto | `#6B7280`: 3,63 | `#7B828E`: 4,78 / 4,52 |
| SwissBorg | `#696E79`: 2,75 | `#8E929A`: 5,37 / 4,53 |
| Bloomberg | `#6E6E73`: 3,42 | `#828287`: 5,03 / 4,55 |
| Nord | `#65738E`: 2,61 | `#939DB0`: 5,34 / 4,58 |
| Midnight | `#64748B`: 3,75 | `#748297`: 4,81 / 4,56 |
| Informe (claro) | `#9CA3AF`: 2,35 | `#6C7079`: 4,57 / 4,95 |

  Todos los temas quedan en 4,5:1 o más sobre ambos fondos (umbral WCAG AA para texto normal).

## Límites de esta revisión

- No hay navegador real en el sandbox: el contenido generado por JS (barra lateral, diccionario, modales, pestañas) no fue recorrido con axe. Se revisó el código, no el árbol de accesibilidad renderizado.
- El contraste se calculó sobre colores literales, no sobre píxeles renderizados; no incluye opacidades ni fondos con degradado.
- No se revisaron roles de los modales (`role="dialog"`, atrapado de foco) ni de las pestañas (`aria-controls`) en tiempo de ejecución.
- Pendiente: prueba con lector de pantalla y navegación solo con teclado en el sitio publicado.
