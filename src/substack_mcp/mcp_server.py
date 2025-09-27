#!/usr/bin/env python3
"""MCP Server for Substack integrations."""

import asyncio
import json
import logging
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qs, urlparse

import mcp.server.stdio
from mcp.server import NotificationOptions, Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolResult,
    Resource,
    ResourceTemplate,
    TextContent,
    Tool,
)

from . import analysis
from .client import SubstackPublicClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance
substack_client = SubstackPublicClient()

server = Server("substack-mcp")


def _json_dump(payload: Any) -> str:
    """Return a stable JSON string for MCP responses."""

    def _to_json_ready(value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")  # type: ignore[no-any-return]
        if isinstance(value, list):
            return [_to_json_ready(item) for item in value]
        if isinstance(value, dict):
            return {key: _to_json_ready(item) for key, item in value.items()}
        return value

    return json.dumps(_to_json_ready(payload), indent=2, ensure_ascii=False)


def _create_text_result(text: str, is_error: bool = False) -> CallToolResult:
    """Create a CallToolResult containing a single text block."""

    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        isError=is_error,
    )


async def _run_io(func, *args):
    """Execute blocking Substack client calls on a thread pool."""

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)


def _parse_bool(params: Dict[str, List[str]], key: str, default: bool) -> bool:
    raw = params.get(key, [None])[0]
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _parse_int(params: Dict[str, List[str]], key: str, default: int) -> int:
    raw = params.get(key, [None])[0]
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid integer for '{key}': {raw}") from exc


def _coerce_bool(value: Any, default: bool) -> bool:
    """Best-effort conversion of tool arguments into booleans."""

    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


