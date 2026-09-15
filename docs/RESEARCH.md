# ThermalCraft Research Extension: A Physics-Grounded ML Surrogate for Passive Shelter Design

This document describes a research extension added to ThermalCraft/ChaiLogic 2.0: a
reproducible pipeline that (1) assembles the project's existing, already-verified
building-physics equations into a complete callable steady-state thermal simulator,
(2) generates a large synthetic dataset by sampling the shelter design space, (3) trains
and rigorously evaluates ML surrogate models against that simulator, (4) uses the
surrogate for large-scale design-space optimization, and (5) validates the optimizer's
picks against the real simulator. Everything here is reproducible from one command and
every number in this document was produced by that command — nothing is hand-typed or
assumed.

All code lives under `Ansys simulation/research/`.

## 1. What ThermalCraft does

ThermalCraft (product name ChaiLogic 2.0) is a simulation-driven design tool for
passive-solar shelters in high-altitude regions (Ladakh, Siachen, Spiti, Kaza). A user
picks a region/season, a shelter geometry (dome/rectangular/custom, size, orientation),
and a wall material combination (rammed earth, PU foam insulation, PCM, insulated
composite — single or layered), and the app reports predicted indoor temperature, solar
energy capture, heat-loss breakdown, and an efficiency score, plus (as of this session's
earlier work) a real optimization/comparison sweep across configurations and live weather
data. See the root `README.md` and `docs/PITCH_DECK_GAP_ANALYSIS.md` for the full
product picture.

## 2. The underlying thermal/scientific problem

A shelter's steady-state indoor temperature is governed by an energy balance: solar and
conductive heat gains through the roof/walls/ground, internal gains from occupants and
equipment, minus conductive losses back out through the envelope and ventilation air
exchange. The project's FEA path (`Ansys simulation/engine/`) solves this with a full
3D finite-element mesh in ANSYS MAPDL — the most physically complete approach, but it
requires a licensed local ANSYS install (unavailable on the machine this was built on;
see §8) and is far too slow (seconds to minutes per run) for generating a
several-thousand-sample ML training set.

## 3. Why ML is useful here

Design-space exploration — "which combination of geometry, material, and ventilation
gives the warmest shelter for the least material cost" — requires evaluating many
candidate designs. A trained ML surrogate can screen hundreds of thousands of candidates
in well under a second (§7), then hand a short list back to the real simulator for
validation. This is standard surrogate-modeling practice in engineering design
(replace an expensive/slow evaluator with a fast approximation for screening, always
re-validating the final picks against the ground truth), applied here to a genuinely
physics-grounded reference model rather than a toy example.

## 4. The simulator: what's reused, what's new, and an honest limitation it exposed

**Reused verbatim** from `Ansys simulation/engine/physics_preprocessor.py`
(`PhysicsPreprocessor.process`), unmodified:
- McAdams external convection correlation: `h_out = max(10, 5.7 + 3.8*v_wind)`
- Sol-Air temperature equation: `T_sol-air = T_amb + alpha*I/h_out`
- Room air volume, internal volumetric heat generation, ventilation heat-removal
  capacity (`C_vent = rho * V_dot * Cp`)

**New** (`Ansys simulation/research/simulator.py`): a complete closed-form steady-state
energy balance assembled from those ingredients — roof + four walls + ground + ventilation
+ internal gains, solved for one indoor air temperature. The codebase computed all these
physical quantities before, but always handed the actual system solve off to the ANSYS
FEA mesh; this module is the piece that was missing to make it a fast, callable, complete
simulator in its own right.

**A genuine finding, not a bug**: while building this, orientation (`south`/`north`/
`east`/`west`) turned out to have **zero effect** on the whole-building steady-state energy
balance, for *any* aspect ratio — the four Sol-Air gain fractions taken from
`physics_preprocessor.py` (0.50 south / 0.40 west / 0.25 east / 0.15 north) satisfy
`0.50+0.15 == 0.40+0.25 == 0.65` exactly, which mathematically forces any pairing of these
fractions onto the building's two face-pairs to sum identically. This is proven directly
(`research/tests/test_simulator.py::test_orientation_invariant_even_with_solar`, sweeping
all 4×4 orientation pairs) and independently confirmed empirically by the trained model's
permutation feature importance (§6: every `orientation_*` dummy has importance ≈0). This
also surfaces a related, separate gap in the *reference FEA path*
(`engine/boundary_conditions.py`): it computes `orientation_azimuth_deg` but never uses it
at all — every FEA run applies the same fixed compass-labeled Sol-Air values to the same
fixed geometric faces regardless of the user's chosen orientation. **We did not "fix" this
by inventing new physics** — we verified, with the existing constants, that no lumped
whole-building fix is possible; capturing real orientation sensitivity would require a
spatially-resolved (multi-node or FEA) model, which is exactly what the ANSYS path is for.

