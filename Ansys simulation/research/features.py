"""
Feature Engineering
=====================
Adds physically meaningful, non-leaky engineered features to the raw
dataset produced by `dataset.py`.

Leakage discipline (important): `simulator.simulate()` first computes
envelope resistances / room volume / areas from the design inputs alone,
and only THEN solves the single linear energy-balance equation for the one
unknown, `indoor_temp_c`, from which every loss column
(`roof_loss_w`, `wall_loss_w`, `ground_loss_w`, `ventilation_loss_w`,
`total_loss_w`) is subsequently derived. That means:
  - `envelope_r_wall`, `envelope_r_roof`, `room_volume_m3` are safe features
    for ANY target — they are pre-solve, deterministic functions of the
    design inputs only.
  - The loss columns and `indoor_temp_c` are mutually derived from the same
    solve and must NEVER appear as features of one another. `get_feature_columns`
    enforces this by construction (it excludes all target-side columns).
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

TARGET_COLUMNS = [
    "indoor_temp_c", "roof_loss_w", "wall_loss_w", "ground_loss_w",
    "ventilation_loss_w", "total_loss_w",
]
ID_COLUMNS = ["sample_id"]
CATEGORICAL_COLUMNS = ["region", "season", "orientation", "primary_material"]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a copy of `df` with additional physically meaningful columns.
    Every added column is a deterministic function of pre-solve design
    inputs only (see module docstring) — safe to use as a feature for any
    target in TARGET_COLUMNS."""
    out = df.copy()

    wall_h = np.maximum(0.1, out["height_m"] - 0.20 - out["roof_thickness_m"])  # 0.20 = fixed floor thickness
    out["wall_height_m"] = wall_h
    out["roof_area_m2"] = out["length_m"] * out["width_m"]
    out["wall_area_m2"] = 2.0 * (out["length_m"] + out["width_m"]) * wall_h
    out["envelope_area_m2"] = out["roof_area_m2"] * 2.0 + out["wall_area_m2"]  # roof + floor + walls
    out["surface_area_to_volume"] = out["envelope_area_m2"] / out["room_volume_m3"].clip(lower=1e-6)

    out["ua_wall_w_k"] = out["wall_area_m2"] / out["envelope_r_wall"]
    out["ua_roof_w_k"] = out["roof_area_m2"] / out["envelope_r_roof"]

    out["insulation_present"] = (out["insulation_thickness_m"] > 0.0).astype(int)
    out["pcm_present"] = (out["pcm_thickness_m"] > 0.0).astype(int)

    # Static thermal-mass proxy (density x specific heat x volume of the
    # primary wall layer). NOTE: the steady-state simulator cannot respond to
    # thermal mass at all (see docs/RESEARCH.md limitations) — this feature
    # is included deliberately so the feature-importance analysis can
    # empirically confirm it carries ~no predictive signal for this target,
    # a meaningful, honest negative check rather than an assumed one.
    material_density = out["primary_material"].map({"rammed-earth": 1994.0, "insulated-composite": 420.0})
    material_cp = out["primary_material"].map({"rammed-earth": 1000.0, "insulated-composite": 2100.0})
    out["wall_thermal_mass_proxy"] = material_density * material_cp * out["wall_area_m2"] * out["wall_thickness_m"]

    out["heating_degree_proxy_c"] = (18.0 - out["ambient_temp_c"]).clip(lower=0.0)
    out["internal_gain_w"] = out["occupant_count"] * 100.0 + out["equipment_load_w"]

    return out


def get_feature_columns(df: pd.DataFrame, target: str) -> List[str]:
    """All columns safe to use as features when predicting `target` —
    everything except IDs and every column in TARGET_COLUMNS (including
    `target` itself and every OTHER target, since they are mutually derived
    from the same solve; see module docstring)."""
    assert target in TARGET_COLUMNS, f"Unknown target '{target}'"
    exclude = set(ID_COLUMNS) | set(TARGET_COLUMNS)
    return [c for c in df.columns if c not in exclude]


def encode_features(df: pd.DataFrame, feature_columns: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    """One-hot encodes the categorical columns among `feature_columns`;
    passes numeric columns through unchanged. Returns (encoded_df, final_column_order)."""
    cat_cols = [c for c in feature_columns if c in CATEGORICAL_COLUMNS]
    num_cols = [c for c in feature_columns if c not in CATEGORICAL_COLUMNS]
    encoded = pd.get_dummies(df[feature_columns], columns=cat_cols, drop_first=False)
    final_cols = num_cols + [c for c in encoded.columns if c not in num_cols]
    return encoded[final_cols], final_cols
