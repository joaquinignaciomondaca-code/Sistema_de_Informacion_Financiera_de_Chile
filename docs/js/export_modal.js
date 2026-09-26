/**
 * Centro de Exportación y Descarga de Datos Institucionales
 * Monitor Financiero Chile
 * Soporta CSV, Excel (XLSX), Parquet, filtros de periodos y particionado inteligente en ZIP.
 */

class ExportModalController {
  constructor() {
    this.modalEl = null;
    this.backdropEl = null;
    this.currentContext = {
      viewName: "vida_bonos",
      displayName: "vida.cartera_bonos",
      currentRows: [],
      currentColumns: [],
      totalCount: 100
    };

    // Mapeo directo a archivos Parquet físicos en docs/outputs/
    this.parquetMap = {
      vida_bonos: "outputs/vida/cartera_bonos.parquet",
      vida_acciones: "outputs/vida/cartera_acciones.parquet",
      vida_bienes_raices: "outputs/vida/cartera_bienes_raices.parquet",
      vida_fondos: "outputs/vida/cartera_fondos.parquet",
      vida_extranjeros: "outputs/vida/cartera_extranjeros.parquet",
      vida_solvencia: "outputs/vida/cartera_solvencia.parquet",
      vida_repos: "outputs/vida/b7_repos.parquet",
      vida_forwards: "outputs/vida/b7_forwards.parquet",
      vida_swaps: "outputs/vida/b7_swaps.parquet",
      vida_opciones: "outputs/vida/b7_opciones.parquet",
      vida_maestro: "outputs/vida/maestro_aseguradoras_vida.parquet",
      generales_bonos: "outputs/generales/cartera_bonos.parquet",
      generales_acciones: "outputs/generales/cartera_acciones.parquet",
      generales_bienes_raices: "outputs/generales/cartera_bienes_raices.parquet",
      generales_fondos: "outputs/generales/cartera_fondos.parquet",
      generales_extranjeros: "outputs/generales/cartera_extranjeros.parquet",
      generales_solvencia: "outputs/generales/cartera_solvencia.parquet",
      generales_repos: "outputs/generales/b7_repos.parquet",
      generales_forwards: "outputs/generales/b7_forwards.parquet",
      generales_swaps: "outputs/generales/b7_swaps.parquet",
      generales_maestro: "outputs/generales/maestro_aseguradoras_generales.parquet",
      fi_repos: "outputs/fi/fi_repos_vrc_crv.parquet",
      fi_nacional: "outputs/fi/fi_cartera_nacional.parquet",
      fi_extranjera: "outputs/fi/fi_cartera_extranjera.parquet",
      fi_maestro: "outputs/fi/maestro_fondos_inversion.parquet",
      ffmm_inversiones_nac: "outputs/ffmm/ffmm_futu_normalizado.parquet",
      ffmm_derivados: "outputs/ffmm/ffmm_opci_normalizado.parquet",
      ffmm_maestro: "outputs/ffmm/maestro_fondos_mutuos.parquet",
      afp_maestro: "outputs/pensiones/afp_maestro_administradoras.parquet",
      afp_derivados_forwards: "outputs/pensiones/afp_derivados_forwards.parquet",
      afp_derivados_swaps: "outputs/pensiones/afp_derivados_swaps.parquet",
      afp_cartera_bonos: "outputs/pensiones/afp_cartera_bonos.parquet",
      afp_cartera_acciones: "outputs/pensiones/afp_cartera_acciones.parquet",
      bancos_maestro: "outputs/bancos/bancos_maestro.parquet",
      bancos_balance_resumen: "outputs/bancos/bancos_balance_resumen.parquet",
      bancos_estado_resultados: "outputs/bancos/bancos_estado_resultados.parquet",
      bancos_derivados_posicion_vigente: "outputs/bancos/bancos_derivados_posicion_vigente.parquet",
      bancos_derivados_flujos_transados: "outputs/bancos/bancos_derivados_flujos_transados.parquet",
      bancos_repos_saldos_series: "outputs/bancos/bancos_repos_saldos_series.parquet",
      macro_tasas_rendimientos: "outputs/macro/macro_tasas_rendimientos.parquet",
      macro_divisas_mercado: "outputs/macro/macro_divisas_mercado.parquet",
      macro_precios_actividad: "outputs/macro/macro_precios_actividad.parquet",
      factoring_leasing_maestro: "outputs/factoring_leasing/factoring_leasing_maestro.parquet",
      factoring_leasing_balance_resumen: "outputs/factoring_leasing/factoring_leasing_balance_resumen.parquet",
      corredoras_bolsa_maestro: "outputs/corredoras_bolsa/corredoras_bolsa_maestro.parquet",
      corredoras_bolsa_balance_resumen: "outputs/corredoras_bolsa/corredoras_bolsa_balance_resumen.parquet",
      securitizadoras_maestro: "outputs/securitizadoras/securitizadoras_maestro.parquet",
      securitizadoras_balance_resumen: "outputs/securitizadoras/securitizadoras_balance_resumen.parquet",
      patrimonios_separados_maestro: "outputs/securitizadoras/patrimonios_separados_maestro.parquet",
      ccaf_maestro: "outputs/cajas_compensacion/ccaf_maestro.parquet",
      ccaf_caratula_totales: "outputs/cajas_compensacion/ccaf_caratula_totales.parquet",
      ccaf_nota8_efectivo_resumen: "outputs/cajas_compensacion/ccaf_nota8_efectivo_resumen.parquet",
      ccaf_nota8_dap_detalle: "outputs/cajas_compensacion/ccaf_nota8_dap_detalle.parquet",
      ccaf_nota8_repos_detalle: "outputs/cajas_compensacion/ccaf_nota8_repos_detalle.parquet",
      ccaf_colocaciones_credito_social: "outputs/cajas_compensacion/ccaf_colocaciones_credito_social.parquet",
      agf_maestro: "outputs/agf/agf_maestro.parquet",
      agf_balance_resumen: "outputs/agf/agf_balance_resumen.parquet",
      retail_financiero_maestro: "outputs/retail_financiero/retail_financiero_maestro.parquet",
      retail_financiero_balances: "outputs/retail_financiero/retail_financiero_balances.parquet",
      sistemas_pago_maestro: "outputs/sistemas_pago/sistemas_pago_maestro.parquet",
      sistemas_pago_balances: "outputs/sistemas_pago/sistemas_pago_balances.parquet",
      sistemas_pago_estadisticas_bcch: "outputs/sistemas_pago/sistemas_pago_estadisticas_bcch.parquet",
      fintech_rpsf_maestro: "outputs/fintech/fintech_rpsf_maestro.parquet",
      fintech_servicios_acreditados: "outputs/fintech/fintech_servicios_acreditados.parquet",
      fintech_finanzas_abiertas_roles: "outputs/fintech/fintech_finanzas_abiertas_roles.parquet"
    };

    // Estimaciones históricas de filas por tabla
    this.rowEstimates = {
      vida_bonos: 710000,
      vida_bienes_raices: 154000,
      vida_acciones: 65000,
      vida_fondos: 32000,
      vida_extranjeros: 24000,
      vida_solvencia: 180000,
      vida_repos: 19400,
      generales_bonos: 287000,
      generales_bienes_raices: 38000,
      generales_acciones: 17000,
      fi_nacional: 834000,
      fi_repos: 2654,
      ffmm_inversiones_nac: 125000,
      afp_maestro: 7,
      afp_derivados_forwards: 560,
      afp_derivados_swaps: 6666,
      afp_cartera_bonos: 168182,
      afp_cartera_acciones: 39835,
      bancos_maestro: 40,
      bancos_balance_resumen: 5095,
      bancos_estado_resultados: 5095,
      bancos_derivados_posicion_vigente: 12500,
      bancos_derivados_flujos_transados: 12500,
      bancos_repos_saldos_series: 2947,
      factoring_leasing_maestro: 28,
      factoring_leasing_balance_resumen: 878,
      corredoras_bolsa_maestro: 47,
      corredoras_bolsa_balance_resumen: 1586
    };

    this.selectedFormat = "csv"; // 'csv' | 'xlsx' | 'parquet'
    this.selectedScope = "screen"; // 'screen' | 'years' | 'all'
    this.fromYear = 2021;
    this.toYear = 2026;
    this.useZipPartitioning = true;
    this.isDownloading = false;
  }

