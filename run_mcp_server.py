#!/usr/bin/env python3
"""Entry point script for running the Substack MCP server."""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from substack_mcp.mcp_server import main

if __name__ == "__main__":
    asyncio.run(main())