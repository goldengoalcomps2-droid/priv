"""
Web interface for the football prediction bot.
Opens in your browser — no terminal needed.
Run: python3.12 -m football_predictor.web
"""

import json
import os
import re
import ssl
import webbrowser
from datetime import date
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import parse_qs, urlparse

from .data import Competition, MatchContext, TeamSeason, HalfStats, TeamForm
from .predictor import FootballPredictor
from .sample_data import get_sample_teams
from .scraper import (
    build_team_season_from_api, fetch_standings, load_all_leagues,
    enrich_team_with_matches, COMPETITION_IDS,
)

# Global state
predictor = FootballPredictor()
teams: dict[str, TeamSeason] = {}
current_match: Optional[MatchContext] = None
api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "")


def find_team(name: str) -> Optional[TeamSeason]:
    name_lower = name.lower().strip()
    if name_lower in teams:
        return teams[name_lower]
    for key, team in teams.items():
        if (name_lower in team.name.lower()
                or team.name.lower() in name_lower
                or name_lower in key):
            return team
    aliases = {
        "man utd": "manchester united", "man united": "manchester united",
        "man city": "manchester city", "spurs": "tottenham hotspur",
        "tottenham": "tottenham hotspur", "forest": "nottingham forest",
        "villa": "aston villa", "barca": "fc barcelona", "barcelona": "fc barcelona",
        "real": "real madrid", "atletico": "atletico madrid",
        "bayern": "bayern munich", "bvb": "borussia dortmund",
        "dortmund": "borussia dortmund", "inter": "inter milan",
        "juve": "juventus", "psg": "paris saint-germain",
        "paris": "paris saint-germain", "leverkusen": "bayer leverkusen",
        "newcastle": "newcastle united", "west ham": "west ham united",
        "wolves": "wolverhampton wanderers", "palace": "crystal palace",
        "brighton": "brighton and hove albion",
    }
    mapped = aliases.get(name_lower, name_lower)
    for key, team in teams.items():
        if mapped in team.name.lower() or mapped in key:
            return team
    return None


