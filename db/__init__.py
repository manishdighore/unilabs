"""SQLite database layer for runs, agent outputs, and settings."""
import sqlite3, json, os
from datetime import datetime
from config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS runs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
        status          TEXT    NOT NULL DEFAULT 'pending',
        trigger         TEXT    NOT NULL DEFAULT 'manual',
        report_frequency TEXT   NOT NULL DEFAULT 'quarterly',
        config_json     TEXT    NOT NULL,
        report_html     TEXT,
        summary         TEXT,
        metadata_json   TEXT
    );
    CREATE TABLE IF NOT EXISTS agent_outputs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id          INTEGER NOT NULL REFERENCES runs(id),
        agent_id        TEXT    NOT NULL,
        agent_title     TEXT    NOT NULL,
        output_a        TEXT,
        output_b        TEXT,
        validated       TEXT,
        status          TEXT    NOT NULL DEFAULT 'pending',
        started_at      TEXT,
        finished_at     TEXT,
        error_msg       TEXT
    );
    CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS watchlist_alerts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
        agent_id        TEXT    NOT NULL,
        alert_type      TEXT    NOT NULL,
        title           TEXT    NOT NULL,
        body            TEXT,
        severity        TEXT    DEFAULT 'info',
        read            INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS custom_modes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        mode_name       TEXT    NOT NULL UNIQUE,
        description     TEXT,
        dynamic_params  TEXT    NOT NULL,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
        enabled         INTEGER DEFAULT 1
    );
    """)
    conn.commit()
    conn.close()

# --- Settings CRUD --------------------------------------------------------
def get_setting(key, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (key, value))
    conn.commit()
    conn.close()

# --- Runs -----------------------------------------------------------------
def create_run(config_dict, trigger="manual"):
    conn = get_conn()
    cur = conn.execute("INSERT INTO runs(config_json, trigger) VALUES(?,?)",
                       (json.dumps(config_dict), trigger))
    run_id = cur.lastrowid
    conn.commit()
    conn.close()
    return run_id

def update_run(run_id, **kwargs):
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    conn.execute(f"UPDATE runs SET {sets} WHERE id=?", (*kwargs.values(), run_id))
    conn.commit()
    conn.close()

def get_run(run_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def list_runs(limit=50):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Agent Outputs --------------------------------------------------------
def create_agent_output(run_id, agent_id, agent_title):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO agent_outputs(run_id, agent_id, agent_title) VALUES(?,?,?)",
        (run_id, agent_id, agent_title))
    out_id = cur.lastrowid
    conn.commit()
    conn.close()
    return out_id

def update_agent_output(out_id, **kwargs):
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    conn.execute(f"UPDATE agent_outputs SET {sets} WHERE id=?", (*kwargs.values(), out_id))
    conn.commit()
    conn.close()

def get_agent_outputs(run_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM agent_outputs WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Alerts ---------------------------------------------------------------
def create_alert(agent_id, alert_type, title, body="", severity="info"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO watchlist_alerts(agent_id, alert_type, title, body, severity) VALUES(?,?,?,?,?)",
        (agent_id, alert_type, title, body, severity))
    conn.commit()
    conn.close()

def list_alerts(limit=100, unread_only=False):
    conn = get_conn()
    q = "SELECT * FROM watchlist_alerts"
    if unread_only:
        q += " WHERE read=0"
    q += " ORDER BY id DESC LIMIT ?"
    rows = conn.execute(q, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Custom Modes ---------------------------------------------------------
def create_custom_mode(mode_name, description, dynamic_params):
    """Create a custom mode with dynamic analysis parameters.
    
    Args:
        mode_name: Unique name for the custom mode
        description: Human-readable description
        dynamic_params: Dict with keys like focus_area, key_questions, etc.
    
    Returns: mode_id
    """
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO custom_modes(mode_name, description, dynamic_params) VALUES(?,?,?)",
        (mode_name, description, json.dumps(dynamic_params)))
    mode_id = cur.lastrowid
    conn.commit()
    conn.close()
    return mode_id

def get_custom_mode(mode_id):
    """Get a custom mode by ID."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM custom_modes WHERE id=?", (mode_id,)).fetchone()
    conn.close()
    if row:
        result = dict(row)
        result["dynamic_params"] = json.loads(result["dynamic_params"])
        return result
    return None

def list_custom_modes(limit=50):
    """List all custom modes."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM custom_modes WHERE enabled=1 ORDER BY id DESC LIMIT ?",
        (limit,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        item = dict(r)
        item["dynamic_params"] = json.loads(item["dynamic_params"])
        result.append(item)
    return result

def update_custom_mode(mode_id, **kwargs):
    """Update a custom mode."""
    conn = get_conn()
    if "dynamic_params" in kwargs:
        kwargs["dynamic_params"] = json.dumps(kwargs["dynamic_params"])
    kwargs["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    conn.execute(f"UPDATE custom_modes SET {sets} WHERE id=?", (*kwargs.values(), mode_id))
    conn.commit()
    conn.close()

def delete_custom_mode(mode_id):
    """Soft delete (disable) a custom mode."""
    conn = get_conn()
    conn.execute("UPDATE custom_modes SET enabled=0, updated_at=? WHERE id=?",
                 (datetime.now().isoformat(), mode_id))
    conn.commit()
    conn.close()

# Database will be initialized in app startup, not at import time
# This prevents initialization errors during module import
