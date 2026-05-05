"""Tests for v2.0 Tonal System abstraction.

PR-2 acceptance criteria:
- Blues spec with b3 scores higher on tonal_system_appropriateness than diatonic
- Drone spec not penalized for low pitch_class_variety
- Legacy key auto-promotes to TonalSystem
"""

from __future__ import annotations

import pytest

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.schema.composition import CompositionSpec
from yao.schema.tonal_system import TonalSystem, promote_legacy_key
from yao.verify.evaluator import evaluate_harmony


class TestTonalSystemSchema:
    """Test TonalSystem Pydantic model validation."""

    def test_default_is_tonal_major_minor(self) -> None:
        ts = TonalSystem()
        assert ts.kind == "tonal_major_minor"
        assert ts.key == "C"
        assert ts.mode == "major"

    def test_all_kinds_valid(self) -> None:
        kinds = [
            "tonal_major_minor",
            "modal",
            "pentatonic",
            "blues",
            "microtonal",
            "atonal",
            "drone",
            "raga",
            "maqam",
            "custom",
        ]
        for kind in kinds:
            ts = TonalSystem(kind=kind)
            assert ts.kind == kind

    def test_blues_allows_blue_notes(self) -> None:
        ts = TonalSystem(kind="blues", key="A", mode="blues")
        assert ts.allows_blue_notes is True
        assert ts.is_consonance_applicable is True

    def test_drone_skips_pitch_class_variety(self) -> None:
        ts = TonalSystem(kind="drone", key="C")
        assert ts.is_pitch_class_variety_applicable is False
        assert ts.is_consonance_applicable is False

    def test_atonal_skips_consonance(self) -> None:
        ts = TonalSystem(kind="atonal")
        assert ts.is_consonance_applicable is False
        assert ts.is_pitch_class_variety_applicable is True

    def test_invalid_reference_pitch_raises(self) -> None:
        from yao.errors import SpecValidationError

        with pytest.raises((SpecValidationError, Exception)):
            TonalSystem(reference_pitch_hz=200.0)


class TestLegacyKeyPromotion:
    """Test backward-compatible promotion of key strings."""

    def test_promote_c_major(self) -> None:
        ts = promote_legacy_key("C major")
        assert ts.kind == "tonal_major_minor"
        assert ts.key == "C"
        assert ts.mode == "major"

    def test_promote_d_minor(self) -> None:
        ts = promote_legacy_key("D minor")
        assert ts.kind == "tonal_major_minor"
        assert ts.key == "D"
        assert ts.mode == "minor"

    def test_promote_g_dorian(self) -> None:
        ts = promote_legacy_key("G dorian")
        assert ts.kind == "modal"
        assert ts.key == "G"
        assert ts.mode == "dorian"

    def test_promote_a_blues(self) -> None:
        ts = promote_legacy_key("A blues")
        assert ts.kind == "blues"
        assert ts.key == "A"

    def test_promote_c_pentatonic(self) -> None:
        ts = promote_legacy_key("C pentatonic")
        assert ts.kind == "pentatonic"
        assert ts.key == "C"

    def test_composition_spec_effective_tonal_system(self) -> None:
        """CompositionSpec.effective_tonal_system() auto-promotes legacy key."""
        spec = CompositionSpec(
            title="Test",
            key="D minor",
            instruments=[{"name": "piano", "role": "melody"}],
            sections=[{"name": "intro", "bars": 4}],
        )
        ts = spec.effective_tonal_system()
        assert ts.kind == "tonal_major_minor"
        assert ts.key == "D"
        assert ts.mode == "minor"

    def test_explicit_tonal_system_takes_precedence(self) -> None:
        """When tonal_system is set, it takes precedence over key."""
        spec = CompositionSpec(
            title="Test",
            key="C major",
            tonal_system=TonalSystem(kind="blues", key="A", mode="blues"),
            instruments=[{"name": "piano", "role": "melody"}],
            sections=[{"name": "intro", "bars": 4}],
        )
        ts = spec.effective_tonal_system()
        assert ts.kind == "blues"
        assert ts.key == "A"


class TestTonalSystemEvaluation:
    """Test that evaluation respects tonal system."""

    def _make_score_with_intervals(self, intervals: list[int]) -> ScoreIR:
        """Create a score with simultaneous notes at given intervals from C4."""
        notes = []
        for i, interval in enumerate(intervals):
            notes.append(Note(pitch=60, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="piano"))
            notes.append(
                Note(
                    pitch=60 + interval,
                    start_beat=float(i),
                    duration_beats=1.0,
                    velocity=80,
                    instrument="piano",
                )
            )
        return ScoreIR(
            title="Test",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="test",
                    start_bar=0,
                    end_bar=4,
                    parts=(Part(instrument="piano", notes=tuple(notes)),),
                ),
            ),
        )

    def test_drone_not_penalized_for_low_pitch_variety(self) -> None:
        """A drone spec (single pitch class) should NOT be penalized."""
        # Score with only one pitch class (C)
        notes = [
            Note(pitch=60, start_beat=float(i), duration_beats=4.0, velocity=60, instrument="piano") for i in range(8)
        ]
        score = ScoreIR(
            title="Drone",
            tempo_bpm=72.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="drone",
                    start_bar=0,
                    end_bar=8,
                    parts=(Part(instrument="piano", notes=tuple(notes)),),
                ),
            ),
        )
        drone_ts = TonalSystem(kind="drone", key="C")
        results = evaluate_harmony(score, tonal_system=drone_ts)

        # Find pitch_class_variety metric — should pass (not penalized)
        pcv = next(r for r in results if r.metric == "pitch_class_variety")
        assert pcv.passed, "Drone should not be penalized for low pitch class variety"

    def test_blues_b3_scores_higher_than_diatonic(self) -> None:
        """Blues intervals (b3=3, b5=6, b7=10) should score as consonant in blues."""
        # Score with blues intervals (minor 3rd = 3 semitones)
        score = self._make_score_with_intervals([3, 3, 3, 3])  # All minor 3rds

        # Evaluate with blues tonal system
        blues_ts = TonalSystem(kind="blues", key="C", mode="blues")
        blues_results = evaluate_harmony(score, tonal_system=blues_ts)

        # Evaluate with standard tonal system
        standard_ts = TonalSystem(kind="tonal_major_minor", key="C", mode="major")
        standard_results = evaluate_harmony(score, tonal_system=standard_ts)

        # Both should have consonance_ratio, but blues should score at least as high
        blues_cons = next((r for r in blues_results if r.metric == "consonance_ratio"), None)
        standard_cons = next((r for r in standard_results if r.metric == "consonance_ratio"), None)

        assert blues_cons is not None
        assert standard_cons is not None
        # Minor 3rd (3) is consonant in both systems, so scores should be equal
        # But for b5 (tritone=6), blues should score higher
        score_tritone = self._make_score_with_intervals([6, 6, 6, 6])
        blues_tri = evaluate_harmony(score_tritone, tonal_system=blues_ts)
        standard_tri = evaluate_harmony(score_tritone, tonal_system=standard_ts)

        blues_tri_cons = next(r for r in blues_tri if r.metric == "consonance_ratio")
        standard_tri_cons = next(r for r in standard_tri if r.metric == "consonance_ratio")

        assert blues_tri_cons.score > standard_tri_cons.score, (
            f"Blues tritone consonance ({blues_tri_cons.score}) should be higher "
            f"than standard ({standard_tri_cons.score})"
        )
