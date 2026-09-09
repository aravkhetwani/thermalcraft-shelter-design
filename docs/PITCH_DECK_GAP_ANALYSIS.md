# Gap Analysis: ChaiLogic 2.0 Pitch Deck vs. Current Codebase

Source: `ChaiLogic 2.0 - SIH2026.pdf`, compared against `feature/thermal-analysis` @ `6e6671f`.

## Fully missing features (to build)

1. **Real weather/climate data source.** Deck cites OpenWeather, Meteostat, IMD. Codebase has two
   hardcoded JSON/dict tables (`server/mockData/climateData.json`, `Ansys simulation/api/service.py::CLIMATE_HOURLY`)
   covering only Ladakh winter/summer.
2. **Multiple high-altitude regions.** Deck names Ladakh, Siachen, Spiti, Kaza. Region dropdown only
   offers Ladakh.
3. **Openings input (doors/windows/ventilation).** Deck lists this as a shelter-design input. UI has
   no control for it — ventilation is a fixed hardcoded ACH constant.
4. **Optimization / comparison engine.** Deck's whole "Optimize" step (vary geometry, orientation,
   material layers; score each; recommend best) does not exist as code. No sweep, no batch run, no
   comparison UI.
5. **Real "best design recommendation."** Currently a hardcoded string (`"PCM + Multi-material"`),
   not computed from any comparison.
6. **Database / persistence.** No DB anywhere. All "data" is static repo files.

## Partially built (to complete)

7. **ANSYS *transient* thermal simulation.** Engine only runs steady-state; the 24h curve shown to
   users is a synthetic sine wave layered on one steady-state solve, not a real transient time-integration.
   (Blocked without a licensed local ANSYS MAPDL install — see note below.)
8. **3D heatmap driven by real spatial field.** Currently colors by a single scalar average temperature.
   `spatial_3d`/VTK output exists in the Python schema but is switched off (`generate_vtk=False`) and
   never forwarded to the frontend.

## Out of scope for this pass

- True ANSYS transient FEA requires a licensed local ANSYS install; this machine's availability was
  checked before starting (see below). If unavailable, the synthetic-sinusoid approach is kept for the
  demo path, and this is called out explicitly rather than faked further.

## What was implemented this session

1. **Real weather data + regions.** `server/services/weatherService.js` pulls live hourly climate
   (temperature, solar radiation, wind, cloud cover) from Open-Meteo's free, key-less archive API,
   with a static/elevation-derived fallback if offline. `server/mockData/regions.json` adds Siachen,
   Spiti and Kaza (real coordinates) alongside Ladakh; `GET /api/regions` and the Location Data panel
   now use them, including corrected latitude/longitude/elevation display (previously hardcoded and
   wrong). See `server/schema.md` for the updated `/api/climate` and `/api/regions` contracts.
2. **Openings input.** `ShelterDesignSection.jsx` adds door/window count steppers and a ventilation
   level select (Low/Medium/High ACH), wired through `SimulationContext` → API →
   `simulationService.js`'s `computeOpeningsLossFactor`, which scales the openings share of heat loss
   and the efficiency score.
3. **Optimization/comparison engine.** `server/services/optimizationService.js` sweeps 3 shapes × 4
   orientations × 7 material combos (84 configurations) for the current site/openings context, scores
   each with the same rule-based model used for single results, and returns a ranked list + a genuine
   best pick — exposed as `GET /api/compare` and rendered in the new "Optimization & Comparison" panel
   (`ComparisonCard.jsx`). `mostEfficientCombo` in every simulation result is now this computed answer,
   not the previous hardcoded `"PCM + Multi-material"` string.
4. **Persistence.** `server/services/historyService.js` uses Node's built-in `node:sqlite` (no external
   DB server) to persist every `POST /api/run-simulation` call to `server/data/history.db`, exposed via
   `GET /api/history` and shown in the new `RunHistoryCard.jsx`.
5. **Python FastAPI side.** `Ansys simulation/api/service.py` / `ansysClient.js` were updated for
   consistency: openings now map to `air_changes_per_hour`, and the four regions get the same
   elevation-lapse-rate climate approximation as the Node fallback. Not independently testable here —
   no licensed ANSYS MAPDL install exists on this machine (checked at session start), so this path
   still falls back to the mock generator in practice.

## Follow-up: VTK/spatial-field heatmap wiring (completed)

Wired the existing spatial-field pathway through to the frontend, as a **real per-height vertical
temperature profile** rather than raw per-node XYZ coordinates — because the FEA engine only ever
meshes a rectangular box (`ShelterGeometry`), while the frontend's 3D view is a stylized shape the
user picks (dome/rectangular/custom) that has no geometric correspondence to that box. A height-
normalized profile (floor=0, roof=1) is the piece of the real field that transfers meaningfully onto
any shelter shape.

- `Ansys simulation/engine/result_extractor.py::_compute_vertical_profile` bins real ANSYS nodal
  temperatures into 10 height bands from the actual FEA solve (`SpatialField3D.vertical_profile`,
  always populated on a successful solve — no flag changes needed).
- `Ansys simulation/api/service.py` / `schemas.py` expose it as `verticalProfile` on the public
  response; `server/services/resultAdapter.js` passes it through.
- `server/services/simulationService.js`'s mock generator synthesizes a physics-informed equivalent
  (stratification spread scales inversely with the insulation/PCM score) so the feature is fully
  exercised without ANSYS.
- `client/src/components/output/heatmapShader.js` + `ShelterViewport.jsx`: the fragment shader
  blends between the old height-based visual gradient and this real per-height profile
  (`uUseProfile`), so the 3D heatmap now reflects genuine floor-to-roof stratification instead of one
  scalar average. Tested against the mock path (no ANSYS needed) — profile data confirmed correct via
  `GET /api/simulation-result`, shader compiles with no console errors, visual gradient responds to
  material/insulation choice.

## True ANSYS transient FEA — still deferred, needs your action

No licensed ANSYS MAPDL install exists on this machine (checked via `find_ansys_executable`'s probed
paths and a filesystem search at session start). This is commercial engineering software — even the
free "Student" tier requires an Ansys account, EULA acceptance, and a large (~25-35GB) interactive
installer — so it can't be silently installed by an agent. Once installed (Ansys Student, node-locked,
no license server needed), the Node/Python plumbing here needs no changes to pick it up automatically:
`server/services/ansysClient.js` already probes `GET /health` and falls back to mock transparently, and
the vertical-profile heatmap wiring above will start receiving genuinely real per-height data the
moment a live ANSYS solve succeeds. The remaining gap even then: `map_request_to_physics_input` in
`api/service.py` still hardcodes `SimulationMode.STEADY_STATE`; switching it to `TRANSIENT_24H` and
driving the 24h curve from a real time-integrated solve (instead of the synthetic sine wave layered on
one steady-state result) is the next step once a licensed install is available to test against.
