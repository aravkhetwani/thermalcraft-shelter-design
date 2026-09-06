import axios from 'axios';

// The only place in the client that knows an HTTP API exists.
// Components must go through these functions — never import mock JSON directly —
// so the data source (mock / DB / live ANSYS) can change without touching the UI.
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:4000/api',
});

/** @returns {Promise<import('./schema').Material[]>} */
export async function fetchMaterials() {
  const { data } = await http.get('/materials');
  return data;
}

/** @returns {Promise<import('./schema').ClimateProfile>} */
export async function fetchClimate(region, season) {
  const { data } = await http.get('/climate', { params: { region, season } });
  return data;
}

/** @returns {Promise<import('./schema').SimulationResult>} */
export async function fetchSimulationResult({ materialCombo, orientation, size, shape }) {
  const { data } = await http.get('/simulation-result', {
    params: { materialCombo, orientation, size, shape },
  });
  return data;
}

/** @returns {Promise<import('./schema').SimulationResult>} */
export async function runSimulation({ materialCombo, orientation, size, shape }) {
  const { data } = await http.post('/run-simulation', {
    materialCombo,
    orientation,
    size,
    shape,
  });
  return data;
}
