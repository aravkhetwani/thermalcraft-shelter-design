# ANSYS Thermal Physics Simulation Module

> **Smart India Hackathon (SIH 2026)** — High Altitude Passive Thermal Shelter System  
> Physics engine powered by **ANSYS Mechanical APDL (2026 R1 / v26.1)** and PyMAPDL.

---

## Directory Structure

```text
Ansys simulation/
├── engine/                       # Core ANSYS FEA thermal physics engine
│   ├── __init__.py               # Public API exports (run_simulation, SimulationInput, etc.)
│   ├── schemas.py                # Typed dataclass contracts & validation
│   ├── physics_preprocessor.py   # McAdams wind correlation, Sol-Air, R-values
│   ├── ansys_session.py          # PyMAPDL session manager & timeout guards
│   ├── geometry_engine.py        # 3D 7-block glued envelope geometry (vglue)
│   ├── material_manager.py       # Linear properties & Bio-PCM enthalpy tables
│   ├── boundary_conditions.py    # Robin surface convection & internal body loads
│   ├── solver_pipeline.py        # SOLID87 meshing & solver execution
│   └── result_extractor.py       # Vectorized flux, surface power, energy auditor
├── api/                          # FastAPI REST microservice
│   ├── __init__.py
│   ├── main.py                   # FastAPI server entrypoint (GET /health, POST /simulate)
│   ├── schemas.py                # Pydantic request & response models
│   └── service.py                # Parameter mapping & diurnal curve generation
├── tests/
│   └── test_simulation.py        # Automated unit & integration tests
├── reports/                      # Engineering reports & documentation ledger
├── run_simulation.py             # Standalone Python simulation runner
└── pyproject.toml                # Dependencies & environment configuration
```

---

## Running the Module

### 1. Start the FastAPI Microservice (Port 8000)
```bash
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Run Standalone Python Simulation
```bash
uv run python run_simulation.py
```

### 3. Run Automated Tests
```bash
uv run python -m unittest tests/test_simulation.py
```
