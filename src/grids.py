"""Persistence for two features built on the same shape — a fixed set of 3
row + 3 column category ids that should keep resolving to the exact same
puzzle across requests and server restarts:

- The daily curated grid (see app.py's /api/daily/today), keyed by date.
- Custom grids built in the editor and shared via a short code (see
  app.py's /api/grids), keyed by a generated code — the same short,
  unambiguous-alphabet code style already used for multiplayer room codes
  (src/multiplayer.py), reused here for a consistent, easy-to-read-aloud
  sharing experience.

Only category ids are ever stored, never full category data — the caller
resolves ids back to real Category objects (via app.py's CATEGORY_BY_ID),
exactly like excluded-category-id settings and LeagueScopedCategory ids
already work elsewhere in this app. This keeps a saved/daily grid valid
across category-catalog changes as long as the id still exists; if it
doesn't (e.g. a club fell out of the prominence whitelist later), the
caller treats that as "not found" rather than crashing — see the callers
in app.py for how they handle a missing id.
"""

from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timezone

# Unambiguous alphabet (no 0/O/1/I) — matches src/multiplayer.py's room
# codes, so both kinds of "enter this code" flow in the app feel consistent.
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 6


def _new_grid_code(db: sqlite3.Connection) -> str:
    while True:
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
        exists = db.execute("SELECT 1 FROM saved_grids WHERE code = ?", (code,)).fetchone()
        if exists is None:
            return code


def save_grid(db: sqlite3.Connection, row_ids: list[str], col_ids: list[str]) -> str:
    code = _new_grid_code(db)
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "INSERT INTO saved_grids (code, row_ids, col_ids, created_at) VALUES (?, ?, ?, ?)",
        (code, ",".join(row_ids), ",".join(col_ids), now),
    )
    db.commit()
    return code


def get_saved_grid(db: sqlite3.Connection, code: str) -> tuple[list[str], list[str]] | None:
    row = db.execute(
        "SELECT row_ids, col_ids FROM saved_grids WHERE code = ?", ((code or "").upper(),)
    ).fetchone()
    if row is None:
        return None
    return row["row_ids"].split(","), row["col_ids"].split(",")


def get_daily_grid(db: sqlite3.Connection, date: str) -> tuple[list[str], list[str]] | None:
    row = db.execute("SELECT row_ids, col_ids FROM daily_grids WHERE date = ?", (date,)).fetchone()
    if row is None:
        return None
    return row["row_ids"].split(","), row["col_ids"].split(",")


def store_daily_grid(db: sqlite3.Connection, date: str, row_ids: list[str], col_ids: list[str]) -> None:
    # REPLACE, not IGNORE: generation for a given date is deterministic (see
    # app.py's api_daily_today, seeded by the date string), so a second
    # write for the same date — whether from a concurrent request or a
    # stale-category-id repair — always carries identical or intentionally
    # refreshed content, never a conflicting alternate puzzle.
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "INSERT OR REPLACE INTO daily_grids (date, row_ids, col_ids, created_at) VALUES (?, ?, ?, ?)",
        (date, ",".join(row_ids), ",".join(col_ids), now),
    )
    db.commit()
