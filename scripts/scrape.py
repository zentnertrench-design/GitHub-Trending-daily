#!/usr/bin/env python3
"""Scrape GitHub Trending page + enrich with GitHub API."""

import sys
import json
import os
import re
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from urllib.request import urlopen, Request

URLS = {
    "daily": "https://github.com/trending?since=daily",
    "weekly": "https://github.com/trending?since=weekly",
    "monthly": "https://github.com/trending?since=monthly",
}

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def api_request(url: str) -> Optional[Dict]:
    """Make a GitHub API request with optional auth."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_trending(url: str) -> str:
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; TrendingBot/1.0)",
        "Accept": "text/html",
    })
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_trending(html: str) -> List[Dict]:
    repos = []
    articles = re.split(r'<article\b[^>]*class="[^"]*Box-row[^"]*"[^>]*>', html)[1:]

    for art in articles:
        href_m = re.search(
            r'<a[^>]*href="(/([^/"]+)/([^/"]+))"[^>]*class="[^"]*Link[^"]*"', art
        )
        if not href_m:
            continue

        repo_path = href_m.group(1)
        owner = href_m.group(2)
        name = href_m.group(3)

        desc_m = re.search(r'<p\b[^>]*class="[^"]*col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', art, re.DOTALL)
        description = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip() if desc_m else ""

        lang_m = re.search(r'<span\b[^>]*itemprop="programmingLanguage"[^>]*>\s*([^<]*?)\s*</span>', art)
        language = lang_m.group(1).strip() if lang_m else ""

        today_m = re.search(r'(\d[\d,]*)\s+stars?\s+today\b', art)
        stars_today = int(today_m.group(1).replace(",", "")) if today_m else 0

        repos.append({
            "owner": owner,
            "name": name,
            "url": f"https://github.com{repo_path}",
            "description": description,
            "language": language,
            "stars_today": stars_today,
            "total_stars": 0,
            "forks": 0,
        })

    return repos


def enrich_with_api(repos: List[Dict]) -> None:
    """Fetch total stars and forks from GitHub API for each repo."""
    for r in repos:
        data = api_request(f"https://api.github.com/repos/{r['owner']}/{r['name']}")
        if data:
            r["total_stars"] = data.get("stargazers_count", 0)
            r["forks"] = data.get("forks_count", 0)
            r["topics"] = data.get("topics", [])
            r["created_at"] = data.get("created_at", "")


def main():
    since = sys.argv[1] if len(sys.argv) > 1 else "daily"
    url = URLS.get(since, URLS["daily"])

    sys.stderr.write(f"Fetching: {url}\n")
    html = fetch_trending(url)
    repos = parse_trending(html)
    sys.stderr.write(f"Parsed {len(repos)} repos\n")

    sys.stderr.write("Enriching with API...\n")
    enrich_with_api(repos)
    sys.stderr.write("Done!\n")

    result = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "period": since,
        "repositories": repos,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
