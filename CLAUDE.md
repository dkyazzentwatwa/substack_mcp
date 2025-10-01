# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Environment setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

# Testing
pytest                              # Run all tests
pytest tests/test_analysis.py       # Specific test module
pytest -v                           # Verbose output

# Testing the MCP server
./run_mcp_with_venv.sh             # Run MCP server for Claude Desktop
```

## Architecture Overview

This is a **Substack MCP (Model Context Protocol) Server** designed for use with Claude Code. It scrapes public Substack content and provides analytics through the MCP protocol.

### Core Components

1. **SubstackPublicClient** (`client.py`) - HTTP wrapper with rate limiting (1 second throttle) and TTL caching (15 minutes)

2. **Data Models** (`models.py`) - Pydantic schemas: `PostSummary`, `PostContent`, `AuthorProfile`, `Note`, `ContentAnalytics`

3. **Content Parsers** (`parsers.py`) - RSS/Atom feed parsing and HTML content extraction using BeautifulSoup

4. **Analytics Engine** (`analysis.py`) - VADER sentiment analysis, Flesch Reading Ease, keyword extraction (TF-IDF), publishing cadence

5. **MCP Server** (`server.py`) - MCP protocol implementation using stdio transport

### MCP Protocol Integration

The server implements the MCP protocol for Claude Desktop/Code integration:

**MCP Tools Available:**
- `get_posts` - Fetch recent posts from a publication
- `get_post_content` - Full content of specific posts
- `get_notes` - Fetch recent notes from a publication
- `get_author_profile` - Get author and publication information
- `analyze_post` - Sentiment and readability analysis
- `crawl_publication` - Comprehensive publication intelligence
- `search` - Search within publications

**Critical MCP Implementation Details:**
- MCP SDK locked to version 1.10.0 due to CallToolResult serialization bug in later versions
- Custom `create_text_result()` workaround returns plain dictionaries
- Stdio transport for Claude Desktop integration
- All tools return structured JSON responses

### Environment Configuration

```bash
# Optional configuration
SUBSTACK_MCP_THROTTLE=1.0          # Request throttling seconds (default: 1.0)
SUBSTACK_MCP_CACHE_TTL=900         # Cache TTL seconds (default: 900)
SUBSTACK_MCP_WARM_PUBLICATION      # Publication to warm cache on startup
```

### Package Structure

- Source code in `src/substack_mcp/` with setuptools configuration in `pyproject.toml`
- Editable install with `-e .` in `requirements.txt`
- MCP server wrapper script: `run_mcp_with_venv.sh`

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
1. MCP request → Tool handler
2. Tool handler → SubstackPublicClient → HTTP request (throttled)
3. HTTP response → Parser → Pydantic model → Analytics (optional)
4. Result → MCP response format → Claude Desktop/Code

### Testing Strategy

- Unit tests with `pytest` and `pytest-asyncio`
- HTTP mocking with `respx` to avoid live network calls
- Sample fixtures for HTML/RSS content in `tests/fixtures/`
- Test coverage for all MCP tools

### Known Issues & Workarounds

1. **MCP SDK Bug**: Locked to version 1.10.0 due to CallToolResult serialization issues in later versions
2. **Field Mapping**: Fixed Pydantic field mismatches (`published` → `published_at`)
3. **JSON Schema**: Removed unsupported `default` properties from MCP tool schemas
4. **Stdio Transport**: MCP server uses stdio, so manual testing will appear to "hang" waiting for input (this is normal)

## Code Organization

### Client Layer (`client.py`)
- `SubstackPublicClient` - Main HTTP client
- Rate limiting: 1 request per second
- TTL cache: 15 minutes default
- Methods: `fetch_feed()`, `fetch_post()`, `fetch_author_profile()`, `fetch_notes()`

### Models (`models.py`)
All Pydantic v2 models with proper validation:
- `PostSummary` - Basic post metadata
- `PostContent` - Full post content with body
- `AuthorProfile` - Author and publication info
- `Note` - Substack notes
- `ContentAnalytics` - Sentiment, readability, keywords
- `PublicationMetadata` - Publication-level data
- `CrawlResult` - Comprehensive crawl response

### Parsers (`parsers.py`)
- `parse_feed()` - RSS/Atom feed parsing
- `extract_post_content()` - HTML content extraction
- `clean_html_text()` - Text cleanup utilities

### Analysis (`analysis.py`)
- `analyse_post()` - Main analytics function
- Sentiment: VADER compound, positive, negative, neutral
- Readability: Flesch Reading Ease, Kincaid Grade Level
- Keywords: TF-IDF extraction (top 10)
- Metrics: Word count, lexical diversity, sentence stats

### MCP Server (`server.py`)
- All tool implementations return structured JSON
- Uses `create_text_result()` helper for MCP responses
- Error handling with proper MCP error types
- Stdio transport for Claude Desktop integration

## Development Workflow

### Adding New Features
1. Define data models in `models.py` first
2. Add client methods in `client.py` if needed
3. Implement MCP tool in `server.py`
4. Add tests in `tests/`
5. Update README.md with new tool documentation

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=substack_mcp --cov-report=html

# Test specific module
pytest tests/test_client.py -v

# Test with network mocking
pytest tests/test_server.py -v
```

### Manual MCP Testing
```bash
# Start the MCP server
./run_mcp_with_venv.sh

# Server will wait for stdio input (normal behavior)
# Test by configuring in Claude Desktop
```

## Common Tasks

### Add a New MCP Tool
1. Define tool schema in `server.py` under `@server.list_tools()`
2. Implement handler under `@server.call_tool()`
3. Use `create_text_result()` for responses
4. Add tests in `tests/test_server.py`

### Update Analytics
1. Modify `analyse_post()` in `analysis.py`
2. Update `ContentAnalytics` model in `models.py`
3. Add tests for new metrics
4. Document in README.md

### Fix MCP Issues
- Check MCP SDK version is 1.10.0: `pip show mcp`
- Verify stdio transport is working (not HTTP)
- Ensure `create_text_result()` returns plain dicts
- Test with Claude Desktop integration

## Dependencies

**Core:**
- `mcp==1.10.0` (locked version)
- `pydantic>=2.0` (data validation)
- `beautifulsoup4` (HTML parsing)
- `feedparser` (RSS/Atom feeds)
- `httpx` (async HTTP client)

**Analytics:**
- `vaderSentiment` (sentiment analysis)
- `textstat` (readability metrics)
- `scikit-learn` (TF-IDF keywords)
- `nltk` (text processing)

**Development:**
- `pytest` (testing framework)
- `pytest-asyncio` (async tests)
- `respx` (HTTP mocking)

## Important Notes

- This server is designed **exclusively for Claude Code/Desktop** via MCP protocol
- No web server deployment needed (uses stdio transport)
- All content access is public only (respects Substack ToS)
- Rate limiting is built-in and should not be disabled
- Cache helps reduce API calls and respect rate limits

## Troubleshooting

### MCP Connection Issues
1. Check `run_mcp_with_venv.sh` is executable: `chmod +x run_mcp_with_venv.sh`
2. Verify virtual environment exists: `.venv/`
3. Check MCP config in Claude Desktop: `claude_desktop_config.json`
4. Restart Claude Desktop after config changes

### Import Errors
1. Ensure editable install: `pip install -e .`
2. Check virtual environment is activated
3. Verify all dependencies installed: `pip list`

### Test Failures
1. Check network mocking is working (respx)
2. Verify test fixtures exist in `tests/fixtures/`
3. Run with verbose output: `pytest -v`
