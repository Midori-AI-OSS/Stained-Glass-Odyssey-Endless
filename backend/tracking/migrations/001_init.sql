-- Initialize tracking database schema
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    start_ts INTEGER NOT NULL,
    end_ts INTEGER,
    outcome TEXT
);

CREATE TABLE IF NOT EXISTS party_members (
    run_id TEXT NOT NULL,
    slot INTEGER NOT NULL,
    character_id TEXT NOT NULL,
    stats_json TEXT,
    PRIMARY KEY (run_id, slot),
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    room_id TEXT,
    card_id TEXT NOT NULL,
    source TEXT,
    ts INTEGER NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS relics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    room_id TEXT,
    relic_id TEXT NOT NULL,
    source TEXT,
    ts INTEGER NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS battle_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    room_id TEXT,
    turns INTEGER,
    dmg_dealt INTEGER,
    dmg_taken INTEGER,
    victory INTEGER NOT NULL,
    logs_url TEXT,
    ts INTEGER NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_pulls (
    pull_id TEXT PRIMARY KEY,
    ts INTEGER NOT NULL,
    character_id TEXT NOT NULL,
    rarity TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS menu_actions (
    action_id TEXT PRIMARY KEY,
    ts INTEGER NOT NULL,
    menu_item TEXT NOT NULL,
    result TEXT,
    details_json TEXT
);

CREATE TABLE IF NOT EXISTS game_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    room_id TEXT,
    action_type TEXT NOT NULL,
    ts INTEGER NOT NULL,
    details_json TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings_changes (
    action_id TEXT PRIMARY KEY,
    ts INTEGER NOT NULL,
    setting TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT
);

CREATE TABLE IF NOT EXISTS deck_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    room_id TEXT,
    change_type TEXT NOT NULL,
    card_id TEXT,
    ts INTEGER NOT NULL,
    details_json TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shop_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    room_id TEXT,
    item_type TEXT,
    item_id TEXT,
    cost INTEGER,
    action TEXT,
    ts INTEGER NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_choices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    room_id TEXT,
    event_name TEXT,
    choice TEXT,
    outcome_json TEXT,
    ts INTEGER NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS overlay_actions (
    action_id TEXT PRIMARY KEY,
    ts INTEGER NOT NULL,
    overlay TEXT NOT NULL,
    details_json TEXT
);

CREATE TABLE IF NOT EXISTS play_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT,
    login_ts INTEGER NOT NULL,
    logout_ts INTEGER,
    duration INTEGER
);

CREATE TABLE IF NOT EXISTS login_events (
    event_id TEXT PRIMARY KEY,
    ts INTEGER NOT NULL,
    user_id TEXT,
    method TEXT,
    success INTEGER,
    details_json TEXT
);

CREATE TABLE IF NOT EXISTS achievement_unlocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    achievement_id TEXT NOT NULL,
    ts INTEGER NOT NULL,
    details_json TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cards_run ON cards(run_id);
CREATE INDEX IF NOT EXISTS idx_relics_run ON relics(run_id);
CREATE INDEX IF NOT EXISTS idx_battles_run ON battle_summaries(run_id);
CREATE INDEX IF NOT EXISTS idx_game_actions_run ON game_actions(run_id);
CREATE INDEX IF NOT EXISTS idx_deck_changes_run ON deck_changes(run_id);
CREATE INDEX IF NOT EXISTS idx_shop_transactions_run ON shop_transactions(run_id);
CREATE INDEX IF NOT EXISTS idx_event_choices_run ON event_choices(run_id);
CREATE INDEX IF NOT EXISTS idx_achievement_unlocks_run ON achievement_unlocks(run_id);
