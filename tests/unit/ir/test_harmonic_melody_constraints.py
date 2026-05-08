"""Tests for HarmonicMelodyConstraints IR type.

Covers all 6 CouplingStyles, all 4 PositionLabels, and edge cases
for score_pitch() behavior.

Phase 3.5 Step 1 — IMPROVEMENT.md §4.1, PROJECT.md §3.4.1.
"""

from __future__ import annotations

import pytest

from yao.ir.harmonic_melody_constraints import (
    CouplingStyle,
    HarmonicMelodyConstraints,
    PositionLabel,
)


class TestCouplingStyle:
    """CouplingStyle enum has all 6 required values."""

    def test_all_styles_exist(self) -> None:
        assert len(CouplingStyle) == 6
        assert CouplingStyle.COMMON_PRACTICE == "common_practice"
        assert CouplingStyle.JAZZ == "jazz"
        assert CouplingStyle.BLUES == "blues"
        assert CouplingStyle.MODAL == "modal"
        assert CouplingStyle.RAGA == "raga"
        assert CouplingStyle.MAQAM == "maqam"

    def test_styles_are_strings(self) -> None:
        for style in CouplingStyle:
            assert isinstance(style.value, str)


class TestPositionLabel:
    """PositionLabel enum has all 4 required values."""

    def test_all_positions_exist(self) -> None:
        assert len(PositionLabel) == 4
        assert PositionLabel.DOWNBEAT == "downbeat"
        assert PositionLabel.UPBEAT == "upbeat"
        assert PositionLabel.OFFBEAT == "offbeat"
        assert PositionLabel.APPROACH == "approach"


class TestHarmonicMelodyConstraintsCreation:
    """HarmonicMelodyConstraints dataclass creation and immutability."""

    def test_creation_with_all_fields(self) -> None:
        constraints = HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(2, 9, 11),
            avoid_notes=(5,),
            target_resolutions={11: 0, 4: 5},
            style=CouplingStyle.COMMON_PRACTICE,
        )
        assert constraints.chord_tones == (0, 4, 7)
        assert constraints.available_extensions == (2, 9, 11)
        assert constraints.avoid_notes == (5,)
        assert constraints.target_resolutions == {11: 0, 4: 5}
        assert constraints.style == CouplingStyle.COMMON_PRACTICE

    def test_frozen_immutable(self) -> None:
        constraints = HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(),
            avoid_notes=(),
            target_resolutions={},
            style=CouplingStyle.JAZZ,
        )
        with pytest.raises(AttributeError):
            constraints.chord_tones = (0, 3, 7)  # type: ignore[misc]

    def test_empty_extensions_and_avoid(self) -> None:
        constraints = HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(),
            avoid_notes=(),
            target_resolutions={},
            style=CouplingStyle.MODAL,
        )
        assert constraints.available_extensions == ()
        assert constraints.avoid_notes == ()


