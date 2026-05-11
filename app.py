from flask import Flask, jsonify, render_template, request
import sqlite3
import unicodedata
import os
import random

import json as _json

from src.category_config import ALL_CATEGORIES, CATEGORY_BY_ID, CLUB_CATEGORIES
from src.db import Database
from src.famous_matches import get_random_match

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "tictactoe.db")

app = Flask(__name__)

Database(DB_PATH).initialize()

VALID_COLS = {
    "name", "current_club_name", "nationality", "position",
    "market_value", "age", "contract_expires",
    "clubs_count", "transfer_count", "career_start", "career_end",
}

# Parse "€5.00m" / "€500k" to a numeric value for sorting.
MV_SORT_EXPR = """
CASE
    WHEN ps.market_value LIKE '%m'
        THEN CAST(REPLACE(REPLACE(ps.market_value, '€', ''), 'm', '') AS REAL) * 1000000
    WHEN ps.market_value LIKE '%k'
        THEN CAST(REPLACE(REPLACE(ps.market_value, '€', ''), 'k', '') AS REAL) * 1000
    ELSE 0
END
"""


def _normalize(s: str | None) -> str:
    if not s:
        return ""
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode("ascii")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.create_function("normalize", 1, _normalize)
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/players")
def api_players():
    search = request.args.get("search", "").strip()
    club = request.args.get("club", "").strip()
    nationality = request.args.get("nationality", "").strip()
    position = request.args.get("position", "").strip()
    sort_by = request.args.get("sort", "name")
    order = request.args.get("order", "asc")
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(200, max(10, int(request.args.get("per_page", 50))))

    if sort_by not in VALID_COLS:
        sort_by = "name"
    if order not in ("asc", "desc"):
        order = "asc"

    where_parts: list[str] = []
    params: list = []

    if search:
        for word in _normalize(search).split():
            where_parts.append("normalize(ps.name) LIKE ?")
            params.append(f"%{word}%")
    if club:
        where_parts.append("ps.current_club_name = ?")
        params.append(club)
    if nationality:
        where_parts.append("ps.nationality LIKE ?")
        params.append(f"%{nationality}%")
    if position:
        where_parts.append("ps.position = ?")
        params.append(position)

    where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""

    if sort_by == "market_value":
        order_expr = f"({MV_SORT_EXPR}) {order}"
    else:
        # ps.col IS NULL evaluates to 1 for NULLs → always sorted last
        order_expr = f"ps.{sort_by} IS NULL, ps.{sort_by} {order}"

    db = get_db()
    try:
        total = db.execute(
            f"SELECT COUNT(*) FROM player_stats ps {where}", params
        ).fetchone()[0]

        offset = (page - 1) * per_page
        rows = db.execute(
            f"""SELECT ps.*, p.source_url
                FROM player_stats ps
                JOIN players p ON p.id = ps.id
                {where}
                ORDER BY {order_expr}
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        ).fetchall()
    finally:
        db.close()

    return jsonify(
        {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page),
            "data": [dict(r) for r in rows],
        }
    )


@app.route("/api/players/<int:player_id>")
def api_player_detail(player_id: int):
    db = get_db()
    try:
        player = db.execute(
            "SELECT ps.*, p.source_url FROM player_stats ps "
            "JOIN players p ON p.id = ps.id WHERE ps.id = ?",
            [player_id],
        ).fetchone()
        if not player:
            return jsonify({"error": "Not found"}), 404

        transfers = db.execute(
            "SELECT * FROM transfers WHERE player_id = ? ORDER BY date_iso DESC",
            [player_id],
        ).fetchall()

        stints = db.execute(
            "SELECT * FROM career_stints WHERE player_id = ? ORDER BY start_season",
            [player_id],
        ).fetchall()
    finally:
        db.close()

    return jsonify(
        {
            "player": dict(player),
            "transfers": [dict(t) for t in transfers],
            "career_stints": [dict(s) for s in stints],
        }
    )


@app.route("/api/filters")
def api_filters():
    db = get_db()
    try:
        clubs = [
            r[0]
            for r in db.execute(
                "SELECT DISTINCT current_club_name FROM players "
                "WHERE current_club_name IS NOT NULL ORDER BY current_club_name"
            ).fetchall()
        ]
        positions = [
            r[0]
            for r in db.execute(
                "SELECT DISTINCT position FROM players "
                "WHERE position IS NOT NULL ORDER BY position"
            ).fetchall()
        ]
    finally:
        db.close()

    return jsonify({"clubs": clubs, "positions": positions})


_CAT_ICONS: dict[str, str] = {
    "nat_ger": "🇩🇪", "nat_eng": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "nat_esp": "🇪🇸",
    "nat_fra": "🇫🇷", "nat_bra": "🇧🇷", "nat_arg": "🇦🇷",
    "nat_ned": "🇳🇱", "nat_por": "🇵🇹", "nat_ita": "🇮🇹",
    "nat_hrv": "🇭🇷", "nat_bel": "🇧🇪", "nat_dnk": "🇩🇰",
    "nat_swe": "🇸🇪", "nat_tur": "🇹🇷", "nat_aut": "🇦🇹",
    "nat_pol": "🇵🇱", "nat_sco": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "nat_wal": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "club_bay": "🔴", "club_bvb": "🟡", "club_b04": "⚫",
    "club_rbl": "🔴", "club_sge": "⚫", "club_s04": "🔵",
    "club_hsv": "🔴", "club_svw": "🟢", "club_bmg": "⚫",
    "club_mnu": "🔴", "club_mci": "🔵", "club_lfc": "🔴",
    "club_ars": "🔴", "club_che": "🔵", "club_tot": "⚪",
    "club_rma": "⚪", "club_fcb": "🔵", "club_atm": "🔴",
    "club_sev": "⚪", "club_val": "🟠", "club_juv": "⚫",
    "club_int": "🔵", "club_mil": "🔴", "club_psg": "🔵",
    "club_laz": "🔵",
    "league_buli": "🇩🇪", "league_pl": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "league_laliga": "🇪🇸",
    "league_seriea": "🇮🇹", "league_ligue1": "🇫🇷",
    "cont_eur": "🌍", "cont_sam": "🌎", "cont_afr": "🌍", "cont_asia": "🌏",
    "cont_non_eu": "🗺️",
    "nat_noneu": "🌍",
    "init_a": "🔡", "init_b": "🔡", "init_c": "🔡", "init_d": "🔡",
    "init_e": "🔡", "init_f": "🔡", "init_g": "🔡", "init_h": "🔡",
    "init_j": "🔡", "init_k": "🔡", "init_l": "🔡", "init_m": "🔡",
    "init_n": "🔡", "init_o": "🔡", "init_p": "🔡", "init_r": "🔡",
    "init_s": "🔡", "init_t": "🔡", "init_w": "🔡",
    "cont_letter_i": "🔠", "cont_letter_u": "🔠", "cont_letter_v": "🔠",
    "cont_letter_x": "🔠", "cont_letter_y": "🔠", "cont_letter_z": "🔠",
    "cont_letter_q": "🔠",
    "age_u23": "🌱", "age_2430": "⚡", "age_30p": "🎖️",
    "mv_high": "💰", "mv_mid": "💵", "mv_low": "💶",
    "trophy_ballon": "🏅", "trophy_world_cup": "🏆", "trophy_cl": "🏆",
    "trophy_liga": "🥇", "trophy_ligue1": "🥇", "trophy_copa": "🏆",
    "trophy_fifa_cwc": "🏆", "trophy_mls_cup": "🏆", "trophy_u20": "🥇",
    "trophy_olympic": "🥇", "trophy_leagues_cup": "🏆",
    "pos_gk": "🧤", "pos_def": "🛡️", "pos_mid": "⚽",
    "pos_fwd": "⚡", "pos_cb": "🛡️", "pos_lb": "◀️",
    "pos_rb": "▶️", "pos_dm": "🧲", "pos_cm": "⚙️",
    "pos_am": "🎯", "pos_st": "⚡", "pos_lw": "◀️", "pos_rw": "▶️",
}


def _cat_display(cat) -> dict:
    return {
        "id": cat.id,
        "label": cat.label,
        "type": cat.type.value,
        "icon": _CAT_ICONS.get(cat.id, "⚽"),
        "difficulty": cat.difficulty,
    }


def _generate_puzzle(db: sqlite3.Connection, max_difficulty: int = 3, min_players: int = 5, max_players: int = 9999, max_attempts: int = 300):
    pool = [cat for cat in ALL_CATEGORIES if cat.difficulty <= max_difficulty]
    eligible: dict[str, set[int]] = {cat.id: cat.eligible_player_ids(db) for cat in pool}
    for _ in range(max_attempts):
        if len(pool) < 6:
            return None, None
        sample = random.sample(pool, 6)
        rows, cols = sample[:3], sample[3:]
        if {c.id for c in rows} & {c.id for c in cols}:
            continue
        counts = [len(eligible[r.id] & eligible[c.id]) for r in rows for c in cols]
        if all(min_players <= n <= max_players for n in counts):
            return rows, cols
    return None, None


@app.route("/game")
def game():
    return render_template("game.html")


@app.route("/api/game/new")
def api_game_new():
    difficulty = min(3, max(1, int(request.args.get("difficulty", 3))))
    # min/max players per cell and attempt budget per difficulty level
    diff_cfg = {
        1: dict(min_players=15, max_players=9999, max_attempts=500),  # easy: generous
        2: dict(min_players=6,  max_players=60,   max_attempts=400),  # medium: moderate
        3: dict(min_players=1,  max_players=20,   max_attempts=300),  # hard: single-digit cells
    }
    db = get_db()
    try:
        rows, cols = _generate_puzzle(
            db,
            max_difficulty=difficulty,
            **diff_cfg[difficulty],
        )
    finally:
        db.close()
    if rows is None:
        return jsonify({"error": "Kein gültiges Rätsel gefunden"}), 500
    return jsonify({"rows": [_cat_display(c) for c in rows], "cols": [_cat_display(c) for c in cols]})


@app.route("/api/game/search")
def api_game_search():
    """Search all players by name (no category filter) — category check happens on validate."""
    q = request.args.get("q", "").strip()
    if len(q) < 3:
        return jsonify({"players": []})

    where_parts = []
    params: list = []
    for word in _normalize(q).split():
        where_parts.append("normalize(p.name) LIKE ?")
        params.append(f"%{word}%")
    where = "WHERE " + " AND ".join(where_parts)

    db = get_db()
    try:
        rows_db = db.execute(
            f"SELECT p.id, p.name, p.current_club_name, p.nationality "
            f"FROM players p {where} ORDER BY p.name LIMIT 20",
            params,
        ).fetchall()
    finally:
        db.close()
    return jsonify({"players": [dict(r) for r in rows_db]})


@app.route("/api/game/solve")
def api_game_solve():
    """Return valid players for every cell in the grid (for the solve view)."""
    row_ids = request.args.get("rows", "").split(",")
    col_ids = request.args.get("cols", "").split(",")
    if len(row_ids) != 3 or len(col_ids) != 3:
        return jsonify({"error": "Need exactly 3 row and 3 col IDs"}), 400

    cats: dict = {}
    for cat_id in row_ids + col_ids:
        cat = CATEGORY_BY_ID.get(cat_id)
        if not cat:
            return jsonify({"error": f"Invalid category: {cat_id}"}), 400
        cats[cat_id] = cat

    db = get_db()
    try:
        grid = []
        for row_id in row_ids:
            row_cat = cats[row_id]
            row_sql, row_params = row_cat.sql_filter()
            row_cells = []
            for col_id in col_ids:
                col_cat = cats[col_id]
                col_sql, col_params = col_cat.sql_filter()
                params = row_params + col_params
                rows_db = db.execute(
                    f"""SELECT p.id, p.name, p.current_club_name
                        FROM players p
                        WHERE {row_sql} AND {col_sql}
                        ORDER BY (
                            CASE
                                WHEN p.market_value LIKE '%m'
                                    THEN CAST(REPLACE(REPLACE(p.market_value, '€', ''), 'm', '') AS REAL) * 1000000
                                WHEN p.market_value LIKE '%k'
                                    THEN CAST(REPLACE(REPLACE(p.market_value, '€', ''), 'k', '') AS REAL) * 1000
                                ELSE 0
                            END
                        ) DESC
                        """,
                    params,
                ).fetchall()
                count = len(rows_db)
                row_cells.append({"count": count, "players": [dict(r) for r in rows_db]})
            grid.append(row_cells)
    finally:
        db.close()
    return jsonify({"grid": grid})


@app.route("/api/game/validate", methods=["POST"])
def api_game_validate():
    data = request.get_json() or {}
    player_id = data.get("player_id")
    row_id = data.get("row_id")
    col_id = data.get("col_id")

    row_cat = CATEGORY_BY_ID.get(row_id or "")
    col_cat = CATEGORY_BY_ID.get(col_id or "")
    if not row_cat or not col_cat or player_id is None:
        return jsonify({"valid": False, "error": "Invalid input"}), 400

    db = get_db()
    try:
        valid = row_cat.check_player(player_id, db) and col_cat.check_player(player_id, db)
        player = db.execute("SELECT id, name, current_club_name FROM players WHERE id = ?", [player_id]).fetchone()
    finally:
        db.close()
    return jsonify({"valid": valid, "player": dict(player) if player else None})



@app.route("/squad-guesser")
def squad_guesser():
    return render_template("squad_guesser.html")


@app.route("/api/squad-guesser/game")
def api_squad_guesser_game():
    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM match_lineups ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
    except Exception:
        row = None
    finally:
        db.close()

    if row:
        return jsonify({
            "match": {
                "competition": row["competition"],
                "date": row["date_display"],
                "venue": row["venue"] or "",
            },
            "home": {
                "name": row["home_name"],
                "colour_primary": row["home_colour_primary"],
                "colour_secondary": row["home_colour_secondary"],
                "players": _json.loads(row["home_xi"]),
            },
            "away": {
                "name": row["away_name"],
                "colour_primary": row["away_colour_primary"],
                "colour_secondary": row["away_colour_secondary"],
                "players": _json.loads(row["away_xi"]),
            },
        })

    # Fallback to hardcoded famous matches if DB is empty
    m = get_random_match()
    return jsonify({
        "match": {
            "competition": m["competition"],
            "date": m["date"],
            "venue": m["venue"],
        },
        "home": {
            "name": m["home"]["name"],
            "colour_primary": m["home"]["colour_primary"],
            "colour_secondary": m["home"]["colour_secondary"],
            "players": m["home"]["xi"],
        },
        "away": {
            "name": m["away"]["name"],
            "colour_primary": m["away"]["colour_primary"],
            "colour_secondary": m["away"]["colour_secondary"],
            "players": m["away"]["xi"],
        },
    })


@app.route("/combos")
def combos():
    return render_template("combos.html")


@app.route("/api/clubs/combos")
def api_clubs_combos():
    club_filter = request.args.get("club", "").strip()
    try:
        max_players = int(request.args.get("max_players", 100))
    except ValueError:
        max_players = 100

    game_club_names = [c.club_name for c in CLUB_CATEGORIES]

    db = get_db()
    try:
        # Build club → player_id sets in one query
        rows = db.execute(
            f"SELECT club_name, player_id FROM career_stints "
            f"WHERE club_name IN ({','.join('?' * len(game_club_names))})",
            game_club_names,
        ).fetchall()

        club_players: dict[str, set[int]] = {}
        for r in rows:
            club_players.setdefault(r["club_name"], set()).add(r["player_id"])

        # Compute all pair intersections
        clubs = sorted(club_players.keys())
        pairs = []
        for i, c1 in enumerate(clubs):
            for c2 in clubs[i + 1 :]:
                shared = club_players[c1] & club_players[c2]
                count = len(shared)
                if count > max_players:
                    continue
                if club_filter and club_filter not in (c1, c2):
                    continue
                pairs.append((c1, c2, count, shared))

        pairs.sort(key=lambda x: x[2])

        # Fetch names for all relevant player IDs in one query
        all_ids = {pid for _, _, _, ids in pairs for pid in ids}
        if all_ids:
            id_list = list(all_ids)
            name_rows = db.execute(
                f"SELECT id, name FROM players WHERE id IN ({','.join('?' * len(id_list))})",
                id_list,
            ).fetchall()
            name_map = {
                r["id"]: (
                    r["name"].split(" ", 1)[1] if r["name"].startswith("#") and " " in r["name"]
                    else r["name"]
                )
                for r in name_rows
            }
        else:
            name_map = {}

        result = [
            {
                "club1": c1,
                "club2": c2,
                "count": count,
                "players": [
                    {"id": pid, "name": name_map.get(pid, str(pid))}
                    for pid in sorted(shared, key=lambda p: name_map.get(p, ""))
                ],
            }
            for c1, c2, count, shared in pairs
        ]
    finally:
        db.close()

    return jsonify({"pairs": result, "total": len(result)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port)
