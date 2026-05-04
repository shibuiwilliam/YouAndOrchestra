"""Tests for frequency clearance."""

from __future__ import annotations

from yao.generators.frequency_clearance import (
    apply_frequency_clearance,
    frequency_collision,
    midi_to_hz,
    notes_overlap_in_time,
)
from yao.ir.conversation import ConversationPlan
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


class TestMidiToHz:
    def test_a440(self) -> None:
        assert abs(midi_to_hz(69) - 440.0) < 0.01

    def test_middle_c(self) -> None:
        # C4 = MIDI 60 ≈ 261.63 Hz
        assert abs(midi_to_hz(60) - 261.63) < 0.1

    def test_octave_doubles(self) -> None:
        assert abs(midi_to_hz(72) / midi_to_hz(60) - 2.0) < 0.01


class TestNotesOverlap:
    def test_overlapping(self) -> None:
        a = Note(pitch=60, start_beat=0, duration_beats=2, velocity=80, instrument="piano")
        b = Note(pitch=62, start_beat=1, duration_beats=2, velocity=80, instrument="strings")
        assert notes_overlap_in_time(a, b)

    def test_non_overlapping(self) -> None:
        a = Note(pitch=60, start_beat=0, duration_beats=1, velocity=80, instrument="piano")
        b = Note(pitch=62, start_beat=2, duration_beats=1, velocity=80, instrument="strings")
        assert not notes_overlap_in_time(a, b)

    def test_adjacent_no_overlap(self) -> None:
        a = Note(pitch=60, start_beat=0, duration_beats=1, velocity=80, instrument="piano")
        b = Note(pitch=62, start_beat=1, duration_beats=1, velocity=80, instrument="strings")
        assert not notes_overlap_in_time(a, b)


class TestFrequencyCollision:
    def test_same_pitch_overlapping(self) -> None:
        primary = Note(pitch=60, start_beat=0, duration_beats=2, velocity=80, instrument="piano")
        acc = Note(pitch=61, start_beat=0, duration_beats=2, velocity=60, instrument="strings")
        assert frequency_collision(primary, acc, bandwidth_semitones=3)

    def test_far_apart_no_collision(self) -> None:
        primary = Note(pitch=60, start_beat=0, duration_beats=2, velocity=80, instrument="piano")
        acc = Note(pitch=80, start_beat=0, duration_beats=2, velocity=60, instrument="strings")
        assert not frequency_collision(primary, acc, bandwidth_semitones=3)

    def test_no_time_overlap_no_collision(self) -> None:
        primary = Note(pitch=60, start_beat=0, duration_beats=1, velocity=80, instrument="piano")
        acc = Note(pitch=61, start_beat=2, duration_beats=1, velocity=60, instrument="strings")
        assert not frequency_collision(primary, acc, bandwidth_semitones=3)


class TestApplyFrequencyClearance:
    def _make_colliding_score(self) -> ScoreIR:
        """Score where accompaniment collides with primary voice."""
        return ScoreIR(
            title="test",
            tempo_bpm=120,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="verse",
                    start_bar=0,
                    end_bar=4,
                    parts=(
                        Part(
                            instrument="piano",
                            notes=(
                                Note(pitch=60, start_beat=0, duration_beats=4, velocity=80, instrument="piano"),
                                Note(pitch=62, start_beat=4, duration_beats=4, velocity=80, instrument="piano"),
                            ),
                        ),
                        Part(
                            instrument="strings",
                            notes=(
                                # These collide with piano (within 3 semitones)
                                Note(pitch=61, start_beat=0, duration_beats=4, velocity=60, instrument="strings"),
                                Note(pitch=63, start_beat=4, duration_beats=4, velocity=60, instrument="strings"),
                            ),
                        ),
                    ),
                ),
            ),
        )

    def _make_conversation(self) -> ConversationPlan:
        return ConversationPlan(
            primary_voice_per_section={"verse": "piano"},
            accompaniment_role_per_section={"verse": ("strings",)},
        )

    def test_resolves_collisions(self) -> None:
        score = self._make_colliding_score()
        conversation = self._make_conversation()
        result, prov = apply_frequency_clearance(score, conversation)

        # Strings notes should be displaced
        for section in result.sections:
            for part in section.parts:
                if part.instrument == "strings":
                    for note in part.notes:
                        # Should be displaced by an octave (±12)
                        assert note.pitch != 61 and note.pitch != 63

    def test_never_silences(self) -> None:
        """Frequency clearance never removes notes."""
        score = self._make_colliding_score()
        conversation = self._make_conversation()
        result, _ = apply_frequency_clearance(score, conversation)

        orig_count = sum(len(p.notes) for s in score.sections for p in s.parts)
        new_count = sum(len(p.notes) for s in result.sections for p in s.parts)
        assert new_count == orig_count

    def test_primary_voice_unchanged(self) -> None:
        """Primary voice notes are never modified."""
        score = self._make_colliding_score()
        conversation = self._make_conversation()
        result, _ = apply_frequency_clearance(score, conversation)

        for section in result.sections:
            for part in section.parts:
                if part.instrument == "piano":
                    # Piano notes unchanged
                    assert part.notes[0].pitch == 60
                    assert part.notes[1].pitch == 62

    def test_provenance_recorded(self) -> None:
        score = self._make_colliding_score()
        conversation = self._make_conversation()
        _, prov = apply_frequency_clearance(score, conversation)
        assert len(prov.records) >= 1
        assert any("frequency_clearance" in r.operation for r in prov.records)

    def test_no_change_without_collisions(self) -> None:
        """When no collisions exist, output equals input."""
        score = ScoreIR(
            title="test",
            tempo_bpm=120,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="verse",
                    start_bar=0,
                    end_bar=4,
                    parts=(
                        Part(
                            instrument="piano",
                            notes=(Note(pitch=60, start_beat=0, duration_beats=4, velocity=80, instrument="piano"),),
                        ),
                        Part(
                            instrument="strings",
                            notes=(
                                # Far from piano — no collision
                                Note(pitch=84, start_beat=0, duration_beats=4, velocity=60, instrument="strings"),
                            ),
                        ),
                    ),
                ),
            ),
        )
        conversation = self._make_conversation()
        result, _ = apply_frequency_clearance(score, conversation)
        # Strings note unchanged
        for section in result.sections:
            for part in section.parts:
                if part.instrument == "strings":
                    assert part.notes[0].pitch == 84
