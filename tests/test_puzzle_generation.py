from __future__ import annotations

import sqlite3
from pathlib import Path

import app as app_module
from src.categories import ClubCategory


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
