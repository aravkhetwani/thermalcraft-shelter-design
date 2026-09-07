# ANSYS Thermal Simulation Learning & Competence Roadmap
## Mastering Heat Flow, 3D Modeling & Thermal Diagnostics for Passive Shelter Design

---

## 🎯 Primary Purpose & Learning Objective

The goal of this roadmap is to build **deep intuitive and computational mastery of thermal physics and ANSYS simulation via PyMAPDL**. 

Rather than treating ANSYS as a "black box" that just spits out colored temperature contours, each stage is engineered so you can answer the fundamental engineering questions:
1. **Where is heat entering the structure?**
2. **Through what paths is heat conducting or convecting?**
3. **Where are thermal bridges and hotspots forming?**
4. **Where and how much heat ($\text{W}$ or $\text{W/m}^2$) is escaping or accumulating?**
5. **How does thermal mass delay and dampen day/night heat waves?**

---

## 🗺️ The 6-Phase Mastery Path Overview

```text
Phase 1: 2D Conduction & Heat Flux Vectors (Visualizing Flow Paths)
   │
   ▼
Phase 2: Realistic Boundary Conditions & Energy Balance Audits (Watts in vs. Watts out)
   │
   ▼
Phase 3: 3D Geometry & Spatial Heat Flow Mapping (Solid Elements & 3D Vector Fields)
   │
   ▼
Phase 4: Transient Analysis & Thermal Mass (Time-Lag, Damping & Diurnal Cycles)
   │
   ▼
Phase 5: Enclosed Air Volumes, Cavities & Ventilation
   │
   ▼
Phase 6: Passive Optimization & Automated Thermal Diagnostics
```

---

## 📘 Phase 1: 2D Conduction Mastery & Heat Flux Vector Tracking

> **Goal:** Move beyond scalar temperatures ($T$) to understand and visualize heat flux vectors ($\vec{q} = -k \nabla T$).

### Stage 1.1 — The Parametric 2D Wall
* **Concept:** Refactor the hardcoded proof-of-concept into a clean function/class where thickness, height, thermal conductivity ($k$), mesh size, and boundary temperatures are variable inputs.
* **Physics & ANSYS Focus:**
  * Element: `PLANE77` (8-node 2D thermal solid).
  * Direct Dirichlet boundary conditions (`TEMP` on lines/nodes).
* **Key Learning Outcome:** Verifying that the 1D temperature profile through the wall matches Fourier's Law:
  $$T(x) = T_{outside} - \frac{T_{outside} - T_{inside}}{L} \cdot x$$

### Stage 1.2 — Heat Flux Vector Extraction & Vector Quiver Plots
* **Concept:** Temperature tells you *how hot* something is; **Heat Flux ($\vec{q}$)** tells you *where heat is flowing and how fast*.
* **Physics & ANSYS Focus:**
  * Extract thermal flux components from MAPDL Postprocessing:
    * `TFX` (Thermal flux in X direction, $\text{W/m}^2$)
    * `TFY` (Thermal flux in Y direction, $\text{W/m}^2$)
    * `TFSUM` (Total thermal flux magnitude, $\text{W/m}^2$)
  * In PyMAPDL: querying element / nodal table results (`mapdl.post_processing.element_values('TF', 'X')` or `ETABLE`).
* **Python Deliverable:** Generate 2D vector quiver plots (arrows showing direction and magnitude of heat flow across the wall).

### Stage 1.3 — Multi-Layer Composite Wall (Conduction in Series)
* **Concept:** Real building walls are composites: Outer Plaster + Brick + Insulation (EPS/Glass Wool) + Inner Plaster.
* **Physics & ANSYS Focus:**
  * Multiple adjacent geometric areas (`BLC4` with shared/glued lines via `AGLUE`).
  * Assigning distinct material IDs (`MAT, 1`, `MAT, 2`, `MAT, 3`) with different thermal conductivities ($k_1, k_2, k_3$).
  * Preserving mesh node continuity across material interfaces.
* **Key Learning Outcome:** Observe temperature drop across insulation layer vs masonry, and verify total thermal resistance $R_{total} = \sum \frac{L_i}{k_i}$.

### Stage 1.4 — 2D Geometric Thermal Bridges (Corners & Junctions)
* **Concept:** Heat doesn't only flow in 1D. At corners (L-junctions, T-junctions) and openings, heat "escapes" faster due to 2D geometric divergence.
* **Physics & ANSYS Focus:**
  * Model an L-shaped corner wall or a wall-roof junction.
  * Analyze heat flux vector bending at the corner.
