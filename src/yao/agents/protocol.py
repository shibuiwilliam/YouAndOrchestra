"""Agent Protocol — the interface all backends must implement.

``AgentBackend`` is a Protocol (structural typing). Any class with
a matching ``invoke()`` method satisfies it — no inheritance required.

Belongs to agents/ package (Tier 4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from yao.subagents.base import AgentContext, AgentOutput, AgentRole


@dataclass(frozen=True)
class AgentInvocationConfig:
    """Configuration for a single agent invocation.

    Attributes:
        timeout_sec: Maximum time for the invocation.
        max_tokens: Maximum tokens for LLM-based backends.
        temperature: LLM temperature (ignored by PythonOnlyBackend).
    """

    timeout_sec: float = 30.0
    max_tokens: int = 4096
    temperature: float = 0.5


@runtime_checkable
class AgentBackend(Protocol):
    """Protocol that all agent backends must satisfy.

    Implementations:
    - PythonOnlyBackend: direct SubagentBase.process() (CI default)
    - AnthropicAPIBackend: Anthropic API calls
    - ClaudeCodeBackend: Claude Code SDK
    - LocalLLMBackend: local model via ollama
    """

    def invoke(
        self,
        role: AgentRole,
        context: AgentContext,
        config: AgentInvocationConfig | None = None,
    ) -> AgentOutput:
        """Invoke a Subagent with the given role and context.

        Args:
            role: Which Subagent to invoke.
            context: The current pipeline state.
            config: Optional invocation configuration.

        Returns:
            AgentOutput from the Subagent.
        """
        ...
