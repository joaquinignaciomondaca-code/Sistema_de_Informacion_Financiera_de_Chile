// GENERADO por scripts/build_estado_claves.py — no editar a mano.
// Fuente: docs/api/claves.csv, medido sobre todas las filas publicadas.
// data_release: 2026-10-26.b332bba5e1ca
window.ESTADO_CLAVES = {
 "generado": "2026-10-26",
 "data_release": "2026-10-26.b332bba5e1ca",
 "como_se_genera": "python3 scripts/build_estado_claves.py",
 "resumen": {
  "objetos": 90,
  "verificadas": 48,
  "propuestas": 15,
  "sin_clave": 22,
  "sin_datos": 5,
  "sin_verificar": 0,
  "con_repetidas": 22,
  "filas_repetidas": 230288
 },
 "objetos": {
  "afp_lista_entidades": {
   "estado": "ok",
   "filas": 7,
   "distintas": 7,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "rut_administradora"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: rut_administradora — única sobre 7 filas."
  },
  "agf_balance": {
   "estado": "propuesta",
   "filas": 71423,
   "distintas": 71423,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "valor",
    "razon_social",
    "cuenta",
    "rut",
    "rut_dv",
    "periodo"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 6 columnas, única sobre 71.423 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "agf_lista_entidades": {
   "estado": "ok",
   "filas": 72,
   "distintas": 72,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "rut"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: rut — única sobre 72 filas."
  },
  "agf_resultados": {
   "estado": "propuesta",
   "filas": 58216,
   "distintas": 58216,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "valor",
    "valor_no_numerico",
    "cuenta",
    "razon_social",
    "rut",
    "rut_dv",
    "periodo",
    "orden"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 8 columnas, única sobre 58.216 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "bancos_balance": {
   "estado": "ok",
   "filas": 722931,
   "distintas": 722931,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "periodo",
    "codigo_institucion",
    "codigo_cuenta",
    "modelo_cmf"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: periodo + codigo_institucion + codigo_cuenta + modelo_cmf — única sobre 722.931 filas."
  },
  "bancos_lista_entidades": {
   "estado": "ok",
   "filas": 41,
   "distintas": 41,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "codigo_institucion"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: codigo_institucion — única sobre 41 filas."
  },
  "bancos_resultados": {
   "estado": "ok",
   "filas": 1240061,
   "distintas": 1240061,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "periodo",
    "codigo_institucion",
    "codigo_cuenta",
    "modelo_cmf"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: periodo + codigo_institucion + codigo_cuenta + modelo_cmf — única sobre 1.240.061 filas."
  },
  "ccaf_balance": {
   "estado": "propuesta",
   "filas": 8043,
   "distintas": 8043,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "valor",
    "cuenta",
    "periodo",
    "orden",
    "rut"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 5 columnas, única sobre 8.043 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "ccaf_lista_entidades": {
   "estado": "ok",
   "filas": 6,
   "distintas": 6,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "rut"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: rut — única sobre 6 filas."
  },
  "ccaf_resultados": {
   "estado": "propuesta",
   "filas": 5506,
   "distintas": 5506,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "valor",
    "periodo",
    "cuenta",
    "orden",
    "rut"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 5 columnas, única sobre 5.506 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "cooperativas_lista_entidades": {
   "estado": "ok",
   "filas": 7,
   "distintas": 7,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "rut"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: rut — única sobre 7 filas."
  },
  "corredoras_bolsa_balance": {
   "estado": "ok",
   "filas": 107976,
   "distintas": 107976,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "periodo",
    "rut",
    "codigo_fecu"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: periodo + rut + codigo_fecu — única sobre 107.976 filas."
  },
  "corredoras_bolsa_lista_entidades": {
   "estado": "ok",
   "filas": 120,
   "distintas": 120,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "rut"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: rut — única sobre 120 filas."
  },
  "corredoras_bolsa_lista_entidades_registro": {
   "estado": "ok",
   "filas": 120,
   "distintas": 120,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "rut"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: rut — única sobre 120 filas."
  },
  "corredoras_bolsa_resultados": {
   "estado": "ok",
   "filas": 77705,
   "distintas": 77705,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "periodo",
    "rut",
    "codigo_fecu"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: periodo + rut + codigo_fecu — única sobre 77.705 filas."
  },
  "factoring_leasing_balance": {
   "estado": "propuesta",
   "filas": 30046,
   "distintas": 30046,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "valor_archivo",
    "valor_texto_original",
    "cuenta",
    "periodo",
    "fuente_archivo",
    "orden",
    "nombre_reportado"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 7 columnas, única sobre 30.046 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "factoring_leasing_lista_entidades": {
   "estado": "ok",
   "filas": 32,
   "distintas": 32,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "rut"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: rut — única sobre 32 filas."
  },
  "factoring_leasing_resultados": {
   "estado": "propuesta",
   "filas": 22368,
   "distintas": 22368,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "valor_texto_original",
    "valor_archivo",
    "cuenta",
    "periodo",
    "fuente_archivo",
    "nombre_reportado",
    "rut",
    "nombre_catalogo",
    "rut_dv",
    "orden"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 10 columnas, única sobre 22.368 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "ffmm_balance": {
   "estado": "ok",
   "filas": 126256,
   "distintas": 126256,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "periodo",
    "run_fondo",
    "codigo_cuenta"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: periodo + run_fondo + codigo_cuenta — única sobre 126.256 filas."
  },
  "ffmm_cartera_extranjera": {
   "estado": "sin_clave",
   "filas": 1461253,
   "distintas": 1445843,
   "sobrantes": 15410,
   "pct_repetidas": 1.0546,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 15.410 filas idénticas (1,1 % de 1.461.253). No sumes sin agrupar. En 2026, sumar `base_tasa_dias` sin agrupar sobreestima 15,2 %.",
   "ejemplo": {
    "columna": "base_tasa_dias",
    "con_repetidas": 1143485,
    "sin_repetidas": 992645,
    "pct": 15.2,
    "periodo": "2026"
   }
  },
  "ffmm_cartera_nacional": {
   "estado": "sin_clave",
   "filas": 1590196,
   "distintas": 1429632,
   "sobrantes": 160564,
   "pct_repetidas": 10.0971,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 160.564 filas idénticas (10,1 % de 1.590.196). No sumes sin agrupar. En 2026-09, sumar `valorizacion_miles_mf` sin agrupar sobreestima 9,7 %.",
   "ejemplo": {
    "columna": "valorizacion_miles_mf",
    "con_repetidas": 82192969139,
    "sin_repetidas": 74916218817,
    "pct": 9.71,
    "periodo": "2026-09"
   }
  },
  "ffmm_futuros": {
   "estado": "sin_clave",
   "filas": 282045,
   "distintas": 268107,
   "sobrantes": 13938,
   "pct_repetidas": 4.9418,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 13.938 filas idénticas (4,9 % de 282.045). No sumes sin agrupar. En 2026, sumar `monto_comprometido_miles_mf` sin agrupar sobreestima 4,2 %.",
   "ejemplo": {
    "columna": "monto_comprometido_miles_mf",
    "con_repetidas": 78223338636,
    "sin_repetidas": 75104264119,
    "pct": 4.15,
    "periodo": "2026"
   }
  },
  "ffmm_lista_entidades": {
   "estado": "ok",
   "filas": 1334,
   "distintas": 1334,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "run_fondo"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: run_fondo — única sobre 1.334 filas."
  },
  "ffmm_opciones": {
   "estado": "sin_clave",
   "filas": 5365,
   "distintas": 5291,
   "sobrantes": 74,
   "pct_repetidas": 1.3793,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 74 filas idénticas (1,4 % de 5.365). No sumes sin agrupar."
  },
  "ffmm_resultados": {
   "estado": "ok",
   "filas": 149929,
   "distintas": 149929,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "periodo",
    "run_fondo",
    "codigo_cuenta"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: periodo + run_fondo + codigo_cuenta — única sobre 149.929 filas."
  },
  "fi_balance": {
   "estado": "ok",
   "filas": 985908,
   "distintas": 985908,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "periodo",
    "run_fondo",
    "contexto",
    "codigo_cuenta"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: periodo + run_fondo + contexto + codigo_cuenta — única sobre 985.908 filas."
  },
  "fi_bienes_raices": {
   "estado": "sin_datos",
   "filas": 0,
   "distintas": 0,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [],
   "declarada": false,
   "texto": "Sin filas publicadas: no hay clave que verificar."
  },
  "fi_cartera_extranjera": {
   "estado": "sin_clave",
   "filas": 76849,
   "distintas": 76043,
   "sobrantes": 806,
   "pct_repetidas": 1.0488,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 806 filas idénticas (1,0 % de 76.849). No sumes sin agrupar."
  },
  "fi_cartera_nacional": {
   "estado": "sin_clave",
   "filas": 933532,
   "distintas": 922499,
   "sobrantes": 11033,
   "pct_repetidas": 1.1819,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 11.033 filas idénticas (1,2 % de 933.532). No sumes sin agrupar. En 2026-06, sumar `valorizacion_miles_mf` sin agrupar sobreestima 1,1 %.",
   "ejemplo": {
    "columna": "valorizacion_miles_mf",
    "con_repetidas": 17387259281,
    "sin_repetidas": 17203962041,
    "pct": 1.07,
    "periodo": "2026-06"
   }
  },
  "fi_futuros": {
   "estado": "sin_clave",
   "filas": 13463,
   "distintas": 13454,
   "sobrantes": 9,
   "pct_repetidas": 0.0668,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 9 filas idénticas (0,067 % de 13.463). No sumes sin agrupar."
  },
  "fi_lista_entidades": {
   "estado": "ok",
   "filas": 1679,
   "distintas": 1679,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "run_fondo"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: run_fondo — única sobre 1.679 filas."
  },
  "fi_metodo_participacion": {
   "estado": "propuesta",
   "filas": 10038,
   "distintas": 10038,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "pct_activo_fondo",
    "valor_cierre_miles_mf",
    "patrimonio_emisor_miles_mf",
    "cantidad_unidades",
    "nombre_emisor",
    "rut_emisor",
    "pct_capital_emisor",
    "run_fondo",
    "provision_deterioro_miles_mf",
    "plusvalia_miles_mf",
    "isin",
    "periodo"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 12 columnas, única sobre 10.038 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "fi_opciones": {
   "estado": "propuesta",
   "filas": 307,
   "distintas": 307,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "valor_mercado_unitario_prima",
    "inversion_primas_miles_mf",
    "valorizacion_precio_ejercicio_miles_mf",
    "precio_ejercicio"
   ],
   "declarada": false,
   "tipo_clave": "medidas",
   "texto": "Clave propuesta: 4 columnas, única sobre 307 filas. No estaba declarada: se midió sobre los datos publicados. Compuesta sobre todo por importes: sirve para deduplicar, no identifica una posición."
  },
  "fi_pactos": {
   "estado": "sin_clave",
   "filas": 1698,
   "distintas": 1686,
   "sobrantes": 12,
   "pct_repetidas": 0.7067,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 12 filas idénticas (0,7 % de 1.698). No sumes sin agrupar."
  },
  "fi_resultados": {
   "estado": "ok",
   "filas": 1164000,
   "distintas": 1164000,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "periodo",
    "run_fondo",
    "contexto",
    "codigo_cuenta"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: periodo + run_fondo + contexto + codigo_cuenta — única sobre 1.164.000 filas."
  },
  "fintech_rpsf_lista_entidades": {
   "estado": "ok",
   "filas": 264,
   "distintas": 264,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "rut"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: rut — única sobre 264 filas."
  },
  "macro_cobre": {
   "estado": "ok",
   "filas": 3263,
   "distintas": 3263,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.263 filas."
  },
  "macro_curva_bonos_pesos": {
   "estado": "ok",
   "filas": 3174,
   "distintas": 3174,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.174 filas."
  },
  "macro_curva_bonos_uf": {
   "estado": "ok",
   "filas": 3176,
   "distintas": 3176,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.176 filas."
  },
  "macro_deuda_publica_pct_pib": {
   "estado": "ok",
   "filas": 50,
   "distintas": 50,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 50 filas."
  },
  "macro_dolar_observado": {
   "estado": "ok",
   "filas": 3191,
   "distintas": 3191,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.191 filas."
  },
  "macro_euro_observado": {
   "estado": "ok",
   "filas": 3191,
   "distintas": 3191,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.191 filas."
  },
  "macro_expectativas_inflacion": {
   "estado": "ok",
   "filas": 154,
   "distintas": 154,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 154 filas."
  },
  "macro_expectativas_operadores": {
   "estado": "ok",
   "filas": 238,
   "distintas": 238,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 238 filas."
  },
  "macro_expectativas_tpm": {
   "estado": "ok",
   "filas": 154,
   "distintas": 154,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 154 filas."
  },
  "macro_imacec": {
   "estado": "ok",
   "filas": 152,
   "distintas": 152,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 152 filas."
  },
  "macro_inflacion_implicita": {
   "estado": "ok",
   "filas": 3080,
   "distintas": 3080,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.080 filas."
  },
  "macro_inflacion_ipc": {
   "estado": "ok",
   "filas": 153,
   "distintas": 153,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 153 filas."
  },
  "macro_mercado_laboral": {
   "estado": "ok",
   "filas": 152,
   "distintas": 152,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 152 filas."
  },
  "macro_metales_preciosos": {
   "estado": "ok",
   "filas": 3191,
   "distintas": 3191,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.191 filas."
  },
  "macro_pib_trimestral": {
   "estado": "ok",
   "filas": 50,
   "distintas": 50,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 50 filas."
  },
  "macro_reservas_internacionales": {
   "estado": "ok",
   "filas": 153,
   "distintas": 153,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 153 filas."
  },
  "macro_series_catalogo": {
   "estado": "ok",
   "filas": 51,
   "distintas": 51,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "clave"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: clave — única sobre 51 filas."
  },
  "macro_swaps_camara": {
   "estado": "ok",
   "filas": 3205,
   "distintas": 3205,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.205 filas."
  },
  "macro_tasa_referencia_fed": {
   "estado": "ok",
   "filas": 3328,
   "distintas": 3328,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.328 filas."
  },
  "macro_tasas_corto_plazo": {
   "estado": "ok",
   "filas": 3192,
   "distintas": 3192,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.192 filas."
  },
  "macro_tipo_cambio_multilateral": {
   "estado": "ok",
   "filas": 3191,
   "distintas": 3191,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 3.191 filas."
  },
  "macro_tipo_cambio_real": {
   "estado": "ok",
   "filas": 153,
   "distintas": 153,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 153 filas."
  },
  "macro_uf": {
   "estado": "ok",
   "filas": 4682,
   "distintas": 4682,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 4.682 filas."
  },
  "macro_utm": {
   "estado": "ok",
   "filas": 154,
   "distintas": 154,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "fecha"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: fecha — única sobre 154 filas."
  },
  "patrimonios_separados_balance": {
   "estado": "ok",
   "filas": 7962,
   "distintas": 7962,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "archivo",
    "codigo_patrimonio",
    "periodo",
    "orden_en_balance",
    "cuenta"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: archivo + codigo_patrimonio + periodo + orden_en_balance + cuenta — única sobre 7.962 filas."
  },
  "patrimonios_separados_lista_entidades": {
   "estado": "ok",
   "filas": 19,
   "distintas": 19,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "numero_inscripcion"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: numero_inscripcion — única sobre 19 filas."
  },
  "securitizadoras_balance": {
   "estado": "propuesta",
   "filas": 13679,
   "distintas": 13679,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "valor",
    "cuenta",
    "periodo",
    "orden",
    "razon_social",
    "rut",
    "rut_dv",
    "tipo_balance"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 8 columnas, única sobre 13.679 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "securitizadoras_lista_entidades": {
   "estado": "ok",
   "filas": 16,
   "distintas": 16,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "rut"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: rut — única sobre 16 filas."
  },
  "securitizadoras_resultados": {
   "estado": "propuesta",
   "filas": 12290,
   "distintas": 12290,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "valor",
    "valor_no_numerico",
    "cuenta",
    "periodo",
    "orden",
    "razon_social",
    "rut",
    "rut_dv",
    "estado_financiero",
    "repeticion",
    "tipo_balance"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 11 columnas, única sobre 12.290 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "seguros_acciones": {
   "estado": "sin_clave",
   "filas": 109019,
   "distintas": 109015,
   "sobrantes": 4,
   "pct_repetidas": 0.0037,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 4 filas idénticas (0,004 % de 109.019). No sumes sin agrupar."
  },
  "seguros_acciones_relevantes": {
   "estado": "sin_clave",
   "filas": 109019,
   "distintas": 109015,
   "sobrantes": 4,
   "pct_repetidas": 0.0037,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 4 filas idénticas (0,004 % de 109.019). No sumes sin agrupar."
  },
  "seguros_bienes_raices": {
   "estado": "sin_clave",
   "filas": 760152,
   "distintas": 760016,
   "sobrantes": 136,
   "pct_repetidas": 0.0179,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 136 filas idénticas (0,018 % de 760.152). No sumes sin agrupar."
  },
  "seguros_bienes_raices_arriendo_morosidad": {
   "estado": "sin_datos",
   "filas": 0,
   "distintas": 0,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [],
   "declarada": false,
   "texto": "Sin filas publicadas: no hay clave que verificar."
  },
  "seguros_bienes_raices_arriendo_morosidad_relevantes": {
   "estado": "sin_datos",
   "filas": 0,
   "distintas": 0,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [],
   "declarada": false,
   "texto": "Sin filas publicadas: no hay clave que verificar."
  },
  "seguros_bienes_raices_relevantes": {
   "estado": "sin_clave",
   "filas": 760152,
   "distintas": 760014,
   "sobrantes": 138,
   "pct_repetidas": 0.0182,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 138 filas idénticas (0,018 % de 760.152). No sumes sin agrupar."
  },
  "seguros_control_inversiones": {
   "estado": "sin_clave",
   "filas": 111410,
   "distintas": 111386,
   "sobrantes": 24,
   "pct_repetidas": 0.0215,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 24 filas idénticas (0,021 % de 111.410). No sumes sin agrupar."
  },
  "seguros_derivados": {
   "estado": "sin_clave",
   "filas": 373469,
   "distintas": 372698,
   "sobrantes": 771,
   "pct_repetidas": 0.2064,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 771 filas idénticas (0,2 % de 373.469). No sumes sin agrupar."
  },
  "seguros_derivados_relevantes": {
   "estado": "sin_clave",
   "filas": 373469,
   "distintas": 361540,
   "sobrantes": 11929,
   "pct_repetidas": 3.1941,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 11.929 filas idénticas (3,2 % de 373.469). No sumes sin agrupar."
  },
  "seguros_extranjeros": {
   "estado": "sin_clave",
   "filas": 471942,
   "distintas": 471329,
   "sobrantes": 613,
   "pct_repetidas": 0.1299,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 613 filas idénticas (0,1 % de 471.942). No sumes sin agrupar."
  },
  "seguros_extranjeros_relevantes": {
   "estado": "sin_clave",
   "filas": 471670,
   "distintas": 464268,
   "sobrantes": 7402,
   "pct_repetidas": 1.5693,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 7.402 filas idénticas (1,6 % de 471.670). No sumes sin agrupar. En 2026, sumar `deterioro_m_clp` sin agrupar sobreestima 9,7 %.",
   "ejemplo": {
    "columna": "deterioro_m_clp",
    "con_repetidas": 673491653,
    "sin_repetidas": 613913920,
    "pct": 9.7,
    "periodo": "2026"
   }
  },
  "seguros_flujos_activos_elegibles": {
   "estado": "propuesta",
   "filas": 4369,
   "distintas": 4369,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "tramo_1_uf",
    "tramo_2_uf",
    "tramo_3_uf",
    "tramo_4_uf",
    "tramo_5_uf",
    "tramo_6_uf",
    "tramo_7_uf",
    "tramo_8_uf",
    "tramo_9_uf",
    "tramo_10_uf",
    "tipo_instrumento",
    "periodo"
   ],
   "declarada": false,
   "tipo_clave": "medidas",
   "texto": "Clave propuesta: 12 columnas, única sobre 4.369 filas. No estaba declarada: se midió sobre los datos publicados. Compuesta sobre todo por importes: sirve para deduplicar, no identifica una posición."
  },
  "seguros_fondos_mutuos": {
   "estado": "sin_clave",
   "filas": 100472,
   "distintas": 100466,
   "sobrantes": 6,
   "pct_repetidas": 0.006,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 6 filas idénticas (0,006 % de 100.472). No sumes sin agrupar."
  },
  "seguros_garantias_derivados": {
   "estado": "sin_clave",
   "filas": 6518,
   "distintas": 6515,
   "sobrantes": 3,
   "pct_repetidas": 0.046,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 3 filas idénticas (0,046 % de 6.518). No sumes sin agrupar."
  },
  "seguros_lista_entidades": {
   "estado": "ok",
   "filas": 84,
   "distintas": 84,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "sector",
    "rut_aseguradora"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: sector + rut_aseguradora — única sobre 84 filas."
  },
  "seguros_otras_inversiones": {
   "estado": "sin_clave",
   "filas": 42494,
   "distintas": 42218,
   "sobrantes": 276,
   "pct_repetidas": 0.6495,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 276 filas idénticas (0,6 % de 42.494). No sumes sin agrupar."
  },
  "seguros_pactos": {
   "estado": "sin_clave",
   "filas": 11371,
   "distintas": 11279,
   "sobrantes": 92,
   "pct_repetidas": 0.8091,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 92 filas idénticas (0,8 % de 11.371). No sumes sin agrupar."
  },
  "seguros_prestamos": {
   "estado": "sin_datos",
   "filas": 0,
   "distintas": 0,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [],
   "declarada": false,
   "texto": "Sin filas publicadas: no hay clave que verificar."
  },
  "seguros_prestamos_relevantes": {
   "estado": "sin_datos",
   "filas": 0,
   "distintas": 0,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [],
   "declarada": false,
   "texto": "Sin filas publicadas: no hay clave que verificar."
  },
  "seguros_registros_tipo6": {
   "estado": "propuesta",
   "filas": 66,
   "distintas": 66,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "archivo_origen"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 1 columnas, única sobre 66 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "seguros_renta_fija": {
   "estado": "propuesta",
   "filas": 2321911,
   "distintas": 2321911,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "costo_amortizado_clp",
    "costo_amortizado_um",
    "valor_razonable_clp",
    "saldo_insoluto_deuda_um",
    "valor_nominal_vigente",
    "deterioro_clp",
    "deuda_garantia_informacion",
    "valor_final_m_clp",
    "valor_comercial_m_clp",
    "saldo_insoluto_deuda_m_clp",
    "valor_compra_clp",
    "porcentaje_valor_par",
    "item_operacion",
    "folio_operacion",
    "periodo"
   ],
   "declarada": false,
   "tipo_clave": "medidas",
   "texto": "Clave propuesta: 15 columnas, única sobre 2.321.911 filas. No estaba declarada: se midió sobre los datos publicados. Compuesta sobre todo por importes: sirve para deduplicar, no identifica una posición."
  },
  "seguros_renta_fija_relevante": {
   "estado": "propuesta",
   "filas": 2321911,
   "distintas": 2321911,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "costo_amortizado_clp",
    "valor_razonable_clp",
    "valor_nominal_vigente",
    "deterioro_clp",
    "valor_final_m_clp",
    "nemotecnico",
    "folio_operacion",
    "serie",
    "fecha_compra",
    "fecha_vencimiento",
    "item_operacion",
    "nombre_aseguradora",
    "periodo"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 13 columnas, única sobre 2.321.911 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "seguros_tablas_desarrollo": {
   "estado": "sin_clave",
   "filas": 2193981,
   "distintas": 2186937,
   "sobrantes": 7044,
   "pct_repetidas": 0.3211,
   "columnas": [],
   "declarada": false,
   "texto": "Sin clave: publica 7.044 filas idénticas (0,3 % de 2.193.981). No sumes sin agrupar."
  },
  "seguros_tablas_descriptores": {
   "estado": "propuesta",
   "filas": 9792,
   "distintas": 9792,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "codigo_nemotecnico",
    "fecha_emision",
    "tasa_descto",
    "tasa_emision",
    "fecha_opcion",
    "nro_flujos",
    "rut_del_emisor",
    "nombre_aseguradora",
    "periodo"
   ],
   "declarada": false,
   "tipo_clave": "identifica",
   "texto": "Clave propuesta: 9 columnas, única sobre 9.792 filas. No estaba declarada: se midió sobre los datos publicados."
  },
  "sistemas_pago_lista_entidades": {
   "estado": "ok",
   "filas": 19,
   "distintas": 19,
   "sobrantes": 0,
   "pct_repetidas": 0.0,
   "columnas": [
    "rut"
   ],
   "declarada": true,
   "tipo_clave": "identifica",
   "texto": "Clave verificada: rut — única sobre 19 filas."
  }
 }
};
