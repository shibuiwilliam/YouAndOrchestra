"""Tests for Adversarial Critic rules.

Each rule has at least 2 tests: one that triggers a finding (positive)
and one that stays silent (negative).
"""

from __future__ import annotations

from yao.ir.plan.harmony import CadenceRole, ChordEvent, HarmonicFunction, HarmonyPlan
from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed, MotifTransform
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.phrase import (
    Phrase,
    PhraseCadence,
    PhrasePlan,
    PhraseRole,
)
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.intent import IntentSpec
from yao.verify.critique.emotional import IntentDivergenceDetector, TrajectoryViolationDetector
from yao.verify.critique.harmonic import (
    CadenceWeaknessDetector,
    ClicheChordProgressionDetector,
    HarmonicMonotonyDetector,
)
from yao.verify.critique.melodic import (
    MotifRecurrenceDetector,
    PhraseClosureWeaknessDetector,
)
from yao.verify.critique.rhythmic import RhythmicMonotonyDetector
from yao.verify.critique.structural import (
    ClimaxAbsenceDetector,
    FormImbalanceDetector,
    SectionMonotonyDetector,
)


def _make_spec(**overrides: object) -> CompositionSpecV2:
    """Create a minimal v2 spec for testing."""
    defaults = {
        "version": "2",
        "identity": {"title": "Test", "duration_sec": 60},
        "global": {"key": "C major", "bpm": 120},
        "form": {
            "sections": [
                {"id": "verse", "bars": 8},
                {"id": "chorus", "bars": 8},
            ]
        },
        "arrangement": {"instruments": {"piano": {"role": "melody"}}},
    }
    defaults.update(overrides)
    return CompositionSpecV2.model_validate(defaults)


def _make_plan(
    sections: list[SectionPlan] | None = None,
    harmony: HarmonyPlan | None = None,
    intent_text: str = "",
    trajectory: MultiDimensionalTrajectory | None = None,
    motif: MotifPlan | None = None,
    phrase: PhrasePlan | None = None,
) -> MusicalPlan:
    """Create a MusicalPlan for testing."""
    if sections is None:
        sections = [
            SectionPlan("verse", 0, 8, "verse", 0.5, 0.4),
            SectionPlan("chorus", 8, 8, "chorus", 0.6, 0.7),
        ]
    return MusicalPlan(
        form=SongFormPlan(sections=sections),
        harmony=harmony or HarmonyPlan(),
        trajectory=trajectory or MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text=intent_text, keywords=[]),
        provenance=ProvenanceLog(),
        motif=motif,
        phrase=phrase,
    )


# ============ Structural Rules ============


class TestSectionMonotonyDetector:
    """Test SectionMonotonyDetector."""

    def test_positive_detects_monotonous_sections(self) -> None:
        plan = _make_plan(
            sections=[
                SectionPlan("verse", 0, 8, "verse", 0.5, 0.5),
                SectionPlan("chorus", 8, 8, "chorus", 0.5, 0.52),  # nearly same
            ]
        )
        findings = SectionMonotonyDetector().detect(plan, _make_spec())
        assert len(findings) == 1
        assert "monotony" in findings[0].rule_id

    def test_negative_varied_sections(self) -> None:
        plan = _make_plan(
            sections=[
                SectionPlan("verse", 0, 8, "verse", 0.5, 0.3),
                SectionPlan("chorus", 8, 8, "chorus", 0.7, 0.8),  # clearly different
            ]
        )
        findings = SectionMonotonyDetector().detect(plan, _make_spec())
        assert len(findings) == 0