def handle_message(text: str) -> str:
    global current_match
    cmd = text.lower().strip()

    if not cmd:
        return "Type a question or 'help' for commands."

    if cmd == "help":
        return (
            "<b>Set up a match:</b><br>"
            "Type: <code>Liverpool vs Arsenal</code><br><br>"
            "<b>Pre-match predictions:</b><br>"
            "• <code>result</code> — who wins?<br>"
            "• <code>scoreline</code> — predicted score<br>"
            "• <code>btts</code> — both teams to score<br>"
            "• <code>over 2.5</code> / <code>over 1.5</code> / <code>over 3.5</code> — total goals<br>"
            "• <code>over 1.5 first half</code> — 1st half goals<br>"
            "• <code>over 2.5 first half</code> — 1st half goals<br>"
            "• <code>over 1.5 second half</code> — 2nd half goals<br>"
            "• <code>over 2.5 second half</code> — 2nd half goals<br>"
            "• <code>corners</code> — over 9.5 corners<br>"
            "• <code>over 10.5 corners</code> — custom corner line<br>"
            "• <code>first half goal?</code> — goal in 1st half<br>"
            "• <code>second half goal?</code> — goal in 2nd half<br>"
            "• <code>clean sheet Liverpool</code><br>"
            "• <code>analysis</code> — full breakdown with H2H<br><br>"
            "<b>Live mode:</b><br>"
            "• <code>live 45 1-0 55% 4sot 2sot 5cor 3cor</code><br>"
            "• <code>next goal</code> — who scores next?<br><br>"
            "<b>Lineups:</b><br>"
            "• <code>lineup home Salah, Van Dijk, Mac Allister</code><br>"
            "• <code>lineup away Saka, Rice, Havertz</code><br><br>"
            "<b>Head-to-head:</b><br>"
            "• <code>h2h 3W 1D 1L 2-1 0-0 3-2</code><br><br>"
            "<b>Other:</b><br>"
            "• <code>teams</code> — list all teams<br>"
            "• <code>team Liverpool</code> — show team stats<br>"
        )

    if cmd == "teams":
        by_league: dict[str, list[TeamSeason]] = {}
        for t in teams.values():
            by_league.setdefault(t.competition.value, []).append(t)
        html = ""
        for league in sorted(by_league):
            html += f"<b>{league}</b><br>"
            for t in sorted(by_league[league], key=lambda x: x.league_position):
                html += (f"&nbsp;&nbsp;{t.league_position}. {t.name} — "
                         f"{t.points}pts ({t.wins}W {t.draws}D {t.losses}L) "
                         f"GD:{t.goal_difference:+d}<br>")
            html += "<br>"
        return html

    if cmd.startswith("team "):
        name = text[5:].strip()
        t = find_team(name)
        if not t:
            return f"Team '{name}' not found. Type <code>teams</code> to see available teams."
        lines = [
            f"<b>{t.name}</b> — {t.competition.value}<br>",
            f"Position: {t.league_position} | Points: {t.points} | PPG: {t.points_per_game:.2f}<br>",
            f"Record: {t.wins}W {t.draws}D {t.losses}L ({t.games_played} played)<br>",
            f"Goals: {t.goals_scored} scored ({t.goals_per_game:.2f}/game), "
            f"{t.goals_conceded} conceded ({t.goals_conceded_per_game:.2f}/game)<br>",
            f"GD: {t.goal_difference:+d}<br>",
            f"1H goals scored: {t.half_stats.first_half_goals_scored} "
            f"({t.half_stats.avg_first_half_scored(t.games_played):.2f}/game)<br>",
            f"2H goals scored: {t.half_stats.second_half_goals_scored} "
            f"({t.half_stats.avg_second_half_scored(t.games_played):.2f}/game)<br>",
            f"Clean sheets: {t.clean_sheets} ({t.clean_sheet_pct:.0f}%)<br>",
            f"Possession: {t.possession_avg:.1f}%<br>",
        ]
        if t.form.results:
            lines.append(f"Form: {' '.join(t.form.results[-6:])} (rating: {t.form.form_rating:.0f}/100)<br>")
        lines.append(f"Fatigue: {t.fatigue_score:.0f}/100 ({t.games_in_last_n_days(21)} games in 21 days)<br>")
        if t.best_player:
            bp = t.best_player
            lines.append(f"Best player: {bp.name} — {bp.goals}G {bp.assists}A (rating {bp.rating:.1f})<br>")
        if t.key_injuries:
            lines.append("Injuries: " + ", ".join(f"{p.name} ({p.injury_description})" for p in t.key_injuries) + "<br>")
        return "".join(lines)

    # Match setup: "X vs Y"
    if "vs" in cmd:
        raw = re.sub(r'^match\s+', '', text, flags=re.IGNORECASE).strip()
        parts = re.split(r'\s+vs?\s+', raw, flags=re.IGNORECASE)
        if len(parts) != 2:
            return "Format: <code>Team A vs Team B</code>"

        home_name, away_name = parts[0].strip(), parts[1].strip()
        home = find_team(home_name)
        away = find_team(away_name)

        if not home and api_key:
            for comp in Competition:
                home = build_team_season_from_api(home_name, comp, api_key)
                if home:
                    teams[home_name.lower()] = home
                    break
        if not away and api_key:
            for comp in Competition:
                away = build_team_season_from_api(away_name, comp, api_key)
                if away:
                    teams[away_name.lower()] = away
                    break

        if not home:
            return f"Team '{home_name}' not found. Type <code>teams</code> to see available teams."
        if not away:
            return f"Team '{away_name}' not found. Type <code>teams</code> to see available teams."

        # Auto-enrich
        if api_key:
            for team in [home, away]:
                if not team.form.results:
                    standings = fetch_standings(team.competition, api_key)
                    for sname, sdata in standings.items():
                        if sname == team.name and "id" in sdata:
                            enrich_team_with_matches(team, api_key, sdata["id"])
                            break

        competition = home.competition
        is_cup = home.competition != away.competition
        if is_cup:
            competition = Competition.CHAMPIONS_LEAGUE

        current_match = MatchContext(
            home_team=home, away_team=away,
            competition=competition, match_date=date.today(),
            is_cup_match=is_cup,
        )

        result = f"<b>✅ Match set: {home.name} vs {away.name}</b><br>"
        result += f"Competition: {competition.value}<br>"
        if home.form.results:
            result += f"{home.name} form: {' '.join(home.form.results[-6:])}<br>"
        if away.form.results:
            result += f"{away.name} form: {' '.join(away.form.results[-6:])}<br>"
        result += "<br>Now ask me anything! Try: <code>result</code>, <code>btts</code>, <code>over 2.5</code>, <code>first half goal?</code>"
        return result

    # Lineup input: "lineup home Salah, Van Dijk, Rice" or "lineup away Saka, Havertz"
    if cmd.startswith("lineup ") and current_match:
        return handle_lineup(text[7:].strip())

    # Head-to-head input: "h2h 3W 1D 1L 2-1 0-0 3-2"
    if cmd.startswith("h2h ") and current_match:
        return handle_h2h(text[4:].strip())

    # Live match update: "live 45 0-0 55% 3sot 2sot 5cor 3cor"
    if cmd.startswith("live ") and current_match:
        return handle_live_update(text[5:].strip())

    # Predictions
    if not current_match:
        return "Set up a match first! Type something like: <code>Liverpool vs Arsenal</code>"

    ctx = current_match

    if "first half" in cmd and "goal" in cmd:
        pred = predictor.predict_first_half_goal(ctx)
    elif ("second half" in cmd or "2nd half" in cmd) and "goal" in cmd:
        pred = predictor.predict_second_half_goal(ctx)
    elif cmd in ("btts", "both teams to score", "both teams score"):
        pred = predictor.predict_btts(ctx)
    elif cmd in ("scoreline", "score", "predicted score", "predict score", "exact score"):
        pred = predictor.predict_scoreline(ctx)
    elif "over" in cmd and ("corner" in cmd):
        match = re.search(r'over\s+(\d+\.?\d*)', cmd)
        line = float(match.group(1)) if match else 9.5
        pred = predictor.predict_corners(ctx, line)
    elif cmd in ("corners", "corner", "over 9.5 corners"):
        pred = predictor.predict_corners(ctx, 9.5)
    elif "over" in cmd and ("first half" in cmd or "1st half" in cmd or "fh" in cmd):
        match = re.search(r'over\s+(\d+\.?\d*)', cmd)
        line = float(match.group(1)) if match else 1.5
        pred = predictor.predict_over_under_half(ctx, 1, line)
    elif "over" in cmd and ("second half" in cmd or "2nd half" in cmd or "sh" in cmd):
        match = re.search(r'over\s+(\d+\.?\d*)', cmd)
        line = float(match.group(1)) if match else 1.5
        pred = predictor.predict_over_under_half(ctx, 2, line)
    elif "over" in cmd:
        match = re.search(r'over\s+(\d+\.?\d*)', cmd)
        line = float(match.group(1)) if match else 2.5
        pred = predictor.predict_over_under(ctx, line)
    elif cmd in ("result", "winner", "who wins", "match result"):
        pred = predictor.predict_match_result(ctx)
    elif "next goal" in cmd or "who scores next" in cmd:
        pred = predictor.predict_next_goal(ctx)
    elif "clean sheet" in cmd:
        team_name = re.sub(r'clean\s*sheet\s*', '', cmd).strip()
        if not team_name:
            team_name = ctx.home_team.name
        pred = predictor.predict_clean_sheet(ctx, team_name)
    elif cmd in ("analysis", "analyze", "analyse"):
        return predictor.get_match_analysis(ctx).replace("\n", "<br>").replace("  ", "&nbsp;&nbsp;")
    elif "goal" in cmd and ("will" in cmd or "?" in cmd):
        if ctx.is_live and ctx.current_minute >= 45:
            pred = predictor.predict_second_half_goal(ctx)
        else:
            pred = predictor.predict_first_half_goal(ctx)
    else:
        return "I didn't understand that. Try: <code>result</code>, <code>btts</code>, <code>over 2.5</code>, <code>first half goal?</code>, or <code>help</code>"

    return format_prediction_html(pred)


