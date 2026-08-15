from flask import Flask, Response, abort, jsonify, render_template, request
import hashlib
import logging
import sqlite3
import time
import unicodedata
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import json as _json

from werkzeug.exceptions import HTTPException

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from src import category_config
from src import dynamic_categories
from src import grids as grid_store
from src.categories import CategoryType
from src.countries import country_flag_image_code
from src.db import Database
from src.famous_matches import get_random_match
from src import multiplayer as mp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "tictactoe.db")

app = Flask(__name__)

# Rate limiting below keys off request.remote_addr — accurate only for a
# direct connection. Once this app sits behind a real reverse proxy/load
# balancer, request.remote_addr becomes the proxy's own IP for every
# request unless something explicitly trusts that proxy's X-Forwarded-For
# header. ProxyFix does that — but blindly trusting X-Forwarded-For with no
# real proxy in front would let any client just set that header themselves
# to spoof a different IP and dodge rate limits entirely, so this stays off
# by default and only activates when TRUSTED_PROXY_COUNT is explicitly set
# (in the deployment's environment, not committed here) to the number of
# proxies actually sitting in front of this process — usually 1 for a
# single nginx/Caddy/PaaS edge load balancer. Sets x_proto/x_host too so
# request.scheme/request.host come out right behind HTTPS-terminating
# proxies, even though nothing here reads them yet.
_trusted_proxy_count = int(os.environ.get("TRUSTED_PROXY_COUNT", "0"))
if _trusted_proxy_count > 0:
    from werkzeug.middleware.proxy_fix import ProxyFix

    app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
        app.wsgi_app, x_for=_trusted_proxy_count, x_proto=_trusted_proxy_count, x_host=_trusted_proxy_count
    )

# Plain stdout/stderr logging — gunicorn (see Dockerfile's --access-logfile/
# --error-logfile) and `docker logs`/journald/etc. already capture whatever
# a process prints, so there's no separate log-shipping setup to stand up
# for a single-container deployment this size. FLASK_DEBUG=1 (local dev)
# gets DEBUG-level noise; production stays at INFO so routine requests
# (already logged by gunicorn's own access log) don't get duplicated here —
# this logger is for our own messages, chiefly the unhandled-exception log
# in handle_unexpected_exception below.
logging.basicConfig(
    level=logging.DEBUG if os.environ.get("FLASK_DEBUG", "0") == "1" else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

# In-memory counters — consistent with the same single-worker-process
# constraint online multiplayer room state already has (see the Dockerfile's
# --workers 1 note and src/multiplayer.py's architecture comment): a second
# gunicorn worker would keep its own, disjoint set of counters, letting a
# client bypass a limit just by getting routed to a different worker.
#
# Keyed by get_remote_address, i.e. request.remote_addr — see the
# TRUSTED_PROXY_COUNT/ProxyFix block above for why that's only the real
# client IP once a trusted reverse proxy is actually in front of this.
#
# default_limits is the floor for every route below that doesn't declare its
# own @limiter.limit(...) — the handful of routes that do are either
# meaningfully more expensive per request (puzzle/room/grid generation) or
# fired rapidly by design (search-as-you-type, gameplay actions); everything
# else (simple reads) is cheap enough that this floor is basically headroom,
# not an active constraint. Flask-Limiter exempts the "static" endpoint
# automatically; the page-shell routes are exempted explicitly below.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per minute"],
    storage_uri="memory://",
    strategy="fixed-window",
    headers_enabled=True,
)

# Real DB/CPU work per request: puzzle generation, and creating a room/grid
# that persists (in memory or in the DB) until something else cleans it up.
RATE_LIMIT_EXPENSIVE = "15 per minute"
# Cheaper per call, but fired rapidly by design — search-as-you-type,
# validation, and in-game actions (a move, a rematch vote, ...).
RATE_LIMIT_MODERATE = "30 per minute"
# Establishing an SSE connection, not the (potentially long-lived) stream
# itself — a limiter check only ever runs once, at connect time.
RATE_LIMIT_CONNECT = "20 per minute"

Database(DB_PATH).initialize()

# Real flag/crest images (see fetch_flags.py, fetch_club_logos.py) — loaded
# once at startup so _cat_display() can do an O(1) lookup instead of hitting
# the filesystem/a dict per request.
_FLAG_CODES_AVAILABLE: set[str] = {
    p.stem for p in (Path(BASE_DIR) / "static" / "flags").glob("*.png")
}
_club_logos_path = Path(BASE_DIR) / "data" / "club_logos.json"
CLUB_LOGO_MAP: dict[str, str] = (
    _json.loads(_club_logos_path.read_text()) if _club_logos_path.exists() else {}
)

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


@app.route("/sw.js")
@limiter.exempt
def service_worker():
    # Served from the root path (not /static/sw.js) so it can be registered
    # with scope "/" — a service worker's max allowed scope is its own
    # directory, and the game (now living at "/", see the game() route
    # below) is the only page meant to be controlled by it — see sw.js's own
    # fetch handler for how it stays out of "/combos" and "/squad-guesser"'s
    # way despite the broad scope.
    response = app.send_static_file("sw.js")
    response.headers["Cache-Control"] = "no-cache"
    return response


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


# League categories (see category_config.py's LEAGUE_CATEGORIES/
# FOREIGN_LEAGUE_CATEGORIES) get their league's home country's flag —
# there's no separate "league crest" artwork, but a flag is an equally
# unambiguous visual anchor and the images are already downloaded (see
# fetch_flags.py). German name, matching src/countries.py's COUNTRY_BY_NAME
# keys (Transfermarkt's own nationality strings).
_LEAGUE_COUNTRY: dict[str, str] = {
    "league_buli": "Deutschland", "league_pl": "England", "league_laliga": "Spanien",
    "league_seriea": "Italien", "league_bra": "Brasilien", "league_arg": "Argentinien",
    "league_ksa": "Saudi-Arabien", "league_ere": "Niederlande", "league_jup": "Japan",
}

