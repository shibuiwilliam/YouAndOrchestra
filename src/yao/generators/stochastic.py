"""Stochastic generator — controlled randomness for musically varied compositions.

Extends the rule-based approach with:
- Melodic contour shaping (arch, ascending, descending, wave)
- Interval variety (leaps, steps, rests)
- Section-aware chord progressions (verse/chorus/bridge patterns)
- Diatonic 7th chords
- Rhythmic variety with syncopation and dotted rhythms
- Walking bass patterns
- Seed + temperature for reproducible variation

Same spec + different seed = different composition.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.constants.music import CHORD_INTERVALS, DYNAMICS_TO_VELOCITY
from yao.generators.base import GeneratorBase
from yao.generators.registry import register_generator
from yao.ir.motif import Motif, invert, retrograde, transpose
from yao.ir.notation import parse_key, scale_notes
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import bars_to_beats
from yao.reflect.provenance import ProvenanceLog
from yao.reflect.recoverable import RecoverableDecision
from yao.schema.composition import CompositionSpec, SectionSpec
from yao.schema.trajectory import TrajectorySpec
from yao.types import Beat, MidiNote, Velocity

# Section-aware chord degree patterns (0-indexed scale degrees)
_CHORD_PATTERNS: dict[str, list[list[int]]] = {
    "intro": [[0, 4], [0, 3, 4, 0]],
    "verse": [[0, 5, 3, 4], [0, 2, 3, 4], [0, 5, 1, 4]],
    "chorus": [[0, 4, 5, 3], [3, 0, 3, 4], [0, 3, 5, 4]],
    "bridge": [[1, 4, 0, 0], [5, 3, 1, 4], [3, 1, 4, 0]],
    "outro": [[3, 4, 0, 0], [0, 3, 4, 0]],
    "default": [[0, 3, 4, 0], [0, 5, 3, 4], [0, 4, 5, 3]],
}

# Rhythm patterns (in beats) — much more varied than rule_based
_MELODY_RHYTHM_POOL: list[list[float]] = [
    [1.0, 1.0, 1.0, 1.0],  # straight quarters
    [2.0, 1.0, 1.0],  # half + quarters
    [1.0, 1.0, 2.0],  # quarters + half
    [1.5, 0.5, 1.0, 1.0],  # dotted quarter + eighth + quarters
    [1.0, 0.5, 0.5, 1.0, 1.0],  # quarter + eighths + quarters
    [0.5, 0.5, 0.5, 0.5, 1.0, 1.0],  # four eighths + two quarters
    [1.0, 1.0, 0.5, 0.5, 1.0],  # syncopated
    [2.0, 2.0],  # two halves (spacious)
    [1.5, 1.5, 1.0],  # dotted feel
    [0.5, 1.5, 1.0, 1.0],  # pickup eighth
    [1.0, 0.5, 0.5, 0.5, 0.5, 1.0],  # mixed
    [3.0, 1.0],  # dotted half + quarter
]

_BASS_RHYTHM_POOL: list[list[float]] = [
    [4.0],  # whole note
    [2.0, 2.0],  # two halves
    [2.0, 1.0, 1.0],  # half + quarters
    [1.0, 1.0, 2.0],  # root-fifth pattern
    [1.0, 1.0, 1.0, 1.0],  # walking quarters
    [1.5, 0.5, 2.0],  # dotted + short + long
]

# Rhythm-role patterns: short, percussive, subdivided
_RHYTHM_PART_POOL: list[list[float]] = [
    [0.5] * 8,  # straight eighths
    [0.5, 0.5, 1.0, 0.5, 0.5, 1.0],  # syncopated eighths
    [1.0, 0.5, 0.5, 1.0, 0.5, 0.5],  # offbeat emphasis
    [0.5, 1.5, 0.5, 1.5],  # dotted quarter feel
    [0.5, 0.5, 0.5, 0.5, 2.0],  # run into hold
    [1.0, 0.5, 0.5, 0.5, 0.5, 1.0],  # mixed subdivisions
]

# Pad patterns: long sustained notes
_PAD_RHYTHM_POOL: list[list[float]] = [
    [4.0],  # whole note
    [2.0, 2.0],  # two halves
]


@dataclass(frozen=True)
class StochasticConfig:
    """Configurable parameters for the stochastic generator.

    These were previously hardcoded throughout the generator.
    Centralizing them makes tuning easier and behaviour auditable.
    """

    melody_duration_factor: float = 0.85
    bass_duration_factor: float = 0.85
    chord_duration_factor: float = 0.85
    pad_duration_factor: float = 0.95
    rhythm_duration_factor: float = 0.5
    rest_probability_scale: float = 0.15
    chord_velocity_offset: int = -10
    pad_velocity_offset: int = -20
    velocity_humanize_range: int = 5
    downbeat_accent: int = 10
    offbeat_accent: int = -5
    low_temp_threshold: float = 0.3
    seventh_chord_probability_scale: float = 0.4
    dominant_seventh_probability_scale: float = 0.5
    tension_velocity_scale: float = 0.4


@register_generator("stochastic")
class StochasticGenerator(GeneratorBase):
    """Stochastic composition generator with controlled randomness.

    Uses seed for reproducibility and temperature for variation control.
    Temperature 0.0 = nearly deterministic, 1.0 = maximum variety.
    """

    _provenance: ProvenanceLog
    config: StochasticConfig = StochasticConfig()

    def _record_recovery(
        self,
        code: str,
        severity: str,
        original: object,
        recovered: object,
        reason: str,
        impact: str,
        fix: list[str] | None = None,
    ) -> None:
        """Record a RecoverableDecision on the current provenance log."""
        decision = RecoverableDecision(
            code=code,
            severity=severity,  # type: ignore[arg-type]
            original_value=original,
            recovered_value=recovered,
            reason=reason,
            musical_impact=impact,
            suggested_fix=fix or [],
        )
        self._provenance.record_recoverable(decision)

    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        """Generate a composition with controlled randomness.

        Args:
            spec: The composition specification.
            trajectory: Optional trajectory for dynamic shaping.

        Returns:
            Tuple of (ScoreIR, ProvenanceLog).
        """
        seed = spec.generation.seed if spec.generation.seed is not None else 42
        temperature = spec.generation.temperature
        rng = random.Random(seed)

        prov = ProvenanceLog()
        self._provenance = prov
        prov.record(
            layer="generator",
            operation="start_generation",
            parameters={
                "title": spec.title,
                "key": spec.key,
                "tempo": spec.tempo_bpm,
                "strategy": "stochastic",
                "seed": seed,
                "temperature": temperature,
            },
            source="StochasticGenerator.generate",
            rationale=f"Stochastic generation with seed={seed}, temperature={temperature}.",
        )

        root_note, scale_type = parse_key(spec.key)
        sections = self._generate_sections(
            spec=spec,
            root_note=root_note,
            scale_type=scale_type,
            trajectory=trajectory,
            provenance=prov,
            rng=rng,
            seed=seed,
            temperature=temperature,
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
            source="StochasticGenerator.generate",
            rationale="Stochastic composition generation complete.",
        )

        return score, prov

    def _generate_sections(
        self,
        *,
        spec: CompositionSpec,
        root_note: str,
        scale_type: str,
        trajectory: TrajectorySpec | None,
        provenance: ProvenanceLog,
        rng: random.Random,
        seed: int,
        temperature: float,
    ) -> list[Section]:
        """Generate all sections with controlled randomness."""
        sections: list[Section] = []
        current_bar = 0

        for section_spec in spec.sections:
            section_start = current_bar
            section_end = current_bar + section_spec.bars

            # Choose chord pattern for this section type (master RNG for section-level)
            chord_pattern = self._choose_chord_pattern(section_spec.name, rng, temperature)

            parts: list[Part] = []
            # Track melody instruments for motif-based differentiation
            melody_instruments = [i for i in spec.instruments if i.role == "melody"]
            primary_melody_notes: list[Note] | None = None

            for instr_spec in spec.instruments:
                # Per-instrument RNG for decorrelated output
                instr_rng = self._instrument_rng(seed, instr_spec.name, section_spec.name)

                # For 2nd+ melody instrument, use motif transformations
                melody_index = (
                    melody_instruments.index(instr_spec)
                    if instr_spec in melody_instruments
                    else -1
                )
                if melody_index > 0 and primary_melody_notes:
                    notes = self._generate_melody_from_motif(
                        seed_notes=primary_melody_notes,
                        instrument=instr_spec.name,
                        melody_index=melody_index,
                        start_bar=section_start,
                        bars=section_spec.bars,
                        time_signature=section_spec.time_signature or spec.time_signature,
                        section_spec=section_spec,
                        trajectory=trajectory,
                        rng=instr_rng,
                    )
                else:
                    notes = self._generate_part(
                        instrument=instr_spec.name,
                        role=instr_spec.role,
                        root_note=root_note,
                        scale_type=scale_type,
                        start_bar=section_start,
                        bars=section_spec.bars,
                        time_signature=section_spec.time_signature or spec.time_signature,
                        section_spec=section_spec,
                        trajectory=trajectory,
                        chord_pattern=chord_pattern,
                        rng=instr_rng,
                        temperature=temperature,
                    )
                    # Capture first melody instrument's output
                    if melody_index == 0:
                        primary_melody_notes = notes

                parts.append(Part(instrument=instr_spec.name, notes=tuple(notes)))

            provenance.record(
                layer="generator",
                operation="generate_section",
                parameters={
                    "section": section_spec.name,
                    "bars": section_spec.bars,
                    "chord_pattern": chord_pattern,
                    "note_count": sum(len(p.notes) for p in parts),
                },
                source="StochasticGenerator._generate_sections",
                rationale=(
                    f"Section '{section_spec.name}' with chord degrees {chord_pattern}. "
                    f"Pattern selected based on section type and temperature={temperature:.1f}."
                ),
            )

            sections.append(
                Section(
                    name=section_spec.name,
                    start_bar=section_start,
                    end_bar=section_end,
                    parts=tuple(parts),
                )
            )
            current_bar = section_end

        return sections

    def _choose_chord_pattern(
        self, section_name: str, rng: random.Random, temperature: float
    ) -> list[int]:
        """Choose a chord degree pattern appropriate for the section type."""
        patterns = _CHORD_PATTERNS.get(section_name, _CHORD_PATTERNS["default"])
        if temperature < 0.2:  # noqa: PLR2004
            return patterns[0]
        return rng.choice(patterns)

    def _generate_part(
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
        trajectory: TrajectorySpec | None,
        chord_pattern: list[int],
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate notes for one instrument part."""
        if role == "melody":
            return self._generate_melody(
                instrument=instrument,
                root_note=root_note,
                scale_type=scale_type,
                start_bar=start_bar,
                bars=bars,
                time_signature=time_signature,
                section_spec=section_spec,
                trajectory=trajectory,
                chord_pattern=chord_pattern,
                rng=rng,
                temperature=temperature,
            )
        if role == "bass":
            return self._generate_bass(
                instrument=instrument,
                root_note=root_note,
                scale_type=scale_type,
                start_bar=start_bar,
                bars=bars,
                time_signature=time_signature,
                section_spec=section_spec,
                trajectory=trajectory,
                chord_pattern=chord_pattern,
                rng=rng,
                temperature=temperature,
            )
        if role == "pad":
            return self._generate_pad(
                instrument=instrument,
                root_note=root_note,
                scale_type=scale_type,
                start_bar=start_bar,
                bars=bars,
                time_signature=time_signature,
                section_spec=section_spec,
                trajectory=trajectory,
                chord_pattern=chord_pattern,
                rng=rng,
                temperature=temperature,
            )
        if role == "rhythm":
            return self._generate_rhythm(
                instrument=instrument,
                root_note=root_note,
                scale_type=scale_type,
                start_bar=start_bar,
                bars=bars,
                time_signature=time_signature,
                section_spec=section_spec,
                trajectory=trajectory,
                chord_pattern=chord_pattern,
                rng=rng,
                temperature=temperature,
            )
        # harmony (default)
        return self._generate_chords(
            instrument=instrument,
            root_note=root_note,
            scale_type=scale_type,
            start_bar=start_bar,
            bars=bars,
            time_signature=time_signature,
            section_spec=section_spec,
            trajectory=trajectory,
            chord_pattern=chord_pattern,
            rng=rng,
            temperature=temperature,
        )

    def _generate_melody(
        self,
        *,
        instrument: str,
        root_note: str,
        scale_type: str,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        chord_pattern: list[int],
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate melody with contour shaping and interval variety."""
        octave = self._target_octave(instrument, "melody")
        all_scale = scale_notes(root_note, scale_type, octave)
        # Extend to span 2 octaves for melodic range
        all_scale = all_scale + [n + 12 for n in all_scale]

        notes: list[Note] = []
        beats_per_bar = bars_to_beats(1, time_signature)
        scale_idx = len(all_scale) // 3  # start in lower-middle

        # Select contour for this section
        contour = self._choose_contour(section_spec.name, temperature, rng)

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            rhythm = rng.choice(_MELODY_RHYTHM_POOL)
            velocity = self._compute_velocity(section_spec, start_bar + bar, trajectory)

            # Occasional rest (temperature-dependent)
            if rng.random() < temperature * self.config.rest_probability_scale:
                self._record_recovery(
                    "REST_INSERTED", "info",
                    f"bar {start_bar + bar}", "rest",
                    "Stochastic rest for natural phrasing",
                    "One fewer bar of melody, creates breathing space",
                )
                continue

            beat_offset: Beat = 0.0
            for dur in rhythm:
                if beat_offset + dur > beats_per_bar + 0.001:
                    break

                # Movement: step, leap, or repeat (temperature controls leap probability)
                movement = self._choose_movement(rng, temperature, bar, bars, contour)
                scale_idx = max(0, min(len(all_scale) - 1, scale_idx + movement))

                pitch = all_scale[scale_idx]
                if not self._is_in_range(pitch, instrument):
                    # Bounce back into range
                    original_pitch = pitch
                    scale_idx = max(0, min(len(all_scale) - 1, scale_idx - movement * 2))
                    pitch = all_scale[scale_idx]
                    if not self._is_in_range(pitch, instrument):
                        self._record_recovery(
                            "MELODY_NOTE_SKIPPED", "warning",
                            original_pitch, None,
                            f"Melody pitch {original_pitch} outside {instrument} range",
                            "One note missing from melody, slight gap in phrase",
                            ["widen instrument range", "adjust melody octave"],
                        )
                        beat_offset += dur
                        continue
                    self._record_recovery(
                        "MELODY_NOTE_OUT_OF_RANGE", "info",
                        original_pitch, pitch,
                        f"Melody pitch {original_pitch} bounced to {pitch}",
                        "Melodic contour slightly altered at this point",
                    )

                # Velocity humanization
                vel_variation = rng.randint(-5, 5) if temperature > 0.3 else 0  # noqa: PLR2004
                raw_vel = velocity + vel_variation
                final_vel = max(1, min(127, raw_vel))
                if final_vel != raw_vel:
                    self._record_recovery(
                        "VELOCITY_CLAMPED", "info",
                        raw_vel, final_vel,
                        f"Velocity {raw_vel} clamped to MIDI range",
                        "Negligible — within normal humanization range",
                    )

                note = Note(
                    pitch=pitch,
                    start_beat=bar_start + beat_offset,
                    duration_beats=dur * self.config.melody_duration_factor,
                    velocity=final_vel,
                    instrument=instrument,
                )
                notes.append(note)
                beat_offset += dur

        return notes

    def _generate_melody_from_motif(
        self,
        *,
        seed_notes: list[Note],
        instrument: str,
        melody_index: int,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        rng: random.Random,
    ) -> list[Note]:
        """Generate a melody derived from the primary melody via motif transformations.

        Uses inversion, retrograde, and transposition from yao.ir.motif to
        create related but distinct melodic lines for 2nd+ melody instruments.

        Args:
            seed_notes: Notes from the primary melody instrument.
            instrument: Target instrument name.
            melody_index: 1-based index of this melody instrument (1=2nd melody, 2=3rd, etc).
            start_bar: Starting bar number.
            bars: Number of bars.
            time_signature: Time signature string.
            section_spec: Section specification.
            trajectory: Optional trajectory.
            rng: Per-instrument RNG.

        Returns:
            List of transformed notes for this instrument.
        """
        if not seed_notes:
            return []

        # Build motif from seed notes
        seed_motif = Motif(notes=tuple(seed_notes), label="primary_melody")

        # Apply transformation based on melody index
        transformations = [invert, retrograde]
        transform_fn = transformations[(melody_index - 1) % len(transformations)]
        transformed = transform_fn(seed_motif)

        # Determine target octave range for this instrument
        target_octave = self._target_octave(instrument, "melody")
        target_center = target_octave * 12 + 12 + 6  # center of target octave (MIDI)

        # Calculate pitch shift to move transformed notes into target range
        if transformed.notes:
            current_center = sum(n.pitch for n in transformed.notes) // len(transformed.notes)
            shift = target_center - current_center
            # Round to nearest octave to stay in key
            shift = round(shift / 12) * 12
            if shift != 0:
                transformed = transpose(transformed, shift)

        # Re-assign instrument and clamp to range
        result: list[Note] = []
        for note in transformed.notes:
            pitch = note.pitch
            if not self._is_in_range(pitch, instrument):
                original_pitch = pitch
                # Try octave adjustments
                if self._is_in_range(pitch + 12, instrument):
                    pitch = pitch + 12
                elif self._is_in_range(pitch - 12, instrument):
                    pitch = pitch - 12
                else:
                    self._record_recovery(
                        "MOTIF_NOTE_OUT_OF_RANGE", "warning",
                        original_pitch, None,
                        f"Transformed motif note {original_pitch} outside {instrument} range",
                        "Note dropped from transformed motif",
                        ["adjust motif transposition interval", "use instrument with wider range"],
                    )
                    continue
                self._record_recovery(
                    "MOTIF_NOTE_OUT_OF_RANGE", "info",
                    original_pitch, pitch,
                    f"Motif note {original_pitch} octave-adjusted to {pitch}",
                    "Slight register shift in transformed melody",
                )

            velocity = self._compute_velocity(section_spec, start_bar, trajectory)
            vel_variation = rng.randint(-5, 5)
            final_vel = max(1, min(127, velocity + vel_variation))

            result.append(
                Note(
                    pitch=pitch,
                    start_beat=note.start_beat,
                    duration_beats=note.duration_beats,
                    velocity=final_vel,
                    instrument=instrument,
                )
            )

        return result

    # Section name → preferred contour mapping.
    # At low temperature (<0.3), arch is always used for predictability.
    _SECTION_CONTOURS: dict[str, str] = {
        "intro": "arch",
        "verse": "arch",
        "chorus": "ascending",
        "bridge": "wave",
        "outro": "descending",
        "solo": "ascending",
        "default": "arch",
    }

    def _choose_contour(
        self, section_name: str, temperature: float, rng: random.Random
    ) -> str:
        """Select melodic contour type based on section and temperature.

        Args:
            section_name: Section identifier (intro, verse, chorus, etc.).
            temperature: Variation control (low = conservative).
            rng: Seeded RNG for reproducibility.

        Returns:
            Contour type string: arch, ascending, descending, or wave.
        """
        # Low temperature = always arch for predictability
        if temperature < self.config.low_temp_threshold:
            return "arch"

        preferred = self._SECTION_CONTOURS.get(
            section_name, self._SECTION_CONTOURS["default"]
        )

        # Higher temperature = chance of random contour
        if rng.random() < temperature * 0.3:
            return rng.choice(["arch", "ascending", "descending", "wave"])
        return preferred

    def _choose_movement(
        self,
        rng: random.Random,
        temperature: float,
        bar: int,
        total_bars: int,
        contour: str = "arch",
    ) -> int:
        """Choose melodic movement based on position, temperature, and contour.

        Contour shapes bias direction probability without forcing it,
        producing natural direction changes.

        Args:
            rng: Seeded RNG.
            temperature: Variation control.
            bar: Current bar within section.
            total_bars: Total bars in section.
            contour: Contour type (arch, ascending, descending, wave).

        Returns:
            Signed step in scale degrees.
        """
        progress = bar / max(total_bars - 1, 1)

        if contour == "ascending":
            # Bias upward, level off at the end
            up_probability = 0.5 if progress > 0.85 else 0.7  # noqa: PLR2004
        elif contour == "descending":
            # Level start, then bias downward
            up_probability = 0.5 if progress < 0.15 else 0.3  # noqa: PLR2004
        elif contour == "wave":
            # Sinusoidal oscillation between 0.3 and 0.7
            up_probability = 0.5 + 0.2 * math.sin(progress * 2 * math.pi)
        else:
            # arch (default): rise, plateau, fall
            if progress < 0.4:  # noqa: PLR2004
                up_probability = 0.65
            elif progress > 0.7:  # noqa: PLR2004
                up_probability = 0.35
            else:
                up_probability = 0.5

        # Step vs leap probability
        r = rng.random()
        if r < 0.5 - temperature * 0.2:
            step = 1
        elif r < 0.8 - temperature * 0.1:
            step = rng.choice([2, 3])
        else:
            step = rng.choice([4, 5])

        direction = 1 if rng.random() < up_probability else -1
        return step * direction

    def _generate_bass(
        self,
        *,
        instrument: str,
        root_note: str,
        scale_type: str,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        chord_pattern: list[int],
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate bass line with walking patterns and rhythm variety."""
        octave = self._target_octave(instrument, "bass")
        root_scale = scale_notes(root_note, scale_type, octave)

        notes: list[Note] = []
        beats_per_bar = bars_to_beats(1, time_signature)

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            degree = chord_pattern[bar % len(chord_pattern)]
            root_pitch = root_scale[degree % len(root_scale)]
            velocity = self._compute_velocity(section_spec, start_bar + bar, trajectory)

            # Choose bass rhythm (temperature-dependent variety)
            if temperature < 0.3:  # noqa: PLR2004
                rhythm = [beats_per_bar]  # whole note
            else:
                rhythm = rng.choice(_BASS_RHYTHM_POOL)
                # Scale to bar length
                total = sum(rhythm)
                rhythm = [r * beats_per_bar / total for r in rhythm]

            beat_offset: Beat = 0.0
            for i, dur in enumerate(rhythm):
                if beat_offset + dur > beats_per_bar + 0.001:
                    break
                # First note = root, subsequent = passing tones
                if i == 0:
                    pitch = root_pitch
                else:
                    # Walking bass: use chord tone or passing tone
                    interval = rng.choice([0, 4, 7, 5])  # root, 3rd, 5th, 4th
                    pitch = root_pitch + interval
                    # Keep in octave
                    while pitch > root_pitch + 12:
                        pitch -= 12

                if not self._is_in_range(pitch, instrument):
                    self._record_recovery(
                        "BASS_NOTE_OUT_OF_RANGE", "warning",
                        pitch, root_pitch,
                        f"Bass passing tone {pitch} outside {instrument} range",
                        "Bass line jumps to root, slight smoothness loss",
                        ["narrow walking bass interval pool", "use instrument with wider range"],
                    )
                    pitch = root_pitch

                note = Note(
                    pitch=pitch,
                    start_beat=bar_start + beat_offset,
                    duration_beats=dur * self.config.bass_duration_factor,
                    velocity=velocity,
                    instrument=instrument,
                )
                notes.append(note)
                beat_offset += dur

        return notes

    @staticmethod
    def _apply_voicing(
        pitches: list[int],
        voicing_type: str,
    ) -> list[int]:
        """Apply a voicing transformation to chord pitches.

        Args:
            pitches: Root-position chord pitches (ascending order).
            voicing_type: One of root, first_inversion, second_inversion,
                         open, drop2.

        Returns:
            Reordered pitches with the voicing applied.
        """
        if len(pitches) < 2 or voicing_type == "root":  # noqa: PLR2004
            return pitches

        result = list(pitches)
        if voicing_type == "first_inversion":
            # Move lowest pitch up an octave
            result[0] += 12
            result.sort()
        elif voicing_type == "second_inversion" and len(result) >= 3:  # noqa: PLR2004
            # Move two lowest pitches up an octave
            result[0] += 12
            result[1] += 12
            result.sort()
        elif voicing_type == "open" and len(result) >= 3:  # noqa: PLR2004
            # Drop 2nd note down an octave for wider spacing
            result[1] -= 12
            result.sort()
        elif voicing_type == "drop2" and len(result) >= 3:  # noqa: PLR2004
            # Take 2nd-from-top note, drop it an octave (jazz voicing)
            idx = len(result) - 2
            result[idx] -= 12
            result.sort()

        return result

    def _choose_voicing(
        self, temperature: float, rng: random.Random
    ) -> str:
        """Select chord voicing type based on temperature.

        Args:
            temperature: Variation control.
            rng: Seeded RNG.

        Returns:
            Voicing type string.
        """
        if temperature < self.config.low_temp_threshold:
            return "root"

        if temperature < 0.6:  # noqa: PLR2004
            return rng.choices(
                ["root", "first_inversion", "second_inversion"],
                weights=[6, 2, 2],
            )[0]

        return rng.choices(
            ["root", "first_inversion", "second_inversion", "open", "drop2"],
            weights=[4, 2, 2, 1, 1],
        )[0]

    def _generate_chords(
        self,
        *,
        instrument: str,
        root_note: str,
        scale_type: str,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        chord_pattern: list[int],
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate chords with diatonic quality, optional 7ths, and voicings."""
        octave = self._target_octave(instrument, "chord")
        root_scale = scale_notes(root_note, scale_type, octave)
        beats_per_bar = bars_to_beats(1, time_signature)

        # Diatonic quality for each degree
        from yao.ir.harmony import diatonic_quality

        notes: list[Note] = []
        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            degree = chord_pattern[bar % len(chord_pattern)]
            root_pitch = root_scale[degree % len(root_scale)]
            velocity = self._compute_velocity(section_spec, start_bar + bar, trajectory)

            # Get proper diatonic quality
            quality = diatonic_quality(degree, scale_type)

            # Sometimes use 7th chords (temperature-dependent)
            seventh_prob = self.config.seventh_chord_probability_scale
            dom_prob = self.config.dominant_seventh_probability_scale
            if quality == "maj" and rng.random() < temperature * seventh_prob:
                quality = "maj7"
            elif quality == "min" and rng.random() < temperature * seventh_prob:
                quality = "min7"
            elif quality == "maj" and degree == 4 and rng.random() < temperature * dom_prob:
                quality = "dom7"  # V7

            chord_intervals = CHORD_INTERVALS.get(quality)
            if chord_intervals is None:
                self._record_recovery(
                    "CHORD_QUALITY_UNDEFINED", "info",
                    quality, "maj",
                    f"Chord quality '{quality}' not found in palette",
                    "Chord defaults to major triad",
                    ["add chord quality to constants"],
                )
                chord_intervals = CHORD_INTERVALS["maj"]

            chord_vel = max(velocity + self.config.chord_velocity_offset, 1)

            # Build chord pitches and apply voicing
            chord_pitches = [root_pitch + iv for iv in chord_intervals]
            voicing = self._choose_voicing(temperature, rng)
            chord_pitches = self._apply_voicing(chord_pitches, voicing)

            for pitch in chord_pitches:
                if self._is_in_range(pitch, instrument):
                    note = Note(
                        pitch=pitch,
                        start_beat=bar_start,
                        duration_beats=beats_per_bar * self.config.chord_duration_factor,
                        velocity=chord_vel,
                        instrument=instrument,
                    )
                    notes.append(note)
                else:
                    self._record_recovery(
                        "CHORD_NOTE_OUT_OF_RANGE", "info",
                        pitch, None,
                        f"Chord note {pitch} outside {instrument} range",
                        "Chord voicing has one fewer note",
                    )

        return notes

    def _generate_pad(
        self,
        *,
        instrument: str,
        root_note: str,
        scale_type: str,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        chord_pattern: list[int],
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate sustained pad chords with open voicings.

        Pads use long durations, soft dynamics, and wide voicings to create
        an atmospheric bed beneath melody and harmony instruments.
        """
        octave = self._target_octave(instrument, "chord")
        root_scale = scale_notes(root_note, scale_type, octave)
        beats_per_bar = bars_to_beats(1, time_signature)

        from yao.ir.harmony import diatonic_quality

        notes: list[Note] = []
        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            degree = chord_pattern[bar % len(chord_pattern)]
            root_pitch = root_scale[degree % len(root_scale)]
            velocity = self._compute_velocity(section_spec, start_bar + bar, trajectory)

            quality = diatonic_quality(degree, scale_type)
            chord_intervals = CHORD_INTERVALS.get(quality)
            if chord_intervals is None:
                self._record_recovery(
                    "CHORD_QUALITY_UNDEFINED", "info",
                    quality, "maj",
                    f"Pad chord quality '{quality}' not found",
                    "Pad chord defaults to major triad",
                )
                chord_intervals = CHORD_INTERVALS["maj"]

            # Pad rhythm: long sustained notes
            rhythm = rng.choice(_PAD_RHYTHM_POOL)
            total = sum(rhythm)
            scaled_rhythm = [r * beats_per_bar / total for r in rhythm]

            beat_offset: Beat = 0.0
            for dur in scaled_rhythm:
                if beat_offset + dur > beats_per_bar + 0.001:
                    break
                for i, interval in enumerate(chord_intervals):
                    pitch = root_pitch + interval
                    # Open voicing: drop middle note(s) down an octave
                    if i == 1 and len(chord_intervals) >= 3:
                        pitch -= 12
                    if self._is_in_range(pitch, instrument):
                        note = Note(
                            pitch=pitch,
                            start_beat=bar_start + beat_offset,
                            duration_beats=dur * self.config.pad_duration_factor,
                            velocity=max(velocity + self.config.pad_velocity_offset, 1),
                            instrument=instrument,
                        )
                        notes.append(note)
                beat_offset += dur

        return notes

    def _generate_rhythm(
        self,
        *,
        instrument: str,
        root_note: str,
        scale_type: str,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        chord_pattern: list[int],
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate short, percussive rhythm patterns.

        Rhythm parts use subdivided patterns with staccato articulation,
        playing root and fifth for percussive clarity.
        """
        octave = self._target_octave(instrument, "chord")
        root_scale = scale_notes(root_note, scale_type, octave)
        beats_per_bar = bars_to_beats(1, time_signature)

        notes: list[Note] = []
        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            degree = chord_pattern[bar % len(chord_pattern)]
            root_pitch = root_scale[degree % len(root_scale)]
            velocity = self._compute_velocity(section_spec, start_bar + bar, trajectory)

            # Choose rhythm pattern
            rhythm = rng.choice(_RHYTHM_PART_POOL)
            total = sum(rhythm)
            scaled_rhythm = [r * beats_per_bar / total for r in rhythm]

            # Rhythm uses root and fifth only for percussive clarity
            rhythm_pitches = [root_pitch, root_pitch + 7]
            rhythm_pitches = [p for p in rhythm_pitches if self._is_in_range(p, instrument)]
            if not rhythm_pitches:
                self._record_recovery(
                    "RHYTHM_PITCH_OUT_OF_RANGE", "warning",
                    [root_pitch, root_pitch + 7], [root_pitch],
                    f"Rhythm pitches outside {instrument} range, using root only",
                    "Rhythm part loses interval variety, only root note",
                    ["use instrument with wider range"],
                )
                rhythm_pitches = [root_pitch]

            beat_offset: Beat = 0.0
            for i, dur in enumerate(scaled_rhythm):
                if beat_offset + dur > beats_per_bar + 0.001:
                    break

                pitch = rng.choice(rhythm_pitches)

                # Accent pattern: downbeat louder, offbeats softer
                accent = self.config.downbeat_accent if i == 0 else self.config.offbeat_accent
                final_vel = max(1, min(127, velocity + accent))

                # Velocity humanization
                if temperature > 0.3:  # noqa: PLR2004
                    final_vel = max(1, min(127, final_vel + rng.randint(-3, 3)))

                note = Note(
                    pitch=pitch,
                    start_beat=bar_start + beat_offset,
                    duration_beats=dur * self.config.rhythm_duration_factor,
                    velocity=final_vel,
                    instrument=instrument,
                )
                notes.append(note)
                beat_offset += dur

        return notes

    def _compute_velocity(
        self,
        section_spec: SectionSpec,
        bar: int,
        trajectory: TrajectorySpec | None,
    ) -> Velocity:
        """Compute velocity from dynamics and trajectory."""
        base_velocity = DYNAMICS_TO_VELOCITY.get(section_spec.dynamics, 80)
        if trajectory is not None:
            tension = trajectory.value_at("tension", bar)
            modifier = (tension - 0.5) * self.config.tension_velocity_scale
            base_velocity = int(base_velocity * (1.0 + modifier))
        clamped = max(1, min(127, base_velocity))
        if clamped != base_velocity:
            self._record_recovery(
                "VELOCITY_CLAMPED", "info",
                base_velocity, clamped,
                f"Base velocity {base_velocity} clamped to MIDI range",
                "Negligible — dynamics at MIDI boundary",
            )
        return clamped

    def _instrument_rng(self, master_seed: int, instrument: str, section: str) -> random.Random:
        """Create a deterministic per-instrument RNG.

        Derives a unique seed from the master seed, instrument name, and section
        name. This decorrelates instruments while preserving reproducibility.

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

    def _target_octave(self, instrument: str, role: str) -> int:
        """Choose octave based on instrument range and role."""
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return {"melody": 5, "bass": 2, "chord": 4}.get(role, 4)
        if role == "bass":
            # MIDI→octave: //12 - 1 gives the octave. +1 puts us one octave above lowest.
            low_octave = (inst_range.midi_low // 12) - 1
            return low_octave + 1
        if role == "melody":
            mid = (inst_range.midi_low + inst_range.midi_high * 2) // 3
            return (mid // 12) - 1
        # chord
        mid = (inst_range.midi_low + inst_range.midi_high) // 2
        return (mid // 12) - 1

    def _is_in_range(self, pitch: MidiNote, instrument: str) -> bool:
        """Check if pitch is within instrument range."""
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return 0 <= pitch <= 127
        return inst_range.midi_low <= pitch <= inst_range.midi_high
