"""
Surrogate-Driven Design-Space Search + Simulator Validation
==============================================================
Downstream task: use the trained XGBoost surrogate for `indoor_temp_c` to
screen a large random pool of candidate shelter designs under a fixed,
real winter climate scenario, then re-run only the most promising
candidates through the actual analytic simulator to validate that the
surrogate's picks are genuinely good (not surrogate artifacts) — per the
requirement to validate ML-derived designs against the original simulator.

FIXED EVALUATION SCENARIO
---------------------------
24-hour-averaged Ladakh winter conditions (ambient temperature and solar
irradiance both averaged over the real 24-hour profile in `climate_data.py`,
wind speed = Ladakh winter's fixed value). This is a genuine, physically
meaningful design point taken directly from the project's own climate data
— not an arbitrary made-up condition — representing "a typical winter day,"
which is exactly the deck's stated design problem (maximize passive comfort
through a full winter day/night cycle).
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
except ImportError:
    from simulator import DESIGN_BOUNDS, ORIENTATIONS, PRIMARY_MATERIALS, simulate
    from climate_data import LADAKH_WINTER
    from features import engineer_features, get_feature_columns, encode_features

SEED = 42
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"
DATA_PATH = BASE_DIR / "data" / "thermal_dataset.csv"

TARGET = "indoor_temp_c"
N_CANDIDATES = 200_000
TOP_K = 20

SCENARIO = {
    "region": "ladakh",
    "season": "winter",
    "hour": -1,  # sentinel: 24h-averaged, not a real single hour
    "ambient_temp_c": float(np.mean(LADAKH_WINTER["ambient"])),
    "solar_irradiance_peak_w_m2": float(np.mean(LADAKH_WINTER["solar"])),
    "wind_speed_m_s": LADAKH_WINTER["wind_speed_m_s"],
}

# A reasonable "typical current practice" baseline: medium rammed-earth,
# no insulation/PCM, moderate ventilation — i.e. roughly what an
# unoptimized, conventionally built shelter looks like, matching the
# app's own pre-existing UI defaults (dome/south/medium/rammed-earth).
BASELINE_DESIGN = {
    "length_m": 4.0, "width_m": 3.0, "height_m": 2.8,
    "wall_thickness_m": 0.25, "roof_thickness_m": 0.15,
    "orientation": "south", "primary_material": "rammed-earth",
    "insulation_thickness_m": 0.0, "pcm_thickness_m": 0.0,
    "occupant_count": 4, "equipment_load_w": 80.0,
    "air_changes_per_hour": 1.5,
    **{k: SCENARIO[k] for k in ("ambient_temp_c", "solar_irradiance_peak_w_m2", "wind_speed_m_s")},
}


def _sample_candidate_pool(n: int, rng: np.random.Generator) -> pd.DataFrame:
    b = DESIGN_BOUNDS
    rows = {
        "length_m": rng.uniform(*b["length_m"], size=n),
        "width_m": rng.uniform(*b["width_m"], size=n),
        "height_m": rng.uniform(*b["height_m"], size=n),
        "wall_thickness_m": rng.uniform(*b["wall_thickness_m"], size=n),
        "roof_thickness_m": rng.uniform(*b["roof_thickness_m"], size=n),
        "orientation": rng.choice(ORIENTATIONS, size=n),
        "primary_material": rng.choice(PRIMARY_MATERIALS, size=n),
        "insulation_thickness_m": rng.uniform(0.0, b["insulation_thickness_m"][1], size=n),
        "pcm_thickness_m": rng.uniform(0.0, b["pcm_thickness_m"][1], size=n),
        "occupant_count": rng.integers(b["occupant_count"][0], b["occupant_count"][1] + 1, size=n),
        "equipment_load_w": rng.uniform(*b["equipment_load_w"], size=n),
        "air_changes_per_hour": rng.uniform(*b["air_changes_per_hour"], size=n),
    }
    df = pd.DataFrame(rows)
    df["region"] = SCENARIO["region"]
    df["season"] = SCENARIO["season"]
    df["hour"] = 12  # placeholder categorical value; ambient/solar/wind set explicitly below (real value used, not looked up)
    df["ambient_temp_c"] = SCENARIO["ambient_temp_c"]
    df["solar_irradiance_peak_w_m2"] = SCENARIO["solar_irradiance_peak_w_m2"]
    df["wind_speed_m_s"] = SCENARIO["wind_speed_m_s"]
    return df


def _add_dummy_target_columns(df: pd.DataFrame) -> pd.DataFrame:
    # engineer_features needs room_volume_m3 / envelope_r_wall / envelope_r_roof,
    # which are themselves produced by the simulator. Compute them directly
    # via simulate()'s internal helpers rather than duplicating the formulas.
    try:
        from .simulator import _wall_envelope, _roof_envelope, FLOOR_THICKNESS_M
    except ImportError:
        from simulator import _wall_envelope, _roof_envelope, FLOOR_THICKNESS_M

    r_wall = df.apply(lambda r: _wall_envelope(r["wall_thickness_m"], r["primary_material"],
                                                r["insulation_thickness_m"], r["pcm_thickness_m"]), axis=1)
    r_roof = df.apply(lambda r: _roof_envelope(r["roof_thickness_m"], r["insulation_thickness_m"],
                                                r["pcm_thickness_m"]), axis=1)
    wall_h = np.maximum(0.1, df["height_m"] - FLOOR_THICKNESS_M - df["roof_thickness_m"])
    room_vol = np.maximum(0.1, df["length_m"] - 2 * df["wall_thickness_m"]) * \
        np.maximum(0.1, df["width_m"] - 2 * df["wall_thickness_m"]) * wall_h

    df = df.copy()
    df["envelope_r_wall"] = r_wall
    df["envelope_r_roof"] = r_roof
    df["room_volume_m3"] = room_vol
    return df


def run_optimization():
    rng = np.random.default_rng(SEED)

    xgb_model = joblib.load(MODELS_DIR / f"{TARGET}__xgboost.joblib")
    with open(MODELS_DIR / f"{TARGET}__feature_columns.json") as f:
        feature_cols = json.load(f)

    candidates = _sample_candidate_pool(N_CANDIDATES, rng)
    candidates = _add_dummy_target_columns(candidates)
    engineered = engineer_features(candidates)

    all_feature_cols = get_feature_columns(engineered, TARGET)
    X, _ = encode_features(engineered, all_feature_cols)
    X = X.reindex(columns=feature_cols, fill_value=0)

    t0 = time.perf_counter()
    predicted = xgb_model.predict(X)
    predict_time_s = time.perf_counter() - t0

    candidates["predicted_indoor_temp_c"] = predicted
    top_k = candidates.nlargest(TOP_K, "predicted_indoor_temp_c").copy()

    # --- Validate the surrogate's top picks against the REAL simulator ---
    real_temps = []
    for _, row in top_k.iterrows():
        design = row[[
            "length_m", "width_m", "height_m", "wall_thickness_m", "roof_thickness_m",
            "orientation", "primary_material", "insulation_thickness_m", "pcm_thickness_m",
            "occupant_count", "equipment_load_w", "air_changes_per_hour",
            "ambient_temp_c", "solar_irradiance_peak_w_m2", "wind_speed_m_s",
        ]].to_dict()
        real_temps.append(simulate(design).indoor_temp_c)
    top_k["actual_indoor_temp_c"] = real_temps
    top_k["surrogate_error_c"] = top_k["predicted_indoor_temp_c"] - top_k["actual_indoor_temp_c"]

    best_row = top_k.loc[top_k["actual_indoor_temp_c"].idxmax()]
    baseline_result = simulate(BASELINE_DESIGN)

    result = {
        "scenario": SCENARIO,
        "n_candidates_screened": N_CANDIDATES,
        "surrogate_batch_predict_seconds": predict_time_s,
        "top_k": TOP_K,
        "validation": {
            "mean_abs_surrogate_error_c": float(top_k["surrogate_error_c"].abs().mean()),
            "max_abs_surrogate_error_c": float(top_k["surrogate_error_c"].abs().max()),
        },
        "best_design": {
            k: (float(v) if isinstance(v, (np.floating, np.integer)) else v)
            for k, v in best_row[[
                "length_m", "width_m", "height_m", "wall_thickness_m", "roof_thickness_m",
                "orientation", "primary_material", "insulation_thickness_m", "pcm_thickness_m",
                "occupant_count", "equipment_load_w", "air_changes_per_hour",
                "predicted_indoor_temp_c", "actual_indoor_temp_c",
            ]].to_dict().items()
        },
        "baseline_design": BASELINE_DESIGN,
        "baseline_actual_indoor_temp_c": baseline_result.indoor_temp_c,
        "improvement_over_baseline_c": float(best_row["actual_indoor_temp_c"] - baseline_result.indoor_temp_c),
    }
    return result, top_k


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result, top_k = run_optimization()

    with open(RESULTS_DIR / "optimization_result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)
    top_k.to_csv(RESULTS_DIR / "optimization_top_k.csv", index=False)

    print(f"Screened {result['n_candidates_screened']} candidates in {result['surrogate_batch_predict_seconds']:.4f}s")
    print(f"Top-{TOP_K} mean |surrogate error| = {result['validation']['mean_abs_surrogate_error_c']:.4f} C")
    print(f"Best validated design: {json.dumps(result['best_design'], indent=2)}")
    print(f"Baseline (typical current design) actual indoor temp: {result['baseline_actual_indoor_temp_c']:.2f} C")
    print(f"Improvement over baseline: {result['improvement_over_baseline_c']:.2f} C")


if __name__ == "__main__":
    main()
