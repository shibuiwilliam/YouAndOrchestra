"""PythonOnlyBackend — no LLM, pure Python Subagent execution.

Delegates directly to the registered Python Subagent implementations
in ``src/yao/subagents/``. This is the default backend for CI and
environments without LLM access.

Belongs to agents/ package (Tier 4).
"""

from __future__ import annotations

# Ensure all subagents are registered
import yao.subagents.adversarial_critic as _ac  # noqa: F401
import yao.subagents.composer as _co  # noqa: F401
import yao.subagents.harmony_theorist as _ht  # noqa: F401
import yao.subagents.mix_engineer as _me  # noqa: F401
import yao.subagents.orchestrator as _or  # noqa: F401
import yao.subagents.producer as _pr  # noqa: F401
import yao.subagents.rhythm_architect as _ra  # noqa: F401
from yao.agents.protocol import AgentInvocationConfig
from yao.subagents.base import AgentContext, AgentOutput, AgentRole, get_subagent


class PythonOnlyBackend:
    """Agent backend that uses pure Python Subagent implementations.

    No LLM calls. Delegates to ``SubagentBase.process()`` directly.
    This backend MUST always work — it is the CI safety net.
    """

    def invoke(
        self,
        role: AgentRole,
        context: AgentContext,
        config: AgentInvocationConfig | None = None,
    ) -> AgentOutput:
        """Invoke a Python Subagent by role.

        Args:
            role: Which Subagent to invoke.
            context: The current pipeline state.
            config: Ignored (Python execution has no LLM config).

        Returns:
            AgentOutput from the Subagent.
        """
        agent = get_subagent(role)
        return agent.process(context)
