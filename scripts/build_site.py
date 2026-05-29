#!/usr/bin/env python3
"""Build the static site from markdown posts."""

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
DATA_DIR = ROOT / "data"
SITE_TITLE = "GitHub Trending Comedy"
SITE_DESC = "Daily GitHub trending repos, roasted with love. What's hot on GitHub today, served with a side of sarcasm."


def parse_frontmatter(md: str) -> tuple[dict, str]:
    """Extract YAML-like frontmatter from markdown."""
    meta = {}
    body = md
    if md.startswith("---"):
        parts = md.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2]
    return meta, body.strip()


def md_to_html(md: str) -> str:
    """Simple markdown → HTML converter."""
    html = md

    # Headers
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold and italic
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', html)

    # Images
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', html)

    # Horizontal rules
    html = re.sub(r'^---+$', '<hr>', html, flags=re.MULTILINE)

    # Paragraphs: wrap blocks of text separated by blank lines
    paragraphs = []
    for block in html.split('\n\n'):
        block = block.strip()
        if not block:
            continue
        if block.startswith('<h') or block.startswith('<hr') or block.startswith('<ul') or block.startswith('<ol'):
            paragraphs.append(block)
        else:
            # Handle inline line breaks
            paragraphs.append(f'<p>{"<br>".join(block.split(chr(10)))}</p>')

    return '\n'.join(paragraphs)


def build_site():
    posts = []
    for f in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        content = f.read_text()
        meta, body = parse_frontmatter(content)
        meta["slug"] = f.stem
        meta["html"] = md_to_html(body)
        # Get first heading for title
        h1 = re.search(r'^# (.+)$', body, re.MULTILINE)
        meta["title"] = h1.group(1) if h1 else f"Trending — {f.stem}"
        posts.append(meta)

    # Build index page
    index_html = build_index(posts)
    (ROOT / "index.html").write_text(index_html)

    # Build individual post pages
    for post in posts:
        post_html = build_post_page(post)
        (ROOT / f"posts/{post['slug']}.html").write_text(post_html)

    # Build archive JSON for potential JS loading
    archive = []
    for p in posts:
        archive.append({
            "date": p.get("date", ""),
            "title": p.get("title", ""),
            "period": p.get("period", ""),
            "top_repo": p.get("top_repo", ""),
            "repo_count": p.get("repo_count", ""),
        })
    (ROOT / "data/archive.json").write_text(json.dumps(archive, indent=2))

    print(f"  Built {len(posts)} post pages + index")


def head(css_path: str = "style.css", title: str = None) -> str:
    t = f"{title} — {SITE_TITLE}" if title else SITE_TITLE
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t}</title>
<meta name="description" content="{SITE_DESC}">
<link rel="stylesheet" href="{css_path}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔥</text></svg>">
</head>
<body>
"""


def build_index(posts: list) -> str:
    html = head()
    html += """
<header class="site-header">
  <div class="container">
    <h1 class="site-title">🔥 GitHub Trending Comedy</h1>
    <p class="site-subtitle">What's hot on GitHub, roasted daily with love and sarcasm.</p>
  </div>
</header>
<main class="container">
  <div class="post-grid">
"""
    for p in posts:
        date_str = p.get("date", "???")
        top = p.get("top_repo", "???")
        count = p.get("repo_count", "?")
        title = p.get("title", "Untitled")

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            display_date = dt.strftime("%B %d, %Y")
        except:
            display_date = date_str

        html += f"""
    <a href="posts/{p['slug']}.html" class="post-card">
      <div class="post-card-date">{display_date}</div>
      <h2 class="post-card-title">{title}</h2>
      <div class="post-card-meta">
        <span>🏆 Top: {top}</span>
        <span>📦 {count} repos</span>
      </div>
    </a>"""

    html += """
  </div>
</main>
<footer class="site-footer">
  <div class="container">
    <p>Built with ❤️ and Python · Data from <a href="https://github.com/trending" target="_blank">GitHub Trending</a></p>
    <p>Updated daily. <a href="https://github.com" target="_blank">View on GitHub</a></p>
  </div>
</footer>
</body>
</html>"""
    return html


def build_post_page(post: dict) -> str:
    date_str = post.get("date", "")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        display_date = dt.strftime("%B %d, %Y")
    except:
        display_date = date_str

    html = head(css_path="../style.css", title=post.get("title", "Post"))
    html += f"""
<header class="site-header">
  <div class="container">
    <a href="../index.html" class="back-link">← Back to all posts</a>
    <div class="post-meta-header">
      <time>{display_date}</time>
      <span>· {post.get('period', 'daily')} trending</span>
    </div>
  </div>
</header>
<main class="container">
  <article class="post-content">
    {post['html']}
  </article>
  <nav class="post-nav">
    <a href="../index.html" class="back-link">← Back to all posts</a>
  </nav>
</main>
<footer class="site-footer">
  <div class="container">
    <p>🔥 GitHub Trending Comedy · Daily roasts since 2026</p>
  </div>
</footer>
</body>
</html>"""
    return html


if __name__ == "__main__":
    build_site()
