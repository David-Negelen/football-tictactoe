from __future__ import annotations

import argparse
from pathlib import Path

from .db import Database
from .pipeline import ImportService
from .scraper import TransfermarktScraper


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import Transfermarkt club data into SQLite.")
    parser.add_argument("--db", default="data/tictactoe.db", help="Path to the SQLite database file.")
    parser.add_argument("--url", action="append", default=[], help="Club or league URL. Can be passed multiple times.")
    parser.add_argument("--whitelist", help="Path to a text file with one club or league URL per line.")
    return parser


def _resolve_club_urls(raw_urls: list[str], scraper: TransfermarktScraper) -> list[str]:
    club_urls: list[str] = []
    seen: set[str] = set()

    for url in raw_urls:
        if scraper.is_league_url(url):
            print(f"League: {url}")
            league = scraper.fetch_league(url)
            print(f"  → {league.name}: {len(league.club_urls)} clubs")
            for club_url in league.club_urls:
                if club_url not in seen:
                    seen.add(club_url)
                    club_urls.append(club_url)
        else:
            if url not in seen:
                seen.add(url)
                club_urls.append(url)

    return club_urls


def main() -> int:
    args = build_parser().parse_args()

    raw_urls: list[str] = list(args.url)
    if args.whitelist:
        lines = Path(args.whitelist).read_text().splitlines()
        raw_urls += [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]

    if not raw_urls:
        print("Error: provide at least one URL via --url or --whitelist.")
        return 1

    scraper = TransfermarktScraper()
    club_urls = _resolve_club_urls(raw_urls, scraper)

    if not club_urls:
        print("Error: no club URLs found after resolving leagues.")
        return 1

    database = Database(Path(args.db))
    database.initialize()
    service = ImportService(database=database, scraper=scraper)

    for club_url in club_urls:
        result = service.import_club(club_url)
        print(
            f"Imported {result.imported_players}/{result.discovered_players} players from {result.club_name} ({result.club_url})"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
