"""
Phase 1 Execution Script.
Runs parametric simulations for both standard masonry and insulated walls,
extracts temperature and heat flux fields, validates against Fourier's Law,
and exports publication-quality diagnostic figures for the Phase 1 report.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ansys.mapdl.core import launch_mapdl
from phases.phase1.parametric_wall import WallSimulationConfig, run_parametric_wall


def main():
    print("=" * 70)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 1 SIMULATION EXECUTION")
    print("=" * 70)

    fig_dir = Path("report/phase1/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Step 1/3] Launching ANSYS MAPDL Solver Instance...")
    mapdl = launch_mapdl(loglevel="WARNING", print_com=False)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    try:
        # Case A: Standard Brick Wall (k = 0.8 W/m·K)
        print("\n" + "-" * 60)
        print("[Case A] Running Standard Brick Wall Simulation (k = 0.8 W/m·K)")
        print("-" * 60)
        
        config_a = WallSimulationConfig(
            width=1.0, height=0.2, thermal_conductivity=0.8,
            outside_temperature=42.0, inside_temperature=26.0, mesh_size=0.04
        )
        
        result_a = run_parametric_wall(
            config=config_a, existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "case_a_brick_wall_flux.png")
        )
        
        print(f"Simulated Heat Flux:   {result_a.simulated_avg_heat_flux_x:.3f} W/m²")
        print(f"Theoretical Heat Flux: {result_a.theoretical_heat_flux:.3f} W/m² (Error: {result_a.relative_error_percent:.5f}%)")

        # Case B: Insulated Wall (k = 0.04 W/m·K)
        print("\n" + "-" * 60)
        print("[Case B] Running High-Performance Insulated Wall (k = 0.04 W/m·K)")
        print("-" * 60)
        
        config_b = WallSimulationConfig(
            width=0.25, height=0.2, thermal_conductivity=0.04,
            outside_temperature=42.0, inside_temperature=26.0, mesh_size=0.02
        )
        
        result_b = run_parametric_wall(
            config=config_b, existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "case_b_insulated_wall_flux.png")
        )

        print(f"Simulated Heat Flux:   {result_b.simulated_avg_heat_flux_x:.3f} W/m²")
        print(f"Theoretical Heat Flux: {result_b.theoretical_heat_flux:.3f} W/m² (Error: {result_b.relative_error_percent:.5f}%)")

    finally:
        print("\n[Step 3/3] Closing ANSYS MAPDL Solver...")
        mapdl.exit()
        print("ANSYS session safely closed.")


if __name__ == "__main__":
    main()
