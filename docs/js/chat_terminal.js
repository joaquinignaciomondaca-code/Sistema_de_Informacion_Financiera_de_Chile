/**
 * Chat & SQL Terminal Controller
 * Monitor Financiero Chile
 * Soporte DuckDB-Wasm, Gráficos Canvas 2D interactivos, URL Hash sharing,
 * Consultas Favoritas en localStorage y formateo financiero chileno ($CLP, %, UF).
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
    this.initSplitter();
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
        }).catch(() => {
          window.location.hash = `sql=${encodeURIComponent(sqlToShare)}`;
          this.addSystemMessage(`URL actualizada en la barra del navegador.`);
        });
      });
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
          setTimeout(() => {
            this.handleSend();
          }, 600);
        }
      } catch (err) {
        console.error("Error al decodificar hash:", err);
      }
    }
  }

  initSplitter() {
    const splitter = document.getElementById("panel-splitter");
    const topPanel = document.querySelector(".top-panel");
    const mainContainer = document.querySelector(".main-container");
    if (!splitter || !topPanel || !mainContainer) return;
    let isResizing = false;

    splitter.addEventListener("mousedown", () => {
      isResizing = true;
      splitter.classList.add("dragging");
      document.body.style.userSelect = "none";
    });

    window.addEventListener("mousemove", (e) => {
      if (!isResizing) return;
      const containerRect = mainContainer.getBoundingClientRect();
      const newHeightPct = ((e.clientY - containerRect.top) / containerRect.height) * 100;
      if (newHeightPct >= 15 && newHeightPct <= 85) {
        topPanel.style.height = `${newHeightPct}%`;
        if (window.erdInstance) {
          window.erdInstance.resize();
        }
      }
    });

    window.addEventListener("mouseup", () => {
      if (isResizing) {
        isResizing = false;
        splitter.classList.remove("dragging");
        document.body.style.userSelect = "";
      }
    });
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
      const bottomPanel = document.querySelector(".bottom-panel");
      if (bottomPanel) bottomPanel.appendChild(modal);

      document.getElementById("close-fav-modal").addEventListener("click", () => {
        modal.classList.remove("visible");
      });
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
    this.addSystemMessage(`Tabla seleccionada: <b>${tableName}</b>. Presiona Enter o clic en Ejecutar para consultar.`);
  }

  setCustomChips(chips, contextTitle) {
    if (!this.chipsContainer) return;
    this.chipsContainer.innerHTML = chips.map((c) => `
      <div class="chip" data-query="${c.query.replace(/"/g, '&quot;')}">
        ${c.label}
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
    this.addSystemMessage(`Contexto activo: <b>${contextTitle}</b>. Sugerencias actualizadas.`);
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
        <b>Bienvenido a Monitor Financiero Chile</b><br>
        <span style="color: var(--text-secondary); font-size: 12px;">
          Esta consola ejecuta consultas SQL mediante <b>DuckDB-Wasm</b> directamente en tu navegador sobre más de <b>11.9 millones de contratos y registros</b> de carteras de inversión institucionales (CMF 2007 – 2024).
        </span>
        <div style="margin-top: 8px; font-size: 12px; color: var(--text-secondary);">
          <i>Selecciona cualquier tabla en el explorador lateral para consultar, o prueba las sugerencias rápidas. Ahora puedes alternar entre Vista Tabla y Vista Gráfico en cada resultado.</i>
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
        this.addBotMessage(`<div style="color: var(--accent-red);">[Error SQL] ${result.error}</div>`);
      }
    } catch (err) {
      this.removeMessage(loadingId);
      this.addBotMessage(`<div style="color: var(--accent-red);">[Excepción] ${err.message}</div>`);
    } finally {
      this.sendBtn.disabled = false;
      this.input.focus();
    }
  }

  formatCellValue(colName, val) {
    if (val === null || val === undefined) return "";
    if (typeof val !== "number") return val;

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
      `<th onclick="window.ChatTerminal.sortTable('${queryId}', ${idx})" title="Clic para ordenar">${col}<span class="sort-icon" id="sort_${queryId}_${idx}"></span></th>`
    ).join("");

    let rowsHtml = result.rows.map((row) => {
      let cells = result.columns.map((col) => {
        let rawVal = row[col];
        let formatted = this.formatCellValue(col, rawVal);
        const isNum = typeof rawVal === "number";
        const valStr = String(rawVal ?? "").replace(/'/g, "\\'").replace(/"/g, "&quot;");
        return `<td class="${isNum ? 'cell-num' : ''}" onclick="window.ChatTerminal.copyCell(this, '${valStr}')" title="Clic para copiar">${formatted}</td>`;
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
          <button class="action-btn" onclick="navigator.clipboard.writeText('${query.replace(/'/g, "\\'")}')">Copiar SQL</button>
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
        const valStr = String(rawVal ?? "").replace(/'/g, "\\'").replace(/"/g, "&quot;");
        return `<td class="${isNum ? 'cell-num' : ''}" onclick="window.ChatTerminal.copyCell(this, '${valStr}')" title="Clic para copiar">${formatted}</td>`;
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
    a.download = `monitor_financiero_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  addUserMessage(text) {
    const div = document.createElement("div");
    div.className = "message message-user";
    div.innerHTML = `<div class="bubble">PS financiero:\\> ${this.escapeHtml(text)}</div>`;
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

  escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
}

window.ChatTerminalController = ChatTerminalController;
