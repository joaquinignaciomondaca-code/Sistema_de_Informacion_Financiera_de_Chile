# Cruce TXT IFRS CMF (junio 2026) vs maestro retail

Fuente: `ver_archivo.php?inicio=202606&termino=202606` (CMF, actualizado 27/09/2026).
Sonda sin publicación: `retail_financiero/scripts/probe_ifrs_rut_cross.py` (workflow `retail_probe_ifrs.yml`).
Lista completa: `ifrs_202606_ruts.csv` (364 de 368 RUT; 4 líneas se cortaron al leer las anotaciones de Actions, ninguna de retail).

Formato: `periodo;rut;razon_social;consolidacion(C/I);moneda;cuenta;monto;taxonomia;tipo_informe`,
~30.200 filas, montos en unidades de la moneda, todo en TAX CI.

## Maestro retail (17 entidades)

**En el IFRS (6), total activos consolidado CLP:** Falabella 28.591.690 MM · Cencosud 15.467.472 MM ·
Ripley Corp 4.286.512 MM · ABC S.A. 600.498 MM · Hites 385.650 MM · Tricot 362.704 MM.

**No están en el IFRS (11):** las filiales emisoras de tarjetas (CAT, Inversiones y Tarjetas, Solventa,
Adm. de Tarjetas Serv. Financieros, Promotora CMR) y las emisoras de prepago (Los Andes, Los Héroes,
Tenpo, Fintual, Haulmer, Banchile Pagos). Esto es esperable: reportan a la CMF por el régimen de emisores
de tarjetas, no como sociedades con valores inscritos; sus datos deben venir de esa otra fuente.

## Candidatos (no incluidos; requieren decisión)

| RUT | Entidad | Activos | Comentario |
|---|---|---|---|
| 86963200 | FORUS S.A. | 404.675 MM (C) | Retail vestuario/calzado; sin negocio financiero relevante |
| 76139506 | AUTOFIN S.A. | 477.813 MM (I) | Crédito automotriz de consumo |
| 76002293 | SANTANDER CONSUMER FINANCE LTDA. | 1.083.733 MM (I) | Crédito automotriz (filial bancaria) |
| 94050000 | GMAC COMERCIAL AUTOMOTRIZ CHILE | 329.302 MM (C) | Crédito automotriz |
| 96678790 | FORUM SERVICIOS FINANCIEROS | 2.563.348 MM (C) | Crédito automotriz (BBVA/Scotiabank) |
| 96667560 | TANNER SERVICIOS FINANCIEROS | 2.627.781 MM (C) | Factoring, leasing, crédito automotriz |
| 76238714 | GAMA SERVICIOS FINANCIEROS | 248.962 MM (C) | Financiamiento |
| 90146000 | SERVICIOS FINANCIEROS PROGRESO | 140.443 MM (C) | Leasing/factoring |
| 76120857 | GLOBAL SOLUCIONES FINANCIERAS | 213.282 MM (C) | Financiamiento |
| 76012676 | SMU S.A. | 2.554.798 MM (C) | Supermercados (tarjeta Unimarc vía terceros) |
| 76433310 | CENCOSUD SHOPPING | 4.821.427 MM (C) | Filial inmobiliaria de Cencosud (malls), no financiera |
| 96792430 | SODIMAC S.A. | 1.583.114 MM (C) | Filial de Falabella; ya consolidada en Falabella |

**No aparecen en el IFRS:** COFISA (96.522.900-0), La Polar/AD Retail, Corona, Tricard, Multicentro,
Unicard, Family Card, CAR. Para ellas el IFRS no sirve; habría que usar otra fuente (emisores de tarjetas CMF
o memorias).
