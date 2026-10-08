/**
 * Utilidades de descarga compartidas
 * Sistema de Información Financiera de Chile
 *
 * Un solo lugar para armar los archivos que el visitante se lleva: CSV con
 * separador ";" y BOM (para que Excel en Chile lo abra sin pasos extra), Excel
 * nativo (.xlsx) y empaquetado .ZIP cuando el volumen no cabe cómodo en una
 * planilla. Lo usan la pestaña Descargas y el visor de datos.
 */
window.MFCDownload = (function () {
  const LIMITE_ZIP_CSV = 250000;
  const LIMITE_ZIP_XLSX = 150000;
  const LIMITE_EXCEL = 1048576;

  function numero(valor) {
    if (valor === null || valor === undefined || Number.isNaN(Number(valor))) return "—";
    return Number(valor).toLocaleString("es-CL");
  }

  function bytes(valor) {
    if (!valor) return "—";
    const unidades = ["B", "KB", "MB", "GB", "TB"];
    let i = 0;
    let v = Number(valor);
    // Base 1000 (decimal), la misma que usa scripts/build_download_catalog.py y
    // el README: así el peso que muestra la web y el que se documenta coinciden.
    while (v >= 1000 && i < unidades.length - 1) {
      v /= 1000;
      i += 1;
    }
    const decimales = v < 10 && i > 0 ? 1 : 0;
    return `${v.toLocaleString("es-CL", { minimumFractionDigits: decimales, maximumFractionDigits: decimales })} ${unidades[i]}`;
  }

  function marcaTiempo() {
    const d = new Date();
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`;
  }

  function celdaCsv(valor) {
    return `"${String(valor === null || valor === undefined ? "" : valor).replace(/"/g, '""')}"`;
  }

  function textoCsv(rows, cols) {
    const cabecera = cols.map(celdaCsv).join(";");
    const lineas = rows.map((fila) => cols.map((col) => celdaCsv(fila[col])).join(";"));
    return `\ufeff${[cabecera, ...lineas].join("\n")}`;
  }

  function blobCsv(rows, cols) {
    return new Blob([textoCsv(rows, cols)], { type: "text/csv;charset=utf-8;" });
  }

  /* Hoja "Diccionario": una fila por columna con el nombre original de la CMF, el tipo, la
     unidad y la descripción de la ficha técnica. Sólo Excel (el CSV queda como estaba) y
     sólo para las tablas que traen diccionario (hoy, las de seguros). */
  function hojaDiccionario(tabla) {
    const datos = window.DICCIONARIO_SEGUROS && tabla && window.DICCIONARIO_SEGUROS[tabla];
    if (!datos || !datos.filas || !datos.filas.length) return null;
    const hoja = window.XLSX.utils.aoa_to_sheet([datos.cabecera].concat(datos.filas));
    hoja["!cols"] = [{ wch: 46 }, { wch: 10 }, { wch: 16 }, { wch: 46 }, { wch: 30 },
                     { wch: 14 }, { wch: 110 }];
    hoja["!autofilter"] = { ref: window.XLSX.utils.encode_range({ s: { r: 0, c: 0 },
      e: { r: datos.filas.length, c: datos.cabecera.length - 1 } }) };
    return hoja;
  }

  function libroXlsx(rows, cols, nombreHoja, tabla) {
    if (!window.XLSX) throw new Error("La librería de Excel (SheetJS) no está cargada en esta página.");
    const hoja = window.XLSX.utils.json_to_sheet(rows, { header: cols });
    const libro = window.XLSX.utils.book_new();
    window.XLSX.utils.book_append_sheet(libro, hoja, String(nombreHoja || "Datos").slice(0, 31));
    const diccionario = hojaDiccionario(tabla);
    if (diccionario) window.XLSX.utils.book_append_sheet(libro, diccionario, "Diccionario");
    const salida = window.XLSX.write(libro, { bookType: "xlsx", type: "array" });
    return new Blob([salida], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  }

  function descargar(blob, nombreArchivo) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = nombreArchivo;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  }

  async function empaquetar(filas, cols, { formato, nombre, limite, tamano, tabla }) {
    if (!window.JSZip) throw new Error("No se pudo empaquetar el .ZIP (JSZip no está cargado).");
    const zip = new window.JSZip();
    const total = Math.ceil(filas.length / tamano);
    for (let parte = 0; parte < total; parte += 1) {
      const bloque = filas.slice(parte * tamano, (parte + 1) * tamano);
      const sufijo = `parte_${parte + 1}_de_${total}`;
      if (formato === "csv") {
        zip.file(`${nombre}_${sufijo}.csv`, textoCsv(bloque, cols));
      } else {
        const hoja = window.XLSX.utils.json_to_sheet(bloque, { header: cols });
        const libro = window.XLSX.utils.book_new();
        window.XLSX.utils.book_append_sheet(libro, hoja, `Parte_${parte + 1}`);
        const diccionario = hojaDiccionario(tabla);
        if (diccionario) window.XLSX.utils.book_append_sheet(libro, diccionario, "Diccionario");
        zip.file(`${nombre}_${sufijo}.xlsx`, window.XLSX.write(libro, { bookType: "xlsx", type: "array" }));
      }
    }
    const blob = await zip.generateAsync({ type: "blob" });
    descargar(blob, `${nombre}_${marcaTiempo()}.zip`);
    return { filas: filas.length, archivos: total, comprimido: true };
  }

  /**
   * Descarga filas ya cargadas en memoria.
   * @returns {Promise<{filas:number, archivos:number, comprimido:boolean}>}
   */
  async function exportarFilas(rows, cols, opciones) {
    const op = opciones || {};
    const formato = op.formato === "xlsx" ? "xlsx" : "csv";
    const nombre = op.nombre || "datos";
    const filas = Array.isArray(rows) ? rows : [];
    const columnas = Array.isArray(cols) && cols.length ? cols : Object.keys(filas[0] || {});
    if (!filas.length) throw new Error("No hay filas para descargar con los criterios elegidos.");

    // El diccionario (hoja extra del Excel) se busca por tabla: sólo las tablas de seguros
    // lo traen por ahora; en las demás la descarga queda igual que antes.
    const tabla = op.diccionario || null;
    if (formato === "csv" && filas.length > LIMITE_ZIP_CSV && op.particionar !== false) {
      return empaquetar(filas, columnas, { formato, nombre, tamano: 150000, tabla });
    }
    if (formato === "xlsx" && filas.length > LIMITE_EXCEL) {
      return empaquetar(filas, columnas, { formato, nombre, tamano: 100000, tabla });
    }
    if (formato === "xlsx" && filas.length > LIMITE_ZIP_XLSX && op.particionar !== false) {
      return empaquetar(filas, columnas, { formato, nombre, tamano: 100000, tabla });
    }

    if (formato === "csv") {
      descargar(blobCsv(filas, columnas), `${nombre}_${marcaTiempo()}.csv`);
    } else {
      descargar(libroXlsx(filas, columnas, nombre, tabla), `${nombre}_${marcaTiempo()}.xlsx`);
    }
    return { filas: filas.length, archivos: 1, comprimido: false };
  }

  return { numero, bytes, textoCsv, blobCsv, hojaDiccionario, libroXlsx, descargar,
           exportarFilas, marcaTiempo };
})();