**Documented limitations**:
- Steady-state only — no thermal mass, no time lag, no true 24h transient response. PCM's
  real benefit (latent-heat buffering of peak swings) is NOT captured; only its steady-state
  conductive resistance contributes here. `wall_thermal_mass_proxy` is deliberately included
  as a feature specifically so the feature-importance analysis could confirm this empirically
  (§6) rather than merely asserting it.
- Roof and floor use fixed reference constructions (RCC roof, concrete floor slab); only
  wall/insulation/PCM composition and thickness are treated as design variables, matching
  what the app's UI actually exposes.
- No night-sky longwave radiative loss term (a real effect at high altitude, clear-sky
  nights) — only convective Sol-Air boundary conditions, exactly as in the reference FEA path.

## 5. Dataset generation

`research/dataset.py` samples the shelter design space (geometry, orientation, wall
material, insulation/PCM thickness, occupancy, ventilation) and crosses it with **real**
(region, season, hour-of-day) climate instants drawn from `research/climate_data.py` —
itself the exact Ladakh winter/summer hourly arrays already used by the Node backend
(`server/mockData/climateData.json`), extended to Siachen/Spiti/Kaza via the same
elevation-lapse-rate approximation already used by `weatherService.js`.

**Why real hourly climate instants instead of independently sampling ambient temperature
and solar irradiance**: independent sampling could generate physically impossible
combinations (e.g. the coldest night-time temperature paired with peak midday solar).
Drawing from real recorded hours guarantees every (ambient, solar) pair is one that
actually occurs. This is verified directly by
`research/tests/test_dataset.py::test_climate_values_are_physically_consistent_pairs`.

Every draw uses a single seeded `numpy.random.default_rng(seed)` (default seed `42`), in a
fixed, documented order — reproducibility is verified by
`research/tests/test_dataset.py::test_reproducibility_same_seed_identical_output` and an
end-to-end version in `test_reproducibility.py`.

**Dataset produced**: 6,000 rows × 28 columns, written to
`Ansys simulation/research/data/thermal_dataset.csv` (committed to the repo).

## 6. Feature engineering, targets, and leakage discipline

**Targets** (both scientifically meaningful, both trained on and reported):
- `indoor_temp_c` — steady-state indoor air temperature (primary; matches the app's core
  comfort output)
