"""End-to-end reproducibility: same seeds -> same dataset -> same metrics."""
from research.dataset import generate_dataset
from research.features import engineer_features
from research.train import split_indices, train_target


def test_full_pipeline_reproducible_given_same_seeds(tmp_path):
    df1 = engineer_features(generate_dataset(n_samples=300, seed=55))
    df2 = engineer_features(generate_dataset(n_samples=300, seed=55))
    assert df1.equals(df2)

    train_idx1, val_idx1, test_idx1 = split_indices(df1, seed=42)
    train_idx2, val_idx2, test_idx2 = split_indices(df2, seed=42)
    assert list(train_idx1) == list(train_idx2)

    result1 = train_target(df1, "indoor_temp_c", train_idx1, val_idx1, test_idx1, models_dir=tmp_path / "a")
    result2 = train_target(df2, "indoor_temp_c", train_idx2, val_idx2, test_idx2, models_dir=tmp_path / "b")

    for name in result1["model_results"]:
        r2_1 = result1["model_results"][name]["test"]["r2"]
        r2_2 = result2["model_results"][name]["test"]["r2"]
        assert abs(r2_1 - r2_2) < 1e-9, f"{name} test R2 should be identical across runs with the same seed"
