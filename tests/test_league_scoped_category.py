from __future__ import annotations

import sqlite3
from pathlib import Path

from src.categories import LeagueScopedCategory, NationalityCategory


def test_league_scoped_category_intersects_base_with_league_membership(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    conn.row_factory = sqlite3.Row
    try:
        base = NationalityCategory("t_nat", "Testland", "Testland")
        # t_nat alone matches Alan, Carl, Hugo, Kara, Farid (per conftest.py's
        # documented pairwise overlaps). Scope to only Testville FC's players.
        scoped = LeagueScopedCategory(base, ["Testville FC"], id="t_nat__testville", label="Testland (Testville FC)")

        base_ids = base.eligible_player_ids(conn)
        scoped_ids = scoped.eligible_player_ids(conn)
        assert scoped_ids <= base_ids
        assert scoped_ids, "expected at least one Testland player who also played for Testville FC"

        all_player_ids = {row[0] for row in conn.execute("SELECT id FROM players")}
        # The three methods must agree, same invariant as every other Category.
        checked = {pid for pid in all_player_ids if scoped.check_player(pid, conn)}
        assert checked == scoped_ids

        sql, params = scoped.sql_filter()
        from_sql = {row[0] for row in conn.execute(f"SELECT p.id FROM players p WHERE {sql}", params)}
        assert from_sql == scoped_ids
    finally:
        conn.close()


def test_league_scoped_category_excludes_players_outside_the_league(fixture_db_path: Path) -> None:
    conn = sqlite3.connect(fixture_db_path)
    conn.row_factory = sqlite3.Row
    try:
        base = NationalityCategory("t_nat", "Testland", "Testland")
        # Hugo Haas is Testland nationality but never played for Sample United.
        scoped = LeagueScopedCategory(base, ["Sample United"], id="t_nat__sample", label="Testland (Sample United)")
        hugo_id = conn.execute("SELECT id FROM players WHERE name = 'Hugo Haas'").fetchone()[0]
        assert scoped.check_player(hugo_id, conn) is False
    finally:
        conn.close()
