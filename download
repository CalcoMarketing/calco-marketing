/**
 * CALCO INDUSTRIA GRÁFICA — Google Ads Scripts
 * revisar_terminos_busqueda.js
 *
 * QUÉ HACE
 * Revisa los términos de búsqueda reales que gatillaron un clic en los
 * últimos 7 días y agrega como negativa (a nivel cuenta) cualquiera que
 * coincida con las categorías de intención equivocada que ya identificamos
 * en la auditoría: "calco" como adhesivo, DIY/gratis, empleo, equipos de
 * impresión, otros países, servicios que no ofrecemos.
 *
 * No agrega negativas "a ciegas": solo actúa sobre términos que matchean
 * contra estas listas ya validadas. Términos ambiguos quedan afuera del
 * script y se listan en el log para revisión humana.
 *
 * CUÁNDO CORRE
 * Diario, sugerido 07:00 America/Montevideo (antes de que arranquen los
 * anuncios a las 08:00).
 *
 * CÓMO INSTALARLO
 * 1. Google Ads → Herramientas y configuración → Acciones masivas → Scripts
 * 2. Botón "+" → pegar este archivo completo
 * 3. Autorizar
 * 4. "Vista previa" antes de la primera ejecución en modo automático,
 *    para confirmar que no hay sorpresas
 * 5. Programar: Diario, 07:00
 */

// ---------------------------------------------------------------------------
// CONFIGURACIÓN
// ---------------------------------------------------------------------------

const DIAS_A_REVISAR = 7;
const CLICS_MINIMOS_PARA_EVALUAR = 1; // revisa desde el primer clic
const LISTA_NEGATIVA_CUENTA = 'Calco - Negativas Cuenta'; // nombre de la lista compartida

// Categorías ya validadas en la auditoría (Sesión 1, 31/07/2026).
// Cualquier término de búsqueda que CONTENGA alguna de estas palabras
// se marca como negativa automática.
const PATRONES_NEGATIVOS = {
  'intencion_calco_adhesivo': [
    'calcos para autos', 'calcomanias', 'calcomanía', 'pegotines', 'pegotin',
    'stickers para autos', 'vinilos para autos', 'tuning', 'calcos moto',
    'adhesivos deportivos', 'tatuajes temporales'
  ],
  'competidores': [
    'calco impresos', 'calco sport', 'calco sport adhesivos'
  ],
  'gratis_diy': [
    'gratis', 'gratuito', 'plantilla', 'plantillas', 'molde', 'moldes',
    'como hacer', 'paso a paso', 'diy', 'casero', 'tutorial', 'pdf descargar'
  ],
  'empleo_educacion': [
    'empleo', 'trabajo', 'curso', 'cursos', 'carrera', 'sueldo', 'salario',
    'pasantia', 'que es', 'significado'
  ],
  'equipos_no_vendemos': [
    'impresora', 'impresoras', 'cartucho', 'cartuchos', 'tinta', 'toner',
    'plotter comprar', 'reparacion', 'service', 'maquina de imprimir',
    'comprar impresora', 'impresion 3d'
  ],
  'otros_paises': [
    'argentina', 'buenos aires', 'brasil', 'brazil', 'chile', 'paraguay',
    'mexico', 'espana', 'españa', 'peru', 'colombia', 'alibaba', 'china'
  ],
  'servicios_no_ofrecemos': [
    'fotocopias', 'fotocopiadora', 'escaneo', 'anillado',
    'plastificado documentos', 'sellos de goma', 'remeras', 'sublimacion',
    'bordado', 'imprenta de dinero'
  ]
};

// ---------------------------------------------------------------------------
// EJECUCIÓN
// ---------------------------------------------------------------------------