- `total_loss_w` — total envelope heat loss (secondary; matches the app's heat-flow output)

**Leakage discipline**: `simulator.simulate()` computes envelope resistances, areas, and
room volume from design inputs *before* solving for indoor temperature; every loss column
is derived *from* that solve. `research/features.py::get_feature_columns` therefore
excludes ALL target-side columns (`indoor_temp_c` and every loss column) from the feature
set for every target, including when one target is used to predict another — enforced by
`research/tests/test_features.py::test_no_target_leakage_for_any_target`. Pre-solve
derived quantities (`envelope_r_wall`, `envelope_r_roof`, `room_volume_m3`) ARE included as
features for any target — they depend only on inputs, never on the solved temperature.

**Engineered features**: envelope surface areas, surface-area-to-volume ratio (a standard
building-compactness metric), UA-values (`area / R`) per surface, insulation/PCM presence
flags, a static thermal-mass proxy (density × specific heat × wall volume — deliberately
included to test whether it matters, see §4), a heating-degree proxy, and total internal
heat gain.

## 7. Validation methodology

Every dataset row is an i.i.d. draw from the design/climate parameter space — there is no
time series, no grouping by a shared entity, and no near-duplicate structure by
construction. **A random train/validation/test split is therefore scientifically
appropriate** (unlike temporal or spatially-correlated data, where random splitting would
leak information across the boundary). We use a 70/15/15 split with a fixed seed
(`research/train.py::split_indices`), fit exclusively on the 70% training partition, and
report final numbers only on the untouched 15% test partition. Split integrity (disjoint
partitions, correct proportions, reproducibility) is directly tested in
`research/tests/test_split.py`.

## 8. Models compared and real results

Five models were trained per target: a mean-value dummy baseline, Linear Regression,
Random Forest, Gradient Boosting, and XGBoost. Reproduce with:

```bash
cd "Ansys simulation"
pip install -r research/requirements.txt
python -m research.run_all
```

**Test-set results** (from `research/results/training_metrics.json`, this exact run):

| Model | Indoor Temp MAE (°C) | Indoor Temp R² | Heat Loss MAE (W) | Heat Loss R² |
|---|---|---|---|---|
| Mean baseline | 14.872 | −0.002 | 212.091 | −0.002 |
| Linear Regression | 0.972 | 0.9942 | 74.496 | 0.8230 |
| Random Forest | 0.689 | 0.9971 | 22.025 | 0.9637 |
| Gradient Boosting | 0.550 | 0.9981 | 23.397 | 0.9753 |
| **XGBoost (best)** | **0.391** | **0.9990** | **14.883** | **0.9858** |

**Why Linear Regression already does extremely well for indoor temperature but
noticeably worse for heat loss**: the steady-state energy balance is a *weighted average*
of boundary temperatures (near-linear in most inputs), so a linear model captures most of
the variance in `indoor_temp_c` directly. The main nonlinearity is the `U = 1/R`
(resistance→conductance) relationship and the `max(0, ...)` clipping used to report only
losses (not gains) per surface — which barely affects the weighted-average target but
compounds significantly for the summed, clipped heat-loss target. This is a genuine,
explainable pattern, not a coincidence, and it justifies using tree ensembles even for
a "simple" physics problem.

**Feature importance** (permutation importance on the held-out test set,
`research/results/training_metrics.json`): `ambient_temp_c` overwhelmingly dominates
`indoor_temp_c` (importance 1.89, next-highest 0.013), as expected for a
weighted-average-like target. For `total_loss_w`, `internal_gain_w`,
`solar_irradiance_peak_w_m2`, and `ua_roof_w_k` dominate. In both cases, **every
`orientation_*` dummy and `wall_thermal_mass_proxy` have importance ≈0** — the empirical
confirmation of the physical findings in §4.

## 9. Downstream task: surrogate-driven design optimization

`research/optimize.py` screens 200,000 random candidate designs under a fixed, real
evaluation scenario — **24-hour-averaged Ladakh winter conditions** (mean of the actual
24-hour ambient/solar arrays in `climate_data.py`) — using the trained XGBoost surrogate's
vectorized batch prediction, takes the top 20 by predicted indoor temperature, and
**re-runs every one of those 20 through the real simulator** (never trusting the
surrogate's own number as ground truth — enforced by
`research/tests/test_optimization.py::test_validation_step_uses_real_simulator_not_surrogate_output`).

**Real result from this run** (`research/results/optimization_result.json`):
- Screened 200,000 candidates in 0.22 s.
- Top-20 mean |surrogate error| vs. the real simulator: **1.67 °C** — a meaningful, honest
  gap, not zero. The best candidates cluster near the edges of the sampled design bounds
  (small footprint, near-maximum insulation, near-minimum ventilation), where the
  surrogate has seen relatively fewer training examples — a textbook surrogate-modeling
  caveat, and exactly why the real-simulator validation step is not optional.
- Best validated design: west-facing (irrelevant per §4, included for completeness),
  insulated-composite wall, 0.35 m wall thickness, 0.13 m insulation, 0.017 m PCM, 8
  occupants, 0.56 ACH.
- Baseline (typical unoptimized design — medium rammed-earth, no insulation, 1.5 ACH,
  matching the app's own pre-existing UI defaults): **−12.80 °C** actual indoor temperature.
- Optimized design, validated by the **real simulator**: **+2.39 °C**.
- **Improvement: +15.19 °C**, a substantial, simulator-verified gain — not a surrogate
  artifact.

## 10. Surrogate vs. simulator speedup — measured, not assumed

`research/benchmark.py` times the real simulator run in a plain Python loop against the
trained surrogate's vectorized batch `.predict()`, at several batch sizes
(`research/results/speedup_benchmark.json`):

| Batch size | Simulator (s) | Surrogate (s) | Speedup |
|---|---|---|---|
| 100 | 0.0036 | 0.0053 | **0.68x (slower)** |
| 1,000 | 0.0301 | 0.0052 | 5.79x |
| 10,000 | 0.2408 | 0.0217 | 11.11x |
| 100,000 | 2.2206 | 0.1195 | 18.59x |

**Honest reading**: because the reference simulator is already a fast closed-form
calculation (not an expensive FEA solve), the surrogate does *not* help — is in fact
slightly slower — for small one-off evaluations, where fixed model-inference overhead
dominates. It becomes clearly worthwhile only at the scale a real design-space search
actually needs (tens of thousands to hundreds of thousands of candidates), where
vectorized batch inference amortizes that overhead. We report this instead of a single
inflated "Nx faster" headline number, because the true answer is scale-dependent.

## 11. Tests

28 tests across 7 files (`Ansys simulation/research/tests/`), covering: simulator physical
correctness (monotonicity, energy-balance closure, the orientation-invariance proof,
determinism), dataset reproducibility/schema/bounds/climate-consistency, feature-leakage
prevention, split integrity, training (beats baseline, models persist, predictions are
finite and physically plausible), optimization (candidate bounds, surrogate-vs-simulator
correlation, validation-uses-real-simulator), and full-pipeline reproducibility. All 28
pass (`python -m pytest research/tests -v`, run from `Ansys simulation/`).

## 12. Limitations (see also §4 and §10)

- The reference simulator is a steady-state lumped-parameter model, not a full transient
  FEA solve — it cannot capture thermal mass / time-lag effects (a real, honest gap
  relative to the ANSYS path, which itself is presently steady-state-only too — see
  `docs/PITCH_DECK_GAP_ANALYSIS.md`).
- Orientation, as modeled, has zero effect on this target — a genuine finding, not a
  missing feature (§4). A future spatially-resolved model (the FEA path, properly wired to
  use `orientation_azimuth_deg`) would be needed to capture real orientation sensitivity.
- The surrogate's top-optimization picks cluster near design-space boundaries, where
  surrogate error is largest (§9) — always re-validate against the real simulator before
  acting on a surrogate-suggested design; this pipeline does so by construction, but a
  future user of the surrogate alone should not skip that step.
- Dataset size (6,000 samples) and design-space bounds are documented, fixed choices
  (`research/simulator.py::DESIGN_BOUNDS`) — extending the bounds (e.g. wider wall
  thickness range) would require regenerating the dataset and retraining before trusting
  surrogate predictions outside the current range.

## 13. Possible future work

- Wire a true ANSYS transient (`TRANSIENT_24H`) solve once a licensed MAPDL install is
  available, and use it (rather than the steady-state analytic model) as the dataset
  generator — would let the surrogate also learn thermal-mass/PCM time-lag effects.
- Extend the design space to include free-form dimensions beyond the current bounds, and
  a genuinely spatially-resolved orientation effect via the FEA path.
- Active learning: use surrogate uncertainty (e.g. an ensemble's prediction spread) to
  choose which new designs to simulate next, rather than uniform random sampling.

## 14. Resume-ready summary

*Built an end-to-end ML surrogate-modeling pipeline for a physics-based passive-solar
shelter design tool: assembled the project's existing building-physics equations (McAdams
convection, Sol-Air temperature) into a complete closed-form thermal simulator, generated
a 6,000-sample synthetic dataset from real regional climate data, trained and rigorously
evaluated 4 regression models (Linear/RF/GBM/XGBoost, R² up to 0.999) with leakage-safe
feature engineering and a defensible i.i.d. train/val/test split, used the trained
surrogate to screen 200,000 candidate designs in 0.2 seconds and validated the top
candidates against the ground-truth simulator (+15.2°C improvement over baseline, 1.67°C
mean surrogate error), and measured — rather than assumed — surrogate speedup (0.7x–19x,
scale-dependent). Along the way, proved analytically and confirmed empirically via
permutation feature importance that a modeling assumption in the reference engine made
"orientation" mathematically unable to affect the whole-building energy balance — an
honest negative finding documented rather than hidden. 28 passing tests cover simulator
physics, dataset reproducibility, leakage prevention, and simulator-vs-surrogate
consistency.*
