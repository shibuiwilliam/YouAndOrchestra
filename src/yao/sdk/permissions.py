"""Permission policies for music production sessions.

A music session has narrower destructive boundaries than general coding.
The default permission callback denies writes to protected paths and
blocks destructive Bash commands against iterations and references.
"""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import (
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)

# Paths that should not be modified during a music session
PROTECTED_WRITE_PATHS = (
    ".claude/agents/",
    ".claude/commands/",
    ".claude/skills/",
    "references/",
    "CLAUDE.md",
)

# Patterns in Bash commands that indicate destructive operations
DESTRUCTIVE_PATTERNS = (
    "rm -rf outputs",
    "rm -rf references",
    "rm -rf .claude",
    "rm -r outputs",
    "rm -r references",
    "rm -r .claude",
)


async def default_yao_permission(
    tool_name: str,
    input_data: dict[str, Any],
    context: ToolPermissionContext,
) -> PermissionResultAllow | PermissionResultDeny:
    """Default permission callback for YaO music production sessions.

    Denies:
    - Write/Edit to protected paths (agents, commands, skills, references, CLAUDE.md)
    - Bash commands containing destructive patterns against protected dirs

    Args:
        tool_name: Name of the tool being used.
        input_data: Tool input arguments.
        context: Permission context from the SDK.

    Returns:
        Allow or Deny result.
    """
    # Block destructive Bash commands
    if tool_name == "Bash":
        cmd = input_data.get("command", "")
        for pattern in DESTRUCTIVE_PATTERNS:
            if pattern in cmd:
                return PermissionResultDeny(
                    message=f"YaO refuses to run destructive command against protected paths: {pattern}",
                )

    # Block writes/edits to protected paths
    if tool_name in {"Write", "Edit"}:
        path = input_data.get("file_path", "")
        for protected in PROTECTED_WRITE_PATHS:
            if protected in path:
                return PermissionResultDeny(
                    message=(
                        f"During a music session, YaO does not permit writes to {path}. "
                        "Use a separate dev session with --permission-mode default."
                    ),
                )

    return PermissionResultAllow(updated_input=input_data)
