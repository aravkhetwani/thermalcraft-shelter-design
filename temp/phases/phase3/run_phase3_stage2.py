"""
Phase 3 Stage 3.2: Runner Script for 3D Full-Shelter Transient Solar Tracking Simulation
----------------------------------------------------------------------------------------
Executes 3D transient FEA in ANSYS MAPDL across 48 continuous hours with dynamic
sun position tracking (East -> South -> West solar migration).

Generates:
  - 4-Panel 3D PyVista Spatial Diurnal Solar Migration Snapshots (09:00, 13:00, 17:00, 02:00)
  - 24-Hour Diurnal Orientation Temperature Trajectories & Core Stability Curves
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from ansys.mapdl.core import launch_mapdl

from phases.phase3.transient_3d_shelter import (
    Transient3DConfig,
    run_3d_transient_shelter_simulation,
    plot_3d_transient_time_series,
    render_3d_diurnal_solar_snapshots
)


def run_phase3_stage2():
    print("=" * 80)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 3 STAGE 3.2 3D TRANSIENT SOLAR TRACKING")
    print("=" * 80)

    # 1. Shelter Configuration: High-Mass Stabilized Earth Envelope with Cool Roof
    config = Transient3DConfig(
        length=4.0,
        width=3.0,
        height=2.5,
        wall_thickness=0.20,
        k_envelope=0.75,         # Stabilized Earth / CSEB
        rho_envelope=1850.0,     # 1850 kg/m³
        cp_envelope=1000.0,      # 1000 J/kg·K (High thermal mass!)
        alpha_roof=0.85,         # Standard dark roof
        alpha_walls=0.60,        # Standard wall finish
        h_outdoor=20.0,
        h_indoor=7.7,
        occupant_heat_total=400.0,
        t_ground=24.0,           # Deep earth floor coupling
        t_ambient_mean=34.0,     # 24°C night to 44°C daytime peak
        t_ambient_amp=10.0,
        hours_simulated=48,
        time_step_sec=3600.0     # 1 hour time steps (48 load steps over 48h for rapid ~15-20s solving)
    )

    figures_dir = PROJECT_ROOT / "report" / "phase3" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 2. Launch Shared ANSYS MAPDL Solver Instance
    print("\n[Step 1/3] Launching ANSYS MAPDL Solver...")
    mapdl = launch_mapdl(override=True)
    print(f"Connected to ANSYS Version: {mapdl.version}")

    # 3. Solve 3D Full-Shelter Transient Solar Migration with Timeout Protection (120s max)
    print("\n[Step 2/3] Solving 3D Transient FEA over 48 Hours with Dynamic Solar Tracking...")
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_3d_transient_shelter_simulation, config=config, existing_mapdl=mapdl)
        try:
            res = future.result(timeout=180.0)  # 3 minute timeout threshold
        except concurrent.futures.TimeoutError:
            print("\n[TIMEOUT ERROR] Simulation exceeded 180s limit. Aborting MAPDL session...")
            mapdl.exit()
            raise TimeoutError("3D Transient simulation timed out after 180 seconds.")

    mask_day2 = (res.time_hours >= 24.0) & (res.time_hours <= 48.0)
    t2_h = res.time_hours[mask_day2] - 24.0
    t_core_day2 = res.t_indoor_core[mask_day2]
    t_roof_day2 = res.t_roof_outer_surface[mask_day2]
    t_west_day2 = res.t_west_outer_surface[mask_day2]
    t_east_day2 = res.t_east_outer_surface[mask_day2]

    print("\n" + "=" * 60)
    print("3D FULL-SHELTER TRANSIENT DIURNAL AUDIT RESULTS:")
    print("=" * 60)
    print(f"  Outdoor Ambient Range:          {np.min(res.t_ambient[mask_day2]):.1f} °C -> {np.max(res.t_ambient[mask_day2]):.1f} °C (Swing = {np.max(res.t_ambient[mask_day2]) - np.min(res.t_ambient[mask_day2]):.1f} °C)")
    print(f"  Peak East Wall Surface Temp:    {np.max(t_east_day2):.1f} °C (at t = {t2_h[np.argmax(t_east_day2)]:.1f}h morning)")
    print(f"  Peak Roof Surface Temp:         {np.max(t_roof_day2):.1f} °C (at t = {t2_h[np.argmax(t_roof_day2)]:.1f}h noon)")
    print(f"  Peak West Wall Surface Temp:    {np.max(t_west_day2):.1f} °C (at t = {t2_h[np.argmax(t_west_day2)]:.1f}h afternoon)")
    print(f"  Indoor Room Core Temp Range:    {np.min(t_core_day2):.1f} °C -> {np.max(t_core_day2):.1f} °C (Swing = {np.max(t_core_day2) - np.min(t_core_day2):.1f} °C!)")
    print(f"  Indoor Thermal Lag relative to Noon: {t2_h[np.argmax(t_core_day2)] - t2_h[np.argmax(t_roof_day2)]:.1f} Hours")
    print("=" * 60)

    # 4. Render 3D PyVista Diagrams & Time Series
    print("\n[Step 3/3] Generating 3D PyVista Diagrams & Time Series...")
    
    chart_path = str(figures_dir / "stage_3_2_3d_diurnal_time_series.png")
    plot_3d_transient_time_series(res, chart_path)
    print(f"  Saved: {chart_path}")

    snap_path = str(figures_dir / "stage_3_2_3d_solar_migration_snapshots.png")
    render_3d_diurnal_solar_snapshots(res, snap_path)
    print(f"  Saved: {snap_path}")

    mapdl.exit()
    print("\nANSYS session safely closed.")
    print("=" * 80)
    print("PHASE 3 STAGE 3.2 COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_phase3_stage2()
