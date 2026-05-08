#!/usr/bin/env python3
"""Fetch and update trophy data for all players from Transfermarkt.

This backfill refreshes the new player_trophies table by scraping each player's
profile page and achievements page, then writing the trophy titles and counts
into SQLite.

Usage:
    python3 update_trophies.py [--db data/tictactoe.db] [--delay 1.5] [--limit N]
"""
from __future__ import annotations

# Bootstrap venv site-packages so the script works regardless of how it's invoked.
import sys as _sys
from pathlib import Path as _Path
_site = next(iter(sorted(_Path(__file__).parent.glob(".venv/lib/python*/site-packages"))), None)
if _site and str(_site) not in _sys.path:
    _sys.path.insert(0, str(_site))
del _sys, _Path, _site

import argparse
from datetime import datetime, timezone
import sys
import time
from pathlib import Path

from src.db import Database
from src.scraper import TransfermarktScraper


def main() -> int:
    parser = argparse.ArgumentParser(description="Update trophy data for all players.")
    parser.add_argument("--db", default="data/tictactoe.db")
    parser.add_argument("--delay", type=float, default=1.5, help="Seconds between requests")
    parser.add_argument("--limit", type=int, default=None, help="Max players to update (for testing)")
    parser.add_argument("--start-id", type=int, default=None, help="Resume from this player ID (inclusive)")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    database = Database(db_path)
    database.initialize()
    scraper = TransfermarktScraper()

    with database.connect() as conn:
        if args.start_id:
            rows = conn.execute(
                "SELECT id, name, source_url FROM players WHERE source_url IS NOT NULL AND id >= ? ORDER BY id",
                (args.start_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, source_url FROM players WHERE source_url IS NOT NULL ORDER BY id"
            ).fetchall()

    if args.limit:
        rows = rows[: args.limit]

    total = len(rows)
    print(f"Found {total} players to update.")

    updated = 0
    skipped = 0
    last_request = 0.0

    for index, row in enumerate(rows, 1):
        elapsed = time.monotonic() - last_request
        if elapsed < args.delay:
            time.sleep(args.delay - elapsed)

        try:
            trophies = scraper.fetch_player_trophies(row["source_url"])
        except Exception as exc:
            print(f"  [{index}/{total}] ✗ fetch error — {row['name']}: {exc}", file=sys.stderr)
            skipped += 1
            last_request = time.monotonic()
            continue

        last_request = time.monotonic()
        database.replace_trophies(row["id"], trophies, datetime.now(timezone.utc))
        updated += 1
        print(f"  [{index}/{total}] {len(trophies):>3} trophies — {row['name']}")

    print(f"\nDone. Updated: {updated}  Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