RESOURCE_HELP = """# Substack MCP Resources

This server exposes a set of read-only resources that map to public Substack data.

## Supported URI templates

- `substack://publication/{handle}/posts{?limit}` – Recent posts for a publication.
- `substack://publication/{handle}/notes{?limit}` – Recent notes for a publication.
- `substack://publication/{handle}/profile` – Author/profile information.
- `substack://publication/{handle}/search{?query,limit}` – Text search across recent posts.
- `substack://publication/{handle}/crawl{?post_limit,notes_limit,analyze}` – Full crawl with analytics.
- `substack://post?url={url}` – Fetch a specific post by URL.

All resources return JSON payloads. Use the URI templates above when issuing
`resources/read` requests from the ChatGPT MCP client.
"""


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for the MCP server."""
    return [
        Tool(
            name="get_posts",
            description="Fetch recent posts from a Substack publication",
            inputSchema={
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "Substack publication handle (e.g., 'platformer')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of posts to fetch",
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["handle"]
            }
        ),
        Tool(
            name="get_post_content",
            description="Get full content of a specific Substack post",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL to the Substack post"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="analyze_post",
            description="Analyze sentiment and readability of a Substack post",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL to the Substack post"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="get_author_profile",
            description="Get author profile information for a Substack publication",
            inputSchema={
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "Substack publication handle"
                    }
                },
                "required": ["handle"]
            }
        ),
        Tool(
            name="get_notes",
            description="Get recent Substack notes from a publication",
            inputSchema={
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "Substack publication handle"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of notes to fetch",
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["handle"]
            }
        ),
        Tool(
            name="crawl_publication",
            description="Comprehensive crawl of a Substack publication including posts, notes, and author profile",
            inputSchema={
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "Substack publication handle"
                    },
                    "post_limit": {
                        "type": "integer",
                        "description": "Maximum number of posts to fetch",
                        "minimum": 1,
                        "maximum": 25
                    },
                    "notes_limit": {
                        "type": "integer",
                        "description": "Maximum number of notes to fetch",
                        "minimum": 0,
                        "maximum": 50
                    },
                    "analyze": {
                        "type": "boolean",
                        "description": "Whether to perform analytics on the content"
                    }
                },
                "required": ["handle"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls from the client."""

    try:
        if name == "get_posts":
            handle = arguments["handle"]
            limit = int(arguments.get("limit", 10))
            posts = await _run_io(substack_client.fetch_feed, handle, limit)
            payload = {"handle": handle, "posts": posts, "limit": limit}
            return _create_text_result(_json_dump(payload))

        if name == "get_post_content":
            url = arguments["url"]
            post_content = await _run_io(substack_client.fetch_post, url)
            return _create_text_result(_json_dump(post_content))

        if name == "analyze_post":
            url = arguments["url"]
            post_content = await _run_io(substack_client.fetch_post, url)
            publication_handle: Optional[str] = None
            summary_publication = post_content.summary.publication
            if summary_publication and summary_publication.handle:
                publication_handle = summary_publication.handle
            else:
                parsed = urlparse(url)
                host = parsed.hostname or ""
                if host.endswith(".substack.com"):
                    publication_handle = host.split(".")[0]
            history: List[Any] = []
            if publication_handle:
                try:
                    history = await _run_io(substack_client.fetch_feed, publication_handle, 10)
                except Exception:  # pragma: no cover - defensive
                    history = []
            analytics_result = await _run_io(analysis.analyse_post, post_content, history)
            return _create_text_result(_json_dump(analytics_result))

        if name == "get_author_profile":
            handle = arguments["handle"]
            profile = await _run_io(substack_client.fetch_author_profile, handle)
            if profile is None:
                return _create_text_result(
                    _json_dump({"error": "Author profile not found", "handle": handle}),
                    is_error=True,
                )
            return _create_text_result(_json_dump(profile))

        if name == "get_notes":
            handle = arguments["handle"]
            limit = int(arguments.get("limit", 10))
            notes = await _run_io(substack_client.fetch_notes, handle, limit)
            payload = {"handle": handle, "notes": notes, "limit": limit}
            return _create_text_result(_json_dump(payload))

        if name == "crawl_publication":
            handle = arguments["handle"]
            post_limit = int(arguments.get("post_limit", 5))
            notes_limit = int(arguments.get("notes_limit", 10))
            analyze = _coerce_bool(arguments.get("analyze", True), True)
            result = await _run_io(
                substack_client.crawl_publication,
                handle,
                post_limit,
                analyze,
                notes_limit,
            )
            return _create_text_result(_json_dump(result))

        return _create_text_result(_json_dump({"error": f"Unknown tool: {name}"}), is_error=True)

    except Exception as exc:  # noqa: BLE001 - surface failure to the client
        logger.error("Error handling tool call %s: %s", name, exc)
        return _create_text_result(_json_dump({"error": str(exc), "tool": name}), is_error=True)


@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """Expose the static root resource so clients discover URI templates."""

    return [
        Resource(
            name="substack-help",
            uri="substack://help",
            description="Documentation for available Substack resource templates.",
            mimeType="text/markdown",
        )
    ]


