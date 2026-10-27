# Skills locales del repositorio

Estas instrucciones son locales a este checkout; no se instalaron globalmente en el equipo.

- `frontend-design/`: skill oficial **Frontend Design** de Anthropic, importada desde `anthropics/skills` en el commit registrado en `frontend-design/SOURCE.md`. Se conserva su `LICENSE.txt` (Apache-2.0).
- `sif-web-design-review/`: guía original y específica del SIF para revisar diseño, UX, gráficos/mapas, accesibilidad y evidencias locales. No copia material de terceros.

## Criterio de selección

No se copió la skill **Web Design Guidelines** de Vercel: en la revisión del repositorio upstream no encontramos una licencia explícita y su flujo de actualización consulta `raw.githubusercontent.com`, host que no está disponible en este entorno. La skill local del SIF cubre una revisión propia sin reproducir sus reglas.

No se añadió **UI/UX Pro Max** en esta pasada. Su licencia es MIT, pero cubre principalmente la misma fase de dirección visual que `frontend-design`; mantenemos la instalación pequeña y priorizamos los tokens, patrones y comprobaciones ya existentes en el producto. Se puede incorporar después si hace falta su catálogo de búsqueda de patrones/tokens.
