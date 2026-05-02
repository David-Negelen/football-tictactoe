"""Whitelist of categories available for puzzle generation.

Club names must match career_stints.club_name exactly (Transfermarkt DE abbreviations).
Nationality names are in German, as stored in players.nationality.
Position prefixes match players.position using a LIKE prefix query.
Award winner names must match players.name case-insensitively.
"""

from __future__ import annotations

from .categories import AwardCategory, Category, ClubCategory, NationalityCategory, PositionCategory

# ---------------------------------------------------------------------------
# Club categories
# Only include clubs with enough career stints to produce valid puzzle
# intersections (~150+ distinct players). Clubs listed here are the first-team
# entries as they appear in career_stints (Transfermarkt DE abbreviations).
# ---------------------------------------------------------------------------
CLUB_CATEGORIES: list[ClubCategory] = [
    # Bundesliga
    ClubCategory("club_bay", "Bayern München",          "Bayern München"),
    ClubCategory("club_bvb", "Borussia Dortmund",       "Bor. Dortmund"),
    ClubCategory("club_b04", "Bayer Leverkusen",        "B. Leverkusen"),
    ClubCategory("club_rbl", "RB Leipzig",              "RB Leipzig"),
    ClubCategory("club_sge", "Eintracht Frankfurt",     "E. Frankfurt"),
    ClubCategory("club_s04", "Schalke 04",              "FC Schalke 04"),
    ClubCategory("club_hsv", "Hamburger SV",            "Hamburger SV"),
    ClubCategory("club_svw", "Werder Bremen",           "Werder Bremen"),
    ClubCategory("club_bmg", "Borussia Mönchengladbach","Bor. M'gladbach"),
    # Premier League
    ClubCategory("club_mnu", "Manchester United",       "Manchester Utd."),
    ClubCategory("club_mci", "Manchester City",         "Man City"),
    ClubCategory("club_lfc", "Liverpool",               "Liverpool"),
    ClubCategory("club_ars", "Arsenal",                 "Arsenal"),
    ClubCategory("club_che", "Chelsea",                 "Chelsea"),
    ClubCategory("club_tot", "Tottenham Hotspur",       "Tottenham"),
    # La Liga
    ClubCategory("club_rma", "Real Madrid",             "Real Madrid"),
    ClubCategory("club_fcb", "FC Barcelona",            "FC Barcelona"),
    ClubCategory("club_atm", "Atlético Madrid",         "Atlético Madrid"),
    ClubCategory("club_sev", "FC Sevilla",              "FC Sevilla"),
    ClubCategory("club_val", "FC Valencia",             "FC Valencia"),
    # Serie A
    ClubCategory("club_juv", "Juventus",                "Juventus"),
    ClubCategory("club_int", "Inter Mailand",           "Inter"),
    ClubCategory("club_mil", "AC Milan",                "Milan"),
    # Other top clubs (appear via transfer histories even though not scraped directly)
    ClubCategory("club_psg", "Paris Saint-Germain",     "Paris SG"),
    ClubCategory("club_laz", "Lazio",                   "Lazio Rom"),
]

# ---------------------------------------------------------------------------
# Nationality categories
# Stored in German in players.nationality. Dual nationals have space-separated
# values ("Deutschland Türkei"), so matching uses LIKE '%nationality%'.
# ---------------------------------------------------------------------------
NATIONALITY_CATEGORIES: list[NationalityCategory] = [
    NationalityCategory("nat_ger", "Deutsch",       "Deutschland"),
    NationalityCategory("nat_eng", "Englisch",      "England"),
    NationalityCategory("nat_esp", "Spanisch",      "Spanien"),
    NationalityCategory("nat_fra", "Französisch",   "Frankreich"),
    NationalityCategory("nat_bra", "Brasilianisch", "Brasilien"),
    NationalityCategory("nat_arg", "Argentinisch",  "Argentinien"),
    NationalityCategory("nat_ned", "Niederländisch","Niederlande"),
    NationalityCategory("nat_por", "Portugiesisch", "Portugal"),
    NationalityCategory("nat_ita", "Italienisch",   "Italien"),
    NationalityCategory("nat_hrv", "Kroatisch",     "Kroatien"),
    NationalityCategory("nat_bel", "Belgisch",      "Belgien"),
    NationalityCategory("nat_dnk", "Dänisch",       "Dänemark"),
    NationalityCategory("nat_swe", "Schwedisch",    "Schweden"),
    NationalityCategory("nat_tur", "Türkisch",      "Türkei"),
    NationalityCategory("nat_aut", "Österreichisch","Österreich"),
    NationalityCategory("nat_pol", "Polnisch",      "Polen"),
    NationalityCategory("nat_sco", "Schottisch",    "Schottland"),
    NationalityCategory("nat_wal", "Walisisch",     "Wales"),
]

# ---------------------------------------------------------------------------
# Position categories
# Positions are stored as "Group - Subposition" (e.g. "Abwehr - Innenverteidiger").
# Broad categories use just the group prefix; specific ones use the full string.
# ---------------------------------------------------------------------------
POSITION_CATEGORIES: list[PositionCategory] = [
    # Broad groups (easy)
    PositionCategory("pos_gk",  "Torwart",              "Torwart"),
    PositionCategory("pos_def", "Abwehrspieler",        "Abwehr"),
    PositionCategory("pos_mid", "Mittelfeldspieler",    "Mittelfeld"),
    PositionCategory("pos_fwd", "Stürmer",              "Sturm"),
    # Specific positions (harder)
    PositionCategory("pos_cb",  "Innenverteidiger",     "Abwehr - Innenverteidiger"),
    PositionCategory("pos_lb",  "Linker Verteidiger",   "Abwehr - Linker Verteidiger"),
    PositionCategory("pos_rb",  "Rechter Verteidiger",  "Abwehr - Rechter Verteidiger"),
    PositionCategory("pos_dm",  "Defensives Mittelfeld","Mittelfeld - Defensives Mittelfeld"),
    PositionCategory("pos_cm",  "Zentrales Mittelfeld", "Mittelfeld - Zentrales Mittelfeld"),
    PositionCategory("pos_am",  "Offensives Mittelfeld","Mittelfeld - Offensives Mittelfeld"),
    PositionCategory("pos_st",  "Mittelstürmer",        "Sturm - Mittelstürmer"),
    PositionCategory("pos_lw",  "Linksaußen",           "Sturm - Linksaußen"),
    PositionCategory("pos_rw",  "Rechtsaußen",          "Sturm - Rechtsaußen"),
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
        [
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
    ),
    AwardCategory(
        "award_euro",
        "Europameister",
        [
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
    ),
    AwardCategory(
        "award_ucl",
        "Champions-League-Sieger",
        [
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
    ),
]

# ---------------------------------------------------------------------------
# Combined index – all categories available for puzzle generation
# ---------------------------------------------------------------------------
ALL_CATEGORIES: list[Category] = [
    *CLUB_CATEGORIES,
    *NATIONALITY_CATEGORIES,
    *POSITION_CATEGORIES,
    *AWARD_CATEGORIES,
]

CATEGORY_BY_ID: dict[str, Category] = {cat.id: cat for cat in ALL_CATEGORIES}
