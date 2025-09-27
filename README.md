# Substack MCP Server - User Guide & Reference

A powerful Model Context Protocol (MCP) server that transforms how you research and analyze Substack content. Unlike traditional search engines or AI assistants, this tool provides **deep, structured access** to Substack publications with real-time content analysis.

## Why Use This Instead of Google Search or Standard AI?

### 🎯 **Precision Over Breadth**
- **Google/Web Search**: Returns scattered results across the entire web
- **Standard AI**: Limited to training data cutoffs and general knowledge
- **Substack MCP**: Provides real-time, comprehensive access to specific Substack publications with structured data

### 📊 **Rich Analytics Built-In**
- **Traditional Search**: Just finds content
- **Substack MCP**: Automatically analyzes sentiment, readability, keywords, publishing patterns, and more

### 🔍 **Publication-Focused Research**
- **Web Search**: Fragmented results from multiple sources
- **Substack MCP**: Complete publication intelligence - posts, notes, author profiles, analytics, trends

### ⚡ **Real-Time & Comprehensive**
- **Static AI**: Knowledge cutoff limitations
- **Substack MCP**: Live data from publications as they publish new content

## Core Capabilities

- **Content Intelligence**: Crawl RSS feeds, posts, author profiles, and notes
- **Advanced Analytics**: Readability scores, sentiment analysis, keyword extraction, publishing cadence
- **Structured Access**: Normalized data models for downstream analysis
- **Real-Time Data**: Fresh content as it's published
- **Publication Insights**: Author analytics, publication trends, content patterns

> ⚠️ **Ethical Use**: Respects Substack's Terms of Service and robots.txt with built-in throttling for responsible crawling.

## 🚀 User Workflows & Use Cases

### **Research Workflows**

#### 📰 **Publication Analysis**
```
"Analyze the sentiment trends in Benedict Evans' recent posts about AI"
→ Fetch posts → Sentiment analysis → Trend identification → Insights
```

#### 🔍 **Competitive Intelligence**
```
"Compare publishing frequency between stratechery and platformer"
→ Multi-publication crawl → Publishing cadence analysis → Comparative insights
```

#### 📊 **Content Strategy Research**
```
"What topics are trending in fintech Substacks this month?"
→ Search multiple publications → Keyword extraction → Topic clustering → Trend analysis
```

#### 🎯 **Deep Dive Analysis**
```
"Get full content analysis of latest crypto regulation posts"
→ Fetch specific posts → Full text analysis → Readability + sentiment → Expert insights
```

### **ChatGPT Integration Workflows**

#### 🔗 **Custom Connector Setup**
1. Deploy to Railway (see deployment section)
2. Add as ChatGPT Custom Connector using your Railway URL
3. ChatGPT can now access live Substack data in conversations

#### 💬 **Example ChatGPT Prompts**
- *"Search for recent posts about 'AI regulation' in Benedict Evans' publication"*
- *"Fetch the latest post from stratechery and analyze its key arguments"*
- *"Compare the writing style complexity between two different Substack authors"*
- *"Get publishing patterns and content trends for platformer over the last month"*

### **Developer Integration Workflows**

#### 🛠 **API-First Access**
```bash
# Quick publication overview
GET /publications/stratechery/posts?limit=10

# Deep content analysis
GET /posts?url=https://stratechery.com/specific-post
GET /analytics?handle=stratechery&limit=5

# Author intelligence
GET /authors/stratechery/profile
```

#### 📈 **Custom Analytics Pipeline**
```python
# Integrate with your own tools
client = SubstackPublicClient()
posts = client.fetch_feed("your-target-publication", 20)
analytics = [analyse_post(client.fetch_post(p.url)) for p in posts]
# → Custom visualization, alerts, reporting
```

### **Business Intelligence Workflows**

#### 📋 **Content Monitoring**
- Track competitor publications for strategy insights
- Monitor industry thought leaders for trend identification
- Analyze content performance patterns across publications

