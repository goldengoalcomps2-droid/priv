"""
Live data fetcher using free football APIs.
Uses football-data.org (free tier) and web scraping for stats.
"""

import json
import os
import re
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

# Competition IDs on football-data.org
COMPETITION_IDS = {
    Competition.PREMIER_LEAGUE: "PL",
    Competition.LA_LIGA: "PD",
    Competition.BUNDESLIGA: "BL1",
    Competition.SERIE_A: "SA",
    Competition.LIGUE_1: "FL1",
    Competition.CHAMPIONSHIP: "ELC",
    Competition.CHAMPIONS_LEAGUE: "CL",
}


def _api_get(endpoint: str, api_key: str) -> dict:
    """Make a request to football-data.org API."""
    url = f"{API_BASE}{endpoint}"
    req = urllib.request.Request(url)
    req.add_header("X-Auth-Token", api_key)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  API error {e.code}: {e.reason}")
        return {}
    except Exception as e:
        print(f"  Request failed: {e}")
        return {}


def fetch_standings(competition: Competition, api_key: str) -> dict[str, dict]:
    """Fetch league standings and return team stats keyed by team name."""
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


def fetch_team_matches(team_id: int, api_key: str, limit: int = 20) -> list[dict]:
    """Fetch recent matches for a team."""
    data = _api_get(f"/teams/{team_id}/matches?status=FINISHED&limit={limit}", api_key)
    if not data or "matches" not in data:
        return []
    return data["matches"]


def fetch_scorers(competition: Competition, api_key: str, limit: int = 20) -> list[dict]:
    """Fetch top scorers for a competition."""
    comp_id = COMPETITION_IDS.get(competition)
    if not comp_id:
        return []

    data = _api_get(f"/competitions/{comp_id}/scorers?limit={limit}", api_key)
    if not data or "scorers" not in data:
        return []
    return data["scorers"]


def search_team_id(team_name: str, api_key: str) -> Optional[int]:
    """Search for a team ID by name."""
    # Try direct search first
    data = _api_get(f"/teams?name={urllib.parse.quote(team_name)}", api_key)
    if data and "teams" in data and data["teams"]:
        return data["teams"][0]["id"]
    return None


def build_team_season_from_api(
    team_name: str,
    competition: Competition,
    api_key: str,
) -> Optional[TeamSeason]:
    """Build a TeamSeason from live API data."""
    standings = fetch_standings(competition, api_key)
    if not standings:
        return None

    # Fuzzy match team name
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

    team = TeamSeason(
        name=matched_name or team_name,
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
    return team


def _fuzzy_match(query: str, candidate: str) -> bool:
    """Basic fuzzy matching for team names."""
    # Handle common abbreviations
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

    # Check if all words in query appear in candidate
    q_words = q.split()
    return all(w in c for w in q_words)


import urllib.parse
