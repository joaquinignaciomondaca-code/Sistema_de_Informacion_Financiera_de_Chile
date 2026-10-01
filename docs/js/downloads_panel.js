/**
 * Pestaña Descargas
 * Sistema de Información Financiera de Chile
 *
 * Reemplaza al antiguo modal de exportación: en vez de elegir a ciegas dentro de
 * una ventana, aquí está todo el catálogo publicado a la vista (filas, peso,
 * periodo y archivos de cada conjunto) y cada fila trae su propia acción:
 * Parquet original, CSV, Excel o consulta SQL.
 */
class DownloadsPanelController {
  constructor() {
    this.container = null;
    this.catalogo = window.DOWNLOAD_CATALOG || { grupos: [], conjuntos: 0, filas: 0, bytes: 0, generado: null };
    this.contexto = null; // { viewName, displayName, rows, columns }
    this.busqueda = "";
    this.sector = "todos";
    this.recorte = { activo: false, desde: null, hasta: null };
    this.abiertos = new Set();
    this.ocupado = false;
    this.iniciado = false;
  }

  /* ── Arranque ─────────────────────────────────────────────────────────── */

  init() {
    if (this.iniciado) return;
    this.container = document.getElementById("downloads-container");
    if (!this.container) return;
    this.iniciado = true;
    this.montar();
    this.aplicarFiltros();
    this.refrescarEstadoMotor();
    window.addEventListener("duckdb-ready", () => this.refrescarEstadoMotor());
  }

  render() {
    if (!this.iniciado) this.init();
  }

  /* ── Catálogo de apoyo ────────────────────────────────────────────────── */

  items() {
    if (!this._items) {
      this._items = [];
      (this.catalogo.grupos || []).forEach((grupo) => {
        (grupo.items || []).forEach((item) => {
          item.grupo = grupo.grupo;
          item.sector = grupo.sector || grupo.grupo;
          this._items.push(item);
        });
      });
    }
    return this._items;
  }

  item(id) {
    return this.items().find((x) => x.id === id) || null;
  }

  sectores() {
    return Array.from(new Set(this.items().map((x) => x.sector))).sort((a, b) => a.localeCompare(b, "es"));
  }

  anos() {
    const desde = [];
    const hasta = [];
    this.items().forEach((item) => {
      if (item.periodo && item.periodo.desde) desde.push(item.periodo.desde.slice(0, 4));
      if (item.periodo && item.periodo.hasta) hasta.push(item.periodo.hasta.slice(0, 4));
    });
    return {
      min: desde.length ? Number(desde.sort()[0]) : new Date().getFullYear() - 10,
      max: hasta.length ? Number(hasta.sort().slice(-1)[0]) : new Date().getFullYear()
    };
  }

  /* ── Montaje del panel ────────────────────────────────────────────────── */

