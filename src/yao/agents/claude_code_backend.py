"""ClaudeCodeBackend — invoke Subagents via Claude Code SDK.

Stub implementation for Tier 4. Currently falls back to PythonOnlyBackend.
Full implementation will use the Claude Code Agent SDK.

Belongs to agents/ package (Tier 4).
"""

from __future__ import annotations

import structlog

from yao.agents.protocol import AgentInvocationConfig
from yao.agents.python_only_backend import PythonOnlyBackend
from yao.subagents.base import AgentContext, AgentOutput, AgentRole

logger = structlog.get_logger()


class ClaudeCodeBackend:
    """Agent backend using Claude Code SDK.

    Currently falls back to PythonOnlyBackend. Full implementation
    will launch Claude Code subagents for creative tasks.
    """

    is_stub = True

    def __init__(self) -> None:
        self._fallback = PythonOnlyBackend()

    def invoke(
        self,
        role: AgentRole,
        context: AgentContext,
        config: AgentInvocationConfig | None = None,
    ) -> AgentOutput:
        """Invoke via Claude Code (stub: falls back to Python).

        Args:
            role: Which Subagent to invoke.
            context: The current pipeline state.
            config: Invocation configuration.

        Returns:
            AgentOutput.
        """
        logger.info(
            "claude_code_fallback",
            role=role.value,
            message="ClaudeCodeBackend not yet implemented, using PythonOnlyBackend.",
        )
        return self._fallback.invoke(role, context, config)
