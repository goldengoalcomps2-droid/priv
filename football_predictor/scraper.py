"""
Live data fetcher using free football APIs.
Uses football-data.org (free tier: 10 req/min) for standings, matches, scorers.
"""

import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import date, datetime, timedelta
from typing import Optional

from .data import (
    Competition, HalfStats, MonthlyRecord, PlayerInfo,
    TeamForm, TeamSeason, MatchContext,
)

# football-data.org free API - 10 requests/minute
API_BASE = "https://api.football-data.org/v4"

# Competition IDs on football-data.org (free tier covers these)
COMPETITION_IDS = {
    Competition.PREMIER_LEAGUE: "PL",
    Competition.LA_LIGA: "PD",
    Competition.BUNDESLIGA: "BL1",
    Competition.SERIE_A: "SA",
    Competition.LIGUE_1: "FL1",
    Competition.CHAMPIONSHIP: "ELC",
    Competition.CHAMPIONS_LEAGUE: "CL",
}

# Rate limiting: track last request time
_last_request_time = 0.0


def _api_get(endpoint: str, api_key: str) -> dict:
    """Make a request to football-data.org API with rate limiting."""
    global _last_request_time

    # Rate limit: minimum 6 seconds between requests (10/min)
    elapsed = time.time() - _last_request_time
    if elapsed < 6.5:
        time.sleep(6.5 - elapsed)

    url = f"{API_BASE}{endpoint}"
    req = urllib.request.Request(url)
    req.add_header("X-Auth-Token", api_key)
    try:
        _last_request_time = time.time()
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("  Rate limited — waiting 60s...")
            time.sleep(60)
            return _api_get(endpoint, api_key)
        print(f"  API error {e.code}: {e.reason}")
        return {}
    except Exception as e:
        print(f"  Request failed: {e}")
        return {}


def fetch_standings(competition: Competition, api_key: str) -> dict[str, dict]:
    """Fetch league standings. Returns {team_name: {position, played, won, ...}}."""
    comp_id = COMPETITION_IDS.get(competition)
    if not comp_id:
        return {}

    data = _api_get(f"/competitions/{comp_id}/standings", api_key)
    if not data or "standings" not in data:
        return {}

    teams = {}
    for standing_type in data["standings"]:
        if standing_type.get("type") == "TOTAL":
            for entry in standing_type.get("table", []):
                team_name = entry["team"]["name"]
                teams[team_name] = {
                    "id": entry["team"]["id"],
                    "position": entry["position"],
                    "played": entry["playedGames"],
                    "won": entry["won"],
                    "draw": entry["draw"],
                    "lost": entry["lost"],
                    "goals_for": entry["goalsFor"],
                    "goals_against": entry["goalsAgainst"],
                    "goal_difference": entry["goalDifference"],
                    "points": entry["points"],
                }
    return teams


def fetch_team_matches(team_id: int, api_key: str, limit: int = 15) -> list[dict]:
    """Fetch recent finished matches for a team."""
    data = _api_get(
        f"/teams/{team_id}/matches?status=FINISHED&limit={limit}", api_key
    )
    if not data or "matches" not in data:
        return []
    return data["matches"]


def fetch_scorers(competition: Competition, api_key: str, limit: int = 25) -> list[dict]:
    """Fetch top scorers for a competition."""
    comp_id = COMPETITION_IDS.get(competition)
    if not comp_id:
        return []

    data = _api_get(f"/competitions/{comp_id}/scorers?limit={limit}", api_key)
    if not data or "scorers" not in data:
        return []
    return data["scorers"]


def _extract_form(matches: list[dict], team_id: int) -> TeamForm:
    """Extract W/D/L form from recent matches."""
    results = []
    for m in matches[:6]:
        home_id = m.get("homeTeam", {}).get("id")
        score = m.get("score", {}).get("fullTime", {})
        hg = score.get("home")
        ag = score.get("away")
        if hg is None or ag is None:
            continue
        if home_id == team_id:
            if hg > ag:
                results.append("W")
            elif hg == ag:
                results.append("D")
            else:
                results.append("L")
        else:
            if ag > hg:
                results.append("W")
            elif ag == hg:
                results.append("D")
            else:
                results.append("L")
    return TeamForm(results=results)


