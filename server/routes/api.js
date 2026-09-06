import { Router } from 'express';
import { getResult, getMaterials, getClimate } from '../services/simulationService.js';

const router = Router();

router.get('/materials', (req, res) => {
  res.json(getMaterials());
});

router.get('/climate', (req, res) => {
  const { region, season } = req.query;
  res.json(getClimate(region, season));
});

router.get('/simulation-result', async (req, res) => {
  const { materialCombo, orientation, size, shape } = req.query;
  const result = await getResult({ materialCombo, orientation, size, shape });
  res.json(result);
});

// Simulates wherever the real computation eventually happens (DB query,
// interpolation, or a live ANSYS trigger) — same params, same delay-then-JSON contract.
router.post('/run-simulation', async (req, res) => {
  const { materialCombo, orientation, size, shape } = req.body || {};
  const delayMs = 1000 + Math.round(Math.random() * 1000);
  await new Promise((resolve) => setTimeout(resolve, delayMs));
  const result = await getResult({ materialCombo, orientation, size, shape });
  res.json(result);
});

export default router;
