"""
Interactive CLI for the football prediction bot.
Supports pre-match and live in-game predictions.
"""

import os
import re
import sys
from datetime import date
from typing import Optional

from .data import Competition, MatchContext, TeamSeason, HalfStats, TeamForm, PlayerInfo
from .predictor import FootballPredictor
from .sample_data import get_sample_teams
from .scraper import (
    build_team_season_from_api, fetch_standings, load_all_leagues,
    enrich_team_with_matches, enrich_league_with_scorers, COMPETITION_IDS,
)


BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ⚽  FOOTBALL PREDICTION BOT  ⚽                          ║
║                                                              ║
║     Covers: Premier League, La Liga, Bundesliga,             ║
║     Serie A, Ligue 1, Championship, Champions League         ║
║     & European Cups                                          ║
║                                                              ║
║     Type 'help' for commands                                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
COMMANDS:
─────────────────────────────────────────────────────────────
  match <home> vs <away>      Set up a match for predictions
  live                        Switch to live mode (in-game)
  update live                 Update live match stats

PREDICTIONS (after setting a match):
  first half goal?            Will there be a 1st half goal?
  second half goal?           Will there be a 2nd half goal?
  btts                        Both teams to score?
  over 2.5                    Over 2.5 goals?
  over 1.5                    Over 1.5 goals?
  over 3.5                    Over 3.5 goals?
  result                      Predict match winner
  next goal                   Who scores next? (live mode)
  clean sheet <team>          Will team keep a clean sheet?
  analysis                    Full pre-match analysis

TEAM INFO:
  team <name>                 Show team stats
  teams                       List all available teams

DATA:
  refresh                     Re-fetch all league data from API
  add team                    Add/update a team manually

GENERAL:
  help                        Show this help
  quit / exit                 Exit the bot
