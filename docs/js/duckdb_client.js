const DUCKDB_WASM_URL = "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.28.0/dist/duckdb-browser.mjs";

// Vistas semánticas disponibles para el chat SQL, el explorador y las exportaciones.
const SEMANTIC_VIEWS = [
  // SEGUROS DE VIDA
  { name: "vida_maestro", file: "outputs/vida/maestro_aseguradoras_vida.parquet" },
  // El Parquet consolidado (9,09M filas) supera el límite de 100 MB de GitHub y no
  // está versionado; la vista une las dos particiones publicadas en docs/outputs/vida.
  { name: "vida_bonos", file: ["outputs/vida/cartera_bonos_2021_2024.parquet", "outputs/vida/cartera_bonos_2016_2020.parquet"] },
  { name: "vida_acciones", file: "outputs/vida/cartera_acciones.parquet" },
  { name: "vida_bienes_raices", file: "outputs/vida/cartera_bienes_raices.parquet" },
  { name: "vida_fondos", file: "outputs/vida/cartera_fondos.parquet" },
  { name: "vida_extranjeros", file: "outputs/vida/cartera_extranjeros.parquet" },
  { name: "vida_solvencia", file: "outputs/vida/cartera_solvencia.parquet" },
  { name: "vida_forwards", file: "outputs/vida/b7_forwards.parquet" },
  { name: "vida_swaps", file: "outputs/vida/b7_swaps.parquet" },
  { name: "vida_repos", file: "outputs/vida/b7_repos.parquet" },
  { name: "vida_opciones", file: "outputs/vida/b7_opciones.parquet" },
  { name: "vida_bonos_reciente", file: "outputs/vida/cartera_bonos_2021_2024.parquet" },
  { name: "vida_bonos_historico", file: "outputs/vida/cartera_bonos_2016_2020.parquet" },

  // SEGUROS GENERALES
  { name: "generales_maestro", file: "outputs/generales/maestro_aseguradoras_generales.parquet" },
  { name: "generales_bonos", file: "outputs/generales/cartera_bonos.parquet" },
  { name: "generales_acciones", file: "outputs/generales/cartera_acciones.parquet" },
  { name: "generales_bienes_raices", file: "outputs/generales/cartera_bienes_raices.parquet" },
  { name: "generales_fondos", file: "outputs/generales/cartera_fondos.parquet" },
  { name: "generales_extranjeros", file: "outputs/generales/cartera_extranjeros.parquet" },
  { name: "generales_solvencia", file: "outputs/generales/cartera_solvencia.parquet" },
  { name: "generales_forwards", file: "outputs/generales/b7_forwards.parquet" },
  { name: "generales_swaps", file: "outputs/generales/b7_swaps.parquet" },
  { name: "generales_repos", file: "outputs/generales/b7_repos.parquet" },

  // FONDOS DE INVERSION
  { name: "fi_maestro", file: "outputs/fi/maestro_fondos_inversion.parquet" },
  { name: "fi_nacional", file: "outputs/fi/fi_cartera_nacional.parquet" },
  { name: "fi_cartera_nac", file: "outputs/fi/fi_cartera_nacional.parquet" },
  { name: "fi_extranjera", file: "outputs/fi/fi_cartera_extranjera.parquet" },
  { name: "fi_cartera_ext", file: "outputs/fi/fi_cartera_extranjera.parquet" },
  { name: "fi_derivados", file: "outputs/fi/fi_futuros_forward.parquet" },
  { name: "fi_metodo_part", file: "outputs/fi/fi_metodo_participacion.parquet" },
  { name: "fi_opciones", file: "outputs/fi/fi_opciones.parquet" },
  { name: "fi_repos", file: "outputs/fi/fi_repos_vrc_crv.parquet" },
  { name: "fi_registro_fondos_universo", file: "outputs/fi/fi_registro_fondos_universo.parquet" },
  { name: "fi_repos_detalle_historico", file: "outputs/fi/fi_repos_detalle_historico.parquet" },

  { name: "fi_eeff_xml_muestra_cmf", file: "outputs/fi/fi_eeff_xml_muestra_cmf.parquet" },

  // FONDOS MUTUOS
  { name: "ffmm_maestro", file: "outputs/ffmm/maestro_fondos_mutuos.parquet" },
  { name: "ffmm_futuros", file: "outputs/ffmm/ffmm_futu_normalizado.parquet" },
  { name: "ffmm_inversiones_nac", file: "outputs/ffmm/ffmm_futu_normalizado.parquet" },
  { name: "ffmm_opciones", file: "outputs/ffmm/ffmm_opci_normalizado.parquet" },
  { name: "ffmm_repos_detalle_historico", file: "outputs/ffmm/ffmm_repos_detalle_historico.parquet" },
  { name: "ffmm_registro_fondos_universo", file: "outputs/ffmm/ffmm_registro_fondos_universo.parquet" },

  { name: "ffmm_eeff_xml_muestra_cmf", file: "outputs/ffmm/ffmm_eeff_xml_muestra_cmf.parquet" },

  // FONDOS DE PENSIONES (SPENSIONES)
  { name: "afp_maestro", file: "outputs/pensiones/afp_maestro_administradoras.parquet" },

  // BANCA: catálogo institucional y líneas CMF publicadas solo tras pasar el gate mensual.
  { name: "bancos_maestro", file: "outputs/bancos/bancos_maestro.parquet" },
  { name: "bancos_cmf_balance", manifest: "outputs/bancos/cmf_b1_b2_r1/manifest.json", where: "familia_archivo_fuente IN ('B1', 'B2')" },
  { name: "bancos_cmf_resultados", manifest: "outputs/bancos/cmf_b1_b2_r1/manifest.json", where: "familia_archivo_fuente = 'R1'" },

  // MACROECONOMIA & TASAS (BCCh SIETE)
  { name: "macro_tasas_rendimientos", file: "outputs/macro/macro_tasas_rendimientos.parquet" },
  { name: "macro_divisas_mercado", file: "outputs/macro/macro_divisas_mercado.parquet" },
  { name: "macro_precios_actividad", file: "outputs/macro/macro_precios_actividad.parquet" },

  // FACTORING & LEASING (CMF / NBFI)
  // BEGIN AUTO FL IFRS SERIES VIEWS
  { name: "factoring_leasing_balance_serie_ifrs_cmf", file: "outputs/factoring_leasing/factoring_leasing_balance_serie_ifrs_cmf.parquet" },
  { name: "factoring_leasing_resultados_serie_ifrs_cmf", file: "outputs/factoring_leasing/factoring_leasing_resultados_serie_ifrs_cmf.parquet" },
  // END AUTO FL IFRS SERIES VIEWS
  { name: "factoring_leasing_maestro", file: "outputs/factoring_leasing/factoring_leasing_maestro.parquet" },
  { name: "factoring_leasing_eeff_muestra_cmf", file: "outputs/factoring_leasing/factoring_leasing_eeff_muestra_cmf.parquet" },
  { name: "factoring_leasing_resultados_muestra_cmf", file: "outputs/factoring_leasing/factoring_leasing_resultados_muestra_cmf.parquet" },

  // CORREDORAS DE BOLSA (CMF)
  { name: "corredoras_bolsa_registro_universo", file: "outputs/corredoras_bolsa/corredoras_bolsa_registro_universo.parquet" },
  { name: "corredoras_bolsa_maestro", file: "outputs/corredoras_bolsa/corredoras_bolsa_maestro.parquet" },
  { name: "corredoras_bolsa_balance_resumen", file: "outputs/corredoras_bolsa/corredoras_bolsa_balance_resumen.parquet" },
  { name: "corredoras_bolsa_caratula_eeff_historico", file: "outputs/corredoras_bolsa/corredoras_bolsa_caratula_eeff_historico.parquet" },

        // SECURITIZADORAS (CMF / Ley 18.045) - Subsección EEFF & Notas Exhaustivas
  { name: "patrimonios_separados_balance_lineas", file: "outputs/securitizadoras/patrimonios_separados_balance_lineas.parquet" },
  { name: "patrimonios_separados_excedentes_lineas", file: "outputs/securitizadoras/patrimonios_separados_excedentes_lineas.parquet" },
  { name: "patrimonios_separados_nota_cartera_detalle", file: "outputs/securitizadoras/patrimonios_separados_nota_cartera_detalle.parquet" },
  { name: "patrimonios_separados_nota_morosidad_detalle", file: "outputs/securitizadoras/patrimonios_separados_nota_morosidad_detalle.parquet" },
  { name: "patrimonios_separados_nota_bonos_detalle", file: "outputs/securitizadoras/patrimonios_separados_nota_bonos_detalle.parquet" },
  { name: "patrimonios_separados_nota_administracion_detalle", file: "outputs/securitizadoras/patrimonios_separados_nota_administracion_detalle.parquet" },
  { name: "patrimonios_separados_nota_sobrecolateral_detalle", file: "outputs/securitizadoras/patrimonios_separados_nota_sobrecolateral_detalle.parquet" },
  { name: "patrimonios_separados_nota_efectivo_detalle", file: "outputs/securitizadoras/patrimonios_separados_nota_efectivo_detalle.parquet" },

   // SECURITIZADORAS (CMF / Ley 18.045) - Gestoras & Resumen
   { name: "securitizadoras_maestro", file: "outputs/securitizadoras/securitizadoras_maestro.parquet" },
   { name: "securitizadoras_balance_resumen", file: "outputs/securitizadoras/securitizadoras_balance_resumen.parquet" },
   { name: "patrimonios_separados_maestro", file: "outputs/securitizadoras/patrimonios_separados_maestro.parquet" },
   { name: "patrimonios_separados_balance_resumen", file: "outputs/securitizadoras/patrimonios_separados_balance_resumen.parquet" },
   { name: "patrimonios_separados_repos_detalle", file: "outputs/securitizadoras/patrimonios_separados_repos_detalle.parquet" },
   { name: "patrimonios_separados_cartera_morosidad_detalle", file: "outputs/securitizadoras/patrimonios_separados_cartera_morosidad_detalle.parquet" },
   { name: "patrimonios_separados_balance_pdf", file: "outputs/securitizadoras/patrimonios_separados_balance_pdf.parquet" },

  // COOPERATIVAS DE AHORRO Y CRÉDITO (CMF)
  { name: "cooperativas_maestro", file: "outputs/cooperativas/cooperativas_maestro.parquet" },
  { name: "cooperativas_balance_resumen", file: "outputs/cooperativas/cooperativas_balance_resumen.parquet" },
  { name: "cooperativas_nota_efectivo_detalle", file: "outputs/cooperativas/cooperativas_nota_efectivo_detalle.parquet" },

  // CAJAS DE COMPENSACION (CCAF / SUSESO - Ley 18.833 / CMF)
  { name: "ccaf_maestro", file: "outputs/cajas_compensacion/ccaf_maestro.parquet" },
  { name: "ccaf_caratula_totales", file: "outputs/cajas_compensacion/ccaf_caratula_totales.parquet" },
  { name: "ccaf_nota8_efectivo_resumen", file: "outputs/cajas_compensacion/ccaf_nota8_efectivo_resumen.parquet" },
  { name: "ccaf_nota8_dap_detalle", file: "outputs/cajas_compensacion/ccaf_nota8_dap_detalle.parquet" },
  { name: "ccaf_nota8_repos_detalle", file: "outputs/cajas_compensacion/ccaf_nota8_repos_detalle.parquet" },
  { name: "ccaf_colocaciones_credito_social", file: "outputs/cajas_compensacion/ccaf_colocaciones_credito_social.parquet" },

  // ADMINISTRADORAS GENERALES DE FONDOS (AGF / Ley 20.712)
  { name: "agf_maestro", file: "outputs/agf/agf_maestro.parquet" },
  { name: "agf_balance_resumen", file: "outputs/agf/agf_balance_resumen.parquet" },

  // RETAIL FINANCIERO Y EMISORES NO BANCARIOS (CMF)
  { name: "retail_financiero_maestro", file: "outputs/retail_financiero/retail_financiero_maestro.parquet" },
  { name: "retail_financiero_balances", file: "outputs/retail_financiero/retail_financiero_balances.parquet" },

  // SISTEMAS DE PAGO (BCCh / CMF)
  { name: "sistemas_pago_maestro", file: "outputs/sistemas_pago/sistemas_pago_maestro.parquet" },
  { name: "sistemas_pago_balances", file: "outputs/sistemas_pago/sistemas_pago_balances.parquet" },
  { name: "sistemas_pago_estadisticas_bcch", file: "outputs/sistemas_pago/sistemas_pago_estadisticas_bcch.parquet" },

  // FINTECH & FINANZAS ABIERTAS (LEY N° 21.521 / CMF)
  { name: "fintech_rpsf_maestro", file: "outputs/fintech/fintech_rpsf_maestro.parquet" },
  { name: "fintech_servicios_acreditados", file: "outputs/fintech/fintech_servicios_acreditados.parquet" },
  { name: "fintech_finanzas_abiertas_roles", file: "outputs/fintech/fintech_finanzas_abiertas_roles.parquet" }
];

