"""Tests for surprise and tension critique rules (Layer 6).

Tests cover:
- surprise_deficit fires on flat plans with no arcs
- surprise_overload fires on over-saturated plans
- tension_arc_unresolved fires on non-deceptive arcs without release
- tension_arc_unresolved exempt for deceptive arcs
"""

from __future__ import annotations

from yao.ir.plan.harmony import ChordEvent, HarmonicFunction, HarmonyPlan
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.tension_arc import ArcLocation, ArcRelease, TensionArc, TensionPattern
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.intent import IntentSpec
from yao.verify.critique.surprise_rules import (
    SurpriseDeficitDetector,
    SurpriseOverloadDetector,
)
from yao.verify.critique.tension_rules import TensionArcUnresolvedDetector


def _make_spec() -> CompositionSpecV2:
    """Create a minimal CompositionSpecV2 for testing."""
    from tests.helpers import make_minimal_spec_v2

    return make_minimal_spec_v2()


def _make_plan(
    sections: list[SectionPlan] | None = None,
    tension_arcs: tuple[TensionArc, ...] = (),
) -> MusicalPlan:
    """Create a minimal MusicalPlan for testing."""
    if sections is None:
        sections = [
            SectionPlan(id="intro", start_bar=0, bars=4, role="intro", target_density=0.3, target_tension=0.3),
            SectionPlan(id="verse", start_bar=4, bars=8, role="verse", target_density=0.5, target_tension=0.5),
            SectionPlan(id="chorus", start_bar=12, bars=8, role="chorus", target_density=0.7, target_tension=0.7),
        ]
    harmony = HarmonyPlan(
        chord_events=[
            ChordEvent(
                section_id=s.id,
                start_beat=float(s.start_bar * 4),
                duration_beats=float(s.bars * 4),
                roman="I",
                function=HarmonicFunction.TONIC,
                tension_level=s.target_tension,
            )
            for s in sections
        ],
        tension_arcs=tension_arcs,
    )
    return MusicalPlan(
        form=SongFormPlan(
            sections=sections,
            climax_section_id="chorus" if any(s.id == "chorus" for s in sections) else "",
        ),
        harmony=harmony,
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test", keywords=[]),
        provenance=ProvenanceLog(),
    )


class TestSurpriseDeficitDetector:
    """Tests for SurpriseDeficitDetector."""

    def test_fires_with_no_arcs(self) -> None:
        """A 3-section plan with no tension arcs triggers deficit."""
        plan = _make_plan()
        spec = _make_spec()
        detector = SurpriseDeficitDetector()
        findings = detector.detect(plan, spec)

        assert len(findings) >= 1
        assert any(f.rule_id == "structure.surprise_deficit" for f in findings)

    def test_no_fire_with_arcs(self) -> None:
        """A plan with tension arcs should not trigger deficit for arc count."""
        arc = TensionArc(
            id="test",
            location=ArcLocation(section="verse", bar_start=5, bar_end=8),
            pattern=TensionPattern.LINEAR_RISE,
            target_release=ArcRelease(section="chorus", bar=1),
            intensity=0.7,
        )
        plan = _make_plan(tension_arcs=(arc,))
        spec = _make_spec()
        detector = SurpriseDeficitDetector()
        findings = detector.detect(plan, spec)

        arc_count_findings = [f for f in findings if "No tension arcs" in f.issue]
        assert len(arc_count_findings) == 0

    def test_fires_on_flat_tension(self) -> None:
        """Sections with very similar tension fire the low-contrast finding."""
        sections = [
            SectionPlan(id="a", start_bar=0, bars=8, role="verse", target_density=0.5, target_tension=0.5),
            SectionPlan(id="b", start_bar=8, bars=8, role="chorus", target_density=0.5, target_tension=0.55),
        ]
        plan = _make_plan(sections=sections)
        spec = _make_spec()
        detector = SurpriseDeficitDetector()
        findings = detector.detect(plan, spec)

        low_contrast = [f for f in findings if "Tension range" in f.issue]
        assert len(low_contrast) == 1