# The standard German two-letter shorthand for each position — same
# convention as an actual team sheet, so the badge reads as real football
# notation rather than an arbitrary abbreviation. Any position id not
# listed (a future addition to category_config.py) still gets a badge, just
# with its label's first two letters instead — see _cat_display.
_POSITION_BADGE: dict[str, str] = {
    "pos_gk": "TW",
    "pos_def": "AB", "pos_cb": "IV", "pos_lb": "LV", "pos_rb": "RV", "pos_sw": "LI",
    "pos_mid": "MF", "pos_cm": "ZM", "pos_dm": "DM", "pos_am": "OM", "pos_rm": "RM", "pos_lm": "LM",
    "pos_fwd": "ST", "pos_st": "MS", "pos_lw": "LA", "pos_rw": "RA", "pos_ss": "HS",
}
# Traditional position-group colors (goalkeeper gold, defense blue, midfield
# green, attack red) — every id above maps to exactly one group; anything
# missing falls back to _club_badge_color's per-id hash instead of guessing
# a group for it.
_POSITION_GROUP_COLOR: dict[str, str] = {
    **{pid: "hsl(45, 70%, 38%)" for pid in ("pos_gk",)},
    **{pid: "hsl(210, 55%, 38%)" for pid in ("pos_def", "pos_cb", "pos_lb", "pos_rb", "pos_sw")},
    **{pid: "hsl(140, 45%, 32%)" for pid in ("pos_mid", "pos_cm", "pos_dm", "pos_am", "pos_rm", "pos_lm")},
    **{pid: "hsl(4, 65%, 42%)" for pid in ("pos_fwd", "pos_st", "pos_lw", "pos_rw", "pos_ss")},
}


def _club_badge_color(cat_id: str) -> str:
    """A deterministic color for a badge with no more specific color rule of
    its own, derived from the category id so the same one always gets the
    same color across requests/sessions."""
    digest = hashlib.sha1(cat_id.encode("utf-8")).hexdigest()
    hue = int(digest[:4], 16) % 360
    return f"hsl({hue}, 55%, 38%)"


def _cat_display(cat) -> dict:
    # Every icon here is either a real downloaded image (a club crest or
    # national/league flag — see fetch_flags.py/fetch_club_logos.py), a
    # colored badge showing real text (a club/position abbreviation, or the
    # specific letter an initial/contains-letter category is actually
    # about), or one of a small shared set of line icons (ICON_PATHS in
    # game.js) — never a system emoji, which renders in fixed,
    # uncontrollable multi-color glyphs that clash with the rest of the
    # flat, single-accent design language. Resolved by category *type*, not
    # a hand-maintained per-id dict — the old id-keyed dict this replaced
    # was already 9 entries short and 8 stale at just 111 categories, which
    # cannot scale to the ~7,000 categories generated dynamically today.
    display = {
        "id": cat.id,
        "label": cat.label,
        "type": cat.type.value,
        "difficulty": cat.difficulty,
    }

    if cat.type == CategoryType.CLUB:
        logo_file = CLUB_LOGO_MAP.get(getattr(cat, "club_name", None))
        if logo_file:
            display["icon_image"] = f"/static/club_logos/{logo_file}"
        else:
            display["icon_letter"] = (cat.label[:1] or "?").upper()
            display["icon_color"] = _club_badge_color(cat.id)
        return display

    if cat.type in (CategoryType.NATIONALITY, CategoryType.LEAGUE):
        country_name = (
            getattr(cat, "nationality", None) if cat.type == CategoryType.NATIONALITY
            else _LEAGUE_COUNTRY.get(cat.id)
        )
        flag_code = country_flag_image_code(country_name) if country_name else None
        if flag_code and flag_code in _FLAG_CODES_AVAILABLE:
            display["icon_image"] = f"/static/flags/{flag_code}.png"
        else:
            # No real flag image (a nationality Transfermarkt records that
            # isn't in src/countries.py's list yet, a dissolved state with
            # no current flag, or one of the smaller foreign leagues) —
            # generic globe rather than guessing at a per-country glyph.
            display["icon"] = "globe"
        return display

    if cat.type == CategoryType.CONTINENT:
        display["icon"] = "globe"
    elif cat.type == CategoryType.AGE:
        display["icon"] = "calendar"
    elif cat.type == CategoryType.MARKET_VALUE:
        display["icon"] = "€"  # a plain currency symbol, not emoji — renders as ordinary text in any font
    elif cat.type == CategoryType.AWARD:
        display["icon"] = "trophy"
    elif cat.type == CategoryType.POSITION:
        display["icon_letter"] = _POSITION_BADGE.get(cat.id, (cat.label[:2] or "?").upper())
        display["icon_color"] = _POSITION_GROUP_COLOR.get(cat.id, _club_badge_color(cat.id))
    elif cat.type in (CategoryType.INITIAL, CategoryType.CONTAINS_LETTER):
        letter = getattr(cat, "letter", None) or (cat.label[-1] if cat.label else "?")
        display["icon_letter"] = letter.upper()
        display["icon_color"] = _club_badge_color(cat.id)
    elif cat.type == CategoryType.TEAMMATE:
        # No player-photo field exists anywhere in the dataset (see
        # src/db.py's players schema) — same "no real per-entity image"
        # situation as AGE/MARKET_VALUE/AWARD above, so this falls back to
        # a shared line icon rather than a per-anchor image.
        display["icon"] = "users"
    # Any other type (there isn't one today — every CategoryType is handled
    # above) gets no icon key at all; the client's own fallback (a plain SVG
    # ball, see categoryIconHtml in game.js) takes over.
    return display


# Clubs are "narrow-and-numerous": with ~6,500 dynamic clubs in the pool,
# two *random* clubs rarely share a transferred player — reliable club x
# club overlap there was a property of the old, small, hand-picked lists,
# not something that holds at this scale. Uniformly sampling 6 categories
# from a pool this lopsided also risked landing on zero clubs at all (e.g.
# an all-nationality/trophy/letter grid) despite "Alle Ligen" being the
# whole-catalog club mode. GENERAL_MIN_CLUBS fixes both: 3 real clubs
# confined to one whole side of the grid (see
# _sample_general_puzzle_categories) — every cell involving them ends up
# club x broad (the reliable pairing type), never club x club, and — since
# neither side ever faces another member of itself — the broad side needs
# no internal grouping either: a nationality x nationality or trophy x
# trophy cell simply can't happen when both land on the same side.
GENERAL_MIN_CLUBS = 3

