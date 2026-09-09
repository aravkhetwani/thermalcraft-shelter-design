/**
 * ANSYS Python FastAPI Service Client
 * ====================================
 * Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
 *
 * Communicates with the FastAPI microservice running the Phase 7 PyMAPDL physics engine.
 */

import { config } from '../config.js';

/**
 * Checks if the ANSYS FastAPI microservice is reachable and healthy.
 * @returns {Promise<boolean>}
 */
export async function isAnsysAvailable() {
  try {
    const res = await fetch(`${config.ansysServiceUrl}/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === 'healthy';
  } catch (err) {
    return false;
  }
}

/**
 * Calls the ANSYS FastAPI microservice to perform a real FEA simulation.
 * @param {Object} params - { materialCombo, orientation, size, shape, region, season }
 * @returns {Promise<Object>} raw response from ANSYS FastAPI service
 */
// Ventilation level -> air changes per hour, matching simulationService.js's VENTILATION_ACH.
const VENTILATION_ACH = { low: 0.8, medium: 1.5, high: 2.6 };

export async function requestAnsysSimulation(params) {
  const url = `${config.ansysServiceUrl}/simulate`;

  const openings = params.openings || {};
  const baseAch = VENTILATION_ACH[(openings.ventilation || 'medium').toLowerCase()] ?? VENTILATION_ACH.medium;
  const doors = Number.isFinite(Number(openings.doors)) ? Number(openings.doors) : 1;
  const windows = Number.isFinite(Number(openings.windows)) ? Number(openings.windows) : 2;
  // More doors/windows increase infiltration on top of the ventilation-level baseline.
  const airChangesPerHour = Number((baseAch * (1 + doors * 0.05 + windows * 0.03)).toFixed(2));

  const payload = {
    materialCombo: params.materialCombo || 'rammed-earth',
    orientation: params.orientation || 'south',
    size: params.size || 'medium',
    shape: params.shape || 'dome',
    region: params.region || 'ladakh',
    season: params.season || 'winter',
    air_changes_per_hour: airChangesPerHour,
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(config.ansysTimeoutMs),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`ANSYS service error (${response.status}): ${errText}`);
  }

  return await response.json();
}
