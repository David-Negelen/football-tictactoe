"""Semantic filtering for player_trophies.title -> which titles become
real TrophyCategory instances.

659 distinct titles exist in the data. The raw list mixes in individual
awards (Torschützenkönig), youth/reserve-team competitions (A-Junioren-
Meister, Primavera), regional/lower-tier honors (Landespokal-*,
Zweitligameister) — and, just as important, a long tail of trophies that
are technically "real" silverware but not what anyone means by "the major
honors": domestic Super Cups (a single exhibition match, not a competition
— the FA Community Shield, DFL-Supercup, Supercoppa Italiana and their
equivalents in every country), league cups (a genuine second cup, but
clearly a notch below the national cup everywhere it coexists with one),
second-tier continental club competitions (Copa Sudamericana, AFC Cup,
CONCACAF League, CAF Confederation Cup — each confederation's Europa-
League-equivalent, not its Champions-League-equivalent), Nations Leagues,
regional multi-sport games, and one-off exhibition trophies (Finalissima).

The policy this module implements: every domestic league's *top-flight
title* and *one major cup*, and — for international/continental honors —
the World Cup, the Olympics, the (defunct but genuinely major)
Confederations Cup, the Club World Cup, and exactly one top national-team
tournament and one top club tournament per FIFA confederation (UEFA gets
three tiers of club competition — Champions League, Europa League, Europa
Conference League — since all three are still meaningfully prestigious;
every other confederation gets just its Champions-League-equivalent).

Domestic honors scale across ~70 countries by pattern (meister/pokal-
sieger/cupsieger), since transfermarkt already only tracks each country's
real top flight and major cup under those names — hardcoding every country
would be unmaintainable. International honors go the other way: pattern
matching on words like "sieger"/"champion"/"winner" is far too broad (it
happily matches "AFC Cup-Sieger" and "UEFA-Supercup-Sieger" right alongside
"Weltmeister"), so that tier is an explicit, hand-curated allowlist
instead.

Exclude-patterns are checked first (order matters — a title excluded by any
of them never reaches the include check), then a title is included only if
it also matches one of the include-words. This two-pass design is what lets
broad include-words like "meister"/"sieger" be used safely for the domestic
tier: they alone would also match plenty of excluded titles, but by
construction those never survive the exclude pass.

`audit_trophy_titles`/`__main__` below re-run the classification against
the live DB and print every included/excluded title with its occurrence
count — the fastest way to eyeball whether some newly-imported title (or an
obscure one from a small league not specifically reasoned about here) needs
a rule adjustment.
"""

from __future__ import annotations

import re

EXCLUDE_INDIVIDUAL = re.compile(
    r"(torschützenkönig|fußballer|fussballer|spieler der|spieler des|"
    r"torhüter der|\bmvp\b|golden boy|goldenen? schuh|"
    r"fritz-walter-medaille|torjäger|puskás|ballon d'or)",
    re.IGNORECASE,
)
EXCLUDE_YOUTH = re.compile(
    r"(\bu-?\d{1,2}\b|jugend|junioren|juniores|primavera|amateur|nachwuchs|"
    r"viareggio|algarve|premier league 2\b|premier league international cup|"
    r"premier league cup|proyección|"
    # Reserve/development leagues that don't read as "U-something" (MLS's
    # is branded as its own league, not an age group).
    r"mls next pro)",
    re.IGNORECASE,
)
EXCLUDE_LOWER_TIER = re.compile(
    r"(zweitliga|drittliga|viertliga|fünftliga|regionalliga|"
    r"landespokal|landesmeister|bezirk|kreis|verbandsliga|oberliga|"
    r"serie c|serie d|"
    # Second-division/lower-tier leagues that don't fit the patterns above
    # because they're named after a region/city rather than a tier number.
    r"série b|meister 2\.\s?liga|primera nacional|\bprimera b\b|superettan|"
    r"westfalenliga|bayernliga|hessenliga|bremenliga|kärntner liga|"
    r"eliteliga vorarlberg|landesliga steiermark|oberösterreich liga|"
    r"tirol liga|landesliga niederösterreich|wiener stadtliga|"
    r"niedersachsenmeister|burgenlandliga|"
    # State/regional leagues below the actual national top flight (the
    # Australian A-League and Indian ISL are tracked separately).
    r"npl victoria|super league kerala|"
    # Lower-tier domestic cups that coexist with the real national cup.
    r"football league trophy|challenge-cup-sieger|copa rfef|"
    # Brazilian state championships (Campeonato Paulista etc.) are a real
    # regional tier below the national Brasileirão ("Brasilianischer
    # Meister", kept separately), not the national title itself.
    r"campeão paulista|campeão carioca|campeão gaúcho|campeão mineiro|"
    r"taça rio|copa do nordeste|"
    # Pre-DFB-Pokal-unification regional German cups.
    r"westdeutscher pokalsieger|norddeutscher pokalsieger|"
    # North American second-tier leagues below MLS/CPL.
    r"usl championship|usl1\b|\bnasl\b)",
    re.IGNORECASE,
)
EXCLUDE_RUNNER_UP = re.compile(
    r"(zweiter\b|vizemeister|finalist|runner-up|2\.\s?platz)",
    re.IGNORECASE,
)