─────────────────────────────────────────────────────────────
"""


class FootballCLI:
    def __init__(self):
        self.predictor = FootballPredictor()
        self.teams = get_sample_teams()
        self.current_match: Optional[MatchContext] = None
        self.api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "")

    def _load_live_data(self):
        """Fetch live data from football-data.org for all supported leagues."""
        print("\n  Fetching live 2025/26 season data from football-data.org...")
        print("  (This takes ~1 min due to API rate limits)\n")
        try:
            live_teams = load_all_leagues(self.api_key, fetch_matches=False)
            if live_teams:
                self.teams.update(live_teams)
                print(f"\n  ✅ Loaded {len(live_teams)} teams with live data!")
                print("  Tip: When you set a match, detailed stats (form, half goals) are fetched automatically.\n")
            else:
                print("  ⚠️  No data returned — using fallback data.\n")
        except Exception as e:
            print(f"  ⚠️  Failed to fetch live data: {e}")
            print("  Using fallback data instead.\n")

    def run(self):
        print(BANNER)

        if self.api_key:
            print("  [API key found — fetching live 2025/26 data]")
            self._load_live_data()
        else:
            print("  [No API key — using built-in fallback data]")
            print("  [For LIVE data, get a FREE key at: https://www.football-data.org/client/register]")
            print("  [Then: export FOOTBALL_DATA_API_KEY=your_key_here]")
        print()

        while True:
            try:
                raw = input("⚽ > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not raw:
                continue

            cmd = raw.lower()

            if cmd in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            elif cmd == "help":
                print(HELP_TEXT)
            elif cmd == "teams":
                self._list_teams()
            elif cmd.startswith("team "):
                self._show_team(raw[5:].strip())
            elif "vs" in cmd and ("match" in cmd or "vs" in cmd):
                self._setup_match(raw)
            elif cmd == "live":
                self._enter_live_mode()
            elif cmd.startswith("update live"):
                self._update_live()
            elif cmd == "refresh":
                self._refresh_data()
            elif cmd == "add team":
                self._add_team_interactive()
            elif self.current_match:
                self._handle_prediction(cmd, raw)
            else:
                print("  No match set. Use 'match <home> vs <away>' first, or type 'help'.")

    def _refresh_data(self):
        if not self.api_key:
            print("  No API key set. Get one free at: https://www.football-data.org/client/register")
            print("  Then: export FOOTBALL_DATA_API_KEY=your_key_here")
            return
        self._load_live_data()

    def _list_teams(self):
        print("\n  Available teams:")
        by_league = {}
        for key, t in sorted(self.teams.items()):
            league = t.competition.value
            by_league.setdefault(league, []).append(t)

        for league, teams in sorted(by_league.items()):
            print(f"\n  {league}:")
            for t in sorted(teams, key=lambda x: x.league_position):
                print(f"    {t.league_position:>2}. {t.name} — {t.points}pts "
                      f"({t.wins}W {t.draws}D {t.losses}L) "
                      f"GD:{t.goal_difference:+d}")
        print()

    def _show_team(self, name: str):
        team = self._find_team(name)
        if not team:
            print(f"  Team '{name}' not found. Type 'teams' to see available teams.")
            return

        t = team
        print(f"\n  {'='*50}")
        print(f"  {t.name} — {t.competition.value}")
        print(f"  {'='*50}")
        print(f"  Position: {t.league_position}  |  Points: {t.points}  |  PPG: {t.points_per_game:.2f}")
        print(f"  Record: {t.wins}W {t.draws}D {t.losses}L ({t.games_played} played)")
        print(f"  Goals: {t.goals_scored} scored ({t.goals_per_game:.2f}/game)")
        print(f"  Goals: {t.goals_conceded} conceded ({t.goals_conceded_per_game:.2f}/game)")
        print(f"  GD: {t.goal_difference:+d}")
        print(f"  1st half goals scored: {t.half_stats.first_half_goals_scored} ({t.half_stats.avg_first_half_scored(t.games_played):.2f}/game)")
        print(f"  2nd half goals scored: {t.half_stats.second_half_goals_scored} ({t.half_stats.avg_second_half_scored(t.games_played):.2f}/game)")
        print(f"  1st half goals conceded: {t.half_stats.first_half_goals_conceded}")
        print(f"  2nd half goals conceded: {t.half_stats.second_half_goals_conceded}")
        print(f"  Clean sheets: {t.clean_sheets} ({t.clean_sheet_pct:.0f}%)")
        print(f"  Failed to score: {t.failed_to_score} games")
        print(f"  Possession: {t.possession_avg:.1f}%")
        if t.xg_per_game > 0:
            print(f"  xG/game: {t.xg_per_game:.2f}  |  xGA/game: {t.xga_per_game:.2f}")
        print(f"  Form: {' '.join(t.form.results[-6:])} (rating: {t.form.form_rating:.0f}/100)")
        print(f"  Fatigue: {t.fatigue_score:.0f}/100 ({t.games_in_last_n_days(21)} games in 21 days)")
        print(f"  Pressure: {t.pressure_score:.0f}/100")

        if t.best_player:
            bp = t.best_player
            print(f"  Best player: {bp.name} ({bp.position}) — {bp.goals}G {bp.assists}A, rating {bp.rating:.1f}")

        if t.key_injuries:
            print(f"  Injuries:")
            for p in t.key_injuries:
                print(f"    ❌ {p.name} ({p.position}) — {p.injury_description}")

        print()

    def _setup_match(self, raw: str):
        # Parse "match X vs Y" or just "X vs Y"
        text = re.sub(r'^match\s+', '', raw, flags=re.IGNORECASE).strip()
        parts = re.split(r'\s+vs?\s+', text, flags=re.IGNORECASE)

        if len(parts) != 2:
            print("  Format: match <home team> vs <away team>")
            return

        home_name, away_name = parts[0].strip(), parts[1].strip()
        home = self._find_team(home_name)
        away = self._find_team(away_name)

        if not home:
            # Try API
            if self.api_key:
                print(f"  Looking up {home_name} via API...")
                for comp in Competition:
                    home = build_team_season_from_api(home_name, comp, self.api_key)
                    if home:
                        self.teams[home_name.lower()] = home
                        break
            if not home:
                print(f"  Team '{home_name}' not found. Use 'add team' or check 'teams' list.")
                return

        if not away:
            if self.api_key:
                print(f"  Looking up {away_name} via API...")
                for comp in Competition:
                    away = build_team_season_from_api(away_name, comp, self.api_key)
                    if away:
                        self.teams[away_name.lower()] = away
                        break
            if not away:
                print(f"  Team '{away_name}' not found. Use 'add team' or check 'teams' list.")
                return

        # Determine competition
        competition = home.competition
        is_cup = False
        is_knockout = False

        # Check if cross-league (likely Champions League)
        if home.competition != away.competition:
            competition = Competition.CHAMPIONS_LEAGUE
            is_cup = True
            print(f"  Cross-league match — treating as {competition.value}")

        # Auto-enrich with match-level data if API available and form is empty
        if self.api_key:
            for team in [home, away]:
                if not team.form.results:
                    print(f"  Fetching detailed stats for {team.name}...")
                    # Find team ID from standings cache
                    standings = fetch_standings(team.competition, self.api_key)
                    for sname, sdata in standings.items():
                        if sname == team.name and "id" in sdata:
                            enrich_team_with_matches(team, self.api_key, sdata["id"])
                            break

        self.current_match = MatchContext(
            home_team=home,
            away_team=away,
            competition=competition,
            match_date=date.today(),
            is_cup_match=is_cup,
            is_knockout=is_knockout,
        )

        print(f"\n  ✅ Match set: {home.name} vs {away.name}")
        print(f"  Competition: {competition.value}")
        if home.form.results:
            print(f"  {home.name} form: {' '.join(home.form.results[-6:])}")
        if away.form.results:
            print(f"  {away.name} form: {' '.join(away.form.results[-6:])}")
        print(f"  Ready for predictions — type a question or 'analysis' for full breakdown.\n")

    def _enter_live_mode(self):
        if not self.current_match:
            print("  Set a match first with 'match <home> vs <away>'")
            return

        self.current_match.is_live = True
        print("\n  🔴 LIVE MODE activated")
        print("  Enter current match state:")
        self._update_live()

    def _update_live(self):
        if not self.current_match:
            print("  Set a match first.")
            return

        ctx = self.current_match
        ctx.is_live = True

        try:
            ctx.current_minute = int(input("  Current minute: ") or "0")
            ctx.home_goals = int(input(f"  {ctx.home_team.name} goals: ") or "0")
            ctx.away_goals = int(input(f"  {ctx.away_team.name} goals: ") or "0")
            ctx.home_possession = float(input(f"  {ctx.home_team.name} possession %: ") or "50")
            ctx.away_possession = 100 - ctx.home_possession
            ctx.home_shots = int(input(f"  {ctx.home_team.name} shots: ") or "0")
            ctx.away_shots = int(input(f"  {ctx.away_team.name} shots: ") or "0")
            ctx.home_shots_on_target = int(input(f"  {ctx.home_team.name} shots on target: ") or "0")
            ctx.away_shots_on_target = int(input(f"  {ctx.away_team.name} shots on target: ") or "0")
            ctx.home_red_cards = int(input(f"  {ctx.home_team.name} red cards: ") or "0")
            ctx.away_red_cards = int(input(f"  {ctx.away_team.name} red cards: ") or "0")

            xg_input = input(f"  {ctx.home_team.name} xG (press enter to skip): ").strip()
            if xg_input:
                ctx.home_xg = float(xg_input)
                ctx.away_xg = float(input(f"  {ctx.away_team.name} xG: ") or "0")

        except ValueError:
            print("  Invalid input — please enter numbers.")
            return

        print(f"\n  🔴 LIVE: {ctx.home_team.name} {ctx.home_goals}-{ctx.away_goals} {ctx.away_team.name} ({ctx.current_minute}')")
        print()

    def _handle_prediction(self, cmd: str, raw: str):
        ctx = self.current_match

        if "first half" in cmd and "goal" in cmd:
            pred = self.predictor.predict_first_half_goal(ctx)
        elif "second half" in cmd and "goal" in cmd or "2nd half" in cmd and "goal" in cmd:
            pred = self.predictor.predict_second_half_goal(ctx)
        elif cmd in ("btts", "both teams to score", "both teams score"):
            pred = self.predictor.predict_btts(ctx)
        elif "over" in cmd:
            # Parse the line (e.g., "over 2.5")
            match = re.search(r'over\s+(\d+\.?\d*)', cmd)
            line = float(match.group(1)) if match else 2.5
            pred = self.predictor.predict_over_under(ctx, line)
        elif cmd in ("result", "winner", "who wins", "match result"):
            pred = self.predictor.predict_match_result(ctx)
        elif "next goal" in cmd or "who scores next" in cmd:
            pred = self.predictor.predict_next_goal(ctx)
        elif "clean sheet" in cmd:
            team_name = re.sub(r'clean\s*sheet\s*', '', cmd).strip()
            if not team_name:
                team_name = ctx.home_team.name
            pred = self.predictor.predict_clean_sheet(ctx, team_name)
        elif cmd in ("analysis", "analyze", "analyse", "full analysis"):
            print(self.predictor.get_match_analysis(ctx))
            return
        elif "goal" in cmd and ("will" in cmd or "?" in cmd):
            # Generic "will there be a goal" — predict for current half
            if ctx.is_live and ctx.current_minute >= 45:
                pred = self.predictor.predict_second_half_goal(ctx)
            else:
                pred = self.predictor.predict_first_half_goal(ctx)
        else:
            print("  Unknown prediction. Type 'help' for available commands.")
            return

        print(pred.display())

    def _find_team(self, name: str) -> Optional[TeamSeason]:
        name_lower = name.lower().strip()

        # Direct key match
        if name_lower in self.teams:
            return self.teams[name_lower]

        # Search by team name
        for key, team in self.teams.items():
            if (name_lower in team.name.lower()
                    or team.name.lower() in name_lower
                    or name_lower in key):
                return team

        # Fuzzy aliases
        aliases = {
            "man utd": "man utd", "man united": "man utd", "manchester united": "man utd",
            "man city": "man city", "manchester city": "man city",
            "spurs": "tottenham", "tottenham hotspur": "tottenham",
            "forest": "nottingham forest", "nott forest": "nottingham forest",
            "villa": "aston villa",
            "barca": "barcelona", "fc barcelona": "barcelona",
            "real": "real madrid",
            "atletico": "atletico madrid", "atleti": "atletico madrid",
            "bayern": "bayern munich", "fcb": "bayern munich",
            "bvb": "dortmund", "borussia dortmund": "dortmund",
            "inter": "inter milan", "internazionale": "inter milan",
            "juve": "juventus",
            "paris": "psg", "paris saint-germain": "psg",
            "leverkusen": "bayer leverkusen",
        }

        mapped = aliases.get(name_lower)
        if mapped and mapped in self.teams:
            return self.teams[mapped]

        return None

    def _add_team_interactive(self):
        print("\n  Add/Update Team")
        print("  ─────────────────")
        try:
            name = input("  Team name: ").strip()
            if not name:
                return

            print("  Competition:")
            comps = list(Competition)
            for i, c in enumerate(comps, 1):
                print(f"    {i}. {c.value}")
            comp_idx = int(input("  Select (number): ") or "1") - 1
            competition = comps[comp_idx]

            gp = int(input("  Games played: ") or "0")
            w = int(input("  Wins: ") or "0")
            d = int(input("  Draws: ") or "0")
            l = int(input("  Losses: ") or "0")
            gs = int(input("  Goals scored: ") or "0")
            gc = int(input("  Goals conceded: ") or "0")
            pos = int(input("  League position: ") or "0")
            pts = int(input("  Points: ") or "0")
            poss = float(input("  Average possession %: ") or "50")

            fh_gs = int(input("  1st half goals scored (total): ") or "0")
            sh_gs = int(input("  2nd half goals scored (total): ") or "0")
            fh_gc = int(input("  1st half goals conceded (total): ") or "0")
            sh_gc = int(input("  2nd half goals conceded (total): ") or "0")

            cs = int(input("  Clean sheets: ") or "0")
            fts = int(input("  Failed to score (games): ") or "0")

            form_str = input("  Last 6 results (e.g., W W D L W W): ").strip()
            form_results = form_str.upper().split() if form_str else []

            team = TeamSeason(
                name=name,
                competition=competition,
                games_played=gp, wins=w, draws=d, losses=l,
                goals_scored=gs, goals_conceded=gc,
                league_position=pos, points=pts,
                possession_avg=poss,
                clean_sheets=cs, failed_to_score=fts,
                half_stats=HalfStats(
                    first_half_goals_scored=fh_gs,
                    second_half_goals_scored=sh_gs,
                    first_half_goals_conceded=fh_gc,
                    second_half_goals_conceded=sh_gc,
                ),
                form=TeamForm(results=form_results),
            )

            self.teams[name.lower()] = team
            print(f"\n  ✅ {name} added/updated!\n")

        except (ValueError, IndexError):
            print("  Invalid input. Try again.")


def main():
    cli = FootballCLI()
    cli.run()


if __name__ == "__main__":
    main()