def handle_lineup(text: str) -> str:
    """Parse: 'home Salah, Van Dijk, Rice' or 'away Saka, Havertz'"""
    global current_match
    if not current_match:
        return "Set up a match first."

    parts = text.split(None, 1)
    if len(parts) < 2:
        return "Format: <code>lineup home Player1, Player2, ...</code>"

    side = parts[0].lower()
    names = [n.strip() for n in parts[1].split(",") if n.strip()]

    if side == "home":
        team = current_match.home_team
    elif side == "away":
        team = current_match.away_team
    else:
        return "Use <code>lineup home ...</code> or <code>lineup away ...</code>"

    from .data import PlayerInfo
    lineup = []
    for name in names:
        # Check if player exists in squad
        existing = [p for p in team.players if name.lower() in p.name.lower()]
        if existing:
            lineup.append(existing[0])
        else:
            lineup.append(PlayerInfo(name=name, position="?", rating=6.5))

    team.lineup = lineup
    player_list = ", ".join(p.name for p in lineup)
    return f"<b>✅ {team.name} lineup set:</b><br>{player_list}"


def handle_h2h(text: str) -> str:
    """Parse: '3W 1D 1L 2-1 0-0 3-2' — W/D/L record then recent scores."""
    global current_match
    if not current_match:
        return "Set up a match first."

    from .data import HeadToHead
    parts = text.upper().split()
    wins = draws = losses = 0
    scores = []
    results = []

    for p in parts:
        p_orig = p
        p = p.strip()
        if p.endswith("W"):
            try:
                wins = int(p[:-1])
                results += ["W"] * wins
            except ValueError:
                pass
        elif p.endswith("D"):
            try:
                draws = int(p[:-1])
                results += ["D"] * draws
            except ValueError:
                pass
        elif p.endswith("L"):
            try:
                losses = int(p[:-1])
                results += ["L"] * losses
            except ValueError:
                pass
        elif "-" in p and p[0].isdigit():
            scores.append(p_orig.lower())

    total = wins + draws + losses
    if total == 0:
        return "Format: <code>h2h 3W 1D 1L 2-1 0-0 3-2</code>"

    # Calculate goals from scores
    total_scored = 0
    total_conceded = 0
    for s in scores:
        try:
            hg, ag = s.split("-")
            total_scored += int(hg)
            total_conceded += int(ag)
        except ValueError:
            pass

    h2h = HeadToHead(
        opponent=current_match.away_team.name,
        games=total, wins=wins, draws=draws, losses=losses,
        goals_scored=total_scored, goals_conceded=total_conceded,
        last_results=results, last_scores=scores,
    )
    current_match.home_team.head_to_head[current_match.away_team.name] = h2h

    return (
        f"<b>✅ H2H set: {current_match.home_team.name} vs {current_match.away_team.name}</b><br>"
        f"Record: {wins}W {draws}D {losses}L ({total} games)<br>"
        f"Recent scores: {', '.join(scores) if scores else 'none entered'}<br>"
        f"Avg goals/game: {h2h.avg_goals_per_game:.1f}"
    )


