-- Track run configuration metadata selections
CREATE TABLE IF NOT EXISTS run_configurations (
    run_id TEXT PRIMARY KEY,
    run_type TEXT,
    modifiers_json TEXT,
    reward_json TEXT,
    version TEXT,
    recorded_ts INTEGER,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

