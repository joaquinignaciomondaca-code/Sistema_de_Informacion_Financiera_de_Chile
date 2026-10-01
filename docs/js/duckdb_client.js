// Motor DuckDB-Wasm. Se intenta primero la copia incluida en el repositorio
// (docs/vendor/duckdb) para que el terminal funcione sin depender de la red del
// visitante ni de un CDN externo; si esa copia faltara o el navegador no
// soportara el bundle "eh", se cae al CDN oficial como respaldo.
const DUCKDB_VERSION = "1.28.0";
const DUCKDB_LOCAL_DIR = "vendor/duckdb/";
// Los .mjs que publica upstream en dist/ importan "apache-arrow" como
// especificador desnudo, que ningún navegador resuelve sin import map. Por eso
// el respaldo usa endpoints que sí entregan el módulo con sus dependencias ya
// resueltas (+esm en jsDelivr, esm.sh), mientras el .wasm y el worker se siguen
// tomando de dist/, que son archivos sueltos y no tienen ese problema.
const DUCKDB_CDN_BASES = [
  {
    id: "jsdelivr",
    label: "CDN jsDelivr",
    mjs: `https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@${DUCKDB_VERSION}/+esm`,
    dist: `https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@${DUCKDB_VERSION}/dist/`
  },
  {
    id: "esmsh",
    label: "CDN esm.sh",
    mjs: `https://esm.sh/@duckdb/duckdb-wasm@${DUCKDB_VERSION}`,
    dist: `https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@${DUCKDB_VERSION}/dist/`
  }
];

// Nombres anteriores de las vistas publicadas. Se conservan como alias SQL para que
// las consultas ya guardadas por los visitantes sigan funcionando, pero la interfaz
// sólo muestra y sugiere el nombre canónico del vocabulario (docs/vocabulario.json).
// La lista la regenera scripts/normalizar_vocabulario.py: no editar a mano.
const LEGACY_VIEW_ALIASES = {
  // BEGIN VOCABULARIO ALIAS
  seguros_lista_entidades: ["seguros_maestro"],
  fi_lista_entidades: ["fi_maestro"],
  ffmm_lista_entidades: ["ffmm_maestro"],
  afp_lista_entidades: ["afp_maestro"],
  bancos_lista_entidades: ["bancos_maestro"],
  bancos_balance: ["bancos_cmf_balance"],
  bancos_resultados: ["bancos_cmf_resultados"],
  factoring_leasing_lista_entidades: ["factoring_leasing_maestro"],
  factoring_leasing_balance: ["factoring_leasing_balance_serie_ifrs_cmf"],
  factoring_leasing_resultados: ["factoring_leasing_resultados_serie_ifrs_cmf"],
  corredoras_bolsa_lista_entidades: ["corredoras_bolsa_maestro"],
  corredoras_bolsa_lista_entidades_registro: ["corredoras_bolsa_registro_universo"],
  securitizadoras_lista_entidades: ["securitizadoras_maestro"],
  patrimonios_separados_lista_entidades: ["patrimonios_separados_maestro"],
  cooperativas_lista_entidades: ["cooperativas_maestro"],
  ccaf_lista_entidades: ["ccaf_maestro"],
  agf_lista_entidades: ["agf_maestro"],
  sistemas_pago_lista_entidades: ["sistemas_pago_maestro"],
  fintech_rpsf_lista_entidades: ["fintech_rpsf_maestro"],
  // END VOCABULARIO ALIAS
};

