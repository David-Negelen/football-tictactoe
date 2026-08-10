"""Whitelist of hand-curated categories available for puzzle generation —
everything EXCEPT clubs, nationalities, and trophies, which are generated
dynamically from the real dataset at app startup instead (see
src/dynamic_categories.py). Those three used to be small hand-picked lists
here; they were retired in favor of dynamic generation because they were
confirmed to be nothing more than a hand-picked subset of what the dynamic
generator produces anyway, and keeping both would mean maintaining two
divergent id schemes for the same clubs/nationalities/trophies.

Position prefixes match players.position using a LIKE prefix query.
"""

from __future__ import annotations

from .categories import AgeCategory, Category, ContainsLetterCategory, ContinentCategory, InitialCategory, LeagueCategory, MarketValueCategory, NonEuropeanNationalityCategory, PositionCategory


POSITION_CATEGORIES: list[PositionCategory] = [
    PositionCategory("pos_gk",  "Torwart",               "Torwart",                          difficulty=1),
    PositionCategory("pos_def", "Abwehrspieler",         "Abwehr",                           difficulty=1),
    PositionCategory("pos_mid", "Mittelfeldspieler",     "Mittelfeld",                       difficulty=1),
    PositionCategory("pos_fwd", "Stürmer",               "Sturm",                            difficulty=1),
    PositionCategory("pos_cb",  "Innenverteidiger",      "Abwehr - Innenverteidiger",        difficulty=2),
    PositionCategory("pos_lb",  "Linker Verteidiger",    "Abwehr - Linker Verteidiger",      difficulty=3),
    PositionCategory("pos_rb",  "Rechter Verteidiger",   "Abwehr - Rechter Verteidiger",     difficulty=3),
    PositionCategory("pos_lw",  "Linksaußen",            "Sturm - Linksaußen",               difficulty=3),
    PositionCategory("pos_rw",  "Rechtsaußen",           "Sturm - Rechtsaußen",              difficulty=3),
    # Sub-positions covering the rest of the 18 distinct values players.position
    # actually takes — the 9 above only covered half of the real data.
    PositionCategory("pos_st",  "Mittelstürmer",         "Sturm - Mittelstürmer",            difficulty=1),
    PositionCategory("pos_cm",  "Zentrales Mittelfeld",  "Mittelfeld - Zentrales Mittelfeld", difficulty=2),
    PositionCategory("pos_dm",  "Defensives Mittelfeld", "Mittelfeld - Defensives Mittelfeld", difficulty=2),
    PositionCategory("pos_am",  "Offensives Mittelfeld", "Mittelfeld - Offensives Mittelfeld", difficulty=2),
    PositionCategory("pos_rm",  "Rechtes Mittelfeld",    "Mittelfeld - Rechtes Mittelfeld",   difficulty=3),
    PositionCategory("pos_lm",  "Linkes Mittelfeld",     "Mittelfeld - Linkes Mittelfeld",    difficulty=3),
    PositionCategory("pos_ss",  "Hängende Spitze",       "Sturm - Hängende Spitze",           difficulty=3),
    PositionCategory("pos_sw",  "Libero",                "Abwehr - Libero",                   difficulty=3),
]

INITIAL_CATEGORIES: list[InitialCategory] = [
    # difficulty 1 — most common first+last combos in European football
    InitialCategory("init_m", "Vor- oder Nachname beginnt mit M", "M", difficulty=1),
    InitialCategory("init_s", "Vor- oder Nachname beginnt mit S", "S", difficulty=1),
    # difficulty 2 — common
    InitialCategory("init_b", "Vor- oder Nachname beginnt mit B", "B", difficulty=2),
    InitialCategory("init_d", "Vor- oder Nachname beginnt mit D", "D", difficulty=2),
    InitialCategory("init_h", "Vor- oder Nachname beginnt mit H", "H", difficulty=2),
    InitialCategory("init_k", "Vor- oder Nachname beginnt mit K", "K", difficulty=2),
    InitialCategory("init_l", "Vor- oder Nachname beginnt mit L", "L", difficulty=2),
    InitialCategory("init_r", "Vor- oder Nachname beginnt mit R", "R", difficulty=2),
    InitialCategory("init_t", "Vor- oder Nachname beginnt mit T", "T", difficulty=2),
    # difficulty 3 — less common
    InitialCategory("init_a", "Vor- oder Nachname beginnt mit A", "A", difficulty=3),
    InitialCategory("init_c", "Vor- oder Nachname beginnt mit C", "C", difficulty=3),
    InitialCategory("init_e", "Vor- oder Nachname beginnt mit E", "E", difficulty=3),
    InitialCategory("init_f", "Vor- oder Nachname beginnt mit F", "F", difficulty=3),
    InitialCategory("init_g", "Vor- oder Nachname beginnt mit G", "G", difficulty=3),
    InitialCategory("init_j", "Vor- oder Nachname beginnt mit J", "J", difficulty=3),
    InitialCategory("init_n", "Vor- oder Nachname beginnt mit N", "N", difficulty=3),
    InitialCategory("init_o", "Vor- oder Nachname beginnt mit O", "O", difficulty=3),
    InitialCategory("init_p", "Vor- oder Nachname beginnt mit P", "P", difficulty=3),
    InitialCategory("init_w", "Vor- oder Nachname beginnt mit W", "W", difficulty=3),
]

