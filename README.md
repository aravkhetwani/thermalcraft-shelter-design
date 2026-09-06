# High Altitude Shelter Model — Dashboard (UI Phase)

A dark-themed, engineering-software-style dashboard for exploring passive
shelter designs (material, size, shape, orientation) for thermal comfort in
high-altitude cold regions like Ladakh.

**This phase is UI only.** Every number on screen — temperatures, solar
energy, heat flow, efficiency scores — is mock data served by a small Express
API. No real thermal physics is computed here; the real engine (ANSYS
Transient Thermal, a precomputed database, or an interpolation model) plugs
in later behind the same API contract without touching the React code.

## Project structure

```
SIH_2026/
├── server/                  # Express mock API
│   ├── mockData/            # materials.json, climateData.json, simulationResults.json
│   ├── services/
│   │   └── simulationService.js   # the ONE swappable module (mock now, real engine later)
│   ├── routes/api.js
│   ├── schema.md            # frozen API contract, documented in full
│   └── index.js
└── client/                  # React + Vite dashboard
    └── src/
        ├── api/client.js     # the ONLY place the UI talks to HTTP — no inline mock data
        ├── context/SimulationContext.jsx  # all app state (inputs, results, loading)
        └── components/
            ├── input/        # Location, Ambient Conditions, Shelter Design, Material System
            └── output/       # 3D viewport + Inside Temp / Solar Energy / Heat Flow / Efficiency cards
```

## Layout decision

The reference image's single-page, three-zone layout (input panel left,
3D view + output cards right) worked well as-is, so this build kept it as one
page rather than splitting into routes — there wasn't enough distinct
functionality (e.g. a standalone material-library admin screen) to justify
extra navigation for a hackathon demo. React Router was left out for the same
reason; it can be added later if the app grows more screens.

## Running it

Two servers, run in separate terminals.

**1. Mock API server** (http://localhost:4000)

```bash
cd server
npm install
npm run dev
```

**2. React dashboard** (http://localhost:5173)

```bash
cd client
npm install
npm run dev
```

Open http://localhost:5173. The client reads `VITE_API_BASE_URL` (defaults to
`http://localhost:4000/api`) if you need to point it elsewhere — set it in a
`client/.env` file.

## How the data layer works (read this before wiring in real data)

- The frontend **only** calls four REST endpoints — `GET /api/materials`,
  `GET /api/climate`, `GET /api/simulation-result`, `POST /api/run-simulation`
  — documented exactly in [server/schema.md](server/schema.md). No component
  ever imports a JSON file directly.
- Every one of those endpoints returns data shaped by the frozen
  `SimulationResult` / `Material` / `ClimateProfile` schemas (also mirrored as
  JSDoc typedefs in `client/src/api/schema.js`).
- All the actual mock logic lives behind one function:
  `server/services/simulationService.js#getResult`. It currently does a
  dataset lookup (`mockData/simulationResults.json`) with a seeded formulaic
  fallback for any material/orientation/size/shape combo that isn't
  precomputed. Swapping in a database query or a live ANSYS trigger later
  means changing only the body of `getResult` — same input, same output
  shape, zero UI changes.

## Interacting with the demo

- **Material System** (left panel, "Material Properties"): click **+ Add
  Layer** on any material card to add it to the wall's layer stack — this
  supports composite walls (e.g. Rammed Earth + PCM). Remove a layer with the
  ✕. Click **Apply Material** to push the new combo into the output charts
  and 3D model.
- **Run Simulation** (bottom of the left panel): re-fetches a result for the
  current inputs via `POST /api/run-simulation`, which has a simulated 1–2s
  delay — this is where a real engine's compute time would show up later.
- **3D View**: orbit/zoom the shelter model. Its color is a height-based
  "thermal heatmap" shifted by the current average inside temperature, plus a
  base ring accent tinted by the primary wall material.
