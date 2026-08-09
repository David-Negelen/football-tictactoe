"""Builds Club/Nationality/Trophy categories dynamically from the real
dataset instead of a small hand-curated list, so puzzle generation can draw
on ~500 trophies instead of the original 19/11 hand-curated lists (clubs and
nationalities are further restricted to a whitelist — see
PROMINENT_CLUB_NAMES / NATIONALITY_DENYLIST).

Trophy difficulty (1-3) is derived directly from how many distinct players
satisfy a category — "how rare is this" is a fair proxy for a trophy, since
winning something obscure is still a real, checkable fact, just a hard one.
Club and nationality difficulty are NOT rarity-based (see CLUB_DIFFICULTY /
NATIONALITY_DIFFICULTY below) — how many players happen to share a
club_name/nationality string measures Transfermarkt scraping/dataset
composition, not how recognizable the club or country actually is to a
casual player (e.g. "Simbabwe" and "Mauretanien" clear a rarity bar just
from a handful of diaspora-listed players, without being remotely
guessable).

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
from .category_config import CONTINENT_CATEGORIES, LEAGUE_CATEGORIES
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
    r"(?:^|\s)U1[5-9](?:$|\s)|(?:^|\s)U2[0-3](?:$|\s)|Jgd\.|Jugend|Junioren|Acad(?:emy|\.)",
    re.IGNORECASE,
)

# Reserve/B-teams use the senior club's own name plus a trailing "II"/"B"/"C"
# marker (e.g. "FC Augsburg II", "Barcelona B", "Real Madrid C") or a small
# set of other conventions ("Amateure", the new "Milan Futuro"). A player who
# only ever played for the reserve side shouldn't count for the senior club's
# category. "Willem II" is a real Dutch club — the "II" is part of its actual
# name, not a reserve marker — so it's the one explicit exception.
_RESERVE_CLUB_PATTERN = re.compile(r"\s(?:II|B|C)$|Amateure|Futuro", re.IGNORECASE)
_RESERVE_CLUB_ALLOWLIST = {"Willem II"}

# Player count no longer decides a club's difficulty tier (see
# CLUB_DIFFICULTY below) — it's still used as a bare viability floor, since
# an answer pool of 1-4 players is too thin to be a fair puzzle no matter how
# famous the club's name is. Same value as the old CLUB_TIER_THRESHOLDS'
# lowest bucket, so this change moves which clubs get which difficulty, not
# which clubs appear at all.
CLUB_MIN_PLAYERS = 5


def _is_junk_club(name: str) -> bool:
    if name in CLUB_STATUS_DENYLIST or bool(_YOUTH_CLUB_PATTERN.search(name)):
        return True
    if name in _RESERVE_CLUB_ALLOWLIST:
        return False
    return bool(_RESERVE_CLUB_PATTERN.search(name))


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

# A club's player count only measures rarity ("how many players have this
# literal club_name"), not recognizability — a 5th-tier German amateur club
# or a long-defunct English lower-league side can easily clear a rarity bar
# just by having been one waypoint in an otherwise-notable career, without
# being remotely guessable. Outside of league mode (which already uses its
# own per-league club_names directly, see build_league_pools) the general
# "club" pool needs an actual prominence whitelist, not just a player-count
# floor. Reusing the clubs that are already hand-picked and DB-verified
# elsewhere — the major-league and continental "played in X" lists — avoids
# re-curating (and re-risking-typos-on) an entirely new list from scratch.
PROMINENT_CLUB_NAMES: set[str] = {
    *(name for league in LEAGUE_CATEGORIES for name in league.club_names),
    *(name for cont in CONTINENT_CATEGORIES for name in cont.club_names),
    *LEGACY_CLUB_IDS.keys(),
}

# Being on the whitelist above only answers "may this club appear at all" —
# every one of these ~160 clubs is wildly different in actual fame (Bayern
# München vs. SC Paderborn vs. Como). This answers "how hard is it": bigger,
# more famous clubs are always easier, because a casual player actually
# knows their squad. Criteria — would a casual football fan recognize the
# club and name two of its players, based on the club's fame across its
# *whole* history, not just this season (e.g. Hamburger SV and FC Schalke 04
# are tier 1 despite currently playing in the second division)?
#   Tier 1: Champions-League/continental-final regulars, multiple major
#     domestic or continental titles in roughly the last 20 years,
#     near-universal name recognition.
#   Tier 2: established, nationally/regionally well-known clubs — not
#     continental regulars, but a real name with at least one household
#     player.
#   Tier 3 (default, not enumerated below): everything else — most of the
#     smaller top-flight clubs and most of the Asia/Africa/smaller-South-
#     America continental whitelist.
#
# Every name below must match career_stints.club_name byte-for-byte (see the
# "Man City" vs "Manchester City" note on LEGACY_CLUB_IDS above for the kind
# of mismatch that silently produces zero matches) — a typo here just falls
# through to DEFAULT_CLUB_DIFFICULTY (tier 3) instead of erroring, which is
# why test_every_fame_tiered_club_name_is_in_the_prominence_whitelist and
# test_every_league_has_enough_easy_clubs exist in
# tests/test_dynamic_categories.py: they're the only things that catch it.
CLUB_FAME_TIER_1: frozenset[str] = frozenset({
    # Bundesliga
    "Bayern München", "Bor. Dortmund", "B. Leverkusen", "RB Leipzig",
    "FC Schalke 04", "Hamburger SV", "E. Frankfurt", "Werder Bremen",
    # Premier League
    "Arsenal", "Chelsea", "Liverpool", "Man City", "Manchester Utd.",
    "Tottenham", "Newcastle", "Aston Villa", "FC Everton",
    # La Liga
    "Real Madrid", "FC Barcelona", "Atlético Madrid", "FC Sevilla",
    "FC Valencia", "Athletic Bilbao", "Real Sociedad", "FC Villarreal",
    "Betis Sevilla",
    # Serie A
    "Juventus", "Milan", "Inter", "SSC Neapel", "AS Rom", "Lazio Rom",
    "Atalanta", "AC Florenz", "AC Parma",
    # South America
    "Boca Juniors", "River Plate", "Flamengo", "Corinthians",
    # Other Europe (from LEGACY_CLUB_IDS, no whitelisted league of their own)
    "Ajax", "Paris SG",
})

CLUB_FAME_TIER_2: frozenset[str] = frozenset({
    # Bundesliga
    "Bor. M'gladbach", "1.FC Köln", "VfL Wolfsburg", "VfB Stuttgart",
    # Premier League
    "Leeds United", "Nottingham", "Crystal Palace", "AFC Sunderland",
    # La Liga
    "Celta Vigo", "Rayo Vallecano", "Esp. Barcelona", "Dep. La Coruña",
    # Serie A
    "FC Turin", "FC Bologna", "Genua CFC", "Udinese",
    # South America
    "Palmeiras", "FC Santos", "FC São Paulo", "Independiente",
    "Fluminense", "Peñarol",
    # Africa
    "Esperance", "Wydad AC", "Raja Casablanca", "Zamalek", "Kaizer Chiefs",
    # Asia — Saudi Pro League's globally-covered signings, and the
    # historically biggest J-League names
    "Al-Hilal", "Al-Nassr", "Al-Ittihad", "Al-Ahli", "Urawa Reds",
    "Kashima Antlers",
    # Other Europe
    "PSV",
})

DEFAULT_CLUB_DIFFICULTY = 3  # unlisted above (or a name typo) -> hardest tier

CLUB_DIFFICULTY: dict[str, int] = {
    **{name: 1 for name in CLUB_FAME_TIER_1},
    **{name: 2 for name in CLUB_FAME_TIER_2},
}

# Transfermarkt records a distinct "nationality" string per birthplace, which
# includes places with no football team of their own to actually represent —
# dissolved historical states and non-independent overseas departments/
# territories whose players are internationally French (or otherwise their
# parent state) for football purposes, not a "nationality" a casual player
# could ever guess as a football category (e.g. "Französisch-Guayana").
NATIONALITY_DENYLIST: frozenset[str] = frozenset({
    "Französisch-Guayana", "Guadeloupe", "Martinique", "Réunion", "Saint-Martin",
    "DDR", "Jugoslawien (SFR)", "Jugoslawien (Bundesrepublik)", "Niederländische Antillen",
    "Monaco",
})

# A nationality's player count only measures how many rows happen to carry
# that string in this specific dataset, not how recognizable the country
# actually is as a football nation (e.g. "Simbabwe"/"Mauretanien" clear a
# rarity bar just from a handful of diaspora-listed players, without being
# remotely guessable) — the same rarity-vs-fame gap PROMINENT_CLUB_NAMES
# exists to close for clubs. Outside the denylist above (real junk, not
# fame), the general nationality pool needs an actual prominence whitelist,
# not just a player-count floor — otherwise lowering NATIONALITY_MIN_PLAYERS
# below the old ~20 implicit floor (needed so genuinely small-but-real
# football nations like Island/Kosovo stay reachable) floods the pool with
# every barely-populated nationality token instead.
PROMINENT_NATIONALITIES: frozenset[str] = frozenset({
    # Fame-tiered below (see NATIONALITY_FAME_TIER_1/2).
    "Deutschland", "Italien", "Spanien", "Frankreich", "England", "Niederlande",
    "Brasilien", "Argentinien", "Schottland", "Portugal", "Belgien", "Marokko",
    "Türkei", "Polen", "Nigeria", "Kroatien", "Dänemark", "Senegal", "Schweden",
    "Schweiz", "Wales", "Uruguay", "Vereinigte Staaten", "Österreich", "Norwegen",
    "Kolumbien", "Japan", "Chile", "Mexiko", "Südkorea", "Ägypten",
    "Irland", "Serbien", "Ghana", "Elfenbeinküste", "Kamerun", "Algerien",
    "Mali", "Tschechien", "Bosnien-Herzegowina", "Australien", "Nordirland",
    "Griechenland", "Rumänien", "Ungarn", "Tunesien", "Russland", "Paraguay",
    "Ukraine", "Kanada", "Island", "Südafrika", "Peru", "Iran", "Ecuador",
    "Costa Rica",
    # Real, recognizable-enough football nations that don't clear a fame
    # tier — whitelisted (may appear, at the default hardest difficulty)
    # but not called out as easy or medium.
    "DR Kongo", "Suriname", "Jamaika", "Guinea", "Albanien", "Slowenien",
    "Bulgarien", "Slowakei", "Finnland", "Kosovo", "Angola", "Kongo",
    "Nordmazedonien", "Montenegro", "Venezuela", "Israel", "Gabun", "Togo",
    "Trinidad und Tobago", "Liberia", "Neuseeland",
})

# Being on the whitelist above only answers "may this nationality appear at
# all" — this answers "how hard is it", the same fame-not-rarity idea
# CLUB_FAME_TIER_1/2 applies to clubs (e.g. Ägypten/Egypt has few players in
# this dataset but is instantly recognizable via Mohamed Salah — the exact
# rarity-vs-fame gap this replaces).
#   Tier 1: World Cup regulars / recent deep runs, globally recognized star
#     players, near-universal name recognition as a football nation.
#   Tier 2: recognizable, established football nations — regular continental
#     (not necessarily World Cup) participants, or known via a handful of
#     star players.
#   Tier 3 (default, not enumerated below): everything else on the
#     whitelist — a real, checkable nationality, just not one most casual
#     players would immediately recognize as a football nation.
#
# Every name below must match a real, exact token from players.nationality
# (see parse_nationality_tokens) and be a subset of PROMINENT_NATIONALITIES —
# a typo here just falls through to DEFAULT_NATIONALITY_DIFFICULTY (tier 3)
# instead of erroring, which is why
# test_every_fame_tiered_nationality_is_in_the_prominence_whitelist exists
# in tests/test_dynamic_categories.py.
NATIONALITY_FAME_TIER_1: frozenset[str] = frozenset({
    "Deutschland", "Italien", "Spanien", "Frankreich", "England", "Niederlande",
    "Brasilien", "Argentinien", "Schottland", "Portugal", "Belgien", "Marokko",
    "Türkei", "Polen", "Nigeria", "Kroatien", "Dänemark", "Senegal", "Schweden",
    "Schweiz", "Wales", "Uruguay", "Vereinigte Staaten", "Österreich", "Norwegen",
    "Kolumbien", "Japan", "Chile", "Mexiko", "Südkorea", "Ägypten",
})

NATIONALITY_FAME_TIER_2: frozenset[str] = frozenset({
    "Irland", "Serbien", "Ghana", "Elfenbeinküste", "Kamerun", "Algerien",
    "Mali", "Tschechien", "Bosnien-Herzegowina", "Australien", "Nordirland",
    "Griechenland", "Rumänien", "Ungarn", "Tunesien", "Russland", "Paraguay",
    "Ukraine", "Kanada", "Island", "Südafrika", "Peru", "Iran", "Ecuador",
    "Costa Rica",
})

DEFAULT_NATIONALITY_DIFFICULTY = 3  # whitelisted, but unlisted above -> hardest

NATIONALITY_DIFFICULTY: dict[str, int] = {
    **{name: 1 for name in NATIONALITY_FAME_TIER_1},
    **{name: 2 for name in NATIONALITY_FAME_TIER_2},
}

# Answer pool of 1-2 players is too thin to be a fair puzzle no matter how
# famous the country's name is — but set much lower than CLUB_MIN_PLAYERS
# (5), since PROMINENT_NATIONALITIES above (not player count) now does the
# real "is this worth including" gatekeeping; this is just a bare sanity
# floor.
NATIONALITY_MIN_PLAYERS = 3


def build_dynamic_clubs(
    conn: sqlite3.Connection,
    prominent_names: set[str] = PROMINENT_CLUB_NAMES,
    club_difficulty: dict[str, int] = CLUB_DIFFICULTY,
) -> list[ClubCategory]:
    rows = conn.execute(
        "SELECT club_name, COUNT(DISTINCT player_id) AS n FROM career_stints GROUP BY club_name"
    ).fetchall()
    categories = []
    for club_name, n in rows:
        if _is_junk_club(club_name) or club_name not in prominent_names:
            continue
        if n < CLUB_MIN_PLAYERS:  # viability floor only — not a difficulty
            continue
        difficulty = club_difficulty.get(club_name, DEFAULT_CLUB_DIFFICULTY)
        cat_id = LEGACY_CLUB_IDS.get(club_name) or _stable_id("club", club_name)
        categories.append(ClubCategory(cat_id, club_name, club_name, difficulty=difficulty))
    return categories


def build_dynamic_nationalities(
    conn: sqlite3.Connection,
    denylist: frozenset[str] = NATIONALITY_DENYLIST,
    prominent_names: frozenset[str] = PROMINENT_NATIONALITIES,
    nationality_difficulty: dict[str, int] = NATIONALITY_DIFFICULTY,
) -> list[NationalityCategory]:
    rows = conn.execute(
        "SELECT nationality, COUNT(*) AS n FROM players WHERE nationality IS NOT NULL AND nationality != '' GROUP BY nationality"
    ).fetchall()
    counts: dict[str, int] = {}
    for raw, n in rows:
        for token in parse_nationality_tokens(raw):
            counts[token] = counts.get(token, 0) + n

    categories = []
    for name, n in counts.items():
        if name not in COUNTRY_BY_NAME or name in denylist or name not in prominent_names:
            continue
        if n < NATIONALITY_MIN_PLAYERS:  # viability floor only — not a difficulty
            continue
        difficulty = nationality_difficulty.get(name, DEFAULT_NATIONALITY_DIFFICULTY)
        legacy = LEGACY_NATIONALITY_ENTRIES.get(name)
        cat_id = legacy[0] if legacy else f"nat_dyn_{COUNTRY_BY_NAME[name].iso_code.lower()}"
        label = legacy[1] if legacy else name
        categories.append(
            NationalityCategory(cat_id, label, name, icon=country_flag(name), difficulty=difficulty)
        )
    return categories


# classify_trophy_title() already filters out individual awards, youth/
# reserve competitions, and lower-tier regional titles — but 490 titles
# still pass, and a trophy's player count (how many rows in this dataset
# happen to carry that title) is no more a fame signal than it was for
# clubs or nationalities: "Intertoto-Cup-Sieger" (a defunct UEFA summer
# tournament) and "Mitropacup-Sieger" (a defunct interwar Central European
# cup) both clear 100+ winners purely because of how many clubs historically
# entered those competitions, while a genuinely famous trophy like a Copa
# Libertadores can have far fewer rows just from this dataset's European-
# heavy squad coverage. Same fix as PROMINENT_CLUB_NAMES/
# PROMINENT_NATIONALITIES: an explicit whitelist of the trophies a casual
# player would actually recognize, tiered by fame — not derived from count.
#
# Tier 1: major international team trophies, the biggest continental club
#   competitions, and the league + primary cup of the biggest football
#   nations (the same nations in NATIONALITY_FAME_TIER_1, plus their
#   domestic league-cup/super-cup where one exists).
# Tier 2: the same idea for NATIONALITY_FAME_TIER_2's nations, plus
#   continental competitions/youth internationals a step below tier 1.
# Unlisted trophies simply don't appear at all (unlike clubs/nationalities,
# there's no "real but hard" tier 3 default here — a trophy nobody's ever
# heard of isn't a harder question, it's an unrecognizable one).
TROPHY_FAME_TIER_1: frozenset[str] = frozenset({
    # Major international team trophies + the one individual award already
    # legacy-curated (see LEGACY_TROPHY_IDS).
    "Weltmeister", "Europameister", "Copa América-Sieger", "Afrikameister",
    "Olympiasieger", "Gewinner Ballon d'Or",
    # Major continental/global club trophies.
    "UEFA Champions League-Sieger", "Europa-League-Sieger", "UEFA-Supercup-Sieger",
    "FIFA-Klub-Weltmeister", "Weltpokalsieger", "Copa Libertadores-Sieger",
    "Europapokal-der-Landesmeister-Sieger", "Europapokal-der-Pokalsieger-Sieger",
    # Domestic league/cup/super-cup for NATIONALITY_FAME_TIER_1's nations.
    "Argentinischer Meister", "Argentinischer Pokalsieger",
    "Belgischer Ligapokalsieger", "Belgischer Meister", "Belgischer Pokalsieger", "Belgischer Superpokalsieger",
    "Brasilianischer Meister", "Brasilianischer Pokalsieger", "Brasilianischer Superpokalsieger",
    "Chilenischer Meister", "Chilenischer Pokalsieger", "Chilenischer Supercupsieger",
    "Deutscher Ligapokalsieger", "Deutscher Meister", "Deutscher Pokalsieger", "Deutscher Superpokalsieger",
    "Dänischer Meister", "Dänischer Pokalsieger",
    "Englischer Ligapokalsieger", "Englischer Meister", "Englischer Pokalsieger", "Englischer Superpokalsieger",
    "Französischer Ligapokalsieger", "Französischer Meister", "Französischer Pokalsieger", "Französischer Superpokalsieger",
    "Italienischer Meister", "Italienischer Pokalsieger", "Italienischer Superpokalsieger",
    "Japanischer Ligapokalsieger", "Japanischer Meister", "Japanischer Pokalsieger", "Japanischer Superpokalsieger",
    "Kolumbianischer Meister", "Kolumbianischer Pokalsieger", "Kolumbianischer Superpokalsieger",
    "Kroatischer Meister", "Kroatischer Pokalsieger", "Kroatischer Superpokalsieger",
    "Marokkanischer Meister", "Marokkanischer Pokalsieger",
    "Mexikanischer Meister", "Mexikanischer Meister Apertura", "Mexikanischer Meister Clausura",
    "Mexikanischer Pokalsieger", "Mexikanischer Pokalsieger Apertura", "Mexikanischer Pokalsieger Clausura",
    "Mexikanischer Supercupsieger",
    "Niederländischer Meister", "Niederländischer Pokalsieger", "Niederländischer Superpokalsieger",
    "Nigerianischer Meister", "Nigerianischer Pokalsieger",
    "Norwegischer Meister", "Norwegischer Pokalsieger", "Norwegischer Superpokalsieger",
    "Polnischer Meister", "Polnischer Pokalsieger", "Polnischer Superpokalsieger",
    "Portugiesischer Ligapokalsieger", "Portugiesischer Meister", "Portugiesischer Pokalsieger", "Portugiesischer Superpokalsieger",
    "Schottischer Ligapokalsieger", "Schottischer Meister", "Schottischer Pokalsieger",
    "Schwedischer Meister", "Schwedischer Pokalsieger", "Schwedischer Superpokalsieger",
    "Schweizer Cupsieger", "Schweizer Ligapokalsieger", "Schweizer Meister", "Schweizer Supercupsieger",
    "Senegalesischer Meister",
    "Spanischer Ligapokalsieger", "Spanischer Meister", "Spanischer Pokalsieger", "Spanischer Superpokalsieger",
    "Südkoreanischer Ligapokalsieger", "Südkoreanischer Meister", "Südkoreanischer Pokalsieger", "Südkoreanischer Superpokalsieger",
    "Türkischer Meister", "Türkischer Pokalsieger", "Türkischer Superpokalsieger",
    "Uruguayischer Meister", "Uruguayischer Pokalsieger",
    "Walisischer Meister",
    "Ägyptischer Ligapokalsieger", "Ägyptischer Meister", "Ägyptischer Pokalsieger", "Ägyptischer Superpokalsieger",
    "Österreichischer Cupsieger", "Österreichischer Meister",
})

TROPHY_FAME_TIER_2: frozenset[str] = frozenset({
    # Continental competitions and youth internationals a step below tier 1.
    "Confederations-Cup-Sieger", "U20-Weltmeister",
    "Copa Sudamericana-Sieger", "Recopa Sudamericana-Sieger", "Conference League-Sieger",
    "CAF-Champions-League-Sieger", "AFC-Champions-League-Sieger", "CONCACAF-Champions-League-Sieger",
    "MLS Cup Champion", "Leagues-Cup-Sieger", "Sieger UEFA Nations League", "Gold-Cup-Sieger",
    "US Open Cup Winner",
    # Domestic league/cup/super-cup for NATIONALITY_FAME_TIER_2's nations.
    "Algerischer Ligapokalsieger", "Algerischer Meister", "Algerischer Pokalsieger", "Algerischer Supercupsieger",
    "Australischer Meister", "Australischer Pokalsieger",
    "Bosnisch-Herzegowinischer Meister", "Bosnisch-Herzegowinischer Pokalsieger", "Bosnisch-Herzegowinischer Superpokalsieger",
    "Costa-Ricanischer Meister", "Costa-Ricanischer Meister Invierno", "Costa-Ricanischer Meister Verano",
    "Costa-Ricanischer Pokalsieger", "Costa-Ricanischer Superpokalsieger",
    "Ecuadorianischer Meister",
    "Ghanaischer Meister",
    "Griechischer Meister", "Griechischer Pokalsieger", "Griechischer Superpokalsieger",
    "Iranischer Meister", "Iranischer Pokalsieger", "Iranischer Supercup-Sieger",
    "Irischer Ligapokalsieger", "Irischer Meister", "Irischer Pokalsieger",
    "Isländischer Ligapokalsieger", "Isländischer Meister", "Isländischer Pokalsieger", "Isländischer Superpokalsieger",
    "Kanadischer Meister", "Kanadischer Pokalsieger",
    "Nordirischer Ligapokalsieger", "Nordirischer Meister", "Nordirischer Pokalsieger",
    "Paraguayischer Meister", "Paraguayischer Meister Apertura", "Paraguayischer Meister Clausura",
    "Peruanischer Meister", "Peruanischer Pokalsieger", "Peruanischer Superpokalsieger",
    "Rumänischer Ligapokalsieger", "Rumänischer Meister", "Rumänischer Pokalsieger", "Rumänischer Superpokalsieger",
    "Russischer Meister", "Russischer Pokalsieger", "Russischer Superpokalsieger",
    "Serbischer Meister", "Serbischer Pokalsieger",
    "Südafrikanischer Meister", "Südafrikanischer Pokalsieger",
    "Tschechischer Meister", "Tschechischer Pokalsieger",
    "Tunesischer Meister", "Tunesischer Pokalsieger", "Tunesischer Superpokalsieger",
    # Two distinct data-scraped variants of the same real title (one with a
    # trailing space) — both need whitelisting or the space-variant would
    # silently vanish despite being the identical trophy.
    "Ukrainischer Meister", "Ukrainischer Meister ",
    "Ukrainischer Pokalsieger", "Ukrainischer Superpokalsieger",
    "Ungarischer Ligapokalsieger", "Ungarischer Meister", "Ungarischer Pokalsieger",
})

PROMINENT_TROPHY_TITLES: frozenset[str] = TROPHY_FAME_TIER_1 | TROPHY_FAME_TIER_2

DEFAULT_TROPHY_DIFFICULTY = 3  # unreachable in practice — every whitelisted title is tier 1 or 2

TROPHY_DIFFICULTY: dict[str, int] = {
    **{title: 1 for title in TROPHY_FAME_TIER_1},
    **{title: 2 for title in TROPHY_FAME_TIER_2},
}


def build_dynamic_trophies(
    conn: sqlite3.Connection,
    prominent_titles: frozenset[str] = PROMINENT_TROPHY_TITLES,
    trophy_difficulty: dict[str, int] = TROPHY_DIFFICULTY,
) -> list[TrophyCategory]:
    rows = conn.execute("SELECT title, COUNT(*) AS n FROM player_trophies GROUP BY title").fetchall()
    categories = []
    for title, n in rows:
        if not classify_trophy_title(title) or title not in prominent_titles:
            continue
        difficulty = trophy_difficulty.get(title, DEFAULT_TROPHY_DIFFICULTY)
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