# On top of the confined 3, one more club is mixed into the *other* side —
# unlike the confined 3, this one does face them in 3 club x club cells, so
# it's only ever picked from clubs that individually clear bounds against
# all 3 (same construction as the broad side below). GENERAL_MIN_CLUBS +
# GENERAL_EXTRA_CLUBS = 4 real clubs per puzzle, same floor league mode
# already guarantees.
GENERAL_EXTRA_CLUBS = 1

# See _sample_general_puzzle_categories: at most this many of the 3 broad
# slots may be AWARD (trophy) categories — a trophy category individually
# clears bounds just fine, but "played for this club AND won that specific
# trophy" is a much narrower, more hyper-specific kind of fact than
# "played for this club AND holds this nationality/position/age", and
# trophies (~490 of ~620 broad categories) would otherwise dominate random
# sampling by sheer count.
GENERAL_MAX_AWARD = 1

# Same reasoning as GENERAL_MAX_AWARD, applied to TEAMMATE ("played with
# X") categories: "played for this club AND was a teammate of this one
# specific famous player" is just as narrow/hyper-specific a fact as a
# trophy pairing, so it gets its own independent cap rather than sharing
# AWARD's budget (a puzzle could otherwise land one trophy cell and one
# teammate cell, still narrow overall).
GENERAL_MAX_TEAMMATE = 1

# League-scoped puzzles (see _resolve_pool/LEAGUE_POOLS): the whole point of
# picking a league is to see that league's own clubs. Unlike the general
# pool above, two clubs *within the same league* commonly do share a
# transferred player, so league mode allows clubs mixed freely across both
# sides rather than confining them to one (see _sample_league_puzzle_categories).
#
# The exact club count is picked once per puzzle from LEAGUE_CLUB_LAYOUTS
# below, not re-randomized on every retry attempt inside the sampler. That
# was the original design (a random 4-6 draw per attempt) and it looked
# varied on paper but wasn't in practice: a broad category ANDed with
# "played in this league" has a much thinner player pool than a plain club
# category, so broad-inclusive attempts fail the caller's min/max_players
# bounds check far more often and get discarded, while all-club attempts (6
# clubs, zero broad) succeed almost immediately and dominate the returned
# puzzles by sheer speed, not genuine randomness — empirically puzzles were
# all-club ~17/18 times sampled. Committing to one target club count for the
# whole retry loop (only the specific clubs/categories get re-rolled each
# attempt, not the shape) removes that bias: a "3 clubs" puzzle keeps
# retrying as a 3-club puzzle until it clears bounds, or the caller's
# fallback ladder loosens min/max_players instead.
LEAGUE_MIN_CLUBS = 3

# Layouts range from 3 clubs (half the grid broad) up to 6 (every cell a
# club) — not lower than 3: the grid splits 3-and-3 across two sides, and
# _sample_league_puzzle_categories keeps same-typed broad categories (all
# nationality, or all trophy) together as one group on a single side, so
# more than 3 broad slots risks a group that structurally can't fit either
# side. One layout is picked per puzzle via random.choice, so some puzzles
# are club-heavy and some are more mixed, instead of every puzzle having the
# identical shape.
LEAGUE_CLUB_LAYOUTS = (3, 4, 5, 6)


def _sample_general_puzzle_categories(
    clubs: list, broad: list, db: sqlite3.Connection, min_players: int, max_players: int, rng=random
) -> tuple[list, list] | None:
    """Non-league mode ("Alle Ligen"): GENERAL_MIN_CLUBS (3) real clubs,
    confined to one whole side of the grid, plus GENERAL_EXTRA_CLUBS (1)
    more mixed into the other side — 4 real clubs total, same floor league
    mode already guarantees. See GENERAL_MIN_CLUBS/GENERAL_EXTRA_CLUBS above
    for why the confined 3 stay fixed and kept to one side (unlike league
    mode's variable, fully-mixed 4-6) while the 4th is treated more like a
    broad category: picked only if it individually clears bounds against
    the confined 3 (3 more club x club cells), and why the rest of the
    "broad" side still needs no internal grouping.

    Unlike every other sampler here, this one checks eligible-player bounds
    itself (via the `db`/`min_players`/`max_players` params) instead of
    leaving that to the caller's blind sample-then-check retry loop. A
    league's ~20-30 clubs all share a broadly similar player pool (that
    league's regulars), so any club paired with any broad category is
    usually fine; three *random* prominent clubs pulled from the whole
    catalog (up to Bayern München next to Kaizer Chiefs) often have almost
    no roster overlap with a specific one of ~600 broad categories (or each
    other) at all — empirically, blind uniform sampling here only cleared
    bounds on ~0.1-8% of attempts depending on difficulty, instead of the
    ~90%+ every other sampler gets. Restricting the draw to only categories
    that already clear bounds against the confined 3 turns that into a
    ~100%-single-attempt success rate for the broad side (~45-99% for the
    extra club, depending on difficulty — still ~100% within the caller's
    per-tier attempt budget) for a bit of upfront filtering (a few thousand
    cached set intersections, single-digit milliseconds) instead of
    hundreds of wasted blind retries.

    `rng` defaults to the `random` module itself; passing a seeded
    `random.Random(seed)` instance instead (same method surface: shuffle/
    sample/randint/random) makes generation fully deterministic without
    touching global random state — used by the daily grid (see
    app.py's /api/daily/today) so everyone gets the identical puzzle on a
    given day, and concurrent requests never race on shared global state.
    """
    if len(clubs) < GENERAL_MIN_CLUBS + GENERAL_EXTRA_CLUBS:
        return None
    chosen_clubs = rng.sample(clubs, GENERAL_MIN_CLUBS)
    club_id_sets = [c.eligible_player_ids(db) for c in chosen_clubs]

    remaining_clubs = [c for c in clubs if c not in chosen_clubs]
    extra_club_candidates = [
        c for c in remaining_clubs
        if all(min_players <= len(ids & c.eligible_player_ids(db)) <= max_players for ids in club_id_sets)
    ]
    if len(extra_club_candidates) < GENERAL_EXTRA_CLUBS:
        return None
    extra_clubs = rng.sample(extra_club_candidates, GENERAL_EXTRA_CLUBS)

    candidate_broad = [
        b for b in broad
        if all(min_players <= len(ids & b.eligible_player_ids(db)) <= max_players for ids in club_id_sets)
    ]

    # AWARD (trophy) categories that individually clear bounds can still
    # make an unfair puzzle together: "played for this obscure club AND
    # won that specific trophy" asks for one exact, hyper-specific
    # transfer-history fact rather than a broadly guessable attribute
    # (nationality/position/age/...) — two or three of those stacked in
    # one puzzle is what "way too hard" complaints actually turned out to
    # be about even after GENERAL_MIN_CLUBS guaranteed real clubs. Capping
    # how many of the remaining broad slots can be trophies keeps most
    # cells paired against a structural category instead, without banning
    # trophies outright (a rare Ballon d'Or category, on its own, is still
    # a fair hard question).
    n_broad_slots = 3 - GENERAL_EXTRA_CLUBS
    award_candidates = [c for c in candidate_broad if c.type == CategoryType.AWARD]
    teammate_candidates = [c for c in candidate_broad if c.type == CategoryType.TEAMMATE]
    other_candidates = [c for c in candidate_broad if c.type not in (CategoryType.AWARD, CategoryType.TEAMMATE)]
    max_award = min(GENERAL_MAX_AWARD, len(award_candidates))
    n_award = rng.randint(0, max_award) if max_award > 0 else 0
    max_teammate = min(GENERAL_MAX_TEAMMATE, len(teammate_candidates), n_broad_slots - n_award)
    n_teammate = rng.randint(0, max_teammate) if max_teammate > 0 else 0
    # Capped at GENERAL_MAX_AWARD/GENERAL_MAX_TEAMMATE unconditionally —
    # never topped up beyond either even if other_candidates falls short of
    # filling the remaining slots (that shortfall means this club triple
    # just doesn't have enough valid categories under the caps; return None
    # and let the caller retry with a fresh club triple instead of silently
    # exceeding a cap).
    n_other = min(len(other_candidates), n_broad_slots - n_award - n_teammate)
    if n_award + n_teammate + n_other < n_broad_slots:
        return None

    chosen_broad = (
        extra_clubs
        + rng.sample(award_candidates, n_award)
        + rng.sample(teammate_candidates, n_teammate)
        + rng.sample(other_candidates, n_other)
    )
    rng.shuffle(chosen_clubs)
    rng.shuffle(chosen_broad)
    return (chosen_clubs, chosen_broad) if rng.random() < 0.5 else (chosen_broad, chosen_clubs)


