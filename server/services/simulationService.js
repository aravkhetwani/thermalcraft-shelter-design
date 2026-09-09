import materials from '../mockData/materials.json' with { type: 'json' };
import precomputedResults from '../mockData/simulationResults.json' with { type: 'json' };
import { config } from '../config.js';
import { requestAnsysSimulation } from './ansysClient.js';
import { formatSimulationResult } from './resultAdapter.js';
import { getClimateProfile } from './weatherService.js';

const materialsById = Object.fromEntries(materials.map((m) => [m.id, m]));

// Ventilation air-changes-per-hour by user-selected level, plus opening
// counts, drive how much of the total heat loss is attributed to openings.
const VENTILATION_ACH = { low: 0.8, medium: 1.5, high: 2.6 };

export function buildComboKey({ materialCombo, orientation, size, shape, region, season, openings }) {
  const combo = (materialCombo || 'rammed-earth').toLowerCase();
  const o = (orientation || 'south').toLowerCase();
  const s = (size || 'medium').toLowerCase();
  const sh = (shape || 'dome').toLowerCase();
  const r = (region || 'ladakh').toLowerCase();
  const se = (season || 'winter').toLowerCase();
  const op = normalizeOpenings(openings);
  return `${combo}_${o}_${s}_${sh}_${r}_${se}_d${op.doors}w${op.windows}${op.ventilation}`;
}

export function normalizeOpenings(openings) {
  const o = openings || {};
  return {
    doors: Number.isFinite(Number(o.doors)) ? Math.max(0, Math.round(Number(o.doors))) : 1,
    windows: Number.isFinite(Number(o.windows)) ? Math.max(0, Math.round(Number(o.windows))) : 2,
    ventilation: VENTILATION_ACH[(o.ventilation || 'medium').toLowerCase()] ? (o.ventilation || 'medium').toLowerCase() : 'medium',
  };
}

