"""Tests for Style Vector Operations."""

from __future__ import annotations

from pathlib import Path

import pretty_midi
import pytest

from yao.arrange.extractor import SourcePlanExtractor
from yao.arrange.style_vector_ops import transfer
from yao.schema.arrangement import (
    ArrangementInputSpec,
    ArrangementSpec,
    PreservationSpec,
    TransformSpec,
)


@pytest.fixture()
def source_plan(tmp_path: Path) -> object:
    """Extract a plan from a simple MIDI."""
    midi = pretty_midi.PrettyMIDI(initial_tempo=120.0)
    piano = pretty_midi.Instrument(program=0, name="piano")
    for i in range(32):
        piano.notes.append(pretty_midi.Note(velocity=80, pitch=60 + (i % 7), start=i * 0.5, end=(i + 1) * 0.5))
    midi.instruments.append(piano)
    path = tmp_path / "source.mid"
    midi.write(str(path))
    plan, _ = SourcePlanExtractor().extract(path)
    return plan


def _make_arrangement_spec(
    target_genre: str = "lofi_hiphop",
    reharm: float = 0.0,
    bpm: float | None = None,
) -> ArrangementSpec:
    return ArrangementSpec(
        input=ArrangementInputSpec(file="source.mid", rights_status="owned_or_licensed"),
        preserve=PreservationSpec(),
        transform=TransformSpec(target_genre=target_genre, reharmonization_level=reharm, bpm=bpm),
    )


class TestTransfer:
    def test_transfer_changes_genre(self, source_plan: object) -> None:
        spec = _make_arrangement_spec(target_genre="jazz")
        target, pres = transfer(source_plan, spec)  # type: ignore[arg-type]
        assert target.global_context.genre == "jazz"

    def test_transfer_changes_tempo(self, source_plan: object) -> None:
        spec = _make_arrangement_spec(bpm=86.0)
        target, _ = transfer(source_plan, spec)  # type: ignore[arg-type]
        assert target.global_context.tempo_bpm == 86.0

    def test_identity_transfer(self, source_plan: object) -> None:
        spec = _make_arrangement_spec(target_genre="general", reharm=0.0)
        target, pres = transfer(source_plan, spec)  # type: ignore[arg-type]
        assert pres.all_passed
        assert pres.chord_similarity == 1.0

    def test_high_reharmonization_lowers_chord_similarity(self, source_plan: object) -> None:
        spec = _make_arrangement_spec(reharm=0.8)
        _, pres = transfer(source_plan, spec)  # type: ignore[arg-type]
        assert pres.chord_similarity < 1.0
