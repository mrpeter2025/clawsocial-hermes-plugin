"""Notification queue — pull model via pre_llm_call hook.

Uses a thread-safe queue that the pre_llm_call hook drains on each LLM turn.
"""

from __future__ import annotations

import collections
import threading

from store import get_settings, set_settings, get_total_unread
from i18n import t

_queue: collections.deque[str] = collections.deque()
_queue_lock = threading.Lock()
_session_id: str | None = None


def set_session_id(session_id: str) -> None:
    global _session_id
    _session_id = session_id


def push_notification(text: str) -> None:
    with _queue_lock:
        _queue.append(text)


def drain_notifications() -> str | None:
    with _queue_lock:
        if not _queue:
            return None
        items = list(_queue)
        _queue.clear()
    return "\n".join(items)


def check_passive_notification() -> None:
    settings = get_settings()
    if settings.get("notifyMode") != "passive":
        return

    current_total = get_total_unread()
    if current_total == 0:
        return

    last_notified = min(settings.get("lastNotifiedUnreadTotal", 0), current_total)

    if current_total > last_notified:
        new_count = current_total - last_notified
        if new_count == current_total:
            push_notification(t("ws_passive_notify", {"count": str(current_total)}))
        else:
            push_notification(t("ws_passive_notify_new", {"count": str(current_total), "new": str(new_count)}))
        set_settings({"lastNotifiedUnreadTotal": current_total})