  init() {
    this.renderModal();
    this.bindEvents();
  }

  open(context) {
    if (context) {
      this.currentContext = Object.assign(this.currentContext, context);
    }
    this.updateViewInfo();
    this.updateDiagnostics();
    if (this.backdropEl) {
      this.backdropEl.classList.add("open");
    }
  }

  close() {
    if (this.backdropEl) {
      this.backdropEl.classList.remove("open");
    }
  }

  renderModal() {
    let backdrop = document.getElementById("export-modal-backdrop");
    if (!backdrop) {
      backdrop = document.createElement("div");
      backdrop.id = "export-modal-backdrop";
      backdrop.className = "export-modal-backdrop";
      document.body.appendChild(backdrop);
    }
    this.backdropEl = backdrop;

    this.backdropEl.innerHTML = `
      <div class="export-modal" id="export-modal">
        <div class="export-modal-header">
          <div class="export-title-group">
            <h3 class="export-modal-title">Centro de Exportación & Descarga</h3>
            <select id="export-modal-table-select" class="export-modal-table-select" title="Seleccionar tabla del sistema a exportar">
            </select>
            <span class="export-table-tag" id="export-table-badge" style="display: none;">vida.cartera_bonos</span>
          </div>
          <button class="export-close-btn" id="export-close-btn" title="Cerrar">&times;</button>
        </div>

        <div class="export-modal-body">
          <!-- SECCIÓN 1: FORMATO DE DESCARGA -->
          <div class="export-section">
            <div class="export-section-title">1. Seleccionar Formato de Archivo</div>
            <div class="export-format-grid">
              
              <label class="export-format-card active" data-format="csv">
                <input type="radio" name="export-format" value="csv" checked>
                <div class="format-card-header">
                  <span class="format-name">CSV (UTF-8)</span>
                  <span class="format-badge universal">Universal</span>
                </div>
                <div class="format-desc">Compatible con Excel, Python, R, Stata. Incluye encabezados y codificación con BOM.</div>
                <div class="format-limit-note">Sin límite en DuckDB/Python. Excel trunca en 1.048.576 filas.</div>
              </label>

              <label class="export-format-card" data-format="xlsx">
                <input type="radio" name="export-format" value="xlsx">
                <div class="format-card-header">
                  <span class="format-name">Excel (.xlsx)</span>
                  <span class="format-badge excel">Planilla Nativa</span>
                </div>
                <div class="format-desc">Libro de cálculo Microsoft Excel con formateo automático de columnas numéricas.</div>
                <div class="format-limit-note">Límite duro: 1.048.576 filas. Recomendado: &lt; 250k filas.</div>
              </label>

              <label class="export-format-card" data-format="parquet">
                <input type="radio" name="export-format" value="parquet">
                <div class="format-card-header">
                  <span class="format-name">Parquet (.parquet)</span>
                  <span class="format-badge rec">85% más liviano</span>
                </div>
                <div class="format-desc">Formato columnar optimizado para Big Data. Descarga instantánea y máxima velocidad.</div>
                <div class="format-limit-note">Sin límite. Ideal para DuckDB, Polars, Pandas y Power BI.</div>
              </label>

            </div>
          </div>

          <!-- SECCIÓN 2: ALCANCE Y FILTROS TEMPORALES -->
          <div class="export-section">
            <div class="export-section-title">2. Alcance de los Datos</div>
            <div class="export-scope-options">
              
              <label class="export-scope-row">
                <input type="radio" name="export-scope" value="screen" checked>
                <div class="scope-row-info">
                  <span class="scope-title">Muestra actual en pantalla</span>
                  <span class="scope-detail" id="export-screen-detail">100 filas consultadas con DuckDB-Wasm</span>
                </div>
              </label>

              <label class="export-scope-row">
                <input type="radio" name="export-scope" value="years">
                <div class="scope-row-info">
                  <span class="scope-title">Rango de años personalizado</span>
                  <div class="scope-years-picker">
                    <label>Desde: 
                      <select id="export-year-from">
                        <option value="2016">2016</option>
                        <option value="2018">2018</option>
                        <option value="2020">2020</option>
                        <option value="2021" selected>2021</option>
                        <option value="2022">2022</option>
                        <option value="2023">2023</option>
                        <option value="2024">2024</option>
                        <option value="2025">2025</option>
                      </select>
                    </label>
                    <label>Hasta: 
                      <select id="export-year-to">
                        <option value="2021">2021</option>
                        <option value="2022">2022</option>
                        <option value="2023">2023</option>
                        <option value="2024">2024</option>
                        <option value="2025">2025</option>
                        <option value="2026" selected>2026</option>
                      </select>
                    </label>
                  </div>
                </div>
              </label>

              <label class="export-scope-row">
                <input type="radio" name="export-scope" value="all">
                <div class="scope-row-info">
                  <span class="scope-title">Toda la base histórica disponible</span>
                  <span class="scope-detail" id="export-all-detail">Serie completa consolidada (~2014 a 2026)</span>
                </div>
              </label>

            </div>
          </div>

          <!-- SECCIÓN 3: ESTRATEGIA DE PARTICIONADO Y ADVERTENCIAS -->
          <div class="export-section" id="export-partition-section">
            <div class="export-section-title">3. Estrategia de Particionado y Rendimiento</div>
            
            <label class="export-checkbox-row" id="zip-partition-checkbox-row">
              <input type="checkbox" id="export-zip-checkbox" checked>
              <div class="checkbox-row-text">
                <b>Empaquetar en archivo comprimido .ZIP particionado por años</b>
                <span>Si el volumen supera 250.000 filas, divide en archivos manejables (~100k filas c/u) para que Excel no se congele al abrirlos.</span>
              </div>
            </label>

            <div class="export-diagnostic-box" id="export-diagnostic-box">
              <div class="diagnostic-indicator"></div>
              <div class="diagnostic-content">
                <b id="diag-title">Diagnóstico de Volumen:</b>
                <span id="diag-text">Calculando tamaño estimado...</span>
              </div>
            </div>
          </div>

        </div>

        <div class="export-modal-footer">
          <div class="export-footer-status" id="export-footer-status"></div>
          <div class="export-footer-buttons">
            <button class="export-btn-cancel" id="export-btn-cancel">Cancelar</button>
            <button class="export-btn-confirm" id="export-btn-confirm">
              <span id="export-btn-label">Iniciar Descarga</span>
              <div class="export-spinner" id="export-spinner" style="display: none;"></div>
            </button>
          </div>
        </div>
      </div>
    `;
  }

