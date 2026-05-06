from __future__ import annotations

import sqlite3
from enum import Enum
from typing import Optional


class CategoryType(str, Enum):
    CLUB = "club"
    NATIONALITY = "nationality"
    POSITION = "position"
    AWARD = "award"
    LEAGUE = "league"
    CONTINENT = "continent"
    INITIAL = "initial"
    CONTAINS_LETTER = "contains_letter"
    AGE = "age"
    MARKET_VALUE = "market_value"


class Category:
    def __init__(self, id: str, label: str, type: CategoryType, icon: Optional[str] = None, difficulty: int = 1) -> None:
        self.id = id
        self.label = label
        self.type = type
        self.icon = icon
        self.difficulty = difficulty

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        raise NotImplementedError

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        """Return the set of all player IDs that satisfy this category."""
        raise NotImplementedError

    def sql_filter(self) -> tuple[str, list]:
        """Return (sql_condition, params) referencing alias `p` for the players table."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, label={self.label!r})"


class ClubCategory(Category):
    """Player must have a career stint at the given club (exact name match against career_stints.club_name)."""

    def __init__(self, id: str, label: str, club_name: str, icon: Optional[str] = None, difficulty: int = 1) -> None:
        super().__init__(id=id, label=label, type=CategoryType.CLUB, icon=icon, difficulty=difficulty)
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

    def sql_filter(self) -> tuple[str, list]:
        return "EXISTS (SELECT 1 FROM career_stints cs WHERE cs.player_id = p.id AND cs.club_name = ?)", [self.club_name]


class NationalityCategory(Category):
    """Player must hold the given nationality.

    Matches using LIKE because the DB stores compound nationalities as
    space-separated strings (e.g. "Deutschland Türkei" for dual nationals).
    """

    def __init__(self, id: str, label: str, nationality: str, icon: Optional[str] = None, difficulty: int = 1) -> None:
        super().__init__(id=id, label=label, type=CategoryType.NATIONALITY, icon=icon, difficulty=difficulty)
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

    def sql_filter(self) -> tuple[str, list]:
        return "p.nationality LIKE ?", [f"%{self.nationality}%"]


class PositionCategory(Category):
    """Player must play the given position.

    Matches using a prefix because the DB stores positions as
    "Group - Subposition" (e.g. "Abwehr - Innenverteidiger").
    Pass the full string for an exact sub-position, or just the group
    (e.g. "Abwehr") to match all defenders.
    """

    def __init__(self, id: str, label: str, position_prefix: str, icon: Optional[str] = None, difficulty: int = 1) -> None:
        super().__init__(id=id, label=label, type=CategoryType.POSITION, icon=icon, difficulty=difficulty)
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

    def sql_filter(self) -> tuple[str, list]:
        return "p.position LIKE ?", [f"{self.position_prefix}%"]


class AwardCategory(Category):
    """Player must appear in a manually maintained list of award winners.

    Names are matched case-insensitively against players.name. The scraper
    stores active players with a jersey-number prefix (e.g. "#16 Rodri"), so
    the prefix is stripped before comparing.
    Keep the list updated as new winners are announced.
    """

    def __init__(self, id: str, label: str, player_names: list[str], icon: Optional[str] = None, difficulty: int = 1) -> None:
        super().__init__(id=id, label=label, type=CategoryType.AWARD, icon=icon, difficulty=difficulty)
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

    def sql_filter(self) -> tuple[str, list]:
        placeholders = ",".join("?" * len(self._lower_names))
        sql = (
            f"LOWER(CASE WHEN p.name LIKE '#% %' THEN SUBSTR(p.name, INSTR(p.name, ' ') + 1)"
            f" ELSE p.name END) IN ({placeholders})"
        )
        return sql, list(self._lower_names)


class TrophyCategory(Category):
    """Player must have won a specific trophy title at least once."""

    def __init__(self, id: str, label: str, trophy_title: str, icon: Optional[str] = None, difficulty: int = 1) -> None:
        super().__init__(id=id, label=label, type=CategoryType.AWARD, icon=icon, difficulty=difficulty)
        self.trophy_title = trophy_title

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            "SELECT 1 FROM player_trophies WHERE player_id = ? AND title = ? LIMIT 1",
            (player_id, self.trophy_title),
        ).fetchone()
        return row is not None

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        rows = conn.execute(
            "SELECT DISTINCT player_id FROM player_trophies WHERE title = ?",
            (self.trophy_title,),
        ).fetchall()
        return {row[0] for row in rows}

    def sql_filter(self) -> tuple[str, list]:
        return (
            "EXISTS (SELECT 1 FROM player_trophies pt WHERE pt.player_id = p.id AND pt.title = ?)",
            [self.trophy_title],
        )


class LeagueCategory(Category):
    """Player must have a career stint at any first-team club in the league."""

    def __init__(self, id: str, label: str, club_names: list[str], icon: Optional[str] = None, difficulty: int = 1) -> None:
        super().__init__(id=id, label=label, type=CategoryType.LEAGUE, icon=icon, difficulty=difficulty)
        self.club_names = club_names

    def _ph(self) -> str:
        return ",".join("?" * len(self.club_names))

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            f"SELECT 1 FROM career_stints WHERE player_id = ? AND club_name IN ({self._ph()}) LIMIT 1",
            [player_id] + self.club_names,
        ).fetchone()
        return row is not None

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        rows = conn.execute(
            f"SELECT DISTINCT player_id FROM career_stints WHERE club_name IN ({self._ph()})",
            self.club_names,
        ).fetchall()
        return {row[0] for row in rows}

    def sql_filter(self) -> tuple[str, list]:
        return (
            f"EXISTS (SELECT 1 FROM career_stints cs WHERE cs.player_id = p.id AND cs.club_name IN ({self._ph()}))",
            list(self.club_names),
        )


class ContinentCategory(Category):
    """Player must have a career stint at any club on the given continent."""

    def __init__(self, id: str, label: str, club_names: list[str], icon: Optional[str] = None, difficulty: int = 1) -> None:
        super().__init__(id=id, label=label, type=CategoryType.CONTINENT, icon=icon, difficulty=difficulty)
        self.club_names = club_names

    def _ph(self) -> str:
        return ",".join("?" * len(self.club_names))

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            f"SELECT 1 FROM career_stints WHERE player_id = ? AND club_name IN ({self._ph()}) LIMIT 1",
            [player_id] + self.club_names,
        ).fetchone()
        return row is not None

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        rows = conn.execute(
            f"SELECT DISTINCT player_id FROM career_stints WHERE club_name IN ({self._ph()})",
            self.club_names,
        ).fetchall()
        return {row[0] for row in rows}

    def sql_filter(self) -> tuple[str, list]:
        return (
            f"EXISTS (SELECT 1 FROM career_stints cs WHERE cs.player_id = p.id AND cs.club_name IN ({self._ph()}))",
            list(self.club_names),
        )


# SQL expression to strip the "#<number> " jersey prefix and return the bare name.
_STRIPPED_NAME = (
    "CASE WHEN p.name LIKE '#% %' THEN SUBSTR(p.name, INSTR(p.name, ' ') + 1) ELSE p.name END"
)

# SQL expression that returns the last word of the stripped name (handles 1–3 word names).
_sn = f"({_STRIPPED_NAME})"
_LAST_WORD_EXPR = (
    f"CASE "
    f"WHEN {_sn} NOT LIKE '% %' THEN {_sn} "
    f"WHEN SUBSTR({_sn}, INSTR({_sn}, ' ') + 1) NOT LIKE '% %' "
    f"  THEN SUBSTR({_sn}, INSTR({_sn}, ' ') + 1) "
    f"ELSE SUBSTR("
    f"  SUBSTR({_sn}, INSTR({_sn}, ' ') + 1), "
    f"  INSTR(SUBSTR({_sn}, INSTR({_sn}, ' ') + 1), ' ') + 1) "
    f"END"
)

# SQL expression to convert players.market_value ("€5.00m" / "€500k") to a numeric float in euros.
_MV_EXPR = (
    "CASE "
    "WHEN p.market_value LIKE '%m' THEN CAST(REPLACE(REPLACE(p.market_value, '€', ''), 'm', '') AS REAL) * 1000000 "
    "WHEN p.market_value LIKE '%k' THEN CAST(REPLACE(REPLACE(p.market_value, '€', ''), 'k', '') AS REAL) * 1000 "
    "ELSE NULL END"
)


class InitialCategory(Category):
    """Player whose first name OR last name starts with the given letter."""

    def __init__(self, id: str, label: str, letter: str, icon: Optional[str] = None, difficulty: int = 2) -> None:
        super().__init__(id=id, label=label, type=CategoryType.INITIAL, icon=icon, difficulty=difficulty)
        self.letter = letter.upper()

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            f"SELECT {_STRIPPED_NAME} FROM players p WHERE p.id = ?",
            (player_id,),
        ).fetchone()
        if row is None:
            return False
        words = row[0].split()
        if not words:
            return False
        return words[0][0].upper() == self.letter or words[-1][0].upper() == self.letter

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        rows = conn.execute(
            f"SELECT p.id FROM players p "
            f"WHERE UPPER(SUBSTR({_STRIPPED_NAME}, 1, 1)) = ? "
            f"OR UPPER(SUBSTR(({_LAST_WORD_EXPR}), 1, 1)) = ?",
            (self.letter, self.letter),
        ).fetchall()
        return {row[0] for row in rows}

    def sql_filter(self) -> tuple[str, list]:
        return (
            f"(UPPER(SUBSTR({_STRIPPED_NAME}, 1, 1)) = ? "
            f"OR UPPER(SUBSTR(({_LAST_WORD_EXPR}), 1, 1)) = ?)",
            [self.letter, self.letter],
        )


class ContainsLetterCategory(Category):
    """Player whose name contains the given letter anywhere (case-insensitive)."""

    def __init__(self, id: str, label: str, letter: str, icon: Optional[str] = None, difficulty: int = 3) -> None:
        super().__init__(id=id, label=label, type=CategoryType.CONTAINS_LETTER, icon=icon, difficulty=difficulty)
        self.letter = letter.upper()

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            f"SELECT {_STRIPPED_NAME} FROM players p WHERE p.id = ?",
            (player_id,),
        ).fetchone()
        return row is not None and self.letter in row[0].upper()

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        rows = conn.execute(
            f"SELECT p.id FROM players p WHERE UPPER({_STRIPPED_NAME}) LIKE ?",
            (f"%{self.letter}%",),
        ).fetchall()
        return {row[0] for row in rows}

    def sql_filter(self) -> tuple[str, list]:
        return f"UPPER({_STRIPPED_NAME}) LIKE ?", [f"%{self.letter}%"]


class AgeCategory(Category):
    """Player whose age falls in [min_age, max_age] (inclusive, in years)."""

    def __init__(self, id: str, label: str, min_age: Optional[int] = None, max_age: Optional[int] = None,
                 icon: Optional[str] = None, difficulty: int = 2) -> None:
        super().__init__(id=id, label=label, type=CategoryType.AGE, icon=icon, difficulty=difficulty)
        self.min_age = min_age
        self.max_age = max_age

    def _conditions(self) -> tuple[str, list]:
        parts = ["p.age IS NOT NULL"]
        params: list = []
        if self.min_age is not None:
            parts.append("p.age >= ?")
            params.append(self.min_age)
        if self.max_age is not None:
            parts.append("p.age <= ?")
            params.append(self.max_age)
        return " AND ".join(parts), params

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        cond, params = self._conditions()
        row = conn.execute(
            f"SELECT 1 FROM players p WHERE p.id = ? AND {cond} LIMIT 1",
            [player_id] + params,
        ).fetchone()
        return row is not None

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        cond, params = self._conditions()
        rows = conn.execute(f"SELECT p.id FROM players p WHERE {cond}", params).fetchall()
        return {row[0] for row in rows}

    def sql_filter(self) -> tuple[str, list]:
        cond, params = self._conditions()
        return f"({cond})", params


class MarketValueCategory(Category):
    """Player whose current market value falls in [min_value, max_value] (inclusive, in euros).

    Requires players.market_value to be populated in the format "€5.00m" / "€500k".
    """

    def __init__(self, id: str, label: str, min_value: Optional[float] = None, max_value: Optional[float] = None,
                 icon: Optional[str] = None, difficulty: int = 2) -> None:
        super().__init__(id=id, label=label, type=CategoryType.MARKET_VALUE, icon=icon, difficulty=difficulty)
        self.min_value = min_value
        self.max_value = max_value

    def _conditions(self) -> tuple[str, list]:
        parts = [f"({_MV_EXPR}) IS NOT NULL"]
        params: list = []
        if self.min_value is not None:
            parts.append(f"({_MV_EXPR}) >= ?")
            params.append(self.min_value)
        if self.max_value is not None:
            parts.append(f"({_MV_EXPR}) <= ?")
            params.append(self.max_value)
        return " AND ".join(parts), params

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        cond, params = self._conditions()
        row = conn.execute(
            f"SELECT 1 FROM players p WHERE p.id = ? AND {cond} LIMIT 1",
            [player_id] + params,
        ).fetchone()
        return row is not None

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        cond, params = self._conditions()
        rows = conn.execute(f"SELECT p.id FROM players p WHERE {cond}", params).fetchall()
        return {row[0] for row in rows}

    def sql_filter(self) -> tuple[str, list]:
        cond, params = self._conditions()
        return f"({cond})", params


# European nationality strings (German) used to exclude EU/European nationals.
# Includes UEFA member associations plus geographically European states.
_EUROPEAN_NATIONALITIES: list[str] = [
    "Deutschland", "England", "Frankreich", "Spanien", "Italien",
    "Portugal", "Niederlande", "Belgien", "Schweiz", "Österreich",
    "Dänemark", "Schweden", "Norwegen", "Finnland", "Polen",
    "Tschechien", "Slowakei", "Ungarn", "Rumänien", "Bulgarien",
    "Kroatien", "Serbien", "Slowenien", "Bosnien-Herzegowina",
    "Nordmazedonien", "Montenegro", "Kosovo", "Albanien", "Griechenland",
    "Türkei", "Ukraine", "Russland", "Weißrussland", "Litauen",
    "Lettland", "Estland", "Island", "Irland", "Schottland",
    "Wales", "Nordirland", "Luxemburg", "Malta", "Zypern",
    "Liechtenstein", "Andorra", "San Marino", "Georgien",
    "Aserbaidschan", "Armenien",
]


class NonEuropeanNationalityCategory(Category):
    """Player holds no European nationality (no UEFA/European national string appears in their nationality field)."""

    def __init__(self, id: str, label: str, icon: Optional[str] = None, difficulty: int = 2) -> None:
        super().__init__(id=id, label=label, type=CategoryType.NATIONALITY, icon=icon, difficulty=difficulty)

    @staticmethod
    def _condition() -> tuple[str, list]:
        parts = ["p.nationality IS NOT NULL"]
        params: list = []
        for nat in _EUROPEAN_NATIONALITIES:
            parts.append("p.nationality NOT LIKE ?")
            params.append(f"%{nat}%")
        return " AND ".join(parts), params

    def check_player(self, player_id: int, conn: sqlite3.Connection) -> bool:
        cond, params = self._condition()
        row = conn.execute(
            f"SELECT 1 FROM players p WHERE p.id = ? AND {cond} LIMIT 1",
            [player_id] + params,
        ).fetchone()
        return row is not None

    def eligible_player_ids(self, conn: sqlite3.Connection) -> set[int]:
        cond, params = self._condition()
        rows = conn.execute(f"SELECT p.id FROM players p WHERE {cond}", params).fetchall()
        return {row[0] for row in rows}

    def sql_filter(self) -> tuple[str, list]:
        return self._condition()
