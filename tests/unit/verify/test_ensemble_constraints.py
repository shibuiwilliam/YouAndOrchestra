"""Tests for EnsembleConstraint — Wave 3.2.

Tests the inter-part constraint checking: register separation,
downbeat consonance, parallel octaves, frequency collision, bass below melody.
"""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.schema.constraints import ConstraintsSpec, EnsembleConstraint
from yao.verify.constraint_checker import check_constraints


def _make_multi_instrument_score(
    melody_pitches: list[int],
    bass_pitches: list[int],
    harmony_pitches: list[int] | None = None,
) -> ScoreIR:
    """Create a score with multiple instruments."""
    melody_notes = tuple(
        Note(pitch=p, start_beat=float(i * 4), duration_beats=4.0, velocity=80, instrument="violin")
        for i, p in enumerate(melody_pitches)
    )
    bass_notes = tuple(
        Note(pitch=p, start_beat=float(i * 4), duration_beats=4.0, velocity=70, instrument="cello")
        for i, p in enumerate(bass_pitches)
    )
    parts = [
        Part(instrument="violin", notes=melody_notes),
        Part(instrument="cello", notes=bass_notes),
    ]
    if harmony_pitches:
        harmony_notes = tuple(
            Note(pitch=p, start_beat=float(i * 4), duration_beats=4.0, velocity=60, instrument="viola")
            for i, p in enumerate(harmony_pitches)
        )
        parts.append(Part(instrument="viola", notes=harmony_notes))

    return ScoreIR(
        title="Ensemble Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="verse", start_bar=0, end_bar=4, parts=tuple(parts)),),
    )


class TestRegisterSeparation:
    """Tests for register_separation ensemble constraint."""

    def test_detects_close_registers(self) -> None:
        """Two instruments in the same octave should trigger violation."""
        # Both instruments around middle C (60-67)
        score = _make_multi_instrument_score(
            melody_pitches=[60, 62, 64, 65],
            bass_pitches=[55, 57, 59, 60],  # Very close to melody
        )
        constraints = ConstraintsSpec(
            ensemble_constraints=[
                EnsembleConstraint(
                    rule="register_separation",
                    parameters={"min_separation_semitones": 12.0},
                )
            ]
        )
        results = check_constraints(score, constraints)
        assert len(results) >= 1
        assert any("register_separation" in r.rule for r in results)

    def test_passes_with_good_separation(self) -> None:
        """Instruments 2 octaves apart should not trigger."""
        score = _make_multi_instrument_score(
            melody_pitches=[72, 74, 76, 77],  # C5 range
            bass_pitches=[36, 38, 40, 41],  # C2 range
        )
        constraints = ConstraintsSpec(
            ensemble_constraints=[
                EnsembleConstraint(
                    rule="register_separation",
                    parameters={"min_separation_semitones": 12.0},
                )
            ]
        )
        results = check_constraints(score, constraints)
        assert not any("register_separation" in r.rule for r in results)


class TestDownbeatConsonance:
    """Tests for downbeat_consonance ensemble constraint."""

    def test_detects_dissonance_on_downbeat(self) -> None:
        """Bass and melody forming a tritone on downbeat should trigger."""
        score = _make_multi_instrument_score(
            melody_pitches=[66, 64, 62, 60],  # F#4, E4, D4, C4
            bass_pitches=[36, 36, 36, 36],  # C2 — C-F# = tritone on beat 0
        )
        constraints = ConstraintsSpec(ensemble_constraints=[EnsembleConstraint(rule="downbeat_consonance")])
        results = check_constraints(score, constraints)
        assert any("downbeat_consonance" in r.rule for r in results)

    def test_passes_consonant_downbeats(self) -> None:
        """Bass-melody in perfect fifth on downbeats should pass."""
        score = _make_multi_instrument_score(
            melody_pitches=[67, 64, 60, 67],  # G4, E4, C4, G4
            bass_pitches=[36, 36, 36, 36],  # C2 — all consonant with C
        )
        constraints = ConstraintsSpec(ensemble_constraints=[EnsembleConstraint(rule="downbeat_consonance")])
        results = check_constraints(score, constraints)
        assert not any("downbeat_consonance" in r.rule for r in results)