CONTAINS_LETTER_CATEGORIES: list[ContainsLetterCategory] = [
    ContainsLetterCategory("cont_letter_i", "Name enthält den Buchstaben I", "I", difficulty=2),
    ContainsLetterCategory("cont_letter_u", "Name enthält den Buchstaben U", "U", difficulty=2),
    ContainsLetterCategory("cont_letter_v", "Name enthält den Buchstaben V", "V", difficulty=3),
    ContainsLetterCategory("cont_letter_x", "Name enthält den Buchstaben X", "X", difficulty=3),
    ContainsLetterCategory("cont_letter_y", "Name enthält den Buchstaben Y", "Y", difficulty=3),
    ContainsLetterCategory("cont_letter_z", "Name enthält den Buchstaben Z", "Z", difficulty=3),
    ContainsLetterCategory("cont_letter_q", "Name enthält den Buchstaben Q", "Q", difficulty=3),
]

AGE_CATEGORIES: list[AgeCategory] = [
    AgeCategory("age_u23",  "Unter 23 Jahre",  max_age=22,              difficulty=2),
    AgeCategory("age_2430", "24–30 Jahre",     min_age=24, max_age=30,  difficulty=2),
    AgeCategory("age_30p",  "Über 30 Jahre",   min_age=31,              difficulty=2),
]

MARKET_VALUE_CATEGORIES: list[MarketValueCategory] = [
    MarketValueCategory("mv_high", "Marktwert ≥ 50 Mio. €", min_value=50_000_000,                            difficulty=2),
    MarketValueCategory("mv_mid",  "Marktwert 10–50 Mio. €", min_value=10_000_000, max_value=50_000_000,     difficulty=2),
    MarketValueCategory("mv_low",  "Marktwert < 10 Mio. €",                         max_value=10_000_000,    difficulty=3),
]

NON_EUROPEAN_CATEGORIES: list[NonEuropeanNationalityCategory] = [
    NonEuropeanNationalityCategory("nat_noneu", "Nicht-Europäer", difficulty=2),
]


LEAGUE_CATEGORIES: list[LeagueCategory] = [
    LeagueCategory("league_buli", "Bundesliga", [
        "FC Augsburg", "Union Berlin", "Werder Bremen", "Bor. Dortmund",
        "SV Elversberg", "E. Frankfurt", "SC Freiburg", "Hamburger SV",
        "TSG Hoffenheim", "1.FC Köln", "RB Leipzig", "B. Leverkusen",
        "1.FSV Mainz 05", "Bor. M'gladbach", "Bayern München", "SC Paderborn",
        "FC Schalke 04", "VfB Stuttgart",
    ], difficulty=1),
    LeagueCategory("league_pl", "Premier League", [
        "Arsenal", "Aston Villa", "Bournemouth", "FC Brentford", "Brighton",
        "Chelsea", "Coventry City", "Crystal Palace", "FC Everton",
        "FC Fulham", "Hull City", "Ipswich Town", "Leeds United", "Liverpool",
        "Man City", "Manchester Utd.", "Newcastle", "Nottingham",
        "AFC Sunderland", "Tottenham",
    ], difficulty=1),
    LeagueCategory("league_laliga", "La Liga", [
        "Dep. La Coruña", "Alavés", "Esp. Barcelona", "FC Barcelona",
        "Athletic Bilbao", "FC Elche", "FC Getafe", "Atlético Madrid",
        "Real Madrid", "FC Málaga", "CA Osasuna", "Real Sociedad",
        "Rac. Santander", "FC Sevilla", "Betis Sevilla", "FC Valencia",
        "UD Levante", "Rayo Vallecano", "Celta Vigo", "FC Villarreal",
    ], difficulty=1),
    LeagueCategory("league_seriea", "Serie A", [
        "Atalanta", "FC Bologna", "Cagliari", "Como", "AC Florenz",
        "Frosinone", "Genua CFC", "Lecce", "Milan", "Inter", "Monza",
        "SSC Neapel", "AC Parma", "AS Rom", "Lazio Rom", "US Sassuolo",
        "FC Turin", "Juventus", "Udinese", "AC Venezia 1907",
    ], difficulty=2),
]

