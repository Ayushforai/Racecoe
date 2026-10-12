"""Structured lookup cache for archive and OpenF1 packets. Never stores LLM answers."""

from __future__ import annotations

import copy
import functools
import hashlib
import inspect
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from utils.db import connect, database_url

_memory: dict[str, tuple[datetime, Any]] = {}

ARCHIVE_TTL_PAST = 7 * 24 * 3600
ARCHIVE_TTL_CURRENT = 6 * 3600
OPENF1_TTL_PAST = 6 * 3600
OPENF1_TTL_CURRENT = 15 * 60


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _current_year() -> int:
    return datetime.now().year


def ttl_seconds(family: str, year: int | None) -> int:
    current = _current_year()
    past = year is not None and int(year) < current
    if family == "openf1":
        return OPENF1_TTL_PAST if past else OPENF1_TTL_CURRENT
    return ARCHIVE_TTL_PAST if past else ARCHIVE_TTL_CURRENT


def cache_key(kind: str, parts: dict[str, Any]) -> str:
    payload = {"kind": kind, **_normalize(parts)}
    blob = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize(parts: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in parts.items():
        if key == "now" or value is None:
            continue
        if isinstance(value, str):
            value = value.strip().lower()
        out[key] = value
    return out


def _cacheable(value: Any) -> bool:
    return isinstance(value, (dict, list)) and value != {} and value != []


def get(kind: str, parts: dict[str, Any]) -> Any | None:
    key = cache_key(kind, parts)
    now = _now()
    if database_url():
        try:
            with connect() as conn:
                row = conn.execute(
                    """
                    SELECT payload FROM app.result_cache
                    WHERE cache_key = %s AND expires_at > now()
                    """,
                    (key,),
                ).fetchone()
            if row:
                return row["payload"]
            return None
        except Exception:
            return None
    entry = _memory.get(key)
    if not entry:
        return None
    expires, payload = entry
    if expires <= now:
        _memory.pop(key, None)
        return None
    return copy.deepcopy(payload)


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=_json_default))


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


def put(kind: str, parts: dict[str, Any], value: Any, *, ttl: int) -> None:
    if not _cacheable(value):
        return
    value = _json_safe(value)
    key = cache_key(kind, parts)
    expires = _now() + timedelta(seconds=max(1, ttl))
    if database_url():
        try:
            from psycopg.types.json import Json

            with connect() as conn:
                conn.execute(
                    """
                    INSERT INTO app.result_cache (cache_key, kind, payload, expires_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (cache_key) DO UPDATE
                    SET payload = EXCLUDED.payload,
                        kind = EXCLUDED.kind,
                        expires_at = EXCLUDED.expires_at
                    """,
                    (key, kind, Json(value), expires),
                )
        except Exception:
            return
        return
    _memory[key] = (expires, copy.deepcopy(value))


def lookup(
    kind: str,
    parts: dict[str, Any],
    loader: Callable[[], Any],
    *,
    family: str = "archive",
) -> Any:
    hit = get(kind, parts)
    if hit is not None:
        return hit
    value = loader()
    year = parts.get("year")
    try:
        year_int = int(year) if year is not None else None
    except (TypeError, ValueError):
        year_int = None
    put(kind, parts, value, ttl=ttl_seconds(family, year_int))
    return value


def cached(kind: str, *key_names: str, family: str = "archive"):
    """Cache a lookup function on named arguments (skips `now`)."""

    def decorator(fn: Callable) -> Callable:
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            names = key_names or tuple(n for n in bound.arguments if n != "now")
            parts = {name: bound.arguments.get(name) for name in names}
            return lookup(kind, parts, lambda: fn(*args, **kwargs), family=family)

        return wrapper

    return decorator


def clear_memory_for_tests() -> None:
    _memory.clear()