class TestSurpriseOverloadDetector:
    """Tests for SurpriseOverloadDetector."""

    def test_fires_on_over_saturated_arcs(self) -> None:
        """Arcs covering >80% of bars trigger overload."""
        sections = [
            SectionPlan(id="verse", start_bar=0, bars=8, role="verse", target_density=0.5, target_tension=0.5),
        ]
        arcs = (
            TensionArc(
                id="a1",
                location=ArcLocation(section="verse", bar_start=1, bar_end=4),
                pattern=TensionPattern.LINEAR_RISE,
                target_release=None,
                intensity=0.5,
            ),
            TensionArc(
                id="a2",
                location=ArcLocation(section="verse", bar_start=5, bar_end=8),
                pattern=TensionPattern.SPIKE,
                target_release=None,
                intensity=0.9,
            ),
        )
        plan = _make_plan(sections=sections, tension_arcs=arcs)
        spec = _make_spec()
        detector = SurpriseOverloadDetector()
        findings = detector.detect(plan, spec)

        assert any("coverage" in f.issue.lower() or "cover" in f.issue.lower() for f in findings)

    def test_fires_on_too_many_high_intensity(self) -> None:
        """More than 3 high-intensity arcs trigger overload."""
        sections = [
            SectionPlan(id="verse", start_bar=0, bars=32, role="verse", target_density=0.5, target_tension=0.5),
        ]
        arcs = tuple(
            TensionArc(
                id=f"a{i}",
                location=ArcLocation(section="verse", bar_start=i * 4 + 1, bar_end=i * 4 + 4),
                pattern=TensionPattern.SPIKE,
                target_release=None,
                intensity=0.85,
            )
            for i in range(4)
        )
        plan = _make_plan(sections=sections, tension_arcs=arcs)
        spec = _make_spec()
        detector = SurpriseOverloadDetector()
        findings = detector.detect(plan, spec)

        assert any("high-intensity" in f.issue.lower() for f in findings)

    def test_no_fire_moderate(self) -> None:
        """A single moderate arc should not trigger overload."""
        sections = [
            SectionPlan(id="verse", start_bar=0, bars=16, role="verse", target_density=0.5, target_tension=0.5),
        ]
        arc = TensionArc(
            id="a1",
            location=ArcLocation(section="verse", bar_start=5, bar_end=8),
            pattern=TensionPattern.LINEAR_RISE,
            target_release=None,
            intensity=0.6,
        )
        plan = _make_plan(sections=sections, tension_arcs=(arc,))
        spec = _make_spec()
        detector = SurpriseOverloadDetector()
        findings = detector.detect(plan, spec)

        assert len(findings) == 0


class TestTensionArcUnresolvedDetector:
    """Tests for TensionArcUnresolvedDetector."""

    def test_fires_on_unresolved_non_deceptive(self) -> None:
        """Non-deceptive arc without release fires."""
        arc = TensionArc(
            id="unresolved",
            location=ArcLocation(section="verse", bar_start=5, bar_end=8),
            pattern=TensionPattern.LINEAR_RISE,
            target_release=None,
            intensity=0.7,
        )
        plan = _make_plan(tension_arcs=(arc,))
        spec = _make_spec()
        detector = TensionArcUnresolvedDetector()
        findings = detector.detect(plan, spec)

        assert len(findings) == 1
        assert findings[0].rule_id == "harmony.tension_arc_unresolved"

    def test_exempt_deceptive(self) -> None:
        """Deceptive arcs without release are intentional — no finding."""
        arc = TensionArc(
            id="deceptive",
            location=ArcLocation(section="verse", bar_start=5, bar_end=8),
            pattern=TensionPattern.DECEPTIVE,
            target_release=None,
            intensity=0.7,
        )
        plan = _make_plan(tension_arcs=(arc,))
        spec = _make_spec()
        detector = TensionArcUnresolvedDetector()
        findings = detector.detect(plan, spec)

        assert len(findings) == 0

    def test_resolved_no_finding(self) -> None:
        """Resolved arc produces no finding."""
        arc = TensionArc(
            id="resolved",
            location=ArcLocation(section="verse", bar_start=5, bar_end=8),
            pattern=TensionPattern.LINEAR_RISE,
            target_release=ArcRelease(section="chorus", bar=1),
            intensity=0.7,
        )
        plan = _make_plan(tension_arcs=(arc,))
        spec = _make_spec()
        detector = TensionArcUnresolvedDetector()
        findings = detector.detect(plan, spec)

        assert len(findings) == 0

    def test_severity_depends_on_intensity(self) -> None:
        """High-intensity unresolved arcs get MAJOR severity."""
        arc_high = TensionArc(
            id="high",
            location=ArcLocation(section="verse", bar_start=5, bar_end=8),
            pattern=TensionPattern.SPIKE,
            target_release=None,
            intensity=0.9,
        )
        arc_low = TensionArc(
            id="low",
            location=ArcLocation(section="verse", bar_start=1, bar_end=4),
            pattern=TensionPattern.DIP,
            target_release=None,
            intensity=0.3,
        )
        plan = _make_plan(tension_arcs=(arc_high, arc_low))
        spec = _make_spec()
        detector = TensionArcUnresolvedDetector()
        findings = detector.detect(plan, spec)

        assert len(findings) == 2
        severities = {f.evidence["arc_id"]: f.severity for f in findings}
        assert severities["high"] == "major"
        assert severities["low"] == "minor"
