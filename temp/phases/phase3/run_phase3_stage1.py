"""
Phase 3 Stage 3.1: Runner Script for Transient Thermal Dynamics & Thermal Mass Mastery
--------------------------------------------------------------------------------------
Simulates 24-48 hour diurnal heat diffusion through 3 distinct wall assemblies:
  1. Lightweight Baseline: Corrugated Galvanized Iron (Tin) + Plywood
  2. Conventional Masonry: Standard Burnt Clay Brick Wall (200 mm)
  3. SIH High-Performance Passive: Rammed Earth (200 mm) + Rockwool Outer Insulation (50 mm)

Generates:
  - 24h Diurnal Temperature Response & Thermal Damping Curve
  - Spatial Thermal Wave Penetration Profiles across Wall Thickness
  - 3D PyVista Peak vs Nighttime Thermal Contour Visualizations
"""

import sys
import os
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pyvista as pv
from ansys.mapdl.core import launch_mapdl

from phases.phase3.transient_thermal import (
    MATERIALS_DB,
    TransientWallAssembly,
    DiurnalEnvironmentConfig,
    run_transient_wall_simulation,
    plot_transient_comparison,
    plot_spatial_temperature_penetration
)


def run_phase3_stage1():
    print("=" * 80)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 3 STAGE 3.1 TRANSIENT THERMAL DYNAMICS")
    print("=" * 80)

    # 1. Define 3 Wall Assemblies for Comparative Study
    # Assembly 1: Lightweight Emergency / Slum Construction (Tin Sheet + Timber)
    lightweight_wall = TransientWallAssembly(
        name="Lightweight (Tin + Wood)",
        layers=[
            (MATERIALS_DB["CGI_Sheet"], 0.002),   # 2 mm CGI Sheet
            (MATERIALS_DB["Plywood"], 0.012)     # 12 mm Plywood Inner
        ]
    )

    # Assembly 2: Conventional Brick Masonry
    masonry_wall = TransientWallAssembly(
        name="Conventional Brick (200mm)",
        layers=[
            (MATERIALS_DB["Standard_Brick"], 0.200)  # 200 mm Brick
        ]
    )

    # Assembly 3: SIH High-Performance Earth + Insulation Composite
    # High thermal mass on interior (200mm Rammed Earth) protected by exterior Rockwool
    passive_earth_wall = TransientWallAssembly(
        name="SIH Rammed Earth + Ext Rockwool",
        layers=[
            (MATERIALS_DB["Rockwool"], 0.050),       # 50 mm Exterior Rockwool
            (MATERIALS_DB["Rammed_Earth"], 0.200)   # 200 mm Rammed Earth Core
        ]
    )

    assemblies = [lightweight_wall, masonry_wall, passive_earth_wall]

    # 2. Environmental Diurnal Profile (Harsh Indian Summer / Arid Zone)
    # Ambient: 34 ± 10°C (24°C night to 44°C daytime peak)
    # Peak Solar: 900 W/m² (Sol-Air Peak reaches ~72°C on dark roof/wall!)
    env_config = DiurnalEnvironmentConfig(
        t_ambient_mean=34.0,
        t_ambient_amp=10.0,
        solar_irradiance_peak=900.0,
        solar_absorptance=0.85,
        h_outdoor=20.0,
        h_indoor=7.7,
        t_indoor_setpoint=26.0,
        hours_simulated=48,
        time_step_sec=600.0  # 10 min time steps
    )

    # 3. Launch Shared ANSYS MAPDL Solver Instance
    print("\n[Step 1/3] Launching ANSYS MAPDL Solver...")
    mapdl = launch_mapdl(override=True)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    results = []
    figures_dir = PROJECT_ROOT / "report" / "phase3" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Step 2/3] Solving Transient FEA Diurnal Cycles...")
    for idx, asm in enumerate(assemblies, start=1):
        print(f"\n--- Simulating Wall {idx}/3: {asm.name} ---")
        print(f"  Total Thickness: {asm.total_thickness*1000:.1f} mm | R-Value: {asm.total_r_value:.3f} m²K/W")
        print(f"  Areal Thermal Mass (C_area): {asm.total_thermal_capacity_per_area:.1f} kJ/(m²·K)")

        res = run_transient_wall_simulation(assembly=asm, env=env_config, existing_mapdl=mapdl)
        results.append(res)

        print(f"  >> RESULTS for {asm.name}:")
        print(f"     Time Lag (Phase Shift):   {res.time_lag_hours:.2f} Hours")
        print(f"     Decrement Factor (mu):     {res.decrement_factor:.3f} ({res.decrement_factor*100:.1f}% amplitude transmission)")
        print(f"     Max Inner Surface Temp:   {np.max(res.t_indoor_surface[res.time_hours >= 24]):.1f} °C")
        print(f"     Min Inner Surface Temp:   {np.min(res.t_indoor_surface[res.time_hours >= 24]):.1f} °C")

    # 4. Generate Comparative 2D & 3D Visualization Figures
    print("\n[Step 3/3] Generating Visualizations & Reports...")

    # Figure 1: 24-Hour Diurnal Response Comparison
    fig1_path = str(figures_dir / "stage_3_1_diurnal_temperature_response.png")
    plot_transient_comparison(results, fig1_path)
    print(f"  Saved: {fig1_path}")

    # Figure 2: Spatial Thermal Wave Penetration Profile for High-Mass Earth Wall
    fig2_path = str(figures_dir / "stage_3_1_transient_thermal_wave_profiles.png")
    plot_spatial_temperature_penetration(results[2], fig2_path)
    print(f"  Saved: {fig2_path}")

    # Figure 3: 3D PyVista Visual Comparison of Temperature Contours
    render_3d_transient_comparison_snapshot(results, str(figures_dir / "stage_3_1_3d_peak_vs_night_temperatures.png"))
    print(f"  Saved: {figures_dir / 'stage_3_1_3d_peak_vs_night_temperatures.png'}")

    mapdl.exit()
    print("\nANSYS session safely closed.")
    print("=" * 80)
    print("PHASE 3 STAGE 3.1 COMPLETED SUCCESSFULLY!")
    print("=" * 80)


