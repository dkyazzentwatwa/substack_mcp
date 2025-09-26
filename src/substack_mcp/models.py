"""Pydantic models that describe Substack artefacts and analytics surfaces."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class PublicationRef(BaseModel):
    """Minimal identity of a Substack publication."""

    handle: str = Field(..., description="Substack handle, e.g. 'littlehakr'.")
    title: Optional[str] = Field(None, description="Friendly title scraped from the site.")
    url: Optional[HttpUrl] = Field(None, description="Canonical URL for the publication homepage.")


class AuthorProfile(BaseModel):
    """Basic author/profile metadata."""

    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    location: Optional[str] = None
    publication: Optional[PublicationRef] = None
    followers: Optional[int] = Field(None, description="Best-effort follower count when visible.")
    social_links: Dict[str, HttpUrl] = Field(default_factory=dict)
    raw: Dict[str, Any] = Field(default_factory=dict, description="Raw JSON payload for debugging.")


class PostSummary(BaseModel):
    """Summary info from RSS feeds or index pages."""

    id: Optional[str] = Field(None, description="Stable identifier if available (e.g. post id).")
    title: str
    url: HttpUrl
    published_at: Optional[datetime] = Field(None, description="Publication timestamp.")
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
    excerpt: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    publication: Optional[PublicationRef] = None


class PostContent(BaseModel):
    """Full content for a post."""

    summary: PostSummary
    html: Optional[str] = Field(None, description="Canonical HTML as served by Substack.")
    text: Optional[str] = Field(None, description="Plain text fallback (stripped HTML).")
    cover_image: Optional[HttpUrl] = None
    topics: List[str] = Field(default_factory=list)
    word_count: Optional[int] = None
    minute_read: Optional[int] = Field(
        None, description="Minutes to read estimate, if provided by Substack or computed locally."
    )
    raw: Dict[str, Any] = Field(default_factory=dict)


class Comment(BaseModel):
    """A comment on a post."""

    id: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    published_at: Optional[datetime] = None
    replies: List["Comment"] = Field(default_factory=list)


class Note(BaseModel):
    """Substack note (Twitter-like short post)."""

    id: str
    url: HttpUrl
    author: Optional[str] = None
    content: str
    published_at: Optional[datetime] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class SentimentBreakdown(BaseModel):
    """Sentiment metrics from VADER."""

    negative: float
    neutral: float
    positive: float
    compound: float


class KeywordScore(BaseModel):
    """Simple keyword/phrase importance score."""

    term: str
    score: float


class ContentAnalytics(BaseModel):
    """Basic analytics derived from a post."""

    summary: PostSummary
    sentiment: Optional[SentimentBreakdown] = None
    keywords: List[KeywordScore] = Field(default_factory=list)
    flesch_reading_ease: Optional[float] = None
    flesch_kincaid_grade: Optional[float] = None
    lexical_diversity: Optional[float] = None
    average_sentence_length: Optional[float] = None
    publishing_cadence_days: Optional[float] = Field(
        None,
        description="Average number of days between recent posts at fetch time (if history available).",
    )
    extra: Dict[str, Any] = Field(default_factory=dict)


class CrawlResult(BaseModel):
    """Aggregate response from the MCP layer."""

    publication: PublicationRef
    posts: List[PostSummary] = Field(default_factory=list)
    notes: List[Note] = Field(default_factory=list)
    author: Optional[AuthorProfile] = None
    analytics: List[ContentAnalytics] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

