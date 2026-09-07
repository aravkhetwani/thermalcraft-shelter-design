"""
Multi-Layer Composite Thermal Wall Simulation Module using PyMAPDL.
Simulates heat conduction in series across layered building materials,
calculates R-values, U-values, and validates interface temperature steps.
"""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import matplotlib.pyplot as plt
from ansys.mapdl.core import launch_mapdl, Mapdl


@dataclass
class LayerConfig:
    """Specification for a single material layer."""
    name: str
    thickness: float            # meters
    thermal_conductivity: float # W/(m·K)


@dataclass
class CompositeWallConfig:
    """Configuration for a multi-layer composite wall."""
    layers: List[LayerConfig]
    height: float = 0.2               # Height in meters
    outside_temperature: float = 42.0 # Temperature at X = 0 (°C)
    inside_temperature: float = 26.0  # Temperature at X = total_width (°C)
    mesh_size: float = 0.01           # Mesh size in meters
    element_type: str = "PLANE77"


@dataclass
class CompositeWallResult:
    """Results from composite wall simulation."""
    config: CompositeWallConfig
    total_thickness: float
    r_values: List[float]             # R-value for each layer (m²·K/W)
    total_r_value: float              # Total R-value (m²·K/W)
    u_value: float                    # Thermal transmittance U (W/m²·K)
    theoretical_heat_flux: float      # Theoretical heat flux q (W/m²)
    theoretical_interface_temps: List[float] # Temperatures at interfaces (°C)
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
    relative_error_percent: float


def run_composite_wall(
    config: CompositeWallConfig,
    existing_mapdl: Optional[Mapdl] = None,
    save_plot_path: Optional[str] = None,
    show_plot: bool = False,
    loglevel: str = "WARNING"
) -> CompositeWallResult:
    """Executes a multi-layer composite wall thermal conduction simulation."""
    should_exit = False
    if existing_mapdl is None:
        mapdl = launch_mapdl(loglevel=loglevel, print_com=False)
        should_exit = True
    else:
        mapdl = existing_mapdl

    try:
        total_thickness = sum(layer.thickness for layer in config.layers)
        delta_t = config.outside_temperature - config.inside_temperature
        
        r_values = [layer.thickness / layer.thermal_conductivity for layer in config.layers]
        total_r = sum(r_values)
        u_value = 1.0 / total_r if total_r > 0 else 0.0
        theoretical_q = u_value * delta_t
        
        interface_temps = [config.outside_temperature]
        curr_t = config.outside_temperature
        for r_i in r_values:
            curr_t -= theoretical_q * r_i
            interface_temps.append(curr_t)

        mapdl.clear()
        mapdl.prep7()
        mapdl.et(1, config.element_type)

        layer_x_starts = []
        layer_x_mids = []
        x_cursor = 0.0
        
        for idx, layer in enumerate(config.layers, start=1):
            mapdl.mp("KXX", idx, layer.thermal_conductivity)
            layer_x_starts.append(x_cursor)
            layer_x_mids.append(x_cursor + layer.thickness / 2.0)
            mapdl.blc4(x_cursor, 0, layer.thickness, config.height)
            x_cursor += layer.thickness

        mapdl.aglue("ALL")

        for idx, (layer, x_mid) in enumerate(zip(config.layers, layer_x_mids), start=1):
            mapdl.asel("S", "LOC", "X", x_mid)
            mapdl.aatt(mat=idx, real=1, type=1)
            mapdl.allsel()

        mapdl.esize(config.mesh_size)
        mapdl.amesh("ALL")

        mapdl.nsel("S", "LOC", "X", 0)
        mapdl.d("ALL", "TEMP", config.outside_temperature)

        mapdl.nsel("S", "LOC", "X", total_thickness)
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

        sim_avg_qx = float(np.mean(q_x))
        error_pct = abs(sim_avg_qx - theoretical_q) / theoretical_q * 100.0 if theoretical_q != 0 else 0.0

        result = CompositeWallResult(
            config=config,
            total_thickness=total_thickness,
            r_values=r_values,
            total_r_value=total_r,
            u_value=u_value,
            theoretical_heat_flux=theoretical_q,
            theoretical_interface_temps=interface_temps,
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
            relative_error_percent=error_pct
        )

        if save_plot_path or show_plot:
            _generate_composite_visualization(result, save_plot_path, show_plot)

        return result

    finally:
        if should_exit:
            mapdl.exit()


def _generate_composite_visualization(result: CompositeWallResult, save_path: Optional[str] = None, show: bool = False):
    """Generates dual-panel plot: 2D Composite Temperature Field & 1D Layer Temperature Drop Profile."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7))

    sc = ax1.scatter(
        result.x_coords,
        result.y_coords,
        c=result.nodal_temperatures,
        cmap="coolwarm",
        s=35,
        edgecolors="none"
    )
    cbar1 = plt.colorbar(sc, ax=ax1, fraction=0.035, pad=0.03)
    cbar1.set_label("Temperature (°C)", fontsize=10)

    x_accum = 0.0
    for idx, layer in enumerate(result.config.layers):
        x_accum += layer.thickness
        if idx < len(result.config.layers) - 1:
            ax1.axvline(x=x_accum, color="black", linestyle="--", linewidth=1.2, alpha=0.8)
        x_mid = x_accum - layer.thickness / 2.0
        ax1.text(
            x_mid, result.config.height * 0.85,
            f"{layer.name}\nk={layer.thermal_conductivity}",
            ha="center", va="center", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85, edgecolor="gray")
        )

    ax1.set_title(
        f"Multi-Layer Composite Wall 2D Temperature Field (Total R = {result.total_r_value:.3f} m²·K/W, U = {result.u_value:.3f} W/m²·K)",
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

    ax2.plot(sampled_x, sampled_t, "b.-", label="ANSYS Simulated Profile", linewidth=2.0, markersize=5)

    x_interfaces = [0.0]
    acc = 0.0
    for layer in result.config.layers:
        acc += layer.thickness
        x_interfaces.append(acc)

    ax2.plot(
        x_interfaces, result.theoretical_interface_temps,
        "ro", markersize=8, label="Theoretical Interface Steps", zorder=5
    )

    for x_pos, t_val in zip(x_interfaces, result.theoretical_interface_temps):
        ax2.annotate(
            f"{t_val:.1f}°C",
            xy=(x_pos, t_val),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center", fontsize=8.5, fontweight="bold", color="darkred"
        )

    for x_int in x_interfaces[1:-1]:
        ax2.axvline(x=x_int, color="gray", linestyle="--", linewidth=1.0, alpha=0.7)

    ax2.set_title(
        f"1D Temperature Drop Across Layers (Simulated q = {result.simulated_avg_heat_flux_x:.3f} W/m², "
        f"Theoretical q = {result.theoretical_heat_flux:.3f} W/m², Error = {result.relative_error_percent:.4f}%)",
        fontsize=11, fontweight="bold"
    )
    ax2.set_xlabel("Wall Thickness X (m)", fontsize=10)
    ax2.set_ylabel("Temperature (°C)", fontsize=10)
    ax2.legend(loc="best", fontsize=9.5)
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)
