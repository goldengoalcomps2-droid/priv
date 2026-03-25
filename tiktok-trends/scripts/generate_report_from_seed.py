#!/usr/bin/env python3
"""
Generate reports from seeded WebSearch data.
This is the primary report generator used by the scheduled agent.

Usage:
    python3 generate_report_from_seed.py                    # Use latest seed
    python3 generate_report_from_seed.py --date 2026-03-25  # Specific date
"""

import json
import csv
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_REPORTS = PROJECT_ROOT / "data" / "reports"
DATA_REPORTS.mkdir(parents=True, exist_ok=True)


def find_seed(target_date=None):
    """Find the seed data file."""
    if target_date:
        f = DATA_RAW / f"seed_{target_date}.json"
        if f.exists():
            return f
    # Latest
    files = sorted(DATA_RAW.glob("seed_*.json"), reverse=True)
    return files[0] if files else None


def generate_markdown(data, date_str):
    """Generate the main human-readable report."""
    rankings = data.get("product_rankings", [])
    products = data.get("specific_products", [])
    insights = data.get("market_insights", {})
    hashtags = data.get("hashtag_data", [])
    brands = data.get("top_brands_mentioned", [])
    sources = data.get("sources", {})

    lines = []
    lines.append(f"# TikTok Trending Products Report — US")
    lines.append(f"**Date:** {date_str}")
    lines.append(f"**Region:** United States")
    lines.append(f"**Sources:** {len(sources.get('source_sites', []))} analytics sites analyzed")
    lines.append(f"**Method:** Automated web intelligence gathering")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ===== QUICK SUMMARY =====
    lines.append("## At a Glance")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| TikTok Shop Global GMV (2026) | {insights.get('global_gmv_2026', 'N/A')} |")
    lines.append(f"| Beauty share of GMV | {insights.get('beauty_share_of_gmv', 'N/A')} |")
    lines.append(f"| Sweet spot price range | {insights.get('sweet_spot_price', 'N/A')} |")
    lines.append(f"| Top buyer age group | {insights.get('top_buyer_age', 'N/A')} |")
    lines.append(f"| Gender split | {insights.get('gender_split', 'N/A')} |")
    lines.append(f"| Creator influence | {insights.get('gen_z_buy_from_creators', 'N/A')} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ===== TOP 10 CATEGORIES =====
    lines.append("## Top 10 Trending Product Categories")
    lines.append("")

    category_briefs = {
        "Skincare": {
            "icon": "#1", "price": "$8-$45", "audience": "Women 18-34",
            "why": "Skincare routines and GRWM videos dominate TikTok. K-beauty, PDRN, and collagen products are the 2026 breakouts. 65% of Gen Z discover skincare on TikTok first.",
            "content": "Before/after transformations, routine videos, dermatologist reactions, ingredient breakdowns",
            "tags": "#SkinTok #SkincareRoutine #GlowUp #GRWM #Kbeauty",
        },
        "Makeup": {
            "icon": "#2", "price": "$5-$48", "audience": "Women 16-30",
            "why": "Lip oils, magnetic lashes, and press-on nails lead the category. Skincare-makeup hybrids (serum foundations) are the new frontier. 60%+ of buyers want skincare benefits in makeup.",
            "content": "Shade swatches, wear tests, dupe reveals, GRWM, before/after",
            "tags": "#MakeupTok #LipOil #BeautyFinds #MakeupDupe #PressOnNails",
        },
        "Health & Wellness": {
            "icon": "#3", "price": "$15-$50", "audience": "Health-conscious 20-40",
            "why": "MaryRuth's Liquid Multivitamin has sold 500K+ units. Liquid supplements, greens powders, and probiotics thrive in morning routine content.",
            "content": "Morning routines, supplement reviews, health journey updates, what-I-eat-in-a-day",
            "tags": "#WellnessTok #HealthTok #Supplements #MorningRoutine",
        },
        "Tech & Gadgets": {
            "icon": "#4", "price": "$10-$50", "audience": "Gen Z & Millennials",
            "why": "Smart posture correctors grew 217% YoY. Galaxy projectors, UV-C sanitizers, and magnetic chargers convert well because they have visual 'wow factor' on camera.",
            "content": "Unboxing, side-by-side comparisons, desk setup/reset videos, room makeovers",
            "tags": "#TechTok #GalaxyProjector #GadgetFinds #DeskSetup",
        },
        "Fashion Accessories": {
            "icon": "#5", "price": "$8-$40", "audience": "Women 16-35",
            "why": "Accessories outperform full apparel (no sizing issues, fewer returns). Crossbody bags, minimalist jewelry, and claw clips are top sellers.",
            "content": "OOTD, styling tips, haul videos, accessory try-ons",
            "tags": "#FashionTok #OOTD #JewelryTok #AccessoryHaul",
        },
        "Home & Organization": {
            "icon": "#6", "price": "$8-$40", "audience": "Women 22-40",
            "why": "#CleanTok transformations sell cleaning products instantly. Candles, kitchen gadgets, and rental-friendly decor are trending for room makeover content.",
            "content": "Before/after room makeovers, organization hacks, cleaning routines, kitchen hacks",
            "tags": "#CleanTok #HomeOrganization #RoomMakeover #KitchenHacks",
        },
        "Fragrance": {
            "icon": "#7", "price": "$10-$60", "audience": "Gen Z fragrance collectors",
            "why": "Perfume dupe culture and scent layering exploded on TikTok. 'Smell like money' content generates hundreds of millions of views.",
            "content": "Scent layering tutorials, blind buys, dupe reveals, compliment getters",
            "tags": "#PerfumeTok #FragranceTok #ScentLayering #PerfumeDupe",
        },
        "Hair Care": {
            "icon": "#8", "price": "$10-$40", "audience": "Women 18-40",
            "why": "Hair transformation content is highly shareable. Hair oils, growth serums, and silk bonnets are consistent sellers.",
            "content": "Hair transformations, growth journeys, styling tutorials, product comparisons",
            "tags": "#HairTok #HairGrowth #HairCare #SilkBonnet",
        },
        "Pet Products": {
            "icon": "#9", "price": "$8-$35", "audience": "Pet owners 18-45",
            "why": "#PetTok is among the most engaging communities. Products that make pets react or look cute drive impulse purchases from devoted pet parents.",
            "content": "Pet reactions, unboxing with pets, outfit try-ons, pet care routines",
            "tags": "#PetTok #DogTok #CatTok #PetFinds",
        },
        "Body Care": {
            "icon": "#10", "price": "$8-$30", "audience": "Women 18-35",
            "why": "Extension of the skincare obsession. Body scrubs, butters, and self-tanners thrive in 'shower routine' and 'self-care night' content.",
            "content": "Shower routines, self-care nights, body care layering, product reviews",
            "tags": "#BodyCare #ShowerRoutine #SelfCare #GlowUp",
        },
    }

    for item in rankings[:10]:
        cat = item["category"]
        brief = category_briefs.get(cat, {})

        lines.append(f"### {item['rank']}. {cat}")
        lines.append("")
        lines.append(f"**Confidence:** {'=' * min(item['source_count'], 10)} ({item['source_count']} sources, {item['total_mentions']} mentions)")
        lines.append("")

        if brief:
            lines.append(f"> {brief.get('why', '')}")
            lines.append("")
            lines.append(f"- **Price range:** {brief.get('price', 'N/A')}")
            lines.append(f"- **Target audience:** {brief.get('audience', 'N/A')}")
            lines.append(f"- **Best content format:** {brief.get('content', 'N/A')}")
            lines.append(f"- **Hashtags:** {brief.get('tags', 'N/A')}")
        lines.append("")

        # Top keywords table
        kws = item.get("top_keywords", [])[:6]
        if kws:
            lines.append("| Trending Keyword | Buzz Score |")
            lines.append("|-----------------|-----------|")
            for kw in kws:
                bar = "+" * min(kw["count"], 20)
                lines.append(f"| {kw['keyword']} | {bar} ({kw['count']}) |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # ===== SPECIFIC VIRAL PRODUCTS =====
    lines.append("## Viral Products Right Now")
    lines.append("")
    lines.append("These are specific products blowing up on TikTok Shop this week:")
    lines.append("")

    for p in products:
        sold = p.get("units_sold_tiktok", "N/A")
        lines.append(f"### {p['product']}")
        lines.append(f"- **Category:** {p['category']}")
        lines.append(f"- **Price:** {p['price']}")
        lines.append(f"- **TikTok Sales:** {sold}")
        lines.append(f"- **Why it's viral:** {p.get('why_viral', 'N/A')}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ===== HASHTAG PULSE =====
    lines.append("## Hashtag Pulse Check")
    lines.append("")
    lines.append("| Hashtag | Status |")
    lines.append("|---------|--------|")
    for h in hashtags:
        lines.append(f"| {h['hashtag']} | {h['status']} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ===== TOP BRANDS =====
    lines.append("## Hot Brands on TikTok Right Now")
    lines.append("")
    lines.append(", ".join(f"**{b}**" for b in brands))
    lines.append("")
    lines.append("---")
    lines.append("")

    # ===== KEY INSIGHTS =====
    lines.append("## Key Insights & Strategy Tips")
    lines.append("")
    lines.append(f"1. **Price sweet spot:** {insights.get('sweet_spot_price', '$10-$30')} — low hesitation = fast checkout")
    lines.append(f"2. **Creator strategy:** {insights.get('strategy_2026', 'N/A')}")
    lines.append(f"3. **Content that converts:** {insights.get('content_that_converts', 'N/A')}")
    lines.append(f"4. **Key aesthetics:** {insights.get('key_aesthetics', 'N/A')}")
    lines.append(f"5. **Beauty mega-trend:** {insights.get('beauty_trend_shift', 'N/A')}")
    lines.append(f"6. **Emerging trend:** {insights.get('emerging_trend', 'N/A')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ===== SOURCES =====
    lines.append("## Sources")
    lines.append("")
    for s in sources.get("source_sites", []):
        lines.append(f"- [{s['name']}]({s['url']})")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated automatically on {datetime.now().strftime('%Y-%m-%d at %H:%M')} UTC*")
    lines.append(f"*Next update: {date_str} + 2 days*")

    return "\n".join(lines)


def generate_json_summary(data, date_str):
    """Clean JSON summary."""
    return {
        "report_date": date_str,
        "region": "US",
        "generated_at": datetime.now().isoformat(),
        "market_insights": data.get("market_insights", {}),
        "top_10_categories": data.get("product_rankings", [])[:10],
        "viral_products": data.get("specific_products", []),
        "hashtag_pulse": data.get("hashtag_data", []),
        "top_brands": data.get("top_brands_mentioned", []),
    }


def generate_csv(data, date_str):
    """CSV export."""
    rows = []
    for item in data.get("product_rankings", [])[:10]:
        top_kws = ", ".join(kw["keyword"] for kw in item.get("top_keywords", [])[:5])
        rows.append({
            "Rank": item["rank"],
            "Category": item["category"],
            "Mentions": item["total_mentions"],
            "Sources": item["source_count"],
            "Confidence": item.get("confidence", "N/A"),
            "Top Keywords": top_kws,
            "Date": date_str,
        })
    return rows


def generate_products_csv(data, date_str):
    """CSV of specific viral products."""
    rows = []
    for p in data.get("specific_products", []):
        rows.append({
            "Product": p["product"],
            "Category": p["category"],
            "Price": p["price"],
            "TikTok Sales": p.get("units_sold_tiktok", "N/A"),
            "Why Viral": p.get("why_viral", ""),
            "Date": date_str,
        })
    return rows


def run(target_date=None):
    seed_file = find_seed(target_date)
    if not seed_file:
        print("ERROR: No seed data found. Run the collection agent first.")
        sys.exit(1)

    with open(seed_file) as f:
        data = json.load(f)

    date_str = target_date or datetime.now().strftime("%Y-%m-%d")
    report_dir = DATA_REPORTS / date_str
    report_dir.mkdir(parents=True, exist_ok=True)

    # 1. Markdown
    md = generate_markdown(data, date_str)
    (report_dir / "trending-products-report.md").write_text(md)
    print(f"  OK  Markdown: {report_dir}/trending-products-report.md")

    # 2. JSON summary
    js = generate_json_summary(data, date_str)
    (report_dir / "trending-products-summary.json").write_text(json.dumps(js, indent=2))
    print(f"  OK  JSON: {report_dir}/trending-products-summary.json")

    # 3. Categories CSV
    cats = generate_csv(data, date_str)
    if cats:
        with open(report_dir / "trending-categories.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cats[0].keys())
            w.writeheader()
            w.writerows(cats)
    print(f"  OK  Categories CSV: {report_dir}/trending-categories.csv")

    # 4. Products CSV
    prods = generate_products_csv(data, date_str)
    if prods:
        with open(report_dir / "viral-products.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=prods[0].keys())
            w.writeheader()
            w.writerows(prods)
    print(f"  OK  Products CSV: {report_dir}/viral-products.csv")

    # 5. Latest copies
    (DATA_REPORTS / "LATEST-REPORT.md").write_text(md)
    (DATA_REPORTS / "latest-summary.json").write_text(json.dumps(js, indent=2))
    print(f"  OK  Latest report: {DATA_REPORTS}/LATEST-REPORT.md")

    print(f"\nAll reports saved to: {report_dir}/")
    return report_dir


if __name__ == "__main__":
    target = None
    if len(sys.argv) > 2 and sys.argv[1] == "--date":
        target = sys.argv[2]
    run(target)