# Domestic Super Cups (a single season-curtain-raiser exhibition match, not
# a competition) in every language/spelling the data uses — this is the
# single biggest source of "Mickey Mouse" categories, e.g. the FA Community
# Shield ("Englischer Superpokalsieger") sitting right next to the actual
# FA Cup with equal visual weight.
EXCLUDE_SUPER_CUP = re.compile(r"super(pokal|cup|coppa|copa)", re.IGNORECASE)

# League Cups are genuine competitions, but everywhere they coexist with a
# national cup they're a clear notch below it (English League Cup vs. FA
# Cup, DFL-Ligapokal vs. DFB-Pokal, etc.) — only the one "major cup" per
# country is kept.
EXCLUDE_LEAGUE_CUP = re.compile(r"(liga(pokal|cup)|\bleague cup\b)", re.IGNORECASE)

# Everything else that's technically a real trophy but not a "major" honor:
# each confederation's second-tier club competition (its Europa-League-
# equivalent, kept distinct from its Champions-League-equivalent, which
# *is* kept — see INTERNATIONAL_ALLOW_TITLES), Nations Leagues, regional
# multi-sport games (a tier below the Olympics), a defunct home-players-
# only AFCON variant, redundant secondary Gulf-state cups, and one-off
# exhibition trophies.
EXCLUDE_MINOR_INTERNATIONAL = {
    "UI-Cup-Sieger",
    "Intertoto-Cup-Sieger",
    "Messe-Cup-Sieger",
    "Mitropacup-Sieger",
    "Europapokal-der-Pokalsieger-Sieger",
    "Recopa Sudamericana-Sieger",
    "Copa Sudamericana-Sieger",
    "Supercopa Sudamericana-Sieger",
    "AFC Cup-Sieger",
    "CONCACAF League-Sieger",
    "CAF-Confederation-Cup-Sieger",
    "CAF-Super-Cup-Sieger",
    "UEFA-Youth-League-Sieger",
    "Campeones Cup-Sieger",
    "Leagues-Cup-Sieger",
    "CONMEBOL-UEFA Cup of Champions-Sieger",
    "Sieger UEFA Nations League",
    "CONCACAF Nations League-Sieger",
    "Sieger Afrikanische Nationenmeisterschaft",
    "U23-Afrikameister",
    "FIFA African-Asian-Pacific Cup Champion",
    "Ostasienmeister",
    "Westasienmeister",
    "Mittelamerikameister",
    "Karibikmeister",
    "Südostasienmeister",
    "Asian Games Goldmedaille",
    "Gewinner der Pan-Amerikanischen Spiele",
    "Zentralamerika- und Karibikspiele Gewinner",
    "Sieger Südamerikaspiele",
    "Southeast Asian Games Sieger",
    "CPL Fall Season Champion",
    "CPL Spring Season Champion",
    # "Regular season leader" / "minor premiership" honors are a secondary
    # award alongside the actual title decider (kept separately) in leagues
    # that settle the real championship via playoffs.
    "Sieger ISL Regular Season",
    "Minor-Premiership-Sieger (NZL)",
    # More defunct/historical secondary continental club competitions, same
    # tier as Copa Sudamericana/Recopa Sudamericana/AFC Cup above.
    "Sieger Copa Mercosur",
    "Copa-CONMEBOL-Sieger",
    "Copa Suruga Bank-Sieger",
    "Asiatischer-Pokal-der-Pokalsieger-Sieger",
    "Sieger Coupe Charles Drago",
    # Sub-confederation zonal club/national-team tournaments (a tier below
    # a full confederation's championship, same reasoning as Ostasienmeister
    # etc. above).
    "UNCAF Klub-Sieger",
    "ASEAN Club Championship-Sieger",
    "Caribbean-Club-Championship-Sieger",
    "Asian Club Championship Sieger",
    "Balkan-Cup-Sieger",
    "Golfpokal-Sieger",
    "CAFA Nations Cup Sieger",
    # Provincial/secondary cups that coexist with the actual national cup
    # (Ireland's "Irischer Pokalsieger" / Hong Kong's "Hongkongnesischer
    # Pokalsieger" are kept separately as the major one).
    "Munster Senior Cup Sieger",
    "Leinster Senior Cup Sieger",
    "Hongkong Senior Challenge Shield Gewinner",
    "Hongkong Viceroy Pokalsieger",
    "Hongkong Sapling Cup Sieger",
    "Derby of the Americas Champion",
    "Challenger Cup Champion",
    # Made-for-TV / knockout-of-last-season's-top-8 style domestic cups,
    # the same "exhibition, not a competition" issue as a Super Cup.
    "MTN8-Cup-Sieger",
    "Costa Ricanischer Recopa-Sieger",
    "MLS is Back Champion",
    "Australischer NPL Victoria Meister (Premiers)",
    # Redundant secondary domestic cups in countries that already have a
    # "the major cup" entry kept elsewhere (a Gulf-state pattern: several
    # countries there run 2-3 differently-branded cups in parallel).
    "VAE President's Cup Sieger",
    "Saudi Crown-Prince-Cup-Sieger",
    "Qatari-Stars-Cup-Sieger",
    "UAE-League-Cup-Sieger",
    "Katarischer-League-Cup-Sieger",
    "Katarischer-Super-Cup-Sieger (Sheikh Jassim Cup)",
}