def handle_live_update(text: str) -> str:
    """Parse live update: 'live 45 1-0 60% 4sot 2sot'
    Format: live <minute> <score> [possession%] [home_sot] [away_sot] [home_red] [away_red]
    """
    global current_match
    if not current_match:
        return "Set up a match first."

    parts = text.split()
    if len(parts) < 2:
        return (
            "Live update format:<br>"
            "<code>live 45 1-0</code> (minute, score)<br>"
            "<code>live 65 1-1 58%</code> (+ possession)<br>"
            "<code>live 70 1-1 58% 4sot 2sot</code> (+ shots on target)<br>"
            "<code>live 80 1-1 58% 4sot 2sot 1red 0red</code> (+ red cards)"
        )

    try:
        current_match.is_live = True
        current_match.current_minute = int(parts[0])

        score = parts[1].split("-")
        current_match.home_goals = int(score[0])
        current_match.away_goals = int(score[1])

        if len(parts) > 2 and "%" in parts[2]:
            current_match.home_possession = float(parts[2].replace("%", ""))
            current_match.away_possession = 100 - current_match.home_possession

        if len(parts) > 3 and "sot" in parts[3]:
            current_match.home_shots_on_target = int(parts[3].replace("sot", ""))
        if len(parts) > 4 and "sot" in parts[4]:
            current_match.away_shots_on_target = int(parts[4].replace("sot", ""))

        sot_count = cor_count = red_count = 0
        for part in parts[3:]:
            pl = part.lower()
            if pl.endswith("sot"):
                val = int(pl.replace("sot", ""))
                if sot_count == 0:
                    current_match.home_shots_on_target = val
                else:
                    current_match.away_shots_on_target = val
                sot_count += 1
            elif pl.endswith("cor"):
                val = int(pl.replace("cor", ""))
                if cor_count == 0:
                    current_match.home_corners = val
                else:
                    current_match.away_corners = val
                cor_count += 1
            elif pl.endswith("red"):
                val = int(pl.replace("red", ""))
                if red_count == 0:
                    current_match.home_red_cards = val
                else:
                    current_match.away_red_cards = val
                red_count += 1

        # Track first-half goals if at or past halftime
        if current_match.current_minute >= 45:
            if current_match.home_first_half_goals == 0 and current_match.away_first_half_goals == 0:
                # First update at HT — assume current goals are FH goals
                current_match.home_first_half_goals = current_match.home_goals
                current_match.away_first_half_goals = current_match.away_goals

        ctx = current_match
        result = (
            f"<b>🔴 LIVE: {ctx.home_team.name} {ctx.home_goals}-{ctx.away_goals} "
            f"{ctx.away_team.name} ({ctx.current_minute}')</b><br>"
            f"Possession: {ctx.home_possession:.0f}%-{ctx.away_possession:.0f}%<br>"
            f"Shots on target: {ctx.home_shots_on_target}-{ctx.away_shots_on_target}<br>"
        )
        if ctx.home_corners > 0 or ctx.away_corners > 0:
            result += f"Corners: {ctx.home_corners}-{ctx.away_corners} (total: {ctx.total_corners})<br>"
        if ctx.home_red_cards > 0 or ctx.away_red_cards > 0:
            result += f"Red cards: {ctx.home_red_cards}-{ctx.away_red_cards}<br>"
        result += "<br>Now ask predictions based on current match state!"
        return result
    except (ValueError, IndexError):
        return "Invalid format. Try: <code>live 45 1-0 55%</code>"