class TestClimaxAbsenceDetector:
    """Test ClimaxAbsenceDetector."""

    def test_positive_no_climax(self) -> None:
        plan = _make_plan(
            sections=[
                SectionPlan("verse", 0, 8, "verse", 0.5, 0.4),
                SectionPlan("chorus", 8, 8, "chorus", 0.5, 0.5),
            ]
        )
        findings = ClimaxAbsenceDetector().detect(plan, _make_spec())
        assert len(findings) == 1

    def test_negative_has_climax(self) -> None:
        plan = _make_plan(
            sections=[
                SectionPlan("verse", 0, 8, "verse", 0.5, 0.3),
                SectionPlan("chorus", 8, 8, "chorus", 0.8, 0.8, is_climax=True),
            ]
        )
        findings = ClimaxAbsenceDetector().detect(plan, _make_spec())
        assert len(findings) == 0

    def test_negative_high_tension_no_flag(self) -> None:
        """High tension section without is_climax flag should still pass."""
        plan = _make_plan(
            sections=[
                SectionPlan("verse", 0, 8, "verse", 0.5, 0.3),
                SectionPlan("chorus", 8, 8, "chorus", 0.8, 0.85),
            ]
        )
        findings = ClimaxAbsenceDetector().detect(plan, _make_spec())
        assert len(findings) == 0  # max_tension >= 0.7 is enough


class TestFormImbalanceDetector:
    """Test FormImbalanceDetector."""

    def test_positive_imbalanced(self) -> None:
        plan = _make_plan(
            sections=[
                SectionPlan("intro", 0, 2, "intro", 0.3, 0.2),
                SectionPlan("verse", 2, 32, "verse", 0.5, 0.5),
            ]
        )
        findings = FormImbalanceDetector().detect(plan, _make_spec())
        assert len(findings) == 1
        assert findings[0].evidence["ratio"] > 4

    def test_negative_balanced(self) -> None:
        plan = _make_plan(
            sections=[
                SectionPlan("verse", 0, 8, "verse", 0.5, 0.5),
                SectionPlan("chorus", 8, 8, "chorus", 0.7, 0.7),
            ]
        )
        findings = FormImbalanceDetector().detect(plan, _make_spec())
        assert len(findings) == 0


# ============ Harmonic Rules ============


class TestClicheChordProgressionDetector:
    """Test ClicheChordProgressionDetector."""

    def test_positive_cliche_repeated(self) -> None:
        # I-V-vi-IV repeated 3 times = 12 chords
        chords = []
        pattern = ["I", "V", "vi", "IV"]
        for i in range(12):
            chords.append(
                ChordEvent(
                    section_id="verse",
                    start_beat=float(i * 4),
                    duration_beats=4.0,
                    roman=pattern[i % 4],
                    function=HarmonicFunction.TONIC,
                    tension_level=0.5,
                )
            )
        plan = _make_plan(harmony=HarmonyPlan(chord_events=chords))
        findings = ClicheChordProgressionDetector().detect(plan, _make_spec())
        assert len(findings) >= 1

    def test_negative_varied_progression(self) -> None:
        chords = [
            ChordEvent("verse", 0.0, 4.0, "I", HarmonicFunction.TONIC, 0.5),
            ChordEvent("verse", 4.0, 4.0, "vi", HarmonicFunction.TONIC, 0.5),
            ChordEvent("verse", 8.0, 4.0, "ii", HarmonicFunction.PREDOMINANT, 0.5),
            ChordEvent("verse", 12.0, 4.0, "V", HarmonicFunction.DOMINANT, 0.5),
        ]
        plan = _make_plan(harmony=HarmonyPlan(chord_events=chords))
        findings = ClicheChordProgressionDetector().detect(plan, _make_spec())
        assert len(findings) == 0


class TestCadenceWeaknessDetector:
    """Test CadenceWeaknessDetector."""

    def test_positive_no_cadence(self) -> None:
        plan = _make_plan(harmony=HarmonyPlan(cadences={}))
        findings = CadenceWeaknessDetector().detect(plan, _make_spec())
        assert len(findings) == 2  # verse and chorus both missing

    def test_negative_has_cadences(self) -> None:
        plan = _make_plan(
            harmony=HarmonyPlan(
                cadences={
                    "verse": CadenceRole.HALF,
                    "chorus": CadenceRole.AUTHENTIC,
                }
            )
        )
        findings = CadenceWeaknessDetector().detect(plan, _make_spec())
        assert len(findings) == 0


