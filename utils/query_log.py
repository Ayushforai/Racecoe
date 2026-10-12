"""Write-only log of user questions. Never read during answering or RAG."""

from __future__ import annotations

from contextvars import ContextVar

from utils.db import connect, database_url

_session_id: ContextVar[str | None] = ContextVar("query_log_session_id", default=None)
_user_id: ContextVar[str | None] = ContextVar("query_log_user_id", default=None)

# In-process fallback when DATABASE_URL is unset (tests / local CSV mode).
_memory: list[dict] = []


def bind(*, session_id: str | None = None, user_id: str | None = None) -> None:
    _session_id.set((session_id or "").strip() or None)
    _user_id.set((user_id or "").strip() or None)


def record(query: str, *, route: str = "", session_id: str | None = None, user_id: str | None = None) -> None:
    text = (query or "").strip()
    if not text:
        return
    sid = (session_id if session_id is not None else _session_id.get()) or None
    uid = (user_id if user_id is not None else _user_id.get()) or None
    route = (route or "").strip() or None
    row = {"session_id": sid, "user_id": uid, "query": text, "route": route}
    if database_url():
        try:
            with connect() as conn:
                conn.execute(
                    """
                    INSERT INTO app.query_log (session_id, user_id, query, route)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (sid, uid, text, route),
                )
            return
        except Exception:
            return
    _memory.append(row)


def memory_rows() -> list[dict]:
    """Test helper. Production answering must not call this."""
    return list(_memory)


def clear_memory_for_tests() -> None:
    _memory.clear()
    _session_id.set(None)
    _user_id.set(None)
