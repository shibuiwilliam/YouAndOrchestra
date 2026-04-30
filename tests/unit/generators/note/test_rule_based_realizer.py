"""Unit tests for RuleBasedNoteRealizer."""

from __future__ import annotations

import yao.generators.note.rule_based as _nrb  # noqa: F401
import yao.generators.rule_based as _rb  # noqa: F401
from yao.generators.note.base import NOTE_REALIZERS
from yao.generators.note.rule_based import _plan_to_v1_spec, _tension_to_dynamics
from yao.ir.plan.harmony import (
    CadenceRole,
    ChordEvent,
    HarmonicFunction,
    HarmonyPlan,
)
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec


def _make_plan() -> MusicalPlan:
    """Create a minimal plan for testing."""
    form = SongFormPlan(
        sections=[
            SectionPlan(
                id="intro",
                start_bar=0,
                bars=4,
                role="intro",
                target_density=0.3,
                target_tension=0.2,
            ),
            SectionPlan(
                id="main",
                start_bar=4,
                bars=8,
                role="verse",
                target_density=0.6,
                target_tension=0.5,
            ),
        ],
        climax_section_id="main",
    )
    harmony = HarmonyPlan(
        chord_events=[
            ChordEvent(
                section_id="intro",
                start_beat=0.0,
                duration_beats=16.0,
                roman="I",
                function=HarmonicFunction.TONIC,
                tension_level=0.2,
            ),
            ChordEvent(
                section_id="main",
                start_beat=16.0,
                duration_beats=32.0,
                roman="V",
                function=HarmonicFunction.DOMINANT,
                tension_level=0.5,
            ),
        ],
        cadences={"main": CadenceRole.AUTHENTIC},
    )
    return MusicalPlan(
        form=form,
        harmony=harmony,
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test piece", keywords=["test"]),
        provenance=ProvenanceLog(),
    )


class TestRuleBasedNoteRealizer:
    """Unit tests for the rule-based note realizer."""

    def test_registered(self) -> None:
        assert "rule_based" in NOTE_REALIZERS

    def test_realize_produces_notes(self) -> None:
        plan = _make_plan()
        realizer = NOTE_REALIZERS["rule_based"]()
        prov = ProvenanceLog()
        score = realizer.realize(plan, seed=42, temperature=0.5, provenance=prov)
        assert len(score.all_notes()) > 0

    def test_realize_preserves_section_count(self) -> None:
        plan = _make_plan()
        realizer = NOTE_REALIZERS["rule_based"]()
        prov = ProvenanceLog()
        score = realizer.realize(plan, seed=42, temperature=0.5, provenance=prov)
        assert len(score.sections) == 2

    def test_realize_records_provenance(self) -> None:
        plan = _make_plan()
        realizer = NOTE_REALIZERS["rule_based"]()
        prov = ProvenanceLog()
        realizer.realize(plan, seed=42, temperature=0.5, provenance=prov)
        assert len(prov.records) > 0
        assert any("note_realization" in r.operation for r in prov.records)

    def test_deterministic_same_seed(self) -> None:
        plan = _make_plan()
        realizer = NOTE_REALIZERS["rule_based"]()
        prov1 = ProvenanceLog()
        prov2 = ProvenanceLog()
        score1 = realizer.realize(plan, seed=42, temperature=0.5, provenance=prov1)
        score2 = realizer.realize(plan, seed=42, temperature=0.5, provenance=prov2)
        notes1 = score1.all_notes()
        notes2 = score2.all_notes()
        assert len(notes1) == len(notes2)
        for n1, n2 in zip(notes1, notes2, strict=True):
            assert n1.pitch == n2.pitch


class TestPlanToV1Spec:
    """Tests for the plan-to-v1 conversion helper."""

    def test_converts_sections(self) -> None:
        plan = _make_plan()
        v1 = _plan_to_v1_spec(plan)
        assert len(v1.sections) == 2
        assert v1.sections[0].name == "intro"
        assert v1.sections[1].name == "main"

    def test_maps_tension_to_dynamics(self) -> None:
        plan = _make_plan()
        v1 = _plan_to_v1_spec(plan)
        # intro tension=0.2 → "p", main tension=0.5 → "mf"
        assert v1.sections[0].dynamics == "p"
        assert v1.sections[1].dynamics == "mf"

    def test_uses_intent_as_title(self) -> None:
        plan = _make_plan()
        v1 = _plan_to_v1_spec(plan)
        assert v1.title == "test piece"


class TestTensionToDynamics:
    """Tests for tension-to-dynamics mapping."""

    def test_low_tension(self) -> None:
        assert _tension_to_dynamics(0.1) == "pp"

    def test_mid_tension(self) -> None:
        assert _tension_to_dynamics(0.5) == "mf"

    def test_high_tension(self) -> None:
        assert _tension_to_dynamics(0.95) == "fff"

    def test_boundary(self) -> None:
        assert _tension_to_dynamics(0.0) == "pp"
        assert _tension_to_dynamics(1.0) == "fff"
