"""Reference data mapping Transfermarkt's German nationality strings to
ISO 3166-1 codes and European/UEFA membership.

This replaces the old ad-hoc `_EUROPEAN_NATIONALITIES` list in
`src/categories.py` with a single, larger source of truth, and adds the
data needed for something the game didn't have before: parsing
dual-national compound strings ("Deutschland Türkei") into individual
country tokens, without ever splitting a genuine multi-word country name
in half (e.g. "Vereinigte Staaten" must stay one token).

Player counts referenced in comments are from a full scan of
`players.nationality` in the real dataset (see conversation/plan notes) —
this list intentionally covers every distinct nationality string with
enough players to matter, not just the ~19 that were hand-curated before.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Country:
    name: str          # exact string as it appears in players.nationality
    iso_code: str       # ISO 3166-1 alpha-2 (best-effort for non-standard entries)
    is_european: bool    # UEFA-membership-flavored "European" flag, matching the
                          # convention already established by the old European list
                          # (e.g. Türkei, Russland, Georgien, Armenien, Aserbaidschan
                          # count as European here, matching UEFA membership)


COUNTRIES: list[Country] = [
    # ── Europe (UEFA) — matches/extends the old _EUROPEAN_NATIONALITIES list ──
    Country("Deutschland", "DE", True),
    Country("Italien", "IT", True),
    Country("Spanien", "ES", True),
    Country("Niederlande", "NL", True),
    # England/Scotland/Wales/Northern Ireland have no ISO 3166-1 code of
    # their own (they're part of GB) — see _FLAG_IMAGE_CODE_OVERRIDES below
    # for the flagcdn.com subdivision codes their flag images actually use.
    Country("England", "GB", True),
    Country("Frankreich", "FR", True),
    Country("Schottland", "GB", True),
    Country("Dänemark", "DK", True),
    Country("Serbien", "RS", True),
    Country("Kroatien", "HR", True),
    Country("Polen", "PL", True),
    Country("Belgien", "BE", True),
    Country("Österreich", "AT", True),
    Country("Irland", "IE", True),
    Country("Portugal", "PT", True),
    Country("Schweden", "SE", True),
    Country("Tschechien", "CZ", True),
    Country("Norwegen", "NO", True),
    Country("Wales", "GB", True),
    Country("Rumänien", "RO", True),
    Country("Nordirland", "GB", True),
    Country("Griechenland", "GR", True),
    Country("Schweiz", "CH", True),
    Country("Türkei", "TR", True),
    Country("Ungarn", "HU", True),
    Country("Slowenien", "SI", True),
    Country("Slowakei", "SK", True),
    Country("Bulgarien", "BG", True),
    Country("Island", "IS", True),
    Country("Finnland", "FI", True),
    Country("Bosnien-Herzegowina", "BA", True),
    Country("Russland", "RU", True),
    Country("Ukraine", "UA", True),
    Country("Montenegro", "ME", True),
    Country("Georgien", "GE", True),
    Country("Nordmazedonien", "MK", True),
    Country("Litauen", "LT", True),
    Country("Albanien", "AL", True),
    Country("Luxemburg", "LU", True),
    Country("Lettland", "LV", True),
    Country("Estland", "EE", True),
    # DB uses "Belarus", not the old list's "Weißrussland" — that old entry
    # never matched anything real (a latent bug in the previous exclusion list).
    Country("Belarus", "BY", True),
    Country("Zypern", "CY", True),
    Country("Färöer", "FO", True),
    Country("Malta", "MT", True),
    Country("Kosovo", "XK", True),
    Country("Armenien", "AM", True),
    Country("Andorra", "AD", True),
    Country("Moldawien", "MD", True),
    Country("Liechtenstein", "LI", True),
    Country("Guernsey", "GG", True),
    Country("Aserbaidschan", "AZ", True),
    Country("Jersey", "JE", True),
    Country("San Marino", "SM", True),
    Country("DDR", "DE", True),  # historical East Germany — see _NO_REAL_FLAG_IMAGE

    # ── South America ──
    Country("Brasilien", "BR", False),
    Country("Argentinien", "AR", False),
    Country("Uruguay", "UY", False),
    Country("Kolumbien", "CO", False),
    Country("Paraguay", "PY", False),
    Country("Chile", "CL", False),
    Country("Peru", "PE", False),
    Country("Venezuela", "VE", False),
    Country("Ecuador", "EC", False),
    Country("Suriname", "SR", False),

    # ── North/Central America & Caribbean ──
    Country("Vereinigte Staaten", "US", False),
    Country("Mexiko", "MX", False),
    Country("Kanada", "CA", False),
    Country("Costa Rica", "CR", False),
    Country("Jamaika", "JM", False),
    Country("Panama", "PA", False),
    Country("Honduras", "HN", False),
    Country("Haiti", "HT", False),
    Country("Guatemala", "GT", False),
    Country("Trinidad und Tobago", "TT", False),
    Country("Dominikanische Republik", "DO", False),
    Country("Curacao", "CW", False),
    Country("Bermuda", "BM", False),
    Country("St. Lucia", "LC", False),
    Country("Puerto Rico", "PR", False),
    Country("El Salvador", "SV", False),

    # ── Africa ──
    Country("Senegal", "SN", False),
    Country("Nigeria", "NG", False),
    Country("Ghana", "GH", False),
    Country("Kamerun", "CM", False),
    Country("Elfenbeinküste", "CI", False),
    Country("Marokko", "MA", False),
    Country("Mali", "ML", False),
    Country("Tunesien", "TN", False),
    Country("Guinea", "GN", False),
    Country("Algerien", "DZ", False),
    Country("Südafrika", "ZA", False),
    Country("Ägypten", "EG", False),
    Country("Gambia", "GM", False),
    Country("Sambia", "ZM", False),
    Country("Togo", "TG", False),
    Country("Liberia", "LR", False),
    Country("Gabun", "GA", False),
    Country("Kongo", "CG", False),
    Country("Simbabwe", "ZW", False),
    Country("Angola", "AO", False),
    Country("Benin", "BJ", False),
    Country("Mauretanien", "MR", False),
    Country("Tschad", "TD", False),
    Country("Niger", "NE", False),
    Country("Madagaskar", "MG", False),
    Country("Libyen", "LY", False),
    Country("Kenia", "KE", False),
    Country("Mosambik", "MZ", False),
    Country("Malawi", "MW", False),
    Country("Tansania", "TZ", False),
    Country("Namibia", "NA", False),
    Country("Mauritius", "MU", False),
    Country("Burundi", "BI", False),
    Country("Äquatorialguinea", "GQ", False),
    Country("Uganda", "UG", False),
    Country("Südsudan", "SS", False),
    Country("Somalia", "SO", False),
    Country("Burkina Faso", "BF", False),
    Country("Sierra Leone", "SL", False),
    Country("Kap Verde", "CV", False),
    Country("DR Kongo", "CD", False),

    # ── Asia & Middle East ──
    Country("Japan", "JP", False),
    Country("Südkorea", "KR", False),
    Country("Israel", "IL", False),
    Country("Iran", "IR", False),
    Country("China", "CN", False),
    Country("Saudi-Arabien", "SA", False),
    Country("Usbekistan", "UZ", False),
    Country("Irak", "IQ", False),
    Country("Vietnam", "VN", False),
    Country("Nordkorea", "KP", False),
    Country("Thailand", "TH", False),
    Country("Singapur", "SG", False),
    Country("Oman", "OM", False),
    Country("Malaysia", "MY", False),
    Country("Libanon", "LB", False),
    Country("Kuwait", "KW", False),
    Country("Jordanien", "JO", False),
    Country("Afghanistan", "AF", False),
    Country("Katar", "QA", False),
    Country("Vereinigte Arabische Emirate", "AE", False),

    # ── Oceania & other ──
    Country("Australien", "AU", False),
    Country("Neuseeland", "NZ", False),
    Country("Tahiti", "PF", False),
    Country("Monaco", "MC", True),  # geographically enclaved in France, plays as its own UEFA-adjacent entity historically
    Country("Martinique", "MQ", False),

    # ── Long-tail entries needed to parse rarer dual-national compounds ──
    Country("Guadeloupe", "GP", False),
    Country("Komoren", "KM", False),
    Country("Réunion", "RE", False),
    Country("Guinea-Bissau", "GW", False),
    Country("Indonesien", "ID", False),
    Country("Barbados", "BB", False),
    Country("Zentralafrikanische Republik", "CF", False),
    Country("Französisch-Guayana", "GF", False),
    Country("Philippinen", "PH", False),
    Country("Aruba", "AW", False),
    Country("Montserrat", "MS", False),
    Country("Guyana", "GY", False),
    Country("Grenada", "GD", False),
    Country("St. Kitts und Nevis", "KN", False),
    Country("Kasachstan", "KZ", False),
    Country("Saint-Martin", "MF", False),
    Country("Sao Tome und Principe", "ST", False),
    Country("Indien", "IN", False),
    Country("Dominica", "DM", False),
    # Historical Yugoslavia — no modern ISO code; both parenthetical variants
    # appear in the data as distinct raw strings, so both need entries.
    Country("Jugoslawien (SFR)", "RS", True),
    Country("Jugoslawien (Bundesrepublik)", "RS", True),

    # ── Final long-tail batch (each affects only a handful of players) ──
    Country("Neukaledonien", "NC", False),
    Country("St. Vincent und die Grenadinen", "VC", False),
    Country("Antigua und Barbuda", "AG", False),
    Country("Eritrea", "ER", False),
    Country("Sri Lanka", "LK", False),
    Country("Syrien", "SY", False),
    Country("Kirgisistan", "KG", False),
    Country("Kuba", "CU", False),
    Country("Palästina", "PS", False),
    Country("Seychellen", "SC", False),
    Country("Niederländische Antillen", "AN", False),  # dissolved territory, no current ISO code
    Country("Pakistan", "PK", False),
    Country("Laos", "LA", False),
    Country("Äthiopien", "ET", False),
    Country("Gibraltar", "GI", True),
    Country("Ruanda", "RW", False),
    Country("Tadschikistan", "TJ", False),
    Country("Hongkong", "HK", False),
]


COUNTRY_BY_NAME: dict[str, Country] = {c.name: c for c in COUNTRIES}

# Sorted longest-name-first so multi-word names (e.g. "Vereinigte Staaten",
# "Vereinigte Arabische Emirate") are matched before any of their words could
# be mistaken for the start of a different token during compound parsing.
_NAMES_BY_LENGTH_DESC: list[str] = sorted(COUNTRY_BY_NAME, key=len, reverse=True)


# flagcdn.com's image code per country — usually just the lowercased ISO
# code, except for a handful of overrides (UK constituent countries use
# flagcdn's "gb-<subdivision>" convention; Kosovo uses "xk"). Countries with
# no real current flag (dissolved states/historical entities — see
# _NO_REAL_FLAG_IMAGE) have no image; see fetch_flags.py, which downloads a
# static/flags/<code>.png per code. A nationality with neither a real image
# nor a downloaded one falls back to a generic icon client-side (see
# app.py's _cat_display) rather than any per-country substitute.
_FLAG_IMAGE_CODE_OVERRIDES = {
    "England": "gb-eng",
    "Schottland": "gb-sct",
    "Wales": "gb-wls",
    "Nordirland": "gb-nir",
    "Kosovo": "xk",
}
_NO_REAL_FLAG_IMAGE = {"DDR", "Tahiti", "Jugoslawien (SFR)", "Jugoslawien (Bundesrepublik)", "Niederländische Antillen"}


def country_flag_image_code(name: str) -> str | None:
    """The flagcdn.com code for this country's flag image, or None if it has
    no real current flag (see _NO_REAL_FLAG_IMAGE) or isn't a known country."""
    country = COUNTRY_BY_NAME.get(name)
    if country is None or name in _NO_REAL_FLAG_IMAGE:
        return None
    return _FLAG_IMAGE_CODE_OVERRIDES.get(name, country.iso_code.lower())


def parse_nationality_tokens(raw: str) -> list[str]:
    """Split a possibly-compound nationality string ("Deutschland Türkei")
    into the individual country names it's built from.

    Transfermarkt stores dual nationals as space-separated country names,
    but several individual country names are themselves multi-word
    ("Vereinigte Staaten", "DR Kongo", "Trinidad und Tobago", ...), so a
    naive `str.split()` would wrongly fracture those. This greedily matches
    known country names (longest first) against the remaining text instead.

    Returns an empty list if any leftover text can't be matched to a known
    country — callers should treat that as "unparseable" rather than
    guessing, since silently misparsing a nationality would corrupt puzzle
    generation for that player.
    """
    remaining = raw.strip()
    tokens: list[str] = []
    while remaining:
        for name in _NAMES_BY_LENGTH_DESC:
            if remaining == name or remaining.startswith(name + " "):
                tokens.append(name)
                remaining = remaining[len(name):].strip()
                break
        else:
            return []  # no known country name matches what's left — unparseable
    return tokens
