"""Builds Club/Nationality/Trophy categories dynamically from the real
dataset instead of a small hand-curated list, so puzzle generation can draw
on ~6,000 clubs, ~150 nationalities, and ~490 trophies instead of the
original 31/19/11.

Difficulty (1-3) is derived directly from how many distinct players satisfy
a category — the same "how rare is this" idea the hand-curated categories
already used, just applied uniformly and automatically instead of by hand
per entry. This is what the user meant by "add this as difficulties" when
asked how permissive the auto-generated pool should be.

Called once at app startup (see app.py) — building the whole catalog is a
low-single-digit-second one-time cost, not something to repeat per request.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field

from .categories import Category, ClubCategory, NationalityCategory, TrophyCategory
from .countries import COUNTRY_BY_NAME, country_flag, parse_nationality_tokens
from .trophy_rules import classify_trophy_title

# ─── Clubs ──────────────────────────────────────────────────────────────────

# Transfermarkt status placeholders that show up as "club names" in
# career_stints — not real clubs. Karriereende alone covers 27,611 players.
CLUB_STATUS_DENYLIST = {"Karriereende", "Vereinslos", "Unbekannt", "pausiert"}

# ~21% of distinct club_name values in the real data are youth-academy squads
# (U15-U23, "Jugend") rather than senior first teams — confusing/uninteresting
# as a trivia category (e.g. "Inter U19" has 415 distinct players on its own).
_YOUTH_CLUB_PATTERN = re.compile(
    r"(?:^|\s)U1[5-9](?:$|\s)|(?:^|\s)U2[0-3](?:$|\s)|Jgd\.|Jugend|Junioren",
    re.IGNORECASE,
)

# (minimum distinct players, difficulty) — checked in order, first match wins.
# Below the lowest threshold, a club/nationality is dropped entirely rather
# than forced into difficulty 3 (an answer pool of 1-4 players is too thin
# to be a fair puzzle even on hard). Trophies get no such floor (see below):
# a rare trophy is still a legitimate, checkable fact, just a hard one.
CLUB_TIER_THRESHOLDS = [(50, 1), (20, 2), (5, 3)]
NATIONALITY_TIER_THRESHOLDS = [(100, 1), (50, 2), (20, 3)]
TROPHY_TIER_THRESHOLDS = [(100, 1), (20, 2), (1, 3)]


def _is_junk_club(name: str) -> bool:
    return name in CLUB_STATUS_DENYLIST or bool(_YOUTH_CLUB_PATTERN.search(name))


def _tier_difficulty(count: int, thresholds: list[tuple[int, int]]) -> int | None:
    for min_count, difficulty in thresholds:
        if count >= min_count:
            return difficulty
    return None


def _slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return slug or "x"


def _stable_id(prefix: str, name: str) -> str:
    """A dynamic-category id that's stable across app restarts (so a user's
    excluded-category-id setting keeps working) without needing a database
    of previously-issued ids: slug + a short hash of the exact name, so two
    different names that happen to slugify the same way don't collide."""
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:6]
    return f"{prefix}_dyn_{_slugify(name)}-{digest}"


# Preserves the ids (and, for nationalities, the nicer adjective-form labels)
# of the ~60 categories that were hand-curated before dynamic generation
# existed, so anyone who already excluded e.g. "club_bay" in their settings
# doesn't have that setting silently stop working. Difficulty is NOT carried
# over from the old hand-picked values — every entry, legacy or new, gets
# its difficulty recomputed from the same tier thresholds as everything else,
# so there's one consistent rule rather than old ad-hoc judgment calls
# coexisting with the new automatic ones.
LEGACY_CLUB_IDS: dict[str, str] = {
    "Bayern München": "club_bay", "Bor. Dortmund": "club_bvb", "B. Leverkusen": "club_b04",
    "RB Leipzig": "club_rbl", "E. Frankfurt": "club_sge", "FC Schalke 04": "club_s04",
    "Hamburger SV": "club_hsv", "Werder Bremen": "club_svw", "FC Augsburg": "club_aug",
    "VfL Wolfsburg": "club_wob", "VfB Stuttgart": "club_stu", "SC Freiburg": "club_frb",
    "Bor. M'gladbach": "club_bmg", "1.FC Köln": "club_koe", "Manchester Utd.": "club_mnu",
    # The old hand-curated club_mci category used the match string "Manchester
    # City", but the real data (and the league club-name lists) uses "Man
    # City" — the old category silently matched zero players. Mapping the
    # legacy id to the real string fixes it rather than just carrying the bug
    # forward.
    "Man City": "club_mci", "Liverpool": "club_lfc", "Arsenal": "club_ars",
    "Chelsea": "club_che", "Tottenham": "club_tot", "Real Madrid": "club_rma",
    "FC Barcelona": "club_fcb", "Atlético Madrid": "club_atm", "FC Sevilla": "club_sev",
    "Juventus": "club_juv", "Inter": "club_int", "Milan": "club_mil", "Paris SG": "club_psg",
    "Ajax": "club_ajx", "PSV": "club_psv", "SV Eintracht Trier": "club_sve",
}

