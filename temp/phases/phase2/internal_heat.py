"""
Internal Heat Generation and Indoor Heat Trapping Simulation Module using PyMAPDL.
Simulates sensible heat release from occupants (100 W/person) and electrical equipment
inside a shelter cross-section, demonstrating the Insulation Paradox and Ventilation Cooling.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
from ansys.mapdl.core import launch_mapdl, Mapdl


@dataclass
class ShelterRoomConfig:
    """Configuration for a 2D shelter cross-section under internal heat loads."""
    room_width: float = 3.0              # Inner room width (m)
    room_height: float = 2.4             # Inner room height (m)
    room_length: float = 4.0             # Shelter length (m) for 2D slice scaling
    wall_thickness: float = 0.25         # Envelope thickness (m)
    wall_conductivity: float = 0.80      # Brick k = 0.80, Insulated k = 0.04 W/(m·K)
    occupant_count: int = 5              # Number of occupants
    heat_per_occupant: float = 100.0     # Sensible heat output per person (W)
    equipment_heat: float = 100.0        # Electronic/lighting heat (W)
    air_change_rate: float = 0.5         # Air changes per hour (ACH, 0.5 = sealed, 6.0 = ventilated)
    outdoor_ambient_temp: float = 38.0   # T_inf,out in °C
    ground_temp: float = 25.0            # Deep ground temperature in °C
    h_outdoor: float = 20.0              # Outdoor film coefficient in W/(m²·K)
    solar_flux_roof: float = 250.0       # Net solar flux absorbed by roof in W/m²
    mesh_size: float = 0.05              # Element size in meters
    element_type: str = "PLANE77"


@dataclass
class ShelterRoomResult:
    """Results from internal heat shelter simulation."""
    config: ShelterRoomConfig
    total_room_internal_heat: float      # Total room W generated
    slice_internal_heat: float           # W in 1m 2D slice
    ventilation_heat_loss: float         # Watts dumped via airflow in 1m slice
    envelope_heat_loss: float            # Watts conducted through walls/roof/floor in 1m slice
    
    # ANSYS Field Results
    node_numbers: np.ndarray
    x_coords: np.ndarray
    y_coords: np.ndarray
    nodal_temperatures: np.ndarray
    elem_centroids_x: np.ndarray
    elem_centroids_y: np.ndarray
    heat_flux_x: np.ndarray
    heat_flux_y: np.ndarray
    heat_flux_mag: np.ndarray
    
    # Key Temperatures
    peak_indoor_temp: float
    avg_indoor_temp: float
    min_indoor_temp: float
    indoor_overheating_delta: float      # T_indoor_avg - T_outdoor


def run_shelter_internal_heat(
    config: ShelterRoomConfig,
    existing_mapdl: Optional[Mapdl] = None,
    save_plot_path: Optional[str] = None,
    show_plot: bool = False,
    loglevel: str = "WARNING"
) -> ShelterRoomResult:
    """Executes a 2D coupled thermal simulation of a shelter envelope with internal occupant loads."""
    should_exit = False
    if existing_mapdl is None:
        mapdl = launch_mapdl(loglevel=loglevel, print_com=False)
        should_exit = True
    else:
        mapdl = existing_mapdl

    try:
        tw = config.wall_thickness
        rw = config.room_width
        rh = config.room_height
        total_w = rw + 2 * tw
        total_h = rh + 2 * tw
        
        # 1. Internal Heat Load per 1-meter slice
        total_room_heat = (config.occupant_count * config.heat_per_occupant) + config.equipment_heat
        slice_heat = total_room_heat / config.room_length # W per 1m depth
        room_area_2d = rw * rh # m²
        
        # Ventilation Capacity: H_vent = ACH * Volume * rho_air * Cp / 3600
        # rho*Cp = 1206 J/m³·K -> 1206 / 3600 = 0.335 W/K per m³
        h_vent_conductance = (config.air_change_rate * room_area_2d * 1206.0) / 3600.0 # W/K per m depth
        
        # Total envelope conductance estimation for 1m slice:
        # Perimeter = 2*rw + 2*rh = 2*(3.0 + 2.4) = 10.8 m
        # U_wall ~ 1 / (1/h_out + tw/k + 1/h_in)
        r_wall_1d = (1.0 / config.h_outdoor) + (tw / config.wall_conductivity) + (1.0 / 7.7)
        u_wall_1d = 1.0 / r_wall_1d
        h_envelope = u_wall_1d * (2.0 * rw + 2.0 * rh) # W/K
        
        # Analytical expected indoor equilibrium temperature:
        delta_t_eq = slice_heat / (h_envelope + h_vent_conductance)
        q_vent_theo = h_vent_conductance * delta_t_eq
        q_env_theo = slice_heat - q_vent_theo
        
        # Net volumetric generation inside air after ventilation extraction:
        effective_volumetric_hgen = (slice_heat - q_vent_theo) / room_area_2d

        # 2. Reset and Preprocessor
        mapdl.clear()
        mapdl.prep7()
        mapdl.et(1, config.element_type)

        # Materials:
        # Material 1: Envelope (Solid Walls, Roof, Floor)
        mapdl.mp("KXX", 1, config.wall_conductivity)
        
        # Material 2: Indoor Air Domain (Effective circulation conductivity k ~ 0.5 W/m·K)
        mapdl.mp("KXX", 2, 0.50)

        # 3. Geometry Construction
        # Floor: X in [0, total_w], Y in [0, tw]
        mapdl.blc4(0, 0, total_w, tw)
        # Left wall: X in [0, tw], Y in [tw, rh]
        mapdl.blc4(0, tw, tw, rh)
        # Right wall: X in [tw + rw, tw], Y in [tw, rh]
        mapdl.blc4(tw + rw, tw, tw, rh)
        # Roof: X in [0, total_w], Y in [tw + rh, tw]
        mapdl.blc4(0, tw + rh, total_w, tw)
        # Indoor Air Volume: X in [tw, rw], Y in [tw, rh]
        mapdl.blc4(tw, tw, rw, rh)

        mapdl.aglue("ALL")

        # 4. Material Attribute Assignment
        # Select indoor air domain area (centered at total_w/2, total_h/2)
        mid_x = total_w / 2.0
        mid_y = total_h / 2.0
        mapdl.asel("S", "LOC", "X", mid_x - rw/4.0, mid_x + rw/4.0)
        mapdl.asel("R", "LOC", "Y", mid_y - rh/4.0, mid_y + rh/4.0)
        mapdl.aatt(mat=2, real=1, type=1)

        # Select all remaining areas (envelope) and assign Material 1
        mapdl.asel("INVE")
        mapdl.aatt(mat=1, real=1, type=1)
        mapdl.allsel()

        # 5. Meshing
        mapdl.esize(config.mesh_size)
        mapdl.amesh("ALL")

        # 6. Apply Volumetric Heat Generation to indoor air elements (MAT = 2)
        mapdl.esel("S", "MAT", "", 2)
        mapdl.bfe("ALL", "HGEN", 1, max(0.1, effective_volumetric_hgen))
        mapdl.allsel()

        # 7. Boundary Conditions
        # Bottom ground boundary: Y = 0 (ground heat sink)
        mapdl.nsel("S", "LOC", "Y", 0)
        mapdl.d("ALL", "TEMP", config.ground_temp)

        # Exterior Left wall: X = 0 (Outdoor convection)
        mapdl.nsel("S", "LOC", "X", 0)
        mapdl.sf("ALL", "CONV", config.h_outdoor, config.outdoor_ambient_temp)

        # Exterior Right wall: X = total_w (Outdoor convection)
        mapdl.nsel("S", "LOC", "X", total_w)
        mapdl.sf("ALL", "CONV", config.h_outdoor, config.outdoor_ambient_temp)

        # Exterior Roof: Y = total_h (Outdoor convection + Solar Sol-Air boost)
        sol_air_roof = config.outdoor_ambient_temp + (config.solar_flux_roof / config.h_outdoor)
        mapdl.nsel("S", "LOC", "Y", total_h)
        mapdl.sf("ALL", "CONV", config.h_outdoor, sol_air_roof)

        mapdl.allsel()

        # 8. Solve
        mapdl.finish()
        mapdl.slashsolu()
        mapdl.antype("STATIC")
        mapdl.solve()
        mapdl.finish()

        # 9. Post-Processing
        mapdl.post1()
        mapdl.set("LAST")

        nodal_temps = mapdl.post_processing.nodal_temperature()
        nodes = mapdl.mesh.nodes
        x_coords = nodes[:, 0]
        y_coords = nodes[:, 1]
        node_numbers = mapdl.mesh.nnum

        q_x = mapdl.post_processing.element_values("TF", "X")
        q_y = mapdl.post_processing.element_values("TF", "Y")
        q_sum = np.sqrt(q_x**2 + q_y**2)

        cell_centers = mapdl.mesh.grid.cell_centers().points
        elem_x = cell_centers[:, 0]
        elem_y = cell_centers[:, 1]

        # Indoor core temperature statistics
        indoor_mask = (
            (x_coords >= tw + 0.05) & (x_coords <= total_w - tw - 0.05) &
            (y_coords >= tw + 0.05) & (y_coords <= total_h - tw - 0.05)
        )
        indoor_temps = nodal_temps[indoor_mask]
        
        peak_t_in = float(np.max(indoor_temps))
        avg_t_in = float(np.mean(indoor_temps))
        min_t_in = float(np.min(indoor_temps))
        overheating_delta = avg_t_in - config.outdoor_ambient_temp

        result = ShelterRoomResult(
            config=config,
            total_room_internal_heat=total_room_heat,
            slice_internal_heat=slice_heat,
            ventilation_heat_loss=q_vent_theo,
            envelope_heat_loss=q_env_theo,
            node_numbers=node_numbers,
            x_coords=x_coords,
            y_coords=y_coords,
            nodal_temperatures=nodal_temps,
            elem_centroids_x=elem_x,
            elem_centroids_y=elem_y,
            heat_flux_x=q_x,
            heat_flux_y=q_y,
            heat_flux_mag=q_sum,
            peak_indoor_temp=peak_t_in,
            avg_indoor_temp=avg_t_in,
            min_indoor_temp=min_t_in,
            indoor_overheating_delta=overheating_delta
        )

        if save_plot_path or show_plot:
            _generate_shelter_visualization(result, save_plot_path, show_plot)

        return result

    finally:
        if should_exit:
            mapdl.exit()


def _generate_shelter_visualization(result: ShelterRoomResult, save_path: Optional[str] = None, show: bool = False):
    """Generates dual-panel plot: 2D Shelter Temperature Contours & 2D Vector Quivers."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))
    cfg = result.config
    tw = cfg.wall_thickness
    total_w = cfg.room_width + 2 * tw
    total_h = cfg.room_height + 2 * tw

    sc1 = ax1.scatter(
        result.x_coords,
        result.y_coords,
        c=result.nodal_temperatures,
        cmap="coolwarm",
        s=25,
        edgecolors="none"
    )
    cbar1 = plt.colorbar(sc1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("Temperature (°C)", fontsize=10)
    
    ax1.plot([tw, total_w - tw, total_w - tw, tw, tw], [tw, tw, total_h - tw, total_h - tw, tw], "k--", linewidth=1.2, label="Inner Wall Boundary")
    ax1.plot([0, total_w, total_w, 0, 0], [0, 0, total_h, total_h, 0], "k-", linewidth=1.5, label="Outer Envelope")
    
    ax1.annotate(
        f"Occupants: {cfg.occupant_count} Pers ({result.total_room_internal_heat:.0f} W)\nSlice Heat = {result.slice_internal_heat:.0f} W\nAvg T_in = {result.avg_indoor_temp:.1f}°C",
        xy=(total_w / 2.0, total_h / 2.0),
        ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.85, edgecolor="black"),
        fontsize=9, fontweight="bold"
    )

    ax1.set_title(
        f"Shelter 2D Temperature Field (T_out = {cfg.outdoor_ambient_temp}°C, ACH = {cfg.air_change_rate})",
        fontsize=11, fontweight="bold"
    )
    ax1.set_xlabel("Width X (m)", fontsize=10)
    ax1.set_ylabel("Height Y (m)", fontsize=10)
    ax1.set_aspect("equal")
    ax1.grid(True, linestyle=":", alpha=0.5)

    sc2 = ax2.scatter(
        result.elem_centroids_x,
        result.elem_centroids_y,
        c=result.heat_flux_mag,
        cmap="inferno",
        s=30,
        alpha=0.5
    )
    
    quiv = ax2.quiver(
        result.elem_centroids_x,
        result.elem_centroids_y,
        result.heat_flux_x,
        result.heat_flux_y,
        color="black",
        angles="xy",
        scale_units="xy",
        scale=250,
        width=0.003,
        headwidth=3.5,
        headlength=4.5
    )
    cbar2 = plt.colorbar(sc2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label("Heat Flux Magnitude |q| (W/m²)", fontsize=10)

    ax2.set_title(
        f"Heat Flow Vectors & Dissipation Paths\n(Envelope Loss = {result.envelope_heat_loss:.1f} W, Vent Loss = {result.ventilation_heat_loss:.1f} W)",
        fontsize=11, fontweight="bold"
    )
    ax2.set_xlabel("Width X (m)", fontsize=10)
    ax2.set_ylabel("Height Y (m)", fontsize=10)
    ax2.set_aspect("equal")
    ax2.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"Internal heat plot saved to: {save_path}")

    if show:
        plt.show()

    plt.close(fig)