def _extract_half_stats(matches: list[dict], team_id: int) -> HalfStats:
    """Extract first/second half goal breakdown from match data."""
    stats = HalfStats()
    for m in matches:
        home_id = m.get("homeTeam", {}).get("id")
        score = m.get("score", {})
        ht = score.get("halfTime", {})
        ft = score.get("fullTime", {})

        ht_home = ht.get("home")
        ht_away = ht.get("away")
        ft_home = ft.get("home")
        ft_away = ft.get("away")

        if any(v is None for v in [ht_home, ht_away, ft_home, ft_away]):
            continue

        sh_home = ft_home - ht_home  # 2nd half home goals
        sh_away = ft_away - ht_away  # 2nd half away goals

        if home_id == team_id:
            stats.first_half_goals_scored += ht_home
            stats.second_half_goals_scored += sh_home
            stats.first_half_goals_conceded += ht_away
            stats.second_half_goals_conceded += sh_away
        else:
            stats.first_half_goals_scored += ht_away
            stats.second_half_goals_scored += sh_away
            stats.first_half_goals_conceded += ht_home
            stats.second_half_goals_conceded += sh_home

    return stats


def _extract_recent_dates(matches: list[dict]) -> list[date]:
    """Extract match dates from recent matches."""
    dates = []
    for m in matches:
        utc_date = m.get("utcDate", "")
        if utc_date:
            try:
                dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
                dates.append(dt.date())
            except ValueError:
                pass
    return dates


def _count_clean_sheets(matches: list[dict], team_id: int) -> int:
    """Count clean sheets from match data."""
    cs = 0
    for m in matches:
        home_id = m.get("homeTeam", {}).get("id")
        ft = m.get("score", {}).get("fullTime", {})
        if home_id == team_id:
            if ft.get("away", 1) == 0:
                cs += 1
        else:
            if ft.get("home", 1) == 0:
                cs += 1
    return cs


def _count_failed_to_score(matches: list[dict], team_id: int) -> int:
    """Count games where team failed to score."""
    fts = 0
    for m in matches:
        home_id = m.get("homeTeam", {}).get("id")
        ft = m.get("score", {}).get("fullTime", {})
        if home_id == team_id:
            if ft.get("home", 1) == 0:
                fts += 1
        else:
            if ft.get("away", 1) == 0:
                fts += 1
    return fts


def build_team_from_standings_and_matches(
    team_name: str,
    team_data: dict,
    competition: Competition,
    api_key: str,
) -> TeamSeason:
    """Build a full TeamSeason from standings + match history."""
    team_id = team_data.get("id", 0)

    team = TeamSeason(
        name=team_name,
        competition=competition,
        games_played=team_data["played"],
        wins=team_data["won"],
        draws=team_data["draw"],
        losses=team_data["lost"],
        goals_scored=team_data["goals_for"],
        goals_conceded=team_data["goals_against"],
        league_position=team_data["position"],
        points=team_data["points"],
    )

    # Fetch match history for deeper stats
    if team_id and api_key:
        matches = fetch_team_matches(team_id, api_key, limit=15)
        if matches:
            team.form = _extract_form(matches, team_id)
            team.half_stats = _extract_half_stats(matches, team_id)
            team.recent_match_dates = _extract_recent_dates(matches)
            team.clean_sheets = _count_clean_sheets(matches, team_id)
            team.failed_to_score = _count_failed_to_score(matches, team_id)

    return team


def build_team_season_from_api(
    team_name: str,
    competition: Competition,
    api_key: str,
) -> Optional[TeamSeason]:
    """Build a TeamSeason by searching standings for a team name."""
    standings = fetch_standings(competition, api_key)
    if not standings:
        return None

    team_data = None
    matched_name = None
    name_lower = team_name.lower()
    for sname, sdata in standings.items():
        if (name_lower in sname.lower()
                or sname.lower() in name_lower
                or _fuzzy_match(name_lower, sname.lower())):
            team_data = sdata
            matched_name = sname
            break

    if not team_data:
        return None

    return build_team_from_standings_and_matches(
        matched_name or team_name, team_data, competition, api_key
    )


def load_all_teams_for_league(
    competition: Competition,
    api_key: str,
    fetch_matches: bool = False,
) -> dict[str, TeamSeason]:
    """Load all teams in a league from the API.

    If fetch_matches=True, also fetches match history per team (slow, 1 API call per team).
    If False, only uses standings data (fast, 1 API call per league).
    """
    standings = fetch_standings(competition, api_key)
    if not standings:
        return {}

    teams = {}
    for team_name, team_data in standings.items():
        if fetch_matches:
            print(f"    Loading {team_name}...")
            team = build_team_from_standings_and_matches(
                team_name, team_data, competition, api_key
            )
        else:
            team = TeamSeason(
                name=team_name,
                competition=competition,
                games_played=team_data["played"],
                wins=team_data["won"],
                draws=team_data["draw"],
                losses=team_data["lost"],
                goals_scored=team_data["goals_for"],
                goals_conceded=team_data["goals_against"],
                league_position=team_data["position"],
                points=team_data["points"],
            )
        # Key by lowercase for easy lookup
        key = team_name.lower().replace("fc ", "").replace(" fc", "").strip()
        teams[key] = team

    return teams


