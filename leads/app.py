#!/usr/bin/env python3
"""
Leads Platform — CRM + Lead Generator for AI agent consultancy.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 app.py

Then open http://127.0.0.1:5055
"""

import json
import os
import sqlite3
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

import llm
from industries import INDUSTRIES, get_industry, list_industries

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "leads.db"

app = Flask(__name__)
app.secret_key = "leads-dev-secret-change-me"


# ---------- database ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        website TEXT,
        industry TEXT,
        country TEXT,
        city TEXT,
        contact_name TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        company_size TEXT,
        grade TEXT,
        opportunity_score INTEGER,
        status TEXT DEFAULT 'new',
        source TEXT,
        notes TEXT,
        ai_assessment TEXT,
        recommended_agents TEXT,
        demo_prompt TEXT,
        outreach_email TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_leads_grade ON leads(grade);
    CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
    CREATE INDEX IF NOT EXISTS idx_leads_country ON leads(country);
    """)
    conn.commit()
    conn.close()


# ---------- website fetching ----------
def fetch_website_summary(url, max_chars=6000):
    """Fetch a website and return a cleaned text summary for Claude to analyze."""
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        r = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; LeadsBot/1.0)"},
        )
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = (soup.title.string if soup.title else "") or ""
        meta_desc = ""
        md = soup.find("meta", attrs={"name": "description"})
        if md:
            meta_desc = md.get("content", "")
        text = " ".join(soup.stripped_strings)
        summary = f"URL: {url}\nTITLE: {title}\nDESCRIPTION: {meta_desc}\n\nCONTENT:\n{text}"
        return summary[:max_chars]
    except Exception as e:
        return f"ERROR fetching {url}: {e}"


# ---------- Claude analysis ----------
def analyze_company(company, website_text, industry_key, country):
    """Ask Claude to analyze a company and score the AI opportunity."""
    industry = get_industry(industry_key) if industry_key else None
    industry_context = ""
    if industry:
        industry_context = f"\n\nINDUSTRY CONTEXT ({industry['name']}):\n"
        industry_context += "Common pain points:\n- " + "\n- ".join(industry["pain_points"])
        industry_context += "\n\nKnown AI agent use cases:\n"
        for uc in industry["use_cases"]:
            industry_context += f"- {uc['title']}: {uc['description']} (Impact: {uc['impact']})\n"

    prompt = f"""You are an AI consultancy analyst. Assess this company's opportunity for AI agent integration.

COMPANY: {company}
COUNTRY: {country or 'unknown'}
INDUSTRY: {industry['name'] if industry else industry_key or 'unknown'}
{industry_context}

{"WEBSITE CONTENT:" + chr(10) + website_text if website_text else "No website content available."}

Return STRICT JSON with this exact schema:
{{
  "grade": "A" | "B" | "C" | "D",
  "opportunity_score": 0-100,
  "current_state": "1-2 sentences on their current digital/AI maturity",
  "gaps": ["gap 1", "gap 2", "gap 3"],
  "recommended_agents": [
    {{"name": "Agent name", "why": "why this specific company needs it", "impact": "measurable outcome"}}
  ],
  "top_3_hooks": ["angle 1", "angle 2", "angle 3"]
}}

GRADING:
- A: Clear, urgent opportunity + budget signals + decision-maker accessible
- B: Strong fit, needs qualification
- C: Possible fit, longer sales cycle
- D: Poor fit or high friction

Return ONLY the JSON, no preamble."""

    text = llm.complete(prompt, max_tokens=2000)
    text = llm.extract_json(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse failed: {e}", "raw": text}


def generate_outreach_email(company, industry_key, analysis, sender_name="the team"):
    """Generate a personalized outreach email."""
    industry = get_industry(industry_key) if industry_key else None
    industry_name = industry["name"] if industry else (industry_key or "your industry")

    prompt = f"""Write a short, specific, no-fluff cold outreach email to {company} offering AI agent consultancy.

INDUSTRY: {industry_name}
COMPANY ASSESSMENT: {json.dumps(analysis, indent=2)}

RULES:
- Under 120 words total
- First sentence must reference something specific about THIS company, not generic flattery
- Propose ONE concrete AI agent idea tied to their pain point
- Include a single, specific call to action (a 15-min call)
- No corporate jargon, no "in today's fast-paced world"
- No bullet lists
- Sign off as "{sender_name}"

Return ONLY:
SUBJECT: <subject line>

<body>"""

    return llm.complete(prompt, max_tokens=800)


def generate_demo_prompt(company, industry_key, analysis):
    """Generate a detailed prompt that can be used to produce a mock website/demo."""
    industry = get_industry(industry_key) if industry_key else None
    industry_name = industry["name"] if industry else (industry_key or "business")

    prompt = f"""Write a detailed prompt that Claude (or any coding AI) can use to build a mock website + AI agent demo for this company. The goal is to showcase to {company} what their business could look like with AI agents.

COMPANY: {company}
INDUSTRY: {industry_name}
ANALYSIS: {json.dumps(analysis, indent=2)}

