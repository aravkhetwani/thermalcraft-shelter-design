# API Contract (frozen)

This is the contract the React client relies on. It must not change shape,
regardless of what powers it behind the scenes (static mock JSON today; a
database lookup, precomputed-case interpolation, or a live ANSYS trigger
later). Only `services/simulationService.js` should ever need to change.

## `GET /api/materials`

Returns the material property library.

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
    "description": "..."
  }
]
```

## `GET /api/regions`

Returns the selectable region library (coordinates feed both the map display
and the live weather lookup below).

```json
[
  { "value": "ladakh", "label": "Ladakh", "latitude": 34.09, "longitude": 77.58, "elevationM": 3500 }
]
```

## `GET /api/climate?region=&season=`

Returns one climate profile object, sourced live from the free, key-less
Open-Meteo archive API (`source: "open-meteo"`) with a static/derived
fallback (`source: "static-fallback"` | `"derived-fallback"`) if the network
call fails.

```json
{
  "label": "Ladakh — Winter (Open-Meteo, 2025)",
  "avgTemp": -18.2,
  "solarIrradiance": 1950,
  "windSpeed": 14.5,
  "cloudCover": 15,
  "dateRangeDefault": "jan1-7",
  "ambientTemp": { "hours": [0,1,"...",23], "values": [-20.5, "..."] },
  "solarFlux": { "hours": [0,1,"...",23], "values": [0, "..."] },
  "source": "open-meteo"
}
```

## `GET /api/simulation-result?materialCombo=&orientation=&size=&shape=&region=&season=&openings=`

`materialCombo` is one or more material ids joined with `+`
(e.g. `pcm+rammed-earth` for a two-layer composite wall). `openings` is a
JSON-encoded string: `{"doors":1,"windows":2,"ventilation":"medium"}`
(`ventilation` is one of `low`/`medium`/`high`).

## `POST /api/run-simulation`

Same params, sent as a JSON body (`openings` as a plain object, not a JSON
string) instead of a query string. Simulates a 1-2s delay (standing in for
wherever the real computation happens), persists the run to the SQLite run
history, then responds with the same shape as `simulation-result`.

## `GET /api/compare?region=&season=&size=&openings=`

Optimization / comparison sweep: scores every combination of shape x
orientation x material combo for the given site/openings context and
returns a ranked list plus the top pick.

```json
{
  "region": "ladakh",
  "season": "winter",
  "size": "medium",
  "configurationsEvaluated": 84,
  "top": [
    { "comboLabel": "insulated-composite+pcm_south_medium_dome", "label": "Dome + South + Insulated Composite + Pcm", "efficiencyScore": 82, "energySavedPercent": 69 }
  ],
  "best": { "...": "same shape as one entry in top" }
}
```

`mostEfficientCombo` in the simulation-result response is no longer a
hardcoded string — it's filled in from this same sweep.

## `GET /api/history?limit=`

Returns the most recent persisted simulation runs (SQLite, `server/data/history.db`).

### Frozen response shape (both endpoints)

```json
{
  "id": "rammed-earth_south_medium_dome",
  "source": "mock",
  "insideTemp": { "hours": [0,1,"...",23], "values": [-2.1, -3.0] },
  "ambientTemp": { "hours": [0,1,"...",23], "values": [-18.2, -19.0] },
  "solarEnergy": { "hours": [0,1,"...",23], "valuesKwh": [0, 0, 1.2] },
  "totalSolarKwh": 46.8,
  "heatFlow": { "roofW": 12, "wallW": 18, "openingsW": 8 },
  "efficiencyScore": 88,
  "mostEfficientCombo": "Dome + South + Insulated Composite + Pcm",
  "energySavedPercent": 74
}
```

`source` is `"mock"` today. Later values: `"database"` | `"ansys-live"` |
`"interpolated"` — the UI can show a small badge for it without any other
change.

## Swappable internals

`services/simulationService.js` exports `getResult(params)`. Right now it
looks up a precomputed object in `mockData/simulationResults.json`, falling
back to a seeded formulaic generator for combos that aren't precomputed.
Later, swap only the body of `getResult`:

```js
// TODO: swap this function's internals for a DB query or ANSYS-triggered
// result — signature and return shape must not change.
export async function getResult(params) {
  return await db.query(...);       // or
  return await triggerAnsysRun(...);
}
```

The route handlers in `routes/api.js` never change.
