from __future__ import annotations

import sqlite3
from pathlib import Path

from src.category_config import ALL_CATEGORIES


def test_every_category_agrees_across_check_eligible_and_sql(fixture_db_path: Path) -> None:
    """check_player(), eligible_player_ids() and sql_filter() must always agree
    on the same set of players for every configured category. Puzzle generation
    relies on eligible_player_ids(); answer validation relies on check_player();
    the solve/reveal view relies on sql_filter(). If a future change to any one
    of the three desyncs it from the others, generation and validation would
    silently disagree about which answers are correct."""
    conn = sqlite3.connect(fixture_db_path)
    conn.row_factory = sqlite3.Row
    try:
        all_player_ids = {row[0] for row in conn.execute("SELECT id FROM players")}
        assert all_player_ids, "fixture roster must not be empty"

        for cat in ALL_CATEGORIES:
            eligible = cat.eligible_player_ids(conn)

            checked = {pid for pid in all_player_ids if cat.check_player(pid, conn)}
            assert eligible == checked, (
                f"{cat.id}: eligible_player_ids() disagrees with check_player() "
                f"(eligible-only: {eligible - checked}, checked-only: {checked - eligible})"
            )

            sql, params = cat.sql_filter()
            rows = conn.execute(f"SELECT p.id FROM players p WHERE {sql}", params).fetchall()
            from_sql = {row[0] for row in rows}
            assert eligible == from_sql, (
                f"{cat.id}: eligible_player_ids() disagrees with sql_filter() "
                f"(eligible-only: {eligible - from_sql}, sql-only: {from_sql - eligible})"
            )
    finally:
        conn.close()
