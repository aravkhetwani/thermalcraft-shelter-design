"""
Phase 3 Stage 3.2: 3D Full-Shelter 24-Hour Transient Solver with Diurnal Solar Tracking
--------------------------------------------------------------------------------------
Simulates a full 3D multi-material passive emergency shelter in ANSYS MAPDL (SOLID87)
over a 48-hour day/night cycle, modeling orientation-dependent solar path migration:
  - East Wall: Morning sun peak (06:00 - 11:00)
  - Roof & South Wall: Solar noon peak (11:00 - 14:00)
  - West Wall: Low-angle afternoon sun (14:00 - 19:00)
  - North Wall: Diffuse sky radiation only
  - Ground Slab: Constant earth thermal coupling (24°C)
  - Room Air Core: Internal metabolic occupant load (400 W)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
from ansys.mapdl.core import launch_mapdl, Mapdl


@dataclass
class SolarIrradianceComponents:
    """Instantaneous solar irradiance incident on each orientation (W/m²)."""
    i_roof: float
    i_east: float
    i_south: float
    i_west: float
    i_north: float


def compute_orientation_solar_irradiance(
    t_hours: float,
    i_peak_horizontal: float = 900.0,
    diffuse_fraction: float = 0.12
) -> SolarIrradianceComponents:
    """
    Computes direct beam and diffuse solar irradiance incident on horizontal
    and vertical surfaces based on sun elevation and azimuth geometry over 24h.
    """
    t_day = t_hours % 24.0

    # Nighttime (before 06:00 or after 18:00)
    if t_day < 6.0 or t_day > 18.0:
        return SolarIrradianceComponents(0.0, 0.0, 0.0, 0.0, 0.0)

    # Solar elevation profile (peaks at noon t=12:00)
    sin_elev = np.sin(np.pi * (t_day - 6.0) / 12.0)
    i_horizontal = i_peak_horizontal * sin_elev

    # 1. Horizontal Roof (Receives direct beam + sky diffuse)
    i_roof = i_horizontal

    # 2. East Wall (Receives direct beam between 06:00 and 12:00)
    if 6.0 <= t_day <= 12.0:
        i_east = i_peak_horizontal * 0.75 * np.sin(np.pi * (t_day - 6.0) / 6.0) + diffuse_fraction * i_horizontal
    else:
        i_east = diffuse_fraction * i_horizontal

    # 3. South Wall (Receives beam between 08:00 and 16:00, peak at noon)
    if 8.0 <= t_day <= 16.0:
        i_south = i_peak_horizontal * 0.55 * np.sin(np.pi * (t_day - 8.0) / 8.0) + diffuse_fraction * i_horizontal
    else:
        i_south = diffuse_fraction * i_horizontal

    # 4. West Wall (Receives direct low-angle intense beam between 12:00 and 18:00)
    if 12.0 <= t_day <= 18.0:
        i_west = i_peak_horizontal * 0.85 * np.sin(np.pi * (t_day - 12.0) / 6.0) + diffuse_fraction * i_horizontal
    else:
        i_west = diffuse_fraction * i_horizontal

    # 5. North Wall (Diffuse only in northern hemisphere summer)
    i_north = diffuse_fraction * i_horizontal

    return SolarIrradianceComponents(
        i_roof=float(max(0.0, i_roof)),
        i_east=float(max(0.0, i_east)),
        i_south=float(max(0.0, i_south)),
        i_west=float(max(0.0, i_west)),
        i_north=float(max(0.0, i_north))
    )


@dataclass
class Transient3DConfig:
    """Configuration for 3D Full-Shelter transient simulation."""
    length: float = 4.0               # X-span (East-West length in meters)
    width: float = 3.0                # Y-span (North-South width in meters)
    height: float = 2.5               # Z-height in meters
    wall_thickness: float = 0.20      # Envelope thickness in meters
    
    # Material thermo-physical properties
    k_envelope: float = 0.65          # Thermal conductivity [W/(m·K)] (Stabilized Earth / Brick)
    rho_envelope: float = 1800.0      # Density [kg/m³]
    cp_envelope: float = 1000.0       # Specific heat [J/(kg·K)]
    
    k_air_core: float = 0.35          # Indoor room air convective equivalent conductivity (W/m·K)
    rho_air_core: float = 1.20
    cp_air_core: float = 1005.0

    # Solar absorptances
    alpha_roof: float = 0.85          # Standard dark roof
    alpha_walls: float = 0.60         # Standard wall finish
    
    # Film coefficients
    h_outdoor: float = 20.0           # Outdoor convective film [W/(m²·K)]
    h_indoor: float = 7.7             # Indoor convective film [W/(m²·K)]
    
    # Internal heat load & ground
    occupant_heat_total: float = 400.0# Watts inside room
    t_ground: float = 24.0            # Deep earth boundary temp (°C)
    t_ambient_mean: float = 34.0      # Mean ambient temp (°C)
    t_ambient_amp: float = 10.0       # Diurnal ambient swing (24°C to 44°C)
    
    # Simulation timing
    hours_simulated: int = 48         # 48 hours for cyclic stabilization
    time_step_sec: float = 1800.0     # 30 minute time steps (1800s)


@dataclass
class Transient3DSimulationResult:
    """Results from 3D transient FEA."""
    config: Transient3DConfig
    time_hours: np.ndarray
    t_ambient: np.ndarray
    t_roof_sol_air: np.ndarray
    t_east_sol_air: np.ndarray
    t_south_sol_air: np.ndarray
    t_west_sol_air: np.ndarray
    
    # Monitored temperatures
    t_indoor_core: np.ndarray
    t_roof_outer_surface: np.ndarray
    t_east_outer_surface: np.ndarray
    t_south_outer_surface: np.ndarray
    t_west_outer_surface: np.ndarray
    t_north_outer_surface: np.ndarray
    
    # Spatial PyVista snapshots at key hours (e.g. 09:00, 13:00, 17:00, 02:00)
    spatial_snapshots: Dict[int, pv.UnstructuredGrid]


def run_3d_transient_shelter_simulation(
    config: Transient3DConfig,
    existing_mapdl: Optional[Mapdl] = None
) -> Transient3DSimulationResult:
    """
    Builds and solves the full 3D transient thermal shelter in ANSYS MAPDL (SOLID87)
    with orientation-dependent solar tracking over 48 hours.
    """
    mapdl = existing_mapdl if existing_mapdl is not None else launch_mapdl()
    mapdl.clear()
    mapdl.prep7()
    mapdl.title("SIH 2026: 3D Full-Shelter Transient Solar Tracking Simulation")

    # 1. Select 10-Node Quadratic Tetrahedral Thermal Solid Element SOLID87
    mapdl.et(1, "SOLID87")

    # 2. Material Definitions
    # Mat 1: Solid Envelope (Rammed Earth / Masonry with Thermal Storage)
    mapdl.mp("KXX", 1, config.k_envelope)
    mapdl.mp("DENS", 1, config.rho_envelope)
    mapdl.mp("C", 1, config.cp_envelope)

    # Mat 2: Indoor Room Core Volume
    mapdl.mp("KXX", 2, config.k_air_core)
    mapdl.mp("DENS", 2, config.rho_air_core)
    mapdl.mp("C", 2, config.cp_air_core)

    lx, ly, lz = config.length, config.width, config.height
    tw = config.wall_thickness

    # 3. 3D Multi-Volume Geometry (7 discrete non-overlapping blocks)
    # Volume 1: Floor Base Slab (Z in [0, tw])
    mapdl.block(0, lx, 0, ly, 0, tw)
    
    # Volume 2: South Wall (Front, Y in [0, tw], Z in [tw, lz - tw])
    mapdl.block(0, lx, 0, tw, tw, lz - tw)
    
    # Volume 3: North Wall (Back, Y in [ly - tw, ly], Z in [tw, lz - tw])
    mapdl.block(0, lx, ly - tw, ly, tw, lz - tw)
    
    # Volume 4: West Wall (Left, X in [0, tw], Y in [tw, ly - tw], Z in [tw, lz - tw])
    mapdl.block(0, tw, tw, ly - tw, tw, lz - tw)
    
    # Volume 5: East Wall (Right, X in [lx - tw, lx], Y in [tw, ly - tw], Z in [tw, lz - tw])
    mapdl.block(lx - tw, lx, tw, ly - tw, tw, lz - tw)
    
    # Volume 6: Roof Slab (Top, Z in [lz - tw, lz])
    mapdl.block(0, lx, 0, ly, lz - tw, lz)
    
    # Volume 7: Indoor Air Cavity (Core)
    mapdl.block(tw, lx - tw, tw, ly - tw, tw, lz - tw)

    # 4. Glue all volumes together for monolithic 3D contact
    mapdl.vglue("ALL")

    # 5. Assign Materials
    # Select indoor air domain volume (centered at lx/2, ly/2, lz/2)
    mapdl.vsel("S", "LOC", "X", lx/2.0 - 0.2, lx/2.0 + 0.2)
    mapdl.vsel("R", "LOC", "Y", ly/2.0 - 0.2, ly/2.0 + 0.2)
    mapdl.vsel("R", "LOC", "Z", lz/2.0 - 0.2, lz/2.0 + 0.2)
    mapdl.vatt(mat=2, real=1, type=1)

    # Select envelope volumes
    mapdl.vsel("INVE")
    mapdl.vatt(mat=1, real=1, type=1)
    mapdl.allsel()

    # 6. Meshing with optimized element size (~2500 - 4000 elements for 15s transient solve)
    mapdl.esize(0.35)  # 350 mm element size
    mapdl.mshape(1, "3D")  # Tetrahedral element shape
    mapdl.mshkey(0)        # Free meshing
    mapdl.vmesh("ALL")

    # 7. Volumetric Internal Heat Generation (Occupants)
    v_indoor_vol = (lx - 2*tw) * (ly - 2*tw) * (lz - 2*tw)
    q_vol = config.occupant_heat_total / v_indoor_vol
    mapdl.esel("S", "MAT", "", 2)
    mapdl.bfe("ALL", "HGEN", 1, q_vol)
    mapdl.allsel()

    # Initial Uniform Temperature
    mapdl.tunif(config.t_ambient_mean)

    # 8. Enter Transient Solution Processor
    mapdl.slashsolu()
    mapdl.antype("TRANS")
    mapdl.timint("ON")
    mapdl.autots("OFF")         # Fixed time stepping for ultra-fast solution
    mapdl.kbc(0)                # Ramped boundary conditions
    mapdl.outres("ERASE")
    mapdl.outres("ALL", "LAST") # Save only converged state at each hour

    dt_sec = config.time_step_sec
    time_steps_hours = np.arange(0.0, config.hours_simulated + (dt_sec / 3600.0), dt_sec / 3600.0)

    # 9. Transient Diurnal Time-Stepping Loop
    total_steps = len(time_steps_hours) - 1
    print(f"  [MAPDL Solver] Starting 3D transient solution: {total_steps} load steps...")
    for step_idx, t_h in enumerate(time_steps_hours[1:], start=1):
        if step_idx % 4 == 0 or step_idx == total_steps:
            print(f"  [MAPDL Solver] Step {step_idx}/{total_steps} (Time: {t_h:.1f}h) solved...")

        current_time_sec = t_h * 3600.0
        mapdl.time(current_time_sec)
        mapdl.deltim(dt_sec)

        # Ambient air temp
        t_amb = config.t_ambient_mean + config.t_ambient_amp * np.sin(2.0 * np.pi * (t_h - 9.0) / 24.0)

        # Orientation-specific solar components
        solar = compute_orientation_solar_irradiance(t_h)

        # Instantaneous Sol-Air Temperatures
        t_sol_roof = t_amb + (config.alpha_roof * solar.i_roof) / config.h_outdoor
        t_sol_east = t_amb + (config.alpha_walls * solar.i_east) / config.h_outdoor
        t_sol_south = t_amb + (config.alpha_walls * solar.i_south) / config.h_outdoor
        t_sol_west = t_amb + (config.alpha_walls * solar.i_west) / config.h_outdoor
        t_sol_north = t_amb + (config.alpha_walls * solar.i_north) / config.h_outdoor

        # 1. Ground Slab Dirichlet BC (Z = 0)
        mapdl.nsel("S", "LOC", "Z", 0.0)
        mapdl.d("ALL", "TEMP", config.t_ground)

        # 2. Roof Exterior (Z = lz)
        mapdl.nsel("S", "LOC", "Z", lz)
        mapdl.sf("ALL", "CONV", config.h_outdoor, t_sol_roof)

        # 3. East Exterior Wall (X = lx)
        mapdl.nsel("S", "LOC", "X", lx)
        mapdl.nsel("R", "LOC", "Z", 0.001, lz)
        mapdl.sf("ALL", "CONV", config.h_outdoor, t_sol_east)

        # 4. South Exterior Wall (Y = 0)
        mapdl.nsel("S", "LOC", "Y", 0.0)
        mapdl.nsel("R", "LOC", "Z", 0.001, lz)
        mapdl.sf("ALL", "CONV", config.h_outdoor, t_sol_south)

        # 5. West Exterior Wall (X = 0)
        mapdl.nsel("S", "LOC", "X", 0.0)
        mapdl.nsel("R", "LOC", "Z", 0.001, lz)
        mapdl.sf("ALL", "CONV", config.h_outdoor, t_sol_west)

        # 6. North Exterior Wall (Y = ly)
        mapdl.nsel("S", "LOC", "Y", ly)
        mapdl.nsel("R", "LOC", "Z", 0.001, lz)
        mapdl.sf("ALL", "CONV", config.h_outdoor, t_sol_north)

        mapdl.allsel()
        mapdl.solve()

    # 8. Post-Processing & Result Extraction
    mapdl.post1()

    # Find representative node IDs for monitoring
    # Core node (center of room)
    mapdl.nsel("S", "LOC", "X", lx / 2.0 - 0.1, lx / 2.0 + 0.1)
    mapdl.nsel("R", "LOC", "Y", ly / 2.0 - 0.1, ly / 2.0 + 0.1)
    mapdl.nsel("R", "LOC", "Z", lz / 2.0 - 0.1, lz / 2.0 + 0.1)
    node_core = int(mapdl.get_value("NODE", 0, "NUM", "MIN"))

    # Roof outer center node
    mapdl.nsel("S", "LOC", "X", lx / 2.0 - 0.1, lx / 2.0 + 0.1)
    mapdl.nsel("R", "LOC", "Y", ly / 2.0 - 0.1, ly / 2.0 + 0.1)
    mapdl.nsel("R", "LOC", "Z", lz)
    node_roof = int(mapdl.get_value("NODE", 0, "NUM", "MIN"))

    # East outer center node
    mapdl.nsel("S", "LOC", "X", lx)
    mapdl.nsel("R", "LOC", "Y", ly / 2.0 - 0.1, ly / 2.0 + 0.1)
    mapdl.nsel("R", "LOC", "Z", lz / 2.0 - 0.1, lz / 2.0 + 0.1)
    node_east = int(mapdl.get_value("NODE", 0, "NUM", "MIN"))

    # South outer center node
    mapdl.nsel("S", "LOC", "X", lx / 2.0 - 0.1, lx / 2.0 + 0.1)
    mapdl.nsel("R", "LOC", "Y", 0.0)
    mapdl.nsel("R", "LOC", "Z", lz / 2.0 - 0.1, lz / 2.0 + 0.1)
    node_south = int(mapdl.get_value("NODE", 0, "NUM", "MIN"))

    # West outer center node
    mapdl.nsel("S", "LOC", "X", 0.0)
    mapdl.nsel("R", "LOC", "Y", ly / 2.0 - 0.1, ly / 2.0 + 0.1)
    mapdl.nsel("R", "LOC", "Z", lz / 2.0 - 0.1, lz / 2.0 + 0.1)
    node_west = int(mapdl.get_value("NODE", 0, "NUM", "MIN"))

    # North outer center node
    mapdl.nsel("S", "LOC", "X", lx / 2.0 - 0.1, lx / 2.0 + 0.1)
    mapdl.nsel("R", "LOC", "Y", ly)
    mapdl.nsel("R", "LOC", "Z", lz / 2.0 - 0.1, lz / 2.0 + 0.1)
    node_north = int(mapdl.get_value("NODE", 0, "NUM", "MIN"))
    mapdl.allsel()

    num_sets = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
    time_h_list = []
    t_amb_list = []
    t_roof_sol_list, t_east_sol_list, t_south_sol_list, t_west_sol_list = [], [], [], []
    t_core_list, t_roof_surf_list, t_east_surf_list, t_south_surf_list, t_west_surf_list, t_north_surf_list = [], [], [], [], [], []

    # Target snapshot hours for 3D PyVista visualization (Day 2: 09:00, 13:00, 17:00, 02:00)
    target_snapshot_hours = [9, 13, 17, 26] # 26 = 02:00 night of day 2
    spatial_snapshots = {}

    for s_idx in range(1, num_sets + 1):
        mapdl.set(s_idx)
        time_sec = float(mapdl.get_value("ACTIVE", 0, "SET", "TIME"))
        th = time_sec / 3600.0
        time_h_list.append(th)

        t_amb = config.t_ambient_mean + config.t_ambient_amp * np.sin(2.0 * np.pi * (th - 9.0) / 24.0)
        solar = compute_orientation_solar_irradiance(th)
        t_amb_list.append(t_amb)
        t_roof_sol_list.append(t_amb + (config.alpha_roof * solar.i_roof) / config.h_outdoor)
        t_east_sol_list.append(t_amb + (config.alpha_walls * solar.i_east) / config.h_outdoor)
        t_south_sol_list.append(t_amb + (config.alpha_walls * solar.i_south) / config.h_outdoor)
        t_west_sol_list.append(t_amb + (config.alpha_walls * solar.i_west) / config.h_outdoor)

        nodal_temps = mapdl.post_processing.nodal_temperature()
        t_core_list.append(float(nodal_temps[node_core - 1]))
        t_roof_surf_list.append(float(nodal_temps[node_roof - 1]))
        t_east_surf_list.append(float(nodal_temps[node_east - 1]))
        t_south_surf_list.append(float(nodal_temps[node_south - 1]))
        t_west_surf_list.append(float(nodal_temps[node_west - 1]))
        t_north_surf_list.append(float(nodal_temps[node_north - 1]))

        # Capture 3D mesh grid if at target snapshot hour
        for target_h in target_snapshot_hours:
            target_time_val = target_h + 24.0 if target_h < 24 else target_h
            if abs(th - target_time_val) <= 0.6 and target_h not in spatial_snapshots:
                grid = mapdl.mesh.grid.copy()
                grid.point_data["Temperature"] = nodal_temps
                spatial_snapshots[target_h] = grid

    return Transient3DSimulationResult(
        config=config,
        time_hours=np.array(time_h_list),
        t_ambient=np.array(t_amb_list),
        t_roof_sol_air=np.array(t_roof_sol_list),
        t_east_sol_air=np.array(t_east_sol_list),
        t_south_sol_air=np.array(t_south_sol_list),
        t_west_sol_air=np.array(t_west_sol_list),
        t_indoor_core=np.array(t_core_list),
        t_roof_outer_surface=np.array(t_roof_surf_list),
        t_east_outer_surface=np.array(t_east_surf_list),
        t_south_outer_surface=np.array(t_south_surf_list),
        t_west_outer_surface=np.array(t_west_surf_list),
        t_north_outer_surface=np.array(t_north_surf_list),
        spatial_snapshots=spatial_snapshots
    )


def plot_3d_transient_time_series(
    res: Transient3DSimulationResult,
    save_path: str
):
    """Plots 24-hour orientation-dependent temperature trajectories."""
    mask_day2 = (res.time_hours >= 24.0) & (res.time_hours <= 48.0)
    t2_h = res.time_hours[mask_day2] - 24.0

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # 1. Outer Surface & Sol-Air Driving Waves
    ax1.plot(t2_h, res.t_ambient[mask_day2], "k:", linewidth=2.0, label="Ambient Air ($T_{amb}$)")
    ax1.plot(t2_h, res.t_roof_outer_surface[mask_day2], color="#e63946", linewidth=2.5, label="Roof Surface (Noon Peak ~13:00)")
    ax1.plot(t2_h, res.t_east_outer_surface[mask_day2], color="#f77f00", linestyle="-.", linewidth=2.2, label="East Wall Surface (Morning Peak ~09:00)")
    ax1.plot(t2_h, res.t_west_outer_surface[mask_day2], color="#d90429", linestyle="--", linewidth=2.2, label="West Wall Surface (Afternoon Peak ~16:30)")
    ax1.plot(t2_h, res.t_south_outer_surface[mask_day2], color="#fcbf49", linestyle=":", linewidth=2.0, label="South Wall Surface")

    ax1.set_ylabel("Surface Temperature (°C)", fontsize=11, fontweight="bold")
    ax1.set_title("3D Solar Path Migration & Exterior Surface Response over 24-Hour Day/Night Cycle", fontsize=13, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", framealpha=0.95, fontsize=9.5)

    # 2. Indoor Room Air Core Response vs Comfort Target
    ax2.plot(t2_h, res.t_ambient[mask_day2], "k:", linewidth=1.5, alpha=0.7, label="Outdoor Ambient Air")
    ax2.plot(t2_h, res.t_indoor_core[mask_day2], color="#2a9d8f", linewidth=3.0, label=f"Indoor Room Core Air ($T_{{core}}$)")
    ax2.axhline(26.0, color="blue", linestyle="--", linewidth=1.8, label="Comfort Target Setpoint (26.0°C)")
    ax2.axhline(res.config.t_ground, color="brown", linestyle="-.", linewidth=1.8, label=f"Earth Ground Foundation ({res.config.t_ground}°C Sink)")

    # Mark time lag
    peak_roof_t = t2_h[np.argmax(res.t_roof_outer_surface[mask_day2])]
    peak_core_t = t2_h[np.argmax(res.t_indoor_core[mask_day2])]
    ax2.axvline(peak_roof_t, color="#e63946", linestyle=":", alpha=0.7)
    ax2.axvline(peak_core_t, color="#2a9d8f", linestyle=":", alpha=0.7)
    ax2.annotate(
        f"Thermal Time Lag: {peak_core_t - peak_roof_t:.1f} Hours",
        xy=(peak_core_t, np.max(res.t_indoor_core[mask_day2])),
        xytext=(peak_core_t + 1.0, np.max(res.t_indoor_core[mask_day2]) + 1.5),
        arrowprops=dict(facecolor="black", arrowstyle="->", lw=1.5),
        fontsize=10, fontweight="bold", backgroundcolor="yellow"
    )

    ax2.set_xlabel("Time of Day (Hours from Midnight [00:00 - 24:00])", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Indoor Air Temperature (°C)", fontsize=11, fontweight="bold")
    ax2.set_title("Indoor Thermal Stabilization & Phase Shift via High-Mass Passive Design", fontsize=12, fontweight="bold")
    ax2.set_xticks(np.arange(0, 25, 2))
    ax2.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left", framealpha=0.95, fontsize=9.5)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def render_3d_diurnal_solar_snapshots(
    res: Transient3DSimulationResult,
    save_path: str
):
    """Renders a 4-panel 3D PyVista spatial visualization of the shelter at 4 critical solar milestones."""
    p = pv.Plotter(shape=(2, 2), off_screen=True, window_size=(1600, 1200))
    p.set_background("#16161a")

    snapshots = res.spatial_snapshots
    cfg = res.config
    lx, ly, lz = cfg.length, cfg.width, cfg.height

    milestones = [
        (9, (0, 0), "1. MORNING (09:00) — Direct Solar Beam on East Wall", "#f77f00"),
        (13, (0, 1), "2. NOON (13:00) — Peak Zenith Solar Shock on Roof", "#e63946"),
        (17, (1, 0), "3. AFTERNOON (17:00) — Low-Angle Severe Heat on West Wall", "#d90429"),
        (26, (1, 1), "4. MIDNIGHT (02:00) — Earth Foundation & Night Sky Cooling", "#0077b6")
    ]

    for hour_key, (row, col), title, banner_col in milestones:
        p.subplot(row, col)
        if hour_key in snapshots:
            grid = snapshots[hour_key]
            p.add_mesh(
                grid,
                scalars="Temperature",
                cmap="turbo",
                clim=[24.0, 55.0],
                opacity=0.92,
                show_scalar_bar=(row == 1 and col == 1),
                scalar_bar_args={"title": "Temperature (°C)", "color": "white", "vertical": True}
            )
            p.add_text(title, position="upper_left", color=banner_col, font_size=10.5)

            # Orientation Compass Indicator
            p.add_point_labels(
                points=[[lx, ly/2.0, lz*0.9]], labels=["EAST"], font_size=8, text_color="#f77f00"
            )
            p.add_point_labels(
                points=[[0.0, ly/2.0, lz*0.9]], labels=["WEST"], font_size=8, text_color="#d90429"
            )
            p.add_point_labels(
                points=[[lx/2.0, 0.0, lz*0.9]], labels=["SOUTH"], font_size=8, text_color="#fcbf49"
            )

        p.camera_position = [(lx * 2.2, -ly * 2.0, lz * 2.1), (lx / 2.0, ly / 2.0, lz / 2.0), (0, 0, 1)]
        p.add_axes(color="white")

    p.screenshot(save_path)
    p.close()
