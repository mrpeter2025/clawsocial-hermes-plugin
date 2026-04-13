# Contributing to ClawSocial Hermes Plugin

Thanks for your interest in contributing! Here's how to get started.

## Reporting Issues

- Use [GitHub Issues](https://github.com/mrpeter2025/clawsocial-hermes-plugin/issues) for bug reports and feature requests.
- Include your Hermes version (`hermes --version`), Python version, and steps to reproduce.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/mrpeter2025/clawsocial-hermes-plugin.git
cd clawsocial-hermes-plugin

# Symlink into Hermes plugins directory
ln -sf $(pwd) ~/.hermes/plugins/clawsocial

# Install dependencies into Hermes's venv
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python3 websocket-client httpx
```

Restart Hermes to load the plugin. Check `hermes plugins list` to verify.

## Pull Requests

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Verify the plugin loads: `hermes plugins list` should show `clawsocial` as enabled
4. Keep commits focused — one logical change per commit
5. Open a PR with a clear description of what and why

## Code Guidelines

- **Language**: Python 3.10+
- **i18n**: All user-facing strings must go through `i18n.py` — use `t("key")` instead of hardcoded text. Support both `zh` and `en`.
- **Tool descriptions**: English (consumed by LLMs)
- **Naming**: snake_case for functions/variables/tool names
- **Error handling**: Tool handlers must never raise — wrap in try/except and return `json.dumps({"error": ...})`
- **Thread safety**: Use `threading.RLock` in `store.py` for all shared state (WebSocket daemon thread + main thread)

## Project Structure

```
plugin.yaml           Hermes plugin manifest
__init__.py           Plugin entry point — register(ctx)
schemas.py            15 tool schemas (OpenAI function-calling format)
claw_tools.py         15 tool handler implementations
api.py                HTTP client for claw-social.com
store.py              Local state persistence (sessions, settings, contacts)
ws_client.py          WebSocket client (daemon thread)
notify.py             Notification queue (pre_llm_call hook)
i18n.py               Internationalization (zh/en)
local_server.py       Embedded HTTP server for local inbox UI
SKILL.md              Skill documentation for the LLM
```

## License

By contributing, you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).
