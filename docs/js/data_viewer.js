/**
 * Visor de Datos en Vivo (Data Grid Viewer)
 * Sistema de Información Financiera de Chile
 * Previsualización interactiva de filas reales mediante DuckDB-Wasm.
 * Soporta ordenamiento, filtro en memoria, límites de filas y exportación.
 */

// Escapa texto para HTML y para valores de atributo (también comillas). Todo dato que venga de
// Parquet o de una consulta del usuario (celdas, alias de columna) pasa por aquí antes de innerHTML.
function dvEscapar(valor) {
  return String(valor ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

const DATA_VIEWER_CATALOG = [
  // <macro:inicio>
  {
    group: "Macroeconomía y Tasas (BCCh)",
    tables: [
      { id: "macro_tasas_corto_plazo", name: "macro.tasas_corto_plazo", detalle: "TPM y tasa interbancaria", descripcion: "Tasas de referencia de corto plazo de Chile: Tasa de Política Monetaria (TPM) del Banco Central y tasa promedio transada en el mercado interbancario (TIB), en porcentaje." },
      { id: "macro_swaps_camara", name: "macro.swaps_camara", detalle: "Swaps de cámara", descripcion: "Tasa de swap promedio de cámara (SPC) del Banco Central: contratos en pesos a 90, 180 y 360 días y a 2 años, y contrato en UF a 1 año, en porcentaje." },
      { id: "macro_curva_bonos_pesos", name: "macro.curva_bonos_pesos", detalle: "Curva de bonos en pesos", descripcion: "Curva de rendimiento de los bonos soberanos en pesos licitados por el BCCh (Bono Corto Plazo, BCP): tasa de interés de mercado secundario a 2, 5 y 10 años." },
      { id: "macro_curva_bonos_uf", name: "macro.curva_bonos_uf", detalle: "Curva de bonos en UF", descripcion: "Curva de rendimiento de los bonos soberanos en UF (BCU/BTU): tasa de interés de mercado secundario a 1, 2, 5, 10, 20 y 30 años." },
      { id: "macro_inflacion_implicita", name: "macro.inflacion_implicita", detalle: "Inflación implícita", descripcion: "Inflación implícita de las curvas soberanas (breakeven): diferencia entre el rendimiento del bono en pesos y el del bono en UF del mismo plazo. Calculada por SIF a partir de las curvas publicadas por el BCCh." },
      { id: "macro_dolar_observado", name: "macro.dolar_observado", detalle: "Dólar observado", descripcion: "Dólar observado: tipo de cambio nominal del dólar de los Estados Unidos en pesos chilenos (CLP por USD), según el Banco Central." },
      { id: "macro_euro_observado", name: "macro.euro_observado", detalle: "Euro observado", descripcion: "Euro observado: tipo de cambio nominal del euro en pesos chilenos (CLP por EUR), según el Banco Central." },
      { id: "macro_tipo_cambio_multilateral", name: "macro.tipo_cambio_multilateral", detalle: "Tipo de cambio multilateral", descripcion: "Índices de tipo de cambio nominal multilateral del Banco Central: TCM, TCM-5 (monedas de Estados Unidos, Japón, Reino Unido, Canadá y Zona Euro) y TCM-X." },
      { id: "macro_tipo_cambio_real", name: "macro.tipo_cambio_real", detalle: "Tipo de cambio real", descripcion: "Índices de tipo de cambio real (TCR) del Banco Central, promedio 1986=100: TCR general y TCR-5 (monedas de Estados Unidos, Japón, Reino Unido, Canadá y Zona Euro)." },
      { id: "macro_uf", name: "macro.uf", detalle: "Unidad de Fomento", descripcion: "Valor diario de la Unidad de Fomento (UF) en pesos chilenos, según el Banco Central." },
      { id: "macro_utm", name: "macro.utm", detalle: "Unidad Tributaria Mensual", descripcion: "Valor mensual de la Unidad Tributaria Mensual (UTM) en pesos chilenos, según el Banco Central." },
      { id: "macro_inflacion_ipc", name: "macro.inflacion_ipc", detalle: "Inflación (IPC)", descripcion: "Índice de Precios al Consumidor (IPC), serie empalmada del BCCh base 2023=100: índice y variaciones mensual y anual en porcentaje (fuente INE)." },
      { id: "macro_imacec", name: "macro.imacec", detalle: "Imacec", descripcion: "Imacec a costo de factores, series empalmadas del BCCh (índice 2018=100): total, no minero, minero, comercio y servicios." },
      { id: "macro_pib_trimestral", name: "macro.pib_trimestral", detalle: "PIB trimestral", descripcion: "Producto Interno Bruto (PIB) en volumen a precios del año anterior encadenado, referencia 2018: miles de millones de pesos encadenados." },
      { id: "macro_mercado_laboral", name: "macro.mercado_laboral", detalle: "Mercado laboral", descripcion: "Mercado laboral de Chile (series no ajustadas del INE, vía BCCh): tasa de desocupación en porcentaje, y personas ocupadas, asalariadas y fuerza de trabajo en miles de personas." },
      { id: "macro_cobre", name: "macro.cobre", detalle: "Cobre", descripcion: "Precio del cobre refinado en dólares por libra: cotización diaria de la Bolsa de Metales de Londres (BML) y valor referencial mensual publicado por el BCCh (la referencia mensual aparece en la fila del primer día de su mes)." },
      { id: "macro_metales_preciosos", name: "macro.metales_preciosos", detalle: "Metales preciosos", descripcion: "Precios de los metales preciosos en dólares por onza troy: oro y plata, según el Banco Central." },
      { id: "macro_reservas_internacionales", name: "macro.reservas_internacionales", detalle: "Reservas internacionales", descripcion: "Activos de reserva internacional del Banco Central de Chile, en millones de dólares de los Estados Unidos." },
      { id: "macro_tasa_referencia_fed", name: "macro.tasa_referencia_fed", detalle: "Tasa de la Reserva Federal", descripcion: "Tasa de interés de política monetaria de la Reserva Federal de los Estados Unidos (fed funds), en porcentaje." },
      { id: "macro_deuda_publica_pct_pib", name: "macro.deuda_publica_pct_pib", detalle: "Deuda pública sobre PIB", descripcion: "Deuda bruta del Gobierno Central como porcentaje del Producto Interno Bruto (PIB), según el Banco Central." },
      { id: "macro_expectativas_inflacion", name: "macro.expectativas_inflacion", detalle: "Expectativas de inflación", descripcion: "Expectativas de inflación de la Encuesta de Expectativas Económicas (EEE) del Banco Central: variación del IPC en 12 meses vista, con horizonte de 11 y 23 meses, mediana en porcentaje." },
      { id: "macro_expectativas_tpm", name: "macro.expectativas_tpm", detalle: "Expectativas de TPM", descripcion: "Expectativas de la Tasa de Política Monetaria (TPM) de la Encuesta de Expectativas Económicas (EEE) del Banco Central, con horizonte de 11 y 23 meses, mediana en porcentaje." },
      { id: "macro_expectativas_operadores", name: "macro.expectativas_operadores", detalle: "Encuesta de Operadores Financieros", descripcion: "Evolución diaria de la Encuesta de Operadores Financieros (EOF) del Banco Central: expectativa de inflación (variación del IPC) y de TPM para los 12 meses siguientes, en porcentaje." },
      { id: "macro_series_catalogo", name: "macro.series_catalogo", detalle: "Catálogo de series", descripcion: "Las 51 series del Banco Central que alimentan las tablas macro: código, nombre, unidad, frecuencia, cobertura y estado de la última consulta." }
    ]
  },
  // <macro:fin>
  {
    group: "Banca (CMF)",
    tables: [
      { id: "bancos_lista_entidades", name: "bancos.lista_entidades", detalle: "Lista de entidades", descripcion: "Bancos comerciales, sucursales de bancos extranjeros y agregados sectoriales de la CMF." },
      { id: "bancos_balance", name: "bancos.balance", detalle: "Balance", descripcion: "Balance B1/B2 de la CMF, con las líneas contables tal como se publican." },
      { id: "bancos_resultados", name: "bancos.resultados", detalle: "Estado de resultados", descripcion: "Estado de resultados R1 de la CMF, con las líneas tal como se publican." }
    ]
  },
  {
    group: "Fondos de Pensiones (SPensiones)",
    tables: [
      { id: "afp_lista_entidades", name: "afp.lista_entidades", detalle: "Lista de entidades", descripcion: "Administradoras de fondos de pensiones del sistema chileno." }
    ]
  },
  {
    group: "Seguros de Vida y Generales (CMF)",
    tables: [
      { id: "seguros_lista_entidades", name: "seguros.lista_entidades", detalle: "Lista de entidades", descripcion: "Compañías de seguros de vida y generales que reportan cartera a la CMF." },
      { id: "seguros_renta_fija", name: "seguros.renta_fija", detalle: "Renta fija", descripcion: "Renta fija en cartera: bonos, depósitos y otros instrumentos, valorizados al cierre." },
      { id: "seguros_acciones", name: "seguros.acciones", detalle: "Acciones", descripcion: "Acciones y cuotas de fondos de inversión en cartera, por nemotécnico." },
      { id: "seguros_fondos_mutuos", name: "seguros.fondos_mutuos", detalle: "Fondos mutuos", descripcion: "Cuotas de fondos mutuos en cartera, por administradora y fondo." },
      { id: "seguros_bienes_raices", name: "seguros.bienes_raices", detalle: "Bienes raíces", descripcion: "Inmuebles en cartera, identificados por rol y ciudad." },
      { id: "seguros_extranjeros", name: "seguros.extranjeros", detalle: "Inversiones en el exterior", descripcion: "Inversiones en el exterior: deuda, acciones y fondos, por país." },
      { id: "seguros_derivados", name: "seguros.derivados", detalle: "Derivados", descripcion: "Derivados vigentes: opciones, forwards, futuros y swaps, por contraparte." },
      { id: "seguros_pactos", name: "seguros.pactos", detalle: "Pactos", descripcion: "Compras y ventas con pacto, con tasa y contraparte." },
      { id: "seguros_control_inversiones", name: "seguros.control_inversiones", detalle: "Control de inversiones", descripcion: "Totales de inversión por tipo, para el control de límites de la Circular 1835." }
    ]
  },
  {
    group: "Fondos de Inversión (CMF)",
    tables: [
      { id: "fi_lista_entidades", name: "fi.lista_entidades", detalle: "Lista de entidades", descripcion: "Registro CMF de fondos de inversión públicos y privados." },
      { id: "fi_cartera_nacional", name: "fi.cartera_nacional", detalle: "Cartera nacional", descripcion: "Cartera de inversiones nacional de cada fondo (informes IFRS trimestrales)." },
      { id: "fi_cartera_extranjera", name: "fi.cartera_extranjera", detalle: "Cartera en el exterior", descripcion: "Cartera de inversiones en el exterior de cada fondo." },
      { id: "fi_metodo_participacion", name: "fi.metodo_participacion", detalle: "Método de participación", descripcion: "Inversiones valorizadas por método de participación." },
      { id: "fi_bienes_raices", name: "fi.bienes_raices", detalle: "Bienes raíces", descripcion: "Bienes raíces en cartera de cada fondo." },
      { id: "fi_futuros", name: "fi.futuros_forwards", detalle: "Futuros y forwards", descripcion: "Contratos de futuros y forwards vigentes de cada fondo." },
      { id: "fi_opciones", name: "fi.opciones", detalle: "Opciones", descripcion: "Contratos de opciones vigentes de cada fondo." },
      { id: "fi_pactos", name: "fi.pactos", detalle: "Pactos", descripcion: "Compras y ventas con pacto de cada fondo." }
    ]
  },
  {
    group: "Fondos Mutuos (CMF)",
    tables: [
      { id: "ffmm_lista_entidades", name: "ffmm.lista_entidades", detalle: "Lista de entidades", descripcion: "Fondos mutuos que reportan cartera a la CMF." },
      { id: "ffmm_cartera_nacional", name: "ffmm.cartera_nacional", detalle: "Cartera nacional", descripcion: "Cartera de inversiones nacional (Circular 1333)." },
      { id: "ffmm_cartera_extranjera", name: "ffmm.cartera_extranjera", detalle: "Cartera en el exterior", descripcion: "Cartera de inversiones en el exterior." },
      { id: "ffmm_futuros", name: "ffmm.futuros_forwards", detalle: "Futuros y forwards", descripcion: "Futuros y forwards vigentes al cierre de cada mes." },
      { id: "ffmm_opciones", name: "ffmm.opciones", detalle: "Opciones", descripcion: "Opciones vigentes al cierre de cada mes." },
      { id: "ffmm_balance", name: "ffmm.balance", detalle: "Balance anual", descripcion: "Balance IFRS de cada fondo mutuo al 31 de diciembre." },
      { id: "ffmm_resultados", name: "ffmm.resultados", detalle: "Estado de resultados", descripcion: "Estado de resultados IFRS de cada fondo mutuo por ejercicio." }
    ]
  },
  {
    group: "Factoring y Leasing (CMF)",
    tables: [
      { id: "factoring_leasing_lista_entidades", name: "factoring_leasing.lista_entidades", detalle: "Lista de entidades", descripcion: "Sociedades de factoring y leasing inscritas en la CMF." },
      // BEGIN AUTO FL IFRS SERIES VIEWER
      { id: "factoring_leasing_balance", name: "factoring_leasing.balance", detalle: "Balance", descripcion: "Serie IFRS de estados de situación financiera, cuenta por cuenta." },
      { id: "factoring_leasing_resultados", name: "factoring_leasing.resultados", detalle: "Estado de resultados", descripcion: "Serie IFRS de estados de resultados, cuenta por cuenta." },
  // END AUTO FL IFRS SERIES VIEWER
    ]
  },
  {
    group: "Corredoras de Bolsa (CMF)",
    tables: [
      { id: "corredoras_bolsa_lista_entidades_registro", name: "corredoras.lista_entidades_registro", detalle: "Lista de entidades (registro único)", descripcion: "Registro único de corredoras por grupo financiero y estado de vigencia." },
      { id: "corredoras_bolsa_lista_entidades", name: "corredoras.lista_entidades", detalle: "Lista de entidades", descripcion: "Corredoras de bolsa inscritas en la CMF." },
      { id: "corredoras_bolsa_balance", name: "corredoras.balance", detalle: "Balance", descripcion: "Balance FECU IFRS de cada corredora de bolsa." },
      { id: "corredoras_bolsa_resultados", name: "corredoras.resultados", detalle: "Estado de resultados", descripcion: "Estado de resultados FECU IFRS de cada corredora de bolsa." }
    ]
  },
  {
    group: "Sociedades Securitizadoras (CMF)",
    tables: [
      { id: "securitizadoras_lista_entidades", name: "securitizadoras.lista_entidades", detalle: "Lista de entidades", descripcion: "Sociedades securitizadoras inscritas en la CMF." },
      { id: "securitizadoras_balance", name: "securitizadoras.balance", detalle: "Balance", descripcion: "Balance IFRS de cada sociedad securitizadora." },
      { id: "securitizadoras_resultados", name: "securitizadoras.resultados", detalle: "Estado de resultados", descripcion: "Estado de resultados IFRS de cada sociedad securitizadora." }
    ]
  },
  {
    group: "Patrimonios Separados (CMF)",
    tables: [
      { id: "patrimonios_separados_lista_entidades", name: "patrimonios_separados.lista_entidades", detalle: "Lista de entidades", descripcion: "Patrimonios separados y sus emisiones inscritas." },
      { id: "patrimonios_separados_balance", name: "patrimonios_separados.balance", detalle: "Balance", descripcion: "Balance general de cada patrimonio separado." }
    ]
  },
  {
    group: "Cooperativas de Ahorro y Crédito (CMF)",
    tables: [
      { id: "cooperativas_lista_entidades", name: "cooperativas.lista_entidades", detalle: "Lista de entidades", descripcion: "Cooperativas de ahorro y crédito supervisadas por la CMF." }
    ]
  },
  {
    group: "Cajas de Compensación (CCAF / SUSESO)",
    tables: [
      { id: "ccaf_lista_entidades", name: "ccaf.lista_entidades", detalle: "Lista de entidades", descripcion: "Cajas de compensación de asignación familiar." },
      { id: "ccaf_balance", name: "ccaf.balance", detalle: "Balance", descripcion: "Balance IFRS de cada caja de compensación." },
      { id: "ccaf_resultados", name: "ccaf.resultados", detalle: "Estado de resultados", descripcion: "Estado de resultados IFRS de cada caja de compensación." }
    ]
  },
  {
    group: "Administradoras Generales de Fondos (CMF)",
    tables: [
      { id: "agf_lista_entidades", name: "agf.lista_entidades", detalle: "Lista de entidades", descripcion: "Administradoras generales de fondos inscritas en la CMF." },
      { id: "agf_balance", name: "agf.balance", detalle: "Balance", descripcion: "Balance IFRS de cada administradora general de fondos." },
      { id: "agf_resultados", name: "agf.resultados", detalle: "Estado de resultados", descripcion: "Estado de resultados IFRS de cada administradora general de fondos." }
    ]
  },
  {
    group: "Sistemas de Pago (BCCh / CMF)",
    tables: [
      { id: "sistemas_pago_lista_entidades", name: "sistemas_pago.lista_entidades", detalle: "Lista de entidades", descripcion: "Operadores de infraestructura financiera y redes de pago." }
    ]
  },
  {
    group: "FinTech & Finanzas Abiertas (Ley 21.521 / CMF)",
    tables: [
      { id: "fintech_rpsf_lista_entidades", name: "fintech.lista_entidades", detalle: "Lista de entidades", descripcion: "Prestadores inscritos en el Registro de Prestadores de Servicios Financieros (RPSF)." }
    ]
  }
];

class DataViewerController {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.currentView = "afp_lista_entidades";
    this.currentDisplayName = "afp.lista_entidades";
    this.currentLimit = 100;
    this.currentRows = [];
    this.currentColumns = [];
    this.filterText = "";
    this.sortCol = null;
    this.sortAsc = true;
    this.isLoading = false;
    this.elapsedMs = 0;
    this.totalCount = 0;
  }

  init() {
    if (!this.container) return;
    this.loadTable(this.currentView, this.currentDisplayName, this.currentLimit);
  }

  sectorForView(viewName) {
    const id = String(viewName || "");
    const sectors = [
      ["patrimonios_separados_", "patrimonios_separados"],
      ["cajas_compensacion_", "cajas_compensacion"],
      ["ccaf_", "cajas_compensacion"],
      ["factoring_leasing_", "factoring_leasing"],
      ["corredoras_bolsa_", "corredoras_bolsa"],
      ["securitizadoras_", "securitizadoras"],
      ["sistemas_pago_", "sistemas_pago"],
      ["cooperativas_", "cooperativas"],
      ["seguros_", "seguros"],
      ["ffmm_", "ffmm"],
      ["agf_", "agf"],
      ["fi_", "fi"],
      ["afp_", "afp_corporativo"],
      ["bancos_", "bancos"],
      ["macro_", "macro"],
      ["fintech_", "fintech"]
    ];
    const match = sectors.find(([prefix]) => id.startsWith(prefix));
    return match ? match[1] : null;
  }

  modeForView() {
    const table = (window.SIFDataDictionary || []).find((item) => item.id === this.currentView);
    const modo = table && table.modo ? table.modo : "Automático";
    const helper = window.SIFDataMode;
    if (!helper) return { className: "auto", label: "Automático", title: "Modalidad de procesamiento" };
    return {
      className: helper.className(modo),
      label: helper.label(modo),
      title: (table && table.modoAyuda) || helper.title(modo)
    };
  }

  async loadTable(viewName, displayName, limit = 100) {
    this.currentView = viewName;
    this.currentDisplayName = displayName || viewName;
    const industry = this.sectorForView(viewName);
    if (industry && window.SidebarNav && typeof window.SidebarNav.setActiveSector === "function") {
      window.SidebarNav.setActiveSector(industry, "data-viewer");
    }
    this.currentLimit = limit;
    this.filterText = "";
    this.sortCol = null;
    this.sortAsc = true;
    this.isLoading = true;
    this.error = null;
    this.render();

    const t0 = performance.now();
    try {
      if (!window.DuckDBClient) {
        throw new Error("DuckDB-Wasm no está inicializado.");
      }
      
      const sql = `SELECT * FROM ${this.currentView} LIMIT ${this.currentLimit};`;
      const res = await window.DuckDBClient.query(sql);

      this.elapsedMs = (performance.now() - t0).toFixed(1);
      if (res && res.success) {
        this.currentColumns = res.columns || [];
        this.currentRows = res.rows || [];
        this.totalCount = res.count || this.currentRows.length;
      } else {
        this.currentColumns = [];
        this.currentRows = [];
        this.error = res ? res.error : "Error desconocido";
      }
    } catch (err) {
      this.elapsedMs = (performance.now() - t0).toFixed(1);
      this.error = err.message;
      this.currentColumns = [];
      this.currentRows = [];
    } finally {
      this.isLoading = false;
      this.render();
    }
  }

  setLimit(limit) {
    this.currentLimit = limit;
    this.loadTable(this.currentView, this.currentDisplayName, limit);
  }

  setFilter(text) {
    this.filterText = text.toLowerCase().trim();
    this.renderRowsOnly();
  }

  sortTable(colIdx) {
    const colName = this.currentColumns[colIdx];
    if (!colName) return;

    if (this.sortCol === colName) {
      this.sortAsc = !this.sortAsc;
    } else {
      this.sortCol = colName;
      this.sortAsc = true;
    }

    this.currentRows.sort((a, b) => {
      let va = a[colName];
      let vb = b[colName];
      if (va === null || va === undefined) return 1;
      if (vb === null || vb === undefined) return -1;
      if (typeof va === "number" && typeof vb === "number") {
        return this.sortAsc ? va - vb : vb - va;
      }
      return this.sortAsc
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va));
    });

    this.renderRowsOnly();
    this.updateSortIcons(colIdx);
  }

  formatCell(colName, val) {
    if (val === null || val === undefined) return '<span class="cell-null">—</span>';
    if (typeof val !== "number") return dvEscapar(val);

    const lower = colName.toLowerCase();
    if (lower.includes("_pct") || lower.includes("tasa") || lower.includes("tir") || lower.includes("presencia")) {
      return val.toLocaleString("es-CL", { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + " %";
    }
    if (lower.includes("_usd_millones") || lower.includes("m_usd") || lower.includes("total_aum_m_usd") || lower.includes("encaje_requerido_m_usd")) {
      return "US$ " + val.toLocaleString("es-CL", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " M";
    }
    if (lower.includes("_m_clp") || lower.includes("tasacion") || lower.includes("avaluo") || lower.includes("inversion") || lower.includes("monto")) {
      return "$" + val.toLocaleString("es-CL", { maximumFractionDigits: 2 }) + " M";
    }
    if (lower.includes("precio")) {
      return "$" + val.toLocaleString("es-CL", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return val.toLocaleString("es-CL", { maximumFractionDigits: 4 });
  }

  copyCell(tdEl, rawVal) {
    navigator.clipboard.writeText(String(rawVal)).then(() => {
      const origBg = tdEl.style.backgroundColor;
      tdEl.style.backgroundColor = "var(--accent-mint-dim)";
      setTimeout(() => {
        tdEl.style.backgroundColor = origBg;
      }, 300);
      if (window.ChatTerminal && typeof window.ChatTerminal.showToast === "function") {
        window.ChatTerminal.showToast(`Copiado: ${String(rawVal).slice(0, 35)}`);
      }
    }).catch(() => {});
  }

  // La exportación vive ahora en la pestaña Descargas: se abre con esta tabla
  // ya seleccionada. Se conserva el nombre del método por compatibilidad con el
  // botón del visor y con enlaces antiguos.
  openExportModal() {
    if (window.MFCUI && window.MFCUI.openDownloads) {
      window.MFCUI.openDownloads({
        viewName: this.currentView,
        displayName: this.currentDisplayName,
        rows: this.getFilteredRows(),
        columns: this.currentColumns,
        origen: "visor"
      });
    } else {
      this.exportCSV();
    }
  }

  exportCSV() {
    if (!this.currentRows.length) return;
    const cols = this.currentColumns;
    const headerLine = cols.map(c => `"${c}"`).join(",");
    const rowLines = this.currentRows.map(r => 
      cols.map(c => `"${String(r[c] ?? '').replace(/"/g, '""')}"`).join(",")
    );
    const csv = "\ufeff" + [headerLine, ...rowLines].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${this.currentView}_export_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  getFilteredRows() {
    if (!this.filterText) return this.currentRows;
    return this.currentRows.filter(r => 
      this.currentColumns.some(c => String(r[c] ?? "").toLowerCase().includes(this.filterText))
    );
  }

  renderRowsOnly() {
    const tbody = this.container ? this.container.querySelector(".dv-table tbody") : null;
    if (!tbody) return;

    const rows = this.getFilteredRows();
    tbody.innerHTML = rows.map(r => {
      const cells = this.currentColumns.map(col => {
        const raw = r[col];
        const formatted = this.formatCell(col, raw);
        const isNum = typeof raw === "number";
        // El valor va en data-copy (escapado) y no dentro de un string JS en el onclick: así
        // ni comillas, barras invertidas ni entidades del dato pueden salir del atributo.
        return `<td class="${isNum ? 'cell-num' : ''}" data-copy="${dvEscapar(raw)}" onclick="window.DataViewer.copyCell(this, this.dataset.copy)" title="Clic para copiar">${formatted}</td>`;
      }).join("");
      return `<tr>${cells}</tr>`;
    }).join("");

    const countInfo = this.container.querySelector(".dv-count-info");
    if (countInfo) {
      countInfo.textContent = `${rows.length} de ${this.currentRows.length} fila(s) · ${this.currentColumns.length} columnas`;
    }
  }

  updateSortIcons(activeIdx) {
    const ths = this.container.querySelectorAll(".dv-table th");
    ths.forEach((th, i) => {
      const icon = th.querySelector(".dv-sort-icon");
      if (icon) {
        if (i === activeIdx) {
          icon.textContent = this.sortAsc ? " ▲" : " ▼";
          icon.style.color = "var(--accent-mint)";
        } else {
          icon.textContent = "";
        }
      }
    });
  }

  render() {
    if (!this.container) return;

    if (this.isLoading) {
      this.container.innerHTML = `
        <div class="dv-loading-state">
          <div class="dv-spinner"></div>
          <span>Consultando <code>${dvEscapar(this.currentView)}</code> con DuckDB-Wasm...</span>
        </div>
      `;
      return;
    }

    if (this.error) {
      // El motor falló o la vista no existe: se muestra el error real en pantalla
      // en lugar de una tabla vacía que parecería decir "no hay datos".
      this.container.innerHTML = `
        <div class="dv-error-state">
          <b>No se pudieron cargar datos reales de <code>${dvEscapar(this.currentView)}</code>.</b>
          <pre>${dvEscapar(this.error)}</pre>
          <span>Revisa el indicador DuckDB de la cabecera. Esta aplicación no muestra datos de demostración.</span>
        </div>
      `;
      return;
    }

    const rows = this.getFilteredRows();
    const mode = this.modeForView();
    const headersHtml = this.currentColumns.map((col, idx) => `
      <th onclick="window.DataViewer.sortTable(${idx})" title="Ordenar por ${dvEscapar(col)}">
        ${dvEscapar(col)}<span class="dv-sort-icon" id="dv_sort_${idx}"></span>
      </th>
    `).join("");

    const rowsHtml = rows.map(r => {
      const cells = this.currentColumns.map(col => {
        const raw = r[col];
        const formatted = this.formatCell(col, raw);
        const isNum = typeof raw === "number";
        // El valor va en data-copy (escapado) y no dentro de un string JS en el onclick: así
        // ni comillas, barras invertidas ni entidades del dato pueden salir del atributo.
        return `<td class="${isNum ? 'cell-num' : ''}" data-copy="${dvEscapar(raw)}" onclick="window.DataViewer.copyCell(this, this.dataset.copy)" title="Clic para copiar">${formatted}</td>`;
      }).join("");
      return `<tr>${cells}</tr>`;
    }).join("");

    const optionsHtml = DATA_VIEWER_CATALOG.map(grp => `
      <optgroup label="${grp.group}">
        ${grp.tables.map(tbl => `
          <option value="${tbl.id}" ${tbl.id === this.currentView ? "selected" : ""}>
            ${tbl.name}${tbl.detalle ? "  ·  " + tbl.detalle : ""}
          </option>
        `).join("")}
      </optgroup>
    `).join("");

    this.container.innerHTML = `
      <div class="dv-wrapper">
        <!-- Barra de herramientas del visor -->
        <div class="dv-toolbar">
          <div class="dv-table-info">
            <label for="dv-table-select" class="dv-select-label">Tabla:</label>
            <select id="dv-table-select" class="dv-table-select">
              ${optionsHtml}
            </select>
            <span class="dv-badge-view">Vista: <code>${dvEscapar(this.currentView)}</code></span>
            <span class="dv-badge-mode mode-${mode.className}" title="${dvEscapar(mode.title)}">${dvEscapar(mode.label)}</span>
            <span class="dv-badge-update" title="Fecha de última actualización del pipeline">Actualizado: 2026-09-23</span>
            <span class="dv-meta-timing"><b>${this.elapsedMs} ms</b></span>
            <span class="dv-count-info">${rows.length} fila(s) · ${this.currentColumns.length} columnas</span>
            <span class="dv-scroll-tag" title="Usa la barra de desplazamiento horizontal para explorar todas las columnas">Desplaza ↔</span>
          </div>
          
          <div class="dv-actions">
            <div class="dv-search-box">
              <input type="text" id="dv-filter-input" placeholder="Filtrar datos en pantalla..." value="${dvEscapar(this.filterText)}">
            </div>
            
            <div class="dv-limit-group">
              <span class="dv-limit-label">Filas:</span>
              <button class="dv-limit-btn ${this.currentLimit === 50 ? 'active' : ''}" onclick="window.DataViewer.setLimit(50)">50</button>
              <button class="dv-limit-btn ${this.currentLimit === 100 ? 'active' : ''}" onclick="window.DataViewer.setLimit(100)">100</button>
              <button class="dv-limit-btn ${this.currentLimit === 250 ? 'active' : ''}" onclick="window.DataViewer.setLimit(250)">250</button>
              <button class="dv-limit-btn ${this.currentLimit === 500 ? 'active' : ''}" onclick="window.DataViewer.setLimit(500)">500</button>
            </div>

            <button class="dv-export-btn" onclick="window.DataViewer.openExportModal()" title="Abrir la pestaña Descargas con esta tabla seleccionada (Parquet, CSV, Excel)">
              Descargar datos
            </button>
          </div>
        </div>

        <!-- Tabla de datos scrollable -->
        <div class="dv-table-container">
          ${this.currentColumns.length > 0 ? `
            <table class="dv-table">
              <thead><tr>${headersHtml}</tr></thead>
              <tbody>${rowsHtml}</tbody>
            </table>
          ` : `
            <div class="dv-empty">No hay columnas o filas disponibles para <code>${dvEscapar(this.currentView)}</code>.</div>
          `}
        </div>
      </div>
    `;

    const filterInput = document.getElementById("dv-filter-input");
    if (filterInput) {
      filterInput.addEventListener("input", (e) => {
        this.setFilter(e.target.value);
      });
    }

    const tableSelect = document.getElementById("dv-table-select");
    if (tableSelect) {
      tableSelect.addEventListener("change", (e) => {
        const selVal = e.target.value;
        let displayName = selVal;
        for (const grp of DATA_VIEWER_CATALOG) {
          const found = grp.tables.find(t => t.id === selVal);
          if (found) {
            displayName = found.name.split(" ")[0];
            break;
          }
        }
        this.loadTable(selVal, displayName, this.currentLimit);
      });
    }
  }
}

window.DataViewer = new DataViewerController("data-viewer-container");
