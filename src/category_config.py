"""Whitelist of categories available for puzzle generation.

Club names must match career_stints.club_name exactly (Transfermarkt DE abbreviations).
Nationality names are in German, as stored in players.nationality.
Position prefixes match players.position using a LIKE prefix query.
"""

from __future__ import annotations

from .categories import AgeCategory, Category, ClubCategory, ContainsLetterCategory, ContinentCategory, InitialCategory, LeagueCategory, MarketValueCategory, NationalityCategory, NonEuropeanNationalityCategory, PositionCategory


CLUB_CATEGORIES: list[ClubCategory] = [
    # Bundesliga
    ClubCategory("club_bay", "Bayern München",           "Bayern München",   difficulty=1),
    ClubCategory("club_bvb", "Borussia Dortmund",        "Bor. Dortmund",    difficulty=1),
    ClubCategory("club_b04", "Bayer Leverkusen",         "B. Leverkusen",    difficulty=2),
    ClubCategory("club_rbl", "RB Leipzig",               "RB Leipzig",       difficulty=2),
    ClubCategory("club_sge", "Eintracht Frankfurt",      "E. Frankfurt",     difficulty=2),
    ClubCategory("club_s04", "Schalke 04",               "FC Schalke 04",    difficulty=3),
    ClubCategory("club_hsv", "Hamburger SV",             "Hamburger SV",     difficulty=3),
    ClubCategory("club_svw", "Werder Bremen",            "Werder Bremen",    difficulty=3),
    ClubCategory("club_aug", "FC Augsburg",              "FC Augsburg",      difficulty=3),
    ClubCategory("club_wob", "VfL Wolfsburg",            "VfL Wolfsburg",    difficulty=3),
    ClubCategory("club_stu", "VfB Stuttgart",            "VfB Stuttgart",    difficulty=3),
    ClubCategory("club_frb", "1.FC Freiburg",            "SC Freiburg",      difficulty=3),
    ClubCategory("club_bmg", "Borussia Mönchengladbach", "Bor. M'gladbach",  difficulty=3),
    ClubCategory("club_koe", "1.FC Köln",                "1.FC Köln",        difficulty=3),
    # Premier League
    ClubCategory("club_mnu", "Manchester United",        "Manchester Utd.",  difficulty=2),
    ClubCategory("club_mci", "Manchester City",          "Manchester City",  difficulty=2),
    ClubCategory("club_lfc", "Liverpool",                "Liverpool",        difficulty=2),
    ClubCategory("club_ars", "Arsenal",                  "Arsenal",          difficulty=2),
    ClubCategory("club_che", "Chelsea",                  "Chelsea",          difficulty=2),
    ClubCategory("club_tot", "Tottenham Hotspur",        "Tottenham",        difficulty=3),
    # La Liga
    ClubCategory("club_rma", "Real Madrid",              "Real Madrid",      difficulty=1),
    ClubCategory("club_fcb", "FC Barcelona",             "FC Barcelona",     difficulty=1),
    ClubCategory("club_atm", "Atlético Madrid",          "Atlético Madrid",  difficulty=2),
    ClubCategory("club_sev", "FC Sevilla",               "FC Sevilla",       difficulty=3),
    # Serie A
    ClubCategory("club_juv", "Juventus",                 "Juventus",         difficulty=3),
    ClubCategory("club_int", "Inter Mailand",            "Inter",            difficulty=3),
    ClubCategory("club_mil", "AC Milan",                 "Milan",            difficulty=3),
    # Sonstiges
    ClubCategory("club_psg", "Paris Saint-Germain",      "Paris SG",         difficulty=2),
    ClubCategory("club_ajx", "Ajax Amsterdam",           "Ajax",             difficulty=3),
    ClubCategory("club_psv", "PSV Eindhoven",            "PSV",              difficulty=3),

    ClubCategory("club_sve", "SV Eintracht Trier",       "SV Eintracht Trier", difficulty=3),
]


