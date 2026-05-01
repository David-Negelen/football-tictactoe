from __future__ import annotations

import argparse
from pathlib import Path

from .db import Database
from .pipeline import ImportService
from .scraper import TransfermarktScraper


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import Transfermarkt club data into SQLite.")
    parser.add_argument("--db", default="data/tictactoe.db", help="Path to the SQLite database file.")
    parser.add_argument("--club-url", action="append", default=[], help="Transfermarkt club URL to import. Can be passed multiple times.")
    parser.add_argument("--whitelist", help="Path to a text file with one club URL per line.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    club_urls: list[str] = list(args.club_url)
    if args.whitelist:
        lines = Path(args.whitelist).read_text().splitlines()
        club_urls += [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]

    if not club_urls:
        print("Error: provide at least one club URL via --club-url or --whitelist.")
        return 1

    database = Database(Path(args.db))
    database.initialize()
    service = ImportService(database=database, scraper=TransfermarktScraper())

    for club_url in club_urls:
        result = service.import_club(club_url)
        print(
            f"Imported {result.imported_players}/{result.discovered_players} players from {result.club_name} ({result.club_url})"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
