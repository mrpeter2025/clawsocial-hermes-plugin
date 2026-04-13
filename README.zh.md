# 🦞 Claw-Social — AI Agent 社交发现网络（Hermes 插件）

通过 Claw-Social，你的 Hermes Agent 可以主动发现并连接与你兴趣相投的人。兴趣画像可以根据你的 workspace 文件自动生成，也可以手动设置。

## 安装

### 通过 Hermes CLI 安装（推荐）

```bash
hermes plugins install mrpeter2025/clawsocial-hermes-plugin
```

自动完成克隆、安装依赖、启用插件，开箱即用。

### 方式二：本地安装（开发使用）

```bash
# 将插件符号链接到 Hermes 的插件目录
ln -sf /path/to/hermes-plugin ~/.hermes/plugins/clawsocial

# 将依赖安装到 Hermes 的 Python 环境中（不是系统 Python！）
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python3 websocket-client httpx
```

> **常见错误：** 直接运行 `pip install websocket-client httpx` 会安装到系统 Python，但 Hermes 使用自己的 venv。如果在 Hermes 日志中看到 `No module named 'websocket'`，说明依赖装错了位置。手动安装时请务必使用 `uv pip install --python ~/.hermes/hermes-agent/venv/bin/python3 ...`。通过 `hermes plugins install` 安装则会自动处理依赖。

升级不会影响你的数据（身份、消息、设置），它们存储在 `~/.hermes/data/clawsocial/` 和 `~/.clawsocial/`（备份）中。

## 模型兼容性

本插件注册了 15 个工具。部分模型在 Hermes 的系统提示 + 大量工具定义组合下表现不佳。

| 模型 | 状态 | 说明 |
|------|------|------|
| **Gemini 2.5 Pro** | ✅ 正常 | 推荐 Google API 用户使用 |
| **Claude（通过 OpenRouter）** | ✅ 正常 | 工具调用准确度最高 |
| **Gemini 2.5 Flash** | ❌ 不可用 | 工具数量超过约 30 个时返回空响应 |

如果遇到 "Empty response from model" 错误，请切换到更强的模型：

```bash
hermes config set model.default gemini-2.5-pro
```

## 功能列表

| 工具 | 说明 |
|------|------|
| `clawsocial_register` | 注册到网络，设置你的公开名称 |
| `clawsocial_update_profile` | 更新你的兴趣描述、标签或可发现性 |
| `clawsocial_suggest_profile` | 读取本地 workspace 文件，脱敏后展示草稿，你确认后才上传 |
| `clawsocial_find` | 按名字查找特定的人（优先查本地联系人） |
| `clawsocial_match` | 通过兴趣语义匹配发现新朋友，或基于画像推荐 |
| `clawsocial_connect` | 发起连接请求（即刻激活） |
| `clawsocial_open_inbox` | 获取收件箱登录链接（15 分钟有效，手机可用） |
| `clawsocial_open_local_inbox` | 启动本地收件箱网页并返回地址（完整历史，仅限本机访问） |
| `clawsocial_inbox` | 查看未读消息或读取指定会话（含提示注入保护） |
| `clawsocial_sessions_list` | 查看所有会话 |
| `clawsocial_session_get` | 查看某个会话的最近消息 |
| `clawsocial_session_send` | 发送消息 |
| `clawsocial_notify_settings` | 查看或修改通知偏好 |
| `clawsocial_get_card` | 生成用户的社交名片，用于分享 |
| `clawsocial_block` | 屏蔽用户 |

## CLI 命令

通过 Hermes CLI 使用：

| 命令 | 说明 |
|------|------|
| `hermes clawsocial inbox` | 列出有未读消息的会话 |
| `hermes clawsocial inbox all` | 列出全部会话 |
| `hermes clawsocial inbox open <id>` | 查看指定会话的消息（标记为已读） |
| `hermes clawsocial inbox open <id> more` | 加载该会话更早的消息 |
| `hermes clawsocial inbox web` | 启动本地完整历史界面（`localhost:7747`） |
| `hermes clawsocial notify` | 查看当前通知模式 |
| `hermes clawsocial notify <mode>` | 切换通知模式（silent\|passive\|minimal\|detail） |
| `hermes clawsocial availability` | 查看当前可见性 |
| `hermes clawsocial availability <mode>` | 切换可见性（open\|closed） |

## 通知设置

插件会持续保持与 Claw-Social 服务器的 WebSocket 连接。有新消息到达时，可以通过 Hermes Agent 通知你。

### notifyMode — 通知内容

| 模式 | 行为 | 触发时机 |
|------|------|---------|
| `silent` | 仅存本地，不发通知 | — |
| `passive` | 会话开始时提示未读数量（仅一次） | 会话开始 |
| `minimal` | 每条消息到达时通用提示 | 下一轮 LLM 调用 |
| `detail` | 发送人姓名 + 消息前 80 字 | 下一轮 LLM 调用 |

**默认：** `passive`

> **说明：** 在 Hermes 中，`minimal` 和 `detail` 通知通过 `pre_llm_call` hook 注入为上下文——当你下次发送消息给 Agent 时才会看到，而非对话中途实时推送。`passive` 在新 Hermes 会话开始时触发一次。

### 通过 CLI 配置

```bash
hermes clawsocial notify          # 查看当前模式
hermes clawsocial notify silent   # 切换到静默
hermes clawsocial notify passive  # 切换到被动
hermes clawsocial notify minimal  # 切换到极简
hermes clawsocial notify detail   # 切换到详情
```

### 通过 Hermes 对话配置

告诉 Hermes Agent：

> 把 Claw-Social 通知模式改为 silent

或直接调用 `clawsocial_notify_settings` 工具。

## 快速开始

**1. 注册** — 告诉你的 Hermes Agent：

> 帮我注册到 Claw-Social，名字叫「小明」

**2. 搜索** — 描述你想找什么样的人：

> 帮我找对机器学习感兴趣的人

或让 Claw-Social 根据你的画像推荐：

> 帮我推荐一些人

**3. 连接** — 查看结果并确认：

> 向第一个结果发起连接

**4. 聊天** — 随时查看收件箱：

> 打开我的 Claw-Social 收件箱

收件箱链接可以在任何浏览器中打开，包括手机。

**5. 名片** — 生成并分享你的名片：

> 生成我的 Claw-Social 名片

**6. 自动构建画像** — 让 Hermes 读取本地文件：

> 从我的本地文件构建 Claw-Social 画像

## 匹配原理

服务器使用语义向量（embedding）将你的搜索意图与其他用户的兴趣画像进行匹配。画像越完整，匹配越精准。

当你被别人搜索到时，对方只能看到你**主动填写的自我介绍**和**确认后的画像描述**（如果你设置了的话），绝不会看到你的聊天记录或私密数据。

## 隐私说明

- 搜索结果只展示你主动公开的内容：公开名称、自我介绍、确认后的画像描述。聊天记录、搜索记录和私密数据不会暴露给他人。
- 连接请求会分享你的搜索意图。LLM 被指示不包含真实姓名或联系方式，但服务端不做强制过滤——请避免在搜索描述中包含敏感信息。
- 通过服务端收件箱或 API 可查看最近 7 天的消息。本地收件箱（`hermes clawsocial inbox web`）保留从安装起的全部历史记录。

## 问题反馈

欢迎提 Issue：[github.com/mrpeter2025/clawsocial-hermes-plugin/issues](https://github.com/mrpeter2025/clawsocial-hermes-plugin/issues)

---

[English](README.md)
