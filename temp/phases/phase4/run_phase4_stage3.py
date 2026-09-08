"""
Phase 4 Stage 4.3: Runner Script for Windcatcher (Malqaf/Badgir) Aerodynamics & Diurnal Night-Flushing Control
-------------------------------------------------------------------------------------------------------------
Simulates multi-directional elevated Windcatcher aerodynamic wind capture, wetted terracotta evaporative cooling,
and 24-hour diurnal night-flushing dynamics coupled with ANSYS Mechanical APDL (SOLID87) 3D FEA.

Generates:
  - 3D PyVista Cutaway Visual of Elevated Windcatcher Tower, Internal Downcomer, Room Sweep, and Chimney Plume
  - 2D Engineering Performance Curves (Wind Speed vs Flow/ACH, 24h Diurnal Curves, Wet-Bulb Depression, Pressure Breakdown)
  - Detailed engineering audit table across wind velocity regimes and operational modes
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from phases.phase4.windcatcher import (
    WindcatcherConfig,
    WindcatcherSolver,
    WindcatcherFEA,
    render_3d_windcatcher_visualization,
    plot_windcatcher_analytics
)


def run_phase4_stage3():
    print("=" * 80)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 4 STAGE 4.3 WINDCATCHER & DIURNAL VENTILATION")
    print("=" * 80)

    # 1. Initialize Configuration
    config = WindcatcherConfig(
        tower_height=4.5,          # 4.5 m elevated tower cowl
        cowl_width=1.0,            # 1.0 m intake aperture
        cowl_depth=0.80,           # 0.80 m depth
        duct_area=0.50,            # 0.50 m2 downcomer shaft
        v_wind_10m=3.5,            # 3.5 m/s typical desert breeze at 10m
        t_ambient_day=44.0,        # 44°C peak dry-bulb day
        rh_ambient_day=20.0,       # 20% RH
        t_ambient_night=22.0,      # 22°C desert night
        rh_ambient_night=55.0,     # 55% RH night
        evap_efficiency=0.75,      # 75% evaporative wet-bulb efficiency
        room_volume=33.6           # 4m x 3m x 2.8m shelter
    )

    figures_dir = PROJECT_ROOT / "report" / "phase4" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 2. Solve Coupled Analytical Aerodynamics & Evaporative Physics
    print("\n[Step 1/3] Solving Aerodynamic Pressure Coefficients & Evaporative Thermodynamics...")
    solver = WindcatcherSolver(config)
    day_res = solver.solve_windcatcher_flow(v_wind=config.v_wind_10m, mode="day")
    night_res = solver.solve_windcatcher_flow(v_wind=config.v_wind_10m, mode="night")

    print("\n" + "=" * 70)
    print("WINDCATCHER DAYTIME EVAPORATIVE PRE-COOLING AUDIT (15:00 Solar Peak):")
    print("=" * 70)
    print(f"  Meteorological Wind (10m):       {config.v_wind_10m:.1f} m/s")
    print(f"  Elevated Cowl Wind Speed:        {day_res['v_cowl']:.2f} m/s (ABL Height = {config.tower_height:.1f} m)")
    print(f"  Outdoor Ambient Conditions:      T_db = {day_res['t_ambient']:.1f} °C | RH = {day_res['rh_ambient']:.1f} %")
    print(f"  Psychrometric Wet-Bulb Temp:     T_wb = {day_res['t_wet_bulb']:.2f} °C (Wet-Bulb Depression: {day_res['t_ambient'] - day_res['t_wet_bulb']:.2f} °C)")
    print(f"  Wetted Conduit Supply Temp:      T_supply = {day_res['t_supply']:.2f} °C (Passive Drop: -{day_res['temperature_drop']:.2f} °C)")
    print("  -------------------------------------------------------------")
    print(f"  Dynamic Wind Pressure Head:      {day_res['dp_wind_pa']:.3f} Pa (Delta Cp = {config.cp_windward - config.cp_leeward:.2f})")
    print(f"  Thermal Stack Buoyancy Head:     {day_res['dp_buoyancy_pa']:.3f} Pa (Solar Chimney Assisted)")
    print(f"  Total Driving Aerodynamic Head:  {day_res['dp_total_pa']:.3f} Pa")
    print(f"  Induced Natural Airflow (Q):     {day_res['vol_flow_rate_m3h']:.1f} m³/h ({day_res['vol_flow_rate_m3s']*1000:.1f} L/s)")
    print(f"  Daytime Air Change Rate (ACH):   {day_res['ach']:.2f} ACH")
    print(f"  Delivered Passive Evap Cooling:  {day_res['cooling_power_w']:.0f} Watts ({day_res['cooling_power_w']/3516.85:.2f} TR)")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("WINDCATCHER NIGHT-TIME FLUSHING AUDIT (03:00 Midnight Desert):")
    print("=" * 70)
    print(f"  Outdoor Night Air Temp:          {night_res['t_ambient']:.1f} °C")
    print(f"  Total Driving Aerodynamic Head:  {night_res['dp_total_pa']:.3f} Pa")
    print(f"  Induced Flushing Airflow (Q):    {night_res['vol_flow_rate_m3h']:.1f} m³/h ({night_res['vol_flow_rate_m3s']*1000:.1f} L/s)")
    print(f"  Night Flushing Rate (ACH):       {night_res['ach']:.2f} ACH (Rapid Mass De-energizing)")
    print("=" * 70)

    # 3. Parametric Sensitivity & 2D Analytics
    print("\n[Step 2/3] Generating 2D Engineering Performance & Diurnal Analytics...")
    chart_img_path = str(figures_dir / "stage_4_3_windcatcher_analytics.png")
    plot_windcatcher_analytics(solver, chart_img_path)

    # 4. 3D FEA in ANSYS MAPDL & PyVista 3D Visualization
    print("\n[Step 3/3] Executing 3D ANSYS MAPDL Simulation & PyVista Rendering...")
    vtk_path = str(figures_dir / "stage_4_3_windcatcher_shelter.vtk")
    fea = WindcatcherFEA(config)
    fea_res = fea.solve_3d_windcatcher_shelter(vtk_path)

    render_img_path = str(figures_dir / "stage_4_3_3d_windcatcher_cutaway.png")
    render_3d_windcatcher_visualization(vtk_path, render_img_path, day_res)

    print("\n" + "=" * 80)
    print("PHASE 4 STAGE 4.3 COMPLETED SUCCESSFULLY!")
    print(f"Figures and Reports Generated in: {figures_dir}")
    print("=" * 80)


if __name__ == "__main__":
    run_phase4_stage3()
