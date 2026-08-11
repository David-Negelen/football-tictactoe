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

# How long a player can go without any request (SSE tick, state poll, or
# move) before the opponent's own SSE loop treats them as gone and
# auto-forfeits in the opponent's favor. Generous relative to the ~1s SSE
# tick so a brief network blip or an EventSource auto-reconnect doesn't
# falsely end the game — see Room.check_opponent_disconnected.
DISCONNECT_TIMEOUT_SECONDS = 20

# How long a public "waiting for opponent" room stays listed in the
# browsable lobby without any activity from its host. Slightly above
# DISCONNECT_TIMEOUT_SECONDS for the same reason: a closed host tab (no more
# SSE ticks -> no more mark_seen calls) shouldn't clutter public matchmaking
# for up to the full ROOM_TTL_SECONDS room lifetime — see list_public_rooms.
PUBLIC_LOBBY_STALE_SECONDS = 30

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
    last_seen: dict = field(default_factory=dict)  # slot (1|2) -> monotonic time of last request
    rematch_requested: set = field(default_factory=set)  # slots that have asked for a rematch this round
    # Most recent wrong guess this round — the opponent otherwise has no way
    # to tell a wrong guess apart from "their turn just ended" (both just
    # flip `current`). `version` here is the room-wide version at the moment
    # of the guess, letting a client tell a genuinely new wrong guess apart
    # from the same one still sitting in a state it's already shown.
    last_wrong_guess: Optional[dict] = None  # {slot, name, row, col, version} | None
    # Why the round ended, when it wasn't a normal 3-in-a-row/draw — lets the
    # remaining player be told "opponent gave up"/"opponent disconnected"
    # instead of a bare "Du gewinnst!" that reads like they were outplayed.
    end_reason: Optional[str] = None  # None | "forfeit" | "disconnect"
    lock: threading.Lock = field(default_factory=threading.Lock)
    # Remembered from room creation (the creator's settings govern the whole
    # room — see api_mp_create_room) so a rematch can generate a fresh
    # puzzle with the same difficulty/league/exclusions without the client
    # having to resend them (the joiner never had them to begin with).
    difficulty: int = 3
    league: Optional[str] = None
    excluded_types: frozenset = field(default_factory=frozenset)
    excluded_ids: frozenset = field(default_factory=frozenset)
    # "private": joinable only by whoever has the code/link (the original,
    # and still default, behavior). "public": additionally listed in the
    # browsable lobby (see list_public_rooms) for anyone to join.
    visibility: str = "private"

    def touch(self) -> None:
        self.last_activity = time.monotonic()

    def is_stale(self) -> bool:
        return time.monotonic() - self.last_activity > ROOM_TTL_SECONDS

    def mark_seen(self, slot: Optional[int]) -> None:
        if slot is not None:
            self.last_seen[slot] = time.monotonic()

    def check_opponent_disconnected(self, slot: int) -> bool:
        """Called periodically by `slot`'s own SSE loop — i.e. driven by
        whichever player still has an open connection, since a player who
        has actually left obviously can't report their own absence. If the
        *other* seated player hasn't made any request (SSE tick, state poll,
        move) in DISCONNECT_TIMEOUT_SECONDS, auto-forfeits them in this
        player's favor. This is what makes "opponent closed the tab /
        lost network / force-quit the app" actually resolve the game
        instead of leaving the remaining player waiting forever — the
        client can't be trusted to always fire a cooperative forfeit
        request on its way out (see game.js's pagehide handler for the
        cooperative half of this fix). Returns True if a forfeit was just
        applied.
        """
        with self.lock:
            if self.winner is not None:
                return False
            other = 2 if slot == 1 else 1
            if other not in self.tokens.values():
                return False  # opponent hasn't even joined yet — nothing to detect
            last = self.last_seen.get(other)
            if last is None or time.monotonic() - last <= DISCONNECT_TIMEOUT_SECONDS:
                return False
            self.winner = slot
            self.win_cells = []
            self.end_reason = "disconnect"
            self.version += 1
            self.touch()
            return True

    def request_rematch(self, slot: int) -> bool:
        """Either seated player can ask for a rematch, but the round only
        actually resets once *both* have asked — see reset_room, called by
        the caller once this returns True. Returns whether both slots have
        now requested one.
        """
        with self.lock:
            if self.winner is None:
                return False
            self.rematch_requested.add(slot)
            self.version += 1
            self.touch()
            return {1, 2} <= self.rematch_requested

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
            "rematchRequested": sorted(self.rematch_requested),
            "lastWrongGuess": self.last_wrong_guess,
            "endReason": self.end_reason,
        }

    def public_lobby_summary(self) -> dict:
        """Just enough for the browsable public-lobby list to render a row
        and let someone join it — no board/category state, unlike
        public_state (that's only handed out once a player is actually
        seated in the room)."""
        return {"code": self.code, "difficulty": self.difficulty, "league": self.league}


