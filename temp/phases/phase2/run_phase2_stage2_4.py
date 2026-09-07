"""
Phase 2 Stage 2.4 Runner Script.
Executes full 3D ANSYS Thermal Simulations with SOLID70 elements,
extracts 3D spatial heat-flux vectors (TFX, TFY, TFZ),
and generates 3D vector glyphs, cutaway sections, and slice planes with PyVista.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ansys.mapdl.core import launch_mapdl
from phases.phase2.heat_flow_3d import (
    Shelter3DConfig,
    run_3d_shelter_simulation,
    render_3d_heat_flow_views
)


def main():
    print("=" * 80)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 2 STAGE 2.4 3D HEAT FLOW")
    print("=" * 80)

    fig_dir = Path("report/phase2/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Step 1/3] Launching Shared ANSYS MAPDL Solver Instance (3D SOLID70)...")
    mapdl = launch_mapdl(loglevel="WARNING", print_com=False)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    try:
        # =========================================================================
        # Case 1: Standard 3D Shelter with Dark Roof (alpha = 0.85, Solar = 600 W/m²)
        # =========================================================================
        print("\n" + "-" * 70)
        print("[Case 1] 3D Shelter Simulation — Standard Dark Roof (alpha = 0.85)")
        print("Solar Load: Roof = 600 W/m², South Wall = 300 W/m², West Wall = 250 W/m²")
        print("-" * 70)

        config_dark = Shelter3DConfig(
            length=4.0, width=3.0, height=2.6,
            wall_thickness=0.25,
            envelope_conductivity=0.80, # Brick masonry
            roof_absorptivity=0.85,
            wall_absorptivity=0.60,
            solar_flux_roof=600.0,
            solar_flux_south_wall=300.0,
            solar_flux_west_wall=250.0,
            outdoor_ambient_temp=38.0,
            ground_temp=24.0,
            occupant_heat_total=400.0,
            mesh_size=0.15
        )

        res_dark = run_3d_shelter_simulation(config=config_dark, existing_mapdl=mapdl)

        print(f"3D Mesh Elements:        {res_dark.grid.n_cells}")
        print(f"3D Mesh Nodes:           {res_dark.grid.n_points}")
        print(f"Roof Sol-Air Temp:       {res_dark.sol_air_roof:.2f} °C (Ambient: 38.00 °C)")
        print(f"South Wall Sol-Air:      {res_dark.sol_air_south:.2f} °C")
        print(f"West Wall Sol-Air:       {res_dark.sol_air_west:.2f} °C")
        print(f"Temperature Range:       {res_dark.min_temp:.2f} °C to {res_dark.max_temp:.2f} °C")
        print(f"Average Indoor Room T:   {res_dark.avg_indoor_temp:.2f} °C")
        print(f"Peak Heat Flux Vector:   {res_dark.peak_flux_mag:.2f} W/m²")
        print(f"Average Heat Flux Mag:   {res_dark.avg_flux_mag:.2f} W/m²")

        print("\nRendering 3D Vector Glyphs & Cutaways with PyVista...")
        render_3d_heat_flow_views(
            res_dark,
            save_prefix=str(fig_dir / "stage_2_4_dark_roof")
        )

        # =========================================================================
        # Case 2: 3D Shelter with High-Albedo Cool Roof Coating (alpha = 0.20)
        # =========================================================================
        print("\n" + "-" * 70)
        print("[Case 2] 3D Shelter Simulation — High-Albedo Cool Roof (alpha = 0.20)")
        print("-" * 70)

        config_cool = Shelter3DConfig(
            length=4.0, width=3.0, height=2.6,
            wall_thickness=0.25,
            envelope_conductivity=0.80,
            roof_absorptivity=0.20, # Cool Roof
            wall_absorptivity=0.60,
            solar_flux_roof=600.0,
            solar_flux_south_wall=300.0,
            solar_flux_west_wall=250.0,
            outdoor_ambient_temp=38.0,
            ground_temp=24.0,
            occupant_heat_total=400.0,
            mesh_size=0.15
        )

        res_cool = run_3d_shelter_simulation(config=config_cool, existing_mapdl=mapdl)

        print(f"Roof Sol-Air Temp:       {res_cool.sol_air_roof:.2f} °C (-{res_dark.sol_air_roof - res_cool.sol_air_roof:.1f} °C reduction!)")
        print(f"Temperature Range:       {res_cool.min_temp:.2f} °C to {res_cool.max_temp:.2f} °C")
        print(f"Average Indoor Room T:   {res_cool.avg_indoor_temp:.2f} °C (-{res_dark.avg_indoor_temp - res_cool.avg_indoor_temp:.1f} °C cooler)")
        print(f"Peak Heat Flux Vector:   {res_cool.peak_flux_mag:.2f} W/m² (-{res_dark.peak_flux_mag - res_cool.peak_flux_mag:.1f} W/m² drop)")

        print("\nRendering 3D Cool Roof Views with PyVista...")
        render_3d_heat_flow_views(
            res_cool,
            save_prefix=str(fig_dir / "stage_2_4_cool_roof")
        )

        print("\n" + "=" * 80)
        print("STAGE 2.4 3D HEAT FLOW SIMULATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    finally:
        print("\n[Step 3/3] Closing ANSYS MAPDL Solver...")
        mapdl.exit()
        print("ANSYS session safely closed.")


if __name__ == "__main__":
    main()
