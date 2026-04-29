"""Tests for the MIDI rendering layer."""

from __future__ import annotations

from pathlib import Path

import pretty_midi

from yao.ir.score_ir import ScoreIR
from yao.render.midi_writer import score_ir_to_midi, write_midi
from yao.schema.composition import CompositionSpec


class TestMidiWriter:
    def test_score_ir_to_midi(self, sample_score_ir: ScoreIR) -> None:
        midi = score_ir_to_midi(sample_score_ir)
        assert isinstance(midi, pretty_midi.PrettyMIDI)
        assert len(midi.instruments) == 1
        assert midi.instruments[0].name == "piano"

    def test_midi_note_count(self, sample_score_ir: ScoreIR) -> None:
        midi = score_ir_to_midi(sample_score_ir)
        total_notes = sum(len(inst.notes) for inst in midi.instruments)
        assert total_notes == 8

    def test_write_midi_creates_file(self, sample_score_ir: ScoreIR, tmp_output_dir: Path) -> None:
        midi_path = tmp_output_dir / "test.mid"
        result = write_midi(sample_score_ir, midi_path)
        assert result == midi_path
        assert midi_path.exists()
        assert midi_path.stat().st_size > 0

    def test_midi_round_trip(self, sample_score_ir: ScoreIR, tmp_output_dir: Path) -> None:
        midi_path = tmp_output_dir / "roundtrip.mid"
        write_midi(sample_score_ir, midi_path)

        # Read back and verify
        loaded = pretty_midi.PrettyMIDI(str(midi_path))
        assert len(loaded.instruments) == 1
        original_count = len(sample_score_ir.all_notes())
        loaded_count = sum(len(inst.notes) for inst in loaded.instruments)
        assert loaded_count == original_count

    def test_multi_instrument_midi(
        self, multi_instrument_spec: CompositionSpec, tmp_output_dir: Path
    ) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(multi_instrument_spec)

        midi_path = tmp_output_dir / "multi.mid"
        write_midi(score, midi_path)

        loaded = pretty_midi.PrettyMIDI(str(midi_path))
        assert len(loaded.instruments) >= 2
