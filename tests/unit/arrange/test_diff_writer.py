"""Tests for Arrangement Diff Writer."""

from __future__ import annotations

from pathlib import Path

import pretty_midi
import pytest

from yao.arrange.diff_writer import ArrangementDiffWriter
from yao.arrange.extractor import SourcePlanExtractor
from yao.arrange.style_vector_ops import transfer
from yao.schema.arrangement import (
    ArrangementInputSpec,
    ArrangementSpec,
    TransformSpec,
)


@pytest.fixture()
def plans(tmp_path: Path) -> tuple[object, object, object]:
    """Create source plan, target plan, and preservation result."""
    midi = pretty_midi.PrettyMIDI(initial_tempo=120.0)
    piano = pretty_midi.Instrument(program=0, name="piano")
    for i in range(16):
        piano.notes.append(pretty_midi.Note(velocity=80, pitch=60 + (i % 5), start=i * 0.5, end=(i + 1) * 0.5))
    midi.instruments.append(piano)
    path = tmp_path / "diff_test.mid"
    midi.write(str(path))

    source, _ = SourcePlanExtractor().extract(path)
    spec = ArrangementSpec(
        input=ArrangementInputSpec(file="test.mid", rights_status="public_domain"),
        transform=TransformSpec(target_genre="jazz", reharmonization_level=0.3, bpm=86.0),
    )
    target, pres = transfer(source, spec)
    return source, target, pres


class TestDiffWriter:
    def test_writes_markdown(self, plans: tuple, tmp_path: Path) -> None:
        source, target, pres = plans
        output = tmp_path / "diff.md"
        writer = ArrangementDiffWriter()
        result = writer.write(source, target, pres, output)
        assert result.exists()
        content = output.read_text()
        assert len(content) > 0

    def test_contains_preserved_section(self, plans: tuple, tmp_path: Path) -> None:
        source, target, pres = plans
        output = tmp_path / "diff2.md"
        ArrangementDiffWriter().write(source, target, pres, output)
        content = output.read_text()
        assert "## Preserved" in content

    def test_contains_changed_section(self, plans: tuple, tmp_path: Path) -> None:
        source, target, pres = plans
        output = tmp_path / "diff3.md"
        ArrangementDiffWriter().write(source, target, pres, output)
        content = output.read_text()
        assert "## Changed" in content
        assert "jazz" in content.lower()

    def test_contains_risks_section(self, plans: tuple, tmp_path: Path) -> None:
        source, target, pres = plans
        output = tmp_path / "diff4.md"
        ArrangementDiffWriter().write(source, target, pres, output)
        content = output.read_text()
        assert "## Risks" in content
