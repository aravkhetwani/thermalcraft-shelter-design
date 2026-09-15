"""Feature engineering and leakage-prevention tests."""
import pytest

from research.dataset import generate_dataset
from research.features import (
    TARGET_COLUMNS, engineer_features, get_feature_columns, encode_features,
)


def test_no_target_leakage_for_any_target():
    """For every target, none of the OTHER target columns (nor the target
    itself) may appear among the returned feature columns."""
    df = engineer_features(generate_dataset(n_samples=30, seed=5))
    for target in TARGET_COLUMNS:
        features = get_feature_columns(df, target)
        assert target not in features
        for other_target in TARGET_COLUMNS:
            assert other_target not in features
        assert "sample_id" not in features


def test_unknown_target_raises():
    df = engineer_features(generate_dataset(n_samples=10, seed=5))
    with pytest.raises(AssertionError):
        get_feature_columns(df, "not_a_real_target")


def test_engineered_columns_are_deterministic_functions_of_inputs():
    df = generate_dataset(n_samples=1, seed=5)
    row = df.iloc[0]
    engineered = engineer_features(df).iloc[0]

    wall_h = max(0.1, row["height_m"] - 0.20 - row["roof_thickness_m"])
    expected_roof_area = row["length_m"] * row["width_m"]
    expected_wall_area = 2.0 * (row["length_m"] + row["width_m"]) * wall_h

    assert engineered["roof_area_m2"] == pytest.approx(expected_roof_area)
    assert engineered["wall_area_m2"] == pytest.approx(expected_wall_area)
    assert engineered["insulation_present"] == int(row["insulation_thickness_m"] > 0.0)
    assert engineered["pcm_present"] == int(row["pcm_thickness_m"] > 0.0)


def test_encode_features_one_hot_and_column_count():
    df = engineer_features(generate_dataset(n_samples=100, seed=5))
    feature_cols = get_feature_columns(df, "indoor_temp_c")
    encoded, final_cols = encode_features(df, feature_cols)
    assert encoded.shape[0] == len(df)
    # one-hot expansion should produce strictly more (or equal) columns than raw categoricals
    assert encoded.shape[1] >= len(feature_cols)
    assert set(final_cols) == set(encoded.columns)
    # no NaNs introduced by encoding
    assert not encoded.isnull().any().any()
