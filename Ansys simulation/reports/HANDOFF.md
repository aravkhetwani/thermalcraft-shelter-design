# HANDOFF.md — SIH 2026 Passive Thermal Shelter Computational Pipeline

> **AI-to-AI Continuity Document**  
> This file is the primary navigation map, engineering status ledger, and runtime guide for any AI assistant continuing work on this codebase.  
> **Philosophy**: Do NOT recreate completed setup or duplicate comprehensive reports. Follow the Documentation Map and continue from the current stage.

---

# 1. Documentation Map

| Markdown Document | Primary Purpose & Contents | When to Read |
| :--- | :--- | :--- |
| **[`AI Project Context — SIH 2026 Passive Thermal Shelter.md`](./AI%20Project%20Context%20—%20SIH%202026%20Passive%20Thermal%20Shelter.md)** | **Authoritative Problem Statement & Master Architecture**: Hackathon goals, regional climate zones, mathematical physics, geometry parameters, and target thermal performance metrics. | Read when designing system architecture or verifying target engineering requirements. |
| **[`ANSYS_THERMAL_LEARNING_ROADMAP.md`](./ANSYS_THERMAL_LEARNING_ROADMAP.md)** | **Authoritative Stage-by-Stage Roadmap (Phases 1–6)**: Full pedagogical curriculum from 1D conduction to coupled Earth-Air Heat Exchangers (EAHE) and genetic algorithm optimization. | Read before planning any new phase or stage. |
| **[`report/phase1/phase1_report.md`](./report/phase1/phase1_report.md)** | **Phase 1 Technical Report**: 1D Fourier conduction, 4-layer composite wall resistance networks ($R=1.7193\,\text{m}^2\text{K/W}$), and 2D L-corner thermal bridges ($2.36\times$ flux concentration). | Reference when reviewing 1D/2D steady-state conduction foundations. |
| **[`report/phase2/stage_2_1_convection_report.md`](./report/phase2/stage_2_1_convection_report.md)** | **Stage 2.1 Technical Report**: Robin convective film boundary conditions ($h_{\text{out}}=20$, $h_{\text{in}}=7.7\,\text{W/m}^2\text{K}$), validated with 0.00000% error against theoretical network. | Reference for convective film resistance calculations. |
| **[`report/phase2/stage_2_2_solar_radiation_report.md`](./report/phase2/stage_2_2_solar_radiation_report.md)** | **Stage 2.2 Technical Report**: Solar radiation flux and Sol-Air temperature formulation ($T_{\text{sol-air}} = T_{\infty} + \frac{\alpha I}{h_{\text{out}}}$); Cool Roof ($\alpha=0.20$) benchmarking. | Reference for solar radiation modeling and cool roof coatings. |
| **[`report/phase2/stage_2_3_internal_heat_report.md`](./report/phase2/stage_2_3_internal_heat_report.md)** | **Stage 2.3 Technical Report**: Internal volumetric occupant loads ($400\,\text{W}$), discovery of the *Insulation Paradox*, and cross-ventilation ($\text{ACH}=6.0$) heat flushing. | Reference for internal metabolic loads and ventilation coupling. |
| **[`report/phase2/stage_2_4_3d_heat_flow_report.md`](./report/phase2/stage_2_4_3d_heat_flow_report.md)** | **Stage 2.4 Technical Report**: Full 3D shelter envelope (`SOLID87` quadratic tets, 73,335 elements), vector field $(\text{TFX}, \text{TFY}, \text{TFZ})$ extraction, and 3D PyVista glyphs/cutaways. | Reference for 3D PyVista vector field visualization pipelines. |
| **[`report/phase2/stage_2_5_energy_balance_report.md`](./report/phase2/stage_2_5_energy_balance_report.md)** | **Stage 2.5 Technical Report**: 3D surface integral energy audit in Watts; First Law of Thermodynamics closure ($2.08\%$ error); Cool roof saves $196\,\text{W}$ of heat gain. | Reference for surface power audits and energy conservation validation. |
| **[`report/phase3/stage_3_1_transient_report.md`](./report/phase3/stage_3_1_transient_report.md)** | **Stage 3.1 Technical Report**: Transient FEA (`PLANE77`, `ANTYPE, TRANS`), thermal storage ($\rho C_p$), 24h diurnal cycle, Time Lag ($\Delta t_{\text{lag}}=8.0\,\text{h}$), and Decrement ($\mu=0.015$). | Reference for thermal mass storage and diurnal time-stepping setup. |
| **[`report/phase3/stage_3_2_3d_transient_report.md`](./report/phase3/stage_3_2_3d_transient_report.md)** | **Stage 3.2 Technical Report**: Full 3D 48h transient shelter with dynamic sun-position tracking (East $\to$ South $\to$ West solar migration) solved in 25 seconds. | Reference for 3D transient FEA and orientation solar tracking. |
| **[`report/phase4/stage_4_1_eahe_report.md`](./report/phase4/stage_4_1_eahe_report.md)** | **Stage 4.1 Technical Report**: Earth-Air Heat Exchanger (EAHE) underground passive cooling pipeline, Kusuda soil model, and 3D FEA soil domain (`SOLID87`). | Reference for geothermal ground cooling and duct convection. |
| **[`report/phase4/stage_4_2_solar_chimney_report.md`](./report/phase4/stage_4_2_solar_chimney_report.md)** | **Stage 4.2 Technical Report**: Solar Chimney natural buoyancy stack effect, coupled hydraulic loop equilibrium with EAHE, 3D FEA (`SOLID87`), and PyVista 3D streamlines. | Reference for zero-electricity buoyancy ventilation and thermal chimney modeling. |
| **[`report/phase4/stage_4_3_windcatcher_report.md`](./report/phase4/stage_4_3_windcatcher_report.md)** | **Stage 4.3 Technical Report**: Multi-Directional Windcatcher (Malqaf/Badgir) aerodynamics, wetted terracotta evaporative cooling, 24h diurnal night-flushing, and 3D FEA (`SOLID87`). | Reference for wind capture, psychrometric evaporative cooling, and night-sky mass flushing. |
| **[`report/phase5/stage_5_1_climate_pcm_report.md`](./report/phase5/stage_5_1_climate_pcm_report.md)** | **Stage 5.1 Technical Report**: 5 Indian Climate Zones (NBC 2016) benchmarking, non-linear Bio-PCM (`MP, ENTH`), Full Newton-Raphson FEA (`SOLID87`), and PyVista cutaways. | Reference for multi-climate regional modeling and latent phase-change thermal storage. |
| **[`report/phase5/stage_5_2_trombe_wall_report.md`](./report/phase5/stage_5_2_trombe_wall_report.md)** | **Stage 5.2 Technical Report**: Indirect Solar Gain Trombe Wall & Attached Solarium modeling, buoyancy thermo-siphon, 10h stone masonry thermal lag, Leh Ladakh cold winter heating. | Reference for passive solar heating, cold climate design, and cavity thermosiphon dynamics. |
| **[`report/phase6/phase6_optimization_report.md`](./report/phase6/phase6_optimization_report.md)** | **Phase 6 Technical Report**: Multi-Objective Genetic Algorithm (NSGA-II), 3D Pareto Frontier, Knee-point selection, 3D MAPDL validation (`SOLID87`), and parallel coordinates. | Reference for automated design optimization, cost-benefit trade-offs, and final system synthesis. |
| **[`report/phase7/phase7_physics_engine_report.md`](./report/phase7/phase7_physics_engine_report.md)** | **Phase 7 Technical Report**: Production-grade ANSYS Simulation Module & Physics Engine, 3-tier input contracts, Sol-Air/McAdams derivations, 3D First Law energy balance audits ($0.97\%$ error), and PyVista cutaways. | Authoritative reference for Phase 7 Physics Engine schemas, derivations, solver integration, and energy audits. |

