"""
Standalone ANSYS Simulation Verification Script
===============================================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System

Run with:
    uv run python run_simulation.py
"""

import sys
from pathlib import Path

# Ensure 'Ansys simulation' root is in sys.path
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from engine.schemas import (
    SimulationInput,
    ClimateInput,
    SiteInput,
    ShelterGeometry,
    EnvelopeAssembly,
    MaterialLayer,
    InternalLoads,
    VentilationInput,
    SimulationSettings,
    SimulationMode,
    SolverStatus,
)
from engine.physics_engine import run_simulation


def main():
    print("=" * 70)
    print("SIH 2026: Passive Thermal Shelter — ANSYS FEA Simulation Engine")
    print("=" * 70)

    # 1. Setup high-performance passive shelter input in Ladakh Winter
    climate = ClimateInput(
        ambient_temp_c=-18.2,
        solar_irradiance_peak_w_m2=720.0,
        wind_speed_m_s=14.5,
        diurnal_swing_c=12.0,
        zone_name="Ladakh (Cold & Sunny)"
    )

    shelter = ShelterGeometry(
        length_m=4.0,
        width_m=3.0,
        height_m=2.8,
        wall_thickness_m=0.25,
        roof_thickness_m=0.15,
        floor_thickness_m=0.20
    )

    materials = EnvelopeAssembly(
        wall_material=MaterialLayer("Rammed Earth Wall", conductivity_w_m_k=0.27, density_kg_m3=1994.0, specific_heat_j_kg_k=1000.0),
        roof_material=MaterialLayer("RCC Roof Slab", conductivity_w_m_k=1.10, density_kg_m3=2300.0, specific_heat_j_kg_k=1000.0),
        insulation_material=MaterialLayer("PU Foam Insulation", conductivity_w_m_k=0.033, density_kg_m3=45.0, specific_heat_j_kg_k=1450.0),
        insulation_thickness_wall_m=0.08,
        insulation_thickness_roof_m=0.08,
        has_pcm=True,
        pcm_thickness_m=0.03
    )

    loads = InternalLoads(occupant_count=4, sensible_heat_per_person_w=100.0, equipment_load_w=80.0)
    ventilation = VentilationInput(air_changes_per_hour=1.5)
    settings = SimulationSettings(mode=SimulationMode.STEADY_STATE, mesh_size_m=0.30, generate_vtk=False)

    sim_input = SimulationInput(
        climate=climate,
        shelter=shelter,
        materials=materials,
        site=SiteInput(ground_temp_c=-13.2, orientation_azimuth_deg=180.0),
        internal_loads=loads,
        ventilation=ventilation,
        settings=settings
    )

    print("\n[1/3] Validating physics input parameters...")
    valid, errors = sim_input.validate_all()
    if not valid:
        print(f"Validation failed: {errors}")
        return

    print("[2/3] Launching ANSYS Mechanical APDL (SOLID87 3D Continuum)...")
    result = run_simulation(sim_input)

    print("\n[3/3] Simulation Complete!")
    print("-" * 70)
    print(f"  Solver Status:             {result.status.value}")
    print(f"  Execution Time:            {result.execution_time_seconds:.2f} s")
    print(f"  Mean Indoor Temperature:   {result.mean_indoor_temp_c:.2f} °C")
    print(f"  Min Envelope Temperature:  {result.min_envelope_temp_c:.2f} °C")
    print(f"  Max Envelope Temperature:  {result.max_envelope_temp_c:.2f} °C")
    print(f"  Envelope Effective R-val:  {result.derived_physics.envelope_effective_r_m2_k_w:.3f} m²·K/W")
    print(f"  First Law Energy In:       {result.energy_balance.total_energy_input_watts:.1f} W")
    print(f"  First Law Energy Out:      {result.energy_balance.total_heat_out_watts:.1f} W")
    print(f"  First Law Residual:        {result.energy_balance.residual_watts:.2f} W ({result.energy_balance.balance_error_pct:.2f}% error)")
    print(f"  First Law Conserved?       {result.energy_balance.is_conserved}")
    print("-" * 70)


if __name__ == "__main__":
    main()
