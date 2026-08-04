/**
 * CALCO INDUSTRIA GRÁFICA — Google Ads Scripts
 * pausar_keywords_sin_conversion.js
 *
 * QUÉ HACE
 * Pausa automáticamente cualquier keyword con más de 30 clics acumulados
 * y CERO conversiones. Es la regla de higiene básica: una keyword que
 * generó 30+ clics sin una sola solicitud de presupuesto está quemando
 * plata sin aportar nada, y no vale la pena esperar más para actuar.
 *
 * No borra la keyword — la pausa. Queda visible en la cuenta con el
 * historial intacto, por si en el futuro conviene reactivarla con otro
 * anuncio o landing.
 *
 * SALVAGUARDA: nunca pausa keywords de la campaña "C3 – Marca defensiva".
 * Esa campaña se mide distinto (protección de marca, no volumen de leads)
 * y sus clics son tan baratos que no aplica la misma regla.
 *
 * CUÁNDO CORRE
 * Semanal, sugerido lunes 06:00 America/Montevideo, antes de que
 * arranque la semana de anuncios.
 *
 * CÓMO INSTALARLO
 * Igual que revisar_terminos_busqueda.js: Scripts → "+" → pegar → autorizar
 * → programar Semanal, lunes 06:00.
 */

// ---------------------------------------------------------------------------
// CONFIGURACIÓN
// ---------------------------------------------------------------------------

const CLICS_UMBRAL = 30;
const CONVERSIONES_MAXIMAS = 0; // pausa solo si conversiones === 0
const DIAS_A_EVALUAR = 'ALL_TIME'; // acumulado histórico de la keyword

// Nombre exacto de la campaña que NUNCA se toca con esta regla
const CAMPANA_EXCLUIDA = 'C3 - Marca defensiva';

// ---------------------------------------------------------------------------
// EJECUCIÓN
// ---------------------------------------------------------------------------

function main() {
  Logger.log('=== Calco: revisión semanal de keywords sin conversión ===');
  Logger.log('Fecha: ' + new Date());

  const keywords = AdsApp.keywords()
    .withCondition("campaign.name != '" + CAMPANA_EXCLUIDA + "'")
    .withCondition("ad_group_criterion.status = 'ENABLED'")
    .withCondition("metrics.clicks >= " + CLICS_UMBRAL)
    .forDateRange(DIAS_A_EVALUAR)
    .get();

  let pausadas = 0;
  let revisadas = 0;
  const detalle = [];

  while (keywords.hasNext()) {
    const keyword = keywords.next();
    revisadas++;

    const stats = keyword.getStatsFor(DIAS_A_EVALUAR);
    const clics = stats.getClicks();
    const conversiones = stats.getConversions();
    const costo = stats.getCost();

    if (clics >= CLICS_UMBRAL && conversiones <= CONVERSIONES_MAXIMAS) {
      keyword.pause();
      pausadas++;
      const linea = 'PAUSADA: "' + keyword.getText() + '" | Campaña: '
        + keyword.getCampaign().getName() + ' | Grupo: '
        + keyword.getAdGroup().getName() + ' | Clics: ' + clics
        + ' | Costo: $' + costo.toFixed(2) + ' | Conversiones: ' + conversiones;
      Logger.log(linea);
      detalle.push(linea);
    }
  }

  Logger.log('--- Resumen ---');
  Logger.log('Keywords evaluadas (>= ' + CLICS_UMBRAL + ' clics): ' + revisadas);
  Logger.log('Keywords pausadas por 0 conversiones: ' + pausadas);

  if (pausadas > 0) {
    enviarResumenPorMail(detalle);
  }
}

// ---------------------------------------------------------------------------
// NOTIFICACIÓN
// ---------------------------------------------------------------------------

function enviarResumenPorMail(detalle) {
  // Se envía solo cuando hay pausas reales, para no generar ruido semanal
  // si no pasó nada. Reemplazar el mail por el que corresponda.
  const destinatario = 'marketing@calco.uy';
  const asunto = 'Calco Ads — ' + detalle.length + ' keyword(s) pausada(s) esta semana';
  const cuerpo = 'Se pausaron automáticamente las siguientes keywords por '
    + 'acumular ' + CLICS_UMBRAL + '+ clics sin conversión:\n\n'
    + detalle.join('\n')
    + '\n\nQuedan pausadas, no eliminadas. Se pueden reactivar manualmente '
    + 'desde Google Ads si se ajusta el anuncio o la landing.';

  try {
    MailApp.sendEmail(destinatario, asunto, cuerpo);
  } catch (e) {
    Logger.log('No se pudo enviar el mail de resumen: ' + e);
  }
}
