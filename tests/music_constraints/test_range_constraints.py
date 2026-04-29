"""Music constraint tests: all generated notes must be in instrument range."""

from __future__ import annotations

import pytest

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.generators.rule_based import RuleBasedGenerator
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec


@pytest.mark.music_constraints
class TestRangeConstraints:
    @pytest.mark.parametrize(
        "instrument,role",
        [
            ("piano", "melody"),
            ("piano", "harmony"),
            ("acoustic_bass", "bass"),
            ("violin", "melody"),
            ("flute", "melody"),
            ("cello", "bass"),
        ],
    )
    def test_generated_notes_in_range(self, instrument: str, role: str) -> None:
        """For each instrument/role combo, all generated notes must be in range."""
        spec = CompositionSpec(
            title=f"Range Test: {instrument}",
            key="C major",
            tempo_bpm=120.0,
            instruments=[InstrumentSpec(name=instrument, role=role)],
            sections=[
                SectionSpec(name="intro", bars=4, dynamics="mp"),
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="chorus", bars=8, dynamics="f"),
            ],
        )

        gen = RuleBasedGenerator()
        score, _ = gen.generate(spec)

        inst_range = INSTRUMENT_RANGES[instrument]
        for note in score.all_notes():
            assert inst_range.midi_low <= note.pitch <= inst_range.midi_high, (
                f"Note {note.pitch} out of {instrument} range "
                f"({inst_range.midi_low}–{inst_range.midi_high}) "
                f"at beat {note.start_beat}"
            )

    def test_all_velocities_valid(self) -> None:
        """All generated velocities must be in 1-127."""
        spec = CompositionSpec(
            title="Velocity Test",
            key="C major",
            instruments=[
                InstrumentSpec(name="piano", role="melody"),
                InstrumentSpec(name="acoustic_bass", role="bass"),
            ],
            sections=[
                SectionSpec(name="pp_section", bars=4, dynamics="pp"),
                SectionSpec(name="ff_section", bars=4, dynamics="ff"),
            ],
        )
        gen = RuleBasedGenerator()
        score, _ = gen.generate(spec)

        for note in score.all_notes():
            assert 1 <= note.velocity <= 127, (
                f"Velocity {note.velocity} out of range at beat {note.start_beat}"
            )
