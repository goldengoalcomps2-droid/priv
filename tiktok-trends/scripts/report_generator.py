#!/usr/bin/env python3
"""
TikTok Trending Products Report Generator
==========================================
Takes raw scrape data and generates clean, easy-to-read reports.

Outputs:
  - Markdown report (human-readable)
  - JSON summary (machine-readable)
  - CSV export (spreadsheet-friendly)

Usage:
    python3 report_generator.py                    # Generate from latest scrape
    python3 report_generator.py --date 2026-03-25  # Generate from specific date
"""

import json
import csv
import sys
import os
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_REPORTS = PROJECT_ROOT / "data" / "reports"

# Ensure dirs exist
DATA_REPORTS.mkdir(parents=True, exist_ok=True)


def find_latest_scrape(target_date=None):
    """Find the most recent enriched scrape file."""
    if target_date:
        enriched = DATA_RAW / f"scrape_{target_date}_enriched.json"
        if enriched.exists():
            return enriched
        basic = DATA_RAW / f"scrape_{target_date}.json"
        if basic.exists():
            return basic

    # Find most recent
    files = sorted(DATA_RAW.glob("scrape_*_enriched.json"), reverse=True)
    if files:
        return files[0]
    files = sorted(DATA_RAW.glob("scrape_*.json"), reverse=True)
    if files:
        return files[0]
    return None


