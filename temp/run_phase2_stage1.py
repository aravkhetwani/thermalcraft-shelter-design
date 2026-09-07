"""
Phase 2 Stage 2.1 Execution Script.
Executes Convective (Robin) Boundary Condition simulations:
1. Bare Brick Wall under standard convection.
2. 4-Layer Insulated Wall under standard convection.
3. Wind speed sensitivity comparison (Calm vs High Wind).
Exports diagnostic figures to report/phase2/figures/.
"""

from pathlib import Path
from ansys.mapdl.core import launch_mapdl
from src.convection_wall import ConvectionWallConfig, LayerSpec, run_convection_wall


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
        # -------------------------------------------------------------
        # Case 1: Bare Brick Wall (250 mm, k = 0.80 W/m·K)
        # -------------------------------------------------------------
        print("\n" + "-" * 65)
        print("[Case 1] Bare Brick Wall with Convective Air Films")
        print("Conditions: T_inf,out = 42°C, T_inf,in = 26°C, h_out = 20 W/m²·K, h_in = 7.7 W/m²·K")
        print("-" * 65)

        config_brick = ConvectionWallConfig(
            layers=[LayerSpec(name="Burnt Brick", thickness=0.250, thermal_conductivity=0.80)],
            outdoor_ambient_temp=42.0,
            indoor_ambient_temp=26.0,
            h_outdoor=20.0,
            h_indoor=7.7,
            mesh_size=0.01
        )

        res_brick = run_convection_wall(
            config=config_brick,
            existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_2_1_brick_convection.png")
        )

        print(f"Total R-Value:           {res_brick.r_total:.4f} m²·K/W (R_out: {res_brick.r_film_out:.4f}, R_wall: {res_brick.r_wall:.4f}, R_in: {res_brick.r_film_in:.4f})")
        print(f"U-Value:                 {res_brick.u_value:.4f} W/m²·K")
        print(f"Simulated Heat Flux:     {res_brick.simulated_avg_heat_flux_x:.4f} W/m²")
        print(f"Theoretical Heat Flux:   {res_brick.theoretical_heat_flux:.4f} W/m² (Error: {res_brick.relative_error_percent:.5f}%)")
        print(f"Outdoor Surface Temp:    {res_brick.simulated_surf_temp_out:.2f} °C (Air: 42.00 °C, Film Drop: {42.0 - res_brick.simulated_surf_temp_out:.2f} °C)")
        print(f"Indoor Surface Temp:     {res_brick.simulated_surf_temp_in:.2f} °C (Air: 26.00 °C, Film Jump: {res_brick.simulated_surf_temp_in - 26.0:.2f} °C)")

        # -------------------------------------------------------------
        # Case 2: Insulated 4-Layer Wall with Convective Air Films
        # -------------------------------------------------------------
        print("\n" + "-" * 65)
        print("[Case 2] 4-Layer Insulated Composite Wall with Convection")
        print("Layers: Ext Plaster (20mm) -> Brick (200mm) -> EPS (50mm) -> Int Plaster (15mm)")
        print("-" * 65)

        config_insulated = ConvectionWallConfig(
            layers=[
                LayerSpec(name="Ext Plaster", thickness=0.020, thermal_conductivity=0.87),
                LayerSpec(name="Burnt Brick", thickness=0.200, thermal_conductivity=0.81),
                LayerSpec(name="EPS Insulation", thickness=0.050, thermal_conductivity=0.035),
                LayerSpec(name="Int Plaster", thickness=0.015, thermal_conductivity=0.72),
            ],
            outdoor_ambient_temp=42.0,
            indoor_ambient_temp=26.0,
            h_outdoor=20.0,
            h_indoor=7.7,
            mesh_size=0.005
        )

        res_insulated = run_convection_wall(
            config=config_insulated,
            existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_2_1_insulated_convection.png")
        )

        print(f"Total R-Value:           {res_insulated.r_total:.4f} m²·K/W (R_wall: {res_insulated.r_wall:.4f}, Films: {res_insulated.r_film_out + res_insulated.r_film_in:.4f})")
        print(f"U-Value:                 {res_insulated.u_value:.4f} W/m²·K")
        print(f"Simulated Heat Flux:     {res_insulated.simulated_avg_heat_flux_x:.4f} W/m²")
        print(f"Theoretical Heat Flux:   {res_insulated.theoretical_heat_flux:.4f} W/m² (Error: {res_insulated.relative_error_percent:.5f}%)")
        print(f"Outdoor Surface Temp:    {res_insulated.simulated_surf_temp_out:.2f} °C")
        print(f"Indoor Surface Temp:     {res_insulated.simulated_surf_temp_in:.2f} °C")

        # -------------------------------------------------------------
        # Case 3: Wind Sensitivity Study (Calm h=10 vs Storm h=50)
        # -------------------------------------------------------------
        print("\n" + "-" * 65)
        print("[Case 3] Wind Speed Sensitivity on Bare Brick Wall")
        print("-" * 65)

        config_calm = ConvectionWallConfig(
            layers=[LayerSpec(name="Burnt Brick", thickness=0.250, thermal_conductivity=0.80)],
            outdoor_ambient_temp=42.0, indoor_ambient_temp=26.0, h_outdoor=10.0, h_indoor=7.7
        )
        res_calm = run_convection_wall(config=config_calm, existing_mapdl=mapdl)

        config_storm = ConvectionWallConfig(
            layers=[LayerSpec(name="Burnt Brick", thickness=0.250, thermal_conductivity=0.80)],
            outdoor_ambient_temp=42.0, indoor_ambient_temp=26.0, h_outdoor=50.0, h_indoor=7.7
        )
        res_storm = run_convection_wall(config=config_storm, existing_mapdl=mapdl)

        print(f"Calm Wind  (h_out = 10 W/m²·K): Heat Flux = {res_calm.simulated_avg_heat_flux_x:.2f} W/m², T_surf,out = {res_calm.simulated_surf_temp_out:.2f} °C")
        print(f"Medium Wind(h_out = 20 W/m²·K): Heat Flux = {res_brick.simulated_avg_heat_flux_x:.2f} W/m², T_surf,out = {res_brick.simulated_surf_temp_out:.2f} °C")
        print(f"Storm Wind (h_out = 50 W/m²·K): Heat Flux = {res_storm.simulated_avg_heat_flux_x:.2f} W/m², T_surf,out = {res_storm.simulated_surf_temp_out:.2f} °C")

        flux_increase = ((res_storm.simulated_avg_heat_flux_x - res_calm.simulated_avg_heat_flux_x) / res_calm.simulated_avg_heat_flux_x) * 100.0
        print(f"Wind Speed Increase Effect: Heat ingress increased by +{flux_increase:.1f}%")

        print("\n" + "=" * 75)
        print("STAGE 2.1 CONVECTION SIMULATIONS FINISHED SUCCESSFULLY!")
        print("=" * 75)

    finally:
        print("\n[Step 3/3] Closing ANSYS MAPDL Solver...")
        mapdl.exit()
        print("ANSYS session safely closed.")


if __name__ == "__main__":
    main()
