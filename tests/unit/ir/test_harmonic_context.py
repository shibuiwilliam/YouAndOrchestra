"""Tests for HarmonicContext IR type."""

from __future__ import annotations

from yao.ir.harmonic_context import HarmonicContext


class TestHarmonicContext:
    """Tests for HarmonicContext dataclass."""

    def test_creation(self) -> None:
        """HarmonicContext created with required fields."""
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="C")
        assert ctx.chord_root == "C"
        assert ctx.chord_quality == "maj"

    def test_chord_tones_major(self) -> None:
        """Major chord tones are correct (root, 3rd, 5th)."""
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="C", chord_quality="maj")
        tones = ctx.chord_tones
        assert 0 in tones  # root
        assert 4 in tones  # major 3rd
        assert 7 in tones  # perfect 5th

    def test_chord_tones_minor(self) -> None:
        """Minor chord tones are correct (root, b3rd, 5th)."""
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="A", chord_quality="min")
        tones = ctx.chord_tones
        assert 0 in tones  # root
        assert 3 in tones  # minor 3rd
        assert 7 in tones  # perfect 5th

    def test_chord_tone_pitches(self) -> None:
        """Chord tone pitches computed correctly for C4."""
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="C", chord_quality="maj")
        pitches = ctx.chord_tone_pitches(octave=4)
        assert 60 in pitches  # C4
        assert 64 in pitches  # E4
        assert 67 in pitches  # G4

    def test_is_chord_tone(self) -> None:
        """Chord tone detection works across octaves."""
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="C", chord_quality="maj")
        assert ctx.is_chord_tone(60)  # C4
        assert ctx.is_chord_tone(72)  # C5
        assert ctx.is_chord_tone(64)  # E4
        assert not ctx.is_chord_tone(61)  # C#4
        assert not ctx.is_chord_tone(63)  # Eb4

    def test_voice_leading_targets_with_next(self) -> None:
        """Voice leading targets returned when next chord exists."""
        ctx = HarmonicContext(
            bar=0,
            beat=0.0,
            chord_root="C",
            chord_quality="maj",
            next_chord_root="F",
            next_chord_quality="maj",
        )
        targets = ctx.voice_leading_targets(octave=4)
        assert len(targets) > 0
        # F4=65, A4=69, C5=72 are F major tones
        assert 65 in targets

    def test_voice_leading_targets_no_next(self) -> None:
        """Empty targets when no next chord."""
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="C")
        assert ctx.voice_leading_targets() == ()

    def test_dom7_chord_tones(self) -> None:
        """Dominant 7th chord has 4 tones."""
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="G", chord_quality="dom7")
        tones = ctx.chord_tones
        assert 0 in tones  # root
        assert 4 in tones  # major 3rd
        assert 7 in tones  # 5th
        assert 10 in tones  # minor 7th
