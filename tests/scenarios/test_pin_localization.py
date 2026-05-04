"""Scenario test: Pin-driven regeneration is localized.

Verifies that pin at section:chorus, bar:6 → only that area regenerates;
bars 1-5 and 7-end in the chorus are bit-identical to previous iteration.
Verse section is completely unchanged.
"""

from __future__ import annotations

from yao.feedback.pin import Pin, PinLocation
from yao.feedback.pin_aware_regenerator import regenerate_with_pins
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


def _make_score() -> ScoreIR:
    """Create a score: verse (8 bars) + chorus (8 bars), piano."""

    def _notes(start_bar: int, bars: int) -> tuple[Note, ...]:
        notes = []
        for i in range(bars * 4):
            notes.append(
                Note(
                    pitch=60 + (i % 12),
                    start_beat=float(start_bar * 4 + i),
                    duration_beats=0.5,
                    velocity=80,
                    instrument="piano",
                )
            )
        return tuple(notes)

    return ScoreIR(
        title="test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(
            Section(name="verse", start_bar=0, end_bar=8, parts=(Part(instrument="piano", notes=_notes(0, 8)),)),
            Section(name="chorus", start_bar=8, end_bar=16, parts=(Part(instrument="piano", notes=_notes(8, 8)),)),
        ),
    )


def _notes_in_bar_range(
    score: ScoreIR,
    instrument: str,
    bar_start: int,
    bar_end: int,
) -> list[tuple[int, float, int]]:
    """Extract (pitch, start_beat, velocity) for notes in a bar range."""
    beat_start = bar_start * 4.0
    beat_end = bar_end * 4.0
    return [
        (n.pitch, n.start_beat, n.velocity)
        for n in score.part_for_instrument(instrument)
        if beat_start <= n.start_beat < beat_end
    ]


class TestPinLocalization:
    """Scenario: pin at chorus bar 6 only affects bars 5-7."""

    def test_verse_completely_unchanged(self) -> None:
        score = _make_score()
        pin = Pin(
            id="pin-001",
            location=PinLocation(section="chorus", bar=6),
            note="too loud",
            user_intent="too_loud",
        )
        result, _ = regenerate_with_pins(score, [pin])

        verse_orig = _notes_in_bar_range(score, "piano", 0, 8)
        verse_result = _notes_in_bar_range(result, "piano", 0, 8)
        assert verse_orig == verse_result

    def test_chorus_early_bars_unchanged(self) -> None:
        """Chorus bars 1-4 (absolute 8-12) should be unchanged."""
        score = _make_score()
        pin = Pin(
            id="pin-001",
            location=PinLocation(section="chorus", bar=6),
            note="too loud",
            user_intent="too_loud",
        )
        result, _ = regenerate_with_pins(score, [pin])

        early_orig = _notes_in_bar_range(score, "piano", 8, 12)
        early_result = _notes_in_bar_range(result, "piano", 8, 12)
        assert early_orig == early_result

    def test_chorus_late_bars_unchanged(self) -> None:
        """Chorus bar 8 (absolute 15-16) should be unchanged."""
        score = _make_score()
        pin = Pin(
            id="pin-001",
            location=PinLocation(section="chorus", bar=6),
            note="too loud",
            user_intent="too_loud",
        )
        result, _ = regenerate_with_pins(score, [pin])

        late_orig = _notes_in_bar_range(score, "piano", 15, 16)
        late_result = _notes_in_bar_range(result, "piano", 15, 16)
        assert late_orig == late_result

    def test_affected_region_changes(self) -> None:
        """Chorus bars 5-7 (absolute 12-15) should change."""
        score = _make_score()
        pin = Pin(
            id="pin-001",
            location=PinLocation(section="chorus", bar=6),
            note="too loud",
            user_intent="too_loud",
        )
        result, _ = regenerate_with_pins(score, [pin])

        affected_orig = _notes_in_bar_range(score, "piano", 12, 15)
        affected_result = _notes_in_bar_range(result, "piano", 12, 15)
        assert affected_orig != affected_result

    def test_total_note_count_unchanged(self) -> None:
        score = _make_score()
        pin = Pin(
            id="pin-001",
            location=PinLocation(section="chorus", bar=6),
            note="too loud",
            user_intent="too_loud",
        )
        result, _ = regenerate_with_pins(score, [pin])
        assert len(result.all_notes()) == len(score.all_notes())
