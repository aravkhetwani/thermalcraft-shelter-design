/**
 * Optimization / Comparison Engine
 * =================================
 * Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
 *
 * Implements the deck's "Optimize" step: vary geometry, orientation and
 * material layers, score every combination with a rule-based efficiency
 * metric, and recommend the best configuration — replacing the previous
 * hardcoded "PCM + Multi-material" placeholder with a real computed answer.
 */
import materials from '../mockData/materials.json' with { type: 'json' };
import { computeCombinedFactor, computeOpeningsLossFactor, normalizeOpenings } from './simulationService.js';

const SHAPES = ['dome', 'rectangular', 'custom'];
const ORIENTATIONS = ['south', 'east', 'west', 'north'];

// Candidate material combos swept during optimization: every single material
// plus the two composite stacks called out in the deck ("Dome + South +
// Rammed Earth + PCM", multi-layer PCM/insulation combos).
const MATERIAL_COMBOS = [
  ...materials.map((m) => m.id),
  'rammed-earth+pcm',
  'insulated-composite+pcm',
  'pu-foam+pcm',
];

function labelForCombo({ materialCombo, orientation, shape }) {
  const matLabel = materialCombo
    .split('+')
    .map((id) => id.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()))
    .join(' + ');
  const shapeLabel = shape[0].toUpperCase() + shape.slice(1);
  const orientationLabel = orientation[0].toUpperCase() + orientation.slice(1);
  return `${shapeLabel} + ${orientationLabel} + ${matLabel}`;
}

/**
 * Scores one configuration without running a full simulation — reuses the
 * same combinedFactor / openings-loss model as generateMockResult so ranking
 * stays consistent with the numbers actually shown for the selected combo.
 */
function scoreConfig(config, openings) {
  const { combinedFactor } = computeCombinedFactor(config);
  const openingsLossFactor = computeOpeningsLossFactor(openings);
  const efficiencyScore = Math.round(
    Math.min(96, Math.max(30, 40 + combinedFactor * 55 - (openingsLossFactor - 1) * 12))
  );
  const energySavedPercent = Math.round(
    Math.min(90, Math.max(10, 20 + combinedFactor * 65 - (openingsLossFactor - 1) * 15))
  );
  return { efficiencyScore, energySavedPercent, combinedFactor };
}

/**
 * Sweeps geometry x orientation x material combos for the given
 * size/region/season/openings and returns a ranked comparison.
 */
export function compareConfigurations(params = {}) {
  const { size = 'medium', region = 'ladakh', season = 'winter', openings } = params;
  const normalizedOpenings = normalizeOpenings(openings);

  const results = [];
  for (const shape of SHAPES) {
    for (const orientation of ORIENTATIONS) {
      for (const materialCombo of MATERIAL_COMBOS) {
        const config = { materialCombo, orientation, size, shape };
        const { efficiencyScore, energySavedPercent } = scoreConfig(config, normalizedOpenings);
        results.push({
          comboLabel: `${materialCombo}_${orientation}_${size}_${shape}`,
          label: labelForCombo({ materialCombo, orientation, shape }),
          shape,
          orientation,
          size,
          materialCombo,
          efficiencyScore,
          energySavedPercent,
        });
      }
    }
  }

  results.sort((a, b) => b.efficiencyScore - a.efficiencyScore);

  return {
    region,
    season,
    size,
    openings: normalizedOpenings,
    configurationsEvaluated: results.length,
    top: results.slice(0, 10),
    best: results[0],
  };
}

/** Cheap accessor used by simulationService to fill in a real "best design" label. */
export async function findBestCombo(params = {}) {
  const { best } = compareConfigurations(params);
  return best;
}
