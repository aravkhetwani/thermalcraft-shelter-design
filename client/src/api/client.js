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

/** @returns {Promise<Array<{value:string,label:string,latitude:number,longitude:number,elevationM:number}>>} */
export async function fetchRegions() {
  const { data } = await http.get('/regions');
  return data;
}

/** @returns {Promise<import('./schema').ClimateProfile>} */
export async function fetchClimate(region, season) {
  const { data } = await http.get('/climate', { params: { region, season } });
  return data;
}

/** @returns {Promise<import('./schema').SimulationResult>} */
export async function fetchSimulationResult({ materialCombo, orientation, size, shape, region, season, openings }) {
  const { data } = await http.get('/simulation-result', {
    params: { materialCombo, orientation, size, shape, region, season, openings: openings ? JSON.stringify(openings) : undefined },
  });
  return data;
}

/** @returns {Promise<import('./schema').SimulationResult>} */
export async function runSimulation({ materialCombo, orientation, size, shape, region, season, openings }) {
  const { data } = await http.post('/run-simulation', {
    materialCombo,
    orientation,
    size,
    shape,
    region,
    season,
    openings,
  });
  return data;
}

/** Sweeps geometry x orientation x material combos and returns a ranked comparison. */
export async function fetchComparison({ region, season, size, openings }) {
  const { data } = await http.get('/compare', {
    params: { region, season, size, openings: openings ? JSON.stringify(openings) : undefined },
  });
  return data;
}

/** Recent persisted simulation runs. */
export async function fetchHistory(limit = 10) {
  const { data } = await http.get('/history', { params: { limit } });
  return data;
}

/** ML research pipeline summary — real trained-model metrics, feature
 * importance, and optimization results. { hasData: false } if the Python
 * pipeline (Ansys simulation/research/run_all.py) hasn't been run yet. */
export async function fetchResearchSummary() {
  const { data } = await http.get('/research/summary');
  return data;
}
