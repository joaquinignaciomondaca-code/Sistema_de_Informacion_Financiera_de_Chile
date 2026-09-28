# Retail financiero — retirado del sitio (2026-09-28)

La sección se quitó de la web y de `docs/outputs/`: mezclaba balances de grupos
(Falabella S.A., Cencosud S.A., Ripley Corp) que son mayormente no financieros y
duplicaban el crédito que ya aparece en bancos (Banco Falabella con CMR, Banco Ripley
con CAR, Scotiabank con CAT).

Se conserva aquí el código y el análisis por si se retoma como
"crédito no bancario / emisores de tarjetas" con una regla única: cada negocio
financiero aparece una vez, con los estados de la sociedad que otorga el crédito.

- `scripts/`: pipeline anterior y sonda IFRS (no publican en la web).
- `analisis/CRUCE_IFRS_202606.md`: cruce TXT IFRS CMF vs maestro anterior.
- Los datos publicados antes siguen disponibles en el historial de git.
