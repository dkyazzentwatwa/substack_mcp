#!/usr/bin/env python3
"""HTTP/SSE MCP Server for Substack integration with ChatGPT."""

import asyncio
import json
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import (
    Tool,
    CallToolResult,
    ListToolsResult,
)
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
import mcp.server.sse

from .client import SubstackPublicClient
from . import analysis

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance
substack_client = SubstackPublicClient()

server = Server("substack-mcp")

# Workaround for MCP CallToolResult serialization bug
def create_text_result(text: str, is_error: bool = False):
    """Create a properly formatted result that avoids MCP serialization issues"""
    return {
        "content": [{
            "type": "text",
            "text": text
        }],
        "isError": is_error
    }


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
            limit = arguments.get("limit", 10)

            posts = await asyncio.get_event_loop().run_in_executor(
                None, substack_client.fetch_feed, handle, limit
            )

            # Convert posts to JSON-serializable format
            posts_data = [
                {
                    "title": post.title,
                    "url": str(post.url),
                    "published": post.published_at.isoformat() if post.published_at else None,
                    "subtitle": post.excerpt,
                    "author": post.author
                }
                for post in posts
            ]

            return create_text_result(json.dumps(posts_data, indent=2))

        elif name == "get_post_content":
            url = arguments["url"]

            post_content = await asyncio.get_event_loop().run_in_executor(
                None, substack_client.fetch_post, url
            )

            post_data = {
                "title": post_content.summary.title,
                "url": str(post_content.summary.url),
                "published": post_content.summary.published_at.isoformat() if post_content.summary.published_at else None,
                "subtitle": post_content.summary.excerpt,
                "author": post_content.summary.author,
                "body": post_content.text,
                "word_count": post_content.word_count
            }

            return create_text_result(json.dumps(post_data, indent=2))

        elif name == "analyze_post":
            url = arguments["url"]

            # Fetch post content first
            post_content = await asyncio.get_event_loop().run_in_executor(
                None, substack_client.fetch_post, url
            )

            # Get feed for context
            # Extract handle from URL for feed context
            if "substack.com" in url:
                parts = url.split(".")
                if len(parts) > 2:
                    handle = parts[0].split("//")[-1]
                    feed = await asyncio.get_event_loop().run_in_executor(
                        None, substack_client.fetch_feed, handle, 10
                    )
                else:
                    feed = []
            else:
                feed = []

            # Analyze the post
            analytics = await asyncio.get_event_loop().run_in_executor(
                None, analysis.analyse_post, post_content, feed
            )

            analytics_data = {
                "title": analytics.summary.title,
                "url": str(analytics.summary.url),
                "published": analytics.summary.published_at.isoformat() if analytics.summary.published_at else None,
                "sentiment": {
                    "compound": analytics.sentiment.compound,
                    "positive": analytics.sentiment.positive,
                    "neutral": analytics.sentiment.neutral,
                    "negative": analytics.sentiment.negative
                } if analytics.sentiment else None,
                "readability": {
                    "flesch_reading_ease": analytics.flesch_reading_ease,
                    "flesch_kincaid_grade": analytics.flesch_kincaid_grade,
                    "lexical_diversity": analytics.lexical_diversity,
                    "average_sentence_length": analytics.average_sentence_length
                },
                "keywords": [
                    {"term": kw.term, "score": kw.score}
                    for kw in analytics.keywords[:10]  # Top 10 keywords
                ],
                "publishing_cadence_days": analytics.publishing_cadence_days,
                "word_count": analytics.extra.get("word_count") if analytics.extra else None
            }

            return create_text_result(json.dumps(analytics_data, indent=2))

        elif name == "get_author_profile":
            handle = arguments["handle"]

            profile = await asyncio.get_event_loop().run_in_executor(
                None, substack_client.fetch_author_profile, handle
            )

            if profile is None:
                return create_text_result(json.dumps({"error": "Author profile not found"}), is_error=True)

            profile_data = {
                "display_name": profile.display_name,
                "bio": profile.bio,
                "avatar_url": str(profile.avatar_url) if profile.avatar_url else None,
                "location": profile.location,
                "followers": profile.followers,
                "publication": {
                    "handle": profile.publication.handle if profile.publication else None,
                    "title": profile.publication.title if profile.publication else None,
                    "url": str(profile.publication.url) if profile.publication and profile.publication.url else None
                } if profile.publication else None,
                "social_links": {k: str(v) for k, v in profile.social_links.items()} if profile.social_links else {}
            }

            return create_text_result(json.dumps(profile_data, indent=2))

        elif name == "get_notes":
            handle = arguments["handle"]
            limit = arguments.get("limit", 10)

            notes = await asyncio.get_event_loop().run_in_executor(
                None, substack_client.fetch_notes, handle, limit
            )

            notes_data = [
                {
                    "id": note.id,
                    "content": note.content,
                    "published": note.published_at.isoformat() if note.published_at else None,
                    "author": note.author,
                    "url": str(note.url)
                }
                for note in notes
            ]

            return create_text_result(json.dumps(notes_data, indent=2))

        elif name == "crawl_publication":
            handle = arguments["handle"]
            post_limit = arguments.get("post_limit", 5)
            notes_limit = arguments.get("notes_limit", 10)
            analyze = arguments.get("analyze", True)

            result = await asyncio.get_event_loop().run_in_executor(
                None, substack_client.crawl_publication,
                handle, post_limit, analyze, notes_limit
            )

            result_data = {
                "handle": result.handle,
                "author_profile": {
                    "display_name": result.author_profile.display_name if result.author_profile else None,
                    "bio": result.author_profile.bio if result.author_profile else None,
                    "avatar_url": str(result.author_profile.avatar_url) if result.author_profile and result.author_profile.avatar_url else None,
                    "location": result.author_profile.location if result.author_profile else None,
                    "followers": result.author_profile.followers if result.author_profile else None,
                    "publication": {
                        "handle": result.author_profile.publication.handle if result.author_profile and result.author_profile.publication else None,
                        "title": result.author_profile.publication.title if result.author_profile and result.author_profile.publication else None,
                        "url": str(result.author_profile.publication.url) if result.author_profile and result.author_profile.publication and result.author_profile.publication.url else None
                    } if result.author_profile and result.author_profile.publication else None
                } if result.author_profile else None,
                "post_summaries": [
                    {
                        "title": post.title,
                        "url": str(post.url),
                        "published": post.published_at.isoformat() if post.published_at else None,
                        "subtitle": post.excerpt,
                        "author": post.author
                    }
                    for post in result.post_summaries
                ],
                "analytics": [
                    {
                        "title": analytic.summary.title,
                        "url": str(analytic.summary.url),
                        "published": analytic.summary.published_at.isoformat() if analytic.summary.published_at else None,
                        "sentiment": {
                            "compound": analytic.sentiment.compound,
                            "positive": analytic.sentiment.positive,
                            "neutral": analytic.sentiment.neutral,
                            "negative": analytic.sentiment.negative
                        } if analytic.sentiment else None,
                        "readability": {
                            "flesch_reading_ease": analytic.flesch_reading_ease,
                            "flesch_kincaid_grade": analytic.flesch_kincaid_grade,
                            "lexical_diversity": analytic.lexical_diversity,
                            "average_sentence_length": analytic.average_sentence_length
                        },
                        "keywords": [
                            {"term": kw.term, "score": kw.score}
                            for kw in analytic.keywords[:10]
                        ],
                        "publishing_cadence_days": analytic.publishing_cadence_days,
                        "word_count": analytic.extra.get("word_count") if analytic.extra else None
                    }
                    for analytic in result.analytics
                ] if result.analytics else [],
                "notes": [
                    {
                        "id": note.id,
                        "content": note.content,
                        "published": note.published_at.isoformat() if note.published_at else None,
                        "author": note.author,
                        "url": note.url,
                        "like_count": note.like_count,
                        "comment_count": note.comment_count
                    }
                    for note in result.notes
                ]
            }

            return create_text_result(json.dumps(result_data, indent=2))

        else:
            return create_text_result(json.dumps({"error": f"Unknown tool: {name}"}), is_error=True)

    except Exception as e:
        logger.error(f"Error handling tool call {name}: {e}")
        return create_text_result(json.dumps({"error": str(e)}), is_error=True)


async def main():
    """Main entry point for the HTTP/SSE MCP server."""
    import os

    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    # Run the server using HTTP/SSE
    async with mcp.server.sse.sse_server(host, port) as server_context:
        await server.run(
            server_context[0],
            server_context[1],
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