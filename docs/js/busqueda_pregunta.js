/* Búsqueda por pregunta o concepto (punto 9).
 *
 * Carga outputs/indice_busqueda.json (generado por scripts/generar_indice_busqueda.py)
 * y ordena las tablas según qué tan bien responden a lo que escribe la persona:
 * conceptos y alias curados, nombre y descripción de la tabla, y nombres de columna.
 * Al elegir un resultado reutiliza el filtro del árbol de la barra lateral
 * (#sidebar-search), así no hay que duplicar la navegación.
 */
(function () {
  "use strict";

  const RUTA_INDICE = "outputs/indice_busqueda.json";
  const MAX_RESULTADOS = 8;
  // Palabras que no aportan a la búsqueda ("¿cuánto es la UF?" → "uf").
  const VACIAS = new Set([
    "a", "al", "como", "con", "cual", "cuales", "cuanto", "cuanta", "cuantos", "de", "del", "el", "en",
    "es", "esta", "la", "las", "lo", "los", "me", "mi", "para", "por", "que", "se", "si", "su",
    "sus", "un", "una", "unos", "y", "o", "hay", "dame", "quiero", "saber", "datos", "tabla", "tablas",
  ]);

  function normalizar(texto) {
    return String(texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[¿?¡!.,;:()]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function tokens(texto) {
    return normalizar(texto).split(" ").filter((t) => t.length > 1 && !VACIAS.has(t));
  }

  function escapar(texto) {
    return String(texto || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  // Puntúa una tabla para una consulta. Devuelve { puntos, motivos }.
  function puntuar(tabla, consulta, palabras) {
    let puntos = 0;
    const motivos = [];
    const q = normalizar(consulta);
    const terminos = (tabla.terminos || []).map(normalizar);
    const nombre = normalizar(tabla.nombre + " " + tabla.vista);
    const desc = normalizar(tabla.descripcion);

    // Coincidencia de frase: el concepto completo aparece en la consulta o al revés.
    for (const t of terminos) {
      if (!t) continue;
      if (q.includes(t) || (q.length > 3 && t.includes(q))) {
        puntos += 10;
        motivos.push(t);
        break;
      }
    }
    // Coincidencia por palabra con un término curado.
    const palabrasTerminos = new Set(terminos.flatMap((t) => t.split(" ")));
    for (const p of palabras) {
      if (palabrasTerminos.has(p)) {
        puntos += 4;
        if (!motivos.includes(p)) motivos.push(p);
      }
      if (nombre.includes(p)) puntos += 3;
      if (desc.includes(p)) puntos += 2;
    }
    // Columnas: se cuentan, pero con poco peso y con tope.
    const cols = (tabla.columnas || []).map((c) => normalizar(c.nombre + " " + c.significado));
    let colHits = 0;
    const colsCoincidentes = [];
    for (const p of palabras) {
      const hit = (tabla.columnas || []).find((c, i) => cols[i].includes(p));
      if (hit) {
        colHits += 1;
        colsCoincidentes.push(hit.nombre);
      }
    }
    puntos += Math.min(colHits, 3);
    // Los listados de entidades solo suben si la persona pregunta por entidades o registros;
    // si pregunta por un concepto ("fondos mutuos cartera"), primero van las tablas de datos.
    const pideEntidades = /entidad|lista|registro|institucion|administradora|sociedad|catalogo|maestro|nomina/.test(q);
    if (tabla.nombre.endsWith("lista_entidades") && !pideEntidades) puntos -= 4;
    return { puntos: Math.max(puntos, 0), motivos, columnas: [...new Set(colsCoincidentes)].slice(0, 3) };
  }

  // El vocabulario se construye una vez por índice, no en cada pulsación. La
  // corrección se limita a una edición, a palabras de 5+ letras y a candidatos
  // únicos: evita «adivinar» siglas cortas o consultas ambiguas.
  const VOCABULARIOS = new WeakMap();

  function vocabulario(indice) {
    if (VOCABULARIOS.has(indice)) return VOCABULARIOS.get(indice);
    const palabras = new Set();
    for (const tabla of indice.tablas || []) {
      const campos = [tabla.nombre, tabla.vista, tabla.descripcion, ...(tabla.terminos || [])];
      for (const columna of tabla.columnas || []) campos.push(columna.nombre, columna.significado);
      for (const campo of campos) {
        for (const palabra of tokens(campo)) {
          if (palabra.length >= 5 && /^[a-z]+$/.test(palabra)) palabras.add(palabra);
        }
      }
    }
    const porLongitud = new Map();
    for (const palabra of palabras) {
      if (!porLongitud.has(palabra.length)) porLongitud.set(palabra.length, []);
      porLongitud.get(palabra.length).push(palabra);
    }
    const resultado = { palabras, porLongitud };
    VOCABULARIOS.set(indice, resultado);
    return resultado;
  }

  // Distancia de edición acotada a una inserción, eliminación o sustitución.
  function distanciaUnaEdicion(a, b) {
    if (a === b) return true;
    if (Math.abs(a.length - b.length) > 1) return false;
    let i = 0, j = 0, diferencias = 0;
    while (i < a.length && j < b.length) {
      if (a[i] === b[j]) { i++; j++; continue; }
      if (++diferencias > 1) return false;
      if (a.length > b.length) i++;
      else if (b.length > a.length) j++;
      else { i++; j++; }
    }
    if (i < a.length || j < b.length) diferencias++;
    return diferencias <= 1;
  }

  function corregirPalabras(indice, palabras) {
    const vocab = vocabulario(indice);
    const correcciones = [];
    const corregidas = palabras.map((palabra) => {
      if (vocab.palabras.has(palabra) || palabra.length < 5 || !/^[a-z]+$/.test(palabra)) return palabra;
      const candidatas = [];
      for (let largo = palabra.length - 1; largo <= palabra.length + 1; largo++) {
        for (const candidata of vocab.porLongitud.get(largo) || []) {
          if (distanciaUnaEdicion(palabra, candidata)) candidatas.push(candidata);
        }
      }
      if (candidatas.length !== 1) return palabra;
      correcciones.push({ original: palabra, corregida: candidatas[0] });
      return candidatas[0];
    });
    return { palabras: corregidas, correcciones };
  }

  function buscar(indice, consulta) {
    const originales = [...new Set(tokens(consulta))];
    if (!originales.length && !normalizar(consulta)) return [];
    const { palabras, correcciones } = corregirPalabras(indice, originales);
    const mapaCorrecciones = new Map(correcciones.map((c) => [c.original, c.corregida]));
    const consultaAjustada = correcciones.length
      ? normalizar(consulta).split(" ").map((p) => mapaCorrecciones.get(p) || p).join(" ")
      : consulta;
    return indice.tablas
      .map((t) => ({ tabla: t, ...puntuar(t, consultaAjustada, palabras), correcciones }))
      .filter((r) => r.puntos > 0)
      .sort((a, b) => b.puntos - a.puntos || a.tabla.nombre.localeCompare(b.tabla.nombre))
      .slice(0, MAX_RESULTADOS);
  }

  function crearInterfaz() {
    const caja = document.querySelector(".sidebar-search-box");
    if (!caja || document.getElementById("pregunta-buscar")) return null;
    const bloque = document.createElement("div");
    bloque.className = "pregunta-buscar";
    bloque.innerHTML = `
      <label class="pregunta-etiqueta" for="pregunta-buscar">Buscar por pregunta o concepto</label>
      <input type="search" id="pregunta-buscar" autocomplete="off"
             placeholder="Ej.: inflación, dólar, fondos mutuos, patrimonio" aria-describedby="pregunta-estado">
      <div id="pregunta-estado" class="pregunta-estado" aria-live="polite"></div>
      <ul id="pregunta-resultados" class="pregunta-resultados" role="list"></ul>`;
    caja.insertAdjacentElement("afterend", bloque);
    return bloque;
  }

  function elegir(tabla) {
    const filtro = document.getElementById("sidebar-search");
    if (filtro) {
      filtro.value = tabla.nombre;
      filtro.dispatchEvent(new Event("input", { bubbles: true }));
      filtro.focus();
    }
  }

  function pintar(resultados, consulta, estado, lista) {
    if (!consulta.trim()) {
      estado.textContent = "";
      lista.innerHTML = "";
      return;
    }
    if (!resultados.length) {
      estado.textContent = "Sin resultados. Pruebe con otro concepto o con el nombre de la industria.";
      lista.innerHTML = "";
      return;
    }
    estado.textContent = `${resultados.length} resultado(s), ordenados por relevancia.`;
    lista.innerHTML = resultados.map((r, i) => {
      const t = r.tabla;
      const desc = (t.descripcion || "").length > 140 ? t.descripcion.slice(0, 137) + "…" : t.descripcion;
      const motivos = [];
      if (r.correcciones && r.correcciones.length) motivos.push("Coincidencia aproximada por escritura");
      if (r.motivos.length) motivos.push(`Coincide con: ${r.motivos.slice(0, 3).map(escapar).join(", ")}`);
      else if (r.columnas.length) motivos.push(`Columnas: ${r.columnas.map(escapar).join(", ")}`);
      const motivo = motivos.join(" · ");
      const formatos = Array.isArray(t.formatos) && t.formatos.length
        ? t.formatos.map((formato) => formato === "PARQUET" ? "Parquet" : formato).join(", ")
        : "sin archivo directo";
      return `<li class="pregunta-item">
        <button type="button" class="pregunta-boton" data-indice="${i}">
          <span class="pregunta-nombre">${escapar(t.nombre)}</span>
          <span class="pregunta-identificador">ID: ${escapar(t.id)}</span>
          <span class="pregunta-sector">${escapar(t.sectorLabel)}</span>
          <span class="pregunta-metadatos">
            <span>Fuente: ${escapar(t.fuente)}</span>
            <span>Cobertura: ${escapar(t.corte)}</span>
            <span>Archivo: ${escapar(formatos)}</span>
          </span>
          <span class="pregunta-desc">${escapar(desc)}</span>
          ${motivo ? `<span class="pregunta-motivo">${motivo}</span>` : ""}
          <span class="pregunta-accion">Seleccionar en el explorador →</span>
        </button>
      </li>`;
    }).join("");
    lista.querySelectorAll(".pregunta-boton").forEach((b) => {
      b.addEventListener("click", () => elegir(resultados[Number(b.dataset.indice)].tabla));
    });
  }

  async function iniciar() {
    const bloque = crearInterfaz();
    if (!bloque) return;
    const entrada = document.getElementById("pregunta-buscar");
    const estado = document.getElementById("pregunta-estado");
    const lista = document.getElementById("pregunta-resultados");

    let indice;
    try {
      // Descarga ya iniciada por el <head> (window.SIF_JSON); si no está, se pide aquí.
      if (window.SIF_JSON && window.SIF_JSON.indice) {
        indice = await window.SIF_JSON.indice;
      } else {
        const respuesta = await fetch(RUTA_INDICE, { cache: "force-cache" });
        if (!respuesta.ok) throw new Error("HTTP " + respuesta.status);
        indice = await respuesta.json();
      }
    } catch (e) {
      estado.textContent = "No se pudo cargar el índice de búsqueda (" + e.message + "). El filtro por nombre de tabla sigue disponible.";
      entrada.disabled = true;
      return;
    }

    entrada.addEventListener("input", () => {
      pintar(buscar(indice, entrada.value), entrada.value, estado, lista);
    });
    entrada.addEventListener("keydown", (ev) => {
      if (ev.key === "ArrowDown") {
        const primero = lista.querySelector(".pregunta-boton");
        if (primero) {
          ev.preventDefault();
          primero.focus();
        }
      } else if (ev.key === "Enter") {
        const primero = buscar(indice, entrada.value)[0];
        if (primero) elegir(primero.tabla);
      }
    });
    lista.addEventListener("keydown", (ev) => {
      const botones = [...lista.querySelectorAll(".pregunta-boton")];
      const botonActual = ev.target.closest(".pregunta-boton");
      const actual = botones.indexOf(botonActual);
      if (actual < 0) return;
      if (ev.key === "Escape") {
        ev.preventDefault();
        entrada.focus();
      } else if (ev.key === "ArrowDown" && actual < botones.length - 1) {
        ev.preventDefault();
        botones[actual + 1].focus();
      } else if (ev.key === "ArrowUp") {
        ev.preventDefault();
        if (actual > 0) botones[actual - 1].focus();
        else entrada.focus();
      } else if (ev.key === "Home") {
        ev.preventDefault();
        botones[0].focus();
      } else if (ev.key === "End") {
        ev.preventDefault();
        botones[botones.length - 1].focus();
      }
    });
  }

  if (typeof window !== "undefined") {
    window.busquedaPregunta = { normalizar, tokens, puntuar, buscar };
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", iniciar);
    } else {
      iniciar();
    }
  }
})();
