from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .db import Database
from .models import ClubImportResult, ClubRecord
from .scraper import TransfermarktScraper


@dataclass
class ImportService:
    database: Database
    scraper: TransfermarktScraper

    def import_club(self, club_url: str) -> ClubImportResult:
        print(f"\n→ Club: {club_url}")
        print("  Fetching squad page...")
        club_page = self.scraper.fetch_club(club_url)
        print(f"  Club: {club_page.name}")
        print(f"  Players found: {len(club_page.player_urls)}")

        scraped_at = datetime.now(timezone.utc)
        club_id = self.database.upsert_club(
            ClubRecord(source_url=club_url, name=club_page.name, scraped_at=scraped_at)
        )
        run_id = self.database.start_scrape_run(club_url=club_url, club_name=club_page.name)

        total = len(club_page.player_urls)
        discovered_players = 0
        imported_players = 0
        skipped_players = 0

        try:
            for i, player_url in enumerate(club_page.player_urls, 1):
                discovered_players += 1
                if self.database.player_exists(player_url):
                    print(f"  [{i:3d}/{total}] SKIP (already in DB)  {player_url}")
                    skipped_players += 1
                    continue

                print(f"  [{i:3d}/{total}] {player_url}")
                try:
                    player = self.scraper.fetch_player(player_url)
                except Exception as exc:
                    print(f"           ✗ fetch failed ({exc}), skipping")
                    skipped_players += 1
                    continue

                if not player.name:
                    print(f"           ✗ no name, skipping")
                    skipped_players += 1
                    continue

                stints_summary = ""
                if player.career_stints:
                    parts = []
                    for s in player.career_stints:
                        start = s.start_season or "?"
                        end = s.end_season or "present"
                        parts.append(f"{s.club_name} ({start}→{end})")
                    stints_summary = " | ".join(parts)

                print(
                    f"           {player.name} | "
                    f"{player.position or '?'} | "
                    f"{player.nationality or '?'} | "
                    f"age {player.age or '?'} | "
                    f"{len(player.transfers)} transfers"
                )
                if stints_summary:
                    print(f"           stints: {stints_summary}")

                player_id = self.database.upsert_player(player)
                self.database.upsert_player_club(player_id, club_id, player.scraped_at)
                self.database.replace_transfers(player_id, player.transfers, player.scraped_at)
                self.database.replace_career_stints(player_id, player.career_stints)
                imported_players += 1

            self.database.finish_scrape_run(run_id, "success", None)
        except Exception as exc:
            self.database.finish_scrape_run(run_id, "failed", str(exc))
            raise

        print(f"  ✓ Imported {imported_players}/{discovered_players} players ({skipped_players} skipped)\n")
        return ClubImportResult(
            club_url=club_url,
            club_name=club_page.name,
            discovered_players=discovered_players,
            imported_players=imported_players,
            skipped_players=skipped_players,
        )
