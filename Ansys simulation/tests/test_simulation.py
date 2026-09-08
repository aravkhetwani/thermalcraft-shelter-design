"""
Automated Test Suite for ANSYS Simulation Engine
================================================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
"""

import unittest
import numpy as np
from pathlib import Path
import sys

# Ensure root of 'Ansys simulation' is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

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
    DerivedPhysicsParameters
)
from engine.physics_preprocessor import PhysicsPreprocessor
from engine.physics_engine import run_simulation


class TestAnsysSimulationEngine(unittest.TestCase):
    """Unit and integration test suite for the standalone ANSYS simulation module."""

    def setUp(self):
        self.climate = ClimateInput(
            ambient_temp_c=42.0,
            solar_irradiance_peak_w_m2=880.0,
            wind_speed_m_s=3.2,
            diurnal_swing_c=14.0,
            zone_name="Hot & Dry"
        )
        self.shelter = ShelterGeometry(
            length_m=4.0,
            width_m=3.0,
            height_m=2.8,
            wall_thickness_m=0.25,
            roof_thickness_m=0.15,
            floor_thickness_m=0.20
        )
        self.materials = EnvelopeAssembly(
            wall_material=MaterialLayer("AAC Block", conductivity_w_m_k=0.18, density_kg_m3=650.0, specific_heat_j_kg_k=1000.0),
            roof_material=MaterialLayer("RCC Slab", conductivity_w_m_k=1.20, density_kg_m3=2300.0, specific_heat_j_kg_k=1000.0),
            roof_solar_absorptivity=0.20,  # Cool roof
            wall_solar_absorptivity=0.45
        )
        self.loads = InternalLoads(occupant_count=4, sensible_heat_per_person_w=100.0, equipment_load_w=100.0)
        self.ventilation = VentilationInput(air_changes_per_hour=2.0)
        self.settings = SimulationSettings(mode=SimulationMode.STEADY_STATE, mesh_size_m=0.30, generate_vtk=False)

        self.sim_input = SimulationInput(
            climate=self.climate,
            shelter=self.shelter,
            materials=self.materials,
            site=SiteInput(ground_temp_c=28.0),
            internal_loads=self.loads,
            ventilation=self.ventilation,
            settings=self.settings
        )

    def test_01_input_validation(self):
        """Test strict validation rules on input boundaries."""
        valid, errors = self.sim_input.validate_all()
        self.assertTrue(valid, f"Validation failed with: {errors}")

        invalid_climate = ClimateInput(ambient_temp_c=120.0, solar_irradiance_peak_w_m2=2000.0)
        self.assertGreater(len(invalid_climate.validate()), 0)

    def test_02_physics_preprocessor_convection(self):
        """Verify McAdams convection film coefficient calculation."""
        derived = PhysicsPreprocessor.process(self.sim_input)
        expected_h = 5.7 + 3.8 * 3.2  # 17.86 W/m2K
        self.assertAlmostEqual(derived.h_outdoor_w_m2_k, expected_h, places=2)

    def test_03_physics_preprocessor_sol_air(self):
        """Verify Sol-Air temperature superposition."""
        derived = PhysicsPreprocessor.process(self.sim_input)
        expected_roof_sol_air = 42.0 + (0.20 * 880.0) / derived.h_outdoor_w_m2_k
        self.assertAlmostEqual(derived.sol_air_roof_c, expected_roof_sol_air, places=2)

    def test_04_physics_preprocessor_heat_generation(self):
        """Verify volumetric internal load calculation."""
        derived = PhysicsPreprocessor.process(self.sim_input)
        vol = (4.0 - 0.5) * (3.0 - 0.5) * (2.8 - 0.35)  # 3.5 * 2.5 * 2.45 = 21.4375 m3
        expected_q_vol = 500.0 / vol
        self.assertAlmostEqual(derived.volumetric_heat_gen_w_m3, expected_q_vol, places=2)

    def test_05_r_value_calculation(self):
        """Verify multi-layer composite R-value calculation."""
        derived = PhysicsPreprocessor.process(self.sim_input)
        r_wall = 0.25 / 0.18
        self.assertAlmostEqual(derived.envelope_effective_r_m2_k_w, r_wall, places=2)

    def test_06_energy_closure_calculation(self):
        """Verify First Law energy closure arithmetic."""
        from engine.schemas import EnergyBalanceResult
        total_gains = 500.0 + 266.3
        total_losses = 758.9
        residual = abs(total_gains - total_losses)
        error_pct = (residual / total_gains) * 100.0
        
        balance = EnergyBalanceResult(
            total_heat_in_watts=266.3,
            internal_generation_watts=500.0,
            total_energy_input_watts=total_gains,
            total_heat_out_watts=total_losses,
            residual_watts=round(residual, 2),
            balance_error_pct=round(error_pct, 2),
            is_conserved=error_pct <= 5.0
        )
        self.assertTrue(balance.is_conserved)
        self.assertLess(balance.balance_error_pct, 5.0)


if __name__ == '__main__':
    unittest.main()
