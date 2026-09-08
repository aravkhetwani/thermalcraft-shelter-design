/**
 * Automated Integration Test for ANSYS Engine & Node.js API Contract
 * =================================================================
 * Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
 */

import { isAnsysAvailable, requestAnsysSimulation } from '../services/ansysClient.js';
import { getResult } from '../services/simulationService.js';
import { formatSimulationResult } from '../services/resultAdapter.js';

async function runTests() {
  console.log('====================================================');
  console.log('SIH 2026: Phase 7 Node.js ↔ ANSYS Engine Integration');
  console.log('====================================================\n');

  let allPassed = true;

  function assert(condition, message) {
    if (condition) {
      console.log(`  [PASS] ${message}`);
    } else {
      console.error(`  [FAIL] ${message}`);
      allPassed = false;
    }
  }

  // Test 1: Service Health Check
  console.log('--- Test 1: ANSYS Service Availability Probe ---');
  const available = await isAnsysAvailable();
  console.log(`  ANSYS FastAPI Service Available: ${available}`);
  assert(typeof available === 'boolean', 'isAnsysAvailable returns boolean');

  // Test 2: Direct Client Simulation Call (if available) or Service Call
  console.log('\n--- Test 2: getResult() Full Pipeline Execution ---');
  const testParams = {
    materialCombo: 'pcm+rammed-earth',
    orientation: 'south',
    size: 'medium',
    shape: 'dome',
    region: 'ladakh',
    season: 'winter',
  };

  const startTime = Date.now();
  const result = await getResult(testParams);
  const elapsedSec = ((Date.now() - startTime) / 1000).toFixed(2);
  console.log(`  Simulation finished in ${elapsedSec} seconds.`);
  console.log(`  Result source: ${result.source}`);

  // Test 3: Validate Frozen Schema Adherence
  console.log('\n--- Test 3: Validating Frozen Schema Structure ---');
  assert(typeof result.id === 'string' && result.id.length > 0, `id is non-empty string (${result.id})`);
  assert(result.source === 'ansys-live' || result.source === 'mock', `source is valid: ${result.source}`);
  assert(Array.isArray(result.insideTemp?.hours) && result.insideTemp.hours.length === 24, 'insideTemp.hours has 24 elements');
  assert(Array.isArray(result.insideTemp?.values) && result.insideTemp.values.length === 24, 'insideTemp.values has 24 numeric elements');
  assert(Array.isArray(result.ambientTemp?.hours) && result.ambientTemp.hours.length === 24, 'ambientTemp.hours has 24 elements');
  assert(Array.isArray(result.ambientTemp?.values) && result.ambientTemp.values.length === 24, 'ambientTemp.values has 24 numeric elements');
  assert(Array.isArray(result.solarEnergy?.hours) && result.solarEnergy.hours.length === 24, 'solarEnergy.hours has 24 elements');
  assert(Array.isArray(result.solarEnergy?.valuesKwh) && result.solarEnergy.valuesKwh.length === 24, 'solarEnergy.valuesKwh has 24 numeric elements');
  assert(typeof result.totalSolarKwh === 'number' && !isNaN(result.totalSolarKwh), `totalSolarKwh is valid number (${result.totalSolarKwh})`);
  assert(typeof result.heatFlow?.roofW === 'number' && !isNaN(result.heatFlow.roofW), `heatFlow.roofW is valid (${result.heatFlow.roofW})`);
  assert(typeof result.heatFlow?.wallW === 'number' && !isNaN(result.heatFlow.wallW), `heatFlow.wallW is valid (${result.heatFlow.wallW})`);
  assert(typeof result.heatFlow?.openingsW === 'number' && !isNaN(result.heatFlow.openingsW), `heatFlow.openingsW is valid (${result.heatFlow.openingsW})`);
  assert(typeof result.efficiencyScore === 'number' && result.efficiencyScore >= 0 && result.efficiencyScore <= 100, `efficiencyScore is between 0-100 (${result.efficiencyScore})`);
  assert(typeof result.mostEfficientCombo === 'string' && result.mostEfficientCombo.length > 0, `mostEfficientCombo is valid (${result.mostEfficientCombo})`);
  assert(typeof result.energySavedPercent === 'number' && result.energySavedPercent >= 0 && result.energySavedPercent <= 100, `energySavedPercent is between 0-100 (${result.energySavedPercent})`);

  console.log('\nSample Temperature Profile (First 6 hours):');
  for (let i = 0; i < 6; i++) {
    console.log(`  Hour ${String(result.insideTemp.hours[i]).padStart(2, '0')}:00 -> Ambient: ${result.ambientTemp.values[i]}°C | Indoor: ${result.insideTemp.values[i]}°C | Solar: ${result.solarEnergy.valuesKwh[i]} kWh`);
  }

  console.log('\nHeat Flow Breakdown:');
  console.log(`  Roof: ${result.heatFlow.roofW} W | Walls: ${result.heatFlow.wallW} W | Openings: ${result.heatFlow.openingsW} W`);

  console.log('\n====================================================');
  if (allPassed) {
    console.log('RESULT: ALL INTEGRATION TESTS PASSED (100% OK)');
  } else {
    console.error('RESULT: SOME INTEGRATION TESTS FAILED');
    process.exit(1);
  }
  console.log('====================================================');
}

runTests().catch((err) => {
  console.error('Fatal test runner error:', err);
  process.exit(1);
});
