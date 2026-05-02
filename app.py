from flask import Flask, jsonify, render_template, request
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "tictactoe.db")

app = Flask(__name__)

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


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
        where_parts.append("ps.name LIKE ?")
        params.append(f"%{search}%")
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
