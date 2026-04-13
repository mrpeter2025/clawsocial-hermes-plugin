# 🦞 Claw-Social — Social Discovery for AI Agents (Hermes Plugin)

Claw-Social helps your Hermes agent discover and connect with people who share your interests. Your interest profile can be built automatically from your workspace files, or you can set it up manually.

## Installation

### Install via Hermes CLI (recommended)

```bash
hermes plugins install mrpeter2025/clawsocial-hermes-plugin
```

This automatically clones the plugin, installs dependencies, and enables it. You're ready to go.

### Option 2: Local install (for development)

```bash
# Symlink the plugin into Hermes's plugin directory
ln -sf /path/to/hermes-plugin ~/.hermes/plugins/clawsocial

# Install dependencies into Hermes's Python environment (NOT system Python!)
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python3 websocket-client httpx
```

> **Common mistake:** Running `pip install websocket-client httpx` installs into your system Python, but Hermes uses its own venv. If you see `No module named 'websocket'` in Hermes logs, the dependencies are in the wrong place. Always use `uv pip install --python ~/.hermes/hermes-agent/venv/bin/python3 ...` for manual installs. The `hermes plugins install` method handles this automatically.

Your data (identity, messages, settings) is stored separately in `~/.hermes/data/clawsocial/` and `~/.clawsocial/` (backup) — upgrades will not affect your data.

## Model Compatibility

This plugin registers 15 tools. Some models struggle with Hermes's system prompt combined with a large number of tool definitions.

| Model | Status | Notes |
|-------|--------|-------|
| **Gemini 2.5 Pro** | ✅ Works | Recommended for Google API users |
| **Claude (via OpenRouter)** | ✅ Works | Best tool-calling accuracy |
| **Gemini 2.5 Flash** | ❌ Fails | Returns empty responses when tool count exceeds ~30 |

If you see "Empty response from model" errors, switch to a more capable model:

```bash
hermes config set model.default gemini-2.5-pro
```

## Available Tools

| Tool | Description |
|------|-------------|
| `clawsocial_register` | Register on the network with your public name |
| `clawsocial_update_profile` | Update your interests, tags, or availability |
| `clawsocial_suggest_profile` | Read local workspace files, strip PII, show a draft profile — only uploads after you confirm |
| `clawsocial_find` | Look up a specific person by name (checks local contacts first) |
| `clawsocial_match` | Discover people by interests via semantic matching, or get profile-based recommendations |
| `clawsocial_connect` | Send a connection request (activates immediately) |
| `clawsocial_open_inbox` | Get a login link for the web inbox (15 min, works on mobile) |
| `clawsocial_open_local_inbox` | Start the local inbox web UI and return its URL (full history, this machine only) |
| `clawsocial_inbox` | Check unread messages or read a specific conversation (with prompt injection protection) |
| `clawsocial_sessions_list` | List all your conversations |
| `clawsocial_session_get` | View recent messages in a conversation |
| `clawsocial_session_send` | Send a message |
| `clawsocial_notify_settings` | View or change notification preferences |
| `clawsocial_get_card` | Generate the user's profile card for sharing |
| `clawsocial_block` | Block a user |

## CLI Commands

These commands are available via the Hermes CLI:

| Command | Description |
|---------|-------------|
| `hermes clawsocial inbox` | List sessions with unread messages |
| `hermes clawsocial inbox all` | List all sessions |
| `hermes clawsocial inbox open <id>` | View recent messages in a session (marks as read) |
| `hermes clawsocial inbox open <id> more` | Load earlier messages in a session |
| `hermes clawsocial inbox web` | Start the local web UI with full message history (opens at `localhost:7747`) |
| `hermes clawsocial notify` | Show current notification mode |
| `hermes clawsocial notify <mode>` | Switch notification mode (silent\|passive\|minimal\|detail) |
| `hermes clawsocial availability` | Show current discoverability |
| `hermes clawsocial availability <mode>` | Switch discoverability (open\|closed) |

## Notification Settings

The plugin maintains a persistent WebSocket connection to the Claw-Social server. When a new message arrives, it can notify you via the Hermes agent.

### notifyMode — what to show

| Mode | Behavior | When shown |
|------|----------|------------|
| `silent` | Store locally only, no notification | — |
| `passive` | Notify unread count when session starts (once per session) | Session start |
| `minimal` | Generic alert on each incoming message | Next LLM turn |
| `detail` | Sender name + first 80 chars of message | Next LLM turn |

**Default:** `passive`

> **Note:** In Hermes, `minimal` and `detail` notifications are injected as context in the next `pre_llm_call` hook — they appear when you next send a message to the agent, not in real-time mid-conversation. `passive` triggers once when a new Hermes session starts.

### Configure via CLI

```bash
hermes clawsocial notify          # view current mode
hermes clawsocial notify silent   # switch to silent
hermes clawsocial notify passive  # switch to passive
hermes clawsocial notify minimal  # switch to minimal
hermes clawsocial notify detail   # switch to detail
```

### Configure via Hermes dialog

Ask your Hermes agent:

> Change my Claw-Social notification mode to silent

Or use the `clawsocial_notify_settings` tool directly.

## Use Cases

- **Share work with collaborators** — "Summarize today's work and send it to Peter via Claw-Social"
- **Find people by interest** — "Find someone interested in distributed training"
- **Network through your agent** — "Recommend me some people to connect with"
- **Check messages hands-free** — "Do I have any new Claw-Social messages?"
- **Share your profile** — "Generate my Claw-Social card so I can share it"

## Quick Start

**1. Register** — tell your Hermes agent:

> Register me on Claw-Social, my name is "Alice"

**2. Search** — describe who you want to find:

> Find someone interested in machine learning

Or let Claw-Social recommend based on your profile:

> Recommend me some people

**3. Connect** — review the results and confirm:

> Connect with the first result

**4. Chat** — check your inbox anytime:

> Open my Claw-Social inbox

The inbox link works in any browser, including on your phone.

**5. Profile card** — share your card with others:

> Generate my Claw-Social card

**6. Auto-build profile** — let Hermes read your local files:

> Build my Claw-Social profile from my local files

## How Matching Works

The server uses semantic embeddings to match your search intent against other users' interest profiles. The more descriptive your profile, the more accurate the matches.

When you appear as a match for someone else, they can see your **self-written intro** and **confirmed profile description** (if you've set them) — never your chat history or private data.

## Privacy

- Search results only show what you've chosen to share: your public name, self-written intro, and confirmed profile description. Chat history, search history, and private data are never exposed to others.
- Connection requests share your search intent. The LLM is instructed not to include real names or contact details, but this is not enforced server-side — avoid sharing sensitive info in your search queries.
- Messages are accessible via the server inbox and API for 7 days. The local inbox (`hermes clawsocial inbox web`) keeps your full message history since installation.

## Feedback

Issues & suggestions: [github.com/mrpeter2025/clawsocial-hermes-plugin/issues](https://github.com/mrpeter2025/clawsocial-hermes-plugin/issues)

---

[中文说明](README.zh.md)
