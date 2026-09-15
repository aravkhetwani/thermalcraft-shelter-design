"""
Analytic Steady-State Thermal Simulator
========================================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System — Research Extension

WHY THIS SIMULATOR EXISTS
--------------------------
The project's FEA path (`engine/physics_engine.py`) requires a licensed local
ANSYS MAPDL install to execute. On this machine, ANSYS Student is installed
but the Mechanical APDL solver component itself is absent (verified: no
`ansysNNN.exe` under any `vNNN/ansys/bin/winx64`; `launch_mapdl()` fails to
auto-detect an executable). Large-scale ML dataset generation needs thousands
of fast, deterministic simulation calls, which a per-call ANSYS FEA solve
could not provide even if it were available (each solve takes seconds to
minutes).

This module is NOT a replacement for the FEA engine and does not claim FEA
-level spatial resolution. It assembles the project's own *already-verified*
building-physics equations from `engine/physics_preprocessor.py` (McAdams
wind convection correlation, Sol-Air temperature equations — both taken
verbatim, unmodified) into a complete, closed-form steady-state lumped-
parameter energy balance for the whole shelter — a standard simplified
building-energy modeling approach (comparable in spirit to ISO 13790 /
ASHRAE steady-state methods), which the existing codebase computed the
*ingredients* for but never assembled into a solvable system (the assembly
step was always handed off to the ANSYS FEA mesh solve instead).

WHAT IS REUSED VS. NEW
-----------------------
Reused verbatim from `engine/physics_preprocessor.py` (via `PhysicsPreprocessor.process`):
  - McAdams external convection film coefficient: h_out = max(10, 5.7 + 3.8*v_wind)
  - Sol-Air temperature: T_sol-air = T_amb + alpha*I/h_out
  - Room air volume, internal volumetric heat generation
  - Multi-layer wall resistance composition
  - Ventilation heat removal capacity: C_vent = rho*V_dot*Cp

New in this module:
  - A corrected, orientation-aware assignment of solar gain fractions to the
    four vertical faces (see `_facing_fractions`). The existing FEA boundary
    condition code (`engine/boundary_conditions.py`) computes
    `orientation_azimuth_deg` but never actually uses it — every run applies
    the same fixed south/north/east/west sol-air values to the same fixed
    geometric faces regardless of the user's chosen orientation. This is a
    genuine gap in the reference engine (documented in
    `docs/RESEARCH.md` limitations). This simulator fixes it by rotating
    which face receives which solar fraction based on orientation, while
    reusing the identical underlying Sol-Air formula and fraction constants.
  - A full closed-form energy balance (roof + 4 walls + ground + ventilation
    + internal gains) solved for one steady-state indoor air temperature.
  - Per-surface heat-loss decomposition and a documented efficiency metric.

KEY MODELING LIMITATIONS (see docs/RESEARCH.md for full discussion)
---------------------------------------------------------------------
  - Steady-state only: no thermal mass / time lag, no true 24h transient
    response. A given design's PCM latent-heat buffering is NOT captured by
    a steady-state model — only its conductive resistance is. This is an
    honest limitation, not a hidden approximation.
  - Roof and floor materials are fixed reference constructions (RCC roof,
    concrete floor slab) — only the wall/insulation/PCM combination and
    layer thicknesses are treated as design variables, matching what the
    existing UI actually exposes to the end user.
  - Radiative exchange with the night sky (an additional real loss mechanism
    at high altitude, clear-sky nights) is not modeled; only convective Sol-
    Air boundary conditions are used, exactly as in the reference FEA path.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

# --- Wire up the sibling `engine` package (same pattern as api/service.py) ---
_APP_DIR = Path(__file__).resolve().parent.parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from engine.schemas import (  # noqa: E402
    ClimateInput,
    SiteInput,
    ShelterGeometry,
    EnvelopeAssembly,
    MaterialLayer,
    InternalLoads,
    VentilationInput,
    SimulationInput,
)
from engine.physics_preprocessor import PhysicsPreprocessor  # noqa: E402


# =============================================================================
# Material library — identical values to Ansys simulation/api/service.py's
# MATERIAL_DB, so results stay consistent with the rest of the application.
# =============================================================================
MATERIAL_DB: Dict[str, Dict[str, float]] = {
    "rammed-earth": {"conductivity": 0.27, "density": 1994.0, "specific_heat": 1000.0},
    "pu-foam": {"conductivity": 0.033, "density": 45.0, "specific_heat": 1450.0},
    "pcm": {"conductivity": 0.15, "density": 860.0, "specific_heat": 1500.0},
    "insulated-composite": {"conductivity": 0.09, "density": 420.0, "specific_heat": 2100.0},
}
PRIMARY_MATERIALS = ["rammed-earth", "insulated-composite"]  # structural wall base options
ROOF_MATERIAL = {"conductivity": 1.1, "density": 2300.0, "specific_heat": 1000.0}  # RCC slab, fixed
FLOOR_MATERIAL_CONDUCTIVITY_W_M_K = 1.4  # fixed concrete slab, not a design variable
GROUND_FILM_COEFF_W_M2_K = 10.0  # matches engine/boundary_conditions.py's h_ground

ORIENTATIONS = ["south", "east", "west", "north"]
FACE_ORDER = ["south", "west", "east", "north"]  # matches engine/boundary_conditions.py's fixed faces

# Design-space bounds used both for dataset sampling and for optimization
# search — chosen from engine/schemas.py's own `validate()` physical ranges
# (never looser than what the reference engine itself considers valid).
DESIGN_BOUNDS = {
    "length_m": (3.0, 6.0),
    "width_m": (2.5, 5.0),
    "height_m": (2.2, 3.2),
    "wall_thickness_m": (0.15, 0.45),
    "roof_thickness_m": (0.10, 0.35),
    "insulation_thickness_m": (0.0, 0.15),  # 0 = no insulation layer
    "pcm_thickness_m": (0.0, 0.06),  # 0 = no PCM layer
    "occupant_count": (1, 8),
    "equipment_load_w": (20.0, 200.0),
    "air_changes_per_hour": (0.3, 3.0),
}
# NOTE: ambient_temp_c / solar_irradiance_peak_w_m2 / wind_speed_m_s are NOT
# sampled independently — see climate_data.py. Independent sampling would let
# the design-space search draw physically impossible joint states (e.g.
# coldest night-time temperature paired with peak midday solar). Instead,
# `dataset.py` draws real (region, season, hour-of-day) triples and looks up
# the actual, mutually-consistent climate values for that instant.
FLOOR_THICKNESS_M = 0.20  # fixed, not sampled (keeps design-space dimensionality focused)


@dataclass
class SimResult:
    indoor_temp_c: float
    roof_loss_w: float
    wall_loss_w: float
    ground_loss_w: float
    ventilation_loss_w: float
    total_loss_w: float
    envelope_r_wall: float
    envelope_r_roof: float
    room_volume_m3: float


def _layer_resistance(conductivity_w_m_k: float, thickness_m: float) -> float:
    if thickness_m <= 0.0 or conductivity_w_m_k <= 0.0:
        return 0.0
    return thickness_m / conductivity_w_m_k


def _facing_fractions(orientation: str) -> Dict[str, float]:
    """Assigns the four Sol-Air gain fractions (0.50/0.40/0.25/0.15 — same
    constants as PhysicsPreprocessor) to the four fixed geometric faces,
    rotated so the user-chosen `orientation` face gets the best exposure and
    its opposite face gets the worst — correcting the reference FEA path's
    unused orientation input (see module docstring)."""
    opposite = {"south": "north", "north": "south", "east": "west", "west": "east"}[orientation]
    remaining = [f for f in FACE_ORDER if f not in (orientation, opposite)]
    fractions = {orientation: 0.50, opposite: 0.15}
    fractions[remaining[0]] = 0.40
    fractions[remaining[1]] = 0.25
    return fractions


def _wall_envelope(wall_thickness_m: float, primary_material: str, insulation_thickness_m: float, pcm_thickness_m: float):
    k_primary = MATERIAL_DB[primary_material]["conductivity"]
    r = _layer_resistance(k_primary, wall_thickness_m)
    if insulation_thickness_m > 0.0:
        r += _layer_resistance(MATERIAL_DB["pu-foam"]["conductivity"], insulation_thickness_m)
    if pcm_thickness_m > 0.0:
        r += _layer_resistance(MATERIAL_DB["pcm"]["conductivity"], pcm_thickness_m)
    return max(r, 1e-6)


def _roof_envelope(roof_thickness_m: float, insulation_thickness_m: float, pcm_thickness_m: float):
    r = _layer_resistance(ROOF_MATERIAL["conductivity"], roof_thickness_m)
    if insulation_thickness_m > 0.0:
        r += _layer_resistance(MATERIAL_DB["pu-foam"]["conductivity"], insulation_thickness_m)
    if pcm_thickness_m > 0.0:
        r += _layer_resistance(MATERIAL_DB["pcm"]["conductivity"], pcm_thickness_m)
    return max(r, 1e-6)


def simulate(design: dict) -> SimResult:
    """Runs the closed-form steady-state energy balance for one design point.

    Required keys in `design` (all validated against DESIGN_BOUNDS by callers
    that sample the design space; this function itself only asserts physical
    sanity, matching engine/schemas.py's own validate() spirit):
      length_m, width_m, height_m, wall_thickness_m, roof_thickness_m,
      orientation ('south'|'east'|'west'|'north'), primary_material
      ('rammed-earth'|'insulated-composite'), insulation_thickness_m,
      pcm_thickness_m, occupant_count, equipment_load_w,
      air_changes_per_hour, ambient_temp_c, solar_irradiance_peak_w_m2,
      wind_speed_m_s.
    """
    lx, ly, lz = design["length_m"], design["width_m"], design["height_m"]
    tw, tr, tf = design["wall_thickness_m"], design["roof_thickness_m"], FLOOR_THICKNESS_M
    orientation = design["orientation"]
    primary_material = design["primary_material"]
    ins_t = design["insulation_thickness_m"]
    pcm_t = design["pcm_thickness_m"]

    # --- Reuse the verified physics preprocessor for convection, ground,
    # room volume, internal gains, and ventilation capacity. ---
    climate = ClimateInput(
        ambient_temp_c=design["ambient_temp_c"],
        solar_irradiance_peak_w_m2=design["solar_irradiance_peak_w_m2"],
        wind_speed_m_s=design["wind_speed_m_s"],
    )
    shelter = ShelterGeometry(
        length_m=lx, width_m=ly, height_m=lz,
        wall_thickness_m=tw, roof_thickness_m=tr, floor_thickness_m=tf,
    )
    mat_db = MATERIAL_DB[primary_material]
    wall_mat = MaterialLayer(primary_material, conductivity_w_m_k=mat_db["conductivity"],
                              density_kg_m3=mat_db["density"], specific_heat_j_kg_k=mat_db["specific_heat"],
                              thickness_m=tw)
    envelope = EnvelopeAssembly(wall_material=wall_mat, has_pcm=pcm_t > 0.0)
    site = SiteInput(ground_temp_c=design["ambient_temp_c"] + 5.0)
    loads = InternalLoads(occupant_count=int(design["occupant_count"]), equipment_load_w=design["equipment_load_w"])
    vent = VentilationInput(air_changes_per_hour=design["air_changes_per_hour"])

    sim_input = SimulationInput(climate=climate, shelter=shelter, materials=envelope,
                                 site=site, internal_loads=loads, ventilation=vent)
    derived = PhysicsPreprocessor.process(sim_input)

    h_out = derived.h_outdoor_w_m2_k
    t_amb = design["ambient_temp_c"]
    i_peak = design["solar_irradiance_peak_w_m2"]
    alpha_wall = envelope.wall_solar_absorptivity
    alpha_roof = envelope.roof_solar_absorptivity

    # --- Orientation-corrected Sol-Air temperatures per vertical face ---
    fractions = _facing_fractions(orientation)
    sol_air_face = {face: t_amb + (alpha_wall * frac * i_peak) / h_out for face, frac in fractions.items()}
    sol_air_roof = t_amb + (alpha_roof * i_peak) / h_out

    # --- Envelope resistances / U-values ---
    r_wall = _wall_envelope(tw, primary_material, ins_t, pcm_t)
    r_roof = _roof_envelope(tr, ins_t, pcm_t)
    u_wall = 1.0 / r_wall
    u_roof = 1.0 / r_roof
    u_ground = FLOOR_MATERIAL_CONDUCTIVITY_W_M_K / tf

    wall_h = max(0.1, lz - tf - tr)
    area_roof = lx * ly
    area_ground = lx * ly
    area_south_north = lx * wall_h  # 'south' and 'north' faces span length lx
    area_east_west = ly * wall_h    # 'east' and 'west' faces span width ly
    face_area = {"south": area_south_north, "north": area_south_north,
                 "east": area_east_west, "west": area_east_west}

    c_vent = derived.ventilation_heat_removal_w_per_k
    q_internal = loads.total_heat_watts
    t_ground = derived.ground_boundary_temp_c

    # --- Closed-form steady-state energy balance: sum(U*A*(T_i - T_in)) + Q_internal = 0 ---
    numerator = u_roof * area_roof * sol_air_roof
    denominator = u_roof * area_roof
    for face in FACE_ORDER:
        numerator += u_wall * face_area[face] * sol_air_face[face]
        denominator += u_wall * face_area[face]
    numerator += u_ground * area_ground * t_ground
    denominator += u_ground * area_ground
    numerator += c_vent * t_amb
    denominator += c_vent
    numerator += q_internal

    t_in = numerator / denominator

    roof_loss_w = max(0.0, u_roof * area_roof * (t_in - sol_air_roof))
    wall_loss_w = sum(max(0.0, u_wall * face_area[f] * (t_in - sol_air_face[f])) for f in FACE_ORDER)
    ground_loss_w = max(0.0, u_ground * area_ground * (t_in - t_ground))
    vent_loss_w = max(0.0, c_vent * (t_in - t_amb))
    total_loss_w = roof_loss_w + wall_loss_w + ground_loss_w + vent_loss_w

    return SimResult(
        indoor_temp_c=round(t_in, 4),
        roof_loss_w=round(roof_loss_w, 4),
        wall_loss_w=round(wall_loss_w, 4),
        ground_loss_w=round(ground_loss_w, 4),
        ventilation_loss_w=round(vent_loss_w, 4),
        total_loss_w=round(total_loss_w, 4),
        envelope_r_wall=round(r_wall, 5),
        envelope_r_roof=round(r_roof, 5),
        room_volume_m3=round(derived.room_air_volume_m3, 4),
    )


def simulate_batch(designs: list[dict]) -> list[SimResult]:
    """Convenience loop wrapper — used by the speedup benchmark to time
    naive per-call Python-loop simulator throughput against vectorized
    surrogate inference."""
    return [simulate(d) for d in designs]
