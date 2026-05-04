"""Tests for groove critique rules (Layer 6).

Tests cover:
- groove_inconsistency fires on groove-dependent genres without groove
- microtiming_flatness fires on long pieces with flat timing
- ensemble_groove_conflict fires on swing/genre mismatches
"""

from __future__ import annotations

from tests.helpers import make_minimal_spec_v2
from yao.ir.plan.drums import DrumHit, DrumPattern, KitPiece
from yao.ir.plan.harmony import HarmonyPlan
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec
from yao.verify.critique.groove_rules import (
    EnsembleGrooveConflictDetector,
    GrooveInconsistencyDetector,
    MicrotimingFlatnessDetector,
)


def _make_plan(
    genre: str = "general",
    drums: DrumPattern | None = None,
    total_bars: int = 8,
) -> MusicalPlan:
    sections = [
        SectionPlan(
            id="section_a",
            start_bar=0,
            bars=total_bars,
            role="verse",
            target_density=0.5,
            target_tension=0.5,
        ),
    ]
    return MusicalPlan(
        form=SongFormPlan(sections=sections),
        harmony=HarmonyPlan(),
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test", keywords=[]),
        provenance=ProvenanceLog(),
        global_context=GlobalContext(genre=genre),
        drums=drums,
    )


def _make_drum_pattern(
    swing: float = 0.0,
    humanize: float = 0.0,
    microtiming_ms: float = 0.0,
    hit_count: int = 8,
) -> DrumPattern:
    hits = [
        DrumHit(
            time=float(i * 0.5),
            duration=0.25,
            kit_piece=KitPiece.KICK if i % 4 == 0 else KitPiece.CLOSED_HAT,
            velocity=80,
            microtiming_ms=microtiming_ms,
        )
        for i in range(hit_count)
    ]
    return DrumPattern(
        id="test",
        genre="test",
        hits=hits,
        swing=swing,
        humanize=humanize,
    )


class TestGrooveInconsistencyDetector:
    def test_fires_on_jazz_without_groove(self) -> None:
        plan = _make_plan(genre="jazz", drums=_make_drum_pattern())
        spec = make_minimal_spec_v2()
        detector = GrooveInconsistencyDetector()
        findings = detector.detect(plan, spec)
        assert any(f.rule_id == "rhythm.groove_inconsistency" for f in findings)

    def test_no_fire_on_pop(self) -> None:
        plan = _make_plan(genre="pop", drums=_make_drum_pattern())
        spec = make_minimal_spec_v2()
        detector = GrooveInconsistencyDetector()
        findings = detector.detect(plan, spec)
        assert len(findings) == 0

    def test_no_fire_with_swing(self) -> None:
        plan = _make_plan(genre="jazz", drums=_make_drum_pattern(swing=0.5))
        spec = make_minimal_spec_v2()
        detector = GrooveInconsistencyDetector()
        findings = detector.detect(plan, spec)
        assert len(findings) == 0


class TestMicrotimingFlatnessDetector:
    def test_fires_on_long_flat_piece(self) -> None:
        plan = _make_plan(
            total_bars=20,
            drums=_make_drum_pattern(hit_count=40),
        )
        spec = make_minimal_spec_v2()
        detector = MicrotimingFlatnessDetector()
        findings = detector.detect(plan, spec)
        assert any(f.rule_id == "rhythm.microtiming_flatness" for f in findings)

    def test_no_fire_on_short_piece(self) -> None:
        plan = _make_plan(
            total_bars=8,
            drums=_make_drum_pattern(),
        )
        spec = make_minimal_spec_v2()
        detector = MicrotimingFlatnessDetector()
        findings = detector.detect(plan, spec)
        assert len(findings) == 0

    def test_no_fire_with_humanize(self) -> None:
        plan = _make_plan(
            total_bars=20,
            drums=_make_drum_pattern(humanize=0.3, hit_count=40),
        )
        spec = make_minimal_spec_v2()
        detector = MicrotimingFlatnessDetector()
        findings = detector.detect(plan, spec)
        assert len(findings) == 0

    def test_no_fire_with_microtiming(self) -> None:
        plan = _make_plan(
            total_bars=20,
            drums=_make_drum_pattern(microtiming_ms=5.0, hit_count=40),
        )
        spec = make_minimal_spec_v2()
        detector = MicrotimingFlatnessDetector()
        findings = detector.detect(plan, spec)
        assert len(findings) == 0


class TestEnsembleGrooveConflictDetector:
    def test_fires_high_swing_in_edm(self) -> None:
        plan = _make_plan(genre="edm", drums=_make_drum_pattern(swing=0.5))
        spec = make_minimal_spec_v2()
        detector = EnsembleGrooveConflictDetector()
        findings = detector.detect(plan, spec)
        assert any(f.rule_id == "rhythm.ensemble_groove_conflict" for f in findings)

    def test_fires_no_swing_in_jazz(self) -> None:
        plan = _make_plan(genre="jazz", drums=_make_drum_pattern(swing=0.1))
        spec = make_minimal_spec_v2()
        detector = EnsembleGrooveConflictDetector()
        findings = detector.detect(plan, spec)
        assert any(f.rule_id == "rhythm.ensemble_groove_conflict" for f in findings)

    def test_no_fire_matching_genre(self) -> None:
        plan = _make_plan(genre="pop", drums=_make_drum_pattern(swing=0.1))
        spec = make_minimal_spec_v2()
        detector = EnsembleGrooveConflictDetector()
        findings = detector.detect(plan, spec)
        assert len(findings) == 0
