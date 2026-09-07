"""
Phase 2 Stage 2.1 Execution Script.
Executes Convective (Robin) Boundary Condition simulations:
1. Bare Brick Wall under standard convection.
2. 4-Layer Insulated Wall under standard convection.
3. Wind speed sensitivity comparison (Calm vs High Wind).
Exports diagnostic figures to report/phase2/figures/.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ansys.mapdl.core import launch_mapdl
from phases.phase2.convection_wall import ConvectionWallConfig, LayerSpec, run_convection_wall


def main():
    print("=" * 75)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 2 STAGE 2.1 CONVECTION")
    print("=" * 75)

    fig_dir = Path("report/phase2/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Step 1/3] Launching Shared ANSYS MAPDL Solver Instance...")
    mapdl = launch_mapdl(loglevel="WARNING", print_com=False)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    try:
        # Case 1: Bare Brick Wall (250 mm, k = 0.80 W/m·K)
        print("\n" + "-" * 65)
        print("[Case 1] Bare Brick Wall with Convective Air Films")
        print("-" * 65)

        config_brick = ConvectionWallConfig(
            layers=[LayerSpec(name="Burnt Brick", thickness=0.250, thermal_conductivity=0.80)],
            outdoor_ambient_temp=42.0, indoor_ambient_temp=26.0,
            h_outdoor=20.0, h_indoor=7.7, mesh_size=0.01
        )

        res_brick = run_convection_wall(
            config=config_brick, existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_2_1_brick_convection.png")
        )

        print(f"Total R-Value:           {res_brick.r_total:.4f} m²·K/W (U = {res_brick.u_value:.4f} W/m²·K)")
        print(f"Simulated Heat Flux:     {res_brick.simulated_avg_heat_flux_x:.4f} W/m²")
        print(f"Theoretical Heat Flux:   {res_brick.theoretical_heat_flux:.4f} W/m² (Error: {res_brick.relative_error_percent:.5f}%)")
        print(f"Outdoor Surface Temp:    {res_brick.simulated_surf_temp_out:.2f} °C (Air: 42.00 °C)")
        print(f"Indoor Surface Temp:     {res_brick.simulated_surf_temp_in:.2f} °C (Air: 26.00 °C)")

        # Case 2: Insulated 4-Layer Wall with Convection
        print("\n" + "-" * 65)
        print("[Case 2] 4-Layer Insulated Composite Wall with Convection")
        print("-" * 65)

        config_insulated = ConvectionWallConfig(
            layers=[
                LayerSpec(name="Ext Plaster", thickness=0.020, thermal_conductivity=0.87),
                LayerSpec(name="Burnt Brick", thickness=0.200, thermal_conductivity=0.81),
                LayerSpec(name="EPS Insulation", thickness=0.050, thermal_conductivity=0.035),
                LayerSpec(name="Int Plaster", thickness=0.015, thermal_conductivity=0.72),
            ],
            outdoor_ambient_temp=42.0, indoor_ambient_temp=26.0,
            h_outdoor=20.0, h_indoor=7.7, mesh_size=0.005
        )

        res_insulated = run_convection_wall(
            config=config_insulated, existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_2_1_insulated_convection.png")
        )

        print(f"Total R-Value:           {res_insulated.r_total:.4f} m²·K/W (U = {res_insulated.u_value:.4f} W/m²·K)")
        print(f"Simulated Heat Flux:     {res_insulated.simulated_avg_heat_flux_x:.4f} W/m²")
        print(f"Theoretical Heat Flux:   {res_insulated.theoretical_heat_flux:.4f} W/m² (Error: {res_insulated.relative_error_percent:.5f}%)")
        print(f"Outdoor Surface Temp:    {res_insulated.simulated_surf_temp_out:.2f} °C")
        print(f"Indoor Surface Temp:     {res_insulated.simulated_surf_temp_in:.2f} °C")

    finally:
        print("\n[Step 3/3] Closing ANSYS MAPDL Solver...")
        mapdl.exit()
        print("ANSYS session safely closed.")


if __name__ == "__main__":
    main()
