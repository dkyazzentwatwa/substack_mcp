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

## TL;DR - Get Started in 30 Seconds

```bash
# 1. Clone and enter the directory
git clone https://github.com/yourusername/substack_mcp.git
cd substack_mcp

# 2. Open Claude Code in this directory
# 3. Ask: "Install this MCP server"
# 4. Use it: "Get the latest posts from platformer"
```

That's it! Claude Code handles everything else.

## Quick Start with Claude Code

### Option 1: Automatic Installation (Recommended)

If you're already in the project directory in Claude Code:

1. **Simply ask Claude Code to set it up:**
   ```
   "Install this MCP server for me"
   ```

   Claude Code will:
   - Create the virtual environment
   - Install dependencies
   - Configure the MCP server automatically
   - Add it to your MCP configuration

2. **Verify it's installed:**
   ```
   /mcp
   ```

   You should see `substack` (or `substack-mcp`) in the list of available MCP servers.

3. **Start using it:**
   ```
   "Get the latest posts from platformer"
   "Analyze sentiment for techtiff's recent posts"
   "Show me publishing patterns for stratechery"
   ```

### Option 2: Manual Installation

```bash
# Clone the repository (if not already)
git clone https://github.com/yourusername/substack_mcp.git
cd substack_mcp

# Let Claude Code handle the rest, or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Then ask Claude Code to:
# "Add this MCP server to my configuration"
```

### Using with Claude Desktop (Alternative)

If you want to use with Claude Desktop instead of Claude Code:

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

Then restart Claude Desktop.

## How to Use with Claude Code

Once installed, simply talk to Claude Code naturally. The MCP tools work automatically in the background.

### Example Conversations

**Research a publication:**
```
You: "Analyze the latest 10 posts from stratechery"

Claude Code will:
- Use get_posts to fetch the posts
- Use analyze_post on each one
- Summarize themes, sentiment, and readability patterns
```

**Compare publications:**
```
You: "Compare the writing complexity between platformer and techtiff"

Claude Code will:
- Fetch posts from both publications
- Run readability analysis
- Present comparative insights
```

**Deep content analysis:**
```
You: "Get the full content and sentiment analysis for this post:
     https://techtiff.substack.com/p/sonnet-4-5-release"

Claude Code will:
- Use get_post_content to fetch the full article
- Use analyze_post for sentiment and readability
- Provide detailed insights
```

**Track publishing patterns:**
```
You: "What's the publishing cadence for littlehakr?"

Claude Code will:
- Use crawl_publication with analytics
- Calculate average days between posts
- Show publishing trends
```

### Natural Language > Tool Names

You don't need to know the tool names. Just ask naturally:

- ❌ "Use get_posts with handle=platformer and limit=5"
- ✅ "Show me the latest 5 posts from platformer"

Claude Code automatically:
- Selects the right MCP tools
- Extracts parameters from your request
- Combines multiple tools when needed
- Presents results in a readable format

### Checking MCP Status

Use the `/mcp` command anytime to:
- List all installed MCP servers
- Check if Substack MCP is available
- See what other MCP tools you have

```
/mcp
```

Output will show:
```
Available MCP servers:
- substack (6 tools available)
  - get_posts
  - get_post_content
  - analyze_post
  - get_author_profile
  - get_notes
  - crawl_publication
```

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

## Common Use Cases

### Content Strategy Research
```
"What topics is stratechery covering this month?"
"How often does platformer publish?"
"Compare the keyword focus between two tech newsletters"
```

### Writing Analysis
```
"Is techtiff's content getting easier or harder to read over time?"
"What's the average grade level for this publication?"
"Show me sentiment trends in recent posts"
```

### Competitive Intelligence
```
"Compare publishing frequency across 3 tech newsletters"
"Which newsletter has the most positive sentiment?"
"Identify content gaps between competing publications"
```

### Author Research
```
"Give me a profile of the stratechery author"
"What's their publishing pattern?"
"Show me their most recent posts with analytics"
```

### Deep Content Dives
```
"Analyze this specific post for readability and sentiment: [URL]"
"Extract key themes from the last 20 posts"
"Show me how their writing style has evolved"
```

### Quick Checks
```
"Latest posts from platformer"
"What did techtiff write about this week?"
"Get notes from this publication"
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

### MCP Server Not Showing Up

**Check with `/mcp` command:**
```
/mcp
```

If you don't see `substack` in the list:

1. **Ask Claude Code to help:**
   ```
   "The substack MCP server isn't showing up in /mcp. Can you help install it?"
   ```

2. **Verify installation:**
   ```bash
   cd /path/to/substack_mcp
   ls run_mcp_with_venv.sh  # Should exist
   source .venv/bin/activate
   pip list | grep mcp       # Should show mcp==1.10.0
   ```

3. **Check Python version:**
   ```bash
   python3 --version  # Should be 3.10 or higher
   ```

### Tools Not Working

If Claude Code says tools aren't available:

1. **Reinstall dependencies:**
   ```
   "Can you reinstall the dependencies for this MCP server?"
   ```

2. **Check for errors:**
   ```bash
   ./run_mcp_with_venv.sh
   # Should start without errors (Ctrl+C to exit)
   ```

### Claude Desktop Not Connecting

If using Claude Desktop instead of Claude Code:

1. Ensure `claude_desktop_config.json` has correct absolute path
2. Make wrapper script executable: `chmod +x run_mcp_with_venv.sh`
3. Restart Claude Desktop after config changes

### Rate Limiting Issues

If you see HTTP 429 errors or timeouts:
- The server has built-in 1-second throttling
- Reduce the number of posts you're analyzing at once
- Try again after a brief pause

## Technical Notes

### MCP SDK Version
This server uses MCP SDK v1.10.0 (locked) with a workaround for a CallToolResult serialization bug in later versions. The implementation uses custom `create_text_result()` functions that return plain dictionaries.

### Rate Limiting
Built-in 1-second throttle between requests to respect Substack's infrastructure. Uses TTL-based in-memory cache (15 minutes default).

### Public Content Only
This tool accesses only public Substack content. No authentication or paywalled content access.

## Getting Help

### Using Claude Code
The best way to get help is to ask Claude Code directly:
```
"I'm having trouble with the substack MCP server. Can you help diagnose?"
"How do I use this MCP server to analyze multiple publications?"
```

### Documentation
- **[CLAUDE.md](CLAUDE.md)** - Developer documentation for working on this project
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **GitHub Issues** - Report bugs or request features

### Quick Checks
```bash
# Verify installation
/mcp

# Test manually
cd substack_mcp && ./run_mcp_with_venv.sh

# Check Python and dependencies
python3 --version
source .venv/bin/activate && pip list
```

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

**Built for [Claude Code](https://claude.com/claude-code)** - The official Anthropic CLI for Claude.

Made with ❤️ for Substack researchers, content strategists, and AI enthusiasts.