---

# 2. Current State

```text
Current Phase:          ALL PHASES (1 through 7) 100% COMPLETED!
Current Objective:      SIH 2026 Passive Thermal Shelter Computational Pipeline Fully Built, Solved, and Validated
Overall Status:         100% OPERATIONAL & VERIFIED (Phases 1.1-1.4, 2.1-2.5, 3.1-3.2, 4.1-4.3, 5.1-5.2, 6.1-6.3, 7.1-7.3)
Last Completed Milestone: Phase 7 Production ANSYS Simulation Module / Physics Engine & Energy Auditor
Current Working Files:  phases/phase7/physics_engine.py, phases/phase7/run_phase7.py, phases/phase7/test_phase7.py
Known Blockers:         None
```

---

# 3. Environment & Technical Stack

- **Operating System**: Windows 11 (x64)
- **Project Root**: `C:\Users\asus\Desktop\temp`
- **Python Version**: `3.13` (Managed via `uv`)
- **Package Manager**: `uv`
- **FEA Physics Engine**: **ANSYS Mechanical APDL 2026 R1** (Internal version `26.1`)
  - Executable Path: `C:\Program Files\ANSYS Inc\v261\ansys\bin\winx64\ansys261.exe`
- **Core Dependencies**:
  - `ansys-mapdl-core` $\ge 0.74.1$ (gRPC interface to MAPDL)
  - `pyvista` $\ge 0.48.4$ (3D interactive mesh rendering, vector glyphs, cutaways)
  - `matplotlib` $\ge 3.10$ (2D engineering charts, diurnal response curves, energy ledgers)
  - `numpy` $\ge 2.2$ (Vectorized post-processing and array mathematics)

