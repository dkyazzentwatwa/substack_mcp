# Claude Desktop MCP Setup for Substack

This guide helps you integrate the Substack MCP server with Claude Desktop.

## Prerequisites

- Claude Desktop application installed
- Python 3.10+ (we use Python 3.11)
- Virtual environment set up and dependencies installed

## Setup Instructions

### 1. Find Claude Desktop Configuration

Claude Desktop stores its configuration in:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 2. Add Substack MCP Configuration

Add the following configuration to your `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "substack-mcp": {
      "command": "/Users/cypher/Documents/coding/substack_mcp/run_mcp_with_venv.sh",
      "args": []
    }
  }
}
```

**Important**: Update the `command` path to match your actual project directory.

### 3. Test the Setup

1. Restart Claude Desktop
2. Look for the MCP connection indicator (🔌) in Claude Desktop
3. Test with a simple command like: "List recent posts from the 'platformer' Substack publication"

## Available Tools

The Substack MCP server provides these tools:

### 1. `get_posts`
- **Description**: Fetch recent posts from a Substack publication
- **Parameters**:
  - `handle` (required): Substack publication handle (e.g., 'platformer')
  - `limit` (optional): Maximum number of posts (1-50, default: 10)

### 2. `get_post_content`
- **Description**: Get full content of a specific Substack post
- **Parameters**:
  - `url` (required): Full URL to the Substack post

### 3. `analyze_post`
- **Description**: Analyze sentiment and readability of a Substack post
- **Parameters**:
  - `url` (required): Full URL to the Substack post

### 4. `get_author_profile`
- **Description**: Get author profile information
- **Parameters**:
  - `handle` (required): Substack publication handle

### 5. `get_notes`
- **Description**: Get recent Substack notes
- **Parameters**:
  - `handle` (required): Substack publication handle
  - `limit` (optional): Maximum number of notes (1-50, default: 10)

### 6. `crawl_publication`
- **Description**: Comprehensive crawl including posts, notes, and profile
- **Parameters**:
  - `handle` (required): Substack publication handle
  - `post_limit` (optional): Maximum posts (1-25, default: 5)
  - `notes_limit` (optional): Maximum notes (0-50, default: 10)
  - `analyze` (optional): Whether to perform analytics (default: true)

## Example Usage

Once configured, you can ask Claude Desktop things like:

- "Get the latest 5 posts from the 'platformer' Substack"
- "Analyze the sentiment of this Substack post: [URL]"
- "Get the author profile for the 'stratechery' Substack"
- "Do a comprehensive crawl of the 'casey' publication with analysis"

## ⚠️ CRITICAL: Known MCP Bug Workaround Applied

**This server implements a workaround for a critical bug in MCP Python SDK versions >1.10.0**

### The Issue
- MCP SDK versions >1.10.0 have a CallToolResult serialization bug
- Causes validation errors like: `Input should be a valid dictionary or instance of TextContent [type=model_type, input_value=('meta', None), input_type=tuple]`
- Results in tuples instead of proper objects during stdio transport

### Our Solution
- **MCP Version**: Locked to 1.10.0 (last working version)
- **Workaround**: Custom `create_text_result()` function returns plain dictionaries instead of CallToolResult objects
- **Status**: ✅ **Fully functional and tested**

## Troubleshooting

### MCP Server Not Connecting
1. Check that the script path in the config is correct and absolute
2. Ensure the wrapper script is executable (`chmod +x run_mcp_with_venv.sh`)
3. Verify Python 3.11 is installed and accessible
4. Check Claude Desktop logs for error messages

### CallToolResult Validation Errors
**If you see tuple validation errors like `('meta', None)`, `('content', [...]))`:**
1. ✅ This is already fixed in our implementation
2. Ensure you're using our version with the workaround applied
3. Restart Claude Desktop after any changes
4. Check that MCP version is 1.10.0: `pip show mcp`

### Virtual Environment Issues
1. Make sure the virtual environment was created with Python 3.11+
2. Verify MCP is version 1.10.0: `source substack_mcp_env/bin/activate && pip show mcp`
3. Verify all dependencies are installed (`pip install .` from the project directory)
4. Test the MCP server manually: `./run_mcp_with_venv.sh`

### Permission Issues
- Ensure all scripts have execute permissions
- Check that Claude Desktop has necessary file system permissions

### Data Model Issues
**If you encounter field attribute errors:**
- ✅ Field name mismatches are already fixed (`published` → `published_at`, etc.)
- ✅ HttpUrl serialization is handled automatically
- ✅ All model structures have been verified and tested

## Testing the MCP Server

You can test the MCP server manually:

```bash
# Navigate to the project directory
cd /Users/cypher/Documents/coding/substack_mcp

# Test the wrapper script
./run_mcp_with_venv.sh

# The server should start and wait for MCP protocol messages
```

The server communicates via stdio using the MCP protocol, so it will appear to "hang" waiting for input when run manually - this is normal behavior.