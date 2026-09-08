"""
Phase 4 Stage 4.1: Earth-Air Heat Exchanger (EAHE) Passive Cooling Model
-----------------------------------------------------------------------
Coupled physics pipeline combining Kusuda-Achenbach soil depth temperature
propagation, 1D turbulent internal convective heat exchange (NTU method),
and 3D ANSYS MAPDL finite element soil domain modeling with PyVista rendering.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
from ansys.mapdl.core import launch_mapdl, Mapdl


@dataclass
class SoilProperties:
    """Thermo-physical properties of surrounding soil."""
    conductivity: float = 1.25        # k [W/(m·K)] (Damp clay / sandy silt)
    density: float = 1900.0           # rho [kg/m³]
    specific_heat: float = 1200.0     # Cp [J/(kg·K)]
    t_mean_annual: float = 25.0       # Mean annual surface temperature (°C)
    amplitude_annual: float = 12.0    # Annual surface temperature swing (°C)
    t_shift_days: float = 35.0        # Phase shift in days from Jan 1 to peak temp

    @property
    def thermal_diffusivity(self) -> float:
        """alpha = k / (rho * Cp) in m²/s."""
        return self.conductivity / (self.density * self.specific_heat)

    @property
    def thermal_diffusivity_day(self) -> float:
        """alpha in m²/day."""
        return self.thermal_diffusivity * 86400.0


@dataclass
class EAHEPipeConfig:
    """Geometry and operating parameters for buried EAHE pipe."""
    diameter: float = 0.20            # Inner diameter in meters (200 mm)
    thickness: float = 0.008          # Pipe wall thickness in meters (8 mm PVC / HDPE)
    length: float = 25.0              # Pipe length in meters
    depth: float = 3.0                # Burial depth in meters
    pipe_conductivity: float = 0.19   # k [W/(m·K)] (PVC = 0.19, HDPE = 0.45, Concrete = 1.4)
    air_velocity: float = 2.5         # Air velocity in pipe (m/s)
    t_inlet: float = 44.0             # Hot outdoor ambient inlet air temp (°C)
    
    # Air thermo-physical properties at ~35°C
    rho_air: float = 1.145            # kg/m³
    cp_air: float = 1007.0            # J/(kg·K)
    k_air: float = 0.0268             # W/(m·K)
    nu_air: float = 1.66e-5           # Kinematic viscosity (m²/s)
    pr_air: float = 0.707             # Prandtl number


@dataclass
class EAHEResult:
    """Output metrics from analytical and 3D FEA simulation."""
    config: EAHEPipeConfig
    soil_props: SoilProperties
    soil_temp_at_depth: float         # Soil temperature at burial depth (°C)
    reynolds_number: float
    nusselt_number: float
    h_convection: float               # W/(m²·K)
    mass_flow_rate: float             # kg/s
    volume_flow_rate_m3h: float       # m³/h
    t_outlet: float                   # Outlet air temperature (°C)
    temperature_drop: float           # Delta T (°C)
    cooling_power_watts: float        # Watts (Q = m_dot * Cp * Delta T)
    cooling_power_tr: float           # Tons of Refrigeration (1 TR = 3517 W)
    x_coords: np.ndarray              # Longitudinal pipe positions (m)
    t_air_profile: np.ndarray         # Air temperature along pipe (°C)
    cumulative_cooling: np.ndarray    # Cumulative Watts extracted along pipe


def compute_kusuda_soil_temperature(
    depth: float,
    day_of_year: float,
    soil: SoilProperties
) -> float:
    """
    Computes undisturbed underground soil temperature using the Kusuda & Achenbach formula:
    T(z, t) = T_mean - A * exp(-z * sqrt(pi / (365 * alpha))) * cos(2*pi/365 * (t - t0 - z/2 * sqrt(365 / (pi * alpha))))
    """
    alpha = soil.thermal_diffusivity_day  # m²/day
    decay_factor = np.sqrt(np.pi / (365.0 * alpha))
    phase_lag = (depth / 2.0) * np.sqrt(365.0 / (np.pi * alpha))
    
    t_soil = soil.t_mean_annual - soil.amplitude_annual * np.exp(-depth * decay_factor) * np.cos(
        (2.0 * np.pi / 365.0) * (day_of_year - soil.t_shift_days - phase_lag)
    )
    return float(t_soil)


def solve_eahe_analytical(
    pipe: EAHEPipeConfig,
    soil: SoilProperties,
    day_of_year: float = 150.0  # Day 150 ~ End of May (Peak Indian Summer)
) -> EAHEResult:
    """Solves 1D turbulent convective heat transfer along the buried duct using the NTU method."""
    t_soil_depth = compute_kusuda_soil_temperature(pipe.depth, day_of_year, soil)
    
    # 1. Flow Hydrodynamics
    cross_area = np.pi * (pipe.diameter / 2.0)**2
    flow_volume = cross_area * pipe.air_velocity  # m³/s
    m_dot = pipe.rho_air * flow_volume            # kg/s
    v_m3h = flow_volume * 3600.0                  # m³/h
    
    # 2. Dimensionless Numbers (Turbulent flow in circular duct)
    re = (pipe.air_velocity * pipe.diameter) / pipe.nu_air
    # Dittus-Boelter cooling correlation: Nu = 0.023 * Re^0.8 * Pr^0.3
    nu = 0.023 * (re**0.8) * (pipe.pr_air**0.3)
    h_conv = (nu * pipe.k_air) / pipe.diameter   # W/(m²·K)
    
    # 3. Overall Heat Transfer Coefficient (U)
    r_pipe_wall = (pipe.diameter * np.log((pipe.diameter + 2*pipe.thickness) / pipe.diameter)) / (2.0 * pipe.pipe_conductivity)
    u_overall = 1.0 / ((1.0 / h_conv) + r_pipe_wall)
    
    # 4. Longitudinal Temperature Profile: T_air(x) = T_soil + (T_in - T_soil) * exp(- (U * pi * D * x) / (m_dot * Cp))
    x_pts = np.linspace(0.0, pipe.length, 100)
    decay_constant = (u_overall * np.pi * pipe.diameter) / (m_dot * pipe.cp_air)
    t_profile = t_soil_depth + (pipe.t_inlet - t_soil_depth) * np.exp(-decay_constant * x_pts)
    
    t_out = float(t_profile[-1])
    delta_t = pipe.t_inlet - t_out
    q_cooling = m_dot * pipe.cp_air * delta_t  # Watts
    q_tr = q_cooling / 3517.0                  # Tons of Refrigeration
    
    cum_cooling = m_dot * pipe.cp_air * (pipe.t_inlet - t_profile)
    
    return EAHEResult(
        config=pipe,
        soil_props=soil,
        soil_temp_at_depth=t_soil_depth,
        reynolds_number=float(re),
        nusselt_number=float(nu),
        h_convection=float(h_conv),
        mass_flow_rate=float(m_dot),
        volume_flow_rate_m3h=float(v_m3h),
        t_outlet=t_out,
        temperature_drop=float(delta_t),
        cooling_power_watts=float(q_cooling),
        cooling_power_tr=float(q_tr),
        x_coords=x_pts,
        t_air_profile=t_profile,
        cumulative_cooling=cum_cooling
    )


def run_3d_eahe_soil_fea(
    pipe: EAHEPipeConfig,
    soil: SoilProperties,
    existing_mapdl: Optional[Mapdl] = None
) -> Tuple[pv.UnstructuredGrid, float]:
    """
    Builds a 3D FEA soil domain in ANSYS MAPDL (SOLID87 quadratic tetrahedrals)
    around the buried EAHE pipe and simulates steady-state soil thermal extraction.
    """
    mapdl = existing_mapdl if existing_mapdl is not None else launch_mapdl()
    mapdl.clear()
    mapdl.prep7()
    mapdl.title("SIH 2026: 3D Underground Soil Domain EAHE Simulation")

    # Use 10-node quadratic tetrahedral element SOLID87
    mapdl.et(1, "SOLID87")
    mapdl.mp("KXX", 1, soil.conductivity)

    # 3D Soil Block: Width = 5m (X: -2.5 to +2.5), Length = pipe.length (Y: 0 to L), Depth = 4.5m (Z: -4.5 to 0)
    # Pipe runs along Y axis at X = 0, Z = -pipe.depth
    lx_half = 2.5
    lz_soil = 4.5
    
    # Create Soil Volume
    v_soil = int(mapdl.block(-lx_half, lx_half, 0.0, pipe.length, -lz_soil, 0.0))

    # Create Buried Cylindrical Duct along Y axis
    mapdl.wpoffs(0.0, 0.0, -pipe.depth)
    mapdl.wprota(0.0, 90.0, 0.0) # Align with Y axis
    v_pipe = int(mapdl.cyl4(0.0, 0.0, pipe.diameter / 2.0, 0.0, 0.0, 360.0, pipe.length))
    mapdl.wpcsys(-1)

    # Subtract pipe cavity from soil
    mapdl.vsbv(v_soil, v_pipe)

    # Mesh Soil Domain with quadratic tetrahedrals (~15,000 nodes, well within 128k node limit)
    mapdl.mat(1)
    mapdl.esize(0.65)  # 650 mm element size
    mapdl.mshape(1, "3D")
    mapdl.mshkey(0)
    mapdl.vmesh("ALL")

    # Boundary Conditions:
    # 1. Top Soil Surface (Z = 0): Hot ambient summer convection
    mapdl.nsel("S", "LOC", "Z", 0.0)
    mapdl.sf("ALL", "CONV", 15.0, 42.0)  # Summer hot ground surface

    # 2. Deep Earth Base (Z = -lz_soil): Constant deep ground temp
    t_deep = soil.t_mean_annual
    mapdl.nsel("S", "LOC", "Z", -lz_soil)
    mapdl.d("ALL", "TEMP", t_deep)

    # 3. Pipe Cavity Wall: Internal convective cooling extraction
    # Analytical solution gives convective heat transfer
    analytical_res = solve_eahe_analytical(pipe, soil)
    t_mean_air_pipe = (pipe.t_inlet + analytical_res.t_outlet) / 2.0
    
    mapdl.nsel("S", "LOC", "Z", -pipe.depth - pipe.diameter, -pipe.depth + pipe.diameter)
    mapdl.nsel("R", "LOC", "X", -pipe.diameter, pipe.diameter)
    mapdl.sf("ALL", "CONV", analytical_res.h_convection, t_mean_air_pipe)
    mapdl.allsel()

    # Solve Steady-State Heat Diffusion
    mapdl.slashsolu()
    mapdl.antype("STATIC")
    mapdl.solve()

    # Post-Processing
    mapdl.post1()
    mapdl.set(1)

    grid = mapdl.mesh.grid.copy()
    grid.point_data["Temperature"] = mapdl.post_processing.nodal_temperature()

    return grid, analytical_res.t_outlet


def render_3d_eahe_cutaway(
    grid: pv.UnstructuredGrid,
    pipe: EAHEPipeConfig,
    res: EAHEResult,
    save_path: str
):
    """Renders an annotated 3D PyVista cutaway of underground soil thermal field around buried pipe."""
    p = pv.Plotter(off_screen=True, window_size=(1600, 950))
    p.set_background("#16161a")

    # Safe VTK visualization of quadratic 10-node tetrahedrals:
    # 1. Outer soil box wireframe / transparent surface
    surf = grid.extract_surface()
    p.add_mesh(surf, scalars="Temperature", cmap="turbo", opacity=0.35, show_scalar_bar=False)

    # 2. Longitudinal cross-sectional slice through pipe centerline (X = 0)
    slice_x = grid.slice(normal="x", origin=(0.0, pipe.length / 2.0, -pipe.depth))
    p.add_mesh(
        slice_x,
        scalars="Temperature",
        cmap="turbo",
        opacity=0.95,
        show_scalar_bar=True,
        scalar_bar_args={"title": "Soil Temperature (°C)", "color": "white", "vertical": True}
    )

    print("  [Cutaway] Adding pipe cylinder...")
    pipe_cyl = pv.Cylinder(
        center=(0.0, pipe.length / 2.0, -pipe.depth),
        direction=(0.0, 1.0, 0.0),
        radius=pipe.diameter / 2.0,
        height=pipe.length,
        resolution=36
    )
    p.add_mesh(pipe_cyl, color="#00ffff", opacity=0.4, style="wireframe", line_width=2)

    # 3D Annotations and Billboards
    # Inlet air label
    p.add_point_labels(
        points=[[0.0, 0.5, -pipe.depth + 0.4]],
        labels=[f"EAHE HOT AIR INLET\n{pipe.t_inlet:.1f}°C (v = {pipe.air_velocity:.1f} m/s)"],
        font_size=11, text_color="#ff4444", shape_color="#222222", fill_shape=True
    )

    # Outlet cool air label
    p.add_point_labels(
        points=[[0.0, pipe.length - 1.0, -pipe.depth + 0.4]],
        labels=[f"COOLED AIR DISCHARGE TO SHELTER\n{res.t_outlet:.1f}°C (Delta T = -{res.temperature_drop:.1f}°C)\nCooling Power: {res.cooling_power_watts:.0f} W ({res.cooling_power_tr:.2f} TR)"],
        font_size=11, text_color="#00ffff", shape_color="#222222", fill_shape=True
    )

    # Deep ground label
    p.add_point_labels(
        points=[[2.5, pipe.length / 2.0, -4.6]],
        labels=[f"UNDISTURBED EARTH SINK\n{res.soil_temp_at_depth:.1f}°C (Constant Year-Round)"],
        font_size=10, text_color="#90be6d", shape_color="#222222", fill_shape=True
    )

    p.add_text(
        f"3D Earth-Air Heat Exchanger (EAHE) Passive Cooling Plume\nPipe Length: {pipe.length:.0f}m | Diameter: {pipe.diameter*1000:.0f}mm | Depth: {pipe.depth:.1f}m | Flow: {res.volume_flow_rate_m3h:.0f} m³/h",
        position="upper_left", color="white", font_size=11
    )

    p.camera_position = [(12.0, -10.0, 4.0), (0.0, pipe.length / 2.0, -pipe.depth), (0, 0, 1)]
    p.add_axes(color="white")

    p.screenshot(save_path)
    p.close()


def plot_eahe_engineering_charts(
    res: EAHEResult,
    soil: SoilProperties,
    save_path: str
):
    """Plots 2D soil depth temperature damping and pipe air cooling curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # 1. Subplot 1: Soil Temperature vs Depth (Summer vs Winter vs Spring)
    depths = np.linspace(0.0, 5.0, 100)
    t_summer = [compute_kusuda_soil_temperature(z, 150.0, soil) for z in depths]  # End of May
    t_winter = [compute_kusuda_soil_temperature(z, 335.0, soil) for z in depths]  # December
    t_spring = [compute_kusuda_soil_temperature(z, 60.0, soil) for z in depths]   # March

    ax1.plot(t_summer, depths, "r-", linewidth=2.5, label="Peak Summer (Day 150 / May)")
    ax1.plot(t_winter, depths, "b--", linewidth=2.2, label="Peak Winter (Day 335 / Dec)")
    ax1.plot(t_spring, depths, "g-.", linewidth=2.0, label="Spring Transition (Day 60)")
    ax1.axhline(res.config.depth, color="black", linestyle=":", linewidth=1.8, label=f"EAHE Burial Depth ({res.config.depth}m)")

    ax1.set_xlabel("Soil Temperature (°C)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Depth Below Ground Level (m)", fontsize=11, fontweight="bold")
    ax1.set_title("Undisturbed Earth Temperature Profile with Depth\n(Kusuda-Achenbach Annual Model)", fontsize=12, fontweight="bold")
    ax1.invert_yaxis() # Depth increases downward
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower left", framealpha=0.95, fontsize=9.5)

    # 2. Subplot 2: Air Temperature & Cooling Watts along Pipe Length
    ax2_twin = ax2.twinx()

    line1 = ax2.plot(res.x_coords, res.t_air_profile, "r-", linewidth=2.8, label="Air Temperature (°C)")
    ax2.axhline(res.soil_temp_at_depth, color="green", linestyle="--", linewidth=1.8, label=f"Soil Sink Temp ({res.soil_temp_at_depth:.1f}°C)")
    
    line2 = ax2_twin.plot(res.x_coords, res.cumulative_cooling, "c-.", linewidth=2.5, label="Cumulative Cooling Power (Watts)")

    ax2.set_xlabel("Pipe Distance from Inlet (m)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Air Stream Temperature (°C)", color="red", fontsize=11, fontweight="bold")
    ax2_twin.set_ylabel("Cooling Power Extracted (Watts)", color="#008b8b", fontsize=11, fontweight="bold")
    ax2.set_title(f"Air Cooling Trajectory & Thermal Power along Buried Pipe\n(Inlet: {res.config.t_inlet:.1f}°C -> Outlet: {res.t_outlet:.1f}°C | Total Cooling: {res.cooling_power_watts:.0f} W)", fontsize=12, fontweight="bold")
    
    ax2.grid(True, linestyle=":", alpha=0.6)

    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc="center right", framealpha=0.95, fontsize=9.5)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
