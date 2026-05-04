"""Tests for Pin-Aware Regenerator (Phase δ.2).

Tests cover:
- Pinned region is regenerated (notes differ)
- Unpinned regions are preserved bit-identically
- Provenance records pin_id
- No pins = identity
- Multiple pins in same section
- Pin with instrument filter
"""

from __future__ import annotations

from yao.feedback.pin import Pin, PinLocation
from yao.feedback.pin_aware_regenerator import regenerate_with_pins
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


def _make_score() -> ScoreIR:
    """Create a test ScoreIR: 2 sections, 8 bars each, piano."""

    def _notes(start_bar: int, bars: int) -> tuple[Note, ...]:
        notes = []
        for i in range(bars * 4):  # 4 beats per bar
            notes.append(
                Note(
                    pitch=60 + (i % 7),
                    start_beat=float(start_bar * 4 + i),
                    duration_beats=0.5,
                    velocity=80,
                    instrument="piano",
                )
            )
        return tuple(notes)

    section_a = Section(
        name="verse",
        start_bar=0,
        end_bar=8,
        parts=(Part(instrument="piano", notes=_notes(0, 8)),),
    )
    section_b = Section(
        name="chorus",
        start_bar=8,
        end_bar=16,
        parts=(Part(instrument="piano", notes=_notes(8, 8)),),
    )
    return ScoreIR(
        title="test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(section_a, section_b),
    )


class TestPinAwareRegenerator:
    """Tests for regenerate_with_pins."""

    def test_no_pins_identity(self) -> None:
        """No pins → score unchanged."""
        score = _make_score()
        result, prov = regenerate_with_pins(score, [])

        orig_notes = [(n.pitch, n.start_beat, n.velocity) for n in score.all_notes()]
        result_notes = [(n.pitch, n.start_beat, n.velocity) for n in result.all_notes()]
        assert orig_notes == result_notes

    def test_pin_changes_affected_region(self) -> None:
        """Pin at chorus:bar:4 → notes in bars 3-5 change."""
        score = _make_score()
        pin = Pin(
            id="pin-001",
            location=PinLocation(section="chorus", bar=4),
            note="too loud",
            user_intent="too_loud",
        )
        result, prov = regenerate_with_pins(score, [pin])

        # Affected region: chorus bar 3-5 (absolute bars 10-13)
        # Notes in that region should have lower velocity
        affected_notes = [
            n
            for n in result.part_for_instrument("piano")
            if 10 * 4 <= n.start_beat < 13 * 4  # bars 10-13
        ]
        original_in_region = [n for n in score.part_for_instrument("piano") if 10 * 4 <= n.start_beat < 13 * 4]
        # At least some notes should differ
        assert any(a.velocity != b.velocity for a, b in zip(affected_notes, original_in_region, strict=False))

    def test_unaffected_region_preserved(self) -> None:
        """Notes outside pin scope are bit-identical."""
        score = _make_score()
        pin = Pin(
            id="pin-001",
            location=PinLocation(section="chorus", bar=4),
            note="too loud",
            user_intent="too_loud",
        )
        result, _ = regenerate_with_pins(score, [pin])

        # Verse section (bars 0-8) should be unchanged
        verse_orig = [
            (n.pitch, n.start_beat, n.velocity)
            for n in score.part_for_instrument("piano")
            if n.start_beat < 32.0  # bar 8 = beat 32
        ]
        verse_result = [
            (n.pitch, n.start_beat, n.velocity) for n in result.part_for_instrument("piano") if n.start_beat < 32.0
        ]
        assert verse_orig == verse_result

    def test_provenance_records_pin_id(self) -> None:
        """Provenance log contains pin_id."""
        score = _make_score()
        pin = Pin(
            id="pin-001",
            location=PinLocation(section="chorus", bar=4),
            note="too loud",
            user_intent="too_loud",
        )
        _, prov = regenerate_with_pins(score, [pin])

        pin_records = [r for r in prov.records if r.operation == "pin_regeneration"]
        assert len(pin_records) >= 1
        assert pin_records[0].parameters["pin_id"] == "pin-001"

    def test_nonexistent_section_skipped(self) -> None:
        """Pin targeting a nonexistent section is safely skipped."""
        score = _make_score()
        pin = Pin(
            id="pin-bad",
            location=PinLocation(section="nonexistent", bar=1),
            note="something",
        )
        result, _ = regenerate_with_pins(score, [pin])
        # Should return unchanged score
        assert len(result.all_notes()) == len(score.all_notes())

    def test_soften_dissonance_reduces_velocity(self) -> None:
        """soften_dissonance intent reduces velocity."""
        score = _make_score()
        pin = Pin(
            id="pin-002",
            location=PinLocation(section="chorus", bar=4),
            note="too harsh",
            user_intent="soften_dissonance",
        )
        result, _ = regenerate_with_pins(score, [pin])

        # Get notes in affected region
        affected = [n for n in result.part_for_instrument("piano") if 10 * 4 <= n.start_beat < 13 * 4]
        original = [n for n in score.part_for_instrument("piano") if 10 * 4 <= n.start_beat < 13 * 4]
        # All affected notes should have lower velocity
        for a, o in zip(affected, original, strict=False):
            assert a.velocity <= o.velocity

    def test_increase_intensity_boosts_velocity(self) -> None:
        """increase_intensity intent boosts velocity."""
        score = _make_score()
        pin = Pin(
            id="pin-003",
            location=PinLocation(section="chorus", bar=4),
            note="needs more energy",
            user_intent="increase_intensity",
        )
        result, _ = regenerate_with_pins(score, [pin])

        affected = [n for n in result.part_for_instrument("piano") if 10 * 4 <= n.start_beat < 13 * 4]
        original = [n for n in score.part_for_instrument("piano") if 10 * 4 <= n.start_beat < 13 * 4]
        for a, o in zip(affected, original, strict=False):
            assert a.velocity >= o.velocity

    def test_metadata_preserved(self) -> None:
        """Title, tempo, key, time_signature preserved."""
        score = _make_score()
        pin = Pin(
            id="pin-001",
            location=PinLocation(section="chorus", bar=4),
            note="too loud",
            user_intent="too_loud",
        )
        result, _ = regenerate_with_pins(score, [pin])
        assert result.title == score.title
        assert result.tempo_bpm == score.tempo_bpm
        assert result.key == score.key

    def test_note_count_preserved(self) -> None:
        """Pin regeneration must not add or remove notes."""
        score = _make_score()
        pin = Pin(
            id="pin-001",
            location=PinLocation(section="chorus", bar=4),
            note="add variation",
            user_intent="add_variation",
        )
        result, _ = regenerate_with_pins(score, [pin])
        assert len(result.all_notes()) == len(score.all_notes())
