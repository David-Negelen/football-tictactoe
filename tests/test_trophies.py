from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.categories import TrophyCategory
from src.db import Database
from src.scraper import TransfermarktScraper


def test_scraper_parses_trophies_from_profile_and_achievements() -> None:
    scraper = TransfermarktScraper()

    profile_html = """
    <html>
      <body>
        <a href="/lionel-messi/erfolge/spieler/28003">Weltfußballer 4</a>
        <a href="/lionel-messi/erfolge/spieler/28003">Gewinner Ballon d'Or 8</a>
        <a href="/lionel-messi/erfolge/spieler/28003">Alle Titel & Erfolge</a>
      </body>
    </html>
    """

    achievements_html = """
    <html>
      <body>
        <h2>4X WELTFUSSBALLER</h2>
        <h2>8X GEWINNER BALLON D'OR</h2>
        <h2>1X WELTMEISTER</h2>
      </body>
    </html>
    """

    profile_trophies = scraper._extract_profile_trophies(profile_html, "https://example.test/player")
    achievements_trophies = scraper._extract_achievement_trophies(achievements_html, "https://example.test/awards")
    combined = scraper._dedupe_trophies(profile_trophies + achievements_trophies)

    assert [t.title for t in combined] == ["Weltfußballer", "Gewinner Ballon d'Or", "Weltmeister"]
    assert [t.count for t in combined] == [4, 8, 1]


def test_trophy_category_checks_player_trophies(tmp_path: Path) -> None:
    db = Database(tmp_path / "sample.db")
    db.initialize()

    with db.connect() as conn:
        player_id = conn.execute(
            "INSERT INTO players (source_url, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (
                "https://example.test/player",
                "Test Player",
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
            ),
        ).lastrowid
        conn.execute(
            "INSERT INTO player_trophies (player_id, title, trophy_count, source_url, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                player_id,
                "Weltmeister",
                1,
                "https://example.test/awards",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    category = TrophyCategory("trophy_world_cup", "Weltmeister", "Weltmeister")

    with db.connect() as conn:
        assert category.check_player(int(player_id), conn)
        assert int(player_id) in category.eligible_player_ids(conn)
        assert category.sql_filter() == (
            "EXISTS (SELECT 1 FROM player_trophies pt WHERE pt.player_id = p.id AND pt.title = ?)",
            ["Weltmeister"],
        )
