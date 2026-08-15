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

from .categories import (
    Category,
    ClubCategory,
    NationalityCategory,
    TeammateCategory,
    TrophyCategory,
    _season_year_sql,
    strip_jersey_prefix,
)
from .countries import COUNTRY_BY_NAME, parse_nationality_tokens
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

# Individual club categories ("played for Bayern München") are restricted
# much harder than the continent-aggregate ones ("played in Asia" — see
# CONTINENT_CATEGORIES): naming a SPECIFIC club by name only works as a fair
# category if a casual player would actually recognize that exact club, not
# just "some club from that continent". Every other whitelisted-but-untiered
# club that used to leak in here via the continental "played in X" lists
# (Chennaiyin FC, GZ Evergrande's Asian neighbors that never made fame tier 2,
# most of the Africa/South America lists) is deliberately excluded — those
# lists exist for their own continent-aggregate category, not to seed the
# general club pool.
#
# A club may appear at all ONLY by being named in one of the three tiers
# below (CLUB_FAME_TIER_1/2/3) — there is no other path in, so add or remove
# a club by editing these three sets directly. Criteria — would a casual
# football fan recognize the club and name two of its players, based on the
# club's fame across its *whole* history, not just this season (e.g. Hamburger
# SV and FC Schalke 04 are tier 1 despite currently playing in the second
# division)?
#   Tier 1: Champions-League/continental-final regulars, multiple major
#     domestic or continental titles in roughly the last 20 years,
#     near-universal name recognition.
#   Tier 2: established, nationally/regionally well-known clubs — not
#     continental regulars, but a real name with at least one household
#     player.
#   Tier 3: real, checkable clubs a casual player is less likely to
#     recognize outright (mostly smaller top-flight sides in the four
#     LEAGUE_CATEGORIES leagues) — whitelisted at the hardest difficulty
#     rather than excluded, since being in a major league is still enough
#     to make the club a fair (if hard) category.
#
# Every name below must match career_stints.club_name byte-for-byte (see the
# "Man City" vs "Manchester City" note on LEGACY_CLUB_IDS above for the kind
# of mismatch that silently produces zero matches) — a typo here just means
# the club never appears at all instead of erroring, which is why
# test_every_fame_tiered_club_name_is_in_the_prominence_whitelist and
# test_every_league_has_enough_easy_clubs exist in
# tests/test_dynamic_categories.py: they're the only things that catch it.
CLUB_FAME_TIER_1: frozenset[str] = frozenset({
    # Bundesliga
    "Bayern München", "Bor. Dortmund", "B. Leverkusen", "RB Leipzig",
    "FC Schalke 04", 
    # Premier League
    "Arsenal", "Chelsea", "Liverpool", "Man City", "Manchester Utd.",
    # La Liga
    "Real Madrid", "FC Barcelona", "Atlético Madrid", "FC Sevilla",
    # Serie A
    "Juventus", "Milan", "Inter", 
    # Other Europe (from LEGACY_CLUB_IDS, no whitelisted league of their own)
    # — Paris SG stays individual: Ligue 1 has no other fame-tiered club, so
    # a one-club "league" category would be a worse, less recognizable
    # wrapper than just naming PSG directly (see FOREIGN_LEAGUE_CATEGORIES
    # in category_config.py for the leagues that DID get grouped this way —
    # Boca Juniors/River Plate/Flamengo/Corinthians/Ajax used to be listed
    # here too, before being folded into Argentinische Liga/Brasilianische
    # Serie A/Eredivisie).
    "Paris SG",
})

CLUB_FAME_TIER_2: frozenset[str] = frozenset({
    # Bundesliga
    "Bor. M'gladbach", "1.FC Köln", "VfL Wolfsburg", "VfB Stuttgart",
    "Hamburger SV", "E. Frankfurt",
    # Premier League
    "Brighton",  "FC Everton", "Tottenham", "Newcastle", "Aston Villa",
    # La Liga
    "FC Valencia", "Athletic Bilbao", "Real Sociedad", "FC Villarreal",
    "Betis Sevilla",
    # Serie A
    "SSC Neapel", "AS Rom", "Lazio Rom", "Atalanta", "AC Florenz", "AC Parma",
})

