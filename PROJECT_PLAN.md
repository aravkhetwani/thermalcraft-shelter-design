# High Altitude Shelter Model — Project Plan & Roadmap

Reference document for PPT building, team alignment, and remaining
development work. Pairs with [PROJECT_BRIEF.md](PROJECT_BRIEF.md) (tech
stack + repo details) and [README.md](README.md) (run instructions).

---

## 1. Problem Statement (as given)

High-altitude cold regions like Ladakh face a specific thermal-comfort
problem:

- Ladakh gets very high solar irradiance (1900–2100 kWh/m²/year), ~7.9
  average sunshine hours/day, and 300+ cloud-free days/year.
- Shelters trap enough solar heat to stay comfortable **during the day**,
  even in winter — but lose that heat fast after sunset through the
  envelope material and openings, and fall close to ambient temperature
  overnight.
- Existing shelters aren't designed region-specifically, so they aren't
  energy-efficient and need external heating (often fossil-fuel based) to
  stay comfortable.

**Core idea**: a passive, area-specific shelter design — right shape, size,
orientation, and wall material(s) — can trap and retain enough solar energy
on its own, cutting or removing the need for external heating.

**Goal of this project**: build a software model that takes user-defined
inputs (real-time/regional climate data, material properties, geometry) and
predicts:
1. Shelter inside temperature over time
2. Thermal energy generated from solar radiation
3. Heat flow through the envelope (ambient vs. inside temperature
   difference), for a defined time period

...and lets the user compare material/shape/size combinations to find the
most thermally efficient design — minimizing energy use for heating and,
in turn, fossil fuel dependence.

---

## 2. Solution Overview — how our system answers the PS

Two components, developed in parallel:

| Component | Role | Status |
|---|---|---|
| **ANSYS Transient Thermal model** | The real physics engine — actually simulates heat transfer through the shelter envelope for a given geometry, material stack, and climate input | In progress (separate track) |
| **Dashboard / Frontend (this repo)** | User-facing app: takes inputs (region, climate, geometry, materials), shows predicted results as charts + 3D visualization, lets user compare combinations | Built — UI complete, running on mock data with a frozen API contract ready to receive real ANSYS/DB output |

This split means the UI/UX and the simulation science can be validated
independently, then connected at the end through one well-defined interface
(see §5).

---

## 3. Feature List

### 3.1 Must-have (from the PS, already built in the dashboard)

- **Region + climate input**: pick region/season/date range; pulls ambient
  temperature and solar flux profiles (24h) plus avg temp, solar
  irradiance, wind speed, cloud cover.
- **Shelter geometry input**: shape (rectangular / dome / custom), fixed
  size presets (small / medium / large — deliberately not free sliders,
  since real cases will map to precomputed/simulated configurations),
  orientation (N/S/E/W or degree presets).
- **Material input, including composite walls**: a material property
  library (thickness, density, thermal conductivity, heat capacity) and the
  ability to stack multiple materials into one wall (e.g. rammed earth +
  PCM) to model thermal-mass + insulation combinations.
- **Prediction 1 — Inside temperature over time**: 24h inside-vs-outside
  temperature chart.
- **Prediction 2 — Solar thermal energy generated**: 24h solar energy bar
  chart + total kWh figure.
- **Prediction 3 — Heat flow through the envelope**: breakdown by roof /
  wall / openings, driven by the ambient-vs-inside temperature difference.
- **Comparative analysis**: switching material combo / shape / size /
  orientation and re-running instantly shows which combination is most
  efficient — surfaced directly as an efficiency score, "most efficient
  combo" label, and % energy saved.
- **3D visualization**: an interactive, orbit-able shelter model with a
  heatmap-style overlay so the temperature outcome is visually obvious, not
  just numeric.

### 3.2 Good-to-have (not required by PS, strengthens the project / demo)

- **Live/real climate data ingestion** — pull real historical or live
  weather-station / satellite data for Ladakh (and other regions) instead
  of a static mock profile, so predictions reflect actual conditions.
- **More regions out of the box** — extend beyond Ladakh to other
  high-altitude/cold regions (Siachen, Spiti, Kaza, Himalayan border
  outposts) to show the model generalizes, matching the PS's note that this
  should be usable "for studying design requirements of other climatic
  region shelters as well."
  - Note: `server/mockData/climateData.json` currently only has a Ladakh
    entry — adding a region is just adding another key to that file.
- **A "source" badge on results** (`mock` / `database` / `ansys-live` /
  `interpolated`) — already in the frozen schema; surface it in the UI so
  reviewers can see at a glance whether they're looking at demo data or a
  real ANSYS run.
- **Report/export**: generate a PDF or shareable summary of a chosen
  design's predicted performance (useful for army/govt stakeholders
  evaluating a real build).
- **Cost/logistics overlay**: pair each material with an approximate cost
  or transport-feasibility note for remote high-altitude sites — turns a
  thermal-only recommendation into a buildable one.
- **Multi-day / seasonal simulation** — not just one representative day,
  but a full week or season, to show degradation/variation over time
  (e.g. cloudy-day resilience).
- **Sensitivity analysis view** — show which single variable (material
  thickness, orientation, opening size) moves the efficiency score the
  most, to guide design decisions.