* **Key Learning Outcome:** Identify high-heat-loss zones (thermal bridges) using heat flux magnitude maps.

---

## 📙 Phase 2: Realistic Boundary Conditions & Energy Balance Auditing

> **Goal:** Graduate from fixed surface temperatures to real ambient convection, solar radiation flux, and quantifying total heat flow rate in Watts.

### Stage 2.1 — Convection Boundary Conditions (Robin / Film BCs)
* **Concept:** Walls don't touch fixed-temperature sources; they interact with moving air through convection ($q = h (T_{surface} - T_{ambient})$).
* **Physics & ANSYS Focus:**
  * Applying film coefficient $h$ ($\text{W/(m}^2\cdot\text{K)}$) and bulk ambient temperature $T_\infty$ (`SF, line_id, CONV, h, T_ambient`).
  * Outdoor wind conditions ($h_{out} \approx 15 - 25\,\text{W/m}^2\text{K}$) vs Indoor still air ($h_{in} \approx 6 - 8\,\text{W/m}^2\text{K}$).
* **Key Learning Outcome:** Observe how surface temperatures differ from air temperatures based on the boundary film resistance ($1/h$).

### Stage 2.2 — Solar Radiation Heat Flux & Surface Absorptivity
* **Concept:** Sunshine adds direct heat flux ($q_{solar} = \alpha \cdot I_{solar}$, where $\alpha$ is solar absorptance and $I$ is irradiance in $\text{W/m}^2$).
* **Physics & ANSYS Focus:**
  * Surface heat flux boundary conditions (`SF, line_id, HFLUX, q_value`).
  * Simulating cool roof coatings (low $\alpha$, high albedo) vs dark surfaces.

### Stage 2.3 — Internal Heat Generation (Occupants & Equipment)
* **Concept:** People and electrical appliances generate internal heat ($Q_{internal}$).
* **Physics & ANSYS Focus:**
  * Internal volumetric heat generation (`BFE, area_id, HGEN, q_gen`) or point/surface heat rate.

### Stage 2.4 — Total Energy Balance Audit ($\sum Q_{in} = \sum Q_{out}$)
* **Concept:** Quantifying the exact number of **Watts** entering through the roof, walls, and escaping through vents/floor.
* **Physics & ANSYS Focus:**
  * Surface reaction heat flow integration (`NFORCE` / `FSUM` / nodal heat flow reaction `HEAT`).
  * Calculate net power in Watts:
    $$Q = \iint q \, dA$$
* **Python Deliverable:** Create an automated Energy Flow Breakdown (e.g., Pie chart/Bar chart: Roof Heat Gain: 62%, East Wall: 23%, West Wall: 15%).

---

## 📕 Phase 3: Transition to 3D Thermal Modeling & Spatial Heat Flow

> **Goal:** Build full 3D thermal domains and track 3D heat flow vectors through walls, roofs, windows, and ground foundations.

### Stage 3.1 — 3D Thermal Elements & Primitives
* **Concept:** Selecting and mastering 3D solid thermal elements.
* **Physics & ANSYS Focus:**
  * Element: `SOLID70` (8-node thermal brick) or `SOLID278` / `SOLID90` (20-node higher order).
  * 3D geometry generation using volumes (`BLOCK`, `VGLUE`, `VSWEEP`, `VMESH`).
  * Managing 3D coordinate selections (`VSEL`, `ASEL`, `NSEL`).

### Stage 3.2 — 3D Single-Room Shelter Envelope
* **Concept:** A full 3D building envelope (4 walls, roof, floor slab on earth).
* **Physics & ANSYS Focus:**
  * Distinct components (Named Components: `CM, ROOF_VOL, VOLU`, `CM, WALLS_VOL, VOLU`, `CM, FLOOR_VOL, VOLU`).
  * Assigning ground temperature boundary condition ($T_{ground}$) to base slab.
  * Assigning orientation-dependent boundary conditions (Solar on Roof and South/West walls, shade on North wall).

