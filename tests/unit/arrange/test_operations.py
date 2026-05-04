"""Tests for the five arrangement operations."""

from __future__ import annotations

import pytest

from yao.arrange.base import get_arrangement, registered_arrangements
from yao.arrange.operations import (  # noqa: F401 — trigger registration
    RegrooveOperation,
    ReharmonizeOperation,
    ReorchestrateOperation,
    RetempoOperation,
    TransposeOperation,
)
from yao.errors import RangeViolationError
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog


def _sample_score(instrument: str = "piano", base_pitch: int = 60) -> ScoreIR:
    """Build a minimal ScoreIR for testing."""
    notes = tuple(
        Note(pitch=base_pitch + i, start_beat=float(i), duration_beats=0.9, velocity=80, instrument=instrument)
        for i in range(8)
    )
    part = Part(instrument=instrument, notes=notes)
    section = Section(name="verse", start_bar=0, end_bar=2, parts=(part,))
    return ScoreIR(
        title="Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(section,),
    )


class TestRegistry:
    """Test the arrangement operation registry."""

    def test_all_five_registered(self) -> None:
        """All five MVP operations must be registered."""
        registry = registered_arrangements()
        for name in ["transpose", "retempo", "reorchestrate", "reharmonize", "regroove"]:
            assert name in registry, f"Missing: {name}"

    def test_get_arrangement_returns_instance(self) -> None:
        """get_arrangement returns an operation instance."""
        op = get_arrangement("transpose")
        assert op.name == "transpose"

    def test_unknown_arrangement_raises(self) -> None:
        """Unknown name raises SpecValidationError."""
        from yao.errors import SpecValidationError

        with pytest.raises(SpecValidationError, match="Unknown arrangement"):
            get_arrangement("nonexistent")


class TestTranspose:
    """Tests for TransposeOperation."""

    def test_transpose_up(self) -> None:
        """Transpose up by 2 semitones."""
        score = _sample_score()
        op = get_arrangement("transpose")
        prov = ProvenanceLog()
        result = op.apply(score, {"semitones": 2}, prov)
        original_pitches = [n.pitch for n in score.all_notes()]
        new_pitches = [n.pitch for n in result.all_notes()]
        assert all(n == o + 2 for o, n in zip(original_pitches, new_pitches, strict=True))

    def test_transpose_zero_returns_same(self) -> None:
        """Transpose by 0 returns the source unchanged."""
        score = _sample_score()
        op = get_arrangement("transpose")
        prov = ProvenanceLog()
        result = op.apply(score, {"semitones": 0}, prov)
        assert result is score

    def test_transpose_out_of_range_raises(self) -> None:
        """Transposing out of instrument range raises RangeViolationError."""
        score = _sample_score(base_pitch=120)  # near top of range
        op = get_arrangement("transpose")
        prov = ProvenanceLog()
        with pytest.raises(RangeViolationError):
            op.apply(score, {"semitones": 20}, prov)

    def test_transpose_provenance_logged(self) -> None:
        """Provenance is recorded for transpose."""
        score = _sample_score()
        op = get_arrangement("transpose")
        prov = ProvenanceLog()
        op.apply(score, {"semitones": 3}, prov)
        assert len(prov) > 0
        assert prov.query_by_operation("transpose")


class TestRetempo:
    """Tests for RetempoOperation."""

    def test_retempo_changes_bpm(self) -> None:
        """Retempo changes the tempo_bpm field."""
        score = _sample_score()
        op = get_arrangement("retempo")
        prov = ProvenanceLog()
        result = op.apply(score, {"target_bpm": 90.0}, prov)
        assert result.tempo_bpm == 90.0

    def test_retempo_scale_durations(self) -> None:
        """scale_durations adjusts note timing proportionally."""
        score = _sample_score()
        op = get_arrangement("retempo")
        prov = ProvenanceLog()
        result = op.apply(score, {"target_bpm": 60.0, "scale_durations": True}, prov)
        # 120 → 60 BPM means ratio = 2.0, durations should double
        orig_note = score.all_notes()[0]
        new_note = result.all_notes()[0]
        assert new_note.duration_beats == pytest.approx(orig_note.duration_beats * 2.0)


class TestReorchestrate:
    """Tests for ReorchestrateOperation."""

    def test_reorchestrate_changes_instrument(self) -> None:
        """Instrument names are remapped."""
        score = _sample_score(instrument="piano")
        op = get_arrangement("reorchestrate")
        prov = ProvenanceLog()
        result = op.apply(score, {"mapping": {"piano": "acoustic_guitar"}}, prov)
        instruments = {n.instrument for n in result.all_notes()}
        assert "acoustic_guitar" in instruments
        assert "piano" not in instruments

    def test_reorchestrate_no_mapping_returns_same(self) -> None:
        """Empty mapping returns source unchanged."""
        score = _sample_score()
        op = get_arrangement("reorchestrate")
        prov = ProvenanceLog()
        result = op.apply(score, {"mapping": {}}, prov)
        assert result is score


class TestReharmonize:
    """Tests for ReharmonizeOperation."""

    def test_reharmonize_modifies_notes(self) -> None:
        """Reharmonization with level > 0 should change some chord tones."""
        # Use a non-melody instrument
        notes = tuple(
            Note(pitch=60 + i, start_beat=float(i), duration_beats=0.9, velocity=80, instrument="acoustic_bass")
            for i in range(8)
        )
        part = Part(instrument="acoustic_bass", notes=notes)
        section = Section(name="verse", start_bar=0, end_bar=2, parts=(part,))
        score = ScoreIR(
            title="Test",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(section,),
        )

        op = get_arrangement("reharmonize")
        prov = ProvenanceLog()
        result = op.apply(score, {"level": 1.0, "seed": 42}, prov)
        orig_pitches = [n.pitch for n in score.all_notes()]
        new_pitches = [n.pitch for n in result.all_notes()]
        assert orig_pitches != new_pitches, "Reharmonize should modify chord tones"

    def test_reharmonize_preserves_melody(self) -> None:
        """Melody parts (violin) should not be modified."""
        notes = tuple(
            Note(pitch=60 + i, start_beat=float(i), duration_beats=0.9, velocity=80, instrument="violin")
            for i in range(4)
        )
        part = Part(instrument="violin", notes=notes)
        section = Section(name="verse", start_bar=0, end_bar=1, parts=(part,))
        score = ScoreIR(
            title="Test",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(section,),
        )

        op = get_arrangement("reharmonize")
        prov = ProvenanceLog()
        result = op.apply(score, {"level": 1.0, "seed": 42}, prov)
        assert score.all_notes() == result.all_notes()


class TestRegroove:
    """Tests for RegrooveOperation."""

    def test_regroove_adjusts_timing(self) -> None:
        """Regroove should shift note start times."""
        score = _sample_score()
        op = get_arrangement("regroove")
        prov = ProvenanceLog()
        result = op.apply(score, {"target_genre": "jazz"}, prov)
        orig_starts = [n.start_beat for n in score.all_notes()]
        new_starts = [n.start_beat for n in result.all_notes()]
        assert orig_starts != new_starts, "Regroove should adjust timing"

    def test_regroove_provenance_logged(self) -> None:
        """Provenance is recorded for regroove."""
        score = _sample_score()
        op = get_arrangement("regroove")
        prov = ProvenanceLog()
        op.apply(score, {"target_genre": "lofi_hiphop"}, prov)
        records = prov.query_by_operation("regroove")
        assert len(records) > 0
