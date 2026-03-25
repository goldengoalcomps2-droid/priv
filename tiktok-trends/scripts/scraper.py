#!/usr/bin/env python3
"""
TikTok Trending Products Scraper
================================
Scrapes multiple public sources for TikTok trending product data in the US.
Sources: Web search aggregation, TikTok Creative Center public pages,
         trend analytics sites, and social listening data.

Usage:
    python3 scraper.py                  # Run full scrape
    python3 scraper.py --source web     # Web search only
    python3 scraper.py --source pages   # Public trend pages only
"""

import json
import os
import sys
import re
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import quote_plus
from html.parser import HTMLParser

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_REPORTS = PROJECT_ROOT / "data" / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure dirs exist
for d in [DATA_RAW, DATA_REPORTS, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class SimpleHTMLTextExtractor(HTMLParser):
    """Extract visible text from HTML."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._skip = False
        self._skip_tags = {"script", "style", "noscript", "header", "nav", "footer"}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self.text_parts.append(text)

    def get_text(self):
        return "\n".join(self.text_parts)


def fetch_url(url, retries=3, timeout=15):
    """Fetch a URL with retries and user-agent spoofing."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = Request(url, headers=headers)
    for attempt in range(retries):
        try:
            with urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                encoding = resp.headers.get_content_charset() or "utf-8"
                return data.decode(encoding, errors="replace")
        except (URLError, HTTPError, TimeoutError) as e:
            log(f"  Attempt {attempt+1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def extract_text(html):
    """Extract visible text from HTML."""
    parser = SimpleHTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


def log(msg):
    """Log to file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    log_file = LOGS_DIR / f"scraper_{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_file, "a") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------
# Source 1: Public trend/analytics pages
# ---------------------------------------------------------------------------
TREND_PAGES = [
    {
        "name": "Shopify TikTok Products",
        "url": "https://www.shopify.com/blog/tiktok-products",
        "type": "blog",
    },
    {
        "name": "Printify TikTok Trending",
        "url": "https://printify.com/blog/tiktok-trending-products/",
        "type": "blog",
    },
    {
        "name": "LitCommerce Viral TikTok Products",
        "url": "https://litcommerce.com/blog/viral-tiktok-products-to-sell/",
        "type": "blog",
    },
    {
        "name": "Accio TikTok Hot Selling",
        "url": "https://www.accio.com/business/tiktok-hot-selling-2026",
        "type": "blog",
    },
    {
        "name": "Darkroom Agency TikTok Products",
        "url": "https://www.darkroomagency.com/observatory/the-best-tiktok-products-to-sell-in-2026-what-actually-works-on-tiktok-shop",
        "type": "blog",
    },
    {
        "name": "FindNiche TikTok Shop Products",
        "url": "https://findniche.com/blog/best-tiktok-shop-products-to-sell-in-2025-with-trends-data-real-examples",
        "type": "blog",
    },
    {
        "name": "QuickSync TikTok Shop Trending",
        "url": "https://quicksync.pro/blog/tiktok-shop-trending-products-2026/",
        "type": "blog",
    },
]


def scrape_trend_pages():
    """Scrape public trend pages for product mentions."""
    log("--- Scraping public trend pages ---")
    results = []

    for page in TREND_PAGES:
        log(f"  Fetching: {page['name']}")
        html = fetch_url(page["url"])
        if not html:
            log(f"  FAILED: {page['name']}")
            continue

        text = extract_text(html)
        # Extract product-related sections (keep first 5000 chars of relevant text)
        relevant = extract_product_mentions(text)
        results.append({
            "source": page["name"],
            "url": page["url"],
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "content_preview": text[:3000],
            "product_mentions": relevant,
        })
        log(f"  OK: {page['name']} - found {len(relevant)} product mentions")
        time.sleep(1)  # Be polite

    return results


def extract_product_mentions(text):
    """Extract product names and categories from text using keyword matching."""
    # Common TikTok product categories and keywords
    product_keywords = {
        "Skincare": ["skincare", "serum", "moisturizer", "cleanser", "spf", "sunscreen",
                      "retinol", "hyaluronic", "niacinamide", "face mask", "sheet mask",
                      "collagen", "vitamin c serum", "toner", "exfoliant"],
        "Makeup": ["lip oil", "lip gloss", "lip tint", "mascara", "foundation",
                   "concealer", "blush", "bronzer", "eyeshadow", "makeup", "primer",
                   "setting spray", "lip liner", "beauty blender"],
        "Hair Care": ["hair oil", "hair mask", "shampoo", "conditioner", "hair growth",
                      "hair serum", "scalp", "hair clip", "claw clip", "silk bonnet"],
        "Fragrance": ["perfume", "fragrance", "cologne", "body mist", "scent",
                      "eau de toilette", "dupe fragrance"],
        "Tech & Gadgets": ["led light", "galaxy projector", "phone case", "earbuds",
                           "headphones", "magnetic charger", "ring light", "portable charger",
                           "wireless charger", "bluetooth speaker", "smart watch"],
        "Home & Organization": ["organizer", "storage", "cleaning", "kitchen gadget",
                                "ice maker", "tumbler", "water bottle", "candle",
                                "diffuser", "blanket", "pillow"],
        "Fashion": ["dress", "hoodie", "bodysuit", "leggings", "sneakers", "sunglasses",
                    "tote bag", "crossbody", "jewelry", "necklace", "earrings", "bracelet"],
        "Health & Wellness": ["supplement", "multivitamin", "protein", "probiotic",
                              "collagen powder", "greens powder", "gummy vitamin",
                              "electrolyte", "sleep aid", "melatonin"],
        "Pet Products": ["pet toy", "dog toy", "cat toy", "pet bed", "pet accessory",
                         "dog treat", "cat tree", "pet grooming"],
        "Body Care": ["body lotion", "body butter", "body scrub", "deodorant",
                      "body wash", "shaving", "self tan", "body oil"],
    }

    mentions = []
    text_lower = text.lower()

    for category, keywords in product_keywords.items():
        found_keywords = []
        for kw in keywords:
            # Count occurrences
            count = text_lower.count(kw)
            if count > 0:
                found_keywords.append({"keyword": kw, "mentions": count})

        if found_keywords:
            found_keywords.sort(key=lambda x: x["mentions"], reverse=True)
            mentions.append({
                "category": category,
                "keywords_found": found_keywords[:10],
                "total_mentions": sum(k["mentions"] for k in found_keywords),
            })

    mentions.sort(key=lambda x: x["total_mentions"], reverse=True)
    return mentions


# ---------------------------------------------------------------------------
# Source 2: TikTok Creative Center (public endpoints)
# ---------------------------------------------------------------------------
def scrape_tiktok_creative_center():
    """Try to pull data from TikTok's public creative center pages."""
    log("--- Scraping TikTok Creative Center ---")
    urls = [
        "https://ads.tiktok.com/business/creativecenter/inspiration/popular/pc/en",
        "https://ads.tiktok.com/business/creativecenter/pc/en",
    ]
    results = []
    for url in urls:
        html = fetch_url(url)
        if html:
            text = extract_text(html)
            results.append({
                "source": "TikTok Creative Center",
                "url": url,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "content_preview": text[:3000],
            })
            log(f"  OK: {url}")
        else:
            log(f"  FAILED: {url}")
        time.sleep(1)
    return results


# ---------------------------------------------------------------------------
# Source 3: Comment/engagement scraping from public embed pages
# ---------------------------------------------------------------------------
def scrape_trending_hashtags():
    """Scrape common TikTok product hashtag pages for insights."""
    log("--- Scraping trending hashtag insights ---")
    hashtags = [
        "TikTokMadeMeBuyIt", "TikTokShopFinds", "TikTokShop",
        "ViralProducts", "TikTokTrending", "AmazonFinds",
        "BeautyTok", "CleanTok", "SkinTok", "TechTok",
    ]

    results = []
    for tag in hashtags:
        # Use public tag pages
        url = f"https://www.tiktok.com/tag/{tag.lower()}"
        html = fetch_url(url)
        if html:
            text = extract_text(html)
            # Look for view counts, video counts
            view_match = re.findall(r'(\d+(?:\.\d+)?[MBK]?)\s*(?:views|video)', text, re.I)
            results.append({
                "hashtag": f"#{tag}",
                "url": url,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "metrics_found": view_match[:10] if view_match else [],
                "content_preview": text[:1500],
            })
            log(f"  OK: #{tag} - metrics: {view_match[:5]}")
        else:
            log(f"  FAILED: #{tag}")
        time.sleep(1.5)

    return results


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
def run_full_scrape():
    """Run all scrapers and save raw data."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    date_str = datetime.now().strftime("%Y-%m-%d")
    log(f"=== Starting full scrape: {timestamp} ===")

    all_data = {
        "scrape_id": hashlib.md5(timestamp.encode()).hexdigest()[:12],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "date": date_str,
        "region": "US",
        "sources": {},
    }

    # Run all scrapers
    all_data["sources"]["trend_pages"] = scrape_trend_pages()
    all_data["sources"]["creative_center"] = scrape_tiktok_creative_center()
    all_data["sources"]["hashtag_insights"] = scrape_trending_hashtags()

    # Save raw data
    raw_file = DATA_RAW / f"scrape_{date_str}.json"
    with open(raw_file, "w") as f:
        json.dump(all_data, f, indent=2, default=str)
    log(f"Raw data saved to: {raw_file}")

    # Generate consolidated product rankings
    rankings = generate_rankings(all_data)
    all_data["product_rankings"] = rankings

    # Save enriched data
    enriched_file = DATA_RAW / f"scrape_{date_str}_enriched.json"
    with open(enriched_file, "w") as f:
        json.dump(all_data, f, indent=2, default=str)
    log(f"Enriched data saved to: {enriched_file}")

    log(f"=== Scrape complete: {len(rankings)} product categories ranked ===")
    return all_data


def generate_rankings(data):
    """Aggregate all sources into a ranked product list."""
    category_scores = {}

    for page_data in data["sources"].get("trend_pages", []):
        for mention in page_data.get("product_mentions", []):
            cat = mention["category"]
            if cat not in category_scores:
                category_scores[cat] = {
                    "category": cat,
                    "total_mentions": 0,
                    "source_count": 0,
                    "top_keywords": {},
                }
            category_scores[cat]["total_mentions"] += mention["total_mentions"]
            category_scores[cat]["source_count"] += 1
            for kw in mention.get("keywords_found", []):
                k = kw["keyword"]
                category_scores[cat]["top_keywords"][k] = (
                    category_scores[cat]["top_keywords"].get(k, 0) + kw["mentions"]
                )

    # Sort and rank
    ranked = sorted(
        category_scores.values(),
        key=lambda x: (x["source_count"], x["total_mentions"]),
        reverse=True,
    )

    for i, item in enumerate(ranked):
        item["rank"] = i + 1
        # Sort keywords by frequency
        sorted_kws = sorted(item["top_keywords"].items(), key=lambda x: x[1], reverse=True)
        item["top_keywords"] = [{"keyword": k, "count": v} for k, v in sorted_kws[:10]]

    return ranked


if __name__ == "__main__":
    source_filter = None
    if len(sys.argv) > 2 and sys.argv[1] == "--source":
        source_filter = sys.argv[2]

    if source_filter == "web":
        data = {"sources": {"trend_pages": scrape_trend_pages()}}
        print(json.dumps(data, indent=2, default=str))
    elif source_filter == "pages":
        data = {"sources": {"creative_center": scrape_tiktok_creative_center()}}
        print(json.dumps(data, indent=2, default=str))
    else:
        run_full_scrape()
