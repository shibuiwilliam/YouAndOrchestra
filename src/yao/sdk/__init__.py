"""YaO Agent SDK — programmatic access to the YaO music production orchestra.

This package provides two lanes of access:

- **Lane A** (``YaoAgent``): High-level façade with one method per slash command.
- **Lane B** (``default_yao_options`` + ``create_yao_mcp_server``): Raw SDK access
  for power users who want to construct their own ``ClaudeAgentOptions``.

Both lanes call the same Conductor and the same seven-layer engine.

Example (Lane A)::

    from yao.sdk import YaoAgent

    async with YaoAgent(project="my-song") as agent:
        async for event in agent.conduct("a calm piano piece in D minor"):
            print(event)

Example (Lane B)::

    from claude_agent_sdk import query
    from yao.sdk import default_yao_options

    opts = default_yao_options(project="my-song")
    async for msg in query(prompt="/compose my-song", options=opts):
        print(msg)
"""

from __future__ import annotations

try:
    import claude_agent_sdk as _sdk  # noqa: F401
except ImportError as _exc:
    raise ImportError(
        'The Claude Agent SDK is required for yao.sdk. Install it with: pip install -e ".[sdk]"'
    ) from _exc

from yao.sdk._options import default_yao_options
from yao.sdk.server import create_yao_mcp_server

__all__ = [
    "create_yao_mcp_server",
    "default_yao_options",
]
