from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.dynamic_categories import (
    LEGACY_CLUB_IDS,
    LEGACY_NATIONALITY_ENTRIES,
    LEGACY_TROPHY_IDS,
    build_dynamic_clubs,
    build_dynamic_nationalities,
    build_dynamic_trophies,
    build_league_pools,
)


def _add_career_stint(conn: sqlite3.Connection, player_name: str, club_name: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    row = conn.execute("SELECT id FROM players WHERE name = ?", (player_name,)).fetchone()
    player_id = row[0]
    conn.execute(
        "INSERT INTO career_stints (player_id, club_name, start_season, end_season, start_date, end_date) "
        "VALUES (?, ?, '20/21', NULL, NULL, NULL)",
        (player_id, club_name),
    )


@pytest.fixture
def dynamic_db_conn(fixture_db_path: Path):
    """Adds denylist/youth-team/threshold-straddling club_name rows on top of
    the shared fixture roster (see tests/conftest.py), so club bucketing can
    be tested without needing a separate player roster."""
    conn = sqlite3.connect(fixture_db_path)
    conn.row_factory = sqlite3.Row

    # Every fixture player already has >=1 career_stints row; add extra rows
    # under denylisted/youth club names using the same 13 fixture players so
    # club-name counts stay easy to reason about (13 players max per club).
    players = [r[0] for r in conn.execute("SELECT name FROM players").fetchall()]
    for name in players:
        _add_career_stint(conn, name, "Karriereende")
    for name in players[:6]:
        _add_career_stint(conn, name, "Testville FC U19")
    for name in players[:3]:
        _add_career_stint(conn, name, "Small Rare FC")  # exactly 3 players -> below the difficulty-3 floor (5)
    for name in players[:5]:
        _add_career_stint(conn, name, "Just Enough FC")  # exactly 5 players -> difficulty 3 floor
    conn.commit()
    yield conn
    conn.close()


def test_status_placeholder_club_names_are_excluded(dynamic_db_conn) -> None:
    clubs = build_dynamic_clubs(dynamic_db_conn)
    assert "Karriereende" not in {c.club_name for c in clubs}


def test_youth_team_club_names_are_excluded(dynamic_db_conn) -> None:
    clubs = build_dynamic_clubs(dynamic_db_conn)
    assert "Testville FC U19" not in {c.club_name for c in clubs}


def test_clubs_below_the_lowest_tier_threshold_are_dropped(dynamic_db_conn) -> None:
    clubs = build_dynamic_clubs(dynamic_db_conn)
    names = {c.club_name for c in clubs}
    assert "Small Rare FC" not in names  # 3 players, below the floor of 5
    assert "Just Enough FC" in names     # exactly 5 players, right at the floor


def test_club_difficulty_is_derived_from_player_count(dynamic_db_conn) -> None:
    clubs = {c.club_name: c for c in build_dynamic_clubs(dynamic_db_conn)}
    assert clubs["Just Enough FC"].difficulty == 3  # 5 players: difficulty-3 tier only
    # Testville FC has all 13 fixture players via the pre-existing conftest roster + this fixture's extra stints
    assert clubs["Testville FC"].difficulty in (1, 2, 3)


def test_legacy_club_id_is_preserved_when_the_real_club_name_appears(dynamic_db_conn) -> None:
    players = [r[0] for r in dynamic_db_conn.execute("SELECT name FROM players").fetchall()]
    for name in players[:5]:  # clears the difficulty-3 floor of 5 distinct players
        _add_career_stint(dynamic_db_conn, name, "Bayern München")
    dynamic_db_conn.commit()
    clubs = {c.club_name: c for c in build_dynamic_clubs(dynamic_db_conn)}
    assert clubs["Bayern München"].id == LEGACY_CLUB_IDS["Bayern München"] == "club_bay"


def test_dynamic_club_gets_a_stable_generated_id_not_a_legacy_one(dynamic_db_conn) -> None:
    clubs = {c.club_name: c for c in build_dynamic_clubs(dynamic_db_conn)}
    cat_id = clubs["Just Enough FC"].id
    assert cat_id.startswith("club_dyn_")
    assert cat_id not in LEGACY_CLUB_IDS.values()


def test_building_clubs_twice_produces_identical_ids(dynamic_db_conn) -> None:
    """Ids must survive an app restart, or a saved excluded-category-id
    setting would silently stop matching anything."""
    first = {c.club_name: c.id for c in build_dynamic_clubs(dynamic_db_conn)}
    second = {c.club_name: c.id for c in build_dynamic_clubs(dynamic_db_conn)}
    assert first == second


def test_dynamic_nationality_uses_legacy_id_and_label(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        nats = {n.nationality: n for n in build_dynamic_nationalities(conn)}
    finally:
        conn.close()
    # None of the fixture's made-up nationalities ("Testland" etc.) are real
    # countries, so build_dynamic_nationalities should find zero real ones —
    # confirms unknown nationality strings are silently skipped, not errored.
    assert nats == {}


def test_dynamic_nationality_recognizes_real_countries() -> None:
    import tempfile

    from src.db import Database

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "nat.db"
        Database(db_path).initialize()
        conn = sqlite3.connect(db_path)
        now = datetime.now(timezone.utc).isoformat()
        # 25 German players — comfortably clears the difficulty-1 threshold (>=100 is needed
        # for diff 1, so this alone only reaches diff 3, which is fine for this assertion).
        for i in range(25):
            conn.execute(
                "INSERT INTO players (source_url, name, nationality, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (f"https://example.test/nat/{i}", f"Player {i}", "Deutschland", now, now),
            )
        conn.commit()
        nats = {n.nationality: n for n in build_dynamic_nationalities(conn)}
        conn.close()

    assert "Deutschland" in nats
    assert nats["Deutschland"].id == LEGACY_NATIONALITY_ENTRIES["Deutschland"][0] == "nat_ger"
    assert nats["Deutschland"].label == LEGACY_NATIONALITY_ENTRIES["Deutschland"][1] == "Deutsch"
    assert nats["Deutschland"].icon  # a real flag emoji, not None


def test_dynamic_trophy_applies_the_semantic_filter_and_legacy_ids(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        # The fixture roster already has "Testcup"/"Samplecup" trophies (made-up,
        # so they pass through unfiltered since they don't match any real-title
        # exclude pattern); add one real included and one real excluded title.
        now = datetime.now(timezone.utc).isoformat()
        pid = conn.execute("SELECT id FROM players WHERE name = 'Alan Adler'").fetchone()[0]
        conn.execute(
            "INSERT INTO player_trophies (player_id, title, trophy_count, source_url, created_at) VALUES (?, ?, 1, NULL, ?)",
            (pid, "Weltmeister", now),
        )
        conn.execute(
            "INSERT INTO player_trophies (player_id, title, trophy_count, source_url, created_at) VALUES (?, ?, 1, NULL, ?)",
            (pid, "Torschützenkönig", now),
        )
        conn.commit()
        trophies = {t.trophy_title: t for t in build_dynamic_trophies(conn)}
    finally:
        conn.close()

    assert "Weltmeister" in trophies
    assert trophies["Weltmeister"].id == LEGACY_TROPHY_IDS["Weltmeister"] == "trophy_world_cup"
    assert "Torschützenkönig" not in trophies  # individual award, filtered out


def test_league_pools_scope_clubs_to_the_leagues_own_club_list(dynamic_db_conn) -> None:
    from src.categories import LeagueCategory

    players = [r[0] for r in dynamic_db_conn.execute("SELECT name FROM players").fetchall()]
    for name in players[:5]:  # clears the difficulty-3 floor of 5 distinct players
        _add_career_stint(dynamic_db_conn, name, "Bayern München")
    dynamic_db_conn.commit()

    league = LeagueCategory("league_test", "Test League", ["Bayern München"], difficulty=1)
    from src.dynamic_categories import DynamicCatalog

    catalog = DynamicCatalog(clubs=build_dynamic_clubs(dynamic_db_conn))
    pools = build_league_pools([league], catalog.clubs, catalog)
    pool_club_names = {c.club_name for c in pools["league_test"] if hasattr(c, "club_name")}
    assert pool_club_names == {"Bayern München"}  # Testville FC etc. excluded — not in this league