def render_3d_transient_comparison_snapshot(
    results: list,
    save_path: str
):
    """Renders a 3D PyVista comparison visual of wall assemblies at Peak Afternoon vs Midnight."""
    p = pv.Plotter(shape=(1, 2), off_screen=True, window_size=(1600, 750))
    p.set_background("#16161a")

    earth_res = results[2]
    tin_res = results[0]

    # Subplot 1: Peak Afternoon (14:00) Thermal State
    p.subplot(0, 0)
    p.add_text("PEAK AFTERNOON (14:00) — High Mass vs Lightweight", position="upper_left", color="white", font_size=11)

    # Create 3D extruded blocks for visualization
    # High-Mass Earth Block
    earth_block = pv.Cube(center=(0.10, 0.5, 0.5), x_length=0.25, y_length=0.8, z_length=0.8)
    p.add_mesh(earth_block, color="#2a9d8f", opacity=0.85, show_edges=True, edge_color="white")
    p.add_point_labels(
        points=[[0.10, 0.5, 0.95]],
        labels=[f"SIH Earth + Rockwool\nInner: {earth_res.spatial_temp_profiles[14][-1]:.1f}°C (Cool!)"],
        font_size=10, text_color="#00ffff", fill_shape=True, shape_color="#222222"
    )

    # Lightweight Tin Block
    tin_block = pv.Cube(center=(0.60, 0.5, 0.5), x_length=0.014, y_length=0.8, z_length=0.8)
    p.add_mesh(tin_block, color="#d90429", opacity=0.9, show_edges=True, edge_color="yellow")
    p.add_point_labels(
        points=[[0.60, 0.5, 0.95]],
        labels=[f"Lightweight Tin\nInner: {tin_res.spatial_temp_profiles[14][-1]:.1f}°C (Overheating!)"],
        font_size=10, text_color="#ff5555", fill_shape=True, shape_color="#222222"
    )
    p.camera_position = [(1.5, -1.8, 1.6), (0.35, 0.5, 0.5), (0, 0, 1)]

    # Subplot 2: Midnight (02:00) Thermal State
    p.subplot(0, 1)
    p.add_text("MIDNIGHT (02:00) — Stored Heat Release into Cool Night", position="upper_left", color="white", font_size=11)

    earth_block_night = pv.Cube(center=(0.10, 0.5, 0.5), x_length=0.25, y_length=0.8, z_length=0.8)
    p.add_mesh(earth_block_night, color="#e76f51", opacity=0.85, show_edges=True, edge_color="white")
    p.add_point_labels(
        points=[[0.10, 0.5, 0.95]],
        labels=[f"SIH Earth Core: {earth_res.spatial_temp_profiles[2][25]:.1f}°C\n(Releasing Stored Heat Outward)"],
        font_size=10, text_color="#ffaa00", fill_shape=True, shape_color="#222222"
    )

    tin_block_night = pv.Cube(center=(0.60, 0.5, 0.5), x_length=0.014, y_length=0.8, z_length=0.8)
    p.add_mesh(tin_block_night, color="#457b9d", opacity=0.9, show_edges=True, edge_color="yellow")
    p.add_point_labels(
        points=[[0.60, 0.5, 0.95]],
        labels=[f"Lightweight Tin: {tin_res.spatial_temp_profiles[2][-1]:.1f}°C\n(No Thermal Storage)"],
        font_size=10, text_color="#a8dadc", fill_shape=True, shape_color="#222222"
    )
    p.camera_position = [(1.5, -1.8, 1.6), (0.35, 0.5, 0.5), (0, 0, 1)]

    p.screenshot(save_path)
    p.close()


if __name__ == "__main__":
    run_phase3_stage1()