def format_prediction_html(pred) -> str:
    bar_pct = pred.probability
    if pred.probability >= 70:
        color = "#22c55e"
    elif pred.probability >= 50:
        color = "#f59e0b"
    else:
        color = "#ef4444"

    html = f"""
    <div style="margin:8px 0">
        <div style="font-size:15px;font-weight:600;margin-bottom:6px">{pred.question}</div>
        <div style="font-size:22px;font-weight:700;color:{color};margin-bottom:4px">{pred.probability:.1f}%</div>
        <div style="background:#1e293b;border-radius:8px;height:14px;overflow:hidden;margin-bottom:8px">
            <div style="background:{color};height:100%;width:{bar_pct}%;border-radius:8px;transition:width 0.5s"></div>
        </div>
        <div style="font-size:14px;margin-bottom:4px"><b>{pred.answer}</b> (Confidence: {pred.confidence})</div>
        <div style="font-size:13px;color:#94a3b8">
    """
    for r in pred.reasoning:
        html += f"• {r}<br>"
    html += "</div></div>"
    return html


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Football Prediction Bot</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    height: 100vh;
    display: flex;
    flex-direction: column;
}
.header {
    background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
    padding: 20px;
    text-align: center;
    border-bottom: 1px solid #1e293b;
}
.header h1 {
    font-size: 24px;
    margin-bottom: 4px;
}
.header p {
    color: #64748b;
    font-size: 13px;
}
.chat-area {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.message {
    max-width: 85%;
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.5;
    word-wrap: break-word;
}
.user-msg {
    align-self: flex-end;
    background: #2563eb;
    color: white;
    border-bottom-right-radius: 4px;
}
.bot-msg {
    align-self: flex-start;
    background: #1e293b;
    color: #e2e8f0;
    border-bottom-left-radius: 4px;
    border: 1px solid #334155;
}
.input-area {
    padding: 16px;
    background: #1e293b;
    border-top: 1px solid #334155;
    display: flex;
    gap: 8px;
}
.input-area input {
    flex: 1;
    padding: 12px 16px;
    border-radius: 10px;
    border: 1px solid #334155;
    background: #0f172a;
    color: #e2e8f0;
    font-size: 15px;
    outline: none;
}
.input-area input:focus {
    border-color: #2563eb;
}
.input-area input::placeholder {
    color: #475569;
}
.input-area button {
    padding: 12px 24px;
    border-radius: 10px;
    border: none;
    background: #2563eb;
    color: white;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
}
.input-area button:hover {
    background: #1d4ed8;
}
.quick-btns {
    padding: 8px 16px;
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    background: #0f172a;
}
.quick-btn {
    padding: 6px 12px;
    border-radius: 16px;
    border: 1px solid #334155;
    background: transparent;
    color: #94a3b8;
    font-size: 12px;
    cursor: pointer;
}
.quick-btn:hover {
    background: #1e293b;
    color: #e2e8f0;
    border-color: #2563eb;
}
.typing {
    color: #64748b;
    font-style: italic;
    font-size: 13px;
    padding: 4px 16px;
}
</style>
</head>
<body>

<div class="header">
    <h1>⚽ Football Prediction Bot</h1>
    <p>Premier League • La Liga • Bundesliga • Serie A • Ligue 1 • Championship • Champions League</p>
</div>

<div class="chat-area" id="chat">
    <div class="message bot-msg">
        Welcome! Start by setting up a match:<br><br>
        Type something like: <code>Liverpool vs Arsenal</code><br><br>
        Then ask predictions like <code>result</code>, <code>btts</code>, <code>over 2.5</code>, <code>first half goal?</code><br><br>
        Type <code>teams</code> to see all available teams, or <code>help</code> for all commands.
    </div>
</div>

<div class="quick-btns" id="quickBtns">
    <button class="quick-btn" onclick="send('teams')">Teams</button>
    <button class="quick-btn" onclick="send('help')">Help</button>
</div>

<div class="input-area">
    <input type="text" id="input" placeholder="Type a question... e.g. Liverpool vs Arsenal" autofocus>
    <button onclick="sendInput()">Send</button>
</div>

<script>
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const quickBtns = document.getElementById('quickBtns');

input.addEventListener('keydown', e => {
    if (e.key === 'Enter') sendInput();
});

function sendInput() {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    send(text);
}

function send(text) {
    addMessage(text, 'user-msg');
    const typing = document.createElement('div');
    typing.className = 'typing';
    typing.textContent = 'Analyzing...';
    chat.appendChild(typing);
    chat.scrollTop = chat.scrollHeight;

    fetch('/api/predict', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: text})
    })
    .then(r => r.json())
    .then(data => {
        typing.remove();
        addMessage(data.response, 'bot-msg');
        if (data.match_set) {
            updateQuickButtons();
        }
    })
    .catch(err => {
        typing.remove();
        addMessage('Error: ' + err.message, 'bot-msg');
    });
}

