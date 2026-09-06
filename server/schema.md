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

## `GET /api/climate?region=&season=`

Returns one climate profile object.

```json
{
  "label": "Ladakh — Winter",
  "avgTemp": -18.2,
  "solarIrradiance": 1950,
  "windSpeed": 14.5,
  "cloudCover": 15,
  "dateRangeDefault": "jan1-7",
  "ambientTemp": { "hours": [0,1,"...",23], "values": [-20.5, "..."] },
  "solarFlux": { "hours": [0,1,"...",23], "values": [0, "..."] }
}
```

## `GET /api/simulation-result?materialCombo=&orientation=&size=&shape=`

`materialCombo` is one or more material ids joined with `+`
(e.g. `pcm+rammed-earth` for a two-layer composite wall).

## `POST /api/run-simulation`

Same params, sent as a JSON body instead of a query string. Simulates a
1-2s delay (standing in for wherever the real computation happens) before
responding with the same shape as `simulation-result`.

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
  "mostEfficientCombo": "PCM + Multi-material",
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