class TestFrequencyCollision:
    """Tests for no_frequency_collision ensemble constraint."""

    def test_detects_overlapping_ranges(self) -> None:
        """Two instruments in the same range should trigger."""
        score = _make_multi_instrument_score(
            melody_pitches=[60, 62, 64, 67],  # C4-G4 (span 7)
            bass_pitches=[59, 61, 63, 66],  # B3-F#4 (span 7, overlap 6/7 > 0.6)
        )
        constraints = ConstraintsSpec(
            ensemble_constraints=[
                EnsembleConstraint(
                    rule="no_frequency_collision",
                    parameters={"max_overlap_ratio": 0.6},
                )
            ]
        )
        results = check_constraints(score, constraints)
        assert any("frequency_collision" in r.rule for r in results)

    def test_passes_separated_ranges(self) -> None:
        """Instruments in different octaves should not trigger."""
        score = _make_multi_instrument_score(
            melody_pitches=[72, 74, 76, 79],  # C5-G5
            bass_pitches=[36, 40, 43, 45],  # C2-A2
        )
        constraints = ConstraintsSpec(
            ensemble_constraints=[
                EnsembleConstraint(
                    rule="no_frequency_collision",
                    parameters={"max_overlap_ratio": 0.6},
                )
            ]
        )
        results = check_constraints(score, constraints)
        assert not any("frequency_collision" in r.rule for r in results)


class TestBassBelowMelody:
    """Tests for bass_below_melody ensemble constraint."""

    def test_detects_bass_above_melody(self) -> None:
        """The lowest-register instrument having notes above the highest should trigger."""
        # violin avg ~75 (high), cello avg ~72 (slightly lower)
        # But cello has some notes that go ABOVE violin's average
        # Actually: the check finds lowest-avg as "bass" and highest-avg as "melody"
        # Then checks if bass notes exceed melody avg
        # Let's create a case where bass (cello, lower avg) has outlier notes above melody avg
        melody_notes = tuple(
            Note(pitch=p, start_beat=float(i * 4), duration_beats=4.0, velocity=80, instrument="violin")
            for i, p in enumerate([60, 62, 60, 62])  # violin avg=61
        )
        bass_notes = tuple(
            Note(pitch=p, start_beat=float(i * 4), duration_beats=4.0, velocity=70, instrument="cello")
            for i, p in enumerate([48, 50, 72, 74])  # cello avg=61 but has notes at 72,74 > violin avg
        )
        score = ScoreIR(
            title="Bass Above",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="verse",
                    start_bar=0,
                    end_bar=4,
                    parts=(
                        Part(instrument="violin", notes=melody_notes),
                        Part(instrument="cello", notes=bass_notes),
                    ),
                ),
            ),
        )
        constraints = ConstraintsSpec(ensemble_constraints=[EnsembleConstraint(rule="bass_below_melody")])
        results = check_constraints(score, constraints)
        assert any("bass_below_melody" in r.rule for r in results)

    def test_passes_correct_bass_position(self) -> None:
        """Bass below melody should not trigger."""
        score = _make_multi_instrument_score(
            melody_pitches=[72, 74, 76, 77],  # C5 area
            bass_pitches=[36, 38, 40, 41],  # C2 area
        )
        constraints = ConstraintsSpec(ensemble_constraints=[EnsembleConstraint(rule="bass_below_melody")])
        results = check_constraints(score, constraints)
        assert not any("bass_below_melody" in r.rule for r in results)


class TestMultipleConstraints:
    """Test combining multiple ensemble constraints."""

    def test_multiple_violations(self) -> None:
        """Score with multiple ensemble problems should report all."""
        # Same register + dissonant downbeats
        score = _make_multi_instrument_score(
            melody_pitches=[66, 64, 62, 60],  # F#-E-D-C (tritone with bass)
            bass_pitches=[60, 62, 64, 65],  # Same register as melody
        )
        constraints = ConstraintsSpec(
            ensemble_constraints=[
                EnsembleConstraint(rule="register_separation", parameters={"min_separation_semitones": 12.0}),
                EnsembleConstraint(rule="downbeat_consonance"),
                EnsembleConstraint(rule="no_frequency_collision", parameters={"max_overlap_ratio": 0.6}),
            ]
        )
        results = check_constraints(score, constraints)
        # Should have violations from multiple rules
        rules_violated = set(r.rule for r in results)
        assert len(rules_violated) >= 2