---

# 4. Status Classification of All Phases & Stages

| Phase / Stage | Scope & Description | Status | Authoritative Report / Code |
| :--- | :--- | :--- | :--- |
| **Phase 1: 1D & 2D Conduction** | 1D plane wall, composite layered walls, 2D L-corner thermal bridge | **COMPLETED** | [`report/phase1/phase1_report.md`](./report/phase1/phase1_report.md) \| [`phases/phase1/`](./phases/phase1/) |
| **Phase 2 — Stage 2.1** | Robin convective film boundary conditions ($h_{\text{out}}, h_{\text{in}}$) | **COMPLETED** | [`report/phase2/stage_2_1_convection_report.md`](./report/phase2/stage_2_1_convection_report.md) \| [`phases/phase2/convection_wall.py`](./phases/phase2/convection_wall.py) |
| **Phase 2 — Stage 2.2** | Solar radiation flux, Sol-Air temperature ($T_{\text{sol-air}}$), Cool roof coating | **COMPLETED** | [`report/phase2/stage_2_2_solar_radiation_report.md`](./report/phase2/stage_2_2_solar_radiation_report.md) \| [`phases/phase2/solar_radiation.py`](./phases/phase2/solar_radiation.py) |
| **Phase 2 — Stage 2.3** | Internal occupant heat generation ($400\,\text{W}$), Insulation Paradox, Cross-ventilation | **COMPLETED** | [`report/phase2/stage_2_3_internal_heat_report.md`](./report/phase2/stage_2_3_internal_heat_report.md) \| [`phases/phase2/internal_heat.py`](./phases/phase2/internal_heat.py) |
| **Phase 2 — Stage 2.4** | 3D full shelter envelope (`SOLID87`), 3D heat-flux vector fields, PyVista cutaways | **COMPLETED** | [`report/phase2/stage_2_4_3d_heat_flow_report.md`](./report/phase2/stage_2_4_3d_heat_flow_report.md) \| [`phases/phase2/heat_flow_3d.py`](./phases/phase2/heat_flow_3d.py) |
| **Phase 2 — Stage 2.5** | Total 3D energy balance & surface power ledger in Watts ($2.08\%$ First Law error) | **COMPLETED** | [`report/phase2/stage_2_5_energy_balance_report.md`](./report/phase2/stage_2_5_energy_balance_report.md) \| [`phases/phase2/energy_audit_3d.py`](./phases/phase2/energy_audit_3d.py) |
| **Phase 3 — Stage 3.1** | Transient 2D FEA (`PLANE77`), thermal mass storage ($\rho C_p$), Time Lag ($\Delta t_{\text{lag}}$), Decrement ($\mu$) | **COMPLETED** | [`report/phase3/stage_3_1_transient_report.md`](./report/phase3/stage_3_1_transient_report.md) \| [`phases/phase3/transient_thermal.py`](./phases/phase3/transient_thermal.py) |
| **Phase 3 — Stage 3.2** | 3D 48h transient shelter with dynamic solar tracking (East $\to$ South $\to$ West migration) | **COMPLETED** | [`report/phase3/stage_3_2_3d_transient_report.md`](./report/phase3/stage_3_2_3d_transient_report.md) \| [`phases/phase3/transient_3d_shelter.py`](./phases/phase3/transient_3d_shelter.py) |
| **Phase 4 — Stage 4.1** | Earth-Air Heat Exchanger (EAHE) underground passive cooling pipeline | **COMPLETED** | [`report/phase4/stage_4_1_eahe_report.md`](./report/phase4/stage_4_1_eahe_report.md) \| [`phases/phase4/eahe_model.py`](./phases/phase4/eahe_model.py) |
| **Phase 4 — Stage 4.2** | Solar Chimney buoyancy stack draft & coupled off-grid ventilation | **COMPLETED** | [`report/phase4/stage_4_2_solar_chimney_report.md`](./report/phase4/stage_4_2_solar_chimney_report.md) \| [`phases/phase4/solar_chimney.py`](./phases/phase4/solar_chimney.py) |
| **Phase 4 — Stage 4.3** | Windcatcher (Malqaf/Badgir) Aerodynamics & Diurnal Control | **COMPLETED** | [`report/phase4/stage_4_3_windcatcher_report.md`](./report/phase4/stage_4_3_windcatcher_report.md) \| [`phases/phase4/windcatcher.py`](./phases/phase4/windcatcher.py) |
| **Phase 5 — Stage 5.1** | 5 Indian Climate Zones Adaptation & Bio-PCM Latent Heat FEA | **COMPLETED** | [`report/phase5/stage_5_1_climate_pcm_report.md`](./report/phase5/stage_5_1_climate_pcm_report.md) \| [`phases/phase5/climate_pcm.py`](./phases/phase5/climate_pcm.py) |
| **Phase 5 — Stage 5.2** | Trombe Wall Solar Storage & Sunspace Modeling for Cold Regions | **COMPLETED** | [`report/phase5/stage_5_2_trombe_wall_report.md`](./report/phase5/stage_5_2_trombe_wall_report.md) \| [`phases/phase5/trombe_wall.py`](./phases/phase5/trombe_wall.py) |
| **Phase 6: Multi-Objective Opt**| Automated Genetic Algorithm pipeline (Min Cost, Min Discomfort, Max Thermal Autonomy) | **COMPLETED** | [`report/phase6/phase6_optimization_report.md`](./report/phase6/phase6_optimization_report.md) \| [`phases/phase6/optimization_engine.py`](./phases/phase6/optimization_engine.py) |
| **Phase 7: ANSYS Physics Engine**| Modular Production ANSYS Simulation Module, 3-Tier Input Contracts & First Law Energy Auditor | **COMPLETED** | [`report/phase7/phase7_physics_engine_report.md`](./report/phase7/phase7_physics_engine_report.md) \| [`phases/phase7/physics_engine.py`](./phases/phase7/physics_engine.py) |
| **Phase 7: Web App Integration**| FastAPI microservice (`ansys_service/`) & Node.js client adapter (`server/services/ansysClient.js`) connecting real FEA to React UI | **COMPLETED** | [`docs/integration/PHASE_7_MAIN_PROJECT_INTEGRATION_PROGRESS.md`](../docs/integration/PHASE_7_MAIN_PROJECT_INTEGRATION_PROGRESS.md) \| [`server/services/simulationService.js`](../server/services/simulationService.js) |