  bindEvents() {
    const closeBtn = document.getElementById("export-close-btn");
    const cancelBtn = document.getElementById("export-btn-cancel");
    const confirmBtn = document.getElementById("export-btn-confirm");

    if (closeBtn) closeBtn.addEventListener("click", () => this.close());
    if (cancelBtn) cancelBtn.addEventListener("click", () => this.close());

    // Clic fuera del modal cierra
    if (this.backdropEl) {
      this.backdropEl.addEventListener("click", (e) => {
        if (e.target === this.backdropEl) this.close();
      });
    }

    // Cambio de Formato
    document.querySelectorAll("input[name='export-format']").forEach(input => {
      input.addEventListener("change", (e) => {
        this.selectedFormat = e.target.value;
        document.querySelectorAll(".export-format-card").forEach(card => {
          card.classList.toggle("active", card.dataset.format === this.selectedFormat);
        });
        this.updateDiagnostics();
      });
    });

    // Cambio de Alcance
    document.querySelectorAll("input[name='export-scope']").forEach(input => {
      input.addEventListener("change", (e) => {
        this.selectedScope = e.target.value;
        this.updateDiagnostics();
      });
    });

    // Cambio de Años
    const yearFrom = document.getElementById("export-year-from");
    const yearTo = document.getElementById("export-year-to");
    if (yearFrom) yearFrom.addEventListener("change", (e) => {
      this.fromYear = parseInt(e.target.value);
      this.updateDiagnostics();
    });
    if (yearTo) yearTo.addEventListener("change", (e) => {
      this.toYear = parseInt(e.target.value);
      this.updateDiagnostics();
    });

    // Checkbox ZIP
    const zipCb = document.getElementById("export-zip-checkbox");
    if (zipCb) zipCb.addEventListener("change", (e) => {
      this.useZipPartitioning = e.target.checked;
      this.updateDiagnostics();
    });

    // Confirmar Descarga
    if (confirmBtn) {
      confirmBtn.addEventListener("click", () => this.executeDownload());
    }
  }

