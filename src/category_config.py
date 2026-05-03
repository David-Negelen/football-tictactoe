"""Whitelist of categories available for puzzle generation.

Club names must match career_stints.club_name exactly (Transfermarkt DE abbreviations).
Nationality names are in German, as stored in players.nationality.
Position prefixes match players.position using a LIKE prefix query.
Award winner names must match players.name case-insensitively.
"""

from __future__ import annotations

from .categories import AwardCategory, Category, ClubCategory, ContinentCategory, LeagueCategory, NationalityCategory, PositionCategory

# ---------------------------------------------------------------------------
# Club categories
# Only include clubs with enough career stints to produce valid puzzle
# intersections (~150+ distinct players). Clubs listed here are the first-team
# entries as they appear in career_stints (Transfermarkt DE abbreviations).
# ---------------------------------------------------------------------------
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
    ClubCategory("club_bmg", "Borussia Mönchengladbach", "Bor. M'gladbach",  difficulty=3),
    # Premier League
    ClubCategory("club_mnu", "Manchester United",        "Manchester Utd.",  difficulty=1),
    ClubCategory("club_mci", "Manchester City",          "Manchester City",  difficulty=1),
    ClubCategory("club_lfc", "Liverpool",                "Liverpool",        difficulty=1),
    ClubCategory("club_ars", "Arsenal",                  "Arsenal",          difficulty=2),
    ClubCategory("club_che", "Chelsea",                  "Chelsea",          difficulty=2),
    ClubCategory("club_tot", "Tottenham Hotspur",        "Tottenham",        difficulty=3),
    # La Liga
    ClubCategory("club_rma", "Real Madrid",              "Real Madrid",      difficulty=1),
    ClubCategory("club_fcb", "FC Barcelona",             "FC Barcelona",     difficulty=1),
    ClubCategory("club_atm", "Atlético Madrid",          "Atlético Madrid",  difficulty=2),
    ClubCategory("club_sev", "FC Sevilla",               "FC Sevilla",       difficulty=3),
    ClubCategory("club_val", "FC Valencia",              "FC Valencia",      difficulty=3),
    # Serie A
    ClubCategory("club_juv", "Juventus",                 "Juventus",         difficulty=3),
    ClubCategory("club_int", "Inter Mailand",            "Inter",            difficulty=3),
    ClubCategory("club_mil", "AC Milan",                 "Milan",            difficulty=3),
    # Sonstige Topklubs
    ClubCategory("club_psg", "Paris Saint-Germain",      "Paris SG",         difficulty=2),
    ClubCategory("club_laz", "Lazio Rom",                "Lazio Rom",        difficulty=3),
]

# ---------------------------------------------------------------------------
# Nationality categories
# Stored in German in players.nationality. Dual nationals have space-separated
# values ("Deutschland Türkei"), so matching uses LIKE '%nationality%'.
# ---------------------------------------------------------------------------
NATIONALITY_CATEGORIES: list[NationalityCategory] = [
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
    NationalityCategory("nat_wal", "Walisisch",      "Wales",        difficulty=3),
]

# ---------------------------------------------------------------------------
# Position categories
# Positions are stored as "Group - Subposition" (e.g. "Abwehr - Innenverteidiger").
# Broad categories use just the group prefix; specific ones use the full string.
# ---------------------------------------------------------------------------
POSITION_CATEGORIES: list[PositionCategory] = [
    # Breite Gruppen (leicht)
    PositionCategory("pos_gk",  "Torwart",               "Torwart",                          difficulty=1),
    PositionCategory("pos_def", "Abwehrspieler",         "Abwehr",                           difficulty=1),
    PositionCategory("pos_mid", "Mittelfeldspieler",     "Mittelfeld",                       difficulty=1),
    PositionCategory("pos_fwd", "Stürmer",               "Sturm",                            difficulty=1),
    # Spezifische Positionen (mittel)
    PositionCategory("pos_cb",  "Innenverteidiger",      "Abwehr - Innenverteidiger",        difficulty=2),
    PositionCategory("pos_dm",  "Defensives Mittelfeld", "Mittelfeld - Defensives Mittelfeld", difficulty=2),
    PositionCategory("pos_cm",  "Zentrales Mittelfeld",  "Mittelfeld - Zentrales Mittelfeld", difficulty=2),
    PositionCategory("pos_am",  "Offensives Mittelfeld", "Mittelfeld - Offensives Mittelfeld", difficulty=2),
    PositionCategory("pos_st",  "Mittelstürmer",         "Sturm - Mittelstürmer",            difficulty=2),
    # Sehr spezifische Positionen (schwer)
    PositionCategory("pos_lb",  "Linker Verteidiger",    "Abwehr - Linker Verteidiger",      difficulty=3),
    PositionCategory("pos_rb",  "Rechter Verteidiger",   "Abwehr - Rechter Verteidiger",     difficulty=3),
    PositionCategory("pos_lw",  "Linksaußen",            "Sturm - Linksaußen",               difficulty=3),
    PositionCategory("pos_rw",  "Rechtsaußen",           "Sturm - Rechtsaußen",              difficulty=3),
]

