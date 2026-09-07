"""
Convective Thermal Wall Simulation Module using PyMAPDL.
Simulates heat transfer through building walls with realistic convective (Robin)
boundary conditions (outdoor wind film and indoor still air film), calculates
film resistances, U-values, and surface temperature depressions.
"""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import matplotlib.pyplot as plt
from ansys.mapdl.core import launch_mapdl, Mapdl


@dataclass
class LayerSpec:
    """Specification for a single material layer."""
    name: str
    thickness: float            # meters
    thermal_conductivity: float # W/(m·K)


@dataclass
class ConvectionWallConfig:
    """Configuration for a wall with convective boundary conditions."""
    layers: List[LayerSpec]
    height: float = 0.2                  # Height in meters
    outdoor_ambient_temp: float = 42.0   # T_inf,out in °C
    indoor_ambient_temp: float = 26.0    # T_inf,in in °C
    h_outdoor: float = 20.0              # Outdoor film coefficient in W/(m²·K)
    h_indoor: float = 7.7                # Indoor film coefficient in W/(m²·K)
    mesh_size: float = 0.005             # Element size in meters
    element_type: str = "PLANE77"


@dataclass
class ConvectionWallResult:
    """Results from convective thermal wall simulation."""
    config: ConvectionWallConfig
    total_thickness: float
    r_film_out: float                    # m²·K/W
    r_wall: float                        # m²·K/W
    r_film_in: float                     # m²·K/W
    r_total: float                       # m²·K/W
    u_value: float                       # W/(m²·K)
    theoretical_heat_flux: float         # W/m²
    theoretical_surf_temp_out: float     # °C
    theoretical_surf_temp_in: float      # °C
    node_numbers: np.ndarray
    x_coords: np.ndarray
    y_coords: np.ndarray
    nodal_temperatures: np.ndarray
    elem_centroids_x: np.ndarray
    elem_centroids_y: np.ndarray
    heat_flux_x: np.ndarray
    heat_flux_y: np.ndarray
    heat_flux_mag: np.ndarray
    simulated_avg_heat_flux_x: float
    simulated_surf_temp_out: float
    simulated_surf_temp_in: float
    relative_error_percent: float


def run_convection_wall(
    config: ConvectionWallConfig,
    existing_mapdl: Optional[Mapdl] = None,
    save_plot_path: Optional[str] = None,
    show_plot: bool = False,
    loglevel: str = "WARNING"
) -> ConvectionWallResult:
    """Executes a 2D convective thermal simulation on a layered wall."""
    should_exit = False
    if existing_mapdl is None:
        mapdl = launch_mapdl(loglevel=loglevel, print_com=False)
        should_exit = True
    else:
        mapdl = existing_mapdl

    try:
        total_thickness = sum(layer.thickness for layer in config.layers)
        r_film_out = 1.0 / config.h_outdoor
        r_wall_layers = [layer.thickness / layer.thermal_conductivity for layer in config.layers]
        r_wall = sum(r_wall_layers)
        r_film_in = 1.0 / config.h_indoor
        r_total = r_film_out + r_wall + r_film_in
        u_val = 1.0 / r_total
        
        delta_t_air = config.outdoor_ambient_temp - config.indoor_ambient_temp
        theo_q = u_val * delta_t_air
        theo_t_surf_out = config.outdoor_ambient_temp - theo_q * r_film_out
        theo_t_surf_in = config.indoor_ambient_temp + theo_q * r_film_in

        mapdl.clear()
        mapdl.prep7()
        mapdl.et(1, config.element_type)

        layer_x_mids = []
        x_cursor = 0.0
        for idx, layer in enumerate(config.layers, start=1):
            mapdl.mp("KXX", idx, layer.thermal_conductivity)
            layer_x_mids.append(x_cursor + layer.thickness / 2.0)
            mapdl.blc4(x_cursor, 0, layer.thickness, config.height)
            x_cursor += layer.thickness

        if len(config.layers) > 1:
            mapdl.aglue("ALL")
            for idx, (layer, x_mid) in enumerate(zip(config.layers, layer_x_mids), start=1):
                mapdl.asel("S", "LOC", "X", x_mid)
                mapdl.aatt(mat=idx, real=1, type=1)
                mapdl.allsel()
        else:
            mapdl.aatt(mat=1, real=1, type=1)

        mapdl.esize(config.mesh_size)
        mapdl.amesh("ALL")

        # Apply Convective Boundary Conditions
        mapdl.nsel("S", "LOC", "X", 0)
        mapdl.sf("ALL", "CONV", config.h_outdoor, config.outdoor_ambient_temp)

        mapdl.nsel("S", "LOC", "X", total_thickness)
        mapdl.sf("ALL", "CONV", config.h_indoor, config.indoor_ambient_temp)

        mapdl.allsel()

        mapdl.finish()
        mapdl.slashsolu()
        mapdl.antype("STATIC")
        mapdl.solve()
        mapdl.finish()

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

        surf_out_mask = np.isclose(x_coords, 0.0, atol=1e-5)
        surf_in_mask = np.isclose(x_coords, total_thickness, atol=1e-5)
        sim_t_surf_out = float(np.mean(nodal_temps[surf_out_mask]))
        sim_t_surf_in = float(np.mean(nodal_temps[surf_in_mask]))

        sim_avg_qx = float(np.mean(q_x))
        error_pct = abs(sim_avg_qx - theo_q) / theo_q * 100.0 if theo_q != 0 else 0.0

        result = ConvectionWallResult(
            config=config,
            total_thickness=total_thickness,
            r_film_out=r_film_out,
            r_wall=r_wall,
            r_film_in=r_film_in,
            r_total=r_total,
            u_value=u_val,
            theoretical_heat_flux=theo_q,
            theoretical_surf_temp_out=theo_t_surf_out,
            theoretical_surf_temp_in=theo_t_surf_in,
            node_numbers=node_numbers,
            x_coords=x_coords,
            y_coords=y_coords,
            nodal_temperatures=nodal_temps,
            elem_centroids_x=elem_x,
            elem_centroids_y=elem_y,
            heat_flux_x=q_x,
            heat_flux_y=q_y,
            heat_flux_mag=q_sum,
            simulated_avg_heat_flux_x=sim_avg_qx,
            simulated_surf_temp_out=sim_t_surf_out,
            simulated_surf_temp_in=sim_t_surf_in,
            relative_error_percent=error_pct
        )

        if save_plot_path or show_plot:
            _generate_convection_visualization(result, save_plot_path, show_plot)

        return result

    finally:
        if should_exit:
            mapdl.exit()


