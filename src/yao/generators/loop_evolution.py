"""Loop-evolution generator — layer-by-layer loop construction with modular arrangement.

Generates music by building a core loop and evolving it across sections through
layer additions, subtractions, and transformations. Supports arrangement strings
like "A B C drop A B C" for structural control.

Designed for genres where repetition + variation is the primary structure:
lo-fi hip-hop, deep house, ambient, drum and bass, trip-hop, etc.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.constants.music import CHORD_INTERVALS
from yao.errors import SpecValidationError
from yao.generators.base import GeneratorBase
from yao.generators.registry import register_generator
from yao.ir.notation import parse_key, scale_notes
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import bars_to_beats
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec, SectionSpec
from yao.schema.trajectory import TrajectorySpec
from yao.types import Beat, MidiNote, Velocity

# Default arrangement blocks
_DEFAULT_ARRANGEMENT = "A B C B"

# Rhythm pools for loop patterns (beat durations)
_LOOP_RHYTHM_POOL: list[list[float]] = [
    [1.0, 1.0, 1.0, 1.0],
    [1.5, 0.5, 1.0, 1.0],
    [0.5, 0.5, 0.5, 0.5, 1.0, 1.0],
    [2.0, 1.0, 1.0],
    [1.0, 0.5, 0.5, 2.0],
    [0.5, 1.5, 1.0, 1.0],
]

_BASS_LOOP_RHYTHM: list[list[float]] = [
    [2.0, 2.0],
    [1.0, 1.0, 2.0],
    [4.0],
    [1.5, 0.5, 2.0],
]


@dataclass(frozen=True)
class LoopEvolutionConfig:
    """Configuration for the loop-evolution generator.

    Attributes:
        core_loop_bars: Number of bars in the core loop (default 4).
        arrangement: Arrangement string (e.g., "A B C drop A B C").
        loopable: Whether the output should be seamlessly loopable.
        layer_add_probability: Probability of adding a layer in a new block.
        layer_remove_probability: Probability of removing a layer in a new block.
        melody_duration_factor: Articulation factor for melody notes.
        bass_duration_factor: Articulation factor for bass notes.
        chord_duration_factor: Articulation factor for chord notes.
        velocity_humanize_range: Random velocity offset range.
    """

    core_loop_bars: int = 4
    arrangement: str = _DEFAULT_ARRANGEMENT
    loopable: bool = True
    layer_add_probability: float = 0.4
    layer_remove_probability: float = 0.2
    melody_duration_factor: float = 0.85
    bass_duration_factor: float = 0.85
    chord_duration_factor: float = 0.90
    velocity_humanize_range: int = 5


@dataclass(frozen=True)
class ArrangementBlock:
    """A single block in the arrangement plan.

    Attributes:
        label: Block label (e.g., "A", "B", "drop").
        active_instruments: Instruments active in this block.
    """

    label: str
    active_instruments: tuple[str, ...]


def parse_arrangement(arrangement_str: str, all_instruments: list[str]) -> list[ArrangementBlock]:
    """Parse an arrangement string into blocks with layer assignments.

    Special tokens:
    - "drop" = only bass/rhythm (minimal instruments)
    - "build" = gradually add instruments
    - Letters (A, B, C, ...) = full or partial instrument sets

    Args:
        arrangement_str: Space-separated arrangement tokens.
        all_instruments: All available instrument names.

    Returns:
        List of ArrangementBlock objects.

    Raises:
        SpecValidationError: If arrangement string is empty.
    """
    tokens = arrangement_str.strip().split()
    if not tokens:
        raise SpecValidationError(
            "Arrangement string cannot be empty",
            field="generation.arrangement",
        )

    blocks: list[ArrangementBlock] = []

    for i, token in enumerate(tokens):
        token_upper = token.upper()

        if token_upper == "DROP":
            # Only keep bass and rhythm instruments
            active = [inst for inst in all_instruments if _is_rhythm_or_bass(inst)]
            if not active:
                # If no bass/rhythm, keep first instrument only
                active = all_instruments[:1] if all_instruments else []
            blocks.append(ArrangementBlock(label="drop", active_instruments=tuple(active)))
        elif token_upper == "BUILD":
            # Gradually add: start with 1 instrument, add one per repetition
            count = min(i + 1, len(all_instruments))
            active = all_instruments[:count]
            blocks.append(ArrangementBlock(label="build", active_instruments=tuple(active)))
        else:
            # Letter blocks: A = all, B = all, C = all (differentiated by variation)
            blocks.append(ArrangementBlock(label=token_upper, active_instruments=tuple(all_instruments)))

    return blocks


def _is_rhythm_or_bass(instrument: str) -> bool:
    """Check if an instrument name suggests a rhythm or bass role."""
    lower = instrument.lower()
    return any(keyword in lower for keyword in ("bass", "drum", "kick", "hat", "snare", "percussion"))


@register_generator("loop_evolution")
class LoopEvolutionGenerator(GeneratorBase):
    """Loop-evolution generator with modular arrangement.

    Builds a core loop and evolves it across blocks via layer additions,
    subtractions, and stochastic variation. Designed for loop-centric genres.
    """

    def __init__(self, config: LoopEvolutionConfig | None = None) -> None:
        """Initialize with optional configuration.

        Args:
            config: Generator configuration. Uses defaults if None.
        """
        self.config = config or LoopEvolutionConfig()

    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        """Generate a loop-based composition with modular arrangement.

        Args:
            spec: The composition specification.
            trajectory: Optional trajectory specification for dynamic shaping.

        Returns:
            Tuple of (ScoreIR, ProvenanceLog).
        """
        seed = spec.generation.seed if spec.generation.seed is not None else 42
        temperature = spec.generation.temperature
        rng = random.Random(seed)

        prov = ProvenanceLog()
        prov.record(
            layer="generator",
            operation="start_generation",
            parameters={
                "title": spec.title,
                "key": spec.key,
                "tempo": spec.tempo_bpm,
                "strategy": "loop_evolution",
                "seed": seed,
                "temperature": temperature,
                "core_loop_bars": self.config.core_loop_bars,
                "arrangement": self.config.arrangement,
                "loopable": self.config.loopable,
            },
            source="LoopEvolutionGenerator.generate",
            rationale=(
                f"Loop-evolution generation: {self.config.core_loop_bars}-bar loop "
                f"with arrangement '{self.config.arrangement}'."
            ),
        )

        root_note, scale_type = parse_key(spec.key)
        all_instruments = [instr.name for instr in spec.instruments]
        instrument_roles: dict[str, str] = {instr.name: instr.role for instr in spec.instruments}

        # Parse arrangement
        arrangement_str = self.config.arrangement
        blocks = parse_arrangement(arrangement_str, all_instruments)

        prov.record(
            layer="generator",
            operation="parse_arrangement",
            parameters={
                "arrangement": arrangement_str,
                "block_count": len(blocks),
                "block_labels": [b.label for b in blocks],
            },
            source="LoopEvolutionGenerator.generate",
            rationale=f"Arrangement parsed into {len(blocks)} blocks.",
        )

        # Generate core loop (one iteration per instrument)
        core_loops = self._generate_core_loops(
            spec=spec,
            root_note=root_note,
            scale_type=scale_type,
            rng=rng,
            temperature=temperature,
            provenance=prov,
        )

        # Build sections from arrangement blocks
        sections = self._build_sections_from_blocks(
            spec=spec,
            blocks=blocks,
            core_loops=core_loops,
            instrument_roles=instrument_roles,
            root_note=root_note,
            scale_type=scale_type,
            rng=rng,
            temperature=temperature,
            trajectory=trajectory,
            provenance=prov,
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
                "instruments": score.instruments(),
            },
            source="LoopEvolutionGenerator.generate",
            rationale="Loop-evolution generation complete.",
        )

        return score, prov

    def _generate_core_loops(
        self,
        *,
        spec: CompositionSpec,
        root_note: str,
        scale_type: str,
        rng: random.Random,
        temperature: float,
        provenance: ProvenanceLog,
    ) -> dict[str, list[Note]]:
        """Generate the core loop for each instrument.

        Args:
            spec: Composition specification.
            root_note: Root note name.
            scale_type: Scale type (major, minor, etc.).
            rng: Seeded RNG.
            temperature: Variation control.
            provenance: Provenance log.

        Returns:
            Dict mapping instrument name to core loop notes.
        """
        loops: dict[str, list[Note]] = {}
        loop_bars = self.config.core_loop_bars
        time_sig = spec.time_signature

        for instr_spec in spec.instruments:
            instr_rng = self._instrument_rng(spec.generation.seed or 42, instr_spec.name, "core_loop")
            notes = self._generate_loop_part(
                instrument=instr_spec.name,
                role=instr_spec.role,
                root_note=root_note,
                scale_type=scale_type,
                bars=loop_bars,
                start_bar=0,
                time_signature=time_sig,
                rng=instr_rng,
                temperature=temperature,
            )
            loops[instr_spec.name] = notes

        provenance.record(
            layer="generator",
            operation="generate_core_loops",
            parameters={
                "loop_bars": loop_bars,
                "instruments": list(loops.keys()),
                "notes_per_instrument": {k: len(v) for k, v in loops.items()},
            },
            source="LoopEvolutionGenerator._generate_core_loops",
            rationale=f"Core {loop_bars}-bar loops generated for all instruments.",
        )

        return loops

    def _generate_loop_part(
        self,
        *,
        instrument: str,
        role: str,
        root_note: str,
        scale_type: str,
        bars: int,
        start_bar: int,
        time_signature: str,
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate a loop part for a single instrument based on its role.

        Args:
            instrument: Instrument name.
            role: Instrument role (melody, bass, harmony, etc.).
            root_note: Root note name.
            scale_type: Scale type.
            bars: Number of bars.
            start_bar: Starting bar offset.
            time_signature: Time signature string.
            rng: Seeded RNG.
            temperature: Variation control.

        Returns:
            List of notes for the loop.
        """
        if role == "melody":
            return self._gen_melody_loop(
                instrument, root_note, scale_type, bars, start_bar, time_signature, rng, temperature
            )
        if role == "bass":
            return self._gen_bass_loop(
                instrument, root_note, scale_type, bars, start_bar, time_signature, rng, temperature
            )
        # harmony / pad / rhythm / counter_melody — generate chords
        return self._gen_chord_loop(
            instrument, root_note, scale_type, bars, start_bar, time_signature, rng, temperature
        )

    def _gen_melody_loop(
        self,
        instrument: str,
        root_note: str,
        scale_type: str,
        bars: int,
        start_bar: int,
        time_signature: str,
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate a melodic loop pattern."""
        octave = self._target_octave(instrument, "melody")
        all_scale = scale_notes(root_note, scale_type, octave)
        all_scale = all_scale + [n + 12 for n in all_scale]

        notes: list[Note] = []
        beats_per_bar = bars_to_beats(1, time_signature)
        scale_idx = len(all_scale) // 3

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            rhythm = rng.choice(_LOOP_RHYTHM_POOL)
            # Scale rhythm to fill bar
            total = sum(rhythm)
            scaled_rhythm = [r * beats_per_bar / total for r in rhythm]

            velocity = self._base_velocity(rng)

            beat_offset: Beat = 0.0
            for dur in scaled_rhythm:
                if beat_offset + dur > beats_per_bar + 0.001:
                    break

                # Step-wise movement with occasional leaps
                step = rng.choice([-2, -1, -1, 0, 1, 1, 2])
                if rng.random() < temperature * 0.2:
                    step = rng.choice([-4, -3, 3, 4])
                scale_idx = max(0, min(len(all_scale) - 1, scale_idx + step))

                pitch = all_scale[scale_idx]
                if not self._is_in_range(pitch, instrument):
                    scale_idx = max(0, min(len(all_scale) - 1, scale_idx - step * 2))
                    pitch = all_scale[scale_idx]
                    if not self._is_in_range(pitch, instrument):
                        beat_offset += dur
                        continue

                note = Note(
                    pitch=pitch,
                    start_beat=bar_start + beat_offset,
                    duration_beats=dur * self.config.melody_duration_factor,
                    velocity=max(1, min(127, velocity + rng.randint(-3, 3))),
                    instrument=instrument,
                )
                notes.append(note)
                beat_offset += dur

        return notes

    def _gen_bass_loop(
        self,
        instrument: str,
        root_note: str,
        scale_type: str,
        bars: int,
        start_bar: int,
        time_signature: str,
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate a bass loop pattern."""
        octave = self._target_octave(instrument, "bass")
        root_scale = scale_notes(root_note, scale_type, octave)

        notes: list[Note] = []
        beats_per_bar = bars_to_beats(1, time_signature)

        # Simple chord progression for the loop
        degrees = [0, 3, 4, 0] if len(root_scale) > 4 else [0, 0, 0, 0]  # noqa: PLR2004

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            degree = degrees[bar % len(degrees)]
            root_pitch = root_scale[degree % len(root_scale)]
            velocity = self._base_velocity(rng)

            rhythm = rng.choice(_BASS_LOOP_RHYTHM)
            total = sum(rhythm)
            scaled_rhythm = [r * beats_per_bar / total for r in rhythm]

            beat_offset: Beat = 0.0
            for i, dur in enumerate(scaled_rhythm):
                if beat_offset + dur > beats_per_bar + 0.001:
                    break
                pitch = root_pitch if i == 0 else root_pitch + rng.choice([0, 7, 5])
                while pitch > root_pitch + 12:
                    pitch -= 12

                if not self._is_in_range(pitch, instrument):
                    pitch = root_pitch

                note = Note(
                    pitch=pitch,
                    start_beat=bar_start + beat_offset,
                    duration_beats=dur * self.config.bass_duration_factor,
                    velocity=max(1, min(127, velocity)),
                    instrument=instrument,
                )
                notes.append(note)
                beat_offset += dur

        return notes

    def _gen_chord_loop(
        self,
        instrument: str,
        root_note: str,
        scale_type: str,
        bars: int,
        start_bar: int,
        time_signature: str,
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate a chord/harmony loop pattern."""
        octave = self._target_octave(instrument, "chord")
        root_scale = scale_notes(root_note, scale_type, octave)
        beats_per_bar = bars_to_beats(1, time_signature)

        degrees = [0, 3, 4, 0] if len(root_scale) > 4 else [0, 0, 0, 0]  # noqa: PLR2004
        notes: list[Note] = []

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            degree = degrees[bar % len(degrees)]
            root_pitch = root_scale[degree % len(root_scale)]
            velocity = max(1, self._base_velocity(rng) - 10)

            # Simple triad
            intervals = CHORD_INTERVALS.get("maj", [0, 4, 7])
            chord_pitches = [root_pitch + iv for iv in intervals]

            for pitch in chord_pitches:
                if self._is_in_range(pitch, instrument):
                    note = Note(
                        pitch=pitch,
                        start_beat=bar_start,
                        duration_beats=beats_per_bar * self.config.chord_duration_factor,
                        velocity=velocity,
                        instrument=instrument,
                    )
                    notes.append(note)

        return notes

    def _build_sections_from_blocks(
        self,
        *,
        spec: CompositionSpec,
        blocks: list[ArrangementBlock],
        core_loops: dict[str, list[Note]],
        instrument_roles: dict[str, str],
        root_note: str,
        scale_type: str,
        rng: random.Random,
        temperature: float,
        trajectory: TrajectorySpec | None,
        provenance: ProvenanceLog,
    ) -> list[Section]:
        """Build score sections from arrangement blocks.

        Each block becomes a section. The core loop is repeated/evolved
        to fill the section based on the spec's section definitions.

        Args:
            spec: Composition specification.
            blocks: Parsed arrangement blocks.
            core_loops: Core loop notes per instrument.
            instrument_roles: Role mapping.
            root_note: Root note name.
            scale_type: Scale type.
            rng: Seeded RNG.
            temperature: Variation control.
            trajectory: Optional trajectory.
            provenance: Provenance log.

        Returns:
            List of Section objects.
        """
        sections: list[Section] = []
        current_bar = 0
        loop_bars = self.config.core_loop_bars

        # If spec has explicit sections, use them; otherwise create from blocks
        section_specs = spec.sections or [SectionSpec(name=f"block_{i}", bars=loop_bars) for i in range(len(blocks))]

        for i, section_spec in enumerate(section_specs):
            block = blocks[i % len(blocks)]
            section_bars = section_spec.bars

            parts: list[Part] = []
            for instrument in block.active_instruments:
                if instrument not in core_loops:
                    continue

                core = core_loops[instrument]
                # Repeat and offset the loop to fill the section
                section_notes = self._repeat_loop(
                    core_notes=core,
                    loop_bars=loop_bars,
                    section_bars=section_bars,
                    section_start_bar=current_bar,
                    time_signature=spec.time_signature,
                    rng=rng,
                    temperature=temperature,
                    block_label=block.label,
                    block_index=i,
                )
                parts.append(Part(instrument=instrument, notes=tuple(section_notes)))

            provenance.record(
                layer="generator",
                operation="build_section",
                parameters={
                    "section_name": section_spec.name,
                    "block_label": block.label,
                    "bars": section_bars,
                    "active_instruments": list(block.active_instruments),
                    "note_count": sum(len(p.notes) for p in parts),
                },
                source="LoopEvolutionGenerator._build_sections_from_blocks",
                rationale=(
                    f"Section '{section_spec.name}' built from block '{block.label}' "
                    f"with {len(block.active_instruments)} active instruments."
                ),
            )

            sections.append(
                Section(
                    name=section_spec.name,
                    start_bar=current_bar,
                    end_bar=current_bar + section_bars,
                    parts=tuple(parts),
                )
            )
            current_bar += section_bars

        return sections

    def _repeat_loop(
        self,
        *,
        core_notes: list[Note],
        loop_bars: int,
        section_bars: int,
        section_start_bar: int,
        time_signature: str,
        rng: random.Random,
        temperature: float,
        block_label: str,
        block_index: int,
    ) -> list[Note]:
        """Repeat and evolve a core loop to fill a section.

        Args:
            core_notes: Notes in the core loop (starting at bar 0).
            loop_bars: Bars in one loop iteration.
            section_bars: Total bars to fill.
            section_start_bar: Starting bar of the section.
            time_signature: Time signature.
            rng: Seeded RNG.
            temperature: Variation control.
            block_label: Current block label for variation decisions.
            block_index: Index of block in arrangement.

        Returns:
            List of notes filling the section.
        """
        if not core_notes:
            return []

        loop_beats = bars_to_beats(loop_bars, time_signature)
        section_start_beat = bars_to_beats(section_start_bar, time_signature)
        section_total_beats = bars_to_beats(section_bars, time_signature)

        notes: list[Note] = []
        current_beat_offset: Beat = 0.0
        iteration = 0

        while current_beat_offset < section_total_beats - 0.001:
            for note in core_notes:
                new_start = section_start_beat + current_beat_offset + note.start_beat
                # Check if note fits within section
                if note.start_beat + current_beat_offset >= section_total_beats:
                    break

                # Apply variation based on iteration and block
                velocity = note.velocity
                pitch = note.pitch

                # Subtle velocity variation per iteration
                if iteration > 0 and temperature > 0.2:
                    vel_offset = rng.randint(
                        -self.config.velocity_humanize_range,
                        self.config.velocity_humanize_range,
                    )
                    velocity = max(1, min(127, velocity + vel_offset))

                new_note = Note(
                    pitch=pitch,
                    start_beat=new_start,
                    duration_beats=note.duration_beats,
                    velocity=velocity,
                    instrument=note.instrument,
                )
                notes.append(new_note)

            current_beat_offset += loop_beats
            iteration += 1

        return notes

    def _base_velocity(self, rng: random.Random) -> Velocity:
        """Generate a base velocity with slight humanization.

        Args:
            rng: Seeded RNG.

        Returns:
            Velocity value in valid MIDI range.
        """
        return max(1, min(127, 80 + rng.randint(-5, 5)))

    def _target_octave(self, instrument: str, role: str) -> int:
        """Choose octave based on instrument range and role.

        Args:
            instrument: Instrument name.
            role: Musical role.

        Returns:
            Target octave number.
        """
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return {"melody": 5, "bass": 2, "chord": 4}.get(role, 4)
        if role == "bass":
            low_octave = (inst_range.midi_low // 12) - 1
            return low_octave + 1
        if role == "melody":
            mid = (inst_range.midi_low + inst_range.midi_high * 2) // 3
            return (mid // 12) - 1
        mid = (inst_range.midi_low + inst_range.midi_high) // 2
        return (mid // 12) - 1

    def _is_in_range(self, pitch: MidiNote, instrument: str) -> bool:
        """Check if pitch is within instrument range.

        Args:
            pitch: MIDI pitch.
            instrument: Instrument name.

        Returns:
            True if in range.
        """
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return 0 <= pitch <= 127
        return inst_range.midi_low <= pitch <= inst_range.midi_high

    def _instrument_rng(self, master_seed: int, instrument: str, section: str) -> random.Random:
        """Create a deterministic per-instrument RNG.

        Args:
            master_seed: The master seed from the spec.
            instrument: Instrument name.
            section: Section name.

        Returns:
            A new Random instance with a derived seed.
        """
        combined = f"{master_seed}:{instrument}:{section}"
        derived_seed = int(hashlib.sha256(combined.encode()).hexdigest()[:8], 16)
        return random.Random(derived_seed)