# ---------------------------------------------------------------------------
# Award categories
# Player names must match players.name exactly (case-insensitive).
# These lists need manual maintenance as new winners are announced.
# ---------------------------------------------------------------------------
AWARD_CATEGORIES: list[AwardCategory] = [
    AwardCategory(
        "award_bdo",
        "Ballon d'Or",
        player_names=[
            # 2024
            "Rodri",
            # 2023
            "Lionel Messi",
            # 2022
            "Karim Benzema",
            # 2021
            # Messi (listed above)
            # 2019
            # Messi (listed above)
            # 2018
            "Luka Modric",
            # 2017
            "Cristiano Ronaldo",
            # 2016
            # Ronaldo (listed above)
            # 2015
            # Messi (listed above)
            # 2014
            # Ronaldo (listed above)
            # 2013
            # Ronaldo (listed above)
            # 2012
            # Messi (listed above)
            # 2011
            # Messi/Ronaldo (listed above)
            # 2010
            # Messi (listed above)
            # 2009
            # Messi (listed above)
            # 2008
            # Ronaldo (listed above)
            # 2007
            "Kaka",
            # 2005
            "Ronaldinho",
            # 2004
            "Andriy Shevchenko",
            # 2003
            "Pavel Nedved",
            # 2001
            "Michael Owen",
            # 1999
            "Rivaldo",
            # 1998
            "Zinedine Zidane",
            # 1997
            "Ronaldo",
            # 1996
            "Matthias Sammer",
            # 1995
            "George Weah",
        ],
        difficulty=1,
    ),
    AwardCategory(
        "award_euro",
        "Europameister",
        player_names=[
            # Euro 2024 – Spain
            "Dani Carvajal", "Rodri", "Marc Cucurella", "Aymeric Laporte",
            "Alejandro Grimaldo", "Fabián Ruiz", "Pedri", "Dani Olmo",
            "Lamine Yamal", "Alvaro Morata", "Nico Williams",
            "Robin Le Normand", "Nacho", "Mikel Merino", "Ferran Torres",
            "Unai Simón", "David Raya", "Alex Remiro",
            # Euro 2020 – Italy (played 2021)
            "Gianluigi Donnarumma", "Giorgio Chiellini", "Leonardo Bonucci",
            "Giovanni Di Lorenzo", "Emerson", "Marco Verratti",
            "Jorginho", "Nicolo Barella", "Lorenzo Insigne",
            "Federico Chiesa", "Ciro Immobile",
            # Euro 2016 – Portugal
            "Rui Patricio", "Pepe", "José Fonte", "Raphael Guerreiro",
            "Cedric Soares", "Joao Moutinho", "Renato Sanches",
            "Eder", "Nani", "Cristiano Ronaldo", "Ricardo Quaresma",
            # Euro 2012 – Spain
            "Iker Casillas", "Sergio Ramos", "Gerard Piqué",
            "Jordi Alba", "Xabi Alonso", "Sergio Busquets",
            "Xavi", "Andrés Iniesta", "David Silva",
            "Fernando Torres", "Cesc Fàbregas",
            # Euro 2008 – Spain (overlapping with 2012 squad, already listed)
            "David Villa", "Santi Cazorla",
        ],
        difficulty=2,
    ),
    AwardCategory(
        "award_ucl",
        "Champions-League-Sieger",
        player_names=[
            # 2024 – Real Madrid
            "Thibaut Courtois", "Dani Carvajal", "Antonio Rüdiger",
            "Eder Militao", "Ferland Mendy", "Luka Modric",
            "Toni Kroos", "Federico Valverde", "Vinicius Junior",
            "Joselu", "Brahim Diaz", "Rodrygo", "Nacho",
            # 2023 – Manchester City
            "Ederson", "Kyle Walker", "Ruben Dias", "Manuel Akanji",
            "Josko Gvardiol", "Rodri", "Ilkay Gündogan",
            "Kevin De Bruyne", "Bernardo Silva", "Phil Foden",
            "Erling Haaland", "Jeremy Doku",
            # 2022 – Real Madrid (overlapping, already listed)
            "Karim Benzema", "Casemiro",
            # 2021 – Chelsea
            "Edouard Mendy", "Cesar Azpilicueta", "Thiago Silva",
            "Andreas Christensen", "Ben Chilwell", "N'Golo Kante",
            "Jorginho", "Mason Mount", "Hakim Ziyech",
            "Timo Werner", "Kai Havertz", "Christian Pulisic",
            # 2020 – Bayern München
            "Manuel Neuer", "David Alaba", "Jerome Boateng",
            "Alphonso Davies", "Joshua Kimmich", "Leon Goretzka",
            "Thomas Müller", "Serge Gnabry", "Kingsley Coman",
            "Robert Lewandowski", "Philippe Coutinho",
            # 2019 – Liverpool
            "Alisson", "Trent Alexander-Arnold", "Virgil van Dijk",
            "Joel Matip", "Andrew Robertson", "Fabinho",
            "Jordan Henderson", "Gini Wijnaldum",
            "Mohamed Salah", "Sadio Mane", "Roberto Firmino",
        ],
        difficulty=1,
    ),
]

