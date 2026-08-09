from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def _player_id(db_path: Path, name: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT id FROM players WHERE name = ?", (name,)).fetchone()
        assert row is not None, f"fixture player {name!r} not found"
        return row[0]
    finally:
        conn.close()


# ─── /api/game/new ────────────────────────────────────────────────────────────
# Difficulty 3 is used here because the fixture roster's pairwise category
# overlaps are only guaranteed to satisfy the loosest (min_players=1) fallback
# tier used by the real difficulty-3 ladder — see conftest.py.

def test_new_game_returns_three_rows_and_three_cols(app_client) -> None:
    resp = app_client.get("/api/game/new?difficulty=3")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["rows"]) == 3
    assert len(data["cols"]) == 3
    ids = [c["id"] for c in data["rows"] + data["cols"]]
    assert len(set(ids)) == 6  # no category used as both a row and a column


def test_new_game_clamps_out_of_range_difficulty(app_client) -> None:
    resp = app_client.get("/api/game/new?difficulty=99")
    assert resp.status_code == 200


# ─── /api/game/search ─────────────────────────────────────────────────────────

def test_search_requires_three_characters(app_client) -> None:
    resp = app_client.get("/api/game/search?q=al")
    assert resp.status_code == 200
    assert resp.get_json()["players"] == []


def test_search_finds_matching_player(app_client) -> None:
    resp = app_client.get("/api/game/search?q=Adler")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.get_json()["players"]]
    assert "Alan Adler" in names


def test_search_is_accent_and_case_insensitive(app_client) -> None:
    resp = app_client.get("/api/game/search?q=jose nunez")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.get_json()["players"]]
    assert "José Núñez" in names


# ─── /api/game/validate ───────────────────────────────────────────────────────

def test_validate_accepts_matching_player(app_client, fixture_db_path) -> None:
    player_id = _player_id(fixture_db_path, "Alan Adler")  # Testville FC + Testland
    resp = app_client.post(
        "/api/game/validate",
        data=json.dumps({"player_id": player_id, "row_id": "t_club", "col_id": "t_nat"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["valid"] is True


def test_validate_rejects_non_matching_player(app_client, fixture_db_path) -> None:
    player_id = _player_id(fixture_db_path, "Dana Diaz")  # Fixture Town / Fixturia, not Testville/Testland
    resp = app_client.post(
        "/api/game/validate",
        data=json.dumps({"player_id": player_id, "row_id": "t_club", "col_id": "t_nat"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["valid"] is False


def test_validate_rejects_malformed_input(app_client) -> None:
    resp = app_client.post(
        "/api/game/validate",
        data=json.dumps({"row_id": "t_club", "col_id": "t_nat"}),  # missing player_id
        content_type="application/json",
    )
    assert resp.status_code == 400


# ─── /api/game/solve ──────────────────────────────────────────────────────────

def test_solve_returns_grid_matching_eligible_sets(app_client) -> None:
    resp = app_client.get("/api/game/solve?rows=t_club,t_nat,t_pos&cols=t_mv,t_trophy,t_age")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["grid"]) == 3
    assert len(data["grid"][0]) == 3
    # t_club (Testville FC) x t_trophy (Testcup) = Alan, Carl, Gina, Kara.
    assert data["grid"][0][1]["count"] == 4


def test_solve_rejects_wrong_row_col_count(app_client) -> None:
    resp = app_client.get("/api/game/solve?rows=t_club,t_nat&cols=t_mv,t_trophy,t_age")
    assert resp.status_code == 400


# ─── /api/daily/today ──────────────────────────────────────────────────────

def test_daily_today_returns_three_rows_and_three_cols(app_client) -> None:
    resp = app_client.get("/api/daily/today")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "date" in data
    assert len(data["rows"]) == 3
    assert len(data["cols"]) == 3


def test_daily_today_is_identical_across_repeated_requests(app_client) -> None:
    """The whole point of a daily grid is that everyone gets the same
    puzzle — two requests (simulating two different players, or the same
    player reloading) must resolve to the exact same categories."""
    first = app_client.get("/api/daily/today").get_json()
    second = app_client.get("/api/daily/today").get_json()
    assert first["date"] == second["date"]
    assert [c["id"] for c in first["rows"]] == [c["id"] for c in second["rows"]]
    assert [c["id"] for c in first["cols"]] == [c["id"] for c in second["cols"]]


# ─── /api/grids (editor save/share/load by code) ──────────────────────────

def test_create_grid_returns_a_loadable_code(app_client) -> None:
    resp = app_client.post(
        "/api/grids",
        data=json.dumps({"row_ids": ["t_club", "t_nat", "t_pos"], "col_ids": ["t_mv", "t_trophy", "t_age"]}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    code = resp.get_json()["code"]
    assert code

    loaded = app_client.get(f"/api/grids/{code}")
    assert loaded.status_code == 200
    data = loaded.get_json()
    assert {c["id"] for c in data["rows"]} == {"t_club", "t_nat", "t_pos"}
    assert {c["id"] for c in data["cols"]} == {"t_mv", "t_trophy", "t_age"}


def test_create_grid_code_is_case_insensitive_on_lookup(app_client) -> None:
    resp = app_client.post(
        "/api/grids",
        data=json.dumps({"row_ids": ["t_club", "t_nat", "t_pos"], "col_ids": ["t_mv", "t_trophy", "t_age"]}),
        content_type="application/json",
    )
    code = resp.get_json()["code"]
    loaded = app_client.get(f"/api/grids/{code.lower()}")
    assert loaded.status_code == 200


def test_get_grid_rejects_unknown_code(app_client) -> None:
    resp = app_client.get("/api/grids/ZZZZZZ")
    assert resp.status_code == 404


def test_create_grid_rejects_wrong_row_col_count(app_client) -> None:
    resp = app_client.post(
        "/api/grids",
        data=json.dumps({"row_ids": ["t_club", "t_nat"], "col_ids": ["t_mv", "t_trophy", "t_age"]}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_create_grid_rejects_a_category_reused_across_rows_and_cols(app_client) -> None:
    resp = app_client.post(
        "/api/grids",
        data=json.dumps({"row_ids": ["t_club", "t_nat", "t_pos"], "col_ids": ["t_club", "t_trophy", "t_age"]}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_create_grid_rejects_an_unknown_category_id(app_client) -> None:
    resp = app_client.post(
        "/api/grids",
        data=json.dumps({"row_ids": ["t_club", "t_nat", "nonexistent"], "col_ids": ["t_mv", "t_trophy", "t_age"]}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_create_grid_rejects_a_combination_with_an_empty_cell(app_client, fixture_categories) -> None:
    from src.categories import AgeCategory

    # No fixture player is 200 years old — this category is guaranteed to
    # produce a zero-answer cell against every other fixture category.
    # fixture_categories is the same dict object app_module.CATEGORY_BY_ID
    # was monkeypatched to (see conftest.py's app_client fixture), so adding
    # to it here is enough for the route to see it too.
    fixture_categories["impossible"] = AgeCategory("impossible", "Impossible", min_age=200, difficulty=1)

    resp = app_client.post(
        "/api/grids",
        data=json.dumps({"row_ids": ["t_club", "t_nat", "impossible"], "col_ids": ["t_mv", "t_trophy", "t_age"]}),
        content_type="application/json",
    )
    assert resp.status_code == 400
