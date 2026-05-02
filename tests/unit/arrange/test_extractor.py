"""Tests for Source Plan Extractor."""

from __future__ import annotations

from pathlib import Path

import pretty_midi
import pytest

from yao.arrange.extractor import ExtractionConfidence, SourcePlanExtractor
from yao.ir.plan.musical_plan import MusicalPlan


@pytest.fixture()
def simple_midi(tmp_path: Path) -> Path:
    """Create a simple 8-bar MIDI file."""
    midi = pretty_midi.PrettyMIDI(initial_tempo=120.0)
    piano = pretty_midi.Instrument(program=0, name="piano")
    for i in range(32):
        note = pretty_midi.Note(velocity=80, pitch=60 + (i % 7), start=i * 0.5, end=(i + 1) * 0.5)
        piano.notes.append(note)
    midi.instruments.append(piano)
    path = tmp_path / "simple.mid"
    midi.write(str(path))
    return path


class TestSourcePlanExtractor:
    def test_extract_produces_plan(self, simple_midi: Path) -> None:
        extractor = SourcePlanExtractor()
        plan, confidence = extractor.extract(simple_midi)
        assert isinstance(plan, MusicalPlan)
        assert isinstance(confidence, ExtractionConfidence)

    def test_confidence_scores_in_range(self, simple_midi: Path) -> None:
        _, conf = SourcePlanExtractor().extract(simple_midi)
        assert 0.0 <= conf.form <= 1.0
        assert 0.0 <= conf.harmony <= 1.0
        assert 0.0 <= conf.melody <= 1.0
        assert 0.0 <= conf.drums <= 1.0

    def test_has_sections(self, simple_midi: Path) -> None:
        plan, _ = SourcePlanExtractor().extract(simple_midi)
        assert len(plan.form.sections) > 0

    def test_has_chord_events(self, simple_midi: Path) -> None:
        plan, _ = SourcePlanExtractor().extract(simple_midi)
        assert len(plan.harmony.chord_events) > 0
