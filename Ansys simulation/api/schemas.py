"""
Pydantic Schemas for ANSYS FastAPI Microservice
===============================================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    """Parameters sent from Node.js backend to Python ANSYS engine."""
    materialCombo: str = Field(default="rammed-earth", description="e.g. 'rammed-earth', 'pcm+rammed-earth'")
    orientation: str = Field(default="south", description="e.g. 'north', 'south', 'east', 'west'")
    size: str = Field(default="medium", description="e.g. 'small', 'medium', 'large'")
    shape: str = Field(default="dome", description="e.g. 'dome', 'rectangular', 'custom'")
    region: Optional[str] = Field(default="ladakh", description="Climate region")
    season: Optional[str] = Field(default="winter", description="Climate season")
    
    # Optional override parameters
    ambient_temp_c: Optional[float] = None
    solar_irradiance_peak_w_m2: Optional[float] = None
    wind_speed_m_s: Optional[float] = None
    occupant_count: Optional[int] = None
    air_changes_per_hour: Optional[float] = None


class TimeSeriesData(BaseModel):
    hours: List[int]
    values: List[float]


class SolarEnergyData(BaseModel):
    hours: List[int]
    valuesKwh: List[float]


class HeatFlowData(BaseModel):
    roofW: float
    wallW: float
    openingsW: float


class VerticalProfilePoint(BaseModel):
    """Mean temperature at a normalized shelter height band (0=floor, 1=roof)."""
    heightFrac: float
    tempC: float


class SimulationResponse(BaseModel):
    """Public frozen contract schema response returned to Node.js backend."""
    id: str
    source: str = "ansys-live"
    insideTemp: TimeSeriesData
    ambientTemp: TimeSeriesData
    solarEnergy: SolarEnergyData
    totalSolarKwh: float
    heatFlow: HeatFlowData
    efficiencyScore: int
    mostEfficientCombo: str
    energySavedPercent: int
    verticalProfile: Optional[List[VerticalProfilePoint]] = None
    raw_physics: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    ansys_version: str
    ansys_available: bool
    platform: str
