"""
Synthetic Dataset Generation
=============================
Samples the shelter design space (geometry, orientation, wall material
composition, ventilation, internal loads) crossed with real
(region, season, hour-of-day) climate instants, runs each design point
through the analytic simulator (`simulator.simulate`), and writes a flat
CSV suitable for supervised ML training.

Reproducibility: a fixed `numpy.random.default_rng(seed)` drives every draw,
and draws are made in a fixed, documented order — the same seed always
produces byte-identical output (verified by `tests/test_reproducibility.py`).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .simulator import DESIGN_BOUNDS, ORIENTATIONS, PRIMARY_MATERIALS, simulate
    from .climate_data import REGIONS, SEASONS, HOURS, get_hourly_climate
except ImportError:  # allows `python dataset.py` when run directly from this folder
    from simulator import DESIGN_BOUNDS, ORIENTATIONS, PRIMARY_MATERIALS, simulate
    from climate_data import REGIONS, SEASONS, HOURS, get_hourly_climate

DEFAULT_SEED = 42
DEFAULT_N_SAMPLES = 6000
DATA_DIR = Path(__file__).resolve().parent / "data"


def _sample_designs(n: int, rng: np.random.Generator) -> pd.DataFrame:
    b = DESIGN_BOUNDS
    rows = []
    for _ in range(n):
        region = rng.choice(REGIONS)
        season = rng.choice(SEASONS)
        hour = int(rng.choice(HOURS))
        ambient_temp_c, solar_w_m2, wind_speed_m_s = get_hourly_climate(region, season, hour)

        has_insulation = rng.random() < 0.5
        insulation_thickness_m = float(rng.uniform(0.02, b["insulation_thickness_m"][1])) if has_insulation else 0.0

        has_pcm = rng.random() < 0.5
        pcm_thickness_m = float(rng.uniform(0.01, b["pcm_thickness_m"][1])) if has_pcm else 0.0

        rows.append({
            "region": region,
            "season": season,
            "hour": hour,
            "ambient_temp_c": ambient_temp_c,
            "solar_irradiance_peak_w_m2": solar_w_m2,
            "wind_speed_m_s": wind_speed_m_s,
            "length_m": float(rng.uniform(*b["length_m"])),
            "width_m": float(rng.uniform(*b["width_m"])),
            "height_m": float(rng.uniform(*b["height_m"])),
            "wall_thickness_m": float(rng.uniform(*b["wall_thickness_m"])),
            "roof_thickness_m": float(rng.uniform(*b["roof_thickness_m"])),
            "orientation": rng.choice(ORIENTATIONS),
            "primary_material": rng.choice(PRIMARY_MATERIALS),
            "insulation_thickness_m": insulation_thickness_m,
            "pcm_thickness_m": pcm_thickness_m,
            "occupant_count": int(rng.integers(b["occupant_count"][0], b["occupant_count"][1] + 1)),
            "equipment_load_w": float(rng.uniform(*b["equipment_load_w"])),
            "air_changes_per_hour": float(rng.uniform(*b["air_changes_per_hour"])),
        })
    return pd.DataFrame(rows)


def generate_dataset(n_samples: int = DEFAULT_N_SAMPLES, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    designs = _sample_designs(n_samples, rng)

    records = []
    for _, row in designs.iterrows():
        design = row.to_dict()
        result = simulate(design)
        record = dict(design)
        record.update({
            "indoor_temp_c": result.indoor_temp_c,
            "roof_loss_w": result.roof_loss_w,
            "wall_loss_w": result.wall_loss_w,
            "ground_loss_w": result.ground_loss_w,
            "ventilation_loss_w": result.ventilation_loss_w,
            "total_loss_w": result.total_loss_w,
            "envelope_r_wall": result.envelope_r_wall,
            "envelope_r_roof": result.envelope_r_roof,
            "room_volume_m3": result.room_volume_m3,
        })
        records.append(record)

    df = pd.DataFrame(records)
    df.insert(0, "sample_id", range(len(df)))
    return df


def main():
    parser = argparse.ArgumentParser(description="Generate the ThermalCraft ML research dataset.")
    parser.add_argument("--n-samples", type=int, default=DEFAULT_N_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=str, default=str(DATA_DIR / "thermal_dataset.csv"))
    args = parser.parse_args()

    df = generate_dataset(n_samples=args.n_samples, seed=args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows x {len(df.columns)} columns to {out_path}")
    print(df.describe(include="all").transpose().to_string())


if __name__ == "__main__":
    main()
