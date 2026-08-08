from flask import Flask, Response, jsonify, render_template, request
import hashlib
import sqlite3
import time
import unicodedata
import os
import random

import json as _json

from src import category_config
from src import dynamic_categories
from src.categories import CategoryType
from src.db import Database
from src.famous_matches import get_random_match
from src import multiplayer as mp

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


# Club/nationality/trophy categories are generated from the real dataset once
# at startup (see src/dynamic_categories.py) rather than hand-curated, so the
# puzzle pool covers ~6,000 clubs / ~100 nationalities / ~500 trophies instead
# of the ~60 that used to be typed out by hand. Built eagerly (not lazily on
# first request) since the deployment already runs a single worker process
# for the multiplayer room store (see Dockerfile) — there's no cache-coherency
# concern either way, and eager building keeps startup latency predictable
# instead of moving it onto whichever request happens to be first.
_startup_conn = get_db()
try:
    _dynamic_catalog = dynamic_categories.build_all(_startup_conn)
finally:
    _startup_conn.close()

ALL_CATEGORIES: list = category_config.ALL_CATEGORIES + _dynamic_catalog.all()
CATEGORY_BY_ID: dict = {cat.id: cat for cat in ALL_CATEGORIES}

# League id -> category pool scoped to that league, for the 4 league-only
# game modes (Bundesliga/Premier League/La Liga/Serie A — the only
# leagues with a hand-curated club list, see category_config.LEAGUE_CATEGORIES).
LEAGUE_POOLS: dict = dynamic_categories.build_league_pools(
    category_config.LEAGUE_CATEGORIES, ALL_CATEGORIES, _dynamic_catalog
)
# /api/game/validate and /api/game/solve look categories up by id from
# whatever the client submits — for a league-mode puzzle that includes the
# wrapped LeagueScopedCategory ids, not just the underlying base ids.
for _league_pool in LEAGUE_POOLS.values():
    for _cat in _league_pool:
        CATEGORY_BY_ID.setdefault(_cat.id, _cat)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sw.js")
def service_worker():
    # Served from the root path (not /static/sw.js) so it can be registered
    # with scope "/game" — a service worker's max allowed scope is its own
    # directory, and only the game page should ever be controlled by it.
    response = app.send_static_file("sw.js")
    response.headers["Cache-Control"] = "no-cache"
    return response


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
    "league_seriea": "🇮🇹",
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


def _club_badge_color(cat_id: str) -> str:
    """A deterministic color for a club's fallback badge, derived from its id
    so the same club always gets the same color across requests/sessions."""
    digest = hashlib.sha1(cat_id.encode("utf-8")).hexdigest()
    hue = int(digest[:4], 16) % 360
    return f"hsl({hue}, 55%, 38%)"


def _cat_display(cat) -> dict:
    # Resolution order: a hand-picked icon (the ~60 legacy ids this dict was
    # originally built for) wins if present; otherwise fall back to the
    # category's own icon (set for dynamic nationalities — a real flag emoji,
    # see src/countries.py); otherwise a programmatic fallback by type. This
    # is what lets ~7,000 dynamically generated categories all get a
    # reasonable icon without hand-maintaining an ever-growing dict — the
    # old approach was already 9 entries short and 8 stale at just 111
    # categories, which cannot scale to thousands.
    icon = _CAT_ICONS.get(cat.id) or getattr(cat, "icon", None)
    display = {
        "id": cat.id,
        "label": cat.label,
        "type": cat.type.value,
        "difficulty": cat.difficulty,
    }
    if icon:
        display["icon"] = icon
    elif cat.type == CategoryType.CLUB:
        # No generic "colored circle with a letter" emoji exists, so the
        # client renders this itself — a small colored badge with the
        # club's first letter — when icon is absent but icon_letter is set.
        display["icon"] = None
        display["icon_letter"] = (cat.label[:1] or "?").upper()
        display["icon_color"] = _club_badge_color(cat.id)
    elif cat.type == CategoryType.AWARD:
        display["icon"] = "🏆"
    else:
        display["icon"] = "⚽"
    return display