---

# 5. Core Engineering Principles & Governing Equations

### 1. Steady-State Multi-Layer Conduction
$$R_{\text{total}} = \frac{1}{h_{\text{out}}} + \sum_{i=1}^{N} \frac{L_i}{k_i} + \frac{1}{h_{\text{in}}} \quad \left[\frac{\text{m}^2\cdot\text{K}}{\text{W}}\right], \quad q = \frac{T_{\text{outdoor}} - T_{\text{indoor}}}{R_{\text{total}}} \quad \left[\frac{\text{W}}{\text{m}^2}\right]$$

### 2. Sol-Air Temperature Superposition
Because ANSYS nodal Robin convection (`SF,,CONV`) and surface flux (`SF,,HFLUX`) overwrite each other on the same node, solar radiation is superposed via Sol-Air Temperature:
$$T_{\text{sol-air}}(t) = T_{\text{ambient}}(t) + \frac{\alpha \cdot I_{\text{solar}}(t)}{h_{\text{out}}}$$

### 3. First Law of Thermodynamics for 3D Continuum
$$\iint_{\text{Envelope}} (\vec{q} \cdot \hat{n})\,dA + \iiint_{\text{Indoor}} \dot{q}_{\text{vol}}\,dV = 0 \iff \sum \dot{Q}_{\text{in}} = \sum \dot{Q}_{\text{out}} \quad [\text{Watts}]$$

### 4. Transient Thermal Diffusion with Storage
$$\rho C_p \frac{\partial T}{\partial t} = \nabla \cdot (k \nabla T) + \dot{q}_{\text{vol}}, \quad \text{Thermal Diffusivity: } \alpha = \frac{k}{\rho C_p} \quad [\text{m}^2/\text{s}]$$
- **Thermal Time Lag**: $\Delta t_{\text{lag}} = t(T_{\text{in, peak}}) - t(T_{\text{out, peak}})$ [Hours]
- **Decrement Factor**: $\mu = \frac{T_{\text{in, max}} - T_{\text{in, min}}}{T_{\text{out, max}} - T_{\text{out, min}}} \le 1.0$