@server.list_resource_templates()
async def handle_list_resource_templates() -> List[ResourceTemplate]:
    """Advertise supported resource URI templates."""

    return [
        ResourceTemplate(
            name="publication-posts",
            title="Publication posts",
            uriTemplate="substack://publication/{handle}/posts{?limit}",
            description="Fetch the most recent posts for a Substack publication.",
            mimeType="application/json",
        ),
        ResourceTemplate(
            name="publication-notes",
            title="Publication notes",
            uriTemplate="substack://publication/{handle}/notes{?limit}",
            description="Fetch recent Substack notes for a publication.",
            mimeType="application/json",
        ),
        ResourceTemplate(
            name="publication-profile",
            title="Author profile",
            uriTemplate="substack://publication/{handle}/profile",
            description="Retrieve author profile metadata for a publication.",
            mimeType="application/json",
        ),
        ResourceTemplate(
            name="publication-search",
            title="Search publication",
            uriTemplate="substack://publication/{handle}/search{?query,limit}",
            description="Search recent posts for the provided query string.",
            mimeType="application/json",
        ),
        ResourceTemplate(
            name="publication-crawl",
            title="Crawl publication",
            uriTemplate="substack://publication/{handle}/crawl{?post_limit,notes_limit,analyze}",
            description="Comprehensive crawl including posts, notes, and analytics.",
            mimeType="application/json",
        ),
        ResourceTemplate(
            name="post-by-url",
            title="Post by URL",
            uriTemplate="substack://post{?url}",
            description="Fetch a specific Substack post by full URL.",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> Iterable[ReadResourceContents]:
    """Resolve Substack resource URIs into JSON payloads."""

    try:
        if uri in {"substack://help", "substack://index"}:
            return [ReadResourceContents(content=RESOURCE_HELP, mime_type="text/markdown")]

        parsed = urlparse(uri)
        if parsed.scheme != "substack":
            raise ValueError("Unsupported URI scheme; expected 'substack'.")

        netloc = parsed.netloc
        path_parts = [part for part in parsed.path.split("/") if part]
        query_params = parse_qs(parsed.query)

        if netloc == "post":
            post_url = query_params.get("url", [None])[0]
            if not post_url:
                raise ValueError("The 'url' query parameter is required for post resources.")
            post_content = await _run_io(substack_client.fetch_post, post_url)
            return [
                ReadResourceContents(
                    content=_json_dump(post_content),
                    mime_type="application/json",
                )
            ]

        if netloc != "publication" or not path_parts:
            raise ValueError(f"Unsupported resource URI: {uri}")

        handle = path_parts[0]
        if len(path_parts) == 1 or path_parts[1] == "posts":
            limit = _parse_int(query_params, "limit", 10)
            posts = await _run_io(substack_client.fetch_feed, handle, limit)
            payload = {"handle": handle, "limit": limit, "posts": posts}
            return [ReadResourceContents(content=_json_dump(payload), mime_type="application/json")]

        resource_type = path_parts[1]
        if resource_type == "notes":
            limit = _parse_int(query_params, "limit", 10)
            notes = await _run_io(substack_client.fetch_notes, handle, limit)
            payload = {"handle": handle, "limit": limit, "notes": notes}
            return [ReadResourceContents(content=_json_dump(payload), mime_type="application/json")]

        if resource_type == "profile":
            profile = await _run_io(substack_client.fetch_author_profile, handle)
            payload = {"handle": handle, "profile": profile}
            return [ReadResourceContents(content=_json_dump(payload), mime_type="application/json")]

        if resource_type == "search":
            query = query_params.get("query", [""])[0].strip()
            if not query:
                raise ValueError("The 'query' parameter is required for search resources.")
            limit = max(1, _parse_int(query_params, "limit", 10))
            search_pool = await _run_io(substack_client.fetch_feed, handle, max(limit, 25))
            lowered = query.lower()
            results = []
            for post in search_pool:
                matches: List[str] = []
                if post.title and lowered in post.title.lower():
                    matches.append("title")
                if post.excerpt and lowered in post.excerpt.lower():
                    matches.append("excerpt")
                if matches:
                    results.append({"match_fields": matches, "post": post})
            payload = {"handle": handle, "query": query, "limit": limit, "results": results[:limit]}
            return [ReadResourceContents(content=_json_dump(payload), mime_type="application/json")]

        if resource_type == "crawl":
            post_limit = _parse_int(query_params, "post_limit", 5)
            notes_limit = _parse_int(query_params, "notes_limit", 10)
            analyze = _parse_bool(query_params, "analyze", True)
            result = await _run_io(
                substack_client.crawl_publication,
                handle,
                post_limit,
                analyze,
                notes_limit,
            )
            payload = {"handle": handle, "post_limit": post_limit, "notes_limit": notes_limit, "analyze": analyze, "result": result}
            return [ReadResourceContents(content=_json_dump(payload), mime_type="application/json")]

        raise ValueError(f"Unsupported resource path: {'/'.join(path_parts)}")

    except Exception as exc:  # noqa: BLE001 - keep the connection alive with JSON error payloads
        logger.error("Error resolving resource %s: %s", uri, exc)
        error_payload = {"error": str(exc), "uri": uri}
        return [ReadResourceContents(content=_json_dump(error_payload), mime_type="application/json")]


async def main():
    """Main entry point for the MCP server."""
    # Run the server using stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="substack-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())