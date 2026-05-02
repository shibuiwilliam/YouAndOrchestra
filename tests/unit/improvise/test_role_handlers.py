"""Tests for role handlers — MIDI response logic."""

from __future__ import annotations

from time import monotonic

from yao.improvise.context_buffer import ContextBuffer, NoteEvent
from yao.improvise.role_handlers import (
    AccompanistHandler,
    BassistHandler,
    DrummerHandler,
    ImprovisationRole,
    MelodyFollowerHandler,
    get_handler,
)


def _make_context_with_notes() -> ContextBuffer:
    buf = ContextBuffer()
    for pitch in [60, 64, 67, 72]:
        buf.push(NoteEvent(pitch=pitch, velocity=80, timestamp=monotonic()))
    return buf


class TestBassist:
    def test_responds_with_bass_notes(self) -> None:
        handler = BassistHandler()
        ctx = _make_context_with_notes()
        responses = handler.respond(ctx)
        assert len(responses) > 0
        # Bass notes should be in low range (36-47)
        assert all(36 <= r.pitch <= 47 for r in responses)


class TestDrummer:
    def test_responds_with_drum_hits(self) -> None:
        handler = DrummerHandler()
        ctx = _make_context_with_notes()
        responses = handler.respond(ctx)
        assert len(responses) > 0
        # Drum hits on channel 9
        assert all(r.channel == 9 for r in responses)


class TestAccompanist:
    def test_responds_with_chord(self) -> None:
        handler = AccompanistHandler()
        ctx = _make_context_with_notes()
        responses = handler.respond(ctx)
        # Should produce a triad (3 notes)
        assert len(responses) == 3


class TestMelodyFollower:
    def test_responds_with_harmony(self) -> None:
        handler = MelodyFollowerHandler()
        ctx = _make_context_with_notes()
        responses = handler.respond(ctx)
        assert len(responses) > 0

    def test_empty_context_no_response(self) -> None:
        handler = MelodyFollowerHandler()
        ctx = ContextBuffer()
        responses = handler.respond(ctx)
        assert len(responses) == 0


class TestGetHandler:
    def test_all_roles_have_handlers(self) -> None:
        for role in ImprovisationRole:
            handler = get_handler(role)
            assert handler is not None
