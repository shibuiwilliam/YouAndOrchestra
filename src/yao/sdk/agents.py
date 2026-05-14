"""Programmatic AgentDefinition mirrors of .claude/agents/*.md.

``yao_agent_definitions()`` parses the Markdown agent files at module
call time and returns a dict of ``AgentDefinition`` objects. This is
useful for hosts without filesystem access (serverless, embedded).

**The Markdown files are authoritative.** This module regenerates
the Python mirror on every call. There is no manual sync step.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from claude_agent_sdk import AgentDefinition

from yao.sdk._frontmatter import parse_agent_md

# Default agents directory
_DEFAULT_AGENTS_DIR = Path(__file__).resolve().parents[3] / ".claude" / "agents"

# Files to skip (internal protocols, not subagents)
_SKIP_PREFIXES = ("_",)

# ---------------------------------------------------------------------------
# Per-subagent tool restrictions (IMPROVEMENT.md §7.2)
# ---------------------------------------------------------------------------

_AGENT_DISALLOWED_TOOLS: dict[str, list[str]] = {
    "adversarial-critic": ["Write", "Edit"],
}

# Per-subagent allowed tools (§7.2 table).
# Agents not listed here get the default allowed_tools from ClaudeAgentOptions.
_AGENT_TOOLS: dict[str, list[str]] = {
    "producer": [
        "Read",
        "Write",
        "Edit",
        "Agent",
        "mcp__yao__*",
    ],
    "composer": [
        "Read",
        "Glob",
        "Grep",
        "mcp__yao__yao_compose",
        "mcp__yao__yao_load_spec",
        "mcp__yao__yao_explain",
    ],
    "harmony-theorist": [
        "Read",
        "mcp__yao__yao_load_spec",
        "mcp__yao__yao_explain",
    ],
    "rhythm-architect": [
        "Read",
        "mcp__yao__yao_load_spec",
        "mcp__yao__yao_explain",
    ],
    "orchestrator": [
        "Read",
        "mcp__yao__yao_load_spec",
        "mcp__yao__yao_read_iteration",
    ],
    "mix-engineer": [
        "Read",
        "mcp__yao__yao_render_audio",
        "mcp__yao__yao_evaluate",
    ],
    "adversarial-critic": [
        "Read",
        "Glob",
        "Grep",
        "mcp__yao__yao_evaluate",
        "mcp__yao__yao_diff",
        "mcp__yao__yao_read_iteration",
    ],
}

# Per-subagent effort tuning (§7.3).
_AGENT_EFFORT: dict[str, Literal["low", "medium", "high", "xhigh", "max"]] = {
    "producer": "high",
    "adversarial-critic": "medium",
}


def yao_agent_definitions(
    *,
    agents_dir: Path | None = None,
) -> dict[str, AgentDefinition]:
    """Return a dict of programmatic AgentDefinition mirroring .claude/agents/*.md.

    Useful when the host cannot rely on filesystem settings (e.g., a serverless
    deployment that bundles YaO without the .claude/ directory).

    Each agent gets:
    - ``tools``: Per-role allowed tools from §7.2
    - ``disallowedTools``: Explicit denials (Critic: Write, Edit)
    - ``effort``: Role-appropriate thinking depth from §7.3
    - ``mcpServers``: Always includes ``"yao"``

    Args:
        agents_dir: Override directory. Defaults to the project's .claude/agents/.

    Returns:
        Dict mapping agent name to AgentDefinition.
    """
    agents_dir = agents_dir or _DEFAULT_AGENTS_DIR
    out: dict[str, AgentDefinition] = {}

    if not agents_dir.exists():
        return out

    for md in sorted(agents_dir.glob("*.md")):
        if md.stem.startswith(_SKIP_PREFIXES):
            continue

        meta, body = parse_agent_md(md)
        name = meta["name"]

        disallowed: list[str] | None = meta.get("disallowed_tools") or _AGENT_DISALLOWED_TOOLS.get(name)
        tools: list[str] | None = _AGENT_TOOLS.get(name)
        effort = _AGENT_EFFORT.get(name) or meta.get("effort")

        out[name] = AgentDefinition(
            description=meta.get("description", ""),
            prompt=body,
            tools=tools,
            disallowedTools=disallowed,
            model=meta.get("model"),
            skills=meta.get("skills"),
            mcpServers=["yao"],
            effort=effort,
        )

    return out
