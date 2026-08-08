from __future__ import annotations

import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

# Unambiguous alphabet (no 0/O/1/I) for room codes read aloud or typed by hand.
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 5
ROOM_TTL_SECONDS = 2 * 60 * 60  # rooms idle this long are swept on the next create/join

WIN_LINES = [
    [(0, 0), (0, 1), (0, 2)], [(1, 0), (1, 1), (1, 2)], [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)], [(0, 1), (1, 1), (2, 1)], [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)], [(0, 2), (1, 1), (2, 0)],
]


def _check_winner(board):
    for line in WIN_LINES:
        vals = [board[r][c]["player"] if board[r][c] else None for r, c in line]
        if vals[0] and vals[0] == vals[1] == vals[2]:
            return vals[0], [list(cell) for cell in line]
    if all(board[r][c] is not None for r in range(3) for c in range(3)):
        return "draw", []
    return None, []


@dataclass
class Room:
    code: str
    rows: list
    cols: list
    board: list = field(default_factory=lambda: [[None, None, None] for _ in range(3)])
    tokens: dict = field(default_factory=dict)  # token -> slot (1 or 2)
    current: int = 1
    winner: object = None  # None | 1 | 2 | "draw"
    win_cells: list = field(default_factory=list)
    used_ids: set = field(default_factory=set)
    version: int = 0
    created_at: float = field(default_factory=time.monotonic)
    last_activity: float = field(default_factory=time.monotonic)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def touch(self) -> None:
        self.last_activity = time.monotonic()

    def is_stale(self) -> bool:
        return time.monotonic() - self.last_activity > ROOM_TTL_SECONDS

    def public_state(self, viewer_slot: Optional[int] = None, cat_display_fn: Optional[Callable] = None) -> dict:
        disp = cat_display_fn or (lambda c: {"id": c.id, "label": c.label})
        return {
            "code": self.code,
            "rows": [disp(c) for c in self.rows],
            "cols": [disp(c) for c in self.cols],
            "board": self.board,
            "current": self.current,
            "winner": self.winner,
            "winCells": self.win_cells,
            "usedIds": list(self.used_ids),
            "version": self.version,
            "playersConnected": len(self.tokens),
            "yourSlot": viewer_slot,
        }


_rooms: dict[str, Room] = {}
_rooms_lock = threading.Lock()


def _new_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


def _sweep_stale_locked() -> None:
    stale = [code for code, room in _rooms.items() if room.is_stale()]
    for code in stale:
        _rooms.pop(code, None)


def create_room(rows: list, cols: list) -> tuple[Room, str]:
    """Create a room and seat the creator as slot 1. Returns (room, creator_token)."""
    with _rooms_lock:
        _sweep_stale_locked()
        code = _new_code()
        while code in _rooms:
            code = _new_code()
        room = Room(code=code, rows=rows, cols=cols)
        token = secrets.token_urlsafe(16)
        room.tokens[token] = 1
        _rooms[code] = room
        return room, token


def get_room(code: str) -> Optional[Room]:
    return _rooms.get((code or "").upper())


def join_room(code: str) -> Optional[tuple[Room, str]]:
    """Seat a second player as slot 2. Returns None if the room doesn't exist or is full."""
    room = get_room(code)
    if room is None:
        return None
    with room.lock:
        if len(room.tokens) >= 2:
            return None
        token = secrets.token_urlsafe(16)
        room.tokens[token] = 2
        room.version += 1
        room.touch()
        return room, token


def room_slot_for_token(room: Room, token: str) -> Optional[int]:
    return room.tokens.get(token or "")


def apply_move(
    room: Room, token: str, row: int, col: int, player_id: int, db: sqlite3.Connection
) -> tuple[bool, str, Optional[dict]]:
    """Attempt to place player_id at (row, col) on behalf of whichever slot owns token.

    A wrong guess (player doesn't satisfy both categories) still advances the
    turn and marks the player as used — identical rules to hot-seat mode,
    just enforced server-side since two untrusted clients are involved.
    Returns (success, reason, placed_cell_or_None).
    """
    with room.lock:
        slot = room.tokens.get(token or "")
        if slot is None:
            return False, "not_in_room", None
        if room.winner is not None:
            return False, "game_over", None
        if slot != room.current:
            return False, "not_your_turn", None
        if not (0 <= row <= 2 and 0 <= col <= 2):
            return False, "bad_cell", None
        if room.board[row][col] is not None:
            return False, "cell_taken", None
        if player_id in room.used_ids:
            return False, "player_used", None

        room.used_ids.add(player_id)

        row_cat, col_cat = room.rows[row], room.cols[col]
        if not (row_cat.check_player(player_id, db) and col_cat.check_player(player_id, db)):
            room.current = 2 if slot == 1 else 1
            room.version += 1
            room.touch()
            return False, "invalid_player", None

        player_row = db.execute(
            "SELECT id, name, current_club_name FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        if player_row is None:
            return False, "unknown_player", None

        placed = {
            "player": slot,
            "id": player_id,
            "name": player_row["name"],
            "club": player_row["current_club_name"],
        }
        room.board[row][col] = placed
        winner, win_cells = _check_winner(room.board)
        room.winner = winner
        room.win_cells = win_cells
        if winner is None:
            room.current = 2 if slot == 1 else 1
        room.version += 1
        room.touch()
        return True, "ok", placed


def forfeit(room: Room, token: str) -> bool:
    with room.lock:
        slot = room.tokens.get(token or "")
        if slot is None or room.winner is not None:
            return False
        room.winner = 2 if slot == 1 else 1
        room.win_cells = []
        room.version += 1
        room.touch()
        return True
