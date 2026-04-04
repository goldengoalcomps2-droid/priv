"""
Core prediction engine.
Analyzes team data and match context to produce probability-based predictions.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from .data import MatchContext, TeamSeason, Competition


@dataclass
class Prediction:
    question: str
    answer: str
    probability: float  # 0-100
    confidence: str  # Low / Medium / High
    reasoning: list[str]

    def display(self) -> str:
        bar_len = 30
        filled = int(self.probability / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        lines = [
            f"\n{'='*60}",
            f"  PREDICTION: {self.question}",
            f"{'='*60}",
            f"",
            f"  Answer: {self.answer}",
            f"  Probability: {self.probability:.1f}%  [{bar}]",
            f"  Confidence: {self.confidence}",
            f"",
            f"  Reasoning:",
        ]
        for r in self.reasoning:
            lines.append(f"    • {r}")
        lines.append(f"{'='*60}\n")
        return "\n".join(lines)


class FootballPredictor:
    """Main prediction engine using statistical analysis."""

    def predict_first_half_goal(self, ctx: MatchContext) -> Prediction:
        """Will there be a goal in the first half?"""
        reasons = []
        prob = 50.0  # base

        home = ctx.home_team
        away = ctx.away_team
        games_h = max(home.games_played, 1)
        games_a = max(away.games_played, 1)

        # 1. First-half goal rates
        h_1h_scored = home.half_stats.avg_first_half_scored(games_h)
        h_1h_conceded = home.half_stats.avg_first_half_conceded(games_h)
        a_1h_scored = away.half_stats.avg_first_half_scored(games_a)
        a_1h_conceded = away.half_stats.avg_first_half_conceded(games_a)

        avg_1h_goals = (h_1h_scored + a_1h_scored + h_1h_conceded + a_1h_conceded) / 2
        if avg_1h_goals > 1.2:
            prob += 15
            reasons.append(f"High avg 1st-half goals in these teams' games ({avg_1h_goals:.2f} combined)")
        elif avg_1h_goals > 0.8:
            prob += 8
            reasons.append(f"Decent 1st-half goal rate ({avg_1h_goals:.2f} combined)")
        elif avg_1h_goals < 0.5:
            prob -= 12
            reasons.append(f"Low 1st-half goal rate ({avg_1h_goals:.2f} combined)")

        # 2. Overall scoring rates
        combined_gpg = home.goals_per_game + away.goals_per_game
        if combined_gpg > 3.5:
            prob += 10
            reasons.append(f"Both teams score freely ({combined_gpg:.2f} combined goals/game)")
        elif combined_gpg < 2.0:
            prob -= 8
            reasons.append(f"Low-scoring teams ({combined_gpg:.2f} combined goals/game)")

        # 3. Defensive weakness
        combined_conceded = home.goals_conceded_per_game + away.goals_conceded_per_game
        if combined_conceded > 3.0:
            prob += 8
            reasons.append(f"Both defences leak goals ({combined_conceded:.2f} conceded/game combined)")

        # 4. Form
        home_form = home.form.form_rating
        away_form = away.form.form_rating
        if home_form > 70 or away_form > 70:
            prob += 5
            reasons.append(f"At least one team in strong form (H:{home_form:.0f}, A:{away_form:.0f})")

        # 5. Cup match urgency
        if ctx.is_knockout:
            prob += 3
            reasons.append("Knockout match — teams may be more attacking early")

        # 6. xG if available
        if home.xg_per_game > 0 and away.xg_per_game > 0:
            combined_xg = home.xg_per_game + away.xg_per_game
            if combined_xg > 3.0:
                prob += 7
                reasons.append(f"High combined xG ({combined_xg:.2f}/game)")

        prob = max(5, min(95, prob))
        return self._build_prediction(
            "Will there be a goal in the first half?", prob, reasons
        )

    def predict_second_half_goal(self, ctx: MatchContext) -> Prediction:
        """Will there be a goal in the second half?"""
        reasons = []
        prob = 55.0  # 2nd halves historically have more goals

        home = ctx.home_team
        away = ctx.away_team
        games_h = max(home.games_played, 1)
        games_a = max(away.games_played, 1)

        # 1. Second-half goal rates
        h_2h_scored = home.half_stats.avg_second_half_scored(games_h)
        a_2h_scored = away.half_stats.avg_second_half_scored(games_a)
        h_2h_conceded = home.half_stats.avg_second_half_conceded(games_h)
        a_2h_conceded = away.half_stats.avg_second_half_conceded(games_a)

        avg_2h_goals = (h_2h_scored + a_2h_scored + h_2h_conceded + a_2h_conceded) / 2
        if avg_2h_goals > 1.5:
            prob += 15
            reasons.append(f"High avg 2nd-half goals ({avg_2h_goals:.2f} combined)")
        elif avg_2h_goals > 1.0:
            prob += 8
            reasons.append(f"Decent 2nd-half goal rate ({avg_2h_goals:.2f} combined)")
        elif avg_2h_goals < 0.6:
            prob -= 10
            reasons.append(f"Low 2nd-half goal rate ({avg_2h_goals:.2f} combined)")

        # 2. Live adjustments
        if ctx.is_live:
            if ctx.total_goals == 0 and ctx.current_minute >= 45:
                prob += 10
                reasons.append("0-0 at half time — subs and tactical changes increase 2nd half goal chance")
                if ctx.home_shots_on_target + ctx.away_shots_on_target > 6:
                    prob += 8
                    reasons.append(f"Many shots on target already ({ctx.home_shots_on_target + ctx.away_shots_on_target}) — goals likely coming")
                if ctx.home_xg + ctx.away_xg > 1.5:
                    prob += 7
                    reasons.append(f"High xG ({ctx.home_xg + ctx.away_xg:.2f}) despite 0-0 — overperforming defensively, unlikely to last")

            if ctx.home_red_cards > 0 or ctx.away_red_cards > 0:
                prob += 8
                reasons.append("Red card — numerical advantage increases goal probability")

        # 3. Fatigue
        home_fatigue = home.fatigue_score
        away_fatigue = away.fatigue_score
        if home_fatigue > 60 or away_fatigue > 60:
            prob += 5
            reasons.append(f"Fatigue factor (H:{home_fatigue:.0f}, A:{away_fatigue:.0f}) — tired legs concede late")

        # 4. Scoring rates
        combined_gpg = home.goals_per_game + away.goals_per_game
        if combined_gpg > 3.5:
            prob += 8
            reasons.append(f"High-scoring matchup ({combined_gpg:.2f} combined goals/game)")

        # 5. Pressure
        if home.pressure_score > 70 or away.pressure_score > 70:
            prob += 3
            reasons.append("High pressure on at least one team — urgency drives late goals")

        prob = max(5, min(95, prob))
        return self._build_prediction(
            "Will there be a goal in the second half?", prob, reasons
        )

    def predict_btts(self, ctx: MatchContext) -> Prediction:
        """Both teams to score."""
        reasons = []
        prob = 45.0

        home = ctx.home_team
        away = ctx.away_team

        # Scoring rates
        home_scoring_pct = home.scoring_rate
        away_scoring_pct = away.scoring_rate
        prob += (home_scoring_pct - 70) * 0.2
        prob += (away_scoring_pct - 70) * 0.2
        reasons.append(f"{home.name} scores in {home_scoring_pct:.0f}% of games")
        reasons.append(f"{away.name} scores in {away_scoring_pct:.0f}% of games")

        # Clean sheet rates — low CS = more likely BTTS
        if home.clean_sheet_pct < 20:
            prob += 10
            reasons.append(f"{home.name} keeps few clean sheets ({home.clean_sheet_pct:.0f}%)")
        if away.clean_sheet_pct < 20:
            prob += 10
            reasons.append(f"{away.name} keeps few clean sheets ({away.clean_sheet_pct:.0f}%)")

        # High clean sheet rate suppresses BTTS
        if home.clean_sheet_pct > 40:
            prob -= 10
            reasons.append(f"{home.name} strong defensively ({home.clean_sheet_pct:.0f}% clean sheets)")
        if away.clean_sheet_pct > 40:
            prob -= 10
            reasons.append(f"{away.name} strong defensively ({away.clean_sheet_pct:.0f}% clean sheets)")

        # Form
        if home.form.form_rating > 65 and away.form.form_rating > 65:
            prob += 5
            reasons.append("Both teams in good form — likely to create chances")

        # Live
        if ctx.is_live and ctx.current_minute >= 45:
            if ctx.home_goals > 0 and ctx.away_goals > 0:
                prob = 99
                reasons.append("Both teams have already scored")
            elif ctx.home_goals > 0 and ctx.away_goals == 0:
                prob += 10
                reasons.append(f"{away.name} chasing the game — will push forward")
            elif ctx.away_goals > 0 and ctx.home_goals == 0:
                prob += 10
                reasons.append(f"{home.name} chasing at home — crowd factor")

        prob = max(5, min(95, prob))
        return self._build_prediction("Both teams to score?", prob, reasons)

    def predict_over_under(self, ctx: MatchContext, line: float = 2.5) -> Prediction:
        """Over/under a goal line (default 2.5)."""
        reasons = []
        prob = 50.0

        home = ctx.home_team
        away = ctx.away_team
        combined_gpg = home.goals_per_game + away.goals_per_game
        combined_conceded = home.goals_conceded_per_game + away.goals_conceded_per_game
        expected_goals = (combined_gpg + combined_conceded) / 2

        if expected_goals > line + 0.5:
            prob += 20
            reasons.append(f"Expected goals ({expected_goals:.2f}) well above {line} line")
        elif expected_goals > line:
            prob += 10
            reasons.append(f"Expected goals ({expected_goals:.2f}) above {line} line")
        elif expected_goals < line - 0.5:
            prob -= 15
            reasons.append(f"Expected goals ({expected_goals:.2f}) below {line} line")
        else:
            reasons.append(f"Expected goals ({expected_goals:.2f}) close to {line} line")

        # Form influence
        if home.form.form_rating > 70:
            prob += 3
            reasons.append(f"{home.name} in strong form — more attacking")
        if away.form.form_rating > 70:
            prob += 3

        # Defensive weaknesses
        if home.goals_conceded_per_game > 1.5:
            prob += 5
            reasons.append(f"{home.name} concedes {home.goals_conceded_per_game:.2f}/game")
        if away.goals_conceded_per_game > 1.5:
            prob += 5
            reasons.append(f"{away.name} concedes {away.goals_conceded_per_game:.2f}/game")

        # Live
        if ctx.is_live:
            remaining_mins = 90 - ctx.current_minute
            goals_needed = line + 1 - ctx.total_goals
            if goals_needed <= 0:
                prob = 98
                reasons.append(f"Already over {line} with {remaining_mins} mins left")
            else:
                rate = expected_goals / 90
                expected_remaining = rate * remaining_mins
                if expected_remaining > goals_needed:
                    prob += 15
                    reasons.append(f"Projected ~{expected_remaining:.1f} more goals in {remaining_mins} mins")
                else:
                    prob -= 10
                    reasons.append(f"Only ~{expected_remaining:.1f} goals expected in {remaining_mins} mins")

        prob = max(5, min(95, prob))
        return self._build_prediction(f"Over {line} goals?", prob, reasons)

    def predict_match_result(self, ctx: MatchContext) -> Prediction:
        """Predict match winner (home/draw/away)."""
        reasons = []

        home = ctx.home_team
        away = ctx.away_team

        # Start with base home advantage
        home_prob = 42.0
        draw_prob = 28.0
        away_prob = 30.0

        # League position gap
        pos_diff = away.league_position - home.league_position
        adjustment = pos_diff * 0.8
        home_prob += adjustment
        away_prob -= adjustment
        if abs(pos_diff) > 5:
            reasons.append(
                f"League position gap: {home.name} {home.league_position}th vs "
                f"{away.name} {away.league_position}th"
            )

        # Form
        form_diff = home.form.form_rating - away.form.form_rating
        home_prob += form_diff * 0.15
        away_prob -= form_diff * 0.15
        reasons.append(f"Form: {home.name} {home.form.form_rating:.0f} vs {away.name} {away.form.form_rating:.0f}")

        # Goal difference quality
        if home.games_played > 0 and away.games_played > 0:
            h_gd_pg = home.goal_difference / home.games_played
            a_gd_pg = away.goal_difference / away.games_played
            gd_diff = h_gd_pg - a_gd_pg
            home_prob += gd_diff * 5
            away_prob -= gd_diff * 5

        # Points per game
        ppg_diff = home.points_per_game - away.points_per_game
        home_prob += ppg_diff * 6
        away_prob -= ppg_diff * 6
        reasons.append(
            f"Points/game: {home.name} {home.points_per_game:.2f} vs "
            f"{away.name} {away.points_per_game:.2f}"
        )

        # Injuries
        home_injuries = len(home.key_injuries)
        away_injuries = len(away.key_injuries)
        if home_injuries > away_injuries + 2:
            home_prob -= 5
            reasons.append(f"{home.name} has {home_injuries} injuries")
        if away_injuries > home_injuries + 2:
            away_prob -= 5
            reasons.append(f"{away.name} has {away_injuries} injuries")

        # Fatigue
        fatigue_diff = away.fatigue_score - home.fatigue_score
        if abs(fatigue_diff) > 20:
            home_prob += fatigue_diff * 0.15
            away_prob -= fatigue_diff * 0.15
            reasons.append(
                f"Fatigue: {home.name} {home.fatigue_score:.0f} vs "
                f"{away.name} {away.fatigue_score:.0f}"
            )

        # Monthly performance
        month = ctx.match_date.month
        h_month = home.month_performance(month)
        a_month = away.month_performance(month)
        if h_month and h_month.games >= 3:
            if h_month.points_per_game > 2.2:
                home_prob += 4
                reasons.append(f"{home.name} historically strong this month ({h_month.points_per_game:.1f} ppg)")
            elif h_month.points_per_game < 1.0:
                home_prob -= 4
                reasons.append(f"{home.name} historically poor this month ({h_month.points_per_game:.1f} ppg)")
        if a_month and a_month.games >= 3:
            if a_month.points_per_game > 2.2:
                away_prob += 4
            elif a_month.points_per_game < 1.0:
                away_prob -= 4

        # Normalize
        total = home_prob + draw_prob + away_prob
        home_prob = max(3, (home_prob / total) * 100)
        draw_prob = max(3, (draw_prob / total) * 100)
        away_prob = max(3, (away_prob / total) * 100)

        # Re-normalize after clamping
        total = home_prob + draw_prob + away_prob
        home_prob = (home_prob / total) * 100
        draw_prob = (draw_prob / total) * 100
        away_prob = (away_prob / total) * 100

        # Determine prediction
        if home_prob > away_prob and home_prob > draw_prob:
            answer = f"{home.name} WIN"
            top_prob = home_prob
        elif away_prob > home_prob and away_prob > draw_prob:
            answer = f"{away.name} WIN"
            top_prob = away_prob
        else:
            answer = "DRAW"
            top_prob = draw_prob

        reasons.insert(0, f"Home {home_prob:.1f}% | Draw {draw_prob:.1f}% | Away {away_prob:.1f}%")

        return self._build_prediction(
            f"Match result: {home.name} vs {away.name}?",
            top_prob, reasons
        )

    def predict_next_goal(self, ctx: MatchContext) -> Prediction:
        """During a live match, who scores next?"""
        if not ctx.is_live:
            return self._build_prediction("Who scores next?", 50,
                                          ["Match not live — provide live data for in-game predictions"])

        reasons = []
        home = ctx.home_team
        away = ctx.away_team

        # Base on current match stats
        home_prob = 45.0
        away_prob = 35.0
        no_goal_prob = 20.0

        # Possession dominance
        if ctx.home_possession > 60:
            home_prob += 10
            reasons.append(f"{home.name} dominating possession ({ctx.home_possession:.0f}%)")
        elif ctx.away_possession > 60:
            away_prob += 10
            reasons.append(f"{away.name} dominating possession ({ctx.away_possession:.0f}%)")

        # Shots on target
        sot_diff = ctx.home_shots_on_target - ctx.away_shots_on_target
        home_prob += sot_diff * 3
        away_prob -= sot_diff * 3
        reasons.append(f"Shots on target: {home.name} {ctx.home_shots_on_target} vs {away.name} {ctx.away_shots_on_target}")

        # xG
        if ctx.home_xg > 0 or ctx.away_xg > 0:
            xg_diff = ctx.home_xg - ctx.away_xg
            home_prob += xg_diff * 8
            away_prob -= xg_diff * 8
            reasons.append(f"xG: {home.name} {ctx.home_xg:.2f} vs {away.name} {ctx.away_xg:.2f}")

        # Red cards
        if ctx.home_red_cards > ctx.away_red_cards:
            away_prob += 12
            reasons.append(f"{home.name} down to {11 - ctx.home_red_cards} men")
        elif ctx.away_red_cards > ctx.home_red_cards:
            home_prob += 12
            reasons.append(f"{away.name} down to {11 - ctx.away_red_cards} men")

        # Trailing team more likely to push
        if ctx.home_goals < ctx.away_goals:
            home_prob += 5
            reasons.append(f"{home.name} trailing — will push for equaliser")
        elif ctx.away_goals < ctx.home_goals:
            away_prob += 3
            reasons.append(f"{away.name} trailing — may push forward")

        # Late game — less likely to be no more goals
        if ctx.current_minute > 75:
            no_goal_prob += 10
            reasons.append(f"Late in the match ({ctx.current_minute}') — game may be winding down")

        # Normalize
        total = home_prob + away_prob + no_goal_prob
        home_prob = (home_prob / total) * 100
        away_prob = (away_prob / total) * 100
        no_goal_prob = (no_goal_prob / total) * 100

        answer = (f"{home.name} {home_prob:.1f}% | {away.name} {away_prob:.1f}% | "
                  f"No more goals {no_goal_prob:.1f}%")

        return self._build_prediction("Who scores next?", max(home_prob, away_prob), reasons)

    def predict_scoreline(self, ctx: MatchContext) -> Prediction:
        """Predict most likely scoreline."""
        reasons = []
        home = ctx.home_team
        away = ctx.away_team

        # Expected goals for each team
        h_attack = home.goals_per_game
        a_defence = away.goals_conceded_per_game
        a_attack = away.goals_per_game
        h_defence = home.goals_conceded_per_game

        exp_home = (h_attack + a_defence) / 2
        exp_away = (a_attack + h_defence) / 2

        # Home advantage bump
        exp_home *= 1.1
        exp_away *= 0.9

        # Form adjustment
        if home.form.form_rating > 70:
            exp_home *= 1.05
        if away.form.form_rating > 70:
            exp_away *= 1.05
        if home.form.form_rating < 35:
            exp_home *= 0.9
        if away.form.form_rating < 35:
            exp_away *= 0.9

        # Head-to-head adjustment
        h2h = home.head_to_head.get(away.name)
        if h2h and h2h.games >= 3:
            h2h_avg = h2h.avg_goals_per_game
            reasons.append(f"H2H: {h2h.wins}W {h2h.draws}D {h2h.losses}L in last {h2h.games} meetings")
            if h2h.last_scores:
                reasons.append(f"Recent scores: {', '.join(h2h.last_scores[:5])}")

        # Round to nearest likely scoreline
        h_goals = round(exp_home)
        a_goals = round(exp_away)

        # Generate top 5 scorelines with rough probabilities using Poisson-like logic
        import math
        def poisson_prob(lam: float, k: int) -> float:
            return (lam ** k) * math.exp(-lam) / math.factorial(k)

        scorelines = []
        for hg in range(5):
            for ag in range(5):
                p = poisson_prob(exp_home, hg) * poisson_prob(exp_away, ag) * 100
                scorelines.append((hg, ag, p))

        scorelines.sort(key=lambda x: -x[2])
        top5 = scorelines[:5]

        reasons.append(f"Expected goals: {home.name} {exp_home:.2f}, {away.name} {exp_away:.2f}")
        answer_parts = []
        for hg, ag, p in top5:
            answer_parts.append(f"{hg}-{ag} ({p:.1f}%)")

        answer = " | ".join(answer_parts)
        best = top5[0]
        prob = best[2]

        reasons.append(f"Most likely: {best[0]}-{best[1]}")

        return self._build_prediction(
            f"Predicted scoreline: {home.name} vs {away.name}",
            prob, reasons
        )

    def predict_over_under_half(self, ctx: MatchContext, half: int, line: float) -> Prediction:
        """Over/under for a specific half. half=1 for first, half=2 for second."""
        reasons = []
        home = ctx.home_team
        away = ctx.away_team
        games_h = max(home.games_played, 1)
        games_a = max(away.games_played, 1)

        half_name = "1st half" if half == 1 else "2nd half"

        if half == 1:
            h_scored = home.half_stats.avg_first_half_scored(games_h)
            h_conceded = home.half_stats.avg_first_half_conceded(games_h)
            a_scored = away.half_stats.avg_first_half_scored(games_a)
            a_conceded = away.half_stats.avg_first_half_conceded(games_a)
        else:
            h_scored = home.half_stats.avg_second_half_scored(games_h)
            h_conceded = home.half_stats.avg_second_half_conceded(games_h)
            a_scored = away.half_stats.avg_second_half_scored(games_a)
            a_conceded = away.half_stats.avg_second_half_conceded(games_a)

        expected_half_goals = (h_scored + a_scored + h_conceded + a_conceded) / 2
        reasons.append(f"Expected {half_name} goals: {expected_half_goals:.2f}")

        prob = 50.0
        if expected_half_goals > line + 0.5:
            prob += 20
            reasons.append(f"Expected goals well above {line} line")
        elif expected_half_goals > line:
            prob += 10
            reasons.append(f"Expected goals above {line} line")
        elif expected_half_goals < line - 0.3:
            prob -= 15
            reasons.append(f"Expected goals below {line} line")

        # Historical over rates
        if half == 1:
            if line == 1.5 and home.games_over_1_5_fh > 0:
                rate = home.games_over_1_5_fh / games_h * 100
                prob += (rate - 50) * 0.2
                reasons.append(f"{home.name}: over 1.5 FH in {rate:.0f}% of games")
            if line == 2.5 and home.games_over_2_5_fh > 0:
                rate = home.games_over_2_5_fh / games_h * 100
                prob += (rate - 30) * 0.2
                reasons.append(f"{home.name}: over 2.5 FH in {rate:.0f}% of games")
        else:
            if line == 1.5 and home.games_over_1_5_sh > 0:
                rate = home.games_over_1_5_sh / games_h * 100
                prob += (rate - 50) * 0.2
                reasons.append(f"{home.name}: over 1.5 SH in {rate:.0f}% of games")
            if line == 2.5 and home.games_over_2_5_sh > 0:
                rate = home.games_over_2_5_sh / games_h * 100
                prob += (rate - 30) * 0.2
                reasons.append(f"{home.name}: over 2.5 SH in {rate:.0f}% of games")

        # Form boost
        combined_gpg = home.goals_per_game + away.goals_per_game
        if combined_gpg > 3.5:
            prob += 8
            reasons.append(f"High-scoring matchup ({combined_gpg:.2f} total goals/game)")

        # Defensive weakness
        if home.goals_conceded_per_game > 1.5 or away.goals_conceded_per_game > 1.5:
            prob += 5
            reasons.append("At least one defence is leaky")

        # Live adjustments
        if ctx.is_live:
            if half == 1 and ctx.current_minute < 45:
                fh_goals = ctx.home_first_half_goals + ctx.away_first_half_goals
                if fh_goals > line:
                    prob = 98
                    reasons.append(f"Already over {line} in {half_name}")
                else:
                    remaining = 45 - ctx.current_minute
                    rate_per_min = expected_half_goals / 45
                    projected = fh_goals + rate_per_min * remaining
                    if projected > line + 0.5:
                        prob += 12
                    reasons.append(f"Current: {fh_goals} goals, ~{remaining} mins left in half")
            elif half == 2 and ctx.current_minute >= 45:
                sh_goals = ctx.second_half_goals
                if sh_goals > line:
                    prob = 98
                    reasons.append(f"Already over {line} in {half_name}")
                else:
                    remaining = 90 - ctx.current_minute
                    rate_per_min = expected_half_goals / 45
                    projected = sh_goals + rate_per_min * remaining
                    reasons.append(f"Current 2H goals: {sh_goals}, ~{remaining} mins left")

        prob = max(3, min(97, prob))
        return self._build_prediction(f"Over {line} goals in {half_name}?", prob, reasons)

    def predict_corners(self, ctx: MatchContext, line: float = 9.5) -> Prediction:
        """Predict over/under corners."""
        reasons = []
        home = ctx.home_team
        away = ctx.away_team

        expected_corners = (
            home.corners_per_game + away.corners_per_game +
            home.corners_conceded_per_game + away.corners_conceded_per_game
        ) / 2
        reasons.append(f"Expected total corners: {expected_corners:.1f}")

        prob = 50.0
        if expected_corners > line + 1:
            prob += 20
            reasons.append(f"Well above {line} line")
        elif expected_corners > line:
            prob += 10
            reasons.append(f"Above {line} line")
        elif expected_corners < line - 1:
            prob -= 15
            reasons.append(f"Below {line} line")

        # Possession-dominant teams force more corners
        if home.possession_avg > 58 or away.possession_avg > 58:
            prob += 5
            dominant = home.name if home.possession_avg > away.possession_avg else away.name
            reasons.append(f"{dominant} dominates possession — forces corners")

        # High-pressing teams create more corner situations
        combined_shots = home.shots_per_game + away.shots_per_game
        if combined_shots > 28:
            prob += 7
            reasons.append(f"High combined shots ({combined_shots:.1f}/game) — more corners likely")
        elif combined_shots < 20:
            prob -= 5
            reasons.append(f"Low shot volume ({combined_shots:.1f}/game)")

        # Quality gap = more corners for dominant team
        pos_gap = abs(home.league_position - away.league_position)
        if pos_gap > 8:
            prob += 5
            reasons.append(f"Big quality gap (positions: {home.league_position} vs {away.league_position}) — one team will dominate")

        # Live
        if ctx.is_live:
            remaining = 90 - ctx.current_minute
            current = ctx.total_corners
            rate = expected_corners / 90
            projected = current + rate * remaining
            if current > line:
                prob = 98
                reasons.append(f"Already {current} corners with {remaining} mins left")
            else:
                needed = line + 1 - current
                reasons.append(f"Current: {current} corners, projected: {projected:.1f}")
                if projected > line + 1:
                    prob += 15
                elif projected < line:
                    prob -= 10

        prob = max(3, min(97, prob))
        return self._build_prediction(f"Over {line} corners?", prob, reasons)

    def predict_clean_sheet(self, ctx: MatchContext, team_name: str) -> Prediction:
        """Will a specific team keep a clean sheet?"""
        reasons = []

        if team_name.lower() in ctx.home_team.name.lower():
            defending = ctx.home_team
            attacking = ctx.away_team
        else:
            defending = ctx.away_team
            attacking = ctx.home_team

        prob = defending.clean_sheet_pct
        reasons.append(f"{defending.name} clean sheet rate: {defending.clean_sheet_pct:.0f}%")

        # Opponent scoring ability
        if attacking.scoring_rate > 80:
            prob -= 10
            reasons.append(f"{attacking.name} scores in {attacking.scoring_rate:.0f}% of games")
        elif attacking.scoring_rate < 60:
            prob += 10
            reasons.append(f"{attacking.name} struggles to score (scores in {attacking.scoring_rate:.0f}%)")

        # Form
        if defending.form.form_rating > 70:
            prob += 5
            reasons.append(f"{defending.name} in strong form")
        if attacking.form.form_rating > 70:
            prob -= 5
            reasons.append(f"{attacking.name} in strong form")

        # Live
        if ctx.is_live:
            if (team_name.lower() in ctx.home_team.name.lower() and ctx.away_goals > 0) or \
               (team_name.lower() in ctx.away_team.name.lower() and ctx.home_goals > 0):
                prob = 0
                reasons.append("Already conceded")

        prob = max(2, min(95, prob))
        return self._build_prediction(
            f"Will {defending.name} keep a clean sheet?", prob, reasons
        )

    def get_match_analysis(self, ctx: MatchContext) -> str:
        """Full pre-match analysis."""
        home = ctx.home_team
        away = ctx.away_team
        lines = [
            f"\n{'='*60}",
            f"  MATCH ANALYSIS: {home.name} vs {away.name}",
            f"  {ctx.competition.value}",
            f"{'='*60}\n",
            f"  --- {home.name} ---",
            f"  Position: {home.league_position}  |  Points: {home.points}  |  PPG: {home.points_per_game:.2f}",
            f"  Record: {home.wins}W {home.draws}D {home.losses}L",
            f"  Goals: {home.goals_scored} scored, {home.goals_conceded} conceded (GD: {home.goal_difference:+d})",
            f"  Goals/game: {home.goals_per_game:.2f} scored, {home.goals_conceded_per_game:.2f} conceded",
            f"  Form (last 6): {' '.join(home.form.results[-6:])} ({home.form.form_rating:.0f}/100)",
            f"  Possession: {home.possession_avg:.1f}%",
            f"  Clean sheets: {home.clean_sheets} ({home.clean_sheet_pct:.0f}%)",
            f"  Failed to score: {home.failed_to_score} games",
            f"  Fatigue: {home.fatigue_score:.0f}/100 ({home.games_in_last_n_days(21)} games in 21 days)",
            f"  Pressure: {home.pressure_score:.0f}/100",
        ]

        if home.best_player:
            bp = home.best_player
            lines.append(f"  Best player: {bp.name} ({bp.position}, rating: {bp.rating:.1f}, {bp.goals}G {bp.assists}A)")
        if home.key_injuries:
            inj = ", ".join(f"{p.name} ({p.injury_description})" for p in home.key_injuries)
            lines.append(f"  Injuries: {inj}")

        lines += [
            f"",
            f"  --- {away.name} ---",
            f"  Position: {away.league_position}  |  Points: {away.points}  |  PPG: {away.points_per_game:.2f}",
            f"  Record: {away.wins}W {away.draws}D {away.losses}L",
            f"  Goals: {away.goals_scored} scored, {away.goals_conceded} conceded (GD: {away.goal_difference:+d})",
            f"  Goals/game: {away.goals_per_game:.2f} scored, {away.goals_conceded_per_game:.2f} conceded",
            f"  Form (last 6): {' '.join(away.form.results[-6:])} ({away.form.form_rating:.0f}/100)",
            f"  Possession: {away.possession_avg:.1f}%",
            f"  Clean sheets: {away.clean_sheets} ({away.clean_sheet_pct:.0f}%)",
            f"  Failed to score: {away.failed_to_score} games",
            f"  Fatigue: {away.fatigue_score:.0f}/100 ({away.games_in_last_n_days(21)} games in 21 days)",
            f"  Pressure: {away.pressure_score:.0f}/100",
        ]

        if away.best_player:
            bp = away.best_player
            lines.append(f"  Best player: {bp.name} ({bp.position}, rating: {bp.rating:.1f}, {bp.goals}G {bp.assists}A)")
        if away.key_injuries:
            inj = ", ".join(f"{p.name} ({p.injury_description})" for p in away.key_injuries)
            lines.append(f"  Injuries: {inj}")

        # Head-to-head
        h2h = home.head_to_head.get(away.name)
        if h2h and h2h.games > 0:
            lines += [
                f"",
                f"  --- Head to Head ---",
                f"  Meetings: {h2h.games}  ({h2h.wins}W {h2h.draws}D {h2h.losses}L for {home.name})",
                f"  Avg goals/game: {h2h.avg_goals_per_game:.1f}",
            ]
            if h2h.last_scores:
                lines.append(f"  Recent scores: {', '.join(h2h.last_scores[:5])}")

        # Lineups if available
        if home.lineup:
            lines += [f"", f"  --- {home.name} Lineup ---"]
            for p in home.lineup:
                status = " (INJ)" if p.injured else ""
                lines.append(f"  {p.position}: {p.name} ({p.goals}G {p.assists}A){status}")
        if away.lineup:
            lines += [f"", f"  --- {away.name} Lineup ---"]
            for p in away.lineup:
                status = " (INJ)" if p.injured else ""
                lines.append(f"  {p.position}: {p.name} ({p.goals}G {p.assists}A){status}")

        lines.append("")
        return "\n".join(lines)

    def _build_prediction(self, question: str, prob: float, reasons: list[str]) -> Prediction:
        prob = max(2, min(98, prob))
        if prob >= 75:
            confidence = "HIGH"
            answer = "YES — very likely" if "?" in question else "Strong lean"
        elif prob >= 55:
            confidence = "MEDIUM"
            answer = "YES — more likely than not" if "?" in question else "Slight lean"
        elif prob >= 40:
            confidence = "LOW"
            answer = "UNCERTAIN — could go either way"
        else:
            confidence = "MEDIUM"
            answer = "NO — unlikely" if "?" in question else "Against"

        return Prediction(
            question=question,
            answer=answer,
            probability=prob,
            confidence=confidence,
            reasoning=reasons,
        )
