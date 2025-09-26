#!/usr/bin/env python3
"""Convenience script to start the Substack MCP server."""

from __future__ import annotations

import argparse
import os

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Substack MCP server")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument(
        "--publication",
        help="Optional publication handle to warm caches (fetch feed on startup).",
        default=os.getenv("SUBSTACK_MCP_WARM_PUBLICATION"),
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "info"),
        help="Uvicorn log level",
    )
    args = parser.parse_args()

    if args.publication:
        from substack_mcp.client import SubstackPublicClient

        client = SubstackPublicClient()
        try:
            client.fetch_feed(args.publication, limit=5)
        finally:
            client.close()

    uvicorn.run(
        "substack_mcp.server:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()
