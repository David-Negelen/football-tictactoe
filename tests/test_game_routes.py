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
