from __future__ import annotations

import sqlite3
from enum import Enum
from typing import Optional


class CategoryType(str, Enum):
    CLUB = "club"
    NATIONALITY = "nationality"
    POSITION = "position"
    AWARD = "award"


class Category:
    def __init__(self, id: str, label: str, type: CategoryType, icon: Optional[str] = None) -> None:
        self.id = id
        self.label = label
        self.type = type
        self.icon = icon

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        raise NotImplementedError

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        """Return the set of all player IDs that satisfy this category."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, label={self.label!r})"


class ClubCategory(Category):
    """Player must have a career stint at the given club (exact name match against career_stints.club_name)."""

    def __init__(self, id: str, label: str, club_name: str, icon: Optional[str] = None) -> None:
        super().__init__(id=id, label=label, type=CategoryType.CLUB, icon=icon)
        self.club_name = club_name

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            "SELECT 1 FROM career_stints WHERE player_id = ? AND club_name = ? LIMIT 1",
            (player_id, self.club_name),
        ).fetchone()
        return row is not None

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        rows = conn.execute(
            "SELECT DISTINCT player_id FROM career_stints WHERE club_name = ?",
            (self.club_name,),
        ).fetchall()
        return {row[0] for row in rows}


class NationalityCategory(Category):
    """Player must hold the given nationality.

    Matches using LIKE because the DB stores compound nationalities as
    space-separated strings (e.g. "Deutschland Türkei" for dual nationals).
    """

    def __init__(self, id: str, label: str, nationality: str, icon: Optional[str] = None) -> None:
        super().__init__(id=id, label=label, type=CategoryType.NATIONALITY, icon=icon)
        self.nationality = nationality

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            "SELECT 1 FROM players WHERE id = ? AND nationality LIKE ? LIMIT 1",
            (player_id, f"%{self.nationality}%"),
        ).fetchone()
        return row is not None

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        rows = conn.execute(
            "SELECT id FROM players WHERE nationality LIKE ?",
            (f"%{self.nationality}%",),
        ).fetchall()
        return {row[0] for row in rows}


class PositionCategory(Category):
    """Player must play the given position.

    Matches using a prefix because the DB stores positions as
    "Group - Subposition" (e.g. "Abwehr - Innenverteidiger").
    Pass the full string for an exact sub-position, or just the group
    (e.g. "Abwehr") to match all defenders.
    """

    def __init__(self, id: str, label: str, position_prefix: str, icon: Optional[str] = None) -> None:
        super().__init__(id=id, label=label, type=CategoryType.POSITION, icon=icon)
        self.position_prefix = position_prefix

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            "SELECT 1 FROM players WHERE id = ? AND position LIKE ? LIMIT 1",
            (player_id, f"{self.position_prefix}%"),
        ).fetchone()
        return row is not None

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        rows = conn.execute(
            "SELECT id FROM players WHERE position LIKE ?",
            (f"{self.position_prefix}%",),
        ).fetchall()
        return {row[0] for row in rows}


class AwardCategory(Category):
    """Player must appear in a manually maintained list of award winners.

    Names are matched case-insensitively against players.name. The scraper
    stores active players with a jersey-number prefix (e.g. "#16 Rodri"), so
    the prefix is stripped before comparing.
    Keep the list updated as new winners are announced.
    """

    def __init__(self, id: str, label: str, player_names: list[str], icon: Optional[str] = None) -> None:
        super().__init__(id=id, label=label, type=CategoryType.AWARD, icon=icon)
        self.player_names = player_names
        self._lower_names = {n.lower() for n in player_names}

    @staticmethod
    def _strip_prefix(name: str) -> str:
        """Remove leading jersey-number prefix like '#16 ' from a DB player name."""
        if name.startswith("#") and " " in name:
            return name.split(" ", 1)[1]
        return name

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        row = conn.execute("SELECT name FROM players WHERE id = ?", (player_id,)).fetchone()
        if row is None:
            return False
        return self._strip_prefix(row[0]).lower() in self._lower_names

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        if not self._lower_names:
            return set()
        placeholders = ",".join("?" * len(self._lower_names))
        # Match both names stored with and without the jersey-number prefix.
        rows = conn.execute(
            f"""
            SELECT id FROM players
            WHERE LOWER(
                CASE WHEN name LIKE '#% %' THEN SUBSTR(name, INSTR(name, ' ') + 1)
                     ELSE name
                END
            ) IN ({placeholders})
            """,
            list(self._lower_names),
        ).fetchall()
        return {row[0] for row in rows}
