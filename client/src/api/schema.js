/**
 * Frozen response shape for GET /api/simulation-result and POST /api/run-simulation.
 * Mirrors server/schema.md exactly. Components should only ever read data that
 * matches this shape — never import mock JSON directly.
 *
 * @typedef {Object} HourlySeries
 * @property {number[]} hours
 * @property {number[]} values
 *
 * @typedef {Object} SolarSeries
 * @property {number[]} hours
 * @property {number[]} valuesKwh
 *
 * @typedef {Object} HeatFlow
 * @property {number} roofW
 * @property {number} wallW
 * @property {number} openingsW
 *
 * @typedef {Object} VerticalProfilePoint
 * @property {number} heightFrac - Normalized shelter height, 0 (floor) to 1 (roof).
 * @property {number} tempC
 *
 * @typedef {Object} SimulationResult
 * @property {string} id
 * @property {'mock'|'database'|'ansys-live'|'interpolated'} source
 * @property {HourlySeries} insideTemp
 * @property {HourlySeries} ambientTemp
 * @property {SolarSeries} solarEnergy
 * @property {number} totalSolarKwh
 * @property {HeatFlow} heatFlow
 * @property {number} efficiencyScore
 * @property {string} mostEfficientCombo
 * @property {number} energySavedPercent
 * @property {VerticalProfilePoint[]} [verticalProfile] - Real (ANSYS) or synthetic-fallback
 *   floor-to-roof temperature stratification, driving the 3D heatmap gradient.
 *
 * @typedef {Object} Material
 * @property {string} id
 * @property {string} name
 * @property {number} thicknessCm
 * @property {number} density
 * @property {number} thermalConductivity
 * @property {number} heatCapacity
 * @property {string} color
 * @property {string} description
 *
 * @typedef {Object} ClimateProfile
 * @property {string} label
 * @property {number} avgTemp
 * @property {number} solarIrradiance
 * @property {number} windSpeed
 * @property {number} cloudCover
 * @property {string} dateRangeDefault
 * @property {HourlySeries} ambientTemp
 * @property {HourlySeries} solarFlux
 */

export {};
