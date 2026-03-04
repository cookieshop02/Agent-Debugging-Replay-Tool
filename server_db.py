"""
server_db.py  — PHASE 3 VERSION
─────────────────────────────────
Added to users table:
  - name           (display name)
  - password_hash  (bcrypt hashed password, never plain text)

Everything else unchanged from Phase 2.
"""

import sqlite3
from datetime import datetime

DB_PATH = "server.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # users — now stores name + hashed password
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            api_key        TEXT PRIMARY KEY,
            name           TEXT,
            email          TEXT UNIQUE,
            password_hash  TEXT,
            created_at     TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id            TEXT PRIMARY KEY,
            api_key       TEXT,
            name          TEXT,
            status        TEXT DEFAULT 'running',
            started_at    TEXT,
            ended_at      TEXT,
            total_cost    REAL DEFAULT 0,
            total_tokens  INTEGER DEFAULT 0,
            FOREIGN KEY (api_key) REFERENCES users(api_key)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS steps (
            id          TEXT PRIMARY KEY,
            session_id  TEXT,
            step_number INTEGER,
            step_type   TEXT,
            input_text  TEXT,
            output_text TEXT,
            duration_ms REAL,
            tokens_used INTEGER DEFAULT 0,
            cost_usd    REAL DEFAULT 0,
            status      TEXT DEFAULT 'success',
            error_msg   TEXT,
            timestamp   TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database ready")


# ── USER HELPERS ──────────────────────────────

def email_exists(email: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT api_key FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return row is not None


def is_valid_key(api_key: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT api_key FROM users WHERE api_key=?", (api_key,)).fetchone()
    conn.close()
    return row is not None


def create_user(api_key: str, name: str, email: str, password_hash: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO users (api_key, name, email, password_hash, created_at) VALUES (?,?,?,?,?)",
        (api_key, name, email, password_hash, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_user_by_email(email: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_key(api_key: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE api_key=?", (api_key,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── SESSION HELPERS ───────────────────────────

def create_session(api_key, session_id, name, started_at):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO sessions (id,api_key,name,status,started_at) VALUES (?,?,?,'running',?)",
                 (session_id, api_key, name, started_at))
    conn.commit()
    conn.close()


def update_session(session_id, status, ended_at, total_cost, total_tokens):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE sessions SET status=?,ended_at=?,total_cost=?,total_tokens=? WHERE id=?",
                 (status, ended_at, total_cost, total_tokens, session_id))
    conn.commit()
    conn.close()


def fetch_sessions(api_key):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM sessions WHERE api_key=? ORDER BY started_at DESC", (api_key,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_session(api_key, session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM sessions WHERE id=? AND api_key=?", (session_id, api_key)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session_db(api_key, session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM steps WHERE session_id=?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id=? AND api_key=?", (session_id, api_key))
    conn.commit()
    conn.close()


# ── STEP HELPERS ──────────────────────────────

def create_step(data):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO steps (id,session_id,step_number,step_type,input_text,output_text,
        duration_ms,tokens_used,cost_usd,status,error_msg,timestamp)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (data["id"], data["session_id"], data["step_number"], data["step_type"],
          data["input_text"], data["output_text"], data["duration_ms"], data["tokens_used"],
          data["cost_usd"], data["status"], data.get("error_msg"), data["timestamp"]))
    conn.commit()
    conn.close()


def fetch_steps(session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM steps WHERE session_id=? ORDER BY step_number ASC",
                        (session_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]