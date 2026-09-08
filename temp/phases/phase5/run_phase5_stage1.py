"""
Phase 5 Stage 5.1: Runner Script for 5 Indian Climate Zones Adaptation & Bio-PCM Latent Heat FEA
------------------------------------------------------------------------------------------------
Simulates climate adaptation across all 5 official Indian Climate Zones (Hot-Dry, Warm-Humid, Composite,
Cold-Cloudy, Cold-Sunny) and simulates non-linear Bio-PCM (PureTemp 25) phase-change latent storage in ANSYS MAPDL (SOLID87).

Generates:
  - 3D PyVista Cutaway Visual of Shelter with Embedded Bio-PCM Isothermal Latent Heat Ceiling/Wall Lining
  - 2D Engineering Performance Analytics (5-Zone Diurnal Curves, Non-Linear Enthalpy, Heat Flux Damping, Discomfort DDH Reduction)
  - Full parametric comparison audit table across all 5 Indian climate regions
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from phases.phase5.climate_pcm import (
    INDIAN_CLIMATE_ZONES,
    BioPCMProperties,
    MultiClimatePCMSimulator,
    BioPCMFEA,
    render_3d_pcm_visualization,
    plot_5zones_pcm_analytics
)


def run_phase5_stage1():
    print("=" * 80)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 5 STAGE 5.1 MULTI-CLIMATE ADAPTATION & BIO-PCM")
    print("=" * 80)

    # 1. Initialize Bio-PCM and Multi-Climate Simulator
    pcm_props = BioPCMProperties(
        name="PureTemp 25 / BioPCMTM Q25",
        t_solidus=24.0,
        t_liquidus=26.0,
        t_melt=25.0,
        latent_heat_jkg=2.10e5, # 210 kJ/kg
        density=860.0,
        conductivity=0.20,
        layer_thickness=0.020 # 20 mm
    )

    simulator = MultiClimatePCMSimulator(pcm_props)

    figures_dir = PROJECT_ROOT / "report" / "phase5" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 2. Run 24-Hour Diurnal Benchmarks Across All 5 Indian Climate Zones
    print("\n[Step 1/3] Simulating Diurnal Thermal Performance across All 5 Indian Climate Zones...")
    sim_results = {}
    for zone_key in INDIAN_CLIMATE_ZONES:
        sim_results[zone_key] = simulator.simulate_zone_diurnal_response(zone_key)

    print("\n" + "=" * 90)
    print("5 INDIAN CLIMATE ZONES (NBC 2016) — PASSIVE BIO-PCM BENCHMARK AUDIT:")
    print("=" * 90)
    print(f"{'Climate Zone':<15} | {'City / Region':<22} | {'T_max Base':<11} | {'T_max PCM':<11} | {'Peak Drop':<10} | {'DDH Saved':<10}")
    print("-" * 90)

    for z_key, res in sim_results.items():
        z_name = res["zone"].name
        city = res["zone"].city
        t_base_max = max(res["t_indoor_base"])
        t_pcm_max = max(res["t_indoor_pcm"])
        drop = res["peak_temp_reduction"]
        ddh_pct = res["ddh_reduction_pct"]
        print(f"{z_name:<15} | {city:<22} | {t_base_max:<11.2f} | {t_pcm_max:<11.2f} | -{drop:<9.2f} | {ddh_pct:<9.1f}%")
    print("=" * 90)

    # 3. Generate 2D Analytics Charts
    print("\n[Step 2/3] Generating 2D Multi-Climate Benchmark Curves & Non-Linear Enthalpy Plots...")
    chart_path = str(figures_dir / "stage_5_1_5zones_pcm_analytics.png")
    plot_5zones_pcm_analytics(sim_results, pcm_props, chart_path)

    # 4. 3D FEA in ANSYS MAPDL & PyVista 3D Visualization
    print("\n[Step 3/3] Executing 3D ANSYS MAPDL Non-Linear ENTH Simulation & PyVista Rendering...")
    vtk_path = str(figures_dir / "stage_5_1_pcm_shelter.vtk")
    fea = BioPCMFEA(pcm_props)
    fea_res = fea.solve_3d_pcm_shelter(vtk_path)

    render_img_path = str(figures_dir / "stage_5_1_3d_pcm_cutaway.png")
    benchmark_meta = {
        "pcm_t_melt": pcm_props.t_melt,
        "peak_reduction": sim_results["hot_dry"]["peak_temp_reduction"]
    }
    render_3d_pcm_visualization(vtk_path, render_img_path, benchmark_meta)

    print("\n" + "=" * 80)
    print("PHASE 5 STAGE 5.1 COMPLETED SUCCESSFULLY!")
    print(f"Figures and Reports Generated in: {figures_dir}")
    print("=" * 80)


if __name__ == "__main__":
    run_phase5_stage1()
