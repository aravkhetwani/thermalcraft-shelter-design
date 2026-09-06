# Project Brief — High Altitude Shelter Model (SIH 2026)

Copy everything below this line and paste it into your own Claude session
(or any teammate's) to get full context for making PPT slides, docs, demo
scripts, or continuing development.

---

## Problem Statement

Develop a software-based model to predict suitable passive shelter design
(materials, size, shape, orientation) for thermal comfort in high-altitude
cold regions like Ladakh, India. The model must be user-friendly, take
user-defined inputs (real-time climate data, material properties, geometry),
and predict:
1. Shelter inside temperature over time
2. Thermal energy generated from solar radiation
3. Heat flow through the shelter envelope based on ambient vs. inside
   temperature difference

The tool should allow comparison of different material/geometry combinations
to identify the most thermally efficient design.

## Our approach (two-part system)

1. **Simulation engine** (separate, in progress): ANSYS Transient Thermal —
   this is where the real physics/heat-transfer computation will happen.
2. **Dashboard / frontend** (this repo, built so far): a user-facing web app
   where a user picks a region, climate conditions, shelter geometry, and
   wall materials, and sees predicted results as interactive charts + a 3D
   model. Currently wired to realistic **mock data**, structured so the mock
   layer can be swapped for real ANSYS output (or a database/interpolation
   layer) later without changing any frontend code.

This split lets the dashboard/UI work proceed in parallel with the ANSYS
simulation work.

## Tech stack

- **Frontend**: React (functional components, hooks), Vite, Tailwind CSS
- **3D visualization**: Three.js via `@react-three/fiber` + `@react-three/drei`
  (OrbitControls, Html overlays, ContactShadows), a custom GLSL shader for a
  height + temperature-based "thermal heatmap" coloring on the shelter mesh
- **Charts**: Recharts (line charts for temperature, bar charts for solar
  energy and heat flow)
- **Animation**: Framer Motion (material wall-layer add/remove transitions)
- **Backend**: Node.js + Express — currently serves mock JSON data via REST
  endpoints, standing in for the eventual real data source
- **HTTP client**: axios

## Repo layout

```
SIH_2026/
├── server/                        # Express mock API (port 4000)
│   ├── mockData/
│   │   ├── materials.json         # material property library
│   │   ├── climateData.json       # ambient temp / solar irradiance per region+season
│   │   └── simulationResults.json # precomputed result objects per combo
│   ├── services/simulationService.js  # the ONE function to swap for real data later
│   ├── routes/api.js
│   ├── schema.md                  # frozen API contract, fully documented
│   └── index.js
├── client/                        # React dashboard (port 5173)
│   └── src/
│       ├── api/client.js          # only place that talks HTTP — no inline mock data
│       ├── api/schema.js          # JSDoc typedefs mirroring the frozen API schema
│       ├── context/SimulationContext.jsx  # all app state (inputs, results, loading)
│       └── components/
│           ├── TopBar.jsx
│           ├── input/    # LocationSection, AmbientConditions, ShelterDesignSection,
│           │             # MaterialSystem, InputPanel
│           └── output/   # ShelterViewport (3D), InsideTempCard, SolarEnergyCard,
│                         # HeatFlowCard, EfficiencyCard, OutputDashboard
├── README.md                      # setup/run instructions
└── PROJECT_BRIEF.md               # this file
```

## API contract (frozen — see server/schema.md for full detail)

- `GET /api/materials` → material property library (id, name, thickness,
  density, thermal conductivity, heat capacity, color)
- `GET /api/climate?region=&season=` → ambient temp + solar flux profile
  (24-hour arrays) plus avg temp, solar irradiance, wind speed, cloud cover
- `GET /api/simulation-result?materialCombo=&orientation=&size=&shape=` →
  one result object
- `POST /api/run-simulation` → same params in body, same result shape, with
  a simulated 1–2s delay (stand-in for real compute time)

Result object shape (this is what every output chart renders from):
```json
{
  "id": "pcm+rammed-earth_south_medium_dome",
  "source": "mock",
  "insideTemp": { "hours": [0,1,"...",23], "values": [10.8, 10.1, "..."] },
  "ambientTemp": { "hours": [0,1,"...",23], "values": [-20.5, -21.2, "..."] },
  "solarEnergy": { "hours": [0,1,"...",23], "valuesKwh": [0, 0, "..."] },
  "totalSolarKwh": 46.8,
  "heatFlow": { "roofW": 12, "wallW": 18, "openingsW": 8 },
  "efficiencyScore": 88,
  "mostEfficientCombo": "PCM + Multi-material",
  "energySavedPercent": 74
}
```

`source` will later read `"database"` | `"ansys-live"` | `"interpolated"`
instead of `"mock"` — that's the only visible signal of the swap.

## What's built and working right now

- **Input Control Panel** (left): region/season/date-range selectors, live
  ambient-conditions readout with mini forecast charts, shape toggle
  (Rectangular / Dome / Custom — each renders a different 3D geometry),
  fixed size presets (Small/Medium/Large), orientation dropdown.
- **Material System**: a library of 4 materials (Rammed Earth, PU Foam, PCM,
  Insulated Composite) shown as cards with real property values; click
  "+ Add Layer" to build a composite wall (multiple layers), animated
  add/remove via Framer Motion; "Apply Material" pushes the new combo to the
  output dashboard and 3D model.
- **3D shelter viewport**: orbit/zoom-able model whose color is a
  height + avg-inside-temp-based heatmap (blue → teal → green → yellow →
  orange → red), plus a base-ring accent tinted by the primary wall material.
- **Output Dashboard** (right): Inside Temperature (inside vs outside,
  24h line chart), Solar Thermal Energy (24h bar chart + total kWh),
  Heat Flow Analysis (roof/wall/openings bar chart), Design Efficiency
  Summary (score ring, most efficient combo, % energy saved).
- **Run Simulation** button: shows a top-bar progress bar and a ~1-2s
  simulated loading state before refreshing all results — feels like a real
  computation is happening even though it's mock data today.
- Dark theme, blues/oranges/teal accents, engineering-software aesthetic,
  closely following the team's reference mockup.

## What's explicitly NOT built yet (by design, for this phase)

- No real thermal physics / RC-network calculations / ANSYS integration
- No user accounts or persistence beyond the mock JSON files
- No real climate API integration (climate data is a small hardcoded mock
  dataset per region/season)
- Mobile responsiveness not a priority (desktop/demo-screen dashboard)

## How to run it locally

```bash
# Terminal 1 — mock API server (localhost:4000)
cd server
npm install
npm run dev

# Terminal 2 — React dashboard (localhost:5173)
cd client
npm install
npm run dev
```

## Suggested use of this brief

If you're picking this up to build slides: the "Problem Statement" and
"Our approach" sections above are your problem/solution slides; the "Tech
stack" and "What's built and working" sections are your architecture/demo
slides. If you're picking this up to keep coding: read `server/schema.md`
first — it's the one contract every future change (real ANSYS integration,
a database layer, more materials/regions) must keep matching.
