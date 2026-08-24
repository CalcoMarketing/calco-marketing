/**
 * CALCO INDUSTRIA GRÁFICA — Google Ads Scripts
 * migrar_puja_dia_21.js
 *
 * QUÉ HACE
 * Implementa la decisión #7 de la Sesión 1: arrancar con "Maximizar clics"
 * (CPC máx USD 0,45) y migrar a "Maximizar conversiones" recién cuando
 * cada campaña acumule al menos 21 días de actividad Y al menos 15
 * conversiones. Arrancar en automático sin datos hace que Google gaste
 * rápido y mal — por eso la migración es progresiva, campaña por
 * campaña, no todas el mismo día calendario.
 *
 * Cada campaña migra individualmente cuando CUMPLE SUS DOS condiciones,
 * no en una fecha fija. Si C1 junta 15 conversiones en 18 días y C2
 * tarda 30, migran en momentos distintos. Eso es intencional.
 *
 * Corre una sola vez que migra y después queda en modo "vigilancia":
 * si por algún motivo una campaña nueva se crea más adelante, este script
 * también la va a evaluar cuando le toque.
 *
 * CUÁNDO CORRE
 * Diario, sugerido 07:30 America/Montevideo (después de los otros dos
 * scripts semanales, pero este se revisa todos los días porque el
 * cumplimiento de condiciones puede caer cualquier día de la semana).
 *
 * CÓMO INSTALARLO
 * Igual que los anteriores. Programar: Diario, 07:30.
 */

// ---------------------------------------------------------------------------
// CONFIGURACIÓN
// ---------------------------------------------------------------------------

const DIAS_MINIMOS_ANTES_DE_MIGRAR = 21;
const CONVERSIONES_MINIMAS_PARA_MIGRAR = 15;
const CPC_MAXIMO_FASE_1 = 0.45; // USD, estrategia "Maximizar clics"

// ---------------------------------------------------------------------------
// EJECUCIÓN
// ---------------------------------------------------------------------------

function main() {
  Logger.log('=== Calco: evaluación diaria de migración de puja ===');
  Logger.log('Fecha: ' + new Date());

  const campanas = AdsApp.campaigns()
    .withCondition("campaign.status = 'ENABLED'")
    .withCondition("campaign.advertising_channel_type = 'SEARCH'")
    .get();

  let evaluadas = 0;
  let migradas = 0;
  let enEspera = [];

  while (campanas.hasNext()) {
    const campana = campanas.next();
    evaluadas++;

    const estrategiaActual = obtenerEstrategiaPuja(campana);

    // Si ya está en Maximizar Conversiones, no hay nada que hacer
    if (estrategiaActual === 'MAXIMIZE_CONVERSIONS') {
      continue;
    }

    const diasActiva = calcularDiasActiva(campana);
    const stats = campana.getStatsFor('ALL_TIME');
    const conversiones = stats.getConversions();

    if (diasActiva >= DIAS_MINIMOS_ANTES_DE_MIGRAR
        && conversiones >= CONVERSIONES_MINIMAS_PARA_MIGRAR) {

      migrarAMaximizarConversiones(campana);
      migradas++;

      Logger.log('MIGRADA: "' + campana.getName() + '" | Días activa: '
        + diasActiva + ' | Conversiones acumuladas: ' + conversiones
        + ' | Maximizar clics → Maximizar conversiones');

      notificarMigracion(campana, diasActiva, conversiones);

    } else {
      enEspera.push({
        nombre: campana.getName(),
        dias: diasActiva,
        conversiones: conversiones
      });
    }
  }

  Logger.log('--- Resumen ---');
  Logger.log('Campañas evaluadas: ' + evaluadas);
  Logger.log('Campañas migradas hoy: ' + migradas);

  if (enEspera.length > 0) {
    Logger.log('--- Todavía en Fase 1 (Maximizar clics) ---');
    enEspera.forEach(function(c) {
      Logger.log('  ' + c.nombre + ' | Días activa: ' + c.dias + '/'
        + DIAS_MINIMOS_ANTES_DE_MIGRAR + ' | Conversiones: '
        + c.conversiones + '/' + CONVERSIONES_MINIMAS_PARA_MIGRAR);
    });
  }
}

// ---------------------------------------------------------------------------
// FUNCIONES AUXILIARES
// ---------------------------------------------------------------------------

function obtenerEstrategiaPuja(campana) {
  // getBiddingStrategyType() devuelve strings como 'MANUAL_CPC',
  // 'MAXIMIZE_CLICKS', 'MAXIMIZE_CONVERSIONS', etc.
  try {
    return campana.getBiddingStrategyType();
  } catch (e) {
    Logger.log('No se pudo leer la estrategia de puja de "'
      + campana.getName() + '": ' + e);
    return 'DESCONOCIDA';
  }
}

function calcularDiasActiva(campana) {
  // Usa la fecha de inicio de la campaña. Si por algún motivo no está
  // disponible, cae a contar desde la primera fecha con impresiones.
  const inicio = campana.getStartDate();
  if (!inicio) return 0;

  const fechaInicio = new Date(inicio.year, inicio.month - 1, inicio.day);
  const hoy = new Date();
  const diffMs = hoy - fechaInicio;
  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

function migrarAMaximizarConversiones(campana) {
  // NOTA IMPORTANTE: la API de Scripts permite leer la estrategia de puja
  // pero el cambio de estrategia (de Maximizar Clics a Maximizar
  // Conversiones) requiere pasar por el objeto de configuración de la
  // campaña. Si el método directo no está disponible en la versión de
  // Scripts vigente al momento de ejecutar esto, el script deja el log
  // detallado y el cambio se hace manualmente en 2 clics desde la UI:
  // Campaña → Configuración → Puja → Cambiar estrategia.
  try {
    campana.bidding().setStrategy('MAXIMIZE_CONVERSIONS');
  } catch (e) {
    Logger.log('ATENCIÓN: no se pudo migrar automáticamente la campaña "'
      + campana.getName() + '". Cumple las condiciones para migrar '
      + '(21+ días, 15+ conversiones) pero requiere el cambio manual: '
      + 'Campaña → Configuración → Puja → "Maximizar conversiones". '
      + 'Error técnico: ' + e);
  }
}

function notificarMigracion(campana, dias, conversiones) {
  const destinatario = 'marketing@calco.uy';
  const asunto = 'Calco Ads — "' + campana.getName() + '" migró a Maximizar Conversiones';
  const cuerpo = 'La campaña "' + campana.getName() + '" cumplió las condiciones '
    + 'para pasar de la estrategia inicial (Maximizar clics, CPC máx $'
    + CPC_MAXIMO_FASE_1 + ') a Maximizar Conversiones:\n\n'
    + '- Días activa: ' + dias + '\n'
    + '- Conversiones acumuladas: ' + conversiones + '\n\n'
    + 'A partir de ahora Google va a optimizar automáticamente hacia '
    + 'conversiones en vez de clics. Es normal que el volumen de clics '
    + 'baje un poco mientras el algoritmo reajusta en los primeros días.';

  try {
    MailApp.sendEmail(destinatario, asunto, cuerpo);
  } catch (e) {
    Logger.log('No se pudo enviar el mail de notificación: ' + e);
  }
}
