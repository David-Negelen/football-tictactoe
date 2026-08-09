from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.dynamic_categories import (
    CLUB_FAME_TIER_1,
    CLUB_FAME_TIER_2,
    DEFAULT_CLUB_DIFFICULTY,
    DEFAULT_NATIONALITY_DIFFICULTY,
    DEFAULT_TROPHY_DIFFICULTY,
    LEGACY_CLUB_IDS,
    LEGACY_NATIONALITY_ENTRIES,
    LEGACY_TROPHY_IDS,
    NATIONALITY_DENYLIST,
    NATIONALITY_FAME_TIER_1,
    NATIONALITY_FAME_TIER_2,
    PROMINENT_CLUB_NAMES,
    PROMINENT_NATIONALITIES,
    PROMINENT_TROPHY_TITLES,
    TROPHY_FAME_TIER_1,
    TROPHY_FAME_TIER_2,
    build_dynamic_clubs,
    build_dynamic_nationalities,
    build_dynamic_trophies,
    build_league_pools,
)

# The fixture roster below uses made-up club names to get precise control
# over distinct-player counts for tier/reserve/youth-filter testing — none of
# them are (or should be) in the real PROMINENT_CLUB_NAMES whitelist, so
# tests that aren't specifically about prominence pass an explicit superset
# that also allows these fixture names through, keeping "is this a legit
# tier-3 club" and "is this club prominent enough to show by default"
# independently testable. See test_default_prominence_whitelist_excludes_an_obscure_club
# below for a test of the real, un-widened whitelist.
FIXTURE_PROMINENT_CLUB_NAMES = PROMINENT_CLUB_NAMES | {
    "Testville FC", "Testville FC U19", "Testville FC II", "Testville FC B",
    "Willem II", "Small Rare FC", "Just Enough FC",
}


def _build_clubs(conn, club_difficulty=None):
    kwargs = {"prominent_names": FIXTURE_PROMINENT_CLUB_NAMES}
    if club_difficulty is not None:
        kwargs["club_difficulty"] = club_difficulty
    return build_dynamic_clubs(conn, **kwargs)


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
    for name in players[:5]:
        _add_career_stint(conn, name, "Testville FC II")  # reserve team, above the floor
    for name in players[:5]:
        _add_career_stint(conn, name, "Testville FC B")  # reserve team, above the floor
    for name in players[:5]:
        _add_career_stint(conn, name, "Willem II")  # real club name, not a reserve marker
    conn.commit()
    yield conn
    conn.close()


def test_status_placeholder_club_names_are_excluded(dynamic_db_conn) -> None:
    clubs = _build_clubs(dynamic_db_conn)
    assert "Karriereende" not in {c.club_name for c in clubs}


def test_youth_team_club_names_are_excluded(dynamic_db_conn) -> None:
    clubs = _build_clubs(dynamic_db_conn)
    assert "Testville FC U19" not in {c.club_name for c in clubs}


def test_reserve_team_club_names_are_excluded(dynamic_db_conn) -> None:
    names = {c.club_name for c in _build_clubs(dynamic_db_conn)}
    assert "Testville FC II" not in names
    assert "Testville FC B" not in names


def test_willem_ii_is_not_treated_as_a_reserve_team(dynamic_db_conn) -> None:
    # "Willem II" is a real club whose actual name ends in "II" — not a
    # reserve-team marker like "Testville FC II" above.
    names = {c.club_name for c in _build_clubs(dynamic_db_conn)}
    assert "Willem II" in names


def test_clubs_below_the_viability_floor_are_dropped(dynamic_db_conn) -> None:
    clubs = _build_clubs(dynamic_db_conn)
    names = {c.club_name for c in clubs}
    assert "Small Rare FC" not in names  # 3 players, below the floor of 5
    assert "Just Enough FC" in names     # exactly 5 players, right at the floor


