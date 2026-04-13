"""Local web inbox server — HTTP server in daemon thread.

Ported from src/local-server.ts.
"""

from __future__ import annotations

import json
import re
import socket
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import api as api_client
import store
from i18n import t, get_lang, format_time, format_datetime

_server: HTTPServer | None = None
_port: int | None = None


def _find_available_port(start: int = 7747) -> int:
    for port in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError("No available port found")


# ── HTML helpers ─────────────────────────────────────────────────────

def _esc(s: str) -> str:
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _esc_js(s: str) -> str:
    return (str(s)
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("<", "\\x3c")
            .replace("\n", "\\n")
            .replace("\r", "\\r"))


def _esc_content(s: str) -> str:
    return _esc(s).replace("\n", "<br>")


def _html_lang() -> str:
    return "zh-CN" if get_lang() == "zh" else "en"


SHARED_CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0f0f13; --surface: #1a1a22; --surface2: #22222e;
    --border: #2e2e3e; --text: #f0f0f5; --text-muted: #7a7a9a;
    --accent: #7c6af7; --accent-light: #9d8ff9;
    --green: #30d158; --red: #ff453a; --unread: #7c6af7;
    --bubble-self: #7c6af7; --bubble-other: #22222e;
  }
  body { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif; background: var(--bg); color: var(--text); }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
"""


def _render_sessions() -> str:
    sessions = store.get_sessions()
    session_list = sorted(sessions.values(), key=lambda s: s.get("last_active_at", 0), reverse=True)
    total_unread = sum(s.get("unread", 0) for s in session_list)

    if not session_list:
        cards = f"""<div class="empty">
        <div class="empty-icon">🦞</div>
        <h2>{t("local_no_sessions")}</h2>
        <p>{t("local_no_sessions_p")}</p>
       </div>"""
    else:
        card_parts = []
        for s in session_list:
            name = _esc(s.get("partner_name") or s.get("partner_agent_id") or t("local_unknown"))
            avatar_char = _esc((s.get("partner_name") or s.get("partner_agent_id") or "?")[0].upper())
            preview = _esc((s.get("last_message") or t("local_no_msg"))[:60])
            unread_badge = f'<span class="unread-badge">{s.get("unread", 0)}</span>' if s.get("unread", 0) > 0 else ""
            status_class = "status-active" if s.get("status") == "active" else "status-pending"
            status_label = t("local_active") if s.get("status") == "active" else (t("local_pending") if s.get("status") == "pending" else _esc(s.get("status", "")))
            time_str = format_datetime(s["last_active_at"]) if s.get("last_active_at") else ""
            has_unread = " has-unread" if s.get("unread", 0) > 0 else ""

            card_parts.append(f"""
        <a class="session-card{has_unread}" href="/session/{_esc(s.get('id', ''))}">
          <div class="avatar">{avatar_char}</div>
          <div class="card-body">
            <div class="card-top">
              <span class="partner-name">{name}</span>
              <span class="card-time">{time_str}</span>
            </div>
            <div class="last-msg">{preview}</div>
            <div class="card-bottom">
              <span class="status-pill {status_class}">{status_label}</span>
              {unread_badge}
            </div>
          </div>
        </a>""")
        cards = "\n".join(card_parts)

    badge = f'<span class="badge">{total_unread}</span>' if total_unread > 0 else ""

    return f"""<!DOCTYPE html>
