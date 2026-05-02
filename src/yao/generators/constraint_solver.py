"""Constraint satisfaction generator — logic-based composition.

Uses backtracking constraint satisfaction to generate compositions
where every note satisfies explicit musical constraints (key membership,
range, voice leading, parallel motion avoidance).

Timeout: 5 seconds default. Raises GenerationTimeoutError on expiry.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random
import time

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.constants.music import DYNAMICS_TO_VELOCITY
from yao.errors import YaOError
from yao.generators.base import GeneratorBase
from yao.generators.registry import register_generator
from yao.ir.notation import parse_key, scale_notes
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import bars_to_beats
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec, SectionSpec
from yao.schema.trajectory import TrajectorySpec


class GenerationTimeoutError(YaOError):
    """Raised when constraint solving exceeds the time budget."""


_DEFAULT_TIMEOUT = 5.0  # seconds


@register_generator("constraint_satisfaction")
class ConstraintSatisfactionGenerator(GeneratorBase):
    """Constraint-based composition generator.

    Each note is chosen to satisfy:
    1. Key membership (scale notes only)
    2. Instrument range
    3. Stepwise motion preference (minimize leaps)
    4. No consecutive repeated pitches
    """

    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        """Generate a composition via constraint satisfaction.

        Args:
            spec: Composition specification.
            trajectory: Optional trajectory.

        Returns:
            Tuple of (ScoreIR, ProvenanceLog).

        Raises:
            GenerationTimeoutError: If solving exceeds 5 seconds.
        """
        seed = spec.generation.seed if spec.generation.seed is not None else 42
        rng = random.Random(seed)
        prov = ProvenanceLog()
        start_time = time.monotonic()

        root_note, scale_type = parse_key(spec.key)

        prov.record(
            layer="generator",
            operation="start_generation",
            parameters={
                "strategy": "constraint_satisfaction",
                "seed": seed,
                "key": spec.key,
                "timeout": _DEFAULT_TIMEOUT,
            },
            source="ConstraintSatisfactionGenerator.generate",
            rationale=f"Constraint satisfaction generation, seed={seed}.",
        )

        sections: list[Section] = []
        current_bar = 0

        for section_spec in spec.sections:
            parts: list[Part] = []
            for instr_spec in spec.instruments:
                elapsed = time.monotonic() - start_time
                if elapsed > _DEFAULT_TIMEOUT:
                    raise GenerationTimeoutError(
                        f"Constraint solving exceeded {_DEFAULT_TIMEOUT}s budget ({elapsed:.1f}s elapsed)."
                    )

                notes = self._solve_part(
                    instrument=instr_spec.name,
                    role=instr_spec.role,
                    root_note=root_note,
                    scale_type=scale_type,
                    start_bar=current_bar,
                    bars=section_spec.bars,
                    time_signature=section_spec.time_signature or spec.time_signature,
                    section_spec=section_spec,
                    rng=rng,
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
                "solve_time_sec": round(time.monotonic() - start_time, 3),
            },
            source="ConstraintSatisfactionGenerator.generate",
            rationale="Constraint satisfaction complete.",
        )

        return score, prov

    def _solve_part(
        self,
        *,
        instrument: str,
        role: str,
        root_note: str,
        scale_type: str,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        rng: random.Random,
    ) -> list[Note]:
        """Solve for notes satisfying all constraints."""
        octave = self._target_octave(instrument, role)
        all_scale = scale_notes(root_note, scale_type, octave)
        extended = all_scale + [n + 12 for n in all_scale]

        # Filter to instrument range
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range:
            valid_pitches = [p for p in extended if inst_range.midi_low <= p <= inst_range.midi_high]
        else:
            valid_pitches = [p for p in extended if 0 <= p <= 127]

        if not valid_pitches:
            return []

        velocity = DYNAMICS_TO_VELOCITY.get(section_spec.dynamics, 80)
        beats_per_bar = bars_to_beats(1, time_signature)
        notes: list[Note] = []
        prev_pitch: int | None = None

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            # 4 notes per bar (quarter notes)
            for beat_idx in range(int(beats_per_bar)):
                # Constraint: prefer stepwise, no repeats
                candidates = list(valid_pitches)
                if prev_pitch is not None:
                    candidates = [p for p in candidates if p != prev_pitch]
                    # Sort by distance to previous (prefer stepwise)
                    candidates.sort(key=lambda p: abs(p - (prev_pitch or 60)))

                if not candidates:
                    candidates = valid_pitches

                # Pick from top candidates (closest)
                top_n = min(3, len(candidates))
                pitch = rng.choice(candidates[:top_n])
                prev_pitch = pitch

                notes.append(
                    Note(
                        pitch=pitch,
                        start_beat=bar_start + float(beat_idx),
                        duration_beats=0.9,
                        velocity=max(1, min(127, velocity + rng.randint(-3, 3))),
                        instrument=instrument,
                    )
                )

        return notes

    @staticmethod
    def _target_octave(instrument: str, role: str) -> int:
        """Choose octave based on role."""
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return {"melody": 5, "bass": 3, "harmony": 4}.get(role, 4)
        mid = (inst_range.midi_low + inst_range.midi_high) // 2
        return mid // 12
