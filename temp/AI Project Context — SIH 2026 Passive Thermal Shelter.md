# SIH 2026 — Passive Thermal Shelter
## AI Project Context, Architecture, Current State & Development Specification

> **Purpose of this document:**  
> This file is the persistent context for an AI coding/research agent working on this project.  
> Read this document completely before modifying, creating, or restructuring project files.
>
> The goal is to allow a new AI session/agent to continue development without losing the decisions, architecture, experiments, environment setup, and ANSYS/Python integration knowledge established so far.

---

# 1. Project Overview

## Project Type

Smart/optimized passive shelter design system for **Smart India Hackathon (SIH) 2026**.

The project focuses on designing shelters that provide better thermal comfort through **region-specific passive design**, reducing dependence on external heating/cooling systems.

The system should eventually take environmental/climate conditions and shelter-design parameters as inputs, simulate thermal performance using ANSYS, process the simulation results using Python, and identify/improve designs that provide better indoor thermal comfort.

---

# 2. SIH Problem Background

The problem statement is based on the following concept:

> Ambient atmospheric conditions affect the temperature inside a shelter, making thermal management necessary for maintaining a comfortable indoor temperature.

Existing shelters are often designed generically rather than according to the specific climatic requirements of the region.

As a result:

- shelters may not be energy efficient,
- indoor temperatures can become uncomfortable,
- external thermal management systems may be required,
- energy consumption increases,
- a single shelter design may not work optimally across different geographical/climatic regions.

The proposed solution is to develop **area-specific smart shelter designs** that use passive thermal-management principles.

The long-term goal is a **one-time, region-specific design solution** that reduces the need for continuous active thermal management.

---

# 3. Main Project Goal

Build a computational design and simulation pipeline that can answer:

> **"Given a particular climate and shelter configuration, how thermally comfortable will the shelter be, and what design/material configuration should be used to improve its performance?"**

The system should eventually be able to:

1. Accept climate/environmental data.
2. Accept shelter dimensions and design parameters.
3. Generate or modify a shelter model.
4. Assign materials and thermal properties.
5. Apply realistic environmental boundary conditions.
6. Send the model to ANSYS.
7. Run thermal/CFD simulations.
8. Retrieve simulation results.
9. Process results in Python.
10. Calculate thermal-comfort metrics.
11. Compare multiple designs.
12. Identify the best design.
13. Potentially optimize the design automatically.
14. Visualize the final design and its thermal performance.

---

# 4. High-Level Architecture

The intended architecture is:

```text
                 ┌───────────────────────┐
                 │   Climate / User Data │
                 │                       │
                 │ Ambient Temperature   │
                 │ Solar Irradiance      │
                 │ Wind Speed            │
                 │ Humidity              │
                 │ Location              │
                 │ Shelter Parameters    │
                 └───────────┬───────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │ Python Preprocessing  │
                 │                       │
                 │ Validate inputs       │
                 │ Calculate parameters  │
                 │ Generate geometry     │
                 │ Select materials      │
                 │ Create BCs            │
                 └───────────┬───────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │ Python → ANSYS Bridge │
                 │                       │
                 │      PyMAPDL          │
                 └───────────┬───────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │        ANSYS          │
                 │                       │
                 │ Geometry / Mesh       │
                 │ Materials             │
                 │ Boundary Conditions   │
                 │ Thermal Solver        │
                 └───────────┬───────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │ Simulation Results    │
                 │                       │
                 │ Temperature           │
                 │ Heat Flux             │
                 │ Thermal gradients     │
                 │ Other quantities      │
                 └───────────┬───────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │ Python Postprocessing │
                 │                       │
                 │ Analyze results       │
                 │ Calculate metrics     │
                 │ Compare designs       │
                 │ Generate plots        │
                 └───────────┬───────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │ Design Optimization   │
                 │                       │
                 │ Find best geometry    │
                 │ Find materials        │
                 │ Minimize heat gain    │
                 │ Improve comfort       │
                 └───────────────────────┘
```

---

# 5. Technology Stack

## Primary Technologies

### Python

Python is the primary orchestration and intelligence layer.

Responsibilities include:

- input processing,
- climate-data processing,
- geometry parameter generation,
- ANSYS automation,
- simulation execution,
- result extraction,
- numerical analysis,
- visualization,
- optimization,
- reporting.

---

## ANSYS

ANSYS is the physics/simulation engine.

It will be used for:

- thermal simulation,
- heat-transfer analysis,
- potentially CFD,
- temperature distribution,
- heat flux,
- thermal gradients,
- more detailed physics than a simplified Python-only model.

Current installed ANSYS version:

```text
ANSYS 26.1
```

---

## PyMAPDL

The Python ↔ ANSYS connection is currently implemented using:

```text
ansys-mapdl-core
```

Imported as:

```python
from ansys.mapdl.core import launch_mapdl
```

PyMAPDL communicates with MAPDL through a gRPC interface.

Conceptually:

```text
Python
   │
   ▼
PyMAPDL
   │
   │ gRPC
   ▼
ANSYS MAPDL
   │
   ▼
Thermal Solver
```

---

# 6. Important Architectural Decision

## Python is NOT intended to replace ANSYS

Python and ANSYS have different responsibilities.

### Python