def test_club_difficulty_comes_from_the_fame_table_not_player_count(dynamic_db_conn) -> None:
    # "Just Enough FC" has only 5 players (the bare viability floor) — a
    # rarity-based scheme would call that hard. Explicitly tiering it as
    # famous must win anyway.
    clubs = {c.club_name: c for c in _build_clubs(dynamic_db_conn, club_difficulty={"Just Enough FC": 1})}
    assert clubs["Just Enough FC"].difficulty == 1


def test_a_high_player_count_club_absent_from_the_fame_table_is_hardest(dynamic_db_conn) -> None:
    # Testville FC has all 13 fixture players (the biggest club in the
    # fixture) but no fame-table entry — this is the actual bug being fixed:
    # a big player count must NOT imply an easy difficulty.
    clubs = {c.club_name: c for c in _build_clubs(dynamic_db_conn, club_difficulty={})}
    assert clubs["Testville FC"].difficulty == DEFAULT_CLUB_DIFFICULTY


def test_unlisted_clubs_default_to_the_hardest_tier() -> None:
    assert DEFAULT_CLUB_DIFFICULTY == 3


def test_every_fame_tiered_club_name_is_in_the_prominence_whitelist() -> None:
    # Catches a byte-for-byte name typo (e.g. "Manchester City" instead of
    # the real "Man City") that would otherwise silently demote a famous
    # club to the hardest tier instead of erroring.
    assert (CLUB_FAME_TIER_1 | CLUB_FAME_TIER_2) <= PROMINENT_CLUB_NAMES


def test_every_league_has_enough_easy_clubs() -> None:
    from src.category_config import LEAGUE_CATEGORIES

    for league in LEAGUE_CATEGORIES:
        tier_1_count = len(set(league.club_names) & CLUB_FAME_TIER_1)
        assert tier_1_count >= 8, f"{league.id} only has {tier_1_count} tier-1 clubs"


def test_legacy_club_id_is_preserved_when_the_real_club_name_appears(dynamic_db_conn) -> None:
    players = [r[0] for r in dynamic_db_conn.execute("SELECT name FROM players").fetchall()]
    for name in players[:5]:  # clears the difficulty-3 floor of 5 distinct players
        _add_career_stint(dynamic_db_conn, name, "Bayern München")
    dynamic_db_conn.commit()
    clubs = {c.club_name: c for c in _build_clubs(dynamic_db_conn)}
    assert clubs["Bayern München"].id == LEGACY_CLUB_IDS["Bayern München"] == "club_bay"


def test_dynamic_club_gets_a_stable_generated_id_not_a_legacy_one(dynamic_db_conn) -> None:
    clubs = {c.club_name: c for c in _build_clubs(dynamic_db_conn)}
    cat_id = clubs["Just Enough FC"].id
    assert cat_id.startswith("club_dyn_")
    assert cat_id not in LEGACY_CLUB_IDS.values()


def test_building_clubs_twice_produces_identical_ids(dynamic_db_conn) -> None:
    """Ids must survive an app restart, or a saved excluded-category-id
    setting would silently stop matching anything."""
    first = {c.club_name: c.id for c in _build_clubs(dynamic_db_conn)}
    second = {c.club_name: c.id for c in _build_clubs(dynamic_db_conn)}
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
        # 25 German players — comfortably clears NATIONALITY_MIN_PLAYERS (3);
        # Deutschland is fame-tiered to difficulty 1 regardless of count.
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
    assert nats["Deutschland"].difficulty == 1


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


