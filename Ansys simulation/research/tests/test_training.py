"""Model training/inference smoke tests (small dataset, tmp model dir —
never touches the real trained models under research/models/)."""
import numpy as np

from research.dataset import generate_dataset
from research.features import engineer_features
from research.train import split_indices, train_target


def test_training_beats_mean_baseline(tmp_path):
    df = engineer_features(generate_dataset(n_samples=400, seed=17))
    train_idx, val_idx, test_idx = split_indices(df, seed=42)
    result = train_target(df, "indoor_temp_c", train_idx, val_idx, test_idx, models_dir=tmp_path)

    baseline_r2 = result["model_results"]["mean_baseline"]["test"]["r2"]
    for name, metrics in result["model_results"].items():
        if name == "mean_baseline":
            continue
        assert metrics["test"]["r2"] > baseline_r2, f"{name} should beat the mean baseline"


def test_trained_models_are_persisted(tmp_path):
    df = engineer_features(generate_dataset(n_samples=200, seed=17))
    train_idx, val_idx, test_idx = split_indices(df, seed=42)
    train_target(df, "indoor_temp_c", train_idx, val_idx, test_idx, models_dir=tmp_path)

    saved_files = list(tmp_path.glob("indoor_temp_c__*.joblib"))
    assert len(saved_files) >= 4  # baseline + linear + RF + GB + xgboost
    assert (tmp_path / "indoor_temp_c__feature_columns.json").exists()


def test_predictions_are_finite_and_in_plausible_range(tmp_path):
    import joblib

    df = engineer_features(generate_dataset(n_samples=300, seed=17))
    train_idx, val_idx, test_idx = split_indices(df, seed=42)
    result = train_target(df, "indoor_temp_c", train_idx, val_idx, test_idx, models_dir=tmp_path)

    best_model = joblib.load(tmp_path / f"indoor_temp_c__{result['best_model']}.joblib")
    from research.features import encode_features, get_feature_columns
    raw_cols = get_feature_columns(df, "indoor_temp_c")
    X, _ = encode_features(df, raw_cols)
    X = X.reindex(columns=result["feature_columns"], fill_value=0)
    preds = best_model.predict(X.loc[test_idx])

    assert np.all(np.isfinite(preds))
    # Design space realistically spans roughly -40C to +50C indoor
    assert preds.min() > -50 and preds.max() < 60
