#!/usr/bin/env python3
"""
Generate humorous blog posts from GitHub trending data.

Uses an LLM API (OpenAI-compatible) to craft witty posts.
Configure with:
  LLM_API_KEY - API key (required)
  LLM_API_BASE - API base URL (default: https://api.openai.com/v1)
  LLM_MODEL   - Model name (default: gpt-4o-mini)
"""

import sys
import json
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError

API_KEY = os.environ.get("LLM_API_KEY", "")
API_BASE = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are "TrendComedyBot", a witty tech blogger who writes about GitHub trending repositories.

Your style:
- Start with a catchy, funny headline
- Use dry humor, tech puns, and sarcasm
- You're wryly amused by the tech world's obsessions
- Each repo gets 1-2 witty paragraphs
- End with a humorous "TL;DR" section ranking the repos by absurdity/impact
- Write in English, keep it snappy
- Format in Markdown

IMPORTANT: Output ONLY the blog post content. No meta-commentary, no "here's your post", just the article."""


def generate_post(trending_data: dict) -> str:
    repos = trending_data["repositories"][:10]
    date_str = trending_data["date"]

    # Build a digestible summary for the LLM
    repo_summaries = []
    for i, r in enumerate(repos, 1):
        total = r.get("total_stars", 0)
        today = r.get("stars_today", 0)
        total_str = f"{total:,}" if total else "?"
        topics = ", ".join(r.get("topics", [])[:3])
        repo_summaries.append(
            f"{i}. **{r['owner']}/{r['name']}** ({r['language'] or 'N/A'})\n"
            f"   {r['description']}\n"
            f"   ⭐ {total_str} total | +{today:,} today"
            + (f" | topics: {topics}" if topics else "")
        )

    user_prompt = f"""Date: {date_str}

Here are today's top 10 trending GitHub repositories:

{chr(10).join(repo_summaries)}

Write a hilarious, insightful blog post about these trending repos. Make tech people laugh and nod."""

    if not API_KEY:
        return _fallback_post(trending_data)

    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.9,
        "max_tokens": 2500,
    }

    try:
        req = Request(
            f"{API_BASE}/chat/completions",
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
        content = result["choices"][0]["message"]["content"]
        return content.strip()
    except HTTPError as e:
        err_body = e.read().decode()[:500]
        sys.stderr.write(f"LLM API error: {e.code} {err_body}\n")
        return _fallback_post(trending_data)
    except Exception as e:
        sys.stderr.write(f"LLM error: {e}\n")
        return _fallback_post(trending_data)


def _fallback_post(trending_data: dict) -> str:
    """Generate a simple post without LLM when API is unavailable."""
    date = trending_data["date"]
    repos = trending_data["repositories"][:10]

    lines = [f"# 🔥 GitHub Trending — {date}", ""]
    lines.append("*No LLM? No problem. Here's what's hot today, straight from the scraping trenches.*")
    lines.append("")

    for i, r in enumerate(repos, 1):
        lines.append(f"## {i}. [{r['owner']}/{r['name']}]({r['url']})")
        lines.append("")
        lines.append(f"**{r['description']}**")
        lines.append("")
        lang = r['language'] or "Unknown"
        today = r['stars_today']
        lines.append(f"📝 {lang} | ⭐ +{today:,} today")
        lines.append("")

    lines.append("---")
    lines.append(f"*Auto-generated on {date}. Set `LLM_API_KEY` for AI-powered humor!*")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2 and sys.stdin.isatty():
        sys.stderr.write("Usage: generate.py <trending.json>\n")
        sys.exit(1)

    input_file = sys.argv[1] if len(sys.argv) > 1 else None
    if input_file:
        with open(input_file) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    post = generate_post(data)
    print(post)


if __name__ == "__main__":
    main()
