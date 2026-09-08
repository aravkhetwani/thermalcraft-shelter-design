"""
Phase 4 Stage 4.2: Runner Script for Solar Chimney Natural Buoyancy & Coupled Off-Grid EAHE Stack Ventilation
-------------------------------------------------------------------------------------------------------------
Simulates coupled solar-thermal chimney buoyancy dynamics integrated with the Earth-Air Heat Exchanger (EAHE)
in Python and 3D FEA in ANSYS MAPDL (SOLID87).

Generates:
  - 3D PyVista Cutaway Visual of Shelter Room, Solar Chimney Riser, and 3D Airflow Streamtubes
  - 2D Engineering Performance Curves (Solar Irradiance vs Flow & ACH, Height Sweeps, Pressure Budget, Cooling Watts)
  - Detailed engineering audit table across solar radiation and chimney dimensions
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from phases.phase4.solar_chimney import (
    SolarChimneyConfig,
    SolarChimneySolver,
    SolarChimneyFEA,
    render_3d_coupled_flow_visualization,
    plot_solar_chimney_analytics
)


def run_phase4_stage2():
    print("=" * 80)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 4 STAGE 4.2 SOLAR CHIMNEY & COUPLED EAHE VENTILATION")
    print("=" * 80)

    # 1. Initialize Configuration
    config = SolarChimneyConfig(
        height=2.0,            # 2.0 m tall solar chimney
        width=1.0,             # 1.0 m wide
        air_gap=0.20,          # 0.20 m cavity depth
        absorber_alpha=0.95,   # High-absorptivity black selective coating
        glazing_tau=0.88,      # Low-iron glass transmission
        i_solar=800.0,         # 800 W/m2 incident solar radiation
        t_ambient=44.0,        # 44°C scorching outdoor summer air
        t_eahe_inlet=27.8,     # 27.8°C supply air from Stage 4.1 EAHE
        room_volume=33.6,      # 4m x 3m x 2.8m shelter (33.6 m3)
        eahe_length=30.0,
        eahe_diameter=0.25
    )

    figures_dir = PROJECT_ROOT / "report" / "phase4" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 2. Solve Coupled Analytical Thermo-Fluid Model
    print("\n[Step 1/3] Solving Coupled Solar Buoyancy & Hydraulic Loop Equilibrium...")
    solver = SolarChimneySolver(config)
    baseline_res = solver.solve_coupled_flow()

    print("\n" + "=" * 70)
    print("SOLAR CHIMNEY COUPLED VENTILATION & BUOYANCY AUDIT:")
    print("=" * 70)
    print(f"  Incident Solar Radiation:        {baseline_res['i_solar']:.1f} W/m²")
    print(f"  Solar Chimney Dimensions:        H = {baseline_res['height']:.1f} m | W = {config.width:.1f} m | Gap = {config.air_gap*1000:.0f} mm")
    print(f"  Absorber Plate Temperature:      {baseline_res['t_plate_c']:.2f} °C")
    print(f"  Mean Cavity Air Temperature:     {baseline_res['t_cavity_c']:.2f} °C (Delta T_buoyant = {baseline_res['t_cavity_c'] - config.t_ambient:+.2f} °C vs Amb)")
    print(f"  Chimney Exhaust Temperature:     {baseline_res['t_out_c']:.2f} °C")
    print(f"  Thermal Stack Driving Pressure:  {baseline_res['delta_p_buoyancy_pa']:.3f} Pa")
    print("  -------------------------------------------------------------")
    print(f"  EAHE Supply Air Inlet:           {config.t_eahe_inlet:.1f} °C (Pre-cooled by subterranean soil)")
    print(f"  EAHE Duct Hydraulic Loss:        {baseline_res['dp_eahe_total_pa']:.3f} Pa")
    print(f"  Chimney & Throat Loss:           {baseline_res['dp_chimney_total_pa']:.3f} Pa")
    print(f"  Coupled Induced Mass Flow Rate:  {baseline_res['mass_flow_rate_kgs']:.4f} kg/s")
    print(f"  Volumetric Natural Airflow (Q):  {baseline_res['vol_flow_rate_m3h']:.1f} m³/h ({baseline_res['vol_flow_rate_m3s']*1000:.1f} L/s)")
    print(f"  Shelter Air Change Rate (ACH):   {baseline_res['ach']:.2f} ACH (NBC Requirement: 3.0 ACH)")
    print(f"  Zero-Electricity Cooling Power:  {baseline_res['cooling_power_w']:.0f} Watts ({baseline_res['cooling_power_w']/3516.85:.2f} TR)")
    print("=" * 70)

    # 3. Parametric Sensitivity Matrix
    print("\n[Step 2/3] Computing Multi-Dimensional Parametric Sweep...")
    i_array, flow_vs_i, h_array, flow_vs_h = solver.run_parametric_sweep()

    print("\n" + "-" * 75)
    print(f"{'Irradiance (W/m²)':<20} | {'ACH (1/h)':<12} | {'Flow (m³/h)':<14} | {'Stack Head (Pa)':<16} | {'Cooling (W)':<12}")
    print("-" * 75)
    for sample_i in [200, 400, 600, 800, 1000]:
        match = next(d for d in flow_vs_i if abs(d["i_solar"] - sample_i) < 25)
        print(f"{match['i_solar']:<20.0f} | {match['ach']:<12.2f} | {match['vol_flow_rate_m3h']:<14.1f} | {match['delta_p_buoyancy_pa']:<16.3f} | {match['cooling_power_w']:<12.0f}")
    print("-" * 75)

    chart_img_path = str(figures_dir / "stage_4_2_solar_chimney_analytics.png")
    plot_solar_chimney_analytics(i_array, flow_vs_i, h_array, flow_vs_h, chart_img_path)

    # 4. 3D FEA in ANSYS MAPDL & PyVista 3D Visualization
    print("\n[Step 3/3] Executing 3D ANSYS MAPDL Simulation & PyVista Rendering...")
    vtk_path = str(figures_dir / "stage_4_2_shelter_chimney.vtk")
    fea = SolarChimneyFEA(config)
    fea_res = fea.solve_3d_shelter_chimney(vtk_path)

    render_img_path = str(figures_dir / "stage_4_2_3d_coupled_solar_chimney_cutaway.png")
    render_3d_coupled_flow_visualization(vtk_path, render_img_path, baseline_res)

    print("\n" + "=" * 80)
    print("PHASE 4 STAGE 4.2 COMPLETED SUCCESSFULLY!")
    print(f"Figures and Reports Generated in: {figures_dir}")
    print("=" * 80)


if __name__ == "__main__":
    run_phase4_stage2()