# Two categories only intersect well when they're either broad (cover a
# large, structural slice of players — nationality, position, age, league...)
# or specifically, individually chosen to relate to each other. Clubs and
# trophies are both "narrow-and-numerous": with ~6,500 dynamic clubs and
# ~490 dynamic trophies (together 97% of the full pool), two *random* clubs
# rarely share a transferred player and two *random* trophies rarely share a
# winner — reliable overlap there was a property of the old, small,
# hand-picked lists, not something that holds at this scale. Uniformly
# sampling 6 categories from a pool this lopsided overwhelmingly picks
# "mostly/all club+trophy rows x mostly/all club+trophy cols", which then
# fails the eligible-count bounds check on nearly every cell. Capping how
# many sparse (club/trophy) categories can appear keeps most cells paired
# against a broad category instead, which reliably has *some* overlap (e.g.
# "German" x "an obscure club" almost always has an answer).
_SPARSE_TYPES = {CategoryType.CLUB, CategoryType.AWARD}
MAX_SPARSE_PER_PUZZLE = 2

# League-scoped puzzles (see _resolve_pool/LEAGUE_POOLS): the whole point of
# picking a league is to see that league's own clubs, but the general sparse
# cap above only allows up to 2 of them — most cells would end up being
# other categories merely *scoped* to the league rather than the league's
# clubs themselves. League mode uses a dedicated sampler guaranteeing this
# many real clubs from the league (one full side of the grid).
LEAGUE_MIN_CLUBS = 4


def _sample_puzzle_categories(sparse: list, broad: list) -> tuple[list, list] | None:
    """Returns (rows, cols), keeping all sparse (club/trophy) categories on
    one side. That guarantees no cell ever pairs two sparse categories
    against each other — by far the least likely pairing to have any
    overlap at all, since it relies on two specific narrow categories
    coinciding rather than either of them being broad enough to reliably
    intersect with anything.
    """
    if len(sparse) + len(broad) < 6:
        return None
    if not broad:
        if len(sparse) < 6:
            return None
        six = random.sample(sparse, 6)
        return six[:3], six[3:]

    # At least 1 sparse category (when available) rather than 0-2: an all-broad
    # sample (nationality x position x age x ...) tends to have *too much*
    # overlap per cell for tighter difficulty bounds to accept, since every
    # side covers a large structural slice of players. Mixing in a sparse
    # category keeps most cells at a moderate, bounds-friendly size instead.
    min_sparse = 1 if sparse else 0
    n_sparse = min(MAX_SPARSE_PER_PUZZLE, len(sparse), random.randint(min_sparse, MAX_SPARSE_PER_PUZZLE))
    n_broad = 6 - n_sparse
    if len(broad) < n_broad:
        n_broad = len(broad)
        n_sparse = min(len(sparse), 6 - n_broad)

    chosen_sparse = random.sample(sparse, n_sparse)
    chosen_broad = random.sample(broad, n_broad)
    fill = 3 - n_sparse
    sparse_side = chosen_sparse + chosen_broad[:fill]
    other_side = chosen_broad[fill:]
    random.shuffle(sparse_side)
    random.shuffle(other_side)
    return (sparse_side, other_side) if random.random() < 0.5 else (other_side, sparse_side)


def _sample_league_puzzle_categories(league_clubs: list, broad_no_award: list, min_clubs: int) -> tuple[list, list] | None:
    """League mode: at least `min_clubs` real clubs from the selected league
    among the 6 categories — but, unlike the general sparse-type cap, mixed
    freely across rows/cols rather than confined to one whole side. Within a
    single league, two clubs are far more likely to share a transferred
    player than two random clubs from the entire catalog (moves within the
    same league are common), so club x club cells are safe to allow here —
    keeping clubs pinned to one solid side every time made every league
    puzzle the same rigid shape ("league's clubs" vs "everything else").
    Non-club/non-trophy categories fill the rest; trophies are excluded even
    though they're not clubs — a trophy narrowed to "won by a player who
    also played in this one league" is often too thin to be reliable, same
    reasoning _SPARSE_TYPES applies elsewhere.
    """
    max_clubs = min(6, len(league_clubs))
    if max_clubs < min_clubs:
        return None
    n_clubs = random.randint(min_clubs, max_clubs)
    n_broad = 6 - n_clubs
    if len(broad_no_award) < n_broad:
        n_broad = len(broad_no_award)
        n_clubs = min(max_clubs, 6 - n_broad)
        if n_clubs < min_clubs:
            return None
    combined = random.sample(league_clubs, n_clubs) + random.sample(broad_no_award, n_broad)
    random.shuffle(combined)
    return combined[:3], combined[3:]


