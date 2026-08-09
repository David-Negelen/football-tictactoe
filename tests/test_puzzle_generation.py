from __future__ import annotations

import random
import sqlite3
from pathlib import Path

import app as app_module
from src.categories import CategoryType, ClubCategory, NationalityCategory, TrophyCategory


def _conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def test_generate_puzzle_succeeds_and_respects_bounds(monkeypatch, fixture_db_path, fixture_categories) -> None:
    monkeypatch.setattr(app_module, "ALL_CATEGORIES", list(fixture_categories.values()))
    conn = _conn(fixture_db_path)
    try:
        rows, cols = app_module._generate_puzzle(
            conn, max_difficulty=3, min_players=1, max_players=9999, max_attempts=5
        )
        assert rows is not None and cols is not None
        assert len(rows) == 3 and len(cols) == 3

        row_ids = {c.id for c in rows}
        col_ids = {c.id for c in cols}
        assert row_ids.isdisjoint(col_ids)
        assert (row_ids | col_ids) <= set(fixture_categories)  # fixture_categories now has more clubs than a single grid needs
        # 3 real clubs (t_club/t_club2/t_club3), confined to one whole side.
        club_ids = {"t_club", "t_club2", "t_club3"}
        assert len(club_ids & (row_ids | col_ids)) == app_module.GENERAL_MIN_CLUBS
        assert club_ids.issuperset(row_ids) or club_ids.issuperset(col_ids)

        for row_cat in rows:
            for col_cat in cols:
                count = len(row_cat.eligible_player_ids(conn) & col_cat.eligible_player_ids(conn))
                assert count >= 1, f"{row_cat.id} x {col_cat.id} has no valid players"
    finally:
        conn.close()


def test_generate_puzzle_returns_none_with_too_few_categories(monkeypatch, fixture_db_path, fixture_categories) -> None:
    small_pool = list(fixture_categories.values())[:4]  # fewer than the required 6
    monkeypatch.setattr(app_module, "ALL_CATEGORIES", small_pool)
    conn = _conn(fixture_db_path)
    try:
        rows, cols = app_module._generate_puzzle(conn, max_difficulty=3, min_players=1, max_attempts=50)
        assert rows is None and cols is None
    finally:
        conn.close()


def test_generate_puzzle_returns_none_when_bounds_unreachable(monkeypatch, fixture_db_path, fixture_categories) -> None:
    monkeypatch.setattr(app_module, "ALL_CATEGORIES", list(fixture_categories.values()))
    conn = _conn(fixture_db_path)
    try:
        rows, cols = app_module._generate_puzzle(conn, max_difficulty=3, min_players=1000, max_attempts=20)
        assert rows is None and cols is None
    finally:
        conn.close()


def test_generate_puzzle_filters_by_difficulty(monkeypatch, fixture_db_path, fixture_categories) -> None:
    hard_only = ClubCategory("t_hard", "Hard-only club", "Nonexistent FC", difficulty=3)
    pool = list(fixture_categories.values()) + [hard_only]
    monkeypatch.setattr(app_module, "ALL_CATEGORIES", pool)
    conn = _conn(fixture_db_path)
    try:
        rows, cols = app_module._generate_puzzle(conn, max_difficulty=1, min_players=1, max_attempts=5)
        assert rows is not None
        assert all(c.id != "t_hard" for c in rows + cols)
    finally:
        conn.close()


def test_generate_puzzle_with_a_seeded_rng_is_deterministic(monkeypatch, fixture_db_path, fixture_categories) -> None:
    """The daily grid (see app.py's /api/daily/today) passes a seeded
    random.Random(...) instead of the global `random` module so that
    everyone gets the same puzzle on a given day — a fresh Random instance
    built from the same seed must reproduce the identical draw every time."""
    monkeypatch.setattr(app_module, "ALL_CATEGORIES", list(fixture_categories.values()))
    conn = _conn(fixture_db_path)
    try:
        first = app_module._generate_puzzle(conn, max_difficulty=3, min_players=1, max_attempts=5, rng=random.Random("same-seed"))
        second = app_module._generate_puzzle(conn, max_difficulty=3, min_players=1, max_attempts=5, rng=random.Random("same-seed"))
        assert [c.id for c in first[0]] == [c.id for c in second[0]]
        assert [c.id for c in first[1]] == [c.id for c in second[1]]
    finally:
        conn.close()


