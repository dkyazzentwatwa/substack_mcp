"""Simple in-memory caching utilities."""

from __future__ import annotations

import threading
from functools import wraps
from typing import Any, Callable, Optional

from cachetools import TTLCache

from .settings import SETTINGS


_cache = TTLCache(maxsize=256, ttl=SETTINGS.cache_ttl.total_seconds())
_lock = threading.RLock()


def _normalise(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple, set)):
        return tuple(_normalise(v) for v in value)
    if isinstance(value, dict):
        return tuple(sorted((k, _normalise(v)) for k, v in value.items()))
    # Fallback: use repr (good enough for self references)
    return repr(value)


def cached(func: Callable) -> Callable:
    """Decorator that caches function output based on args/kwargs."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        key = (func.__qualname__, _normalise(args), _normalise(kwargs))
        with _lock:
            if key in _cache:
                return _cache[key]
        result = func(*args, **kwargs)
        with _lock:
            _cache[key] = result
        return result

    return wrapper


def clear_cache(key_prefix: Optional[str] = None) -> None:
    """Clear cache optionally scoped by function qualname prefix."""

    with _lock:
        if key_prefix is None:
            _cache.clear()
            return
        keys_to_pop = [key for key in _cache if isinstance(key, tuple) and key[0].startswith(key_prefix)]
        for key in keys_to_pop:
            _cache.pop(key, None)


__all__ = ["cached", "clear_cache"]

