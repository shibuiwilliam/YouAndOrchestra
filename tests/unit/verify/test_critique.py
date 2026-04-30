"""Tests for critique system types, base class, and registry."""

from __future__ import annotations

import pytest

from yao.ir.plan.harmony import ChordEvent, HarmonicFunction, HarmonyPlan
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.intent import IntentSpec
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.registry import CritiqueRegistry
from yao.verify.critique.types import Finding, Role, Severity, SongLocation

_MINIMAL_V2 = {
    "version": "2",
    "identity": {"title": "Critique Test", "duration_sec": 16},
    "global": {"key": "C major", "bpm": 120, "time_signature": "4/4"},
    "form": {"sections": [{"id": "main", "bars": 8, "density": 0.5}]},
    "arrangement": {"instruments": {"piano": {"role": "melody"}}},
}


def _make_plan() -> MusicalPlan:
    return MusicalPlan(
        form=SongFormPlan(
            sections=[SectionPlan(
                id="main", start_bar=0, bars=8, role="verse",
                target_density=0.5, target_tension=0.5,
            )],
            climax_section_id="main",
        ),
        harmony=HarmonyPlan(chord_events=[
            ChordEvent(
                section_id="main", start_beat=0.0, duration_beats=32.0,
                roman="I", function=HarmonicFunction.TONIC, tension_level=0.5,
            ),
        ]),
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test", keywords=[]),
        provenance=ProvenanceLog(),
    )


class TestFinding:
    def test_construction(self) -> None:
        f = Finding(
            rule_id="test.rule",
            severity=Severity.MAJOR,
            role=Role.HARMONY,
            issue="Test issue",
        )
        assert f.rule_id == "test.rule"
        assert f.severity == Severity.MAJOR

    def test_with_evidence(self) -> None:
        f = Finding(
            rule_id="test.rule",
            severity=Severity.MINOR,
            role=Role.MELODY,
            issue="Contour is flat",
            evidence={"direction_changes": 2, "target": 10},
            location=SongLocation(section="verse", bars=(4, 8)),
        )
        assert f.evidence["direction_changes"] == 2
        assert f.location is not None
        assert f.location.section == "verse"

    def test_with_recommendation(self) -> None:
        f = Finding(
            rule_id="test.rule",
            severity=Severity.SUGGESTION,
            role=Role.ARRANGEMENT,
            issue="Thin texture",
            recommendation={"arrangement": "add counter-melody"},
        )
        assert "arrangement" in f.recommendation

    def test_frozen(self) -> None:
        f = Finding(
            rule_id="test.rule",
            severity=Severity.CRITICAL,
            role=Role.STRUCTURE,
            issue="No climax",
        )
        with pytest.raises(AttributeError):
            f.issue = "changed"  # type: ignore[misc]


class TestSongLocation:
    def test_section_only(self) -> None:
        loc = SongLocation(section="chorus")
        assert loc.section == "chorus"
        assert loc.bars is None

    def test_with_bars(self) -> None:
        loc = SongLocation(section="verse", bars=(4, 12))
        assert loc.bars == (4, 12)

    def test_with_instrument(self) -> None:
        loc = SongLocation(instrument="violin")
        assert loc.instrument == "violin"


class _DummyRule(CritiqueRule):
    """Test rule that always finds an issue."""

    rule_id = "test.always_fail"
    role = Role.STRUCTURE

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        return [Finding(
            rule_id=self.rule_id,
            severity=Severity.MINOR,
            role=self.role,
            issue="Dummy issue for testing",
        )]


class _SilentRule(CritiqueRule):
    """Test rule that never finds issues."""

    rule_id = "test.always_pass"
    role = Role.MELODY

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        return []


class TestCritiqueRegistry:
    def test_register_and_count(self) -> None:
        reg = CritiqueRegistry()
        reg.register(_DummyRule())
        assert len(reg) == 1

    def test_run_all(self) -> None:
        reg = CritiqueRegistry()
        reg.register(_DummyRule())
        reg.register(_SilentRule())
        plan = _make_plan()
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        findings = reg.run_all(plan, spec)
        assert len(findings) == 1
        assert findings[0].rule_id == "test.always_fail"

    def test_rules_by_role(self) -> None:
        reg = CritiqueRegistry()
        reg.register(_DummyRule())
        reg.register(_SilentRule())
        assert len(reg.rules_by_role(Role.STRUCTURE)) == 1
        assert len(reg.rules_by_role(Role.MELODY)) == 1
        assert len(reg.rules_by_role(Role.HARMONY)) == 0

    def test_all_rules(self) -> None:
        reg = CritiqueRegistry()
        reg.register(_DummyRule())
        reg.register(_SilentRule())
        assert len(reg.all_rules()) == 2

    def test_empty_registry(self) -> None:
        reg = CritiqueRegistry()
        plan = _make_plan()
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        assert reg.run_all(plan, spec) == []