def _sample_league_puzzle_categories(league_clubs: list, broad: list, n_clubs_target: int, rng=random) -> tuple[list, list] | None:
    """League mode: `n_clubs_target` real clubs from the selected league
    among the 6 categories (the caller picks this once per puzzle from
    LEAGUE_CLUB_LAYOUTS, see there for why it's fixed per-call rather than
    re-randomized here) — but, unlike the general sparse-type cap, mixed
    freely across rows/cols rather than confined to one whole side. Within a
    single league, two clubs are far more likely to share a transferred
    player than two random clubs from the entire catalog (moves within the
    same league are common), so club x club cells are safe to allow here —
    keeping clubs pinned to one solid side every time made every league
    puzzle the same rigid shape ("league's clubs" vs "everything else").
    Non-club categories fill the rest, trophies included — a trophy doesn't
    need to be specific to the selected league (e.g. "Ballon d'Or" showing up
    in a Bundesliga puzzle is fine). The thinness risk of a rare trophy ANDed
    with "played in this league" is handled structurally rather than by
    exclusion: at most 3 broad slots exist per puzzle (LEAGUE_CLUB_LAYOUTS'
    floor of 3 clubs), the trophy group is kept whole on one side (below) so
    trophy x trophy cells never occur, and the caller's bounds check + retry
    loop rejects any sample that comes out too thin anyway. TEAMMATE
    categories carry the same (in fact sharper) thinness risk once wrapped
    in LeagueScopedCategory — "was a teammate of this one specific player"
    AND "was a teammate of that other specific player" AND "played in this
    league" starts from an already-small pool and intersects it twice —
    confirmed empirically: Bundesliga generation failed ~3/8 attempts with
    two TEAMMATE categories landing on opposite sides, 0/8 once grouped the
    same way as nat/trophy below.
    """
    n_clubs = min(n_clubs_target, len(league_clubs))
    if n_clubs <= 0:
        return None
    n_broad = 6 - n_clubs
    if len(broad) < n_broad:
        n_broad = len(broad)
        n_clubs = min(len(league_clubs), 6 - n_broad)
        if n_clubs <= 0:
            return None

    chosen_clubs = rng.sample(league_clubs, n_clubs)
    chosen_broad = rng.sample(broad, n_broad)
    nat = [c for c in chosen_broad if c.type == CategoryType.NATIONALITY]
    award = [c for c in chosen_broad if c.type == CategoryType.AWARD]
    teammate = [c for c in chosen_broad if c.type == CategoryType.TEAMMATE]
    other = [c for c in chosen_broad if c.type not in (CategoryType.NATIONALITY, CategoryType.AWARD, CategoryType.TEAMMATE)]

    # Clubs and non-nationality/non-trophy/non-teammate categories can be
    # placed individually (a club x club or club x nationality cell is a
    # normal, fine question); the nationality/trophy/teammate groups, if
    # they have more than one member, must each stay whole on one side,
    # unlike the general pool's _sample_general_puzzle_categories (which
    # needs no such grouping at all — see its docstring for why).
    singles = chosen_clubs + other
    rng.shuffle(singles)
    side_a: list = []
    side_b: list = []
    for group in (nat, award, teammate, *([c] for c in singles)):
        (side_a if len(side_a) + len(group) <= 3 else side_b).extend(group)

    rng.shuffle(side_a)
    rng.shuffle(side_b)
    return (side_a, side_b) if rng.random() < 0.5 else (side_b, side_a)