def test_default_prominence_whitelist_excludes_an_obscure_trophy(fixture_db_path: Path) -> None:
    # "Intertoto-Cup-Sieger" is a real title that passes classify_trophy_
    # title (a defunct UEFA summer tournament, semantically a legitimate
    # team trophy) and clears any rarity bar in the real data — but isn't a
    # trophy any casual player would recognize, exactly the gap the
    # whitelist closes.
    conn = sqlite3.connect(fixture_db_path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        pid = conn.execute("SELECT id FROM players WHERE name = 'Alan Adler'").fetchone()[0]
        conn.execute(
            "INSERT INTO player_trophies (player_id, title, trophy_count, source_url, created_at) VALUES (?, ?, 1, NULL, ?)",
            (pid, "Intertoto-Cup-Sieger", now),
        )
        conn.commit()
        trophies = {t.trophy_title for t in build_dynamic_trophies(conn)}
    finally:
        conn.close()

    assert "Intertoto-Cup-Sieger" not in trophies
    assert "Intertoto-Cup-Sieger" not in PROMINENT_TROPHY_TITLES


def test_trophy_difficulty_comes_from_the_fame_table_not_player_count(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        pid = conn.execute("SELECT id FROM players WHERE name = 'Alan Adler'").fetchone()[0]
        conn.execute(
            "INSERT INTO player_trophies (player_id, title, trophy_count, source_url, created_at) VALUES (?, ?, 1, NULL, ?)",
            (pid, "Weltmeister", now),
        )
        conn.commit()
        # A single winner in the whole dataset — a rarity-based scheme would
        # call that hard. Explicitly tiering it as famous must win anyway.
        trophies = {
            t.trophy_title: t
            for t in build_dynamic_trophies(
                conn, prominent_titles=frozenset({"Weltmeister"}), trophy_difficulty={"Weltmeister": 1}
            )
        }
    finally:
        conn.close()

    assert trophies["Weltmeister"].difficulty == 1


def test_unlisted_trophies_default_to_the_hardest_tier() -> None:
    assert DEFAULT_TROPHY_DIFFICULTY == 3


def test_every_fame_tiered_trophy_is_in_the_prominence_whitelist() -> None:
    # Catches a typo that would otherwise silently drop a famous trophy
    # (PROMINENT_TROPHY_TITLES is defined as the union of both tiers, so
    # this can only fail if the two are edited out of sync).
    assert (TROPHY_FAME_TIER_1 | TROPHY_FAME_TIER_2) <= PROMINENT_TROPHY_TITLES


def test_trophy_fame_tiers_do_not_overlap() -> None:
    assert TROPHY_FAME_TIER_1.isdisjoint(TROPHY_FAME_TIER_2)


def test_default_prominence_whitelist_excludes_an_obscure_club(dynamic_db_conn) -> None:
    # No prominent_names override here — this is the real default whitelist.
    # "Just Enough FC" clears the rarity tier threshold (5 players) but isn't
    # a club anyone would recognize, which is exactly the gap the whitelist
    # closes: rarity alone let obscure-but-real clubs through as "hard".
    clubs = build_dynamic_clubs(dynamic_db_conn)
    assert "Just Enough FC" not in {c.club_name for c in clubs}


def test_default_prominence_whitelist_includes_a_known_club(dynamic_db_conn) -> None:
    players = [r[0] for r in dynamic_db_conn.execute("SELECT name FROM players").fetchall()]
    for name in players[:5]:
        _add_career_stint(dynamic_db_conn, name, "Bayern München")
    dynamic_db_conn.commit()
    clubs = build_dynamic_clubs(dynamic_db_conn)
    assert "Bayern München" in {c.club_name for c in clubs}


def test_denylisted_nationalities_are_excluded_even_at_high_player_counts() -> None:
    import tempfile

    from src.db import Database

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "nat.db"
        Database(db_path).initialize()
        conn = sqlite3.connect(db_path)
        now = datetime.now(timezone.utc).isoformat()
        for name in NATIONALITY_DENYLIST:
            for i in range(150):  # comfortably clears the viability floor
                conn.execute(
                    "INSERT INTO players (source_url, name, nationality, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (f"https://example.test/nat/{name}/{i}", f"Player {name} {i}", name, now, now),
                )
        conn.commit()
        nats = {n.nationality for n in build_dynamic_nationalities(conn)}
        conn.close()

    assert nats.isdisjoint(NATIONALITY_DENYLIST)


def test_default_prominence_whitelist_excludes_an_obscure_nationality() -> None:
    import tempfile

    from src.db import Database

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "nat.db"
        Database(db_path).initialize()
        conn = sqlite3.connect(db_path)
        now = datetime.now(timezone.utc).isoformat()
        # "Simbabwe" is a real, non-denylisted country (passes COUNTRY_BY_NAME
        # and NATIONALITY_DENYLIST) that clears the viability floor here, but
        # isn't on PROMINENT_NATIONALITIES — exactly the gap the whitelist
        # closes: a real country too obscure as a football nation to be fair.
        for i in range(50):
            conn.execute(
                "INSERT INTO players (source_url, name, nationality, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (f"https://example.test/nat/{i}", f"Player {i}", "Simbabwe", now, now),
            )
        conn.commit()
        nats = {n.nationality for n in build_dynamic_nationalities(conn)}
        conn.close()

    assert "Simbabwe" not in nats
    assert "Simbabwe" not in PROMINENT_NATIONALITIES


def test_nationality_difficulty_comes_from_the_fame_table_not_player_count() -> None:
    import tempfile

    from src.db import Database

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "nat.db"
        Database(db_path).initialize()
        conn = sqlite3.connect(db_path)
        now = datetime.now(timezone.utc).isoformat()
        # "Ägypten" (Egypt) has few players in the real dataset but is
        # instantly recognizable via Mohamed Salah — a rarity-based scheme
        # would call that hard. Fame-tiering it must win regardless of count.
        for i in range(3):  # right at NATIONALITY_MIN_PLAYERS
            conn.execute(
                "INSERT INTO players (source_url, name, nationality, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (f"https://example.test/nat/{i}", f"Player {i}", "Ägypten", now, now),
            )
        conn.commit()
        nats = {n.nationality: n for n in build_dynamic_nationalities(conn)}
        conn.close()

    assert nats["Ägypten"].difficulty == 1


def test_unlisted_nationalities_default_to_the_hardest_tier() -> None:
    assert DEFAULT_NATIONALITY_DIFFICULTY == 3


def test_every_fame_tiered_nationality_is_in_the_prominence_whitelist() -> None:
    # Catches a typo that would otherwise silently demote a famous football
    # nation to the hardest tier instead of erroring.
    assert (NATIONALITY_FAME_TIER_1 | NATIONALITY_FAME_TIER_2) <= PROMINENT_NATIONALITIES


def test_nationality_fame_tiers_do_not_overlap() -> None:
    assert NATIONALITY_FAME_TIER_1.isdisjoint(NATIONALITY_FAME_TIER_2)


def test_nationality_denylist_and_prominence_whitelist_do_not_overlap() -> None:
    assert NATIONALITY_DENYLIST.isdisjoint(PROMINENT_NATIONALITIES)


def test_league_pools_scope_clubs_to_the_leagues_own_club_list(dynamic_db_conn) -> None:
    from src.categories import LeagueCategory

    players = [r[0] for r in dynamic_db_conn.execute("SELECT name FROM players").fetchall()]
    for name in players[:5]:  # clears the difficulty-3 floor of 5 distinct players
        _add_career_stint(dynamic_db_conn, name, "Bayern München")
    dynamic_db_conn.commit()

    league = LeagueCategory("league_test", "Test League", ["Bayern München"], difficulty=1)
    from src.dynamic_categories import DynamicCatalog

    catalog = DynamicCatalog(clubs=_build_clubs(dynamic_db_conn))
    pools = build_league_pools([league], catalog.clubs, catalog)
    pool_club_names = {c.club_name for c in pools["league_test"] if hasattr(c, "club_name")}
    assert pool_club_names == {"Bayern München"}  # Testville FC etc. excluded — not in this league
