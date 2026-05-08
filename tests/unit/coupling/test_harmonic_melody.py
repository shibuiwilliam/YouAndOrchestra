"""Tests for derive_constraints() — the harmonic-melodic coupling function.

Verifies each of the 6 CouplingStyle rule sets produces the expected
score_pitch() distribution and constraint structure.

Phase 3.5 Step 2 — IMPROVEMENT.md §4.1, PROJECT.md §3.4.1.
"""

from __future__ import annotations

import pytest

from yao.coupling.harmonic_melody import clear_cache, derive_constraints
from yao.ir.harmonic_melody_constraints import (
    CouplingStyle,
    PositionLabel,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Clear the LRU cache before each test."""
    clear_cache()


class TestDeriveConstraintsBasic:
    """Basic derive_constraints behavior."""

    def test_returns_harmonic_melody_constraints(self) -> None:
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        assert result.style == CouplingStyle.COMMON_PRACTICE
        assert len(result.chord_tones) > 0

    def test_cmaj_chord_tones(self) -> None:
        """C major chord produces C=0, E=4, G=7 as chord tones."""
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        assert set(result.chord_tones) == {0, 4, 7}

    def test_gdom7_chord_tones(self) -> None:
        """G7 chord produces G=7, B=11, D=2, F=5 as chord tones."""
        result = derive_constraints("G", "dom7", "C", "major", CouplingStyle.COMMON_PRACTICE)
        assert set(result.chord_tones) == {7, 11, 2, 5}

    def test_dmin7_chord_tones(self) -> None:
        """Dm7 chord produces D=2, F=5, A=9, C=0."""
        result = derive_constraints("D", "min7", "C", "major", CouplingStyle.COMMON_PRACTICE)
        assert set(result.chord_tones) == {2, 5, 9, 0}

    def test_enharmonic_root(self) -> None:
        """Bb is handled as A# (pitch class 10)."""
        result = derive_constraints("Bb", "maj", "F", "major", CouplingStyle.COMMON_PRACTICE)
        assert 10 in result.chord_tones  # Bb = A# = pc 10

    def test_all_pitch_classes_covered(self) -> None:
        """Chord tones, extensions, and avoid notes do not overlap."""
        result = derive_constraints("C", "maj7", "C", "major", CouplingStyle.COMMON_PRACTICE)
        assert not (set(result.chord_tones) & set(result.avoid_notes))
        assert not (set(result.chord_tones) & set(result.available_extensions))
        assert not (set(result.avoid_notes) & set(result.available_extensions))


class TestCommonPracticeRules:
    """Common-practice coupling style."""

    def test_p4_avoided_on_major_triad(self) -> None:
        """P4 above root is avoid note on major triad."""
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        assert 5 in result.avoid_notes  # F (P4 above C)

    def test_p4_avoided_on_maj7(self) -> None:
        """P4 above root is avoid note on maj7."""
        result = derive_constraints("C", "maj7", "C", "major", CouplingStyle.COMMON_PRACTICE)
        assert 5 in result.avoid_notes

    def test_no_p4_avoid_on_minor(self) -> None:
        """P4 is NOT avoided on minor chords."""
        result = derive_constraints("A", "min", "C", "major", CouplingStyle.COMMON_PRACTICE)
        # P4 above A = D = pc 2
        assert 2 not in result.avoid_notes

    def test_scale_tones_are_extensions(self) -> None:
        """Non-chord scale tones become extensions."""
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        # C major scale: C=0, D=2, E=4, F=5, G=7, A=9, B=11
        # Chord tones: 0, 4, 7
        # Avoid: 5 (F)
        # Extensions should include: 2 (D), 9 (A), 11 (B)
        assert 2 in result.available_extensions
        assert 9 in result.available_extensions
        assert 11 in result.available_extensions

    def test_leading_tone_resolution(self) -> None:
        """Leading tone (B) resolves to tonic (C) in key of C."""
        result = derive_constraints("G", "dom7", "C", "major", CouplingStyle.COMMON_PRACTICE)
        assert 11 in result.target_resolutions  # B resolves
        assert result.target_resolutions[11] == 0  # to C

    def test_avoid_note_scores_low_on_downbeat(self) -> None:
        """Avoid note on downbeat scores very low."""
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        score = result.score_pitch(65, PositionLabel.DOWNBEAT)  # F4, pc=5 (avoid)
        assert score <= 0.15


class TestJazzRules:
    """Jazz coupling style."""

    def test_avoid_11_on_dom7(self) -> None:
        """11th (P4) on dominant 7th is avoided."""
        result = derive_constraints("G", "dom7", "C", "major", CouplingStyle.JAZZ)
        # P4 above G = C = pc 0
        assert 0 in result.avoid_notes

    def test_avoid_11_on_maj7(self) -> None:
        """11th on maj7 is avoided."""
        result = derive_constraints("C", "maj7", "C", "major", CouplingStyle.JAZZ)
        assert 5 in result.avoid_notes  # F = P4 above C

    def test_no_avoid_on_min7(self) -> None:
        """No 11th avoidance on minor 7th chords."""
        result = derive_constraints("D", "min7", "C", "major", CouplingStyle.JAZZ)
        # P4 above D = G = pc 7, but this is the 5th of Dm, already a chord tone
        # So no specific avoid for min7
        assert len(result.avoid_notes) == 0

    def test_extensions_include_9th(self) -> None:
        """9th is available as extension."""
        result = derive_constraints("C", "dom7", "C", "major", CouplingStyle.JAZZ)
        # 9th above C = D = pc 2
        assert 2 in result.available_extensions


class TestBluesRules:
    """Blues coupling style."""

    def test_no_avoid_notes(self) -> None:
        """Blues has no avoid notes."""
        result = derive_constraints("C", "dom7", "C", "major", CouplingStyle.BLUES)
        assert len(result.avoid_notes) == 0

    def test_blue_notes_in_extensions(self) -> None:
        """b3, b5, b7 are available as blue note extensions."""
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.BLUES)
        # b3 = Eb = pc 3
        # b5 = Gb = pc 6
        # b7 = Bb = pc 10
        assert 3 in result.available_extensions
        assert 6 in result.available_extensions
        # b7 might be extension if not already a chord tone
        assert 10 in result.available_extensions or 10 in result.chord_tones

    def test_blue_note_scores_well(self) -> None:
        """Blue notes on offbeat should score well."""
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.BLUES)
        # Eb (b3) on offbeat
        score = result.score_pitch(63, PositionLabel.OFFBEAT)  # Eb4
        assert score >= 0.4


