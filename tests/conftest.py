from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.categories import (
    AgeCategory,
    ClubCategory,
    MarketValueCategory,
    NationalityCategory,
    PositionCategory,
    TrophyCategory,
)
from src.db import Database

# ─── Fixture roster ──────────────────────────────────────────────────────────
# A small, hand-crafted set of players with deliberately-chosen overlapping
# attributes, so that FIXTURE_CATEGORIES below has known, non-empty pairwise
# intersections. See test_puzzle_generation.py for why every pairwise
# intersection (not just some) needs to be non-empty.
#
# name, age, nationality, position, market_value, club, career_clubs, trophies
#
# Alan Adler and Carl Cole additionally carry stints at "Third FC",
# "Fourth United" and "Fifth FC" — three extra clubs that exist purely so
# fixture_categories below can offer 4 distinct club categories
# (t_club/t_club2/t_club3/t_club4), all with the same non-empty-overlap-
# against-every-broad-category guarantee as t_club, *and* non-empty overlap
# against each other: between them, Alan (Testland/Defense/Testcup/U23) and
# Carl (Testland/High-value/Testcup) already cover every one of the 5 broad
# fixture categories, so any club the two of them share inherits full
# coverage for free — including club x club, since both play at all four.
PLAYERS = [
    ("Alan Adler",     22, "Testland",             "Defense - Center Back", "€5.00m",  "Testville FC",  ["Testville FC", "Third FC", "Fourth United", "Fifth FC"],  ["Testcup"]),
    ("Bella Bauer",    29, "Sampleland",            "Defense - Full Back",   "€25.00m", "Sample United", ["Sample United"],                  []),
    ("Carl Cole",      31, "Testland",              "Midfield - Central",    "€15.00m", "Testville FC",  ["Testville FC", "Fixture Town", "Third FC", "Fourth United", "Fifth FC"],   ["Testcup", "Samplecup"]),
    ("Dana Diaz",      19, "Fixturia",              "Attack - Striker",      "€500k",   "Fixture Town",  ["Fixture Town"],                   []),
    ("Elan Evans",     35, "Sampleland",            "Goalkeeper",            "€1.00m",  "Demo Athletic", ["Demo Athletic"],                  ["Samplecup"]),
    ("Farid Fischer",  22, "Testland Sampleland",   "Midfield - Defensive",  "€20.00m", "Sample United", ["Sample United", "Testville FC"],  []),
    ("#7 Gina Gomez",  27, "Fixturia",              "Attack - Winger",       "€30.00m", "Testville FC",  ["Testville FC"],                   ["Testcup"]),
    ("Hugo Haas",      33, "Testland",              "Defense - Center Back", "€3.00m",  "Fixture Town",  ["Fixture Town", "Demo Athletic"],  []),
    ("Ines Ibarra",    21, "Sampleland",            "Attack - Striker",      "€12.00m", "Demo Athletic", ["Demo Athletic"],                  []),
    ("#9 Jonas Young", 26, "Fixturia",              "Midfield - Central",    "€18.00m", "Sample United", ["Sample United"],                  ["Samplecup"]),
    ("Kara Klein",     30, "Testland",              "Attack - Striker",      "€40.00m", "Testville FC",  ["Testville FC"],                   ["Testcup", "Samplecup"]),
    ("Liam Lopez",     20, "Sampleland",            "Defense - Full Back",   "€2.00m",  "Fixture Town",  ["Fixture Town"],                   []),
    ("José Núñez",     24, "Fixturia",              "Midfield - Central",    "€4.00m",  "Demo Athletic", ["Demo Athletic"],                  []),
]


def _insert_player(
    conn: sqlite3.Connection, idx: int, name: str, age: int, nationality: str,
    position: str, market_value: str, club: str, career_clubs: list[str], trophies: list[str],
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """INSERT INTO players
           (source_url, name, age, nationality, position, market_value,
            contract_expires, current_club_name, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)""",
        (f"https://example.test/player/{idx}", name, age, nationality, position,
         market_value, club, now, now),
    )
    player_id = int(cur.lastrowid)
    for club_name in career_clubs:
        conn.execute(
            """INSERT INTO career_stints (player_id, club_name, start_season, end_season, start_date, end_date)
               VALUES (?, ?, '20/21', NULL, NULL, NULL)""",
            (player_id, club_name),
        )
    for title in trophies:
        conn.execute(
            """INSERT INTO player_trophies (player_id, title, trophy_count, source_url, created_at)
               VALUES (?, ?, 1, NULL, ?)""",
            (player_id, title, now),
        )
    return player_id


@pytest.fixture
def fixture_db_path(tmp_path: Path) -> Path:
    """A small SQLite DB (schema via the real Database class) seeded with PLAYERS."""
    db_path = tmp_path / "fixture.db"
    db = Database(db_path)
    db.initialize()
    conn = db.connect()
    try:
        for idx, row in enumerate(PLAYERS, start=1):
            _insert_player(conn, idx, *row)
        conn.commit()
    finally:
        conn.close()
    return db_path


@pytest.fixture
def fixture_categories() -> dict[str, object]:
    """Nine categories with hand-verified, non-empty pairwise intersections
    against PLAYERS. The first six (t_club/t_nat/t_pos/t_mv/t_trophy/t_age)
    are the original set — every one of their 15 possible pairs has at
    least one eligible player in common. t_club2/t_club3/t_club4 are
    appended after them (not interleaved) so code that slices "the first N"
    of this dict keeps seeing the original six in the original order (see
    tests/test_multiplayer.py's _room() helper); each has the same
    non-empty overlap against every one of the five non-club categories
    (t_nat/t_pos/t_mv/t_trophy/t_age) as t_club, *and* against each other —
    needed because _sample_general_puzzle_categories (see app.py) requires
    GENERAL_MIN_CLUBS + GENERAL_EXTRA_CLUBS (4) real clubs to generate a
    general-pool puzzle at all: 3 confined to one whole side (no club x
    club overlap needed among those three) plus 1 more mixed into the other
    side, which does need club x club overlap against the first three."""
    cats = [
        ClubCategory("t_club", "Testville FC", "Testville FC", difficulty=1),
        NationalityCategory("t_nat", "Testland", "Testland", difficulty=1),
        PositionCategory("t_pos", "Defense", "Defense", difficulty=1),
        MarketValueCategory("t_mv", "High value", min_value=10_000_000, difficulty=1),
        TrophyCategory("t_trophy", "Testcup", "Testcup", difficulty=1),
        AgeCategory("t_age", "U23", max_age=23, difficulty=1),
        ClubCategory("t_club2", "Third FC", "Third FC", difficulty=1),
        ClubCategory("t_club3", "Fourth United", "Fourth United", difficulty=1),
        ClubCategory("t_club4", "Fifth FC", "Fifth FC", difficulty=1),
    ]
    return {cat.id: cat for cat in cats}


@pytest.fixture
def app_client(monkeypatch, fixture_db_path, fixture_categories):
    """Flask test client wired to the fixture DB and the known category set above."""
    import app as app_module

    monkeypatch.setattr(app_module, "DB_PATH", str(fixture_db_path))
    monkeypatch.setattr(app_module, "ALL_CATEGORIES", list(fixture_categories.values()))
    monkeypatch.setattr(app_module, "CATEGORY_BY_ID", fixture_categories)
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()