DOMESTIC_INCLUDE_WORDS = re.compile(
    r"(meister|sieger|gewinner|champion|campeão|campeón|winner|"
    r"scudetto|goldmedaille)",
    re.IGNORECASE,
)

# International/continental honors: precision matters here (see the module
# docstring — broad word matching over-includes far too much), so this
# tier is an explicit allowlist rather than a pattern. One top national-
# team and one top club trophy per FIFA confederation, plus the two
# genuinely global honors and UEFA's extra two competition tiers.
INTERNATIONAL_ALLOW_TITLES = {
    # Global
    "Weltmeister",                          # FIFA World Cup
    "Weltpokalsieger",                      # Intercontinental Cup / Club World Cup, pre-2000s name
    "FIFA-Klub-Weltmeister",                # Club World Cup, 2000s-2023 name
    "FIFA Interkontinental-Pokal-Sieger",   # Club World Cup, 2024- name (revived Intercontinental Cup)
    "Olympiasieger",
    "Confederations-Cup-Sieger",
    # UEFA
    "Europameister",
    "UEFA Champions League-Sieger",
    "Europapokal-der-Landesmeister-Sieger",  # old name for the above
    "Europa-League-Sieger",
    "Uefa-Cup-Sieger",                       # old name for the above
    "Conference League-Sieger",
    # CONMEBOL
    "Copa América-Sieger",
    "Copa Libertadores-Sieger",
    # CAF
    "Afrikameister",
    "CAF-Champions-League-Sieger",
    # CONCACAF
    "Gold-Cup-Sieger",
    "CONCACAF-Championship-Sieger",          # old name for the above
    "CONCACAF-Champions-League-Sieger",
    "CONCACAF-Champions-Cup-Sieger",         # old/new naming for the same competition
    # AFC
    "Asienmeister",
    "AFC-Champions-League-Sieger",
    # OFC
    "OFC-Nationen-Pokal-Sieger",
    "OFC-Champions-League-Sieger",
}

# International youth tournaments (national team, not club academy) are
# genuinely legitimate honors — e.g. "U20-Weltmeister" was already
# hand-curated before this module existed. EXCLUDE_YOUTH's `\bu-?\d{1,2}\b`
# would otherwise catch these too, so they're allowed back in explicitly.
# (U23-Afrikameister is deliberately excluded via EXCLUDE_MINOR_INTERNATIONAL
# above instead — it's a qualification-tier competition, not a senior honor.)
_YOUTH_INTERNATIONAL_ALLOW = re.compile(
    r"u-?\d{1,2}[\s-]*(weltmeister|europameister)",
    re.IGNORECASE,
)


def classify_trophy_title(title: str) -> bool:
    """True if `title` should become a TrophyCategory."""
    if title in INTERNATIONAL_ALLOW_TITLES:
        return True
    if title in EXCLUDE_MINOR_INTERNATIONAL:
        return False
    if _YOUTH_INTERNATIONAL_ALLOW.search(title):
        return True
    if EXCLUDE_INDIVIDUAL.search(title):
        return False
    if EXCLUDE_YOUTH.search(title):
        return False
    if EXCLUDE_LOWER_TIER.search(title):
        return False
    if EXCLUDE_RUNNER_UP.search(title):
        return False
    if EXCLUDE_SUPER_CUP.search(title):
        return False
    if EXCLUDE_LEAGUE_CUP.search(title):
        return False
    return bool(DOMESTIC_INCLUDE_WORDS.search(title))


def audit_trophy_titles(conn) -> dict:
    """Classify every distinct trophy title in the DB. Returns
    {"included": [(title, count), ...], "excluded": [(title, count), ...]},
    both sorted by count descending — meant to be eyeballed (or diffed
    across data refreshes) before shipping, not asserted on line-by-line."""
    rows = conn.execute(
        "SELECT title, COUNT(*) AS n FROM player_trophies GROUP BY title ORDER BY n DESC"
    ).fetchall()
    included, excluded = [], []
    for row in rows:
        title, n = row[0], row[1]
        (included if classify_trophy_title(title) else excluded).append((title, n))
    return {"included": included, "excluded": excluded}


if __name__ == "__main__":
    import os
    import sqlite3

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "tictactoe.db")
    conn = sqlite3.connect(db_path)
    result = audit_trophy_titles(conn)
    print(f"Included: {len(result['included'])}")
    print(f"Excluded: {len(result['excluded'])}")
    print("\n--- Excluded titles (review these) ---")
    for title, n in result["excluded"]:
        print(f"{n}\t{title}")
