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
    }

    @app.middleware("http")
    async def _root_passthrough(request, call_next):  # type: ignore[override]
        if request.url.path == "/" and request.method in {"GET", "POST", "HEAD", "OPTIONS"}:
            return JSONResponse(payload)
        return await call_next(request)

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

    # Handle favicon requests
    @app.get("/favicon.ico")
    async def favicon():
        """Return empty response for favicon requests."""
        return Response(status_code=204)

    return app


# Lazily instantiate a default app so `uvicorn substack_mcp.server:app` works.
app = create_app()