def test_sample_general_puzzle_categories_always_uses_exactly_the_min_clubs(fixture_db_path) -> None:
    """"Alle Ligen" mode must always feature GENERAL_MIN_CLUBS (3) real
    clubs — the bug this replaces let a puzzle land on zero clubs at all
    (e.g. an all-nationality/trophy/letter grid) since clubs used to
    compete with trophies for a single small "sparse" slot. Bounds are
    passed as (0, 9999) — trivially satisfied by anything — to isolate the
    structural behavior under test from the bounds-filtering behavior
    covered separately below."""
    conn = _conn(fixture_db_path)
    try:
        clubs = [ClubCategory(f"club_{i}", f"Club {i}", f"Club {i}", difficulty=1) for i in range(20)]
        broad = list(app_module.category_config.AGE_CATEGORIES) + list(app_module.category_config.POSITION_CATEGORIES)

        for _ in range(50):
            rows, cols = app_module._sample_general_puzzle_categories(clubs, broad, conn, 0, 9999)
            sample = rows + cols
            assert len(sample) == 6
            assert len({c.id for c in sample}) == 6  # no duplicates
            n_clubs = sum(1 for c in sample if c.type == CategoryType.CLUB)
            assert n_clubs == app_module.GENERAL_MIN_CLUBS
            # All clubs confined to one whole side — every cell ends up
            # club x broad, never club x club (see _sample_general_puzzle_
            # categories' docstring for why that pairing is unreliable at
            # the scale of the general, whole-catalog club pool).
            row_clubs = sum(1 for c in rows if c.type == CategoryType.CLUB)
            col_clubs = sum(1 for c in cols if c.type == CategoryType.CLUB)
            assert row_clubs == 0 or col_clubs == 0
    finally:
        conn.close()


def test_sample_general_puzzle_categories_returns_none_when_not_enough_categories(fixture_db_path) -> None:
    conn = _conn(fixture_db_path)
    try:
        assert app_module._sample_general_puzzle_categories([], [], conn, 0, 9999) is None
        few_clubs = [ClubCategory(f"club_{i}", f"Club {i}", f"Club {i}") for i in range(2)]
        broad = list(app_module.category_config.AGE_CATEGORIES)
        assert app_module._sample_general_puzzle_categories(few_clubs, broad, conn, 0, 9999) is None  # below GENERAL_MIN_CLUBS
    finally:
        conn.close()


def test_sample_general_puzzle_categories_broad_side_needs_no_grouping(fixture_db_path) -> None:
    """Unlike the old sampler, two nationality (or two trophy) categories
    landing on the same broad side is completely fine now: since clubs
    occupy the other whole side, neither broad category ever faces another
    broad category in a cell — every cell is club x broad by construction."""
    conn = _conn(fixture_db_path)
    try:
        clubs = [ClubCategory(f"club_{i}", f"Club {i}", f"Club {i}") for i in range(10)]
        nationalities = [NationalityCategory(f"nat_{i}", f"Nat {i}", f"Nat {i}") for i in range(10)]

        saw_two_nationalities_same_side = False
        for _ in range(50):
            rows, cols = app_module._sample_general_puzzle_categories(clubs, nationalities, conn, 0, 9999)
            assert rows is not None
            sample = rows + cols
            assert len(sample) == 6
            assert len({c.id for c in sample}) == 6

            row_nat = sum(1 for c in rows if c.type == CategoryType.NATIONALITY)
            col_nat = sum(1 for c in cols if c.type == CategoryType.NATIONALITY)
            saw_two_nationalities_same_side = saw_two_nationalities_same_side or row_nat >= 2 or col_nat >= 2

        assert saw_two_nationalities_same_side
    finally:
        conn.close()


