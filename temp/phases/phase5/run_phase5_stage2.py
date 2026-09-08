"""
Phase 5 Stage 5.2: Runner Script for Indirect Solar Gain Trombe Wall & Sunspace Modeling (Cold Climates)
--------------------------------------------------------------------------------------------------------
Simulates South-facing Trombe Wall solar absorption, thermosiphon cavity circulation, and high-mass
masonry thermal time lag heating in severe winter mountain climates (Leh Ladakh / Shimla) in ANSYS MAPDL (SOLID87).

Generates:
  - 3D PyVista Cutaway Visual of Shelter in -16 C Cold with Solar Absorber (72 C), Air Streamtubes, and Living Space (+21.5 C)
  - 2D Engineering Performance Analytics (24h Diurnal Winter Curves, Masonry Thickness vs Lag, Day Convection vs Night Radiation, SSF)
  - Detailed engineering audit table across winter operating regimes
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from phases.phase5.trombe_wall import (
    TrombeWallConfig,
    TrombeWallSolver,
    TrombeWallFEA,
    render_3d_trombe_visualization,
    plot_trombe_wall_analytics
)


def run_phase5_stage2():
    print("=" * 80)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 5 STAGE 5.2 TROMBE WALL COLD-CLIMATE SOLAR HEATING")
    print("=" * 80)

    # 1. Initialize Configuration for Leh Ladakh (-16 C Winter Night, 980 W/m2 High-Altitude Sun)
    config = TrombeWallConfig(
        wall_height=2.6,           # 2.6 m height
        wall_width=3.6,            # 3.6 m width (South facade)
        wall_thickness=0.35,       # 350 mm dense stone masonry mass
        air_gap=0.08,              # 80 mm glazed air cavity
        vent_area_each=0.18,       # Upper & lower vents
        conductivity=1.30,         # W/(m.K)
        density=2200.0,            # kg/m3
        specific_heat=900.0,       # J/(kg.K)
        glazing_tau=0.78,          # Double low-E glazing
        absorber_alpha=0.95,       # Selective black coating
        absorber_eps=0.15,
        t_ambient_min=-16.0,       # -16°C extreme cold winter night
        t_ambient_max=4.0,         # +4°C winter daytime peak
        solar_peak=980.0           # 980 W/m2 clear high-altitude solar flux
    )

    figures_dir = PROJECT_ROOT / "report" / "phase5" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 2. Solve Coupled Analytical Thermo-Siphon & Thermal Lag Physics
    print("\n[Step 1/3] Solving High-Altitude Solar Absorption & Thermo-Siphon Hydrodynamics...")
    solver = TrombeWallSolver(config)
    day_res = solver.solve_daytime_thermosiphon(i_solar=config.solar_peak)
    winter_res = solver.simulate_24h_winter_cycle()

    print("\n" + "=" * 70)
    print("TROMBE WALL SOLAR ABSORPTION & THERMOSIPHON AUDIT (13:00 Solar Peak):")
    print("=" * 70)
    print(f"  Incident Solar Flux on South Facade: {day_res['i_solar']:.1f} W/m²")
    print(f"  Effective Absorbed Solar Radiation:  {day_res['s_eff']:.1f} W/m² (tau=0.78, alpha=0.95)")
    print(f"  Absorber Surface Temperature:        {day_res['t_absorber']:.2f} °C (Outdoor Cold: -6.0 °C)")
    print(f"  Cavity Mean Air Temperature:         {day_res['t_cavity_mean']:.2f} °C")
    print(f"  Upper Vent Discharge Temperature:    {day_res['t_top_vent']:.2f} °C")
    print("  -------------------------------------------------------------")
    print(f"  Thermal Buoyancy Driving Head:       {day_res['dp_buoyancy_pa']:.3f} Pa")
    print(f"  Thermosiphon Natural Airflow (Q):    {day_res['vol_flow_rate_m3h']:.1f} m³/h ({day_res['vol_flow_rate_m3s']*1000:.1f} L/s)")
    print(f"  Daytime Room Air Exchange (ACH):     {day_res['ach']:.2f} ACH")
    print(f"  Daytime Convective Solar Gain:       {day_res['q_conv_delivered_w']:.0f} Watts")
    print(f"  Conductive Heat Stored into Mass:    {day_res['q_cond_stored_w']:.0f} Watts")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("TROMBE WALL NIGHTTIME THERMAL MASS DISCHARGE AUDIT (03:00 Midnight -16°C):")
    print("=" * 70)
    print(f"  Masonry Wall Thickness & Mass:       {config.wall_thickness*1000:.0f} mm ({config.density * config.wall_thickness * config.wall_width * config.wall_height / 1000:.1f} Tons Stone)")
    print(f"  Thermal Phase Time Lag (Delta t):    {winter_res['time_lag_hours']:.2f} Hours")
    print(f"  Amplitude Decrement Factor (mu):     {winter_res['decrement_factor']:.3f}")
    print(f"  Inner Wall Surface Midnight Temp:    {max(winter_res['t_inner_surface']):.2f} °C (Warm Radiator)")
    print(f"  Indoor Living Room Midnight Temp:    {min(winter_res['t_room_trombe']):.2f} °C (Baseline Unheated: {min(winter_res['t_room_base']):.2f} °C)")
    print(f"  Passive Solar Heating Elevation:     +{min(winter_res['t_room_trombe']) - min(winter_res['t_room_base']):.2f} °C Higher Comfort!")
    print("=" * 70)

    # 3. Generate 2D Performance Analytics
    print("\n[Step 2/3] Generating 2D Engineering Performance & Diurnal Winter Curves...")
    chart_path = str(figures_dir / "stage_5_2_trombe_wall_analytics.png")
    plot_trombe_wall_analytics(solver, chart_path)

    # 4. 3D FEA in ANSYS MAPDL & PyVista 3D Visualization
    print("\n[Step 3/3] Executing 3D ANSYS MAPDL Simulation & PyVista Rendering...")
    vtk_path = str(figures_dir / "stage_5_2_trombe_shelter.vtk")
    fea = TrombeWallFEA(config)
    fea_res = fea.solve_3d_trombe_shelter(vtk_path)

    render_img_path = str(figures_dir / "stage_5_2_3d_trombe_cutaway.png")
    render_3d_trombe_visualization(vtk_path, render_img_path, winter_res)

    print("\n" + "=" * 80)
    print("PHASE 5 STAGE 5.2 COMPLETED SUCCESSFULLY!")
    print(f"Figures and Reports Generated in: {figures_dir}")
    print("=" * 80)


if __name__ == "__main__":
    run_phase5_stage2()