_rooms: dict[str, Room] = {}
_rooms_lock = threading.Lock()


def _new_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


def _sweep_stale_locked() -> None:
    stale = [code for code, room in _rooms.items() if room.is_stale()]
    for code in stale:
        _rooms.pop(code, None)


def create_room(
    rows: list,
    cols: list,
    difficulty: int = 3,
    league: Optional[str] = None,
    excluded_types: frozenset = frozenset(),
    excluded_ids: frozenset = frozenset(),
    visibility: str = "private",
) -> tuple[Room, str]:
    """Create a room and seat the creator as slot 1. Returns (room, creator_token)."""
    with _rooms_lock:
        _sweep_stale_locked()
        code = _new_code()
        while code in _rooms:
            code = _new_code()
        room = Room(
            code=code, rows=rows, cols=cols, difficulty=difficulty, league=league,
            excluded_types=excluded_types, excluded_ids=excluded_ids,
            visibility="public" if visibility == "public" else "private",
        )
        token = secrets.token_urlsafe(16)
        room.tokens[token] = 1
        _rooms[code] = room
        return room, token


def reset_room(room: Room, rows: list, cols: list) -> None:
    """Starts a fresh round with a newly generated puzzle in the same room —
    same code, same two seated players/tokens — instead of making both
    players leave and one create a brand new room and re-share the link."""
    with room.lock:
        room.rows = rows
        room.cols = cols
        room.board = [[None, None, None] for _ in range(3)]
        room.current = 1
        room.winner = None
        room.win_cells = []
        room.used_ids = set()
        room.rematch_requested = set()
        room.last_wrong_guess = None
        room.end_reason = None
        room.version += 1
        room.touch()


def get_room(code: str) -> Optional[Room]:
    return _rooms.get((code or "").upper())


def list_public_rooms() -> list[Room]:
    """Public rooms currently open to join — waiting for a second player,
    and with a host who's still actually around. Newest first, since a
    just-created room is the one most likely to still need an opponent."""
    now = time.monotonic()
    with _rooms_lock:
        _sweep_stale_locked()
        rooms = [
            room for room in _rooms.values()
            if room.visibility == "public"
            and len(room.tokens) == 1
            and now - room.last_seen.get(1, room.created_at) <= PUBLIC_LOBBY_STALE_SECONDS
        ]
    rooms.sort(key=lambda room: room.created_at, reverse=True)
    return rooms


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
        room.mark_seen(slot)
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
            # The opponent otherwise has no way to tell "wrong guess, my
            # turn now" apart from a normal turn handoff — see the
            # last_wrong_guess field doc on Room. Best-effort name lookup:
            # an unknown player_id still advances the turn either way, it
            # just falls back to a blank name in that (shouldn't-happen) case.
            wrong_row = db.execute("SELECT name FROM players WHERE id = ?", (player_id,)).fetchone()
            room.last_wrong_guess = {
                "slot": slot,
                "name": wrong_row["name"] if wrong_row else "",
                "row": row, "col": col,
                "version": room.version,
            }
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
        room.end_reason = "forfeit"
        room.version += 1
        room.touch()
        return True