def load_data(file_path):
    """Load scrape data from JSON."""
    with open(file_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Product brief data - enriched descriptions for each category
# ---------------------------------------------------------------------------
CATEGORY_BRIEFS = {
    "Skincare": {
        "emoji": "🧴",
        "why_trending": "Skincare routines and 'Get Ready With Me' videos dominate TikTok. Products with visible before/after results go viral easily.",
        "price_range": "$8 - $45",
        "target_audience": "Women 18-34, skincare enthusiasts",
        "content_angle": "Before/after transformations, routine videos, dermatologist reactions",
        "top_hashtags": ["#SkinTok", "#SkincareRoutine", "#GlowUp", "#GRWM"],
    },
    "Makeup": {
        "emoji": "💄",
        "why_trending": "Quick makeup tutorials and shade comparisons drive impulse purchases. Lip products especially thrive because they're easy to demo on camera.",
        "price_range": "$5 - $35",
        "target_audience": "Women 16-30, beauty creators",
        "content_angle": "Shade swatches, wear tests, dupes vs. originals, GRWM",
        "top_hashtags": ["#MakeupTok", "#LipOil", "#BeautyFinds", "#MakeupDupe"],
    },
    "Hair Care": {
        "emoji": "💇",
        "why_trending": "Hair transformation content is highly shareable. Products promising growth, repair, or styling versatility perform well.",
        "price_range": "$10 - $40",
        "target_audience": "Women 18-40, all hair types",
        "content_angle": "Hair transformations, growth journeys, styling tutorials",
        "top_hashtags": ["#HairTok", "#HairGrowth", "#HairCare", "#ClawClip"],
    },
    "Fragrance": {
        "emoji": "🌸",
        "why_trending": "Gen Z fragrance culture exploded on TikTok. Scent layering, blind buys, and luxury dupe content generate hundreds of millions of views.",
        "price_range": "$10 - $60",
        "target_audience": "Gen Z & Millennials, fragrance collectors",
        "content_angle": "Scent layering, blind buys, compliment getters, dupe reveals",
        "top_hashtags": ["#PerfumeTok", "#FragranceTok", "#ScentLayering", "#PerfumeDupe"],
    },
    "Tech & Gadgets": {
        "emoji": "📱",
        "why_trending": "Unboxing and review content is a TikTok staple. Affordable gadgets under $30 convert extremely well because of low purchase hesitation.",
        "price_range": "$10 - $50",
        "target_audience": "Gen Z & Millennials, tech-curious shoppers",
        "content_angle": "Unboxing, side-by-side comparisons, setup videos, room makeovers",
        "top_hashtags": ["#TechTok", "#GalaxyProjector", "#GadgetFinds", "#PhoneCase"],
    },
    "Home & Organization": {
        "emoji": "🏠",
        "why_trending": "Transformation content is irresistible on TikTok. Before/after room makeovers, pantry organization, and cleaning hacks drive massive engagement.",
        "price_range": "$8 - $40",
        "target_audience": "Women 22-40, homeowners and renters",
        "content_angle": "Before/after transformations, organization hacks, cleaning routines",
        "top_hashtags": ["#CleanTok", "#HomeOrganization", "#RoomMakeover", "#ApartmentHacks"],
    },
    "Fashion": {
        "emoji": "👗",
        "why_trending": "Outfit-of-the-day content and haul videos keep fashion trending. Accessories outperform clothing because they avoid sizing issues.",
        "price_range": "$10 - $60",
        "target_audience": "Women 16-35, fashion-forward shoppers",
        "content_angle": "OOTD, try-on hauls, styling tips, seasonal capsule wardrobes",
        "top_hashtags": ["#FashionTok", "#OOTD", "#StyleInspo", "#TikTokFashion"],
    },
    "Health & Wellness": {
        "emoji": "💊",
        "why_trending": "Wellness culture is massive on TikTok. Liquid vitamins and greens powders sell well because they're easy to demo in morning routine content.",
        "price_range": "$15 - $50",
        "target_audience": "Health-conscious 20-40 year olds",
        "content_angle": "Morning routines, supplement reviews, health journey updates",
        "top_hashtags": ["#WellnessTok", "#HealthTok", "#Supplements", "#MorningRoutine"],
    },
    "Pet Products": {
        "emoji": "🐾",
        "why_trending": "Pet content is among the most engaging on TikTok. Products that make pets look cute or react funny drive impulse purchases from devoted pet parents.",
        "price_range": "$8 - $35",
        "target_audience": "Pet owners 18-45",
        "content_angle": "Pet reactions, unboxing with pets, cute outfit try-ons",
        "top_hashtags": ["#PetTok", "#DogTok", "#CatTok", "#PetFinds"],
    },
    "Body Care": {
        "emoji": "🧼",
        "why_trending": "Body care is an extension of the skincare obsession. Luxurious body butters, scrubs, and self-tan products thrive in routine content.",
        "price_range": "$8 - $30",
        "target_audience": "Women 18-35",
        "content_angle": "Shower routines, self-care nights, product layering",
        "top_hashtags": ["#BodyCare", "#ShowerRoutine", "#SelfCare", "#GlowUp"],
    },
}


def generate_markdown_report(data, date_str):
    """Generate a clean, easy-to-read Markdown report."""
    rankings = data.get("product_rankings", [])
    if not rankings:
        return "No product rankings found in data."

    lines = []
    lines.append(f"# 🔥 TikTok Trending Products Report — US")
    lines.append(f"**Date:** {date_str}")
    lines.append(f"**Region:** United States")
    lines.append(f"**Sources analyzed:** {len(data.get('sources', {}).get('trend_pages', []))}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📊 Top 10 Trending Product Categories")
    lines.append("")

    for item in rankings[:10]:
        cat = item["category"]
        brief = CATEGORY_BRIEFS.get(cat, {})
        emoji = brief.get("emoji", "📦")
        rank = item["rank"]

        lines.append(f"### {rank}. {emoji} {cat}")
        lines.append("")

        # Mention stats
        lines.append(f"- **Mentions across sources:** {item['total_mentions']}")
        lines.append(f"- **Found in:** {item['source_count']} sources")

        if brief:
            lines.append(f"- **Price range:** {brief.get('price_range', 'N/A')}")
            lines.append(f"- **Target audience:** {brief.get('target_audience', 'N/A')}")
            lines.append(f"- **Content angle:** {brief.get('content_angle', 'N/A')}")
            lines.append(f"- **Top hashtags:** {', '.join(brief.get('top_hashtags', []))}")
            lines.append("")
            lines.append(f"> **Why it's trending:** {brief.get('why_trending', '')}")
        lines.append("")

        # Top keywords
        top_kws = item.get("top_keywords", [])[:5]
        if top_kws:
            lines.append("| Keyword | Mentions |")
            lines.append("|---------|----------|")
            for kw in top_kws:
                lines.append(f"| {kw['keyword']} | {kw['count']} |")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Hashtag insights
    hashtag_data = data.get("sources", {}).get("hashtag_insights", [])
    if hashtag_data:
        lines.append("## #️⃣ Hashtag Pulse Check")
        lines.append("")
        lines.append("| Hashtag | Status |")
        lines.append("|---------|--------|")
        for h in hashtag_data:
            metrics = h.get("metrics_found", [])
            status = f"{', '.join(metrics[:3])}" if metrics else "Active"
            lines.append(f"| {h['hashtag']} | {status} |")
        lines.append("")

    # Quick insights
    lines.append("## 💡 Quick Insights")
    lines.append("")
    lines.append("- **Best price point:** $10-$30 (low hesitation = fast checkout)")
    lines.append("- **Top buyer demo:** Women 25-34 (29% of TikTok shoppers)")
    lines.append("- **Content that converts:** Before/after, tutorials, unboxing, GRWM")
    lines.append("- **Key success factors:** Visually demonstrable, creator-friendly, impulse-priced")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated automatically on {datetime.now().strftime('%Y-%m-%d at %H:%M')} UTC*")
    lines.append(f"*Next update scheduled in 2 days*")

    return "\n".join(lines)


def generate_json_summary(data, date_str):
    """Generate a clean JSON summary."""
    rankings = data.get("product_rankings", [])
    summary = {
        "report_date": date_str,
        "region": "US",
        "generated_at": datetime.now().isoformat(),
        "top_10_products": [],
    }

    for item in rankings[:10]:
        cat = item["category"]
        brief = CATEGORY_BRIEFS.get(cat, {})
        summary["top_10_products"].append({
            "rank": item["rank"],
            "category": cat,
            "total_mentions": item["total_mentions"],
            "sources_found_in": item["source_count"],
            "price_range": brief.get("price_range", "N/A"),
            "target_audience": brief.get("target_audience", "N/A"),
            "why_trending": brief.get("why_trending", ""),
            "content_angle": brief.get("content_angle", ""),
            "top_hashtags": brief.get("top_hashtags", []),
            "top_keywords": [kw["keyword"] for kw in item.get("top_keywords", [])[:5]],
        })

    return summary


def generate_csv_export(data, date_str):
    """Generate a CSV export for spreadsheet use."""
    rankings = data.get("product_rankings", [])
    rows = []

    for item in rankings[:10]:
        cat = item["category"]
        brief = CATEGORY_BRIEFS.get(cat, {})
        rows.append({
            "Rank": item["rank"],
            "Category": cat,
            "Total Mentions": item["total_mentions"],
            "Sources": item["source_count"],
            "Price Range": brief.get("price_range", "N/A"),
            "Target Audience": brief.get("target_audience", "N/A"),
            "Why Trending": brief.get("why_trending", ""),
            "Content Angle": brief.get("content_angle", ""),
            "Top Hashtags": "; ".join(brief.get("top_hashtags", [])),
            "Top Keywords": "; ".join(kw["keyword"] for kw in item.get("top_keywords", [])[:5]),
            "Report Date": date_str,
        })

    return rows


def generate_all_reports(target_date=None):
    """Generate all report formats from scrape data."""
    scrape_file = find_latest_scrape(target_date)
    if not scrape_file:
        print("ERROR: No scrape data found. Run scraper.py first.")
        return

    data = load_data(scrape_file)
    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    print(f"Generating reports for {date_str}...")

    # Create date-specific report folder
    report_dir = DATA_REPORTS / date_str
    report_dir.mkdir(parents=True, exist_ok=True)

    # 1. Markdown report
    md_content = generate_markdown_report(data, date_str)
    md_file = report_dir / "trending-products-report.md"
    with open(md_file, "w") as f:
        f.write(md_content)
    print(f"  ✓ Markdown report: {md_file}")

    # 2. JSON summary
    json_summary = generate_json_summary(data, date_str)
    json_file = report_dir / "trending-products-summary.json"
    with open(json_file, "w") as f:
        json.dump(json_summary, f, indent=2)
    print(f"  ✓ JSON summary: {json_file}")

    # 3. CSV export
    csv_rows = generate_csv_export(data, date_str)
    csv_file = report_dir / "trending-products.csv"
    if csv_rows:
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(csv_rows)
    print(f"  ✓ CSV export: {csv_file}")

    # 4. Also save latest report to root for easy access
    latest_md = DATA_REPORTS / "LATEST-REPORT.md"
    with open(latest_md, "w") as f:
        f.write(md_content)
    print(f"  ✓ Latest report: {latest_md}")

    latest_json = DATA_REPORTS / "latest-summary.json"
    with open(latest_json, "w") as f:
        json.dump(json_summary, f, indent=2)
    print(f"  ✓ Latest JSON: {latest_json}")

    print(f"\nAll reports saved to: {report_dir}/")
    return report_dir


if __name__ == "__main__":
    target = None
    if len(sys.argv) > 2 and sys.argv[1] == "--date":
        target = sys.argv[2]
    generate_all_reports(target)
