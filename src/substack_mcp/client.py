"""HTTP client for public Substack content."""

from __future__ import annotations

import time
from typing import List, Optional

import httpx

from . import analysis, parsers
from .cache import cached
from .models import AuthorProfile, ContentAnalytics, CrawlResult, Note, PostContent, PostSummary, PublicationRef
from .settings import RuntimeSettings, SETTINGS


def _extract_handle_from_url(url: str) -> str:
    parsed = httpx.URL(url)
    host = parsed.host or ""
    if not host.endswith(".substack.com"):
        raise ValueError(f"Unsupported Substack URL: {url}")
    return host.split(".")[0]


class SubstackPublicClient:
    """Best-effort scraper for public Substack artefacts."""

    def __init__(self, settings: RuntimeSettings | None = None, client: httpx.Client | None = None) -> None:
        self.settings = settings or SETTINGS
        headers = {
            "user-agent": self.settings.user_agent,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/ *;q=0.8",
            "accept-language": "en-US,en;q=0.9",
        }
        timeout = httpx.Timeout(
            timeout=self.settings.read_timeout,
            connect=self.settings.connect_timeout,
            read=self.settings.read_timeout,
        )
        self._client = client or httpx.Client(headers=headers, timeout=timeout)
        self._last_request_ts = 0.0

    def close(self) -> None:
        self._client.close()

    def _throttle(self) -> None:
        delta = time.time() - self._last_request_ts
        remaining = self.settings.throttle_seconds - delta
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_ts = time.time()

    def _get(self, url: str) -> httpx.Response:
        self._throttle()
        response = self._client.get(url)
        response.raise_for_status()
        return response

    @cached
    def fetch_feed(self, handle: str, limit: int | None = 20) -> List[PostSummary]:
        url = f"https://{handle}.substack.com/feed"
        response = self._get(url)
        return parsers.parse_feed(handle, response.text, limit=limit)

    @cached
    def fetch_post(self, url: str, history: Optional[List[PostSummary]] = None) -> PostContent:
        handle = _extract_handle_from_url(url)
        response = self._get(url)
        return parsers.parse_post_html(handle=handle, url=url, html=response.text, history=history)

    @cached
    def fetch_author_profile(self, handle: str) -> Optional[AuthorProfile]:
        about_url = f"https://{handle}.substack.com/about"
        try:
            response = self._get(about_url)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise
        return parsers.parse_author_profile(handle, response.text)

    @cached
    def fetch_notes(self, handle: str, limit: int | None = 20) -> List[Note]:
        # Use the publication subdomain API endpoint
        notes_url = f"https://{handle}.substack.com/api/v1/notes?limit={limit or 20}"
        try:
            response = self._get(notes_url)
        except httpx.HTTPStatusError as exc:
            # Handle redirects, authorization, and not found errors gracefully
            if exc.response.status_code in {302, 401, 403, 404}:
                # Notes endpoint is not accessible
                return []
            raise
        notes = parsers.parse_notes_json(handle, response.text)
        return notes[:limit] if limit else notes

    def search_notes(self, handle: str, query: str, limit: int | None = 20) -> List[Note]:
        """Search notes by content text matching."""
        all_notes = self.fetch_notes(handle, limit=limit or 50)
        query_lower = query.lower()

        # Filter notes that contain the search query (case-insensitive)
        matching_notes = [
            note for note in all_notes
            if query_lower in note.content.lower()
        ]

        return matching_notes[:limit] if limit else matching_notes

    def crawl_publication(
        self,
        handle: str,
        post_limit: int = 5,
        analyse: bool = True,
        notes_limit: int = 10,
    ) -> CrawlResult:
        posts = self.fetch_feed(handle, limit=post_limit)
        notes = self.fetch_notes(handle, limit=notes_limit)
        author_profile = self.fetch_author_profile(handle)

        analytics_payload: List[ContentAnalytics] = []
        if analyse:
            history = posts[:post_limit]
            for summary in posts:
                try:
                    content = self.fetch_post(summary.url, history=history)
                except Exception as exc:  # noqa: BLE001
                    analytics_payload.append(
                        ContentAnalytics(
                            summary=summary,
                            extra={"error": str(exc)},
                        )
                    )
                    continue
                analytics_payload.append(analysis.analyse_post(content, history=history))

        publication = posts[0].publication if posts else PublicationRef(handle=handle)

        return CrawlResult(
            publication=publication,
            posts=posts,
            notes=notes,
            author=author_profile,
            analytics=analytics_payload,
        )


__all__ = ["SubstackPublicClient"]