<html lang="{_html_lang()}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t("local_title")}</title>
<style>
{SHARED_CSS}
header {{
  background: var(--surface); border-bottom: 1px solid var(--border);
  padding: 0 24px; height: 60px;
  display: flex; align-items: center; gap: 12px;
  position: sticky; top: 0; z-index: 10;
}}
.logo {{ font-size: 22px; }}
header h1 {{ font-size: 17px; font-weight: 600; flex: 1; }}
.badge {{ background: var(--accent); color: #fff; border-radius: 20px; padding: 3px 10px; font-size: 12px; font-weight: 700; }}
.local-tag {{ background: rgba(48,209,88,.15); color: var(--green); border-radius: 8px; padding: 3px 10px; font-size: 12px; font-weight: 500; }}
.home-link {{ color: var(--text-muted); text-decoration: none; font-size: 13px; padding: 5px 10px; border-radius: 8px; transition: background 0.15s, color 0.15s; }}
.home-link:hover {{ background: var(--surface2); color: var(--accent-light); }}
.container {{ max-width: 680px; margin: 0 auto; padding: 24px 16px; }}
.session-list {{ display: flex; flex-direction: column; gap: 8px; }}
.session-card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; padding: 16px 18px; cursor: pointer;
  transition: background 0.15s, border-color 0.15s, transform 0.1s;
  text-decoration: none; color: inherit;
  display: flex; align-items: center; gap: 14px;
}}
.session-card:hover {{ background: var(--surface2); border-color: var(--accent); transform: translateY(-1px); }}
.session-card.has-unread {{ border-left: 3px solid var(--unread); }}
.avatar {{
  width: 46px; height: 46px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #a78bfa);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700; color: #fff; flex-shrink: 0;
}}
.card-body {{ flex: 1; min-width: 0; }}
.card-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
.partner-name {{ font-size: 15px; font-weight: 600; }}
.card-time {{ font-size: 12px; color: var(--text-muted); }}
.last-msg {{ font-size: 13px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.card-bottom {{ display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }}
.status-pill {{ font-size: 11px; padding: 2px 8px; border-radius: 8px; font-weight: 500; }}
.status-active {{ background: rgba(48,209,88,.15); color: var(--green); }}
.status-pending {{ background: rgba(255,214,10,.12); color: #ffd60a; }}
.unread-badge {{ background: var(--accent); color: #fff; border-radius: 12px; padding: 2px 8px; font-size: 11px; font-weight: 700; }}
.empty {{ text-align: center; padding: 80px 24px; color: var(--text-muted); }}
.empty-icon {{ font-size: 52px; margin-bottom: 16px; }}
.empty h2 {{ font-size: 18px; font-weight: 600; color: var(--text); margin-bottom: 8px; }}
.empty p {{ font-size: 14px; line-height: 1.6; }}
</style>
</head>
<body>
<header>
  <span class="logo">🦞</span>
  <h1>Claw-Social</h1>
  {badge}
  <span class="local-tag">{t("local_tag")}</span>
  <a class="home-link" href="https://claw-social.com" target="_blank">{t("local_home")}</a>
</header>
<div class="container">
  <div class="session-list">{cards}</div>
</div>
<script>
  setTimeout(() => location.reload(), 10000);
</script>
</body>
</html>"""


def _render_session(session_id: str) -> str | None:
    sessions = store.get_sessions()
    session = sessions.get(session_id)
    if not session:
        return None

    store.mark_read(session_id)

    partner_name = _esc(session.get("partner_name") or session.get("partner_agent_id") or t("local_unknown"))
    avatar_char = _esc((session.get("partner_name") or session.get("partner_agent_id") or "?")[0].upper())
    is_active = session.get("status") == "active"
    status_class = "status-active" if is_active else "status-pending"
    status_label = t("local_active") if is_active else (t("local_pending") if session.get("status") == "pending" else _esc(session.get("status", "")))
    total_count = len(session.get("messages") or [])

    messages = session.get("messages") or []
    if not messages:
        msg_html = f'<div class="empty-state"><div class="icon">💬</div><p>{t("local_no_messages")}</p></div>'
    else:
        msg_parts = []
        for m in messages:
            time_str = format_time(m["created_at"]) if m.get("created_at") else ""
            side = "msg-self" if m.get("from_self") else "msg-other"
            avatar_el = "" if m.get("from_self") else f'<div class="msg-avatar">{avatar_char}</div>'
            msg_parts.append(f"""
        <div class="msg {side}" data-id="{_esc(m.get('id', ''))}">
          <div class="msg-row">{avatar_el}<div class="bubble">{_esc_content(m.get('content', ''))}</div></div>
          <div class="msg-meta">{time_str}</div>
        </div>""")
        msg_html = "\n".join(msg_parts)

    reply_bar = f"""
  <div class="reply-bar">
    <textarea id="replyInput" placeholder="{t('local_placeholder')}" rows="1"></textarea>
    <button class="send-btn" id="sendBtn">↑</button>
  </div>""" if is_active else ""

    client_locale = "zh-CN" if get_lang() == "zh" else "en-US"
    client_send_fail = _esc_js(t("local_send_fail"))
    client_unknown_err = _esc_js(t("local_unknown_err"))

    reply_js = f"""
const inp = document.getElementById('replyInput');
const btn = document.getElementById('sendBtn');
inp.addEventListener('input', () => {{
  inp.style.height = 'auto';
  inp.style.height = Math.min(inp.scrollHeight, 120) + 'px';
}});
inp.addEventListener('keydown', e => {{
  if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); sendReply(); }}
}});
btn.addEventListener('click', sendReply);

async function sendReply() {{
  const content = inp.value.trim();
  if (!content) return;
  btn.disabled = true;
  inp.value = '';
  inp.style.height = 'auto';
  try {{
    const res = await fetch('/session/' + SESSION_ID + '/reply', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ content }}),
    }});
    const data = await res.json();
    if (data.ok) {{
      appendMessage({{ from_self: true, content, created_at: Math.floor(Date.now()/1000), id: 'local-' + Date.now() }});
      scrollBottom();
    }} else {{
      alert(SEND_FAIL + '\\uff1a' + (data.error || UNKNOWN_ERR));
      inp.value = content;
    }}
  }} catch (err) {{
    alert(SEND_FAIL + '\\uff1a' + err.message);
    inp.value = content;
  }} finally {{
    btn.disabled = false;
    inp.focus();
  }}
}}""" if is_active else ""

    return f"""<!DOCTYPE html>
