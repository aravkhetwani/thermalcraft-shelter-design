# API Contract Specification — Public vs. Internal

> **Authoritative API Specification**  
> Formally defines the boundary between the **Public API (React ↔ Node.js)** and the **Internal API (Node.js ↔ FastAPI)**.

---

## 1. Public API Contract (React Client ↔ Node.js Server)

Base URL: `http://localhost:4000/api`

### 1.1 `GET /api/materials`
Returns the material property library.

**Response (200 OK)**:
```json
[
  {
    "id": "rammed-earth",
    "name": "Rammed Earth",
    "thicknessCm": 30,
    "density": 1994.0,
    "thermalConductivity": 0.27,
    "heatCapacity": 1.0,
    "color": "#a97a4f",
    "description": "High thermal mass traditional high-altitude material."
  }
]
```

### 1.2 `GET /api/climate?region=ladakh&season=winter`
Returns 24h diurnal climate profile.

**Response (200 OK)**:
```json
{
  "label": "Ladakh — Winter",
  "avgTemp": -18.2,
  "solarIrradiance": 1950,
  "windSpeed": 14.5,
  "cloudCover": 15,
  "dateRangeDefault": "jan1-7",
  "ambientTemp": {
    "hours": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    "values": [-20.5, -21.0, -21.5, -22.0, -22.5, -22.0, -21.0, -19.5, -17.0, -14.0, -12.0, -11.0, -10.5, -11.0, -12.5, -14.5, -16.5, -18.0, -19.0, -19.5, -20.0, -20.5, -20.8, -21.0]
  },
  "solarFlux": {
    "hours": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    "values": [0, 0, 0, 0, 0, 0, 50, 220, 450, 680, 850, 950, 980, 920, 780, 560, 320, 110, 0, 0, 0, 0, 0, 0]
  }
}
```

### 1.3 `POST /api/run-simulation` (and `GET /api/simulation-result`)
Executes thermal simulation and returns structured physical and performance results.

**Request Body**:
```json
{
  "materialCombo": "rammed-earth+pcm",
  "orientation": "south",
  "size": "medium",
  "shape": "dome"
}
```

**Response (200 OK)** — **Frozen Schema**:
```json
{
  "id": "rammed-earth+pcm_south_medium_dome",
  "source": "ansys-live",
  "insideTemp": {
    "hours": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    "values": [4.2, 3.8, 3.5, 3.2, 3.0, 3.2, 4.1, 6.5, 9.8, 13.2, 16.5, 18.2, 19.1, 18.8, 17.2, 15.1, 12.4, 9.8, 7.5, 6.2, 5.4, 4.9, 4.5, 4.3]
  },
  "ambientTemp": {
    "hours": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    "values": [-20.5, -21.0, -21.5, -22.0, -22.5, -22.0, -21.0, -19.5, -17.0, -14.0, -12.0, -11.0, -10.5, -11.0, -12.5, -14.5, -16.5, -18.0, -19.0, -19.5, -20.0, -20.5, -20.8, -21.0]
  },
  "solarEnergy": {
    "hours": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    "valuesKwh": [0, 0, 0, 0, 0, 0, 0.45, 1.98, 4.05, 6.12, 7.65, 8.55, 8.82, 8.28, 7.02, 5.04, 2.88, 0.99, 0, 0, 0, 0, 0, 0]
  },
  "totalSolarKwh": 61.83,
  "heatFlow": {
    "roofW": 84,
    "wallW": 126,
    "openingsW": 42
  },
  "efficiencyScore": 91,
  "mostEfficientCombo": "PCM + Multi-material",
  "energySavedPercent": 78
}
```

---

## 2. Internal API Contract (Node.js Server ↔ Python FastAPI)

Base URL: `http://localhost:8000`

### 2.1 `GET /health`
Returns readiness of the Python simulation environment and ANSYS MAPDL.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "service": "ansys-physics-engine",
  "pymapdl_available": true,
  "ansys_version": "26.1"
}
```

### 2.2 `POST /simulate`
Executes finite element thermal simulation in ANSYS MAPDL and returns structured physical field results.

**Request Body (`SimulationRequest`)**:
```json
{
  "simulation_id": "SIM-20260908-0001",
  "climate": {
    "ambient_temp_c": -18.2,
    "solar_irradiance_peak_w_m2": 980.0,
    "wind_speed_m_s": 4.5,
    "relative_humidity_pct": 25.0,
    "diurnal_swing_c": 12.0,
    "zone_name": "ladakh_winter"
  },
  "shelter": {
    "length_m": 4.0,
    "width_m": 3.0,
    "height_m": 2.8,
    "wall_thickness_m": 0.30,
    "roof_thickness_m": 0.20,
    "floor_thickness_m": 0.25,
    "shape_type": "dome",
    "size_preset": "medium"
  },
  "materials": {
    "wall_material": {
      "name": "Rammed Earth",
      "conductivity_w_m_k": 0.27,
      "density_kg_m3": 1994.0,
      "specific_heat_j_kg_k": 1000.0,
      "thickness_m": 0.30
    },
    "has_pcm": true,
    "pcm_melt_temp_c": 21.0,
    "pcm_latent_heat_j_kg": 210000.0,
    "pcm_thickness_m": 0.025,
    "roof_solar_absorptivity": 0.85,
    "wall_solar_absorptivity": 0.70
  },
  "internal_loads": {
    "occupant_count": 4,
    "sensible_heat_per_person_w": 100.0,
    "equipment_load_w": 100.0
  },
  "settings": {
    "mode": "STEADY_STATE",
    "mesh_size_m": 0.20,
    "log_level": "WARNING"
  }
}
```

**Response (`SimulationResponse`)**:
```json
{
  "simulation_id": "SIM-20260908-0001",
  "status": "SUCCESS",
  "source": "ansys-live",
  "execution_time_seconds": 16.2,
  "mean_indoor_temp_c": 6.8,
  "min_envelope_temp_c": -18.2,
  "max_envelope_temp_c": 28.5,
  "surfaces": {
    "Roof (Solar + Air)": { "area_m2": 12.0, "mean_flux_w_m2": 7.0, "heat_rate_watts": 84.0, "is_input": true },
    "South Wall (Sunlit)": { "area_m2": 8.4, "mean_flux_w_m2": 15.0, "heat_rate_watts": 126.0, "is_input": true },
    "Ground Foundation Sink": { "area_m2": 12.0, "mean_flux_w_m2": 18.0, "heat_rate_watts": 216.0, "is_input": false }
  },
  "energy_balance": {
    "total_heat_in_watts": 710.0,
    "internal_generation_watts": 500.0,
    "total_energy_input_watts": 1210.0,
    "total_heat_out_watts": 1198.5,
    "residual_watts": 11.5,
    "balance_error_pct": 0.95,
    "is_conserved": true
  }
}
```
