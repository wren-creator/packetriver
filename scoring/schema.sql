-- Packet Creek scoreboard. SQLite. Created on first boot by app.py.

CREATE TABLE IF NOT EXISTS users (
  id         INTEGER PRIMARY KEY,
  name       TEXT UNIQUE NOT NULL,
  pw_hash    TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS runs (
  id         INTEGER PRIMARY KEY,
  user_id    INTEGER NOT NULL REFERENCES users(id),
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  mode       TEXT NOT NULL DEFAULT 'normal'   -- normal | speedrun
);

-- The authoritative flag map for this session. Populated by flags.py at boot
-- (Phase 1+). base = point value before stealth/chain/speed multipliers.
CREATE TABLE IF NOT EXISTS flags (
  technique_id  TEXT PRIMARY KEY,
  flag          TEXT NOT NULL,
  subsystem     TEXT NOT NULL,
  target        TEXT NOT NULL,
  effect        TEXT NOT NULL,          -- effects.py key the sim applies
  severity      TEXT NOT NULL DEFAULT 'medium',
  base          INTEGER NOT NULL DEFAULT 100,
  location_hint TEXT
);

CREATE TABLE IF NOT EXISTS submissions (
  id           INTEGER PRIMARY KEY,
  run_id       INTEGER NOT NULL REFERENCES runs(id),
  user_id      INTEGER NOT NULL REFERENCES users(id),
  technique_id TEXT NOT NULL,
  points       INTEGER NOT NULL,
  stealth      INTEGER NOT NULL DEFAULT 0,
  chain_n      INTEGER NOT NULL DEFAULT 0,
  elapsed_s    REAL NOT NULL DEFAULT 0,
  ts           TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (run_id, technique_id)
);

CREATE TABLE IF NOT EXISTS scores (
  user_id             INTEGER PRIMARY KEY REFERENCES users(id),
  total               INTEGER NOT NULL DEFAULT 0,
  best_run_total      INTEGER NOT NULL DEFAULT 0,
  fastest_full_clear_s REAL
);