class DuckDBClient {
  constructor() {
    this.db = null;
    this.conn = null;
    this.duckdb = null;
    this.isReady = false;
    // engineAvailable es true solo cuando WebAssembly quedó operativo y las
    // vistas semánticas fueron creadas sobre archivos reales.
    this.engineAvailable = false;
    this.engineError = null;
    this.unavailableViews = [];
    this.registeredFiles = new Set();
    this.initPromise = this.init();
  }

  async init() {
    try {
      console.log("[DuckDB-Wasm] Inicializando motor WebAssembly...");
      if (!window.duckdb) {
        window.duckdb = await import(DUCKDB_WASM_URL);
      }
      const duckdb = window.duckdb;
      this.duckdb = duckdb;

      const bundle = await duckdb.selectBundle(duckdb.getJsDelivrBundles());
      const worker = await duckdb.createWorker(bundle.mainWorker);
      this.db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(), worker);
      await this.db.instantiate(bundle.mainModule, bundle.pthreadWorker);
      this.conn = await this.db.connect();

      await this.registerSemanticViews();
      this.engineAvailable = true;
      console.log(`[DuckDB-Wasm] Motor listo: ${SEMANTIC_VIEWS.length - this.unavailableViews.length}/${SEMANTIC_VIEWS.length} vistas disponibles.`);
    } catch (e) {
      this.engineAvailable = false;
      this.engineError = e && e.message ? e.message : String(e);
      console.error("[DuckDB-Wasm] Motor no disponible; las consultas fallarán de forma explícita:", this.engineError);
    } finally {
      this.isReady = true;
      this.updateEngineBadge();
      if (typeof window.dispatchEvent === "function" && typeof CustomEvent === "function") {
        window.dispatchEvent(new CustomEvent("duckdb-ready", {
          detail: {
            available: this.engineAvailable,
            error: this.engineError,
            unavailableViews: this.unavailableViews.slice()
          }
        }));
      }
    }
  }

  updateEngineBadge() {
    const badge = document.getElementById("engine-badge");
    if (!badge) return;
    badge.classList.remove("live", "offline");
    if (this.engineAvailable && this.unavailableViews.length === 0) {
      badge.textContent = "DuckDB-Wasm activo";
      badge.classList.add("live");
    } else if (this.engineAvailable) {
      badge.textContent = `DuckDB activo · ${this.unavailableViews.length} vista(s) no disponible(s)`;
      badge.classList.add("offline");
      badge.title = this.unavailableViews.join(", ");
    } else {
      badge.textContent = "Motor DuckDB no disponible";
      badge.classList.add("offline");
      if (this.engineError) badge.title = this.engineError;
    }
  }

  absoluteUrl(relativePath) {
    return new URL(relativePath, document.baseURI).href;
  }

  // Registra el Parquet en el sistema de archivos virtual de DuckDB-Wasm; sin
  // este paso las rutas relativas no existen para el motor y toda consulta falla.
  async registerFile(relativePath) {
    if (this.registeredFiles.has(relativePath)) return relativePath;
    await this.db.registerFileURL(
      relativePath,
      this.absoluteUrl(relativePath),
      this.duckdb.DuckDBDataProtocol.HTTP,
      false
    );
    this.registeredFiles.add(relativePath);
    return relativePath;
  }

  async registerSemanticViews() {
    this.unavailableViews = [];
    if (!this.conn) return;

    for (const view of SEMANTIC_VIEWS) {
      try {
        let files;
        if (view.manifest) {
          const response = await fetch(this.absoluteUrl(view.manifest), { cache: "no-store" });
          if (!response.ok) throw new Error(`Manifiesto HTTP ${response.status}: ${view.manifest}`);
          const manifest = await response.json();
          files = manifest.files;
          if (!Array.isArray(files) || files.length === 0) {
            throw new Error(`No hay particiones CMF publicadas para ${view.name}`);
          }
        } else {
          files = Array.isArray(view.file) ? view.file : [view.file];
        }
        if (files.some((file) => typeof file !== "string" || file.startsWith("/") || file.split("/").includes(".."))) {
          throw new Error(`Ruta de partición no válida en ${view.name}`);
        }
        for (const file of files) {
          await this.registerFile(file);
        }
        const safePath = (file) => file.replace(/'/g, "''");
        const source = files.length === 1
          ? `read_parquet('${safePath(files[0])}')`
          : `read_parquet([${files.map((f) => `'${safePath(f)}'`).join(", ")}])`;
        const filter = view.where ? ` WHERE ${view.where}` : "";
        await this.conn.query(`CREATE OR REPLACE VIEW ${view.name} AS SELECT * FROM ${source}${filter};`);
      } catch (err) {
        // Una vista rota se declara como no disponible: la consulta que la use
        // fallará visiblemente en lugar de devolver datos inventados.
        this.unavailableViews.push(view.name);
        console.error(`[DuckDB-Wasm] Vista ${view.name} no disponible:`, err);
      }
    }

    console.log(`[DuckDB-Wasm] Vistas registradas: ${SEMANTIC_VIEWS.length - this.unavailableViews.length}/${SEMANTIC_VIEWS.length}`);
    if (this.unavailableViews.length) {
      console.warn("[DuckDB-Wasm] Vistas no disponibles:", this.unavailableViews.join(", "));
    }
  }

  async query(sql) {
    await this.initPromise;
    const t0 = performance.now();

    if (!this.engineAvailable || !this.conn) {
      return {
        success: false,
        error: `Motor DuckDB-Wasm no disponible${this.engineError ? `: ${this.engineError}` : ""}. ` +
               "Verifica la conexión al CDN y que los Parquet de docs/outputs sean accesibles; " +
               "no se muestran datos de demostración."
      };
    }

    try {
      const result = await this.conn.query(sql);
      const replacer = (key, value) => (typeof value === "bigint" ? Number(value) : value);
      const rows = result.toArray().map((row) => {
        const obj = row.toJSON();
        for (const [k, v] of Object.entries(obj)) {
          if (typeof v === "bigint") obj[k] = Number(v);
        }
        return obj;
      });
      return {
        success: true,
        rows,
        columns: result.schema.fields.map((f) => f.name),
        elapsedMs: (performance.now() - t0).toFixed(1),
        count: rows.length
      };
    } catch (err) {
      // El error real de SQL o de lectura de archivo se comunica tal cual.
      return {
        success: false,
        error: err && err.message ? err.message : String(err),
        elapsedMs: (performance.now() - t0).toFixed(1)
      };
    }
  }
}

window.DuckDBClient = new DuckDBClient();
