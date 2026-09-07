"""
Parametric 2D Thermal Wall Simulation Module using PyMAPDL.
Solves steady-state thermal conduction and extracts both temperature and heat flux vector fields.
"""

from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional
from ansys.mapdl.core import launch_mapdl, Mapdl


@dataclass
class WallSimulationConfig:
    """Configuration parameters for 2D parametric thermal wall simulation."""
    width: float = 1.0                # Wall thickness (m) in X
    height: float = 0.2               # Wall height (m) in Y
    thermal_conductivity: float = 0.8 # Thermal conductivity k in W/(m·K)
    outside_temperature: float = 40.0 # Boundary temperature at X=0 (°C)
    inside_temperature: float = 25.0  # Boundary temperature at X=width (°C)
    mesh_size: float = 0.05           # Element size (m)
    element_type: str = "PLANE77"     # 2D 8-node thermal solid element


@dataclass
class WallSimulationResult:
    """Results extracted from the thermal wall simulation."""
    config: WallSimulationConfig
    node_numbers: np.ndarray
    x_coords: np.ndarray
    y_coords: np.ndarray
    nodal_temperatures: np.ndarray
    elem_centroids_x: np.ndarray
    elem_centroids_y: np.ndarray
    heat_flux_x: np.ndarray  # W/m^2 (q_x)
    heat_flux_y: np.ndarray  # W/m^2 (q_y)
    heat_flux_mag: np.ndarray # W/m^2 (|q|)
    min_temperature: float = 0.0
    max_temperature: float = 0.0
    avg_temperature: float = 0.0
    theoretical_heat_flux: float = 0.0
    simulated_avg_heat_flux_x: float = 0.0
    relative_error_percent: float = 0.0


def run_parametric_wall(
    config: WallSimulationConfig,
    existing_mapdl: Optional[Mapdl] = None,
    save_plot_path: Optional[str] = None,
    show_plot: bool = False,
    loglevel: str = "WARNING"
) -> WallSimulationResult:
    """Executes a steady-state 2D thermal conduction simulation on a wall."""
    should_exit = False
    if existing_mapdl is None:
        mapdl = launch_mapdl(loglevel=loglevel, print_com=False)
        should_exit = True
    else:
        mapdl = existing_mapdl

    try:
        mapdl.clear()
        mapdl.prep7()
        mapdl.et(1, config.element_type)
        mapdl.mp("KXX", 1, config.thermal_conductivity)
        mapdl.blc4(0, 0, config.width, config.height)

        mapdl.esize(config.mesh_size)
        mapdl.amesh("ALL")

        # Boundary Conditions
        mapdl.nsel("S", "LOC", "X", 0)
        mapdl.d("ALL", "TEMP", config.outside_temperature)

        mapdl.nsel("S", "LOC", "X", config.width)
        mapdl.d("ALL", "TEMP", config.inside_temperature)
        mapdl.allsel()

        # Solve
        mapdl.finish()
        mapdl.slashsolu()
        mapdl.antype("STATIC")
        mapdl.solve()
        mapdl.finish()

        # Post-Processing
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

        delta_t = config.outside_temperature - config.inside_temperature
        theoretical_q = config.thermal_conductivity * (delta_t / config.width)
        simulated_avg_qx = float(np.mean(q_x))
        error_pct = abs(simulated_avg_qx - theoretical_q) / theoretical_q * 100.0 if theoretical_q != 0 else 0.0

        result = WallSimulationResult(
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
            avg_temperature=float(np.mean(nodal_temps)),
            theoretical_heat_flux=theoretical_q,
            simulated_avg_heat_flux_x=simulated_avg_qx,
            relative_error_percent=error_pct
        )

        if save_plot_path or show_plot:
            _generate_visualization(result, save_plot_path, show_plot)

        return result

    finally:
        if should_exit:
            mapdl.exit()


def _generate_visualization(result: WallSimulationResult, save_path: Optional[str] = None, show: bool = False):
    """Generates dual-panel plot: Temperature Contours & Heat Flux Vector Field."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)

    sc = ax1.scatter(
        result.x_coords,
        result.y_coords,
        c=result.nodal_temperatures,
        cmap="coolwarm",
        s=45,
        edgecolors="none"
    )
    cbar1 = plt.colorbar(sc, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("Temperature (°C)", fontsize=10)
    ax1.set_title(
        f"2D Temperature Distribution (k = {result.config.thermal_conductivity} W/m·K, "
        f"T_out = {result.config.outside_temperature}°C, T_in = {result.config.inside_temperature}°C)",
        fontsize=11, fontweight="bold"
    )
    ax1.set_ylabel("Height Y (m)", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.set_aspect("equal")

    q_mag = result.heat_flux_mag
    quiv = ax2.quiver(
        result.elem_centroids_x,
        result.elem_centroids_y,
        result.heat_flux_x,
        result.heat_flux_y,
        q_mag,
        cmap="autumn_r",
        angles="xy",
        scale_units="xy",
        scale=None,
        width=0.005,
        headwidth=4,
        headlength=5
    )
    cbar2 = plt.colorbar(quiv, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label("Heat Flux Magnitude |q| (W/m²)", fontsize=10)
    ax2.set_title(
        f"Heat Flux Vectors (q̄_x = {result.simulated_avg_heat_flux_x:.2f} W/m², "
        f"Theoretical = {result.theoretical_heat_flux:.2f} W/m², Error = {result.relative_error_percent:.3f}%)",
        fontsize=11, fontweight="bold"
    )
    ax2.set_xlabel("Wall Thickness X (m)", fontsize=10)
    ax2.set_ylabel("Height Y (m)", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.set_aspect("equal")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)
