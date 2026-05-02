"""Contract tests for all Subagents.

Verifies that each Subagent:
1. Can be instantiated via the registry
2. Returns AgentOutput with provenance populated
3. Populates its designated output fields
"""

from __future__ import annotations

import yao.subagents.adversarial_critic as _ac  # noqa: F401
import yao.subagents.composer as _co  # noqa: F401
import yao.subagents.harmony_theorist as _ht  # noqa: F401
import yao.subagents.mix_engineer as _me  # noqa: F401
import yao.subagents.orchestrator as _or  # noqa: F401
import yao.subagents.producer as _pr  # noqa: F401
import yao.subagents.rhythm_architect as _ra  # noqa: F401
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.intent import IntentSpec
from yao.subagents.base import (
    AgentContext,
    AgentOutput,
    AgentRole,
    get_subagent,
    registered_subagents,
)


def _minimal_context() -> AgentContext:
    """Create a minimal AgentContext for testing."""
    spec = CompositionSpec(
        title="Subagent Test",
        key="C major",
        tempo_bpm=120.0,
        instruments=[
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="acoustic_bass", role="bass"),
        ],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="rule_based", seed=42),
    )
    intent = IntentSpec(text="Test composition", keywords=["test"])
    trajectory = MultiDimensionalTrajectory.default()
    return AgentContext(spec=spec, intent=intent, trajectory=trajectory)


class TestRegistration:
    def test_all_seven_roles_registered(self) -> None:
        registry = registered_subagents()
        for role in AgentRole:
            assert role in registry, f"Role {role} not registered"

    def test_registry_has_seven_entries(self) -> None:
        assert len(registered_subagents()) == 7  # noqa: PLR2004


class TestComposerContract:
    def test_returns_provenance(self) -> None:
        agent = get_subagent(AgentRole.COMPOSER)
        ctx = _minimal_context()
        out = agent.process(ctx)
        assert isinstance(out, AgentOutput)
        assert len(out.provenance) > 0

    def test_produces_motif_and_phrase(self) -> None:
        agent = get_subagent(AgentRole.COMPOSER)
        out = agent.process(_minimal_context())
        assert out.motif_plan is not None
        assert out.phrase_plan is not None


class TestHarmonyTheoristContract:
    def test_returns_provenance(self) -> None:
        agent = get_subagent(AgentRole.HARMONY_THEORIST)
        out = agent.process(_minimal_context())
        assert len(out.provenance) > 0

    def test_produces_harmony_plan(self) -> None:
        agent = get_subagent(AgentRole.HARMONY_THEORIST)
        out = agent.process(_minimal_context())
        assert out.harmony_plan is not None


class TestRhythmArchitectContract:
    def test_returns_provenance(self) -> None:
        agent = get_subagent(AgentRole.RHYTHM_ARCHITECT)
        out = agent.process(_minimal_context())
        assert len(out.provenance) > 0

    def test_produces_drum_pattern(self) -> None:
        agent = get_subagent(AgentRole.RHYTHM_ARCHITECT)
        out = agent.process(_minimal_context())
        assert out.drum_pattern is not None


class TestOrchestratorContract:
    def test_returns_provenance(self) -> None:
        agent = get_subagent(AgentRole.ORCHESTRATOR)
        out = agent.process(_minimal_context())
        assert len(out.provenance) > 0

    def test_produces_arrangement_plan(self) -> None:
        agent = get_subagent(AgentRole.ORCHESTRATOR)
        out = agent.process(_minimal_context())
        assert out.arrangement_plan is not None


class TestAdversarialCriticContract:
    def test_returns_provenance(self) -> None:
        agent = get_subagent(AgentRole.ADVERSARIAL_CRITIC)
        out = agent.process(_minimal_context())
        assert len(out.provenance) > 0

    def test_findings_is_tuple(self) -> None:
        agent = get_subagent(AgentRole.ADVERSARIAL_CRITIC)
        out = agent.process(_minimal_context())
        assert isinstance(out.findings, tuple)


class TestMixEngineerContract:
    def test_returns_provenance(self) -> None:
        agent = get_subagent(AgentRole.MIX_ENGINEER)
        out = agent.process(_minimal_context())
        assert len(out.provenance) > 0

    def test_produces_production_manifest(self) -> None:
        agent = get_subagent(AgentRole.MIX_ENGINEER)
        out = agent.process(_minimal_context())
        assert out.production_manifest is not None


class TestProducerContract:
    def test_returns_provenance(self) -> None:
        agent = get_subagent(AgentRole.PRODUCER)
        out = agent.process(_minimal_context())
        assert len(out.provenance) > 0

    def test_produces_all_plans(self) -> None:
        agent = get_subagent(AgentRole.PRODUCER)
        out = agent.process(_minimal_context())
        assert out.form_plan is not None
        assert out.harmony_plan is not None
        assert out.motif_plan is not None
        assert out.phrase_plan is not None
        assert out.drum_pattern is not None
        assert out.arrangement_plan is not None
