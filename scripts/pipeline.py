#!/usr/bin/env python3
"""Full pipeline: scrape trending → generate post → update site."""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
POSTS_DIR = ROOT / "posts"
DATA_DIR.mkdir(exist_ok=True)
POSTS_DIR.mkdir(exist_ok=True)


def step(msg: str):
    print(f"\n{'='*50}\n  {msg}\n{'='*50}", flush=True)


def run_script(name: str, *args) -> str:
    import subprocess
    script = ROOT / "scripts" / name
    cmd = [sys.executable, str(script)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}", file=sys.stderr)
        raise RuntimeError(f"{name} failed with code {result.returncode}")
    return result.stdout


def main():
    period = sys.argv[1] if len(sys.argv) > 1 else "daily"

    # 1. Scrape
    step(f"Step 1/4: Scraping GitHub Trending ({period})...")
    raw = run_script("scrape.py", period)
    data = json.loads(raw)
    date_str = data["date"]
    print(f"  Got {len(data['repositories'])} repos")

    # Save raw data
    data_file = DATA_DIR / f"trending-{date_str}.json"
    data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"  Saved to {data_file}")

    # 2. Generate post
    step("Step 2/4: Generating blog post...")
    post_md = run_script("generate.py", str(data_file))
    print(f"  Generated {len(post_md)} chars")

    # Add YAML frontmatter
    top_repo = data["repositories"][0] if data["repositories"] else {"owner": "?", "name": "?"}
    frontmatter = f"""---
date: {date_str}
period: {period}
top_repo: {top_repo['owner']}/{top_repo['name']}
repo_count: {len(data['repositories'])}
---
"""
    full_md = frontmatter + "\n" + post_md

    post_file = POSTS_DIR / f"{date_str}.md"
    post_file.write_text(full_md)
    print(f"  Saved to {post_file}")

    # 3. Build site
    step("Step 3/4: Building static site...")
    run_script("build_site.py")
    print("  Site rebuilt!")

    # 4. Summary
    step("Pipeline complete!")
    top3 = data["repositories"][:3]
    for i, r in enumerate(top3, 1):
        print(f"  {i}. {r['owner']}/{r['name']} (+{r['stars_today']:,}⭐ today)")
    print(f"\n  Post: {post_file}")
    print(f"  Data: {data_file}")


if __name__ == "__main__":
    main()
