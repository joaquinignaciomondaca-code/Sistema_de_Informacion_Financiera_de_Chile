/**
 * Visor de Datos en Vivo (Data Grid Viewer)
 * Monitor Financiero Chile
 * Previsualización interactiva de filas reales mediante DuckDB-Wasm.
 * Soporta ordenamiento, filtro en memoria, límites de filas y exportación.
 */

const DATA_VIEWER_CATALOG = [
  {
    group: "Macroeconomía & Tasas (BCCh SIETE)",
    tables: [
      { id: "macro_tasas_rendimientos", name: "macro.tasas_rendimientos (Curvas BCP/BCU & TPM)" },
      { id: "macro_divisas_mercado", name: "macro.divisas_mercado (USD/CLP, EUR, TCR)" },
      { id: "macro_precios_actividad", name: "macro.precios_actividad (UF, IPC, IMACEC, Cobre, EEE)" }
    ]
  },
  {
    group: "Banca Comercial (CMF / BCCh)",
    tables: [
      { id: "bancos_maestro", name: "bancos.lista_instituciones (40 entidades)" },
      { id: "bancos_balance_resumen", name: "bancos.balance_general (5.1k balances)" },
      { id: "bancos_estado_resultados", name: "bancos.estado_resultados (5.1k resultados)" },
      { id: "bancos_repos_saldos_series", name: "bancos.repos_saldos_series (2.9k pactos/repos)" },
      { id: "bancos_derivados_posicion_vigente", name: "bancos.derivados_posicion_vigente (BCCh F099)" },
      { id: "bancos_derivados_flujos_transados", name: "bancos.derivados_flujos_transados (BCCh F099)" }
    ]
  },
  {
    group: "Fondos de Pensiones (SPensiones)",
    tables: [
      { id: "afp_cartera_bonos", name: "afp.cartera_bonos (168k tenencias)" },
      { id: "afp_cartera_acciones", name: "afp.cartera_acciones (39.8k tenencias)" },
      { id: "afp_derivados_swaps", name: "afp.derivados_swaps (6.6k contratos)" },
      { id: "afp_derivados_forwards", name: "afp.derivados_forwards (560 contratos)" },
      { id: "afp_maestro", name: "afp.lista_administradoras (7 AFPs)" }
    ]
  },
  {
    group: "Seguros de Vida (CMF Circular 1835)",
    tables: [
      { id: "vida_bonos", name: "vida.cartera_bonos (9.09M filas)" },
      { id: "vida_acciones", name: "vida.cartera_acciones (124k filas)" },
      { id: "vida_bienes_raices", name: "vida.cartera_bienes_raices (1.88M filas)" },
      { id: "vida_forwards", name: "vida.b7_forwards (165k contratos)" },
      { id: "vida_swaps", name: "vida.b7_swaps (314k contratos)" },
      { id: "vida_repos", name: "vida.b7_repos (19.4k pactos)" },
      { id: "vida_maestro", name: "vida.lista_entidades (61 entidades)" }
    ]
  },
  {
    group: "Seguros Generales (CMF Circular 1835)",
    tables: [
      { id: "generales_bonos", name: "generales.cartera_bonos (287k filas)" },
      { id: "generales_acciones", name: "generales.cartera_acciones (15k filas)" },
      { id: "generales_bienes_raices", name: "generales.cartera_bienes_raices (36k filas)" },
      { id: "generales_repos", name: "generales.b7_repos (275 pactos)" },
      { id: "generales_maestro", name: "generales.lista_entidades (42 entidades)" }
    ]
  },
  {
    group: "Fondos de Inversión (CMF)",
    tables: [
      { id: "fi_caratula_eeff_historico", name: "fi.caratula_eeff_historico (Panel Histórico CMF)" },
      { id: "fi_repos_detalle_historico", name: "fi.repos_detalle_historico (2.95k contratos 2010-2026)" },
      { id: "fi_registro_fondos_universo", name: "fi.registro_fondos_universo (1.677 fondos Censo CMF)" },
      { id: "fi_repos", name: "fi.repos_vrc_crv (2.66k pactos)" },
      { id: "fi_nacional", name: "fi.cartera_nacional (834k activos)" },
      { id: "fi_extranjera", name: "fi.cartera_extranjera (67.4k activos)" },
      { id: "fi_maestro", name: "fi.lista_entidades (1.129 fondos)" }
    ]
  },
  {
    group: "Fondos Mutuos (CMF)",
    tables: [
      { id: "ffmm_caratula_eeff_2024", name: "ffmm.caratula_eeff_2024 (376 fondos auditados)" },
      { id: "ffmm_repos_detalle_2024", name: "ffmm.repos_detalle_2024 (Contratos literales CMF)" },
      { id: "ffmm_caratula_eeff_historico", name: "ffmm.caratula_eeff_historico (Panel 2015-2025)" },
      { id: "ffmm_repos_detalle_historico", name: "ffmm.repos_detalle_historico (Contratos 2015-2025)" },
      { id: "ffmm_maestro", name: "ffmm.lista_entidades (1.156 fondos)" },
      { id: "ffmm_futuros", name: "ffmm.circular_1333_futuros (11k datos)" },
      { id: "ffmm_opciones", name: "ffmm.circular_1333_opciones (3.7k datos)" }
    ]
  },
  {
    group: "Factoring & Leasing (CMF / NBFI)",
    tables: [
      { id: "factoring_leasing_maestro", name: "factoring_leasing.maestro (28 entidades CMF)" },
      { id: "factoring_leasing_balance_resumen", name: "factoring_leasing.balance_resumen (878 balances IFRS)" },
      { id: "factoring_leasing_nota_efectivo_detalle", name: "factoring_leasing.nota_efectivo_detalle (2.9k datos)" },
      { id: "factoring_leasing_cartera_morosidad_detalle", name: "factoring_leasing.cartera_morosidad_detalle (17.4k datos)" }
    ]
  },
  {
    group: "Corredoras de Bolsa (CMF)",
    tables: [
      { id: "corredoras_bolsa_registro_universo", name: "corredoras.universo (120 entidades)" },
      { id: "corredoras_bolsa_maestro", name: "corredoras.maestro (120 entidades)" },
      { id: "corredoras_bolsa_caratula_eeff_historico", name: "corredoras.caratula_eeff (621 balances IFRS)" },
      { id: "corredoras_bolsa_balance_resumen", name: "corredoras.balance_resumen (621 balances)" },
      { id: "corredoras_repos_contrapartes_tasas", name: "corredoras.repos_contrapartes (2.5k contratos)" },
      { id: "corredoras_repos_colaterales_detalle", name: "corredoras.repos_colaterales (2.6k colaterales)" }
    ]
  },
  {
    group: "Securitizadoras (CMF Ley 18.045) - EEFF",
    tables: [
      { id: "patrimonios_separados_balance_lineas", name: "patrimonios.balance_lineas (23,600 filas FECU)" },
      { id: "patrimonios_separados_excedentes_lineas", name: "patrimonios.excedentes_lineas (16,312 filas)" },
      { id: "patrimonios_separados_nota_cartera_detalle", name: "patrimonios.nota_cartera (808 filas)" },
      { id: "patrimonios_separados_nota_morosidad_detalle", name: "patrimonios.nota_morosidad (1,242 filas)" },
      { id: "patrimonios_separados_nota_bonos_detalle", name: "patrimonios.nota_bonos (498 filas)" },
      { id: "patrimonios_separados_nota_administracion_detalle", name: "patrimonios.nota_administracion (325 filas)" },
      { id: "patrimonios_separados_nota_sobrecolateral_detalle", name: "patrimonios.nota_sobrecolateral (316 filas)" },
      { id: "patrimonios_separados_nota_saldo_precio_detalle", name: "patrimonios.nota_saldo_precio (13 filas)" }
    ]
  },
  {
    group: "Securitizadoras (CMF Ley 18.045) - Otros de Interés",
    tables: [
      { id: "securitizadoras_maestro", name: "securitizadoras.maestro (16 entidades)" },
      { id: "securitizadoras_balance_resumen", name: "securitizadoras.balance_resumen (362 balances IFRS)" },
      { id: "patrimonios_separados_maestro", name: "securitizadoras.patrimonios_separados (18 programas)" },
      { id: "patrimonios_separados_balance_resumen", name: "securitizadoras.balance_resumen (64 balances)" },
      { id: "patrimonios_separados_repos_detalle", name: "securitizadoras.repos_detalle (74 pactos)" },
      { id: "patrimonios_separados_cartera_morosidad_detalle", name: "securitizadoras.cartera_morosidad (67 tramos)" }
    ]
  },
  {
    group: "Patrimonios Separados (CMF Ley 18.045)",
    tables: [
      { id: "patrimonios_separados_balance_resumen", name: "patrimonios.balance_resumen (64 balances)" },
      { id: "patrimonios_separados_nota_efectivo_detalle", name: "patrimonios.nota_efectivo_detalle (74 notas)" },
      { id: "patrimonios_separados_repos_detalle", name: "patrimonios.repos_detalle (74 pactos)" },
      { id: "patrimonios_separados_cartera_morosidad_detalle", name: "patrimonios.cartera_morosidad_detalle (67 tramos)" }
    ]
  },
  {
    group: "Cooperativas de Ahorro y Crédito (CMF)",
    tables: [
      { id: "cooperativas_maestro", name: "cooperativas.maestro (7 entidades)" },
      { id: "cooperativas_balance_resumen", name: "cooperativas.balance_resumen (294 balances IFRS)" },
      { id: "cooperativas_nota_efectivo_detalle", name: "cooperativas.nota_efectivo_detalle (122 registros Notas 5/6)" }
    ]
  },
  {
    group: "Cajas de Compensación (CCAF / CMF - SUSESO)",
    tables: [
      { id: "ccaf_maestro", name: "ccaf.maestro (6 cajas: 4 vigentes, 2 absorbidas)" },
      { id: "ccaf_caratula_totales", name: "ccaf.caratula_totales (288 balances XBRL: 2019-2026)" },
      { id: "ccaf_nota8_efectivo_resumen", name: "ccaf.nota8_efectivo_resumen (213 componentes: 2019-2026)" },
      { id: "ccaf_colocaciones_credito_social", name: "ccaf.colocaciones_credito_social (268 componentes atómicos: 2019-2026)" },
      { id: "ccaf_nota8_dap_detalle", name: "ccaf.nota8_dap_detalle (52 depósitos a plazo)" },
      { id: "ccaf_nota8_repos_detalle", name: "ccaf.nota8_repos_detalle (158 pactos de retroventa)" }
    ]
  },
  {
    group: "Administradoras Generales de Fondos (AGF)",
    tables: [
      { id: "agf_maestro", name: "agf.maestro (68 gestoras)" },
      { id: "agf_balance_resumen", name: "agf.balance_resumen (1.572 balances IFRS)" }
    ]
  },
  {
    group: "Retail Financiero (CMF)",
    tables: [
      { id: "retail_financiero_maestro", name: "retail.maestro (17 emisores y matrices)" },
      { id: "retail_financiero_balances", name: "retail.balances (190 balances IFRS)" }
    ]
  },
  {
    group: "Sistemas de Pago (BCCh / CMF)",
    tables: [
      { id: "sistemas_pago_maestro", name: "pagos.maestro (12 infraestructuras)" },
      { id: "sistemas_pago_balances", name: "pagos.balances (82 balances IFRS)" },
      { id: "sistemas_pago_estadisticas_bcch", name: "pagos.estadisticas (102 meses)" }
    ]
  },
  {
    group: "FinTech & Finanzas Abiertas (Ley 21.521 / CMF)",
    tables: [
      { id: "fintech_rpsf_maestro", name: "fintech.rpsf_maestro (262 prestadores)" },
      { id: "fintech_servicios_acreditados", name: "fintech.servicios (262 licencias)" },
      { id: "fintech_finanzas_abiertas_roles", name: "fintech.open_finance (262 roles SFA)" }
    ]
  }
];

