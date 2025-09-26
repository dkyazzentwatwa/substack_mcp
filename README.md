# Substack MCP (Read-Only)

A Model Context Protocol (MCP) compliant server that scrapes, normalises, and analyses public Substack content.  
The initial focus is **read-only intelligence** across publications such as
`https://littlehakr.substack.com`:

- Crawl RSS feeds, post pages, author profiles, and notes without cookies.  
- Normalise the scraped payloads into typed data models for downstream tools.  
- Run lightweight analytics (readability, keyword extraction, sentiment, cadence).  
- Serve everything through an MCP server (FastAPI) with a queue-friendly design.

> ⚠️ Respect Substack's Terms of Service and `robots.txt`. Add throttling when running
automated crawls.

## Project layout

```
pyproject.toml
src/substack_mcp/
    __init__.py
    client.py          # HTTP wrapper + content fetchers
    models.py          # Pydantic schemas for posts, authors, notes, analytics
    parsers.py         # Feed + HTML parsing utilities
    analysis.py        # Text analytics helpers
    cache.py           # Simple time-aware caching layer
    server.py          # FastAPI MCP server definition
    settings.py        # Runtime configuration & throttling helpers
scripts/
    run_server.py      # Convenience entrypoint for local dev
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/run_server.py --publication littlehakr --port 8080
```

Example MCP calls once the server is running:

- `GET /health` – heartbeat + upstream scrape status.
- `GET /publications/littlehakr/posts?limit=5` – recent posts from RSS/HTML.
- `GET /posts?url=https://littlehakr.substack.com/p/example` – full post + analytics.
- `GET /authors/littlehakr/profile` – author bio + publication stats.
- `GET /notes/littlehakr` – most recent public notes (best-effort; falls back to RSS if available).

See `scripts/examples.http` for ready-to-run HTTPie recipes.

## Analytics surface area

- Word / sentence / paragraph metrics
- Flesch Reading Ease + grade level (approximate syllable estimator)
- Keyword extraction (TF and TF-IDF proxies with stopword filtering)
- Named entity sniffing via heuristic capitalised phrases (keeps dependencies light)
- Sentiment using VADER (rule-based, license-friendly)
- Publishing cadence (rolling average days between posts)

Extend `analysis.py` to plug in heavier ML/NLP models when you are ready.

## Railway deployment

This repository includes everything needed to deploy the FastAPI server on [Railway](https://railway.app/):

- `Procfile` starts `uvicorn` with the correct host/port bindings for Railway's runtime.
- `runtime.txt` pins Python 3.11 for consistent builds.
- `railway.toml` defines a single web process, healthcheck at `/health`, and restarts on failure.
- `requirements.txt` delegates dependency installation to `pip install -e .` so project metadata stays in sync.

To launch a new service:

1. Install the Railway CLI and authenticate: `npm i -g @railway/cli && railway login`.
2. Run `railway up` from the repository root; Railway detects the Python service and builds it via Nixpacks.
3. After the first deploy, set any optional env vars (for example `SUBSTACK_MCP_THROTTLE`, `SUBSTACK_MCP_CACHE_TTL`, or `SUBSTACK_MCP_WARM_PUBLICATION`) in the Railway dashboard.
4. Visit the generated URL and hit `/health` to confirm the server is running; other endpoints behave the same as the local quick-start commands above.

The `scripts/run_server.py` entrypoint now respects `HOST`, `PORT`, and `LOG_LEVEL` env vars, matching Railway's runtime defaults.

## Offline development

Network access is restricted in this environment. The code is organised so that:

- Parsers work against stored fixtures (see `tests/fixtures`).
- HTTP calls pass through an injectable transport. In tests you can use [`respx`](https://lundberg.github.io/respx/)
  to stub Substack endpoints.

To add a new publication, drop a HAR/HTML sample into `tests/fixtures` and add a parser
case so regressions surface quickly.

## Roadmap

1. Implement persistent storage (SQLite) for scraped artefacts.
2. Add background worker (RQ/Celery) for scheduled crawls.
3. Integrate summarisation + topic modelling.
4. Support authenticated actions once terms & automation policy are reviewed.