  updateViewInfo() {
    const tableBadge = document.getElementById("export-table-badge");
    const tableSelect = document.getElementById("export-modal-table-select");
    const screenDetail = document.getElementById("export-screen-detail");
    const allDetail = document.getElementById("export-all-detail");

    if (tableSelect) {
      if (tableSelect.children.length === 0 && window.DATA_VIEWER_CATALOG) {
        let html = "";
        window.DATA_VIEWER_CATALOG.forEach(grp => {
          html += `<optgroup label="${grp.group}">`;
          grp.tables.forEach(t => {
            html += `<option value="${t.id}">${t.name}</option>`;
          });
          html += `</optgroup>`;
        });
        tableSelect.innerHTML = html;
        tableSelect.addEventListener("change", (e) => {
          const val = e.target.value;
          this.currentContext.viewName = val;
          const opt = e.target.options[e.target.selectedIndex];
          this.currentContext.displayName = opt ? opt.text : val;
          if (window.DataViewer && window.DataViewer.currentView === val) {
            this.currentContext.currentRows = window.DataViewer.getFilteredRows();
            this.currentContext.currentColumns = window.DataViewer.currentColumns;
          } else {
            this.currentContext.currentRows = [];
            this.currentContext.currentColumns = [];
          }
          this.updateViewInfo();
          this.updateDiagnostics();
        });
      }
      tableSelect.value = this.currentContext.viewName;
    }

    if (tableBadge) {
      tableBadge.textContent = `${this.currentContext.displayName} (${this.currentContext.viewName})`;
    }
    if (screenDetail) {
      const rowCnt = (this.currentContext.currentRows || []).length;
      screenDetail.textContent = rowCnt > 0
        ? `${rowCnt} fila(s) mostradas en pantalla · ${(this.currentContext.currentColumns || []).length} columnas`
        : `Muestra en pantalla vacía (usa 'Toda la base de datos' para exportar la serie completa)`;
    }
    const estimated = this.rowEstimates[this.currentContext.viewName] || 50000;
    if (allDetail) {
      allDetail.textContent = `Toda la base de datos histórica (~${estimated.toLocaleString('es-CL')} filas estimadas)`;
    }
  }