function addMessage(html, cls) {
    const div = document.createElement('div');
    div.className = 'message ' + cls;
    div.innerHTML = html;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function promptLive() {
    const min = prompt('Current minute:');
    if (!min) return;
    const score = prompt('Score (e.g. 1-0):');
    if (!score) return;
    const poss = prompt('Home possession % (e.g. 55):') || '50';
    const hsot = prompt('Home shots on target:') || '0';
    const asot = prompt('Away shots on target:') || '0';
    const hcor = prompt('Home corners:') || '0';
    const acor = prompt('Away corners:') || '0';
    let cmd = `live ${min} ${score} ${poss}%`;
    if (hsot !== '0' || asot !== '0') cmd += ` ${hsot}sot ${asot}sot`;
    if (hcor !== '0' || acor !== '0') cmd += ` ${hcor}cor ${acor}cor`;
    send(cmd);
}

function updateQuickButtons() {
    quickBtns.innerHTML = `
        <button class="quick-btn" onclick="send('result')">Result</button>
        <button class="quick-btn" onclick="send('scoreline')">Scoreline</button>
        <button class="quick-btn" onclick="send('btts')">BTTS</button>
        <button class="quick-btn" onclick="send('over 2.5')">Over 2.5</button>
        <button class="quick-btn" onclick="send('over 1.5')">Over 1.5</button>
        <button class="quick-btn" onclick="send('over 1.5 first half')">O1.5 FH</button>
        <button class="quick-btn" onclick="send('over 2.5 first half')">O2.5 FH</button>
        <button class="quick-btn" onclick="send('over 1.5 second half')">O1.5 SH</button>
        <button class="quick-btn" onclick="send('over 2.5 second half')">O2.5 SH</button>
        <button class="quick-btn" onclick="send('corners')">Corners 9.5</button>
        <button class="quick-btn" onclick="send('first half goal?')">1H Goal?</button>
        <button class="quick-btn" onclick="send('second half goal?')">2H Goal?</button>
        <button class="quick-btn" onclick="send('analysis')">Analysis</button>
        <button class="quick-btn" onclick="promptH2H()">📊 Add H2H</button>
        <button class="quick-btn" onclick="promptLineup('home')">📋 Home Lineup</button>
        <button class="quick-btn" onclick="promptLineup('away')">📋 Away Lineup</button>
        <button class="quick-btn" onclick="promptLive()">🔴 Go Live</button>
    `;
}

function promptH2H() {
    const data = prompt('Head-to-head record (home team perspective)\\nFormat: 3W 1D 1L 2-1 0-0 3-2\\n(wins draws losses then recent scores)');
    if (data) send('h2h ' + data);
}

function promptLineup(side) {
    const names = prompt(side.charAt(0).toUpperCase() + side.slice(1) + ' team lineup:\\nEnter player names separated by commas');
    if (names) send('lineup ' + side + ' ' + names);
}
</script>
</body>
</html>"""


class PredictionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode())

    def do_POST(self):
        if self.path == "/api/predict":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            message = body.get("message", "")

            response = handle_message(message)
            match_set = current_match is not None and "vs" in message.lower()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": response,
                "match_set": match_set,
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress request logs


def main():
    global teams

    print("\n  ⚽ Football Prediction Bot — Web Interface")
    print("  ─────────────────────────────────────────")

    teams = get_sample_teams()

    if api_key:
        print("  API key found — fetching live 2025/26 data...")
        try:
            live_teams = load_all_leagues(api_key, fetch_matches=False)
            if live_teams:
                teams.update(live_teams)
                print(f"  ✅ Loaded {len(live_teams)} teams with live data!")
        except Exception as e:
            print(f"  ⚠️  API fetch failed: {e} — using fallback data")
    else:
        print("  No API key — using fallback data")
        print("  For live data: export FOOTBALL_DATA_API_KEY=your_key")

    port = 8080
    server = HTTPServer(("127.0.0.1", port), PredictionHandler)
    url = f"http://localhost:{port}"
    print(f"\n  ✅ Server running at: {url}")
    print("  Opening in your browser...\n")
    print("  Press Ctrl+C to stop.\n")

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