LEGACY_NATIONALITY_ENTRIES: dict[str, tuple[str, str]] = {
    # name -> (id, label)
    "England": ("nat_eng", "Englisch"), "Spanien": ("nat_esp", "Spanisch"),
    "Italien": ("nat_ita", "Italienisch"), "Frankreich": ("nat_fra", "Französisch"),
    "Deutschland": ("nat_ger", "Deutsch"), "Brasilien": ("nat_bra", "Brasilianisch"),
    "Argentinien": ("nat_arg", "Argentinisch"), "Niederlande": ("nat_ned", "Niederländisch"),
    "Portugal": ("nat_por", "Portugiesisch"), "Kroatien": ("nat_hrv", "Kroatisch"),
    "Belgien": ("nat_bel", "Belgisch"), "Dänemark": ("nat_dnk", "Dänisch"),
    "Schweden": ("nat_swe", "Schwedisch"), "Türkei": ("nat_tur", "Türkisch"),
    "Österreich": ("nat_aut", "Österreichisch"), "Polen": ("nat_pol", "Polnisch"),
    "Schottland": ("nat_sco", "Schottisch"), "Schweiz": ("nat_sui", "Schweizerisch"),
    "Wales": ("nat_wal", "Walisisch"),
}

LEGACY_TROPHY_IDS: dict[str, str] = {
    "Gewinner Ballon d'Or": "trophy_ballon", "Weltmeister": "trophy_world_cup",
    "UEFA Champions League-Sieger": "trophy_cl", "Spanischer Meister": "trophy_liga",
    "Französischer Meister": "trophy_ligue1", "Copa América-Sieger": "trophy_copa",
    "FIFA-Klub-Weltmeister": "trophy_fifa_cwc", "MLS Cup Champion": "trophy_mls_cup",
    "U20-Weltmeister": "trophy_u20", "Olympiasieger": "trophy_olympic",
    "Leagues-Cup-Sieger": "trophy_leagues_cup",
}


def build_dynamic_clubs(conn: sqlite3.Connection) -> list[ClubCategory]:
    rows = conn.execute(
        "SELECT club_name, COUNT(DISTINCT player_id) AS n FROM career_stints GROUP BY club_name"
    ).fetchall()
    categories = []
    for club_name, n in rows:
        if _is_junk_club(club_name):
            continue
        difficulty = _tier_difficulty(n, CLUB_TIER_THRESHOLDS)
        if difficulty is None:
            continue
        cat_id = LEGACY_CLUB_IDS.get(club_name) or _stable_id("club", club_name)
        categories.append(ClubCategory(cat_id, club_name, club_name, difficulty=difficulty))
    return categories


def build_dynamic_nationalities(conn: sqlite3.Connection) -> list[NationalityCategory]:
    rows = conn.execute(
        "SELECT nationality, COUNT(*) AS n FROM players WHERE nationality IS NOT NULL AND nationality != '' GROUP BY nationality"
    ).fetchall()
    counts: dict[str, int] = {}
    for raw, n in rows:
        for token in parse_nationality_tokens(raw):
            counts[token] = counts.get(token, 0) + n

    categories = []
    for name, n in counts.items():
        if name not in COUNTRY_BY_NAME:
            continue
        difficulty = _tier_difficulty(n, NATIONALITY_TIER_THRESHOLDS)
        if difficulty is None:
            continue
        legacy = LEGACY_NATIONALITY_ENTRIES.get(name)
        cat_id = legacy[0] if legacy else f"nat_dyn_{COUNTRY_BY_NAME[name].iso_code.lower()}"
        label = legacy[1] if legacy else name
        categories.append(
            NationalityCategory(cat_id, label, name, icon=country_flag(name), difficulty=difficulty)
        )
    return categories


def build_dynamic_trophies(conn: sqlite3.Connection) -> list[TrophyCategory]:
    rows = conn.execute("SELECT title, COUNT(*) AS n FROM player_trophies GROUP BY title").fetchall()
    categories = []
    for title, n in rows:
        if not classify_trophy_title(title):
            continue
        difficulty = _tier_difficulty(n, TROPHY_TIER_THRESHOLDS)
        if difficulty is None:
            continue
        cat_id = LEGACY_TROPHY_IDS.get(title) or _stable_id("trophy", title)
        categories.append(TrophyCategory(cat_id, title, title, difficulty=difficulty))
    return categories


@dataclass
class DynamicCatalog:
    clubs: list[ClubCategory] = field(default_factory=list)
    nationalities: list[NationalityCategory] = field(default_factory=list)
    trophies: list[TrophyCategory] = field(default_factory=list)

    def all(self) -> list[Category]:
        return [*self.clubs, *self.nationalities, *self.trophies]


def build_all(conn: sqlite3.Connection) -> DynamicCatalog:
    return DynamicCatalog(
        clubs=build_dynamic_clubs(conn),
        nationalities=build_dynamic_nationalities(conn),
        trophies=build_dynamic_trophies(conn),
    )


def build_league_pools(league_categories: list, all_categories: list[Category], catalog: DynamicCatalog) -> dict[str, list[Category]]:
    """League id -> a category pool scoped to that league, for league-only
    game modes. Clubs are filtered to the league's own (small, curated) club
    list directly — no wrapping needed. Every other type gets wrapped in
    LeagueScopedCategory, ANDing the category with "played for a club in this
    league". Deliberately does NOT pre-filter wrapped categories by actual
    overlap size (that would mean an eligible_player_ids() DB query per
    category per league — thousands of queries added to startup for little
    benefit): a wrapped category with too few real answers just fails the
    puzzle-generator's existing bounds check and gets retried, the same way
    it already handles the full ~7,000-category unscoped pool.
    """
    from .categories import CategoryType, LeagueScopedCategory

    pools: dict[str, list[Category]] = {}
    for league in league_categories:
        club_names = set(league.club_names)
        league_clubs = [c for c in catalog.clubs if c.club_name in club_names]
        wrapped = [
            LeagueScopedCategory(cat, league.club_names, id=f"{cat.id}__{league.id}", label=cat.label)
            for cat in all_categories
            if cat.type not in (CategoryType.CLUB, CategoryType.LEAGUE, CategoryType.CONTINENT)
        ]
        pools[league.id] = league_clubs + wrapped
    return pools