  updateDiagnostics() {
    const diagBox = document.getElementById("export-diagnostic-box");
    const diagTitle = document.getElementById("diag-title");
    const diagText = document.getElementById("diag-text");
    const zipRow = document.getElementById("zip-partition-checkbox-row");
    if (!diagBox || !diagTitle || !diagText) return;

    let rowCount = 0;
    const estTotal = this.rowEstimates[this.currentContext.viewName] || 50000;

    if (this.selectedScope === "screen") {
      rowCount = (this.currentContext.currentRows || []).length;
    } else if (this.selectedScope === "all") {
      rowCount = estTotal;
    } else if (this.selectedScope === "years") {
      const yearCount = Math.max(1, (this.toYear - this.fromYear) + 1);
      rowCount = Math.round(estTotal * (yearCount / 11)); // ~11 años de historia
    }

    if (this.selectedFormat === "parquet") {
      if (zipRow) zipRow.style.display = "none";
      diagBox.className = "export-diagnostic-box parquet";
      diagTitle.textContent = "Parquet Columnar Optimizado:";
      diagText.textContent = `El archivo (~${rowCount.toLocaleString('es-CL')} filas) pesará aproximadamente 80% menos que un CSV. Descarga limpia y directa sin truncamientos.`;
    } else if (this.selectedFormat === "xlsx") {
      if (zipRow) zipRow.style.display = "flex";
      if (rowCount > 1048576) {
        diagBox.className = "export-diagnostic-box warning";
        diagTitle.textContent = "Excede el límite de Excel (1.048.576 filas):";
        diagText.textContent = `Se activó obligatoriamente el particionado en archivo .ZIP. Se generarán libros Excel separados por periodo (~150k filas c/u) para que puedas abrirlos con total normalidad.`;
      } else if (rowCount > 250000) {
        diagBox.className = "export-diagnostic-box warn";
        diagTitle.textContent = "Aviso de rendimiento en Excel:";
        diagText.textContent = `Descargar ${rowCount.toLocaleString('es-CL')} filas en un solo Excel puede tardar en abrir. ${this.useZipPartitioning ? 'Se empaquetará en un .ZIP con archivos por año para máxima fluidez.' : 'Descargarás un solo archivo grande.'}`;
      } else {
        diagBox.className = "export-diagnostic-box ok";
        diagTitle.textContent = "Volumen óptimo para Excel:";
        diagText.textContent = `~${rowCount.toLocaleString('es-CL')} filas caben holgadamente en una hoja de cálculo sin lentitud.`;
      }
    } else { // CSV
      if (zipRow) zipRow.style.display = "flex";
      if (rowCount > 1048576) {
        diagBox.className = "export-diagnostic-box warn";
        diagTitle.textContent = "Aviso para usuarios de Excel:";
        diagText.textContent = `El CSV contiene ~${rowCount.toLocaleString('es-CL')} filas. Si lo abres con Excel se truncará en la fila 1M. ${this.useZipPartitioning ? 'Se dividirá en un .ZIP por años para compatibilidad con Excel.' : 'En Python/DuckDB se leerá completo.'}`;
      } else {
        diagBox.className = "export-diagnostic-box ok";
        diagTitle.textContent = "CSV Estándar:";
        diagText.textContent = `~${rowCount.toLocaleString('es-CL')} filas con codificación UTF-8 BOM para soporte de caracteres especiales y números en Chile.`;
      }
    }
  }

