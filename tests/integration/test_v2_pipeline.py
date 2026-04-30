"""Integration tests for the v2 pipeline: Spec → MPIR → ScoreIR.

Tests that the full v2 pipeline produces valid output, and that the
legacy adapter correctly bridges v1 specs to the v2 pipeline.
"""

from __future__ import annotations

import yao.generators.note.rule_based as _nrb  # noqa: F401
import yao.generators.note.stochastic as _nst  # noqa: F401
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.generators.legacy_adapter import build_plan_from_v1, generate_via_v2_pipeline
from yao.generators.note.base import NOTE_REALIZERS
from yao.generators.plan.orchestrator import PlanOrchestrator
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.intent import IntentSpec

_MINIMAL_V2 = {
    "version": "2",
    "identity": {"title": "Pipeline Test", "duration_sec": 32},
    "global": {"key": "C major", "bpm": 120, "time_signature": "4/4"},
    "form": {
        "sections": [
            {"id": "intro", "bars": 4, "density": 0.3},
            {"id": "main", "bars": 8, "density": 0.6},
            {"id": "outro", "bars": 4, "density": 0.2},
        ]
    },
    "harmony": {
        "chord_palette": ["I", "IV", "V", "vi"],
        "cadence": {"main": "authentic"},
    },
    "arrangement": {"instruments": {"piano": {"role": "melody"}}},
    "generation": {"strategy": "rule_based"},
}


class TestV2Pipeline:
    """Full v2 pipeline: CompositionSpecV2 → MusicalPlan → ScoreIR."""

    def test_plan_generation(self) -> None:
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        traj = MultiDimensionalTrajectory.default()
        intent = IntentSpec(text="A test piece", keywords=["test"])
        prov = ProvenanceLog()

        orchestrator = PlanOrchestrator(plan_strategy="rule_based")
        plan = orchestrator.build_plan(spec, traj, intent, prov)

        assert plan.is_phase_alpha_complete()
        assert plan.form.total_bars() == 16
        assert len(plan.harmony.chord_events) > 0

    def test_note_realization_rule_based(self) -> None:
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        traj = MultiDimensionalTrajectory.default()
        intent = IntentSpec(text="test", keywords=[])
        prov = ProvenanceLog()

        plan = PlanOrchestrator().build_plan(spec, traj, intent, prov)
        realizer = NOTE_REALIZERS["rule_based"]()
        score = realizer.realize(plan, seed=42, temperature=0.5, provenance=prov)

        assert score.title
        assert len(score.sections) > 0
        assert len(score.all_notes()) > 0

    def test_note_realization_stochastic(self) -> None:
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        traj = MultiDimensionalTrajectory.default()
        intent = IntentSpec(text="test", keywords=[])
        prov = ProvenanceLog()

        plan = PlanOrchestrator().build_plan(spec, traj, intent, prov)
        realizer = NOTE_REALIZERS["stochastic"]()
        score = realizer.realize(plan, seed=42, temperature=0.5, provenance=prov)

        assert len(score.all_notes()) > 0

    def test_determinism_same_seed(self) -> None:
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        traj = MultiDimensionalTrajectory.default()
        intent = IntentSpec(text="test", keywords=[])

        scores = []
        for _ in range(2):
            prov = ProvenanceLog()
            plan = PlanOrchestrator().build_plan(spec, traj, intent, prov)
            realizer = NOTE_REALIZERS["stochastic"]()
            score = realizer.realize(plan, seed=42, temperature=0.5, provenance=prov)
            scores.append(score)

        notes_a = scores[0].all_notes()
        notes_b = scores[1].all_notes()
        assert len(notes_a) == len(notes_b)
        for na, nb in zip(notes_a, notes_b, strict=True):
            assert na.pitch == nb.pitch
            assert na.start_beat == nb.start_beat


class TestLegacyAdapter:
    """Legacy v1 specs work through the v2 pipeline."""

    def _make_v1_spec(self) -> CompositionSpec:
        return CompositionSpec(
            title="Legacy Test",
            key="C major",
            tempo_bpm=120.0,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="intro", bars=4, dynamics="mp"),
                SectionSpec(name="verse", bars=8, dynamics="mf"),
            ],
            generation=GenerationConfig(strategy="rule_based"),
        )

    def test_build_plan_from_v1(self) -> None:
        spec = self._make_v1_spec()
        plan, prov = build_plan_from_v1(spec)
        assert plan.form.total_bars() == 12
        assert len(plan.harmony.chord_events) > 0

    def test_generate_via_v2_pipeline(self) -> None:
        spec = self._make_v1_spec()
        score, prov = generate_via_v2_pipeline(spec)
        assert len(score.all_notes()) > 0
        assert score.total_bars() > 0

    def test_v1_stochastic_via_v2(self) -> None:
        spec = CompositionSpec(
            title="Stochastic Legacy",
            key="D minor",
            tempo_bpm=100.0,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="main", bars=8, dynamics="mf")],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )
        score, prov = generate_via_v2_pipeline(spec)
        assert len(score.all_notes()) > 0


class TestRegistries:
    """Both registries have the expected entries."""

    def test_plan_generators_registered(self) -> None:
        from yao.generators.plan.base import PLAN_GENERATORS

        assert "rule_based_form" in PLAN_GENERATORS
        assert "rule_based_harmony" in PLAN_GENERATORS

    def test_note_realizers_registered(self) -> None:
        assert "rule_based" in NOTE_REALIZERS
        assert "stochastic" in NOTE_REALIZERS
