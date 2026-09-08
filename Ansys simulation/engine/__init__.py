"""
ANSYS Simulation Module / Physics Engine Package
================================================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
"""

from .schemas import (
    SimulationMode,
    SolverStatus,
    ClimateInput,
    SiteInput,
    ShelterGeometry,
    MaterialLayer,
    EnvelopeAssembly,
    InternalLoads,
    VentilationInput,
    SimulationSettings,
    SimulationInput,
    SurfaceHeatRate,
    EnergyBalanceResult,
    SpatialField3D,
    TransientHistory,
    SimulationResult,
    DerivedPhysicsParameters
)

from .physics_preprocessor import PhysicsPreprocessor
from .ansys_session import AnsysSessionManager
from .geometry_engine import GeometryEngine
from .material_manager import MaterialManager
from .boundary_conditions import BoundaryConditionsManager
from .solver_pipeline import SolverPipeline
from .result_extractor import ResultExtractor
from .physics_engine import SimulationEngine, run_simulation

__all__ = [
    "SimulationMode",
    "SolverStatus",
    "ClimateInput",
    "SiteInput",
    "ShelterGeometry",
    "MaterialLayer",
    "EnvelopeAssembly",
    "InternalLoads",
    "VentilationInput",
    "SimulationSettings",
    "SimulationInput",
    "SurfaceHeatRate",
    "EnergyBalanceResult",
    "SpatialField3D",
    "TransientHistory",
    "SimulationResult",
    "DerivedPhysicsParameters",
    "PhysicsPreprocessor",
    "AnsysSessionManager",
    "GeometryEngine",
    "MaterialManager",
    "BoundaryConditionsManager",
    "SolverPipeline",
    "ResultExtractor",
    "SimulationEngine",
    "run_simulation"
]
