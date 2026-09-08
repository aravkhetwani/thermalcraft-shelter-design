# High Altitude Passive Thermal Shelter — Simulation & Dashboard System

> **Smart India Hackathon (SIH 2026)**  
> A high-performance passive thermal shelter design and simulation platform tailored for extreme high-altitude cold climates (e.g., Ladakh, -20°C ambient).

The platform couples a dark-themed engineering dashboard with a live **ANSYS Mechanical APDL (2026 R1 / v26.1)** Finite Element thermal physics simulation engine running via PyMAPDL and a FastAPI microservice.

---

## 1. System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│               React Dashboard (Port 5173)               │
│          Vite + Tailwind + Three.js + Recharts          │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP (POST /api/run-simulation, GET /api/simulation-result)
                            ▼
┌─────────────────────────────────────────────────────────┐
│            Node.js Express Server (Port 4000)           │
│  - config.js (SIMULATION_MODE="ansys-live" | "mock")    │
│  - services/ansysClient.js (FastAPI HTTP client)        │
│  - services/resultAdapter.js (Frozen schema enforcement)│
│  - services/simulationService.js (Engine & mock fallback│
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP (POST /simulate, GET /health)
                            ▼
┌─────────────────────────────────────────────────────────┐
│       Python FastAPI Microservice (Port 8000)           │
│  - Ansys simulation/api/main.py (REST API)              │
│  - Ansys simulation/api/service.py (Diurnal curve)      │
│  - Ansys simulation/engine/physics_engine.py (Engine)   │
└───────────────────────────┬─────────────────────────────┘
                            │ gRPC via PyMAPDL
                            ▼
┌─────────────────────────────────────────────────────────┐
│            ANSYS Mechanical APDL (v26.1)                │
│  - SOLID87 10-Node Quadratic Tetrahedral Continuum      │
│  - Robin Convection + Multi-Orientation Sol-Air         │
│  - First Law Surface Power Ledger (Q_in ≈ Q_out)        │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Project Structure

```text
SIH_2026/
├── client/                     # React + Vite frontend dashboard
│   ├── src/
│   │   ├── api/client.js       # HTTP client talking to Node.js backend
│   │   ├── context/SimulationContext.jsx  # State management (inputs, results, loading)
│   │   └── components/
│   │       ├── input/          # Location, Ambient, Shelter Design, Material System
│   │       └── output/         # 3D Viewport, Temperature, Solar Energy, Heat Flow cards
│   └── package.json
│
├── server/                     # Node.js Express API & Adapter
│   ├── config.js               # Port, Simulation Mode, ANSYS URL configurations
│   ├── routes/api.js           # API route handlers
│   ├── services/
│   │   ├── ansysClient.js      # HTTP client to Python FastAPI microservice
│   │   ├── resultAdapter.js    # Enforces frozen public schema (schema.md)
│   │   └── simulationService.js# Swappable physics dispatcher with mock fallback
│   ├── tests/
│   │   └── ansysIntegration.test.js # Automated integration test suite
│   ├── mockData/               # Precomputed offline datasets & materials library
│   ├── schema.md               # Frozen public API contract documentation
│   └── index.js                # Server entrypoint (Port 4000)
│
├── "Ansys simulation"/         # Standalone ANSYS FEA Simulation Engine & Microservice
│   ├── api/                    # FastAPI microservice (Port 8000)
│   │   ├── main.py             # FastAPI app with /health and /simulate
│   │   ├── schemas.py          # Pydantic request & response models
│   │   └── service.py          # Parameter mapping & diurnal curve generation
│   ├── engine/                 # Production ANSYS Physics Engine
│   │   ├── schemas.py          # Typed dataclass contracts
│   │   ├── physics_preprocessor.py # McAdams wind convection, Sol-Air, R-values
│   │   ├── ansys_session.py    # PyMAPDL session manager & timeout guards
│   │   ├── geometry_engine.py  # 3D glued 7-block envelope geometry
│   │   ├── material_manager.py # Linear thermal props & Bio-PCM enthalpy curves
│   │   ├── boundary_conditions.py # Nodal Robin convection & body loads
│   │   ├── solver_pipeline.py  # SOLID87 meshing & solver execution
│   │   ├── result_extractor.py # Vectorized flux, surface power, energy auditor
│   │   └── physics_engine.py   # Master run_simulation() API
│   ├── tests/
│   │   └── test_simulation.py  # Automated Python unit test suite
│   ├── reports/                # Engineering reports & documentation ledger
│   ├── run_simulation.py       # Standalone physics verification script
│   └── README.md               # Dedicated engine documentation
│
└── docs/                       # Integration documentation & API contracts
    └── integration/
        ├── PHASE_7_MAIN_PROJECT_INTEGRATION_PROGRESS.md
        ├── PHASE_7_BACKEND_INTEGRATION_PLAN.md
        └── API_CONTRACT_SPECIFICATION.md
```

---

## 3. Quick Start & Running the Stack

To run the complete system with live ANSYS FEA simulation, start the three services in separate terminals:

### 1. Python FastAPI Simulation Microservice (Port 8000)
```bash
cd "Ansys simulation"
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
*Health Check: `http://localhost:8000/health`*

### 2. Node.js Express API Server (Port 4000)
```bash
cd server
npm install
npm run dev
```
*Test API: `http://localhost:4000/api/materials` or `http://localhost:4000/api/simulation-result`*

### 3. React Frontend Dashboard (Port 5173)
```bash
cd client
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 4. Simulation Modes

You can control how the backend generates results via the `SIMULATION_MODE` environment variable in `server/`:

| Mode | Behavior | Use Case |
| :--- | :--- | :--- |
| `ansys-live` *(Default)* | Connects to FastAPI microservice and executes real 3D `SOLID87` FEA in ANSYS MAPDL. If ANSYS is offline, automatically falls back to mock dataset. | Live production, hackathon demos with ANSYS installed. |
| `mock` | Directly returns precomputed or formulaic mock data with a simulated 1–2s delay without calling Python. | Offline development, machines without ANSYS license. |

To run the backend in strict mock mode:
```bash
# In Windows PowerShell:
$env:SIMULATION_MODE="mock"; npm run dev
```

---

## 5. Verification & Testing

### A. Node.js ↔ ANSYS Integration Test
Runs an automated end-to-end test validating the complete pipeline, health checks, and frozen schema compliance:
```bash
cd server
npm test
```

### B. Python Physics Engine Unit Tests
Executes the test suite inside the `Ansys simulation` directory:
```bash
cd "Ansys simulation"
uv run python -m unittest tests/test_simulation.py
```

---

## 6. Public API Contract

The API contract between React and Node.js is **frozen** and documented in [`server/schema.md`](server/schema.md):

- `GET /api/materials`: Returns available wall and insulation materials.
- `GET /api/climate?region=&season=`: Returns ambient hourly temperature and solar flux.
- `GET /api/simulation-result?materialCombo=&orientation=&size=&shape=`: Fetches simulation results.
- `POST /api/run-simulation`: Triggers simulation computation with JSON payload `{ materialCombo, orientation, size, shape, region, season }`.

### Frozen Response Shape
```json
{
  "id": "pcm+rammed-earth_south_medium_dome",
  "source": "ansys-live",
  "insideTemp": { "hours": [0, 1, 2, "...", 23], "values": [4.1, 3.9, 3.8, "..."] },
  "ambientTemp": { "hours": [0, 1, 2, "...", 23], "values": [-20.5, -21.2, "..."] },
  "solarEnergy": { "hours": [0, 1, 2, "...", 23], "valuesKwh": [0, 0, 0.15, "..."] },
  "totalSolarKwh": 46.8,
  "heatFlow": { "roofW": 47.2, "wallW": 295.2, "openingsW": 260.7 },
  "efficiencyScore": 77,
  "mostEfficientCombo": "PCM + Multi-material",
  "energySavedPercent": 75
}
```

---

## 7. License & Hackathon Context

Built for the **Smart India Hackathon (SIH 2026)** — High Altitude Passive Thermal Shelter Design problem statement.
All thermal calculations comply with the First Law of Thermodynamics and ASHRAE / NBC 2016 building physics standards.