# Every other club in the four LEAGUE_CATEGORIES leagues (category_config.py)
# that isn't individually fame-tiered above — real top-flight clubs, just not
# ones most casual players would name unprompted. Add/remove a club here (or
# to tier 1/2 above) to change what can appear at all; nothing outside these
# three sets is eligible, regardless of league membership or player count.
CLUB_FAME_TIER_3: frozenset[str] = frozenset({
    # Bundesliga
    "FC Augsburg", "1.FSV Mainz 05", "Union Berlin",  "Werder Bremen",
    "SC Freiburg", "TSG Hoffenheim", "Hertha BSC", "1.FC Nürnberg",
    "Hannover 96", "1.FC K'lautern", "FC St. Pauli",
    # Premier League
    "Bournemouth", "FC Brentford", "Coventry City", "FC Fulham",
    "Leeds United", "Nottingham", "Crystal Palace",
    # La Liga
    "Alavés", "FC Elche", "FC Getafe", "FC Málaga", "CA Osasuna",
    "Rac. Santander", "UD Levante", "Celta Vigo", "Rayo Vallecano",
    "Esp. Barcelona", "Dep. La Coruña", "RCD Mallorca", "FC Girona",
    # Serie A
    "Cagliari", "Como", "Frosinone", "Lecce", "Monza", "US Sassuolo",
    "FC Turin", "FC Bologna", "Genua CFC", "Udinese",
    "AC Venezia 1907", "Sampdoria", "Hellas Verona", "US Palermo", "Bari",
    # More 2nd-division clubs — still real, checkable names, just a notch
    # below CLUB_FAME_TIER_2's second-division entries above.
    # 2. Bundesliga
    "Karlsruher SC", "Greuther Fürth", "Arm. Bielefeld", "F. Düsseldorf",
    "Holstein Kiel", "Darmstadt 98", "E. Braunschweig", "VfL Bochum",
})

PROMINENT_CLUB_NAMES: set[str] = CLUB_FAME_TIER_1 | CLUB_FAME_TIER_2 | CLUB_FAME_TIER_3

DEFAULT_CLUB_DIFFICULTY = 3  # unreachable in practice — every whitelisted club is tier 1/2/3

