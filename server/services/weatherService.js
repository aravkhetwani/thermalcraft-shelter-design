/**
 * Weather Service
 * ===============
 * Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
 *
 * Sources real climate data from Open-Meteo's free, key-less archive API
 * (https://open-meteo.com) instead of the fully hardcoded tables used
 * previously. Falls back to a static approximation (derived from the
 * region's elevation via a standard lapse rate) if the network call fails
 * or times out, so the app still works offline / air-gapped for demos.
 */
import regions from '../mockData/regions.json' with { type: 'json' };
import staticClimate from '../mockData/climateData.json' with { type: 'json' };

const ARCHIVE_URL = 'https://archive-api.open-meteo.com/v1/archive';
const FETCH_TIMEOUT_MS = 8000;
const CACHE_TTL_MS = 1000 * 60 * 60; // 1 hour

// Representative 7-day windows used to sample a typical diurnal profile
// for each season, per the deck's "Season / Date (e.g., Jan 15, Winter)".
const SEASON_WINDOWS = {
  winter: { start: '01-08', end: '01-14', dateRangeDefault: 'jan1-7' },
  summer: { start: '07-08', end: '07-14', dateRangeDefault: 'jul1-7' },
};

// Most recent full calendar year, so the archive API always has data.
const REFERENCE_YEAR = new Date().getFullYear() - 1;

const cache = new Map();

function average(arr) {
  return arr.reduce((a, b) => a + b, 0) / (arr.length || 1);
}

/** Groups an hourly array (N days * 24h) into a 24-value hour-of-day average. */
function hourlyDiurnalAverage(values) {
  const buckets = Array.from({ length: 24 }, () => []);
  values.forEach((v, i) => {
    if (typeof v === 'number' && !Number.isNaN(v)) buckets[i % 24].push(v);
  });
  return buckets.map((b) => (b.length ? Number(average(b).toFixed(2)) : 0));
}

function deriveFallback(regionKey, season) {
  const staticEntry = staticClimate[regionKey]?.[season];
  if (staticEntry) return { ...staticEntry, source: 'static-fallback' };

  // No hardcoded entry for this region — approximate from Ladakh using a
  // standard environmental lapse rate (~6.5°C per 1000m elevation gain).
  const base = staticClimate.ladakh[season];
  const region = regions[regionKey];
  const baseRegion = regions.ladakh;
  const elevationDeltaM = (region?.elevationM ?? baseRegion.elevationM) - baseRegion.elevationM;
  const tempDelta = -(elevationDeltaM / 1000) * 6.5;

  return {
    label: `${region?.label ?? regionKey} — ${season[0].toUpperCase()}${season.slice(1)}`,
    avgTemp: Number((base.avgTemp + tempDelta).toFixed(1)),
    solarIrradiance: base.solarIrradiance,
    windSpeed: base.windSpeed,
    cloudCover: base.cloudCover,
    dateRangeDefault: base.dateRangeDefault,
    ambientTemp: {
      hours: base.ambientTemp.hours,
      values: base.ambientTemp.values.map((v) => Number((v + tempDelta).toFixed(1))),
    },
    solarFlux: base.solarFlux,
    source: 'derived-fallback',
  };
}

async function fetchOpenMeteoArchive(regionKey, season) {
  const region = regions[regionKey];
  const window = SEASON_WINDOWS[season] || SEASON_WINDOWS.winter;
  if (!region) throw new Error(`Unknown region: ${regionKey}`);

  const startDate = `${REFERENCE_YEAR}-${window.start}`;
  const endDate = `${REFERENCE_YEAR}-${window.end}`;

  const url = new URL(ARCHIVE_URL);
  url.searchParams.set('latitude', region.latitude);
  url.searchParams.set('longitude', region.longitude);
  url.searchParams.set('start_date', startDate);
  url.searchParams.set('end_date', endDate);
  url.searchParams.set('hourly', 'temperature_2m,shortwave_radiation,wind_speed_10m,cloud_cover');
  url.searchParams.set('timezone', 'auto');

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, { signal: controller.signal });
    if (!res.ok) throw new Error(`Open-Meteo request failed: ${res.status}`);
    const data = await res.json();
    const hourly = data.hourly;
    if (!hourly?.temperature_2m?.length) throw new Error('Open-Meteo returned no hourly data');

    const ambientValues = hourlyDiurnalAverage(hourly.temperature_2m);
    const solarValues = hourlyDiurnalAverage(hourly.shortwave_radiation);
    const windSpeed = Number(average(hourly.wind_speed_10m.filter((v) => typeof v === 'number')).toFixed(1));
    const cloudCover = Number(average(hourly.cloud_cover.filter((v) => typeof v === 'number')).toFixed(0));
    const avgTemp = Number(average(ambientValues).toFixed(1));

    // Annualized solar irradiance estimate (kWh/m²/year) from the sampled week.
    const weeklyKwhPerM2 = (hourly.shortwave_radiation.reduce((a, b) => a + (b || 0), 0) / 1000) / 7;
    const solarIrradiance = Math.round(weeklyKwhPerM2 * 365);

    return {
      label: `${region.label} — ${season[0].toUpperCase()}${season.slice(1)} (Open-Meteo, ${REFERENCE_YEAR})`,
      avgTemp,
      solarIrradiance,
      windSpeed,
      cloudCover,
      dateRangeDefault: window.dateRangeDefault,
      ambientTemp: { hours: Array.from({ length: 24 }, (_, i) => i), values: ambientValues },
      solarFlux: { hours: Array.from({ length: 24 }, (_, i) => i), values: solarValues },
      source: 'open-meteo',
    };
  } finally {
    clearTimeout(timeout);
  }
}

export async function getClimateProfile(region, season) {
  const regionKey = (region || 'ladakh').toLowerCase();
  const seasonKey = (season || 'winter').toLowerCase();
  const cacheKey = `${regionKey}_${seasonKey}`;

  const cached = cache.get(cacheKey);
  if (cached && Date.now() - cached.at < CACHE_TTL_MS) return cached.value;

  try {
    const value = await fetchOpenMeteoArchive(regionKey, seasonKey);
    cache.set(cacheKey, { at: Date.now(), value });
    return value;
  } catch (err) {
    console.warn(`[weatherService] Live weather fetch failed for ${cacheKey}: ${err.message}. Using fallback.`);
    const value = deriveFallback(regionKey, seasonKey);
    cache.set(cacheKey, { at: Date.now(), value });
    return value;
  }
}

export function listRegions() {
  return Object.entries(regions).map(([value, r]) => ({
    value,
    label: r.label,
    latitude: r.latitude,
    longitude: r.longitude,
    elevationM: r.elevationM,
  }));
}
