/**
 * CALCO INDUSTRIA GRÁFICA — Google Ads Scripts
 * pausar_keywords_sin_conversion.js
 *
 * QUÉ HACE
 * Una vez por semana, revisa todas las keywords activas de las campañas
 * de Búsqueda y pausa las que acumularon 30 o más clics sin ninguna
 * conversión en los últimos 30 días. Esas keywords ya tuvieron volumen
 * suficiente para que el algoritmo aprenda algo y, sin embargo, no
 * convirtieron: siguen gastando presupuesto sin traer resultados.
 *
 * REGLAS DE SEGURIDAD (no negociables, están puestas a propósito):
 * - Nunca toca keywords de "C3 - Marca defensiva". Esa campaña es barata
 *   y su función es defensiva, no de volumen: no importa si sus keywords
 *   no "convierten" en el sentido estricto, protegen la marca.
 * - PAUSA, no elimina. Todo reversible con un clic desde la interfaz.
 * - Nunca pausa la última keyword activa de un grupo de anuncios: un
 *   grupo sin ninguna keyword activa deja de servir anuncios sin que
 *   nadie lo note hasta mucho después. Si una keyword es la última
 *   elegible, queda para revisión humana en el log en vez de pausarse.
 * - Umbral configurable, pero pensado para esta cuenta (330/mes,
 *   volumen bajo): 30 clics es una muestra chica en términos absolutos,
 *   así que el corte no es agresivo — evita pausar por 2 o 3 clics
 *   sueltos que todavía no significan nada.
 *
 * CUÁNDO CORRE
 * Semanal, sugerido lunes 06:00 America/Montevideo (antes del script de
 * redistribuir presupuesto, que corre 06:30 el mismo día — así el
 * presupuesto se redistribuye ya sin las keywords muertas compitiendo
 * por él).
 *
 * CÓMO INSTALARLO
 * Igual que los anteriores. Programar: Semanal, lunes 06:00.
 */

// ---------------------------------------------------------------------------
// CONFIGURACIÓN
// ---------------------------------------------------------------------------

const DIAS_A_REVISAR = 30;
const CLICS_MINIMOS_PARA_PAUSAR = 30;
const CAMPANA_EXCLUIDA = 'C3 - Marca defensiva'; // nunca se toca

// ---------------------------------------------------------------------------
// EJECUCIÓN
// ---------------------------------------------------------------------------

function main() {
  Logger.log('=== Calco: pausado semanal de keywords sin conversión ===');
  Logger.log('Fecha: ' + new Date());

  const keywords = obtenerKeywordsCandidatas();

  let pausadas = 0;
  let paraRevision = [];
  let excluidasPorMarca = 0;

  for (const k of keywords) {
    if (k.campana === CAMPANA_EXCLUIDA) {
      excluidasPorMarca++;
      continue;
    }

    if (k.esUltimaDelGrupo) {
      paraRevision.push(
        k.texto + ' (grupo: ' + k.grupo + ', clics: ' + k.clics
        + ', costo: $' + k.costo.toFixed(2) + ') — es la ÚNICA keyword '
        + 'activa de su grupo de anuncios, no se pausa automáticamente'
      );
      continue;
    }

    k.keyword.pause();
    pausadas++;
    Logger.log('PAUSADA: "' + k.texto + '" | Campaña: ' + k.campana
      + ' | Grupo: ' + k.grupo + ' | Clics (' + DIAS_A_REVISAR + 'd): '
      + k.clics + ' | Costo: $' + k.costo.toFixed(2) + ' | Conversiones: 0');
  }

  Logger.log('--- Resumen ---');
  Logger.log('Keywords pausadas: ' + pausadas);
  Logger.log('Excluidas por ser de la campaña de marca defensiva: ' + excluidasPorMarca);

  if (paraRevision.length > 0) {
    Logger.log('--- Para revisión humana (última keyword activa del grupo) ---');
    paraRevision.forEach(function(t) { Logger.log('  - ' + t); });
  }

  if (pausadas > 0) {
    notificarPausado(pausadas, paraRevision.length);
  }
}

// ---------------------------------------------------------------------------
// FUNCIONES AUXILIARES
// ---------------------------------------------------------------------------