  montar() {
    const anios = this.anos();
    const opciones = [];
    for (let a = anios.max; a >= anios.min; a -= 1) opciones.push(a);
    const opcionesHtml = opciones.map((a) => `<option value="${a}">${a}</option>`).join("");
    const sectoresHtml = this.sectores()
      .map((s) => `<option value="${this.escapar(s)}">${this.escapar(s)}</option>`)
      .join("");

    this.container.innerHTML = `
      <div class="dl-shell">
        <header class="dl-hero">
          <div class="dl-hero-text">
            <h2 id="dl-title">Descargas</h2>
            <p>
              Todo lo publicado por el sistema, en un solo lugar. Cada conjunto muestra cuántas filas,
              qué periodo y cuánto pesa <b>antes</b> de descargar. El Parquet original se baja directo
              desde este servidor; CSV y Excel se arman con el motor que corre en tu navegador.
            </p>
          </div>
          <div class="dl-hero-stats">
            <div class="dl-stat"><b>${window.MFCDownload.numero(this.catalogo.conjuntos)}</b><span>conjuntos</span></div>
            <div class="dl-stat"><b>${window.MFCDownload.numero(this.catalogo.filas)}</b><span>filas</span></div>
            <div class="dl-stat"><b>${window.MFCDownload.bytes(this.catalogo.bytes)}</b><span>Parquet</span></div>
          </div>
        </header>

        <section class="dl-context" id="dl-context" hidden aria-live="polite"></section>

        <section class="dl-catalog" aria-labelledby="dl-title">
          <div class="dl-toolbar">
            <div class="dl-search-wrap">
              <input type="search" id="dl-search" autocomplete="off" placeholder="Buscar conjunto, tabla o sector…" aria-label="Buscar conjunto de datos">
            </div>
            <select id="dl-sector" aria-label="Filtrar por sector">
              <option value="todos">Todos los sectores</option>
              ${sectoresHtml}
            </select>
            <div class="dl-years">
              <label class="dl-years-toggle">
                <input type="checkbox" id="dl-years-on"> Recortar series por años
              </label>
              <select id="dl-year-from" aria-label="Año inicial" disabled>${opcionesHtml}</select>
              <span class="dl-years-sep">a</span>
              <select id="dl-year-to" aria-label="Año final" disabled>${opcionesHtml}</select>
            </div>
            <span class="dl-counter" id="dl-counter"></span>
          </div>

          <div class="dl-groups" id="dl-groups"></div>
          <div class="dl-empty" id="dl-vacio" hidden>
            <b>Sin resultados.</b>
            <span>Prueba con el nombre de la tabla (por ejemplo <code>seguros_renta_fija</code>) o quita los filtros.</span>
          </div>
        </section>

        <footer class="dl-notas">
          <b>Cómo leer esta pestaña.</b>
          <span><b>Parquet</b> es el archivo tal como se publica: liviano, sin truncamientos y listo para Python, DuckDB, Power BI o R.
          <b>CSV</b> y <b>Excel</b> se generan en tu navegador a partir de la vista publicada; si el volumen supera las 250.000 filas se entrega un .ZIP
          con partes manejables. Los conteos de filas provienen de los manifiestos publicados junto a los datos.</span>
        </footer>
      </div>
    `;

    this.controles = {
      search: this.container.querySelector("#dl-search"),
      sector: this.container.querySelector("#dl-sector"),
      yearsOn: this.container.querySelector("#dl-years-on"),
      yearFrom: this.container.querySelector("#dl-year-from"),
      yearTo: this.container.querySelector("#dl-year-to"),
      counter: this.container.querySelector("#dl-counter"),
      groups: this.container.querySelector("#dl-groups"),
      vacio: this.container.querySelector("#dl-vacio"),
      context: this.container.querySelector("#dl-context")
    };
    this.controles.yearFrom.value = String(this.anos().min);
    this.controles.yearTo.value = String(this.anos().max);

    this.pintarGrupos();
    this.bind();
  }

  pintarGrupos() {
    const html = (this.catalogo.grupos || [])
      .map((grupo) => {
        const filas = grupo.items.reduce((acc, i) => acc + (i.filas || 0), 0);
        const peso = grupo.items.reduce((acc, i) => acc + (i.bytes || 0), 0);
        const tarjetas = grupo.items.map((item) => this.tarjeta(item)).join("");
        return `
          <section class="dl-group" data-grupo="${this.escapar(grupo.grupo)}">
            <div class="dl-group-head">
              <span class="dl-group-name">${this.escapar(grupo.grupo)}</span>
              <span class="dl-group-meta">${grupo.items.length} conjunto(s) · ${window.MFCDownload.numero(filas)} filas · ${window.MFCDownload.bytes(peso)}</span>
            </div>
            <div class="dl-items">${tarjetas}</div>
          </section>
        `;
      })
      .join("");
    this.controles.groups.innerHTML = html;
  }