### Stage 3.3 — 3D Vector Heat Flow Visualization
* **Concept:** Visualizing 3D thermal fields and identifying where heat is escaping.
* **Physics & ANSYS Focus & Python Deliverable:**
  * 3D Isosurface temperature maps.
  * Cross-sectional slice planes (X-Z and Y-Z plane heat cutaways).
  * 3D 3-component heat flux vectors ($\text{TFX}, \text{TFY}, \text{TFZ}$) visualizer (e.g., using `PyVista` or `Matplotlib 3D`).

### Stage 3.4 — Component-by-Component Heat Loss/Gain Audit
* **Concept:** Automated reporting of total heat entering or leaving through each 3D face.
* **Python Deliverable:** A tabular and graphical summary:
  * Heat entering through Roof ($\text{W}$)
  * Heat entering through South Wall ($\text{W}$)
  * Heat conducted to ground through Floor ($\text{W}$)

---

## 📗 Phase 4: Transient Thermal Dynamics & Thermal Mass Mastery

> **Goal:** Understand the role of time, thermal inertia, phase shift, and decrement factor over a 24-hour day/night cycle.

### Stage 4.1 — Thermal Storage Properties ($\rho, C_p$)
* **Concept:** Steady-state only depends on conductivity ($k$). Transient heat depends on **Thermal Diffusivity**:
  $$\alpha = \frac{k}{\rho \cdot C_p}$$
* **Physics & ANSYS Focus:**
  * Define density (`DENS`) and specific heat capacity (`C` or `SPHT`).
  * Compare high thermal mass materials (stone, rammed earth, brick, concrete) vs lightweight materials (tin sheet, PVC).

### Stage 4.2 — Transient Solver & Time-Stepping (`ANTYPE, TRANS`)
* **Concept:** Simulating time-dependent temperature variations over a 24-hour diurnal cycle.
* **Physics & ANSYS Focus:**
  * Transient analysis setup (`ANTYPE, TRANS`, `TIMINT, ON`, `AUTOTS, ON`).
  * Setting up Multiple Load Steps or time-table boundary conditions for ambient temperature curve $T(t)$ and solar irradiance curve $I(t)$.

### Stage 4.3 — Thermal Lag & Decrement Factor Diagnostics
* **Concept:** 
  * **Thermal Lag (Phase Delay $\Delta t$):** Hours of delay between outdoor peak temperature and indoor peak temperature.
  * **Decrement Factor ($\mu$):** Ratio of indoor temperature swing to outdoor temperature swing.
* **Python Deliverable:**
  * 24-hour transient temperature curves: $T_{outdoor}(t)$, $T_{indoor\_surface}(t)$, $T_{indoor\_air}(t)$.
  * Automated calculation of $\Delta t$ (hours) and $\mu$ (attenuation ratio).

---

## 🏛️ Phase 5: Enclosed Air Domains, Cavities & Ventilation

> **Goal:** Model air spaces inside the shelter, roof air gaps, and natural ventilation heat removal.

### Stage 5.1 — Air Cavity Thermal Modeling
* **Concept:** Double-wall cavities and ventilated roof overhangs create effective thermal resistance or active convective heat flushing.
* **Physics & ANSYS Focus:**
  * Equivalent thermal resistance of air layers (ISO 6946 standard).
  * Modeling the interior indoor air volume as a thermal capacitance node or fluid-thermal domain.

### Stage 5.2 — Natural Ventilation & Infiltration Heat Removal
* **Concept:** Night-time flushing (opening windows at night to dump heat stored in thermal mass).
* **Physics & ANSYS Focus:**
  * Modeling air change rate ($\text{ACH}$ — Air Changes per Hour) as an effective heat sink term ($Q_{vent} = \dot{m} C_p (T_{in} - T_{out})$).

---

## 🚀 Phase 6: Passive Design Toolkit & Automated Optimization

> **Goal:** Use Python to explore, benchmark, and optimize passive strategies for maximum thermal comfort.

### Stage 6.1 — Passive Strategy Simulation Modules
* **Techniques to simulate:**
  1. **Roof Shading & Overhangs:** Geometry modifications blocking high summer sun angles.
  2. **Cool Roof Coating:** High solar reflectance surface boundary conditions.
  3. **Insulation Placement:** External insulation vs Internal insulation comparison.
  4. **Phase Change Materials (PCM):** Non-linear enthalpy-temperature curves (`ENTH` in ANSYS).

### Stage 6.2 — Thermal Comfort Index Calculation
* **Metrics:**
  * Adaptive Thermal Comfort bands (ASHRAE 55 / NBC India 2016).
  * Predicted Mean Vote (PMV) / Predicted Percentage of Dissatisfied (PPD).
  * Discomfort Hours per day/year.

