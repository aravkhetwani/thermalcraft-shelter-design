"""
Phase 1 Execution Script.
Runs parametric simulations for both standard masonry and insulated walls,
extracts temperature and heat flux fields, validates against Fourier's Law,
and exports publication-quality diagnostic figures for the Phase 1 report.
"""

import os
from pathlib import Path
from src.parametric_wall import WallSimulationConfig, run_parametric_wall
from ansys.mapdl.core import launch_mapdl

def main():
    print("=" * 70)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 1 SIMULATION EXECUTION")
    print("=" * 70)

    # Ensure output directories exist
    fig_dir = Path("report/phase1/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy folders for upcoming phases
    for p in range(2, 7):
        Path(f"report/phase{p}").mkdir(parents=True, exist_ok=True)

    print("\n[Step 1/3] Launching ANSYS MAPDL Solver Instance...")
    mapdl = launch_mapdl(loglevel="WARNING", print_com=False)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    try:
        # -------------------------------------------------------------
        # Case A: Standard Masonry Wall (k = 0.8 W/m·K)
        # -------------------------------------------------------------
        print("\n" + "-" * 60)
        print("[Case A] Running Standard Brick Wall Simulation (k = 0.8 W/m·K)")
        print("-" * 60)
        
        config_a = WallSimulationConfig(
            width=1.0,
            height=0.2,
            thermal_conductivity=0.8,
            outside_temperature=42.0,  # Peak Indian summer ambient
            inside_temperature=26.0,   # Target indoor comfort
            mesh_size=0.04
        )
        
        plot_a_path = str(fig_dir / "case_a_brick_wall_flux.png")
        result_a = run_parametric_wall(
            config=config_a,
            existing_mapdl=mapdl,
            save_plot_path=plot_a_path
        )
        
        print(f"Nodes Generated:       {len(result_a.node_numbers)}")
        print(f"Elements Generated:    {len(result_a.elem_centroids_x)}")
        print(f"Temperature Range:     {result_a.min_temperature:.2f} °C to {result_a.max_temperature:.2f} °C (Mean: {result_a.avg_temperature:.2f} °C)")
        print(f"Simulated Heat Flux:   {result_a.simulated_avg_heat_flux_x:.3f} W/m²")
        print(f"Theoretical Heat Flux: {result_a.theoretical_heat_flux:.3f} W/m²")
        print(f"Relative Error:        {result_a.relative_error_percent:.5f}%")

        # -------------------------------------------------------------
        # Case B: High-Performance Insulated Wall (k = 0.04 W/m·K)
        # -------------------------------------------------------------
        print("\n" + "-" * 60)
        print("[Case B] Running High-Performance Insulated Wall (k = 0.04 W/m·K)")
        print("-" * 60)
        
        config_b = WallSimulationConfig(
            width=0.25,                # Realistic thickness (250 mm)
            height=0.2,
            thermal_conductivity=0.04, # Mineral wool / EPS insulation
            outside_temperature=42.0,
            inside_temperature=26.0,
            mesh_size=0.02
        )
        
        plot_b_path = str(fig_dir / "case_b_insulated_wall_flux.png")
        result_b = run_parametric_wall(
            config=config_b,
            existing_mapdl=mapdl,
            save_plot_path=plot_b_path
        )

        print(f"Nodes Generated:       {len(result_b.node_numbers)}")
        print(f"Elements Generated:    {len(result_b.elem_centroids_x)}")
        print(f"Temperature Range:     {result_b.min_temperature:.2f} °C to {result_b.max_temperature:.2f} °C (Mean: {result_b.avg_temperature:.2f} °C)")
        print(f"Simulated Heat Flux:   {result_b.simulated_avg_heat_flux_x:.3f} W/m²")
        print(f"Theoretical Heat Flux: {result_b.theoretical_heat_flux:.3f} W/m²")
        print(f"Relative Error:        {result_b.relative_error_percent:.5f}%")

        print("\n" + "=" * 70)
        print("HEAT GAIN REDUCTION COMPARISON:")
        heat_flux_reduction = (1.0 - (result_b.simulated_avg_heat_flux_x / result_a.simulated_avg_heat_flux_x)) * 100.0
        print(f"Standard Brick Wall Heat Ingress Rate:   {result_a.simulated_avg_heat_flux_x:.2f} W/m²")
        print(f"Insulated Passive Wall Heat Ingress Rate: {result_b.simulated_avg_heat_flux_x:.2f} W/m²")
        print(f"Thermal Ingress Reduction:               {heat_flux_reduction:.1f}%")
        print("=" * 70)

    finally:
        print("\n[Step 3/3] Closing ANSYS MAPDL Solver...")
        mapdl.exit()
        print("ANSYS session successfully closed.")

if __name__ == "__main__":
    main()
