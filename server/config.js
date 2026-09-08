/**
 * Server Configuration
 * Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
 */

export const config = {
  port: parseInt(process.env.PORT || '4000', 10),
  simulationMode: process.env.SIMULATION_MODE || 'ansys-live', // 'ansys-live' | 'mock'
  ansysServiceUrl: process.env.ANSYS_SERVICE_URL || 'http://localhost:8000',
  ansysTimeoutMs: parseInt(process.env.ANSYS_TIMEOUT_MS || '60000', 10),
};
