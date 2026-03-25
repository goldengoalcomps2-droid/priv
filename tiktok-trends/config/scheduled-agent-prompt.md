# Scheduled Agent Prompt — TikTok Trends Collector
# Run this with: /schedule every 2 days

## Task

You are the TikTok Trending Products data collector. Every 2 days, you gather fresh trend data and generate reports.

## Steps

### 1. Search for trending product data

Run these 3 web searches:
- "TikTok Shop top selling products US [current month] [current year] bestsellers"
- "TikTok viral products [year] skincare makeup trending what to sell"
- "TikTok Shop trending gadgets home products fashion accessories [year]"

### 2. Compile data into seed file

Save a JSON file to:
```
/home/user/priv/tiktok-trends/data/raw/seed_[YYYY-MM-DD].json
```

Use the exact same format as the existing seed files in that directory (product_rankings, specific_products, market_insights, hashtag_data, etc).

### 3. Generate reports

```bash
cd /home/user/priv/tiktok-trends/scripts
python3 generate_report_from_seed.py --date [YYYY-MM-DD]
```

### 4. Commit and push

```bash
cd /home/user/priv
git add tiktok-trends/
git commit -m "TikTok trends update: [YYYY-MM-DD]"
git push -u origin claude/trending-tiktok-products-lFuab
```
