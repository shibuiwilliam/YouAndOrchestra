"""Tests for Note IR v2.0 performance fields in MIDI rendering."""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.render.midi_writer import score_ir_to_midi


def _make_score(notes: tuple[Note, ...], tempo: float = 120.0) -> ScoreIR:
    """Build a minimal ScoreIR from a tuple of notes."""
    part = Part(instrument="piano", notes=notes)
    section = Section(name="test", start_bar=0, end_bar=1, parts=(part,))
    return ScoreIR(
        title="Test",
        tempo_bpm=tempo,
        time_signature="4/4",
        key="C major",
        sections=(section,),
    )


class TestDefaultNoteRendering:
    """Default Note fields produce identical output to pre-v2.0 behavior."""

    def test_default_note_renders(self) -> None:
        note = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        score = _make_score((note,))
        midi = score_ir_to_midi(score)
        assert len(midi.instruments) == 1
        assert len(midi.instruments[0].notes) == 1
        mn = midi.instruments[0].notes[0]
        assert mn.pitch == 60
        assert mn.velocity == 80

    def test_no_pitch_bends_by_default(self) -> None:
        note = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        score = _make_score((note,))
        midi = score_ir_to_midi(score)
        assert len(midi.instruments[0].pitch_bends) == 0


class TestArticulationRendering:
    """Articulation field affects MIDI note duration."""

    def test_staccato_shortens_duration(self) -> None:
        normal = Note(pitch=60, start_beat=0.0, duration_beats=2.0, velocity=80, instrument="piano")
        staccato = Note(
            pitch=60,
            start_beat=0.0,
            duration_beats=2.0,
            velocity=80,
            instrument="piano",
            articulation="staccato",
        )
        score_normal = _make_score((normal,))
        score_staccato = _make_score((staccato,))
        midi_normal = score_ir_to_midi(score_normal)
        midi_staccato = score_ir_to_midi(score_staccato)
        dur_normal = midi_normal.instruments[0].notes[0].end - midi_normal.instruments[0].notes[0].start
        dur_staccato = midi_staccato.instruments[0].notes[0].end - midi_staccato.instruments[0].notes[0].start
        assert dur_staccato < dur_normal
        assert abs(dur_staccato - dur_normal * 0.5) < 0.01

    def test_legato_extends_duration(self) -> None:
        normal = Note(pitch=60, start_beat=0.0, duration_beats=2.0, velocity=80, instrument="piano")
        legato = Note(
            pitch=60,
            start_beat=0.0,
            duration_beats=2.0,
            velocity=80,
            instrument="piano",
            articulation="legato",
        )
        score_normal = _make_score((normal,))
        score_legato = _make_score((legato,))
        midi_normal = score_ir_to_midi(score_normal)
        midi_legato = score_ir_to_midi(score_legato)
        dur_normal = midi_normal.instruments[0].notes[0].end - midi_normal.instruments[0].notes[0].start
        dur_legato = midi_legato.instruments[0].notes[0].end - midi_legato.instruments[0].notes[0].start
        assert dur_legato > dur_normal

    def test_unknown_articulation_no_change(self) -> None:
        normal = Note(pitch=60, start_beat=0.0, duration_beats=2.0, velocity=80, instrument="piano")
        tenuto = Note(
            pitch=60,
            start_beat=0.0,
            duration_beats=2.0,
            velocity=80,
            instrument="piano",
            articulation="tenuto",
        )
        score_normal = _make_score((normal,))
        score_tenuto = _make_score((tenuto,))
        midi_normal = score_ir_to_midi(score_normal)
        midi_tenuto = score_ir_to_midi(score_tenuto)
        dur_normal = midi_normal.instruments[0].notes[0].end - midi_normal.instruments[0].notes[0].start
        dur_tenuto = midi_tenuto.instruments[0].notes[0].end - midi_tenuto.instruments[0].notes[0].start
        assert abs(dur_normal - dur_tenuto) < 0.001


class TestTuningOffsetRendering:
    """tuning_offset_cents produces MIDI pitch bend events."""

    def test_positive_offset_produces_bend(self) -> None:
        note = Note(
            pitch=60,
            start_beat=0.0,
            duration_beats=1.0,
            velocity=80,
            instrument="piano",
            tuning_offset_cents=50.0,
        )
        score = _make_score((note,))
        midi = score_ir_to_midi(score)
        bends = midi.instruments[0].pitch_bends
        assert len(bends) >= 1
        # Positive offset -> positive pitch bend
        assert bends[0].pitch > 0

    def test_negative_offset_produces_negative_bend(self) -> None:
        note = Note(
            pitch=60,
            start_beat=0.0,
            duration_beats=1.0,
            velocity=80,
            instrument="piano",
            tuning_offset_cents=-50.0,
        )
        score = _make_score((note,))
        midi = score_ir_to_midi(score)
        bends = midi.instruments[0].pitch_bends
        assert len(bends) >= 1
        assert bends[0].pitch < 0

    def test_zero_offset_no_bend(self) -> None:
        note = Note(
            pitch=60,
            start_beat=0.0,
            duration_beats=1.0,
            velocity=80,
            instrument="piano",
            tuning_offset_cents=0.0,
        )
        score = _make_score((note,))
        midi = score_ir_to_midi(score)
        assert len(midi.instruments[0].pitch_bends) == 0

    def test_bend_resets_after_note(self) -> None:
        note = Note(
            pitch=60,
            start_beat=0.0,
            duration_beats=1.0,
            velocity=80,
            instrument="piano",
            tuning_offset_cents=100.0,
        )
        score = _make_score((note,))
        midi = score_ir_to_midi(score)
        bends = midi.instruments[0].pitch_bends
        # Should have at least onset bend + reset bend
        assert len(bends) >= 2
        # Last bend should be reset (pitch=0 means center)
        assert bends[-1].pitch == 0


class TestMicrotimingRendering:
    """microtiming_offset_ms shifts note start time."""

    def test_positive_offset_delays_note(self) -> None:
        normal = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        delayed = Note(
            pitch=60,
            start_beat=0.0,
            duration_beats=1.0,
            velocity=80,
            instrument="piano",
            microtiming_offset_ms=50.0,
        )
        score_normal = _make_score((normal,))
        score_delayed = _make_score((delayed,))
        midi_normal = score_ir_to_midi(score_normal)
        midi_delayed = score_ir_to_midi(score_delayed)
        start_normal = midi_normal.instruments[0].notes[0].start
        start_delayed = midi_delayed.instruments[0].notes[0].start
        assert start_delayed > start_normal
        assert abs(start_delayed - start_normal - 0.05) < 0.001

    def test_negative_offset_does_not_go_below_zero(self) -> None:
        note = Note(
            pitch=60,
            start_beat=0.0,
            duration_beats=1.0,
            velocity=80,
            instrument="piano",
            microtiming_offset_ms=-1000.0,
        )
        score = _make_score((note,))
        midi = score_ir_to_midi(score)
        assert midi.instruments[0].notes[0].start >= 0.0
