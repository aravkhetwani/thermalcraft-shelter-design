/**
 * Run History / Persistence
 * ==========================
 * Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System
 *
 * Lightweight SQLite persistence (Node's built-in node:sqlite, no external
 * DB server required) so completed simulation runs survive server restarts
 * and can be listed back to the dashboard — the "Database" layer called out
 * in the architecture diagram, previously entirely absent.
 */
import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdirSync } from 'node:fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const dataDir = join(__dirname, '..', 'data');
mkdirSync(dataDir, { recursive: true });

const db = new DatabaseSync(join(dataDir, 'history.db'));

db.exec(`
  CREATE TABLE IF NOT EXISTS simulation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    region TEXT,
    season TEXT,
    shape TEXT,
    size TEXT,
    orientation TEXT,
    material_combo TEXT,
    openings_json TEXT,
    source TEXT,
    efficiency_score INTEGER,
    energy_saved_percent INTEGER,
    most_efficient_combo TEXT,
    result_json TEXT NOT NULL
  )
`);

const insertStmt = db.prepare(`
  INSERT INTO simulation_runs
    (created_at, region, season, shape, size, orientation, material_combo, openings_json, source, efficiency_score, energy_saved_percent, most_efficient_combo, result_json)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

const listStmt = db.prepare(`
  SELECT id, created_at, region, season, shape, size, orientation, material_combo, openings_json, source, efficiency_score, energy_saved_percent, most_efficient_combo
  FROM simulation_runs
  ORDER BY id DESC
  LIMIT ?
`);

export function recordRun(params, result) {
  try {
    insertStmt.run(
      new Date().toISOString(),
      params.region || 'ladakh',
      params.season || 'winter',
      params.shape || 'dome',
      params.size || 'medium',
      params.orientation || 'south',
      params.materialCombo || 'rammed-earth',
      JSON.stringify(params.openings || {}),
      result.source || 'mock',
      result.efficiencyScore ?? null,
      result.energySavedPercent ?? null,
      result.mostEfficientCombo || null,
      JSON.stringify(result)
    );
  } catch (err) {
    console.warn(`[historyService] Failed to record run: ${err.message}`);
  }
}

export function listRuns(limit = 20) {
  try {
    const rows = listStmt.all(limit);
    return rows.map((r) => ({
      id: r.id,
      createdAt: r.created_at,
      region: r.region,
      season: r.season,
      shape: r.shape,
      size: r.size,
      orientation: r.orientation,
      materialCombo: r.material_combo,
      openings: JSON.parse(r.openings_json || '{}'),
      source: r.source,
      efficiencyScore: r.efficiency_score,
      energySavedPercent: r.energy_saved_percent,
      mostEfficientCombo: r.most_efficient_combo,
    }));
  } catch (err) {
    console.warn(`[historyService] Failed to list runs: ${err.message}`);
    return [];
  }
}
