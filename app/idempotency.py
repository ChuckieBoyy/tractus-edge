# app/idempotency.py
import sqlite3
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timezone

DB_PATH = Path("state.sqlite")

DDL = """
CREATE TABLE IF NOT EXISTS idempotency (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  idempotency_key TEXT NOT NULL,
  device_id       TEXT NOT NULL,
  capability      TEXT NOT NULL,
  created_at      TEXT NOT NULL,
  status          TEXT NOT NULL,     -- accepted | completed | failed
  result_json     TEXT,               -- response to return on duplicate
  UNIQUE(idempotency_key)
);
"""

def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute(DDL)
    return con

def reserve(key: str, device_id: str, capability: str) -> bool:
    """Try to reserve a key; returns True if reserved, False if duplicate exists."""
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        try:
            con.execute(
                "INSERT INTO idempotency (idempotency_key, device_id, capability, created_at, status) "
                "VALUES (?, ?, ?, ?, 'accepted')",
                (key, device_id, capability, now),
            )
            return True
        except sqlite3.IntegrityError:
            return False

def complete(key: str, result_json: str, status: str = "completed") -> None:
    with _conn() as con:
        con.execute(
            "UPDATE idempotency SET status=?, result_json=? WHERE idempotency_key=?",
            (status, result_json, key),
        )

def lookup(key: str) -> Optional[Tuple[str, str]]:
    """Return (status, result_json) if exists, else None."""
    with _conn() as con:
        cur = con.execute(
            "SELECT status, result_json FROM idempotency WHERE idempotency_key=?",
            (key,),
        )
        row = cur.fetchone()
        return (row[0], row[1]) if row else None