---

# 6. Critical ANSYS / PyMAPDL Discoveries & Rules

The next AI **must strictly follow these verified findings**:

1. **2D vs 3D Element Selection**:
   - `PLANE55` (4-node 2D quad) hangs on Windows gRPC $\to$ **Always use `PLANE77`** (8-node quadratic quad).
   - `SOLID70` (8-node brick) fails with `invalid topology for mapped brick meshing` on multi-volume glued geometry $\to$ **Always use `SOLID87`** (10-node quadratic tetrahedral element with `mapdl.mshape(1, "3D")` and `mapdl.mshkey(0)`).
2. **Multi-Volume 3D Geometry Creation**:
   - Never use boolean subtraction `VSBV` followed by `VGLU` (causes non-manifold overlapping contact errors).
   - **Always create 7 discrete orthogonal non-overlapping blocks**: Foundation ($Z \in [0, t_w]$), 4 Walls ($Z \in [t_w, L_z - t_w]$), Roof ($Z \in [L_z - t_w, L_z]$), and Core Air cavity, then call `mapdl.vglue("ALL")`.
3. **Transient Solver Speed & I/O Optimization**:
   - Never use `outres("ALL", "ALL")` on 3D transient meshes (causes 35+ min runtime and disk thrashing).
   - **Always use `outres("ERASE")` + `outres("ALL", "LAST")`** with $h=0.35\,\text{m}$ mesh and fixed time stepping (`AUTOTS, OFF`). This solves a 48-hour 3D transient FEA in **under 25 seconds**.
4. **Vectorized In-Memory Post-Processing**:
   - Never query individual node temperatures using sequential `mapdl.get_value("NODE", ...)` in time loops (creates hundreds of slow gRPC round-trips).
   - Call `nodal_temps = mapdl.post_processing.nodal_temperature()` once per load step to pull the NumPy array into memory and index directly.
5. **Multi-Layer `AGLUE` Entity Renumbering**:
   - `AGLUE` deletes input area indices. Always select layers by spatial bounds: `mapdl.asel("S", "LOC", "X", x_min, x_max)`.
   - Single-layer walls fail on `AGLUE`. Always guard: `if len(assembly.layers) > 1: mapdl.aglue("ALL")`.
6. **Path Imports**:
   - Add `sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))` at the top of all runner scripts so they run smoothly via `uv run python phases/...`.

---

# 7. Practical Command Reference (Copy-Pasteable PowerShell)

### Run Existing Fully-Tested Simulations

```powershell
# 1. Phase 1: 1D Conduction, Composite 4-Layer Wall, & 2D Thermal Bridge
uv run python phases/phase1/run_phase1.py
uv run python phases/phase1/run_phase1_advanced.py

# 2. Phase 2: Robin Convection, Sol-Air Radiation, & Internal Occupant Heat
uv run python phases/phase2/run_phase2_stage1.py
uv run python phases/phase2/run_phase2_stage2.py
uv run python phases/phase2/run_phase2_stage3.py

# 3. Phase 2 Stage 2.4 & 2.5: 3D Heat-Flow Vectors & 3D Total Energy Balance (Watts)
uv run python phases/phase2/run_phase2_stage2_4.py
uv run python phases/phase2/run_phase2_stage2_5.py

# 4. Phase 3: Transient Diurnal Thermal Mass & 3D Solar Path Migration
uv run python phases/phase3/run_phase3_stage1.py
uv run python phases/phase3/run_phase3_stage2.py

# 5. Phase 4: Earth-Air Heat Exchanger, Solar Chimney, & Windcatcher
uv run python phases/phase4/run_phase4_stage1.py
uv run python phases/phase4/run_phase4_stage2.py
uv run python phases/phase4/run_phase4_stage3.py

# 6. Phase 5: 5 Indian Climate Zones, Bio-PCM FEA, & Trombe Wall Cold Heating
uv run python phases/phase5/run_phase5_stage1.py
uv run python phases/phase5/run_phase5_stage2.py

# 7. Phase 6: Multi-Objective Genetic Algorithm (NSGA-II) Optimization
uv run python phases/phase6/run_phase6.py

# 8. Phase 7: Production ANSYS Simulation Module / Physics Engine
uv run python phases/phase7/run_phase7.py
uv run python -m unittest phases/phase7/test_phase7.py
```

