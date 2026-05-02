"""Process music generator — Reich/Glass-style repetition and gradual change.

Generates compositions using three process types:
- Phasing: two voices play the same cell, one gradually shifts
- Additive: cell grows by adding notes over time
- Subtractive: cell shrinks by removing notes over time

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.constants.music import DYNAMICS_TO_VELOCITY
from yao.generators.base import GeneratorBase
from yao.generators.registry import register_generator
from yao.ir.notation import parse_key, scale_notes
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import bars_to_beats
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.trajectory import TrajectorySpec
from yao.types import Beat


def _generate_cell(
    root_note: str,
    scale_type: str,
    octave: int,
    rng: random.Random,
    cell_length: int = 4,
) -> list[int]:
    """Generate a short melodic cell from scale notes.

    Args:
        root_note: Root note name.
        scale_type: Scale type.
        octave: Target octave.
        rng: Seeded RNG.
        cell_length: Number of notes in the cell.

    Returns:
        List of MIDI pitches.
    """
    scale = scale_notes(root_note, scale_type, octave)
    return [rng.choice(scale) for _ in range(cell_length)]


@register_generator("process_music")
class ProcessMusicGenerator(GeneratorBase):
    """Process music composition generator.

    Creates compositions through systematic transformation of a
    short melodic cell via phasing, addition, or subtraction.
    """

    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        """Generate a process music composition.

        Args:
            spec: Composition specification.
            trajectory: Optional trajectory.

        Returns:
            Tuple of (ScoreIR, ProvenanceLog).
        """
        seed = spec.generation.seed if spec.generation.seed is not None else 42
        temperature = spec.generation.temperature
        rng = random.Random(seed)

        root_note, scale_type = parse_key(spec.key)

        prov = ProvenanceLog()

        # Determine process type from temperature
        # Low temp = phasing (most orderly), high temp = additive/subtractive
        if temperature < 0.35:  # noqa: PLR2004
            process_type = "phasing"
        elif temperature < 0.65:  # noqa: PLR2004
            process_type = "additive"
        else:
            process_type = "subtractive"

        # Generate the cell
        octave = 5
        inst = spec.instruments[0] if spec.instruments else None
        if inst:
            inst_range = INSTRUMENT_RANGES.get(inst.name)
            if inst_range:
                octave = (inst_range.midi_low + inst_range.midi_high) // 2 // 12

        cell = _generate_cell(root_note, scale_type, octave, rng, cell_length=4)

        prov.record(
            layer="generator",
            operation="start_generation",
            parameters={
                "title": spec.title,
                "strategy": "process_music",
                "seed": seed,
                "process_type": process_type,
                "cell_pitches": cell,
            },
            source="ProcessMusicGenerator.generate",
            rationale=f"Process music generation: {process_type} with cell {cell}.",
        )

        sections = self._generate_sections(
            spec,
            cell,
            process_type,
            root_note,
            scale_type,
            trajectory,
            prov,
            rng,
        )

        score = ScoreIR(
            title=spec.title,
            tempo_bpm=spec.tempo_bpm,
            time_signature=spec.time_signature,
            key=spec.key,
            sections=tuple(sections),
        )

        prov.record(
            layer="generator",
            operation="complete_generation",
            parameters={
                "total_notes": len(score.all_notes()),
                "total_bars": score.total_bars(),
                "process_type": process_type,
            },
            source="ProcessMusicGenerator.generate",
            rationale="Process music composition complete.",
        )

        return score, prov

    def _generate_sections(
        self,
        spec: CompositionSpec,
        cell: list[int],
        process_type: str,
        root_note: str,
        scale_type: str,
        trajectory: TrajectorySpec | None,
        prov: ProvenanceLog,
        rng: random.Random,
    ) -> list[Section]:
        """Generate all sections."""
        sections: list[Section] = []
        current_bar = 0

        for section_spec in spec.sections:
            parts: list[Part] = []
            velocity = DYNAMICS_TO_VELOCITY.get(section_spec.dynamics, 80)
            time_sig = section_spec.time_signature or spec.time_signature

            for instr_spec in spec.instruments:
                if process_type == "phasing":
                    notes = self._phasing(
                        cell,
                        instr_spec.name,
                        current_bar,
                        section_spec.bars,
                        time_sig,
                        velocity,
                        rng,
                    )
                elif process_type == "additive":
                    notes = self._additive(
                        cell,
                        instr_spec.name,
                        current_bar,
                        section_spec.bars,
                        time_sig,
                        velocity,
                    )
                else:
                    notes = self._subtractive(
                        cell,
                        instr_spec.name,
                        current_bar,
                        section_spec.bars,
                        time_sig,
                        velocity,
                    )
                parts.append(Part(instrument=instr_spec.name, notes=tuple(notes)))

            sections.append(
                Section(
                    name=section_spec.name,
                    start_bar=current_bar,
                    end_bar=current_bar + section_spec.bars,
                    parts=tuple(parts),
                )
            )
            current_bar += section_spec.bars

        return sections

    @staticmethod
    def _phasing(
        cell: list[int],
        instrument: str,
        start_bar: int,
        bars: int,
        time_sig: str,
        velocity: int,
        rng: random.Random,
    ) -> list[Note]:
        """Generate phasing process: cell repeats with gradual time shift."""
        beats_per_bar = bars_to_beats(1, time_sig)
        cell_dur = 1.0  # each cell note = 1 beat
        notes: list[Note] = []

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_sig)
            # Phase offset increases by a small amount each bar
            phase_offset = bar * 0.0625  # 1/16 beat per bar

            for i, pitch in enumerate(cell):
                if i >= int(beats_per_bar):
                    break
                beat = bar_start + i * cell_dur + phase_offset
                pitch = max(0, min(127, pitch))
                notes.append(
                    Note(
                        pitch=pitch,
                        start_beat=beat,
                        duration_beats=cell_dur * 0.85,
                        velocity=max(1, min(127, velocity)),
                        instrument=instrument,
                    )
                )

        return notes

    @staticmethod
    def _additive(
        cell: list[int],
        instrument: str,
        start_bar: int,
        bars: int,
        time_sig: str,
        velocity: int,
    ) -> list[Note]:
        """Generate additive process: cell grows by adding notes."""
        beats_per_bar = bars_to_beats(1, time_sig)
        notes: list[Note] = []

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_sig)
            # Number of active notes increases each bar
            active_count = min(bar + 1, len(cell))

            beat_offset: Beat = 0.0
            for i in range(active_count):
                if beat_offset + 1.0 > beats_per_bar + 0.001:
                    break
                pitch = max(0, min(127, cell[i % len(cell)]))
                notes.append(
                    Note(
                        pitch=pitch,
                        start_beat=bar_start + beat_offset,
                        duration_beats=0.85,
                        velocity=max(1, min(127, velocity)),
                        instrument=instrument,
                    )
                )
                beat_offset += 1.0

        return notes

    @staticmethod
    def _subtractive(
        cell: list[int],
        instrument: str,
        start_bar: int,
        bars: int,
        time_sig: str,
        velocity: int,
    ) -> list[Note]:
        """Generate subtractive process: cell shrinks by removing notes."""
        beats_per_bar = bars_to_beats(1, time_sig)
        notes: list[Note] = []

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_sig)
            # Number of active notes decreases each bar
            active_count = max(1, len(cell) - bar)

            beat_offset: Beat = 0.0
            for i in range(active_count):
                if beat_offset + 1.0 > beats_per_bar + 0.001:
                    break
                pitch = max(0, min(127, cell[i % len(cell)]))
                notes.append(
                    Note(
                        pitch=pitch,
                        start_beat=bar_start + beat_offset,
                        duration_beats=0.85,
                        velocity=max(1, min(127, velocity)),
                        instrument=instrument,
                    )
                )
                beat_offset += 1.0

        return notes
