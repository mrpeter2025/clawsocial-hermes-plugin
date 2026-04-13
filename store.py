"""JSON file persistence with thread-safe access (RLock).

Ported from src/store.ts — all public functions are protected by a reentrant
lock so the background WebSocket thread and the main Hermes thread can safely
share state.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

# ── Module state ─────────────────────────────────────────────────────

_data_dir: str | None = None
_lock = threading.RLock()

BACKUP_ROOT = Path.home() / ".clawsocial"


def init_store(directory: str) -> None:
    global _data_dir
    _data_dir = directory
    os.makedirs(directory, exist_ok=True)


def _get_data_dir() -> str:
    if _data_dir:
        return _data_dir
    fallback = str(Path.home() / ".hermes" / "data" / "clawsocial")
    os.makedirs(fallback, exist_ok=True)
    return fallback


def _state_file() -> str:
    return os.path.join(_get_data_dir(), "state.json")


def _sessions_file() -> str:
    return os.path.join(_get_data_dir(), "sessions.json")


def _settings_file() -> str:
    return os.path.join(_get_data_dir(), "settings.json")


# ── Low-level JSON I/O ──────────────────────────────────────────────

def _read_json(filepath: str, fallback: Any = None) -> Any:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback if fallback is not None else {}


def _write_json(filepath: str, data: Any) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Backup helpers ──────────────────────────────────────────────────

def _backup_dir(agent_id: str) -> Path:
    return BACKUP_ROOT / agent_id


def _backup_write(agent_id: str, name: str, data: Any) -> None:
    try:
        d = _backup_dir(agent_id)
        d.mkdir(parents=True, exist_ok=True)
        _write_json(str(d / name), data)
        (BACKUP_ROOT / "last_active").write_text(agent_id, encoding="utf-8")
    except Exception:
        pass  # best-effort


def _backup_read(agent_id: str, name: str, fallback: Any = None) -> Any:
    try:
        return _read_json(str(_backup_dir(agent_id) / name), fallback)
    except Exception:
        return fallback if fallback is not None else {}


def _get_last_active_agent_id() -> str | None:
    try:
        return (BACKUP_ROOT / "last_active").read_text(encoding="utf-8").strip() or None
    except Exception:
        return None


# ── Agent state ─────────────────────────────────────────────────────

def get_state() -> dict:
    with _lock:
        state = _read_json(_state_file(), {})
        if not state.get("agent_id") or not state.get("api_key"):
            last_id = _get_last_active_agent_id()
            if last_id:
                backup = _backup_read(last_id, "credentials.json", {})
                if backup.get("agent_id") and backup.get("api_key"):
                    _write_json(_state_file(), backup)
                    return backup
        return state


def set_state(data: dict) -> None:
    with _lock:
        s = get_state()
        merged = {**s, **data}
        _write_json(_state_file(), merged)
        if merged.get("agent_id") and merged.get("api_key"):
            _backup_write(merged["agent_id"], "credentials.json", {
                "agent_id": merged["agent_id"],
                "api_key": merged["api_key"],
                "public_name": merged.get("public_name"),
                "lang": merged.get("lang"),
            })


# ── Settings ────────────────────────────────────────────────────────

DEFAULT_SETTINGS: dict = {"notifyMode": "passive"}

NotifyMode = str  # "silent" | "passive" | "minimal" | "detail"


def get_settings() -> dict:
    with _lock:
        s = _read_json(_settings_file(), {})
        if not s:
            agent_id = get_state().get("agent_id")
            if agent_id:
                backup = _backup_read(agent_id, "settings.json", {})
                if backup:
                    _write_json(_settings_file(), backup)
                    return {**DEFAULT_SETTINGS, **backup}
        return {**DEFAULT_SETTINGS, **s}


def set_settings(data: dict) -> None:
    with _lock:
        s = get_settings()
        merged = {**s, **data}
        _write_json(_settings_file(), merged)
        agent_id = _read_json(_state_file(), {}).get("agent_id")
        if agent_id:
            _backup_write(agent_id, "settings.json", merged)


# ── Sessions ────────────────────────────────────────────────────────

def get_sessions() -> dict:
    with _lock:
        sessions = _read_json(_sessions_file(), {})
        if not sessions:
            agent_id = get_state().get("agent_id")
            if agent_id:
                backup = _backup_read(agent_id, "sessions.json", {})
                if backup:
                    _write_json(_sessions_file(), backup)
                    return backup
        return sessions


def get_session(session_id: str) -> dict | None:
    with _lock:
        return get_sessions().get(session_id)


def _write_sessions(sessions: dict) -> None:
    """Write sessions and backup. Caller must hold _lock."""
    _write_json(_sessions_file(), sessions)
    agent_id = _read_json(_state_file(), {}).get("agent_id")
    if agent_id:
        _backup_write(agent_id, "sessions.json", sessions)


def upsert_session(session_id: str, data: dict) -> dict:
    with _lock:
        sessions = get_sessions()
        existing = sessions.get(session_id, {"id": session_id, "messages": [], "unread": 0})
        sessions[session_id] = {**existing, **data, "id": session_id}
        _write_sessions(sessions)
        return sessions[session_id]


def add_message(session_id: str, msg: dict) -> None:
    with _lock:
        sessions = get_sessions()
        if session_id not in sessions:
            sessions[session_id] = {"id": session_id, "messages": [], "status": "active", "unread": 0}
        session = sessions[session_id]
        if "messages" not in session:
            session["messages"] = []
        session["messages"].append(msg)
        session["last_message"] = msg.get("content", "")
        session["last_active_at"] = msg.get("created_at", int(time.time()))
        if not msg.get("from_self"):
            session["unread"] = session.get("unread", 0) + 1
        session["updated_at"] = int(time.time())
        _write_sessions(sessions)


def get_total_unread() -> int:
    with _lock:
        sessions = get_sessions()
        return sum(s.get("unread", 0) for s in sessions.values())


def mark_read(session_id: str) -> None:
    with _lock:
        sessions = get_sessions()
        if session_id in sessions:
            sessions[session_id]["unread"] = 0
            _write_sessions(sessions)
            set_settings({"lastNotifiedUnreadTotal": get_total_unread()})


# ── Contacts ────────────────────────────────────────────────────────

def _contacts_file() -> str:
    return str(Path.home() / ".openclaw" / "clawsocial_contacts.json")


def read_contacts() -> list[dict]:
    with _lock:
        try:
            data = _read_json(_contacts_file(), {})
            if isinstance(data.get("contacts"), list) and data["contacts"]:
                return data["contacts"]
        except Exception:
            pass
        agent_id = get_state().get("agent_id")
        if agent_id:
            backup = _backup_read(agent_id, "contacts.json", {})
            if isinstance(backup.get("contacts"), list) and backup["contacts"]:
                os.makedirs(os.path.dirname(_contacts_file()), exist_ok=True)
                _write_json(_contacts_file(), {"contacts": backup["contacts"]})
                return backup["contacts"]
        return []


def upsert_contact(contact: dict) -> None:
    with _lock:
        contacts = read_contacts()
        idx = next((i for i, c in enumerate(contacts) if c.get("agent_id") == contact.get("agent_id")), -1)
        entry = {**contact, "added_at": contact.get("added_at", int(time.time()))}
        if idx >= 0:
            contacts[idx] = {**contacts[idx], **entry}
        else:
            contacts.append(entry)
        data = {"contacts": contacts}
        os.makedirs(os.path.dirname(_contacts_file()), exist_ok=True)
        _write_json(_contacts_file(), data)
        agent_id = _read_json(_state_file(), {}).get("agent_id")
        if agent_id:
            _backup_write(agent_id, "contacts.json", data)


def lookup_contact_by_name(name: str) -> list[dict]:
    with _lock:
        lower = name.lower()
        return [c for c in read_contacts() if lower in c.get("name", "").lower()]
