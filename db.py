import sqlite3
from pathlib import Path

DB = Path("data/applications.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY,
    job_id TEXT UNIQUE NOT NULL,
    company TEXT, title TEXT, url TEXT,
    description TEXT,
    score INTEGER, rationale TEXT,
    draft_answers TEXT,
    status TEXT DEFAULT 'DISCOVERED',
    attempt INTEGER DEFAULT 0,
    screenshot_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_status ON applications(status);
"""

def get_db():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con

def update_status(con, job_id, status, **fields):
    """Updates the status and any other provided fields for a specific job."""
    sets = ", ".join([f"{k}=?" for k in fields] + ["status=?", "updated_at=CURRENT_TIMESTAMP"])
    vals = list(fields.values()) + [status, job_id]
    con.execute(f"UPDATE applications SET {sets} WHERE job_id=?", vals)
    con.commit()
