"""Twelve-tone serial generator — Schoenberg-style pitch class row manipulation.

Generates compositions by systematically transforming a 12-pitch-class row
through its 4 standard forms: Prime (P), Inversion (I), Retrograde (R),
and Retrograde-Inversion (RI).

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.constants.music import DYNAMICS_TO_VELOCITY
from yao.generators.base import GeneratorBase
from yao.generators.registry import register_generator
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import bars_to_beats
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec, SectionSpec
from yao.schema.trajectory import TrajectorySpec
from yao.types import Beat

# Rhythm patterns for serial music (quarter-note based)
_SERIAL_RHYTHMS: list[list[float]] = [
    [1.0, 1.0, 1.0, 1.0],
    [2.0, 1.0, 1.0],
    [1.0, 2.0, 1.0],
    [1.0, 1.0, 2.0],
    [2.0, 2.0],
    [1.5, 0.5, 1.0, 1.0],
    [1.0, 0.5, 0.5, 1.0, 1.0],
    [3.0, 1.0],
    [1.0, 3.0],
]

# Default row pattern cycle per section
_DEFAULT_ROW_PATTERN = ["P", "I", "R", "RI"]


def generate_row(rng: random.Random) -> list[int]:
    """Generate a random 12-tone row (permutation of 0-11).

    Args:
        rng: Seeded RNG.

    Returns:
        List of 12 unique pitch classes (0-11).
    """
    row = list(range(12))
    rng.shuffle(row)
    return row


def prime(row: list[int]) -> list[int]:
    """Return the Prime form (original row)."""
    return list(row)


def inversion(row: list[int]) -> list[int]:
    """Return the Inversion: intervals reversed in direction."""
    if not row:
        return []
    first = row[0]
    return [(2 * first - pc) % 12 for pc in row]


def retrograde(row: list[int]) -> list[int]:
    """Return the Retrograde: row reversed."""
    return list(reversed(row))


def retrograde_inversion(row: list[int]) -> list[int]:
    """Return the Retrograde-Inversion."""
    return retrograde(inversion(row))


_TRANSFORMS = {
    "P": prime,
    "I": inversion,
    "R": retrograde,
    "RI": retrograde_inversion,
}


@register_generator("twelve_tone")
class TwelveToneSerialGenerator(GeneratorBase):
    """12-tone serial composition generator.

    Uses a pitch-class row and its 4 transformations to generate
    atonal compositions following serial technique principles.
    """

    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        """Generate a serial composition.

        Args:
            spec: Composition specification.
            trajectory: Optional trajectory.

        Returns:
            Tuple of (ScoreIR, ProvenanceLog).
        """
        seed = spec.generation.seed if spec.generation.seed is not None else 42
        temperature = spec.generation.temperature
        rng = random.Random(seed)

        prov = ProvenanceLog()

        # Generate or use provided row
        row = generate_row(rng)

        prov.record(
            layer="generator",
            operation="start_generation",
            parameters={
                "title": spec.title,
                "strategy": "twelve_tone",
                "seed": seed,
                "row": row,
            },
            source="TwelveToneSerialGenerator.generate",
            rationale=f"12-tone serial generation with row {row}, seed={seed}.",
        )

        sections = self._generate_sections(spec, row, trajectory, prov, rng, temperature)

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
            },
            source="TwelveToneSerialGenerator.generate",
            rationale="12-tone serial composition complete.",
        )

        return score, prov

    def _generate_sections(
        self,
        spec: CompositionSpec,
        row: list[int],
        trajectory: TrajectorySpec | None,
        prov: ProvenanceLog,
        rng: random.Random,
        temperature: float,
    ) -> list[Section]:
        """Generate all sections using row transformations."""
        sections: list[Section] = []
        current_bar = 0

        for sec_idx, section_spec in enumerate(spec.sections):
            # Cycle through P, I, R, RI
            transform_name = _DEFAULT_ROW_PATTERN[sec_idx % len(_DEFAULT_ROW_PATTERN)]
            transform_fn = _TRANSFORMS[transform_name]
            transformed_row = transform_fn(row)

            parts: list[Part] = []
            for instr_spec in spec.instruments:
                notes = self._generate_part(
                    instrument=instr_spec.name,
                    role=instr_spec.role,
                    row=transformed_row,
                    start_bar=current_bar,
                    bars=section_spec.bars,
                    time_signature=section_spec.time_signature or spec.time_signature,
                    section_spec=section_spec,
                    trajectory=trajectory,
                    rng=rng,
                    temperature=temperature,
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

            prov.record(
                layer="generator",
                operation="generate_section",
                parameters={
                    "section": section_spec.name,
                    "transform": transform_name,
                    "row": transformed_row,
                },
                source="TwelveToneSerialGenerator._generate_sections",
                rationale=f"Section '{section_spec.name}' uses {transform_name} form.",
            )

            current_bar += section_spec.bars

        return sections

    def _generate_part(
        self,
        *,
        instrument: str,
        role: str,
        row: list[int],
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate notes for one instrument part using row pitches."""
        octave = self._target_octave(instrument, role)
        beats_per_bar = bars_to_beats(1, time_signature)
        velocity = DYNAMICS_TO_VELOCITY.get(section_spec.dynamics, 80)

        notes: list[Note] = []
        row_idx = 0

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            rhythm = rng.choice(_SERIAL_RHYTHMS)

            beat_offset: Beat = 0.0
            for dur in rhythm:
                if beat_offset + dur > beats_per_bar + 0.001:
                    break

                pc = row[row_idx % len(row)]
                row_idx += 1

                # Place in target octave
                pitch = octave * 12 + pc
                pitch = max(0, min(127, pitch))

                # Clamp to instrument range
                inst_range = INSTRUMENT_RANGES.get(instrument)
                if inst_range is not None:
                    pitch = max(inst_range.midi_low, min(inst_range.midi_high, pitch))

                # Velocity variation
                vel_mod = rng.randint(-5, 5) if temperature > 0.3 else 0
                final_vel = max(1, min(127, velocity + vel_mod))

                notes.append(
                    Note(
                        pitch=pitch,
                        start_beat=bar_start + beat_offset,
                        duration_beats=dur * 0.85,
                        velocity=final_vel,
                        instrument=instrument,
                    )
                )
                beat_offset += dur

        return notes

    @staticmethod
    def _target_octave(instrument: str, role: str) -> int:
        """Choose octave based on role."""
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return {"melody": 5, "bass": 3, "harmony": 4}.get(role, 4)
        mid = (inst_range.midi_low + inst_range.midi_high) // 2
        return mid // 12
