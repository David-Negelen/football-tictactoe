from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Union

from .models import CareerStint, ClubRecord, PlayerRecord, TransferRecord


class Database:
    def __init__(self, db_path: Union[str, Path]) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS clubs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_url TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_url TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    age INTEGER,
                    nationality TEXT,
                    position TEXT,
                    market_value TEXT,
                    contract_expires TEXT,
                    current_club_name TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS player_clubs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    club_id INTEGER NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    UNIQUE(player_id, club_id),
                    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE,
                    FOREIGN KEY(club_id) REFERENCES clubs(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    source_url TEXT,
                    season TEXT,
                    from_club TEXT,
                    to_club TEXT,
                    transfer_date TEXT,
                    date_iso TEXT,
                    fee TEXT,
                    market_value TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(player_id, season, from_club, to_club),
                    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS career_stints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    club_name TEXT NOT NULL,
                    start_season TEXT,
                    end_season TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS scrape_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    club_url TEXT NOT NULL,
                    club_name TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    message TEXT
                );

                -- Aggregated player stats for sorting and exploration.
                -- career_start/end are "YY/YY" season strings (lexicographic order works for sorting).
                CREATE VIEW IF NOT EXISTS player_stats AS
                SELECT
                    p.id,
                    p.name,
                    p.nationality,
                    p.position,
                    p.market_value,
                    p.current_club_name,
                    p.age,
                    p.contract_expires,
                    COUNT(DISTINCT cs.club_name)  AS clubs_count,
                    COUNT(DISTINCT t.id)           AS transfer_count,
                    MIN(cs.start_season)           AS career_start,
                    MAX(COALESCE(cs.end_season, cs.start_season)) AS career_end
                FROM players p
                LEFT JOIN career_stints cs ON p.id = cs.player_id
                LEFT JOIN transfers     t  ON p.id = t.player_id
                GROUP BY p.id;
                """
            )

    def upsert_club(self, club: ClubRecord) -> int:
        now = club.scraped_at.astimezone(timezone.utc).isoformat()
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id FROM clubs WHERE source_url = ?",
                (club.source_url,),
            ).fetchone()
            if row is None:
                cursor = connection.execute(
                    "INSERT INTO clubs (source_url, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (club.source_url, club.name, now, now),
                )
                return int(cursor.lastrowid)
            connection.execute(
                "UPDATE clubs SET name = ?, updated_at = ? WHERE id = ?",
                (club.name, now, int(row["id"])),
            )
            return int(row["id"])

    def player_exists(self, source_url: str) -> bool:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id FROM players WHERE source_url = ?", (source_url,)
            ).fetchone()
            return row is not None

    def upsert_player(self, player: PlayerRecord) -> int:
        now = player.scraped_at.astimezone(timezone.utc).isoformat()
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id FROM players WHERE source_url = ?",
                (player.source_url,),
            ).fetchone()
            if row is None:
                cursor = connection.execute(
                    """
                    INSERT INTO players (
                        source_url, name, age, nationality, position, market_value,
                        contract_expires, current_club_name, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        player.source_url, player.name, player.age, player.nationality,
                        player.position, player.market_value, player.contract_expires,
                        player.club_name, now, now,
                    ),
                )
                return int(cursor.lastrowid)
            connection.execute(
                """
                UPDATE players
                SET name = ?, age = ?, nationality = ?, position = ?, market_value = ?,
                    contract_expires = ?, current_club_name = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    player.name, player.age, player.nationality, player.position,
                    player.market_value, player.contract_expires, player.club_name,
                    now, int(row["id"]),
                ),
            )
            return int(row["id"])

    def upsert_player_club(self, player_id: int, club_id: int, seen_at: datetime) -> None:
        timestamp = seen_at.astimezone(timezone.utc).isoformat()
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id FROM player_clubs WHERE player_id = ? AND club_id = ?",
                (player_id, club_id),
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO player_clubs (player_id, club_id, first_seen_at, last_seen_at) VALUES (?, ?, ?, ?)",
                    (player_id, club_id, timestamp, timestamp),
                )
            else:
                connection.execute(
                    "UPDATE player_clubs SET last_seen_at = ? WHERE id = ?",
                    (timestamp, int(row["id"])),
                )

    def replace_transfers(self, player_id: int, transfers: Iterable[TransferRecord], created_at: datetime) -> None:
        timestamp = created_at.astimezone(timezone.utc).isoformat()
        with self.connect() as connection:
            connection.execute("DELETE FROM transfers WHERE player_id = ?", (player_id,))
            for transfer in transfers:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO transfers (
                        player_id, source_url, season, from_club, to_club,
                        transfer_date, date_iso, fee, market_value, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        player_id,
                        transfer.source_url,
                        transfer.season,
                        transfer.from_club,
                        transfer.to_club,
                        transfer.transfer_date,
                        transfer.date_iso,
                        transfer.fee,
                        transfer.market_value,
                        timestamp,
                    ),
                )

    def replace_career_stints(self, player_id: int, stints: Iterable[CareerStint]) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM career_stints WHERE player_id = ?", (player_id,))
            for stint in stints:
                connection.execute(
                    """
                    INSERT INTO career_stints (
                        player_id, club_name, start_season, end_season, start_date, end_date
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (player_id, stint.club_name, stint.start_season, stint.end_season,
                     stint.start_date, stint.end_date),
                )

    def start_scrape_run(self, club_url: str, club_name: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO scrape_runs (club_url, club_name, started_at, status) VALUES (?, ?, ?, ?)",
                (club_url, club_name, now, "running"),
            )
            return int(cursor.lastrowid)

    def finish_scrape_run(self, run_id: int, status: str, message: Optional[str] = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            connection.execute(
                "UPDATE scrape_runs SET finished_at = ?, status = ?, message = ? WHERE id = ?",
                (now, status, message, run_id),
            )