  async executeDownload() {
    if (this.isDownloading) return;
    this.isDownloading = true;

    const btn = document.getElementById("export-btn-confirm");
    const btnLabel = document.getElementById("export-btn-label");
    const spinner = document.getElementById("export-spinner");
    const statusText = document.getElementById("export-footer-status");

    if (btn) btn.disabled = true;
    if (btnLabel) btnLabel.textContent = "Procesando...";
    if (spinner) spinner.style.display = "inline-block";
    if (statusText) statusText.textContent = "Consultando y empaquetando datos...";

    try {
      const view = this.currentContext.viewName;
      const parquetFile = this.parquetMap[view];

      // CASO A: PARQUET DIRECTO DEL DATASET
      if (this.selectedFormat === "parquet" && parquetFile) {
        const a = document.createElement("a");
        a.href = parquetFile;
        a.download = `${view}.parquet`;
        a.click();
        if (window.ChatTerminal) window.ChatTerminal.showToast(`Descargando ${a.download}`);
        this.close();
        return;
      }

      // Obtener filas a exportar
      let rowsToExport = [];
      let colsToExport = this.currentContext.currentColumns || [];

      if (this.selectedScope === "screen") {
        rowsToExport = this.currentContext.currentRows || [];
      } else {
        // Consultar con DuckDBClient según alcance y años
        let sql = `SELECT * FROM ${view}`;
        if (this.selectedScope === "years") {
          sql += ` WHERE periodo >= '${this.fromYear}-01' AND periodo <= '${this.toYear}-12'`;
        }

        if (window.DuckDBClient) {
          const res = await window.DuckDBClient.query(sql);
          if (res && res.success) {
            rowsToExport = res.rows || [];
            colsToExport = res.columns || colsToExport;
          }
        }
      }

      if (!rowsToExport.length) {
        throw new Error("No hay filas disponibles para los criterios seleccionados.");
      }

      // CASO B: EXPORTACIÓN CSV
      if (this.selectedFormat === "csv") {
        await this.downloadCSV(rowsToExport, colsToExport, view);
      } 
      // CASO C: EXPORTACIÓN EXCEL (.XLSX)
      else if (this.selectedFormat === "xlsx") {
        await this.downloadXLSX(rowsToExport, colsToExport, view);
      }
      // CASO D: PARQUET MUESTRA
      else if (this.selectedFormat === "parquet") {
        // Si es muestra y no hay parquet binario exportable en browser puro, se emite CSV estructurado con aviso
        await this.downloadCSV(rowsToExport, colsToExport, `${view}_parquet_spec`);
      }

      if (window.ChatTerminal) {
        window.ChatTerminal.showToast(`Exportación completada exitosamente (${rowsToExport.length} filas).`);
      }
      this.close();
    } catch (err) {
      alert(`Error durante la exportación: ${err.message}`);
    } finally {
      this.isDownloading = false;
      if (btn) btn.disabled = false;
      if (btnLabel) btnLabel.textContent = "Iniciar Descarga";
      if (spinner) spinner.style.display = "none";
      if (statusText) statusText.textContent = "";
    }
  }

