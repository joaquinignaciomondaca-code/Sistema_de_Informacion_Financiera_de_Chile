/**
 * Theme and Color Palette Switcher (Dropdown Swatch Selector)
 * Sistema de Información Financiera de Chile
 * Displays color swatches while providing descriptive accessible names.
 */

(function () {
  // v2: la paleta predeterminada cambió a "dark-ide" (estilo IDE oscuro),
  // por lo que se reinicia la preferencia guardada una única vez.
  const STORAGE_KEY = "mfc_color_theme_v2";
  const DEFAULT_THEME = "dark-ide";

  const PALETTES = [
    {
      id: "dark-ide",
      label: "Oscuro con acento azul",
      colors: ["#121316", "#18191E", "#3B82F6", "#E5E7EB"]
    },
    {
      id: "swissborg",
      label: "Oscuro con acento verde",
      colors: ["#191E29", "#132D46", "#01C38D", "#FFFFFF"]
    },
    {
      id: "bloomberg",
      label: "Oscuro con acento naranja",
      colors: ["#0F0F10", "#1A1A1E", "#FF9900", "#FCD34D"]
    },
    {
      id: "nord",
      label: "Oscuro azul grisáceo",
      colors: ["#242933", "#2E3440", "#88C0D0", "#ECEFF4"]
    },
    {
      id: "midnight",
      label: "Oscuro azul profundo",
      colors: ["#0B1120", "#0F172A", "#38BDF8", "#F8FAFC"]
    },
    {
      id: "informe",
      label: "Claro para informes",
      colors: ["#F5F6F8", "#FFFFFF", "#0B6F54", "#1657A8"]
    }
  ];

  function createSwatchStripHtml(colors) {
    return `<div class="theme-swatch-strip">` +
      colors.map((c) => `<span class="swatch-block" style="background:${c};"></span>`).join("") +
      `</div>`;
  }

  function updateTriggerPreview(themeName) {
    const triggerSwatch = document.getElementById("theme-trigger-swatch");
    if (!triggerSwatch) return;
    const p = PALETTES.find((item) => item.id === themeName) || PALETTES[0];
    triggerSwatch.innerHTML = p.colors
      .map((c) => `<span class="swatch-block" style="background:${c};"></span>`)
      .join("");
  }

  function applyTheme(themeName) {
    document.documentElement.setAttribute("data-theme", themeName);
    try {
      localStorage.setItem(STORAGE_KEY, themeName);
    } catch (e) {
      // Ignorar restricciones en almacenamiento
    }

    updateTriggerPreview(themeName);

    // Mantener una única opción visual y semánticamente seleccionada.
    const items = document.querySelectorAll(".theme-palette-item");
    items.forEach((item) => {
      const selected = item.dataset.theme === themeName;
      item.classList.toggle("active", selected);
      item.setAttribute("aria-pressed", selected ? "true" : "false");
    });

    // Notificar al grafo relacional y componentes
    window.dispatchEvent(new CustomEvent("mfc:themechange", { detail: { theme: themeName } }));
    if (window.erdInstance && typeof window.erdInstance.render === "function") {
      window.erdInstance.render();
    }
  }

  function initThemeSwitcher() {
    const container = document.getElementById("theme-dropdown-container");
    const triggerBtn = document.getElementById("theme-dropdown-btn");
    const menu = document.getElementById("theme-dropdown-menu");

    if (!container || !triggerBtn || !menu) return;
    // La inicialización puede reintentarse al evaluar varias veces la vista;
    // no duplicar botones ni listeners si el evento DOMContentLoaded se repite.
    if (container.dataset.themeSwitcherInitialized === "true") return;
    container.dataset.themeSwitcherInitialized = "true";

    // Renderizar las opciones como botones de color con nombres distinguibles.
    menu.setAttribute("role", "group");
    menu.setAttribute("aria-label", "Paletas de colores");
    triggerBtn.setAttribute("aria-controls", menu.id);
    menu.innerHTML = "";
    PALETTES.forEach((p) => {
      const itemBtn = document.createElement("button");
      itemBtn.type = "button";
      itemBtn.className = "theme-palette-item";
      itemBtn.dataset.theme = p.id;
      itemBtn.setAttribute("aria-label", `Paleta: ${p.label}`);
      itemBtn.setAttribute("aria-pressed", "false");

      itemBtn.innerHTML = `
        <span class="theme-item-indicator" aria-hidden="true"></span>
        <div class="theme-swatch-strip" aria-hidden="true">
          ${p.colors.map((c) => `<span class="swatch-block" style="background:${c};"></span>`).join("")}
        </div>
      `;

      itemBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        applyTheme(p.id);
        container.classList.remove("open");
        triggerBtn.setAttribute("aria-expanded", "false");
        triggerBtn.focus();
      });

      menu.appendChild(itemBtn);
    });

    // Toggle del menu desplegable
    triggerBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = container.classList.toggle("open");
      triggerBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    // Cerrar al hacer clic fuera
    document.addEventListener("click", (e) => {
      if (!container.contains(e.target)) {
        container.classList.remove("open");
        triggerBtn.setAttribute("aria-expanded", "false");
      }
    });

    // Cerrar con Escape
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && container.classList.contains("open")) {
        container.classList.remove("open");
        triggerBtn.setAttribute("aria-expanded", "false");
        triggerBtn.focus();
      }
    });

    // Cargar tema inicial
    let savedTheme = DEFAULT_THEME;
    try {
      savedTheme = localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME;
    } catch (e) {
      savedTheme = DEFAULT_THEME;
    }

    applyTheme(savedTheme);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initThemeSwitcher);
  } else {
    initThemeSwitcher();
  }

  window.MFCThemes = {
    applyTheme: applyTheme,
    getCurrentTheme: function () {
      return document.documentElement.getAttribute("data-theme") || DEFAULT_THEME;
    }
  };
})();
