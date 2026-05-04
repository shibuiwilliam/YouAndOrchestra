"""Integration test: arrangement pipeline end-to-end.

Generates a source MIDI, then applies arrangement operations and
verifies the output.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Ensure generators are registered
import yao.generators.rule_based as _rb  # noqa: F401
from yao.generators.registry import get_generator
from yao.render.midi_writer import write_midi
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec


def _generate_source_midi(tmp_path: Path) -> Path:
    """Generate a source MIDI for arrangement tests."""
    spec = CompositionSpec(
        title="Arrangement Source",
        key="C major",
        tempo_bpm=120.0,
        time_signature="4/4",
        instruments=[
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="acoustic_bass", role="bass"),
        ],
        sections=[
            SectionSpec(name="verse", bars=8, dynamics="mf"),
        ],
    )
    gen = get_generator("rule_based")
    score, _ = gen.generate(spec)
    midi_path = tmp_path / "source.mid"
    write_midi(score, midi_path)
    return midi_path


@pytest.mark.integration
class TestArrangePipeline:
    """End-to-end arrangement pipeline tests."""

    def test_arrange_with_retempo_and_regroove(self, tmp_path: Path) -> None:
        """Apply retempo + regroove and verify output MIDI."""
        source_midi = _generate_source_midi(tmp_path)

        arr_data = {
            "input": {
                "file": str(source_midi),
                "rights_status": "original",
            },
            "preserve": {
                "melody": True,
                "form": True,
            },
            "transform": {
                "target_genre": "jazz",
                "bpm": 90.0,
                "reharmonization_level": 0.0,
            },
        }
        arr_path = tmp_path / "arrangement.yaml"
        arr_path.write_text(yaml.dump(arr_data))

        from click.testing import CliRunner

        from cli.main import cli

        runner = CliRunner()
        out_dir = tmp_path / "output"
        result = runner.invoke(cli, ["arrange", str(arr_path), "-o", str(out_dir)])
        assert result.exit_code == 0, result.output

        # Verify outputs
        assert (out_dir / "full.mid").exists()
        assert (out_dir / "provenance.json").exists()
        assert (out_dir / "arrangement_diff.md").exists()

        # Verify provenance has records
        import json

        prov_data = json.loads((out_dir / "provenance.json").read_text())
        assert len(prov_data) > 0  # list of provenance records

    def test_arrange_with_reharmonize(self, tmp_path: Path) -> None:
        """Apply reharmonization and verify chord changes."""
        source_midi = _generate_source_midi(tmp_path)

        arr_data = {
            "input": {
                "file": str(source_midi),
                "rights_status": "original",
            },
            "transform": {
                "reharmonization_level": 0.8,
            },
        }
        arr_path = tmp_path / "arrangement.yaml"
        arr_path.write_text(yaml.dump(arr_data))

        from yao.arrange.base import get_arrangement
        from yao.arrange.operations import ReharmonizeOperation as _  # noqa: F401
        from yao.reflect.provenance import ProvenanceLog
        from yao.render.midi_reader import load_midi_to_score_ir

        source_score = load_midi_to_score_ir(source_midi)
        op = get_arrangement("reharmonize")
        prov = ProvenanceLog()
        result = op.apply(source_score, {"level": 0.8, "seed": 42}, prov)

        # Some notes should have changed
        orig_pitches = set(n.pitch for n in source_score.all_notes())
        new_pitches = set(n.pitch for n in result.all_notes())
        assert orig_pitches != new_pitches, "Reharmonize should produce different pitches"

        # Provenance recorded
        assert len(prov) > 0

    def test_transpose_range_violation(self, tmp_path: Path) -> None:
        """Transposing too high raises RangeViolationError."""
        from yao.arrange.base import get_arrangement
        from yao.arrange.operations import TransposeOperation as _  # noqa: F401
        from yao.errors import RangeViolationError
        from yao.reflect.provenance import ProvenanceLog
        from yao.render.midi_reader import load_midi_to_score_ir

        source_midi = _generate_source_midi(tmp_path)
        source_score = load_midi_to_score_ir(source_midi)

        op = get_arrangement("transpose")
        prov = ProvenanceLog()
        # Transpose way up — should exceed piano range
        with pytest.raises(RangeViolationError):
            op.apply(source_score, {"semitones": 60}, prov)
