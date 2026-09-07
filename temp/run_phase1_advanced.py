"""
Phase 1 Advanced Runner.
Executes:
1. Multi-Layer Composite Wall Simulation (External Plaster + Burnt Brick + EPS Insulation + Internal Plaster).
2. 2D Geometric Thermal Bridge Simulation (L-Shaped Corner Junction).
Exports diagnostic figures to report/phase1/figures/.
"""

from pathlib import Path
from ansys.mapdl.core import launch_mapdl
from src.composite_wall import CompositeWallConfig, LayerConfig, run_composite_wall
from src.thermal_bridge import CornerBridgeConfig, run_corner_bridge


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
        # =========================================================================
        # Simulation 1: Multi-Layer Composite Wall (Stage 1.3)
        # =========================================================================
        print("\n" + "-" * 65)
        print("[Simulation 1] Multi-Layer Composite Wall (4 Layers)")
        print("Layers: Exterior Plaster (20mm) -> Brick (200mm) -> EPS (50mm) -> Interior Plaster (15mm)")
        print("-" * 65)

        composite_config = CompositeWallConfig(
            layers=[
                LayerConfig(name="Ext Plaster", thickness=0.020, thermal_conductivity=0.87), # Cement plaster
                LayerConfig(name="Burnt Brick", thickness=0.200, thermal_conductivity=0.81), # Standard clay brick
                LayerConfig(name="EPS Insulation", thickness=0.050, thermal_conductivity=0.035), # Expanded Polystyrene
                LayerConfig(name="Int Plaster", thickness=0.015, thermal_conductivity=0.72), # Gypsum/lime plaster
            ],
            height=0.20,
            outside_temperature=42.0,  # Peak outdoor ambient
            inside_temperature=26.0,   # Indoor comfort
            mesh_size=0.005            # High-resolution 5mm mesh
        )

        comp_plot_path = str(fig_dir / "stage_1_3_composite_wall.png")
        comp_result = run_composite_wall(
            config=composite_config,
            existing_mapdl=mapdl,
            save_plot_path=comp_plot_path
        )

        print(f"Total Wall Thickness:    {comp_result.total_thickness * 1000:.1f} mm")
        print(f"Total Thermal R-Value:   {comp_result.total_r_value:.4f} m²·K/W")
        print(f"U-Value:                 {comp_result.u_value:.4f} W/m²·K")
        print(f"Simulated Heat Flux:     {comp_result.simulated_avg_heat_flux_x:.4f} W/m²")
        print(f"Theoretical Heat Flux:   {comp_result.theoretical_heat_flux:.4f} W/m²")
        print(f"Relative Error:          {comp_result.relative_error_percent:.5f}%")
        print("\nInterface Temperatures:")
        for idx, (layer, temp) in enumerate(zip(composite_config.layers, comp_result.theoretical_interface_temps[1:]), start=1):
            print(f"  Layer {idx} ({layer.name:15s}): Outlet T = {temp:.2f} °C")

        # =========================================================================
        # Simulation 2: 2D Corner Thermal Bridge (Stage 1.4)
        # =========================================================================
        print("\n" + "-" * 65)
        print("[Simulation 2] 2D Corner Thermal Bridge Analysis (L-Junction)")
        print("Analyzing 2D geometric heat divergence and flux amplification at corners")
        print("-" * 65)

        corner_config = CornerBridgeConfig(
            arm_length_x=0.70,
            arm_length_y=0.70,
            wall_thickness=0.25,        # 250 mm wall
            thermal_conductivity=0.80,  # Brick
            outside_temperature=42.0,
            inside_temperature=26.0,
            mesh_size=0.015             # 15mm mesh
        )

        corner_plot_path = str(fig_dir / "stage_1_4_corner_thermal_bridge.png")
        corner_result = run_corner_bridge(
            config=corner_config,
            existing_mapdl=mapdl,
            save_plot_path=corner_plot_path
        )

        print(f"Nominal 1D Heat Flux (Far from corner): {corner_result.nominal_1d_heat_flux:.2f} W/m²")
        print(f"Peak Heat Flux (At Inner Corner):       {corner_result.max_heat_flux:.2f} W/m²")
        print(f"Corner Flux Amplification Factor:       {corner_result.corner_flux_concentration_ratio:.2f}x")
        print(f"Total Nodes: {len(corner_result.node_numbers)}, Total Elements: {len(corner_result.elem_centroids_x)}")

        print("\n" + "=" * 75)
        print("PHASE 1 SIMULATION SUITE COMPLETED SUCCESSFULLY!")
        print("=" * 75)

    finally:
        print("\n[Step 3/3] Closing ANSYS MAPDL Solver...")
        mapdl.exit()
        print("ANSYS session safely closed.")


if __name__ == "__main__":
    main()
