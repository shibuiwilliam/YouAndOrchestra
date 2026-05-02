"""Markov chain generator — n-gram probabilistic pitch selection.

Uses pre-computed transition tables (YAML) to produce melodies that
follow statistical voice-leading patterns. Each note is chosen based
on the probability distribution conditioned on the previous note(s).

Key design choices:
- Transition tables operate on **scale degrees** (0–6 for diatonic),
  not MIDI pitches. This makes the model key-agnostic.
- Temperature controls distribution sharpening via softmax scaling.
- Trajectory coupling follows the same contract as stochastic generator:
  tension → velocity + leaps, density → rhythm, register_height → octave.
- n-gram tables are lazy-loaded from YAML; no heavy computation at import time.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.constants.music import CHORD_INTERVALS, DYNAMICS_TO_VELOCITY
from yao.generators.base import GeneratorBase
from yao.generators.registry import register_generator
from yao.ir.harmony import diatonic_quality
from yao.ir.notation import parse_key, scale_notes
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import bars_to_beats
from yao.reflect.provenance import ProvenanceLog
from yao.reflect.recoverable import RecoverableDecision
from yao.schema.composition import CompositionSpec, SectionSpec
from yao.schema.trajectory import TrajectorySpec
from yao.types import Beat, MidiNote, Velocity

_MODELS_DIR = Path(__file__).parent / "markov_models"

# ---------------------------------------------------------------------------
# Rhythm pools — shared with stochastic (same patterns, different pitch logic)
# ---------------------------------------------------------------------------

_MELODY_RHYTHM_POOL: list[list[float]] = [
    [1.0, 1.0, 1.0, 1.0],
    [2.0, 1.0, 1.0],
    [1.0, 1.0, 2.0],
    [1.5, 0.5, 1.0, 1.0],
    [1.0, 0.5, 0.5, 1.0, 1.0],
    [0.5, 0.5, 0.5, 0.5, 1.0, 1.0],
    [1.0, 1.0, 0.5, 0.5, 1.0],
    [2.0, 2.0],
    [1.5, 1.5, 1.0],
    [0.5, 1.5, 1.0, 1.0],
    [1.0, 0.5, 0.5, 0.5, 0.5, 1.0],
    [3.0, 1.0],
]

_BASS_RHYTHM_POOL: list[list[float]] = [
    [4.0],
    [2.0, 2.0],
    [2.0, 1.0, 1.0],
    [1.0, 1.0, 2.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.5, 0.5, 2.0],
]

_CHORD_PATTERNS: dict[str, list[list[int]]] = {
    "intro": [[0, 4], [0, 3, 4, 0]],
    "verse": [[0, 5, 3, 4], [0, 2, 3, 4], [0, 5, 1, 4]],
    "chorus": [[0, 4, 5, 3], [3, 0, 3, 4], [0, 3, 5, 4]],
    "bridge": [[1, 4, 0, 0], [5, 3, 1, 4], [3, 1, 4, 0]],
    "outro": [[3, 4, 0, 0], [0, 3, 4, 0]],
    "default": [[0, 3, 4, 0], [0, 5, 3, 4], [0, 4, 5, 3]],
}


# ---------------------------------------------------------------------------
# Markov model loading
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MarkovModel:
    """A loaded n-gram transition table.

    Attributes:
        name: Model identifier.
        description: Human-readable description.
        source: Provenance of the training data.
        license: License of the model data.
        n_gram_order: Order of the n-gram (2 = bigram).
        num_degrees: Number of scale degrees in the model.
        transitions: Mapping from degree → {next_degree: probability}.
    """

    name: str
    description: str
    source: str
    license: str
    n_gram_order: int
    num_degrees: int
    transitions: dict[int, dict[int, float]]


_MODEL_CACHE: dict[str, MarkovModel] = {}


def _load_model(model_name: str) -> MarkovModel:
    """Lazy-load a Markov model from YAML.

    Args:
        model_name: Name of the model file (without .yaml extension).

    Returns:
        Parsed MarkovModel.

    Raises:
        FileNotFoundError: If the model file does not exist.
    """
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    path = _MODELS_DIR / f"{model_name}.yaml"
    if not path.exists():
        available = [p.stem for p in _MODELS_DIR.glob("*.yaml")]
        raise FileNotFoundError(f"Markov model '{model_name}' not found at {path}. Available models: {available}")

    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f)

    meta = data["metadata"]
    raw_transitions = data["transitions"]

    # Convert string keys to int
    transitions: dict[int, dict[int, float]] = {}
    for degree_str, targets in raw_transitions.items():
        degree = int(degree_str)
        transitions[degree] = {int(k): float(v) for k, v in targets.items()}

    num_degrees = len(transitions)

    model = MarkovModel(
        name=meta["name"],
        description=meta["description"],
        source=meta["source"],
        license=meta["license"],
        n_gram_order=meta["n_gram_order"],
        num_degrees=num_degrees,
        transitions=transitions,
    )
    _MODEL_CACHE[model_name] = model
    return model


def _select_model_for_scale(scale_type: str) -> str:
    """Choose the best model name for a given scale type.

    Args:
        scale_type: Scale type from the spec (e.g., "major", "pentatonic_minor").

    Returns:
        Model file name (without .yaml).
    """
    if "pentatonic" in scale_type:
        return "pentatonic_bigram"
    return "diatonic_bigram"


def _temperature_scale(
    probs: dict[int, float],
    temperature: float,
) -> dict[int, float]:
    """Apply temperature scaling to a probability distribution.

    Temperature 0.0 → argmax (near-deterministic).
    Temperature 1.0 → original distribution.
    Temperature > 1.0 → flatter (more uniform).

    Args:
        probs: Mapping from degree to probability.
        temperature: Temperature parameter (>0).

    Returns:
        Rescaled probability distribution summing to 1.0.
    """
    if not probs:
        return probs

    temp = max(temperature, 0.01)  # avoid division by zero

    # Softmax with temperature: p_i^(1/T) / sum(p_j^(1/T))
    scaled: dict[int, float] = {}
    for k, p in probs.items():
        if p <= 0:
            scaled[k] = 0.0
        else:
            scaled[k] = math.pow(p, 1.0 / temp)

    total = sum(scaled.values())
    if total <= 0:
        # Fallback to uniform
        n = len(probs)
        return {k: 1.0 / n for k in probs}

    return {k: v / total for k, v in scaled.items()}


def _sample_from_dist(
    dist: dict[int, float],
    rng: random.Random,
) -> int:
    """Sample a key from a probability distribution.

    Args:
        dist: Mapping from value to probability.
        rng: Seeded RNG.

    Returns:
        Sampled key.
    """
    keys = list(dist.keys())
    weights = [dist[k] for k in keys]
    return rng.choices(keys, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@register_generator("markov")
class MarkovGenerator(GeneratorBase):
    """Markov chain composition generator using n-gram pitch transitions.

    Uses pre-computed transition tables operating on scale degrees.
    Temperature controls distribution sharpening. Seed ensures reproducibility.
    Trajectory coupling matches the stochastic generator contract.
    """

    _provenance: ProvenanceLog

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
        """Generate a composition using Markov chain pitch selection.

        Args:
            spec: The composition specification.
            trajectory: Optional trajectory for dynamic shaping.

        Returns:
            Tuple of (ScoreIR, ProvenanceLog).
        """
        seed = spec.generation.seed if spec.generation.seed is not None else 42
        temperature = spec.generation.temperature
        rng = random.Random(seed)

        root_note, scale_type = parse_key(spec.key)
        model_name = _select_model_for_scale(scale_type)
        model = _load_model(model_name)

        prov = ProvenanceLog()
        self._provenance = prov
        prov.record(
            layer="generator",
            operation="start_generation",
            parameters={
                "title": spec.title,
                "key": spec.key,
                "tempo": spec.tempo_bpm,
                "strategy": "markov",
                "seed": seed,
                "temperature": temperature,
                "n_gram_order": model.n_gram_order,
                "model_name": model.name,
            },
            source="MarkovGenerator.generate",
            rationale=(f"Markov chain generation with model='{model.name}', seed={seed}, temperature={temperature}."),
        )

        sections = self._generate_sections(
            spec=spec,
            root_note=root_note,
            scale_type=scale_type,
            model=model,
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
            source="MarkovGenerator.generate",
            rationale="Markov composition generation complete.",
        )

        return score, prov

    def _generate_sections(
        self,
        *,
        spec: CompositionSpec,
        root_note: str,
        scale_type: str,
        model: MarkovModel,
        trajectory: TrajectorySpec | None,
        provenance: ProvenanceLog,
        rng: random.Random,
        seed: int,
        temperature: float,
    ) -> list[Section]:
        """Generate all sections."""
        sections: list[Section] = []
        current_bar = 0

        for section_spec in spec.sections:
            section_start = current_bar
            section_end = current_bar + section_spec.bars

            chord_pattern = self._choose_chord_pattern(section_spec.name, rng, temperature)

            parts: list[Part] = []
            for instr_spec in spec.instruments:
                instr_rng = self._instrument_rng(seed, instr_spec.name, section_spec.name)

                notes = self._generate_part(
                    instrument=instr_spec.name,
                    role=instr_spec.role,
                    root_note=root_note,
                    scale_type=scale_type,
                    model=model,
                    start_bar=section_start,
                    bars=section_spec.bars,
                    time_signature=section_spec.time_signature or spec.time_signature,
                    section_spec=section_spec,
                    trajectory=trajectory,
                    chord_pattern=chord_pattern,
                    rng=instr_rng,
                    temperature=temperature,
                )

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
                source="MarkovGenerator._generate_sections",
                rationale=(
                    f"Section '{section_spec.name}' generated via Markov chain with chord degrees {chord_pattern}."
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

    def _generate_part(
        self,
        *,
        instrument: str,
        role: str,
        root_note: str,
        scale_type: str,
        model: MarkovModel,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        chord_pattern: list[int],
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate notes for one instrument part.

        Routes to role-specific methods. Melody and bass use Markov transitions;
        harmony/pad use chord-based generation (same as stochastic).
        """
        if role == "melody":
            return self._generate_melody(
                instrument=instrument,
                root_note=root_note,
                scale_type=scale_type,
                model=model,
                start_bar=start_bar,
                bars=bars,
                time_signature=time_signature,
                section_spec=section_spec,
                trajectory=trajectory,
                rng=rng,
                temperature=temperature,
            )
        if role == "bass":
            return self._generate_bass(
                instrument=instrument,
                root_note=root_note,
                scale_type=scale_type,
                model=model,
                start_bar=start_bar,
                bars=bars,
                time_signature=time_signature,
                section_spec=section_spec,
                trajectory=trajectory,
                chord_pattern=chord_pattern,
                rng=rng,
                temperature=temperature,
            )
        # harmony / pad / rhythm — chord-based (not Markov)
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
        model: MarkovModel,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate melody using Markov chain transitions on scale degrees.

        Trajectory response:
        - tension → velocity modifier + leap bias in transition sampling
        - density → rhythm subdivision selection
        - register_height → octave offset
        """
        octave = self._target_octave(instrument, "melody")

        register_offset = 0
        if trajectory is not None:
            reg_height = trajectory.value_at("register_height", start_bar)
            register_offset = round((reg_height - 0.5) * 2)

        all_scale = scale_notes(root_note, scale_type, octave + register_offset)
        num_degrees = len(all_scale)

        notes: list[Note] = []
        beats_per_bar = bars_to_beats(1, time_signature)

        # Start from tonic (degree 0) in the middle of the range
        current_degree = 0
        current_octave_offset = 0  # octaves above base

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)

            density = 0.5
            if trajectory is not None:
                density = trajectory.value_at("density", start_bar + bar)
            rhythm = self._density_aware_rhythm(rng, density)

            velocity = self._compute_velocity(section_spec, start_bar + bar, trajectory)

            # Occasional rest
            if rng.random() < temperature * 0.15:
                continue

            bar_tension = 0.5
            if trajectory is not None:
                bar_tension = trajectory.value_at("tension", start_bar + bar)

            beat_offset: Beat = 0.0
            for dur in rhythm:
                if beat_offset + dur > beats_per_bar + 0.001:
                    break

                # Get transition probabilities from model
                model_degree = current_degree % model.num_degrees
                raw_probs = model.transitions.get(model_degree, {})

                # Apply temperature scaling
                probs = _temperature_scale(raw_probs, temperature)

                # Bias toward leaps at high tension
                if bar_tension > 0.6 and probs:
                    # Boost probabilities for non-adjacent degrees
                    biased: dict[int, float] = {}
                    for deg, p in probs.items():
                        dist = abs(deg - model_degree)
                        if dist > 1:
                            biased[deg] = p * (1.0 + bar_tension)
                        else:
                            biased[deg] = p
                    total = sum(biased.values())
                    if total > 0:
                        probs = {k: v / total for k, v in biased.items()}

                # Sample next degree
                next_degree = _sample_from_dist(probs, rng) if probs else rng.randint(0, num_degrees - 1)

                # Handle octave transitions for smooth melodic contour
                degree_jump = next_degree - current_degree
                if degree_jump > num_degrees // 2:
                    current_octave_offset -= 1
                elif degree_jump < -(num_degrees // 2):
                    current_octave_offset += 1

                # Keep octave offset in reasonable range
                current_octave_offset = max(-1, min(1, current_octave_offset))

                # Compute MIDI pitch
                base_pitch = all_scale[next_degree % num_degrees]
                pitch = base_pitch + current_octave_offset * 12

                current_degree = next_degree

                if not self._is_in_range(pitch, instrument):
                    original_pitch = pitch
                    # Try bouncing octave
                    if current_octave_offset > 0 and self._is_in_range(pitch - 12, instrument):
                        pitch -= 12
                        current_octave_offset -= 1
                    elif current_octave_offset < 0 and self._is_in_range(pitch + 12, instrument):
                        pitch += 12
                        current_octave_offset += 1
                    elif self._is_in_range(base_pitch, instrument):
                        pitch = base_pitch
                        current_octave_offset = 0
                    else:
                        self._record_recovery(
                            "MARKOV_NOTE_SKIPPED",
                            "warning",
                            original_pitch,
                            None,
                            f"Markov pitch {original_pitch} outside {instrument} range",
                            "One note missing from melody",
                            ["adjust melody octave", "use wider-range instrument"],
                        )
                        beat_offset += dur
                        continue

                    if pitch != original_pitch:
                        self._record_recovery(
                            "MARKOV_NOTE_OUT_OF_RANGE",
                            "info",
                            original_pitch,
                            pitch,
                            f"Markov pitch {original_pitch} adjusted to {pitch}",
                            "Slight register shift at this point",
                        )

                # Velocity humanization
                vel_variation = rng.randint(-5, 5) if temperature > 0.3 else 0
                raw_vel = velocity + vel_variation
                final_vel = max(1, min(127, raw_vel))

                note = Note(
                    pitch=pitch,
                    start_beat=bar_start + beat_offset,
                    duration_beats=dur * 0.85,
                    velocity=final_vel,
                    instrument=instrument,
                )
                notes.append(note)
                beat_offset += dur

        return notes

    def _generate_bass(
        self,
        *,
        instrument: str,
        root_note: str,
        scale_type: str,
        model: MarkovModel,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        chord_pattern: list[int],
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Generate bass using chord roots with Markov passing tones."""
        octave = self._target_octave(instrument, "bass")
        root_scale = scale_notes(root_note, scale_type, octave)
        beats_per_bar = bars_to_beats(1, time_signature)

        notes: list[Note] = []
        current_degree = 0

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            chord_degree = chord_pattern[bar % len(chord_pattern)]
            root_pitch = root_scale[chord_degree % len(root_scale)]
            velocity = self._compute_velocity(section_spec, start_bar + bar, trajectory)

            if temperature < 0.3:
                rhythm = [beats_per_bar]
            else:
                rhythm = rng.choice(_BASS_RHYTHM_POOL)
                total = sum(rhythm)
                rhythm = [r * beats_per_bar / total for r in rhythm]

            beat_offset: Beat = 0.0
            for i, dur in enumerate(rhythm):
                if beat_offset + dur > beats_per_bar + 0.001:
                    break

                if i == 0:
                    pitch = root_pitch
                    current_degree = chord_degree
                else:
                    # Use Markov chain for passing tones
                    model_degree = current_degree % model.num_degrees
                    raw_probs = model.transitions.get(model_degree, {})
                    probs = _temperature_scale(raw_probs, temperature)
                    if probs:
                        next_deg = _sample_from_dist(probs, rng)
                        pitch = root_scale[next_deg % len(root_scale)]
                        current_degree = next_deg
                    else:
                        pitch = root_pitch

                if not self._is_in_range(pitch, instrument):
                    self._record_recovery(
                        "BASS_NOTE_OUT_OF_RANGE",
                        "warning",
                        pitch,
                        root_pitch,
                        f"Bass passing tone {pitch} outside {instrument} range",
                        "Bass falls back to chord root",
                        ["narrow bass interval pool", "use wider-range instrument"],
                    )
                    pitch = root_pitch

                note = Note(
                    pitch=pitch,
                    start_beat=bar_start + beat_offset,
                    duration_beats=dur * 0.85,
                    velocity=velocity,
                    instrument=instrument,
                )
                notes.append(note)
                beat_offset += dur

        return notes

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
        """Generate chord/harmony/pad/rhythm parts (non-Markov, chord-based)."""
        octave = self._target_octave(instrument, "chord")
        root_scale = scale_notes(root_note, scale_type, octave)
        beats_per_bar = bars_to_beats(1, time_signature)

        notes: list[Note] = []
        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            degree = chord_pattern[bar % len(chord_pattern)]
            root_pitch = root_scale[degree % len(root_scale)]
            velocity = self._compute_velocity(section_spec, start_bar + bar, trajectory)

            quality = diatonic_quality(degree, scale_type)
            chord_intervals = CHORD_INTERVALS.get(quality)
            if chord_intervals is None:
                chord_intervals = CHORD_INTERVALS["maj"]

            chord_vel = max(velocity - 10, 1)
            chord_pitches = [root_pitch + iv for iv in chord_intervals]

            for pitch in chord_pitches:
                if self._is_in_range(pitch, instrument):
                    note = Note(
                        pitch=pitch,
                        start_beat=bar_start,
                        duration_beats=beats_per_bar * 0.85,
                        velocity=chord_vel,
                        instrument=instrument,
                    )
                    notes.append(note)

        return notes

    # ------------------------------------------------------------------
    # Helpers (same patterns as stochastic generator)
    # ------------------------------------------------------------------

    def _choose_chord_pattern(
        self,
        section_name: str,
        rng: random.Random,
        temperature: float,
    ) -> list[int]:
        """Choose a chord degree pattern for a section type."""
        patterns = _CHORD_PATTERNS.get(section_name, _CHORD_PATTERNS["default"])
        if temperature < 0.2:
            return patterns[0]
        return rng.choice(patterns)

    def _density_aware_rhythm(
        self,
        rng: random.Random,
        density: float,
    ) -> list[float]:
        """Select rhythm biased by density trajectory."""
        if density >= 0.7:
            dense = [p for p in _MELODY_RHYTHM_POOL if len(p) >= 5]
            if dense:
                return rng.choice(dense)
        elif density <= 0.3:
            sparse = [p for p in _MELODY_RHYTHM_POOL if len(p) <= 3]
            if sparse:
                return rng.choice(sparse)
        return rng.choice(_MELODY_RHYTHM_POOL)

    def _compute_velocity(
        self,
        section_spec: SectionSpec,
        bar: int,
        trajectory: TrajectorySpec | None,
    ) -> Velocity:
        """Compute velocity from dynamics and trajectory tension."""
        base_velocity = DYNAMICS_TO_VELOCITY.get(section_spec.dynamics, 80)
        if trajectory is not None:
            tension = trajectory.value_at("tension", bar)
            modifier = (tension - 0.5) * 0.4
            base_velocity = int(base_velocity * (1.0 + modifier))
        clamped = max(1, min(127, base_velocity))
        if clamped != base_velocity:
            self._record_recovery(
                "VELOCITY_CLAMPED",
                "info",
                base_velocity,
                clamped,
                f"Velocity {base_velocity} clamped to MIDI range",
                "Negligible — dynamics at MIDI boundary",
            )
        return clamped

    def _instrument_rng(
        self,
        master_seed: int,
        instrument: str,
        section: str,
    ) -> random.Random:
        """Create a deterministic per-instrument RNG."""
        combined = f"{master_seed}:{instrument}:{section}"
        derived_seed = int(hashlib.sha256(combined.encode()).hexdigest()[:8], 16)
        return random.Random(derived_seed)

    def _target_octave(self, instrument: str, role: str) -> int:
        """Choose octave based on instrument range and role."""
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
        """Check if pitch is within instrument range."""
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return 0 <= pitch <= 127
        return inst_range.midi_low <= pitch <= inst_range.midi_high
