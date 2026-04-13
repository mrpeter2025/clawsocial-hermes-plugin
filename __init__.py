"""Claw-Social Hermes Plugin — entry point.

Registers 15 tools, 2 hooks, and 1 CLI command with the Hermes agent runtime.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add plugin directory to sys.path so modules can import each other
_plugin_dir = str(Path(__file__).parent)
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

import store
import api as api_client
import ws_client
import notify
from schemas import TOOL_SCHEMAS
from claw_tools import HANDLERS

SERVER_URL = "https://claw-social.com"


def register(ctx):
    """Hermes plugin entry point — called once during plugin initialization."""

    # 1. Determine data directory (separate from plugin source to avoid
    #    writing data files into the code repo when using symlinks)
    data_dir = getattr(ctx, "data_dir", None)
    if not data_dir:
        data_dir = str(Path.home() / ".hermes" / "data" / "clawsocial")
    store.init_store(data_dir)

    # 2. Initialize API client
    api_client.init_api(SERVER_URL)

    # 3. Seed notifyMode from config on first run
    config = getattr(ctx, "config", None) or {}
    config_notify_mode = config.get("notifyMode")
    if config_notify_mode and config_notify_mode in ("silent", "passive", "minimal", "detail"):
        settings_file = os.path.join(data_dir, "settings.json")
        if not os.path.exists(settings_file):
            store.set_settings({"notifyMode": config_notify_mode})

    # 4. Start WebSocket client (daemon thread, always online)
    ws_client.start_ws_client(SERVER_URL)

    # 5. Register all 15 tools
    for tool_name, schema in TOOL_SCHEMAS.items():
        handler = HANDLERS.get(tool_name)
        if handler:
            ctx.register_tool(
                name=tool_name,
                toolset="clawsocial",
                schema=schema,
                handler=handler,
            )

    # 6. Register hooks
    def on_session_start_handler(session_id=None, **kwargs):
        if session_id:
            notify.set_session_id(session_id)
        notify.check_passive_notification()

    def pre_llm_call_handler(**kwargs):
        return notify.drain_notifications()

    ctx.register_hook("on_session_start", on_session_start_handler)
    ctx.register_hook("pre_llm_call", pre_llm_call_handler)

    # 7. Register CLI commands
    def _setup_cli(parser):
        sub = parser.add_subparsers(dest="subcommand")

        inbox_parser = sub.add_parser("inbox", help="View Claw-Social inbox")
        inbox_parser.add_argument("action", nargs="?", default="", help="web | all | open <id> [more]")
        inbox_parser.add_argument("extra", nargs="*", default=[])

        avail_parser = sub.add_parser("availability", help="View or change discoverability (open|closed)")
        avail_parser.add_argument("mode", nargs="?", default="")

        notify_parser = sub.add_parser("notify", help="View or change notification mode")
        notify_parser.add_argument("mode", nargs="?", default="")

    def _handle_cli(args):
        from i18n import t, format_time
        from local_server import start_local_server, get_local_server_url

        sub = getattr(args, "subcommand", "")

        if sub == "inbox":
            action = getattr(args, "action", "")
            extra = getattr(args, "extra", [])

            # inbox web
            if action == "web":
                existing = get_local_server_url()
                if existing:
                    print(t("inbox_local_running", {"url": existing}))
                else:
                    url = start_local_server()
                    print(t("inbox_local_started", {"url": url}))
                return

            # inbox open <id> [more]
            if action == "open" and extra:
                session_id = extra[0]
                show_more = len(extra) > 1 and extra[1] == "more"
                session = store.get_sessions().get(session_id)
                if not session:
                    print(t("inbox_session_404", {"id": session_id}))
                    return

                msgs = session.get("messages") or []
                limit = 30 if show_more else 10
                slice_msgs = msgs[-limit:]
                partner_name = session.get("partner_name") or session.get("partner_agent_id") or t("unknown")

                text = f"{t('inbox_chat_title', {'name': partner_name})}\n"
                text += f"{t('inbox_session_id', {'id': session_id})}\n"
                text += "─────────────────────────\n"

                if not slice_msgs:
                    text += f"{t('inbox_no_messages')}\n"
                else:
                    for m in slice_msgs:
                        time_str = format_time(m["created_at"]) if m.get("created_at") else ""
                        sender = t("inbox_my_lobster") if m.get("from_self") else partner_name
                        content = m.get("content", "")
                        preview = content[:100] + f"… ({len(content)})" if len(content) > 100 else content
                        text += f"[{time_str}] {sender}: {preview}\n"

                if len(msgs) > limit:
                    text += f"\n{t('inbox_msg_count', {'total': len(msgs), 'limit': limit})}\n"
                    if not show_more:
                        text += f"{t('inbox_more_hint', {'id': session_id})}\n"

                store.mark_read(session_id)
                print(text)
                return

            # inbox [all]
            show_all = action == "all"
            sessions = store.get_sessions()
            session_list = [s for s in sessions.values() if show_all or s.get("unread", 0) > 0]
            session_list.sort(key=lambda s: s.get("last_active_at", 0), reverse=True)
            total_unread = sum(s.get("unread", 0) for s in sessions.values())

            if show_all:
                text = t("inbox_all_title", {"count": len(session_list), "unread": total_unread})
            else:
                text = t("inbox_unread_title", {"count": total_unread})

            if not session_list:
                text += t("inbox_no_sessions") if show_all else t("inbox_no_unread")
            else:
                for s in session_list[:15]:
                    name = s.get("partner_name") or s.get("partner_agent_id") or t("unknown")
                    unread_badge = t("inbox_unread_badge", {"n": s["unread"]}) if s.get("unread", 0) > 0 else ""
                    preview = s.get("last_message", "")[:50] if s.get("last_message") else t("inbox_no_preview")
                    text += f"• {name}{unread_badge}\n"
                    text += f"  {preview}\n"
                    text += f"  → hermes clawsocial inbox open {s.get('id')}\n\n"
                if len(session_list) > 15:
                    text += t("inbox_more_sessions", {"n": len(session_list) - 15})

            if not show_all:
                text += t("inbox_show_all")

            try:
                data = api_client.open_inbox_token()
                text += f"\n🔗 {data['url']}\n"
            except Exception:
                text += t("inbox_link_fail")

            print(text)

        elif sub == "availability":
            mode = getattr(args, "mode", "").strip().lower()
            VALID_AVAIL = ["open", "closed"]
            AVAIL_KEY = {"open": "avail_open", "closed": "avail_closed"}

            if mode and mode in VALID_AVAIL:
                try:
                    api_client.update_profile({"availability": mode})
                    print(t("avail_set", {"mode": t(AVAIL_KEY[mode])}))
                except Exception:
                    print(t("avail_fail"))
            else:
                try:
                    me = api_client.me()
                    current = me.get("availability", "open")
                    text = f"{t('avail_current', {'mode': current})}\n\n"
                    for m in VALID_AVAIL:
                        marker = "→" if m == current else " "
                        text += f"  {marker} {t(AVAIL_KEY[m])}\n"
                    text += "\nUsage: hermes clawsocial availability <mode>"
                    print(text)
                except Exception:
                    print(t("avail_fail"))

        elif sub == "notify":
            mode = getattr(args, "mode", "").strip().lower()
            VALID_MODES = ["silent", "passive", "minimal", "detail"]
            MODE_KEY = {
                "silent": "notify_silent",
                "passive": "notify_passive",
                "minimal": "notify_minimal",
                "detail": "notify_detail",
            }

            if mode and mode in VALID_MODES:
                store.set_settings({"notifyMode": mode})
                if mode == "passive":
                    notify.check_passive_notification()
                print(t("notify_set", {"mode": t(MODE_KEY[mode])}))
            else:
                current = store.get_settings().get("notifyMode", "passive")
                text = f"{t(MODE_KEY.get(current, 'notify_passive'))}\n\n"
                for m in VALID_MODES:
                    marker = "→" if m == current else " "
                    text += f"  {marker} {m} — {t(MODE_KEY[m])}\n"
                text += "\nUsage: hermes clawsocial notify <mode>"
                print(text)
        else:
            print("Usage: hermes clawsocial <inbox|availability|notify>")

    ctx.register_cli_command(
        name="clawsocial",
        help="Claw-Social — inbox, availability, and notification settings",
        setup_fn=_setup_cli,
        handler_fn=_handle_cli,
    )
