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
    build_dynamic_teammates,
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


def _add_career_stint(
    conn: sqlite3.Connection, player_name: str, club_name: str,
    start_season: str | None = "20/21", end_season: str | None = None,
) -> None:
    row = conn.execute("SELECT id FROM players WHERE name = ?", (player_name,)).fetchone()
    player_id = row[0]
    conn.execute(
        "INSERT INTO career_stints (player_id, club_name, start_season, end_season, start_date, end_date) "
        "VALUES (?, ?, ?, ?, NULL, NULL)",
        (player_id, club_name, start_season, end_season),
    )


def _grant_trophies(conn: sqlite3.Connection, player_name: str, titles: list[str]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    row = conn.execute("SELECT id FROM players WHERE name = ?", (player_name,)).fetchone()
    player_id = row[0]
    for title in titles:
        conn.execute(
            "INSERT INTO player_trophies (player_id, title, trophy_count, source_url, created_at) VALUES (?, ?, 1, NULL, ?)",
            (player_id, title, datetime.now(timezone.utc).isoformat()),
        )


# A small, self-contained trophy/club vocabulary for teammate tests — kept
# separate from the real PROMINENT_TROPHY_TITLES/PROMINENT_CLUB_NAMES
# whitelists (same reasoning as FIXTURE_PROMINENT_CLUB_NAMES above) so
# these tests are about the overlap/fame mechanism, not any one real
# trophy or club's current whitelist membership.
TEAMMATE_TEST_TROPHY_TITLES = frozenset({"Test Trophy A", "Test Trophy B", "Test Trophy C"})
TEAMMATE_TEST_CLUB = "Teammate Test FC"


def _build_teammates(conn, **kwargs):
    kwargs.setdefault("prominent_trophy_titles", TEAMMATE_TEST_TROPHY_TITLES)
    kwargs.setdefault("overlap_club_names", frozenset({TEAMMATE_TEST_CLUB}))
    kwargs.setdefault("min_anchor_trophies", 3)
    kwargs.setdefault("min_players", 1)
    return build_dynamic_teammates(conn, **kwargs)


def _player_id(conn, name: str) -> int:
    return conn.execute("SELECT id FROM players WHERE name = ?", (name,)).fetchone()[0]


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
    # A sanity floor, not a target — CLUB_FAME_TIER_1 is hand-tuned and free
    # to be rebalanced; this just catches a league ending up with too few
    # (or zero) tier-1 clubs to be playable at all in the league-only "easy"
    # difficulty filter.
    from src.category_config import LEAGUE_CATEGORIES

    for league in LEAGUE_CATEGORIES:
        tier_1_count = len(set(league.club_names) & CLUB_FAME_TIER_1)
        assert tier_1_count >= 3, f"{league.id} only has {tier_1_count} tier-1 clubs"


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
    # No per-category icon precomputed — app.py's _cat_display resolves a
    # real flag image (or a shared fallback icon) off `nationality` at
    # render time instead.
    assert nats["Deutschland"].icon is None
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
        trophies = {t.label: t for t in build_dynamic_trophies(conn)}
    finally:
        conn.close()

    assert "Weltmeister" in trophies
    assert trophies["Weltmeister"].id == LEGACY_TROPHY_IDS["Weltmeister"] == "trophy_world_cup"
    assert "Torschützenkönig" not in trophies  # individual award, filtered out


def test_aliased_trophy_titles_merge_into_one_category(fixture_db_path: Path) -> None:
    # "Europapokal-der-Landesmeister-Sieger" is the pre-1992 name for the
    # same competition as "UEFA Champions League-Sieger" — a player who won
    # it under the old name must still count for the (single) merged
    # category, not fall through the cracks or produce a second category.
    conn = sqlite3.connect(fixture_db_path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        old_winner = conn.execute("SELECT id FROM players WHERE name = 'Alan Adler'").fetchone()[0]
        new_winner = conn.execute("SELECT id FROM players WHERE name = 'Carl Cole'").fetchone()[0]
        conn.execute(
            "INSERT INTO player_trophies (player_id, title, trophy_count, source_url, created_at) VALUES (?, ?, 1, NULL, ?)",
            (old_winner, "Europapokal-der-Landesmeister-Sieger", now),
        )
        conn.execute(
            "INSERT INTO player_trophies (player_id, title, trophy_count, source_url, created_at) VALUES (?, ?, 1, NULL, ?)",
            (new_winner, "UEFA Champions League-Sieger", now),
        )
        conn.commit()
        trophies = {t.label: t for t in build_dynamic_trophies(conn)}
    finally:
        conn.close()

    assert "Europapokal-der-Landesmeister-Sieger" not in trophies  # folded into the canonical entry
    cl = trophies["UEFA Champions League-Sieger"]
    assert cl.check_player(old_winner, sqlite3.connect(fixture_db_path))
    assert cl.check_player(new_winner, sqlite3.connect(fixture_db_path))


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
        trophies = {t.label for t in build_dynamic_trophies(conn)}
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
            t.label: t
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
        # "Ägypten" (Egypt) stands in for any country with few players in the
        # real dataset but instant recognizability (e.g. via a single star
        # player) — a rarity-based scheme would call that hard. Fame-tiering
        # it must win regardless of count. Explicit overrides (rather than
        # relying on Ägypten's real tier, which is free to move as the real
        # whitelist gets retuned) keep this test about the mechanism, not
        # about any one country's current placement.
        for i in range(3):  # right at NATIONALITY_MIN_PLAYERS
            conn.execute(
                "INSERT INTO players (source_url, name, nationality, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (f"https://example.test/nat/{i}", f"Player {i}", "Ägypten", now, now),
            )
        conn.commit()
        nats = {
            n.nationality: n
            for n in build_dynamic_nationalities(
                conn, prominent_names=frozenset({"Ägypten"}), nationality_difficulty={"Ägypten": 1}
            )
        }
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


def test_build_dynamic_teammates_requires_min_prominent_trophies(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        _grant_trophies(conn, "Alan Adler", ["Test Trophy A", "Test Trophy B"])  # only 2 -> not an anchor
        _grant_trophies(conn, "Carl Cole", ["Test Trophy A", "Test Trophy B", "Test Trophy C"])  # 3 -> anchor
        _add_career_stint(conn, "Alan Adler", TEAMMATE_TEST_CLUB)
        _add_career_stint(conn, "Bella Bauer", TEAMMATE_TEST_CLUB)
        _add_career_stint(conn, "Carl Cole", TEAMMATE_TEST_CLUB)
        _add_career_stint(conn, "Dana Diaz", TEAMMATE_TEST_CLUB)
        conn.commit()
        anchors = {t.anchor_player_id for t in _build_teammates(conn)}
        alan_id, carl_id = _player_id(conn, "Alan Adler"), _player_id(conn, "Carl Cole")
    finally:
        conn.close()
    assert alan_id not in anchors
    assert carl_id in anchors


def test_build_dynamic_teammates_requires_season_overlap(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        _grant_trophies(conn, "Alan Adler", list(TEAMMATE_TEST_TROPHY_TITLES))
        _add_career_stint(conn, "Alan Adler", TEAMMATE_TEST_CLUB, start_season="96/97", end_season="98/99")
        _add_career_stint(conn, "Bella Bauer", TEAMMATE_TEST_CLUB, start_season="10/11", end_season="12/13")  # no overlap
        _add_career_stint(conn, "Carl Cole", TEAMMATE_TEST_CLUB, start_season="97/98", end_season="99/00")  # overlaps
        conn.commit()
        cats = {t.anchor_player_id: t for t in _build_teammates(conn)}
        alan_id = _player_id(conn, "Alan Adler")
        bella_id, carl_id = _player_id(conn, "Bella Bauer"), _player_id(conn, "Carl Cole")
        cat = cats[alan_id]
        assert not cat.check_player(bella_id, conn)
        assert cat.check_player(carl_id, conn)
    finally:
        conn.close()


def test_build_dynamic_teammates_treats_null_end_season_as_ongoing(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        _grant_trophies(conn, "Alan Adler", list(TEAMMATE_TEST_TROPHY_TITLES))
        _add_career_stint(conn, "Alan Adler", TEAMMATE_TEST_CLUB, start_season="20/21", end_season=None)  # ongoing
        _add_career_stint(conn, "Bella Bauer", TEAMMATE_TEST_CLUB, start_season="22/23", end_season="23/24")
        conn.commit()
        cats = {t.anchor_player_id: t for t in _build_teammates(conn)}
        alan_id = _player_id(conn, "Alan Adler")
        bella_id = _player_id(conn, "Bella Bauer")
        assert cats[alan_id].check_player(bella_id, conn)
    finally:
        conn.close()


def test_build_dynamic_teammates_treats_null_start_season_as_unbounded_early(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        _grant_trophies(conn, "Alan Adler", list(TEAMMATE_TEST_TROPHY_TITLES))
        _add_career_stint(conn, "Alan Adler", TEAMMATE_TEST_CLUB, start_season=None, end_season="05/06")  # earliest known stint
        _add_career_stint(conn, "Bella Bauer", TEAMMATE_TEST_CLUB, start_season="04/05", end_season="06/07")
        conn.commit()
        cats = {t.anchor_player_id: t for t in _build_teammates(conn)}
        alan_id = _player_id(conn, "Alan Adler")
        bella_id = _player_id(conn, "Bella Bauer")
        assert cats[alan_id].check_player(bella_id, conn)
    finally:
        conn.close()


def test_build_dynamic_teammates_ignores_non_whitelisted_clubs(fixture_db_path: Path) -> None:
    # "Karriereende" is Transfermarkt's status placeholder, not a real club
    # (27k+ real rows carry it) — two players sharing it in the same season
    # must NOT register as having "played together", even though they do
    # share a club_name with overlapping seasons. The default
    # overlap_club_names (only TEAMMATE_TEST_CLUB) already excludes it —
    # this is exactly the mechanism that has to hold for the real
    # PROMINENT_CLUB_NAMES whitelist to be a correctness guard, not just a
    # fame nicety.
    conn = sqlite3.connect(fixture_db_path)
    try:
        _grant_trophies(conn, "Alan Adler", list(TEAMMATE_TEST_TROPHY_TITLES))
        _add_career_stint(conn, "Alan Adler", "Karriereende", start_season="20/21", end_season=None)
        _add_career_stint(conn, "Bella Bauer", "Karriereende", start_season="20/21", end_season=None)
        conn.commit()
        teammates = _build_teammates(conn)
    finally:
        conn.close()
    assert teammates == []  # Alan's only shared club isn't whitelisted -> no pool -> below the floor


def test_build_dynamic_teammates_below_min_players_floor_is_dropped(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        _grant_trophies(conn, "Alan Adler", list(TEAMMATE_TEST_TROPHY_TITLES))
        _add_career_stint(conn, "Alan Adler", TEAMMATE_TEST_CLUB)
        _add_career_stint(conn, "Bella Bauer", TEAMMATE_TEST_CLUB)  # exactly 1 overlapping teammate
        conn.commit()
        at_floor = _build_teammates(conn, min_players=1)
        above_floor = _build_teammates(conn, min_players=2)
    finally:
        conn.close()
    assert len(at_floor) == 1
    assert len(above_floor) == 0


def test_teammate_difficulty_comes_from_prominent_trophy_count(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        titles = ["Test Trophy A", "Test Trophy B", "Test Trophy C", "Test Trophy D", "Test Trophy E", "Test Trophy F"]
        _grant_trophies(conn, "Alan Adler", titles)          # 6 -> tier 1
        _grant_trophies(conn, "Carl Cole", titles[:4])        # 4 -> tier 2
        _grant_trophies(conn, "Bella Bauer", titles[:3])      # 3 -> tier 3 (floor)
        for name in ("Alan Adler", "Carl Cole", "Bella Bauer", "Dana Diaz"):
            _add_career_stint(conn, name, TEAMMATE_TEST_CLUB)
        conn.commit()
        cats = {
            t.anchor_player_id: t
            for t in build_dynamic_teammates(
                conn, prominent_trophy_titles=frozenset(titles),
                overlap_club_names=frozenset({TEAMMATE_TEST_CLUB}),
                min_anchor_trophies=3, min_players=1,
            )
        }
        alan_id, carl_id, bella_id = (
            _player_id(conn, "Alan Adler"), _player_id(conn, "Carl Cole"), _player_id(conn, "Bella Bauer")
        )
    finally:
        conn.close()
    assert cats[alan_id].difficulty == 1
    assert cats[carl_id].difficulty == 2
    assert cats[bella_id].difficulty == 3


def test_teammate_category_label_and_id(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        _grant_trophies(conn, "Alan Adler", list(TEAMMATE_TEST_TROPHY_TITLES))
        _add_career_stint(conn, "Alan Adler", TEAMMATE_TEST_CLUB)
        _add_career_stint(conn, "Bella Bauer", TEAMMATE_TEST_CLUB)
        conn.commit()
        cats = _build_teammates(conn)
    finally:
        conn.close()
    assert len(cats) == 1
    assert cats[0].label == "Mit Alan Adler gespielt"
    assert cats[0].id.startswith("teammate_dyn_")


def test_building_teammates_twice_produces_identical_ids(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    try:
        _grant_trophies(conn, "Alan Adler", list(TEAMMATE_TEST_TROPHY_TITLES))
        _add_career_stint(conn, "Alan Adler", TEAMMATE_TEST_CLUB)
        _add_career_stint(conn, "Bella Bauer", TEAMMATE_TEST_CLUB)
        conn.commit()
        first = {t.anchor_player_id: t.id for t in _build_teammates(conn)}
        second = {t.anchor_player_id: t.id for t in _build_teammates(conn)}
    finally:
        conn.close()
    assert first == second


def test_teammate_categories_agree_across_check_eligible_and_sql(dynamic_db_conn) -> None:
    """Mirrors test_category_consistency.py's check_player/eligible_player_ids/
    sql_filter agreement invariant, but for the new dynamic teammate
    categories — dynamic categories (clubs/nationalities/trophies too)
    aren't covered by that generic test, which only iterates
    category_config.ALL_CATEGORIES. Seasons below are deliberately staggered
    and include NULL start/end so the overlap SQL's open-interval and
    century-pivot branches all get exercised, not just the fixture's default
    always-overlapping stint."""
    all_player_ids = {row[0] for row in dynamic_db_conn.execute("SELECT id FROM players")}
    players = [r[0] for r in dynamic_db_conn.execute("SELECT name FROM players").fetchall()]
    titles = list(TEAMMATE_TEST_TROPHY_TITLES)
    _grant_trophies(dynamic_db_conn, players[0], titles)
    _grant_trophies(dynamic_db_conn, players[1], titles)
    seasons = [
        ("96/97", "98/99"), ("97/98", None), (None, "01/02"),
        ("10/11", "12/13"), ("20/21", None), ("05/06", "07/08"),
        ("99/00", "00/01"), ("30/31", "32/33"),
    ]
    for name, (start, end) in zip(players, seasons):
        _add_career_stint(dynamic_db_conn, name, TEAMMATE_TEST_CLUB, start_season=start, end_season=end)
    dynamic_db_conn.commit()

    teammates = build_dynamic_teammates(
        dynamic_db_conn,
        prominent_trophy_titles=frozenset(titles),
        overlap_club_names=frozenset({TEAMMATE_TEST_CLUB}),
        min_anchor_trophies=3,
        min_players=1,
    )
    assert teammates, "fixture setup must produce at least one teammate category"

    for cat in teammates:
        eligible = cat.eligible_player_ids(dynamic_db_conn)
        checked = {pid for pid in all_player_ids if cat.check_player(pid, dynamic_db_conn)}
        assert eligible == checked, (
            f"{cat.id}: eligible_player_ids() disagrees with check_player() "
            f"(eligible-only: {eligible - checked}, checked-only: {checked - eligible})"
        )

        sql, params = cat.sql_filter()
        rows = dynamic_db_conn.execute(f"SELECT p.id FROM players p WHERE {sql}", params).fetchall()
        from_sql = {row[0] for row in rows}
        assert eligible == from_sql, (
            f"{cat.id}: eligible_player_ids() disagrees with sql_filter() "
            f"(eligible-only: {eligible - from_sql}, sql-only: {from_sql - eligible})"
        )
