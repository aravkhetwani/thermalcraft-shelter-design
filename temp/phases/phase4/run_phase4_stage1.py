"""
Phase 4 Stage 4.1: Runner Script for Earth-Air Heat Exchanger (EAHE) Passive Cooling Pipeline
-------------------------------------------------------------------------------------------
Simulates buried underground air duct cooling coupling in ANSYS MAPDL (SOLID87)
and analyzes air temperature drop, Nusselt numbers, and total passive cooling wattage (Watts & TR).

Generates:
  - 3D PyVista Subsurface Soil Thermal Plume Cutaway
  - 2D Soil Depth Temperature Profiles (Summer vs Winter) & Duct Cooling Trajectories
  - Parametric Performance Comparison Table for Pipe Sizing and Flow Rates
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from ansys.mapdl.core import launch_mapdl

from phases.phase4.eahe_model import (
    SoilProperties,
    EAHEPipeConfig,
    solve_eahe_analytical,
    run_3d_eahe_soil_fea,
    render_3d_eahe_cutaway,
    plot_eahe_engineering_charts
)


def run_phase4_stage1():
    print("=" * 80)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 4 STAGE 4.1 EARTH-AIR HEAT EXCHANGER (EAHE)")
    print("=" * 80)

    # 1. Define Soil & Baseline Pipe Configuration
    # Harsh Indian Arid Zone (Jodhpur / Bikaner / Jaisalmer)
    soil_props = SoilProperties(
        conductivity=1.25,        # W/(m·K) (Damp silt/clay subsoil)
        density=1900.0,           # kg/m³
        specific_heat=1200.0,     # J/(kg·K)
        t_mean_annual=25.0,       # 25°C annual average
        amplitude_annual=12.0,    # Surface swings between 13°C (Winter) and 37°C (Summer)
        t_shift_days=35.0
    )

    baseline_pipe = EAHEPipeConfig(
        diameter=0.20,            # 200 mm inner diameter
        thickness=0.008,          # 8 mm HDPE / PVC
        length=25.0,              # 25 meters long
        depth=3.0,                # 3 meters burial depth
        pipe_conductivity=0.25,   # W/(m·K)
        air_velocity=2.5,         # 2.5 m/s flow velocity
        t_inlet=44.0              # 44°C scorching outdoor summer air
    )

    figures_dir = PROJECT_ROOT / "report" / "phase4" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 2. Solve Analytical NTU Convective Heat Exchanger Model
    print("\n[Step 1/3] Solving Analytical Turbulent Convective Duct Heat Transfer...")
    res = solve_eahe_analytical(pipe=baseline_pipe, soil=soil_props, day_of_year=150.0)

    print("\n" + "=" * 65)
    print("EAHE BASELINE PASSIVE COOLING PERFORMANCE AUDIT:")
    print("=" * 65)
    print(f"  Burial Depth (z):               {baseline_pipe.depth:.1f} m")
    print(f"  Undisturbed Soil Temp at Depth: {res.soil_temp_at_depth:.2f} °C (Constant)")
    print(f"  Pipe Diameter & Length:         D = {baseline_pipe.diameter*1000:.0f} mm | L = {baseline_pipe.length:.1f} m")
    print(f"  Air Flow Velocity & Rate:       v = {baseline_pipe.air_velocity:.1f} m/s | V = {res.volume_flow_rate_m3h:.0f} m³/h ({res.mass_flow_rate:.3f} kg/s)")
    print(f"  Reynolds Number (Re):           {res.reynolds_number:.0f} (Fully Turbulent)")
    print(f"  Nusselt Number (Nu):            {res.nusselt_number:.1f}")
    print(f"  Convective Film Coeff (h):      {res.h_convection:.2f} W/(m²·K)")
    print("  -------------------------------------------------------------")
    print(f"  Inlet Hot Air Temperature:      {baseline_pipe.t_inlet:.1f} °C")
    print(f"  Discharged Cool Air to Shelter: {res.t_outlet:.2f} °C")
    print(f"  Passive Temperature Drop:       -{res.temperature_drop:.2f} °C")
    print(f"  TOTAL PASSIVE COOLING POWER:    {res.cooling_power_watts:.0f} Watts ({res.cooling_power_tr:.2f} Tons of Refrigeration)")
    print("=" * 65)

    # 3. Parametric Sensitivity Study (Diameters & Velocities)
    print("\n[Step 2/3] Performing Parametric Sizing & Velocity Sweep...")
    print("\n" + "-" * 75)
    print(f"{'Diameter (mm)':<15} | {'Velocity (m/s)':<15} | {'Flow (m³/h)':<12} | {'T_out (°C)':<12} | {'Cooling (Watts)':<15}")
    print("-" * 75)

    diameters = [0.15, 0.20, 0.25]
    velocities = [1.5, 2.5, 3.5]

    for d in diameters:
        for v in velocities:
            p_config = EAHEPipeConfig(
                diameter=d, thickness=0.008, length=25.0, depth=3.0,
                pipe_conductivity=0.25, air_velocity=v, t_inlet=44.0
            )
            p_res = solve_eahe_analytical(pipe=p_config, soil=soil_props, day_of_year=150.0)
            print(f"{d*1000:<15.0f} | {v:<15.1f} | {p_res.volume_flow_rate_m3h:<12.0f} | {p_res.t_outlet:<12.2f} | {p_res.cooling_power_watts:<15.0f}")
    print("-" * 75)

    # 4. 3D FEA Soil Domain Simulation in ANSYS MAPDL
    print("\n[Step 3/3] Launching ANSYS MAPDL for 3D Underground Thermal Domain FEA...")
    mapdl = launch_mapdl(override=True)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    grid, t_fea_out = run_3d_eahe_soil_fea(pipe=baseline_pipe, soil=soil_props, existing_mapdl=mapdl)

    # 5. Render 3D PyVista Diagrams & Engineering Charts
    print("\nGenerating 3D PyVista Visuals & 2D Engineering Charts...")
    cutaway_path = str(figures_dir / "stage_4_1_3d_eahe_subsurface_cutaway.png")
    render_3d_eahe_cutaway(grid, baseline_pipe, res, cutaway_path)
    print(f"  Saved: {cutaway_path}")

    chart_path = str(figures_dir / "stage_4_1_eahe_engineering_charts.png")
    plot_eahe_engineering_charts(res, soil_props, chart_path)
    print(f"  Saved: {chart_path}")

    mapdl.exit()
    print("\nANSYS session safely closed.")
    print("=" * 80)
    print("PHASE 4 STAGE 4.1 COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_phase4_stage1()
