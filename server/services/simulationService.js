import materials from '../mockData/materials.json' with { type: 'json' };
import climateData from '../mockData/climateData.json' with { type: 'json' };
import precomputedResults from '../mockData/simulationResults.json' with { type: 'json' };
import { config } from '../config.js';
import { requestAnsysSimulation } from './ansysClient.js';
import { formatSimulationResult } from './resultAdapter.js';

const materialsById = Object.fromEntries(materials.map((m) => [m.id, m]));

export function buildComboKey({ materialCombo, orientation, size, shape }) {
  const combo = (materialCombo || 'rammed-earth').toLowerCase();
  const o = (orientation || 'south').toLowerCase();
  const s = (size || 'medium').toLowerCase();
  const sh = (shape || 'dome').toLowerCase();
  return `${combo}_${o}_${s}_${sh}`;
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
 * Formulaic fallback generator — used only when a combo isn't in the
 * precomputed mock dataset and ANSYS is offline/disabled. Produces plausible,
 * deterministic (seeded by comboKey) numbers so the same inputs always return
 * the same result.
 */
function generateMockResult(comboKey, { materialCombo, orientation, size, shape }) {
  const rand = seededRandom(comboKey);
  const ids = (materialCombo || 'rammed-earth').split('+').map((s) => s.trim()).filter(Boolean);
  const layers = ids.map((id) => materialsById[id]).filter(Boolean);
  const effectiveLayers = layers.length ? layers : [materials[0]];

  const resistanceSum = effectiveLayers.reduce(
    (acc, m) => acc + m.thicknessCm / 100 / m.thermalConductivity,
    0
  );
  const massSum = effectiveLayers.reduce(
    (acc, m) => acc + m.density * m.heatCapacity,
    0
  );

  const orientationBoost = { south: 1.15, east: 1.05, west: 1.0, north: 0.85 }[
    (orientation || 'south').toLowerCase()
  ] ?? 1.0;
  const sizeFactor = { small: 1.08, medium: 1.0, large: 0.9 }[
    (size || 'medium').toLowerCase()
  ] ?? 1.0;
  const shapeFactor = { dome: 1.1, rectangular: 0.95, custom: 1.0 }[
    (shape || 'dome').toLowerCase()
  ] ?? 1.0;

  const insulationScore = Math.min(1, resistanceSum / 4) * 0.6 + Math.min(1, massSum / 500000) * 0.4;
  const combinedFactor = insulationScore * orientationBoost * shapeFactor * sizeFactor;

  const climate = climateData.ladakh.winter;
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
  const openingsW = Math.round(baseHeatLoss * 0.2);

  const efficiencyScore = Math.round(Math.min(96, 40 + combinedFactor * 55));
  const energySavedPercent = Math.round(Math.min(90, 20 + combinedFactor * 65));

  return {
    id: comboKey,
    source: 'mock',
    insideTemp: { hours: climate.ambientTemp.hours, values: insideValues },
    ambientTemp: { hours: climate.ambientTemp.hours, values: ambientValues },
    solarEnergy: { hours: climate.solarFlux.hours, valuesKwh: solarValues },
    totalSolarKwh,
    heatFlow: { roofW, wallW, openingsW },
    efficiencyScore,
    mostEfficientCombo: 'PCM + Multi-material',
    energySavedPercent,
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
  const mockGenerated = generateMockResult(comboKey, params);
  return formatSimulationResult(mockGenerated, 'mock');
}

export function getMaterials() {
  return materials;
}

export function getClimate(region, season) {
  const r = (region || 'ladakh').toLowerCase();
  const s = (season || 'winter').toLowerCase();
  return climateData[r]?.[s] ?? climateData.ladakh.winter;
}
