/**
 * Theme and Color Palette Switcher (Dropdown Swatch Selector)
 * Sistema de Información Financiera de Chile
 * Shows exclusively color swatches in a dropdown menu without text names.
 */

(function () {
  // v2: la paleta predeterminada cambió a "dark-ide" (estilo IDE oscuro),
  // por lo que se reinicia la preferencia guardada una única vez.
  const STORAGE_KEY = "mfc_color_theme_v2";
  const DEFAULT_THEME = "dark-ide";

  const PALETTES = [
    {
      id: "dark-ide",
      colors: ["#121316", "#18191E", "#3B82F6", "#E5E7EB"]
    },
    {
      id: "swissborg",
      colors: ["#191E29", "#132D46", "#01C38D", "#FFFFFF"]
    },
    {
      id: "bloomberg",
      colors: ["#0F0F10", "#1A1A1E", "#FF9900", "#FCD34D"]
    },
    {
      id: "nord",
      colors: ["#242933", "#2E3440", "#88C0D0", "#ECEFF4"]
    },
    {
      id: "midnight",
      colors: ["#0B1120", "#0F172A", "#38BDF8", "#F8FAFC"]
    },
    {
      id: "informe",
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

    // Actualizar elementos activos en el menu desplegable
    const items = document.querySelectorAll(".theme-palette-item");
    items.forEach((item) => {
      if (item.dataset.theme === themeName) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
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

    // Renderizar las opciones mostrando unicamente los 4 bloques de color
    menu.innerHTML = "";
    PALETTES.forEach((p) => {
      const itemBtn = document.createElement("button");
      itemBtn.type = "button";
      itemBtn.className = "theme-palette-item";
      itemBtn.dataset.theme = p.id;
      itemBtn.setAttribute("aria-label", "Tema");

      itemBtn.innerHTML = `
        <span class="theme-item-indicator"></span>
        <div class="theme-swatch-strip">
          ${p.colors.map((c) => `<span class="swatch-block" style="background:${c};"></span>`).join("")}
        </div>
      `;

      itemBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        applyTheme(p.id);
        container.classList.remove("open");
        triggerBtn.setAttribute("aria-expanded", "false");
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
