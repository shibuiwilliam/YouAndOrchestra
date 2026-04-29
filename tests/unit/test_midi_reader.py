"""Tests for MIDI-to-ScoreIR loading (round-trip and edge cases)."""

from __future__ import annotations

from pathlib import Path

import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.render.midi_reader import load_midi_to_score_ir
from yao.render.midi_writer import write_midi
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)


def _make_spec(**overrides: object) -> CompositionSpec:
    defaults: dict[str, object] = {
        "title": "Round Trip Test",
        "key": "C major",
        "tempo_bpm": 120.0,
        "instruments": [
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="acoustic_bass", role="bass"),
        ],
        "sections": [
            SectionSpec(name="verse", bars=4, dynamics="mf"),
            SectionSpec(name="chorus", bars=4, dynamics="f"),
        ],
        "generation": GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
    }
    defaults.update(overrides)
    return CompositionSpec(**defaults)  # type: ignore[arg-type]


class TestMidiReaderRoundTrip:
    def test_round_trip_preserves_note_count(self, tmp_path: Path) -> None:
        """Write ScoreIR to MIDI and read it back; note counts should match."""
        spec = _make_spec()
        from yao.generators.stochastic import StochasticGenerator

        gen = StochasticGenerator()
        score, _ = gen.generate(spec)

        midi_path = tmp_path / "test.mid"
        write_midi(score, midi_path)
        loaded = load_midi_to_score_ir(midi_path, spec=spec)

        original_notes = len(score.all_notes())
        loaded_notes = len(loaded.all_notes())
        assert loaded_notes == original_notes

    def test_round_trip_preserves_instruments(self, tmp_path: Path) -> None:
        """Instruments should survive the round trip."""
        spec = _make_spec()
        from yao.generators.stochastic import StochasticGenerator

        gen = StochasticGenerator()
        score, _ = gen.generate(spec)

        midi_path = tmp_path / "test.mid"
        write_midi(score, midi_path)
        loaded = load_midi_to_score_ir(midi_path, spec=spec)

        assert set(loaded.instruments()) == set(score.instruments())

    def test_round_trip_preserves_pitches(self, tmp_path: Path) -> None:
        """Pitches are exact integers and should survive perfectly."""
        spec = _make_spec()
        from yao.generators.stochastic import StochasticGenerator

        gen = StochasticGenerator()
        score, _ = gen.generate(spec)

        midi_path = tmp_path / "test.mid"
        write_midi(score, midi_path)
        loaded = load_midi_to_score_ir(midi_path, spec=spec)

        original_pitches = sorted(n.pitch for n in score.all_notes())
        loaded_pitches = sorted(n.pitch for n in loaded.all_notes())
        assert original_pitches == loaded_pitches

    def test_round_trip_preserves_tempo(self, tmp_path: Path) -> None:
        """Tempo should be preserved."""
        spec = _make_spec(tempo_bpm=90.0)
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(spec)

        midi_path = tmp_path / "test.mid"
        write_midi(score, midi_path)
        loaded = load_midi_to_score_ir(midi_path, spec=spec)

        assert abs(loaded.tempo_bpm - 90.0) < 1.0

    def test_round_trip_sections_from_spec(self, tmp_path: Path) -> None:
        """When spec is provided, sections should match."""
        spec = _make_spec()
        from yao.generators.stochastic import StochasticGenerator

        gen = StochasticGenerator()
        score, _ = gen.generate(spec)

        midi_path = tmp_path / "test.mid"
        write_midi(score, midi_path)
        loaded = load_midi_to_score_ir(midi_path, spec=spec)

        assert len(loaded.sections) == len(spec.sections)
        for loaded_sec, spec_sec in zip(loaded.sections, spec.sections, strict=True):
            assert loaded_sec.name == spec_sec.name


class TestMidiReaderWithoutSpec:
    def test_load_without_spec_creates_single_section(self, tmp_path: Path) -> None:
        """Without a spec, all notes go into a single 'full' section."""
        score = ScoreIR(
            title="Simple",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="verse",
                    start_bar=0,
                    end_bar=4,
                    parts=(
                        Part(
                            instrument="piano",
                            notes=(
                                Note(pitch=60, start_beat=0.0, duration_beats=1.0,
                                     velocity=80, instrument="piano"),
                                Note(pitch=64, start_beat=4.0, duration_beats=1.0,
                                     velocity=80, instrument="piano"),
                            ),
                        ),
                    ),
                ),
            ),
        )
        midi_path = tmp_path / "simple.mid"
        write_midi(score, midi_path)
        loaded = load_midi_to_score_ir(midi_path)

        assert len(loaded.sections) == 1
        assert loaded.sections[0].name == "full"
        assert len(loaded.all_notes()) == 2

    def test_load_title_defaults_to_filename(self, tmp_path: Path) -> None:
        """Title should be the filename stem when no spec or title given."""
        score = ScoreIR(
            title="Ignored",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="a", start_bar=0, end_bar=1,
                    parts=(Part(instrument="piano", notes=(
                        Note(pitch=60, start_beat=0.0, duration_beats=1.0,
                             velocity=80, instrument="piano"),
                    )),),
                ),
            ),
        )
        midi_path = tmp_path / "my_song.mid"
        write_midi(score, midi_path)
        loaded = load_midi_to_score_ir(midi_path)
        assert loaded.title == "my_song"


class TestMidiReaderEdgeCases:
    def test_nonexistent_file_raises(self, tmp_path: Path) -> None:
        """Loading a non-existent file should raise RenderError."""
        import pytest

        from yao.errors import RenderError

        with pytest.raises(RenderError):
            load_midi_to_score_ir(tmp_path / "does_not_exist.mid")

    def test_title_override(self, tmp_path: Path) -> None:
        """The title parameter should override all other sources."""
        score = ScoreIR(
            title="Original",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="a", start_bar=0, end_bar=1,
                    parts=(Part(instrument="piano", notes=(
                        Note(pitch=60, start_beat=0.0, duration_beats=1.0,
                             velocity=80, instrument="piano"),
                    )),),
                ),
            ),
        )
        midi_path = tmp_path / "test.mid"
        write_midi(score, midi_path)
        loaded = load_midi_to_score_ir(midi_path, title="Custom Title")
        assert loaded.title == "Custom Title"
