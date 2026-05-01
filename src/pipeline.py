from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from .db import Database
from .models import ClubImportResult, ClubRecord
from .scraper import TransfermarktScraper

_FROM_YEAR = 1970


@dataclass
class ImportService:
    database: Database
    scraper: TransfermarktScraper

    def import_club(self, club_url: str) -> ClubImportResult:
        print(f"\n→ Club: {club_url}")
        print("  Fetching current squad...")
        current_page = self.scraper.fetch_club(club_url)
        print(f"  Club: {current_page.name}")

        scraped_at = datetime.now(timezone.utc)
        club_id = self.database.upsert_club(
            ClubRecord(source_url=club_url, name=current_page.name, scraped_at=scraped_at)
        )
        run_id = self.database.start_scrape_run(club_url=club_url, club_name=current_page.name)

        to_year = date.today().year - 1
        historical_years = list(range(_FROM_YEAR, to_year + 1))
        total_seasons = 1 + len(historical_years)

        seen_player_urls: set[str] = set()
        discovered = 0
        imported = 0
        skipped = 0

        try:
            # Current squad first, then historical seasons oldest-to-newest
            seasons = [("current", club_url)] + [
                (str(y), f"{club_url.rstrip('/')}/saison_id/{y}") for y in historical_years
            ]

            for season_num, (label, season_url) in enumerate(seasons, 1):
                print(f"  [{season_num:3d}/{total_seasons}] Season {label}: fetching squad...")
                try:
                    page = self.scraper.fetch_club(season_url)
                except Exception as exc:
                    print(f"               ✗ failed ({exc}), skipping")
                    continue

                new_urls = [u for u in page.player_urls if u not in seen_player_urls]
                seen_player_urls.update(page.player_urls)

                if not new_urls:
                    print(f"               0 new players")
                    continue

                print(f"               {len(new_urls)} new player URLs → importing...")

                for player_url in new_urls:
                    discovered += 1
                    if self.database.player_exists(player_url):
                        print(f"               ~ SKIP (already in DB)  {player_url}")
                        skipped += 1
                        continue

                    try:
                        player = self.scraper.fetch_player(player_url)
                    except Exception as exc:
                        print(f"               ✗ fetch failed ({exc}), skipping")
                        skipped += 1
                        continue

                    if not player.name:
                        print(f"               ✗ no name, skipping")
                        skipped += 1
                        continue

                    stints_summary = ""
                    if player.career_stints:
                        parts = [
                            f"{s.club_name} ({s.start_season or '?'}→{s.end_season or 'present'})"
                            for s in player.career_stints
                        ]
                        stints_summary = " | ".join(parts)

                    print(
                        f"               + {player.name} | "
                        f"{player.position or '?'} | "
                        f"{player.nationality or '?'} | "
                        f"age {player.age or '?'} | "
                        f"{len(player.transfers)} transfers"
                    )
                    if stints_summary:
                        print(f"                 stints: {stints_summary}")

                    player_id = self.database.upsert_player(player)
                    self.database.upsert_player_club(player_id, club_id, player.scraped_at)
                    self.database.replace_transfers(player_id, player.transfers, player.scraped_at)
                    self.database.replace_career_stints(player_id, player.career_stints)
                    imported += 1

            self.database.finish_scrape_run(run_id, "success", None)
        except Exception as exc:
            self.database.finish_scrape_run(run_id, "failed", str(exc))
            raise

        print(f"  ✓ Imported {imported}/{discovered} players ({skipped} skipped)\n")
        return ClubImportResult(
            club_url=club_url,
            club_name=current_page.name,
            discovered_players=discovered,
            imported_players=imported,
            skipped_players=skipped,
        )