class DataViewerController {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.currentView = "afp_cartera_bonos";
    this.currentDisplayName = "afp.cartera_bonos";
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

  async loadTable(viewName, displayName, limit = 100) {
    this.currentView = viewName;
    this.currentDisplayName = displayName || viewName;
    this.currentLimit = limit;
    this.filterText = "";
    this.sortCol = null;
    this.sortAsc = true;
    this.isLoading = true;
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
    if (typeof val !== "number") return String(val);

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

  openExportModal() {
    if (window.ExportModal) {
      window.ExportModal.open({
        viewName: this.currentView,
        displayName: this.currentDisplayName,
        currentRows: this.getFilteredRows(),
        currentColumns: this.currentColumns,
        totalCount: this.totalCount
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
        const valEsc = String(raw ?? "").replace(/'/g, "\\'").replace(/"/g, "&quot;");
        return `<td class="${isNum ? 'cell-num' : ''}" onclick="window.DataViewer.copyCell(this, '${valEsc}')" title="Clic para copiar">${formatted}</td>`;
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
          <span>Consultando <code>${this.currentView}</code> con DuckDB-Wasm...</span>
        </div>
      `;
      return;
    }

    const rows = this.getFilteredRows();
    const headersHtml = this.currentColumns.map((col, idx) => `
      <th onclick="window.DataViewer.sortTable(${idx})" title="Ordenar por ${col}">
        ${col}<span class="dv-sort-icon" id="dv_sort_${idx}"></span>
      </th>
    `).join("");

    const rowsHtml = rows.map(r => {
      const cells = this.currentColumns.map(col => {
        const raw = r[col];
        const formatted = this.formatCell(col, raw);
        const isNum = typeof raw === "number";
        const valEsc = String(raw ?? "").replace(/'/g, "\\'").replace(/"/g, "&quot;");
        return `<td class="${isNum ? 'cell-num' : ''}" onclick="window.DataViewer.copyCell(this, '${valEsc}')" title="Clic para copiar">${formatted}</td>`;
      }).join("");
      return `<tr>${cells}</tr>`;
    }).join("");

    const optionsHtml = DATA_VIEWER_CATALOG.map(grp => `
      <optgroup label="${grp.group}">
        ${grp.tables.map(tbl => `
          <option value="${tbl.id}" ${tbl.id === this.currentView ? "selected" : ""}>
            ${tbl.name}
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
            <span class="dv-badge-view">Vista: <code>${this.currentView}</code></span>
            <span class="dv-badge-mode mode-auto">Automático</span>
            <span class="dv-badge-update" title="Fecha de última actualización del pipeline">Actualizado: 2026-09-23</span>
            <span class="dv-meta-timing"><b>${this.elapsedMs} ms</b></span>
            <span class="dv-count-info">${rows.length} fila(s) · ${this.currentColumns.length} columnas</span>
            <span class="dv-scroll-tag" title="Usa la barra de desplazamiento horizontal para explorar todas las columnas">Desplaza ↔</span>
          </div>
          
          <div class="dv-actions">
            <div class="dv-search-box">
              <input type="text" id="dv-filter-input" placeholder="Filtrar datos en pantalla..." value="${this.filterText}">
            </div>
            
            <div class="dv-limit-group">
              <span class="dv-limit-label">Filas:</span>
              <button class="dv-limit-btn ${this.currentLimit === 50 ? 'active' : ''}" onclick="window.DataViewer.setLimit(50)">50</button>
              <button class="dv-limit-btn ${this.currentLimit === 100 ? 'active' : ''}" onclick="window.DataViewer.setLimit(100)">100</button>
              <button class="dv-limit-btn ${this.currentLimit === 250 ? 'active' : ''}" onclick="window.DataViewer.setLimit(250)">250</button>
              <button class="dv-limit-btn ${this.currentLimit === 500 ? 'active' : ''}" onclick="window.DataViewer.setLimit(500)">500</button>
            </div>

            <button class="dv-export-btn" onclick="window.DataViewer.openExportModal()" title="Abrir centro de exportación (CSV, Excel, Parquet con filtros)">
              Exportar Datos ▾
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
            <div class="dv-empty">No hay columnas o filas disponibles para <code>${this.currentView}</code>.</div>
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
