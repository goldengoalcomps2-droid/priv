#!/usr/bin/env python3
"""
TikTok Trends Pipeline Runner
==============================
Runs the full pipeline: scrape → generate reports → archive old data.

This is the single entry point for both manual and scheduled runs.

Usage:
    python3 run_pipeline.py           # Run full pipeline
    python3 run_pipeline.py --quick   # Quick mode (fewer sources)
"""

import sys
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scraper import run_full_scrape, log
from report_generator import generate_all_reports

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_ARCHIVE = PROJECT_ROOT / "data" / "archive"
DATA_REPORTS = PROJECT_ROOT / "data" / "reports"


def archive_old_data(keep_days=14):
    """Move data older than keep_days to archive."""
    cutoff = datetime.now() - timedelta(days=keep_days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    archived = 0
    for f in DATA_RAW.glob("scrape_*.json"):
        # Extract date from filename
        try:
            file_date = f.stem.split("_")[1]  # scrape_2026-03-25 -> 2026-03-25
            if file_date < cutoff_str:
                dest = DATA_ARCHIVE / f.name
                shutil.move(str(f), str(dest))
                archived += 1
        except (IndexError, ValueError):
            continue

    if archived:
        log(f"Archived {archived} old data files (older than {keep_days} days)")


def run_pipeline():
    """Run the complete pipeline."""
    start = datetime.now()
    log("=" * 60)
    log("TIKTOK TRENDS PIPELINE - STARTING")
    log("=" * 60)

    # Step 1: Scrape
    log("\n[STEP 1/3] Running scrapers...")
    try:
        data = run_full_scrape()
        log(f"Scraping complete. {len(data.get('product_rankings', []))} categories ranked.")
    except Exception as e:
        log(f"ERROR in scraping: {e}")
        raise

    # Step 2: Generate reports
    log("\n[STEP 2/3] Generating reports...")
    try:
        report_dir = generate_all_reports()
        log(f"Reports generated at: {report_dir}")
    except Exception as e:
        log(f"ERROR in report generation: {e}")
        raise

    # Step 3: Archive old data
    log("\n[STEP 3/3] Archiving old data...")
    try:
        archive_old_data()
    except Exception as e:
        log(f"WARNING: Archive step failed: {e}")

    elapsed = (datetime.now() - start).total_seconds()
    log(f"\n{'=' * 60}")
    log(f"PIPELINE COMPLETE in {elapsed:.1f}s")
    log(f"{'=' * 60}")

    # Print a quick summary to stdout
    print("\n" + "=" * 50)
    print("📊 QUICK SUMMARY")
    print("=" * 50)
    rankings = data.get("product_rankings", [])
    for item in rankings[:10]:
        print(f"  #{item['rank']} {item['category']} ({item['total_mentions']} mentions)")
    print(f"\n📁 Full report: {DATA_REPORTS / 'LATEST-REPORT.md'}")
    print(f"📊 JSON data: {DATA_REPORTS / 'latest-summary.json'}")


if __name__ == "__main__":
    run_pipeline()