  tarjeta(item) {
    const filas = item.filas === null || item.filas === undefined
      ? "filas: se cuentan al consultar"
      : `${window.MFCDownload.numero(item.filas)} filas`;
    const archivos = item.archivosN === 1 ? "1 archivo" : `${item.archivosN} archivos`;
    const periodo = item.periodo ? `${item.periodo.desde} → ${item.periodo.hasta}` : "sin desglose por periodo";
    const etiquetas = [];
    if (item.detalle) etiquetas.push(`<span class="dl-tag" title="${this.escapar(item.descripcion || item.detalle)}">${this.escapar(item.detalle)}</span>`);
    if (item.unificado) etiquetas.push(`<span class="dl-tag dl-tag-info" title="Esta vista une varios archivos publicados y aplica un filtro; el Parquet original baja los archivos completos.">Serie unificada</span>`);

    const botonParquet = item.archivosN === 1
      ? `<a class="dl-btn dl-btn-primary" data-action="parquet" data-id="${item.id}" href="${item.archivos[0].ruta}" download="${item.id}.parquet">
           Parquet · ${window.MFCDownload.bytes(item.bytes)}
         </a>`
      : `<button class="dl-btn dl-btn-primary" data-action="files" data-id="${item.id}" aria-expanded="${this.abiertos.has(item.id) ? "true" : "false"}">
           Archivos · ${window.MFCDownload.bytes(item.bytes)}
         </button>`;

    return `
      <article class="dl-item" data-id="${item.id}" data-sector="${this.escapar(item.sector)}"
               data-buscar="${this.escapar((item.id + " " + item.nombre + " " + item.detalle + " " + item.grupo).toLowerCase())}">
        <div class="dl-item-main">
          <div class="dl-item-title">
            <code>${this.escapar(item.nombre)}</code>
            ${etiquetas.join("")}
          </div>
          <div class="dl-item-detail" title="${this.escapar(item.descripcion || "")}">
            ${this.escapar(item.descripcion || "")}${item.descripcion ? " · " : ""}${filas} · ${archivos} · ${periodo}
          </div>
        </div>
        <div class="dl-item-actions">
          ${this.selectorFrecuencia(item)}
          ${botonParquet}
          <button class="dl-btn dl-btn-motor" data-action="csv" data-id="${item.id}" title="Genera el CSV completo con el motor DuckDB del navegador">CSV</button>
          <button class="dl-btn dl-btn-motor" data-action="xlsx" data-id="${item.id}" title="Genera un Excel (.xlsx) con el motor DuckDB del navegador">Excel</button>
          <button class="dl-btn dl-btn-ghost" data-action="sql" data-id="${item.id}" title="Abrir esta tabla en Consultas SQL">SQL</button>
        </div>
        <div class="dl-files" data-files="${item.id}" ${this.abiertos.has(item.id) ? "" : "hidden"}>
          ${this.listaArchivos(item)}
        </div>
      </article>
    `;
  }

  listaArchivos(item) {
    const filas = item.archivos
      .map((a) => {
        const etiqueta = a.periodo || a.ruta.split("/").slice(-2).join("/");
        return `<a class="dl-file" href="${a.ruta}" download>
          <span class="dl-file-name">${this.escapar(etiqueta)}</span>
          <span class="dl-file-size">${window.MFCDownload.bytes(a.bytes)}</span>
        </a>`;
      })
      .join("");
    return `<div class="dl-files-head">Archivos Parquet publicados (${item.archivosN}) · se descargan sueltos, uno por periodo</div>${filas}`;
  }

  /* ── Bloque "lo que estás viendo" ─────────────────────────────────────── */

  setContexto(contexto) {
    if (!contexto || !contexto.viewName) return;
    const filas = Array.isArray(contexto.rows) ? contexto.rows : [];
    const columnas = Array.isArray(contexto.columns) ? contexto.columns : [];
    this.contexto = {
      viewName: contexto.viewName,
      displayName: contexto.displayName || contexto.viewName,
      rows: filas,
      columns: columnas,
      origen: contexto.origen || "visor"
    };
    this.pintarContexto();
  }

  pintarContexto() {
    if (!this.controles || !this.controles.context) return;
    const ctx = this.contexto;
    if (!ctx) {
      this.controles.context.hidden = true;
      this.controles.context.innerHTML = "";
      return;
    }
    const item = this.item(ctx.viewName);
    const parquet = item && item.archivosN === 1
      ? `<a class="dl-btn dl-btn-ghost" href="${item.archivos[0].ruta}" download="${item.id}.parquet">Parquet original · ${window.MFCDownload.bytes(item.bytes)}</a>`
      : "";
    const enPantalla = ctx.rows.length
      ? `${window.MFCDownload.numero(ctx.rows.length)} ${ctx.rows.length === 1 ? "fila" : "filas"} en pantalla · ` +
        `${window.MFCDownload.numero(ctx.columns.length)} ${ctx.columns.length === 1 ? "columna" : "columnas"}`
      : "sin filas cargadas en pantalla";

    this.controles.context.hidden = false;
    this.controles.context.innerHTML = `
      <div class="dl-context-card">
        <div class="dl-context-head">
          <span class="dl-context-kicker">${ctx.origen === "sql" ? "Resultado en Consultas SQL" : "Tabla activa en el visor"}</span>
          <b class="dl-context-name">${this.escapar(ctx.displayName)}</b>
          <span class="dl-context-meta">${enPantalla}</span>
        </div>
        <div class="dl-context-actions">
          <button class="dl-btn dl-btn-primary" data-action="pantalla" data-fmt="csv">Descargar pantalla · CSV</button>
          <button class="dl-btn" data-action="pantalla" data-fmt="xlsx">Excel</button>
          ${parquet}
          ${item ? `<button class="dl-btn dl-btn-ghost" data-action="csv" data-id="${item.id}">Serie completa · CSV</button>` : ""}
        </div>
      </div>
    `;
  }