// Vistas semánticas disponibles para el chat SQL, el explorador y las exportaciones.
const SEMANTIC_VIEWS = [
  // SEGUROS (vida y generales en las mismas tablas, columna "sector"). Cartera de inversiones
  // de la Circular 1835 leída con la ficha técnica oficial; se actualiza sola 3 veces al mes y
  // cada tabla se publica en archivos por año o por mes listados en su manifiesto.
  { name: "seguros_lista_entidades", file: "outputs/seguros/aseguradoras.parquet" },
  { name: "seguros_renta_fija", manifest: "outputs/seguros/renta_fija/manifest.json" },
  { name: "seguros_acciones", manifest: "outputs/seguros/acciones/manifest.json" },
  { name: "seguros_fondos_mutuos", manifest: "outputs/seguros/fondos_mutuos/manifest.json" },
  { name: "seguros_bienes_raices", manifest: "outputs/seguros/bienes_raices/manifest.json" },
  { name: "seguros_extranjeros", manifest: "outputs/seguros/extranjeros/manifest.json" },
  { name: "seguros_derivados", manifest: "outputs/seguros/derivados/manifest.json" },
  { name: "seguros_pactos", manifest: "outputs/seguros/pactos/manifest.json" },
  { name: "seguros_control_inversiones", manifest: "outputs/seguros/control_inversiones/manifest.json" },

  // FONDOS DE INVERSIÓN. Cartera y pactos de los informes IFRS trimestrales de cada fondo (CMF);
  // se actualiza sola 3 veces al mes. Montos en miles de la moneda funcional de cada fondo.
  { name: "fi_lista_entidades", file: "outputs/fi/maestro_fondos_inversion.parquet" },
  { name: "fi_cartera_nacional", manifest: "outputs/fi/cartera_nacional/manifest.json" },
  { name: "fi_cartera_extranjera", manifest: "outputs/fi/cartera_extranjera/manifest.json" },
  { name: "fi_metodo_participacion", manifest: "outputs/fi/metodo_participacion/manifest.json" },
  { name: "fi_bienes_raices", manifest: "outputs/fi/bienes_raices/manifest.json" },
  { name: "fi_futuros", manifest: "outputs/fi/futuros_forwards/manifest.json" },
  { name: "fi_opciones", manifest: "outputs/fi/opciones/manifest.json" },
  { name: "fi_pactos", manifest: "outputs/fi/pactos/manifest.json" },
  // BEGIN AUTO FI EEFF VIEWS
  // END AUTO FI EEFF VIEWS

  // FONDOS MUTUOS. Cartera de inversiones de la Circular 1333 (archivo mensual CMF) y balance y estado de
  // resultados anuales IFRS (XML de la Circular 1997, uno por fondo y año); se actualizan solos 3 veces al mes.
  // Montos en miles de la moneda funcional de cada fondo.
  { name: "ffmm_lista_entidades", file: "outputs/ffmm/maestro_fondos_mutuos.parquet" },
  { name: "ffmm_cartera_nacional", manifest: "outputs/ffmm/cartera_nacional/manifest.json" },
  { name: "ffmm_cartera_extranjera", manifest: "outputs/ffmm/cartera_extranjera/manifest.json" },
  { name: "ffmm_futuros", manifest: "outputs/ffmm/futuros_forwards/manifest.json" },
  { name: "ffmm_opciones", manifest: "outputs/ffmm/opciones/manifest.json" },
  { name: "ffmm_balance", manifest: "outputs/ffmm/ffmm_balance/manifest.json" },
  { name: "ffmm_resultados", manifest: "outputs/ffmm/ffmm_resultados/manifest.json" },

  // FONDOS DE PENSIONES (SPENSIONES)
  { name: "afp_lista_entidades", file: "outputs/pensiones/afp_maestro_administradoras.parquet" },

  // BANCA: catálogo institucional y líneas CMF publicadas solo tras pasar el gate mensual.
  { name: "bancos_lista_entidades", file: "outputs/bancos/bancos_maestro.parquet" },
  { name: "bancos_balance", manifest: "outputs/bancos/cmf_b1_b2_r1/manifest.json", where: "familia_archivo_fuente IN ('B1', 'B2')" },
  { name: "bancos_resultados", manifest: "outputs/bancos/cmf_b1_b2_r1/manifest.json", where: "familia_archivo_fuente = 'R1'" },

  // MACROECONOMÍA & TASAS (BCCh SIETE)
  // <macro:inicio>
  { name: "macro_tasas_corto_plazo", file: "outputs/macro/macro_tasas_corto_plazo.parquet" },
  { name: "macro_swaps_camara", file: "outputs/macro/macro_swaps_camara.parquet" },
  { name: "macro_curva_bonos_pesos", file: "outputs/macro/macro_curva_bonos_pesos.parquet" },
  { name: "macro_curva_bonos_uf", file: "outputs/macro/macro_curva_bonos_uf.parquet" },
  { name: "macro_inflacion_implicita", file: "outputs/macro/macro_inflacion_implicita.parquet" },
  { name: "macro_dolar_observado", file: "outputs/macro/macro_dolar_observado.parquet" },
  { name: "macro_euro_observado", file: "outputs/macro/macro_euro_observado.parquet" },
  { name: "macro_tipo_cambio_multilateral", file: "outputs/macro/macro_tipo_cambio_multilateral.parquet" },
  { name: "macro_tipo_cambio_real", file: "outputs/macro/macro_tipo_cambio_real.parquet" },
  { name: "macro_uf", file: "outputs/macro/macro_uf.parquet" },
  { name: "macro_utm", file: "outputs/macro/macro_utm.parquet" },
  { name: "macro_inflacion_ipc", file: "outputs/macro/macro_inflacion_ipc.parquet" },
  { name: "macro_imacec", file: "outputs/macro/macro_imacec.parquet" },
  { name: "macro_pib_trimestral", file: "outputs/macro/macro_pib_trimestral.parquet" },
  { name: "macro_mercado_laboral", file: "outputs/macro/macro_mercado_laboral.parquet" },
  { name: "macro_cobre", file: "outputs/macro/macro_cobre.parquet" },
  { name: "macro_metales_preciosos", file: "outputs/macro/macro_metales_preciosos.parquet" },
  { name: "macro_reservas_internacionales", file: "outputs/macro/macro_reservas_internacionales.parquet" },
  { name: "macro_tasa_referencia_fed", file: "outputs/macro/macro_tasa_referencia_fed.parquet" },
  { name: "macro_deuda_publica_pct_pib", file: "outputs/macro/macro_deuda_publica_pct_pib.parquet" },
  { name: "macro_expectativas_inflacion", file: "outputs/macro/macro_expectativas_inflacion.parquet" },
  { name: "macro_expectativas_tpm", file: "outputs/macro/macro_expectativas_tpm.parquet" },
  { name: "macro_expectativas_operadores", file: "outputs/macro/macro_expectativas_operadores.parquet" },
  { name: "macro_series_catalogo", file: "outputs/macro/macro_series_catalogo.parquet" },
  // <macro:fin>

  // FACTORING & LEASING (CMF / NBFI)
  // BEGIN AUTO FL IFRS SERIES VIEWS
  { name: "factoring_leasing_balance", file: "outputs/factoring_leasing/factoring_leasing_balance_serie_ifrs_cmf.parquet" },
  { name: "factoring_leasing_resultados", file: "outputs/factoring_leasing/factoring_leasing_resultados_serie_ifrs_cmf.parquet" },
  // END AUTO FL IFRS SERIES VIEWS
  { name: "factoring_leasing_lista_entidades", file: "outputs/factoring_leasing/factoring_leasing_maestro.parquet" },

  // CORREDORAS DE BOLSA (CMF)
  { name: "corredoras_bolsa_lista_entidades_registro", file: "outputs/corredoras_bolsa/corredoras_bolsa_registro_universo.parquet" },
  { name: "corredoras_bolsa_lista_entidades", file: "outputs/corredoras_bolsa/corredoras_bolsa_maestro.parquet" },


   // SECURITIZADORAS (CMF / Ley 18.045) - Gestoras & Resumen
   { name: "securitizadoras_lista_entidades", file: "outputs/securitizadoras/securitizadoras_maestro.parquet" },
   { name: "patrimonios_separados_lista_entidades", file: "outputs/securitizadoras/patrimonios_separados_maestro.parquet" },
   { name: "patrimonios_separados_balance", file: "outputs/securitizadoras/patrimonios_separados_balance.parquet" },

  // COOPERATIVAS DE AHORRO Y CRÉDITO (CMF)
  { name: "cooperativas_lista_entidades", file: "outputs/cooperativas/cooperativas_maestro.parquet" },

  // CAJAS DE COMPENSACION (CCAF / SUSESO - Ley 18.833 / CMF)
  { name: "ccaf_lista_entidades", file: "outputs/cajas_compensacion/ccaf_maestro.parquet" },

  // ADMINISTRADORAS GENERALES DE FONDOS (AGF / Ley 20.712)
  { name: "agf_lista_entidades", file: "outputs/agf/agf_maestro.parquet" },
  { name: "agf_balance", manifest: "outputs/agf/agf_balance/manifest.json" },
  { name: "agf_resultados", manifest: "outputs/agf/agf_resultados/manifest.json" },
  { name: "securitizadoras_balance", manifest: "outputs/securitizadoras/securitizadoras_balance/manifest.json" },
  { name: "securitizadoras_resultados", manifest: "outputs/securitizadoras/securitizadoras_resultados/manifest.json" },
  { name: "ccaf_balance", manifest: "outputs/cajas_compensacion/ccaf_balance/manifest.json" },
  { name: "ccaf_resultados", manifest: "outputs/cajas_compensacion/ccaf_resultados/manifest.json" },
  { name: "corredoras_bolsa_balance", manifest: "outputs/corredoras_bolsa/corredoras_bolsa_balance/manifest.json" },
  { name: "corredoras_bolsa_resultados", manifest: "outputs/corredoras_bolsa/corredoras_bolsa_resultados/manifest.json" },

  // SISTEMAS DE PAGO (BCCh / CMF)
  { name: "sistemas_pago_lista_entidades", file: "outputs/sistemas_pago/sistemas_pago_maestro.parquet" },

  // FINTECH & FINANZAS ABIERTAS (LEY N° 21.521 / CMF)
  { name: "fintech_rpsf_lista_entidades", file: "outputs/fintech/fintech_rpsf_maestro.parquet" },
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
    this.engineSource = null;
    this.localEngineError = null;
    // Nombre del archivo (vista) -> motivo por el que no pudo crearse. Se
    // muestra en el diagnóstico para poder decir qué Parquet concreto falló.
    this.viewErrors = {};
    // Una conexión DuckDB-Wasm no admite dos runQuery simultáneos. La
    // inicialización crea muchas vistas y la interfaz también puede recibir
    // consultas concurrentes; mantener una cola aquí evita que los mensajes
    // Thrift se intercalen y terminen en TProtocolException: Invalid data.
    this.queryQueue = Promise.resolve();
    this.initPromise = this.init();
  }

  // Monta worker, base y conexión a partir de un bundle ya resuelto.
  async startEngine(duckdb, bundle) {
    const worker = await duckdb.createWorker(bundle.mainWorker);
    this.db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(), worker);
    await this.db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    this.conn = await this.db.connect();
  }

  // Comprueba si el entorno puede alojar un Web Worker creado desde un Blob URL.
  // El motor arma su worker así (ver createWorker en duckdb-browser.mjs), de modo
  // que un CSP que bloquee blob: o un iframe en sandbox sin allow-same-origin
  // impiden arrancarlo aunque los archivos estén disponibles.
  probeBlobWorker() {
    return new Promise((resolve) => {
      let url = null;
      try {
        url = URL.createObjectURL(new Blob(["self.onmessage=function(){self.postMessage('ok')};"], { type: "text/javascript" }));
        const worker = new Worker(url);
        const cerrar = (resultado) => {
          clearTimeout(temporizador);
          try { worker.terminate(); } catch (e) { /* ya cerrado */ }
          URL.revokeObjectURL(url);
          resolve(resultado);
        };
        const temporizador = setTimeout(() => cerrar({ ok: false, reason: "el worker no respondió en 2 s" }), 2000);
        worker.onmessage = () => cerrar({ ok: true, reason: null });
        worker.onerror = (evento) => cerrar({ ok: false, reason: (evento && evento.message) || "el worker emitió un error" });
        worker.postMessage("ping");
      } catch (err) {
        if (url) URL.revokeObjectURL(url);
        resolve({ ok: false, reason: err && err.message ? err.message : String(err) });
      }
    });
  }

  // Sonda del entorno: qué puede hacer este navegador. Se muestra en el
  // diagnóstico de la pestaña de consultas cuando el motor no arranca.
  async probeEnvironment() {
    const soporte = {
      wasm: typeof WebAssembly === "object",
      wasmExceptions: null,
      wasmSIMD: null,
      crossOriginIsolated: Boolean(window.crossOriginIsolated),
      blobWorker: null,
      blobWorkerError: null
    };
    if (this.duckdb && typeof this.duckdb.getPlatformFeatures === "function") {
      try {
        const features = await this.duckdb.getPlatformFeatures();
        soporte.wasmExceptions = Boolean(features.wasmExceptions);
        soporte.wasmSIMD = Boolean(features.wasmSIMD);
      } catch (e) { /* sonda opcional */ }
    }
    const worker = await this.probeBlobWorker();
    soporte.blobWorker = worker.ok;
    soporte.blobWorkerError = worker.reason;
    return soporte;
  }

  async init() {
    try {
      console.log("[DuckDB-Wasm] Inicializando motor WebAssembly...");
      this.engineAvailable = false;
      this.engineError = null;
      this.localEngineError = null;
      this.attempts = [];
      this.environment = null;
      this.unavailableViews = [];
      this.viewErrors = {};
      this.registeredFiles = new Set();
      this.db = null;
      this.conn = null;

      // Orden de intentos: copia local del repositorio y, si falla, CDNs públicos.
      const localBase = this.absoluteUrl(DUCKDB_LOCAL_DIR);
      const intentos = [{
        id: "local",
        label: "copia local del repositorio",
        mjs: `${localBase}duckdb-browser.mjs`,
        bundles: {
          eh: {
            mainModule: `${localBase}duckdb-eh.wasm`,
            mainWorker: `${localBase}duckdb-browser-eh.worker.js`
          }
        }
      }];
      for (const cdn of DUCKDB_CDN_BASES) {
        const base = cdn.dist;
        intentos.push({
          id: cdn.id,
          label: cdn.label,
          mjs: cdn.mjs,
          bundles: {
            eh: { mainModule: `${base}duckdb-eh.wasm`, mainWorker: `${base}duckdb-browser-eh.worker.js` },
            mvp: { mainModule: `${base}duckdb-mvp.wasm`, mainWorker: `${base}duckdb-browser-mvp.worker.js` }
          }
        });
      }

      for (const intento of intentos) {
        try {
          const modulo = await import(intento.mjs);
          this.duckdb = modulo;
          // selectBundle exige la entrada "mvp" cuando el navegador no soporta el
          // bundle "eh"; sin ella lanza un TypeError que no explica nada.
          if (!intento.bundles.mvp) {
            const respaldo = DUCKDB_CDN_BASES[0].dist;
            intento.bundles.mvp = {
              mainModule: `${respaldo}duckdb-mvp.wasm`,
              mainWorker: `${respaldo}duckdb-browser-mvp.worker.js`
            };
          }
          const bundle = await modulo.selectBundle(intento.bundles);
          await this.startEngine(modulo, bundle);
          this.engineSource = intento.id;
          this.engineSourceLabel = intento.label;
          break;
        } catch (error) {
          const motivo = error && error.message ? error.message : String(error);
          this.attempts.push({ id: intento.id, label: intento.label, error: motivo });
          if (intento.id === "local") this.localEngineError = motivo;
          console.warn(`[DuckDB-Wasm] Falló ${intento.label}: ${motivo}`);
          this.db = null;
          this.conn = null;
        }
      }

      if (!this.conn) {
        const detalle = this.attempts.map((a) => `${a.label}: ${a.error}`).join(" | ");
        throw new Error(detalle || "ninguna fuente del motor respondió");
      }

      await this.registerSemanticViews();
      this.engineAvailable = true;
      console.log(`[DuckDB-Wasm] Motor listo (${this.engineSourceLabel}): ${SEMANTIC_VIEWS.length - this.unavailableViews.length}/${SEMANTIC_VIEWS.length} vistas disponibles.`);
    } catch (e) {
      this.engineAvailable = false;
      this.engineError = e && e.message ? e.message : String(e);
      // Con el motor caído se sondea el entorno, para poder explicar la causa.
      try {
        this.environment = await this.probeEnvironment();
      } catch (err) {
        this.environment = null;
      }
      console.error("[DuckDB-Wasm] Motor no disponible; las consultas fallarán de forma explícita:", this.engineError);
    } finally {
      this.isReady = true;
      this.updateEngineBadge();
      if (typeof window.dispatchEvent === "function" && typeof CustomEvent === "function") {
        window.dispatchEvent(new CustomEvent("duckdb-ready", {
          detail: {
            available: this.engineAvailable,
            error: this.engineError,
            source: this.engineSource,
            sourceLabel: this.engineSourceLabel,
            localError: this.localEngineError,
            attempts: (this.attempts || []).slice(),
            environment: this.environment,
            unavailableViews: this.unavailableViews.slice(),
            viewErrors: { ...(this.viewErrors || {}) }
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
      badge.textContent = `DuckDB activo · ${this.unavailableViews.length} sin publicar`;
      badge.classList.add("offline");
      badge.title = this.unavailableViews.join(", ");
    } else {
      badge.textContent = "DuckDB sin conexión";
      badge.classList.add("offline");
      badge.title = this.engineError ? `Motor no disponible: ${this.engineError}` : "Motor no disponible";
    }
  }

  // Reintenta levantar el motor (por ejemplo, si la primera carga falló por red).
  async retry() {
    this.isReady = false;
    this.initPromise = this.init();
    return this.initPromise;
  }

  // Informe de texto para pegar en un issue cuando el motor no arranca.
  buildDiagnostics() {
    const lineas = [
      "Diagnostico DuckDB-Wasm - Sistema de Informacion Financiera de Chile",
      `Fecha: ${new Date().toISOString()}`,
      `Navegador: ${navigator.userAgent}`,
      `Motor disponible: ${this.engineAvailable ? "si (" + (this.engineSourceLabel || this.engineSource) + ")" : "no"}`,
      `Motivo final: ${this.engineError || "(sin error)"}`,
      "Intentos:"
    ];
    for (const intento of (this.attempts || [])) {
      lineas.push(`  - ${intento.label}: ${intento.error}`);
    }
    const entorno = this.environment;
    if (entorno) {
      const si = (valor) => (valor === null || valor === undefined) ? "sin dato" : (valor ? "si" : "no");
      lineas.push("Entorno:");
      lineas.push(`  - WebAssembly: ${si(entorno.wasm)}`);
      lineas.push(`  - WebAssembly exception handling: ${si(entorno.wasmExceptions)}`);
      lineas.push(`  - WebAssembly SIMD: ${si(entorno.wasmSIMD)}`);
      lineas.push(`  - Contexto aislado (crossOriginIsolated): ${si(entorno.crossOriginIsolated)}`);
      lineas.push(`  - Web Worker desde Blob URL: ${entorno.blobWorker === false ? "no (" + entorno.blobWorkerError + ")" : si(entorno.blobWorker)}`);
    }
    if ((this.unavailableViews || []).length) {
      lineas.push("Vistas no disponibles (el motor sigue activo para el resto):");
      for (const vista of this.unavailableViews) {
        const motivo = (this.viewErrors || {})[vista];
        lineas.push(`  - ${vista}${motivo ? ": " + motivo : ""}`);
      }
    }
    return lineas.join("\n");
  }


  absoluteUrl(relativePath) {
    return new URL(relativePath, document.baseURI).href;
  }

  // DuckDB-Wasm lee los Parquet con XHR síncronos de rango hechos desde el
  // worker. En Chrome/Edge sobre Windows, tras un recargo esas respuestas
  // pueden salir de la caché HTTP con bytes corridos y el parser Thrift de
  // Parquet muere con "TProtocolException: Invalid data" (duckdb/duckdb-wasm
  // issue #1658; Firefox y el modo incógnito no fallan). Un sufijo de URL
  // único por carga de página saca esas peticiones de la caché del navegador.
  // Se calcula perezosamente para que también funcione en instancias creadas
  // sin pasar por el constructor (arnés de scripts/audit_duckdb_client.js).
  sufijoAntiCache() {
    if (!this.httpCacheBuster) {
      this.httpCacheBuster = `cb=${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
    }
    return this.httpCacheBuster;
  }

  // Registra el Parquet en el sistema de archivos virtual de DuckDB-Wasm; sin
  // este paso las rutas relativas no existen para el motor y toda consulta falla.
  // La URL lleva el sufijo anti-caché: las lecturas de rango que hace el worker
  // (XHR síncrono) no deben reutilizarse de una carga anterior de la página.
  async registerFile(relativePath) {
    if (this.registeredFiles.has(relativePath)) return relativePath;
    const base = this.absoluteUrl(relativePath);
    const url = `${base}${base.includes("?") ? "&" : "?"}${this.sufijoAntiCache()}`;
    await this.db.registerFileURL(
      relativePath,
      url,
      this.duckdb.DuckDBDataProtocol.HTTP,
      false
    );
    this.registeredFiles.add(relativePath);
    return relativePath;
  }

  // Lista de archivos de una vista (manifiesto o fichero fijo). Se resuelve
  // fuera de las vistas para poder pedir todos los manifiestos a la vez: en
  // serie, el arranque pagaba un ida-y-vuelta de red por vista (30+ RTT).
  async prepararVista(view) {
    let files;
    if (view.manifest) {
      // no-store: el manifiesto es la lista de verdad de lo publicado; una
      // copia en caché haría que la vista no viera particiones nuevas.
      const response = await fetch(this.absoluteUrl(view.manifest), { cache: "no-store" });
      if (!response.ok) throw new Error(`Manifiesto HTTP ${response.status}: ${view.manifest}`);
      const manifest = await response.json();
      files = manifest.files;
      if (!Array.isArray(files) || files.length === 0) {
        throw new Error(`No hay particiones publicadas para ${view.name}`);
      }
    } else {
      files = Array.isArray(view.file) ? view.file : [view.file];
    }
    if (files.some((file) => typeof file !== "string" || file.startsWith("/") || file.split("/").includes(".."))) {
      throw new Error(`Ruta de partición no válida en ${view.name}`);
    }
    return { view, files };
  }

  // DuckDB-Wasm procesa una conexión de forma serial. Aunque el worker puede
  // recibir varios mensajes, dos conn.query() simultáneos sobre la misma
  // conexión pueden intercalar el protocolo Thrift y devolver "TProtocolException:
  // Invalid data". La cola conserva el paralelismo de la red y serializa sólo
  // la sección crítica del motor.
  runQuerySerial(sql) {
    if (!this.queryQueue) this.queryQueue = Promise.resolve();
    const siguiente = this.queryQueue.then(() => {
      if (!this.conn) throw new Error("La conexión DuckDB-Wasm no está disponible");
      return this.conn.query(sql);
    });
    // Una consulta fallida no debe bloquear las siguientes. El error original
    // sigue viajando por `siguiente` al llamador.
    this.queryQueue = siguiente.catch(() => undefined);
    return siguiente;
  }

  // Ejecuta `fn` sobre cada elemento con a lo sumo `max` en paralelo. Las
  // operaciones de base se serializan en runQuerySerial; este límite conserva
  // la concurrencia de la preparación/cola sin corromper el protocolo.
  async enTandas(lista, max, fn) {
    let i = 0;
    const workers = Array.from({ length: Math.min(max, lista.length) }, async () => {
      while (i < lista.length) {
        const actual = i++;
        await fn(lista[actual], actual);
      }
    });
    await Promise.all(workers);
  }

  async crearVista({ view, files }) {
    const safePath = (file) => file.replace(/'/g, "''");
    const source = files.length === 1
      ? `read_parquet('${safePath(files[0])}')`
      : `read_parquet([${files.map((f) => `'${safePath(f)}'`).join(", ")}])`;
    const filter = view.where ? ` WHERE ${view.where}` : "";
    await this.runQuerySerial(`CREATE OR REPLACE VIEW ${view.name} AS SELECT * FROM ${source}${filter};`);
    // Alias de compatibilidad: un nombre viejo nunca debe ocultar un error,
    // pero tampoco debe dejar sin datos a quien ya guardó una consulta.
    for (const alias of (LEGACY_VIEW_ALIASES[view.name] || [])) {
      try {
        await this.runQuerySerial(`CREATE OR REPLACE VIEW ${alias} AS SELECT * FROM ${view.name};`);
      } catch (errAlias) {
        console.warn(`[DuckDB-Wasm] No se pudo crear el alias ${alias}:`, errAlias);
      }
    }
  }

  async registerSemanticViews() {
    this.unavailableViews = [];
    if (!this.conn) return;

    // 1) Manifiestos y rutas, todo a la vez. El fallo de un manifiesto solo
    //    desactiva su vista, igual que antes.
    const preparadas = await Promise.all(
      SEMANTIC_VIEWS.map(async (view) => {
        try {
          const p = await this.prepararVista(view);
          return { ok: true, ...p };
        } catch (err) {
          this.unavailableViews.push(view.name);
          console.error(`[DuckDB-Wasm] Vista ${view.name} no disponible:`, err);
          return { ok: false };
        }
      })
    );
    const ok = preparadas.filter((p) => p.ok);

    // 2) Todos los ficheros del sistema a la vez (registerFileURL es idempotente
    //    y dos vistas pueden compartir particiones).
    const todos = [...new Set(ok.flatMap((p) => p.files))];
    await Promise.all(todos.map((file) => this.registerFile(file)));

    // 3) La preparación puede seguir en tandas, pero runQuerySerial mantiene
    //    una sola consulta activa por conexión; así no se corrompe el protocolo
    //    mientras conservamos el resto de la mejora de arranque. Un fallo al
    //    crear UNA vista (p.ej. un Parquet cuya lectura por red se corrompió)
    //    no debe tumbar el motor completo: esa vista queda como no disponible
    //    con su motivo y el resto del sistema sigue funcionando. Antes de
    //    rendirse se reintenta una vez: la corrupción de lectura del
    //    navegador (issue #1658 de duckdb-wasm) es intermitente y el segundo
    //    intento suele leer de la red.
    this.viewErrors = {};
    await this.enTandas(ok, 8, async (p) => {
      try {
        await this.crearVista(p);
      } catch (primerError) {
        const motivo = primerError && primerError.message ? primerError.message : String(primerError);
        console.warn(`[DuckDB-Wasm] Vista ${p.view.name} falló al crearse; se reintenta:`, motivo);
        try {
          await this.crearVista(p);
        } catch (segundoError) {
          const motivo2 = segundoError && segundoError.message ? segundoError.message : String(segundoError);
          this.unavailableViews.push(p.view.name);
          this.viewErrors[p.view.name] = motivo2;
          console.error(`[DuckDB-Wasm] Vista ${p.view.name} no disponible tras reintento:`, motivo2);
        }
      }
    });

    console.log(`[DuckDB-Wasm] Vistas registradas: ${SEMANTIC_VIEWS.length - this.unavailableViews.length}/${SEMANTIC_VIEWS.length}`);
    if (this.unavailableViews.length) {
      console.warn("[DuckDB-Wasm] Vistas no disponibles:", this.unavailableViews.join(", "));
    }
  }

  // El motor corre en memoria, dentro de la pestaña, sobre Parquet servidos por
  // HTTP: una consulta no puede tocar los archivos publicados ni el repositorio.
  // Pero sí puede alterar el catálogo de ESTA sesión (DROP VIEW, CREATE OR REPLACE
  // VIEW sobre una tabla real, INSERT en una tabla fabricada), y eso es grave
  // porque `checkUrlHash()` ejecuta lo que traiga el enlace. La guardia se aplica
  // aquí —único punto por donde pasa el SQL del visitante— y no en la terminal,
  // para que también cubra al visor de datos y a cualquier llamador futuro.
  revisarSoloLectura(sql) {
    if (typeof window === "undefined" || !window.SIFSqlGuard) return { ok: true, motivo: "" };
    try {
      return window.SIFSqlGuard.validar(sql);
    } catch (err) {
      // Una guardia que falla no debe abrir la puerta: se rechaza la consulta.
      return { ok: false, motivo: "No se pudo verificar la consulta y no se ejecuta por seguridad." };
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

    const revision = this.revisarSoloLectura(sql);
    if (!revision.ok) {
      return {
        success: false,
        bloqueada: true,
        error: revision.motivo,
        elapsedMs: (performance.now() - t0).toFixed(1)
      };
    }

    try {
      const result = await this.runQuerySerial(sql);
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
      const mensaje = err && err.message ? err.message : String(err);
      // Red de seguridad: si algo borró una vista del catálogo (DROP VIEW escrito
      // por el visitante, o un error nuestro), la recreamos y reintentamos una vez.
      // En el camino normal no cuesta nada: solo se mira el texto del error.
      const reparado = this.parecenFaltarVistas(mensaje) ? await this.repararVistas() : false;
      if (reparado) {
        try {
          const retry = await this.runQuerySerial(sql);
          const rows = retry.toArray().map((row) => {
            const obj = row.toJSON();
            for (const [k, v] of Object.entries(obj)) {
              if (typeof v === "bigint") obj[k] = Number(v);
            }
            return obj;
          });
          return {
            success: true, rows, columns: retry.schema.fields.map((f) => f.name),
            elapsedMs: (performance.now() - t0).toFixed(1), count: rows.length, vistasReparadas: true
          };
        } catch (segundo) {
          return {
            success: false,
            error: segundo && segundo.message ? segundo.message : String(segundo),
            elapsedMs: (performance.now() - t0).toFixed(1)
          };
        }
      }
      // El error real de SQL o de lectura de archivo se comunica tal cual.
      return {
        success: false,
        error: mensaje,
        elapsedMs: (performance.now() - t0).toFixed(1)
      };
    }
  }

  // ¿El error dice que falta un objeto del catálogo que podría ser una vista nuestra?
  parecenFaltarVistas(mensaje) {
    return /Catalog Error/i.test(mensaje) && /does not exist|not found|Unknown table/i.test(mensaje);
  }

  // Vuelve a crear las vistas semánticas y devuelve true si se pudo. Es la
  // reparación de una sesión dañada: no toca ningún archivo, solo el catálogo
  // en memoria de esta pestaña.
  async repararVistas() {
    if (!this.conn || typeof this.registerSemanticViews !== "function") return false;
    try {
      await this.registerSemanticViews();
      console.warn("[DuckDB-Wasm] Vistas restauradas tras un error de catálogo.");
      return true;
    } catch (err) {
      console.error("[DuckDB-Wasm] No se pudieron restaurar las vistas:", err);
      return false;
    }
  }
}

window.DuckDBClient = new DuckDBClient();
