"""Integration test: composition with drum pattern.

Verifies that a spec with `drums:` produces a MIDI file containing
a drum track, and that specs without `drums:` remain unchanged.
"""

from __future__ import annotations

from pathlib import Path

import pretty_midi

# Ensure generators are registered
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.generators.drum_patterner import generate_drum_hits
from yao.generators.registry import get_generator
from yao.render.midi_writer import write_midi
from yao.schema.composition import (
    CompositionSpec,
    DrumsSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)


class TestComposeWithDrums:
    """End-to-end: spec with drums produces MIDI with drum track."""

    def test_lofi_spec_has_drum_track(self, tmp_path: Path) -> None:
        """A spec with drums: should produce a MIDI with a drum instrument."""
        spec = CompositionSpec(
            title="Lofi Test",
            key="A minor",
            tempo_bpm=82,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=4, dynamics="mp")],
            drums=DrumsSpec(pattern_family="lofi_laidback", swing=0.6),
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )

        # Generate pitched notes
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)

        # Generate drum hits
        drum_hits, _ = generate_drum_hits(spec, seed=42)
        assert len(drum_hits) > 0

        # Write MIDI with drums
        out = tmp_path / "with_drums.mid"
        write_midi(score, out, drum_hits=drum_hits)
        assert out.exists()

        # Verify MIDI has a drum instrument
        midi = pretty_midi.PrettyMIDI(str(out))
        drum_instruments = [i for i in midi.instruments if i.is_drum]
        assert len(drum_instruments) == 1
        assert len(drum_instruments[0].notes) > 0

    def test_no_drums_spec_has_no_drum_track(self, tmp_path: Path) -> None:
        """A spec without drums: should produce MIDI without drum track."""
        spec = CompositionSpec(
            title="No Drums",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=4, dynamics="mf")],
            generation=GenerationConfig(strategy="rule_based"),
        )

        gen = get_generator("rule_based")
        score, _ = gen.generate(spec)

        out = tmp_path / "no_drums.mid"
        write_midi(score, out)
        assert out.exists()

        midi = pretty_midi.PrettyMIDI(str(out))
        drum_instruments = [i for i in midi.instruments if i.is_drum]
        assert len(drum_instruments) == 0