def _generate_convection_visualization(result: ConvectionWallResult, save_path: Optional[str] = None, show: bool = False):
    """Generates dual-panel plot: 2D Temperature Field & 1D Temperature Profile with Boundary Air Films."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7.5))

    sc = ax1.scatter(
        result.x_coords,
        result.y_coords,
        c=result.nodal_temperatures,
        cmap="coolwarm",
        s=30,
        edgecolors="none"
    )
    cbar1 = plt.colorbar(sc, ax=ax1, fraction=0.035, pad=0.03)
    cbar1.set_label("Temperature (°C)", fontsize=10)

    x_accum = 0.0
    for idx, layer in enumerate(result.config.layers):
        x_accum += layer.thickness
        if idx < len(result.config.layers) - 1:
            ax1.axvline(x=x_accum, color="black", linestyle="--", linewidth=1.0, alpha=0.7)
        x_mid = x_accum - layer.thickness / 2.0
        ax1.text(
            x_mid, result.config.height * 0.85,
            f"{layer.name}\nk={layer.thermal_conductivity}",
            ha="center", va="center", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85, edgecolor="gray")
        )

    ax1.set_title(
        f"2D Temperature Distribution with Convective Boundaries (h_out={result.config.h_outdoor}, h_in={result.config.h_indoor} W/m²·K)",
        fontsize=11, fontweight="bold"
    )
    ax1.set_ylabel("Height Y (m)", fontsize=10)
    ax1.set_aspect("equal")
    ax1.grid(True, linestyle=":", alpha=0.5)

    mid_y = result.config.height / 2.0
    tol = result.config.mesh_size * 0.6
    mask = np.abs(result.y_coords - mid_y) <= tol
    
    sorted_idx = np.argsort(result.x_coords[mask])
    sampled_x = result.x_coords[mask][sorted_idx]
    sampled_t = result.nodal_temperatures[mask][sorted_idx]

    ax2.plot(sampled_x, sampled_t, "b-", linewidth=2.2, label="Solid Wall Temperature Profile")

    x_air_out = -0.04
    ax2.plot([x_air_out, 0.0], [result.config.outdoor_ambient_temp, result.simulated_surf_temp_out], "r--", linewidth=1.5, label="Outdoor Air Film (h_out)")
    ax2.plot([x_air_out], [result.config.outdoor_ambient_temp], "rs", markersize=7)
    ax2.annotate(f"Outdoor Air\nT_inf = {result.config.outdoor_ambient_temp}°C", xy=(x_air_out, result.config.outdoor_ambient_temp), xytext=(-10, 10), textcoords="offset points", ha="right", fontsize=8.5, color="darkred")

    x_air_in = result.total_thickness + 0.04
    ax2.plot([result.total_thickness, x_air_in], [result.simulated_surf_temp_in, result.config.indoor_ambient_temp], "g--", linewidth=1.5, label="Indoor Air Film (h_in)")
    ax2.plot([x_air_in], [result.config.indoor_ambient_temp], "gs", markersize=7)
    ax2.annotate(f"Indoor Air\nT_inf = {result.config.indoor_ambient_temp}°C", xy=(x_air_in, result.config.indoor_ambient_temp), xytext=(10, 10), textcoords="offset points", ha="left", fontsize=8.5, color="darkgreen")

    ax2.plot(0.0, result.simulated_surf_temp_out, "ro", markersize=6)
    ax2.annotate(f"T_surf,out = {result.simulated_surf_temp_out:.2f}°C", xy=(0.0, result.simulated_surf_temp_out), xytext=(5, -15), textcoords="offset points", fontsize=8.5, fontweight="bold")

    ax2.plot(result.total_thickness, result.simulated_surf_temp_in, "go", markersize=6)
    ax2.annotate(f"T_surf,in = {result.simulated_surf_temp_in:.2f}°C", xy=(result.total_thickness, result.simulated_surf_temp_in), xytext=(-10, 12), textcoords="offset points", ha="right", fontsize=8.5, fontweight="bold")

    ax2.set_title(
        f"Convective Resistance Network (Simulated q = {result.simulated_avg_heat_flux_x:.2f} W/m², "
        f"Total R = {result.r_total:.4f} m²·K/W, U = {result.u_value:.3f} W/m²·K, Error = {result.relative_error_percent:.4f}%)",
        fontsize=11, fontweight="bold"
    )
    ax2.set_xlabel("Wall Thickness X (m)", fontsize=10)
    ax2.set_ylabel("Temperature (°C)", fontsize=10)
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)