# ---------------------------------------------------------------------------
# League categories
# Club names match career_stints.club_name (Transfermarkt DE, first-team only).
# ---------------------------------------------------------------------------
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
    ], difficulty=1),
    LeagueCategory("league_ligue1", "Ligue 1", [
        "Paris SG", "Olympique Lyon", "Marseille", "AS Monaco",
        "LOSC Lille", "Stade Rennes",
    ], difficulty=1),
]

# ---------------------------------------------------------------------------
# Continent categories
# Club names match career_stints.club_name. A player qualifies if they have
# at least one career stint at a club on that continent.
# ---------------------------------------------------------------------------
CONTINENT_CATEGORIES: list[ContinentCategory] = [
    ContinentCategory("cont_eur", "In Europa gespielt", [
        # Bundesliga
        "Bayern München", "Bor. Dortmund", "B. Leverkusen", "RB Leipzig",
        "E. Frankfurt", "FC Schalke 04", "Hamburger SV", "Werder Bremen",
        "Bor. M'gladbach", "VfB Stuttgart", "Hertha BSC", "1.FC Köln",
        "FC Augsburg", "VfL Wolfsburg", "Hannover 96", "F. Düsseldorf",
        "Arm. Bielefeld", "Darmstadt 98", "SC Freiburg", "TSG Hoffenheim",
        "VfL Bochum", "1.FSV Mainz 05",
        # Premier League
        "Arsenal", "Chelsea", "Liverpool", "Manchester Utd.", "Man City",
        "Tottenham", "Newcastle", "FC Everton", "Aston Villa", "West Ham Utd.",
        "Brighton", "FC Brentford", "FC Fulham", "Crystal Palace",
        "Wolverhampton", "Nottingham", "Leeds United", "AFC Sunderland",
        "Bournemouth", "Leicester City",
        # La Liga
        "Real Madrid", "FC Barcelona", "Atlético Madrid", "FC Sevilla",
        "FC Valencia", "FC Villarreal", "Betis Sevilla", "Athletic Bilbao",
        "Rayo Vallecano", "Esp. Barcelona", "UD Levante", "Alavés",
        "RCD Mallorca", "Celta Vigo", "FC Getafe", "CA Osasuna",
        "Real Sociedad", "Real Valladolid", "UD Almería", "Deportivo LC",
        # Serie A
        "Inter", "Milan", "Juventus", "AS Rom", "SSC Neapel", "Lazio Rom",
        "Atalanta", "FC Bologna", "Sampdoria", "Genua CFC", "US Sassuolo",
        "Torino", "Hellas Verona", "Lecce", "AC Pisa", "Cremonese",
        "Udinese", "Como",
        # Ligue 1
        "Paris SG", "Olympique Lyon", "Marseille", "AS Monaco",
        "LOSC Lille", "Stade Rennes",
        # Portugal
        "Benfica", "FC Porto", "Sporting",
        # Netherlands
        "Ajax", "PSV", "Feyenoord",
        # Belgium
        "RSC Anderlecht",
        # Scotland
        "Celtic Glasgow", "Glasgow Rangers",
        # Turkey
        "Galatasaray", "Fenerbahce",
        # Russia / Ukraine
        "Spartak Moskau", "Zenit S-Pb", "Dynamo Kyiv", "Shakhtar D.",
        # Greece
        "Olympiakos",
        # Denmark
        "FC Midtjylland", "Rosenborg BK",
    ], difficulty=1),
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
    ], difficulty=2),
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

# ---------------------------------------------------------------------------
# Combined index – all categories available for puzzle generation
# ---------------------------------------------------------------------------
ALL_CATEGORIES: list[Category] = [
    *CLUB_CATEGORIES,
    *NATIONALITY_CATEGORIES,
    *POSITION_CATEGORIES,
    *AWARD_CATEGORIES,
    *LEAGUE_CATEGORIES,
    *CONTINENT_CATEGORIES,
]

CATEGORY_BY_ID: dict[str, Category] = {cat.id: cat for cat in ALL_CATEGORIES}
