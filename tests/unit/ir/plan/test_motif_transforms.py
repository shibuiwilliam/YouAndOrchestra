"""Tests for motif transformations including new v2.1 paraphrase transforms."""

from __future__ import annotations

import random

import pytest

from yao.generators.note.rule_based_v2 import _apply_motif_transform
from yao.ir.plan.motif import MotifTransform

# Sample motif for testing
SAMPLE_INTERVALS = (0, 2, 4, 5, 7, 5, 4, 2)
SAMPLE_RHYTHM = (1.0, 0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 1.0)


class TestOriginalTransforms:
    """Verify original transforms still work correctly."""

    def test_identity(self) -> None:
        result = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.IDENTITY)
        assert result == (SAMPLE_INTERVALS, SAMPLE_RHYTHM)

    def test_inversion(self) -> None:
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.INVERSION)
        assert iv == tuple(-i for i in SAMPLE_INTERVALS)
        assert rh == SAMPLE_RHYTHM

    def test_retrograde(self) -> None:
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.RETROGRADE)
        assert iv == tuple(reversed(SAMPLE_INTERVALS))
        assert rh == tuple(reversed(SAMPLE_RHYTHM))

    def test_sequence_up(self) -> None:
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.SEQUENCE_UP)
        assert iv == tuple(i + 2 for i in SAMPLE_INTERVALS)


class TestNewTransforms:
    """Test v2.1 paraphrase transforms."""

    def test_ornament_add_with_rng(self) -> None:
        rng = random.Random(42)
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.ORNAMENT_ADD, rng)
        # Ornaments add notes, so length may increase
        assert len(iv) >= len(SAMPLE_INTERVALS)
        assert len(iv) == len(rh)

    def test_ornament_add_deterministic_no_rng(self) -> None:
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.ORNAMENT_ADD, None)
        # Without rng, no ornaments added
        assert iv == SAMPLE_INTERVALS
        assert rh == SAMPLE_RHYTHM

    def test_ornament_remove(self) -> None:
        # Create a motif with short notes
        intervals = (0, 1, 2, 3, 4)
        rhythm = (1.0, 0.25, 0.25, 1.0, 1.0)
        iv, rh = _apply_motif_transform(intervals, rhythm, MotifTransform.ORNAMENT_REMOVE)
        # Short notes should be merged
        assert len(iv) <= len(intervals)
        assert len(iv) == len(rh)

    def test_rhythm_displace(self) -> None:
        rng = random.Random(42)
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.RHYTHM_DISPLACE, rng)
        # Pitches preserved, rhythm changed, total duration preserved
        assert iv == SAMPLE_INTERVALS
        assert abs(sum(rh) - sum(SAMPLE_RHYTHM)) < 0.01

    def test_interval_fill(self) -> None:
        # Motif with a large leap
        intervals = (0, 7, 12, 5)
        rhythm = (1.0, 1.0, 1.0, 1.0)
        iv, rh = _apply_motif_transform(intervals, rhythm, MotifTransform.INTERVAL_FILL)
        # Should add passing tones for leaps >= 4
        assert len(iv) > len(intervals)
        assert len(iv) == len(rh)

    def test_interval_leap(self) -> None:
        # Motif with stepwise motion
        intervals = (0, 1, 2, 3, 4, 5)
        rhythm = (0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        iv, rh = _apply_motif_transform(intervals, rhythm, MotifTransform.INTERVAL_LEAP)
        # Should collapse some steps into leaps
        assert len(iv) <= len(intervals)
        assert len(iv) == len(rh)

    def test_octave_displace_with_rng(self) -> None:
        rng = random.Random(42)
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.OCTAVE_DISPLACE, rng)
        assert len(iv) == len(SAMPLE_INTERVALS)
        assert rh == SAMPLE_RHYTHM
        # At least one note should be displaced by 12
        diffs = [abs(a - b) for a, b in zip(iv, SAMPLE_INTERVALS, strict=False)]
        assert any(d == 12 for d in diffs)

    def test_expand(self) -> None:
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.EXPAND)
        assert len(iv) > len(SAMPLE_INTERVALS)
        assert len(iv) == len(rh)

    def test_contract_with_rng(self) -> None:
        rng = random.Random(42)
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.CONTRACT, rng)
        assert len(iv) < len(SAMPLE_INTERVALS)
        assert len(iv) == len(rh)

    def test_fragment_first_half(self) -> None:
        rng = random.Random(0)  # Seed that gives first half
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.FRAGMENT, rng)
        assert len(iv) < len(SAMPLE_INTERVALS)
        assert len(iv) >= 2

    def test_extend_with_rng(self) -> None:
        rng = random.Random(42)
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.EXTEND, rng)
        assert len(iv) == len(SAMPLE_INTERVALS) + 2
        assert len(rh) == len(SAMPLE_RHYTHM) + 2

    def test_question_answer(self) -> None:
        iv, rh = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, MotifTransform.QUESTION_ANSWER)
        assert len(iv) == len(SAMPLE_INTERVALS)
        assert rh == SAMPLE_RHYTHM
        # First half preserved
        half = len(SAMPLE_INTERVALS) // 2
        assert iv[:half] == SAMPLE_INTERVALS[:half]

    def test_question_answer_short_motif(self) -> None:
        short_iv = (0, 2)
        short_rh = (1.0, 1.0)
        iv, rh = _apply_motif_transform(short_iv, short_rh, MotifTransform.QUESTION_ANSWER)
        # Too short, returned unchanged
        assert iv == short_iv


class TestTransformDeterminism:
    """Verify deterministic transforms produce consistent results."""

    @pytest.mark.parametrize(
        "transform",
        [
            MotifTransform.IDENTITY,
            MotifTransform.INVERSION,
            MotifTransform.RETROGRADE,
            MotifTransform.AUGMENTATION,
            MotifTransform.DIMINUTION,
            MotifTransform.INTERVAL_FILL,
            MotifTransform.INTERVAL_LEAP,
            MotifTransform.EXPAND,
            MotifTransform.QUESTION_ANSWER,
        ],
    )
    def test_deterministic_same_result(self, transform: MotifTransform) -> None:
        r1 = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, transform)
        r2 = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, transform)
        assert r1 == r2

    @pytest.mark.parametrize(
        "transform",
        [
            MotifTransform.ORNAMENT_ADD,
            MotifTransform.RHYTHM_DISPLACE,
            MotifTransform.OCTAVE_DISPLACE,
            MotifTransform.CONTRACT,
            MotifTransform.EXTEND,
        ],
    )
    def test_stochastic_same_seed_same_result(self, transform: MotifTransform) -> None:
        r1 = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, transform, random.Random(42))
        r2 = _apply_motif_transform(SAMPLE_INTERVALS, SAMPLE_RHYTHM, transform, random.Random(42))
        assert r1 == r2