NATIONALITY_CATEGORIES: list[NationalityCategory] = [
    NationalityCategory("nat_eng", "Englisch",       "England",      difficulty=1),
    NationalityCategory("nat_esp", "Spanisch",       "Spanien",      difficulty=1),
    NationalityCategory("nat_ita", "Italienisch",    "Italien",      difficulty=1),
    NationalityCategory("nat_fra", "Französisch",    "Frankreich",   difficulty=1),
    NationalityCategory("nat_ger", "Deutsch",        "Deutschland",  difficulty=1),
    NationalityCategory("nat_bra", "Brasilianisch",  "Brasilien",    difficulty=1),
    NationalityCategory("nat_arg", "Argentinisch",   "Argentinien",  difficulty=1),
    NationalityCategory("nat_ned", "Niederländisch", "Niederlande",  difficulty=1),
    NationalityCategory("nat_por", "Portugiesisch",  "Portugal",     difficulty=1),
    NationalityCategory("nat_hrv", "Kroatisch",      "Kroatien",     difficulty=2),
    NationalityCategory("nat_bel", "Belgisch",       "Belgien",      difficulty=2),
    NationalityCategory("nat_dnk", "Dänisch",        "Dänemark",     difficulty=3),
    NationalityCategory("nat_swe", "Schwedisch",     "Schweden",     difficulty=3),
    NationalityCategory("nat_tur", "Türkisch",       "Türkei",       difficulty=2),
    NationalityCategory("nat_aut", "Österreichisch", "Österreich",   difficulty=3),
    NationalityCategory("nat_pol", "Polnisch",       "Polen",        difficulty=2),
    NationalityCategory("nat_sco", "Schottisch",     "Schottland",   difficulty=3),
    NationalityCategory("nat_sui", "Schweizerisch",  "Schweiz",      difficulty=3),
    NationalityCategory("nat_wal", "Walisisch",      "Wales",        difficulty=3),

]

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
        "Bayern München", "Bor. Dortmund", "B. Leverkusen", "RB Leipzig",
        "E. Frankfurt", "FC Schalke 04", "Hamburger SV", "Werder Bremen",
        "Bor. M'gladbach", "VfB Stuttgart", "Hertha BSC", "1.FC Köln",
        "FC Augsburg", "VfL Wolfsburg", "Hannover 96", "F. Düsseldorf",
        "Arm. Bielefeld", "Darmstadt 98", "SC Freiburg", "TSG Hoffenheim",
        "VfL Bochum", "1.FSV Mainz 05",
    ], difficulty=1),
    LeagueCategory("league_pl", "Premier League", [
        "Arsenal", "Chelsea", "Liverpool", "Manchester Utd.", "Man City",
        "Tottenham", "Newcastle", "FC Everton", "Aston Villa", "West Ham Utd.",
        "Brighton", "FC Brentford", "FC Fulham", "Crystal Palace",
        "Wolverhampton", "Nottingham", "Leeds United", "AFC Sunderland",
        "Bournemouth", "Leicester City",
    ], difficulty=1),
    LeagueCategory("league_laliga", "La Liga", [
        "Real Madrid", "FC Barcelona", "Atlético Madrid", "FC Sevilla",
        "FC Valencia", "FC Villarreal", "Betis Sevilla", "Athletic Bilbao",
        "Rayo Vallecano", "Esp. Barcelona", "UD Levante", "Alavés",
        "RCD Mallorca", "Celta Vigo", "FC Getafe", "CA Osasuna",
        "Real Sociedad", "Real Valladolid", "UD Almería", "Deportivo LC",
    ], difficulty=1),
    LeagueCategory("league_seriea", "Serie A", [
        "Inter", "Milan", "Juventus", "AS Rom", "SSC Neapel", "Lazio Rom",
        "Atalanta", "FC Bologna", "Sampdoria", "Genua CFC", "US Sassuolo",
        "Torino", "Hellas Verona", "Lecce", "AC Pisa", "Cremonese",
        "Udinese", "Como",
    ], difficulty=2),
    LeagueCategory("league_ligue1", "Ligue 1", [
        "Paris SG", "Olympique Lyon", "Marseille", "AS Monaco",
        "LOSC Lille", "Stade Rennes",
    ], difficulty=2),
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
    *CLUB_CATEGORIES,
    *NATIONALITY_CATEGORIES,
    *NON_EUROPEAN_CATEGORIES,
    *POSITION_CATEGORIES,
    *LEAGUE_CATEGORIES,
    *CONTINENT_CATEGORIES,
    *INITIAL_CATEGORIES,
    *CONTAINS_LETTER_CATEGORIES,
    *AGE_CATEGORIES,
    *MARKET_VALUE_CATEGORIES,
]

CATEGORY_BY_ID: dict[str, Category] = {cat.id: cat for cat in ALL_CATEGORIES}
