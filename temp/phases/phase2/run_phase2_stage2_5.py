"""
Phase 2 Stage 2.5 Runner Script.
Executes 3D Total Energy Balance and Heat Flow Rate Audit (Watts),
verifies the First Law of Thermodynamics, and generates 3D spatial energy maps with PyVista.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ansys.mapdl.core import launch_mapdl
from phases.phase2.heat_flow_3d import Shelter3DConfig
from phases.phase2.energy_audit_3d import compute_3d_energy_audit, render_3d_energy_diagrams


def main():
    print("=" * 80)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 2 STAGE 2.5 3D ENERGY AUDIT")
    print("=" * 80)

    fig_dir = Path("report/phase2/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Step 1/3] Launching Shared ANSYS MAPDL Solver Instance...")
    mapdl = launch_mapdl(loglevel="WARNING", print_com=False)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    try:
        # =========================================================================
        # Case 1: Standard 3D Shelter with Dark Roof (alpha = 0.85)
        # =========================================================================
        print("\n" + "-" * 70)
        print("[Case 1] 3D Energy Audit — Standard Dark Roof Shelter (alpha = 0.85)")
        print("-" * 70)

        config_dark = Shelter3DConfig(
            length=4.0, width=3.0, height=2.6, wall_thickness=0.25,
            envelope_conductivity=0.80, roof_absorptivity=0.85, wall_absorptivity=0.60,
            solar_flux_roof=600.0, solar_flux_south_wall=300.0, solar_flux_west_wall=250.0,
            outdoor_ambient_temp=38.0, ground_temp=24.0, occupant_heat_total=400.0, mesh_size=0.20
        )

        audit_dark = compute_3d_energy_audit(config=config_dark, existing_mapdl=mapdl)

        print("\n" + "=" * 60)
        print("3D SURFACE-BY-SURFACE THERMAL POWER LEDGER (WATTS):")
        print("=" * 60)
        for name, s in audit_dark.surfaces.items():
            dir_str = "INPUT " if s.is_input else "OUTPUT"
            pct = (s.heat_rate / audit_dark.total_energy_input) * 100.0 if s.is_input else 100.0
            print(f"  [{dir_str}] {name:25s}: Area = {s.area:4.1f} m² | Flux = {s.mean_flux:+6.1f} W/m² | Power = {s.heat_rate:+6.0f} W ({pct:4.1f}%)")

        print("-" * 60)
        print(f"Total External Heat Gain:      {audit_dark.total_heat_in:6.0f} W")
        print(f"Internal Occupant Generation:  {audit_dark.total_internal_gen:6.0f} W")
        print(f"TOTAL ENERGY INPUT (Q_in):     {audit_dark.total_energy_input:6.0f} W")
        print(f"TOTAL GROUND DISSIPATION:      {audit_dark.total_heat_out:6.0f} W")
        print(f"First Law Energy Residual:     {audit_dark.balance_residual_watts:6.1f} W (Error: {audit_dark.balance_error_percent:.2f}%)")
        print("=" * 60)

        print("\nRendering 3D Energy Audit Diagrams...")
        render_3d_energy_diagrams(audit_dark, save_prefix=str(fig_dir / "stage_2_5_dark_roof"))

        # =========================================================================
        # Case 2: Cool Roof Coated 3D Shelter (alpha = 0.20)
        # =========================================================================
        print("\n" + "-" * 70)
        print("[Case 2] 3D Energy Audit — Cool Roof Coated Shelter (alpha = 0.20)")
        print("-" * 70)

        config_cool = Shelter3DConfig(
            length=4.0, width=3.0, height=2.6, wall_thickness=0.25,
            envelope_conductivity=0.80, roof_absorptivity=0.20, wall_absorptivity=0.60,
            solar_flux_roof=600.0, solar_flux_south_wall=300.0, solar_flux_west_wall=250.0,
            outdoor_ambient_temp=38.0, ground_temp=24.0, occupant_heat_total=400.0, mesh_size=0.20
        )

        audit_cool = compute_3d_energy_audit(config=config_cool, existing_mapdl=mapdl)

        print(f"Dark Roof Thermal Power Ingress:  {audit_dark.surfaces['Roof (Solar + Air)'].heat_rate:.0f} W")
        print(f"Cool Roof Thermal Power Ingress:  {audit_cool.surfaces['Roof (Solar + Air)'].heat_rate:.0f} W")
        roof_power_saved = audit_dark.surfaces['Roof (Solar + Air)'].heat_rate - audit_cool.surfaces['Roof (Solar + Air)'].heat_rate
        print(f">> ROOF COOLING BENEFIT: Slashed roof thermal power by -{roof_power_saved:.0f} Watts (-{roof_power_saved / audit_dark.surfaces['Roof (Solar + Air)'].heat_rate * 100.0:.1f}%)!")

        print("\nRendering 3D Cool Roof Diagrams...")
        render_3d_energy_diagrams(audit_cool, save_prefix=str(fig_dir / "stage_2_5_cool_roof"))

        print("\n" + "=" * 80)
        print("PHASE 2 STAGE 2.5 TOTAL ENERGY AUDIT COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    finally:
        print("\n[Step 3/3] Closing ANSYS MAPDL Solver...")
        mapdl.exit()
        print("ANSYS session safely closed.")


if __name__ == "__main__":
    main()