class TestHarmonicMonotonyDetector:
    """Test HarmonicMonotonyDetector."""

    def test_positive_only_two_chords(self) -> None:
        chords = []
        for i in range(8):
            chords.append(
                ChordEvent(
                    section_id="verse",
                    start_beat=float(i * 4),
                    duration_beats=4.0,
                    roman="I" if i % 2 == 0 else "V",
                    function=HarmonicFunction.TONIC,
                    tension_level=0.5,
                )
            )
        plan = _make_plan(
            sections=[SectionPlan("verse", 0, 8, "verse", 0.5, 0.5)],
            harmony=HarmonyPlan(chord_events=chords),
        )
        findings = HarmonicMonotonyDetector().detect(plan, _make_spec())
        assert len(findings) == 1

    def test_negative_varied_chords(self) -> None:
        chords = []
        romans = ["I", "IV", "V", "vi", "ii", "iii", "V/V", "I"]
        for i, roman in enumerate(romans):
            chords.append(
                ChordEvent(
                    section_id="verse",
                    start_beat=float(i * 4),
                    duration_beats=4.0,
                    roman=roman,
                    function=HarmonicFunction.TONIC,
                    tension_level=0.5,
                )
            )
        plan = _make_plan(
            sections=[SectionPlan("verse", 0, 8, "verse", 0.5, 0.5)],
            harmony=HarmonyPlan(chord_events=chords),
        )
        findings = HarmonicMonotonyDetector().detect(plan, _make_spec())
        assert len(findings) == 0


# ============ Melodic Rules ============


class TestMotifRecurrenceDetector:
    """Test MotifRecurrenceDetector."""

    def test_positive_low_recurrence(self) -> None:
        motif = MotifPlan(
            seeds=[MotifSeed("M1", (1.0,), (0,), "verse")],
            placements=[MotifPlacement("M1", "verse", 0.0)],  # only once
        )
        plan = _make_plan(motif=motif)
        findings = MotifRecurrenceDetector().detect(plan, _make_spec())
        assert len(findings) == 1
        assert findings[0].evidence["recurrence_count"] == 1

    def test_negative_sufficient_recurrence(self) -> None:
        motif = MotifPlan(
            seeds=[MotifSeed("M1", (1.0,), (0,), "verse")],
            placements=[
                MotifPlacement("M1", "verse", 0.0),
                MotifPlacement("M1", "chorus", 16.0, MotifTransform.SEQUENCE_UP),
                MotifPlacement("M1", "verse", 32.0, MotifTransform.INVERSION),
            ],
        )
        plan = _make_plan(motif=motif)
        findings = MotifRecurrenceDetector().detect(plan, _make_spec())
        assert len(findings) == 0


class TestPhraseClosureWeaknessDetector:
    """Test PhraseClosureWeaknessDetector."""

    def test_positive_consequent_without_cadence(self) -> None:
        phrase_plan = PhrasePlan(
            phrases=[
                Phrase("p1", "verse", 0.0, 16.0, PhraseRole.CONSEQUENT, cadence=PhraseCadence.NONE),
            ]
        )
        plan = _make_plan(phrase=phrase_plan)
        findings = PhraseClosureWeaknessDetector().detect(plan, _make_spec())
        assert len(findings) == 1

    def test_negative_consequent_with_cadence(self) -> None:
        phrase_plan = PhrasePlan(
            phrases=[
                Phrase(
                    "p1",
                    "verse",
                    0.0,
                    16.0,
                    PhraseRole.CONSEQUENT,
                    cadence=PhraseCadence.AUTHENTIC,
                ),
            ]
        )
        plan = _make_plan(phrase=phrase_plan)
        findings = PhraseClosureWeaknessDetector().detect(plan, _make_spec())
        assert len(findings) == 0


# ============ Rhythmic Rules ============


