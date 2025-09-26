"""FastAPI surface that exposes the Substack MCP actions."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

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

    return app


# Lazily instantiate a default app so `uvicorn substack_mcp.server:app` works.
app = create_app()