class TestScorePitchReturnRange:
    """score_pitch() always returns values in [0.0, 1.0]."""

    @pytest.fixture()
    def cmaj_common(self) -> HarmonicMelodyConstraints:
        """C major triad, common practice style."""
        return HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(2, 9, 11),
            avoid_notes=(5,),
            target_resolutions={11: 0},
            style=CouplingStyle.COMMON_PRACTICE,
        )

    def test_score_always_in_range(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """All pitches and positions produce scores in [0.0, 1.0]."""
        for midi_pitch in range(36, 97):
            for pos in PositionLabel:
                score = cmaj_common.score_pitch(midi_pitch, pos)
                assert 0.0 <= score <= 1.0, f"score_pitch({midi_pitch}, {pos}) = {score}, expected [0.0, 1.0]"

    def test_score_pitch_returns_float(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        score = cmaj_common.score_pitch(60, PositionLabel.DOWNBEAT)
        assert isinstance(score, float)


class TestScorePitchChordTones:
    """Chord tones should score highly, especially on strong beats."""

    @pytest.fixture()
    def cmaj_common(self) -> HarmonicMelodyConstraints:
        return HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(2, 9, 11),
            avoid_notes=(5,),
            target_resolutions={11: 0},
            style=CouplingStyle.COMMON_PRACTICE,
        )

    def test_chord_tone_on_downbeat_scores_high(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """Root (C4=60) on downbeat should score very high."""
        score = cmaj_common.score_pitch(60, PositionLabel.DOWNBEAT)
        assert score >= 0.85

    def test_chord_tone_on_upbeat_scores_high(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """Chord tone on upbeat still scores well."""
        score = cmaj_common.score_pitch(64, PositionLabel.UPBEAT)  # E4
        assert score >= 0.7

    def test_chord_tone_any_octave(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """Chord tones in different octaves score the same."""
        score_c4 = cmaj_common.score_pitch(60, PositionLabel.DOWNBEAT)
        score_c5 = cmaj_common.score_pitch(72, PositionLabel.DOWNBEAT)
        assert score_c4 == score_c5

    def test_fifth_on_downbeat_scores_high(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """G (fifth) on downbeat scores high."""
        score = cmaj_common.score_pitch(67, PositionLabel.DOWNBEAT)  # G4
        assert score >= 0.85


class TestScorePitchExtensions:
    """Available extensions score mid-range."""

    @pytest.fixture()
    def cmaj7_jazz(self) -> HarmonicMelodyConstraints:
        """Cmaj7 chord, jazz style with extensions."""
        return HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7, 11),
            available_extensions=(2, 9),  # 9th, 13th
            avoid_notes=(5,),  # P4 (avoid 11 on major)
            target_resolutions={11: 0},
            style=CouplingStyle.JAZZ,
        )

    def test_extension_on_downbeat_lower_than_chord_tone(self, cmaj7_jazz: HarmonicMelodyConstraints) -> None:
        """Extensions on downbeat score lower than chord tones."""
        chord_tone_score = cmaj7_jazz.score_pitch(60, PositionLabel.DOWNBEAT)  # C
        extension_score = cmaj7_jazz.score_pitch(62, PositionLabel.DOWNBEAT)  # D (9th)
        assert chord_tone_score > extension_score

    def test_extension_on_offbeat_acceptable(self, cmaj7_jazz: HarmonicMelodyConstraints) -> None:
        """Extensions on offbeats score reasonably well."""
        score = cmaj7_jazz.score_pitch(62, PositionLabel.OFFBEAT)  # D (9th)
        assert score >= 0.4

    def test_extension_better_than_avoid_on_downbeat(self, cmaj7_jazz: HarmonicMelodyConstraints) -> None:
        """Extension scores higher than avoid note on downbeat."""
        ext_score = cmaj7_jazz.score_pitch(62, PositionLabel.DOWNBEAT)  # D (9th)
        avoid_score = cmaj7_jazz.score_pitch(65, PositionLabel.DOWNBEAT)  # F (P4/avoid)
        assert ext_score > avoid_score


class TestScorePitchAvoidNotes:
    """Avoid notes score low on strong beats."""

    @pytest.fixture()
    def cmaj_common(self) -> HarmonicMelodyConstraints:
        return HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(2, 9, 11),
            avoid_notes=(5,),
            target_resolutions={11: 0},
            style=CouplingStyle.COMMON_PRACTICE,
        )

    def test_avoid_note_on_downbeat_scores_very_low(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """Avoid note (P4=F) on downbeat near zero."""
        score = cmaj_common.score_pitch(65, PositionLabel.DOWNBEAT)  # F4
        assert score <= 0.15

    def test_avoid_note_on_offbeat_tolerated(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """Avoid notes are slightly more tolerated on weak beats."""
        score_downbeat = cmaj_common.score_pitch(65, PositionLabel.DOWNBEAT)
        score_offbeat = cmaj_common.score_pitch(65, PositionLabel.OFFBEAT)
        assert score_offbeat > score_downbeat

    def test_avoid_note_on_approach_more_tolerated(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """Avoid notes as approach tones are more tolerated than on downbeats."""
        score_downbeat = cmaj_common.score_pitch(65, PositionLabel.DOWNBEAT)
        score_approach = cmaj_common.score_pitch(65, PositionLabel.APPROACH)
        assert score_approach > score_downbeat


class TestScorePitchNonChordNonAvoid:
    """Notes that are neither chord tones, extensions, nor avoid notes."""

    @pytest.fixture()
    def cmaj_common(self) -> HarmonicMelodyConstraints:
        return HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(2, 9),
            avoid_notes=(5,),
            target_resolutions={},
            style=CouplingStyle.COMMON_PRACTICE,
        )

    def test_passing_tone_scores_moderate(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """A passing tone (not chord, not avoid) scores moderate."""
        # A (pitch class 9) is available extension, already covered
        # Bb (pitch class 10) is none of the categories
        score = cmaj_common.score_pitch(70, PositionLabel.OFFBEAT)  # Bb4, pc=10
        assert 0.1 < score < 0.7

    def test_passing_tone_on_downbeat_lower_than_chord_tone(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """Passing tones on downbeats score lower than chord tones."""
        chord_score = cmaj_common.score_pitch(60, PositionLabel.DOWNBEAT)
        pass_score = cmaj_common.score_pitch(61, PositionLabel.DOWNBEAT)  # C#, pc=1
        assert chord_score > pass_score


class TestScorePitchTargetResolutions:
    """Target resolutions affect scoring on approach positions."""

    def test_resolution_target_on_approach_scores_well(self) -> None:
        """When approaching a resolution, the target pitch scores well."""
        constraints = HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(2,),
            avoid_notes=(),
            target_resolutions={11: 0},  # B resolves to C
            style=CouplingStyle.COMMON_PRACTICE,
        )
        # The leading tone (B, pc=11) on approach should get a bonus
        score = constraints.score_pitch(71, PositionLabel.APPROACH)  # B4
        assert score >= 0.5


class TestScorePitchBluesStyle:
    """Blues style: blue notes (b3, b5, b7) are neutral, not avoid."""

    @pytest.fixture()
    def c7_blues(self) -> HarmonicMelodyConstraints:
        """C7 chord, blues style — blue notes are chord tones."""
        return HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7, 10),  # C E G Bb
            available_extensions=(3, 6),  # b3 and b5 are blue notes
            avoid_notes=(),  # Blues: no avoid notes
            target_resolutions={},
            style=CouplingStyle.BLUES,
        )

    def test_blue_note_b3_not_penalized(self, c7_blues: HarmonicMelodyConstraints) -> None:
        """b3 (Eb, pc=3) is an extension in blues, not penalized."""
        score = c7_blues.score_pitch(63, PositionLabel.DOWNBEAT)  # Eb4
        assert score >= 0.4

    def test_blue_note_b5_not_penalized(self, c7_blues: HarmonicMelodyConstraints) -> None:
        """b5 (Gb, pc=6) is an extension in blues, not penalized."""
        score = c7_blues.score_pitch(66, PositionLabel.OFFBEAT)  # Gb4
        assert score >= 0.4


class TestScorePitchModalStyle:
    """Modal style: all scale tones equal, no avoid notes."""

    @pytest.fixture()
    def d_dorian_modal(self) -> HarmonicMelodyConstraints:
        """Dm7 chord, modal style — no avoid notes. Absolute PCs: D=2, F=5, A=9, C=0."""
        return HarmonicMelodyConstraints(
            chord_tones=(2, 5, 9, 0),  # D, F, A, C
            available_extensions=(4, 7, 11),  # E, G, B (other D dorian scale tones)
            avoid_notes=(),  # Modal: no avoid notes
            target_resolutions={},
            style=CouplingStyle.MODAL,
        )

    def test_modal_no_avoid_penalty(self, d_dorian_modal: HarmonicMelodyConstraints) -> None:
        """In modal style, all scale tones should score reasonably."""
        # D dorian absolute pitch classes: D=2, E=4, F=5, G=7, A=9, B=11, C=0
        # Test with absolute MIDI notes
        test_notes = [62, 64, 65, 67, 69, 71, 72]  # D4, E4, F4, G4, A4, B4, C5
        for midi in test_notes:
            score = d_dorian_modal.score_pitch(midi, PositionLabel.DOWNBEAT)
            assert score >= 0.3, f"MIDI {midi} (pc={midi % 12}) scored {score}, expected >= 0.3"


class TestScorePitchJazzStyle:
    """Jazz style: extensions favored, 11 on V7 penalized."""

    @pytest.fixture()
    def g7_jazz(self) -> HarmonicMelodyConstraints:
        """G7 chord, jazz style. Absolute pitch classes: G=7, B=11, D=2, F=5."""
        return HarmonicMelodyConstraints(
            chord_tones=(7, 11, 2, 5),  # G, B, D, F
            available_extensions=(9, 4),  # A (9th), E (13th)
            avoid_notes=(0,),  # C (11th on dominant — clashes with B)
            target_resolutions={5: 4, 11: 0},  # F→E (b7→6), B→C (3→root of I)
            style=CouplingStyle.JAZZ,
        )

    def test_avoid_11_on_dominant_downbeat(self, g7_jazz: HarmonicMelodyConstraints) -> None:
        """11th (C over G7) penalized on downbeat in jazz."""
        # C5=72, absolute pc=0, which is in avoid_notes
        score = g7_jazz.score_pitch(72, PositionLabel.DOWNBEAT)
        assert score <= 0.2

    def test_extensions_welcome_on_offbeat(self, g7_jazz: HarmonicMelodyConstraints) -> None:
        """9th (A) on offbeat scores well in jazz."""
        # A4=69, absolute pc=9, which is in available_extensions
        score = g7_jazz.score_pitch(69, PositionLabel.OFFBEAT)
        assert score >= 0.4


class TestScorePitchRagaStyle:
    """Raga style: uses target_resolutions for characteristic phrases."""

    def test_raga_characteristic_pitch_on_approach(self) -> None:
        constraints = HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(2, 6, 9, 11),
            avoid_notes=(),
            target_resolutions={6: 7},  # tivra Ma resolves to Pa
            style=CouplingStyle.RAGA,
        )
        score = constraints.score_pitch(66, PositionLabel.APPROACH)  # F#4, pc=6
        assert score >= 0.4


class TestScorePitchMaqamStyle:
    """Maqam style: pitch hierarchy from tonal system."""

    def test_maqam_creation(self) -> None:
        constraints = HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(2, 5, 9, 11),
            avoid_notes=(),
            target_resolutions={},
            style=CouplingStyle.MAQAM,
        )
        assert constraints.style == CouplingStyle.MAQAM


class TestScorePitchPositionDifference:
    """Position affects scoring — strong beats are stricter."""

    @pytest.fixture()
    def cmaj_common(self) -> HarmonicMelodyConstraints:
        return HarmonicMelodyConstraints(
            chord_tones=(0, 4, 7),
            available_extensions=(2, 9, 11),
            avoid_notes=(5,),
            target_resolutions={},
            style=CouplingStyle.COMMON_PRACTICE,
        )

    def test_downbeat_stricter_than_offbeat_for_non_chord_tone(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """Non-chord-tone on downbeat scores lower than on offbeat."""
        score_down = cmaj_common.score_pitch(61, PositionLabel.DOWNBEAT)  # C#, pc=1
        score_off = cmaj_common.score_pitch(61, PositionLabel.OFFBEAT)
        assert score_off >= score_down

    def test_chord_tone_high_regardless_of_position(self, cmaj_common: HarmonicMelodyConstraints) -> None:
        """Chord tones score well on all positions."""
        for pos in PositionLabel:
            score = cmaj_common.score_pitch(60, pos)  # C4 root
            assert score >= 0.7, f"Chord tone on {pos} scored {score}"
