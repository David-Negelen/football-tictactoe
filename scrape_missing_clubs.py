#!/usr/bin/env python3
"""Backfill the clubs from LEAGUE_CATEGORIES that were never directly
scraped as their own squad page.

Found by comparing src/category_config.py's Bundesliga/Premier League/La
Liga/Serie A whitelists against the `clubs` table (which records every club
whose /kader/ page we've actually imported): 9 of the 78 whitelisted clubs
only appear in the data as a `from_club`/`to_club` in some other player's
transfer history, never as an imported squad. Their rosters in the game are
therefore incomplete — we're missing anyone who spent their whole career
there without ever transferring through an already-scraped club.

transfermarkt.de was down when this script was written, so club URLs are
resolved via the site's own search at run time instead of being hardcoded —
a guessed numeric /verein/<id> that happens to 404 or (worse) hit the wrong
club would silently corrupt data. Once the site is back:

    .venv/bin/python3 scrape_missing_clubs.py
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from src.config import BASE_URL
from src.db import Database
from src.http import HttpClient
from src.pipeline import ImportService
from src.scraper import TransfermarktScraper

# (name to search for, expected career_stints.club_name once imported)
MISSING_CLUBS = [
    ("Coventry City", "Coventry City"),
    ("Hull City", "Hull City"),
    ("Ipswich Town", "Ipswich Town"),
    ("Deportivo La Coruna", "Dep. La Coruña"),
    ("FC Malaga", "FC Málaga"),
    ("Racing Santander", "Rac. Santander"),
    ("Frosinone Calcio", "Frosinone"),
    ("AC Monza", "Monza"),
    ("Venezia FC", "AC Venezia 1907"),
]


def resolve_club_url(http: HttpClient, query: str) -> str | None:
    search_url = f"{BASE_URL}/schnellsuche/ergebnis/schnellsuche?query={quote(query)}"
    result = http.get_html(search_url)
    soup = BeautifulSoup(result.html, "html.parser")
    for link in soup.select("a[href]"):
        href = link.get("href") or ""
        if "/verein/" in href:
            return urljoin(BASE_URL, href)
    return None


def main() -> int:
    http = HttpClient()
    scraper = TransfermarktScraper(http)
    database = Database(Path("data/tictactoe.db"))
    database.initialize()
    service = ImportService(database=database, scraper=scraper)

    for query, expected_club_name in MISSING_CLUBS:
        print(f"\n→ Resolving: {query}")
        url = resolve_club_url(http, query)
        if not url:
            print(f"  Could not resolve a club URL for {query!r} — skipping, needs a manual URL.")
            continue
        print(f"  → {url}")

        result = service.import_club(url)
        print(f"  Imported {result.imported_players}/{result.discovered_players} players from {result.club_name}")
        if result.club_name and expected_club_name not in result.club_name and result.club_name not in expected_club_name:
            print(
                f"  WARNING: expected a club matching career_stints name {expected_club_name!r}, "
                f"got {result.club_name!r} — verify this is the right club before trusting the import."
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
