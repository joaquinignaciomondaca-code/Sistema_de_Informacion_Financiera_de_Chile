/** Selección compartida. Cada pestaña sigue una selección nueva una sola vez. */
window.SIFTableContext = (() => {
  let selected = null;
  let revision = 0;
  const applied = new Map();
  function paint() {
    const bar = document.getElementById("table-context");
    if (!bar) return;
    bar.hidden = !selected;
    bar.querySelector("code").textContent = selected ? selected.name : "";
  }
  function select(id, name) {
    if (!id || (selected && selected.id === id)) return;
    selected = { id, name: name || id };
    revision++;
    paint();
  }
  function apply(tab) {
    paint();
    if (!selected || applied.get(tab) === revision) return;
    const { id, name } = selected;
    if (tab === "dict" && window.DataDictionary) {
      const dict = window.DataDictionary;
      dict.selectedTableId = id;
      dict.currentGroup = "todos";
      dict.currentSector = "todos";
      dict.searchQuery = "";
      dict.render();
      dict.container.scrollTop = 0;
    } else if (tab === "erd" && window.erdInstance) {
      window.erdInstance.focusTable(id);
    } else if (tab === "downloads" && window.DownloadsPanel) {
      const panel = window.DownloadsPanel;
      panel.render();
      panel.grupo = "todos";
      panel.sector = "todos";
      panel.busqueda = id;
      panel.controles.search.value = id;
      panel.container.querySelector("#dl-group").value = "todos";
      panel.actualizarSectores();
      panel.aplicarFiltros();
      const card = Array.from(panel.container.querySelectorAll(".dl-item")).find(el => el.dataset.id === id);
      if (card && typeof card.scrollIntoView === "function") card.scrollIntoView({ block: "center" });
    } else if (tab === "data" && window.DataViewer) {
      if (window.DataViewer.currentView !== id || !window.DataViewer.loadRequestId) window.DataViewer.loadTable(id, name);
    } else if (tab === "sql" && window.ChatTerminal) {
      window.ChatTerminal.setQueryInput(`SELECT * FROM ${id} LIMIT 10;`, name, true);
    }
    applied.set(tab, revision);
  }
  function clear() {
    const barra = document.getElementById("table-context");
    const focoEnBarra = barra && barra.contains(document.activeElement);
    const anterior = selected;
    selected = null;
    revision++;
    applied.clear();
    if (window.SidebarNav) window.SidebarNav.selectedTableId = null;
    document.querySelectorAll(".tree-table.selected").forEach(el => el.classList.remove("selected"));
    if (window.DataDictionary) {
      window.DataDictionary.selectedTableId = null;
      window.DataDictionary.render();
    }
    if (anterior && window.DownloadsPanel && window.DownloadsPanel.controles && window.DownloadsPanel.busqueda === anterior.id) {
      window.DownloadsPanel.busqueda = "";
      window.DownloadsPanel.controles.search.value = "";
      window.DownloadsPanel.aplicarFiltros();
    }
    if (window.erdInstance && typeof window.erdInstance.render === "function") window.erdInstance.render();
    if (window.cerrarEsquema) window.cerrarEsquema();
    paint();
    if (focoEnBarra) {
      const tab = document.querySelector('.panel-tabs [role="tab"][aria-selected="true"]');
      if (tab) tab.focus();
    }
  }
  return { select, apply, clear, follow(tab) { applied.delete(tab); apply(tab); }, get selected() { return selected; } };
})();
