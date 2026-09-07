"""
Phase 2 Stage 2.3 Execution Script.
Simulates internal heat generation from occupants (100 W/person) and electronics:
1. Sealed Standard Brick Shelter (ACH = 0.5, 5 occupants = 600 W Heat).
2. Sealed Highly Insulated Shelter (Demonstrating the Insulation Heat-Trap Paradox).
3. Passive Cross-Ventilated Insulated Shelter (Night-Flush ACH = 6.0).
Exports diagnostic figures to report/phase2/figures/.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ansys.mapdl.core import launch_mapdl
from phases.phase2.internal_heat import ShelterRoomConfig, run_shelter_internal_heat


def main():
    print("=" * 75)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 2 STAGE 2.3 INTERNAL HEAT")
    print("=" * 75)

    fig_dir = Path("report/phase2/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Step 1/3] Launching Shared ANSYS MAPDL Solver Instance...")
    mapdl = launch_mapdl(loglevel="WARNING", print_com=False)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    try:
        # =========================================================================
        # Scenario A: Sealed Standard Brick Shelter (k = 0.80 W/m·K, ACH = 0.5)
        # =========================================================================
        print("\n" + "-" * 65)
        print("[Scenario A] Sealed Brick Shelter (5 Occupants + 100W Equip = 600W Heat)")
        print("Conditions: T_out = 38°C, Ground = 25°C, ACH = 0.5 (Sealed)")
        print("-" * 65)

        cfg_brick = ShelterRoomConfig(
            wall_conductivity=0.80,
            occupant_count=5,
            heat_per_occupant=100.0,
            equipment_heat=100.0,
            air_change_rate=0.5,
            outdoor_ambient_temp=38.0,
            ground_temp=25.0,
            mesh_size=0.06
        )

        res_brick = run_shelter_internal_heat(
            config=cfg_brick,
            existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_2_3_sealed_brick.png")
        )

        print(f"Total Room Heat:           {res_brick.total_room_internal_heat:.0f} W (Slice Heat = {res_brick.slice_internal_heat:.1f} W)")
        print(f"Average Indoor Temp:       {res_brick.avg_indoor_temp:.2f} °C (Outdoor: 38.00 °C)")
        print(f"Peak Indoor Air Temp:      {res_brick.peak_indoor_temp:.2f} °C")
        print(f"Indoor Overheating:        +{res_brick.indoor_overheating_delta:.2f} °C above ambient")
        print(f"Ventilation Heat Escape:   {res_brick.ventilation_heat_loss:.1f} W")
        print(f"Envelope Conduction Loss:  {res_brick.envelope_heat_loss:.1f} W")

        # =========================================================================
        # Scenario B: Sealed Insulated Shelter (k = 0.04 W/m·K, ACH = 0.5)
        # =========================================================================
        print("\n" + "-" * 65)
        print("[Scenario B] Sealed Insulated Shelter (The 'Insulation Trap' Paradox)")
        print("Thick insulation without ventilation traps occupant metabolic heat!")
        print("-" * 65)

        cfg_insulated_sealed = ShelterRoomConfig(
            wall_conductivity=0.04, # High insulation
            occupant_count=5,
            heat_per_occupant=100.0,
            equipment_heat=100.0,
            air_change_rate=0.5,    # Sealed
            outdoor_ambient_temp=38.0,
            ground_temp=25.0,
            mesh_size=0.06
        )

        res_insulated_sealed = run_shelter_internal_heat(
            config=cfg_insulated_sealed,
            existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_2_3_sealed_insulated.png")
        )

        print(f"Average Indoor Temp:       {res_insulated_sealed.avg_indoor_temp:.2f} °C")
        print(f"Peak Indoor Air Temp:      {res_insulated_sealed.peak_indoor_temp:.2f} °C")
        print(f"Indoor Overheating:        +{res_insulated_sealed.indoor_overheating_delta:.2f} °C above ambient!")
        print(f">> OBSERVATION: High insulation without ventilation causes internal heat accumulation (+{res_insulated_sealed.avg_indoor_temp - res_brick.avg_indoor_temp:.1f} °C hotter than brick!)")

        # =========================================================================
        # Scenario C: Passive Cross-Ventilated Insulated Shelter (ACH = 6.0)
        # =========================================================================
        print("\n" + "-" * 65)
        print("[Scenario C] Passive Cross-Ventilated Insulated Shelter (ACH = 6.0)")
        print("Combining thermal insulation with active/natural cross-ventilation")
        print("-" * 65)

        cfg_ventilated = ShelterRoomConfig(
            wall_conductivity=0.04,
            occupant_count=5,
            heat_per_occupant=100.0,
            equipment_heat=100.0,
            air_change_rate=6.0,    # Good cross-ventilation / night flush
            outdoor_ambient_temp=38.0,
            ground_temp=25.0,
            mesh_size=0.06
        )

        res_ventilated = run_shelter_internal_heat(
            config=cfg_ventilated,
            existing_mapdl=mapdl,
            save_plot_path=str(fig_dir / "stage_2_3_ventilated_insulated.png")
        )

        print(f"Average Indoor Temp:       {res_ventilated.avg_indoor_temp:.2f} °C")
        print(f"Peak Indoor Air Temp:      {res_ventilated.peak_indoor_temp:.2f} °C")
        print(f"Ventilation Heat Escape:   {res_ventilated.ventilation_heat_loss:.1f} W")
        print(f"Envelope Conduction Loss:  {res_ventilated.envelope_heat_loss:.1f} W")
        print(f">> VENTILATION BENEFIT: Slashed indoor temperature from {res_insulated_sealed.avg_indoor_temp:.1f} °C down to {res_ventilated.avg_indoor_temp:.1f} °C (-{res_insulated_sealed.avg_indoor_temp - res_ventilated.avg_indoor_temp:.1f} °C reduction!)")

        print("\n" + "=" * 75)
        print("STAGE 2.3 INTERNAL HEAT SIMULATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 75)

    finally:
        print("\n[Step 3/3] Closing ANSYS MAPDL Solver...")
        mapdl.exit()
        print("ANSYS session safely closed.")


if __name__ == "__main__":
    main()
