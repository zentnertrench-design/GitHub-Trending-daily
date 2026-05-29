# 🔥 GitHub Trending Comedy

Daily GitHub trending repos, roasted with love and sarcasm.

A static blog that scrapes [GitHub Trending](https://github.com/trending) every day and writes a humorous post about what's hot. Powered by Python and LLM wit.

## How It Works

```
GitHub Trending → scrape.py → generate.py (LLM) → build_site.py → static HTML
```

- **`scripts/scrape.py`** — scrapes trending repos from GitHub
- **`scripts/generate.py`** — uses an LLM to write a funny blog post
- **`scripts/build_site.py`** — generates static HTML pages
- **`scripts/pipeline.py`** — orchestrates the full daily run

## Setup for GitHub Pages

1. Fork/clone this repo
2. Enable GitHub Pages in Settings → Pages:
   - Source: **Deploy from a branch**
   - Branch: `main` / `/(root)`
3. Set up secrets for LLM-powered posts:
   - `LLM_API_KEY` — your OpenAI-compatible API key
4. The daily workflow runs at 8 AM UTC

Without an LLM key, posts use a clean template format instead.

## Local Development

```bash
# Scrape trending
python scripts/scrape.py daily

# Full pipeline (scrape → generate → build)
python scripts/pipeline.py daily

# Open the site
open index.html
```

## Design

Clean, dark-themed, responsive. No frameworks — just handcrafted HTML and CSS. Inspired by modern dev tools like Linear and Vercel.

## License

MIT