function obtenerKeywordsCandidatas() {
  const resultado = [];

  const query = 'SELECT ad_group_criterion.keyword.text, '
    + 'ad_group.name, campaign.name, metrics.clicks, '
    + 'metrics.cost_micros, metrics.conversions, '
    + 'ad_group_criterion.criterion_id, ad_group.id '
    + 'FROM keyword_view '
    + 'WHERE segments.date DURING LAST_' + DIAS_A_REVISAR + '_DAYS '
    + 'AND ad_group_criterion.status = \'ENABLED\' '
    + 'AND campaign.status = \'ENABLED\' '
    + 'AND metrics.clicks >= ' + CLICS_MINIMOS_PARA_PAUSAR
    + ' AND metrics.conversions = 0';

  const report = AdsApp.report(query);
  const rows = report.rows();

  // Primero armamos la lista candidata, y por separado contamos cuántas
  // keywords activas le quedan a cada grupo de anuncios, para no dejar
  // ninguno en cero.
  const candidatas = [];
  while (rows.hasNext()) {
    const row = rows.next();
    candidatas.push({
      texto: row['ad_group_criterion.keyword.text'],
      grupo: row['ad_group.name'],
      grupoId: row['ad_group.id'],
      campana: row['campaign.name'],
      clics: parseInt(row['metrics.clicks'], 10),
      costo: parseInt(row['metrics.cost_micros'], 10) / 1000000,
      criterionId: row['ad_group_criterion.criterion_id'],
    });
  }

  if (candidatas.length === 0) {
    return resultado;
  }

  const conteoActivasPorGrupo = contarKeywordsActivasPorGrupo(
    candidatas.map(function(c) { return c.grupoId; })
  );

  for (const c of candidatas) {
    const keywordObj = obtenerObjetoKeyword(c.grupoId, c.criterionId);
    if (!keywordObj) {
      continue; // no se pudo resolver el objeto, se salta con seguridad
    }
    resultado.push({
      keyword: keywordObj,
      texto: c.texto,
      grupo: c.grupo,
      campana: c.campana,
      clics: c.clics,
      costo: c.costo,
      esUltimaDelGrupo: (conteoActivasPorGrupo[c.grupoId] || 0) <= 1,
    });
  }

  return resultado;
}

function contarKeywordsActivasPorGrupo(idsDeGrupo) {
  const conteo = {};
  const unicos = Array.from(new Set(idsDeGrupo));

  // AdsApp.keywords() con condición IN es más simple que reconsultar
  // report por report; se recorre una sola vez.
  const iterator = AdsApp.keywords()
    .withCondition("ad_group_criterion.status = 'ENABLED'")
    .get();

  while (iterator.hasNext()) {
    const kw = iterator.next();
    const idGrupo = kw.getAdGroup().getId();
    if (unicos.indexOf(idGrupo) === -1) {
      continue; // no es un grupo que nos interese, no hace falta contar
    }
    conteo[idGrupo] = (conteo[idGrupo] || 0) + 1;
  }

  return conteo;
}

function obtenerObjetoKeyword(idGrupo, idCriterio) {
  const iterator = AdsApp.keywords()
    .withCondition("ad_group_criterion.status = 'ENABLED'")
    .withCondition('ad_group.id = ' + idGrupo)
    .get();

  while (iterator.hasNext()) {
    const kw = iterator.next();
    if (String(kw.getId()) === String(idCriterio)) {
      return kw;
    }
  }
  return null;
}

function notificarPausado(cantidad, pendientesDeRevision) {
  const destinatario = 'marketing@calco.uy';
  const asunto = 'Calco Ads — ' + cantidad + ' keyword(s) pausada(s) sin conversión';
  let cuerpo = 'El script semanal pausó ' + cantidad + ' keyword(s) que acumularon '
    + CLICS_MINIMOS_PARA_PAUSAR + '+ clics en los últimos ' + DIAS_A_REVISAR
    + ' días sin ninguna conversión.\n\n'
    + 'Se puede reactivar cualquiera desde Google Ads si hace falta: '
    + 'quedan en estado Pausada, no se eliminó nada.\n\n'
    + 'La campaña de marca defensiva nunca se toca.';

  if (pendientesDeRevision > 0) {
    cuerpo += '\n\nAdemás, ' + pendientesDeRevision + ' keyword(s) cumplían '
      + 'la condición pero eran la única keyword activa de su grupo de '
      + 'anuncios, así que no se pausaron automáticamente. Ver el log del '
      + 'script para revisarlas a mano.';
  }

  try {
    MailApp.sendEmail(destinatario, asunto, cuerpo);
  } catch (e) {
    Logger.log('No se pudo enviar el mail de notificación: ' + e);
  }
}
