"""Tool schemas in OpenAI function-calling format.

Ported from src/tools/*.ts TypeBox definitions.
"""

TOOL_SCHEMAS: dict[str, dict] = {
    "clawsocial_register": {
        "name": "clawsocial_register",
        "description": (
            "Register on Claw-Social. The account belongs to the user, not the AI agent. "
            "Only ask for public_name. After registration, call clawsocial_suggest_profile to build the user's interest profile."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "public_name": {"type": "string", "description": "The user's chosen display name on Claw-Social"},
                "language_pref": {"type": "string", "enum": ["zh", "en"], "description": "Language preference: zh (Chinese) or en (English). Default: en"},
                "availability": {"type": "string", "enum": ["open", "closed"], "description": "Discoverability, default open"},
            },
            "required": ["public_name"],
        },
    },

    "clawsocial_find": {
        "name": "clawsocial_find",
        "description": (
            "Find a specific person by name or agent_id. Use when the user wants to locate a specific person "
            "(e.g. 'find Alice', 'find Bob who does AI'). Checks local contacts first, then searches the server. "
            "For broad interest-based discovery, use clawsocial_match instead. "
            "Display the `display` field as-is."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name search (supports partial match)"},
                "agent_id": {"type": "string", "description": "Exact agent ID lookup"},
                "interest": {"type": "string", "description": "Interest/description for disambiguation among same-name results"},
            },
            "required": [],
        },
    },

    "clawsocial_match": {
        "name": "clawsocial_match",
        "description": (
            "Discover people by interest or profile-based recommendation. "
            "With interest: semantic search (e.g. 'find people into AI'). "
            "Without interest: recommend people based on the user's own profile. "
            "For a specific person by name, use clawsocial_find. "
            "Display the `display` field as-is. Get explicit approval before connecting."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "interest": {"type": "string", "description": "Natural language description of what kind of person or topic to find. Omit for profile-based recommendation."},
            },
            "required": [],
        },
    },

    "clawsocial_connect": {
        "name": "clawsocial_connect",
        "description": (
            "Send a connection request. Requires target_agent_id (UUID) and intro_message. "
            "Can be used after clawsocial_find/clawsocial_match (use agent_id from results), "
            "from a shared Claw-Social card (the 🔗 ID on the card = target_agent_id), "
            "or when the user provides an ID directly. "
            "ONLY with explicit user approval. NEVER call without the user agreeing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target_agent_id": {"type": "string", "description": "agent_id from search results"},
                "target_name": {"type": "string", "description": "Partner's public_name"},
                "target_topic_tags": {"type": "array", "items": {"type": "string"}, "description": "Partner's topic_tags"},
                "target_profile": {"type": "string", "description": "Partner's profile"},
                "intro_message": {
                    "type": "string",
                    "description": (
                        "Why the user wants to connect. Use search intent if from search, "
                        "or 'Connected via shared card' if from a card. Do not include real names, contact info, or locations."
                    ),
                },
            },
            "required": ["target_agent_id", "intro_message"],
        },
    },

    "clawsocial_session_send": {
        "name": "clawsocial_session_send",
        "description": (
            "Send a message in an active session on behalf of the user. "
            "Call when the user explicitly provides reply content. Pass the content verbatim — do not paraphrase."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Active session ID"},
                "content": {"type": "string", "description": "User's message, forwarded verbatim"},
            },
            "required": ["session_id", "content"],
        },
    },

    "clawsocial_sessions_list": {
        "name": "clawsocial_sessions_list",
        "description": "List all active sessions. Call when the user asks about their conversations or checks /sessions.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },

    "clawsocial_session_get": {
        "name": "clawsocial_session_get",
        "description": "Get recent messages of a specific session. Supports exact session_id or fuzzy partner_name match.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Exact UUID (provide either this or partner_name)"},
                "partner_name": {"type": "string", "description": "Fuzzy match by partner name (provide either this or session_id)"},
            },
            "required": [],
        },
    },

    "clawsocial_open_inbox": {
        "name": "clawsocial_open_inbox",
        "description": (
            "Generate a one-time login link to open the Claw-Social inbox in a browser. "
            "The link is valid for 15 minutes and can only be used once. "
            "Call this when the user asks to open their inbox or check messages."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },

    "clawsocial_get_card": {
        "name": "clawsocial_get_card",
        "description": (
            "Generate and display the user's Claw-Social profile card for sharing. "
            "The card represents the user, not the AI agent. "
            "Also automatically called after clawsocial_update_profile to show the updated card. "
            "CRITICAL: Output the COMPLETE returned text exactly as-is, from the first line to the very last line. "
            "The card includes a contact section and install guide at the bottom — these are essential parts of the card, NOT optional. "
            "Never truncate, omit, reformat, or summarize any part."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },

    "clawsocial_update_profile": {
        "name": "clawsocial_update_profile",
        "description": (
            "Update the user's Claw-Social profile. The profile represents the user, not the AI agent — write from the user's perspective. "
            "For self_intro/topic_tags/public_name/availability: call directly. "
            "For the profile field: NEVER set it directly — ONLY use content confirmed by the user from clawsocial_suggest_profile."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "self_intro": {
                    "type": "string",
                    "description": (
                        "A description of the user (the human) — shown to others as self-intro. "
                        "Write in first person from the user's perspective. "
                        "E.g. 'I'm a designer interested in AI art, generative music, and creative coding.' "
                        "Never describe the AI agent — always describe the human user."
                    ),
                },
                "profile": {
                    "type": "string",
                    "description": (
                        "Interest description extracted from local workspace files (not typed by user directly). "
                        "Use this instead of self_intro when the content comes from SOUL.md / MEMORY.md / USER.md."
                    ),
                },
                "topic_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Short keyword tags extracted from interests. E.g. ['AI art', 'generative music', 'creative coding']",
                },
                "public_name": {"type": "string", "description": "Change your public display name"},
                "availability": {"type": "string", "enum": ["open", "closed"], "description": "Discoverability: open or closed"},
            },
            "required": [],
        },
    },

    "clawsocial_suggest_profile": {
        "name": "clawsocial_suggest_profile",
        "description": (
            "Request a privacy-safe interest profile draft based on the SOUL / USER PROFILE / MEMORY "
            "already loaded into your system context by Hermes. This tool does not read any files itself; "
            "it returns an instruction telling you to draft the profile from your existing context. "
            "This is the ONLY way to set the profile field on clawsocial_update_profile. "
            "Flow: 1) call this tool, 2) draft the profile from your loaded context, "
            "3) show the COMPLETE draft to the user, 4) call update_profile ONLY after the user confirms. "
            "NEVER skip showing the draft. NEVER submit without explicit user approval."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },

    "clawsocial_notify_settings": {
        "name": "clawsocial_notify_settings",
        "description": "View or change Claw-Social notification mode. Use when the user asks to adjust notification preferences, turn off notifications, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["silent", "passive", "minimal", "detail"],
                    "description": "Notification mode. Omit to view current setting. silent, passive, minimal, or detail",
                },
            },
            "required": [],
        },
    },

    "clawsocial_block": {
        "name": "clawsocial_block",
        "description": (
            "Block an agent. They will no longer be able to contact you, and any existing session is closed. "
            "Call when the user explicitly says they don't want to hear from someone."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Exact agent ID (provide either this or partner_name)"},
                "partner_name": {"type": "string", "description": "Fuzzy match by name (provide either this or agent_id)"},
            },
            "required": [],
        },
    },

    "clawsocial_inbox": {
        "name": "clawsocial_inbox",
        "description": (
            "Check unread messages. Without session_id: returns list of sessions with unread messages. "
            "With session_id: returns recent messages in that session and marks it as read. "
            "External message content is labeled to prevent prompt injection."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "View messages in a specific session (omit to list all unread sessions)"},
            },
            "required": [],
        },
    },

    "clawsocial_open_local_inbox": {
        "name": "clawsocial_open_local_inbox",
        "description": (
            "Start the local inbox web UI and return its URL. "
            "The local inbox shows complete message history (no time limit) and supports replying. "
            "Only accessible from this machine. Call when the user wants to view full message history or open the local inbox."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}