def load_all_leagues(
    api_key: str,
    leagues: Optional[list[Competition]] = None,
    fetch_matches: bool = False,
) -> dict[str, TeamSeason]:
    """Load teams from multiple leagues.

    Default leagues (free tier): PL, La Liga, Bundesliga, Serie A, Ligue 1, Championship, CL.
    """
    if leagues is None:
        leagues = [
            Competition.PREMIER_LEAGUE,
            Competition.LA_LIGA,
            Competition.BUNDESLIGA,
            Competition.SERIE_A,
            Competition.LIGUE_1,
            Competition.CHAMPIONSHIP,
            Competition.CHAMPIONS_LEAGUE,
        ]

    all_teams = {}
    for comp in leagues:
        print(f"  Loading {comp.value}...")
        league_teams = load_all_teams_for_league(comp, api_key, fetch_matches)
        all_teams.update(league_teams)
        print(f"    -> {len(league_teams)} teams loaded")

    return all_teams


def enrich_team_with_matches(team: TeamSeason, api_key: str, team_id: int) -> None:
    """Enrich an existing team with match-level data (form, half stats, etc.)."""
    matches = fetch_team_matches(team_id, api_key, limit=15)
    if matches:
        team.form = _extract_form(matches, team_id)
        team.half_stats = _extract_half_stats(matches, team_id)
        team.recent_match_dates = _extract_recent_dates(matches)
        team.clean_sheets = _count_clean_sheets(matches, team_id)
        team.failed_to_score = _count_failed_to_score(matches, team_id)


def enrich_league_with_scorers(
    teams: dict[str, TeamSeason],
    competition: Competition,
    api_key: str,
) -> None:
    """Add top scorer data as player info to teams."""
    scorers = fetch_scorers(competition, api_key, limit=25)
    for s in scorers:
        player_name = s.get("player", {}).get("name", "")
        team_name = s.get("team", {}).get("name", "")
        goals = s.get("goals", 0) or 0
        assists = s.get("assists", 0) or 0

        # Find the team
        for key, team in teams.items():
            if team.name == team_name or team_name.lower() in key:
                # Check if player already exists
                existing = [p for p in team.players if p.name == player_name]
                if existing:
                    existing[0].goals = goals
                    existing[0].assists = assists
                else:
                    team.players.append(PlayerInfo(
                        name=player_name,
                        position="FW",
                        goals=goals,
                        assists=assists,
                        rating=min(9.0, 6.0 + goals * 0.1 + assists * 0.05),
                    ))
                break


def _fuzzy_match(query: str, candidate: str) -> bool:
    """Basic fuzzy matching for team names."""
    aliases = {
        "man utd": "manchester united",
        "man united": "manchester united",
        "man city": "manchester city",
        "spurs": "tottenham",
        "wolves": "wolverhampton",
        "villa": "aston villa",
        "barca": "barcelona",
        "atletico": "atletico madrid",
        "atleti": "atletico madrid",
        "real": "real madrid",
        "bayern": "bayern munich",
        "bayern munchen": "bayern munich",
        "dortmund": "borussia dortmund",
        "bvb": "borussia dortmund",
        "psg": "paris saint-germain",
        "paris": "paris saint-germain",
        "inter": "inter milan",
        "ac milan": "ac milan",
        "juve": "juventus",
        "napoli": "ssc napoli",
        "lyon": "olympique lyonnais",
        "marseille": "olympique marseille",
        "leeds": "leeds united",
        "newcastle": "newcastle united",
        "west ham": "west ham united",
        "forest": "nottingham forest",
        "nott forest": "nottingham forest",
        "palace": "crystal palace",
        "brighton": "brighton and hove albion",
        "leicester": "leicester city",
        "ipswich": "ipswich town",
        "southampton": "southampton fc",
        "everton": "everton fc",
        "fulham": "fulham fc",
        "bournemouth": "afc bournemouth",
        "brentford": "brentford fc",
    }

    q = aliases.get(query, query)
    c = candidate.lower()

    if q in c or c in q:
        return True

    q_words = q.split()
    return all(w in c for w in q_words)
