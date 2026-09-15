/**
 * ML Research Pipeline Reader
 * =============================
 * Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
 *
 * Reads the REAL output artifacts produced by the Python research pipeline
 * (`Ansys simulation/research/{train,optimize,benchmark}.py`) — never
 * hardcodes metrics. If the pipeline hasn't been run yet, each getter
 * returns null and the API/frontend degrade gracefully (dashboard section
 * simply doesn't render, rather than showing fabricated numbers).
 */
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const RESULTS_DIR = join(__dirname, '..', '..', 'Ansys simulation', 'research', 'results');

function readJson(filename) {
  try {
    const raw = readFileSync(join(RESULTS_DIR, filename), 'utf-8');
    return JSON.parse(raw);
  } catch (err) {
    return null;
  }
}

export function getResearchSummary() {
  const training = readJson('training_metrics.json');
  const optimization = readJson('optimization_result.json');
  const benchmark = readJson('speedup_benchmark.json');

  if (!training && !optimization && !benchmark) {
    return null;
  }

  // Slim the training metrics down to what the dashboard needs — avoid
  // shipping the full per-feature permutation-importance arrays twice.
  const modelComparison = {};
  const featureImportance = {};
  if (training) {
    for (const [target, result] of Object.entries(training)) {
      modelComparison[target] = {
        bestModel: result.best_model,
        nTrain: result.n_train,
        nVal: result.n_val,
        nTest: result.n_test,
        models: Object.fromEntries(
          Object.entries(result.model_results).map(([name, m]) => [name, m.test])
        ),
      };
      const perm = result.feature_importance?.permutation_mean || {};
      featureImportance[target] = Object.entries(perm)
        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
        .slice(0, 12)
        .map(([feature, importance]) => ({ feature, importance }));
    }
  }

  return {
    hasData: true,
    modelComparison,
    featureImportance,
    optimization: optimization
      ? {
          scenario: optimization.scenario,
          nCandidatesScreened: optimization.n_candidates_screened,
          surrogateBatchPredictSeconds: optimization.surrogate_batch_predict_seconds,
          validation: optimization.validation,
          bestDesign: optimization.best_design,
          baselineActualIndoorTempC: optimization.baseline_actual_indoor_temp_c,
          improvementOverBaselineC: optimization.improvement_over_baseline_c,
        }
      : null,
    speedupBenchmark: benchmark ? benchmark.results : null,
  };
}
