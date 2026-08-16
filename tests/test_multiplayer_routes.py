from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src import multiplayer as mp


def _create_room(app_client, **body) -> dict:
    resp = app_client.post(
        "/api/multiplayer/rooms",
        data=json.dumps(body),
        content_type="application/json",
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)
    return resp.get_json()


def _direct_room(fixture_categories):
    """Bypasses the HTTP creation endpoint to get a room with known,
    deterministic categories (same six used by tests/test_multiplayer.py's
    _room() helper) — /api/multiplayer/rooms itself generates a random
    puzzle from the pool, which the move/win-condition tests below need to
    know in advance to pick a player that actually satisfies a given cell."""
    cats = list(fixture_categories.values())[:6]
    return mp.create_room(rows=cats[:3], cols=cats[3:])


def _player_id(db_path: Path, name: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT id FROM players WHERE name = ?", (name,)).fetchone()[0]
    finally:
        conn.close()


# ─── POST /api/multiplayer/rooms ────────────────────────────────────────────

def test_create_room_returns_code_token_and_slot(app_client) -> None:
    room = _create_room(app_client)
    assert len(room["code"]) == 5
    assert room["token"]
    assert room["slot"] == 1
    assert room["visibility"] == "private"


def test_create_room_honors_public_visibility(app_client) -> None:
    room = _create_room(app_client, visibility="public")
    assert room["visibility"] == "public"


def test_create_room_rejects_non_numeric_difficulty(app_client) -> None:
    resp = app_client.post(
        "/api/multiplayer/rooms",
        data=json.dumps({"difficulty": "abc"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]


# ─── POST /api/multiplayer/rooms/<code>/join ────────────────────────────────

def test_join_room_seats_second_player(app_client) -> None:
    room = _create_room(app_client)
    resp = app_client.post(f"/api/multiplayer/rooms/{room['code']}/join")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == room["code"]
    assert data["slot"] == 2
    assert data["token"] != room["token"]


def test_join_room_rejects_unknown_code(app_client) -> None:
    resp = app_client.post("/api/multiplayer/rooms/ZZZZZ/join")
    assert resp.status_code == 404
    assert resp.get_json()["error"]


def test_join_room_rejects_when_already_full(app_client) -> None:
    room = _create_room(app_client)
    first = app_client.post(f"/api/multiplayer/rooms/{room['code']}/join")
    assert first.status_code == 200
    second = app_client.post(f"/api/multiplayer/rooms/{room['code']}/join")
    assert second.status_code == 409
    assert second.get_json()["error"]


# ─── GET /api/multiplayer/lobbies ───────────────────────────────────────────

def test_lobbies_lists_public_rooms(app_client) -> None:
    room = _create_room(app_client, visibility="public")
    resp = app_client.get("/api/multiplayer/lobbies")
    assert resp.status_code == 200
    codes = {r["code"] for r in resp.get_json()["rooms"]}
    assert room["code"] in codes


def test_lobbies_excludes_private_rooms(app_client) -> None:
    room = _create_room(app_client, visibility="private")
    resp = app_client.get("/api/multiplayer/lobbies")
    assert resp.status_code == 200
    codes = {r["code"] for r in resp.get_json()["rooms"]}
    assert room["code"] not in codes


# ─── GET /api/multiplayer/lobbies/events (SSE) ──────────────────────────────
# No request body/params to malform — this stream takes no input at all, so
# there's only a happy path to cover. The body itself is an infinite
# generator (see api_mp_lobbies_events), so this only checks the immediate
# response (status/headers), never reads the stream — Flask's test client
# doesn't start iterating the generator until something reads .data, so this
# stays instant instead of blocking on the route's internal time.sleep loop.

def test_lobbies_events_stream_opens_with_correct_headers(app_client) -> None:
    resp = app_client.get("/api/multiplayer/lobbies/events")
    try:
        assert resp.status_code == 200
        assert resp.mimetype == "text/event-stream"
        assert resp.headers.get("Cache-Control") == "no-cache"
    finally:
        resp.close()


# ─── GET /api/multiplayer/rooms/<code>/state ────────────────────────────────

def test_room_state_reflects_the_room(app_client, fixture_categories) -> None:
    room, token = _direct_room(fixture_categories)
    resp = app_client.get(f"/api/multiplayer/rooms/{room.code}/state?token={token}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == room.code
    assert data["yourSlot"] == 1
    assert len(data["rows"]) == 3
    assert len(data["cols"]) == 3


def test_room_state_rejects_unknown_code(app_client) -> None:
    resp = app_client.get("/api/multiplayer/rooms/ZZZZZ/state")
    assert resp.status_code == 404
    assert resp.get_json()["error"]


# ─── GET /api/multiplayer/rooms/<code>/events (SSE) ─────────────────────────

def test_room_events_stream_opens_for_a_known_room(app_client, fixture_categories) -> None:
    room, token = _direct_room(fixture_categories)
    resp = app_client.get(f"/api/multiplayer/rooms/{room.code}/events?token={token}")
    try:
        assert resp.status_code == 200
        assert resp.mimetype == "text/event-stream"
    finally:
        resp.close()


def test_room_events_rejects_unknown_code(app_client) -> None:
    resp = app_client.get("/api/multiplayer/rooms/ZZZZZ/events")
    assert resp.status_code == 404
    assert resp.get_json()["error"]


# ─── POST /api/multiplayer/rooms/<code>/moves ───────────────────────────────

def test_move_places_correct_answer(app_client, fixture_db_path, fixture_categories) -> None:
    room, creator_token = _direct_room(fixture_categories)
    # rows/cols = [t_club, t_nat, t_pos] x [t_mv, t_trophy, t_age] (insertion order,
    # same as tests/test_multiplayer.py's _room()). Alan Adler satisfies
    # t_club (Testville FC) and t_trophy (Testcup) — row 0, col 1.
    pid = _player_id(fixture_db_path, "Alan Adler")
    resp = app_client.post(
        f"/api/multiplayer/rooms/{room.code}/moves",
        data=json.dumps({"token": creator_token, "row": 0, "col": 1, "player_id": pid}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["placed"]["name"] == "Alan Adler"


def test_move_rejects_unknown_room_code(app_client) -> None:
    resp = app_client.post(
        "/api/multiplayer/rooms/ZZZZZ/moves",
        data=json.dumps({"token": "x", "row": 0, "col": 0, "player_id": 1}),
        content_type="application/json",
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"]


def test_move_rejects_missing_fields(app_client) -> None:
    room = _create_room(app_client)
    resp = app_client.post(
        f"/api/multiplayer/rooms/{room['code']}/moves",
        data=json.dumps({"token": room["token"], "row": 0}),  # col, player_id missing
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_move_rejects_non_numeric_row(app_client) -> None:
    room = _create_room(app_client)
    resp = app_client.post(
        f"/api/multiplayer/rooms/{room['code']}/moves",
        data=json.dumps({"token": room["token"], "row": "x", "col": 0, "player_id": 1}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


# ─── POST /api/multiplayer/rooms/<code>/forfeit ─────────────────────────────

def test_forfeit_gives_the_other_slot_the_win(app_client) -> None:
    room = _create_room(app_client)
    app_client.post(f"/api/multiplayer/rooms/{room['code']}/join")
    resp = app_client.post(
        f"/api/multiplayer/rooms/{room['code']}/forfeit",
        data=json.dumps({"token": room["token"]}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True

    state = app_client.get(f"/api/multiplayer/rooms/{room['code']}/state").get_json()
    assert state["winner"] == 2


def test_forfeit_rejects_unknown_room_code(app_client) -> None:
    resp = app_client.post(
        "/api/multiplayer/rooms/ZZZZZ/forfeit",
        data=json.dumps({"token": "x"}),
        content_type="application/json",
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"]


def test_forfeit_with_unknown_token_is_a_no_op(app_client) -> None:
    room = _create_room(app_client)
    resp = app_client.post(
        f"/api/multiplayer/rooms/{room['code']}/forfeit",
        data=json.dumps({"token": "not-a-real-token"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is False


# ─── POST /api/multiplayer/rooms/<code>/rematch ─────────────────────────────

def test_rematch_starts_once_both_slots_agree(app_client, fixture_categories) -> None:
    room, creator_token = _direct_room(fixture_categories)
    _room2, joiner_token = mp.join_room(room.code)
    room.winner = 1  # round must be over before a rematch can be requested

    first = app_client.post(
        f"/api/multiplayer/rooms/{room.code}/rematch",
        data=json.dumps({"token": creator_token}),
        content_type="application/json",
    )
    assert first.status_code == 200
    assert first.get_json() == {"ok": True, "started": False}

    second = app_client.post(
        f"/api/multiplayer/rooms/{room.code}/rematch",
        data=json.dumps({"token": joiner_token}),
        content_type="application/json",
    )
    assert second.status_code == 200
    assert second.get_json() == {"ok": True, "started": True}

    state = app_client.get(f"/api/multiplayer/rooms/{room.code}/state").get_json()
    assert state["winner"] is None  # fresh round


def test_rematch_rejects_unknown_room_code(app_client) -> None:
    resp = app_client.post(
        "/api/multiplayer/rooms/ZZZZZ/rematch",
        data=json.dumps({"token": "x"}),
        content_type="application/json",
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"]


def test_rematch_rejects_a_token_not_in_the_room(app_client) -> None:
    room = _create_room(app_client)
    resp = app_client.post(
        f"/api/multiplayer/rooms/{room['code']}/rematch",
        data=json.dumps({"token": "not-a-real-token"}),
        content_type="application/json",
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]


def test_rematch_rejects_while_the_round_is_still_running(app_client) -> None:
    room = _create_room(app_client)
    resp = app_client.post(
        f"/api/multiplayer/rooms/{room['code']}/rematch",
        data=json.dumps({"token": room["token"]}),
        content_type="application/json",
    )
    assert resp.status_code == 409


# ─── GET /api/game/solve?code=... (online) ──────────────────────────────────
# A ?code=/&token= pair routes /api/game/solve through the room's own
# server-side state instead of trusting client-supplied row/col IDs — the
# one mode with a real opponent this could unfairly advantage (see
# api_game_solve's docstring).

def test_solve_with_code_rejects_unknown_room(app_client) -> None:
    resp = app_client.get("/api/game/solve?code=ZZZZZ&token=x")
    assert resp.status_code == 404
    assert resp.get_json()["error"]


def test_solve_with_code_rejects_a_token_not_in_the_room(app_client, fixture_categories) -> None:
    room, _token = _direct_room(fixture_categories)
    resp = app_client.get(f"/api/game/solve?code={room.code}&token=not-a-real-token")
    assert resp.status_code == 403
    assert resp.get_json()["error"]


def test_solve_with_code_rejects_while_the_round_is_still_running(app_client, fixture_categories) -> None:
    room, token = _direct_room(fixture_categories)
    resp = app_client.get(f"/api/game/solve?code={room.code}&token={token}")
    assert resp.status_code == 409


def test_solve_with_code_returns_the_room_grid_once_the_round_ends(app_client, fixture_categories) -> None:
    room, token = _direct_room(fixture_categories)
    room.winner = 1
    resp = app_client.get(f"/api/game/solve?code={room.code}&token={token}")
    assert resp.status_code == 200
    data = resp.get_json()
    # Same categories/order as _direct_room: [t_club, t_nat, t_pos] x
    # [t_mv, t_trophy, t_age] — t_club (Testville FC) x t_trophy (Testcup)
    # = Alan, Carl, Gina, Kara, matching test_solve_returns_grid_matching_
    # eligible_sets in test_game_routes.py.
    assert data["grid"][0][1]["count"] == 4


def test_solve_with_code_ignores_client_supplied_row_col_ids(app_client, fixture_categories) -> None:
    """A malicious client can't override which categories get solved by also
    passing ?rows=/&cols= alongside a valid code/token — the room's own
    categories always win once code is present."""
    room, token = _direct_room(fixture_categories)
    room.winner = 1
    resp = app_client.get(
        f"/api/game/solve?code={room.code}&token={token}&rows=t_nat,t_pos,t_club&cols=t_age,t_mv,t_trophy"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["grid"][0][1]["count"] == 4