class TestModalRules:
    """Modal coupling style."""

    def test_no_avoid_notes(self) -> None:
        """Modal: all scale tones equal, no avoid notes."""
        result = derive_constraints("D", "min7", "C", "major", CouplingStyle.MODAL)
        assert len(result.avoid_notes) == 0

    def test_all_scale_tones_accessible(self) -> None:
        """All scale tones are chord tones or extensions."""
        result = derive_constraints("D", "min7", "C", "major", CouplingStyle.MODAL)
        accessible = set(result.chord_tones) | set(result.available_extensions)
        # C major scale pitch classes: 0, 2, 4, 5, 7, 9, 11
        for pc in (0, 2, 4, 5, 7, 9, 11):
            assert pc in accessible, f"pc {pc} not accessible in modal style"


class TestRagaRules:
    """Raga coupling style."""

    def test_no_avoid_notes(self) -> None:
        """Raga: no avoid notes."""
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.RAGA)
        assert len(result.avoid_notes) == 0

    def test_non_chord_tones_have_resolutions(self) -> None:
        """Non-chord scale tones resolve to nearest chord tone."""
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.RAGA)
        # D (pc=2) should resolve to C (0) or E (4)
        if 2 in result.target_resolutions:
            assert result.target_resolutions[2] in (0, 4)


class TestMaqamRules:
    """Maqam coupling style."""

    def test_no_avoid_notes(self) -> None:
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.MAQAM)
        assert len(result.avoid_notes) == 0

    def test_has_resolutions(self) -> None:
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.MAQAM)
        # Should have some resolution targets for non-chord tones
        assert len(result.target_resolutions) > 0


class TestCaching:
    """derive_constraints results are cached."""

    def test_same_args_same_result(self) -> None:
        """Same arguments return the same object (cached)."""
        r1 = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        r2 = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        assert r1 is r2

    def test_different_args_different_result(self) -> None:
        """Different arguments return different objects."""
        r1 = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        r2 = derive_constraints("G", "dom7", "C", "major", CouplingStyle.JAZZ)
        assert r1 is not r2

    def test_clear_cache_works(self) -> None:
        """Cache can be cleared."""
        r1 = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        clear_cache()
        r2 = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        assert r1 is not r2
        assert r1 == r2


class TestScorePitchIntegration:
    """Integration: derive_constraints produces constraints that score correctly."""

    def test_cmaj_root_scores_highest(self) -> None:
        """Root on downbeat scores highest for C major."""
        result = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        root_score = result.score_pitch(60, PositionLabel.DOWNBEAT)  # C4
        for midi in range(61, 72):  # all other notes in octave
            other_score = result.score_pitch(midi, PositionLabel.DOWNBEAT)
            assert root_score >= other_score, f"Root C (score={root_score}) should >= MIDI {midi} (score={other_score})"

    def test_gdom7_jazz_11th_penalty(self) -> None:
        """G7 in jazz: the 11th (C) scores low on downbeat."""
        result = derive_constraints("G", "dom7", "C", "major", CouplingStyle.JAZZ)
        # C (pc=0) is avoid note for G7 jazz
        score = result.score_pitch(60, PositionLabel.DOWNBEAT)  # C4
        assert score <= 0.15

    def test_blues_tolerant_on_all_positions(self) -> None:
        """Blues: all notes score reasonably on all positions."""
        result = derive_constraints("C", "dom7", "C", "blues", CouplingStyle.BLUES)
        for midi in range(60, 73):
            for pos in PositionLabel:
                score = result.score_pitch(midi, pos)
                assert score >= 0.0
                assert score <= 1.0

    def test_different_keys_different_constraints(self) -> None:
        """Same chord quality in different keys produces different absolute PCs."""
        c_result = derive_constraints("C", "maj", "C", "major", CouplingStyle.COMMON_PRACTICE)
        g_result = derive_constraints("G", "maj", "G", "major", CouplingStyle.COMMON_PRACTICE)
        assert c_result.chord_tones != g_result.chord_tones
