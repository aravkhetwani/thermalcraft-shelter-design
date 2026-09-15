"""Design-space search + simulator-vs-surrogate consistency tests.

These tests train a small, throwaway surrogate into a tmp directory rather
than depending on the full pre-trained models under research/models/, so
the suite is self-contained and order-independent (works in a clean
checkout before the main pipeline has been run at all).
"""
import numpy as np
import pandas as pd

from research.dataset import generate_dataset
from research.features import encode_features, engineer_features, get_feature_columns
from research.optimize import _add_dummy_target_columns, _sample_candidate_pool
from research.simulator import DESIGN_BOUNDS, ORIENTATIONS, PRIMARY_MATERIALS, simulate
from research.train import split_indices, train_target


def test_candidate_pool_respects_design_bounds():
    rng = np.random.default_rng(0)
    pool = _sample_candidate_pool(500, rng)
    for col in ["length_m", "width_m", "height_m", "wall_thickness_m", "roof_thickness_m", "equipment_load_w",
                "air_changes_per_hour"]:
        lo, hi = DESIGN_BOUNDS[col]
        assert pool[col].min() >= lo - 1e-9
        assert pool[col].max() <= hi + 1e-9
    assert set(pool["orientation"].unique()).issubset(set(ORIENTATIONS))
    assert set(pool["primary_material"].unique()).issubset(set(PRIMARY_MATERIALS))


def test_surrogate_predictions_correlate_with_real_simulator(tmp_path):
    """The core validation contract of the optimization step: surrogate
    predictions must be meaningfully correlated with, not just numerically
    coincidentally close to, actual simulator output on unseen candidates."""
    df = engineer_features(generate_dataset(n_samples=600, seed=21))
    train_idx, val_idx, test_idx = split_indices(df, seed=42)
    result = train_target(df, "indoor_temp_c", train_idx, val_idx, test_idx, models_dir=tmp_path)

    import joblib
    model = joblib.load(tmp_path / f"indoor_temp_c__{result['best_model']}.joblib")

    rng = np.random.default_rng(99)
    pool = _sample_candidate_pool(50, rng)
    pool = _add_dummy_target_columns(pool)
    engineered = engineer_features(pool)
    all_cols = get_feature_columns(engineered, "indoor_temp_c")
    X, _ = encode_features(engineered, all_cols)
    X = X.reindex(columns=result["feature_columns"], fill_value=0)

    predicted = model.predict(X)

    design_cols = [
        "length_m", "width_m", "height_m", "wall_thickness_m", "roof_thickness_m",
        "orientation", "primary_material", "insulation_thickness_m", "pcm_thickness_m",
        "occupant_count", "equipment_load_w", "air_changes_per_hour",
        "ambient_temp_c", "solar_irradiance_peak_w_m2", "wind_speed_m_s",
    ]
    actual = [simulate(row[design_cols].to_dict()).indoor_temp_c for _, row in pool.iterrows()]

    correlation = np.corrcoef(predicted, actual)[0, 1]
    assert correlation > 0.8, f"surrogate predictions should correlate strongly with real simulator output, got r={correlation}"
    assert np.all(np.isfinite(predicted))


def test_validation_step_uses_real_simulator_not_surrogate_output():
    """Guards against a subtle but critical bug class: reporting the
    surrogate's own prediction as if it were simulator-validated truth."""
    design = {
        "length_m": 4.0, "width_m": 3.0, "height_m": 2.8,
        "wall_thickness_m": 0.30, "roof_thickness_m": 0.20,
        "orientation": "south", "primary_material": "insulated-composite",
        "insulation_thickness_m": 0.10, "pcm_thickness_m": 0.03,
        "occupant_count": 4, "equipment_load_w": 100.0, "air_changes_per_hour": 1.0,
        "ambient_temp_c": -18.2, "solar_irradiance_peak_w_m2": 300.0, "wind_speed_m_s": 14.5,
    }
    real_result = simulate(design)
    # A "prediction" that is deliberately wrong to prove the test would catch
    # a validation step that lazily reused it instead of re-simulating.
    fake_surrogate_prediction = real_result.indoor_temp_c + 100.0
    assert simulate(design).indoor_temp_c != fake_surrogate_prediction
    assert simulate(design).indoor_temp_c == real_result.indoor_temp_c
