"""
Phase 2 Stage 2.2 Execution Script.
Simulates Solar Radiation Heat Flux and Sol-Air Temperatures:
1. Standard Dark Roof / Wall (alpha = 0.85, I = 800 W/m²).
2. High-Albedo Cool Roof Coating (alpha = 0.20, I = 800 W/m²).
3. Insulated Roof with Cool Roof Coating.
Exports diagnostic figures to report/phase2/figures/.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ansys.mapdl.core import launch_mapdl
from phases.phase2.solar_radiation import SolarWallConfig, LayerSpec, run_solar_wall


def main():
    print("=" * 75)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 2 STAGE 2.2 SOLAR RADIATION")
    print("=" * 75)

    fig_dir = Path("report/phase2/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Step 1/3] Launching Shared ANSYS MAPDL Solver Instance...")
    mapdl = launch_mapdl(loglevel="WARNING", print_com=False)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    try:
        # =========================================================================
        # Case 1: Standard Dark Roof (alpha = 0.85, I = 800 W/m², Concrete/Brick)
        # =========================================================================
        print("\n" + "-" * 65)
        print("[Case 1] Standard Dark Exterior Surface (alpha = 0.85, I = 800 W/m²)")
        print("Conditions: T_inf,out = 42°C, T_inf,in = 26°C, h_out = 20 W/m²·K, h_in = 7.7 W/m²·K")
        print("-" * 65)

        config_dark = SolarWallConfig(
            layers=[LayerSpec(name="RCC Slab / Brick", thickness=0.150, thermal_conductivity=1.10)],
            solar_irradiance=800.0,
            absorptivity=0.85,
            outdoor_ambient_temp=42.0,
            indoor_ambient_temp=26.0,
            h_outdoor=20.0,
            h_indoor=7.7,
            mesh_size=0.005
        )

        res_dark = run_solar_wall(
            config=config_dark,
            existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_2_2_dark_surface_solar.png")
        )

        print(f"Absorbed Solar Radiation: {res_dark.absorbed_solar_flux:.1f} W/m²")
        print(f"Sol-Air Temperature:      {res_dark.sol_air_temperature:.2f} °C (Ambient Air: 42.00 °C, Solar Boost: +{res_dark.sol_air_temperature - 42.0:.2f} °C)")
        print(f"Simulated Heat Flux:      {res_dark.simulated_avg_heat_flux_x:.4f} W/m²")
        print(f"Theoretical Heat Flux:    {res_dark.theoretical_heat_flux:.4f} W/m² (Error: {res_dark.relative_error_percent:.5f}%)")
        print(f"Outdoor Surface Temp:     {res_dark.simulated_surf_temp_out:.2f} °C")
        print(f"Indoor Surface Temp:      {res_dark.simulated_surf_temp_in:.2f} °C")

        # =========================================================================
        # Case 2: High-Albedo Cool Roof Coating (alpha = 0.20, I = 800 W/m²)
        # =========================================================================
        print("\n" + "-" * 65)
        print("[Case 2] High-Albedo Cool Roof Coating (alpha = 0.20, I = 800 W/m²)")
        print("-" * 65)

        config_cool = SolarWallConfig(
            layers=[LayerSpec(name="RCC Slab / Brick", thickness=0.150, thermal_conductivity=1.10)],
            solar_irradiance=800.0,
            absorptivity=0.20, # Reflective white paint / high albedo
            outdoor_ambient_temp=42.0,
            indoor_ambient_temp=26.0,
            h_outdoor=20.0,
            h_indoor=7.7,
            mesh_size=0.005
        )

        res_cool = run_solar_wall(
            config=config_cool,
            existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_2_2_cool_roof_solar.png")
        )

        print(f"Absorbed Solar Radiation: {res_cool.absorbed_solar_flux:.1f} W/m²")
        print(f"Sol-Air Temperature:      {res_cool.sol_air_temperature:.2f} °C (Ambient Air: 42.00 °C, Solar Boost: +{res_cool.sol_air_temperature - 42.0:.2f} °C)")
        print(f"Simulated Heat Flux:      {res_cool.simulated_avg_heat_flux_x:.4f} W/m²")
        print(f"Theoretical Heat Flux:    {res_cool.theoretical_heat_flux:.4f} W/m² (Error: {res_cool.relative_error_percent:.5f}%)")
        print(f"Outdoor Surface Temp:     {res_cool.simulated_surf_temp_out:.2f} °C")
        print(f"Indoor Surface Temp:      {res_cool.simulated_surf_temp_in:.2f} °C")

        flux_saved = ((res_dark.simulated_avg_heat_flux_x - res_cool.simulated_avg_heat_flux_x) / res_dark.simulated_avg_heat_flux_x) * 100.0
        print(f"\n>> COOL ROOF BENEFIT: Heat ingress reduced from {res_dark.simulated_avg_heat_flux_x:.1f} W/m² to {res_cool.simulated_avg_heat_flux_x:.1f} W/m² (-{flux_saved:.1f}% reduction!)")
        print(f">> Outdoor Surface Temp reduced by: {res_dark.simulated_surf_temp_out - res_cool.simulated_surf_temp_out:.2f} °C")

        # =========================================================================
        # Case 3: Ultimate Passive Roof (Cool Coating + EPS Insulation + Concrete)
        # =========================================================================
        print("\n" + "-" * 65)
        print("[Case 3] Ultimate Passive Roof (Cool Coating + 50mm EPS + 150mm RCC)")
        print("-" * 65)

        config_passive = SolarWallConfig(
            layers=[
                LayerSpec(name="EPS Insulation", thickness=0.050, thermal_conductivity=0.035),
                LayerSpec(name="RCC Slab", thickness=0.150, thermal_conductivity=1.10),
                LayerSpec(name="Int Plaster", thickness=0.015, thermal_conductivity=0.72),
            ],
            solar_irradiance=800.0,
            absorptivity=0.20,
            outdoor_ambient_temp=42.0,
            indoor_ambient_temp=26.0,
            h_outdoor=20.0,
            h_indoor=7.7,
            mesh_size=0.005
        )

        res_passive = run_solar_wall(
            config=config_passive,
            existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_2_2_passive_insulated_roof.png")
        )

        print(f"Total R-Value:            {res_passive.r_total:.4f} m²·K/W (U = {res_passive.u_value:.4f} W/m²·K)")
        print(f"Simulated Heat Flux:      {res_passive.simulated_avg_heat_flux_x:.4f} W/m²")
        print(f"Outdoor Surface Temp:     {res_passive.simulated_surf_temp_out:.2f} °C")
        print(f"Indoor Surface Temp:      {res_passive.simulated_surf_temp_in:.2f} °C")

        total_savings = ((res_dark.simulated_avg_heat_flux_x - res_passive.simulated_avg_heat_flux_x) / res_dark.simulated_avg_heat_flux_x) * 100.0
        print(f">> COMBINED PASSIVE BENEFIT: Heat ingress reduced from {res_dark.simulated_avg_heat_flux_x:.1f} W/m² to {res_passive.simulated_avg_heat_flux_x:.1f} W/m² (-{total_savings:.1f}% reduction!)")

        print("\n" + "=" * 75)
        print("STAGE 2.2 SOLAR SIMULATIONS FINISHED SUCCESSFULLY!")
        print("=" * 75)

    finally:
        print("\n[Step 3/3] Closing ANSYS MAPDL Solver...")
        mapdl.exit()
        print("ANSYS session safely closed.")


if __name__ == "__main__":
    main()
