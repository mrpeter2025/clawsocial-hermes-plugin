"""HTTP client for the Claw-Social server.

Ported from src/api.ts — uses httpx in synchronous mode with a threading lock
for safe concurrent access from the main thread and the WS daemon thread.
"""

from __future__ import annotations

import threading
from urllib.parse import urlencode

import httpx

from store import get_state, set_state

_server_url: str = "http://localhost:3000"
_client: httpx.Client | None = None
_client_lock = threading.Lock()


def init_api(url: str) -> None:
    global _server_url, _client
    _server_url = url
    _client = httpx.Client(timeout=30.0)


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(timeout=30.0)
    return _client


def _ensure_token() -> str | None:
    state = get_state()
    if state.get("token"):
        return state["token"]

    if state.get("agent_id") and state.get("api_key"):
        try:
            with _client_lock:
                resp = _get_client().post(
                    f"{_server_url}/agents/auth",
                    json={"agent_id": state["agent_id"], "api_key": state["api_key"]},
                    headers={"Content-Type": "application/json"},
                )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("token"):
                    set_state({"token": data["token"]})
                    return data["token"]
        except Exception:
            pass
    return None


def _do_request(method: str, path: str, body: dict | None = None, auth_token: str | None = None) -> tuple[int, dict]:
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "X-App-Name": "clawsocial-plugin",
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    kwargs: dict = {"headers": headers}
    if body is not None:
        kwargs["json"] = body

    with _client_lock:
        resp = _get_client().request(method, f"{_server_url}{path}", **kwargs)
    try:
        data = resp.json()
    except Exception:
        data = {}
    return resp.status_code, data


def request(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    auth_token = token or _ensure_token()

    status, data = _do_request(method, path, body, auth_token)

    # On 401, clear stale token, refresh with api_key and retry once
    if status == 401 and not token:
        set_state({"token": None})
        state = get_state()
        if state.get("agent_id") and state.get("api_key"):
            try:
                with _client_lock:
                    resp = _get_client().post(
                        f"{_server_url}/agents/auth",
                        json={"agent_id": state["agent_id"], "api_key": state["api_key"]},
                        headers={"Content-Type": "application/json"},
                    )
                if resp.status_code == 200:
                    refresh_data = resp.json()
                    if refresh_data.get("token"):
                        set_state({"token": refresh_data["token"]})
                        auth_token = refresh_data["token"]
                        status, data = _do_request(method, path, body, auth_token)
            except Exception:
                pass

    if status < 200 or status >= 300:
        error_msg = data.get("error", f"HTTP {status}") if isinstance(data, dict) else f"HTTP {status}"
        raise Exception(error_msg)

    return data


# ── Public API methods ──────────────────────────────────────────────

def register(body: dict) -> dict:
    return request("POST", "/agents/register", body)


def auth(agent_id: str, api_key: str) -> dict:
    return request("POST", "/agents/auth", {"agent_id": agent_id, "api_key": api_key})


def me() -> dict:
    return request("GET", "/agents/me")


def search(body: dict) -> dict:
    return request("POST", "/agents/search", body)


def search_by_name(q: str, intent: str | None = None) -> dict:
    params: dict[str, str] = {"q": q}
    if intent:
        params["intent"] = intent
    return request("GET", f"/agents/search/name?{urlencode(params)}")


def get_agent(agent_id: str) -> dict:
    return request("GET", f"/agents/{agent_id}")


def connect(body: dict) -> dict:
    return request("POST", "/sessions/connect", body)


def send_message(session_id: str, body: dict) -> dict:
    return request("POST", f"/sessions/{session_id}/messages", body)


def get_messages(session_id: str, since: int | None = None) -> dict:
    path = f"/sessions/{session_id}/messages"
    if since is not None:
        path += f"?since={since}"
    return request("GET", path)


def list_sessions() -> dict:
    return request("GET", "/sessions")


def get_session(session_id: str) -> dict:
    return request("GET", f"/sessions/{session_id}")


def open_inbox_token() -> dict:
    return request("POST", "/auth/web-token")


def update_profile(body: dict) -> dict:
    return request("PATCH", "/agents/me", body)


def get_card() -> dict:
    return request("GET", "/agents/me/card")


def block_agent(agent_id: str) -> dict:
    return request("POST", f"/agents/{agent_id}/block")
