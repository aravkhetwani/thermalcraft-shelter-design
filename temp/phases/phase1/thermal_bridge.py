"""
2D Geometric Thermal Bridge Simulation Module using PyMAPDL.
Models L-shaped corner junctions to demonstrate 2D heat flux vector divergence,
corner heat leaks, and local thermal flux concentration.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
from ansys.mapdl.core import launch_mapdl, Mapdl


@dataclass
class CornerBridgeConfig:
    """Configuration for an L-shaped corner thermal bridge."""
    arm_length_x: float = 0.8         # Horizontal arm outer length (m)
    arm_length_y: float = 0.8         # Vertical arm outer length (m)
    wall_thickness: float = 0.25      # Wall thickness (m)
    thermal_conductivity: float = 0.8 # Material conductivity k in W/(m·K)
    outside_temperature: float = 42.0 # Temperature on outer faces (°C)
    inside_temperature: float = 26.0  # Temperature on inner faces (°C)
    mesh_size: float = 0.025          # Mesh element size (m)
    element_type: str = "PLANE77"


@dataclass
class CornerBridgeResult:
    """Results from corner thermal bridge simulation."""
    config: CornerBridgeConfig
    node_numbers: np.ndarray
    x_coords: np.ndarray
    y_coords: np.ndarray
    nodal_temperatures: np.ndarray
    elem_centroids_x: np.ndarray
    elem_centroids_y: np.ndarray
    heat_flux_x: np.ndarray
    heat_flux_y: np.ndarray
    heat_flux_mag: np.ndarray
    min_temperature: float
    max_temperature: float
    max_heat_flux: float
    nominal_1d_heat_flux: float
    corner_flux_concentration_ratio: float


def run_corner_bridge(
    config: CornerBridgeConfig,
    existing_mapdl: Optional[Mapdl] = None,
    save_plot_path: Optional[str] = None,
    show_plot: bool = False,
    loglevel: str = "WARNING"
) -> CornerBridgeResult:
    """Executes a 2D L-shaped corner thermal bridge simulation."""
    should_exit = False
    if existing_mapdl is None:
        mapdl = launch_mapdl(loglevel=loglevel, print_com=False)
        should_exit = True
    else:
        mapdl = existing_mapdl

    try:
        delta_t = config.outside_temperature - config.inside_temperature
        nominal_1d_q = config.thermal_conductivity * (delta_t / config.wall_thickness)

        mapdl.clear()
        mapdl.prep7()
        mapdl.et(1, config.element_type)
        mapdl.mp("KXX", 1, config.thermal_conductivity)

        mapdl.blc4(0, 0, config.arm_length_x, config.wall_thickness)
        mapdl.blc4(0, config.wall_thickness, config.wall_thickness, config.arm_length_y - config.wall_thickness)

        mapdl.aglue("ALL")

        mapdl.esize(config.mesh_size)
        mapdl.amesh("ALL")

        mapdl.nsel("S", "LOC", "Y", 0)
        mapdl.nsel("A", "LOC", "X", 0)
        mapdl.d("ALL", "TEMP", config.outside_temperature)

        mapdl.nsel("S", "LOC", "Y", config.wall_thickness)
        mapdl.nsel("R", "LOC", "X", config.wall_thickness, config.arm_length_x)
        mapdl.d("ALL", "TEMP", config.inside_temperature)

        mapdl.nsel("S", "LOC", "X", config.wall_thickness)
        mapdl.nsel("R", "LOC", "Y", config.wall_thickness, config.arm_length_y)
        mapdl.d("ALL", "TEMP", config.inside_temperature)

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

        max_q = float(np.max(q_sum))
        concentration_ratio = max_q / nominal_1d_q if nominal_1d_q > 0 else 1.0

        result = CornerBridgeResult(
            config=config,
            node_numbers=node_numbers,
            x_coords=x_coords,
            y_coords=y_coords,
            nodal_temperatures=nodal_temps,
            elem_centroids_x=elem_x,
            elem_centroids_y=elem_y,
            heat_flux_x=q_x,
            heat_flux_y=q_y,
            heat_flux_mag=q_sum,
            min_temperature=float(np.min(nodal_temps)),
            max_temperature=float(np.max(nodal_temps)),
            max_heat_flux=max_q,
            nominal_1d_heat_flux=nominal_1d_q,
            corner_flux_concentration_ratio=concentration_ratio
        )

        if save_plot_path or show_plot:
            _generate_corner_visualization(result, save_plot_path, show_plot)

        return result

    finally:
        if should_exit:
            mapdl.exit()


def _generate_corner_visualization(result: CornerBridgeResult, save_path: Optional[str] = None, show: bool = False):
    """Generates dual-panel plot: 2D Temperature Field & 2D Heat Flux Quiver with Corner Convergence."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    sc1 = ax1.scatter(
        result.x_coords,
        result.y_coords,
        c=result.nodal_temperatures,
        cmap="coolwarm",
        s=30,
        edgecolors="none"
    )
    cbar1 = plt.colorbar(sc1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("Temperature (°C)", fontsize=10)
    ax1.set_title(
        f"2D Corner Temperature Field (T_out = {result.config.outside_temperature}°C, T_in = {result.config.inside_temperature}°C)",
        fontsize=11, fontweight="bold"
    )
    ax1.set_xlabel("X Position (m)", fontsize=10)
    ax1.set_ylabel("Y Position (m)", fontsize=10)
    ax1.set_aspect("equal")
    ax1.grid(True, linestyle=":", alpha=0.5)

    tw = result.config.wall_thickness
    ax1.plot(tw, tw, "ko", markersize=6)
    ax1.annotate("Inner Corner\n(Thermal Bridge)", xy=(tw, tw), xytext=(tw + 0.12, tw + 0.12),
                 arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=5),
                 fontsize=8.5, fontweight="bold")

    sc2 = ax2.scatter(
        result.elem_centroids_x,
        result.elem_centroids_y,
        c=result.heat_flux_mag,
        cmap="inferno",
        s=40,
        alpha=0.6
    )
    
    quiv = ax2.quiver(
        result.elem_centroids_x,
        result.elem_centroids_y,
        result.heat_flux_x,
        result.heat_flux_y,
        color="black",
        angles="xy",
        scale_units="xy",
        scale=300,
        width=0.004,
        headwidth=3.5,
        headlength=4.5
    )
    cbar2 = plt.colorbar(sc2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label("Heat Flux Magnitude |q| (W/m²)", fontsize=10)
    
    ax2.set_title(
        f"Heat Flux Vectors & 2D Divergence\n(Peak Flux = {result.max_heat_flux:.1f} W/m² vs 1D Nominal = {result.nominal_1d_heat_flux:.1f} W/m², Ratio = {result.corner_flux_concentration_ratio:.2f}×)",
        fontsize=11, fontweight="bold"
    )
    ax2.set_xlabel("X Position (m)", fontsize=10)
    ax2.set_ylabel("Y Position (m)", fontsize=10)
    ax2.set_aspect("equal")
    ax2.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)