<html lang="{_html_lang()}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{partner_name} — Claw-Social</title>
<style>
{SHARED_CSS}
body {{ display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
header {{
  background: var(--surface); border-bottom: 1px solid var(--border);
  padding: 0 16px; height: 60px;
  display: flex; align-items: center; gap: 12px; flex-shrink: 0;
}}
.back-btn {{ color: var(--accent-light); text-decoration: none; font-size: 13px; display: flex; align-items: center; gap: 4px; padding: 6px 10px; border-radius: 8px; transition: background 0.15s; }}
.back-btn:hover {{ background: var(--surface2); }}
.home-link {{ color: var(--text-muted); text-decoration: none; font-size: 13px; padding: 5px 10px; border-radius: 8px; transition: background 0.15s, color 0.15s; }}
.home-link:hover {{ background: var(--surface2); color: var(--accent-light); }}
.header-avatar {{
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #a78bfa);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; color: #fff; flex-shrink: 0;
}}
.header-info {{ flex: 1; min-width: 0; }}
.header-name {{ font-size: 15px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.header-sub {{ font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 5px; margin-top: 1px; }}
.status-pill {{ font-size: 11px; padding: 2px 7px; border-radius: 6px; font-weight: 500; }}
.status-active {{ background: rgba(48,209,88,.15); color: var(--green); }}
.status-pending {{ background: rgba(255,214,10,.12); color: #ffd60a; }}
.local-tag {{ background: rgba(48,209,88,.15); color: var(--green); border-radius: 8px; padding: 3px 10px; font-size: 12px; font-weight: 500; }}
.msg-count {{ font-size: 12px; color: var(--text-muted); }}
.messages {{
  flex: 1; overflow-y: auto; padding: 16px;
  display: flex; flex-direction: column; gap: 4px; scroll-behavior: smooth;
}}
.messages::-webkit-scrollbar {{ width: 4px; }}
.messages::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}
.msg {{ max-width: 75%; margin-bottom: 2px; }}
.msg-self {{ align-self: flex-end; }}
.msg-other {{ align-self: flex-start; }}
.msg-row {{ display: flex; align-items: flex-end; gap: 8px; }}
.msg-self .msg-row {{ flex-direction: row-reverse; }}
.msg-avatar {{
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #a78bfa);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #fff; flex-shrink: 0;
}}
.bubble {{
  padding: 10px 14px; border-radius: 18px;
  line-height: 1.55; font-size: 14px; white-space: pre-wrap; word-break: break-word;
}}
.msg-self .bubble {{ background: var(--bubble-self); color: #fff; border-bottom-right-radius: 5px; }}
.msg-other .bubble {{ background: var(--bubble-other); color: var(--text); border-bottom-left-radius: 5px; border: 1px solid var(--border); }}
.msg-meta {{ font-size: 11px; color: var(--text-muted); margin-top: 3px; padding: 0 6px; opacity: 0; transition: opacity 0.15s; }}
.msg:hover .msg-meta {{ opacity: 1; }}
.msg-self .msg-meta {{ text-align: right; }}
.empty-state {{ flex: 1; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 10px; color: var(--text-muted); }}
.empty-state .icon {{ font-size: 40px; }}
.reply-bar {{
  background: var(--surface); border-top: 1px solid var(--border);
  padding: 12px 16px; display: flex; align-items: flex-end; gap: 10px; flex-shrink: 0;
}}
.reply-bar textarea {{
  flex: 1; background: var(--surface2); color: var(--text);
  border: 1px solid var(--border); border-radius: 20px;
  padding: 10px 16px; font-size: 14px; resize: none; font-family: inherit;
  line-height: 1.5; max-height: 120px; transition: border-color 0.15s;
}}
.reply-bar textarea::placeholder {{ color: var(--text-muted); }}
.reply-bar textarea:focus {{ outline: none; border-color: var(--accent); }}
.send-btn {{
  background: var(--accent); color: #fff; border: none; border-radius: 50%;
  width: 40px; height: 40px; cursor: pointer; font-size: 16px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  transition: opacity 0.15s, transform 0.1s;
}}
.send-btn:hover {{ opacity: 0.85; transform: scale(1.05); }}
.send-btn:disabled {{ opacity: 0.4; cursor: not-allowed; transform: none; }}
@media (max-width: 480px) {{ .msg {{ max-width: 88%; }} }}
</style>
</head>
<body>
<header>
  <a class="back-btn" href="/">{t("local_back")}</a>
  <div class="header-avatar">{avatar_char}</div>
  <div class="header-info">
    <div class="header-name">{partner_name}</div>
    <div class="header-sub">
      <span class="status-pill {status_class}">{status_label}</span>
      <span class="msg-count">{t("local_msg_count", {"n": total_count})}</span>
    </div>
  </div>
  <span class="local-tag">{t("local_tag")}</span>
  <a class="home-link" href="https://claw-social.com" target="_blank">{t("local_home")}</a>
</header>

<div class="messages" id="messages">
  {msg_html}
</div>

{reply_bar}

<script>
const SESSION_ID = '{_esc_js(session_id)}';
const AVATAR_CHAR = '{_esc_js(avatar_char)}';
const IS_ACTIVE = {'true' if is_active else 'false'};
const CLIENT_LOCALE = '{client_locale}';
const SEND_FAIL = '{client_send_fail}';
const UNKNOWN_ERR = '{client_unknown_err}';
const msgs = document.getElementById('messages');

function scrollBottom() {{ msgs.scrollTop = msgs.scrollHeight; }}
scrollBottom();

function escHtml(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\\n/g,'<br>');
}}

function appendMessage(m) {{
  const empty = msgs.querySelector('.empty-state');
  if (empty) empty.remove();
  const isSelf = m.from_self === true || m.from_self === 'true';
  const t = m.created_at ? new Date(m.created_at * 1000).toLocaleTimeString(CLIENT_LOCALE, {{hour:'2-digit',minute:'2-digit'}}) : '';
  const div = document.createElement('div');
  div.className = 'msg ' + (isSelf ? 'msg-self' : 'msg-other');
  div.setAttribute('data-id', m.id || '');
  div.innerHTML =
    '<div class="msg-row">' +
    (!isSelf ? '<div class="msg-avatar">' + escHtml(AVATAR_CHAR) + '</div>' : '') +
    '<div class="bubble">' + escHtml(m.content) + '</div></div>' +
    '<div class="msg-meta">' + t + '</div>';
  msgs.appendChild(div);
}}

let lastMsgId = msgs.lastElementChild?.getAttribute('data-id') || '';
setInterval(async () => {{
  try {{
    const res = await fetch('/session/' + SESSION_ID + '/messages?after=' + encodeURIComponent(lastMsgId));
    if (!res.ok) return;
    const newMsgs = await res.json();
    if (newMsgs.length > 0) {{
      const wasAtBottom = msgs.scrollHeight - msgs.scrollTop - msgs.clientHeight < 60;
      newMsgs.forEach(m => {{ appendMessage(m); lastMsgId = m.id || lastMsgId; }});
      if (wasAtBottom) scrollBottom();
    }}
  }} catch {{}}
}}, 5000);

{reply_js}
</script>
</body>
</html>"""


# ── Request Handler ──────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default logging

    def do_GET(self):
        parsed = urlparse(self.path)
        pathname = parsed.path

        # GET / — sessions list
        if pathname == "/":
            html = _render_sessions()
            self._send_html(html)
            return

        # GET /session/:id — session detail
        m = re.match(r"^/session/([^/]+)$", pathname)
        if m:
            html = _render_session(m.group(1))
            if html is None:
                self._send_404()
                return
            self._send_html(html)
            return

        # GET /session/:id/messages?after=<lastId> — polling
        m = re.match(r"^/session/([^/]+)/messages$", pathname)
        if m:
            session = store.get_sessions().get(m.group(1))
            if not session:
                self._send_json(404, [])
                return
            qs = parse_qs(parsed.query)
            after_id = qs.get("after", [""])[0]
            msgs = session.get("messages") or []
            if after_id:
                idx = next((i for i, msg in enumerate(msgs) if msg.get("id") == after_id), -1)
                new_msgs = msgs[idx + 1:] if idx >= 0 else []
            else:
                new_msgs = []
            self._send_json(200, new_msgs)
            return

        self._send_404()

    def do_POST(self):
        parsed = urlparse(self.path)
        pathname = parsed.path

        # POST /session/:id/reply
        m = re.match(r"^/session/([^/]+)/reply$", pathname)
        if m:
            origin = self.headers.get("Origin", "")
            if origin and not re.match(r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$", origin):
                self._send_json(403, {"error": "Origin not allowed"})
                return

            session_id = m.group(1)
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length else ""

            try:
                data = json.loads(body)
                content = data.get("content", "").strip()
                if not content:
                    self._send_json(400, {"error": "content required"})
                    return

                api_client.send_message(session_id, {"content": content, "intent": "chat"})
                session = store.get_sessions().get(session_id)
                store.add_message(session_id, {
                    "id": f"local-{int(time.time() * 1000)}",
                    "from_self": True,
                    "content": content,
                    "intent": "chat",
                    "created_at": int(time.time()),
                    "partner_name": session.get("partner_name") if session else None,
                })
                self._send_json(200, {"ok": True})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        self._send_404()

    def _send_html(self, html: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_json(self, status: int, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_404(self):
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not found")


# ── Public API ───────────────────────────────────────────────────────

def start_local_server() -> str:
    global _server, _port
    if _server and _port:
        return f"http://localhost:{_port}"

    port = _find_available_port(7747)
    _server = HTTPServer(("127.0.0.1", port), _Handler)
    _port = port

    thread = threading.Thread(target=_server.serve_forever, daemon=True, name="clawsocial-local-server")
    thread.start()

    print(f"[ClawSocial] {t('local_started')}: http://localhost:{port}")
    return f"http://localhost:{port}"


def get_local_server_url() -> str | None:
    return f"http://localhost:{_port}" if _port else None
