"""Programmatic AgentDefinition mirrors of .claude/agents/*.md.

``yao_agent_definitions()`` parses the Markdown agent files at module
call time and returns a dict of ``AgentDefinition`` objects. This is
useful for hosts without filesystem access (serverless, embedded).

**The Markdown files are authoritative.** This module regenerates
the Python mirror on every call. There is no manual sync step.
"""

from __future__ import annotations

from pathlib import Path

from claude_agent_sdk import AgentDefinition

from yao.sdk._frontmatter import parse_agent_md

# Default agents directory
_DEFAULT_AGENTS_DIR = Path(__file__).resolve().parents[3] / ".claude" / "agents"

# Files to skip (internal protocols, not subagents)
_SKIP_PREFIXES = ("_",)

# Known tool restrictions from PROJECT.md §5.6
# The Adversarial Critic reads, judges, and reports — it never modifies.
_AGENT_DISALLOWED_TOOLS: dict[str, list[str]] = {
    "adversarial-critic": ["Write", "Edit"],
}


def yao_agent_definitions(
    *,
    agents_dir: Path | None = None,
) -> dict[str, AgentDefinition]:
    """Return a dict of programmatic AgentDefinition mirroring .claude/agents/*.md.

    Useful when the host cannot rely on filesystem settings (e.g., a serverless
    deployment that bundles YaO without the .claude/ directory).

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
        # Skip internal files (e.g., _protocol.md)
        if md.stem.startswith(_SKIP_PREFIXES):
            continue

        meta, body = parse_agent_md(md)
        name = meta["name"]

        # Build tool restrictions — from metadata or known restrictions
        disallowed: list[str] | None = meta.get("disallowed_tools") or _AGENT_DISALLOWED_TOOLS.get(name)

        out[name] = AgentDefinition(
            description=meta.get("description", ""),
            prompt=body,
            disallowedTools=disallowed,
            model=meta.get("model"),
            skills=meta.get("skills"),
            mcpServers=["yao"],
        )

    return out
