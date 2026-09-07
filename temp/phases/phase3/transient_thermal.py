"""
Phase 3 Stage 3.1: Transient Thermal Dynamics & Diurnal Cycle Solver
-------------------------------------------------------------------
Simulates 24-hour transient heat diffusion with thermal mass storage (rho * Cp),
quantifying Time Lag (Delta t_lag) and Decrement Factor (mu) under realistic
diurnal ambient temperature and solar irradiance cycles.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
from ansys.mapdl.core import launch_mapdl, Mapdl


@dataclass
class TransientMaterial:
    """Thermo-physical properties including thermal mass (density and specific heat)."""
    name: str
    conductivity: float     # k [W/(m·K)]
    density: float          # rho [kg/m³]
    specific_heat: float    # Cp [J/(kg·K)]

    @property
    def volumetric_heat_capacity(self) -> float:
        """Cv = rho * Cp in J/(m³·K) or MJ/(m³·K)."""
        return self.density * self.specific_heat

    @property
    def thermal_diffusivity(self) -> float:
        """alpha = k / (rho * Cp) in m²/s."""
        return self.conductivity / (self.density * self.specific_heat)


# Predefined material database with thermal mass
MATERIALS_DB = {
    "CGI_Sheet": TransientMaterial("Corrugated Galvanized Iron (Tin)", conductivity=50.0, density=7850.0, specific_heat=480.0),
    "Plywood": TransientMaterial("Plywood / Timber", conductivity=0.13, density=600.0, specific_heat=1600.0),
    "Standard_Brick": TransientMaterial("Burnt Clay Brick Masonry", conductivity=0.84, density=1900.0, specific_heat=840.0),
    "Concrete": TransientMaterial("Dense Concrete Slab", conductivity=1.40, density=2300.0, specific_heat=1000.0),
    "AAC_Block": TransientMaterial("Autoclaved Aerated Concrete", conductivity=0.24, density=700.0, specific_heat=1000.0),
    "Rammed_Earth": TransientMaterial("Rammed Earth / Stabilized Earth (CSEB)", conductivity=0.95, density=1850.0, specific_heat=1050.0),
    "Rockwool": TransientMaterial("Rockwool Insulation", conductivity=0.038, density=45.0, specific_heat=1030.0),
    "Air_Cavity": TransientMaterial("Indoor Air Buffer", conductivity=0.026, density=1.20, specific_heat=1005.0)
}


@dataclass
class TransientWallAssembly:
    """Multi-layer wall assembly with specific thicknesses and materials."""
    name: str
    layers: List[Tuple[TransientMaterial, float]]  # List of (Material, thickness_meters)

    @property
    def total_thickness(self) -> float:
        return sum(thick for _, thick in self.layers)

    @property
    def total_r_value(self) -> float:
        return sum(thick / mat.conductivity for mat, thick in self.layers)

    @property
    def total_thermal_capacity_per_area(self) -> float:
        """Areal thermal capacity C_area = sum(rho_i * Cp_i * d_i) in kJ/(m²·K)."""
        return sum(mat.density * mat.specific_heat * thick for mat, thick in self.layers) / 1000.0


@dataclass
class DiurnalEnvironmentConfig:
    """Environmental parameters defining the 24-hour diurnal cycle."""
    t_ambient_mean: float = 34.0       # Mean ambient air temperature (°C)
    t_ambient_amp: float = 10.0        # Ambient amplitude (e.g. 34 ± 10 -> 24°C to 44°C)
    solar_irradiance_peak: float = 900.0 # Peak noon solar irradiance (W/m²)
    solar_absorptance: float = 0.85    # Exterior surface solar absorptance (alpha)
    h_outdoor: float = 20.0            # Outdoor convective film coefficient (W/m²·K)
    h_indoor: float = 7.7              # Indoor convective film coefficient (W/m²·K)
    t_indoor_setpoint: float = 26.0    # Indoor target / ventilation temperature (°C)
    t_ground: float = 24.0             # Constant deep ground temperature (°C)
    hours_simulated: int = 48          # Run 48h to allow initial transient decay and reach cyclic steady-state
    time_step_sec: float = 600.0       # 10 minute time steps (600s)


@dataclass
class TransientSimulationResult:
    """Time-series output from 24h / 48h transient FEA simulation."""
    assembly: TransientWallAssembly
    env: DiurnalEnvironmentConfig
    time_hours: np.ndarray             # Time array in hours [0, 48]
    t_outdoor_ambient: np.ndarray      # Outdoor air temperature (°C)
    t_outdoor_sol_air: np.ndarray      # Sol-Air temperature (°C)
    t_outdoor_surface: np.ndarray      # Outer wall surface temperature (°C)
    t_indoor_surface: np.ndarray       # Inner wall surface temperature (°C)
    time_lag_hours: float              # Delta t_lag in hours
    decrement_factor: float            # mu = A_in / A_out
    spatial_x: np.ndarray              # Coordinates along wall thickness (m)
    spatial_temp_profiles: Dict[int, np.ndarray] # Temperature distribution at key hours (e.g. 14:00, 02:00)


def calculate_diurnal_conditions(env: DiurnalEnvironmentConfig, t_hours: float) -> Tuple[float, float, float]:
    """Calculates instantaneous ambient temp, solar irradiance, and Sol-Air temp at time t."""
    # Day-night cycle: Peak ambient at t=15:00 (3 PM), min at t=03:00 (3 AM)
    # Sinusoidal with period 24h, phase shifted by 9 hours
    t_amb = env.t_ambient_mean + env.t_ambient_amp * np.sin(2.0 * np.pi * (t_hours - 9.0) / 24.0)

    # Solar irradiance: Only between 06:00 (sunrise) and 18:00 (sunset)
    t_day = t_hours % 24.0
    if 6.0 <= t_day <= 18.0:
        i_solar = env.solar_irradiance_peak * np.sin(np.pi * (t_day - 6.0) / 12.0)
    else:
        i_solar = 0.0

    # Sol-Air Temperature: T_sol_air = T_amb + (alpha * I_solar) / h_out
    t_sol_air = t_amb + (env.solar_absorptance * i_solar) / env.h_outdoor
    return t_amb, i_solar, t_sol_air


def run_transient_wall_simulation(
    assembly: TransientWallAssembly,
    env: DiurnalEnvironmentConfig,
    existing_mapdl: Optional[Mapdl] = None
) -> TransientSimulationResult:
    """
    Executes a high-precision 2D/1D transient thermal FEA simulation in ANSYS MAPDL
    across a 48-hour diurnal cycle with automatic time-stepping (ANTYPE, TRANS).
    """
    mapdl = existing_mapdl if existing_mapdl is not None else launch_mapdl()
    mapdl.clear()
    mapdl.prep7()
    mapdl.title(f"SIH 2026: Transient Thermal Simulation - {assembly.name}")

    # Use 2D 8-Node Higher Order Thermal Element PLANE77
    mapdl.et(1, "PLANE77")

    # Define Materials in MAPDL
    current_mat_id = 1
    for mat, _ in assembly.layers:
        mapdl.mp("KXX", current_mat_id, mat.conductivity)
        mapdl.mp("DENS", current_mat_id, mat.density)
        mapdl.mp("C", current_mat_id, mat.specific_heat)
        current_mat_id += 1

    # Geometry: 2D Wall Strip (Height = 1.0 m, Layer thicknesses along X)
    wall_height = 1.0
    x_curr = 0.0
    area_ids = []

    for idx, (mat, thick) in enumerate(assembly.layers, start=1):
        x_next = x_curr + thick
        mapdl.rectng(x_curr, x_next, 0.0, wall_height)
        area_ids.append(idx)
        x_curr = x_next

    total_wall_thickness = x_curr

    # Glue areas for perfect thermal contact only if multi-layer assembly
    if len(assembly.layers) > 1:
        mapdl.aglue("ALL")

    # Mesh each layer with its assigned material using spatial location selection
    x_curr = 0.0
    for idx, (mat, thick) in enumerate(assembly.layers, start=1):
        x_next = x_curr + thick
        mapdl.asel("S", "LOC", "X", x_curr - 1e-6, x_next + 1e-6)
        mapdl.mat(idx)
        e_size = max(0.0005, min(thick / 4.0, 0.005))
        mapdl.esize(e_size)
        mapdl.amesh("ALL")
        x_curr = x_next

    mapdl.allsel()

    # Initial Uniform Temperature Condition (at t = 0s)
    t_amb_0, _, t_sol_0 = calculate_diurnal_conditions(env, 0.0)
    mapdl.tunif(t_sol_0)

    # Enter Transient Solution Processor
    mapdl.slashsolu()
    mapdl.antype("TRANS")       # Transient thermal analysis
    mapdl.timint("ON")          # Time integration ON (dE/dt != 0)
    mapdl.autots("ON")          # Automatic time-stepping
    mapdl.kbc(0)                # Ramped boundary conditions between load steps
    mapdl.outres("ALL", "ALL")  # Save all sub-step results

    # Time-stepping setup
    dt_sec = env.time_step_sec
    total_time_sec = env.hours_simulated * 3600.0
    time_steps_hours = np.arange(0.0, env.hours_simulated + (dt_sec / 3600.0), dt_sec / 3600.0)

    # Apply Diurnal Boundary Conditions per Load Step
    for t_h in time_steps_hours[1:]:
        current_time_sec = t_h * 3600.0
        t_amb, i_solar, t_sol_air = calculate_diurnal_conditions(env, t_h)

        mapdl.time(current_time_sec)
        mapdl.deltim(dt_sec, dt_sec / 4.0, dt_sec * 2.0)  # Min/Max substeps

        # 1. Outer Surface (X = 0): Outdoor Convection with Sol-Air Temperature
        mapdl.nsel("S", "LOC", "X", 0.0)
        mapdl.sf("ALL", "CONV", env.h_outdoor, t_sol_air)

        # 2. Inner Surface (X = total_wall_thickness): Indoor Convection with Room Air Setpoint
        mapdl.nsel("S", "LOC", "X", total_wall_thickness)
        mapdl.sf("ALL", "CONV", env.h_indoor, env.t_indoor_setpoint)

        mapdl.allsel()
        mapdl.solve()

    # Post-Processing: Extract Time-History and Spatial Profiles
    mapdl.post1()

    # Query Nodes on Outer and Inner Surfaces
    mapdl.nsel("S", "LOC", "X", 0.0)
    outer_node = int(mapdl.get_value("NODE", 0, "NUM", "MIN"))

    mapdl.nsel("S", "LOC", "X", total_wall_thickness)
    inner_node = int(mapdl.get_value("NODE", 0, "NUM", "MIN"))
    mapdl.allsel()

    num_sets = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
    t_hours_list = []
    t_out_surf_list = []
    t_in_surf_list = []
    t_amb_list = []
    t_sol_list = []

    for s_idx in range(1, num_sets + 1):
        mapdl.set(s_idx)
        time_curr_sec = float(mapdl.get_value("ACTIVE", 0, "SET", "TIME"))
        time_curr_h = time_curr_sec / 3600.0
        t_hours_list.append(time_curr_h)

        t_amb, _, t_sol = calculate_diurnal_conditions(env, time_curr_h)
        t_amb_list.append(t_amb)
        t_sol_list.append(t_sol)

        t_out_val = float(mapdl.get_value("NODE", outer_node, "TEMP"))
        t_in_val = float(mapdl.get_value("NODE", inner_node, "TEMP"))
        t_out_surf_list.append(t_out_val)
        t_in_surf_list.append(t_in_val)

    t_hours_arr = np.array(t_hours_list)
    t_out_arr = np.array(t_out_surf_list)
    t_in_arr = np.array(t_in_surf_list)
    t_amb_arr = np.array(t_amb_list)
    t_sol_arr = np.array(t_sol_list)

    # Analyze the 2nd 24h cycle (t in [24, 48]) to eliminate initial condition transients
    mask_day2 = (t_hours_arr >= 24.0) & (t_hours_arr <= 48.0)
    t2_hours = t_hours_arr[mask_day2] - 24.0
    t2_out = t_out_arr[mask_day2]
    t2_in = t_in_arr[mask_day2]
    t2_sol = t_sol_arr[mask_day2]

    # Peak times
    peak_out_idx = np.argmax(t2_sol)
    peak_in_idx = np.argmax(t2_in)

    time_peak_out = t2_hours[peak_out_idx]
    time_peak_in = t2_hours[peak_in_idx]

    time_lag = time_peak_in - time_peak_out
    if time_lag < 0:
        time_lag += 24.0

    # Amplitudes & Decrement Factor
    a_out = (np.max(t2_sol) - np.min(t2_sol)) / 2.0
    a_in = (np.max(t2_in) - np.min(t2_in)) / 2.0
    decrement = a_in / a_out if a_out > 0 else 1.0

    # Extract spatial temperature profile along wall thickness at key hours (e.g. 14:00 peak, 02:00 night)
    spatial_profiles = {}
    target_hours_day2 = [14.0, 20.0, 26.0, 32.0]  # 14h (2 PM), 20h (8 PM), 26h (2 AM night), 32h (8 AM)
    x_coords = np.linspace(0.0, total_wall_thickness, 50)

    for th in target_hours_day2:
        # Find closest substep set
        target_sec = (th + 24.0 if th < 24.0 else th) * 3600.0
        closest_set = int(np.argmin(np.abs(t_hours_arr * 3600.0 - target_sec))) + 1
        mapdl.set(closest_set)
        
        # Sample temperature along center horizontal line Y = 0.5
        t_profile = []
        for x_val in x_coords:
            mapdl.nsel("S", "LOC", "X", x_val - 0.005, x_val + 0.005)
            mapdl.nsel("R", "LOC", "Y", 0.45, 0.55)
            if int(mapdl.get_value("NODE", 0, "COUNT")) > 0:
                nd = int(mapdl.get_value("NODE", 0, "NUM", "MIN"))
                t_profile.append(float(mapdl.get_value("NODE", nd, "TEMP")))
            else:
                t_profile.append(t_profile[-1] if t_profile else env.t_indoor_setpoint)
        mapdl.allsel()
        spatial_profiles[int(th % 24)] = np.array(t_profile)

    return TransientSimulationResult(
        assembly=assembly,
        env=env,
        time_hours=t_hours_arr,
        t_outdoor_ambient=t_amb_arr,
        t_outdoor_sol_air=t_sol_arr,
        t_outdoor_surface=t_out_arr,
        t_indoor_surface=t_in_arr,
        time_lag_hours=float(time_lag),
        decrement_factor=float(decrement),
        spatial_x=x_coords,
        spatial_temp_profiles=spatial_profiles
    )


def plot_transient_comparison(
    results: List[TransientSimulationResult],
    save_path: str
):
    """Plots the 24-hour diurnal thermal damping and time-lag response comparing wall assemblies."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # 1. Top Subplot: Sol-Air Outdoor Driver vs Indoor Surface Response
    res0 = results[0]
    mask_day2 = (res0.time_hours >= 24.0) & (res0.time_hours <= 48.0)
    t_day2_h = res0.time_hours[mask_day2] - 24.0

    # Plot Outdoor Sol-Air driver
    ax1.plot(t_day2_h, res0.t_outdoor_sol_air[mask_day2], "r--", linewidth=2.2, label=f"Outdoor Sol-Air Driver ($T_{{sol-air}}$)")
    ax1.plot(t_day2_h, res0.t_outdoor_ambient[mask_day2], "k:", linewidth=1.8, label=f"Ambient Air ($T_{{ambient}}$)")

    colors = ["#d90429", "#f77f00", "#2a9d8f"]
    styles = ["-", "-.", "-"]

    for idx, (res, col, sty) in enumerate(zip(results, colors, styles)):
        t_in_day2 = res.t_indoor_surface[mask_day2]
        ax1.plot(
            t_day2_h, t_in_day2,
            color=col, linestyle=sty, linewidth=2.5,
            label=f"{res.assembly.name} (Lag: {res.time_lag_hours:.1f}h, $\\mu$: {res.decrement_factor:.2f})"
        )

    ax1.set_ylabel("Temperature (°C)", fontsize=11, fontweight="bold")
    ax1.set_title("24-Hour Diurnal Thermal Damping & Phase Shift Comparison", fontsize=13, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", framealpha=0.95, fontsize=10)
    ax1.axhline(26.0, color="blue", linestyle="--", alpha=0.7, label="Comfort Setpoint (26°C)")

    # 2. Bottom Subplot: Decrement & Thermal Heat Flux Ingress
    for idx, (res, col) in enumerate(zip(results, colors)):
        t_in_day2 = res.t_indoor_surface[mask_day2]
        # Inward heat flux into room: q_in = h_in * (T_in_surf - T_setpoint)
        q_in_flux = res.env.h_indoor * (t_in_day2 - res.env.t_indoor_setpoint)
        ax2.plot(t_day2_h, q_in_flux, color=col, linewidth=2.2, label=f"{res.assembly.name}")

    ax2.axhline(0.0, color="black", linewidth=1.2)
    ax2.set_xlabel("Time of Day (Hours from Midnight [00:00 - 24:00])", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Inward Convective Flux ($W/m^2$)", fontsize=11, fontweight="bold")
    ax2.set_title("Convective Heat Ingress into Occupied Space Over 24-Hour Cycle", fontsize=12, fontweight="bold")
    ax2.set_xticks(np.arange(0, 25, 2))
    ax2.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", framealpha=0.95, fontsize=10)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_spatial_temperature_penetration(
    res: TransientSimulationResult,
    save_path: str
):
    """Plots internal temperature wave penetration depth across wall thickness at key hours."""
    fig, ax = plt.subplots(figsize=(10, 6))

    time_labels = {
        14: ("14:00 (Peak Solar)", "#d90429", "-"),
        20: ("20:00 (Evening Sunset)", "#f77f00", "-."),
        2: ("02:00 (Cool Night)", "#0077b6", "--"),
        8: ("08:00 (Morning)", "#2a9d8f", ":")
    }

    x_cm = res.spatial_x * 100.0  # Convert to cm

    for hour, t_prof in res.spatial_temp_profiles.items():
        if hour in time_labels:
            lbl, col, sty = time_labels[hour]
            ax.plot(x_cm, t_prof, color=col, linestyle=sty, linewidth=2.5, label=lbl)

    # Draw layer boundaries
    x_bound = 0.0
    for mat, thick in res.assembly.layers:
        x_bound += thick * 100.0
        ax.axvline(x_bound, color="gray", linestyle=":", alpha=0.7)

    ax.set_xlabel("Wall Depth from Exterior to Interior (cm)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Local Temperature (°C)", fontsize=11, fontweight="bold")
    ax.set_title(f"Thermal Wave Penetration Profile — {res.assembly.name}\n(Time Lag $\\Delta t = {res.time_lag_hours:.1f}$h, Decrement $\\mu = {res.decrement_factor:.2f}$)", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.95, fontsize=10)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
