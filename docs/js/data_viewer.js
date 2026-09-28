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
      { id: "macro_tasas_rendimientos", name: "macro.tasas_rendimientos (153 registros)" },
      { id: "macro_divisas_mercado", name: "macro.divisas_mercado (153 registros)" },
      { id: "macro_precios_actividad", name: "macro.precios_actividad (153 registros)" },
      { id: "macro_series", name: "macro.series (51 series BCCh, una fila por serie y fecha)" },
      { id: "macro_series_catalogo", name: "macro.series_catalogo (código, nombre, frecuencia y cobertura)" }
    ]
  },
  {
    group: "Banca Comercial (CMF) · estados financieros validados",
    tables: [
      { id: "bancos_maestro", name: "bancos.lista_instituciones (catálogo institucional)" },
      { id: "bancos_cmf_balance", name: "bancos.cmf_balance_b1_b2 (Balance B1/B2 · importes fuente)" },
      { id: "bancos_cmf_resultados", name: "bancos.cmf_resultados_r1 (Estado de Resultados R1 · importes fuente)" }
    ]
  },
  {
    group: "Fondos de Pensiones (SPensiones)",
    tables: [
      { id: "afp_maestro", name: "afp.lista_administradoras (7 entidades)" }
    ]
  },
  {
    group: "Seguros de Vida y Generales (CMF Circular 1835)",
    tables: [
      { id: "seguros_maestro", name: "seguros.lista_entidades (compañías que reportan)" },
      { id: "seguros_renta_fija", name: "seguros.renta_fija (bonos y depósitos por instrumento)" },
      { id: "seguros_acciones", name: "seguros.acciones (acciones y cuotas de fondos de inversión)" },
      { id: "seguros_fondos_mutuos", name: "seguros.fondos_mutuos (cuotas de fondos mutuos)" },
      { id: "seguros_bienes_raices", name: "seguros.bienes_raices (inmuebles por rol)" },
      { id: "seguros_extranjeros", name: "seguros.extranjeros (deuda, acciones y fondos en el exterior)" },
      { id: "seguros_derivados", name: "seguros.derivados (opciones, forwards, futuros y swaps)" },
      { id: "seguros_pactos", name: "seguros.pactos (compras y ventas con pacto)" },
      { id: "seguros_control_inversiones", name: "seguros.control_inversiones (totales por tipo de inversión)" }
    ]
  },
  {
    group: "Administración de fondos · Fondos de Inversión (FI)",
    tables: [
      { id: "fi_maestro", name: "fi.lista_entidades (registro CMF de fondos)" },
      { id: "fi_cartera_nacional", name: "fi.cartera_nacional (trimestral desde 2020-03)" },
      { id: "fi_cartera_extranjera", name: "fi.cartera_extranjera (trimestral desde 2020-03)" },
      { id: "fi_metodo_participacion", name: "fi.metodo_participacion (trimestral desde 2020-03)" },
      { id: "fi_bienes_raices", name: "fi.bienes_raices (trimestral desde 2020-03)" },
      { id: "fi_futuros", name: "fi.futuros_forwards (trimestral desde 2020-03)" },
      { id: "fi_opciones", name: "fi.opciones (trimestral desde 2020-03)" },
      { id: "fi_pactos", name: "fi.pactos (trimestral desde 2020-03)" }
    ]
  },
  {
    group: "Administración de fondos · Fondos Mutuos (FFMM)",
    tables: [
      { id: "ffmm_maestro", name: "ffmm.lista_entidades (fondos que reportan cartera)" },
      { id: "ffmm_cartera_nacional", name: "ffmm.cartera_nacional (mensual desde 2022-01)" },
      { id: "ffmm_cartera_extranjera", name: "ffmm.cartera_extranjera (mensual desde 2001)" },
      { id: "ffmm_futuros", name: "ffmm.futuros_forwards (mensual desde 2001)" },
      { id: "ffmm_opciones", name: "ffmm.opciones (mensual desde 2001)" }
    ]
  },
  {
    group: "Factoring & Leasing (CMF / NBFI)",
    tables: [
      { id: "factoring_leasing_maestro", name: "factoring_leasing.lista_entidades (28 entidades)" },
      // BEGIN AUTO FL IFRS SERIES VIEWER
      { id: "factoring_leasing_balance_serie_ifrs_cmf", name: "factoring_leasing.balance_serie_ifrs_cmf (30,046 cuentas; no cotejo integral)" },
      { id: "factoring_leasing_resultados_serie_ifrs_cmf", name: "factoring_leasing.resultados_serie_ifrs_cmf (22,368 cuentas; no cotejo integral)" },
  // END AUTO FL IFRS SERIES VIEWER
    ]
  },
  {
    group: "Corredoras de Bolsa (CMF)",
    tables: [
      { id: "corredoras_bolsa_registro_universo", name: "corredoras.registro_unico (120 entidades)" },
      { id: "corredoras_bolsa_maestro", name: "corredoras.lista_entidades (120 entidades)" },
      { id: "corredoras_bolsa_balance", name: "corredoras.balance (2010-12–2026-06)" },
      { id: "corredoras_bolsa_resultados", name: "corredoras.resultados (2010-12–2026-06)" }
    ]
  },
  {
    group: "Securitización · Sociedades Securitizadoras (CMF)",
    tables: [
      { id: "securitizadoras_maestro", name: "securitizadoras.lista_entidades (16 entidades)" },
      { id: "securitizadoras_balance", name: "securitizadoras.balance (2009-12–2026-06)" },
      { id: "securitizadoras_resultados", name: "securitizadoras.resultados (2009-12–2026-06)" }
    ]
  },
  {
    group: "Securitización · Patrimonios Separados (CMF / Ley 18.045)",
    tables: [
      { id: "patrimonios_separados_maestro", name: "patrimonios_separados.lista_emisiones (18 emisiones)" },
      { id: "patrimonios_separados_balance", name: "patrimonios_separados.balance (358 balances · 7.962 cuentas, 2014–2025)" }
    ]
  },
  {
    group: "Cooperativas de Ahorro y Crédito (CMF)",
    tables: [
      { id: "cooperativas_maestro", name: "cooperativas.lista_entidades (7 entidades)" }
    ]
  },
  {
    group: "Cajas de Compensación (CCAF / CMF - SUSESO)",
    tables: [
      { id: "ccaf_maestro", name: "ccaf.lista_entidades (6 entidades)" },
      { id: "ccaf_balance", name: "ccaf.balance (2010-06–2026-06)" },
      { id: "ccaf_resultados", name: "ccaf.resultados (2010-06–2026-06)" }
    ]
  },
  {
    group: "Administración de fondos · AGF (sociedades gestoras)",
    tables: [
      { id: "agf_maestro", name: "agf.lista_administradoras (68 entidades)" },
      { id: "agf_balance", name: "agf.balance (2010-06–2026-06)" },
      { id: "agf_resultados", name: "agf.resultados (2010-06–2026-06)" }
    ]
  },
  {
    group: "Sistemas de Pago (BCCh / CMF)",
    tables: [
      { id: "sistemas_pago_maestro", name: "sistemas_pago.lista_entidades (12 entidades)" }
    ]
  },
  {
    group: "FinTech & Finanzas Abiertas (Ley 21.521 / CMF)",
    tables: [
      { id: "fintech_rpsf_maestro", name: "fintech.lista_entidades (262 entidades)" }
    ]
  }
];

class DataViewerController {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.currentView = "afp_maestro";
    this.currentDisplayName = "afp.lista_administradoras";
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

    if (this.error) {
      // El motor falló o la vista no existe: se muestra el error real en pantalla
      // en lugar de una tabla vacía que parecería decir "no hay datos".
      this.container.innerHTML = `
        <div class="dv-error-state">
          <b>No se pudieron cargar datos reales de <code>${String(this.currentView).replace(/[<>&]/g, "")}</code>.</b>
          <pre>${String(this.error).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</pre>
          <span>Revisa el indicador DuckDB de la cabecera. Esta aplicación no muestra datos de demostración.</span>
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