def _generate_puzzle(db: sqlite3.Connection, max_difficulty: int = 3, min_players: int = 5, max_players: int = 9999, max_attempts: int = 300, pool: list | None = None, min_league_clubs: int = 0):
    if pool is None:
        pool = ALL_CATEGORIES
    pool = [cat for cat in pool if cat.difficulty <= max_difficulty]
    if len(pool) < 6:
        return None, None

    # Eligible-player-id sets are computed lazily and cached per category id,
    # not eagerly for the whole pool up front. With ~7,000 dynamically
    # generated categories in play, eagerly computing eligible_player_ids()
    # for every one of them (most of which never get sampled) made a single
    # /api/game/new request take several seconds — this only ever queries
    # the categories that actually get drawn.
    eligible_cache: dict[str, set[int]] = {}

    def eligible_ids(cat) -> set[int]:
        cached = eligible_cache.get(cat.id)
        if cached is None:
            cached = cat.eligible_player_ids(db)
            eligible_cache[cat.id] = cached
        return cached

    if min_league_clubs > 0:
        league_clubs = [c for c in pool if c.type == CategoryType.CLUB]
        broad_no_award = [c for c in pool if c.type not in (CategoryType.CLUB, CategoryType.AWARD, CategoryType.LEAGUE, CategoryType.CONTINENT)]
        for _ in range(max_attempts):
            sampled = _sample_league_puzzle_categories(league_clubs, broad_no_award, min_league_clubs)
            if sampled is None:
                return None, None
            rows, cols = sampled
            counts = [len(eligible_ids(r) & eligible_ids(c)) for r in rows for c in cols]
            if all(min_players <= n <= max_players for n in counts):
                return rows, cols
        return None, None

    sparse = [c for c in pool if c.type in _SPARSE_TYPES]
    broad = [c for c in pool if c.type not in _SPARSE_TYPES]
    for _ in range(max_attempts):
        sampled = _sample_puzzle_categories(sparse, broad)
        if sampled is None:
            return None, None
        rows, cols = sampled
        counts = [len(eligible_ids(r) & eligible_ids(c)) for r in rows for c in cols]
        if all(min_players <= n <= max_players for n in counts):
            return rows, cols
    return None, None


# Each entry is tried in order; constraints are relaxed until a puzzle is found.
# The final fallback for each level has no upper bound and a high attempt count,
# making it virtually guaranteed to succeed.
# Retuned for the dynamic (~7,000-category) pool: with this much variety,
# requiring every one of the 9 cells to simultaneously clear a strict bound
# is a much harder combinatorial ask than it was against the old ~111
# hand-picked categories (empirically, even min_players=15 on the easiest
# difficulty now succeeds well under half the time no matter how many
# attempts you throw at it). The tight tiers are kept — they still give the
# best puzzles on the occasions they succeed — but with small attempt
# budgets so they fail fast instead of grinding; the final, loosest tier
# per difficulty (empirically ~90%+ reliable within a few hundred attempts)
# carries the actual "virtually guaranteed to succeed" guarantee.
_DIFFICULTY_FALLBACKS = {
    1: [
        dict(min_players=15, max_players=9999, max_attempts=30),
        dict(min_players=5,  max_players=9999, max_attempts=30),
        dict(min_players=1,  max_players=9999, max_attempts=500),
    ],
    2: [
        dict(min_players=6,  max_players=60,   max_attempts=30),
        dict(min_players=2,  max_players=100,  max_attempts=30),
        dict(min_players=1,  max_players=9999, max_attempts=500),
    ],
    3: [
        dict(min_players=1,  max_players=20,   max_attempts=30),
        dict(min_players=1,  max_players=40,   max_attempts=30),
        dict(min_players=1,  max_players=9999, max_attempts=500),
    ],
}


