/**
 * ChartRenderer (Motor de Visualización Gráfica Canvas 2D)
 * Monitor Financiero Chile
 * Renderiza gráficos de barras y líneas interactivos con paleta Swissborg.
 * Cero emojis y cero dependencias externas.
 */

class ChartRenderer {
  constructor(canvasContainerId, options = {}) {
    this.container = typeof canvasContainerId === "string" 
      ? document.getElementById(canvasContainerId) 
      : canvasContainerId;
    this.options = Object.assign({
      barColor: "#01C38D",
      barHoverColor: "#00ADB5",
      gridColor: "rgba(105, 110, 121, 0.25)",
      textColor: "#A6B1C2",
      titleColor: "#FFFFFF",
      fontFamily: "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
      monoFont: "JetBrains Mono, monospace"
    }, options);

    this.canvas = document.createElement("canvas");
    this.ctx = this.canvas.getContext("2d");
    this.canvas.className = "result-chart-canvas";
    this.container.innerHTML = "";
    this.container.appendChild(this.canvas);

    this.data = [];
    this.hoverIndex = -1;
    this.initEvents();
  }

  initEvents() {
    this.canvas.addEventListener("mousemove", (e) => this.onMouseMove(e));
    this.canvas.addEventListener("mouseleave", () => {
      this.hoverIndex = -1;
      this.render();
    });
    window.addEventListener("resize", () => this.resize());
  }

  resize() {
    if (!this.container) return;
    const rect = this.container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = Math.max(rect.width, 320);
    this.height = Math.max(rect.height || 260, 240);

    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;
    this.ctx.scale(dpr, dpr);
    this.render();
  }

  setData(columns, rows) {
    if (!rows || rows.length === 0 || !columns || columns.length === 0) {
      this.data = [];
      return;
    }

    // 1. Identificar columna de etiquetas (dimensión categórica o temporal)
    let labelCol = columns.find(c => {
      const lower = c.toLowerCase();
      return lower.includes("nemo") || lower.includes("comuna") || lower.includes("tipo") ||
             lower.includes("gestora") || lower.includes("periodo") || lower.includes("nombre") ||
             lower.includes("rubro");
    }) || columns.find(c => typeof rows[0][c] === "string") || columns[0];

    // 2. Identificar columna de valores (métrica numérica principal)
    let valueCol = columns.find(c => {
      const lower = c.toLowerCase();
      return (lower.includes("prom") || lower.includes("total") || lower.includes("tir") ||
              lower.includes("precio") || lower.includes("tasacion") || lower.includes("monto") ||
              lower.includes("filas") || lower.includes("tenencias") || lower.includes("contratos") ||
              lower.includes("inversion")) && typeof rows[0][c] === "number";
    }) || columns.find(c => c !== labelCol && typeof rows[0][c] === "number") || columns[1];

    if (!valueCol) {
      // Fallback: contar ocurrencias o primer valor numérico
      for (const col of columns) {
        if (col !== labelCol && typeof rows[0][col] === "number") {
          valueCol = col;
          break;
        }
      }
    }

    this.labelCol = labelCol;
    this.valueCol = valueCol || labelCol;
    this.isTimeSeries = labelCol.toLowerCase().includes("periodo");

    this.data = rows.slice(0, 15).map(r => ({
      label: String(r[labelCol] ?? "N/A"),
      value: Number(r[valueCol]) || 0
    }));

    this.resize();
  }

  onMouseMove(e) {
    if (!this.bars || this.bars.length === 0) return;
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    let newHover = -1;
    for (let i = 0; i < this.bars.length; i++) {
      const b = this.bars[i];
      if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) {
        newHover = i;
        break;
      }
    }

