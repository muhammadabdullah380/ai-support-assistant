"""In-memory, per-session conversation history.

Good enough for a single-process MVP. For production with multiple workers
or restarts, swap this dict for Redis (same get/add/clear interface).
"""
from collections import defaultdict
from app.config import settings

_sessions: dict[str, list[dict]] = defaultdict(list)


def get_history(session_id: str) -> list[dict]:
    return _sessions[session_id]


def add_turn(session_id: str, role: str, content: str):
    history = _sessions[session_id]
    history.append({"role": role, "content": content})
    max_messages = settings.MAX_HISTORY_TURNS * 2  # user+assistant per turn
    if len(history) > max_messages:
        _sessions[session_id] = history[-max_messages:]


def clear_session(session_id: str):
    _sessions.pop(session_id, None)