### Inspecting Environment & Dependencies

```powershell
# Check Python environment
uv python list
uv pip list

# Test ANSYS MAPDL gRPC connectivity
uv run python test_ansys.py
```

---

# 8. Known Issues / Warnings

| Warning / Issue | Severity | Status | Explanation & Action |
| :--- | :---: | :---: | :--- |
| `***** MAPDL VERIFICATION RUN ONLY *****` | Low (Informational) | **Investigated & Understood** | Normal standard academic / student license banner output by MAPDL. Does not affect solver physics, matrix equations, or result validity. |
| `UserWarning: The following keyword arguments are not used: type` | Low | **Resolved** | PyMAPDL `vatt` signature uses `type_` instead of `type`. Replaced in code. |
| Process Hanging on Long 3D FEA Runs | Medium | **Resolved** | Solved by adding `concurrent.futures.ThreadPoolExecutor(timeout=180.0)` wrapper and optimizing `outres("ALL", "LAST")`. |
| PyVista `extract_surface()` Future Warning | Low | **Resolved** | Always pass `algorithm="dataset_surface"` to `extract_surface()` in PyVista visualizers. |

---

# 9. Master Roadmap Completion & Future Extensions

**ALL 6 ROADMAP PHASES ARE 100% COMPLETED AND FULLY TESTED.**

### Summary of System Capabilities
1. **Multi-Physics Simulation**: 1D/2D/3D thermal conduction (`PLANE77`, `SOLID87`), Robin film convection, solar radiation superposition, internal occupant loads, and thermal mass phase-lag dynamics.
2. **Geo-Solar & Aerodynamic Systems**: Coupled Earth-Air Heat Exchangers (EAHE), rooftop Solar Chimneys, and Multi-Directional Windcatchers (Malqaf/Badgir) delivering zero-electricity cooling.
3. **Advanced Materials & Climate Adaptation**: Multi-climate zone modeling across all 5 Indian zones, Bio-PCM latent heat storage with non-linear enthalpy (`MP, ENTH`), and South-facing Trombe wall solar heating for cold mountain regions.
4. **Intelligent Design Optimization**: Tri-objective NSGA-II genetic algorithm searching parametric shelter configurations to minimize cost and discomfort while maximizing thermal autonomy.

### Potential Future Extensions for Production Deployment
- Integration of live OpenWeatherMap / IMD API streaming data.
- GUI / Web Application wrapper (Next.js / Streamlit) for field deployment by architectural engineers and disaster relief agencies.

---

# 10. AI TAKEOVER INSTRUCTIONS & MANDATORY RULES

When you take over this codebase, you **MUST** strictly adhere to the following workflow:

1. **Read `HANDOFF.md` first** to understand the architecture, completed stages, and technical conventions.
2. **Follow the Documentation Map**: For any deep physical or numerical questions, read the dedicated report in `report/phaseX/`.
3. **Inspect before modifying**: Check existing working scripts in `phases/` and ensure all imports and paths are preserved.
4. **Preserve working code**: Do not restart from scratch, do not rewrite working PyMAPDL solver wrappers, and do not remove existing functionality.
5. **Always validate physics**: Ensure all simulations satisfy the First Law of Thermodynamics ($\sum Q_{\text{in}} = \sum Q_{\text{out}}$) and make physical sense.
6. **Include 3D PyVista Diagrams**: Every new stage/step must generate 3D spatial diagrams (using PyVista) and 2D analytical charts saved to `report/phaseX/figures/`.
7. **MANDATORY FULL DOCUMENTATION FOR EVERY STEP**:
   - Whenever **ANY** new step or sub-step (even incremental steps like `Stage 4.1`, `Stage 4.2`, etc.) is completed, you **MUST** create a dedicated standalone report file: `report/phaseX/stage_X_Y_<topic>_report.md`.
   - **MANDATORY SECTION**: Every report file **MUST** contain a dedicated section titled:  
     `## Walls Faced & How We Overcame Them (Technical Challenges & Engineering Solutions)`  
     documenting the exact obstacles encountered (solver errors, meshing failures, convergence issues, mathematical/API hurdles) and the exact technical solutions applied to overcome them.
   - All figures in reports must use **relative paths** (`./figures/filename.png`) so images render properly in IDEs and markdown viewers.
8. **Update `HANDOFF.md`**: Update this handoff ledger whenever a major phase or stage is completed to maintain continuous AI-to-AI project state clarity.
