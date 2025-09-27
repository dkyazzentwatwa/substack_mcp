# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Environment setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

# Local development servers
python scripts/run_server.py --port 8080 --publication littlehakr  # FastAPI server
./run_mcp_with_venv.sh                                             # MCP server for Claude Desktop

# Testing
pytest                              # Run all tests
pytest tests/test_analysis.py       # Specific test module

# Deployment
railway up                          # Deploy to Railway
railway logs                        # Monitor deployment logs
```

## Architecture Overview

This is a **Substack MCP (Model Context Protocol) Server** that scrapes public Substack content and provides analytics through both FastAPI REST endpoints and MCP protocol integration.

### Core Components

1. **SubstackPublicClient** (`client.py`) - HTTP wrapper with rate limiting (1 second throttle) and TTL caching (15 minutes)

2. **Data Models** (`models.py`) - Pydantic schemas: `PostSummary`, `PostContent`, `AuthorProfile`, `Note`, `ContentAnalytics`

3. **Content Parsers** (`parsers.py`) - RSS/Atom feed parsing and HTML content extraction using BeautifulSoup

4. **Analytics Engine** (`analysis.py`) - VADER sentiment analysis, Flesch Reading Ease, keyword extraction (TF-IDF), publishing cadence

5. **Server Implementation** (`server.py`) - FastAPI app with both REST endpoints and MCP JSON-RPC 2.0 protocol

### MCP Protocol Integration

The server implements dual endpoints:
- REST API endpoints (`/publications/{handle}/posts`, `/posts`, `/analytics`, etc.)
- MCP JSON-RPC endpoint at `/mcp` and `/` (root) for ChatGPT compatibility

**MCP Tools Available:**
- `get_posts` - Fetch recent posts from a publication
- `get_post_content` - Full content of specific posts
- `search` - Search within publications (required for ChatGPT)

**Critical MCP Implementation Details:**
- Root middleware detects MCP vs HTTP requests by content-type
- JSON-RPC 2.0 protocol with proper error codes (-32601, -32602, -32603)
- MCP SDK locked to version 1.10.0 due to CallToolResult serialization bug
- Custom `create_text_result()` workaround for MCP SDK issues

### Environment Configuration

```bash
# Required for production
SUBSTACK_MCP_THROTTLE=1.0          # Request throttling seconds
SUBSTACK_MCP_CACHE_TTL=900         # Cache TTL seconds
SUBSTACK_MCP_WARM_PUBLICATION      # Publication to warm cache on startup
```

### Deployment Architecture

**Railway Configuration:**
- `Procfile`: `web: uvicorn substack_mcp.server:app --host 0.0.0.0 --port ${PORT:-8000}`
- `nixpacks.toml`: Nixpacks build override
- `runtime.txt`: Python 3.11.9
- Health check endpoint: `/health`

**Package Structure:**
- Source code in `src/substack_mcp/` with setuptools configuration in `pyproject.toml`
- Editable install with `-e .` in `requirements.txt`

### Key Implementation Patterns

**Error Handling:**
- HTTP status errors mapped to appropriate MCP error responses
- Graceful degradation when content unavailable
- Thread-safe caching with RLock

**Rate Limiting & Caching:**
- 1-second throttle between requests to respect Substack ToS
- TTL-based in-memory cache (15 minutes default)
- Public content only, no authentication bypass

**Data Flow:**
1. MCP request → JSON-RPC parsing → Tool handler
2. Tool handler → SubstackPublicClient → HTTP request (throttled)
3. HTTP response → Parser → Pydantic model → Analytics (optional)
4. Result → MCP response format → Client

### Testing Strategy

- Unit tests with `pytest` and `pytest-asyncio`
- HTTP mocking with `respx` to avoid live network calls
- Sample fixtures for HTML/RSS content
- Manual testing recipes in `scripts/examples.http`

### Known Issues & Workarounds

1. **MCP SDK Bug**: Locked to version 1.10.0 due to CallToolResult serialization issues
2. **Field Mapping**: Fixed Pydantic field mismatches (`published` → `published_at`)
3. **JSON Schema**: Removed unsupported `default` properties from MCP tool schemas
4. **ChatGPT Integration**: Root endpoint (`/`) required for ChatGPT custom connector discovery