    if (newHover !== this.hoverIndex) {
      this.hoverIndex = newHover;
      this.render();
    }
  }

  render() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    ctx.clearRect(0, 0, w, h);

    if (!this.data || this.data.length === 0) {
      ctx.fillStyle = this.options.textColor;
      ctx.font = `12px ${this.options.fontFamily}`;
      ctx.textAlign = "center";
      ctx.fillText("No hay datos numéricos suficientes para graficar.", w / 2, h / 2);
      return;
    }

    const padding = { top: 35, right: 25, bottom: 48, left: 65 };
    const chartW = w - padding.left - padding.right;
    const chartH = h - padding.top - padding.bottom;

    const maxVal = Math.max(...this.data.map(d => d.value), 1);
    const minVal = Math.min(0, ...this.data.map(d => d.value));
    const range = maxVal - minVal;

    // Título del Gráfico
    ctx.save();
    ctx.fillStyle = this.options.titleColor;
    ctx.font = `bold 11px ${this.options.fontFamily}`;
    ctx.textAlign = "left";
    ctx.fillText(`${this.valueCol.toUpperCase()} POR ${this.labelCol.toUpperCase()}`, padding.left, 20);
    ctx.restore();

    // Líneas de Cuadrícula Horizontal
    const gridSteps = 4;
    ctx.save();
    ctx.strokeStyle = this.options.gridColor;
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.font = `10px ${this.options.monoFont}`;
    ctx.fillStyle = this.options.textColor;
    ctx.textAlign = "right";

    for (let i = 0; i <= gridSteps; i++) {
      const val = minVal + (range * i) / gridSteps;
      const y = padding.top + chartH - (i / gridSteps) * chartH;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + chartW, y);
      ctx.stroke();

      let labelText = val >= 1e6 ? `${(val / 1e6).toFixed(1)}M` :
                      val >= 1e3 ? `${(val / 1e3).toFixed(0)}k` :
                      val.toFixed(val < 10 && val > 0 ? 2 : 0);
      ctx.fillText(labelText, padding.left - 8, y + 3);
    }
    ctx.restore();

    // Dibujar Barras
    this.bars = [];
    const n = this.data.length;
    const barSpacing = Math.max(chartW / n, 20);
    const barWidth = Math.min(barSpacing * 0.65, 45);

    this.data.forEach((d, i) => {
      const barH = ((d.value - minVal) / range) * chartH;
      const x = padding.left + i * barSpacing + (barSpacing - barWidth) / 2;
      const y = padding.top + chartH - barH;
      const isHov = this.hoverIndex === i;

      this.bars.push({ x, y, w: barWidth, h: barH, data: d });

      // Sombra
      ctx.save();
      if (isHov) {
        ctx.shadowColor = "rgba(1, 195, 141, 0.6)";
        ctx.shadowBlur = 12;
      }

      // Gradiente de Barra
      const grad = ctx.createLinearGradient(x, y, x, y + barH);
      grad.addColorStop(0, isHov ? this.options.barHoverColor : this.options.barColor);
      grad.addColorStop(1, "rgba(1, 195, 141, 0.45)");

      ctx.fillStyle = grad;
      this.roundRect(ctx, x, y, barWidth, Math.max(barH, 2), 4);
      ctx.fill();
      ctx.restore();

      // Etiqueta del Eje X
      ctx.save();
      ctx.fillStyle = isHov ? "#FFFFFF" : this.options.textColor;
      ctx.font = `${isHov ? "bold " : ""}9.5px ${this.options.fontFamily}`;
      ctx.textAlign = "center";
      const shortLabel = d.label.length > 8 ? d.label.substring(0, 7) + "…" : d.label;
      ctx.fillText(shortLabel, x + barWidth / 2, padding.top + chartH + 16);
      ctx.restore();
    });

    // Tooltip en Hover
    if (this.hoverIndex >= 0 && this.bars[this.hoverIndex]) {
      const b = this.bars[this.hoverIndex];
      const d = b.data;
      const tipText = `${d.label}: ${d.value.toLocaleString("es-CL", { maximumFractionDigits: 2 })}`;

      ctx.save();
      ctx.font = `bold 10.5px ${this.options.monoFont}`;
      const tipW = ctx.measureText(tipText).width + 16;
      const tipH = 24;
      let tipX = b.x + b.w / 2 - tipW / 2;
      tipX = Math.max(padding.left, Math.min(tipX, w - padding.right - tipW));
      const tipY = Math.max(b.y - tipH - 8, padding.top);

      ctx.fillStyle = "#191E29";
      ctx.strokeStyle = this.options.barColor;
      ctx.lineWidth = 1;
      this.roundRect(ctx, tipX, tipY, tipW, tipH, 5);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#FFFFFF";
      ctx.textAlign = "center";
      ctx.fillText(tipText, tipX + tipW / 2, tipY + 16);
      ctx.restore();
    }
  }

  roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
}

window.ChartRenderer = ChartRenderer;
