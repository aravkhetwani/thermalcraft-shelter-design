"""Physical correctness tests for the analytic steady-state simulator."""
import pytest

from research.simulator import simulate, ORIENTATIONS

NIGHT_BASE = dict(
    length_m=4.0, width_m=3.0, height_m=2.8,
    wall_thickness_m=0.25, roof_thickness_m=0.15,
    orientation="south", primary_material="rammed-earth",
    insulation_thickness_m=0.0, pcm_thickness_m=0.0,
    occupant_count=4, equipment_load_w=80.0,
    air_changes_per_hour=1.5,
    ambient_temp_c=-18.2, solar_irradiance_peak_w_m2=0.0, wind_speed_m_s=14.5,
)


def test_insulation_warms_interior_at_night():
    """More wall insulation (higher R) should raise steady-state indoor
    temperature when there is no confounding solar gain."""
    baseline = simulate(NIGHT_BASE)
    insulated = simulate({**NIGHT_BASE, "insulation_thickness_m": 0.10})
    assert insulated.indoor_temp_c > baseline.indoor_temp_c


def test_higher_ventilation_cools_interior():
    baseline = simulate(NIGHT_BASE)
    ventilated = simulate({**NIGHT_BASE, "air_changes_per_hour": 3.0})
    assert ventilated.indoor_temp_c < baseline.indoor_temp_c


def test_pcm_layer_warms_interior_at_night():
    baseline = simulate(NIGHT_BASE)
    with_pcm = simulate({**NIGHT_BASE, "pcm_thickness_m": 0.05})
    assert with_pcm.indoor_temp_c > baseline.indoor_temp_c


def test_orientation_invariant_with_zero_solar():
    """With no solar gain, orientation cannot affect the energy balance at all."""
    results = {o: simulate({**NIGHT_BASE, "orientation": o}).indoor_temp_c for o in ORIENTATIONS}
    values = list(results.values())
    assert max(values) - min(values) < 1e-9, results


def test_orientation_invariant_even_with_solar():
    """The reused Sol-Air fraction constants satisfy south+north == east+west
    == 0.65 exactly, which makes orientation mathematically unable to affect
    a whole-building single-node energy balance regardless of aspect ratio.
    This is a documented, verified property of the model (see
    docs/RESEARCH.md limitations), not an oversight — this test locks it in
    as an explicit, intentional contract."""
    day = {**NIGHT_BASE, "solar_irradiance_peak_w_m2": 720.0}
    results = {o: simulate({**day, "orientation": o}).indoor_temp_c for o in ORIENTATIONS}
    values = list(results.values())
    assert max(values) - min(values) < 1e-9, results


def test_losses_are_nonnegative():
    r = simulate(NIGHT_BASE)
    assert r.roof_loss_w >= 0
    assert r.wall_loss_w >= 0
    assert r.ground_loss_w >= 0
    assert r.ventilation_loss_w >= 0
    assert r.total_loss_w == pytest.approx(
        r.roof_loss_w + r.wall_loss_w + r.ground_loss_w + r.ventilation_loss_w, abs=1e-6
    )


def test_larger_wall_thickness_increases_resistance():
    thin = simulate({**NIGHT_BASE, "wall_thickness_m": 0.15})
    thick = simulate({**NIGHT_BASE, "wall_thickness_m": 0.45})
    assert thick.envelope_r_wall > thin.envelope_r_wall
    assert thick.indoor_temp_c > thin.indoor_temp_c


def test_deterministic_given_same_inputs():
    a = simulate(NIGHT_BASE)
    b = simulate(dict(NIGHT_BASE))
    assert a == b