function seededRandom(seedStr) {
  let h = 0;
  for (let i = 0; i < seedStr.length; i++) {
    h = Math.imul(31, h) + seedStr.charCodeAt(i) | 0;
  }
  return () => {
    h = Math.imul(h ^ (h >>> 15), 1 | h);
    h ^= h + Math.imul(h ^ (h >>> 7), 61 | h);
    return ((h ^ (h >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Pure scoring model shared by single-result generation and the
 * optimization/comparison sweep, so "which combo is best" is always computed
 * the same way rather than duplicated per call site.
 */
export function computeCombinedFactor({ materialCombo, orientation, size, shape }) {
  const ids = (materialCombo || 'rammed-earth').split('+').map((s) => s.trim()).filter(Boolean);
  const layers = ids.map((id) => materialsById[id]).filter(Boolean);
  const effectiveLayers = layers.length ? layers : [materials[0]];

  const resistanceSum = effectiveLayers.reduce(
    (acc, m) => acc + m.thicknessCm / 100 / m.thermalConductivity,
    0
  );
  const massSum = effectiveLayers.reduce((acc, m) => acc + m.density * m.heatCapacity, 0);

  const orientationBoost = { south: 1.15, east: 1.05, west: 1.0, north: 0.85 }[
    (orientation || 'south').toLowerCase()
  ] ?? 1.0;
  const sizeFactor = { small: 1.08, medium: 1.0, large: 0.9 }[(size || 'medium').toLowerCase()] ?? 1.0;
  const shapeFactor = { dome: 1.1, rectangular: 0.95, custom: 1.0 }[(shape || 'dome').toLowerCase()] ?? 1.0;

  const insulationScore = Math.min(1, resistanceSum / 4) * 0.6 + Math.min(1, massSum / 500000) * 0.4;
  return { combinedFactor: insulationScore * orientationBoost * shapeFactor * sizeFactor, insulationScore };
}

/** More doors/windows/ventilation level → higher share of heat lost through openings. */
export function computeOpeningsLossFactor(openings) {
  const o = normalizeOpenings(openings);
  const ach = VENTILATION_ACH[o.ventilation];
  // Normalized against a "typical" reference opening (1 door, 2 windows, medium ACH).
  const referenceUnits = 1 + 2 * 0.6 + VENTILATION_ACH.medium * 1.2;
  const units = o.doors + o.windows * 0.6 + ach * 1.2;
  return Math.max(0.4, Math.min(2.2, units / referenceUnits));
}

/**
 * Formulaic fallback generator — used only when a combo isn't in the
 * precomputed mock dataset and ANSYS is offline/disabled. Produces plausible,
 * deterministic (seeded by comboKey) numbers so the same inputs always return
 * the same result.
 */
function generateMockResult(comboKey, params, climate, mostEfficientCombo) {
  const { materialCombo, orientation, size, shape, openings } = params;
  const rand = seededRandom(comboKey);
  const { combinedFactor, insulationScore } = computeCombinedFactor({ materialCombo, orientation, size, shape });
  const openingsLossFactor = computeOpeningsLossFactor(openings);

  const ambientValues = climate.ambientTemp.values;

  const nightBase = -4 + combinedFactor * 20 + (rand() - 0.5) * 2;
  const dayBase = nightBase + 10 + combinedFactor * 4;

  const insideValues = ambientValues.map((_, i) => {
    const hour = climate.ambientTemp.hours[i];
    const dayCurve = Math.sin(((hour - 6) / 24) * Math.PI * 2) * 0.5 + 0.5;
    return Number((nightBase + (dayBase - nightBase) * dayCurve).toFixed(1));
  });

  const totalSolarKwh = Number((38 + combinedFactor * 14 + rand() * 4).toFixed(1));
  const solarValues = climate.solarFlux.values.map((v) =>
    Number(((v / 1000) * (totalSolarKwh / 46.8)).toFixed(2))
  );

  const baseHeatLoss = 60 * (1 - insulationScore * 0.6);
  const roofW = Math.round(baseHeatLoss * 0.3);
  const wallW = Math.round(baseHeatLoss * 0.45);
  const openingsW = Math.round(baseHeatLoss * 0.2 * openingsLossFactor);

  const efficiencyScore = Math.round(Math.min(96, Math.max(30, 40 + combinedFactor * 55 - (openingsLossFactor - 1) * 12)));
  const energySavedPercent = Math.round(Math.min(90, Math.max(10, 20 + combinedFactor * 65 - (openingsLossFactor - 1) * 15)));

  // Vertical temperature profile: floor-to-roof stratification. Better
  // insulated / higher-thermal-mass combos (higher insulationScore) flatten
  // the gradient; poorly insulated ones stratify more (hot roof, cold floor).
  // Mirrors the shape of the real per-height profile ANSYS would report via
  // `spatial_3d.vertical_profile` (see Ansys simulation/engine/result_extractor.py).
  const avgInside = insideValues.reduce((a, b) => a + b, 0) / insideValues.length;
  const stratificationSpread = (1 - insulationScore) * 7 + 1.5;
  const verticalProfile = Array.from({ length: 10 }, (_, i) => {
    const heightFrac = Number((0.05 + i * 0.1).toFixed(2));
    const tempC = Number((avgInside + (heightFrac - 0.5) * stratificationSpread + (rand() - 0.5) * 0.4).toFixed(2));
    return { heightFrac, tempC };
  });

  return {
    id: comboKey,
    source: 'mock',
    insideTemp: { hours: climate.ambientTemp.hours, values: insideValues },
    ambientTemp: { hours: climate.ambientTemp.hours, values: ambientValues },
    solarEnergy: { hours: climate.solarFlux.hours, valuesKwh: solarValues },
    totalSolarKwh,
    heatFlow: { roofW, wallW, openingsW },
    efficiencyScore,
    mostEfficientCombo: mostEfficientCombo || 'Dome + South + Rammed Earth',
    energySavedPercent,
    verticalProfile,
  };
}

/**
 * Returns simulation results adhering to the frozen schema in server/schema.md.
 * In 'ansys-live' mode, delegates to the ANSYS MAPDL microservice.
 * Falls back to precomputed / mock dataset if service is unavailable or in 'mock' mode.
 */
export async function getResult(params = {}) {
  const comboKey = buildComboKey(params);

  // Live ANSYS Simulation Path
  if (config.simulationMode === 'ansys-live') {
    try {
      const rawResult = await requestAnsysSimulation(params);
      return formatSimulationResult(rawResult, 'ansys-live');
    } catch (err) {
      console.warn(`[simulationService] Live ANSYS run failed: ${err.message}. Falling back to precomputed/mock result.`);
    }
  }

  // Precomputed or Formulaic Fallback Path
  if (precomputedResults[comboKey]) {
    return formatSimulationResult(precomputedResults[comboKey], 'mock');
  }

  const climate = await getClimateProfile(params.region, params.season);
  const { findBestCombo } = await import('./optimizationService.js');
  const best = await findBestCombo(params);
  const mockGenerated = generateMockResult(comboKey, params, climate, best?.label);
  return formatSimulationResult(mockGenerated, 'mock');
}

export function getMaterials() {
  return materials;
}

export async function getClimate(region, season) {
  return getClimateProfile(region, season);
}

export { generateMockResult };