CLUB_DIFFICULTY: dict[str, int] = {
    **{name: 1 for name in CLUB_FAME_TIER_1},
    **{name: 2 for name in CLUB_FAME_TIER_2},
    **{name: 3 for name in CLUB_FAME_TIER_3},
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
#
# A nationality may appear at all ONLY by being named in one of the three
# tiers below (NATIONALITY_FAME_TIER_1/2/3) — there is no other path in, so
# add or remove a country by editing these three sets directly. Being in a
# tier answers both "may this appear" and "how hard is it" (the same
# fame-not-rarity idea CLUB_FAME_TIER_1/2/3 applies to clubs — e.g. Ägypten/
# Egypt has few players in this dataset but is instantly recognizable via
# Mohamed Salah).
#   Tier 1: World Cup regulars / recent deep runs, globally recognized star
#     players, near-universal name recognition as a football nation.
#   Tier 2: recognizable, established football nations — regular continental
#     (not necessarily World Cup) participants, or known via a handful of
#     star players.
#   Tier 3: real, checkable football nations that don't clear a fame tier —
#     whitelisted at the hardest difficulty rather than excluded.
#
# Every name below must match a real, exact token from players.nationality
# (see parse_nationality_tokens) — a typo here just means the country never
# appears at all instead of erroring, which is why
# test_every_fame_tiered_nationality_is_in_the_prominence_whitelist exists
# in tests/test_dynamic_categories.py.
NATIONALITY_FAME_TIER_1: frozenset[str] = frozenset({
    "Deutschland", "Italien", "Spanien", "Frankreich", "England", "Niederlande",
    "Brasilien", "Argentinien", "Portugal", 
})

NATIONALITY_FAME_TIER_2: frozenset[str] = frozenset({
    "Belgien", "Marokko",
    "Türkei", "Polen", "Kroatien", 
    "Schweiz", "Österreich", "Norwegen",
})

# Real, recognizable-enough football nations that don't clear a fame tier —
# whitelisted at the hardest difficulty rather than excluded. Add/remove a
# country here (or to tier 1/2 above) to change what can appear at all.
NATIONALITY_FAME_TIER_3: frozenset[str] = frozenset({
    "Nigeria", "Dänemark", "Senegal", "Schweden", "Uruguay",
    "Vereinigte Staaten", "Ukraine", "Kanada", "Island",
    "Ghana", "Elfenbeinküste", "Tschechien", "Bosnien-Herzegowina", 
    "Griechenland", "Russland", "Kolumbien", "Japan", "Chile", "Mexiko",
    "Südkorea", "Ägypten", "Schottland", 
})

PROMINENT_NATIONALITIES: frozenset[str] = (
    NATIONALITY_FAME_TIER_1 | NATIONALITY_FAME_TIER_2 | NATIONALITY_FAME_TIER_3
)

DEFAULT_NATIONALITY_DIFFICULTY = 3  # unreachable in practice — every whitelisted nationality is tier 1/2/3

NATIONALITY_DIFFICULTY: dict[str, int] = {
    **{name: 1 for name in NATIONALITY_FAME_TIER_1},
    **{name: 2 for name in NATIONALITY_FAME_TIER_2},
    **{name: 3 for name in NATIONALITY_FAME_TIER_3},
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
        # No per-category icon here — app.py's _cat_display resolves a real
        # flag image (or a shared generic fallback icon) off `nationality`
        # at render time instead, so there's nothing to precompute.
        categories.append(
            NationalityCategory(cat_id, label, name, difficulty=difficulty)
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
#   competitions, and the league + one major cup of the biggest football
#   nations (the same nations in NATIONALITY_FAME_TIER_1). Super Cups and
#   League Cups are not whitelisted here for any other nation — see
#   trophy_rules.classify_trophy_title, which excludes them outright
#   (a Super Cup is a single exhibition match, not a competition; a League
#   Cup is real silverware but a clear notch below the national cup
#   wherever the two coexist) — so listing them here would be dead weight.
#   England is the one deliberate exception (see
#   trophy_rules._DOMESTIC_CUP_ALLOW_TITLES): the League Cup (Carabao/EFL
#   Cup) and the Community Shield are both genuinely recognizable English
#   silverware, not just domestic trivia.
# Tier 2: the same idea for NATIONALITY_FAME_TIER_2's nations, plus each
#   confederation's top continental club competition and top national-team
#   championship a step below tier 1's biggest (UEFA's three tiers of club
#   competition are the one exception, all three in tier 1/tier 2 above).
# Tier 3: the domestic league title for NATIONALITY_FAME_TIER_3 nations
#   whose league still has a real, checkable pool of winners in this
#   dataset — real silverware, just for a country most casual players
#   wouldn't immediately name as a football nation. Unlike tier 1/2, no
#   domestic cup is added here (thinner pool, and a second hard-tier
#   category per country isn't worth the added obscurity).
TROPHY_FAME_TIER_1: frozenset[str] = frozenset({
    "Weltmeister", "Europameister", "Copa América-Sieger", "Afrikameister",
    "Asienmeister", "Olympiasieger",
    "UEFA Champions League-Sieger",
    "Europa-League-Sieger",
})

TROPHY_FAME_TIER_2: frozenset[str] = frozenset({
    "Deutscher Meister", "Deutscher Pokalsieger",
    "Englischer Meister", 
    #"Englischer Pokalsieger","Englischer Ligapokalsieger", "Englischer Superpokalsieger",
    "Französischer Meister", "Französischer Pokalsieger",
    "Italienischer Meister", "Italienischer Pokalsieger",
    "Spanischer Meister", "Spanischer Pokalsieger",
    "FIFA-Klub-Weltmeister",
})

# Domestic league titles for NATIONALITY_FAME_TIER_3 nations, filtered to
# ones with a real enough pool of winners in this dataset (≥10 distinct
# trophy rows) — thinner than that (e.g. "Jamaikanischer Meister" at 1,
# "Kosovarischer Meister" at 2) isn't a fair puzzle cell no matter the tier.
TROPHY_FAME_TIER_3: frozenset[str] = frozenset({

})

PROMINENT_TROPHY_TITLES: frozenset[str] = TROPHY_FAME_TIER_1 | TROPHY_FAME_TIER_2 | TROPHY_FAME_TIER_3

DEFAULT_TROPHY_DIFFICULTY = 3  # unreachable in practice — every whitelisted title is tier 1/2/3

TROPHY_DIFFICULTY: dict[str, int] = {
    **{title: 1 for title in TROPHY_FAME_TIER_1},
    **{title: 2 for title in TROPHY_FAME_TIER_2},
    **{title: 3 for title in TROPHY_FAME_TIER_3},
}

# Old/renamed names and data-scrape spelling variants that are really the
# same real-world trophy as their canonical (right-hand) entry — mapped so
# build_dynamic_trophies merges them into one category matching a player who
# won it under ANY of these names, instead of splitting winners across two
# board cells for what a casual player would see as one honor. Only the
# canonical name needs to be in a TROPHY_FAME_TIER above; classify_trophy_
# title() (trophy_rules.py) still needs to recognize each raw alias too, via
# INTERNATIONAL_ALLOW_TITLES for the international ones.
TROPHY_ALIASES: dict[str, str] = {
    "Europapokal-der-Landesmeister-Sieger": "UEFA Champions League-Sieger",
    "Uefa-Cup-Sieger": "Europa-League-Sieger",
    "CONCACAF-Championship-Sieger": "Gold-Cup-Sieger",
    "CONCACAF-Champions-Cup-Sieger": "CONCACAF-Champions-League-Sieger",
    "Ukrainischer Meister ": "Ukrainischer Meister",  # trailing-space scrape variant
    "Weltpokalsieger": "FIFA-Klub-Weltmeister",
    "FIFA Interkontinental-Pokal-Sieger": "FIFA-Klub-Weltmeister",
}


def build_dynamic_trophies(
    conn: sqlite3.Connection,
    prominent_titles: frozenset[str] = PROMINENT_TROPHY_TITLES,
    trophy_difficulty: dict[str, int] = TROPHY_DIFFICULTY,
    aliases: dict[str, str] = TROPHY_ALIASES,
) -> list[TrophyCategory]:
    rows = conn.execute("SELECT DISTINCT title FROM player_trophies").fetchall()
    titles_by_canonical: dict[str, list[str]] = {}
    for (title,) in rows:
        if not classify_trophy_title(title):
            continue
        canonical = aliases.get(title, title)
        if canonical not in prominent_titles:
            continue
        titles_by_canonical.setdefault(canonical, []).append(title)

    categories = []
    for canonical, titles in titles_by_canonical.items():
        difficulty = trophy_difficulty.get(canonical, DEFAULT_TROPHY_DIFFICULTY)
        cat_id = LEGACY_TROPHY_IDS.get(canonical) or _stable_id("trophy", canonical)
        categories.append(TrophyCategory(cat_id, canonical, titles, difficulty=difficulty))
    return categories


# Anchor eligibility for "played with X" is a deliberately small, hand-
# picked whitelist — unlike clubs/nationalities/trophies above, this is
# NOT threshold-derived from the data (a trophy-count cutoff pulled in
# hundreds of merely-good players, not just recognizable legends; there's
# no reliable purely data-driven "is this player famous to a casual
# player" signal — market_value doesn't work either, it's NULL for most
# retired legends in the real dataset: Zidane, Maldini, Beckenbauer all
# NULL). Keep this list short and genuinely iconic.
#
# Keyed on players.source_url (the Transfermarkt profile URL), NOT name —
# two real correctness bugs found while building this: (1) "Pedro" alone
# matches 3 distinct real players in the dataset (a Barcelona/Chelsea
# legend plus two unrelated obscure ones) — name collisions among common
# names are real, not hypothetical; (2) an accented name typed as a
# Python string literal here ("Ángel Di María", "Álvaro Morata") can be a
# different Unicode normalization form than the same name as stored in
# SQLite, so a name-based `=`/`IN` comparison can silently match zero
# rows even though the player exists — this happened here and both
# players were dropped without any error. source_url is plain ASCII and
# already the unique-identity column the rest of this file uses (see
# _stable_id) — sidesteps both problems entirely.
TEAMMATE_ANCHOR_SOURCE_URLS: dict[str, str] = {
    # display name (for readability only) -> source_url (the actual match key)
    "Lionel Messi": "https://www.transfermarkt.de/lionel-messi/profil/spieler/28003",
    "Cristiano Ronaldo": "https://www.transfermarkt.de/cristiano-ronaldo/profil/spieler/8198",
    "Thierry Henry": "https://www.transfermarkt.de/thierry-henry/profil/spieler/3207",
    "Samuel Eto'o": "https://www.transfermarkt.de/samuel-etoo/profil/spieler/4257",
    "Dani Alves": "https://www.transfermarkt.de/dani-alves/profil/spieler/15951",
    "Ángel Di María": "https://www.transfermarkt.de/angel-di-maria/profil/spieler/45320",
    "Álvaro Morata": "https://www.transfermarkt.de/alvaro-morata/profil/spieler/128223",
    "Sami Khedira": "https://www.transfermarkt.de/sami-khedira/profil/spieler/29401",
    "Lucas Hernández": "https://www.transfermarkt.de/lucas-hernandez/profil/spieler/281963",
    "Pedro": "https://www.transfermarkt.de/pedro/profil/spieler/65278",
}
TEAMMATE_ANCHOR_URLS: frozenset[str] = frozenset(TEAMMATE_ANCHOR_SOURCE_URLS.values())

# Bare viability floor — same idea as CLUB_MIN_PLAYERS: a teammate pool of
# 1-4 players is too thin to be a fair puzzle no matter how famous the
# anchor is.
TEAMMATE_MIN_PLAYERS = 5

# Difficulty is still derived from prominent-trophy count (not anchor
# selection anymore — see TEAMMATE_ANCHOR_NAMES above) — mirrors
# CLUB_FAME_TIER_1/2/3's hand-picked-threshold approach, just applied to
# the fixed whitelist instead of the whole dataset.
TEAMMATE_FAME_TIER_1_MIN = 6
TEAMMATE_FAME_TIER_2_MIN = 4


def _teammate_difficulty(prominent_trophy_count: int) -> int:
    if prominent_trophy_count >= TEAMMATE_FAME_TIER_1_MIN:
        return 1
    if prominent_trophy_count >= TEAMMATE_FAME_TIER_2_MIN:
        return 2
    return 3


def build_dynamic_teammates(
    conn: sqlite3.Connection,
    anchor_urls: frozenset[str] = TEAMMATE_ANCHOR_URLS,
    prominent_trophy_titles: frozenset[str] = PROMINENT_TROPHY_TITLES,
    overlap_club_names: frozenset[str] = PROMINENT_CLUB_NAMES,
    min_players: int = TEAMMATE_MIN_PLAYERS,
    id_prefix: str = "teammate",
) -> list[TeammateCategory]:
    """One TeammateCategory per anchor player in `anchor_urls` (matched on
    players.source_url — see TEAMMATE_ANCHOR_SOURCE_URLS for why not name)
    with a real enough teammate pool (>= min_players) to be a fair puzzle
    cell. `prominent_trophy_titles` only feeds difficulty tiering here, not
    anchor selection. Pool size is computed with a single batched query
    across all candidate anchors (not one query per anchor) — a naive
    per-anchor self-join against the full career_stints table (548k rows)
    measured ~12s at startup for a few hundred anchors; pre-filtering to
    just the prominent-club rows (~70k) into a temp table with the
    season->year conversion precomputed once brings the whole thing well
    under 1s for a whitelist this size.
    """
    if not anchor_urls:
        return []
    ph_urls = ",".join("?" * len(anchor_urls))
    name_rows = conn.execute(
        f"SELECT id FROM players WHERE source_url IN ({ph_urls})",
        list(anchor_urls),
    ).fetchall()
    anchor_ids = [row[0] for row in name_rows]
    if not anchor_ids:
        return []

    anchor_trophy_count: dict[int, int] = {}
    if prominent_trophy_titles:
        ph_tr = ",".join("?" * len(prominent_trophy_titles))
        ph_anchor_ids = ",".join("?" * len(anchor_ids))
        trophy_rows = conn.execute(
            f"SELECT player_id, COUNT(*) FROM player_trophies "
            f"WHERE player_id IN ({ph_anchor_ids}) AND title IN ({ph_tr}) GROUP BY player_id",
            [*anchor_ids, *prominent_trophy_titles],
        ).fetchall()
        anchor_trophy_count = dict(trophy_rows)

    ph_club = ",".join("?" * len(overlap_club_names))
    conn.execute("DROP TABLE IF EXISTS temp.teammate_pool_stints")
    conn.execute(
        f"CREATE TEMP TABLE teammate_pool_stints AS "
        f"SELECT player_id, club_name, "
        f"({_season_year_sql('start_season')}) AS start_year, "
        f"({_season_year_sql('end_season')}) AS end_year "
        f"FROM career_stints WHERE club_name IN ({ph_club})",
        list(overlap_club_names),
    )
    conn.execute("CREATE INDEX idx_teammate_pool_stints_club ON teammate_pool_stints(club_name)")

    overlap = (
        "((a.start_year IS NULL) OR (cs.end_year IS NULL) OR (a.start_year <= cs.end_year)) "
        "AND ((cs.start_year IS NULL) OR (a.end_year IS NULL) OR (cs.start_year <= a.end_year))"
    )
    ph_anchor = ",".join("?" * len(anchor_ids))
    pool_rows = conn.execute(
        f"SELECT a.player_id, COUNT(DISTINCT cs.player_id) FROM teammate_pool_stints a "
        f"JOIN teammate_pool_stints cs ON cs.club_name = a.club_name AND cs.player_id != a.player_id AND {overlap} "
        f"WHERE a.player_id IN ({ph_anchor}) GROUP BY a.player_id",
        anchor_ids,
    ).fetchall()
    conn.execute("DROP TABLE teammate_pool_stints")

    pool_size = dict(pool_rows)
    eligible_ids = [pid for pid in anchor_ids if pool_size.get(pid, 0) >= min_players]
    if not eligible_ids:
        return []

    ph_p = ",".join("?" * len(eligible_ids))
    rows = conn.execute(
        f"SELECT id, name, source_url FROM players WHERE id IN ({ph_p})", eligible_ids
    ).fetchall()

    categories = []
    for pid, raw_name, source_url in rows:
        name = strip_jersey_prefix(raw_name)
        difficulty = _teammate_difficulty(anchor_trophy_count.get(pid, 0))
        # Keyed on source_url (unique, stable identity string) rather than
        # the local autoincrement players.id, which can shift across a DB
        # rebuild/rescrape.
        cat_id = _stable_id(id_prefix, source_url or f"{pid}:{name}")
        label = f"Mit {name} gespielt"
        categories.append(TeammateCategory(cat_id, label, pid, overlap_club_names, difficulty=difficulty))
    return categories


# Per-league "played with X" anchors — players famous mainly to that
# league's own fans rather than globally (TEAMMATE_ANCHOR_SOURCE_URLS
# above), so this whole category only makes sense scoped to that league's
# own puzzles: see build_dynamic_league_teammates/build_league_pools for
# how visibility is restricted, and note overlap_club_names there is the
# league's own club list, not the global PROMINENT_CLUB_NAMES — a "played
# with Kahn" match should require the overlap to have actually happened
# at a Bundesliga club, not anywhere in Kahn's career. Same source_url
# rationale as the global whitelist (name matching is unsafe — see there).
TEAMMATE_ANCHOR_SOURCE_URLS_BY_LEAGUE: dict[str, dict[str, str]] = {
    "league_buli": {
        "Oliver Kahn": "https://www.transfermarkt.de/oliver-kahn/profil/spieler/206",
        "Michael Ballack": "https://www.transfermarkt.de/michael-ballack/profil/spieler/63",
        "Franck Ribéry": "https://www.transfermarkt.de/franck-ribery/profil/spieler/22068",
        "Miroslav Klose": "https://www.transfermarkt.de/miroslav-klose/profil/spieler/10",
        "Robert Lewandowski": "https://www.transfermarkt.de/robert-lewandowski/profil/spieler/38253",
        "Bastian Schweinsteiger": "https://www.transfermarkt.de/bastian-schweinsteiger/profil/spieler/2514",
        "Mario Götze": "https://www.transfermarkt.de/mario-gotze/profil/spieler/74842",
        "Manuel Neuer": "https://www.transfermarkt.de/manuel-neuer/profil/spieler/17259",
    },
    "league_pl": {
        "Wayne Rooney": "https://www.transfermarkt.de/wayne-rooney/profil/spieler/3332",
        "Steven Gerrard": "https://www.transfermarkt.de/steven-gerrard/profil/spieler/3109",
        "Didier Drogba": "https://www.transfermarkt.de/didier-drogba/profil/spieler/3924",
        "Sergio Agüero": "https://www.transfermarkt.de/sergio-aguero/profil/spieler/26399",
        "Harry Kane": "https://www.transfermarkt.de/harry-kane/profil/spieler/132098",
        "John Terry": "https://www.transfermarkt.de/john-terry/profil/spieler/3160",
        "Frank Lampard": "https://www.transfermarkt.de/frank-lampard/profil/spieler/3163",
    },
    "league_laliga": {
        "Sergio Ramos": "https://www.transfermarkt.de/sergio-ramos/profil/spieler/25557",
        "Xavi": "https://www.transfermarkt.de/xavi/profil/spieler/7607",
        "Andrés Iniesta": "https://www.transfermarkt.de/andres-iniesta/profil/spieler/7600",
        "Karim Benzema": "https://www.transfermarkt.de/karim-benzema/profil/spieler/18922",
        "Raúl": "https://www.transfermarkt.de/raul/profil/spieler/7349",
        "Sergio Busquets": "https://www.transfermarkt.de/sergio-busquets/profil/spieler/65230",
    },
    "league_seriea": {
        "Francesco Totti": "https://www.transfermarkt.de/francesco-totti/profil/spieler/5958",
        "Alessandro Del Piero": "https://www.transfermarkt.de/alessandro-del-piero/profil/spieler/4289",
        "Paolo Maldini": "https://www.transfermarkt.de/paolo-maldini/profil/spieler/5803",
        "Andrea Pirlo": "https://www.transfermarkt.de/andrea-pirlo/profil/spieler/5817",
        "Gianluigi Buffon": "https://www.transfermarkt.de/gianluigi-buffon/profil/spieler/5023",
        "Zlatan Ibrahimović": "https://www.transfermarkt.de/zlatan-ibrahimovic/profil/spieler/3455",
    },
}


def build_dynamic_league_teammates(
    conn: sqlite3.Connection,
    league_categories: list,
    anchor_urls_by_league: dict[str, dict[str, str]] = TEAMMATE_ANCHOR_SOURCE_URLS_BY_LEAGUE,
    prominent_trophy_titles: frozenset[str] = PROMINENT_TROPHY_TITLES,
    min_players: int = TEAMMATE_MIN_PLAYERS,
) -> dict[str, list[TeammateCategory]]:
    """League id -> that league's own "played with X" categories, built with
    the league's own club list as overlap_club_names (not the global
    PROMINENT_CLUB_NAMES — see TEAMMATE_ANCHOR_SOURCE_URLS_BY_LEAGUE).
    `id_prefix` is namespaced per league so a player who happened to appear
    as an anchor in more than one league's whitelist wouldn't collide on
    category id (doesn't happen with the current lists, but isn't assumed).
    Returned separately from DynamicCatalog.all() — these are meant to
    populate a league's own LEAGUE_POOLS entry only, never the general/
    unscoped catalog (see build_league_pools).
    """
    result: dict[str, list[TeammateCategory]] = {}
    for league in league_categories:
        urls = anchor_urls_by_league.get(league.id)
        if not urls:
            continue
        result[league.id] = build_dynamic_teammates(
            conn,
            anchor_urls=frozenset(urls.values()),
            prominent_trophy_titles=prominent_trophy_titles,
            overlap_club_names=frozenset(league.club_names),
            min_players=min_players,
            id_prefix=f"teammate_{league.id}",
        )
    return result


@dataclass
class DynamicCatalog:
    clubs: list[ClubCategory] = field(default_factory=list)
    nationalities: list[NationalityCategory] = field(default_factory=list)
    trophies: list[TrophyCategory] = field(default_factory=list)
    teammates: list[TeammateCategory] = field(default_factory=list)

    def all(self) -> list[Category]:
        return [*self.clubs, *self.nationalities, *self.trophies, *self.teammates]


def build_all(conn: sqlite3.Connection) -> DynamicCatalog:
    return DynamicCatalog(
        clubs=build_dynamic_clubs(conn),
        nationalities=build_dynamic_nationalities(conn),
        trophies=build_dynamic_trophies(conn),
        teammates=build_dynamic_teammates(conn),
    )


def build_league_pools(
    league_categories: list,
    all_categories: list[Category],
    catalog: DynamicCatalog,
    league_teammates: dict[str, list[Category]] | None = None,
) -> dict[str, list[Category]]:
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

    `league_teammates` (see build_dynamic_league_teammates) adds each
    league's own "played with X" anchors on top, unwrapped — those are
    already computed with that league's own club list as overlap_club_names,
    so wrapping them again with LeagueScopedCategory would be redundant, and
    they're deliberately absent from `all_categories`/the general pool (a
    Bundesliga-only legend has no business anchoring a category in "Alle
    Ligen" mode or another league's puzzles).
    """
    from .categories import CategoryType, LeagueScopedCategory

    league_teammates = league_teammates or {}
    pools: dict[str, list[Category]] = {}
    for league in league_categories:
        club_names = set(league.club_names)
        league_clubs = [c for c in catalog.clubs if c.club_name in club_names]
        wrapped = [
            LeagueScopedCategory(cat, league.club_names, id=f"{cat.id}__{league.id}", label=cat.label)
            for cat in all_categories
            if cat.type not in (CategoryType.CLUB, CategoryType.LEAGUE, CategoryType.CONTINENT)
        ]
        pools[league.id] = league_clubs + wrapped + league_teammates.get(league.id, [])
    return pools