def _generate_puzzle(db: sqlite3.Connection, max_difficulty: int = 3, min_players: int = 5, max_players: int = 9999, max_attempts: int = 300, pool: list | None = None, min_league_clubs: int = 0, rng=random):
    if pool is None:
        pool = ALL_CATEGORIES
    pool = [cat for cat in pool if cat.difficulty <= max_difficulty]
    if len(pool) < 6:
        return None, None

    # cat.eligible_player_ids(db) is cached on the category instance itself
    # (see src/categories.py) and only ever computed for categories that
    # actually get sampled — with ~7,000 dynamically generated categories in
    # the pool, eagerly computing it for all of them up front would make
    # every /api/game/new request pay for categories that never get drawn.
    if min_league_clubs > 0:
        league_clubs = [c for c in pool if c.type == CategoryType.CLUB]
        # LEAGUE/CONTINENT stay excluded (already-scoped clubs make a
        # "played in league X" or "played on continent Y" cell tautological
        # or irrelevant); AWARD (trophies) is allowed — see
        # _sample_league_puzzle_categories' docstring.
        broad = [c for c in pool if c.type not in (CategoryType.CLUB, CategoryType.LEAGUE, CategoryType.CONTINENT)]
        # Picked once for the whole retry loop, not re-rolled per attempt —
        # see LEAGUE_CLUB_LAYOUTS for why re-rolling the shape every attempt
        # defeated the point of having several of them.
        layouts = [n for n in LEAGUE_CLUB_LAYOUTS if n >= min_league_clubs]
        n_clubs_target = rng.choice(layouts or [min_league_clubs])
        for _ in range(max_attempts):
            sampled = _sample_league_puzzle_categories(league_clubs, broad, n_clubs_target, rng=rng)
            if sampled is None:
                return None, None
            rows, cols = sampled
            counts = [len(r.eligible_player_ids(db) & c.eligible_player_ids(db)) for r in rows for c in cols]
            if all(min_players <= n <= max_players for n in counts):
                return rows, cols
        return None, None

    clubs = [c for c in pool if c.type == CategoryType.CLUB]
    if len(clubs) < GENERAL_MIN_CLUBS + GENERAL_EXTRA_CLUBS:
        return None, None
    broad = [c for c in pool if c.type != CategoryType.CLUB]
    for _ in range(max_attempts):
        # Bounds are already checked inside the sampler itself (see its
        # docstring for why) — unlike every other branch here, a None
        # result doesn't mean "structurally impossible", it means "this
        # particular random 3-club draw didn't pan out", so retry with a
        # fresh draw instead of aborting the whole loop.
        sampled = _sample_general_puzzle_categories(clubs, broad, db, min_players, max_players, rng=rng)
        if sampled is not None:
            return sampled
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
        # min_players=1 here (both tight tiers) is what let a puzzle land on
        # cells with literally one possible answer in the whole dataset —
        # "hard" should mean a genuinely narrow category, not a single
        # obscure fact with no other correct answer. GENERAL_MIN_CLUBS'
        # constructive sampler (see _sample_general_puzzle_categories)
        # comfortably sustains min_players=2 here at essentially the same
        # reliability as min_players=1 used to have; the loosest tier below
        # stays at 1 as the genuine last-resort safety net.
        dict(min_players=2,  max_players=20,   max_attempts=30),
        dict(min_players=2,  max_players=40,   max_attempts=30),
        dict(min_players=1,  max_players=9999, max_attempts=500),
    ],
}


def _generate_puzzle_for_difficulty(db: sqlite3.Connection, difficulty: int, pool: list | None = None, min_league_clubs: int = 0, rng=random):
    """Generate a puzzle for a clamped 1-3 difficulty, walking the fallback ladder.

    Shared by /api/game/new (solo + local), multiplayer room creation, and
    the daily grid so all draw puzzles with identical quality guarantees.
    `pool` defaults to the full category catalog; callers pass a narrower
    one to respect a league-scoped game mode (see _resolve_pool()).
    `min_league_clubs` > 0 switches to the league-priority sampler (see
    _sample_league_puzzle_categories). `rng` defaults to the `random`
    module; the daily grid passes a seeded `random.Random(...)` instead so
    the same date always produces the same puzzle (see _sample_puzzle_
    categories' docstring).
    """
    difficulty = min(3, max(1, difficulty))
    for cfg in _DIFFICULTY_FALLBACKS[difficulty]:
        rows, cols = _generate_puzzle(db, max_difficulty=difficulty, pool=pool, min_league_clubs=min_league_clubs, rng=rng, **cfg)
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
@limiter.limit(RATE_LIMIT_MODERATE)
def api_categories():
    """Server-side search over the category catalog — with ~6,500 clubs and
    ~490 trophies, shipping the full catalog to the browser up front isn't
    practical, so this mirrors the debounced-search pattern /api/game/search
    already uses for players. Backs the editor's category picker (see
    game.js); `type` is optional there (searching "Bayern" should find the
    club regardless of the user thinking in terms of category types), but
    still supported for a type-scoped browse."""
    cat_type = request.args.get("type", "").strip()
    query = _normalize(request.args.get("q", "").strip())
    try:
        limit = min(100, max(1, int(request.args.get("limit", 50))))
    except ValueError:
        limit = 50

    results = [c for c in ALL_CATEGORIES if c.type.value == cat_type] if cat_type else list(ALL_CATEGORIES)
    if query:
        results = [c for c in results if query in _normalize(c.label)]
    results.sort(key=lambda c: (c.difficulty, c.label))
    return jsonify({"categories": [_cat_display(c) for c in results[:limit]]})


@app.route("/")
@app.route("/<path:subpath>")
@limiter.exempt
def game(subpath=None):
    # Client-side router (see the "Router" section in static/js/game.js) owns
    # every URL under the site root (e.g. /setup/solo, /online/ABCDE) — the
    # server's only job is to serve the same shell for all of them so a
    # direct navigation or hard refresh doesn't 404. subpath itself is never
    # inspected; game.js reads location.pathname on load to decide what to
    # show. Werkzeug's routing prefers a more-static rule over this catch-all
    # for any URL that also matches one (/combos, /squad-guesser, /sw.js,
    # /api/..., /static/...), so those keep working unshadowed regardless of
    # declaration order — including api_not_found just below, which is more
    # specific than this route for anything under /api/ and keeps a typoed
    # or removed API endpoint a real 404 instead of a 200 full of HTML.
    return render_template("game.html")


@app.route("/api/<path:subpath>")
def api_not_found(subpath):
    # Without this, an unmatched /api/* request would fall through to the
    # game() catch-all above and get a 200 response full of HTML — the SPA
    # shell is a reasonable fallback for a mistyped *page* URL, but silently
    # handing a client expecting JSON an HTML document (rather than an error
    # it can actually detect) is a footgun, not a feature.
    abort(404)


