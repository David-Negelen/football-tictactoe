from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from src import multiplayer as mp


def _conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _room(fixture_categories):
    cats = list(fixture_categories.values())
    room, creator_token = mp.create_room(rows=cats[:3], cols=cats[3:])
    return room, creator_token


def _player_id(db_path: Path, name: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT id FROM players WHERE name = ?", (name,)).fetchone()[0]
    finally:
        conn.close()


def test_create_room_seats_creator_as_slot_1(fixture_categories) -> None:
    room, token = _room(fixture_categories)
    assert room.tokens[token] == 1
    assert len(room.code) == 5
    assert mp.get_room(room.code) is room


def test_join_room_seats_second_player_and_bumps_version(fixture_categories) -> None:
    room, _creator_token = _room(fixture_categories)
    version_before = room.version

    result = mp.join_room(room.code)
    assert result is not None
    joined_room, joiner_token = result
    assert joined_room is room
    assert room.tokens[joiner_token] == 2
    assert room.version == version_before + 1


def test_join_room_rejects_when_full(fixture_categories) -> None:
    room, _creator_token = _room(fixture_categories)
    first = mp.join_room(room.code)
    assert first is not None
    second = mp.join_room(room.code)
    assert second is None  # already full


def test_join_room_rejects_unknown_code() -> None:
    assert mp.join_room("ZZZZZ") is None
    assert mp.get_room("ZZZZZ") is None


def test_apply_move_places_correct_answer_and_advances_turn(fixture_db_path, fixture_categories) -> None:
    room, creator_token = _room(fixture_categories)
    _room2, joiner_token = mp.join_room(room.code)
    conn = _conn(fixture_db_path)
    try:
        # rows/cols = [t_club, t_nat, t_pos] x [t_mv, t_trophy, t_age] (insertion order).
        # Alan Adler satisfies t_club (Testville FC) and t_trophy (Testcup) — row 0, col 1.
        pid = _player_id(fixture_db_path, "Alan Adler")
        ok, reason, placed = mp.apply_move(room, creator_token, 0, 1, pid, conn)
        assert ok is True
        assert reason == "ok"
        assert placed["player"] == 1
        assert placed["name"] == "Alan Adler"
        assert room.board[0][1]["id"] == pid
        assert room.current == 2  # turn passed to slot 2
        assert pid in room.used_ids
    finally:
        conn.close()


def test_apply_move_rejects_wrong_player_but_still_advances_turn(fixture_db_path, fixture_categories) -> None:
    room, creator_token = _room(fixture_categories)
    mp.join_room(room.code)
    conn = _conn(fixture_db_path)
    try:
        # Dana Diaz doesn't satisfy t_club (Testville FC) — row 0.
        pid = _player_id(fixture_db_path, "Dana Diaz")
        ok, reason, placed = mp.apply_move(room, creator_token, 0, 0, pid, conn)
        assert ok is False
        assert reason == "invalid_player"
        assert placed is None
        assert room.board[0][0] is None  # cell stays empty
        assert room.current == 2  # turn still passes, matching hot-seat rules
        assert pid in room.used_ids  # can't be retried by either player
    finally:
        conn.close()


def test_apply_move_rejects_out_of_turn(fixture_db_path, fixture_categories) -> None:
    room, creator_token = _room(fixture_categories)
    _room2, joiner_token = mp.join_room(room.code)
    conn = _conn(fixture_db_path)
    try:
        pid = _player_id(fixture_db_path, "Alan Adler")
        ok, reason, _placed = mp.apply_move(room, joiner_token, 0, 0, pid, conn)  # slot 2 moving on slot 1's turn
        assert ok is False
        assert reason == "not_your_turn"
    finally:
        conn.close()


def test_apply_move_rejects_taken_cell_and_reused_player(fixture_db_path, fixture_categories) -> None:
    room, creator_token = _room(fixture_categories)
    _room2, joiner_token = mp.join_room(room.code)
    conn = _conn(fixture_db_path)
    try:
        # row 0 = t_club (Testville FC), col 1 = t_trophy (Testcup) — Alan satisfies both.
        pid = _player_id(fixture_db_path, "Alan Adler")
        assert mp.apply_move(room, creator_token, 0, 1, pid, conn)[0] is True

        # Same cell again (now slot 2's turn) should be rejected regardless of the player.
        other_pid = _player_id(fixture_db_path, "Kara Klein")
        ok, reason, _ = mp.apply_move(room, joiner_token, 0, 1, other_pid, conn)
        assert ok is False and reason == "cell_taken"

        # Reusing the already-placed player at a different cell should be rejected
        # (still slot 2's turn: the rejected attempt above had no side effects).
        ok2, reason2, _ = mp.apply_move(room, joiner_token, 0, 2, pid, conn)
        assert ok2 is False and reason2 == "player_used"
    finally:
        conn.close()


def test_apply_move_detects_win(fixture_db_path, fixture_categories) -> None:
    """rows = [t_club, t_nat, t_pos], cols = [t_mv, t_trophy, t_age] (insertion
    order of fixture_categories). Slot 1 completes row 0 (t_club = Testville FC)
    across cols 0-2 using three distinct Testville players; slot 2 plays two
    unrelated, valid cells in row 1 in between so turns stay legal throughout."""
    room, creator_token = _room(fixture_categories)
    _room2, joiner_token = mp.join_room(room.code)
    conn = _conn(fixture_db_path)
    try:
        carl = _player_id(fixture_db_path, "Carl Cole")       # t_club x t_mv
        gina = _player_id(fixture_db_path, "#7 Gina Gomez")   # t_club x t_trophy
        alan = _player_id(fixture_db_path, "Alan Adler")      # t_club x t_age
        farid = _player_id(fixture_db_path, "Farid Fischer")  # t_nat x t_mv (slot 2, row 1)
        kara = _player_id(fixture_db_path, "Kara Klein")      # t_nat x t_trophy (slot 2, row 1)

        assert mp.apply_move(room, creator_token, 0, 0, carl, conn)[0] is True   # slot 1, turn -> 2
        assert mp.apply_move(room, joiner_token, 1, 0, farid, conn)[0] is True   # slot 2, turn -> 1
        assert mp.apply_move(room, creator_token, 0, 1, gina, conn)[0] is True   # slot 1, turn -> 2
        assert room.winner is None

        assert mp.apply_move(room, joiner_token, 1, 1, kara, conn)[0] is True    # slot 2, turn -> 1

        ok, reason, placed = mp.apply_move(room, creator_token, 0, 2, alan, conn)  # slot 1 completes row 0
        assert ok is True and reason == "ok"
        assert placed["player"] == 1
        assert room.winner == 1
        assert room.win_cells == [[0, 0], [0, 1], [0, 2]]

        # The game is over — further moves must be rejected outright.
        someone_else = _player_id(fixture_db_path, "Ines Ibarra")
        ok2, reason2, _ = mp.apply_move(room, joiner_token, 2, 2, someone_else, conn)
        assert ok2 is False and reason2 == "game_over"
    finally:
        conn.close()


def test_forfeit_gives_the_other_slot_the_win(fixture_categories) -> None:
    room, creator_token = _room(fixture_categories)
    mp.join_room(room.code)
    assert mp.forfeit(room, creator_token) is True
    assert room.winner == 2
    assert room.win_cells == []

    # Forfeiting again after the game is already over should be a no-op.
    assert mp.forfeit(room, creator_token) is False


def test_public_state_shape(fixture_categories) -> None:
    room, token = _room(fixture_categories)
    state = room.public_state(viewer_slot=1, cat_display_fn=lambda c: {"id": c.id, "label": c.label, "icon": "⚽"})
    assert state["code"] == room.code
    assert len(state["rows"]) == 3 and len(state["cols"]) == 3
    assert state["yourSlot"] == 1
    assert state["playersConnected"] == 1
    assert state["winner"] is None


def test_check_opponent_disconnected_is_false_before_the_timeout(fixture_categories) -> None:
    room, creator_token = _room(fixture_categories)
    _room2, joiner_token = mp.join_room(room.code)
    room.mark_seen(2)  # slot 2 just made a request
    assert room.check_opponent_disconnected(1) is False
    assert room.winner is None


def test_check_opponent_disconnected_forfeits_after_the_timeout(fixture_categories) -> None:
    room, creator_token = _room(fixture_categories)
    _room2, joiner_token = mp.join_room(room.code)
    # Slot 2 was last seen well beyond the disconnect timeout.
    room.last_seen[2] = time.monotonic() - (mp.DISCONNECT_TIMEOUT_SECONDS + 5)
    assert room.check_opponent_disconnected(1) is True
    assert room.winner == 1
    assert room.win_cells == []

    # Idempotent: calling again after the game is already decided is a no-op.
    assert room.check_opponent_disconnected(1) is False


def test_check_opponent_disconnected_is_false_when_opponent_never_joined(fixture_categories) -> None:
    room, creator_token = _room(fixture_categories)
    # Only slot 1 has ever joined — nothing to detect for slot 2.
    assert room.check_opponent_disconnected(1) is False


def test_check_opponent_disconnected_is_false_with_no_last_seen_record_yet(fixture_categories) -> None:
    room, creator_token = _room(fixture_categories)
    mp.join_room(room.code)
    # Slot 2 joined but mark_seen(2) hasn't been called yet (e.g. their very
    # first SSE connection hasn't ticked once) — must not be misread as a
    # disconnect.
    assert room.check_opponent_disconnected(1) is False
