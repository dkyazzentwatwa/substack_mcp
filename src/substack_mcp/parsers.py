"""Utilities for parsing feed, HTML, and notes payloads from Substack."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, Iterable, List, Optional

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from .models import AuthorProfile, Note, PostContent, PostSummary, PublicationRef


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return date_parser.parse(value)
    except Exception:
        return None


def _guess_publication(handle: str, title: Optional[str] = None) -> PublicationRef:
    url = f"https://{handle}.substack.com"
    return PublicationRef(handle=handle, title=title, url=url)


def parse_feed(handle: str, feed_text: str, limit: Optional[int] = None) -> List[PostSummary]:
    """Parse an RSS/Atom feed into `PostSummary` records."""

    feed = feedparser.parse(feed_text)
    title = feed.feed.get("title") if feed.feed else None
    publication = _guess_publication(handle, title)
    entries: Iterable[Dict] = feed.entries or []
    results: List[PostSummary] = []
    for entry in entries:
        summary = PostSummary(
            id=str(entry.get("id")) if entry.get("id") else None,
            title=entry.get("title", "Untitled"),
            url=entry.get("link"),
            published_at=_parse_datetime(entry.get("published") or entry.get("updated")),
            updated_at=_parse_datetime(entry.get("updated")),
            author=entry.get("author"),
            excerpt=entry.get("summary"),
            tags=[tag.get("term") for tag in entry.get("tags", []) if tag.get("term")],
            publication=publication,
        )
        results.append(summary)
        if limit and len(results) >= limit:
            break
    return results


def _extract_next_data(soup: BeautifulSoup) -> Dict:
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return {}
    try:
        return json.loads(script.string)
    except json.JSONDecodeError:
        return {}


def _plain_text_from_html(html: Optional[str]) -> Optional[str]:
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(separator="\n", strip=True)


def parse_post_html(handle: str, url: str, html: str, history: Optional[List[PostSummary]] = None) -> PostContent:
    """Parse a post page."""

    soup = BeautifulSoup(html, "lxml")
    next_data = _extract_next_data(soup)

    page_props = next_data.get("props", {}).get("pageProps", {})
    post_payload = page_props.get("post") or page_props.get("fallbackPost") or {}

    # Some Substack pages embed a JSON blob under `initialState`
    if not post_payload:
        state = page_props.get("initialState") or next_data.get("__STATE__")
        if isinstance(state, dict):
            post_payload = state.get("post") or {}

    title = (
        post_payload.get("title")
        or soup.find("h1", attrs={"data-element": "post-title"})
        or soup.find("h1")
    )
    if hasattr(title, "get_text"):
        title = title.get_text(strip=True)

    author = None
    if isinstance(post_payload.get("author"), dict):
        author = post_payload.get("author", {}).get("name")
    elif page_props.get("publication"):  # fallback to publication author
        author = (
            page_props.get("publication", {})
            .get("authors", [{}])[0]
            .get("name")
        )

    published_at = _parse_datetime(post_payload.get("publishedAt") or post_payload.get("publishedAtLocal"))
    updated_at = _parse_datetime(post_payload.get("updatedAt"))

    cover_image = post_payload.get("coverImage") or post_payload.get("coverImageUrl")

    body_html = (
        post_payload.get("body_html")
        or post_payload.get("body")
        or page_props.get("bodyHtml")
    )
    if not body_html:
        article = soup.find("article")
        if article:
            body_html = str(article)

    plain_text = _plain_text_from_html(body_html)

    summary = PostSummary(
        id=str(post_payload.get("id")) if post_payload.get("id") else None,
        title=title or "Untitled",
        url=url,
        published_at=published_at,
        updated_at=updated_at,
        author=author,
        excerpt=_plain_text_from_html(post_payload.get("subtitle")) if post_payload.get("subtitle") else None,
        tags=post_payload.get("tags", []) or page_props.get("tags", []),
        publication=_guess_publication(handle, page_props.get("publication", {}).get("title")),
    )

    topics = []
    if "seoTopics" in page_props:
        topics = page_props.get("seoTopics") or []
    elif isinstance(post_payload.get("topics"), list):
        topics = [topic.get("title") if isinstance(topic, dict) else topic for topic in post_payload["topics"]]

    minute_read = post_payload.get("readingTime")
    if minute_read is None and plain_text:
        minute_read = max(1, len(plain_text.split()) // 220)

    return PostContent(
        summary=summary,
        html=body_html,
        text=plain_text,
        cover_image=cover_image,
        topics=[topic for topic in topics if topic],
        word_count=len(plain_text.split()) if plain_text else None,
        minute_read=minute_read,
        raw={
            "page_props": page_props,
            "post": post_payload,
            "history_count": len(history or []),
        },
    )


def parse_author_profile(handle: str, html: str) -> AuthorProfile:
    soup = BeautifulSoup(html, "lxml")
    next_data = _extract_next_data(soup)
    page_props = next_data.get("props", {}).get("pageProps", {})
    publication = page_props.get("publication") or {}
    author = page_props.get("author") or publication.get("author") or {}

    avatar = None
    if isinstance(author, dict):
        avatar = author.get("imageUrl") or author.get("profileImageUrl")

    social_links = {}
    if isinstance(author, dict):
        for field in ("twitter_url", "website", "mastodon_url", "threads_url"):
            value = author.get(field)
            if value:
                social_links[field.replace("_url", "")] = value

    return AuthorProfile(
        display_name=author.get("name") if isinstance(author, dict) else None,
        bio=author.get("bio") if isinstance(author, dict) else None,
        avatar_url=avatar,
        location=author.get("location") if isinstance(author, dict) else None,
        publication=_guess_publication(handle, publication.get("title")),
        followers=publication.get("subscriberCount"),
        social_links=social_links,
        raw={
            "page_props": page_props,
            "author": author,
        },
    )


def parse_notes_html(handle: str, html: str) -> List[Note]:
    soup = BeautifulSoup(html, "lxml")
    next_data = _extract_next_data(soup)
    page_props = next_data.get("props", {}).get("pageProps", {})

    notes_payload: Iterable[Dict] = []
    if isinstance(page_props.get("notes"), list):
        notes_payload = page_props["notes"]
    elif isinstance(page_props.get("initialState"), dict):
        notes_payload = page_props["initialState"].get("notes", [])

    notes: List[Note] = []
    for item in notes_payload:
        if not isinstance(item, dict):
            continue
        note_id = str(item.get("id") or item.get("note_id"))
        if not note_id:
            continue
        notes.append(
            Note(
                id=note_id,
                url=item.get("permalink")
                or f"https://substack.com/@{handle}/note/{note_id}",
                author=item.get("user", {}).get("name") if isinstance(item.get("user"), dict) else None,
                content=item.get("body") or item.get("body_html") or "",
                published_at=_parse_datetime(item.get("published_at") or item.get("created_at")),
                reaction_count=item.get("reaction_count", 0),
                restacks=item.get("restacks", 0),
                children_count=item.get("children_count", 0),
                raw=item,
            )
        )
    return notes


def parse_notes_json(handle: str, json_text: str) -> List[Note]:
    """Parse notes from the /api/v1/notes JSON endpoint."""
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return []

    items = data.get("items", [])
    notes: List[Note] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        # Notes are wrapped in a comment object
        comment = item.get("comment")
        if not isinstance(comment, dict):
            continue

        note_id = str(comment.get("id"))
        if not note_id:
            continue

        # Build note URL
        note_url = f"https://substack.com/@{handle}/note/c-{note_id}"

        # Extract text content from body or body_json
        content = comment.get("body", "")

        notes.append(
            Note(
                id=note_id,
                url=note_url,
                author=comment.get("name"),
                content=content,
                published_at=_parse_datetime(comment.get("date")),
                reaction_count=comment.get("reaction_count", 0),
                restacks=comment.get("restacks", 0),
                children_count=comment.get("children_count", 0),
                raw=comment,
            )
        )

    return notes


__all__ = [
    "parse_feed",
    "parse_post_html",
    "parse_author_profile",
    "parse_notes_html",
    "parse_notes_json",
]

