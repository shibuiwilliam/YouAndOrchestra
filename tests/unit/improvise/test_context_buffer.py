"""Tests for ContextBuffer — ring buffer and feature estimation."""

from __future__ import annotations

from time import monotonic

from yao.improvise.context_buffer import ContextBuffer, NoteEvent


def _note(pitch: int, velocity: int = 80) -> NoteEvent:
    return NoteEvent(pitch=pitch, velocity=velocity, timestamp=monotonic())


class TestRingBuffer:
    def test_push_respects_max_size(self) -> None:
        buf = ContextBuffer(max_events=5)
        for i in range(10):
            buf.push(_note(60 + i))
        assert buf.size == 5

    def test_wrap_around_preserves_latest(self) -> None:
        buf = ContextBuffer(max_events=3)
        for i in range(5):
            buf.push(_note(60 + i))
        events = buf.all_events()
        assert len(events) == 3
        # Should have the last 3 (62, 63, 64)
        pitches = [e.pitch for e in events]
        assert pitches == [62, 63, 64]

    def test_clear(self) -> None:
        buf = ContextBuffer(max_events=10)
        buf.push(_note(60))
        buf.clear()
        assert buf.size == 0

    def test_max_size_property(self) -> None:
        buf = ContextBuffer(max_events=100)
        assert buf.max_size == 100


class TestKeyEstimation:
    def test_empty_returns_default(self) -> None:
        buf = ContextBuffer()
        assert buf.estimate_key() == "C major"

    def test_c_major_notes_detect_c(self) -> None:
        buf = ContextBuffer()
        # C major scale: C D E F G A B
        for pitch in [60, 62, 64, 65, 67, 69, 71]:
            buf.push(_note(pitch))
        key = buf.estimate_key()
        assert "C" in key


class TestChordEstimation:
    def test_empty_returns_default(self) -> None:
        buf = ContextBuffer()
        assert buf.estimate_current_chord() == "C"

    def test_c_triad_detects_c(self) -> None:
        buf = ContextBuffer()
        for pitch in [60, 64, 67]:  # C E G
            buf.push(_note(pitch))
        chord = buf.estimate_current_chord()
        assert chord == "C"


class TestTempoEstimation:
    def test_empty_returns_default(self) -> None:
        buf = ContextBuffer()
        assert buf.estimate_tempo() == 120.0

    def test_returns_positive_bpm(self) -> None:
        buf = ContextBuffer()
        # Simulate notes at regular intervals
        base = monotonic()
        for i in range(5):
            buf.push(NoteEvent(pitch=60, velocity=80, timestamp=base + i * 0.5))
        bpm = buf.estimate_tempo()
        assert bpm > 0
        assert 40 <= bpm <= 300
