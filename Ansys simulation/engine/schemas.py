"""
Phase 7: Schemas and Typed Contracts for ANSYS Physics Engine
==============================================================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System

Defines strictly validated data contracts for:
1. User / Dashboard Inputs (Climate, Site, Shelter Geometry, Materials, Loads, Ventilation)
2. Derived Physical Parameters (Sol-Air temperatures, convection film coefficients, volumetric heat)
3. Internal Numerical Configuration (Meshing, Solver settings)
4. Structured Physical Simulation Results (Temperatures, Heat Rates in Watts, Energy Balance, 3D Fields)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class SimulationMode(str, Enum):
    """Supported physical simulation analysis types."""
    STEADY_STATE = "STEADY_STATE"
    TRANSIENT_24H = "TRANSIENT_24H"
    PCM_LATENT = "PCM_LATENT"


class SolverStatus(str, Enum):
    """Status of the ANSYS MAPDL solver execution."""
    SUCCESS = "SUCCESS"
    CONVERGENCE_ERROR = "CONVERGENCE_ERROR"
    MESH_ERROR = "MESH_ERROR"
    LICENSE_ERROR = "LICENSE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


# =============================================================================
# 1. INPUT CONTRACTS
# =============================================================================

@dataclass
class ClimateInput:
    """External climate & environmental boundary parameters."""
    ambient_temp_c: float                # Outdoor shade ambient temperature [°C]
    solar_irradiance_peak_w_m2: float    # Peak global horizontal irradiance (GHI) [W/m²]
    wind_speed_m_s: float = 2.5          # Average ambient wind velocity [m/s]
    relative_humidity_pct: float = 40.0  # Ambient relative humidity [%]
    diurnal_swing_c: float = 12.0        # Day/night temperature amplitude [°C]
    zone_name: str = "custom"            # Indian climate zone identifier

    def validate(self) -> List[str]:
        errors = []
        if not (-40.0 <= self.ambient_temp_c <= 65.0):
            errors.append(f"ambient_temp_c={self.ambient_temp_c} is outside physical range [-40, 65] °C")
        if not (0.0 <= self.solar_irradiance_peak_w_m2 <= 1400.0):
            errors.append(f"solar_irradiance_peak_w_m2={self.solar_irradiance_peak_w_m2} is outside [0, 1400] W/m²")
        if not (0.0 <= self.wind_speed_m_s <= 50.0):
            errors.append(f"wind_speed_m_s={self.wind_speed_m_s} is outside [0, 50] m/s")
        if not (0.0 <= self.relative_humidity_pct <= 100.0):
            errors.append(f"relative_humidity_pct={self.relative_humidity_pct} is outside [0, 100] %")
        return errors


@dataclass
class SiteInput:
    """Geographical and ground boundary parameters."""
    ground_temp_c: float = 24.0          # Deep ground contact temperature [°C]
    orientation_azimuth_deg: float = 0.0 # Orientation (0° = North, 90° = East, 180° = South)
    elevation_m: float = 250.0           # Site altitude above sea level [m]

    def validate(self) -> List[str]:
        errors = []
        if not (-20.0 <= self.ground_temp_c <= 45.0):
            errors.append(f"ground_temp_c={self.ground_temp_c} is outside physical range [-20, 45] °C")
        if not (0.0 <= self.orientation_azimuth_deg <= 360.0):
            errors.append(f"orientation_azimuth_deg={self.orientation_azimuth_deg} is outside [0, 360] deg")
        return errors


@dataclass
class ShelterGeometry:
    """3D envelope dimensional geometry."""
    length_m: float = 4.0                # Outer length in X direction [m]
    width_m: float = 3.0                 # Outer width in Y direction [m]
    height_m: float = 2.8                # Outer height in Z direction [m]
    wall_thickness_m: float = 0.25       # Exterior wall thickness [m]
    roof_thickness_m: float = 0.15       # Roof slab thickness [m]
    floor_thickness_m: float = 0.20      # Foundation slab thickness [m]
    window_to_wall_ratio: float = 0.15   # Glazing fraction [0.0 - 0.50]
    overhang_depth_m: float = 0.40       # Shading overhang depth [m]

    def validate(self) -> List[str]:
        errors = []
        if self.length_m <= 0.5:
            errors.append(f"length_m={self.length_m} must be > 0.5 m")
        if self.width_m <= 0.5:
            errors.append(f"width_m={self.width_m} must be > 0.5 m")
        if self.height_m <= 1.0:
            errors.append(f"height_m={self.height_m} must be > 1.0 m")
        if self.wall_thickness_m <= 0.02 or self.wall_thickness_m >= min(self.length_m, self.width_m) / 2.0:
            errors.append(f"wall_thickness_m={self.wall_thickness_m} is invalid for given shelter dimensions")
        if self.roof_thickness_m <= 0.02 or self.roof_thickness_m >= self.height_m / 2.0:
            errors.append(f"roof_thickness_m={self.roof_thickness_m} is invalid")
        if not (0.0 <= self.window_to_wall_ratio <= 0.70):
            errors.append(f"window_to_wall_ratio={self.window_to_wall_ratio} must be between 0.0 and 0.70")
        return errors


@dataclass
class MaterialLayer:
    """Single physical material layer definition."""
    name: str
    conductivity_w_m_k: float            # Thermal conductivity k [W/(m·K)]
    density_kg_m3: float = 1800.0        # Density ρ [kg/m³]
    specific_heat_j_kg_k: float = 900.0  # Specific heat capacity Cp [J/(kg·K)]
    thickness_m: float = 0.20            # Layer thickness [m]

    def validate(self) -> List[str]:
        errors = []
        if self.conductivity_w_m_k <= 0.0:
            errors.append(f"Material '{self.name}' conductivity must be > 0, got {self.conductivity_w_m_k}")
        if self.density_kg_m3 <= 0.0:
            errors.append(f"Material '{self.name}' density must be > 0, got {self.density_kg_m3}")
        if self.specific_heat_j_kg_k <= 0.0:
            errors.append(f"Material '{self.name}' specific heat must be > 0, got {self.specific_heat_j_kg_k}")
        return errors


@dataclass
class EnvelopeAssembly:
    """Envelope material properties, coatings and composite layers."""
    wall_material: MaterialLayer = field(
        default_factory=lambda: MaterialLayer("Burnt Clay Brick", conductivity_w_m_k=0.80, density_kg_m3=1800.0, specific_heat_j_kg_k=840.0)
    )
    roof_material: MaterialLayer = field(
        default_factory=lambda: MaterialLayer("RCC Concrete Slab", conductivity_w_m_k=1.20, density_kg_m3=2300.0, specific_heat_j_kg_k=1000.0)
    )
    insulation_material: Optional[MaterialLayer] = None
    insulation_thickness_wall_m: float = 0.0 # Wall insulation thickness [m]
    insulation_thickness_roof_m: float = 0.0 # Roof insulation thickness [m]
    roof_solar_absorptivity: float = 0.85    # External roof absorptance (0.85 dark, 0.20 cool roof)
    wall_solar_absorptivity: float = 0.60    # External wall absorptance
    thermal_emissivity: float = 0.90         # Longwave emissivity
    has_pcm: bool = False                    # Phase Change Material presence
    pcm_melt_temp_c: float = 25.0            # PCM melting temperature [°C]
    pcm_latent_heat_j_kg: float = 210000.0   # PCM latent heat of fusion [J/kg]
    pcm_thickness_m: float = 0.02            # PCM layer thickness [m]

    def validate(self) -> List[str]:
        errors = []
        errors.extend(self.wall_material.validate())
        errors.extend(self.roof_material.validate())
        if self.insulation_material:
            errors.extend(self.insulation_material.validate())
        if not (0.0 <= self.roof_solar_absorptivity <= 1.0):
            errors.append(f"roof_solar_absorptivity={self.roof_solar_absorptivity} must be in [0, 1]")
        if not (0.0 <= self.wall_solar_absorptivity <= 1.0):
            errors.append(f"wall_solar_absorptivity={self.wall_solar_absorptivity} must be in [0, 1]")
        if not (0.0 <= self.thermal_emissivity <= 1.0):
            errors.append(f"thermal_emissivity={self.thermal_emissivity} must be in [0, 1]")
        return errors


@dataclass
class InternalLoads:
    """Internal heat sources inside the shelter."""
    occupant_count: int = 4              # Number of occupants
    sensible_heat_per_person_w: float = 100.0 # Sensible metabolic heat [W/person]
    equipment_load_w: float = 100.0      # Lighting, electronics, appliances [W]
    schedule_fraction: float = 1.0       # Occupancy fraction [0.0 - 1.0]

    @property
    def total_heat_watts(self) -> float:
        return (self.occupant_count * self.sensible_heat_per_person_w + self.equipment_load_w) * self.schedule_fraction

    def validate(self) -> List[str]:
        errors = []
        if self.occupant_count < 0:
            errors.append(f"occupant_count={self.occupant_count} cannot be negative")
        if self.sensible_heat_per_person_w < 0.0:
            errors.append("sensible_heat_per_person_w cannot be negative")
        if self.equipment_load_w < 0.0:
            errors.append("equipment_load_w cannot be negative")
        if not (0.0 <= self.schedule_fraction <= 1.0):
            errors.append("schedule_fraction must be in [0, 1]")
        return errors


@dataclass
class VentilationInput:
    """Natural & mechanical ventilation configuration."""
    air_changes_per_hour: float = 2.0    # ACH [1/h]
    night_flushing_enabled: bool = False # Diurnal night convective flushing
    night_flushing_ach: float = 6.0      # Enhanced night ACH [1/h]
    inlet_temperature_c: Optional[float] = None # Optional EAHE/precooling inlet [°C]

    def validate(self) -> List[str]:
        errors = []
        if self.air_changes_per_hour < 0.0:
            errors.append("air_changes_per_hour cannot be negative")
        if self.night_flushing_ach < 0.0:
            errors.append("night_flushing_ach cannot be negative")
        return errors


@dataclass
class SimulationSettings:
    """ANSYS MAPDL numerical solver configuration."""
    mode: SimulationMode = SimulationMode.STEADY_STATE
    mesh_size_m: float = 0.25            # Element size in meters
    element_type: str = "SOLID87"        # 10-node 3D tetrahedral thermal solid element
    time_step_hours: float = 1.0         # Time step for transient runs [hours]
    total_duration_hours: float = 24.0   # Transient duration [hours]
    solver_timeout_seconds: float = 180.0# Max execution time before abort [s]
    generate_vtk: bool = True            # Whether to compile PyVista 3D grid
    log_level: str = "WARNING"           # ANSYS log output verbosity

    def validate(self) -> List[str]:
        errors = []
        if self.mesh_size_m <= 0.01:
            errors.append(f"mesh_size_m={self.mesh_size_m} is too small (< 0.01 m)")
        if self.element_type not in ["SOLID87", "PLANE77"]:
            errors.append(f"element_type='{self.element_type}' must be SOLID87 or PLANE77")
        return errors


@dataclass
class SimulationInput:
    """Root container for all validated inputs passed to Phase 7 Physics Engine."""
    climate: ClimateInput
    shelter: ShelterGeometry
    materials: EnvelopeAssembly = field(default_factory=EnvelopeAssembly)
    site: SiteInput = field(default_factory=SiteInput)
    internal_loads: InternalLoads = field(default_factory=InternalLoads)
    ventilation: VentilationInput = field(default_factory=VentilationInput)
    settings: SimulationSettings = field(default_factory=SimulationSettings)

    def validate_all(self) -> Tuple[bool, List[str]]:
        """Performs comprehensive validation across all input categories."""
        all_errors = []
        all_errors.extend(self.climate.validate())
        all_errors.extend(self.shelter.validate())
        all_errors.extend(self.materials.validate())
        all_errors.extend(self.site.validate())
        all_errors.extend(self.internal_loads.validate())
        all_errors.extend(self.ventilation.validate())
        all_errors.extend(self.settings.validate())
        return len(all_errors) == 0, all_errors


# =============================================================================
# 2. DERIVED PHYSICS INTERMEDIATE CONTRACT
# =============================================================================

@dataclass
class DerivedPhysicsParameters:
    """Parameters derived internally by the Physics Preprocessor for ANSYS."""
    h_outdoor_w_m2_k: float              # External Robin convection film coefficient [W/m²·K]
    h_indoor_w_m2_k: float               # Internal natural convection film coefficient [W/m²·K]
    sol_air_roof_c: float                # Sol-Air boundary temperature for roof [°C]
    sol_air_south_c: float               # Sol-Air boundary temperature for south wall [°C]
    sol_air_west_c: float                # Sol-Air boundary temperature for west wall [°C]
    sol_air_north_c: float               # Sol-Air boundary temperature for north wall [°C]
    sol_air_east_c: float                # Sol-Air boundary temperature for east wall [°C]
    ground_boundary_temp_c: float        # Foundation slab boundary temperature [°C]
    room_air_volume_m3: float            # Internal usable air volume [m³]
    volumetric_heat_gen_w_m3: float      # Core volumetric heat generation [W/m³]
    envelope_effective_k_w_m_k: float    # Combined equivalent envelope conductivity [W/(m·K)]
    envelope_effective_r_m2_k_w: float   # Combined thermal resistance R [m²·K/W]
    ventilation_heat_removal_w_per_k: float # Convective heat removal capacity [W/K]


# =============================================================================
# 3. OUTPUT CONTRACTS
# =============================================================================

@dataclass
class SurfaceHeatRate:
    """Detailed heat flow rate for an individual 3D boundary surface."""
    name: str                            # Surface descriptor (e.g. "Roof (Solar + Air)")
    area_m2: float                       # Surface surface area [m²]
    mean_flux_w_m2: float                # Surface-averaged heat flux [W/m²]
    heat_rate_watts: float               # Total thermal power Q = flux * area [Watts]
    is_input: bool                       # True = Net ingress into shelter, False = Net heat loss


@dataclass
class EnergyBalanceResult:
    """First Law of Thermodynamics Energy Balance audit."""
    total_heat_in_watts: float           # Sum of solar and convective heat entering envelope [W]
    internal_generation_watts: float     # Total occupant and equipment heat generated inside [W]
    total_energy_input_watts: float      # Q_in + Q_gen [W]
    total_heat_out_watts: float          # Sum of heat dissipated to ground and ambient [W]
    residual_watts: float                # |Total In - Total Out| [W]
    balance_error_pct: float             # Residual / Total In * 100 [%]
    is_conserved: bool                   # True if error < 5.0% tolerance


@dataclass
class SpatialField3D:
    """3D spatial mesh and vector field extraction."""
    nodal_temperatures: np.ndarray       # Nodal temperature array [°C]
    heat_flux_x: np.ndarray              # TFX flux component [W/m²]
    heat_flux_y: np.ndarray              # TFY flux component [W/m²]
    heat_flux_z: np.ndarray              # TFZ flux component [W/m²]
    heat_flux_mag: np.ndarray            # |q| magnitude [W/m²]
    peak_flux_mag: float                 # Peak local heat flux [W/m²]
    mean_flux_mag: float                 # Average envelope heat flux [W/m²]
    node_count: int                      # Total FEA mesh nodes
    element_count: int                   # Total FEA mesh elements
    vtk_file_path: Optional[str] = None  # Saved PyVista VTK file location


@dataclass
class TransientHistory:
    """Time-series thermal response data for 24h/48h transient simulations."""
    time_hours: List[float]              # Time array [h]
    indoor_temp_c: List[float]           # Indoor temperature response [°C]
    outdoor_temp_c: List[float]          # Outdoor driving ambient [°C]
    peak_indoor_temp_c: float            # Peak indoor temperature [°C]
    min_indoor_temp_c: float             # Minimum indoor temperature [°C]
    time_lag_hours: float                # Thermal phase lag Δt_lag [hours]
    decrement_factor: float              # Amplitude decrement factor μ [0.0 - 1.0]


@dataclass
class SimulationResult:
    """Authoritative structured output contract returned by the ANSYS Physics Engine."""
    status: SolverStatus
    execution_time_seconds: float
    min_envelope_temp_c: float           # Minimum envelope temperature [°C]
    max_envelope_temp_c: float           # Maximum envelope temperature [°C]
    mean_indoor_temp_c: float            # Average indoor core temperature [°C]
    derived_physics: DerivedPhysicsParameters
    surfaces: Dict[str, SurfaceHeatRate]
    energy_balance: EnergyBalanceResult
    spatial_3d: Optional[SpatialField3D] = None
    transient: Optional[TransientHistory] = None
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
