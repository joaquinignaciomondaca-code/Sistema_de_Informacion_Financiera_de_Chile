/**
 * Conector comunitario de Looker Studio para los marts de SIF Chile.
 *
 * Qué hace: lee `docs/looker/catalogo.json`, muestra una lista con los marts
 * publicados y devuelve a Looker Studio el CSV elegido como tabla. No hay
 * backend: el conector sólo descarga archivos estáticos del sitio.
 *
 * Cómo se instala (10 minutos, sin servidores):
 *   1. script.google.com → Nuevo proyecto.
 *   2. Pega este archivo como `Code.gs` y el `appsscript.json` de al lado.
 *   3. Implementar → Implementaciones de prueba → copia el ID de la
 *      implementación Head.
 *   4. Abre https://datastudio.google.com/datasources/create?connectorId=ID
 *      y autoriza el permiso de script.external_request.
 *
 * Limitaciones honestas: Apps Script tiene tiempo máximo de ejecución y el
 * conector devuelve filas, no agregados. Está pensado para los marts (máximo
 * ~26.000 filas). Para el detalle de 19 millones de filas usa BigQuery, que sí
 * agrega del lado del motor (ver docs/looker/README.md).
 */

var CATALOGO_URL =
  'https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/looker/catalogo.json';

var cc = DataStudioApp.createCommunityConnector();

function getAuthType() {
  return cc
    .newAuthTypeResponse()
    .setAuthType(cc.AuthType.NONE)
    .build();
}

function isAdminUser() {
  return false;
}

function getConfig() {
  var config = cc.getConfig();
  config
    .newInfo()
    .setId('que_es')
    .setText(
      'Marts agregados del Sistema de Información Financiera de Chile (CMF, ' +
      'Banco Central y Superintendencia de Pensiones). Cada tabla trae su ' +
      'período, su grano y su unidad en el catálogo. El detalle instrumento por ' +
      'instrumento no está acá: vive en los Parquet y en el catálogo API v2.'
    );

  var seleccion = config
    .newSelectSingle()
    .setId('mart')
    .setName('Tabla')
    .setHelpText('Una tabla por dashboard. Elige según el sector que quieras mirar.');

  var catalogo = leerCatalogo();
  catalogo.marts.forEach(function (mart) {
    seleccion.addOption(
      config
        .newOptionBuilder()
        .setLabel(mart.titulo + ' · ' + mart.periodicidad.toLowerCase())
        .setValue(mart.id)
    );
  });
  if (catalogo.marts.length > 0) {
    seleccion.setAllowOverride(false);
  }

  // Los marts ya vienen recortados por período; si Looker pidiera un rango,
  // habría que filtrar en el conector y perderíamos la fila de contexto. El
  // filtro de fechas se hace en el informe, sobre la dimensión `fecha`.
  config.setDateRangeRequired(false);
  return config.build();
}

function getSchema(request) {
  var mart = buscarMart(request.configParams);
  return { schema: camposDe(mart).build() };
}

function getData(request) {
  var mart = buscarMart(request.configParams);
  var campos = camposDe(mart).forIds(
    request.fields.map(function (f) {
      return f.name;
    })
  );
  var pedidos = request.fields.map(function (f) {
    return f.name;
  });

  var filas;
  try {
    filas = leerCsv(mart.url);
  } catch (e) {
    cc.newUserError()
      .setText('No se pudo descargar el mart. Revisa que el sitio responda.')
      .setDebugText('Error al bajar ' + mart.url + ': ' + e)
      .throwException();
  }

  var cabecera = filas.shift();
  var indices = {};
  cabecera.forEach(function (nombre, i) {
    indices[nombre] = i;
  });
  var faltantes = pedidos.filter(function (n) {
    return !(n in indices);
  });
  if (faltantes.length > 0) {
    cc.newUserError()
      .setText('El mart no publica las columnas pedidas: ' + faltantes.join(', '))
      .setDebugText('Cabecera publicada: ' + cabecera.join(', '))
      .throwException();
  }

  var tipos = {};
  mart.columnas.forEach(function (c) {
    tipos[c.nombre] = c.tipo;
  });

  // El orden de los valores debe ser exactamente el del esquema que devolvemos
  // (`forIds` conserva el orden de declaración, no el de la solicitud). Si no,
  // Looker Studio pinta las columnas corridas.
  var orden = campos.build().map(function (campo) {
    return campo.id;
  });

  var datos = [];
  filas.forEach(function (fila) {
    if (fila.length !== cabecera.length) return; // línea en blanco o rota
    datos.push({
      values: orden.map(function (nombre) {
        return formatear(fila[indices[nombre]], tipos[nombre]);
      }),
    });
  });

  return { schema: campos.build(), rows: datos };
}

