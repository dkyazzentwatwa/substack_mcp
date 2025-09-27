"""FastAPI surface that exposes the Substack MCP actions."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, StreamingResponse

from . import analysis
from .client import SubstackPublicClient
from .models import AuthorProfile, ContentAnalytics, CrawlResult, Note, PostContent, PostSummary


def create_app(client: SubstackPublicClient | None = None) -> FastAPI:
    app = FastAPI(title="Substack MCP", version="0.1.0")
    substack = client or SubstackPublicClient()

    @app.on_event("shutdown")
    def _shutdown() -> None:
        substack.close()

    payload = {
        "service": "Substack MCP",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "mcp_endpoint": "/mcp"
    }

    @app.get("/")
    async def root_info():
        """Return service information for GET requests to root."""
        return JSONResponse(payload)

    @app.get("/health")
    async def healthcheck() -> dict:
        return {
            "status": "ok",
            "throttle_seconds": substack.settings.throttle_seconds,
            "cache_ttl": substack.settings.cache_ttl.total_seconds(),
        }

    @app.get("/publications/{handle}/posts", response_model=list[PostSummary])
    async def list_posts(handle: str, limit: int = Query(10, ge=1, le=50)) -> list[PostSummary]:
        return await run_in_threadpool(substack.fetch_feed, handle, limit)

    @app.get("/posts", response_model=PostContent)
    async def get_post(url: str = Query(..., description="Full URL to a Substack post")) -> PostContent:
        try:
            return await run_in_threadpool(substack.fetch_post, url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/analytics", response_model=list[ContentAnalytics])
    async def get_analytics(handle: str, limit: int = Query(5, ge=1, le=25)) -> list[ContentAnalytics]:
        posts = await run_in_threadpool(substack.fetch_feed, handle, limit)
        results: list[ContentAnalytics] = []
        for summary in posts:
            content = await run_in_threadpool(substack.fetch_post, summary.url, posts)
            results.append(await run_in_threadpool(analysis.analyse_post, content, posts))
        return results

    @app.get("/notes/{handle}", response_model=list[Note])
    async def list_notes(handle: str, limit: int = Query(10, ge=1, le=50)) -> list[Note]:
        return await run_in_threadpool(substack.fetch_notes, handle, limit)

    @app.get("/authors/{handle}/profile", response_model=AuthorProfile)
    async def author_profile(handle: str) -> AuthorProfile:
        profile = await run_in_threadpool(substack.fetch_author_profile, handle)
        if profile is None:
            raise HTTPException(status_code=404, detail="Author not found")
        return profile

    @app.get("/crawl/{handle}", response_model=CrawlResult)
    async def crawl(
        handle: str,
        post_limit: int = Query(5, ge=1, le=25),
        notes_limit: int = Query(10, ge=0, le=50),
        analyse: bool = True,
    ) -> CrawlResult:
        return await run_in_threadpool(substack.crawl_publication, handle, post_limit, analyse, notes_limit)

    # MCP endpoint for ChatGPT custom connectors
    @app.post("/mcp")
    @app.get("/mcp")
    async def mcp_endpoint(request: Request):
        """Handle MCP requests according to Streamable HTTP transport spec."""
        accept_header = request.headers.get("accept", "")

        if request.method == "GET":
            # For GET requests, return SSE stream if requested
            if "text/event-stream" in accept_header:
                async def event_stream():
                    yield "data: {}\n\n"

                return StreamingResponse(
                    event_stream(),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
                )
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

        elif request.method == "POST":
            try:
                # Get JSON-RPC request
                body = await request.json()

                # Handle basic MCP requests
                if body.get("method") == "tools/list":
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "tools": [
                                {
                                    "name": "get_posts",
                                    "description": "Fetch recent posts from a Substack publication",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "handle": {"type": "string", "description": "Substack publication handle"}
                                        },
                                        "required": ["handle"]
                                    }
                                },
                                {
                                    "name": "get_post_content",
                                    "description": "Get full content of a specific Substack post",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "url": {"type": "string", "description": "Full URL to the Substack post"}
                                        },
                                        "required": ["url"]
                                    }
                                },
                                {
                                    "name": "search",
                                    "description": "Search for content across Substack publications",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {"type": "string", "description": "Search query to find relevant content"},
                                            "handle": {"type": "string", "description": "Optional: specific publication handle to search within"}
                                        },
                                        "required": ["query"]
                                    }
                                },
                                {
                                    "name": "fetch",
                                    "description": "Fetch content from specific Substack resources by ID or URL",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {
                                                "type": "string",
                                                "description": "Resource identifier in format 'post:URL' or 'publication:handle'"
                                            }
                                        },
                                        "required": ["id"]
                                    }
                                }
                            ]
                        }
                    })

                elif body.get("method") == "tools/call":
                    params = body.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})

                    if tool_name == "get_posts":
                        handle = arguments.get("handle")
                        if not handle:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32602, "message": "Missing required parameter: handle"}
                            })

                        posts = await run_in_threadpool(substack.fetch_feed, handle, 10)
                        result_text = f"Recent posts from {handle}:\n\n"
                        for post in posts[:5]:
                            result_text += f"- {post.title}\n  {post.url}\n  Published: {post.published_at}\n\n"

                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "result": {"content": [{"type": "text", "text": result_text}]}
                        })

                    elif tool_name == "get_post_content":
                        url = arguments.get("url")
                        if not url:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32602, "message": "Missing required parameter: url"}
                            })

                        try:
                            post = await run_in_threadpool(substack.fetch_post, url)
                            result_text = f"Title: {post.summary.title}\n\nContent:\n{post.text[:2000]}..."

                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "result": {"content": [{"type": "text", "text": result_text}]}
                            })
                        except Exception as e:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32603, "message": f"Error fetching post: {str(e)}"}
                            })

                    elif tool_name == "search":
                        query = arguments.get("query")
                        handle = arguments.get("handle")

                        if not query:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32602, "message": "Missing required parameter: query"}
                            })

                        try:
                            # If handle is provided, search within that publication
                            if handle:
                                posts = await run_in_threadpool(substack.fetch_feed, handle, 20)
                                # Filter posts that match the query (simple text search)
                                matching_posts = [
                                    post for post in posts
                                    if query.lower() in post.title.lower() or (post.excerpt and query.lower() in post.excerpt.lower())
                                ]

                                result_text = f"Search results for '{query}' in {handle}:\n\n"
                                if matching_posts:
                                    for post in matching_posts[:5]:
                                        excerpt = post.excerpt or "No excerpt available"
                                        result_text += f"- {post.title}\n  {excerpt}\n  {post.url}\n  Published: {post.published_at}\n\n"
                                else:
                                    result_text += "No matching posts found."
                            else:
                                # Generic search - this is a simplified implementation
                                # In a real implementation, you might search across multiple publications
                                result_text = f"Search query: '{query}'\n\nTo search within a specific publication, please provide the publication handle. For example, you can search within publications like 'stratechery', 'platformer', or any other Substack handle."

                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "result": {"content": [{"type": "text", "text": result_text}]}
                            })
                        except Exception as e:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32603, "message": f"Error performing search: {str(e)}"}
                            })

                    elif tool_name == "fetch":
                        resource_id = arguments.get("id")

                        if not resource_id:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32602, "message": "Missing required parameter: id"}
                            })

                        try:
                            # Parse resource ID format: 'post:URL' or 'publication:handle'
                            if resource_id.startswith("post:"):
                                # Fetch specific post content by URL
                                url = resource_id[5:]  # Remove 'post:' prefix
                                post = await run_in_threadpool(substack.fetch_post, url)
                                result_text = f"Title: {post.summary.title}\n\nAuthor: {post.summary.author}\nPublished: {post.summary.published_at}\nURL: {post.summary.url}\n\nContent:\n{post.text}"
                            elif resource_id.startswith("publication:"):
                                # Fetch recent posts from publication
                                handle = resource_id[12:]  # Remove 'publication:' prefix
                                posts = await run_in_threadpool(substack.fetch_feed, handle, 10)
                                result_text = f"Recent posts from {handle}:\n\n"
                                for post in posts:
                                    excerpt = post.excerpt or "No excerpt available"
                                    result_text += f"- {post.title}\n  {excerpt}\n  {post.url}\n  Published: {post.published_at}\n\n"
                            elif resource_id.startswith("http"):
                                # Direct URL - treat as post URL
                                post = await run_in_threadpool(substack.fetch_post, resource_id)
                                result_text = f"Title: {post.summary.title}\n\nAuthor: {post.summary.author}\nPublished: {post.summary.published_at}\nURL: {post.summary.url}\n\nContent:\n{post.text}"
                            else:
                                # Treat as publication handle
                                posts = await run_in_threadpool(substack.fetch_feed, resource_id, 10)
                                result_text = f"Recent posts from {resource_id}:\n\n"
                                for post in posts:
                                    excerpt = post.excerpt or "No excerpt available"
                                    result_text += f"- {post.title}\n  {excerpt}\n  {post.url}\n  Published: {post.published_at}\n\n"

                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "result": {"content": [{"type": "text", "text": result_text}]}
                            })
                        except Exception as e:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32603, "message": f"Error fetching content: {str(e)}"}
                            })

                    else:
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                        })

                elif body.get("method") == "initialize":
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": {
                                "name": "substack-mcp",
                                "version": "0.1.0"
                            }
                        }
                    })

                else:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {"code": -32601, "message": "Method not found"}
                    })

            except Exception as e:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id") if 'body' in locals() else None,
                    "error": {"code": -32603, "message": "Internal error"}
                })

    # MCP endpoint at root for ChatGPT discovery
    @app.post("/")
    async def mcp_root_endpoint(request: Request):
        """Handle MCP requests at root path for ChatGPT compatibility."""
        return await mcp_endpoint(request)

    # ChatGPT search aggregation endpoint
    @app.post("/search")
    async def chatgpt_search(request: Request):
        """Handle ChatGPT's search aggregation requests."""
        try:
            body = await request.json()

            # Extract search parameters from ChatGPT's format
            source_params = body.get("source_specific_search_parameters", {})
            connector_id = "slurm_mcp_connector_68d74578ccd88191adf2f7eb8c8f7301"

            if connector_id in source_params:
                params_list = source_params[connector_id]
                if params_list and len(params_list) > 0:
                    search_params = params_list[0]
                    query = search_params.get("query")
                    handle = search_params.get("handle")

                    if query:
                        # Use existing search logic
                        if handle:
                            posts = await run_in_threadpool(substack.fetch_feed, handle, 20)
                            matching_posts = [
                                post for post in posts
                                if query.lower() in post.title.lower() or (post.excerpt and query.lower() in post.excerpt.lower())
                            ]

                            results = []
                            for post in matching_posts[:5]:
                                excerpt = post.excerpt or "No excerpt available"
                                results.append({
                                    "title": post.title,
                                    "content": excerpt,
                                    "url": str(post.url),
                                    "published_at": post.published_at.isoformat() if post.published_at else None,
                                    "source": handle
                                })
                        else:
                            # Generic search response
                            results = [{
                                "title": f"Search Query: {query}",
                                "content": f"To search within a specific publication, provide the publication handle. Available for search: stratechery, platformer, importai, and other Substack handles.",
                                "url": "",
                                "source": "search_guidance"
                            }]

                        return JSONResponse({"results": results})

            # Default empty response
            return JSONResponse({"results": []})

        except Exception as e:
            return JSONResponse({"results": [], "error": str(e)})

    # Handle favicon requests
    @app.get("/favicon.ico")
    async def favicon():
        """Return empty response for favicon requests."""
        return Response(status_code=204)

    return app


# Lazily instantiate a default app so `uvicorn substack_mcp.server:app` works.
app = create_app()