Use Python for:

- automation,
- parameter handling,
- climate data,
- optimization,
- data processing,
- visualization,
- orchestration.

### ANSYS

Use ANSYS for:

- detailed physical simulation,
- heat-transfer calculations,
- finite-element calculations,
- thermal field calculation,
- future CFD calculations.

Do not unnecessarily recreate the ANSYS solver in Python.

---

# 7. Current Development Environment

Operating system:

```text
Windows
```

Current project directory:

```text
C:\Users\asus\Desktop\temp
```

Python environment is managed using:

```text
uv
```

Current uv version observed:

```text
uv 0.11.25
```

---

# 8. Python Version Decision

Python 3.14 was initially present on the machine.

However, the PyMAPDL compatibility requirements led to using:

```text
Python 3.13
```

Reason:

The current PyMAPDL package supports Python 3.10–3.13.

Therefore:

> **Use Python 3.13 for this project unless compatibility is explicitly verified for another version.**

Do not casually upgrade the project to Python 3.14.

---

# 9. uv Project Management

The project uses `uv` instead of manually managing a traditional virtual environment.

Important commands:

```powershell
uv init
```

Pin Python:

```powershell
uv python pin 3.13
```

Add PyMAPDL:

```powershell
uv add ansys-mapdl-core
```

Run a Python file:

```powershell
uv run python test.py
```

or:

```powershell
uv run python thermal_test.py
```

### Important

Prefer:

```powershell
uv run python script.py
```

for running Python scripts in this project.

The command:

```powershell
uv run script.py
```

is not the standard way to explicitly run a Python source file.

---

# 10. Current Project Environment

The project previously had a normal `venv` created using Python 3.14.

That approach was abandoned in favor of the uv-managed Python 3.13 project environment.

The intended workflow is now:

```text
uv project
   │
   ├── Python 3.13
   │
   └── ansys-mapdl-core
```

Do not recreate the environment with Python 3.14 unless compatibility has been verified.

---

# 11. First Successful Python → ANSYS Test

The first major milestone was successfully establishing communication between Python and ANSYS.

Test concept:

```python
from ansys.mapdl.core import launch_mapdl

mapdl = launch_mapdl()

print("Connected to ANSYS MAPDL")

mapdl.input_strings("""
*SET,A,25
*SET,B,4
*SET,C,A*B
""")

result = mapdl.parameters["C"]

print("ANSYS calculated:", result)

mapdl.exit()
```

The result was:

```text
Connected to ANSYS
ANSYS calculated: 100.0
ANSYS closed.
```

This proved:

```text
Python
   ↓
PyMAPDL
   ↓
ANSYS MAPDL
   ↓
ANSYS calculation
   ↓
Result returned to Python
```

---

# 12. Important PyMAPDL Detail

A multiline MAPDL command block should be sent using:

```python
mapdl.input_strings("""
...
""")
```

rather than relying on:

```python
mapdl.run("""
...
""")
```

for multiline command blocks.

This was discovered during debugging.

For individual commands, normal PyMAPDL wrappers can be used:

```python
mapdl.prep7()
mapdl.et(...)
mapdl.mp(...)
mapdl.solve()
```

---

# 13. First Successful Thermal Simulation

A simple 2-D thermal wall model was successfully implemented.

This is an important proof-of-concept milestone.

The model represents a wall:

```text
Outside                     Inside

40°C                         25°C
 │                            │
 │                            │
 ▼                            ▼

x=0                          x=1
┌──────────────────────────────┐
│                              │
│          WALL                │
│                              │
└──────────────────────────────┘
          thickness = 1 m

height = 0.2 m
```

Material thermal conductivity:

```text
k = 0.8 W/(m·K)
```

Boundary conditions:

```text
Outside temperature = 40°C
Inside temperature  = 25°C
```

---

# 14. ANSYS Element Used

The initial attempt used:

```text
PLANE55
```

That approach caused problems/stalling in the current setup.

The working implementation switched to:

```text
PLANE77
```

Therefore the current known-good thermal proof of concept uses:

```python
mapdl.et(1, "PLANE77")
```

PLANE77 is a 2-D 8-node thermal solid element.

### Important

Do not automatically switch back to PLANE55.

If changing element types, verify compatibility with ANSYS 26.1 first.

---

# 15. Working Thermal Model

The following logic represents the known-working thermal simulation:

```python
from ansys.mapdl.core import launch_mapdl
import matplotlib.pyplot as plt

print("1. Starting ANSYS...")

mapdl = launch_mapdl(
    loglevel="DEBUG",
    print_com=True
)

print(f"2. Connected to ANSYS {mapdl.version}")

mapdl.clear()
mapdl.prep7()

# Element
mapdl.et(1, "PLANE77")

# Material
thermal_conductivity = 0.8
mapdl.mp("KXX", 1, thermal_conductivity)

# Geometry
width = 1.0
height = 0.2

mapdl.blc4(
    0,
    0,
    width,
    height
)

# Mesh
mapdl.esize(0.05)
mapdl.amesh("ALL")

# Boundary conditions
outside_temperature = 40
inside_temperature = 25

mapdl.nsel("S", "LOC", "X", 0)
mapdl.d("ALL", "TEMP", outside_temperature)

mapdl.nsel("S", "LOC", "X", width)
mapdl.d("ALL", "TEMP", inside_temperature)

mapdl.allsel()

# Solve
mapdl.finish()
mapdl.slashsolu()
mapdl.antype("STATIC")
mapdl.solve()
mapdl.finish()

# Post-processing
mapdl.post1()
mapdl.set("LAST")

nodal_temperatures = (
    mapdl.post_processing.nodal_temperature()
)

nodes = mapdl.mesh.nodes

x_coordinates = nodes[:, 0]
y_coordinates = nodes[:, 1]

print(
    "Number of nodes:",
    len(nodal_temperatures)
)

print(
    "Minimum temperature:",
    nodal_temperatures.min(),
    "°C"
)

print(
    "Maximum temperature:",
    nodal_temperatures.max(),
    "°C"
)

for i in range(
    min(10, len(nodal_temperatures))
):
    print(
        f"Node {i + 1}: "
        f"X={x_coordinates[i]:.3f} m, "
        f"Y={y_coordinates[i]:.3f} m, "
        f"T={nodal_temperatures[i]:.2f} °C"
    )

# Visualization
plt.figure(figsize=(10, 3))

scatter = plt.scatter(
    x_coordinates,
    y_coordinates,
    c=nodal_temperatures,
    cmap="hot",
    s=50
)

plt.colorbar(
    scatter,
    label="Temperature (°C)"
)

plt.xlabel("X position (m)")
plt.ylabel("Y position (m)")

plt.title(
    "Temperature Distribution Through Wall"
)

plt.tight_layout()
plt.show()

mapdl.exit()
```

---

# 16. Successful Thermal Simulation Output

The successful simulation produced:

```text
Connected to ANSYS 26.1

Number of nodes: 289

Minimum temperature: 25.0 °C
Maximum temperature: 40.0 °C
```

Example nodal values:

```text
Node 1: X=0.000 m, Y=0.000 m, T=40.00 °C
Node 2: X=1.000 m, Y=0.000 m, T=25.00 °C
Node 3: X=0.025 m, Y=0.000 m, T=39.63 °C
Node 4: X=0.050 m, Y=0.000 m, T=39.25 °C
Node 5: X=0.075 m, Y=0.000 m, T=38.88 °C
Node 6: X=0.100 m, Y=0.000 m, T=38.50 °C
Node 7: X=0.125 m, Y=0.000 m, T=38.13 °C
Node 8: X=0.150 m, Y=0.000 m, T=37.75 °C
Node 9: X=0.175 m, Y=0.000 m, T=37.38 °C
Node 10: X=0.200 m, Y=0.000 m, T=37.00 °C
```

Mesh:

```text
Nodes:    289
Elements: 80
```

Geometry:

```text
Width:  1.0 m
Height: 0.2 m
```

---

# 17. What This Simulation Actually Proves

This proof-of-concept demonstrates that the project can already perform the following pipeline:

```text
Python
   ↓
Start ANSYS
   ↓
Define thermal element
   ↓
Define material
   ↓
Create geometry
   ↓
Generate mesh
   ↓
Apply temperature boundary conditions
   ↓
Run ANSYS thermal solver
   ↓
Read nodal temperatures
   ↓
Return results to Python
   ↓
Plot temperature distribution
```

This is the foundation for the full SIH system.

---

# 18. How ANSYS Solver Behaves

The user initially expected the solver to potentially keep "computing" until a physical thermal process reached equilibrium.

For the current model, that is not what happens.

The current simulation is:

```text
STATIC
STEADY-STATE
THERMAL
```

Conceptually, ANSYS solves a mathematical thermal system similar to:

```text
[K]{T} = {Q}
```

where:

- `K` = thermal conductivity/system matrix,
- `T` = unknown temperatures,
- `Q` = thermal loads/boundary effects.

Therefore:

```python
mapdl.solve()
```

blocks until the ANSYS solver has finished.

The current simple linear problem solves very quickly.

More complicated simulations may involve:

- nonlinear iterations,
- transient time steps,
- radiation,
- temperature-dependent materials,
- convection,
- CFD iterations,
- coupled physics.

Those should be added later.

---

# 19. ANSYS Debugging / Logging

During development, ANSYS should be launched with:

```python
mapdl = launch_mapdl(
    loglevel="DEBUG",
    print_com=True
)
```

Useful options include:

```text
loglevel
print_com
log_apdl
mapdl_output
```

The current PyMAPDL installation was inspected using:

```powershell
uv run python -c "import inspect; from ansys.mapdl.core import launch_mapdl; print(inspect.signature(launch_mapdl))"
```

The observed function supports options including:

```text
exec_file
run_location
jobname
nproc
port
ip
mode
version
start_instance
ram
timeout
cleanup_on_exit
clear_on_connect
override
additional_switches
license_type
loglevel
log_apdl
print_com
mapdl_output
transport_mode
graphics_backend
...
```

When debugging ANSYS integration, inspect the installed version's signature/documentation instead of assuming an API parameter exists.

---

# 20. Important Debugging Discovery: MAPDL Command Log

A debug log was captured from the thermal simulation.

The log demonstrated that Python commands were being translated into actual MAPDL commands.

Examples included:

```text
/PREP7
ET,1,PLANE77
MP,KXX,1,0.8
BLC4,0,0,1.0,0.2
ESIZE,0.05
AMESH,ALL
```

Then boundary conditions:

```text
NSEL,S,LOC,X,0
D,ALL,TEMP,40

NSEL,S,LOC,X,1.0
D,ALL,TEMP,25
```

Then solution:

```text
/SOLU
ANTYPE,STATIC
SOLVE
```

Then post-processing:

```text
/POST1
SET,LAST
```

This confirms that the PyMAPDL layer is correctly controlling MAPDL.

---

# 21. Important Result-Extraction Detail

The correct usage is:

```python
mapdl.post_processing.nodal_temperature()
```

with parentheses.

Incorrect:

```python
mapdl.post_processing.nodal_temperature
```

The latter returns a function/method rather than the actual temperature array.

This previously caused:

```text
AttributeError:
'function' object has no attribute 'min'
```

Correct:

```python
nodal_temperatures = (
    mapdl.post_processing.nodal_temperature()
)
```

---

# 22. ANSYS Process Management

During experimentation, multiple ANSYS processes remained active.

The following PowerShell command was used to inspect them:

```powershell
Get-Process |
    Where-Object {
        $_.ProcessName -like "*ansys*"
    }
```

Some processes observed included:

```text
ANSYS
ansyscl
AnsysFWW
```

The main ANSYS process could be terminated if a simulation became stuck.

However:

> Do not casually kill shared licensing/background services such as `ansyscl` or `AnsysFWW` unless necessary.

Prefer proper:

```python
mapdl.exit()
```

when possible.

---

# 23. Current Known Issue: "VERIFICATION RUN ONLY"

The ANSYS debug output repeatedly contained:

```text
***** MAPDL VERIFICATION RUN ONLY *****

DO NOT USE RESULTS FOR PRODUCTION
```

This appeared even though the thermal simulation completed successfully.

This needs to be investigated before treating ANSYS results as production-quality engineering results.

### AI agent requirement

Do NOT simply assume this warning is harmless.

Investigate:

1. Why ANSYS 26.1 is reporting verification mode.
2. Whether the current license is a student/verification configuration.
3. Whether PyMAPDL is launching a verification instance.
4. Whether results are numerically valid for the SIH prototype.
5. Whether any solver limitations are active.
6. Whether a different launch configuration is required.
7. Whether the warning affects result validity or only licensing/testing status.

Use current ANSYS documentation when investigating this.

---

# 24. Current Project Maturity

The project is currently at:

```text
Phase 1 — Python ↔ ANSYS integration proof of concept
```

Completed:

- [x] Python project initialized.
- [x] uv environment established.
- [x] Python 3.13 selected.
- [x] PyMAPDL installed.
- [x] ANSYS detected.
- [x] Python successfully launches ANSYS MAPDL.
- [x] Python sends commands to ANSYS.
- [x] ANSYS performs calculations.
- [x] Python retrieves results.
- [x] Basic thermal model created.
- [x] Geometry generated programmatically.
- [x] Mesh generated programmatically.
- [x] Temperature boundary conditions applied.
- [x] Thermal solver completed.
- [x] Nodal temperature data retrieved.
- [x] Temperature distribution visualized.

Not yet completed:

- [ ] Real shelter geometry.
- [ ] Multiple wall/roof/floor layers.
- [ ] Real material database.
- [ ] Solar radiation.
- [ ] External/internal convection.
- [ ] Wind effects.
- [ ] Humidity/climate integration.
- [ ] Transient simulation.
- [ ] CFD.
- [ ] Indoor air volume.
- [ ] Thermal comfort model.
- [ ] Optimization engine.
- [ ] Automated design comparison.
- [ ] User interface.
- [ ] Final SIH demonstration pipeline.

---

# 25. Development Roadmap

The project should be developed incrementally.

Do NOT jump directly from the simple wall to a huge CFD system.

Use the following progression.

---

## Phase 1 — Integration Proof of Concept

Status:

```text
COMPLETED
```

Demonstrate:

```text
Python → ANSYS → Python
```

with a simple thermal wall.

---

# Phase 2 — Parametric Wall Model

Next goal:

Make the wall model configurable from Python.

Instead of hardcoding:

```python
thermal_conductivity = 0.8
width = 1.0
height = 0.2
outside_temperature = 40
inside_temperature = 25
```

create a configuration object.

Example:

```python
wall_config = {
    "width": 1.0,
    "height": 0.2,
    "thermal_conductivity": 0.8,
    "outside_temperature": 40,
    "inside_temperature": 25,
}
```

Then create functions such as:

```python
def build_wall(mapdl, config):
    ...
```

```python
def solve_wall(mapdl, config):
    ...
```

```python
def extract_results(mapdl):
    ...
```

---

# Phase 3 — Multi-Layer Wall

Introduce realistic shelter construction.

Example:

```text
OUTSIDE
   │
   ▼
┌───────────────────┐
│ Exterior coating  │
├───────────────────┤
│ Insulation        │
├───────────────────┤
│ Structural wall   │
├───────────────────┤
│ Interior coating  │
└───────────────────┘
   │
   ▼
INSIDE
```

Each layer should have its own:

- thickness,
- thermal conductivity,
- density,
- specific heat.

For steady-state analysis, conductivity is immediately important.

For transient analysis:

```text
density
specific heat
```

also become important.

---

# Phase 4 — Full Shelter Geometry

Move from a 2-D wall to a shelter.

Potential geometry parameters:

```text
length
width
height
roof angle
wall thickness
roof thickness
floor thickness
door size
window size
window orientation
overhang
ventilation opening
```

The geometry should be parameterized.

Example:

```python
shelter = {
    "length": ...,
    "width": ...,
    "height": ...,
    "roof_angle": ...,
    "wall_thickness": ...,
    "roof_thickness": ...,
}
```

---

# Phase 5 — Climate Input Layer

The system should eventually accept:

```text
Location
Ambient temperature
Solar irradiance
Wind speed
Relative humidity
Time/date
```

Potential architecture:

```text
Climate Data
     ↓
Python
     ↓
Environmental Boundary Conditions
     ↓
ANSYS
```

The climate layer should be separated from the ANSYS layer.

For example:

```text
climate/
    loader.py
    processor.py
    models.py
```

---

# Phase 6 — Realistic Thermal Boundary Conditions

The simple model currently uses fixed temperatures:

```text
Outside = 40°C
Inside = 25°C
```

This should eventually be replaced/expanded with physically meaningful conditions.

Potential effects:

### External convection

```text
Ambient air
     ↓
Convection
     ↓
Shelter wall
```

### Solar radiation

```text
Sun
 ↓
Solar irradiance
 ↓
Exterior surface
 ↓
Heat absorbed by shelter
```

### Internal heat generation

Potential sources:

- occupants,
- equipment,
- lighting.

### Ground interaction

For floor/ground:

```text
Shelter floor
      ↓
Ground thermal interaction
```

### Ventilation / infiltration

Eventually model air exchange.

---

# Phase 7 — Transient Thermal Simulation

After steady-state simulations are reliable, implement time-dependent simulation.

Example:

```text
06:00 → 20°C
08:00 → 24°C
10:00 → 30°C
12:00 → 35°C
14:00 → 38°C
16:00 → 35°C
18:00 → 30°C
20:00 → 26°C
```

The system should calculate indoor temperature as a function of time:

```text
T_inside(t)
```

This is much more useful for real shelter design than a single steady-state temperature.

---

# Phase 8 — Indoor Air / CFD Model

After the solid thermal model is stable, introduce the indoor air domain.

Conceptually:

```text
             ROOF
        ┌──────────────┐
        │              │
        │   AIR        │
        │   DOMAIN     │
        │              │
        │              │
        └──────────────┘
          FLOOR
```

Potentially simulate:

- natural convection,
- air circulation,
- ventilation,
- hot-air accumulation,
- roof heat effects,
- opening placement.

Do not introduce CFD before the basic thermal workflow is reliable.

---

# Phase 9 — Thermal Comfort

The project ultimately needs a meaningful definition of "good shelter".

Possible metrics can include:

```text
Indoor temperature
Temperature variation
Heat gain
Heat loss
Thermal gradient
Time outside comfort range
Energy requirement
```

A useful initial metric is:

```text
Comfort violation time
=
total time where indoor temperature is
outside the desired comfort range
```

Example:

```text
Comfort range:
20°C ≤ T_inside ≤ 28°C
```

Then:

```text
12 hours simulated

Inside comfort:
10 hours

Outside comfort:
2 hours
```

The design with fewer comfort violations is better.

The exact comfort model should be selected based on the SIH requirements and appropriate standards/research.

---

# Phase 10 — Design Optimization

Once the simulation pipeline works, automate design search.

Potential variables:

```text
wall thickness
insulation thickness
roof thickness
roof angle
window size
window position
ventilation opening
material
orientation
overhang
```

Example:

```text
Design A
wall = 100 mm
insulation = 20 mm
roof angle = 10°

Design B
wall = 150 mm
insulation = 40 mm
roof angle = 20°

Design C
wall = 120 mm
insulation = 60 mm
roof angle = 30°
```

Each design:

```text
Python
   ↓
ANSYS
   ↓
Temperature results
   ↓
Comfort score
```

Then choose the best design.

---

# 26. Optimization Objective

The optimization should eventually consider multiple objectives.

For example:

```text
Minimize:
    indoor temperature deviation
    heat gain
    energy consumption
    material cost

Maximize:
    thermal comfort
    passive performance
    constructability
```

A conceptual objective function could be:

```text
Score =
    w1 × ComfortPenalty
  + w2 × HeatGain
  + w3 × Cost
  + w4 × EnergyRequirement
```

The weights should be configurable rather than hardcoded.

---

# 27. Suggested Software Architecture

As the project grows, avoid putting everything into one Python file.

Suggested structure:

```text
SIH_2026/
│
├── README.md
├── PROJECT_CONTEXT.md
├── pyproject.toml
├── uv.lock
│
├── src/
│   └── shelter/
│       │
│       ├── __init__.py
│       │
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py
│       │
│       ├── climate/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   └── processor.py
│       │
│       ├── geometry/
│       │   ├── __init__.py
│       │   └── shelter_geometry.py
│       │
│       ├── materials/
│       │   ├── __init__.py
│       │   └── database.py
│       │
│       ├── ansys/
│       │   ├── __init__.py
│       │   ├── connection.py
│       │   ├── model.py
│       │   ├── thermal.py
│       │   └── results.py
│       │
│       ├── simulation/
│       │   ├── __init__.py
│       │   └── runner.py
│       │
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── thermal_metrics.py
│       │   └── comfort.py
│       │
│       ├── optimization/
│       │   ├── __init__.py
│       │   └── optimizer.py
│       │
│       └── visualization/
│           ├── __init__.py
│           └── plots.py
│
├── tests/
│   ├── test_climate.py
│   ├── test_geometry.py
│   ├── test_materials.py
│   └── test_ansys.py
│
├── examples/
│   ├── simple_wall.py
│   └── shelter_demo.py
│
├── data/
│   ├── climate/
│   └── materials/
│
├── results/
│
└── logs/
```

This structure is a target architecture, not a requirement to create everything immediately.

---

# 28. Important Design Principle: Separation of Concerns

Keep these layers independent:

```text
Climate
   ↓
Design Configuration
   ↓
ANSYS Model
   ↓
Simulation
   ↓
Results
   ↓
Analysis
   ↓
Optimization
```

For example:

`climate/loader.py` should not directly contain ANSYS commands.

Similarly:

`ansys/thermal.py` should not contain optimization logic.

This makes the system easier to test and modify.

---

# 29. ANSYS Connection Module

A dedicated ANSYS connection should eventually be created.

Concept:

```python
from ansys.mapdl.core import launch_mapdl


def connect_to_ansys():
    mapdl = launch_mapdl(
        loglevel="DEBUG",
        print_com=True
    )

    return mapdl
```

Then:

```python
mapdl = connect_to_ansys()
```

All ANSYS-specific code should eventually use this connection.

---

# 30. Simulation Lifecycle

A simulation should follow a predictable lifecycle:

```text
START
  │
  ▼
Connect to ANSYS
  │
  ▼
Clear previous model
  │
  ▼
Enter preprocessing
  │
  ▼
Define element types
  │
  ▼
Define materials
  │
  ▼
Create geometry
  │
  ▼
Generate mesh
  │
  ▼
Apply boundary conditions
  │
  ▼
Solve
  │
  ▼
Post-process
  │
  ▼
Extract results
  │
  ▼
Return Python data
  │
  ▼
Close ANSYS
  │
  ▼
END
```

---

# 31. Error Handling

The final system must not silently fail.

Potential errors:

```text
ANSYS unavailable
ANSYS license unavailable
MAPDL startup failure
Invalid geometry
Invalid material
Mesh failure
Solver convergence failure
Missing climate data
Invalid boundary conditions
Result extraction failure
```

Use explicit exceptions/logging.

Example:

```python
try:
    mapdl.solve()
except Exception as exc:
    logger.exception(
        "ANSYS thermal solve failed"
    )
    raise
```

---

# 32. Logging Requirements

The system should eventually create logs such as:

```text
logs/
    ansys.log
    simulation.log
    optimization.log
```

At minimum, record:

```text
simulation ID
timestamp
climate inputs
geometry parameters
material parameters
mesh information
boundary conditions
ANSYS version
solver status
result summary
```

This is important because an optimization system may run hundreds of simulations.

---

# 33. Simulation Reproducibility

Every simulation should eventually have a unique configuration.

Example:

```json
{
    "simulation_id": "SIM_001",
    "climate": {
        "ambient_temperature": 35,
        "solar_irradiance": 700,
        "wind_speed": 3
    },
    "geometry": {
        "length": 5,
        "width": 4,
        "height": 3
    },
    "materials": {
        "wall": "..."
    }
}
```

The simulation output should be traceable back to its input.

---

# 34. Result Data Model

Eventually results should be represented in a structured way.

For example:

```python
result = {
    "simulation_id": "...",
    "min_temperature": ...,
    "max_temperature": ...,
    "average_temperature": ...,
    "heat_flux": ...,
    "comfort_score": ...,
}
```

For transient simulations:

```python
result = {
    "time": [...],
    "indoor_temperature": [...],
    "outdoor_temperature": [...],
    "solar_irradiance": [...],
}
```

---

# 35. Visualization Requirements

The system should eventually produce:

### Temperature distribution

```text
2-D/3-D thermal map
```

### Indoor temperature vs time

```text
Temperature
    │
35  │       ╭───╮
30  │    ╭──╯   ╰──╮
25  │────╯         ╰────
20  │
    └────────────────────
       Time
```

### Design comparison

Compare:

```text
Design A
Design B
Design C
```

using:

- maximum indoor temperature,
- average indoor temperature,
- comfort violation time,
- heat gain,
- estimated energy requirement.

---

# 36. Current Known-Good Minimal Test

Before making major architectural changes, preserve a minimal test that proves:

```text
Python → ANSYS → thermal solve → Python result
```

The simple wall simulation should remain available as a regression test/example.

Suggested file:

```text
examples/simple_wall.py
```

If a future change breaks this example, investigate the regression before continuing.

---

# 37. Do Not Overcomplicate the First Prototype

The project should evolve incrementally.

Bad approach:

```text
Immediately build:
Full shelter
+
CFD
+
Radiation
+
Weather API
+
Optimization
+
GUI
+
Database
```

This creates too many simultaneous failure points.

Preferred:

```text
Simple wall
   ↓
Parametric wall
   ↓
Multi-layer wall
   ↓
Shelter geometry
   ↓
Real climate inputs
   ↓
Transient thermal
   ↓
Indoor air
   ↓
Comfort
   ↓
Optimization
   ↓
UI
```

---

# 38. Important Engineering Principle

Do not claim that a simulation result is physically accurate merely because ANSYS produced a number.

The model must be validated.

Validation should eventually compare simulation outputs against:

- analytical solutions,
- simplified thermal calculations,
- published experimental results,
- measured prototype data if available.

For example, the simple wall can be checked using 1-D conduction theory:

```text
Q = k A ΔT / L
```

where:

```text
k = thermal conductivity
A = area
ΔT = temperature difference
L = thickness
```

The ANSYS result should be compared against this analytical expectation.

---

# 39. SIH Demonstration Strategy

The final demo should be understandable to judges.

A good demonstration pipeline could be:

```text
SELECT LOCATION
       ↓
Climate data loaded
       ↓
System determines environmental conditions
       ↓
User selects shelter type / constraints
       ↓
Python generates candidate designs
       ↓
ANSYS simulations run
       ↓
Thermal performance calculated
       ↓
Designs ranked
       ↓
BEST PASSIVE DESIGN
       ↓
Thermal visualization
       ↓
Expected comfort improvement
       ↓
Energy-saving estimate
```

The final interface should hide unnecessary ANSYS complexity from the user.

---

# 40. Potential User-Facing Inputs

The eventual application could accept:

```text
Location
Shelter length
Shelter width
Shelter height
Number of occupants
Budget
Preferred materials
Target comfort range
```

Climate information can either be:

```text
automatically loaded
```

or:

```text
manually supplied
```

for testing.

---

# 41. Potential User-Facing Outputs

The application should eventually show:

```text
Recommended Design
────────────────────────

Wall Material: ...
Roof Material: ...
Insulation Thickness: ...
Roof Angle: ...
Ventilation Configuration: ...

Predicted Indoor Temperature:
XX °C

Outdoor Temperature:
YY °C

Thermal Comfort:
XX%

Heat Gain:
XX W

Estimated Energy Requirement:
XX kWh

Improvement vs Baseline:
XX%
```

These values are illustrative only.

Do not fabricate numerical results before running simulations.

---

# 42. AI Agent Instructions

Any AI agent continuing this project should follow these rules.

## Rule 1 — Preserve working functionality

Do not replace the existing working PyMAPDL connection without a reason.

---

## Rule 2 — Check installed APIs

Before using an unfamiliar PyMAPDL/ANSYS parameter:

- inspect the installed package,
- check the current documentation,
- verify compatibility with ANSYS 26.1.

Do not assume older tutorials are compatible.

---

## Rule 3 — Test incrementally

After each major change:

```text
Run
→ inspect output
→ verify ANSYS
→ verify results
→ continue
```

---

## Rule 4 — Don't hide errors

Never write code that catches an ANSYS error and continues as if the simulation succeeded.

---

## Rule 5 — Preserve the simple thermal example

The simple wall model is the current known-good integration test.

---

## Rule 6 — Don't assume GUI requirements

PyMAPDL primarily controls MAPDL.

ANSYS Workbench/Mechanical GUI and MAPDL are related but are not the same interface.

If GUI visualization/control is required, investigate the appropriate current ANSYS API rather than assuming PyMAPDL provides the Workbench GUI.

---

## Rule 7 — Investigate the verification warning

The following warning needs to be understood before production-level engineering claims:

```text
***** MAPDL VERIFICATION RUN ONLY *****
DO NOT USE RESULTS FOR PRODUCTION
```

---

## Rule 8 — Don't invent scientific results

Simulation results must come from:

```text
ANSYS
```

or validated calculations.

Never fabricate:

- thermal conductivity,
- climate values,
- heat flux,
- temperature,
- energy savings,
- comfort improvement.

If assumptions are necessary, label them clearly.

---

# 43. Current Known Command Workflow

Typical development commands:

### Check uv

```powershell
uv --version
```

### Check Python versions

```powershell
uv python list
```

### Run a script

```powershell
uv run python test.py
```

### Run thermal test

```powershell
uv run python thermal_test.py
```

### Inspect PyMAPDL API

```powershell
uv run python -c "import inspect; from ansys.mapdl.core import launch_mapdl; print(inspect.signature(launch_mapdl))"
```

### Inspect ANSYS processes

```powershell
Get-Process |
    Where-Object {
        $_.ProcessName -like "*ansys*"
    }
```

---

# 44. Current Milestone Summary

## Milestone 1

```text
Python environment
        ↓
uv
        ↓
Python 3.13
        ↓
ansys-mapdl-core
```

Status:

```text
DONE
```

---

## Milestone 2

```text
Python
   ↓
PyMAPDL
   ↓
ANSYS MAPDL
   ↓
Calculation
   ↓
Python
```

Status:

```text
DONE
```

---

## Milestone 3