#### 📊 **Market Research**
- Publication landscape analysis in specific industries
- Author influence and reach assessment
- Content strategy benchmarking

#### 🎯 **Lead Generation & Outreach**
- Identify high-engagement posts for partnership opportunities
- Find authors writing about relevant topics in your industry
- Track publication momentum and growth patterns

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

## 🏃 Quick Start

### **For ChatGPT Users (Recommended)**
1. Use the deployed version: `https://substackmcp-production.up.railway.app/`
2. Add as a ChatGPT Custom Connector
3. Start asking questions like: *"Search for AI posts in Benedict Evans' Substack"*

### **For Developers**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/run_server.py --publication littlehakr --port 8080
```

### **Essential API Endpoints**

#### 🔍 **Discovery & Search**
```bash
# Health check and server status
GET /health

# Search within a publication
GET /search?query=AI&handle=stratechery

# Fetch recent posts
GET /publications/stratechery/posts?limit=10

# Fetch specific post content
GET /posts?url=https://stratechery.com/2024/example-post
```

#### 📊 **Analytics & Intelligence**
```bash
# Content analytics with sentiment, readability, keywords
GET /analytics?handle=stratechery&limit=5

# Author profile and publication stats
GET /authors/stratechery/profile

# Recent notes and commentary
GET /notes/stratechery?limit=10

# Comprehensive publication crawl
GET /crawl/stratechery?post_limit=10&analyse=true
```

#### 🎯 **MCP Tools (for ChatGPT/Claude)**
- **search**: Find content across publications
- **fetch**: Get specific posts or publication feeds
- **get_posts**: Recent posts from a publication
- **get_post_content**: Full post analysis

### **Example Use Cases**

```bash
# Competitive analysis
curl "https://your-server.com/analytics?handle=platformer&limit=10"

# Content research
curl "https://your-server.com/search?query=crypto%20regulation&handle=stratechery"

# Author intelligence
curl "https://your-server.com/authors/benthompson/profile"

# Publication monitoring
curl "https://your-server.com/crawl/newsletter?post_limit=5&analyse=true"
```

See `scripts/examples.http` for ready-to-run HTTPie recipes and advanced examples.

## 🧠 Advanced Analytics Capabilities

### **Content Analysis**
- **Readability Metrics**: Flesch Reading Ease + Kincaid Grade Level
- **Sentiment Analysis**: VADER-based emotional tone detection (positive, negative, neutral, compound scores)
- **Keyword Intelligence**: TF-IDF extraction with stopword filtering
- **Structure Analysis**: Word/sentence/paragraph metrics and lexical diversity
- **Entity Detection**: Heuristic capitalized phrase identification

### **Publication Intelligence**
- **Publishing Cadence**: Rolling average days between posts
- **Content Trends**: Topic evolution and keyword trending over time
- **Author Patterns**: Writing style consistency and evolution
- **Engagement Signals**: Post length vs. publication frequency analysis

### **Competitive Advantages Over Traditional Tools**

| Feature | Google Search | Standard AI | Substack MCP |
|---------|---------------|-------------|--------------|
| **Real-time Data** | ❌ SEO-dependent | ❌ Training cutoff | ✅ Live content |
| **Publication Focus** | ❌ Scattered results | ❌ General knowledge | ✅ Deep publication intelligence |
| **Content Analytics** | ❌ Basic snippets | ❌ No analysis tools | ✅ Built-in sentiment, readability, keywords |
| **Structured Access** | ❌ Unstructured HTML | ❌ Text responses only | ✅ JSON APIs + MCP protocol |
| **Author Intelligence** | ❌ Limited bio info | ❌ Static profiles | ✅ Dynamic author analytics |
| **Trend Analysis** | ❌ Manual aggregation | ❌ No trend tools | ✅ Publishing patterns & content evolution |
| **API Integration** | ❌ Limited APIs | ❌ Chat-only | ✅ Full REST + MCP + ChatGPT Custom Connectors |

**Extend `analysis.py` to plug in heavier ML/NLP models when you are ready.**

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
