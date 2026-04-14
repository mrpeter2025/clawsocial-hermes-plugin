"""Internationalization — Chinese / English string table.

Ported from src/i18n.ts.
"""

from __future__ import annotations

from datetime import datetime

_STRINGS: dict[str, dict[str, str]] = {
    # ── WebSocket notifications ────────────────────────────────────
    "ws_auth_ok":            {"zh": "认证成功",           "en": "Authenticated"},
    "ws_auth_fail":          {"zh": "认证失败",           "en": "Auth failed"},
    "ws_connected":          {"zh": "已连接服务器",       "en": "Connected to server"},
    "ws_disconnected":       {"zh": "连接断开",           "en": "Disconnected"},
    "ws_reconnect":          {"zh": "5s 后重连",          "en": "reconnecting in 5s"},
    "ws_not_registered":     {"zh": "尚未注册，跳过 WS 连接", "en": "Not registered, skipping WS"},
    "ws_new_msg_notify":     {"zh": "[Claw-Social] 你有新的 Claw-Social 消息。说「打开收件箱」查看。",
                              "en": "[Claw-Social] You have new Claw-Social messages. Say \"open my inbox\" to view."},
    "ws_connect_req":        {"zh": "收到连接请求！来自：{name}。说「打开收件箱」查看。",
                              "en": "Connection request from {name}. Say \"open my inbox\" to view."},
    "ws_connect_req_notify": {"zh": "[Claw-Social] 收到来自 {name} 的连接请求。说「打开收件箱」查看。",
                              "en": "[Claw-Social] Connection request from {name}. Say \"open my inbox\" to view."},
    "ws_session_accepted":   {"zh": "{name} 接受了连接请求，会话 ID：{id}",
                              "en": "{name} accepted your connection, session: {id}"},
    "ws_session_notify":     {"zh": "[Claw-Social] {name} 开始了与你的会话。说「打开收件箱」查看。",
                              "en": "[Claw-Social] {name} started a conversation with you. Say \"open my inbox\" to view."},
    "ws_msg_log":            {"zh": "来自 {name}：{preview}",
                              "en": "From {name}: {preview}"},
    "ws_msg_notify":         {"zh": "[Claw-Social] 收到 {name} 的新消息：{preview}",
                              "en": "[Claw-Social] New message from {name}: {preview}"},
    "ws_passive_notify":     {"zh": "[Claw-Social] 你有 {count} 条 Claw-Social 未读消息。说「打开收件箱」查看。",
                              "en": "[Claw-Social] You have {count} unread Claw-Social message(s). Say \"open my inbox\" to view."},
    "ws_passive_notify_new": {"zh": "[Claw-Social] 你有 {count} 条 Claw-Social 未读消息（{new} 条新消息）。说「打开收件箱」查看。",
                              "en": "[Claw-Social] You have {count} unread Claw-Social message(s) ({new} new). Say \"open my inbox\" to view."},

    # ── /clawsocial-inbox command ────────────────────────────────────
    "inbox_local_running":   {"zh": "🦞 本地收件箱已在运行：{url}",
                              "en": "🦞 Local inbox already running: {url}"},
    "inbox_local_started":   {"zh": "🦞 本地收件箱已启动（完整历史，仅限本机访问）：\n{url}",
                              "en": "🦞 Local inbox started (full history, local only):\n{url}"},
    "inbox_session_404":     {"zh": "❌ 未找到会话 {id}\n\n输入 hermes clawsocial inbox 查看有未读消息的会话，hermes clawsocial inbox all 查看全部会话。",
                              "en": "❌ Session {id} not found.\n\nType hermes clawsocial inbox for unread sessions, hermes clawsocial inbox all for all."},
    "inbox_chat_title":      {"zh": "📨 与 {name} 的对话",   "en": "📨 Chat with {name}"},
    "inbox_session_id":      {"zh": "会话 ID: {id}",         "en": "Session ID: {id}"},
    "inbox_no_messages":     {"zh": "（暂无消息）",           "en": "(no messages)"},
    "inbox_my_lobster":      {"zh": "我",                     "en": "Me"},
    "inbox_msg_count":       {"zh": "（共 {total} 条消息，显示最近 {limit} 条）",
                              "en": "({total} messages total, showing last {limit})"},
    "inbox_more_hint":       {"zh": "输入 hermes clawsocial inbox open {id} more 查看更早的消息",
                              "en": "Type hermes clawsocial inbox open {id} more for older messages"},
    "inbox_all_title":       {"zh": "📬 Claw-Social 全部会话（共 {count} 个，{unread} 条未读）\n\n",
                              "en": "📬 Claw-Social all sessions ({count} total, {unread} unread)\n\n"},
    "inbox_unread_title":    {"zh": "📬 Claw-Social 未读消息（{count} 条）\n\n",
                              "en": "📬 Claw-Social unread messages ({count})\n\n"},
    "inbox_no_sessions":     {"zh": "暂无会话。\n",           "en": "No sessions yet.\n"},
    "inbox_no_unread":       {"zh": "没有未读消息。\n",       "en": "No unread messages.\n"},
    "inbox_unread_badge":    {"zh": " [{n}条未读]",           "en": " [{n} unread]"},
    "inbox_no_preview":      {"zh": "（无消息）",             "en": "(no messages)"},
    "inbox_show_all":        {"zh": "输入 hermes clawsocial inbox all 查看全部会话\n",
                              "en": "Type hermes clawsocial inbox all to view all sessions\n"},
    "inbox_more_sessions":   {"zh": "... 还有 {n} 个会话\n\n",
                              "en": "... {n} more sessions\n\n"},
    "inbox_link_fail":       {"zh": "\n（无法生成登录链接，请确认已注册）\n",
                              "en": "\n(Unable to generate login link — make sure you are registered)\n"},

    # ── /clawsocial-notify command ─────────────────────────────────
    "notify_silent":         {"zh": "静默 — 不推送通知",       "en": "Silent — no notifications"},
    "notify_passive":        {"zh": "被动 — 对话开始时提示未读数", "en": "Passive — notify unread count when conversation starts"},
    "notify_minimal":        {"zh": "极简 — 仅提示有新消息",   "en": "Minimal — new message hint only"},
    "notify_detail":         {"zh": "详情 — 显示发送人和消息内容", "en": "Detail — show sender and content"},
    "notify_set":            {"zh": "✅ 通知模式已设为「{mode}」", "en": '✅ Notification mode set to "{mode}"'},

    # ── /clawsocial-availability command ─────────────────────────────
    "avail_open":            {"zh": "open — 开放，可被搜索和连接", "en": "open — discoverable, accepts connections"},
    "avail_closed":          {"zh": "closed — 隐身，不可被搜索，拒绝新连接", "en": "closed — hidden, no new connections"},
    "avail_set":             {"zh": "✅ 可见性已设为「{mode}」",   "en": '✅ Availability set to "{mode}"'},
    "avail_current":         {"zh": "当前可见性：{mode}",          "en": "Current availability: {mode}"},
    "avail_fail":            {"zh": "❌ 设置失败，请确认已注册",   "en": "❌ Failed to set — make sure you are registered"},

    # ── Local server UI ────────────────────────────────────────────
    "local_title":           {"zh": "本地收件箱 — Claw-Social", "en": "Local Inbox — Claw-Social"},
    "local_no_sessions":     {"zh": "暂无会话",               "en": "No sessions"},
    "local_no_sessions_p":   {"zh": "通过 Claw-Social 发起或接受连接后，会话将显示在这里",
                              "en": "Sessions will appear here after you connect with someone via Claw-Social"},
    "local_unknown":         {"zh": "未知",                   "en": "Unknown"},
    "local_no_msg":          {"zh": "（无消息）",             "en": "(no messages)"},
    "local_active":          {"zh": "进行中",                 "en": "Active"},
    "local_pending":         {"zh": "等待中",                 "en": "Pending"},
    "local_tag":             {"zh": "本地全量消息",           "en": "Full local history"},
    "local_home":            {"zh": "🦞 官网",                "en": "🦞 Home"},
    "local_no_messages":     {"zh": "暂无消息",               "en": "No messages"},
    "local_placeholder":     {"zh": "发送消息…",              "en": "Send a message…"},
    "local_back":            {"zh": "← 收件箱",              "en": "← Inbox"},
    "local_msg_count":       {"zh": "共 {n} 条消息",          "en": "{n} messages"},
    "local_send_fail":       {"zh": "发送失败",               "en": "Send failed"},
    "local_unknown_err":     {"zh": "未知错误",               "en": "Unknown error"},
    "local_started":         {"zh": "本地收件箱已启动",       "en": "Local inbox started"},

    # ── Display formatting (match / find results) ──────────────────
    "display_self_intro":    {"zh": "自我介绍",     "en": "Self-intro"},
    "display_profile":       {"zh": "画像",         "en": "Profile"},
    "display_match_reason":  {"zh": "匹配原因",     "en": "Match reason"},
    "display_tags":          {"zh": "标签",         "en": "Tags"},
    "display_completeness":  {"zh": "完整度",       "en": "Completeness"},
    "display_contact":       {"zh": "已连接",       "en": "contact"},
    "display_empty":         {"zh": "—",            "en": "—"},

    # ── Tools ──────────────────────────────────────────────────────
    "tools_not_registered":  {"zh": "尚未注册 Claw-Social，请先使用 clawsocial_register 注册。",
                              "en": "Not registered on Claw-Social. Use clawsocial_register first."},
    "tools_registered":      {"zh": "✅ 已成功注册 Claw-Social。你的 Claw-Social 名：{name}",
                              "en": "✅ Registered on Claw-Social. Your Claw-Social name: {name}"},
    "tools_msg_delivered":   {"zh": "✅ 消息已送达",          "en": "✅ Message delivered"},
    "tools_msg_queued":      {"zh": "📬 消息已入队（对方当前离线）",
                              "en": "📬 Message queued (recipient offline)"},
    "tools_blocked":         {"zh": "✅ 已屏蔽，对方将无法再联系你",
                              "en": "✅ Blocked. They can no longer contact you."},
    "tools_profile_updated": {"zh": "✅ 资料已更新！其他人现在可以根据你的兴趣找到你了。",
                              "en": "✅ Profile updated! Others can now find you by your interests."},
    "tools_suggest_profile_instruction": {
        "zh": (
            "请基于你已加载的 SOUL / USER PROFILE / MEMORY 等系统上下文，"
            "生成一段 100-300 字的用户画像（兴趣话题、性格特点、工作/生活方式、想认识什么样的人）。"
            "去除所有姓名、公司、地点、凭据等敏感信息。"
            "生成后【先展示给用户查看】，等用户确认或修改后，再调用 clawsocial_update_profile 提交到服务端。"
            "参数：profile（画像文本）、topic_tags（兴趣关键词数组，如 [\"AI\", \"Web3\", \"产品设计\"]），"
            "不要传 self_intro，不要传 completeness_score（服务端计算）。"
            "未经用户明确同意不要直接提交。"
        ),
        "en": (
            "Based on the SOUL / USER PROFILE / MEMORY already loaded in your system context, "
            "draft a 100-300 char user profile (interest topics, personality traits, work/life style, "
            "who they want to meet). Strip all names, companies, locations, and credentials. "
            "Show the draft to the user FIRST and wait for confirmation or edits. "
            "Only after the user explicitly approves, call clawsocial_update_profile to submit. "
            "Pass: profile (the drafted text) and topic_tags (array of interest keywords, "
            "e.g. [\"AI\", \"Web3\", \"product design\"]). Do NOT pass self_intro or completeness_score "
            "(server-side calculated). Never submit without explicit user approval."
        ),
    },
    "tools_no_update":       {"zh": "没有提供任何要更新的内容。",
                              "en": "No updates provided."},
    "tools_session_404":     {"zh": "未找到该会话",           "en": "Session not found"},
    "tools_no_match":        {"zh": "暂时没有找到匹配的人。可以稍后再试，或者换一个话题描述。",
                              "en": "No matches found. Try again later or use a different description."},
    "tools_me":              {"zh": "我",                     "en": "Me"},
    "tools_my_lobster":      {"zh": "我",                     "en": "Me"},
    "tools_other":           {"zh": "对方",                   "en": "Other"},
    "tools_inbox_link":      {"zh": "🦞 收件箱登录链接（{min} 分钟有效，仅可使用一次）：\n{url}\n\n链接失效后可再次调用此工具重新生成。",
                              "en": "🦞 Inbox login link ({min} min, single use):\n{url}\n\nCall this tool again if the link expires."},
    "tools_local_inbox":     {"zh": "🦞 本地收件箱已启动（完整历史，仅限本机访问）：\n{url}\n\n浏览器打开即可查看全部消息记录并回复。",
                              "en": "🦞 Local inbox started (full history, local only):\n{url}\n\nOpen in browser to view all messages and reply."},

    # ── Common ─────────────────────────────────────────────────────
    "unknown":               {"zh": "未知",                   "en": "Unknown"},
}


def get_lang() -> str:
    from store import get_state
    state = get_state()
    return "en" if state.get("lang") == "en" else "zh"


def format_time(ts: int | float) -> str:
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%H:%M")


def format_datetime(ts: int | float) -> str:
    dt = datetime.fromtimestamp(ts)
    lang = get_lang()
    if lang == "zh":
        return dt.strftime("%Y/%m/%d %H:%M")
    return dt.strftime("%m/%d/%Y %I:%M %p")


def t(key: str, vars: dict[str, str | int] | None = None) -> str:
    entry = _STRINGS.get(key)
    if not entry:
        return key
    lang = get_lang()
    s = entry.get(lang, entry.get("en", key))
    if vars:
        for k, v in vars.items():
            s = s.replace("{" + k + "}", str(v))
    return s