```text
Python
   ↓
ANSYS
   ↓
2-D thermal wall
   ↓
Temperature BCs
   ↓
Solve
   ↓
Nodal temperatures
   ↓
Python plot
```

Status:

```text
DONE
```

---

## Milestone 4

Next:

```text
Parametric thermal wall
```

Status:

```text
NEXT
```

---

# 45. Immediate Next Task

The next development task should be:

> **Convert the working hardcoded thermal wall example into a reusable parametric thermal simulation module.**

The module should allow Python to specify:

```text
width
height
thermal conductivity
outside temperature
inside temperature
mesh size
```

and return:

```text
minimum temperature
maximum temperature
average temperature
nodal temperatures
node coordinates
```

Prefer a clean API such as:

```python
result = run_wall_simulation(
    width=1.0,
    height=0.2,
    conductivity=0.8,
    outside_temperature=40,
    inside_temperature=25,
    mesh_size=0.05,
)
```

Then:

```python
print(result.minimum_temperature)
print(result.maximum_temperature)
```

The exact implementation can be designed by the AI agent, but it should preserve the currently working ANSYS workflow.

---

# 46. After the Parametric Wall

The next sequence should be:

```text
1. Parametric wall
       ↓
2. Multi-layer wall
       ↓
3. Parametric roof
       ↓
4. Parametric floor
       ↓
5. Combine into shelter
       ↓
6. Add climate inputs
       ↓
7. Add realistic thermal BCs
       ↓
8. Transient simulation
       ↓
9. Thermal comfort
       ↓
10. Design optimization
       ↓
11. Visualization/UI
```

---

# 47. Project Philosophy

The core philosophy is:

> **Use Python to intelligently automate ANSYS rather than manually building every simulation.**

The final system should transform:

```text
Climate Data
+
Shelter Design Parameters
+
Material Properties
```

into:

```text
ANSYS Simulation
```

and then transform:

```text
ANSYS Results
```

into:

```text
Thermal Performance
+
Comfort Metrics
+
Design Ranking
+
Optimization
```

---

# 48. Final Target Architecture

The eventual system should look approximately like:

```text
                        USER
                         │
                         ▼
              ┌────────────────────┐
              │   Input Interface  │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Climate Processing │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Design Generator   │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Material Selector  │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Python Simulation  │
              │    Controller      │
              └─────────┬──────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   PyMAPDL    │
                 └──────┬───────┘
                        │
                        ▼
              ┌────────────────────┐
              │       ANSYS        │
              │ Thermal / CFD      │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Result Extraction  │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Python Analytics   │
              └─────────┬──────────┘
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
     ┌────────────────┐   ┌────────────────┐
     │ Thermal Comfort│   │ Visualization  │
     └───────┬────────┘   └────────────────┘
             │
             ▼
     ┌────────────────┐
     │ Optimization   │
     └───────┬────────┘
             │
             ▼
     ┌────────────────────────┐
     │ Recommended Shelter    │
     │ Design                 │
     └────────────────────────┘
```

---

# 49. Definition of Success

The project is successful when a user can provide something like:

```text
Location:
Mumbai

Shelter:
5m × 4m × 3m

Target indoor temperature:
24–28°C

Occupants:
10

Constraints:
Low cost
Low energy consumption
Passive-first design
```

and the system can automatically:

```text
1. Obtain/process climate conditions
2. Generate candidate shelter designs
3. Assign appropriate materials
4. Build ANSYS models
5. Run simulations
6. Extract temperatures/heat transfer results
7. Calculate thermal comfort
8. Compare designs
9. Optimize parameters
10. Recommend the best design
11. Explain why it is better
12. Visualize its thermal behavior
```

The system should ultimately demonstrate that **region-specific passive shelter design can improve thermal comfort and reduce dependence on active thermal management**.

---

# 50. Current State — One-Sentence Summary

> **The project has successfully established a Python 3.13 + uv + PyMAPDL + ANSYS 26.1 pipeline capable of programmatically creating, meshing, solving, and extracting results from a basic 2-D steady-state thermal wall model; the next step is to turn this proof of concept into a modular parametric shelter simulation and gradually add realistic climate physics, thermal comfort, and optimization.**

---

# 51. AI Agent Startup Instructions

When an AI agent starts working on this repository:

```text
STEP 1
Read PROJECT_CONTEXT.md.

STEP 2
Inspect the existing repository before creating files.

STEP 3
Identify which milestones are already completed.

STEP 4
Do not redo completed setup unless it is broken.

STEP 5
Run the existing simple thermal example before making
major changes.

STEP 6
Implement the next milestone incrementally.

STEP 7
Test Python → PyMAPDL → ANSYS → Python after
each significant ANSYS integration change.

STEP 8
Keep simulation parameters configurable.

STEP 9
Keep climate, geometry, materials, ANSYS,
post-processing, and optimization modular.

STEP 10
Never claim engineering accuracy without validation.
```

---

# 52. Golden Rule

**Do not build the entire final system in one step.**

Build and validate the physics pipeline first:

```text
WORKING
   ↓
PARAMETRIC
   ↓
REALISTIC
   ↓
VALIDATED
   ↓
OPTIMIZED
   ↓
USER-FACING
```

The project should prioritize **correctness and reproducibility over complexity**.

---

## END OF PROJECT CONTEXT