class TestRhythmicMonotonyDetector:
    """Test RhythmicMonotonyDetector."""

    def test_positive_all_same_density(self) -> None:
        plan = _make_plan(
            sections=[
                SectionPlan("intro", 0, 4, "intro", 0.5, 0.5),
                SectionPlan("verse", 4, 8, "verse", 0.5, 0.5),
                SectionPlan("chorus", 12, 8, "chorus", 0.5, 0.5),
            ]
        )
        findings = RhythmicMonotonyDetector().detect(plan, _make_spec())
        assert len(findings) == 1

    def test_negative_varied_density(self) -> None:
        plan = _make_plan(
            sections=[
                SectionPlan("intro", 0, 4, "intro", 0.3, 0.2),
                SectionPlan("verse", 4, 8, "verse", 0.5, 0.5),
                SectionPlan("chorus", 12, 8, "chorus", 0.8, 0.8),
            ]
        )
        findings = RhythmicMonotonyDetector().detect(plan, _make_spec())
        assert len(findings) == 0


# ============ Emotional Rules ============


class TestIntentDivergenceDetector:
    """Test IntentDivergenceDetector."""

    def test_positive_calm_intent_high_tension(self) -> None:
        plan = _make_plan(
            sections=[
                SectionPlan("verse", 0, 8, "verse", 0.5, 0.9),  # very high tension
            ],
            intent_text="a calm peaceful piano piece",
        )
        findings = IntentDivergenceDetector().detect(plan, _make_spec())
        assert len(findings) >= 1

    def test_negative_calm_intent_low_tension(self) -> None:
        plan = _make_plan(
            sections=[
                SectionPlan("verse", 0, 8, "verse", 0.5, 0.3),
            ],
            intent_text="a calm peaceful piano piece",
        )
        findings = IntentDivergenceDetector().detect(plan, _make_spec())
        assert len(findings) == 0

    def test_no_intent_no_findings(self) -> None:
        plan = _make_plan(intent_text="")
        findings = IntentDivergenceDetector().detect(plan, _make_spec())
        assert len(findings) == 0


class TestTrajectoryViolationDetector:
    """Test TrajectoryViolationDetector."""

    def test_positive_trajectory_mismatch(self) -> None:
        # Trajectory says 0.1 tension, section says 0.8
        from yao.ir.trajectory import MultiDimensionalTrajectory, TrajectoryCurve

        low_traj = MultiDimensionalTrajectory(
            tension=TrajectoryCurve(curve_type="linear", target=0.1),
            density=TrajectoryCurve(curve_type="linear", target=0.5),
            predictability=TrajectoryCurve(curve_type="linear", target=0.5),
            brightness=TrajectoryCurve(curve_type="linear", target=0.5),
            register_height=TrajectoryCurve(curve_type="linear", target=0.5),
        )
        plan = _make_plan(
            sections=[SectionPlan("verse", 0, 8, "verse", 0.5, 0.8)],
            trajectory=low_traj,
        )
        findings = TrajectoryViolationDetector().detect(plan, _make_spec())
        assert len(findings) >= 1

    def test_negative_trajectory_aligned(self) -> None:
        plan = _make_plan(
            sections=[SectionPlan("verse", 0, 8, "verse", 0.5, 0.5)],
        )
        findings = TrajectoryViolationDetector().detect(plan, _make_spec())
        assert len(findings) == 0


# ============ Registry Integration ============


class TestCritiqueRegistry:
    """Test that all rules are registered."""

    def test_all_rules_registered(self) -> None:
        from yao.verify.critique import CRITIQUE_RULES

        assert len(CRITIQUE_RULES) >= 12  # noqa: PLR2004

    def test_run_all_produces_findings(self) -> None:
        """Run all rules on a deliberately problematic plan."""
        from yao.verify.critique import CRITIQUE_RULES

        plan = _make_plan(
            sections=[
                SectionPlan("verse", 0, 8, "verse", 0.5, 0.5),
                SectionPlan("chorus", 8, 8, "chorus", 0.5, 0.5),
            ],
            harmony=HarmonyPlan(cadences={}),
        )
        findings = CRITIQUE_RULES.run_all(plan, _make_spec())
        # Should find: section monotony, climax absence, cadence weakness (2x),
        # rhythmic monotony
        assert len(findings) >= 3  # noqa: PLR2004