The prompt should specify:
1. A modern single-page website with their branding (suggest palette/style based on industry)
2. A specific AI agent widget embedded (chat or form) that solves the #1 pain point
3. Hero copy that speaks to their actual problem
4. 3 feature sections showing AI-powered workflows relevant to them
5. A "book a call" CTA
6. Tech: plain HTML/CSS/JS, no frameworks, self-contained single file

Return a clear, actionable prompt another AI can execute to build the demo. Keep it under 400 words."""

    return llm.complete(prompt, max_tokens=1200)


def suggest_leads(country, industry_key, count=10):
    """Use Claude to suggest companies to target in a given region + industry."""
    industry = get_industry(industry_key) if industry_key else None
    industry_name = industry["name"] if industry else industry_key

    prompt = f"""Suggest {count} real companies or organizations in {country} in the {industry_name} sector that would be strong targets for AI agent consultancy.

For each, return JSON with:
- name (real, well-known)
- website (best guess)
- city
- why_good_fit (1 sentence - specific reason they'd benefit)
- likely_decision_maker_title

Return STRICT JSON array only:
[{{"name": "...", "website": "...", "city": "...", "why_good_fit": "...", "likely_decision_maker_title": "..."}}]

Only return companies you are confident exist. No made-up names."""

    text = llm.complete(prompt, max_tokens=3000)
    text = llm.extract_json(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return []


# ---------- routes ----------
@app.route("/")
def dashboard():
    db = get_db()
    stats = {
        "total": db.execute("SELECT COUNT(*) FROM leads").fetchone()[0],
        "by_grade": dict(
            db.execute(
                "SELECT COALESCE(grade, 'Ungraded'), COUNT(*) FROM leads GROUP BY grade"
            ).fetchall()
        ),
        "by_status": dict(
            db.execute(
                "SELECT status, COUNT(*) FROM leads GROUP BY status"
            ).fetchall()
        ),
        "by_country": dict(
            db.execute(
                "SELECT COALESCE(country, 'Unknown'), COUNT(*) FROM leads GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10"
            ).fetchall()
        ),
    }
    recent = db.execute(
        "SELECT * FROM leads ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    return render_template("dashboard.html", stats=stats, recent=recent)


@app.route("/crm")
def crm():
    db = get_db()
    q = request.args.get("q", "").strip()
    grade = request.args.get("grade", "")
    country = request.args.get("country", "")
    status = request.args.get("status", "")
    industry = request.args.get("industry", "")

    sql = "SELECT * FROM leads WHERE 1=1"
    params = []
    if q:
        sql += " AND (company LIKE ? OR contact_name LIKE ? OR contact_email LIKE ?)"
        like = f"%{q}%"
        params += [like, like, like]
    if grade:
        sql += " AND grade = ?"
        params.append(grade)
    if country:
        sql += " AND country = ?"
        params.append(country)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if industry:
        sql += " AND industry = ?"
        params.append(industry)
    sql += " ORDER BY opportunity_score DESC, created_at DESC"

    leads = db.execute(sql, params).fetchall()
    countries = [
        r[0]
        for r in db.execute(
            "SELECT DISTINCT country FROM leads WHERE country IS NOT NULL"
        ).fetchall()
    ]
    return render_template(
        "crm.html",
        leads=leads,
        countries=countries,
        industries=list_industries(),
        filters={
            "q": q,
            "grade": grade,
            "country": country,
            "status": status,
            "industry": industry,
        },
    )


@app.route("/lead/new", methods=["GET", "POST"])
def lead_new():
    if request.method == "POST":
        data = request.form
        db = get_db()
        cur = db.execute(
            """INSERT INTO leads (company, website, industry, country, city, contact_name,
               contact_email, contact_phone, company_size, grade, opportunity_score,
               status, source, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("company"),
                data.get("website"),
                data.get("industry"),
                data.get("country"),
                data.get("city"),
                data.get("contact_name"),
                data.get("contact_email"),
                data.get("contact_phone"),
                data.get("company_size"),
                data.get("grade"),
                int(data.get("opportunity_score") or 0),
                data.get("status") or "new",
                data.get("source"),
                data.get("notes"),
            ),
        )
        db.commit()
        return redirect(url_for("lead_detail", lead_id=cur.lastrowid))
    return render_template(
        "lead_form.html", lead=None, industries=list_industries()
    )


@app.route("/lead/<int:lead_id>")
def lead_detail(lead_id):
    db = get_db()
    lead = db.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        return "Not found", 404
    industry = get_industry(lead["industry"]) if lead["industry"] else None
    return render_template("lead_detail.html", lead=lead, industry=industry)


