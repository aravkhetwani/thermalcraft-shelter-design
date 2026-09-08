"""
Phase 7: ANSYS Physics Simulation Engine
========================================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System

Unified facade and entrypoint for the complete Phase 7 Physics Engine:
    run_simulation(input_data: SimulationInput) -> SimulationResult

Coordinates:
    Input Validation
          ↓
    Physics Preprocessing (Sol-Air, Convection, Heat Generation)
          ↓
    ANSYS MAPDL Model Construction (SOLID87 7-Block Conformal Geometry)
          ↓
    Material Assignment & Finite Element Meshing
          ↓
    Thermal Boundary Conditions (Robin Convection, Sol-Air, Internal Load, Ground)
          ↓
    FEA Solution Execution (/SOLU)
          ↓
    Vectorized Result Extraction & 3D Spatial Field Assembly
          ↓
    First Law of Thermodynamics Energy Balance Auditing
          ↓
    Structured SimulationResult Return
"""

import time
from typing import Optional
from ansys.mapdl.core import Mapdl
from .schemas import (
    SimulationInput,
    SimulationResult,
    SolverStatus,
    DerivedPhysicsParameters,
    EnergyBalanceResult
)
from .physics_preprocessor import PhysicsPreprocessor
from .ansys_session import AnsysSessionManager
from .geometry_engine import GeometryEngine
from .material_manager import MaterialManager
from .boundary_conditions import BoundaryConditionsManager
from .solver_pipeline import SolverPipeline
from .result_extractor import ResultExtractor


class SimulationEngine:
    """Master ANSYS thermal physics execution engine."""

    @classmethod
    def execute(
        cls,
        sim_input: SimulationInput,
        existing_mapdl: Optional[Mapdl] = None,
        vtk_output_path: Optional[str] = None
    ) -> SimulationResult:
        """Executes full end-to-end thermal FEA simulation and returns structured physical results."""
        t_start = time.perf_counter()
        warnings = []

        # 1. Step 1: Input Validation
        is_valid, validation_errors = sim_input.validate_all()
        if not is_valid:
            return SimulationResult(
                status=SolverStatus.VALIDATION_ERROR,
                execution_time_seconds=time.perf_counter() - t_start,
                min_envelope_temp_c=0.0,
                max_envelope_temp_c=0.0,
                mean_indoor_temp_c=0.0,
                derived_physics=PhysicsPreprocessor.process(sim_input),
                surfaces={},
                energy_balance=EnergyBalanceResult(0, 0, 0, 0, 0, 0, False),
                error_message="; ".join(validation_errors)
            )

        # 2. Step 2: Physics Preprocessing
        derived = PhysicsPreprocessor.process(sim_input)

        # 3. Step 3: ANSYS Execution Pipeline
        try:
            with AnsysSessionManager.get_session(
                existing_mapdl=existing_mapdl,
                loglevel=sim_input.settings.log_level
            ) as mapdl:

                # Geometry Construction (SOLID87 7-Block Conformal Geometry)
                GeometryEngine.build_shelter_geometry(mapdl, sim_input.shelter)

                # Thermal Material Attribution
                MaterialManager.apply_materials(mapdl, sim_input.materials, derived)

                # Finite Element Meshing (SOLID87)
                SolverPipeline.setup_elements_and_mesh(mapdl, sim_input.settings)

                # Thermal Boundary Conditions (Robin convection, Sol-Air, Internal Load, Ground)
                BoundaryConditionsManager.apply_steady_state_bcs(mapdl, sim_input.shelter, derived)

                # FEA Solution Execution
                solver_status = SolverPipeline.solve(mapdl, sim_input.settings)
                if solver_status != SolverStatus.SUCCESS:
                    return SimulationResult(
                        status=solver_status,
                        execution_time_seconds=time.perf_counter() - t_start,
                        min_envelope_temp_c=0.0,
                        max_envelope_temp_c=0.0,
                        mean_indoor_temp_c=0.0,
                        derived_physics=derived,
                        surfaces={},
                        energy_balance=EnergyBalanceResult(0, 0, 0, 0, 0, 0, False),
                        error_message="ANSYS solver failed to converge."
                    )

                # Result Extraction & Energy Balance Auditing
                min_t, max_t, indoor_t, surfaces, energy_bal, spatial_3d = (
                    ResultExtractor.extract_steady_state_results(
                        mapdl=mapdl,
                        geom=sim_input.shelter,
                        loads=sim_input.internal_loads,
                        derived=derived,
                        vtk_output_path=vtk_output_path
                    )
                )

                if not energy_bal.is_conserved:
                    warnings.append(
                        f"First Law energy balance residual ({energy_bal.balance_error_pct:.2f}%) exceeds 5% numerical tolerance."
                    )

                t_exec = time.perf_counter() - t_start

                return SimulationResult(
                    status=SolverStatus.SUCCESS,
                    execution_time_seconds=round(t_exec, 3),
                    min_envelope_temp_c=round(min_t, 2),
                    max_envelope_temp_c=round(max_t, 2),
                    mean_indoor_temp_c=round(indoor_t, 2),
                    derived_physics=derived,
                    surfaces=surfaces,
                    energy_balance=energy_bal,
                    spatial_3d=spatial_3d,
                    warnings=warnings
                )

        except Exception as e:
            return SimulationResult(
                status=SolverStatus.CONVERGENCE_ERROR,
                execution_time_seconds=time.perf_counter() - t_start,
                min_envelope_temp_c=0.0,
                max_envelope_temp_c=0.0,
                mean_indoor_temp_c=0.0,
                derived_physics=derived,
                surfaces={},
                energy_balance=EnergyBalanceResult(0, 0, 0, 0, 0, 0, False),
                error_message=str(e)
            )


def run_simulation(
    input_data: SimulationInput,
    existing_mapdl: Optional[Mapdl] = None,
    vtk_output_path: Optional[str] = None
) -> SimulationResult:
    """Convenience public API function to execute a Phase 7 simulation."""
    return SimulationEngine.execute(
        sim_input=input_data,
        existing_mapdl=existing_mapdl,
        vtk_output_path=vtk_output_path
    )
