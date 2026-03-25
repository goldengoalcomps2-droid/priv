#!/usr/bin/env python3
"""
TikTok Trends Data Collector
=============================
This script is called by the Claude scheduled agent to seed data
collected via WebSearch into the pipeline's raw data format.

The Claude agent gathers data using WebSearch, then calls this script
to save it and generate reports.

Usage:
    python3 collect_data.py --seed '{"products": [...]}'
    python3 collect_data.py --seed-file /path/to/data.json
"""

import json
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_REPORTS = PROJECT_ROOT / "data" / "reports"

for d in [DATA_RAW, DATA_REPORTS]:
    d.mkdir(parents=True, exist_ok=True)


def seed_data(data_dict):
    """Save externally collected data into the pipeline format."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now(timezone.utc).isoformat()

    # Wrap in pipeline format
    pipeline_data = {
        "scrape_id": hashlib.md5(timestamp.encode()).hexdigest()[:12],
        "timestamp": timestamp,
        "date": date_str,
        "region": "US",
        "collection_method": "websearch_agent",
        "sources": data_dict.get("sources", {}),
        "product_rankings": data_dict.get("product_rankings", []),
        "specific_products": data_dict.get("specific_products", []),
        "market_insights": data_dict.get("market_insights", {}),
        "hashtag_data": data_dict.get("hashtag_data", []),
    }

    # Save raw
    raw_file = DATA_RAW / f"scrape_{date_str}.json"
    with open(raw_file, "w") as f:
        json.dump(pipeline_data, f, indent=2)
    print(f"Raw data saved: {raw_file}")

    # Save enriched
    enriched_file = DATA_RAW / f"scrape_{date_str}_enriched.json"
    with open(enriched_file, "w") as f:
        json.dump(pipeline_data, f, indent=2)
    print(f"Enriched data saved: {enriched_file}")

    return pipeline_data


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--seed":
        data = json.loads(sys.argv[2])
        seed_data(data)
    elif len(sys.argv) > 2 and sys.argv[1] == "--seed-file":
        with open(sys.argv[2]) as f:
            data = json.load(f)
        seed_data(data)
    else:
        print("Usage: python3 collect_data.py --seed-file /path/to/data.json")
        sys.exit(1)