  /* ── Interacción ──────────────────────────────────────────────────────── */

  bind() {
    if (this._bind) return;
    this._bind = true;

    this.controles.search.addEventListener("input", (e) => {
      this.busqueda = e.target.value.trim().toLowerCase();
      this.aplicarFiltros();
    });
    this.controles.sector.addEventListener("change", (e) => {
      this.sector = e.target.value;
      this.aplicarFiltros();
    });
    const recorte = () => {
      this.recorte = {
        activo: this.controles.yearsOn.checked,
        desde: Number(this.controles.yearFrom.value),
        hasta: Number(this.controles.yearTo.value)
      };
      this.controles.yearFrom.disabled = !this.recorte.activo;
      this.controles.yearTo.disabled = !this.recorte.activo;
      this.aplicarFiltros();
    };
    this.controles.yearsOn.addEventListener("change", recorte);
    this.controles.yearFrom.addEventListener("change", recorte);
    this.controles.yearTo.addEventListener("change", recorte);

    this.container.addEventListener("change", (e) => {
      const sel = e.target.closest("select[data-freq]");
      if (!sel) return;
      if (!this.frecuencias) this.frecuencias = new Map();
      this.frecuencias.set(sel.dataset.freq, sel.value);
    });
    this.container.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-action]");
      if (!boton) return;
      const accion = boton.dataset.action;
      const id = boton.dataset.id;
      if (accion === "files") {
        this.alternarArchivos(id, boton);
      } else if (accion === "pantalla") {
        this.descargarPantalla(boton.dataset.fmt, boton);
      } else if (accion === "csv" || accion === "xlsx") {
        this.exportarSerie(id, accion, boton);
      } else if (accion === "sql") {
        this.abrirEnSql(id);
      }
    });
  }

  alternarArchivos(id, boton) {
    const bloque = this.container.querySelector(`[data-files="${id}"]`);
    if (!bloque) return;
    const abierto = bloque.hasAttribute("hidden");
    if (abierto) {
      bloque.removeAttribute("hidden");
      this.abiertos.add(id);
    } else {
      bloque.setAttribute("hidden", "");
      this.abiertos.delete(id);
    }
    boton.setAttribute("aria-expanded", abierto ? "true" : "false");
  }

  aplicarFiltros() {
    if (!this.controles) return;
    const q = this.busqueda;
    let visibles = 0;
    const grupos = this.container.querySelectorAll(".dl-group");
    grupos.forEach((grupo) => {
      let enGrupo = 0;
      grupo.querySelectorAll(".dl-item").forEach((fila) => {
        const coincideTexto = !q || fila.dataset.buscar.includes(q);
        const coincideSector = this.sector === "todos" || fila.dataset.sector === this.sector;
        const visible = coincideTexto && coincideSector;
        fila.hidden = !visible;
        if (visible) {
          enGrupo += 1;
          visibles += 1;
        }
      });
      grupo.hidden = enGrupo === 0;
    });
    if (this.controles.vacio) this.controles.vacio.hidden = visibles > 0;
    if (this.controles.counter) {
      const total = this.items().length;
      const partes = [`${window.MFCDownload.numero(visibles)} de ${window.MFCDownload.numero(total)} conjuntos`];
      if (this.recorte.activo) partes.push(`recorte ${this.recorte.desde}–${this.recorte.hasta}`);
      this.controles.counter.textContent = partes.join(" · ");
    }
    this.refrescarEstadoMotor();
  }

  refrescarEstadoMotor() {
    if (!this.controles) return;
    const motor = window.DuckDBClient;
    const disponible = Boolean(motor && motor.engineAvailable);
    const sinPublicar = (motor && Array.isArray(motor.unavailableViews)) ? motor.unavailableViews : [];
    this.container.querySelectorAll(".dl-btn-motor").forEach((boton) => {
      const item = this.item(boton.dataset.id);
      const bloqueado = !disponible || (item && sinPublicar.includes(item.id));
      boton.classList.toggle("dl-btn-off", bloqueado);
      boton.disabled = Boolean(item && sinPublicar.includes(item.id));
      boton.title = bloqueado
        ? (disponible
          ? "Esta vista no se pudo publicar en el motor de consulta. Baja el Parquet original."
          : "El motor de consulta no está disponible aquí. Puedes bajar el Parquet original o exportar lo que ves en pantalla.")
        : `Descargar ${boton.textContent.trim()} de la serie completa (motor DuckDB en tu navegador)`;
    });
    this.container.querySelectorAll(".dl-item").forEach((fila) => {
      const noPublicada = sinPublicar.includes(fila.dataset.id);
      fila.classList.toggle("dl-item-warn", noPublicada);
    });
  }

  /* ── Descargas ────────────────────────────────────────────────────────── */

  async descargarPantalla(formato, boton) {
    const ctx = this.contexto;
    if (!ctx || !ctx.rows.length) {
      this.avisar("No hay filas en pantalla para exportar. Abre el Visor con la tabla que quieras o usa la serie completa.");
      return;
    }
    await this.conBoton(boton, async () => {
      const resumen = await window.MFCDownload.exportarFilas(ctx.rows, ctx.columns, {
        formato,
        nombre: `${ctx.viewName}_pantalla`,
        particionar: false
      });
      this.avisar(`Descarga lista: ${window.MFCDownload.numero(resumen.filas)} filas en ${formato === "csv" ? "CSV" : "Excel"}.`);
    });
  }

  /* Tablas macro diarias: el CSV/Excel puede bajarse en frecuencia diaria o mensual.
     En mensual, cada columna toma el valor del último día del mes con dato
     (cierre de mes) y se informa esa fecha. */
  esDiaria(item) {
    return item && item.id.startsWith("macro_") && /por d[ií]a/i.test(item.cobertura || "");
  }

  frecuenciaDe(id) {
    return (this.frecuencias && this.frecuencias.get(id)) || "diaria";
  }

  selectorFrecuencia(item) {
    if (!this.esDiaria(item)) return "";
    const actual = this.frecuenciaDe(item.id);
    return `
      <label class="dl-freq" title="Frecuencia del CSV/Excel. Mensual: valor del último día de cada mes con dato (cierre). El Parquet original siempre es diario.">
        <span class="dl-freq-label">Frecuencia</span>
        <select class="dl-freq-select" data-freq="${item.id}">
          <option value="diaria" ${actual === "diaria" ? "selected" : ""}>Diaria</option>
          <option value="mensual" ${actual === "mensual" ? "selected" : ""}>Mensual · cierre</option>
        </select>
      </label>`;
  }

  async columnasIndicador(item) {
    const motor = window.DuckDBClient;
    const res = await motor.query(`SELECT column_name FROM information_schema.columns WHERE table_name = '${item.id}' ORDER BY ordinal_position`);
    if (!res || !res.success) throw new Error((res && res.error) || "No se pudieron leer las columnas de la tabla.");
    return (res.rows || [])
      .map((r) => (Array.isArray(r) ? r[0] : r.column_name))
      .filter((c) => c !== "fecha" && c !== "periodo");
  }

  filtroRecorte(item) {
    if (this.recorte.activo && item.periodo) {
      return ` WHERE periodo >= '${this.recorte.desde}-01' AND periodo <= '${this.recorte.hasta}-12'`;
    }
    return "";
  }

  sqlSerie(item) {
    return `SELECT * FROM ${item.id}` + this.filtroRecorte(item);
  }

  sqlSerieMensual(item, columnas) {
    const partes = columnas.flatMap((c) => [
      `arg_max(${c}, fecha) FILTER (WHERE ${c} IS NOT NULL) AS ${c}`,
      `max(fecha) FILTER (WHERE ${c} IS NOT NULL) AS ${c}_fecha_dato`
    ]);
    return `SELECT periodo, ${partes.join(", ")} FROM ${item.id}${this.filtroRecorte(item)} GROUP BY periodo ORDER BY periodo`;
  }

  async exportarSerie(id, formato, boton) {
    const item = this.item(id);
    if (!item) return;
    const motor = window.DuckDBClient;
    if (!motor || typeof motor.query !== "function" || !motor.engineAvailable) {
      this.avisar("El motor de consulta no está disponible en este navegador. Puedes bajar el Parquet original o exportar lo que ves en pantalla.");
      return;
    }
    const mensual = this.esDiaria(item) && this.frecuenciaDe(item.id) === "mensual";
    let sql = this.sqlSerie(item);
    if (mensual) {
      try {
        sql = this.sqlSerieMensual(item, await this.columnasIndicador(item));
      } catch (err) {
        this.avisar("No se pudo preparar la versión mensual: " + (err && err.message ? err.message : err));
        return;
      }
    }
    const nombreArchivo = mensual ? `${item.id}_mensual_cierre` : item.id;
    const estimado = mensual ? 0 : (item.filas || 0);
    if (estimado > 600000) {
      const seguir = window.confirm(
        `Vista ${item.id}: ${window.MFCDownload.numero(estimado)} filas.\n\n` +
        "Generar el archivo en el navegador puede tardar y consumir bastante memoria. " +
        "El Parquet original es más rápido y pesa menos.\n\n¿Continuar con la descarga?"
      );
      if (!seguir) return;
    }
    await this.conBoton(boton, async () => {
      this.avisar(`Consultando ${item.id}…`, 4000);
      const res = await motor.query(sql);
      if (!res || !res.success) {
        throw new Error((res && res.error) || "El motor devolvió una respuesta inválida.");
      }
      const filas = res.rows || [];
      if (!filas.length) throw new Error("La consulta no devolvió filas (revisa el recorte de años).");
      const resumen = await window.MFCDownload.exportarFilas(filas, res.columns || [], {
        formato,
        nombre: nombreArchivo,
        particionar: true
      });
      this.avisar(
        `Listo: ${window.MFCDownload.numero(resumen.filas)} ${mensual ? "meses (cierre)" : "filas"} en ` +
        (resumen.comprimido ? `${resumen.archivos} partes .ZIP` : formato === "csv" ? "CSV" : "Excel") + "."
      );
    });
  }

  abrirEnSql(id) {
    const sql = `SELECT * FROM ${id} LIMIT 100;`;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(sql).catch(() => {});
    }
    if (window.switchMainTab) window.switchMainTab("sql");
    if (window.ChatTerminal && window.ChatTerminal.setQueryInput) {
      window.ChatTerminal.setQueryInput(sql, id);
    } else {
      this.avisar("Consulta copiada: " + sql);
    }
  }

  /* ── Apoyo ────────────────────────────────────────────────────────────── */

  async conBoton(boton, tarea) {
    if (this.ocupado) return;
    this.ocupado = true;
    const textoOriginal = boton ? boton.textContent : "";
    if (boton) {
      boton.disabled = true;
      boton.classList.add("dl-btn-busy");
      boton.textContent = "Preparando…";
    }
    try {
      await tarea();
    } catch (err) {
      console.error("[Descargas]", err);
      this.avisar(`No se pudo completar la descarga: ${err.message}`, 5000);
    } finally {
      this.ocupado = false;
      if (boton) {
        boton.disabled = false;
        boton.classList.remove("dl-btn-busy");
        boton.textContent = textoOriginal;
      }
    }
  }

  avisar(texto, duracion) {
    if (window.MFCUI && window.MFCUI.toast) {
      window.MFCUI.toast(texto, "info", duracion);
    } else if (window.ChatTerminal && window.ChatTerminal.showToast) {
      window.ChatTerminal.showToast(texto);
    } else {
      console.log("[Descargas]", texto);
    }
  }

  escapar(texto) {
    return String(texto === null || texto === undefined ? "" : texto).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }
}

window.DownloadsPanel = new DownloadsPanelController();
document.addEventListener("DOMContentLoaded", () => {
  window.DownloadsPanel.init();
});
