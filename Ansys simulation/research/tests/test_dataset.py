"""Dataset generation correctness and reproducibility tests."""
import numpy as np

from research.dataset import generate_dataset
from research.simulator import DESIGN_BOUNDS


def test_reproducibility_same_seed_identical_output():
    df1 = generate_dataset(n_samples=50, seed=123)
    df2 = generate_dataset(n_samples=50, seed=123)
    assert df1.equals(df2)


def test_different_seed_gives_different_output():
    df1 = generate_dataset(n_samples=50, seed=1)
    df2 = generate_dataset(n_samples=50, seed=2)
    assert not df1["indoor_temp_c"].equals(df2["indoor_temp_c"])


def test_no_missing_values():
    df = generate_dataset(n_samples=200, seed=7)
    assert not df.isnull().any().any()


def test_continuous_columns_within_declared_bounds():
    df = generate_dataset(n_samples=500, seed=7)
    for col in ["length_m", "width_m", "height_m", "wall_thickness_m", "roof_thickness_m",
                "equipment_load_w", "air_changes_per_hour"]:
        lo, hi = DESIGN_BOUNDS[col]
        assert df[col].min() >= lo - 1e-9
        assert df[col].max() <= hi + 1e-9


def test_expected_columns_present():
    df = generate_dataset(n_samples=20, seed=7)
    expected = {
        "sample_id", "region", "season", "hour", "ambient_temp_c",
        "solar_irradiance_peak_w_m2", "wind_speed_m_s", "length_m", "width_m",
        "height_m", "wall_thickness_m", "roof_thickness_m", "orientation",
        "primary_material", "insulation_thickness_m", "pcm_thickness_m",
        "occupant_count", "equipment_load_w", "air_changes_per_hour",
        "indoor_temp_c", "roof_loss_w", "wall_loss_w", "ground_loss_w",
        "ventilation_loss_w", "total_loss_w", "envelope_r_wall",
        "envelope_r_roof", "room_volume_m3",
    }
    assert expected.issubset(set(df.columns))


def test_climate_values_are_physically_consistent_pairs():
    """Every row's (ambient_temp_c, solar_irradiance_peak_w_m2) pair must come
    from a real recorded hour — this test rules out the failure mode of
    independently sampling temperature and solar irradiance, which could
    otherwise produce physically impossible combinations (e.g. the coldest
    night-time temperature paired with peak midday solar)."""
    from research.climate_data import get_hourly_climate

    df = generate_dataset(n_samples=300, seed=11)
    for _, row in df.iterrows():
        amb, solar, wind = get_hourly_climate(row["region"], row["season"], row["hour"])
        assert np.isclose(row["ambient_temp_c"], amb)
        assert np.isclose(row["solar_irradiance_peak_w_m2"], solar)
        assert np.isclose(row["wind_speed_m_s"], wind)
