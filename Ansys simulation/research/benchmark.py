"""
Surrogate vs. Simulator Speedup Benchmark
============================================
Honestly measures wall-clock throughput of the real analytic simulator
(run in a plain Python loop, as any straightforward design-space sweep
would call it) against the trained XGBoost surrogate's vectorized batch
`.predict()`, at several batch sizes. Reports the actual measured numbers
— including the (very plausible) case where the surrogate does NOT help,
or only helps at scale — rather than assuming a speedup.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

try:
    from .simulator import DESIGN_BOUNDS, ORIENTATIONS, PRIMARY_MATERIALS, simulate
    from .climate_data import LADAKH_WINTER
    from .features import engineer_features, get_feature_columns, encode_features
    from .optimize import _sample_candidate_pool, _add_dummy_target_columns, SCENARIO
except ImportError:
    from simulator import DESIGN_BOUNDS, ORIENTATIONS, PRIMARY_MATERIALS, simulate
    from climate_data import LADAKH_WINTER
    from features import engineer_features, get_feature_columns, encode_features
    from optimize import _sample_candidate_pool, _add_dummy_target_columns, SCENARIO

SEED = 42
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"
TARGET = "indoor_temp_c"
BATCH_SIZES = [100, 1_000, 10_000, 100_000]
N_REPEATS = 3


def _time_simulator_loop(designs: list[dict]) -> float:
    t0 = time.perf_counter()
    for d in designs:
        simulate(d)
    return time.perf_counter() - t0


def _time_surrogate_batch(model, X: pd.DataFrame) -> float:
    t0 = time.perf_counter()
    model.predict(X)
    return time.perf_counter() - t0


def run_benchmark() -> dict:
    rng = np.random.default_rng(SEED)
    xgb_model = joblib.load(MODELS_DIR / f"{TARGET}__xgboost.joblib")
    with open(MODELS_DIR / f"{TARGET}__feature_columns.json") as f:
        feature_cols = json.load(f)

    results = []
    for n in BATCH_SIZES:
        pool = _sample_candidate_pool(n, rng)
        pool = _add_dummy_target_columns(pool)
        engineered = engineer_features(pool)
        all_cols = get_feature_columns(engineered, TARGET)
        X, _ = encode_features(engineered, all_cols)
        X = X.reindex(columns=feature_cols, fill_value=0)

        design_dicts = pool[[
            "length_m", "width_m", "height_m", "wall_thickness_m", "roof_thickness_m",
            "orientation", "primary_material", "insulation_thickness_m", "pcm_thickness_m",
            "occupant_count", "equipment_load_w", "air_changes_per_hour",
            "ambient_temp_c", "solar_irradiance_peak_w_m2", "wind_speed_m_s",
        ]].to_dict("records")

        sim_times = [_time_simulator_loop(design_dicts) for _ in range(N_REPEATS)]
        surrogate_times = [_time_surrogate_batch(xgb_model, X) for _ in range(N_REPEATS)]

        sim_mean = float(np.mean(sim_times))
        surrogate_mean = float(np.mean(surrogate_times))
        results.append({
            "batch_size": n,
            "simulator_seconds_mean": sim_mean,
            "surrogate_seconds_mean": surrogate_mean,
            "speedup_x": sim_mean / surrogate_mean if surrogate_mean > 0 else float("inf"),
            "simulator_calls_per_second": n / sim_mean if sim_mean > 0 else float("inf"),
            "surrogate_calls_per_second": n / surrogate_mean if surrogate_mean > 0 else float("inf"),
        })
    return {"n_repeats": N_REPEATS, "results": results}


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result = run_benchmark()
    with open(RESULTS_DIR / "speedup_benchmark.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"{'batch':>10} {'simulator(s)':>14} {'surrogate(s)':>14} {'speedup':>10}")
    for row in result["results"]:
        print(f"{row['batch_size']:>10} {row['simulator_seconds_mean']:>14.5f} "
              f"{row['surrogate_seconds_mean']:>14.5f} {row['speedup_x']:>9.2f}x")


if __name__ == "__main__":
    main()
