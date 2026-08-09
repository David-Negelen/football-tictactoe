from __future__ import annotations

import sqlite3
from pathlib import Path

import app as app_module
from src.categories import CategoryType, ClubCategory, NationalityCategory


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
        assert row_ids | col_ids == set(fixture_categories)

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


def test_sample_puzzle_categories_never_exceeds_the_sparse_cap() -> None:
    """Regression test for the "random.sample() from a club/trophy-dominated
    pool picks almost-all-sparse grids, which then almost never has any
    overlapping players" bug found while building the dynamic catalog (see
    app.py's MAX_SPARSE_PER_PUZZLE / _SPARSE_TYPES comments)."""
    sparse = [ClubCategory(f"club_{i}", f"Club {i}", f"Club {i}", difficulty=1) for i in range(20)]
    broad = list(app_module.category_config.AGE_CATEGORIES) + list(app_module.category_config.POSITION_CATEGORIES)

    for _ in range(50):
        rows, cols = app_module._sample_puzzle_categories(sparse, broad)
        sample = rows + cols
        assert len(sample) == 6
        assert len({c.id for c in sample}) == 6  # no duplicates
        n_sparse = sum(1 for c in sample if c.type in app_module._SPARSE_TYPES)
        assert 1 <= n_sparse <= app_module.MAX_SPARSE_PER_PUZZLE
        # No two sparse categories ever land on opposite sides (that would
        # create a sparse-x-sparse cell, the least likely to have any answer).
        row_sparse = sum(1 for c in rows if c.type in app_module._SPARSE_TYPES)
        col_sparse = sum(1 for c in cols if c.type in app_module._SPARSE_TYPES)
        assert row_sparse == 0 or col_sparse == 0


def test_sample_puzzle_categories_returns_none_when_not_enough_categories() -> None:
    assert app_module._sample_puzzle_categories([], []) is None
    assert app_module._sample_puzzle_categories([ClubCategory("a", "A", "A")], []) is None


def test_sample_puzzle_categories_never_splits_nationalities_across_sides() -> None:
    """Regression test: a "German" row crossing a "Belgian" column asks a
    "who holds both nationalities" question, a different (and less
    interesting) kind of cell than the rest of the puzzle — nationality
    categories must always land together on one side, like sparse ones."""
    sparse: list = []
    nationalities = [NationalityCategory(f"nat_{i}", f"Nat {i}", f"Nat {i}") for i in range(10)]
    other_broad = list(app_module.category_config.AGE_CATEGORIES) + list(app_module.category_config.POSITION_CATEGORIES)
    broad = nationalities + other_broad

    for _ in range(50):
        rows, cols = app_module._sample_puzzle_categories(sparse, broad)
        sample = rows + cols
        assert len(sample) == 6
        assert len({c.id for c in sample}) == 6

        n_nat = sum(1 for c in sample if c.type == CategoryType.NATIONALITY)
        assert n_nat <= app_module.MAX_NATIONALITY_PER_PUZZLE
        row_nat = sum(1 for c in rows if c.type == CategoryType.NATIONALITY)
        col_nat = sum(1 for c in cols if c.type == CategoryType.NATIONALITY)
        assert row_nat == 0 or col_nat == 0


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
