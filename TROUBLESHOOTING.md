# Substack MCP Server - Troubleshooting Guide

This guide covers common issues and their solutions when using the Substack MCP server with Claude Desktop.

## 🚨 Critical Known Issues & Solutions

### 1. CallToolResult Validation Errors ✅ **FIXED**

**Symptoms:**
```
20 validation errors for CallToolResult
content.0.TextContent
  Input should be a valid dictionary or instance of TextContent [type=model_type, input_value=('meta', None), input_type=tuple]
```

**Root Cause:**
- MCP Python SDK bug in versions >1.10.0
- CallToolResult objects serialized as tuples instead of proper objects during stdio transport

**Our Solution:**
- ✅ **MCP Version**: Downgraded to 1.10.0 (last working version)
- ✅ **Workaround Applied**: Custom `create_text_result()` function returns dictionaries
- ✅ **Status**: Fully resolved and tested

**If You Still See This Error:**
1. Verify MCP version: `source substack_mcp_env/bin/activate && pip show mcp`
2. Should show version 1.10.0
3. If not: `pip install mcp==1.10.0`
4. Restart Claude Desktop

---

### 2. Model Field Attribute Errors ✅ **FIXED**

**Symptoms:**
```
AttributeError: 'PostSummary' object has no attribute 'published'
AttributeError: 'PostSummary' object has no attribute 'subtitle'
Object of type HttpUrl is not JSON serializable
```

**Our Solution:**
- ✅ **Field Name Mapping**: `published` → `published_at`, `subtitle` → `excerpt`
- ✅ **Model Structure**: PostContent fields accessed via `summary` property
- ✅ **URL Serialization**: All HttpUrl objects converted to strings
- ✅ **All Models Updated**: PostSummary, ContentAnalytics, AuthorProfile properly mapped

---

### 3. JSON Schema Validation Issues ✅ **FIXED**

**Symptoms:**
- MCP tool schemas failing validation
- Default parameter values causing issues

**Our Solution:**
- ✅ **Removed Default Values**: All `"default"` properties removed from tool schemas
- ✅ **Schema Validation**: All 6 tools pass MCP protocol validation

---

## 🔧 Common Setup Issues

### MCP Server Not Detected by Claude Desktop

**Check Configuration:**
1. Verify path in `claude_desktop_config.json`:
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
2. Update the path to match your actual directory
3. Ensure wrapper script is executable: `chmod +x run_mcp_with_venv.sh`

**Test Script Manually:**
```bash
cd /Users/cypher/Documents/coding/substack_mcp
./run_mcp_with_venv.sh
```
- Should start server and wait for input (this is correct behavior)
- Press Ctrl+C to exit

**Restart Claude Desktop** after configuration changes.

---

### Virtual Environment Issues

**Python Version:**
- Requires Python 3.11+ (for MCP SDK compatibility)
- Check: `python3.11 --version` or `/opt/homebrew/bin/python3.11 --version`

**Dependencies:**
```bash
cd /Users/cypher/Documents/coding/substack_mcp
source substack_mcp_env/bin/activate
pip show mcp  # Should show version 1.10.0
pip install . # Reinstall project if needed
```

---

### Permission Issues

**Script Permissions:**
```bash
chmod +x run_mcp_with_venv.sh
chmod +x run_mcp_server.py
```

**Directory Access:**
- Ensure Claude Desktop can access the project directory
- No special permissions needed beyond standard user access

---

## 🧪 Testing & Verification

### Manual Server Testing

1. **Test Tool Loading:**
   ```bash
   source substack_mcp_env/bin/activate
   python -c "
   import asyncio
   from substack_mcp.mcp_server import handle_list_tools
   async def test():
       tools = await handle_list_tools()
       print(f'Loaded {len(tools)} tools')
   asyncio.run(test())
   "
   ```

2. **Test Real Data Fetch:**
   ```bash
   source substack_mcp_env/bin/activate
   python -c "
   import asyncio, json
   from substack_mcp.mcp_server import handle_call_tool
   async def test():
       result = await handle_call_tool('get_posts', {'handle': 'techtiff', 'limit': 2})
       print('Success!' if isinstance(result, dict) else 'Failed')
   asyncio.run(test())
   "
   ```

### Verify MCP Integration

1. **Check Claude Desktop MCP Status:**
   - Look for MCP connection indicator (🔌) in Claude Desktop
   - Should show "substack-mcp" as connected

2. **Test Commands:**
   - "Get recent posts from techtiff Substack"
   - "List posts from platformer"
   - "Analyze sentiment of this Substack post: [URL]"

---

## 🐛 Debugging Steps

### Enable Detailed Logging

1. **Add Logging to MCP Server:**
   ```bash
   # Edit src/substack_mcp/mcp_server.py
   # Add at top: logging.basicConfig(level=logging.DEBUG)
   ```

2. **Capture Server Output:**
   ```bash
   source substack_mcp_env/bin/activate
   python run_mcp_server.py 2>&1 | tee mcp_debug.log &
   # Test from Claude Desktop, then check mcp_debug.log
   ```

### Common Error Patterns

**Import Errors:**
- Reinstall project: `pip install -e . --force-reinstall`
- Check Python path in virtual environment

**Network Errors:**
- Test direct URL access: `curl https://techtiff.substack.com/feed`
- Check firewall/proxy settings

**Parsing Errors:**
- Usually indicates RSS feed format changes
- Check specific publication feed format

---

## 🔄 Recovery Procedures

### Complete Reset

```bash
cd /Users/cypher/Documents/coding/substack_mcp
rm -rf substack_mcp_env
/opt/homebrew/bin/python3.11 -m venv substack_mcp_env
source substack_mcp_env/bin/activate
pip install --upgrade pip
pip install mcp==1.10.0
pip install .
```

### Verify Installation

```bash
source substack_mcp_env/bin/activate
python -c "
from substack_mcp.mcp_server import handle_list_tools
from mcp.types import TextContent
import asyncio
print('✅ All imports successful')
"
```

---

## 📞 Getting Help

If you encounter issues not covered here:

1. **Check Dependencies**: Ensure all required packages are installed
2. **Version Compatibility**: Verify Python 3.11+ and MCP 1.10.0
3. **Test Isolation**: Try running components individually
4. **Log Analysis**: Capture and review detailed error logs

## 🎯 Success Indicators

Your setup is working correctly when:
- ✅ MCP indicator (🔌) appears in Claude Desktop
- ✅ Commands like "Get posts from techtiff" return JSON data
- ✅ No validation errors in Claude Desktop
- ✅ All 6 tools (get_posts, analyze_post, etc.) function properly

---

**Last Updated:** September 2025
**MCP Version:** 1.10.0 (with workarounds)
**Status:** Production Ready ✅