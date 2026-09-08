import { Router } from 'express';
import { getResult, getMaterials, getClimate } from '../services/simulationService.js';
import { config } from '../config.js';

const router = Router();

router.get('/materials', (req, res) => {
  res.json(getMaterials());
});

router.get('/climate', (req, res) => {
  const { region, season } = req.query;
  res.json(getClimate(region, season));
});

router.get('/simulation-result', async (req, res) => {
  const { materialCombo, orientation, size, shape, region, season } = req.query;
  const result = await getResult({ materialCombo, orientation, size, shape, region, season });
  res.json(result);
});

// Runs full simulation via ANSYS MAPDL (or mock fallback)
router.post('/run-simulation', async (req, res) => {
  const { materialCombo, orientation, size, shape, region, season } = req.body || {};
  if (config.simulationMode === 'mock') {
    const delayMs = 1000 + Math.round(Math.random() * 1000);
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  const result = await getResult({ materialCombo, orientation, size, shape, region, season });
  res.json(result);
});

export default router;