@app.route("/lead/<int:lead_id>/edit", methods=["GET", "POST"])
def lead_edit(lead_id):
    db = get_db()
    lead = db.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        return "Not found", 404
    if request.method == "POST":
        data = request.form
        db.execute(
            """UPDATE leads SET company=?, website=?, industry=?, country=?, city=?,
               contact_name=?, contact_email=?, contact_phone=?, company_size=?,
               grade=?, opportunity_score=?, status=?, source=?, notes=?,
               updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (
                data.get("company"),
                data.get("website"),
                data.get("industry"),
                data.get("country"),
                data.get("city"),
                data.get("contact_name"),
                data.get("contact_email"),
                data.get("contact_phone"),
                data.get("company_size"),
                data.get("grade"),
                int(data.get("opportunity_score") or 0),
                data.get("status"),
                data.get("source"),
                data.get("notes"),
                lead_id,
            ),
        )
        db.commit()
        return redirect(url_for("lead_detail", lead_id=lead_id))
    return render_template(
        "lead_form.html", lead=lead, industries=list_industries()
    )


@app.route("/lead/<int:lead_id>/delete", methods=["POST"])
def lead_delete(lead_id):
    db = get_db()
    db.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    db.commit()
    return redirect(url_for("crm"))


# ---------- generator ----------
@app.route("/generator")
def generator():
    return render_template(
        "generator.html",
        industries=list_industries(),
        countries=["UK", "USA", "UAE", "Saudi Arabia", "Oman", "Abu Dhabi"],
    )


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.json
    company = data.get("company", "").strip()
    website = data.get("website", "").strip()
    industry_key = data.get("industry", "")
    country = data.get("country", "")
    if not company:
        return jsonify({"error": "Company name required"}), 400

    website_text = fetch_website_summary(website) if website else None
    try:
        analysis = analyze_company(company, website_text, industry_key, country)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"analysis": analysis, "website_fetched": bool(website_text)})


@app.route("/api/generate_email", methods=["POST"])
def api_generate_email():
    data = request.json
    try:
        email = generate_outreach_email(
            data.get("company", ""),
            data.get("industry", ""),
            data.get("analysis", {}),
            data.get("sender_name", "the team"),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"email": email})


@app.route("/api/generate_demo", methods=["POST"])
def api_generate_demo():
    data = request.json
    try:
        prompt = generate_demo_prompt(
            data.get("company", ""),
            data.get("industry", ""),
            data.get("analysis", {}),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"prompt": prompt})


@app.route("/api/suggest_leads", methods=["POST"])
def api_suggest_leads():
    data = request.json
    try:
        leads = suggest_leads(
            data.get("country", ""),
            data.get("industry", ""),
            int(data.get("count", 10)),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"leads": leads})


@app.route("/api/save_lead", methods=["POST"])
def api_save_lead():
    data = request.json
    db = get_db()
    analysis = data.get("analysis", {})
    grade = analysis.get("grade") if isinstance(analysis, dict) else None
    score = analysis.get("opportunity_score") if isinstance(analysis, dict) else None

    cur = db.execute(
        """INSERT INTO leads (company, website, industry, country, city, contact_name,
           contact_email, contact_phone, grade, opportunity_score, status, source,
           ai_assessment, recommended_agents, demo_prompt, outreach_email)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.get("company"),
            data.get("website"),
            data.get("industry"),
            data.get("country"),
            data.get("city"),
            data.get("contact_name"),
            data.get("contact_email"),
            data.get("contact_phone"),
            grade,
            int(score or 0) if score is not None else 0,
            "new",
            data.get("source", "generator"),
            json.dumps(analysis) if analysis else None,
            json.dumps(analysis.get("recommended_agents", []))
            if isinstance(analysis, dict)
            else None,
            data.get("demo_prompt"),
            data.get("outreach_email"),
        ),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "url": url_for("lead_detail", lead_id=cur.lastrowid)})


# ---------- industries reference ----------
@app.route("/industries")
def industries_page():
    return render_template("industries.html", industries=INDUSTRIES)


@app.route("/industries/<key>")
def industry_detail(key):
    industry = get_industry(key)
    if not industry:
        return "Not found", 404
    return render_template("industry_detail.html", key=key, industry=industry)


# ---------- export ----------
@app.route("/export.csv")
def export_csv():
    import csv
    from io import StringIO

    db = get_db()
    leads = db.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    si = StringIO()
    if leads:
        writer = csv.DictWriter(si, fieldnames=leads[0].keys())
        writer.writeheader()
        for row in leads:
            writer.writerow(dict(row))
    from flask import Response

    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


if __name__ == "__main__":
    init_db()
    provider = llm.provider_name()
    if provider == "none":
        print("WARNING: No LLM provider configured. Set one of:")
        print("  export GEMINI_API_KEY=...  (free, from https://aistudio.google.com/apikey)")
        print("  OR run Ollama:  brew install ollama && ollama pull llama3.1:8b && ollama serve")
        print("  OR export ANTHROPIC_API_KEY=... (paid)")
    else:
        print(f"LLM provider: {provider}")
    port = 5055
    url = f"http://127.0.0.1:{port}"
    print(f"\nLeads Platform running at {url}")
    print("Opening in your browser…")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    app.run(host="127.0.0.1", port=port, debug=False)