def test_sample_general_puzzle_categories_excludes_broads_that_dont_overlap_every_chosen_club(fixture_db_path) -> None:
    """Regression test for the actual reliability bug: a broad category
    that doesn't clear bounds against every one of the 3 chosen clubs must
    never be selectable, however many times the sampler runs — this is what
    took general-pool generation from ~0.1-8% single-attempt success (blind
    uniform sampling) to ~100% (see _sample_general_puzzle_categories'
    docstring)."""
    conn = _conn(fixture_db_path)
    try:
        # t_club2/t_club3 (Third FC/Fourth United) are only played for by
        # Alan Adler (Defense) and Carl Cole (Midfield) — neither plays
        # "Attack", so bad_pos (Attack) has zero overlap with those two
        # clubs and must never be selected once all 3 clubs are in play.
        # Nationality/age/a different position all include Alan and so give
        # the filter enough valid options to still succeed once bad_pos is
        # excluded.
        from src.categories import AgeCategory, PositionCategory

        clubs = [
            ClubCategory("t_club", "Testville FC", "Testville FC"),
            ClubCategory("t_club2", "Third FC", "Third FC"),
            ClubCategory("t_club3", "Fourth United", "Fourth United"),
        ]
        bad_pos = PositionCategory("t_bad_pos", "Attack", "Attack")
        broad = [
            NationalityCategory("t_nat", "Testland", "Testland"),
            bad_pos,
            AgeCategory("t_age", "U23", max_age=23),
            PositionCategory("t_pos", "Defense", "Defense"),
        ]

        for _ in range(30):
            rows, cols = app_module._sample_general_puzzle_categories(clubs, broad, conn, 1, 9999)
            assert rows is not None
            sample = rows + cols
            assert bad_pos.id not in {c.id for c in sample}
    finally:
        conn.close()


def test_sample_league_puzzle_categories_never_splits_nationalities_across_sides() -> None:
    league_clubs = [ClubCategory(f"club_{i}", f"Club {i}", f"Club {i}") for i in range(10)]
    nationalities = [NationalityCategory(f"nat_{i}", f"Nat {i}", f"Nat {i}") for i in range(10)]

    for _ in range(50):
        rows, cols = app_module._sample_league_puzzle_categories(league_clubs, nationalities, min_clubs=4)
        assert rows is not None
        sample = rows + cols
        assert len(sample) == 6
        assert len({c.id for c in sample}) == 6

        row_nat = sum(1 for c in rows if c.type == CategoryType.NATIONALITY)
        col_nat = sum(1 for c in cols if c.type == CategoryType.NATIONALITY)
        assert row_nat == 0 or col_nat == 0


def test_sample_league_puzzle_categories_never_splits_trophies_across_sides() -> None:
    """Trophies are allowed in league mode (not just clubs/nationality) —
    same grouping rule applies: two trophy categories must never end up on
    opposite sides of the grid, and they do need to actually show up (a
    regression here could silently re-exclude AWARD entirely)."""
    league_clubs = [ClubCategory(f"club_{i}", f"Club {i}", f"Club {i}") for i in range(10)]
    trophies = [TrophyCategory(f"trophy_{i}", f"Trophy {i}", f"Trophy {i}") for i in range(10)]

    saw_award = False
    for _ in range(50):
        rows, cols = app_module._sample_league_puzzle_categories(league_clubs, trophies, min_clubs=4)
        assert rows is not None
        sample = rows + cols
        assert len(sample) == 6
        assert len({c.id for c in sample}) == 6

        row_award = sum(1 for c in rows if c.type == CategoryType.AWARD)
        col_award = sum(1 for c in cols if c.type == CategoryType.AWARD)
        assert row_award == 0 or col_award == 0
        saw_award = saw_award or (row_award + col_award) > 0

    assert saw_award