### Stage 6.3 — Automated Shelter Optimization Engine
* **Workflow:**
  * Python optimization loop (e.g., Genetic Algorithm / Bayesian Optimization via `scipy.optimize`).
  * Variables: Wall thickness, insulation thickness, window-to-wall ratio, overhang depth.
  * Objective: Minimize Indoor Discomfort Degree Hours and peak heat gain.

---

## 📊 Summary of Stages & Milestone Tracker

| Phase | Stage | Description | Key ANSYS Element / Command | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | **1.1** | Parametric 2D Wall Function | `PLANE77`, `BLC4`, `D, TEMP` | ✅ **Complete** |
| | **1.2** | Heat Flux Vector Field ($\vec{q}$) | `PLANE77`, `TF X/Y`, Quiver plots | ✅ **Complete** |
| | **1.3** | Multi-Layer Composite Wall | `PLANE77`, Multi-material `MP, KXX`, `AGLUE` | ✅ **Complete** |
| | **1.4** | 2D Corner & Thermal Bridge Analysis | `PLANE77`, L-junction geometry | ✅ **Complete** |
| **Phase 2** | **2.1** | Convective (Film) Boundary Conditions | `SF, node, CONV, h, T_inf` | ✅ **Complete** |
| | **2.2** | Solar Flux & Absorptivity | `SF, node, CONV, h, T_sol_air` | ✅ **Complete** |
| | **2.3** | Internal Heat Generation | `BFE, elem, HGEN` | ✅ **Complete** |
| | **2.4** | 3D Spatial Heat-Flow & PyVista Vectors | `SOLID87`, `TFX/Y/Z`, PyVista Glyphs | ✅ **Complete** |
| | **2.5** | Total Energy Balance & Heat Rate Audit (Watts) | `FSUM`, Surface Heat Flow integration | ⏳ *Next Step* |
| **Phase 3** | **3.1** | 3D Thermal Solid Modeling | `SOLID70` / `SOLID278`, `BLOCK`, `VMESH` | ⬜ Planned |
| | **3.2** | 3D Single Room Shelter Geometry | Named Components (`CM`), Multi-volume gluing | ⬜ Planned |
| | **3.3** | 3D Heat Flux Vector Visualization | 3D vector fields, PyVista slicing | ⬜ Planned |
| | **3.4** | Surface-by-Surface Energy Audit | 3D boundary heat flux integration | ⬜ Planned |
| **Phase 4** | **4.1** | Material Thermal Storage Properties | `MP, DENS`, `MP, C` | ⬜ Planned |
| | **4.2** | 24-hr Diurnal Transient Simulation | `ANTYPE, TRANS`, Time-dependent load steps | ⬜ Planned |
| | **4.3** | Thermal Lag & Decrement Factor | Time-series analysis, Peak delay extraction | ⬜ Planned |
| **Phase 5** | **5.1** | Air Cavity & Double-Wall Modeling | ISO 6946 equivalent cavity resistance | ⬜ Planned |
| | **5.2** | Night-time Ventilation & ACH | Ventilation heat removal source terms | ⬜ Planned |
| **Phase 6** | **6.1** | Passive Strategy Toolkit (Shading/Cool Roof) | Parametric geometry + surface properties | ⬜ Planned |
| | **6.2** | Thermal Comfort Metrics (ASHRAE/NBC) | PMV / PPD / Discomfort Degree Hours | ⬜ Planned |
| | **6.3** | Automated Design Optimization Loop | `scipy.optimize` + PyMAPDL pipeline | ⬜ Planned |

---

## 🛠️ Recommended Development Rules

1. **Step-by-Step Validation:** Never jump to 3D or transient models until the 2D steady-state physics and heat flux extractions are completely validated.
2. **Always Check the Vector Field ($\vec{q}$):** When debugging heat transfer, look at where the arrows point. If heat is flowing in an unexpected direction, check your boundary temperatures and contact interfaces.
3. **Verify Conservation of Energy:** For any steady-state model, total heat entering must equal total heat leaving:
   $$\sum Q_{in} + \sum Q_{generated} = \sum Q_{out}$$
4. **Keep Modules Isolated:** Separate geometry creation, material databases, boundary condition calculation, solver execution, and postprocessing.
