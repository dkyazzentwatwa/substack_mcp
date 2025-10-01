# Substack MCP Server for Claude Code

A powerful Model Context Protocol (MCP) server that gives Claude Code deep, structured access to Substack publications with real-time content analysis.

## Why Use This?

### 🎯 **Precision Research**
- Real-time access to specific Substack publications
- Comprehensive publication intelligence - posts, notes, author profiles
- Structured data vs. scattered web search results

### 📊 **Built-In Analytics**
- Sentiment analysis (VADER-based emotional tone detection)
- Readability metrics (Flesch Reading Ease, Kincaid Grade Level)
- Keyword extraction (TF-IDF with stopword filtering)
- Publishing patterns and content trends

### ⚡ **Live Data**
- Fresh content as it's published
- No AI knowledge cutoff limitations
- Direct access to RSS feeds and public content

> ⚠️ **Ethical Use**: Respects Substack's Terms of Service with built-in throttling (1-second delays) for responsible crawling.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/substack_mcp.git
cd substack_mcp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### Configure Claude Code

Add the Substack MCP server to your Claude Desktop configuration:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "substack": {
      "command": "/absolute/path/to/substack_mcp/run_mcp_with_venv.sh",
      "args": []
    }
  }
}
```

**Important**: Update the `command` path to your actual project directory.

### Verify Setup

1. Restart Claude Desktop
2. Look for the MCP connection indicator (🔌)
3. Test with: *"Get the latest posts from platformer"*

## Available Tools

### 🔍 **Content Discovery**

#### `get_posts`
Fetch recent posts from a Substack publication.
```
Parameters:
- handle (required): Publication handle (e.g., 'platformer')
- limit (optional): Number of posts (1-50, default: 10)
```

#### `get_post_content`
Get full content of a specific Substack post.
```
Parameters:
- url (required): Full URL to the Substack post
```

#### `search`
Search for content across publications.
```
Parameters:
- query (required): Search terms
- handle (optional): Specific publication to search
```

### 📊 **Analytics & Intelligence**

#### `analyze_post`
Analyze sentiment and readability of a post.
```
Parameters:
- url (required): Full URL to the Substack post

Returns:
- Sentiment scores (positive, negative, neutral, compound)
- Readability metrics (Flesch Reading Ease, grade level)
- Keyword extraction
- Word count and structure analysis
```

#### `get_author_profile`
Get author and publication information.
```
Parameters:
- handle (required): Substack publication handle

Returns:
- Author bio and profile
- Publication metadata
- Social links
```

#### `get_notes`
Get recent Substack notes from a publication.
```
Parameters:
- handle (required): Publication handle
- limit (optional): Number of notes (1-50, default: 10)
```

#### `crawl_publication`
Comprehensive publication crawl with analytics.
```
Parameters:
- handle (required): Publication handle
- post_limit (optional): Max posts (1-25, default: 5)
- notes_limit (optional): Max notes (0-50, default: 10)
- analyze (optional): Perform analytics (default: true)

Returns:
- Complete publication overview
- Author profile
- Recent posts with analytics
- Recent notes
- Publishing patterns
```

## Example Workflows

### Research a Publication
```
"Analyze the latest 10 posts from stratechery and identify common themes"
```

### Compare Writing Styles
```
"Compare the readability scores between platformer and stratechery"
```

### Track Publishing Patterns
```
"Show me the publishing cadence for Benedict Evans over the last month"
```

### Content Analysis
```
"Analyze the sentiment and key topics in this post: [URL]"
```

### Deep Dive
```
"Do a comprehensive crawl of the newsletter handle and summarize the key insights"
```

## Analytics Capabilities

### Content Metrics
- **Sentiment Analysis**: Positive, negative, neutral, and compound scores
- **Readability**: Flesch Reading Ease (0-100 scale)
- **Grade Level**: Flesch-Kincaid Grade Level
- **Lexical Diversity**: Vocabulary richness metrics
- **Structure**: Word count, sentence count, average sentence length

### Publication Intelligence
- **Publishing Cadence**: Average days between posts
- **Content Trends**: Topic evolution over time
- **Keyword Analysis**: TF-IDF-based keyword extraction
- **Author Patterns**: Writing style consistency

## Project Structure

```
substack_mcp/
├── src/substack_mcp/
│   ├── client.py       # HTTP client with rate limiting
│   ├── models.py       # Pydantic data models
│   ├── parsers.py      # RSS/HTML parsing
│   ├── analysis.py     # Text analytics
│   ├── cache.py        # TTL-based caching
│   ├── server.py       # MCP server implementation
│   └── settings.py     # Configuration
├── tests/              # Test suite
├── scripts/            # Utility scripts
└── run_mcp_with_venv.sh # Wrapper script
```

## Configuration

Optional environment variables:

```bash
# Request throttling (seconds between requests)
export SUBSTACK_MCP_THROTTLE=1.0

# Cache time-to-live (seconds)
export SUBSTACK_MCP_CACHE_TTL=900

# Publication to warm cache on startup
export SUBSTACK_MCP_WARM_PUBLICATION=platformer
```

## Troubleshooting

### MCP Server Not Connecting
1. Verify the script path in config is correct and absolute
2. Ensure wrapper script is executable: `chmod +x run_mcp_with_venv.sh`
3. Check Python 3.10+ is installed
4. Restart Claude Desktop after config changes

### Permission Issues
1. Ensure scripts have execute permissions
2. Verify virtual environment is activated
3. Check Claude Desktop has file system permissions

### Testing Manually
```bash
cd /path/to/substack_mcp
./run_mcp_with_venv.sh
```

The server uses stdio for MCP protocol, so it will wait for input (this is normal).

## Technical Notes

### MCP SDK Version
This server uses MCP SDK v1.10.0 (locked) with a workaround for a CallToolResult serialization bug in later versions. The implementation uses custom `create_text_result()` functions that return plain dictionaries.

### Rate Limiting
Built-in 1-second throttle between requests to respect Substack's infrastructure. Uses TTL-based in-memory cache (15 minutes default).

### Public Content Only
This tool accesses only public Substack content. No authentication or paywalled content access.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] Persistent storage (SQLite) for cached content
- [ ] Background worker for scheduled crawls
- [ ] Advanced summarization and topic modeling
- [ ] Support for authenticated content (pending ToS review)

---

Built for use with [Claude Code](https://claude.com/claude-code) - The official Anthropic CLI for Claude.