def _generate_puzzle_for_difficulty(db: sqlite3.Connection, difficulty: int, pool: list | None = None, min_league_clubs: int = 0):
    """Generate a puzzle for a clamped 1-3 difficulty, walking the fallback ladder.

    Shared by /api/game/new (solo + local) and multiplayer room creation so
    both draw puzzles with identical quality guarantees. `pool` defaults to
    the full category catalog; callers pass a narrower one to respect a
    player's excluded-categories settings or a league-scoped game mode
    (see _resolve_pool()). `min_league_clubs` > 0 switches to the
    league-priority sampler (see _sample_league_puzzle_categories).
    """
    difficulty = min(3, max(1, difficulty))
    for cfg in _DIFFICULTY_FALLBACKS[difficulty]:
        rows, cols = _generate_puzzle(db, max_difficulty=difficulty, pool=pool, min_league_clubs=min_league_clubs, **cfg)
        if rows is not None:
            return rows, cols
    return None, None


def _resolve_pool(excluded_types: set[str] | None = None, excluded_ids: set[str] | None = None, league: str | None = None) -> list:
    """Build the category pool /api/game/new and room creation both generate
    puzzles from — the single seam settings-filtering and league-scoping both
    plug into, so solo/local and online rooms apply them identically (the
    same way `difficulty` already does today).
    """
    pool = LEAGUE_POOLS.get(league, ALL_CATEGORIES) if league else ALL_CATEGORIES
    if excluded_types:
        pool = [cat for cat in pool if cat.type.value not in excluded_types]
    if excluded_ids:
        pool = [cat for cat in pool if cat.id not in excluded_ids]
    return pool


