"""Tests for PythonOnlyBackend — all Subagents must work without LLM."""

from __future__ import annotations

from yao.agents.python_only_backend import PythonOnlyBackend
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.intent import IntentSpec
from yao.subagents.base import AgentContext, AgentRole


def _make_context() -> AgentContext:
    spec = CompositionSpec(
        title="Python Backend Test",
        key="C major",
        tempo_bpm=120.0,
        instruments=[
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="acoustic_bass", role="bass"),
        ],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="rule_based", seed=42),
    )
    return AgentContext(
        spec=spec,
        intent=IntentSpec(text="test composition", keywords=["test"]),
        trajectory=MultiDimensionalTrajectory.default(),
    )


class TestPythonOnlySubagents:
    def test_composer_returns_motif_plan(self) -> None:
        backend = PythonOnlyBackend()
        out = backend.invoke(AgentRole.COMPOSER, _make_context())
        assert out.motif_plan is not None
        assert out.phrase_plan is not None

    def test_harmony_theorist_returns_plan(self) -> None:
        backend = PythonOnlyBackend()
        out = backend.invoke(AgentRole.HARMONY_THEORIST, _make_context())
        assert out.harmony_plan is not None

    def test_producer_returns_all_plans(self) -> None:
        backend = PythonOnlyBackend()
        out = backend.invoke(AgentRole.PRODUCER, _make_context())
        assert out.form_plan is not None
        assert out.harmony_plan is not None
        assert out.motif_plan is not None
        assert out.drum_pattern is not None
        assert out.arrangement_plan is not None

    def test_critic_returns_findings(self) -> None:
        backend = PythonOnlyBackend()
        out = backend.invoke(AgentRole.ADVERSARIAL_CRITIC, _make_context())
        assert isinstance(out.findings, tuple)

    def test_all_invocations_have_provenance(self) -> None:
        backend = PythonOnlyBackend()
        ctx = _make_context()
        for role in AgentRole:
            out = backend.invoke(role, ctx)
            assert len(out.provenance) > 0, f"{role.value} missing provenance"
