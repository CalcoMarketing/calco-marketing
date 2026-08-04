/**
 * CALCO INDUSTRIA GRÁFICA — Google Ads Scripts
 * redistribuir_presupuesto.js
 *
 * QUÉ HACE
 * Una vez por semana, mira qué campaña está convirtiendo mejor (menor
 * costo por conversión) y le corre presupuesto diario desde la que peor
 * convierte, dentro de límites de seguridad para no vaciar ninguna
 * campaña ni pasarse del techo mensual acordado (USD 325).
 *
 * REGLAS DE SEGURIDAD (no negociables, están puestas a propósito):
 * - Nunca mueve más del 15% del presupuesto diario de una campaña en
 *   una sola corrida. Los cambios son graduales, no bandazos.
 * - Ninguna campaña puede bajar de un piso mínimo (ver PISOS_MINIMOS).
 *   C3 (marca) en particular no se toca casi nunca: es barata y su
 *   función es defensiva, no de volumen.
 * - Solo redistribuye entre campañas con AL MENOS 15 conversiones
 *   acumuladas cada una. Con menos datos, el costo por conversión es
 *   ruido estadístico, no una señal confiable.
 * - La suma total de los 3 presupuestos diarios nunca supera el techo
 *   mensual configurado, convertido a diario.
 *
 * CUÁNDO CORRE
 * Semanal, sugerido lunes 06:30 America/Montevideo (después del script
 * de pausar keywords).
 *
 * CÓMO INSTALARLO
 * Igual que los anteriores. Programar: Semanal, lunes 06:30.
 */

// ---------------------------------------------------------------------------
// CONFIGURACIÓN
// ---------------------------------------------------------------------------

const TECHO_MENSUAL_USD = 325;
const TECHO_DIARIO_TOTAL = TECHO_MENSUAL_USD / 30.4; // ≈ 10.70

const CONVERSIONES_MINIMAS_PARA_ACTUAR = 15;
const PORCENTAJE_MAXIMO_A_MOVER = 0.15; // 15% del presupuesto diario de la campaña

// Pisos mínimos de presupuesto diario, en USD. Ninguna campaña baja de esto.
const PISOS_MINIMOS = {
  'C1 - Productos Core': 4.00,
  'C2 - Urgentes': 1.50,
  'C3 - Marca defensiva': 1.00
};

// ---------------------------------------------------------------------------
// EJECUCIÓN
// ---------------------------------------------------------------------------

function main() {
  Logger.log('=== Calco: redistribución semanal de presupuesto ===');
  Logger.log('Fecha: ' + new Date());

  const campanas = obtenerDatosCampanas();

  if (campanas.length < 2) {
    Logger.log('Menos de 2 campañas activas encontradas. Nada que redistribuir.');
    return;
  }

  const elegibles = campanas.filter(function(c) {
    return c.conversiones >= CONVERSIONES_MINIMAS_PARA_ACTUAR;
  });

  if (elegibles.length < 2) {
    Logger.log('Menos de 2 campañas con ' + CONVERSIONES_MINIMAS_PARA_ACTUAR
      + '+ conversiones acumuladas. Todavía es pronto para redistribuir '
      + 'con confianza estadística. No se hacen cambios esta semana.');
    logResumenCampanas(campanas);
    return;
  }

  elegibles.sort(function(a, b) {
    return a.costoPorConversion - b.costoPorConversion;
  });

  const mejor = elegibles[0];
  const peor = elegibles[elegibles.length - 1];

  if (mejor.nombre === peor.nombre) {
    Logger.log('Solo hay una campaña elegible. No se redistribuye.');
    return;
  }

  Logger.log('Mejor costo por conversión: ' + mejor.nombre + ' ($'
    + mejor.costoPorConversion.toFixed(2) + ')');
  Logger.log('Peor costo por conversión: ' + peor.nombre + ' ($'
    + peor.costoPorConversion.toFixed(2) + ')');

  const pisoPeor = PISOS_MINIMOS[peor.nombre] || 1.00;
  const montoMaximoAMover = peor.presupuestoActual * PORCENTAJE_MAXIMO_A_MOVER;
  const margenDisponibleEnPeor = peor.presupuestoActual - pisoPeor;
  const montoAMover = Math.min(montoMaximoAMover, margenDisponibleEnPeor);

  if (montoAMover <= 0) {
    Logger.log(peor.nombre + ' ya está en su piso mínimo ($' + pisoPeor
      + '). No se le puede quitar presupuesto.');
    return;
  }

  const nuevoPresupuestoMejor = mejor.presupuestoActual + montoAMover;
  const nuevoPresupuestoPeor = peor.presupuestoActual - montoAMover;

  const sumaTotal = campanas.reduce(function(acc, c) {
    if (c.nombre === mejor.nombre) return acc + nuevoPresupuestoMejor;
    if (c.nombre === peor.nombre) return acc + nuevoPresupuestoPeor;
    return acc + c.presupuestoActual;
  }, 0);

  if (sumaTotal > TECHO_DIARIO_TOTAL) {
    Logger.log('El movimiento propuesto superaría el techo diario total '
      + '($' + TECHO_DIARIO_TOTAL.toFixed(2) + '). No se aplica el cambio. '
      + 'Revisar manualmente.');
    return;
  }

  aplicarNuevoPresupuesto(mejor.campana, nuevoPresupuestoMejor);
  aplicarNuevoPresupuesto(peor.campana, nuevoPresupuestoPeor);

  Logger.log('APLICADO: ' + mejor.nombre + ' pasa de $'
    + mejor.presupuestoActual.toFixed(2) + ' a $'
    + nuevoPresupuestoMejor.toFixed(2) + '/día');
  Logger.log('APLICADO: ' + peor.nombre + ' pasa de $'
    + peor.presupuestoActual.toFixed(2) + ' a $'
    + nuevoPresupuestoPeor.toFixed(2) + '/día');

  logResumenCampanas(campanas);
}

// ---------------------------------------------------------------------------
// FUNCIONES AUXILIARES
// ---------------------------------------------------------------------------

function obtenerDatosCampanas() {
  const resultado = [];
  const iterator = AdsApp.campaigns()
    .withCondition("campaign.status = 'ENABLED'")
    .withCondition("campaign.advertising_channel_type = 'SEARCH'")
    .get();

  while (iterator.hasNext()) {
    const campana = iterator.next();
    const stats = campana.getStatsFor('LAST_30_DAYS');
    const conversiones = stats.getConversions();
    const costo = stats.getCost();
    const costoPorConversion = conversiones > 0 ? (costo / conversiones) : Infinity;

    resultado.push({
      campana: campana,
      nombre: campana.getName(),
      presupuestoActual: campana.getBudget().getAmount(),
      conversiones: conversiones,
      costo: costo,
      costoPorConversion: costoPorConversion
    });
  }

  return resultado;
}

function aplicarNuevoPresupuesto(campana, nuevoMonto) {
  // Redondeo a centavos para evitar valores con demasiados decimales
  const monto = Math.round(nuevoMonto * 100) / 100;
  campana.getBudget().setAmount(monto);
}

function logResumenCampanas(campanas) {
  Logger.log('--- Estado de campañas (últimos 30 días) ---');
  campanas.forEach(function(c) {
    const cpc = c.costoPorConversion === Infinity ? 'N/A (sin conversiones)'
      : '$' + c.costoPorConversion.toFixed(2);
    Logger.log('  ' + c.nombre + ' | Presupuesto: $'
      + c.presupuestoActual.toFixed(2) + '/día | Conversiones: '
      + c.conversiones + ' | Costo por conversión: ' + cpc);
  });
}