def _parse_csv_param(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {part.strip() for part in raw.split(",") if part.strip()}


@app.route("/api/categories")
def api_categories():
    """Server-side search over the category catalog, backing the settings
    page's individual-exclude checklist — with ~6,500 clubs and ~490
    trophies, shipping the full catalog to the browser up front isn't
    practical, so this mirrors the debounced-search pattern /api/game/search
    already uses for players."""
    cat_type = request.args.get("type", "").strip()
    query = _normalize(request.args.get("q", "").strip())
    try:
        limit = min(100, max(1, int(request.args.get("limit", 50))))
    except ValueError:
        limit = 50

    results = [c for c in ALL_CATEGORIES if c.type.value == cat_type]
    if query:
        results = [c for c in results if query in _normalize(c.label)]
    results.sort(key=lambda c: (c.difficulty, c.label))
    return jsonify({"categories": [_cat_display(c) for c in results[:limit]]})


@app.route("/game")
def game():
    return render_template("game.html")


@app.route("/api/game/new")
def api_game_new():
    difficulty = min(3, max(1, int(request.args.get("difficulty", 3))))
    league = request.args.get("league") or None
    excluded_types = _parse_csv_param(request.args.get("excluded_types"))
    excluded_ids = _parse_csv_param(request.args.get("excluded"))
    pool = _resolve_pool(excluded_types=excluded_types, excluded_ids=excluded_ids, league=league)

    db = get_db()
    try:
        rows, cols = _generate_puzzle_for_difficulty(
            db, difficulty, pool=pool, min_league_clubs=LEAGUE_MIN_CLUBS if league else 0
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


# ─── Online 1v1 (multiplayer rooms) ────────────────────────────────────────
# Room state lives in-process (src/multiplayer.py) — the deployment must run
# a single worker process (see Dockerfile) since a second process would have
# its own, disjoint copy of the room dict.

@app.route("/api/multiplayer/rooms", methods=["POST"])
def api_mp_create_room():
    data = request.get_json(silent=True) or {}
    difficulty = min(3, max(1, int(data.get("difficulty", 3))))
    # The room creator's settings govern the whole room, exactly mirroring how
    # difficulty already works — the joiner never supplies their own.
    league = data.get("league") or None
    excluded_types = set(data.get("excludedTypes") or [])
    excluded_ids = set(data.get("excludedCategoryIds") or [])
    pool = _resolve_pool(excluded_types=excluded_types, excluded_ids=excluded_ids, league=league)

    db = get_db()
    try:
        rows, cols = _generate_puzzle_for_difficulty(
            db, difficulty, pool=pool, min_league_clubs=LEAGUE_MIN_CLUBS if league else 0
        )
    finally:
        db.close()
    if rows is None:
        return jsonify({"error": "Kein gültiges Rätsel gefunden"}), 500
    room, token = mp.create_room(rows, cols)
    return jsonify({"code": room.code, "token": token, "slot": 1})


@app.route("/api/multiplayer/rooms/<code>/join", methods=["POST"])
def api_mp_join_room(code):
    result = mp.join_room(code)
    if result is None:
        status = 404 if mp.get_room(code) is None else 409
        return jsonify({"error": "Raum nicht gefunden oder bereits voll"}), status
    room, token = result
    return jsonify({"code": room.code, "token": token, "slot": 2})


@app.route("/api/multiplayer/rooms/<code>/state")
def api_mp_room_state(code):
    room = mp.get_room(code)
    if room is None:
        return jsonify({"error": "Raum nicht gefunden"}), 404
    slot = mp.room_slot_for_token(room, request.args.get("token", ""))
    return jsonify(room.public_state(viewer_slot=slot, cat_display_fn=_cat_display))


@app.route("/api/multiplayer/rooms/<code>/events")
def api_mp_room_events(code):
    room = mp.get_room(code)
    if room is None:
        return jsonify({"error": "Raum nicht gefunden"}), 404

    def stream():
        last_version = -1
        ticks = 0
        while True:
            if room.version != last_version:
                last_version = room.version
                yield f"data: {_json.dumps({'version': last_version})}\n\n"
            elif ticks % 15 == 0:
                yield ": ping\n\n"  # keep proxies/browsers from closing the idle connection
            ticks += 1
            time.sleep(1)
            if room.is_stale():
                break

    resp = Response(stream(), mimetype="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"  # disable reverse-proxy response buffering for SSE
    return resp


@app.route("/api/multiplayer/rooms/<code>/moves", methods=["POST"])
def api_mp_move(code):
    room = mp.get_room(code)
    if room is None:
        return jsonify({"error": "Raum nicht gefunden"}), 404

    data = request.get_json(silent=True) or {}
    token = data.get("token", "")
    row, col, player_id = data.get("row"), data.get("col"), data.get("player_id")
    if row is None or col is None or player_id is None:
        return jsonify({"ok": False, "reason": "bad_input"}), 400

    db = get_db()
    try:
        ok, reason, placed = mp.apply_move(room, token, int(row), int(col), int(player_id), db)
    finally:
        db.close()
    return jsonify({"ok": ok, "reason": reason, "placed": placed})


@app.route("/api/multiplayer/rooms/<code>/forfeit", methods=["POST"])
def api_mp_forfeit(code):
    room = mp.get_room(code)
    if room is None:
        return jsonify({"error": "Raum nicht gefunden"}), 404
    data = request.get_json(silent=True) or {}
    ok = mp.forfeit(room, data.get("token", ""))
    return jsonify({"ok": ok})


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

    # This page kept its original ~31-club scope (now via the legacy id map
    # in dynamic_categories.py, which also happens to fix a long-standing bug
    # where "Manchester City" never matched anything — see that module).
    game_club_names = list(dynamic_categories.LEGACY_CLUB_IDS.keys())

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
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    # threaded=True: the multiplayer SSE stream is a long-lived connection —
    # without it the single-threaded dev server can't also serve moves/state
    # requests while a room's event stream is open.
    app.run(debug=debug, host="0.0.0.0", port=port, threaded=True)
