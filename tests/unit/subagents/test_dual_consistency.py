"""Dual consistency tests — verify .md and .py definitions match.

Each .claude/agents/*.md file must have a corresponding Python Subagent,
and vice versa.
"""

from __future__ import annotations

from pathlib import Path

import yao.subagents.adversarial_critic as _ac  # noqa: F401
import yao.subagents.composer as _co  # noqa: F401
import yao.subagents.harmony_theorist as _ht  # noqa: F401
import yao.subagents.mix_engineer as _me  # noqa: F401
import yao.subagents.orchestrator as _or  # noqa: F401
import yao.subagents.producer as _pr  # noqa: F401
import yao.subagents.rhythm_architect as _ra  # noqa: F401
from yao.subagents.base import AgentRole, registered_subagents

AGENTS_DIR = Path(".claude/agents")

# Mapping from .md filename to AgentRole
_MD_TO_ROLE: dict[str, AgentRole] = {
    "composer.md": AgentRole.COMPOSER,
    "harmony-theorist.md": AgentRole.HARMONY_THEORIST,
    "rhythm-architect.md": AgentRole.RHYTHM_ARCHITECT,
    "orchestrator.md": AgentRole.ORCHESTRATOR,
    "adversarial-critic.md": AgentRole.ADVERSARIAL_CRITIC,
    "mix-engineer.md": AgentRole.MIX_ENGINEER,
    "producer.md": AgentRole.PRODUCER,
}


class TestDualConsistency:
    def test_every_md_has_python_implementation(self) -> None:
        """Each .md agent definition must have a registered Python Subagent."""
        registry = registered_subagents()
        for md_name, role in _MD_TO_ROLE.items():
            md_path = AGENTS_DIR / md_name
            assert md_path.exists(), f"Missing agent definition: {md_path}"
            assert role in registry, f"No Python Subagent for {md_name} (role={role})"

    def test_every_python_subagent_has_md(self) -> None:
        """Each registered Python Subagent must have a .md agent definition."""
        role_to_md = {v: k for k, v in _MD_TO_ROLE.items()}
        for role in registered_subagents():
            assert role in role_to_md, f"No .md definition for {role}"
            md_path = AGENTS_DIR / role_to_md[role]
            assert md_path.exists(), f"Missing: {md_path}"

    def test_all_seven_agents_have_both(self) -> None:
        """All 7 roles must have both .md and .py."""
        registry = registered_subagents()
        assert len(registry) == 7  # noqa: PLR2004
        assert len(_MD_TO_ROLE) == 7  # noqa: PLR2004
