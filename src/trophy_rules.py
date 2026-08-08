"""Semantic filtering for player_trophies.title -> which titles become
real TrophyCategory instances.

659 distinct titles exist in the data; the vast majority are legitimate
team silverware (domestic titles, cups, continental trophies, international
tournaments), but the raw list also mixes in individual awards
(Torschützenkönig), youth/reserve-team competitions (A-Junioren-Meister,
Primavera), and regional/lower-tier honors (Landespokal-*, Zweitligameister)
that would make for confusing or trivial grid cells.

Exclude-patterns are checked first (order matters — a title excluded by any
of them never reaches the include check), then a title is included only if
it also matches one of the include-words. This two-pass design is what lets
broad include-words like "meister"/"sieger" be used safely: they alone would
also match plenty of excluded titles, but by construction those never survive
the exclude pass.
"""

from __future__ import annotations

import re

EXCLUDE_INDIVIDUAL = re.compile(
    r"(torschützenkönig|fußballer|fussballer|spieler der|spieler des|"
    r"torhüter der|\bmvp\b|golden boy|goldenen? schuh|"
    r"fritz-walter-medaille|torjäger|puskás)",
    re.IGNORECASE,
)
EXCLUDE_YOUTH = re.compile(
    r"(\bu-?\d{1,2}\b|jugend|junioren|primavera|amateur|nachwuchs|"
    r"viareggio|algarve)",
    re.IGNORECASE,
)
EXCLUDE_LOWER_TIER = re.compile(
    r"(zweitliga|drittliga|viertliga|fünftliga|regionalliga|"
    r"landespokal|landesmeister|bezirk|kreis|verbandsliga|oberliga|"
    r"serie c|serie d)",
    re.IGNORECASE,
)
EXCLUDE_RUNNER_UP = re.compile(
    r"(zweiter\b|vizemeister|finalist|runner-up|2\.\s?platz)",
    re.IGNORECASE,
)

INCLUDE_WORDS = re.compile(
    r"(meister|sieger|gewinner|champion|campeão|campeón|winner|"
    r"scudetto|goldmedaille)",
    re.IGNORECASE,
)

# International youth tournaments (national team, not club academy) are
# genuinely legitimate honors — e.g. "U20-Weltmeister" was already
# hand-curated before this module existed. EXCLUDE_YOUTH's `\bu-?\d{1,2}\b`
# would otherwise catch these too, so they're allowed back in explicitly.
_YOUTH_INTERNATIONAL_ALLOW = re.compile(
    r"u-?\d{1,2}[\s-]*(weltmeister|europameister|afrikameister)",
    re.IGNORECASE,
)

# "Landesmeister" is ambiguous: EXCLUDE_LOWER_TIER's "landesmeister" pattern
# is meant for regional amateur titles like "Landesmeister Schleswig-Holstein",
# but the exact same substring also appears in "Europapokal der Landesmeister"
# — the old name for the European Cup (Champions League's predecessor), a
# major trophy that must not be excluded. Only this one real title uses the
# phrase that way in the data, so it's carved out explicitly rather than
# trying to write a regex that reliably tells "regional title" apart from
# "competition named after champions" from the word alone.
_EXPLICIT_ALLOW_TITLES = {"Europapokal-der-Landesmeister-Sieger"}


def classify_trophy_title(title: str) -> bool:
    """True if `title` should become a TrophyCategory."""
    if title in _EXPLICIT_ALLOW_TITLES:
        return True
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
    return bool(INCLUDE_WORDS.search(title))


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
