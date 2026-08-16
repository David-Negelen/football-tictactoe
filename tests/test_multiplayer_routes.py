from __future__ import annotations

import json


def _create_room(app_client, **body) -> dict:
    resp = app_client.post(
        "/api/multiplayer/rooms",
        data=json.dumps(body),
        content_type="application/json",
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)
    return resp.get_json()


# ─── Malformed-input guards ────────────────────────────────────────────────

def test_create_room_rejects_non_numeric_difficulty(app_client) -> None:
    resp = app_client.post(
        "/api/multiplayer/rooms",
        data=json.dumps({"difficulty": "abc"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]


def test_move_rejects_non_numeric_row(app_client) -> None:
    room = _create_room(app_client)
    resp = app_client.post(
        f"/api/multiplayer/rooms/{room['code']}/moves",
        data=json.dumps({"token": room["token"], "row": "x", "col": 0, "player_id": 1}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False
