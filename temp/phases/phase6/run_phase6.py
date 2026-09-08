"""
Phase 6: Multi-Objective Optimization Runner Script (NSGA-II)
==============================================================
Smart India Hackathon (SIH 2026) — Automated Computational Passive Shelter Pipeline

Runs the multi-objective genetic algorithm (NSGA-II) to extract the 3D Pareto frontier
(Cost vs. Discomfort Degree Hours vs. Thermal Autonomy), validates the knee-point candidate in
ANSYS MAPDL (SOLID87), and generates high-resolution 2D/3D engineering analytics and PyVista visualizations.
"""

import sys
from pathlib import Path
import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from phases.phase6.optimization_engine import (
    DesignVariables,
    CandidateSolution,
    MultiObjectiveEvaluator,
    NSGA2Engine,
    OptimalShelterFEA,
    plot_pareto_analytics,
    render_3d_optimal_shelter
)


def run_phase6():
    print("=" * 85)
    print("SIH 2026 — PASSIVE THERMAL SHELTER: PHASE 6 MULTI-OBJECTIVE GENETIC ALGORITHM OPTIMIZATION")
    print("=" * 85)

    figures_dir = PROJECT_ROOT / "report" / "phase6" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize Climate Evaluator (Composite Zone: New Delhi / Jaipur)
    climate_zone = "composite"
    evaluator = MultiObjectiveEvaluator(climate_zone=climate_zone)

    # 2. Execute NSGA-II Multi-Objective Optimization
    # Population = 50, Generations = 30 (1,500 candidate evaluations)
    nsga2 = NSGA2Engine(evaluator=evaluator, pop_size=50, generations=30)
    pareto_frontier = nsga2.run_optimization()

    # 3. Extract Characteristic Solutions on the Pareto Frontier
    costs = np.array([sol.cost_inr for sol in pareto_frontier])
    ddh = np.array([sol.discomfort_ddh for sol in pareto_frontier])
    autonomy = np.array([sol.thermal_autonomy_pct for sol in pareto_frontier])

    # A. Economy / Cost-Optimal
    idx_cost = int(np.argmin(costs))
    sol_cost = pareto_frontier[idx_cost]

    # B. Balanced Knee Point (Normalized Euclidean distance to utopian point)
    norm_cost = (costs - min(costs)) / (max(costs) - min(costs) + 1e-5)
    norm_ddh = (ddh - min(ddh)) / (max(ddh) - min(ddh) + 1e-5)
    norm_auto = 1.0 - (autonomy - min(autonomy)) / (max(autonomy) - min(autonomy) + 1e-5)
    dist = norm_cost**2 + norm_ddh**2 + norm_auto**2
    idx_knee = int(np.argmin(dist))
    sol_knee = pareto_frontier[idx_knee]

    # C. Maximum Autonomy (Ultra-Passive Performance)
    idx_auto = int(np.argmax(autonomy))
    sol_auto = pareto_frontier[idx_auto]

    print("\n" + "=" * 80)
    print("PARETO OPTIMIZATION CANDIDATE COMPARISON MATRIX (COMPOSITE CLIMATE):")
    print("=" * 80)
    header = f"{'Design Parameter / Metric':<32} | {'A: Cost-Optimal':<18} | {'B: Knee Point (Rec.)':<20} | {'C: Max Autonomy':<18}"
    print(header)
    print("-" * len(header))

    rows = [
        ("Wall Insulation (mm)", f"{sol_cost.genes.d_ins_wall*1000:.0f} mm", f"{sol_knee.genes.d_ins_wall*1000:.0f} mm", f"{sol_auto.genes.d_ins_wall*1000:.0f} mm"),
        ("Roof Insulation (mm)", f"{sol_cost.genes.d_ins_roof*1000:.0f} mm", f"{sol_knee.genes.d_ins_roof*1000:.0f} mm", f"{sol_auto.genes.d_ins_roof*1000:.0f} mm"),
        ("Bio-PCM Layer (mm)", f"{sol_cost.genes.d_pcm*1000:.0f} mm", f"{sol_knee.genes.d_pcm*1000:.0f} mm", f"{sol_auto.genes.d_pcm*1000:.0f} mm"),
        ("Window-to-Wall Ratio (%)", f"{sol_cost.genes.wwr*100:.0f}%", f"{sol_knee.genes.wwr*100:.0f}%", f"{sol_auto.genes.wwr*100:.0f}%"),
        ("Shading Overhang Depth (m)", f"{sol_cost.genes.l_overhang:.2f} m", f"{sol_knee.genes.l_overhang:.2f} m", f"{sol_auto.genes.l_overhang:.2f} m"),
        ("EAHE Pipe Length (m)", f"{sol_cost.genes.l_eahe:.0f} m", f"{sol_knee.genes.l_eahe:.0f} m", f"{sol_auto.genes.l_eahe:.0f} m"),
        ("-----------------------------", "------------------", "--------------------", "------------------"),
        ("Initial Capital Cost (INR)", f"INR {sol_cost.cost_inr:,.0f}", f"INR {sol_knee.cost_inr:,.0f}", f"INR {sol_auto.cost_inr:,.0f}"),
        ("Annual Discomfort (DDH)", f"{sol_cost.discomfort_ddh:,.0f} C.h", f"{sol_knee.discomfort_ddh:,.0f} C.h", f"{sol_auto.discomfort_ddh:,.0f} C.h"),
        ("Thermal Autonomy (%)", f"{sol_cost.thermal_autonomy_pct:.1f}%", f"{sol_knee.thermal_autonomy_pct:.1f}%", f"{sol_auto.thermal_autonomy_pct:.1f}%"),
        ("Peak Summer Temp (deg C)", f"{sol_cost.peak_indoor_temp:.2f} C", f"{sol_knee.peak_indoor_temp:.2f} C", f"{sol_auto.peak_indoor_temp:.2f} C"),
        ("Min Winter Temp (deg C)", f"{sol_cost.min_indoor_temp:.2f} C", f"{sol_knee.min_indoor_temp:.2f} C", f"{sol_auto.min_indoor_temp:.2f} C")
    ]
    for r in rows:
        print(f"{r[0]:<32} | {r[1]:<18} | {r[2]:<20} | {r[3]:<18}")
    print("=" * 80)

    # 4. Generate 2D/3D Analytics & Parallel Coordinates
    print("\n[Step 2/3] Generating High-Resolution 2D/3D Pareto Visualizations...")
    plot_pareto_analytics(pareto_frontier, figures_dir)

    # 5. 3D ANSYS MAPDL FEA Validation of Knee Point Solution
    print("\n[Step 3/3] Executing High-Fidelity 3D ANSYS MAPDL FEA on Optimal Knee Point...")
    vtk_path = str(figures_dir / "phase6_optimal_shelter.vtk")
    fea_res = OptimalShelterFEA.validate_pareto_candidate(sol_knee, vtk_path)

    # Render 3D PyVista Cutaway
    render_img_path = str(figures_dir / "phase6_3d_optimal_shelter.png")
    render_3d_optimal_shelter(vtk_path, render_img_path, sol_knee)

    print("\n" + "=" * 85)
    print("PHASE 6 MULTI-OBJECTIVE OPTIMIZATION COMPLETED SUCCESSFULLY!")
    print(f"Generated Visualizations & Reports in: {figures_dir}")
    print("=" * 85)


if __name__ == "__main__":
    run_phase6()
