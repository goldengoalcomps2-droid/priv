"""
Sample data for European top leagues 2024/25 season.
This serves as fallback when the API is unavailable.
Users can update this data or the bot can fetch live data.
"""

from datetime import date
from .data import (
    Competition, HalfStats, MonthlyRecord, PlayerInfo,
    TeamForm, TeamSeason,
)


def get_sample_teams() -> dict[str, TeamSeason]:
    """Return sample team data. In production, this would come from the API/scraper."""
    teams = {}

    # ===== PREMIER LEAGUE =====
    teams["liverpool"] = TeamSeason(
        name="Liverpool",
        competition=Competition.PREMIER_LEAGUE,
        games_played=33, wins=25, draws=6, losses=2,
        goals_scored=75, goals_conceded=28,
        league_position=1, points=81,
        possession_avg=58.2, shots_per_game=15.3,
        shots_on_target_per_game=6.1, xg_per_game=2.15, xga_per_game=0.95,
        clean_sheets=14, failed_to_score=2,
        half_stats=HalfStats(
            first_half_goals_scored=35, second_half_goals_scored=40,
            first_half_goals_conceded=10, second_half_goals_conceded=18,
        ),
        form=TeamForm(results=["W", "W", "D", "W", "W", "W"]),
        players=[
            PlayerInfo("Mohamed Salah", "RW", goals=22, assists=14, rating=8.5),
            PlayerInfo("Virgil van Dijk", "CB", goals=3, assists=1, rating=7.8),
            PlayerInfo("Alexis Mac Allister", "CM", goals=5, assists=8, rating=7.5),
            PlayerInfo("Cody Gakpo", "LW", goals=12, assists=6, rating=7.4),
            PlayerInfo("Ryan Gravenberch", "DM", goals=3, assists=5, rating=7.6),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 26), date(2025, 3, 22)],
    )

    teams["arsenal"] = TeamSeason(
        name="Arsenal",
        competition=Competition.PREMIER_LEAGUE,
        games_played=33, wins=22, draws=7, losses=4,
        goals_scored=68, goals_conceded=26,
        league_position=2, points=73,
        possession_avg=60.1, shots_per_game=16.1,
        shots_on_target_per_game=5.8, xg_per_game=2.05, xga_per_game=0.88,
        clean_sheets=16, failed_to_score=3,
        half_stats=HalfStats(
            first_half_goals_scored=30, second_half_goals_scored=38,
            first_half_goals_conceded=8, second_half_goals_conceded=18,
        ),
        form=TeamForm(results=["W", "W", "W", "D", "W", "L"]),
        players=[
            PlayerInfo("Bukayo Saka", "RW", goals=14, assists=12, rating=8.2),
            PlayerInfo("Kai Havertz", "CF", goals=15, assists=5, rating=7.6),
            PlayerInfo("Martin Odegaard", "CAM", goals=6, assists=10, rating=7.9),
            PlayerInfo("William Saliba", "CB", goals=2, assists=0, rating=7.9),
            PlayerInfo("Declan Rice", "CM", goals=4, assists=7, rating=7.7),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 26), date(2025, 3, 22), date(2025, 3, 18)],
    )

    teams["man city"] = TeamSeason(
        name="Manchester City",
        competition=Competition.PREMIER_LEAGUE,
        games_played=33, wins=18, draws=6, losses=9,
        goals_scored=62, goals_conceded=38,
        league_position=4, points=60,
        possession_avg=63.5, shots_per_game=17.2,
        shots_on_target_per_game=6.3, xg_per_game=2.10, xga_per_game=1.15,
        clean_sheets=9, failed_to_score=4,
        half_stats=HalfStats(
            first_half_goals_scored=28, second_half_goals_scored=34,
            first_half_goals_conceded=14, second_half_goals_conceded=24,
        ),
        form=TeamForm(results=["W", "D", "W", "L", "W", "D"]),
        players=[
            PlayerInfo("Erling Haaland", "ST", goals=20, assists=4, rating=7.9),
            PlayerInfo("Phil Foden", "AM", goals=8, assists=7, rating=7.3),
            PlayerInfo("Kevin De Bruyne", "CM", goals=4, assists=9, rating=7.6, injured=True, injury_description="hamstring"),
            PlayerInfo("Rodri", "DM", goals=0, assists=0, rating=0, injured=True, injury_description="ACL - season over"),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 27), date(2025, 3, 23), date(2025, 3, 19), date(2025, 3, 15)],
    )

    teams["nottingham forest"] = TeamSeason(
        name="Nottingham Forest",
        competition=Competition.PREMIER_LEAGUE,
        games_played=33, wins=19, draws=7, losses=7,
        goals_scored=55, goals_conceded=35,
        league_position=3, points=64,
        possession_avg=44.8, shots_per_game=11.2,
        shots_on_target_per_game=4.2, xg_per_game=1.35, xga_per_game=1.30,
        clean_sheets=11, failed_to_score=5,
        half_stats=HalfStats(
            first_half_goals_scored=22, second_half_goals_scored=33,
            first_half_goals_conceded=12, second_half_goals_conceded=23,
        ),
        form=TeamForm(results=["W", "L", "W", "W", "D", "W"]),
        players=[
            PlayerInfo("Chris Wood", "ST", goals=18, assists=3, rating=7.8),
            PlayerInfo("Morgan Gibbs-White", "AM", goals=6, assists=10, rating=7.5),
            PlayerInfo("Murillo", "CB", goals=1, assists=2, rating=7.4),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 26)],
    )

    teams["chelsea"] = TeamSeason(
        name="Chelsea",
        competition=Competition.PREMIER_LEAGUE,
        games_played=33, wins=17, draws=7, losses=9,
        goals_scored=60, goals_conceded=42,
        league_position=5, points=58,
        possession_avg=55.3, shots_per_game=14.5,
        shots_on_target_per_game=5.2, xg_per_game=1.75, xga_per_game=1.25,
        clean_sheets=8, failed_to_score=5,
        half_stats=HalfStats(
            first_half_goals_scored=25, second_half_goals_scored=35,
            first_half_goals_conceded=18, second_half_goals_conceded=24,
        ),
        form=TeamForm(results=["D", "W", "L", "W", "W", "D"]),
        players=[
            PlayerInfo("Cole Palmer", "AM", goals=18, assists=11, rating=8.1),
            PlayerInfo("Nicolas Jackson", "ST", goals=14, assists=6, rating=7.3),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 26), date(2025, 3, 22)],
    )

    teams["aston villa"] = TeamSeason(
        name="Aston Villa",
        competition=Competition.PREMIER_LEAGUE,
        games_played=33, wins=16, draws=8, losses=9,
        goals_scored=52, goals_conceded=42,
        league_position=6, points=56,
        possession_avg=52.1, shots_per_game=13.8,
        shots_on_target_per_game=4.8, xg_per_game=1.55, xga_per_game=1.20,
        clean_sheets=8, failed_to_score=6,
        half_stats=HalfStats(
            first_half_goals_scored=20, second_half_goals_scored=32,
            first_half_goals_conceded=16, second_half_goals_conceded=26,
        ),
        form=TeamForm(results=["L", "W", "D", "W", "L", "W"]),
        players=[
            PlayerInfo("Ollie Watkins", "ST", goals=13, assists=9, rating=7.5),
            PlayerInfo("Morgan Rogers", "AM", goals=7, assists=8, rating=7.4),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 27), date(2025, 3, 23), date(2025, 3, 19)],
    )

    teams["tottenham"] = TeamSeason(
        name="Tottenham Hotspur",
        competition=Competition.PREMIER_LEAGUE,
        games_played=33, wins=14, draws=5, losses=14,
        goals_scored=62, goals_conceded=52,
        league_position=10, points=47,
        possession_avg=56.8, shots_per_game=15.5,
        shots_on_target_per_game=5.5, xg_per_game=1.85, xga_per_game=1.50,
        clean_sheets=5, failed_to_score=4,
        half_stats=HalfStats(
            first_half_goals_scored=28, second_half_goals_scored=34,
            first_half_goals_conceded=22, second_half_goals_conceded=30,
        ),
        form=TeamForm(results=["L", "W", "L", "W", "L", "D"]),
        players=[
            PlayerInfo("Son Heung-min", "LW", goals=14, assists=8, rating=7.6),
            PlayerInfo("Dominic Solanke", "ST", goals=10, assists=5, rating=7.0),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 26), date(2025, 3, 22)],
    )

    teams["man utd"] = TeamSeason(
        name="Manchester United",
        competition=Competition.PREMIER_LEAGUE,
        games_played=33, wins=12, draws=6, losses=15,
        goals_scored=42, goals_conceded=48,
        league_position=13, points=42,
        possession_avg=53.2, shots_per_game=12.8,
        shots_on_target_per_game=4.2, xg_per_game=1.40, xga_per_game=1.45,
        clean_sheets=7, failed_to_score=8,
        half_stats=HalfStats(
            first_half_goals_scored=16, second_half_goals_scored=26,
            first_half_goals_conceded=18, second_half_goals_conceded=30,
        ),
        form=TeamForm(results=["L", "D", "L", "W", "L", "L"]),
        players=[
            PlayerInfo("Bruno Fernandes", "AM", goals=8, assists=7, rating=7.2),
            PlayerInfo("Rasmus Hojlund", "ST", goals=9, assists=3, rating=6.8),
            PlayerInfo("Marcus Rashford", "LW", goals=5, assists=2, rating=6.2),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 27), date(2025, 3, 23)],
    )

    # ===== LA LIGA =====
    teams["barcelona"] = TeamSeason(
        name="FC Barcelona",
        competition=Competition.LA_LIGA,
        games_played=31, wins=22, draws=5, losses=4,
        goals_scored=75, goals_conceded=30,
        league_position=1, points=71,
        possession_avg=64.2, shots_per_game=17.5,
        shots_on_target_per_game=6.8, xg_per_game=2.30, xga_per_game=0.90,
        clean_sheets=15, failed_to_score=2,
        half_stats=HalfStats(
            first_half_goals_scored=38, second_half_goals_scored=37,
            first_half_goals_conceded=10, second_half_goals_conceded=20,
        ),
        form=TeamForm(results=["W", "W", "W", "D", "W", "W"]),
        players=[
            PlayerInfo("Robert Lewandowski", "ST", goals=22, assists=5, rating=8.3),
            PlayerInfo("Lamine Yamal", "RW", goals=10, assists=14, rating=8.4),
            PlayerInfo("Raphinha", "LW", goals=14, assists=10, rating=8.0),
            PlayerInfo("Pedri", "CM", goals=5, assists=9, rating=7.8),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 26), date(2025, 3, 22)],
    )

    teams["real madrid"] = TeamSeason(
        name="Real Madrid",
        competition=Competition.LA_LIGA,
        games_played=31, wins=20, draws=6, losses=5,
        goals_scored=65, goals_conceded=28,
        league_position=2, points=66,
        possession_avg=60.5, shots_per_game=15.8,
        shots_on_target_per_game=5.9, xg_per_game=1.95, xga_per_game=0.92,
        clean_sheets=14, failed_to_score=3,
        half_stats=HalfStats(
            first_half_goals_scored=28, second_half_goals_scored=37,
            first_half_goals_conceded=10, second_half_goals_conceded=18,
        ),
        form=TeamForm(results=["W", "D", "W", "W", "L", "W"]),
        players=[
            PlayerInfo("Kylian Mbappe", "ST", goals=16, assists=5, rating=7.8),
            PlayerInfo("Vinicius Jr", "LW", goals=14, assists=8, rating=8.1),
            PlayerInfo("Jude Bellingham", "AM", goals=10, assists=8, rating=7.9),
            PlayerInfo("Rodrygo", "RW", goals=8, assists=6, rating=7.5),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 27), date(2025, 3, 23), date(2025, 3, 19)],
    )

    teams["atletico madrid"] = TeamSeason(
        name="Atletico Madrid",
        competition=Competition.LA_LIGA,
        games_played=31, wins=19, draws=7, losses=5,
        goals_scored=55, goals_conceded=25,
        league_position=3, points=64,
        possession_avg=52.3, shots_per_game=13.2,
        shots_on_target_per_game=4.8, xg_per_game=1.65, xga_per_game=0.85,
        clean_sheets=16, failed_to_score=4,
        half_stats=HalfStats(
            first_half_goals_scored=22, second_half_goals_scored=33,
            first_half_goals_conceded=8, second_half_goals_conceded=17,
        ),
        form=TeamForm(results=["W", "W", "D", "W", "W", "D"]),
        players=[
            PlayerInfo("Antoine Griezmann", "AM", goals=12, assists=10, rating=7.9),
            PlayerInfo("Julian Alvarez", "ST", goals=11, assists=4, rating=7.5),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 26)],
    )

    # ===== BUNDESLIGA =====
    teams["bayern munich"] = TeamSeason(
        name="Bayern Munich",
        competition=Competition.BUNDESLIGA,
        games_played=28, wins=20, draws=4, losses=4,
        goals_scored=72, goals_conceded=30,
        league_position=1, points=64,
        possession_avg=62.8, shots_per_game=16.9,
        shots_on_target_per_game=6.5, xg_per_game=2.25, xga_per_game=1.00,
        clean_sheets=12, failed_to_score=2,
        half_stats=HalfStats(
            first_half_goals_scored=32, second_half_goals_scored=40,
            first_half_goals_conceded=10, second_half_goals_conceded=20,
        ),
        form=TeamForm(results=["W", "W", "W", "D", "W", "W"]),
        players=[
            PlayerInfo("Harry Kane", "ST", goals=25, assists=8, rating=8.7),
            PlayerInfo("Jamal Musiala", "AM", goals=12, assists=10, rating=8.3),
            PlayerInfo("Leroy Sane", "LW", goals=8, assists=7, rating=7.4),
        ],
        recent_match_dates=[date(2025, 3, 29), date(2025, 3, 25), date(2025, 3, 22)],
    )

    teams["bayer leverkusen"] = TeamSeason(
        name="Bayer Leverkusen",
        competition=Competition.BUNDESLIGA,
        games_played=28, wins=17, draws=7, losses=4,
        goals_scored=62, goals_conceded=32,
        league_position=2, points=58,
        possession_avg=58.5, shots_per_game=15.2,
        shots_on_target_per_game=5.8, xg_per_game=1.95, xga_per_game=1.10,
        clean_sheets=10, failed_to_score=3,
        half_stats=HalfStats(
            first_half_goals_scored=25, second_half_goals_scored=37,
            first_half_goals_conceded=12, second_half_goals_conceded=20,
        ),
        form=TeamForm(results=["W", "D", "W", "W", "D", "W"]),
        players=[
            PlayerInfo("Florian Wirtz", "AM", goals=14, assists=12, rating=8.5),
            PlayerInfo("Patrik Schick", "ST", goals=10, assists=3, rating=7.3),
        ],
        recent_match_dates=[date(2025, 3, 29), date(2025, 3, 25)],
    )

    teams["dortmund"] = TeamSeason(
        name="Borussia Dortmund",
        competition=Competition.BUNDESLIGA,
        games_played=28, wins=15, draws=5, losses=8,
        goals_scored=58, goals_conceded=38,
        league_position=4, points=50,
        possession_avg=55.2, shots_per_game=14.8,
        shots_on_target_per_game=5.2, xg_per_game=1.80, xga_per_game=1.25,
        clean_sheets=7, failed_to_score=4,
        half_stats=HalfStats(
            first_half_goals_scored=24, second_half_goals_scored=34,
            first_half_goals_conceded=15, second_half_goals_conceded=23,
        ),
        form=TeamForm(results=["W", "L", "W", "D", "W", "L"]),
        players=[
            PlayerInfo("Serhou Guirassy", "ST", goals=16, assists=3, rating=7.6),
            PlayerInfo("Julian Brandt", "AM", goals=7, assists=9, rating=7.5),
        ],
        recent_match_dates=[date(2025, 3, 29), date(2025, 3, 25), date(2025, 3, 22)],
    )

    # ===== SERIE A =====
    teams["inter milan"] = TeamSeason(
        name="Inter Milan",
        competition=Competition.SERIE_A,
        games_played=30, wins=22, draws=5, losses=3,
        goals_scored=65, goals_conceded=22,
        league_position=1, points=71,
        possession_avg=56.8, shots_per_game=15.5,
        shots_on_target_per_game=5.8, xg_per_game=1.95, xga_per_game=0.80,
        clean_sheets=17, failed_to_score=3,
        half_stats=HalfStats(
            first_half_goals_scored=28, second_half_goals_scored=37,
            first_half_goals_conceded=8, second_half_goals_conceded=14,
        ),
        form=TeamForm(results=["W", "W", "D", "W", "W", "W"]),
        players=[
            PlayerInfo("Lautaro Martinez", "ST", goals=18, assists=5, rating=8.1),
            PlayerInfo("Marcus Thuram", "ST", goals=14, assists=7, rating=7.8),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 26)],
    )

    teams["napoli"] = TeamSeason(
        name="SSC Napoli",
        competition=Competition.SERIE_A,
        games_played=30, wins=20, draws=5, losses=5,
        goals_scored=55, goals_conceded=24,
        league_position=2, points=65,
        possession_avg=53.5, shots_per_game=13.8,
        shots_on_target_per_game=5.2, xg_per_game=1.70, xga_per_game=0.90,
        clean_sheets=14, failed_to_score=4,
        half_stats=HalfStats(
            first_half_goals_scored=22, second_half_goals_scored=33,
            first_half_goals_conceded=8, second_half_goals_conceded=16,
        ),
        form=TeamForm(results=["W", "D", "W", "W", "L", "W"]),
        players=[
            PlayerInfo("Victor Osimhen", "ST", goals=15, assists=3, rating=7.9),
            PlayerInfo("Khvicha Kvaratskhelia", "LW", goals=10, assists=8, rating=7.7),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 26)],
    )

    teams["juventus"] = TeamSeason(
        name="Juventus",
        competition=Competition.SERIE_A,
        games_played=30, wins=13, draws=12, losses=5,
        goals_scored=42, goals_conceded=28,
        league_position=4, points=51,
        possession_avg=55.8, shots_per_game=14.2,
        shots_on_target_per_game=4.8, xg_per_game=1.55, xga_per_game=1.00,
        clean_sheets=10, failed_to_score=7,
        half_stats=HalfStats(
            first_half_goals_scored=18, second_half_goals_scored=24,
            first_half_goals_conceded=10, second_half_goals_conceded=18,
        ),
        form=TeamForm(results=["D", "W", "D", "D", "W", "D"]),
        players=[
            PlayerInfo("Dusan Vlahovic", "ST", goals=12, assists=3, rating=7.2),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 26), date(2025, 3, 22)],
    )

    # ===== LIGUE 1 =====
    teams["psg"] = TeamSeason(
        name="Paris Saint-Germain",
        competition=Competition.LIGUE_1,
        games_played=29, wins=22, draws=4, losses=3,
        goals_scored=62, goals_conceded=22,
        league_position=1, points=70,
        possession_avg=63.5, shots_per_game=17.8,
        shots_on_target_per_game=6.8, xg_per_game=2.20, xga_per_game=0.85,
        clean_sheets=16, failed_to_score=2,
        half_stats=HalfStats(
            first_half_goals_scored=28, second_half_goals_scored=34,
            first_half_goals_conceded=8, second_half_goals_conceded=14,
        ),
        form=TeamForm(results=["W", "W", "W", "D", "W", "W"]),
        players=[
            PlayerInfo("Bradley Barcola", "LW", goals=14, assists=8, rating=8.0),
            PlayerInfo("Ousmane Dembele", "RW", goals=12, assists=10, rating=7.8),
        ],
        recent_match_dates=[date(2025, 3, 30), date(2025, 3, 27), date(2025, 3, 23)],
    )

    return teams
