"""Default SDK options builder for YaO music production.

``default_yao_options()`` returns a ``ClaudeAgentOptions`` pre-configured
for music production: the in-process MCP server, the ``claude_code`` system
prompt preset, project-scoped settings, and sensible permission defaults.

Power users override any field via ``extra_options``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions

from yao.sdk.server import create_yao_mcp_server


def default_yao_options(
    project: str,
    *,
    cwd: str | Path | None = None,
    extra_options: ClaudeAgentOptions | None = None,
) -> ClaudeAgentOptions:
    """Build a ``ClaudeAgentOptions`` pre-configured for YaO music production.

    This is the Lane B entry point: power users who want full control
    construct their ``ClaudeAgentOptions`` from this starting point
    and override any field via ``extra_options``.

    Args:
        project: Project name (used for output directory resolution).
        cwd: Working directory. Defaults to the current directory.
        extra_options: Optional overrides merged on top of the defaults.

    Returns:
        A fully configured ``ClaudeAgentOptions``.
    """
    resolved_cwd = str(Path(cwd).resolve()) if cwd else str(Path.cwd())

    opts = ClaudeAgentOptions(
        system_prompt={"type": "preset", "preset": "claude_code"},
        setting_sources=["project"],
        mcp_servers={"yao": create_yao_mcp_server()},
        permission_mode="acceptEdits",
        cwd=resolved_cwd,
        effort="high",
        skills="all",
        allowed_tools=[
            "Read",
            "Write",
            "Edit",
            "Glob",
            "Grep",
            "Bash",
            "Agent",
            "mcp__yao__*",
        ],
    )

    # Merge extra_options if provided
    if extra_options is not None:
        opts = _merge_options(opts, extra_options)

    return opts


def _merge_options(
    base: ClaudeAgentOptions,
    overrides: ClaudeAgentOptions,
) -> ClaudeAgentOptions:
    """Merge override options into base, with overrides winning.

    Only non-default fields from ``overrides`` are applied.

    Args:
        base: The base options.
        overrides: Override options (non-default values win).

    Returns:
        A new ``ClaudeAgentOptions`` with merged values.
    """
    # ClaudeAgentOptions is a dataclass — iterate its fields
    merged_kwargs: dict[str, Any] = {}
    defaults = ClaudeAgentOptions()

    for field_name in ClaudeAgentOptions.__annotations__:
        base_val = getattr(base, field_name, None)
        override_val = getattr(overrides, field_name, None)
        default_val = getattr(defaults, field_name, None)

        # Use override if it differs from the default
        if override_val != default_val:
            merged_kwargs[field_name] = override_val
        else:
            merged_kwargs[field_name] = base_val

    return ClaudeAgentOptions(**merged_kwargs)
