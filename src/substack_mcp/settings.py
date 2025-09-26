"""Centralised runtime configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)


@dataclass
class RuntimeSettings:
    """Settings representing HTTP + caching behaviour."""

    user_agent: str = DEFAULT_USER_AGENT
    connect_timeout: float = 10.0
    read_timeout: float = 15.0
    cache_ttl: timedelta = timedelta(minutes=15)
    throttle_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "RuntimeSettings":
        return cls(
            user_agent=os.getenv("SUBSTACK_MCP_USER_AGENT", DEFAULT_USER_AGENT),
            connect_timeout=float(os.getenv("SUBSTACK_MCP_CONNECT_TIMEOUT", 10.0)),
            read_timeout=float(os.getenv("SUBSTACK_MCP_READ_TIMEOUT", 15.0)),
            cache_ttl=timedelta(
                seconds=float(os.getenv("SUBSTACK_MCP_CACHE_TTL", 15 * 60))
            ),
            throttle_seconds=float(os.getenv("SUBSTACK_MCP_THROTTLE", 1.0)),
        )


SETTINGS = RuntimeSettings.from_env()

