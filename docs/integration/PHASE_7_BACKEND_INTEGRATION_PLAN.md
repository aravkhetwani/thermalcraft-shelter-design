# Phase 7 Backend Integration Plan

> **Document Classification**: Engineering Backend Specification  
> **Status**: APPROVED & IN PROGRESS  
> **Target System**: Node.js Express (`server/`) ↔ Python FastAPI (`temp/ansys_service/`) ↔ ANSYS MAPDL 2026 R1

---

## 1. Overview & Objective

The objective of this integration is to connect the real ANSYS thermal simulation physics engine into the existing SIH 2026 Node.js Express backend while preserving the frozen API contract documented in [`server/schema.md`](file:///c:/Users/asus/Desktop/SIH_2026/server/schema.md).

---

## 2. Itemized Backend Changes

| Change Item | File Path | Current Behavior | Required Modification | Category | Risk | Dependencies |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **1. ANSYS HTTP Client** | `server/services/ansysClient.js` | None (new file) | Implement HTTP client connecting Node.js to FastAPI (`http://localhost:8000`), with timeout guard, correlation ID, and error handling | **REQUIRED** | Low | `node-fetch` / native `fetch` |
| **2. Public Schema Adapter** | `server/services/resultAdapter.js` | None (new file) | Translate internal `SimulationResponse` from FastAPI into public JSON schema (`insideTemp`, `ambientTemp`, `solarEnergy`, `totalSolarKwh`, `heatFlow`, `efficiencyScore`, `mostEfficientCombo`, `energySavedPercent`, `source`) | **REQUIRED** | Low | None |
| **3. Simulation Service Facade** | `server/services/simulationService.js` | Reads `mockData/simulationResults.json` with formula fallback | Call `ansysClient.runSimulation(...)` when `SIMULATION_MODE=ansys-live` (or if FastAPI is available); fall back to mock data if `SIMULATION_MODE=mock` | **REQUIRED** | Low | `ansysClient.js`, `resultAdapter.js` |
| **4. Server Environment Config** | `server/.env` / `server/index.js` | Hardcoded port 4000 | Add support for `FASTAPI_URL`, `SIMULATION_MODE`, and timeout environment variables | **RECOMMENDED**| Low | None |
| **5. Contract & Integration Tests**| `server/tests/ansysIntegration.test.js` | None (new file) | Unit & integration tests asserting frozen schema compliance for both mock and `ansys-live` sources | **REQUIRED** | Low | `node:test` / Jest |

---

## 3. Data Flow & Translation Pipeline

```text
React Client (:5173)
       │  POST /api/run-simulation { materialCombo: "rammed-earth+pcm", orientation: "south", size: "medium", shape: "dome" }
       ▼
Node.js Express Server (:4000)
       │  routes/api.js → simulationService.getResult(params)
       │
       ▼
services/ansysClient.js
       │  Builds internal SimulationRequest (maps material IDs to thermal conductivities, sizes to meters, climate to Ladakh winter)
       │  POST http://localhost:8000/simulate
       ▼
Python FastAPI Service (:8000)
       │  Pydantic Validation → phases.phase7.PhysicsPreprocessor
       │  PyMAPDL → SOLID87 FEA Solve → Result Extraction & Energy Balance
       │  Returns internal SimulationResponse JSON
       ▼
services/resultAdapter.js
       │  Formats 24h diurnal inside temperatures, solar kWh, surface heat flow in Watts, efficiency metrics
       │  Sets source = "ansys-live"
       ▼
React Client (:5173)
       │  Receives exact frozen JSON schema defined in server/schema.md
```

---

## 4. Error Handling & Resilience Chain

1. **FastAPI Offline / Unreachable**:
   - `ansysClient.js` catches connection error (`ECONNREFUSED`).
   - If `SIMULATION_MODE=ansys-live` is explicitly requested, returns structured HTTP 503 error (`"ANSYS Simulation Service is currently offline"`).
   - If in auto/fallback mode, logs warning and seamlessly returns deterministic mock data with `source: "mock"`.
2. **ANSYS Convergence / Solver Error**:
   - FastAPI catches solver exception and returns `{ status: "CONVERGENCE_ERROR", error_message: "..." }`.
   - Node.js translates this into a clean user-facing error message without leaking internal stack traces.
3. **Timeout Protection**:
   - Node.js enforces a 60-second request abort timeout preventing indefinite thread hanging.