@app.route("/api/game/new")
@limiter.limit(RATE_LIMIT_EXPENSIVE)
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
        return jsonify({"error": "Kein gültiges Grid gefunden"}), 500
    return jsonify({"rows": [_cat_display(c) for c in rows], "cols": [_cat_display(c) for c in cols]})


@app.route("/api/game/search")
@limiter.limit(RATE_LIMIT_MODERATE)
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
            f"SELECT p.id, p.name, p.current_club_name, p.nationality, p.age "
            f"FROM players p {where} ORDER BY p.name LIMIT 20",
            params,
        ).fetchall()
    finally:
        db.close()
    return jsonify({"players": [dict(r) for r in rows_db]})


@app.route("/api/game/solve")
@limiter.limit(RATE_LIMIT_MODERATE)
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
        # eligible_player_ids() is cached on each category instance (see
        # src/categories.py) — by the time a round ends, the exact row/col
        # categories being solved here already had it computed during
        # /api/game/new's generation, so this is a set intersection in
        # Python, not a fresh query. That replaces what used to be 9
        # separate SQL queries (one per cell, each re-scanning the players
        # table via row_sql AND col_sql) with at most 6 cached lookups plus
        # one query for the union of matching player ids — this is what
        # made the post-round solution reveal visibly lag (~0.5s).
        cell_id_sets = [
            [cats[row_id].eligible_player_ids(db) & cats[col_id].eligible_player_ids(db) for col_id in col_ids]
            for row_id in row_ids
        ]
        union_ids = set().union(*[ids for row in cell_id_sets for ids in row])

        players_by_id: dict[int, dict] = {}
        order: list[int] = []
        if union_ids:
            placeholders = ",".join("?" * len(union_ids))
            rows_db = db.execute(
                f"""SELECT p.id, p.name, p.current_club_name
                    FROM players p
                    WHERE p.id IN ({placeholders})
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
                list(union_ids),
            ).fetchall()
            players_by_id = {row["id"]: dict(row) for row in rows_db}
            order = [row["id"] for row in rows_db]

        grid = [
            [
                {"count": len(ids), "players": [players_by_id[pid] for pid in order if pid in ids]}
                for ids in row
            ]
            for row in cell_id_sets
        ]
    finally:
        db.close()
    return jsonify({"grid": grid})


@app.route("/api/game/validate", methods=["POST"])
@limiter.limit(RATE_LIMIT_MODERATE)
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


# ─── Daily Grid (daily curated grid + streak) ────────────────────────
# The "once per day" gate and streak itself live entirely client-side (see
# game.js), matching this app's existing trust model — nothing else here
# (stats, settings) has ever had server-verified per-user state, and
# real-world Wordle works the same way (localStorage-gated, not server-
# enforced). What the backend *does* guarantee is that everyone who opens
# the daily puzzle on the same UTC calendar day gets the exact same grid —
# that's the part that actually needs to be authoritative and shared.

DAILY_WEEKDAY_DIFFICULTY = 2
DAILY_WEEKEND_DIFFICULTY = 3  # Saturday/Sunday a bit harder, like a crossword


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@app.route("/api/daily/today")
def api_daily_today():
    date = _today_str()
    db = get_db()
    try:
        rows = cols = None
        existing = grid_store.get_daily_grid(db, date)
        if existing is not None:
            row_ids, col_ids = existing
            rows = [CATEGORY_BY_ID[i] for i in row_ids if i in CATEGORY_BY_ID]
            cols = [CATEGORY_BY_ID[i] for i in col_ids if i in CATEGORY_BY_ID]
            if len(rows) != 3 or len(cols) != 3:
                # A category the stored grid referenced no longer exists
                # (e.g. a club fell out of the prominence whitelist since) —
                # regenerate below rather than serve a broken puzzle.
                rows = cols = None

        if rows is None:
            weekday = datetime.now(timezone.utc).weekday()  # 0=Mon .. 6=Sun
            difficulty = DAILY_WEEKEND_DIFFICULTY if weekday >= 5 else DAILY_WEEKDAY_DIFFICULTY
            # Seeded by the date, not the global `random` module — every
            # request for the same date computes the identical puzzle, and
            # concurrent requests never race on shared global RNG state.
            rng = random.Random(f"daily-{date}")
            rows, cols = _generate_puzzle_for_difficulty(db, difficulty, pool=ALL_CATEGORIES, rng=rng)
            if rows is None:
                return jsonify({"error": "Kein gültiges Tagesrätsel gefunden"}), 500
            grid_store.store_daily_grid(db, date, [c.id for c in rows], [c.id for c in cols])
    finally:
        db.close()
    return jsonify({
        "date": date,
        "rows": [_cat_display(c) for c in rows],
        "cols": [_cat_display(c) for c in cols],
    })


# ─── Editor: build, save, and load custom grids by code ────────────────────

@app.route("/api/grids/preview")
@limiter.limit(RATE_LIMIT_MODERATE)
def api_grid_preview():
    """Live cell-count preview for the editor grid (see game.js's
    renderEditorGrid) — as the builder fills in row/col categories, each
    cell where both a row and a column are picked shows how many players
    would answer it, so thin/impossible combos are obvious before saving.
    Only counts are returned, never player names. Empty slots are sent as
    empty strings (not omitted) so the response stays aligned to the 3x3
    grid positions."""
    row_ids = (request.args.get("rows", "") or "").split(",")
    col_ids = (request.args.get("cols", "") or "").split(",")
    if len(row_ids) != 3 or len(col_ids) != 3:
        return jsonify({"error": "Need exactly 3 row and 3 col slots"}), 400

    db = get_db()
    try:
        row_players = [CATEGORY_BY_ID[i].eligible_player_ids(db) if i in CATEGORY_BY_ID else None for i in row_ids]
        col_players = [CATEGORY_BY_ID[i].eligible_player_ids(db) if i in CATEGORY_BY_ID else None for i in col_ids]
        counts = [
            [len(rp & cp) if rp is not None and cp is not None else None for cp in col_players]
            for rp in row_players
        ]
    finally:
        db.close()
    return jsonify({"counts": counts})


@app.route("/api/grids", methods=["POST"])
@limiter.limit(RATE_LIMIT_EXPENSIVE)
def api_create_grid():
    data = request.get_json(silent=True) or {}
    row_ids = data.get("row_ids") or []
    col_ids = data.get("col_ids") or []
    if (
        not isinstance(row_ids, list) or not isinstance(col_ids, list)
        or len(row_ids) != 3 or len(col_ids) != 3
    ):
        return jsonify({"error": "Genau 3 Zeilen- und 3 Spalten-Kategorien nötig"}), 400
    if len(set(row_ids)) != 3 or len(set(col_ids)) != 3 or set(row_ids) & set(col_ids):
        return jsonify({"error": "Kategorien dürfen sich nicht wiederholen"}), 400

    cats = {}
    for cid in row_ids + col_ids:
        cat = CATEGORY_BY_ID.get(cid)
        if cat is None:
            return jsonify({"error": f"Unbekannte Kategorie: {cid}"}), 400
        cats[cid] = cat

    db = get_db()
    try:
        # Every one of the 9 cells needs at least one real answer — reusing
        # the same eligible-player-id intersection the generator itself
        # relies on, so a shared code can never point at an unsolvable cell.
        empty_cells = []
        for r_id in row_ids:
            row_cat = cats[r_id]
            row_players = row_cat.eligible_player_ids(db)
            for c_id in col_ids:
                col_cat = cats[c_id]
                if not (row_players & col_cat.eligible_player_ids(db)):
                    empty_cells.append(f"{row_cat.label} × {col_cat.label}")
        if empty_cells:
            return jsonify({"error": "Diese Kombination hat leere Felder: " + ", ".join(empty_cells)}), 400

        code = grid_store.save_grid(db, row_ids, col_ids)
    finally:
        db.close()
    return jsonify({"code": code})


@app.route("/api/grids/<code>")
def api_get_grid(code):
    db = get_db()
    try:
        result = grid_store.get_saved_grid(db, code)
        if result is None:
            return jsonify({"error": "Grid nicht gefunden"}), 404
        row_ids, col_ids = result
        rows = [CATEGORY_BY_ID.get(i) for i in row_ids]
        cols = [CATEGORY_BY_ID.get(i) for i in col_ids]
        if None in rows or None in cols:
            return jsonify({"error": "Grid enthält veraltete Kategorien"}), 410
    finally:
        db.close()
    return jsonify({
        "code": code.upper(),
        "rows": [_cat_display(c) for c in rows],
        "cols": [_cat_display(c) for c in cols],
    })


# ─── Online 1v1 (multiplayer rooms) ────────────────────────────────────────
# Room state lives in-process (src/multiplayer.py) — the deployment must run
# a single worker process (see Dockerfile) since a second process would have
# its own, disjoint copy of the room dict.

@app.route("/api/multiplayer/rooms", methods=["POST"])
@limiter.limit(RATE_LIMIT_EXPENSIVE)
def api_mp_create_room():
    data = request.get_json(silent=True) or {}
    difficulty = min(3, max(1, int(data.get("difficulty", 3))))
    # The room creator's settings govern the whole room, exactly mirroring how
    # difficulty already works — the joiner never supplies their own.
    league = data.get("league") or None
    excluded_types = set(data.get("excludedTypes") or [])
    excluded_ids = set(data.get("excludedCategoryIds") or [])
    visibility = "public" if data.get("visibility") == "public" else "private"
    pool = _resolve_pool(excluded_types=excluded_types, excluded_ids=excluded_ids, league=league)

    db = get_db()
    try:
        rows, cols = _generate_puzzle_for_difficulty(
            db, difficulty, pool=pool, min_league_clubs=LEAGUE_MIN_CLUBS if league else 0
        )
    finally:
        db.close()
    if rows is None:
        return jsonify({"error": "Kein gültiges Grid gefunden"}), 500
    room, token = mp.create_room(
        rows, cols, difficulty=difficulty, league=league,
        excluded_types=frozenset(excluded_types), excluded_ids=frozenset(excluded_ids),
        visibility=visibility,
    )
    return jsonify({"code": room.code, "token": token, "slot": 1, "visibility": room.visibility})


@app.route("/api/multiplayer/rooms/<code>/join", methods=["POST"])
@limiter.limit(RATE_LIMIT_MODERATE)
def api_mp_join_room(code):
    result = mp.join_room(code)
    if result is None:
        status = 404 if mp.get_room(code) is None else 409
        return jsonify({"error": "Raum nicht gefunden oder bereits voll"}), status
    room, token = result
    return jsonify({"code": room.code, "token": token, "slot": 2})


@app.route("/api/multiplayer/lobbies")
def api_mp_lobbies():
    return jsonify({"rooms": [room.public_lobby_summary() for room in mp.list_public_rooms()]})


@app.route("/api/multiplayer/lobbies/events")
@limiter.limit(RATE_LIMIT_CONNECT)
def api_mp_lobbies_events():
    # Same version-diff SSE shape as a room's own /events (see
    # api_mp_room_events) — a browsing client just refetches /lobbies on any
    # message rather than trusting a payload here, so this only has to
    # signal "something changed", not carry the list itself.
    def stream():
        last_codes = None
        ticks = 0
        while True:
            codes = tuple(room.code for room in mp.list_public_rooms())
            if codes != last_codes:
                last_codes = codes
                yield f"data: {_json.dumps({'count': len(codes)})}\n\n"
            elif ticks % 15 == 0:
                yield ": ping\n\n"  # keep proxies/browsers from closing the idle connection
            ticks += 1
            time.sleep(1)
            # Not tied to a single room's own TTL check like api_mp_room_events
            # (this stream outlives any one room) — this is just a backstop so
            # a connection whose close a proxy swallows doesn't leak its
            # thread forever; the client's EventSource just reconnects.
            if ticks > mp.ROOM_TTL_SECONDS:
                break

    resp = Response(stream(), mimetype="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"  # disable reverse-proxy response buffering for SSE
    return resp


@app.route("/api/multiplayer/rooms/<code>/state")
def api_mp_room_state(code):
    room = mp.get_room(code)
    if room is None:
        return jsonify({"error": "Raum nicht gefunden"}), 404
    slot = mp.room_slot_for_token(room, request.args.get("token", ""))
    room.mark_seen(slot)
    return jsonify(room.public_state(viewer_slot=slot, cat_display_fn=_cat_display))


@app.route("/api/multiplayer/rooms/<code>/events")
@limiter.limit(RATE_LIMIT_CONNECT)
def api_mp_room_events(code):
    room = mp.get_room(code)
    if room is None:
        return jsonify({"error": "Raum nicht gefunden"}), 404
    slot = mp.room_slot_for_token(room, request.args.get("token", ""))

    def stream():
        last_version = -1
        ticks = 0
        room.mark_seen(slot)
        while True:
            # Driven by whichever player still has this connection open —
            # see check_opponent_disconnected's docstring for why a
            # disconnected player can't report their own absence. Any
            # forfeit it applies is picked up by the version-change check
            # right below.
            if slot is not None:
                room.check_opponent_disconnected(slot)
            if room.version != last_version:
                last_version = room.version
                yield f"data: {_json.dumps({'version': last_version})}\n\n"
            elif ticks % 15 == 0:
                yield ": ping\n\n"  # keep proxies/browsers from closing the idle connection
            ticks += 1
            room.mark_seen(slot)
            time.sleep(1)
            if room.is_stale():
                break

    resp = Response(stream(), mimetype="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"  # disable reverse-proxy response buffering for SSE
    return resp


@app.route("/api/multiplayer/rooms/<code>/moves", methods=["POST"])
@limiter.limit(RATE_LIMIT_MODERATE)
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
@limiter.limit(RATE_LIMIT_MODERATE)
def api_mp_forfeit(code):
    room = mp.get_room(code)
    if room is None:
        return jsonify({"error": "Raum nicht gefunden"}), 404
    data = request.get_json(silent=True) or {}
    ok = mp.forfeit(room, data.get("token", ""))
    return jsonify({"ok": ok})


@app.route("/api/multiplayer/rooms/<code>/rematch", methods=["POST"])
@limiter.limit(RATE_LIMIT_MODERATE)
def api_mp_rematch(code):
    # Either player can ask for a rematch, but the round only actually
    # resets once both have — request_rematch just records this player's
    # vote and tells us whether the other one already voted too.
    room = mp.get_room(code)
    if room is None:
        return jsonify({"error": "Raum nicht gefunden"}), 404
    data = request.get_json(silent=True) or {}
    slot = mp.room_slot_for_token(room, data.get("token", ""))
    if slot is None:
        return jsonify({"error": "Nicht in diesem Raum"}), 403
    if room.winner is None:
        return jsonify({"error": "Runde läuft noch"}), 409

    both_agreed = room.request_rematch(slot)
    if not both_agreed:
        return jsonify({"ok": True, "started": False})

    pool = _resolve_pool(excluded_types=set(room.excluded_types), excluded_ids=set(room.excluded_ids), league=room.league)
    db = get_db()
    try:
        rows, cols = _generate_puzzle_for_difficulty(
            db, room.difficulty, pool=pool, min_league_clubs=LEAGUE_MIN_CLUBS if room.league else 0
        )
    finally:
        db.close()
    if rows is None:
        return jsonify({"error": "Kein gültiges Grid gefunden"}), 500

    mp.reset_room(room, rows, cols)
    return jsonify({"ok": True, "started": True})


@app.route("/squad-guesser")
@limiter.exempt
def squad_guesser():
    return render_template("squad_guesser.html")


@app.route("/api/squad-guesser/game")
@limiter.limit(RATE_LIMIT_MODERATE)
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
@limiter.exempt
def combos():
    return render_template("combos.html")


@app.route("/api/clubs/combos")
@limiter.limit(RATE_LIMIT_EXPENSIVE)
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


@app.route("/datenschutz")
@limiter.exempt
def datenschutz():
    return render_template("datenschutz.html")


@app.route("/impressum")
@limiter.exempt
def impressum():
    return render_template("impressum.html")


# ─── Error handling ─────────────────────────────────────────────────────────
# Two handlers, deliberately not one: HTTPException (404, 405, a route's own
# abort(400), ...) is expected, routine traffic — no logging beyond gunicorn's
# own access log. A bare Exception reaching here is always a bug (every
# anticipated failure in this codebase already returns its own error
# response instead of raising) — that one gets logged with its full
# traceback server-side and a generic message to the client, never the
# traceback itself. Both render an HTML page for a normal page request and
# JSON for anything under /api/, matching how the rest of the app already
# splits those two response styles.
#
# Neither handler runs at all while FLASK_DEBUG=1: Flask's own
# PROPAGATE_EXCEPTIONS default (True whenever app.debug is True) lets
# exceptions surface to Werkzeug's interactive debugger instead, which is
# what local development actually wants. This only takes over once that's
# off, i.e. exactly the "FLASK_DEBUG left on in production" case this exists
# to make impossible to observe from the outside.
def _wants_json() -> bool:
    return request.path.startswith("/api/")


# German titles/messages for the handful of HTTPExceptions either a real
# visitor or an API client could plausibly hit on this German-language site
# — everything else falls back to Werkzeug's own (English) e.name/
# e.description rather than transcribing its entire exception catalog for
# codes nobody here will ever actually see. 429 specifically also keeps
# flask-limiter's own e.description (e.g. "15 per 1 minute") out of the
# response — that's the exact limit a client would need to time an
# abuse-flavored retry around, not something worth handing over.
_HTTP_ERROR_DE: dict[int, tuple[str, str]] = {
    404: ("Seite nicht gefunden", "Die aufgerufene Seite existiert nicht (mehr)."),
    405: ("Methode nicht erlaubt", "Diese Aktion ist für diese Seite nicht vorgesehen."),
    429: ("Zu viele Anfragen", "Bitte versuche es in Kürze erneut."),
}


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    title, message = _HTTP_ERROR_DE.get(e.code, (e.name, e.description))
    if _wants_json():
        return jsonify({"error": message or title}), e.code
    return render_template("error.html", code=e.code, title=title, message=message), e.code


@app.errorhandler(Exception)
def handle_unexpected_exception(e: Exception):
    app.logger.exception("Unhandled exception on %s %s", request.method, request.path)
    if _wants_json():
        return jsonify({"error": "Internal server error"}), 500
    return render_template(
        "error.html", code=500, title="Etwas ist schiefgelaufen",
        message="Bitte lade die Seite neu oder versuche es später erneut.",
    ), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    # threaded=True: the multiplayer SSE stream is a long-lived connection —
    # without it the single-threaded dev server can't also serve moves/state
    # requests while a room's event stream is open.
    app.run(debug=debug, host="0.0.0.0", port=port, threaded=True)
