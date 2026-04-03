"""
Fallback sample data for 2025/26 season.
Used ONLY when no API key is configured.
For live, accurate data, set FOOTBALL_DATA_API_KEY.

Get a free key at: https://www.football-data.org/client/register
"""

from datetime import date, timedelta
from .data import (
    Competition, HalfStats, MonthlyRecord, PlayerInfo,
    TeamForm, TeamSeason,
)


def _recent_dates(*days_ago: int) -> list[date]:
    today = date.today()
    return [today - timedelta(days=d) for d in days_ago]


def get_sample_teams() -> dict[str, TeamSeason]:
    """Return fallback 2025/26 team data.

    NOTE: This data is approximate and will become outdated.
    For real-time data, get a free API key from football-data.org
    and set the FOOTBALL_DATA_API_KEY environment variable.
    """
    teams = {}

    # ===== PREMIER LEAGUE 2025/26 =====
    # (Season starts Aug 2025, these are projections based on squads)

    teams["liverpool"] = TeamSeason(
        name="Liverpool",
        competition=Competition.PREMIER_LEAGUE,
        games_played=6, wins=4, draws=1, losses=1,
        goals_scored=14, goals_conceded=6,
        league_position=2, points=13,
        possession_avg=57.5, shots_per_game=15.8,
        shots_on_target_per_game=6.2, xg_per_game=2.10, xga_per_game=1.00,
        clean_sheets=2, failed_to_score=0,
        half_stats=HalfStats(
            first_half_goals_scored=6, second_half_goals_scored=8,
            first_half_goals_conceded=2, second_half_goals_conceded=4,
        ),
        form=TeamForm(results=["W", "W", "D", "W", "L", "W"]),
        players=[
            PlayerInfo("Mohamed Salah", "RW", goals=5, assists=3, rating=8.3),
            PlayerInfo("Virgil van Dijk", "CB", goals=1, assists=0, rating=7.6),
            PlayerInfo("Alexis Mac Allister", "CM", goals=1, assists=2, rating=7.4),
            PlayerInfo("Cody Gakpo", "LW", goals=3, assists=1, rating=7.5),
            PlayerInfo("Ryan Gravenberch", "DM", goals=1, assists=1, rating=7.5),
        ],
        recent_match_dates=_recent_dates(3, 7, 14, 18),
    )

    teams["arsenal"] = TeamSeason(
        name="Arsenal",
        competition=Competition.PREMIER_LEAGUE,
        games_played=6, wins=5, draws=1, losses=0,
        goals_scored=15, goals_conceded=3,
        league_position=1, points=16,
        possession_avg=61.2, shots_per_game=16.5,
        shots_on_target_per_game=6.0, xg_per_game=2.15, xga_per_game=0.82,
        clean_sheets=3, failed_to_score=0,
        half_stats=HalfStats(
            first_half_goals_scored=7, second_half_goals_scored=8,
            first_half_goals_conceded=1, second_half_goals_conceded=2,
        ),
        form=TeamForm(results=["W", "W", "W", "D", "W", "W"]),
        players=[
            PlayerInfo("Bukayo Saka", "RW", goals=4, assists=3, rating=8.4),
            PlayerInfo("Kai Havertz", "CF", goals=3, assists=1, rating=7.5),
            PlayerInfo("Martin Odegaard", "CAM", goals=2, assists=4, rating=8.0),
            PlayerInfo("William Saliba", "CB", goals=0, assists=0, rating=7.9),
            PlayerInfo("Declan Rice", "CM", goals=1, assists=2, rating=7.7),
        ],
        recent_match_dates=_recent_dates(3, 7, 14),
    )

    teams["man city"] = TeamSeason(
        name="Manchester City",
        competition=Competition.PREMIER_LEAGUE,
        games_played=6, wins=4, draws=1, losses=1,
        goals_scored=12, goals_conceded=5,
        league_position=3, points=13,
        possession_avg=64.0, shots_per_game=17.5,
        shots_on_target_per_game=6.5, xg_per_game=2.20, xga_per_game=1.05,
        clean_sheets=2, failed_to_score=1,
        half_stats=HalfStats(
            first_half_goals_scored=5, second_half_goals_scored=7,
            first_half_goals_conceded=2, second_half_goals_conceded=3,
        ),
        form=TeamForm(results=["W", "D", "W", "L", "W", "W"]),
        players=[
            PlayerInfo("Erling Haaland", "ST", goals=6, assists=1, rating=8.5),
            PlayerInfo("Phil Foden", "AM", goals=2, assists=2, rating=7.4),
            PlayerInfo("Kevin De Bruyne", "CM", goals=1, assists=3, rating=7.8),
            PlayerInfo("Rodri", "DM", goals=0, assists=1, rating=7.5),
        ],
        recent_match_dates=_recent_dates(3, 7, 11, 14, 18),
    )

    teams["chelsea"] = TeamSeason(
        name="Chelsea",
        competition=Competition.PREMIER_LEAGUE,
        games_played=6, wins=3, draws=2, losses=1,
        goals_scored=10, goals_conceded=6,
        league_position=5, points=11,
        possession_avg=56.0, shots_per_game=14.8,
        shots_on_target_per_game=5.3, xg_per_game=1.80, xga_per_game=1.15,
        clean_sheets=2, failed_to_score=1,
        half_stats=HalfStats(
            first_half_goals_scored=4, second_half_goals_scored=6,
            first_half_goals_conceded=2, second_half_goals_conceded=4,
        ),
        form=TeamForm(results=["D", "W", "L", "W", "W", "D"]),
        players=[
            PlayerInfo("Cole Palmer", "AM", goals=4, assists=3, rating=8.2),
            PlayerInfo("Nicolas Jackson", "ST", goals=3, assists=1, rating=7.2),
        ],
        recent_match_dates=_recent_dates(3, 7, 14),
    )

    teams["man utd"] = TeamSeason(
        name="Manchester United",
        competition=Competition.PREMIER_LEAGUE,
        games_played=6, wins=2, draws=2, losses=2,
        goals_scored=7, goals_conceded=8,
        league_position=10, points=8,
        possession_avg=52.5, shots_per_game=12.5,
        shots_on_target_per_game=4.0, xg_per_game=1.35, xga_per_game=1.40,
        clean_sheets=1, failed_to_score=2,
        half_stats=HalfStats(
            first_half_goals_scored=2, second_half_goals_scored=5,
            first_half_goals_conceded=3, second_half_goals_conceded=5,
        ),
        form=TeamForm(results=["L", "D", "W", "L", "W", "D"]),
        players=[
            PlayerInfo("Bruno Fernandes", "AM", goals=2, assists=2, rating=7.1),
            PlayerInfo("Rasmus Hojlund", "ST", goals=2, assists=0, rating=6.8),
            PlayerInfo("Marcus Rashford", "LW", goals=1, assists=1, rating=6.3),
        ],
        recent_match_dates=_recent_dates(3, 7, 14),
    )

    teams["tottenham"] = TeamSeason(
        name="Tottenham Hotspur",
        competition=Competition.PREMIER_LEAGUE,
        games_played=6, wins=3, draws=1, losses=2,
        goals_scored=11, goals_conceded=9,
        league_position=7, points=10,
        possession_avg=57.0, shots_per_game=15.8,
        shots_on_target_per_game=5.5, xg_per_game=1.90, xga_per_game=1.45,
        clean_sheets=1, failed_to_score=1,
        half_stats=HalfStats(
            first_half_goals_scored=5, second_half_goals_scored=6,
            first_half_goals_conceded=4, second_half_goals_conceded=5,
        ),
        form=TeamForm(results=["L", "W", "L", "W", "D", "W"]),
        players=[
            PlayerInfo("Son Heung-min", "LW", goals=3, assists=2, rating=7.6),
            PlayerInfo("Dominic Solanke", "ST", goals=3, assists=1, rating=7.1),
        ],
        recent_match_dates=_recent_dates(3, 7, 14),
    )

    teams["aston villa"] = TeamSeason(
        name="Aston Villa",
        competition=Competition.PREMIER_LEAGUE,
        games_played=6, wins=3, draws=1, losses=2,
        goals_scored=9, goals_conceded=7,
        league_position=6, points=10,
        possession_avg=52.5, shots_per_game=13.5,
        shots_on_target_per_game=4.8, xg_per_game=1.55, xga_per_game=1.18,
        clean_sheets=2, failed_to_score=1,
        half_stats=HalfStats(
            first_half_goals_scored=3, second_half_goals_scored=6,
            first_half_goals_conceded=3, second_half_goals_conceded=4,
        ),
        form=TeamForm(results=["L", "W", "D", "W", "L", "W"]),
        players=[
            PlayerInfo("Ollie Watkins", "ST", goals=3, assists=2, rating=7.5),
            PlayerInfo("Morgan Rogers", "AM", goals=2, assists=2, rating=7.3),
        ],
        recent_match_dates=_recent_dates(3, 7, 11, 14),
    )

    teams["newcastle"] = TeamSeason(
        name="Newcastle United",
        competition=Competition.PREMIER_LEAGUE,
        games_played=6, wins=3, draws=2, losses=1,
        goals_scored=10, goals_conceded=5,
        league_position=4, points=11,
        possession_avg=53.0, shots_per_game=14.2,
        shots_on_target_per_game=5.0, xg_per_game=1.70, xga_per_game=1.00,
        clean_sheets=2, failed_to_score=1,
        half_stats=HalfStats(
            first_half_goals_scored=4, second_half_goals_scored=6,
            first_half_goals_conceded=2, second_half_goals_conceded=3,
        ),
        form=TeamForm(results=["W", "D", "W", "L", "W", "D"]),
        players=[
            PlayerInfo("Alexander Isak", "ST", goals=4, assists=1, rating=8.0),
            PlayerInfo("Bruno Guimaraes", "CM", goals=1, assists=3, rating=7.6),
        ],
        recent_match_dates=_recent_dates(3, 7, 14),
    )

    teams["nottingham forest"] = TeamSeason(
        name="Nottingham Forest",
        competition=Competition.PREMIER_LEAGUE,
        games_played=6, wins=3, draws=1, losses=2,
        goals_scored=8, goals_conceded=6,
        league_position=8, points=10,
        possession_avg=44.5, shots_per_game=11.0,
        shots_on_target_per_game=4.2, xg_per_game=1.30, xga_per_game=1.25,
        clean_sheets=2, failed_to_score=1,
        half_stats=HalfStats(
            first_half_goals_scored=3, second_half_goals_scored=5,
            first_half_goals_conceded=2, second_half_goals_conceded=4,
        ),
        form=TeamForm(results=["W", "L", "W", "W", "D", "L"]),
        players=[
            PlayerInfo("Chris Wood", "ST", goals=3, assists=0, rating=7.5),
            PlayerInfo("Morgan Gibbs-White", "AM", goals=1, assists=3, rating=7.3),
        ],
        recent_match_dates=_recent_dates(3, 7),
    )

    # ===== LA LIGA 2025/26 =====

    teams["barcelona"] = TeamSeason(
        name="FC Barcelona",
        competition=Competition.LA_LIGA,
        games_played=6, wins=5, draws=0, losses=1,
        goals_scored=16, goals_conceded=5,
        league_position=1, points=15,
        possession_avg=65.0, shots_per_game=18.0,
        shots_on_target_per_game=7.0, xg_per_game=2.40, xga_per_game=0.88,
        clean_sheets=2, failed_to_score=0,
        half_stats=HalfStats(
            first_half_goals_scored=8, second_half_goals_scored=8,
            first_half_goals_conceded=2, second_half_goals_conceded=3,
        ),
        form=TeamForm(results=["W", "W", "L", "W", "W", "W"]),
        players=[
            PlayerInfo("Robert Lewandowski", "ST", goals=5, assists=1, rating=8.2),
            PlayerInfo("Lamine Yamal", "RW", goals=3, assists=4, rating=8.5),
            PlayerInfo("Raphinha", "LW", goals=3, assists=2, rating=7.9),
            PlayerInfo("Pedri", "CM", goals=1, assists=3, rating=7.8),
        ],
        recent_match_dates=_recent_dates(4, 7, 14),
    )

    teams["real madrid"] = TeamSeason(
        name="Real Madrid",
        competition=Competition.LA_LIGA,
        games_played=6, wins=4, draws=1, losses=1,
        goals_scored=13, goals_conceded=5,
        league_position=2, points=13,
        possession_avg=61.0, shots_per_game=16.0,
        shots_on_target_per_game=6.0, xg_per_game=2.00, xga_per_game=0.90,
        clean_sheets=2, failed_to_score=0,
        half_stats=HalfStats(
            first_half_goals_scored=5, second_half_goals_scored=8,
            first_half_goals_conceded=2, second_half_goals_conceded=3,
        ),
        form=TeamForm(results=["W", "D", "W", "W", "L", "W"]),
        players=[
            PlayerInfo("Kylian Mbappe", "ST", goals=4, assists=2, rating=8.0),
            PlayerInfo("Vinicius Jr", "LW", goals=3, assists=2, rating=8.1),
            PlayerInfo("Jude Bellingham", "AM", goals=2, assists=3, rating=7.8),
        ],
        recent_match_dates=_recent_dates(4, 7, 11, 14),
    )

    teams["atletico madrid"] = TeamSeason(
        name="Atletico Madrid",
        competition=Competition.LA_LIGA,
        games_played=6, wins=4, draws=1, losses=1,
        goals_scored=10, goals_conceded=4,
        league_position=3, points=13,
        possession_avg=52.0, shots_per_game=13.0,
        shots_on_target_per_game=4.8, xg_per_game=1.60, xga_per_game=0.82,
        clean_sheets=3, failed_to_score=1,
        half_stats=HalfStats(
            first_half_goals_scored=4, second_half_goals_scored=6,
            first_half_goals_conceded=1, second_half_goals_conceded=3,
        ),
        form=TeamForm(results=["W", "W", "D", "W", "L", "W"]),
        players=[
            PlayerInfo("Antoine Griezmann", "AM", goals=3, assists=2, rating=7.8),
            PlayerInfo("Julian Alvarez", "ST", goals=3, assists=1, rating=7.5),
        ],
        recent_match_dates=_recent_dates(4, 7),
    )

    # ===== BUNDESLIGA 2025/26 =====

    teams["bayern munich"] = TeamSeason(
        name="Bayern Munich",
        competition=Competition.BUNDESLIGA,
        games_played=5, wins=4, draws=1, losses=0,
        goals_scored=15, goals_conceded=4,
        league_position=1, points=13,
        possession_avg=63.0, shots_per_game=17.0,
        shots_on_target_per_game=6.8, xg_per_game=2.30, xga_per_game=0.95,
        clean_sheets=2, failed_to_score=0,
        half_stats=HalfStats(
            first_half_goals_scored=7, second_half_goals_scored=8,
            first_half_goals_conceded=1, second_half_goals_conceded=3,
        ),
        form=TeamForm(results=["W", "W", "D", "W", "W"]),
        players=[
            PlayerInfo("Harry Kane", "ST", goals=6, assists=2, rating=8.8),
            PlayerInfo("Jamal Musiala", "AM", goals=3, assists=3, rating=8.3),
        ],
        recent_match_dates=_recent_dates(4, 7, 14),
    )

    teams["bayer leverkusen"] = TeamSeason(
        name="Bayer Leverkusen",
        competition=Competition.BUNDESLIGA,
        games_played=5, wins=3, draws=2, losses=0,
        goals_scored=12, goals_conceded=5,
        league_position=2, points=11,
        possession_avg=58.5, shots_per_game=15.0,
        shots_on_target_per_game=5.8, xg_per_game=1.95, xga_per_game=1.05,
        clean_sheets=2, failed_to_score=0,
        half_stats=HalfStats(
            first_half_goals_scored=4, second_half_goals_scored=8,
            first_half_goals_conceded=2, second_half_goals_conceded=3,
        ),
        form=TeamForm(results=["W", "D", "W", "W", "D"]),
        players=[
            PlayerInfo("Florian Wirtz", "AM", goals=4, assists=3, rating=8.5),
        ],
        recent_match_dates=_recent_dates(4, 7),
    )

    teams["dortmund"] = TeamSeason(
        name="Borussia Dortmund",
        competition=Competition.BUNDESLIGA,
        games_played=5, wins=3, draws=0, losses=2,
        goals_scored=10, goals_conceded=7,
        league_position=4, points=9,
        possession_avg=55.0, shots_per_game=14.5,
        shots_on_target_per_game=5.2, xg_per_game=1.80, xga_per_game=1.20,
        clean_sheets=1, failed_to_score=1,
        half_stats=HalfStats(
            first_half_goals_scored=4, second_half_goals_scored=6,
            first_half_goals_conceded=3, second_half_goals_conceded=4,
        ),
        form=TeamForm(results=["W", "L", "W", "L", "W"]),
        players=[
            PlayerInfo("Serhou Guirassy", "ST", goals=4, assists=1, rating=7.7),
        ],
        recent_match_dates=_recent_dates(4, 7, 14),
    )

    # ===== SERIE A 2025/26 =====

    teams["inter milan"] = TeamSeason(
        name="Inter Milan",
        competition=Competition.SERIE_A,
        games_played=5, wins=4, draws=1, losses=0,
        goals_scored=12, goals_conceded=3,
        league_position=1, points=13,
        possession_avg=57.0, shots_per_game=15.5,
        shots_on_target_per_game=5.8, xg_per_game=2.00, xga_per_game=0.78,
        clean_sheets=3, failed_to_score=0,
        half_stats=HalfStats(
            first_half_goals_scored=5, second_half_goals_scored=7,
            first_half_goals_conceded=1, second_half_goals_conceded=2,
        ),
        form=TeamForm(results=["W", "W", "D", "W", "W"]),
        players=[
            PlayerInfo("Lautaro Martinez", "ST", goals=4, assists=1, rating=8.1),
            PlayerInfo("Marcus Thuram", "ST", goals=3, assists=2, rating=7.8),
        ],
        recent_match_dates=_recent_dates(4, 7),
    )

    teams["napoli"] = TeamSeason(
        name="SSC Napoli",
        competition=Competition.SERIE_A,
        games_played=5, wins=3, draws=2, losses=0,
        goals_scored=9, goals_conceded=3,
        league_position=2, points=11,
        possession_avg=54.0, shots_per_game=14.0,
        shots_on_target_per_game=5.2, xg_per_game=1.72, xga_per_game=0.88,
        clean_sheets=2, failed_to_score=1,
        half_stats=HalfStats(
            first_half_goals_scored=4, second_half_goals_scored=5,
            first_half_goals_conceded=1, second_half_goals_conceded=2,
        ),
        form=TeamForm(results=["W", "D", "W", "D", "W"]),
        players=[
            PlayerInfo("Victor Osimhen", "ST", goals=3, assists=0, rating=7.8),
        ],
        recent_match_dates=_recent_dates(4, 7),
    )

    teams["juventus"] = TeamSeason(
        name="Juventus",
        competition=Competition.SERIE_A,
        games_played=5, wins=2, draws=3, losses=0,
        goals_scored=7, goals_conceded=4,
        league_position=4, points=9,
        possession_avg=56.0, shots_per_game=14.0,
        shots_on_target_per_game=4.8, xg_per_game=1.55, xga_per_game=0.98,
        clean_sheets=2, failed_to_score=1,
        half_stats=HalfStats(
            first_half_goals_scored=3, second_half_goals_scored=4,
            first_half_goals_conceded=1, second_half_goals_conceded=3,
        ),
        form=TeamForm(results=["D", "W", "D", "D", "W"]),
        players=[
            PlayerInfo("Dusan Vlahovic", "ST", goals=3, assists=0, rating=7.3),
        ],
        recent_match_dates=_recent_dates(4, 7, 14),
    )

    # ===== LIGUE 1 2025/26 =====

    teams["psg"] = TeamSeason(
        name="Paris Saint-Germain",
        competition=Competition.LIGUE_1,
        games_played=6, wins=5, draws=1, losses=0,
        goals_scored=14, goals_conceded=3,
        league_position=1, points=16,
        possession_avg=64.0, shots_per_game=18.0,
        shots_on_target_per_game=7.0, xg_per_game=2.25, xga_per_game=0.80,
        clean_sheets=3, failed_to_score=0,
        half_stats=HalfStats(
            first_half_goals_scored=6, second_half_goals_scored=8,
            first_half_goals_conceded=1, second_half_goals_conceded=2,
        ),
        form=TeamForm(results=["W", "W", "W", "D", "W", "W"]),
        players=[
            PlayerInfo("Bradley Barcola", "LW", goals=4, assists=2, rating=8.0),
            PlayerInfo("Ousmane Dembele", "RW", goals=3, assists=3, rating=7.9),
        ],
        recent_match_dates=_recent_dates(4, 7, 11),
    )

    return teams
