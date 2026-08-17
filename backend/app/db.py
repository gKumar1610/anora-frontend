from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import settings
from app.defaults import DEFAULT_SYSTEM_PROMPT, default_profile_json


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS calls (
  id TEXT PRIMARY KEY,
  room_name TEXT NOT NULL,
  direction TEXT NOT NULL DEFAULT 'inbound',
  caller_number TEXT,
  from_number TEXT,
  to_number TEXT,
  twilio_call_sid TEXT,
  sip_status_code TEXT,
  failure_reason TEXT,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  ended_at TEXT,
  duration_seconds INTEGER,
  caller_joined_at TEXT,
  caller_left_at TEXT,
  caller_duration_seconds INTEGER,
  owner_identity TEXT,
  owner_joined_at TEXT,
  agent_left_at TEXT,
  handoff_status TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transcript_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  call_id TEXT NOT NULL,
  speaker TEXT NOT NULL,
  text TEXT NOT NULL,
  is_final INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(call_id) REFERENCES calls(id)
);

CREATE TABLE IF NOT EXISTS bookings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  confirmation_code TEXT NOT NULL UNIQUE,
  guest_name TEXT NOT NULL,
  phone TEXT,
  party_size INTEGER NOT NULL,
  reservation_date TEXT NOT NULL,
  reservation_time TEXT NOT NULL,
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'confirmed',
  call_id TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(call_id) REFERENCES calls(id)
);

CREATE INDEX IF NOT EXISTS idx_calls_started_at ON calls(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_transcript_call_id ON transcript_events(call_id, id);
CREATE INDEX IF NOT EXISTS idx_bookings_created_at ON bookings(created_at DESC);
"""

CALLS_COLUMNS = {
    "direction": "TEXT NOT NULL DEFAULT 'inbound'",
    "from_number": "TEXT",
    "to_number": "TEXT",
    "sip_status_code": "TEXT",
    "failure_reason": "TEXT",
    "caller_joined_at": "TEXT",
    "caller_left_at": "TEXT",
    "caller_duration_seconds": "INTEGER",
    "owner_identity": "TEXT",
    "owner_joined_at": "TEXT",
    "agent_left_at": "TEXT",
    "handoff_status": "TEXT",
}


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        existing_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(calls)").fetchall()
        }
        for column, definition in CALLS_COLUMNS.items():
            if column not in existing_columns:
                conn.execute(f"ALTER TABLE calls ADD COLUMN {column} {definition}")
        conn.execute(
            """
            UPDATE calls
            SET status = 'completed',
                ended_at = COALESCE(ended_at, caller_left_at),
                duration_seconds = COALESCE(
                  duration_seconds,
                  CAST((julianday(COALESCE(caller_left_at, updated_at)) - julianday(started_at)) * 86400 AS INTEGER)
                ),
                updated_at = COALESCE(caller_left_at, updated_at)
            WHERE status = 'owner_active' AND caller_left_at IS NOT NULL
            """
        )
        conn.execute(
            """
            UPDATE calls
            SET status = 'completed',
                ended_at = COALESCE(ended_at, updated_at),
                duration_seconds = COALESCE(duration_seconds, 0),
                updated_at = COALESCE(ended_at, updated_at)
            WHERE id LIKE 'demo-%' AND status IN ('active', 'dialing', 'owner_active')
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO settings(key, value)
            VALUES ('system_prompt', ?)
            """,
            (DEFAULT_SYSTEM_PROMPT,),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO settings(key, value)
            VALUES ('restaurant_profile', ?)
            """,
            (default_profile_json(),),
        )
        conn.commit()