- **User accounts / saved designs** — let a user save and revisit specific
  design configurations (explicitly out of scope for the current UI phase,
  but a natural next step).
- **Mobile-friendly / field-use mode** — a stripped-down view usable on a
  tablet at a construction site.

---

## 4. Workflow — how the system works end to end

```
 1. User selects region + season + date range
          │
          ▼
 2. System loads ambient climate profile
    (ambient temperature curve, solar flux curve,
     avg temp, solar irradiance, wind speed, cloud cover)
          │
          ▼
 3. User defines shelter design
    → shape (rectangular / dome / custom)
    → size preset (small / medium / large)
    → orientation (N/S/E/W)
          │
          ▼
 4. User builds the wall material stack
    → pick from material library (thickness, density,
      thermal conductivity, heat capacity)
    → stack multiple layers for composite walls
    → "Apply Material" recalculates the result
      for this combo only
          │
          ▼
 5. User clicks "Run Simulation"
    → all inputs (climate + geometry + material combo)
      are sent to the simulation engine
          │
          ▼
 6. Simulation engine computes/returns:
    → inside temperature over 24h
    → solar thermal energy generated (24h + total kWh)
    → heat flow through roof / wall / openings
    → efficiency score, most efficient combo, % energy saved
          │
          ▼
 7. Dashboard renders results
    → 3D model recolors as a temperature heatmap
    → charts update (inside vs outside temp,
      solar energy, heat flow breakdown)
    → efficiency summary updates
          │
          ▼
 8. User iterates
    → changes material / shape / size / orientation
    → re-runs and compares efficiency scores
    → converges on the most thermally efficient,
      region-specific passive shelter design
```

**Where ANSYS plugs in**: step 6 ("simulation engine computes/returns") is
currently answered by mock data + a formulaic stand-in behind one function
(`getResult` in `server/services/simulationService.js`). The plan is for
that same function to eventually call into ANSYS (directly, via a
precomputed case database, or via an interpolation layer) — the input it
receives (climate + geometry + material combo) and the output shape it must
return are already fixed, so this swap doesn't require changing steps 1–5
or 7–8 at all.

---

## 5. Integration Contract (dashboard ↔ ANSYS)

This is the handshake the ANSYS team and the dashboard team both build
against, so the two tracks can merge without rework.

**Inputs the dashboard sends** (per simulation request):
- Region + season → ambient temperature profile (24h), solar flux profile
  (24h), avg temp, solar irradiance, wind speed, cloud cover
- Shape (rectangular / dome / custom)
- Size preset (small / medium / large → fixed dimensions)
- Orientation (N/S/E/W or degrees)
- Material combo: ordered list of layers, each with thickness, density,
  thermal conductivity, heat capacity

**Output the dashboard expects back** (see `server/schema.md` for the exact
JSON shape):
- `insideTemp`: 24 hourly values
- `ambientTemp`: 24 hourly values (echoed back for the comparison chart)
- `solarEnergy`: 24 hourly kWh values + `totalSolarKwh`
- `heatFlow`: watts through roof / wall / openings
- `efficiencyScore`, `mostEfficientCombo`, `energySavedPercent`
- `source`: tag saying whether this came from mock data, a database, or a
  live ANSYS run

Whoever wires up the real engine only needs to make sure a real ANSYS run
(or a precomputed case lookup) can be mapped into this exact shape — no
frontend changes required.

---

## 6. Roadmap

### Phase 1 — Dashboard UI (done)
- Input controls for location, climate, shelter design, materials
- 3D shelter viewer with temperature heatmap
- Output charts for all 3 required predictions + efficiency comparison
- Mock API with a frozen, documented contract

### Phase 2 — ANSYS model development (in progress, parallel track)
- Build the parametric ANSYS Transient Thermal model for the shelter
  (shape, size, orientation, material stack as parameters)
- Validate against known heat-loss behavior for at least one real material
  (e.g. rammed earth) before generalizing
- Produce a batch of precomputed cases across the input space (region ×
  season × shape × size × orientation × material combo) to seed the result
  database

### Phase 3 — Integration
- Replace the mock `getResult` function with either:
  (a) a lookup against the precomputed ANSYS case database, or
  (b) a live-triggered ANSYS run per request, or
  (c) an interpolation model trained on the precomputed cases (fastest for
      interactive use)
- Add the `source` badge to the UI so real vs. mock results are visually
  distinguishable during testing
- Validate that dashboard predictions match ANSYS output within an
  acceptable tolerance for a handful of spot-check cases

### Phase 4 — Real climate data
- Swap the static mock climate profile for a real data source (historical
  weather station data for Ladakh, or a live weather API) so predictions
  reflect actual conditions rather than a representative sample week

### Phase 5 — Generalization + polish
- Extend beyond Ladakh to at least one more high-altitude cold region, to
  demonstrate the model isn't hardcoded to a single location
- Add good-to-have features as time allows: report export, cost/logistics
  overlay, multi-day/seasonal runs, sensitivity analysis view

### Phase 6 — Presentation
- Finalize demo script: pick 2–3 material/shape combinations that tell a
  clear "before vs. after efficiency" story
- Build PPT around: Problem → Why passive design → How the model works
  (workflow diagram in §4) → Live demo → Roadmap / future scope
