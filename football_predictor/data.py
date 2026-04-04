"""
Football team and match data models with historical statistics.
Covers Europe's top leagues, Champions League, and cups.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional


class Competition(Enum):
    PREMIER_LEAGUE = "Premier League"
    LA_LIGA = "La Liga"
    BUNDESLIGA = "Bundesliga"
    SERIE_A = "Serie A"
    LIGUE_1 = "Ligue 1"
    CHAMPIONSHIP = "EFL Championship"
    CHAMPIONS_LEAGUE = "Champions League"
    EUROPA_LEAGUE = "Europa League"
    CONFERENCE_LEAGUE = "Conference League"
    FA_CUP = "FA Cup"
    CARABAO_CUP = "Carabao Cup"
    COPA_DEL_REY = "Copa del Rey"
    DFB_POKAL = "DFB-Pokal"
    COPPA_ITALIA = "Coppa Italia"
    COUPE_DE_FRANCE = "Coupe de France"


@dataclass
class TeamForm:
    """Last N match results."""
    results: list[str] = field(default_factory=list)  # W/D/L

    @property
    def wins(self) -> int:
        return self.results.count("W")

    @property
    def draws(self) -> int:
        return self.results.count("D")

    @property
    def losses(self) -> int:
        return self.results.count("L")

    @property
    def points_from_last(self) -> int:
        return self.wins * 3 + self.draws

    @property
    def form_rating(self) -> float:
        """0-100 form rating, recent matches weighted more."""
        if not self.results:
            return 50.0
        total = 0.0
        weight_sum = 0.0
        for i, r in enumerate(self.results):
            weight = len(self.results) - i  # most recent = highest weight
            pts = {"W": 3, "D": 1, "L": 0}.get(r, 0)
            total += pts * weight
            weight_sum += 3 * weight
        return (total / weight_sum) * 100 if weight_sum > 0 else 50.0


@dataclass
class HalfStats:
    """Goals scored/conceded broken down by half."""
    first_half_goals_scored: int = 0
    second_half_goals_scored: int = 0
    first_half_goals_conceded: int = 0
    second_half_goals_conceded: int = 0

    @property
    def total_goals_scored(self) -> int:
        return self.first_half_goals_scored + self.second_half_goals_scored

    @property
    def total_goals_conceded(self) -> int:
        return self.first_half_goals_conceded + self.second_half_goals_conceded

    def avg_first_half_scored(self, games: int) -> float:
        return self.first_half_goals_scored / games if games > 0 else 0

    def avg_second_half_scored(self, games: int) -> float:
        return self.second_half_goals_scored / games if games > 0 else 0

    def avg_first_half_conceded(self, games: int) -> float:
        return self.first_half_goals_conceded / games if games > 0 else 0

    def avg_second_half_conceded(self, games: int) -> float:
        return self.second_half_goals_conceded / games if games > 0 else 0


@dataclass
class MonthlyRecord:
    """How a team performs in a given month."""
    month: int  # 1-12
    games: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0

    @property
    def points_per_game(self) -> float:
        if self.games == 0:
            return 0.0
        return (self.wins * 3 + self.draws) / self.games

    @property
    def goals_per_game(self) -> float:
        return self.goals_scored / self.games if self.games > 0 else 0


@dataclass
class PlayerInfo:
    name: str
    position: str
    goals: int = 0
    assists: int = 0
    minutes_played: int = 0
    injured: bool = False
    injury_description: str = ""
    suspended: bool = False
    rating: float = 0.0  # season average 1-10

    @property
    def available(self) -> bool:
        return not self.injured and not self.suspended


@dataclass
class HeadToHead:
    """Historical record between two teams."""
    opponent: str = ""
    games: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0
    last_results: list[str] = field(default_factory=list)  # W/D/L most recent first
    last_scores: list[str] = field(default_factory=list)  # "2-1", "0-0" etc

    @property
    def avg_goals_per_game(self) -> float:
        return (self.goals_scored + self.goals_conceded) / self.games if self.games > 0 else 0

    @property
    def win_pct(self) -> float:
        return (self.wins / self.games * 100) if self.games > 0 else 0


@dataclass
class TeamSeason:
    """Full season data for a team."""
    name: str
    competition: Competition
    games_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0
    league_position: int = 0
    points: int = 0
    possession_avg: float = 50.0
    shots_per_game: float = 0.0
    shots_on_target_per_game: float = 0.0
    xg_per_game: float = 0.0
    xga_per_game: float = 0.0
    clean_sheets: int = 0
    failed_to_score: int = 0

    # Corner stats
    corners_per_game: float = 5.0
    corners_conceded_per_game: float = 5.0

    # Half-by-half breakdown
    half_stats: HalfStats = field(default_factory=HalfStats)

    # Form (last 6 matches)
    form: TeamForm = field(default_factory=TeamForm)

    # Monthly records
    monthly_records: dict[int, MonthlyRecord] = field(default_factory=dict)

    # Squad
    players: list[PlayerInfo] = field(default_factory=list)

    # Starting lineup for current/upcoming match
    lineup: list[PlayerInfo] = field(default_factory=list)

    # Fixture congestion
    recent_match_dates: list[date] = field(default_factory=list)

    # Head-to-head records vs specific opponents
    head_to_head: dict[str, HeadToHead] = field(default_factory=dict)

    # Home/Away splits
    home_wins: int = 0
    home_draws: int = 0
    home_losses: int = 0
    home_goals_scored: int = 0
    home_goals_conceded: int = 0
    away_wins: int = 0
    away_draws: int = 0
    away_losses: int = 0
    away_goals_scored: int = 0
    away_goals_conceded: int = 0

    # Games with over X.5 goals in first half
    games_over_1_5_fh: int = 0
    games_over_2_5_fh: int = 0
    # Games with over X.5 goals in second half
    games_over_1_5_sh: int = 0
    games_over_2_5_sh: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_scored - self.goals_conceded

    @property
    def goals_per_game(self) -> float:
        return self.goals_scored / self.games_played if self.games_played > 0 else 0

    @property
    def goals_conceded_per_game(self) -> float:
        return self.goals_conceded / self.games_played if self.games_played > 0 else 0

    @property
    def points_per_game(self) -> float:
        return self.points / self.games_played if self.games_played > 0 else 0

    @property
    def clean_sheet_pct(self) -> float:
        return (self.clean_sheets / self.games_played * 100) if self.games_played > 0 else 0

    @property
    def scoring_rate(self) -> float:
        """Percentage of games where team scored."""
        if self.games_played == 0:
            return 0
        return ((self.games_played - self.failed_to_score) / self.games_played) * 100

    @property
    def best_player(self) -> Optional[PlayerInfo]:
        available = [p for p in self.players if p.available]
        if not available:
            return None
        return max(available, key=lambda p: p.rating)

    @property
    def key_injuries(self) -> list[PlayerInfo]:
        return [p for p in self.players if p.injured]

    @property
    def suspended_players(self) -> list[PlayerInfo]:
        return [p for p in self.players if p.suspended]

    def games_in_last_n_days(self, n: int = 21) -> int:
        today = date.today()
        return sum(1 for d in self.recent_match_dates
                   if (today - d).days <= n)

    @property
    def fatigue_score(self) -> float:
        """0-100 fatigue rating based on fixture congestion."""
        games_21 = self.games_in_last_n_days(21)
        if games_21 <= 2:
            return 10.0
        elif games_21 == 3:
            return 30.0
        elif games_21 == 4:
            return 55.0
        elif games_21 == 5:
            return 75.0
        else:
            return 90.0

    def month_performance(self, month: int) -> Optional[MonthlyRecord]:
        return self.monthly_records.get(month)

    @property
    def pressure_score(self) -> float:
        """0-100 pressure rating based on league position and expectations."""
        if self.games_played < 5:
            return 30.0
        ppg = self.points_per_game
        # Teams near top under title pressure, teams near bottom under relegation pressure
        if self.league_position <= 2:
            return 70.0 + (2 - self.league_position) * 10
        elif self.league_position <= 4:
            return 55.0
        elif self.league_position <= 6:
            return 40.0
        elif self.league_position >= 18:
            return 80.0 + min((self.league_position - 18) * 5, 15)
        elif self.league_position >= 15:
            return 60.0
        else:
            return 30.0


@dataclass
class MatchContext:
    """Context for a specific match prediction."""
    home_team: TeamSeason
    away_team: TeamSeason
    competition: Competition
    match_date: date
    is_cup_match: bool = False
    is_knockout: bool = False
    # Live match state (for in-game predictions)
    is_live: bool = False
    current_minute: int = 0
    home_goals: int = 0
    away_goals: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0
    home_possession: float = 50.0
    away_possession: float = 50.0
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_xg: float = 0.0
    away_xg: float = 0.0
    home_corners: int = 0
    away_corners: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    # First-half goals (for live half-specific predictions)
    home_first_half_goals: int = 0
    away_first_half_goals: int = 0
    # Lineups
    home_lineup: list[str] = field(default_factory=list)
    away_lineup: list[str] = field(default_factory=list)

    @property
    def is_halftime(self) -> bool:
        return 45 <= self.current_minute <= 46 and self.is_live

    @property
    def is_second_half(self) -> bool:
        return self.current_minute >= 46 and self.is_live

    @property
    def scoreline(self) -> str:
        return f"{self.home_goals}-{self.away_goals}"

    @property
    def total_goals(self) -> int:
        return self.home_goals + self.away_goals

    @property
    def total_corners(self) -> int:
        return self.home_corners + self.away_corners

    @property
    def second_half_goals(self) -> int:
        return self.total_goals - self.home_first_half_goals - self.away_first_half_goals