# Big non-top-4 leagues, as ordinary selectable categories (same idea as
# CONTINENT_CATEGORIES) — deliberately NOT part of LEAGUE_CATEGORIES above,
# which is specifically the 4 leagues with a full club roster used for the
# "Liga" filter-mode picker (see app.py's LEAGUE_POOLS comment). These exist
# so a handful of individually-famous foreign clubs (Boca Juniors, Flamengo,
# Al-Hilal, Ajax, ...) surface as "played in the Argentine/Brazilian/Saudi/
# Dutch league" instead of requiring recognition of one specific foreign
# club by name — the league itself is often the more recognizable thing.
# Only leagues with enough individually-famous clubs to form a real category
# (≥2) get one; a lone famous club per league (Paris SG/Ligue 1, Jeonbuk
# Hyundai/K-League, GZ Evergrande/CSL) stays an individual club category
# instead of a fake one-club "league" — see CLUB_FAME_TIER_1/2 in
# dynamic_categories.py, which is where those live.
FOREIGN_LEAGUE_CATEGORIES: list[LeagueCategory] = [
    LeagueCategory("league_bra", "Brasilianische Serie A", [
        "Flamengo", "Corinthians", "Palmeiras", "FC Santos", "FC São Paulo",
        "Fluminense", "Grêmio", "Internacional",
    ], difficulty=2),
    LeagueCategory("league_arg", "Argentinische Liga", [
        "Boca Juniors", "River Plate", "Independiente", "Racing Club",
        "Estudiantes LP", "San Lorenzo",
    ], difficulty=2),
    LeagueCategory("league_ksa", "Saudi Pro League", [
        "Al-Hilal", "Al-Nassr", "Al-Ittihad", "Al-Ahli",
    ], difficulty=2),
    LeagueCategory("league_ere", "Eredivisie", [
        "Ajax", "PSV",
    ], difficulty=3),
    LeagueCategory("league_jup", "J-League", [
        "Urawa Reds", "Kashima Antlers", "Vissel Kobe",
    ], difficulty=3),
]

CONTINENT_CATEGORIES: list[ContinentCategory] = [
    ContinentCategory("cont_sam", "In Südamerika gespielt", [
        # Brazil
        "Flamengo", "Palmeiras", "FC São Paulo", "FC Santos", "Grêmio",
        "Corinthians", "Fluminense", "Internacional",
        # Argentina
        "River Plate", "Boca Juniors", "Independiente", "San Lorenzo",
        "Estudiantes LP", "Racing Club",
        # Uruguay
        "Peñarol", "Nacional",
        # Colombia
        "Atl. Nacional",
        # Chile
        "U. de Chile",
    ], difficulty=1),
    ContinentCategory("cont_afr", "In Afrika gespielt", [
        # Tunisia
        "Esperance", "Club Africain", "ES Sahel", "CS Sfaxien",
        # Morocco
        "Wydad AC", "Raja Casablanca",
        # Egypt
        "Zamalek", "Pyramids FC",
        # South Africa
        "Kaizer Chiefs", "Sundowns",
        # Côte d'Ivoire
        "ASEC Mimosas",
        # Nigeria
        "Enyimba Aba",
        # Algeria
        "JS Kabylie",
        # DR Congo
        "TP Mazembe",
    ], difficulty=3),
    ContinentCategory("cont_asia", "In Asien gespielt", [
        # Saudi Arabia
        "Al-Hilal", "Al-Nassr", "Al-Ittihad", "Al-Ahli", "Al-Shabab",
        "Al-Qadsiah", "Al-Taawoun", "Al-Fayha", "Al-Raed", "Al-Batin",
        # UAE
        "Al-Jazira", "Al-Wahda", "Al-Ahli (UAE)", "Al-Wasl",
        "Al-Dhafra FC", "Shabab Al-Ahli",
        # Japan
        "Urawa Reds", "Gamba Osaka", "Kawasaki Front.", "Nagoya Grampus",
        "Vissel Kobe", "Cerezo Osaka", "Kashima Antlers", "Yokohama F. M.",
        "Shimizu S-Pulse", "Avispa Fukuoka", "Sagan Tosu",
        # South Korea
        "Ulsan Hyundai", "Suwon Bluewings", "Jeonbuk Hyundai", "FC Seoul",
        "Pohang Steelers", "Incheon Utd.", "Jeju United",
        # China
        "GZ Evergrande", "SH SIPG", "Jiangsu FC",
        # India
        "Chennaiyin FC", "FC Goa", "Kerala Blasters", "Mumbai City",
        "Bengaluru FC",
        # Thailand
        "Buriram Utd.", "Muangthong Utd.", "Port FC",
    ], difficulty=2),
]

ALL_CATEGORIES: list[Category] = [
    *NON_EUROPEAN_CATEGORIES,
    *POSITION_CATEGORIES,
    *LEAGUE_CATEGORIES,
    *FOREIGN_LEAGUE_CATEGORIES,
    *CONTINENT_CATEGORIES,
    *INITIAL_CATEGORIES,
    *CONTAINS_LETTER_CATEGORIES,
    *AGE_CATEGORIES,
    *MARKET_VALUE_CATEGORIES,
]

CATEGORY_BY_ID: dict[str, Category] = {cat.id: cat for cat in ALL_CATEGORIES}
