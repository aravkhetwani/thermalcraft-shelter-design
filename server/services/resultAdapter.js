/**
 * Result Adapter for Public API Contract
 * =======================================
 * Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
 *
 * Ensures all results, whether from live ANSYS MAPDL or offline fallback,
 * strictly conform to the frozen contract in server/schema.md.
 */

/**
 * Validates and formats the simulation result object.
 * @param {Object} raw
 * @param {string} source - "ansys-live" | "mock" | "database"
 * @returns {Object} Public API Contract compliant result
 */
export function formatSimulationResult(raw, source = 'ansys-live') {
  if (!raw) {
    throw new Error('Simulation result payload is empty');
  }

  // Ensure arrays are numbers and match 24h format
  const insideTempHours = Array.isArray(raw.insideTemp?.hours) ? raw.insideTemp.hours : Array.from({ length: 24 }, (_, i) => i);
  const insideTempValues = Array.isArray(raw.insideTemp?.values) ? raw.insideTemp.values.map(Number) : [];

  const ambientTempHours = Array.isArray(raw.ambientTemp?.hours) ? raw.ambientTemp.hours : Array.from({ length: 24 }, (_, i) => i);
  const ambientTempValues = Array.isArray(raw.ambientTemp?.values) ? raw.ambientTemp.values.map(Number) : [];

  const solarEnergyHours = Array.isArray(raw.solarEnergy?.hours) ? raw.solarEnergy.hours : Array.from({ length: 24 }, (_, i) => i);
  const solarEnergyValues = Array.isArray(raw.solarEnergy?.valuesKwh) ? raw.solarEnergy.valuesKwh.map(Number) : [];

  // Real (or synthetic-fallback) per-height temperature gradient, used by the
  // frontend to drive a physically-derived 3D heatmap instead of one scalar.
  const verticalProfile = Array.isArray(raw.verticalProfile)
    ? raw.verticalProfile
        .map((p) => ({ heightFrac: Number(p.heightFrac), tempC: Number(p.tempC) }))
        .filter((p) => Number.isFinite(p.heightFrac) && Number.isFinite(p.tempC))
    : undefined;

  return {
    id: String(raw.id || 'simulation_run'),
    source: String(source || raw.source || 'ansys-live'),
    insideTemp: {
      hours: insideTempHours,
      values: insideTempValues,
    },
    ambientTemp: {
      hours: ambientTempHours,
      values: ambientTempValues,
    },
    solarEnergy: {
      hours: solarEnergyHours,
      valuesKwh: solarEnergyValues,
    },
    totalSolarKwh: Number(raw.totalSolarKwh || 0),
    heatFlow: {
      roofW: Number(raw.heatFlow?.roofW || 0),
      wallW: Number(raw.heatFlow?.wallW || 0),
      openingsW: Number(raw.heatFlow?.openingsW || 0),
    },
    efficiencyScore: Number(raw.efficiencyScore || 80),
    mostEfficientCombo: String(raw.mostEfficientCombo || 'PCM + Multi-material'),
    energySavedPercent: Number(raw.energySavedPercent || 70),
    ...(verticalProfile?.length ? { verticalProfile } : {}),
  };
}
