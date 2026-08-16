from __future__ import annotations

import sqlite3
from pathlib import Path

from src.categories import CategoryType, ContinentCategory, LeagueCategory


def test_league_and_continent_category_keep_their_own_category_type() -> None:
    """LeagueCategory and ContinentCategory share an implementation
    (_ClubWhitelistCategory) but must still tag instances with their own
    distinct CategoryType — app.py's excluded_types filtering (see
    _resolve_pool) keys off exactly this."""
    league = LeagueCategory("lg", "Some League", ["Testville FC"])
    continent = ContinentCategory("ct", "Some Continent", ["Testville FC"])
    assert league.type == CategoryType.LEAGUE
    assert continent.type == CategoryType.CONTINENT
    assert not isinstance(league, ContinentCategory)
    assert not isinstance(continent, LeagueCategory)


def test_league_and_continent_category_match_players_by_club_whitelist(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    conn.row_factory = sqlite3.Row
    try:
        league = LeagueCategory("lg", "Testville + Sample", ["Testville FC", "Sample United"])
        continent = ContinentCategory("ct", "Fixture + Demo", ["Fixture Town", "Demo Athletic"])

        league_ids = league.eligible_player_ids(conn)
        continent_ids = continent.eligible_player_ids(conn)

        def pid(name: str) -> int:
            return conn.execute("SELECT id FROM players WHERE name = ?", (name,)).fetchone()[0]

        assert pid("Alan Adler") in league_ids   # Testville FC
        assert pid("Bella Bauer") in league_ids   # Sample United
        assert pid("Dana Diaz") not in league_ids  # Fixture Town only

        assert pid("Dana Diaz") in continent_ids   # Fixture Town
        assert pid("Ines Ibarra") in continent_ids  # Demo Athletic
        assert pid("Alan Adler") not in continent_ids  # Testville FC only
    finally:
        conn.close()
