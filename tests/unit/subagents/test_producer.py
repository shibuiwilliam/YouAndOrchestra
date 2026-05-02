"""Producer-specific tests — override authority and pipeline coordination."""

from __future__ import annotations

import yao.subagents.adversarial_critic as _ac  # noqa: F401
import yao.subagents.composer as _co  # noqa: F401
import yao.subagents.harmony_theorist as _ht  # noqa: F401
import yao.subagents.mix_engineer as _me  # noqa: F401
import yao.subagents.orchestrator as _or  # noqa: F401
import yao.subagents.producer as _pr  # noqa: F401
import yao.subagents.rhythm_architect as _ra  # noqa: F401
from yao.reflect.provenance import ProvenanceLog
from yao.subagents.base import AgentRole, get_subagent
from yao.subagents.producer import ProducerSubagent


class TestProducerOverrideAuthority:
    def test_producer_has_override_method(self) -> None:
        """Only ProducerSubagent has override_other_subagent()."""
        agent = get_subagent(AgentRole.PRODUCER)
        assert hasattr(agent, "override_other_subagent")

    def test_non_producers_lack_override(self) -> None:
        """No other Subagent may have override_other_subagent()."""
        non_producer_roles = [r for r in AgentRole if r != AgentRole.PRODUCER]
        for role in non_producer_roles:
            agent = get_subagent(role)
            assert not hasattr(agent, "override_other_subagent"), (
                f"{role.value} should NOT have override_other_subagent()"
            )

    def test_override_records_provenance(self) -> None:
        """Override must be recorded in provenance."""
        producer = ProducerSubagent()
        prov = ProvenanceLog()
        producer.override_other_subagent(
            AgentRole.COMPOSER,
            "Motif too repetitive, requesting variation",
            prov,
        )
        assert len(prov) > 0
        last_record = prov.records[-1]
        assert "override" in last_record.operation
        params = last_record.parameters or {}
        assert params["overridden_role"] == "composer"

    def test_producer_is_registered_subagent(self) -> None:
        """Producer must be an instance of ProducerSubagent."""
        agent = get_subagent(AgentRole.PRODUCER)
        assert isinstance(agent, ProducerSubagent)
