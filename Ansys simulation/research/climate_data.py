"""
Real hourly climate profiles, shared with the rest of ThermalCraft
=====================================================================
Copied verbatim from `server/mockData/climateData.json` (Ladakh winter and
summer — themselves cross-checked against Open-Meteo's live archive API by
`server/services/weatherService.js`) plus the same elevation-lapse-rate
approximation used by `weatherService.js::deriveFallback` /
`Ansys simulation/api/service.py::_climate_for` to extend coverage to the
app's other three regions (Siachen, Spiti, Kaza).

Using REAL, already-verified hour-by-hour (ambient temperature, solar flux)
pairs — rather than sampling ambient temperature and solar irradiance
independently — is what keeps the synthetic dataset physically consistent:
it guarantees the model never sees nonsensical combinations such as
"coldest night-time temperature" paired with "peak midday solar," which a
naive independent-range sampler would otherwise generate.
"""
from typing import Dict, List, Tuple

HOURS = list(range(24))

LADAKH_WINTER = {
    "ambient": [-20.5, -21.2, -21.8, -22.1, -22.3, -22.0, -21.0, -19.2, -17.0, -15.1, -13.6, -12.8,
                -12.4, -12.6, -13.5, -15.0, -16.8, -18.2, -19.1, -19.7, -20.0, -20.2, -20.3, -20.4],
    "solar": [0, 0, 0, 0, 0, 0, 15, 120, 310, 480, 610, 690, 720, 700, 600, 460, 290, 110, 10, 0, 0, 0, 0, 0],
    "wind_speed_m_s": 14.5,
}
LADAKH_SUMMER = {
    "ambient": [4.2, 3.5, 2.9, 2.6, 2.8, 3.6, 5.5, 8.2, 11.0, 13.8, 16.2, 18.0,
                19.1, 19.6, 19.2, 18.0, 16.1, 13.9, 11.5, 9.2, 7.4, 6.1, 5.2, 4.6],
    "solar": [0, 0, 0, 0, 0, 40, 180, 380, 560, 720, 840, 900, 920, 890, 800, 650, 470, 270, 90, 0, 0, 0, 0, 0],
    "wind_speed_m_s": 8.2,
}

# Elevation (m), identical to server/mockData/regions.json.
REGION_ELEVATION_M = {"ladakh": 3500.0, "siachen": 5400.0, "spiti": 3800.0, "kaza": 3650.0}
LAPSE_RATE_C_PER_1000M = 6.5

REGIONS = list(REGION_ELEVATION_M.keys())
SEASONS = ["winter", "summer"]


def _derive_profile(region: str, season: str) -> Dict:
    base = LADAKH_WINTER if season == "winter" else LADAKH_SUMMER
    if region == "ladakh":
        return base
    delta_elev = REGION_ELEVATION_M[region] - REGION_ELEVATION_M["ladakh"]
    temp_delta = -(delta_elev / 1000.0) * LAPSE_RATE_C_PER_1000M
    return {
        "ambient": [v + temp_delta for v in base["ambient"]],
        "solar": base["solar"],
        "wind_speed_m_s": base["wind_speed_m_s"],
    }


_PROFILE_CACHE = {(r, s): _derive_profile(r, s) for r in REGIONS for s in SEASONS}


def get_hourly_climate(region: str, season: str, hour: int) -> Tuple[float, float, float]:
    """Returns (ambient_temp_c, solar_irradiance_w_m2, wind_speed_m_s) for one
    real (region, season, hour-of-day) combination."""
    profile = _PROFILE_CACHE[(region, season)]
    h = int(hour) % 24
    return profile["ambient"][h], profile["solar"][h], profile["wind_speed_m_s"]


def all_region_season_hour_combos() -> List[Tuple[str, str, int]]:
    return [(r, s, h) for r in REGIONS for s in SEASONS for h in HOURS]