/* ----------------------------- utilidades ------------------------------ */

function leerCatalogo() {
  var respuesta = UrlFetchApp.fetch(CATALOGO_URL, { muteHttpExceptions: true });
  if (respuesta.getResponseCode() !== 200) {
    cc.newUserError()
      .setText('No se pudo leer el catálogo de marts de SIF Chile.')
      .setDebugText('HTTP ' + respuesta.getResponseCode() + ' en ' + CATALOGO_URL)
      .throwException();
  }
  return JSON.parse(respuesta.getContentText('UTF-8'));
}

function buscarMart(configParams) {
  var id = configParams && configParams.mart;
  var catalogo = leerCatalogo();
  if (!id) id = catalogo.marts[0].id;
  var encontrado = catalogo.marts.filter(function (m) {
    return m.id === id;
  })[0];
  if (!encontrado) {
    cc.newUserError()
      .setText('La tabla «' + id + '» no está en el catálogo.')
      .setDebugText('Marts publicados: ' + catalogo.marts.map(function (m) { return m.id; }).join(', '))
      .throwException();
  }
  encontrado.url = catalogo.base + encontrado.url;
  return encontrado;
}

function camposDe(mart) {
  var fields = cc.getFields();
  var tipos = cc.FieldType;
  var agregaciones = cc.AggregationType;

  mart.columnas.forEach(function (columna) {
    var tipo = String(columna.tipo || 'TEXT').toUpperCase();
    if (tipo === 'DATE') {
      fields
        .newDimension()
        .setId(columna.nombre)
        .setName(etiqueta(columna.nombre))
        .setType(tipos.YEAR_MONTH_DAY);
      return;
    }
    if (tipo === 'NUMBER') {
      var campo = fields
        .newMetric()
        .setId(columna.nombre)
        .setName(etiqueta(columna.nombre))
        .setType(tipos.NUMBER);
      campo.setAggregation(
        String(columna.agregacion || 'sum').toLowerCase() === 'avg'
          ? agregaciones.AVG
          : agregaciones.SUM
      );
      return;
    }
    if (tipo === 'BOOLEAN') {
      fields
        .newDimension()
        .setId(columna.nombre)
        .setName(etiqueta(columna.nombre))
        .setType(tipos.BOOLEAN);
      return;
    }
    fields
      .newDimension()
      .setId(columna.nombre)
      .setName(etiqueta(columna.nombre))
      .setType(tipos.TEXT);
  });

  return fields;
}

function etiqueta(nombre) {
  var t = String(nombre).replace(/_/g, ' ');
  return t.charAt(0).toUpperCase() + t.slice(1);
}

function formatear(valor, tipo) {
  if (valor === undefined || valor === null || valor === '') return null;
  var t = String(tipo || 'TEXT').toUpperCase();
  if (t === 'NUMBER') {
    var n = Number(String(valor).replace(',', '.'));
    return isNaN(n) ? null : n;
  }
  if (t === 'BOOLEAN') {
    return String(valor).toLowerCase() === 'true';
  }
  if (t === 'DATE') {
    // Looker Studio espera la fecha compacta AAAAMMDD en los conectores
    // comunitarios; el CSV la publica como AAAA-MM-DD.
    return String(valor).slice(0, 10).replace(/-/g, '');
  }
  return String(valor);
}

/** Parser CSV mínimo (RFC 4180): comillas dobles y saltos dentro de comillas. */
function leerCsv(url) {
  var respuesta = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
  if (respuesta.getResponseCode() !== 200) {
    throw new Error('HTTP ' + respuesta.getResponseCode());
  }
  var texto = respuesta.getContentText('UTF-8');
  if (texto.charCodeAt(0) === 0xfeff) texto = texto.slice(1);

  var filas = [];
  var fila = [];
  var campo = '';
  var entreComillas = false;
  for (var i = 0; i < texto.length; i++) {
    var c = texto.charAt(i);
    if (entreComillas) {
      if (c === '"') {
        if (texto.charAt(i + 1) === '"') {
          campo += '"';
          i++;
        } else {
          entreComillas = false;
        }
      } else {
        campo += c;
      }
      continue;
    }
    if (c === '"') {
      entreComillas = true;
    } else if (c === ',') {
      fila.push(campo);
      campo = '';
    } else if (c === '\n') {
      fila.push(campo);
      filas.push(fila);
      fila = [];
      campo = '';
    } else if (c !== '\r') {
      campo += c;
    }
  }
  if (campo !== '' || fila.length > 0) {
    fila.push(campo);
    filas.push(fila);
  }
  return filas;
}
