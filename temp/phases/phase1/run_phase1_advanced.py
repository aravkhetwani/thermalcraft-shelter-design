"""
Phase 1 Advanced Runner.
Executes:
1. Multi-Layer Composite Wall Simulation.
2. 2D Geometric Thermal Bridge Simulation.
Exports diagnostic figures to report/phase1/figures/.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ansys.mapdl.core import launch_mapdl
from phases.phase1.composite_wall import CompositeWallConfig, LayerConfig, run_composite_wall
from phases.phase1.thermal_bridge import CornerBridgeConfig, run_corner_bridge


def main():
    print("=" * 75)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 1 ADVANCED SIMULATIONS")
    print("=" * 75)

    fig_dir = Path("report/phase1/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Step 1/3] Launching Shared ANSYS MAPDL Solver Instance...")
    mapdl = launch_mapdl(loglevel="WARNING", print_com=False)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    try:
        # Simulation 1: Multi-Layer Composite Wall
        print("\n" + "-" * 65)
        print("[Simulation 1] Multi-Layer Composite Wall (4 Layers)")
        print("-" * 65)

        composite_config = CompositeWallConfig(
            layers=[
                LayerConfig(name="Ext Plaster", thickness=0.020, thermal_conductivity=0.87),
                LayerConfig(name="Burnt Brick", thickness=0.200, thermal_conductivity=0.81),
                LayerConfig(name="EPS Insulation", thickness=0.050, thermal_conductivity=0.035),
                LayerConfig(name="Int Plaster", thickness=0.015, thermal_conductivity=0.72),
            ],
            height=0.20, outside_temperature=42.0, inside_temperature=26.0, mesh_size=0.005
        )

        comp_result = run_composite_wall(
            config=composite_config, existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_1_3_composite_wall.png")
        )

        print(f"Simulated Heat Flux:     {comp_result.simulated_avg_heat_flux_x:.4f} W/m²")
        print(f"Theoretical Heat Flux:   {comp_result.theoretical_heat_flux:.4f} W/m² (Error: {comp_result.relative_error_percent:.5f}%)")

        # Simulation 2: 2D Corner Thermal Bridge
        print("\n" + "-" * 65)
        print("[Simulation 2] 2D Corner Thermal Bridge Analysis (L-Junction)")
        print("-" * 65)

        corner_config = CornerBridgeConfig(
            arm_length_x=0.70, arm_length_y=0.70, wall_thickness=0.25,
            thermal_conductivity=0.80, outside_temperature=42.0, inside_temperature=26.0, mesh_size=0.015
        )

        corner_result = run_corner_bridge(
            config=corner_config, existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_1_4_corner_thermal_bridge.png")
        )

        print(f"Nominal 1D Heat Flux: {corner_result.nominal_1d_heat_flux:.2f} W/m²")
        print(f"Peak Corner Heat Flux: {corner_result.max_heat_flux:.2f} W/m² (Amplification: {corner_result.corner_flux_concentration_ratio:.2f}x)")

    finally:
        print("\n[Step 3/3] Closing ANSYS MAPDL Solver...")
        mapdl.exit()
        print("ANSYS session safely closed.")


if __name__ == "__main__":
    main()
