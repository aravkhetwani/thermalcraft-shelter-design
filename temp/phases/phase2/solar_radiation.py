"""
Solar Radiation and Sol-Air Temperature Simulation Module using PyMAPDL.
Simulates combined incident solar radiation (heat flux) and outdoor/indoor convection,
models surface solar absorptivity (albedo), and validates against the Sol-Air Temperature theory.
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
class SolarWallConfig:
    """Configuration for wall/roof under solar radiation and convection."""
    layers: List[LayerSpec]
    solar_irradiance: float = 800.0      # Incident solar radiation I in W/m²
    absorptivity: float = 0.85           # Solar absorptance alpha (0.0 to 1.0)
    height: float = 0.2                  # Height in meters
    outdoor_ambient_temp: float = 42.0   # T_inf,out in °C
    indoor_ambient_temp: float = 26.0    # T_inf,in in °C
    h_outdoor: float = 20.0              # Outdoor film coeff in W/(m²·K)
    h_indoor: float = 7.7                # Indoor film coeff in W/(m²·K)
    mesh_size: float = 0.005             # Mesh size in meters
    element_type: str = "PLANE77"


@dataclass
class SolarWallResult:
    """Results from solar radiation simulation."""
    config: SolarWallConfig
    total_thickness: float
    absorbed_solar_flux: float           # W/m² (alpha * I)
    sol_air_temperature: float          # °C (T_sol_air)
    r_film_out: float                    # m²·K/W
    r_wall: float                        # m²·K/W
    r_film_in: float                     # m²·K/W
    r_total: float                       # m²·K/W
    u_value: float                       # W/(m²·K)
    theoretical_heat_flux: float         # W/m²
    theoretical_surf_temp_out: float     # °C
    theoretical_surf_temp_in: float      # °C
    
    # ANSYS Results
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


def run_solar_wall(
    config: SolarWallConfig,
    existing_mapdl: Optional[Mapdl] = None,
    save_plot_path: Optional[str] = None,
    show_plot: bool = False,
    loglevel: str = "WARNING"
) -> SolarWallResult:
    """Executes a 2D thermal simulation of a wall under combined solar flux and convection."""
    should_exit = False
    if existing_mapdl is None:
        mapdl = launch_mapdl(loglevel=loglevel, print_com=False)
        should_exit = True
    else:
        mapdl = existing_mapdl

    try:
        # 1. Theoretical Sol-Air & Resistance Calculation
        total_thickness = sum(layer.thickness for layer in config.layers)
        absorbed_flux = config.absorptivity * config.solar_irradiance
        sol_air_temp = config.outdoor_ambient_temp + (absorbed_flux / config.h_outdoor)
        
        r_film_out = 1.0 / config.h_outdoor
        r_wall_layers = [layer.thickness / layer.thermal_conductivity for layer in config.layers]
        r_wall = sum(r_wall_layers)
        r_film_in = 1.0 / config.h_indoor
        r_total = r_film_out + r_wall + r_film_in
        u_val = 1.0 / r_total
        
        theo_q = u_val * (sol_air_temp - config.indoor_ambient_temp)
        theo_t_surf_out = sol_air_temp - theo_q * r_film_out
        theo_t_surf_in = config.indoor_ambient_temp + theo_q * r_film_in

        # 2. Reset and Preprocessor
        mapdl.clear()
        mapdl.prep7()
        mapdl.et(1, config.element_type)

        # 3. Create Areas and assign materials
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

        # 4. Apply Combined Solar Radiation & Convective Boundary Conditions
        # In building physics and FEA, combined solar flux (alpha*I) and outdoor convection (h_out)
        # act through the Sol-Air Temperature: T_sol_air = T_inf,out + (alpha*I / h_out)
        # Applying convection with T_sol_air exactly balances solar gain and outdoor convective dissipation.
        mapdl.nsel("S", "LOC", "X", 0)
        mapdl.sf("ALL", "CONV", config.h_outdoor, sol_air_temp)

        # Indoor Boundary: X = total_thickness
        mapdl.nsel("S", "LOC", "X", total_thickness)
        mapdl.sf("ALL", "CONV", config.h_indoor, config.indoor_ambient_temp)

        mapdl.allsel()

        # 5. Solve
        mapdl.finish()
        mapdl.slashsolu()
        mapdl.antype("STATIC")
        mapdl.solve()
        mapdl.finish()

        # 6. Post-Processing
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

        result = SolarWallResult(
            config=config,
            total_thickness=total_thickness,
            absorbed_solar_flux=absorbed_flux,
            sol_air_temperature=sol_air_temp,
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
            _generate_solar_visualization(result, save_plot_path, show_plot)

        return result

    finally:
        if should_exit:
            mapdl.exit()


def _generate_solar_visualization(result: SolarWallResult, save_path: Optional[str] = None, show: bool = False):
    """Generates dual-panel plot: 2D Temperature Field & 1D Profile with Sol-Air Temperature."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7.5))

    # Panel 1: 2D Temperature Field
    sc = ax1.scatter(
        result.x_coords,
        result.y_coords,
        c=result.nodal_temperatures,
        cmap="inferno",
        s=30,
        edgecolors="none"
    )
    cbar1 = plt.colorbar(sc, ax=ax1, fraction=0.035, pad=0.03)
    cbar1.set_label("Temperature (°C)", fontsize=10)

    x_accum = 0.0
    for idx, layer in enumerate(result.config.layers):
        x_accum += layer.thickness
        if idx < len(result.config.layers) - 1:
            ax1.axvline(x=x_accum, color="white", linestyle="--", linewidth=1.0, alpha=0.7)
        x_mid = x_accum - layer.thickness / 2.0
        ax1.text(
            x_mid, result.config.height * 0.85,
            f"{layer.name}\nk={layer.thermal_conductivity}",
            ha="center", va="center", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9, edgecolor="gray")
        )

    ax1.set_title(
        f"2D Temperature Distribution Under Solar Radiation (I={result.config.solar_irradiance} W/m², α={result.config.absorptivity}, T_sol-air={result.sol_air_temperature:.1f}°C)",
        fontsize=11, fontweight="bold"
    )
    ax1.set_ylabel("Height Y (m)", fontsize=10)
    ax1.set_aspect("equal")
    ax1.grid(True, linestyle=":", alpha=0.5)

    # Panel 2: 1D Temperature Profile with Sol-Air Concept
    mid_y = result.config.height / 2.0
    tol = result.config.mesh_size * 0.6
    mask = np.abs(result.y_coords - mid_y) <= tol
    
    sorted_idx = np.argsort(result.x_coords[mask])
    sampled_x = result.x_coords[mask][sorted_idx]
    sampled_t = result.nodal_temperatures[mask][sorted_idx]

    ax2.plot(sampled_x, sampled_t, "r-", linewidth=2.2, label="Wall Temperature Profile")

    # Plot Sol-Air Temperature
    x_air_out = -0.05
    ax2.plot([x_air_out, 0.0], [result.sol_air_temperature, result.simulated_surf_temp_out], "m--", linewidth=1.5, label="Effective Sol-Air Film")
    ax2.plot([x_air_out], [result.sol_air_temperature], "m*", markersize=10)
    ax2.annotate(f"Sol-Air Temp\nT_sol-air = {result.sol_air_temperature:.1f}°C", xy=(x_air_out, result.sol_air_temperature), xytext=(-10, 8), textcoords="offset points", ha="right", fontsize=8.5, fontweight="bold", color="purple")

    # Plot Ambient Outdoor Air Temp
    ax2.plot([x_air_out], [result.config.outdoor_ambient_temp], "ro", markersize=6)
    ax2.annotate(f"Ambient Air T = {result.config.outdoor_ambient_temp}°C\n(Solar Boost: +{result.sol_air_temperature - result.config.outdoor_ambient_temp:.1f}°C)", xy=(x_air_out, result.config.outdoor_ambient_temp), xytext=(-10, -25), textcoords="offset points", ha="right", fontsize=8, color="darkred")

    # Plot Indoor Air Film Step
    x_air_in = result.total_thickness + 0.04
    ax2.plot([result.total_thickness, x_air_in], [result.simulated_surf_temp_in, result.config.indoor_ambient_temp], "g--", linewidth=1.5, label="Indoor Air Film")
    ax2.plot([x_air_in], [result.config.indoor_ambient_temp], "gs", markersize=7)
    ax2.annotate(f"Indoor Air\nT_inf = {result.config.indoor_ambient_temp}°C", xy=(x_air_in, result.config.indoor_ambient_temp), xytext=(10, 10), textcoords="offset points", ha="left", fontsize=8.5, color="darkgreen")

    # Surface Temperatures
    ax2.plot(0.0, result.simulated_surf_temp_out, "ko", markersize=6)
    ax2.annotate(f"T_surf,out = {result.simulated_surf_temp_out:.2f}°C", xy=(0.0, result.simulated_surf_temp_out), xytext=(5, -15), textcoords="offset points", fontsize=8.5, fontweight="bold")

    ax2.plot(result.total_thickness, result.simulated_surf_temp_in, "go", markersize=6)
    ax2.annotate(f"T_surf,in = {result.simulated_surf_temp_in:.2f}°C", xy=(result.total_thickness, result.simulated_surf_temp_in), xytext=(-10, 12), textcoords="offset points", ha="right", fontsize=8.5, fontweight="bold")

    ax2.set_title(
        f"Solar Thermal Ingress (Heat Flux q = {result.simulated_avg_heat_flux_x:.2f} W/m², "
        f"Absorbed Solar Flux = {result.absorbed_solar_flux:.1f} W/m², Error = {result.relative_error_percent:.4f}%)",
        fontsize=11, fontweight="bold"
    )
    ax2.set_xlabel("Wall Thickness X (m)", fontsize=10)
    ax2.set_ylabel("Temperature (°C)", fontsize=10)
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"Solar radiation plot saved to: {save_path}")

    if show:
        plt.show()

    plt.close(fig)