function main() {
  Logger.log('=== Calco: revisión diaria de términos de búsqueda ===');
  Logger.log('Fecha: ' + new Date());

  const listaNegativa = obtenerOCrearListaNegativa(LISTA_NEGATIVA_CUENTA);
  const terminos = obtenerTerminosDeBusqueda(DIAS_A_REVISAR);

  let agregados = 0;
  let paraRevision = [];
  let yaExistentes = 0;

  const existentes = obtenerNegativasExistentes(listaNegativa);

  for (const t of terminos) {
    const termino = t.termino.toLowerCase().trim();

    if (existentes.has(termino)) {
      yaExistentes++;
      continue;
    }

    const categoria = clasificarTermino(termino);

    if (categoria) {
      agregarNegativa(listaNegativa, termino);
      existentes.add(termino);
      agregados++;
      Logger.log('NEGATIVA AGREGADA [' + categoria + ']: "' + termino + '" '
        + '(clics: ' + t.clics + ', costo: $' + t.costo.toFixed(2) + ')');
    } else if (t.clics >= 3 && t.conversiones === 0) {
      // Términos con clics reales pero sin conversión y sin match en
      // ninguna lista: no se tocan automáticamente, quedan para que un
      // humano decida. Evita falsos positivos sobre búsquedas legítimas
      // que todavía no convirtieron.
      paraRevision.push(termino + ' (clics: ' + t.clics + ', costo: $'
        + t.costo.toFixed(2) + ')');
    }
  }

  Logger.log('--- Resumen ---');
  Logger.log('Negativas nuevas agregadas: ' + agregados);
  Logger.log('Ya existentes (sin duplicar): ' + yaExistentes);

  if (paraRevision.length > 0) {
    Logger.log('--- Términos para revisión humana (sin match automático) ---');
    paraRevision.forEach(function(t) { Logger.log('  - ' + t); });
  }
}

// ---------------------------------------------------------------------------
// FUNCIONES AUXILIARES
// ---------------------------------------------------------------------------

function clasificarTermino(termino) {
  for (const categoria in PATRONES_NEGATIVOS) {
    const patrones = PATRONES_NEGATIVOS[categoria];
    for (const patron of patrones) {
      if (termino.indexOf(patron) !== -1) {
        return categoria;
      }
    }
  }
  return null;
}

function obtenerTerminosDeBusqueda(dias) {
  const resultado = [];
  const query = 'SELECT search_term_view.search_term, metrics.clicks, '
    + 'metrics.cost_micros, metrics.conversions '
    + 'FROM search_term_view '
    + 'WHERE segments.date DURING LAST_' + dias + '_DAYS '
    + 'AND metrics.clicks >= ' + CLICS_MINIMOS_PARA_EVALUAR;

  const report = AdsApp.report(query);
  const rows = report.rows();

  while (rows.hasNext()) {
    const row = rows.next();
    resultado.push({
      termino: row['search_term_view.search_term'],
      clics: parseInt(row['metrics.clicks'], 10),
      costo: parseInt(row['metrics.cost_micros'], 10) / 1000000,
      conversiones: parseFloat(row['metrics.conversions'])
    });
  }

  return resultado;
}

function obtenerOCrearListaNegativa(nombre) {
  const iterator = AdsApp.negativeKeywordLists()
    .withCondition("shared_set.name = '" + nombre + "'")
    .get();

  if (iterator.hasNext()) {
    return iterator.next();
  }

  Logger.log('Lista "' + nombre + '" no existe. Creándola...');
  const operation = AdsApp.newNegativeKeywordListBuilder()
    .withName(nombre)
    .build();
  const lista = operation.getResult();

  // Adjuntar la lista a todas las campañas activas de la cuenta
  const campanas = AdsApp.campaigns().withCondition("campaign.status = 'ENABLED'").get();
  while (campanas.hasNext()) {
    const campana = campanas.next();
    campana.addNegativeKeywordList(lista);
  }

  return lista;
}

function obtenerNegativasExistentes(lista) {
  const set = new Set();
  const keywords = lista.negativeKeywords().get();
  while (keywords.hasNext()) {
    set.add(keywords.next().getText().toLowerCase().trim());
  }
  return set;
}

function agregarNegativa(lista, termino) {
  // Frase negativa (no exacta): bloquea el término y variantes cercanas,
  // sin ser tan amplia como para pisar búsquedas legítimas.
  lista.addNegativeKeyword('"' + termino + '"');
}
