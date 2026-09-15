import { Router } from 'express';
import { getResult, getMaterials, getClimate } from '../services/simulationService.js';
import { listRegions } from '../services/weatherService.js';
import { compareConfigurations } from '../services/optimizationService.js';
import { recordRun, listRuns } from '../services/historyService.js';
import { getResearchSummary } from '../services/researchService.js';
import { config } from '../config.js';

const router = Router();

function parseOpenings(source) {
  if (!source) return undefined;
  if (typeof source === 'object' && !Array.isArray(source)) return source;
  try {
    return JSON.parse(source);
  } catch {
    return undefined;
  }
}

router.get('/materials', (req, res) => {
  res.json(getMaterials());
});

router.get('/regions', (req, res) => {
  res.json(listRegions());
});

router.get('/climate', async (req, res) => {
  const { region, season } = req.query;
  res.json(await getClimate(region, season));
});

router.get('/simulation-result', async (req, res) => {
  const { materialCombo, orientation, size, shape, region, season, openings } = req.query;
  const result = await getResult({
    materialCombo,
    orientation,
    size,
    shape,
    region,
    season,
    openings: parseOpenings(openings),
  });
  res.json(result);
});

// Runs full simulation via ANSYS MAPDL (or mock fallback)
router.post('/run-simulation', async (req, res) => {
  const { materialCombo, orientation, size, shape, region, season, openings } = req.body || {};
  if (config.simulationMode === 'mock') {
    const delayMs = 1000 + Math.round(Math.random() * 1000);
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  const params = { materialCombo, orientation, size, shape, region, season, openings };
  const result = await getResult(params);
  recordRun(params, result);
  res.json(result);
});

// Optimization / Comparison: sweeps geometry x orientation x material combos
// and returns a ranked list plus the genuinely computed best configuration.
router.get('/compare', async (req, res) => {
  const { region, season, size, openings } = req.query;
  const comparison = compareConfigurations({ region, season, size, openings: parseOpenings(openings) });
  res.json(comparison);
});

// Recent simulation run history (persisted in SQLite).
router.get('/history', (req, res) => {
  const limit = Math.min(100, Math.max(1, parseInt(req.query.limit, 10) || 20));
  res.json(listRuns(limit));
});

// ML research pipeline summary (model comparison, feature importance,
// optimization result, surrogate speedup) — reads real artifacts produced by
// `Ansys simulation/research/run_all.py`; returns { hasData: false } if the
// pipeline hasn't been run yet.
router.get('/research/summary', (req, res) => {
  const summary = getResearchSummary();
  res.json(summary || { hasData: false });
});

export default router;
