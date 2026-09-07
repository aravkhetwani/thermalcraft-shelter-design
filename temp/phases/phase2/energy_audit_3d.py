"""
3D Total Energy Balance & Surface Heat Flow Rate Audit Module using PyMAPDL and PyVista.
Computes exact thermal power in Watts across every 3D face of the shelter envelope,
verifies the First Law of Thermodynamics, and renders 3D spatial energy maps and audit charts.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv
from ansys.mapdl.core import launch_mapdl, Mapdl
from phases.phase2.heat_flow_3d import Shelter3DConfig, run_3d_shelter_simulation, Shelter3DResult


@dataclass
class SurfaceHeatRate:
    """Heat rate details for a specific 3D surface."""
    name: str
    area: float                          # m²
    mean_flux: float                     # W/m² (inward positive, outward negative)
    heat_rate: float                     # Watts (Q = mean_flux * area)
    is_input: bool                       # True if heat enters, False if heat leaves


@dataclass
class EnergyAuditResult:
    """Comprehensive 3D Energy Audit and First Law validation."""
    config: Shelter3DConfig
    sim_result: Shelter3DResult
    surfaces: Dict[str, SurfaceHeatRate]
    total_heat_in: float                 # Watts entering from outside
    total_internal_gen: float            # Watts generated inside
    total_energy_input: float            # Q_in + Q_gen
    total_heat_out: float                # Watts dissipated to ground/ambient
    balance_residual_watts: float        # |Input - Output|
    balance_error_percent: float         # Residual / Input * 100%


def compute_3d_energy_audit(
    config: Shelter3DConfig,
    existing_mapdl: Optional[Mapdl] = None
) -> EnergyAuditResult:
    """Executes 3D simulation and calculates the complete 3D surface energy balance in Watts."""
    sim_res = run_3d_shelter_simulation(config=config, existing_mapdl=existing_mapdl)
    
    grid = sim_res.grid
    tw = config.wall_thickness
    lx, ly, lz = config.length, config.width, config.height

    # Surface Areas
    area_roof = lx * ly                  # 4.0 * 3.0 = 12.0 m²
    area_ground = lx * ly                # 12.0 m²
    area_south = lx * (lz - 2*tw)        # 4.0 * 2.1 = 8.4 m²
    area_north = lx * (lz - 2*tw)        # 8.4 m²
    area_west = ly * (lz - 2*tw)         # 3.0 * 2.1 = 6.3 m²
    area_east = ly * (lz - 2*tw)         # 6.3 m²

    cell_centers = grid.cell_centers().points
    q_x = sim_res.heat_flux_x
    q_y = sim_res.heat_flux_y
    q_z = sim_res.heat_flux_z

    # 1. Roof Surface (Z near lz, net inward flux is -q_z)
    roof_mask = cell_centers[:, 2] >= lz - tw - 0.05
    roof_flux = float(np.mean(-q_z[roof_mask]))
    q_roof_watts = roof_flux * area_roof

    # 2. South Wall (Y near 0, net inward flux is +q_y)
    south_mask = (cell_centers[:, 1] <= tw + 0.05) & (cell_centers[:, 2] >= tw) & (cell_centers[:, 2] <= lz - tw)
    south_flux = float(np.mean(q_y[south_mask]))
    q_south_watts = south_flux * area_south

    # 3. West Wall (X near 0, net inward flux is +q_x)
    west_mask = (cell_centers[:, 0] <= tw + 0.05) & (cell_centers[:, 2] >= tw) & (cell_centers[:, 2] <= lz - tw)
    west_flux = float(np.mean(q_x[west_mask]))
    q_west_watts = west_flux * area_west

    # 4. North Wall (Y near ly, net inward flux is -q_y)
    north_mask = (cell_centers[:, 1] >= ly - tw - 0.05) & (cell_centers[:, 2] >= tw) & (cell_centers[:, 2] <= lz - tw)
    north_flux = float(np.mean(-q_y[north_mask]))
    q_north_watts = north_flux * area_north

    # 5. East Wall (X near lx, net inward flux is -q_x)
    east_mask = (cell_centers[:, 0] >= lx - tw - 0.05) & (cell_centers[:, 2] >= tw) & (cell_centers[:, 2] <= lz - tw)
    east_flux = float(np.mean(-q_x[east_mask]))
    q_east_watts = east_flux * area_east

    # 6. Ground Foundation Slab (Z near 0, heat conducts downward into earth: q_outward = -q_z)
    ground_mask = cell_centers[:, 2] <= tw + 0.05
    ground_flux = float(np.mean(-q_z[ground_mask]))
    q_ground_watts = ground_flux * area_ground

    # 7. Internal Heat Generation (Occupants & Equipment)
    q_internal_gen = config.occupant_heat_total

    # Compile Surface Data (classify as net ingress vs net dissipation based on sign)
    surfaces = {
        "Roof (Solar + Air)": SurfaceHeatRate("Roof (Solar + Air)", area_roof, roof_flux, q_roof_watts, q_roof_watts >= 0),
        "South Wall (Sunlit)": SurfaceHeatRate("South Wall (Sunlit)", area_south, south_flux, q_south_watts, q_south_watts >= 0),
        "West Wall (Sunlit)": SurfaceHeatRate("West Wall (Sunlit)", area_west, west_flux, q_west_watts, q_west_watts >= 0),
        "North Wall (Shaded)": SurfaceHeatRate("North Wall (Shaded)", area_north, north_flux, q_north_watts, q_north_watts >= 0),
        "East Wall (Shaded)": SurfaceHeatRate("East Wall (Shaded)", area_east, east_flux, q_east_watts, q_east_watts >= 0),
        "Ground Foundation Sink": SurfaceHeatRate("Ground Foundation Sink", area_ground, ground_flux, q_ground_watts, False),
        "Occupants & Electronics": SurfaceHeatRate("Occupants & Electronics", 0.0, 0.0, q_internal_gen, True)
    }

    # Sum of all heat gains (inputs) and losses (outputs)
    total_gains = q_internal_gen
    total_losses = q_ground_watts  # Ground is always a sink in hot summer

    for s_name in ["Roof (Solar + Air)", "South Wall (Sunlit)", "West Wall (Sunlit)", "North Wall (Shaded)", "East Wall (Shaded)"]:
        s_rate = surfaces[s_name].heat_rate
        if s_rate >= 0:
            total_gains += s_rate
        else:
            total_losses += abs(s_rate)

    total_heat_in = total_gains - q_internal_gen
    total_energy_input = total_gains
    total_heat_out = total_losses

    residual = abs(total_energy_input - total_heat_out)
    error_pct = (residual / total_energy_input * 100.0) if total_energy_input > 0 else 0.0

    return EnergyAuditResult(
        config=config,
        sim_result=sim_res,
        surfaces=surfaces,
        total_heat_in=total_heat_in,
        total_internal_gen=q_internal_gen,
        total_energy_input=total_energy_input,
        total_heat_out=total_heat_out,
        balance_residual_watts=residual,
        balance_error_percent=error_pct
    )


def render_3d_energy_diagrams(
    audit: EnergyAuditResult,
    save_prefix: str
) -> Tuple[str, str]:
    """Generates 3D PyVista annotated spatial energy map and 2D energy breakdown audit charts."""
    grid = audit.sim_result.grid
    cfg = audit.config
    lx, ly, lz = cfg.length, cfg.width, cfg.height

    # -------------------------------------------------------------
    # 1. PyVista 3D Annotated Spatial Energy Map
    # -------------------------------------------------------------
    p = pv.Plotter(off_screen=True, window_size=(1500, 950))
    p.set_background("#16161a")

    p.add_mesh(
        grid,
        scalars="Temperature",
        cmap="turbo",
        opacity=0.88,
        show_scalar_bar=True,
        scalar_bar_args={"title": "Temperature (°C)", "color": "white", "vertical": True}
    )

    # 3D Billboards / Labels with Watts and %
    s = audit.surfaces
    tot_in = audit.total_energy_input

    # Roof label
    pct_roof = (s["Roof (Solar + Air)"].heat_rate / tot_in) * 100.0 if tot_in > 0 else 0.0
    p.add_point_labels(
        points=[[lx/2.0, ly/2.0, lz + 0.15]],
        labels=[f"ROOF SOLAR GAIN\n+{s['Roof (Solar + Air)'].heat_rate:.0f} W ({pct_roof:.1f}%)"],
        font_size=11, text_color="#ffff00", shape_color="#333333", shape_opacity=0.9, fill_shape=True
    )

    # South Wall label
    pct_south = (s["South Wall (Sunlit)"].heat_rate / tot_in) * 100.0 if tot_in > 0 else 0.0
    p.add_point_labels(
        points=[[lx/2.0, -0.2, lz/2.0]],
        labels=[f"SOUTH WALL\n+{s['South Wall (Sunlit)'].heat_rate:.0f} W ({pct_south:.1f}%)"],
        font_size=10, text_color="#ff9900", shape_color="#333333", shape_opacity=0.9, fill_shape=True
    )

    # West Wall label
    pct_west = (s["West Wall (Sunlit)"].heat_rate / tot_in) * 100.0 if tot_in > 0 else 0.0
    p.add_point_labels(
        points=[[-0.2, ly/2.0, lz/2.0]],
        labels=[f"WEST WALL\n+{s['West Wall (Sunlit)'].heat_rate:.0f} W ({pct_west:.1f}%)"],
        font_size=10, text_color="#ff9900", shape_color="#333333", shape_opacity=0.9, fill_shape=True
    )

    # Ground Foundation Sink label
    p.add_point_labels(
        points=[[lx/2.0, ly/2.0, -0.25]],
        labels=[f"GROUND FOUNDATION SINK\n-{audit.total_heat_out:.0f} W (100% Heat Escaped)"],
        font_size=11, text_color="#00ffff", shape_color="#222222", shape_opacity=0.95, fill_shape=True
    )

    # Room Core internal label
    pct_int = (audit.total_internal_gen / tot_in) * 100.0 if tot_in > 0 else 0.0
    p.add_point_labels(
        points=[[lx/2.0, ly/2.0, lz/2.0]],
        labels=[f"OCCUPANTS & EQUIP\n+{audit.total_internal_gen:.0f} W ({pct_int:.1f}%)"],
        font_size=10, text_color="#ff33cc", shape_color="#222222", shape_opacity=0.9, fill_shape=True
    )

    p.add_text(
        f"3D Shelter Total Energy Audit Map\nTotal Input Power: {audit.total_energy_input:.0f} W | Ground Dissipation: {audit.total_heat_out:.0f} W | First Law Error: {audit.balance_error_percent:.2f}%",
        position="upper_left", color="white", font_size=11
    )
    p.camera_position = [(lx*2.3, -ly*2.0, lz*2.1), (lx/2.0, ly/2.0, lz/2.0), (0, 0, 1)]
    p.add_axes(color="white")

    view1_path = f"{save_prefix}_3d_energy_map.png"
    p.screenshot(view1_path)
    p.close()

    # -------------------------------------------------------------
    # 2. 2D Energy Breakdown Charts (Ledger & Pie)
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Subplot 1: Bar Chart of Sources and Sinks
    labels = ["Roof", "South Wall", "West Wall", "North Wall", "East Wall", "Internal Load", "Ground Sink"]
    values = [
        s["Roof (Solar + Air)"].heat_rate,
        s["South Wall (Sunlit)"].heat_rate,
        s["West Wall (Sunlit)"].heat_rate,
        s["North Wall (Shaded)"].heat_rate,
        s["East Wall (Shaded)"].heat_rate,
        audit.total_internal_gen,
        -audit.total_heat_out
    ]
    colors = ["#e63946", "#f77f00", "#fcbf49", "#90be6d", "#43aa8b", "#9d4edd", "#0077b6"]

    bars = ax1.bar(labels, values, color=colors, edgecolor="black", linewidth=1.0)
    ax1.axhline(0, color="black", linewidth=1.2)
    ax1.set_ylabel("Thermal Power (Watts)", fontsize=11, fontweight="bold")
    ax1.set_title(f"3D Thermal Energy Ledger (Total Input = {audit.total_energy_input:.0f} W)", fontsize=12, fontweight="bold")
    ax1.tick_params(axis="x", rotation=30, labelsize=9.5)
    ax1.grid(True, linestyle=":", alpha=0.5, axis="y")

    # Add value annotations on bars
    for bar in bars:
        h = bar.get_height()
        va = "bottom" if h >= 0 else "top"
        ax1.annotate(f"{h:+.0f} W",
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3 if h >= 0 else -12),
                     textcoords="offset points",
                     ha="center", va=va, fontsize=8.5, fontweight="bold")

    # Subplot 2: Energy Input Breakdown Donut Chart
    raw_input_labels = ["Roof Solar/Air", "South Wall", "West Wall", "North Wall", "East Wall", "Occupants/Equip"]
    raw_input_vals = [
        s["Roof (Solar + Air)"].heat_rate,
        s["South Wall (Sunlit)"].heat_rate,
        s["West Wall (Sunlit)"].heat_rate,
        s["North Wall (Shaded)"].heat_rate,
        s["East Wall (Shaded)"].heat_rate,
        audit.total_internal_gen
    ]
    raw_colors = ["#e63946", "#f77f00", "#fcbf49", "#90be6d", "#43aa8b", "#9d4edd"]

    valid_labels = []
    valid_vals = []
    valid_colors = []
    for lbl, val, col in zip(raw_input_labels, raw_input_vals, raw_colors):
        if val > 0.1:
            valid_labels.append(lbl)
            valid_vals.append(val)
            valid_colors.append(col)

    if sum(valid_vals) > 0:
        wedges, texts, autotexts = ax2.pie(
            valid_vals,
            labels=valid_labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=valid_colors,
            wedgeprops=dict(width=0.45, edgecolor="white")
        )
        plt.setp(autotexts, size=9, weight="bold")
    ax2.set_title(f"Thermal Energy Ingress Distribution\n(Total Input = {audit.total_energy_input:.0f} W)", fontsize=12, fontweight="bold")

    plt.tight_layout()
    chart_path = f"{save_prefix}_energy_breakdown_chart.png"
    plt.savefig(chart_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Energy Audit Diagrams saved:\n  1. {view1_path}\n  2. {chart_path}")
    return view1_path, chart_path
