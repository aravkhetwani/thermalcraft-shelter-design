"""
FastAPI Server Entry Point for ANSYS Simulation Engine
======================================================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System

Run with:
    uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

import sys
import platform
import traceback
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Ensure 'Ansys simulation' root is in sys.path
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from .schemas import (
    SimulationRequest,
    SimulationResponse,
    HealthResponse,
)
from .service import execute_ansys_simulation

app = FastAPI(
    title="Passive Thermal Shelter — ANSYS MAPDL Simulation Engine",
    version="1.0.0",
    description="Microservice providing real-time 3D finite element thermal simulations via ANSYS MAPDL (SOLID87) for SIH 2026."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint to verify service readiness and ANSYS MAPDL availability."""
    ansys_available = False
    ansys_version = "None"

    try:
        from engine.ansys_session import find_ansys_executable
        ansys_exe, ver = find_ansys_executable()
        if ansys_exe:
            ansys_available = True
            ansys_version = str(ver)
    except Exception as e:
        ansys_version = f"Error: {e}"

    return HealthResponse(
        status="healthy",
        ansys_version=ansys_version,
        ansys_available=ansys_available,
        platform=platform.platform(),
    )


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest):
    """Executes full FEA simulation via ANSYS MAPDL and returns structured results."""
    try:
        response = execute_ansys_simulation(request)
        return response
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ANSYS FEA Simulation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
