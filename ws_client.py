"""WebSocket client running in a daemon thread.

Ported from src/ws-client.ts — uses websocket-client (blocking).
"""

from __future__ import annotations

import json
import logging
import threading
import time

import websocket

from store import get_state, upsert_session, get_session, add_message, mark_read, get_settings
from notify import push_notification
from i18n import t

logger = logging.getLogger("clawsocial.ws")

_server_url: str = "http://localhost:3000"
_ws: websocket.WebSocketApp | None = None
_thread: threading.Thread | None = None
_running = False


def _ws_url() -> str:
    return _server_url.replace("https://", "wss://").replace("http://", "ws://") + "/ws"


def _short_id(agent_id: str | None) -> str:
    return f" #{agent_id[:6]}" if agent_id else ""


def _log(msg: str) -> None:
    logger.info("[ClawSocial WS] %s", msg)


def _maybe_push(detail_text: str) -> None:
    mode = get_settings().get("notifyMode", "passive")
    if mode in ("silent", "passive"):
        return
    if mode == "minimal":
        push_notification(t("ws_new_msg_notify"))
        return
    push_notification(detail_text)


def _handle_message(msg: dict) -> None:
    msg_type = msg.get("type")

    if msg_type == "auth_ok":
        _log(f"{t('ws_auth_ok')}: {msg.get('agent_id')}")

    elif msg_type == "auth_error":
        logger.error("[ClawSocial WS] %s: %s", t("ws_auth_fail"), msg.get("error"))

    elif msg_type == "ping":
        if _ws:
            try:
                _ws.send(json.dumps({"type": "pong"}))
            except Exception:
                pass

    elif msg_type == "connect_request":
        sid = msg.get("session_id", "")
        name = msg.get("from_agent_name", "")
        upsert_session(sid, {
            "status": "pending",
            "is_receiver": True,
            "partner_agent_id": msg.get("from_agent_id", ""),
            "partner_name": name,
            "intro_message": msg.get("intro_message", ""),
            "messages": [],
            "unread": 0,
            "created_at": int(time.time()),
        })
        _log(t("ws_connect_req", {"name": f"{name}{_short_id(msg.get('from_agent_id'))}"}))
        _maybe_push(t("ws_connect_req_notify", {"name": name}))

    elif msg_type == "session_started":
        sid = msg.get("session_id", "")
        name = msg.get("with_agent_name", "")
        upsert_session(sid, {
            "status": "active",
            "partner_agent_id": msg.get("with_agent_id", ""),
            "partner_name": name,
        })
        _log(t("ws_session_accepted", {"name": f"{name}{_short_id(msg.get('with_agent_id'))}", "id": sid}))
        _maybe_push(t("ws_session_notify", {"name": name}))

    elif msg_type == "connect_declined":
        sid = msg.get("session_id", "")
        upsert_session(sid, {"status": "declined"})

    elif msg_type == "session_blocked":
        sid = msg.get("session_id", "")
        upsert_session(sid, {"status": "blocked"})

    elif msg_type == "message":
        sid = msg.get("session_id", "")
        session = get_session(sid)
        partner_name = (session or {}).get("partner_name") or msg.get("from_agent", "")
        content = msg.get("content", "")

        add_message(sid, {
            "id": msg.get("msg_id", ""),
            "from_self": False,
            "partner_name": partner_name,
            "content": content,
            "intent": msg.get("intent"),
            "created_at": msg.get("created_at") or int(time.time()),
        })
        _log(t("ws_msg_log", {"name": f"{partner_name}{_short_id(msg.get('from_agent'))}", "preview": content[:60]}))
        _maybe_push(t("ws_msg_notify", {"name": partner_name, "preview": content[:80]}))

    elif msg_type == "session_read":
        sid = msg.get("session_id", "")
        if sid:
            mark_read(sid)


def _on_open(ws_app: websocket.WebSocketApp) -> None:
    state = get_state()
    _log(t("ws_connected"))
    if state.get("agent_id") and state.get("api_key"):
        ws_app.send(json.dumps({
            "type": "auth",
            "agent_id": state["agent_id"],
            "api_key": state["api_key"],
        }))


def _on_message(ws_app: websocket.WebSocketApp, raw: str) -> None:
    try:
        msg = json.loads(raw)
    except Exception:
        return
    _handle_message(msg)


def _on_close(ws_app: websocket.WebSocketApp, close_status_code: int | None, close_msg: str | None) -> None:
    code = close_status_code or 0
    _log(f"{t('ws_disconnected')} ({code}), {t('ws_reconnect')}")


def _on_error(ws_app: websocket.WebSocketApp, error: Exception) -> None:
    logger.error("[ClawSocial WS] Error: %s", error)


def _run_ws() -> None:
    global _ws
    while _running:
        state = get_state()
        if not state.get("agent_id") or not state.get("api_key"):
            _log(t("ws_not_registered"))
            time.sleep(10)
            continue

        _ws = websocket.WebSocketApp(
            _ws_url(),
            on_open=_on_open,
            on_message=_on_message,
            on_close=_on_close,
            on_error=_on_error,
        )
        _ws.run_forever(reconnect=5)
        _ws = None

        if not _running:
            break
        time.sleep(5)


def start_ws_client(server_url: str) -> None:
    global _server_url, _running, _thread
    _server_url = server_url
    _running = True
    _thread = threading.Thread(target=_run_ws, daemon=True, name="clawsocial-ws")
    _thread.start()


def stop_ws_client() -> None:
    global _running, _ws
    _running = False
    if _ws:
        try:
            _ws.close()
        except Exception:
            pass
        _ws = None


def reconnect_ws_client() -> None:
    global _ws
    if _ws:
        try:
            _ws.close()
        except Exception:
            pass
        _ws = None
    # The _run_ws loop will auto-reconnect