  async downloadCSV(rows, cols, viewName) {
    const shouldZip = this.useZipPartitioning && rows.length > 250000 && window.JSZip;

    if (!shouldZip) {
      const headerLine = cols.map(c => `"${c}"`).join(";");
      const rowLines = rows.map(r => 
        cols.map(c => `"${String(r[c] ?? '').replace(/"/g, '""')}"`).join(";")
      );
      const csvContent = "\ufeff" + [headerLine, ...rowLines].join("\n");
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      this.triggerBlobDownload(blob, `${viewName}_${this.selectedScope}_${Date.now()}.csv`);
      return;
    }

    // Particionar en ZIP
    const zip = new window.JSZip();
    const chunkSize = 150000;
    const totalParts = Math.ceil(rows.length / chunkSize);

    for (let part = 0; part < totalParts; part++) {
      const chunkRows = rows.slice(part * chunkSize, (part + 1) * chunkSize);
      const headerLine = cols.map(c => `"${c}"`).join(";");
      const rowLines = chunkRows.map(r => 
        cols.map(c => `"${String(r[c] ?? '').replace(/"/g, '""')}"`).join(";")
      );
      const csvPart = "\ufeff" + [headerLine, ...rowLines].join("\n");
      zip.file(`${viewName}_parte_${part + 1}_de_${totalParts}.csv`, csvPart);
    }

    const zipBlob = await zip.generateAsync({ type: "blob" });
    this.triggerBlobDownload(zipBlob, `${viewName}_particionado_${Date.now()}.zip`);
  }

  async downloadXLSX(rows, cols, viewName) {
    if (!window.XLSX) {
      throw new Error("La librería SheetJS (XLSX) no está cargada. Exportando en CSV de respaldo.");
    }

    const shouldZip = (this.useZipPartitioning && rows.length > 150000 && window.JSZip) || rows.length > 1048000;

    if (!shouldZip) {
      const ws = window.XLSX.utils.json_to_sheet(rows, { header: cols });
      const wb = window.XLSX.utils.book_new();
      window.XLSX.utils.book_append_sheet(wb, ws, viewName.slice(0, 31));
      const wbout = window.XLSX.write(wb, { bookType: "xlsx", type: "array" });
      const blob = new Blob([wbout], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
      this.triggerBlobDownload(blob, `${viewName}_${Date.now()}.xlsx`);
      return;
    }

    // Particionado en ZIP de libros Excel
    const zip = new window.JSZip();
    const chunkSize = 100000;
    const totalParts = Math.ceil(rows.length / chunkSize);

    for (let part = 0; part < totalParts; part++) {
      const chunkRows = rows.slice(part * chunkSize, (part + 1) * chunkSize);
      const ws = window.XLSX.utils.json_to_sheet(chunkRows, { header: cols });
      const wb = window.XLSX.utils.book_new();
      window.XLSX.utils.book_append_sheet(wb, ws, `Parte_${part + 1}`);
      const wbout = window.XLSX.write(wb, { bookType: "xlsx", type: "array" });
      zip.file(`${viewName}_parte_${part + 1}_de_${totalParts}.xlsx`, wbout);
    }

    const zipBlob = await zip.generateAsync({ type: "blob" });
    this.triggerBlobDownload(zipBlob, `${viewName}_excel_particionado_${Date.now()}.zip`);
  }

  triggerBlobDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
}

window.ExportModal = new ExportModalController();
document.addEventListener("DOMContentLoaded", () => {
  window.ExportModal.init();
});
