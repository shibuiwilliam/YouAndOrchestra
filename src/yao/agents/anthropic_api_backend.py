"""AnthropicAPIBackend — invoke Subagents via Anthropic API.

Stub implementation for Tier 4. Currently falls back to PythonOnlyBackend
with a warning. Full API integration in a future PR.

Belongs to agents/ package (Tier 4).
"""

from __future__ import annotations

import structlog

from yao.agents.protocol import AgentInvocationConfig
from yao.agents.python_only_backend import PythonOnlyBackend
from yao.subagents.base import AgentContext, AgentOutput, AgentRole

logger = structlog.get_logger()


class AnthropicAPIBackend:
    """Agent backend using the Anthropic API.

    Currently falls back to PythonOnlyBackend. Full implementation
    will read .claude/agents/<role>.md prompts and call the API.
    """

    def __init__(self) -> None:
        self._fallback = PythonOnlyBackend()

    def invoke(
        self,
        role: AgentRole,
        context: AgentContext,
        config: AgentInvocationConfig | None = None,
    ) -> AgentOutput:
        """Invoke via Anthropic API (stub: falls back to Python).

        Args:
            role: Which Subagent to invoke.
            context: The current pipeline state.
            config: Invocation configuration.

        Returns:
            AgentOutput.
        """
        logger.info(
            "anthropic_api_fallback",
            role=role.value,
            message="AnthropicAPIBackend not yet implemented, using PythonOnlyBackend.",
        )
        return self._fallback.invoke(role, context, config)
