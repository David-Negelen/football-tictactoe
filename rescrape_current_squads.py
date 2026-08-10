#!/usr/bin/env python3
"""Smart rescrape: refresh every already-known club's *current* squad only.

A full import_club() run re-walks every historical season page too, which
is why the last full scrape took 1.5-3.5h per club (see scrape_runs) — but
historical rosters never change once imported, so that's wasted work on a
rescrape. This script instead:

  - fetches only the current squad page per club (historical=False)
  - re-fetches players already in the DB instead of skipping them
    (refresh_existing=True), so a completed transfer, a market-value
    change, or a new trophy since the last scrape gets picked up
  - still imports any brand-new signing found on the current squad

Clubs are processed oldest-updated-first, so if this gets interrupted the
staleest data was refreshed first.

    .venv/bin/python3 rescrape_current_squads.py
"""

from __future__ import annotations

from pathlib import Path

from src.db import Database
from src.http import HttpClient
from src.pipeline import ImportService
from src.scraper import TransfermarktScraper


def main() -> int:
    http = HttpClient()
    scraper = TransfermarktScraper(http)
    database = Database(Path("data/tictactoe.db"))
    database.initialize()
    service = ImportService(database=database, scraper=scraper)

    with database.connect() as conn:
        clubs = conn.execute(
            "SELECT source_url, name, updated_at FROM clubs ORDER BY updated_at ASC"
        ).fetchall()

    print(f"Rescraping current squads for {len(clubs)} known clubs...\n")

    totals = {"new": 0, "refreshed": 0, "skipped": 0}
    for i, row in enumerate(clubs, 1):
        print(f"[{i}/{len(clubs)}] {row['name']} (last updated {row['updated_at']})")
        try:
            result = service.import_club(row["source_url"], historical=False, refresh_existing=True)
        except Exception as exc:
            print(f"  ✗ FAILED: {exc}\n")
            continue
        totals["new"] += result.imported_players
        totals["refreshed"] += result.refreshed_players
        totals["skipped"] += result.skipped_players

    print(
        f"\nDone. {totals['new']} new signings imported, "
        f"{totals['refreshed']} existing players refreshed, "
        f"{totals['skipped']} skipped (fetch failures)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
