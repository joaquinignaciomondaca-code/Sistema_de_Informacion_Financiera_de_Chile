/**
 * Terminal SQL (pestaña "Consultas SQL")
 * Sistema de Información Financiera de Chile
 * Soporte DuckDB-Wasm, gráficos Canvas 2D interactivos, enlaces compartibles,
 * consultas favoritas en localStorage y formato financiero chileno ($CLP, %, UF).
 * La pestaña ocupa el panel completo: ya no existe panel inferior ni splitter.
 * Cero emojis.
 */

class ChatTerminalController {
  constructor() {
    this.messagesContainer = document.getElementById("chat-messages");
    this.input = document.getElementById("chat-input");
    this.sendBtn = document.getElementById("send-btn");
    this.chipsContainer = document.querySelector(".quick-chips");
    this.defaultChipsHTML = this.chipsContainer ? this.chipsContainer.innerHTML : "";

    // Historial tipo consola (flechas arriba/abajo)
    this.history = [];
    this.historyIndex = -1;
    this.lastExecutedQuery = "";
    this.resultsMap = {};

    this.initEvents();
    this.initFavoritesModal();
    this.showWelcomeMessage();
    this.checkUrlHash();
  }

  initEvents() {
    this.sendBtn.addEventListener("click", () => this.handleSend());

    this.input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.handleSend();
      } else if (e.key === "Tab") {
        e.preventDefault();
        this.completeInput();
      } else if (e.key === "ArrowUp") {
        if (this.historyIndex > 0) {
          this.historyIndex--;
          this.input.value = this.history[this.historyIndex];
        }
      } else if (e.key === "ArrowDown") {
        if (this.historyIndex < this.history.length - 1) {
          this.historyIndex++;
          this.input.value = this.history[this.historyIndex];
        } else {
          this.historyIndex = this.history.length;
          this.input.value = "";
        }
      }
    });

    // Chips de sugerencias rápidas
    document.querySelectorAll(".chip").forEach((chip) => {
      chip.addEventListener("click", (e) => {
        const query = e.currentTarget.dataset.query;
        if (query) {
          this.input.value = query;
          this.handleSend();
        }
      });
    });

    // Cerrar modal de esquema
    const closeBtn = document.getElementById("close-schema-modal");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        document.getElementById("schema-modal").classList.remove("visible");
      });
    }

    // Compartir Link directo por URL Hash
    const shareBtn = document.getElementById("btn-share-query");
    if (shareBtn) {
      shareBtn.addEventListener("click", () => {
        const sqlToShare = this.lastExecutedQuery || this.input.value.trim();
        if (!sqlToShare) {
          this.addSystemMessage("Escribe o ejecuta una consulta antes de compartir el enlace.");
          return;
        }
        const url = new URL(window.location.href);
        url.hash = `sql=${encodeURIComponent(sqlToShare)}`;
        navigator.clipboard.writeText(url.href).then(() => {
          this.addSystemMessage(`Enlace directo copiado al portapapeles: <code>${this.escapeHtml(url.hash)}</code>`);
          if (window.MFCUI) window.MFCUI.toast("Enlace con la consulta copiado", "ok");
        }).catch(() => {
          window.location.hash = `sql=${encodeURIComponent(sqlToShare)}`;
          this.addSystemMessage(`URL actualizada en la barra del navegador.`);
        });
      });
    }

    // Limpiar la conversación de la sesión (no toca las consultas guardadas)
    const clearBtn = document.getElementById("btn-clear-terminal");
    if (clearBtn) {
      clearBtn.addEventListener("click", () => this.clearTerminal());
    }

    // Botón para desplegar Favoritas
    const favBtn = document.getElementById("btn-show-favorites");
    if (favBtn) {
      favBtn.addEventListener("click", () => {
        this.toggleFavoritesModal();
      });
    }
  }

  checkUrlHash() {
    const hash = window.location.hash;
    if (hash && hash.startsWith("#sql=")) {
      try {
        const sql = decodeURIComponent(hash.substring(5));
        if (sql) {
          this.input.value = sql;
          // Un enlace compartido ejecuta SQL en el navegador de quien lo abre.
          // Decirlo evita que una consulta ajena pase por propia: el visitante ve
          // el texto antes del resultado y puede borrarlo sin ejecutarlo.
          this.addSystemMessage(
            "Esta consulta viene del enlace que abriste, no la escribiste tú: <code>" +
            this.escapeHtml(sql.length > 220 ? sql.slice(0, 220) + "…" : sql) +
            "</code>. Revisa el texto antes de usar el resultado. Se ejecutará en unos segundos " +
            "(o bórrala y escribe la tuya)."
          );
          setTimeout(() => {
            this.handleSend();
          }, 600);
        }
      } catch (err) {
        console.error("Error al decodificar hash:", err);
      }
    }
  }

  // La pestaña SQL ocupa todo el panel: no hay splitter que ajustar.
  focusTerminal() {
    if (this.messagesContainer) this.scrollToBottom();
    if (this.input) setTimeout(() => this.input.focus(), 30);
  }

  clearTerminal() {
    if (!this.messagesContainer) return;
    this.messagesContainer.innerHTML = "";
    this.resultsMap = {};
    this.showWelcomeMessage();
    if (window.MFCUI) window.MFCUI.toast("Conversación limpia. Las consultas guardadas siguen disponibles.", "info");
  }

  // Autocompletado con Tab sobre los nombres de las vistas publicadas y palabras clave SQL.
  completionCandidates() {
    // Los nombres se toman del catálogo de vistas (duckdb_client.js) y, como
    // respaldo, de las tablas ya dibujadas en el explorador: así el autocompletado
    // no depende del orden de carga de los scripts.
    const views = (typeof SEMANTIC_VIEWS !== "undefined" && Array.isArray(SEMANTIC_VIEWS))
      ? SEMANTIC_VIEWS.map((v) => v.name)
      : [];
    const domViews = Array.from(document.querySelectorAll(".tree-table"))
      .map((el) => el.dataset.tableId)
      .filter(Boolean);
    const keywords = ["SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "LIMIT", "HAVING",
      "JOIN", "LEFT JOIN", "AS", "DESC", "ASC", "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX",
      "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN", "WITH", "UNION", "NULL", "CAST", "ROUND"];
    return Array.from(new Set(views.concat(domViews, keywords)));
  }

  completeInput() {
    const input = this.input;
    if (!input) return;
    const caret = input.selectionStart != null ? input.selectionStart : input.value.length;
    const before = input.value.slice(0, caret);
    const match = before.match(/([A-Za-z_][A-Za-z0-9_]*)$/);
    if (!match) return;
    const fragment = match[1];
    const lower = fragment.toLowerCase();
    const candidates = this.completionCandidates().filter((c) => {
      const lc = c.toLowerCase();
      return lc.startsWith(lower) && lc !== lower;
    });
    if (candidates.length === 0) return;
    let completion = candidates[0];
    if (candidates.length > 1) {
      for (const candidate of candidates) {
        let i = 0;
        while (i < completion.length && i < candidate.length &&
               completion[i].toLowerCase() === candidate[i].toLowerCase()) i++;
        completion = completion.slice(0, i);
      }
      if (completion.toLowerCase() === lower) completion = candidates[0];
    }
    const rest = input.value.slice(caret);
    input.value = before.slice(0, caret - fragment.length) + completion + rest;
    const newCaret = caret - fragment.length + completion.length;
    input.selectionStart = input.selectionEnd = newCaret;
    if (candidates.length > 1 && window.MFCUI) {
      window.MFCUI.toast(`${candidates.length} coincidencias: ${candidates.slice(0, 5).join(", ")}${candidates.length > 5 ? "…" : ""}`, "info");
    }
  }

  initFavoritesModal() {
    let modal = document.getElementById("saved-queries-modal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "saved-queries-modal";
      modal.className = "saved-queries-modal";
      modal.innerHTML = `
        <div class="saved-modal-header">
          <span>CONSULTAS GUARDADAS</span>
          <button id="close-fav-modal" style="background:transparent; border:none; color:#8b949e; cursor:pointer; font-size:14px;">&times;</button>
        </div>
        <ul class="saved-list" id="saved-queries-list"></ul>
      `;
      // El panel inferior ya no existe: el modal se ancla al documento y se
      // posiciona de forma fija (ver .saved-queries-modal en app.css).
      document.body.appendChild(modal);

      const closeBtn = modal.querySelector("#close-fav-modal");
      if (closeBtn) {
        closeBtn.addEventListener("click", () => modal.classList.remove("visible"));
      }
    }
  }

  toggleFavoritesModal() {
    const modal = document.getElementById("saved-queries-modal");
    if (!modal) return;
    const isVis = modal.classList.toggle("visible");
    if (isVis) {
      this.renderFavoritesList();
    }
  }

  getSavedQueries() {
    try {
      return JSON.parse(localStorage.getItem("mfc_saved_queries") || "[]");
    } catch {
      return [];
    }
  }

  renderFavoritesList() {
    const listEl = document.getElementById("saved-queries-list");
    if (!listEl) return;
    const queries = this.getSavedQueries();

    if (queries.length === 0) {
      listEl.innerHTML = `<li style="padding: 10px; font-size: 11px; color: var(--text-secondary); text-align: center;">No tienes consultas guardadas aún. Haz clic en "Guardar" en cualquier resultado.</li>`;
      return;
    }

    listEl.innerHTML = queries.map((q, idx) => `
      <li class="saved-item" data-index="${idx}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span class="saved-item-title">${this.escapeHtml(q.title)}</span>
          <button class="delete-fav-btn" data-index="${idx}" style="background:transparent; border:none; color:#696E79; cursor:pointer; font-size:11px;" title="Eliminar">&times;</button>
        </div>
        <span class="saved-item-sql">${this.escapeHtml(q.sql)}</span>
      </li>
    `).join("");

    listEl.querySelectorAll(".saved-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        if (e.target.classList.contains("delete-fav-btn")) return;
        const idx = parseInt(item.dataset.index, 10);
        const q = queries[idx];
        if (q) {
          this.input.value = q.sql;
          document.getElementById("saved-queries-modal").classList.remove("visible");
          this.handleSend();
        }
      });
    });

    listEl.querySelectorAll(".delete-fav-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const idx = parseInt(btn.dataset.index, 10);
        this.deleteSavedQuery(idx);
      });
    });
  }

  saveQuery(queryId) {
    const stored = this.resultsMap[queryId];
    if (!stored) return;
    const titlePrompt = prompt("Nombre o etiqueta para esta consulta:", stored.query.substring(0, 35) + "…");
    if (!titlePrompt) return;

    const queries = this.getSavedQueries();
    queries.unshift({
      title: titlePrompt.trim(),
      sql: stored.query,
      timestamp: new Date().toISOString()
    });
    localStorage.setItem("mfc_saved_queries", JSON.stringify(queries.slice(0, 20)));
    this.addSystemMessage(`Consulta guardada en Favoritos: <b>${this.escapeHtml(titlePrompt)}</b>.`);
  }

  deleteSavedQuery(index) {
    const queries = this.getSavedQueries();
    queries.splice(index, 1);
    localStorage.setItem("mfc_saved_queries", JSON.stringify(queries));
    this.renderFavoritesList();
  }

  setQueryInput(sql, tableName) {
    this.input.value = sql;
    this.input.focus();
    this.addSystemMessage(`Tabla seleccionada: <b>${this.escapeHtml(tableName)}</b>. Presiona Enter o clic en Ejecutar para consultar.`);
  }

  setCustomChips(chips, contextTitle) {
    if (!this.chipsContainer) return;
    this.chipsContainer.innerHTML = chips.map((c) => `
      <div class="chip" data-query="${this.escapeHtml(c.query)}">
        ${this.escapeHtml(c.label)}
      </div>
    `).join("");
    this.chipsContainer.querySelectorAll(".chip").forEach((chip) => {
      chip.addEventListener("click", (e) => {
        const query = e.currentTarget.dataset.query;
        if (query) {
          this.input.value = query;
          this.handleSend();
        }
      });
    });
    this.addSystemMessage(`Contexto activo: <b>${this.escapeHtml(contextTitle)}</b>. Sugerencias actualizadas.`);
  }

  restoreDefaultChips() {
    if (!this.chipsContainer || !this.defaultChipsHTML) return;
    this.chipsContainer.innerHTML = this.defaultChipsHTML;
    this.chipsContainer.querySelectorAll(".chip").forEach((chip) => {
      chip.addEventListener("click", (e) => {
        const query = e.currentTarget.dataset.query;
        if (query) {
          this.input.value = query;
          this.handleSend();
        }
      });
    });
  }

  showWelcomeMessage() {
    this.addBotMessage(`
      <div style="line-height: 1.5;">
        <b>Terminal SQL del Sistema de Información Financiera de Chile</b><br>
        <span style="color: var(--text-secondary); font-size: 12px;">
          Las consultas se ejecutan con <b>DuckDB-Wasm</b> dentro de tu navegador, directamente sobre los Parquet publicados: no hay servidor de datos ni se envía nada a terceros.
        </span>
        <div style="margin-top: 8px; font-size: 12px; color: var(--text-secondary);">
          <i>Elige una tabla en el explorador de la izquierda para cargar su consulta, o parte por una de las sugerencias de arriba. Cada resultado se puede ver como tabla o como gráfico y exportar a CSV.</i>
        </div>
      </div>
    `);
  }

  async handleSend() {
    const text = this.input.value.trim();
    if (!text) return;

    this.lastExecutedQuery = text;
    this.history.push(text);
    this.historyIndex = this.history.length;
    this.input.value = "";
    this.sendBtn.disabled = true;

    this.addUserMessage(text);
    const loadingId = this.addLoadingMessage();

    try {
      const result = await window.DuckDBClient.query(text);
      this.removeMessage(loadingId);

      if (result.success) {
        this.renderQueryResult(text, result);
      } else {
        this.addBotMessage(`<div style="color: var(--accent-red);">[Error SQL] ${this.escapeHtml(String(result.error || "error desconocido del motor DuckDB"))}</div>`);
      }
    } catch (err) {
      this.removeMessage(loadingId);
      this.addBotMessage(`<div style="color: var(--accent-red);">[Excepción] ${this.escapeHtml(err && err.message ? err.message : String(err))}</div>`);
    } finally {
      this.sendBtn.disabled = false;
      this.input.focus();
    }
  }

  formatCellValue(colName, val) {
    if (val === null || val === undefined) return "";
    if (typeof val !== "number") return this.escapeHtml(val);

    const lower = colName.toLowerCase();
    if (lower.includes("_pct") || lower.includes("tasa") || lower.includes("tir") || lower.includes("presencia")) {
      return val.toLocaleString("es-CL", { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + " %";
    }
    if (lower.includes("_m_clp") || lower.includes("tasacion") || lower.includes("avaluo") || lower.includes("inversion")) {
      return "$" + val.toLocaleString("es-CL", { maximumFractionDigits: 2 }) + " M";
    }
    if (lower.includes("precio")) {
      return "$" + val.toLocaleString("es-CL", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return val.toLocaleString("es-CL", { maximumFractionDigits: 4 });
  }

  renderQueryResult(query, result) {
    const queryId = "q_" + Date.now();
    const tableWrapperId = "tbl_" + queryId;
    const chartContainerId = "chart_" + queryId;

    this.resultsMap[queryId] = { query, result, sortCol: null, sortAsc: true };

    let headersHtml = result.columns.map((col, idx) => 
      `<th onclick="window.ChatTerminal.sortTable('${queryId}', ${idx})" title="Clic para ordenar">${this.escapeHtml(col)}<span class="sort-icon" id="sort_${queryId}_${idx}"></span></th>`
    ).join("");

    let rowsHtml = result.rows.map((row) => {
      let cells = result.columns.map((col) => {
        let rawVal = row[col];
        let formatted = this.formatCellValue(col, rawVal);
        const isNum = typeof rawVal === "number";
        return `<td class="${isNum ? 'cell-num' : ''}" data-copy="${this.escapeHtml(rawVal)}" onclick="window.ChatTerminal.copyCell(this, this.dataset.copy)" title="Clic para copiar">${formatted}</td>`;
      }).join("");
      return `<tr>${cells}</tr>`;
    }).join("");

    const content = `
      <div class="query-meta">
        <span><b>${result.elapsedMs} ms</b> | ${result.count.toLocaleString()} fila(s)</span>
        <div class="actions">
          <div class="view-switch" id="switch_${queryId}">
            <button class="view-btn active" onclick="window.ChatTerminal.switchView('${queryId}', 'table')">Tabla</button>
            <button class="view-btn" onclick="window.ChatTerminal.switchView('${queryId}', 'chart')">Gráfico</button>
          </div>
          <button class="action-btn" onclick="window.ChatTerminal.exportCSV('${tableWrapperId}')">Exportar CSV</button>
          <button class="action-btn" onclick="window.ChatTerminal.saveQuery('${queryId}')">Guardar</button>
          <button class="action-btn" data-sql="${this.escapeHtml(query)}" onclick="navigator.clipboard.writeText(this.dataset.sql)">Copiar SQL</button>
        </div>
      </div>
      <div class="table-wrapper" id="${tableWrapperId}">
        <table class="results-table">
          <thead><tr>${headersHtml}</tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>
      <div class="result-chart-wrapper" id="${chartContainerId}" style="display: none;"></div>
    `;

    this.addBotMessage(content);
  }

  sortTable(queryId, colIdx) {
    const stored = this.resultsMap[queryId];
    if (!stored || !stored.result || !stored.result.rows) return;
    const colName = stored.result.columns[colIdx];
    if (!colName) return;

    if (stored.sortCol === colName) {
      stored.sortAsc = !stored.sortAsc;
    } else {
      stored.sortCol = colName;
      stored.sortAsc = true;
    }

    stored.result.rows.sort((a, b) => {
      let va = a[colName];
      let vb = b[colName];
      if (va === null || va === undefined) return 1;
      if (vb === null || vb === undefined) return -1;
      if (typeof va === "number" && typeof vb === "number") {
        return stored.sortAsc ? va - vb : vb - va;
      }
      return stored.sortAsc
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va));
    });

    const tableWrapper = document.getElementById("tbl_" + queryId);
    if (!tableWrapper) return;
    const tbody = tableWrapper.querySelector("tbody");
    if (!tbody) return;

    tbody.innerHTML = stored.result.rows.map((row) => {
      let cells = stored.result.columns.map((col) => {
        let rawVal = row[col];
        let formatted = this.formatCellValue(col, rawVal);
        const isNum = typeof rawVal === "number";
        return `<td class="${isNum ? 'cell-num' : ''}" data-copy="${this.escapeHtml(rawVal)}" onclick="window.ChatTerminal.copyCell(this, this.dataset.copy)" title="Clic para copiar">${formatted}</td>`;
      }).join("");
      return `<tr>${cells}</tr>`;
    }).join("");

    const ths = tableWrapper.querySelectorAll("th");
    ths.forEach((th, i) => {
      const icon = th.querySelector(".sort-icon");
      if (icon) {
        if (i === colIdx) {
          icon.textContent = stored.sortAsc ? " ▲" : " ▼";
          icon.style.color = "var(--accent-mint)";
        } else {
          icon.textContent = "";
        }
      }
    });
  }

  copyCell(tdElement, value) {
    navigator.clipboard.writeText(value).then(() => {
      const origBg = tdElement.style.backgroundColor;
      tdElement.style.backgroundColor = "var(--accent-mint-dim)";
      setTimeout(() => {
        tdElement.style.backgroundColor = origBg;
      }, 300);
      this.showToast(`Copiado: ${value.slice(0, 35)}`);
    }).catch(() => {});
  }

  showToast(text) {
    let toast = document.getElementById("mfc-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "mfc-toast";
      toast.className = "mfc-toast";
      document.body.appendChild(toast);
    }
    toast.textContent = text;
    toast.classList.add("visible");
    clearTimeout(this._toastTimeout);
    this._toastTimeout = setTimeout(() => {
      toast.classList.remove("visible");
    }, 1500);
  }

  switchView(queryId, mode) {
    const tableEl = document.getElementById("tbl_" + queryId);
    const chartEl = document.getElementById("chart_" + queryId);
    const switchEl = document.getElementById("switch_" + queryId);
    if (!tableEl || !chartEl) return;

    if (switchEl) {
      switchEl.querySelectorAll(".view-btn").forEach((btn) => {
        btn.classList.toggle("active", btn.textContent.toLowerCase().includes(mode));
      });
    }

    if (mode === "table") {
      tableEl.style.display = "block";
      chartEl.style.display = "none";
    } else {
      tableEl.style.display = "none";
      chartEl.style.display = "flex";

      if (!chartEl._rendered && window.ChartRenderer) {
        const stored = this.resultsMap[queryId];
        if (stored) {
          const renderer = new window.ChartRenderer(chartEl);
          renderer.setData(stored.result.columns, stored.result.rows);
          chartEl._rendered = true;
        }
      }
    }
  }

  exportCSV(tableWrapperId) {
    const wrapper = document.getElementById(tableWrapperId);
    if (!wrapper) return;
    const rows = Array.from(wrapper.querySelectorAll("tr"));
    const csvContent = rows.map((r) => {
      const cells = Array.from(r.querySelectorAll("th, td"));
      return cells.map((c) => `"${c.textContent.replace(/"/g, '""')}"`).join(",");
    }).join("\n");

    const blob = new Blob(["\ufeff" + csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sif_chile_resultado_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  addUserMessage(text) {
    const div = document.createElement("div");
    div.className = "message message-user";
    div.innerHTML = `<div class="bubble">sql&gt; ${this.escapeHtml(text)}</div>`;
    this.messagesContainer.appendChild(div);
    this.scrollToBottom();
  }

  addBotMessage(html) {
    const div = document.createElement("div");
    div.className = "message message-bot";
    div.innerHTML = `<div class="bubble">${html}</div>`;
    this.messagesContainer.appendChild(div);
    this.scrollToBottom();
  }

  addSystemMessage(html) {
    const div = document.createElement("div");
    div.className = "message message-bot";
    div.innerHTML = `<div class="bubble" style="background-color: rgba(56, 139, 253, 0.1); border-color: rgba(56, 139, 253, 0.3); font-size: 12px;">${html}</div>`;
    this.messagesContainer.appendChild(div);
    this.scrollToBottom();
  }

  addLoadingMessage() {
    const id = "loading_" + Date.now();
    const div = document.createElement("div");
    div.id = id;
    div.className = "message message-bot";
    div.innerHTML = `<div class="bubble" style="color: var(--text-secondary); font-size: 12px;">Ejecutando consulta con DuckDB-Wasm...</div>`;
    this.messagesContainer.appendChild(div);
    this.scrollToBottom();
    return id;
  }

  removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  scrollToBottom() {
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }

  // Sirve para texto y para valores de atributo (escapa también comillas).
  escapeHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
}

window.ChatTerminalController = ChatTerminalController;
