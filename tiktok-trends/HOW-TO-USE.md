# TikTok Trending Products Tracker

## What Is This?

An automated system that tracks the **top 10 trending products on TikTok in the US** every 2 days. It scrapes public data sources, ranks products, and generates easy-to-read reports.

---

## Quick Start (Find Your Reports)

### Where are my reports?

```
tiktok-trends/
├── data/
│   ├── reports/
│   │   ├── LATEST-REPORT.md        ← START HERE (always the newest report)
│   │   ├── latest-summary.json      ← Same data in JSON format
│   │   └── 2026-03-25/              ← Reports by date
│   │       ├── trending-products-report.md
│   │       ├── trending-products-summary.json
│   │       └── trending-products.csv
│   ├── raw/                          ← Raw scrape data (for nerds)
│   └── archive/                      ← Old data (auto-archived after 14 days)
├── scripts/                          ← The automation scripts
├── config/                           ← Settings
└── logs/                             ← Scrape logs
```

### Just want the highlights?
Open **`data/reports/LATEST-REPORT.md`** — it has everything in plain English.

### Want a spreadsheet?
Open **`data/reports/[date]/trending-products.csv`** in Excel or Google Sheets.

### Want raw data for code?
Use **`data/reports/latest-summary.json`** — clean JSON with all fields.

---

## What Each Report Tells You

For each of the Top 10 trending product categories, you get:

| Field | What It Means |
|-------|---------------|
| **Rank** | Position based on how many sources mention it |
| **Total Mentions** | How often this category appeared across all sources |
| **Price Range** | Typical selling price on TikTok Shop |
| **Target Audience** | Who's buying these products |
| **Why Trending** | Plain-English explanation of why it's hot |
| **Content Angle** | Best video format to sell this product |
| **Top Hashtags** | Hashtags to use in your content |
| **Top Keywords** | Specific product terms that are trending |

---

## Run It Manually

```bash
# Run the full pipeline (scrape + reports)
cd tiktok-trends/scripts
python3 run_pipeline.py

# Just scrape (no reports)
python3 scraper.py

# Just generate reports (from existing data)
python3 report_generator.py

# Generate report for a specific date
python3 report_generator.py --date 2026-03-25
```

---

## Schedule

Reports are automatically generated **every 2 days** via a scheduled Claude agent.

| Setting | Value |
|---------|-------|
| Frequency | Every 2 days |
| Start date | March 25, 2026 |
| Region | US |
| Sources | 7+ analytics sites, TikTok Creative Center, 10+ hashtag pages |

---

## How It Works (Behind the Scenes)

1. **Scrape** — Pulls data from 7+ trend analytics sites, TikTok Creative Center, and 10+ trending hashtag pages
2. **Extract** — Finds product mentions using keyword matching across 10 categories
3. **Rank** — Scores each category by mention count and source breadth
4. **Report** — Generates Markdown, JSON, and CSV reports
5. **Archive** — Old data is automatically moved to archive after 14 days
