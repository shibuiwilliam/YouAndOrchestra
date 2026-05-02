"""Stochastic note realizer V2 — consumes MusicalPlan directly with randomness.

Extends RuleBasedNoteRealizerV2 with seed/temperature-controlled variation:
- Temperature controls the probability of non-chord tones
- Temperature controls rhythmic variety (syncopation, subdivision)
- Seed ensures reproducibility

No _plan_to_v1_spec(). No legacy_adapter. Direct plan consumption.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from yao.generators.note.base import NoteRealizerBase, register_note_realizer
from yao.generators.note.rule_based_v2 import (
    _apply_motif_transform,
    _contour_direction,
    _density_to_notes_per_beat,
    _parse_key,
    _tension_to_velocity,
)
from yao.ir.harmony import ChordFunction
from yao.ir.harmony import realize as realize_chord
from yao.ir.note import Note
from yao.ir.plan.harmony import ChordEvent
from yao.ir.plan.motif import MotifPlacement
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.phrase import Phrase
from yao.ir.plan.song_form import SectionPlan
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog

if TYPE_CHECKING:
    from yao.schema.composition import CompositionSpec


@register_note_realizer("stochastic_v2")
class StochasticNoteRealizerV2(NoteRealizerBase):
    """V2 stochastic realizer — direct plan consumption with temperature.

    Temperature (0.0–1.0) controls:
    - 0.0: Only chord tones, uniform rhythm (like rule_based_v2)
    - 0.5: Some passing tones, moderate rhythmic variety
    - 1.0: Frequent non-chord tones, high rhythmic variety, wider leaps
    """

    consumed_plan_fields = (
        "global_context.key",
        "global_context.tempo_bpm",
        "global_context.time_signature",
        "global_context.instruments",
        "form.sections",
        "harmony.chord_events",
        "motif.seeds",
        "motif.placements",
        "phrase.phrases",
        "trajectory",
    )

    def realize(
        self,
        plan: MusicalPlan,
        seed: int,
        temperature: float,
        provenance: ProvenanceLog,
        original_spec: CompositionSpec | None = None,
    ) -> ScoreIR:
        """Realize a MusicalPlan into ScoreIR with stochastic variation.

        Args:
            plan: The musical plan to realize.
            seed: Random seed for reproducibility.
            temperature: Variation control (0.0=deterministic, 1.0=maximum variety).
            provenance: Provenance log.
            original_spec: Ignored in V2.

        Returns:
            ScoreIR with concrete notes.
        """
        rng = random.Random(seed)
        ctx = plan.global_context
        key_root, scale_type = _parse_key(ctx.key)

        provenance.record(
            layer="generator",
            operation="note_realization_v2",
            parameters={
                "realizer": "stochastic_v2",
                "seed": seed,
                "temperature": temperature,
                "key": ctx.key,
                "tempo": ctx.tempo_bpm,
                "consumed_fields": list(self.consumed_plan_fields),
            },
            source="StochasticNoteRealizerV2.realize",
            rationale=f"V2 stochastic plan consumption (seed={seed}, temp={temperature}).",
        )

        # Determine instruments
        if plan.arrangement and plan.arrangement.assignments:
            melody_assigns = [a for a in plan.arrangement.assignments if a.role == "melody"]
            instruments = (
                [a.instrument for a in melody_assigns]
                if melody_assigns
                else [plan.arrangement.assignments[0].instrument]
            )
        elif ctx.instruments:
            instruments = [name for name, _role in ctx.instruments]
        else:
            instruments = ["piano"]
        melody_instrument = instruments[0]

        if plan.drums:
            provenance.record(
                layer="generator",
                operation="drum_pattern_acknowledged",
                parameters={"drum_genre": plan.drums.genre if hasattr(plan.drums, "genre") else "none"},
                source="StochasticNoteRealizerV2.realize",
                rationale="Drum pattern informs rhythmic density choices.",
            )

        beats_per_bar = self._beats_per_bar(ctx.time_signature)

        sections: list[Section] = []
        for section_plan in plan.form.sections:
            section_notes = self._realize_section(
                section_plan=section_plan,
                plan=plan,
                key_root=key_root,
                scale_type=scale_type,
                beats_per_bar=beats_per_bar,
                melody_instrument=melody_instrument,
                rng=rng,
                temperature=temperature,
                provenance=provenance,
            )
            sections.append(
                Section(
                    name=section_plan.id,
                    start_bar=section_plan.start_bar,
                    end_bar=section_plan.end_bar(),
                    parts=(Part(instrument=melody_instrument, notes=tuple(section_notes)),),
                )
            )

        return ScoreIR(
            title=plan.intent.text[:50] if plan.intent.text else "Untitled",
            tempo_bpm=ctx.tempo_bpm,
            time_signature=ctx.time_signature,
            key=ctx.key,
            sections=tuple(sections),
        )

    def _realize_section(
        self,
        section_plan: SectionPlan,
        plan: MusicalPlan,
        key_root: str,
        scale_type: str,
        beats_per_bar: float,
        melody_instrument: str,
        rng: random.Random,
        temperature: float,
        provenance: ProvenanceLog,
    ) -> list[Note]:
        """Realize a section with stochastic variation."""
        notes: list[Note] = []
        section_start_beat = section_plan.start_bar * beats_per_bar
        section_end_beat = section_plan.end_bar() * beats_per_bar

        section_chords = [ce for ce in plan.harmony.chord_events if ce.section_id == section_plan.id]

        motif_placements: list[MotifPlacement] = []
        if plan.motif:
            motif_placements = plan.motif.placements_in_section(section_plan.id)

        section_phrases: list[Phrase] = []
        if plan.phrase:
            section_phrases = plan.phrase.phrases_in_section(section_plan.id)

        base_velocity = _tension_to_velocity(section_plan.target_tension)
        notes_per_beat = _density_to_notes_per_beat(section_plan.target_density)

        # Motif placements first
        motif_beats: set[float] = set()
        for placement in motif_placements:
            motif_notes = self._realize_motif(
                placement,
                plan,
                key_root,
                scale_type,
                base_velocity,
                melody_instrument,
                section_chords,
                rng,
                temperature,
            )
            for n in motif_notes:
                motif_beats.add(n.start_beat)
            notes.extend(motif_notes)

        # Fill with stochastic melody
        beat = section_start_beat
        last_pitch = 60
        base_duration = 1.0 / max(notes_per_beat, 0.5)

        while beat < section_end_beat:
            if any(abs(beat - mb) < 0.25 for mb in motif_beats):
                beat += base_duration
                continue

            current_chord = self._chord_at_beat(section_chords, beat)
            if current_chord is None:
                beat += base_duration
                continue

            chord_pitches = self._realize_chord_pitches(current_chord, key_root, scale_type)
            if not chord_pitches:
                beat += base_duration
                continue

            # Phrase contour
            direction = 0
            for phrase in section_phrases:
                if phrase.start_beat <= beat < phrase.end_beat():
                    position = (beat - phrase.start_beat) / max(phrase.length_beats, 1.0)
                    direction = _contour_direction(phrase.contour, position)
                    break

            # Stochastic pitch choice
            pitch = self._choose_pitch_stochastic(
                chord_pitches,
                last_pitch,
                direction,
                rng,
                temperature,
                key_root,
                scale_type,
            )

            # Stochastic velocity
            vel_base = int(base_velocity * (0.7 + 0.3 * current_chord.tension_level))
            vel_variation = int(rng.gauss(0, 8 * temperature))
            velocity = max(30, min(127, vel_base + vel_variation))

            # Stochastic duration
            duration = self._stochastic_duration(base_duration, rng, temperature, beats_per_bar)
            if current_chord.cadence_role is not None:
                duration = min(duration * 1.5, beats_per_bar)
                velocity = min(velocity + 10, 127)

            notes.append(
                Note(
                    pitch=pitch,
                    start_beat=beat,
                    duration_beats=duration,
                    velocity=velocity,
                    instrument=melody_instrument,
                )
            )

            last_pitch = pitch
            beat += duration

        return notes

    def _realize_motif(
        self,
        placement: MotifPlacement,
        plan: MusicalPlan,
        key_root: str,
        scale_type: str,
        base_velocity: int,
        melody_instrument: str,
        section_chords: list[ChordEvent],
        rng: random.Random,
        temperature: float,
    ) -> list[Note]:
        """Realize a motif with stochastic micro-variations."""
        if plan.motif is None:
            return []
        seed_motif = plan.motif.seed_by_id(placement.motif_id)
        if seed_motif is None:
            return []

        intervals, rhythm = _apply_motif_transform(
            seed_motif.interval_shape,
            seed_motif.rhythm_shape,
            placement.transform,
        )

        chord_at = self._chord_at_beat(section_chords, placement.start_beat)
        if chord_at:
            cp = self._realize_chord_pitches(chord_at, key_root, scale_type)
            root_pitch = cp[0] if cp else 60
        else:
            from yao.ir.notation import note_name_to_midi

            root_pitch = note_name_to_midi(f"{key_root}4")

        root_pitch += placement.transposition

        notes: list[Note] = []
        beat = placement.start_beat
        current_pitch = root_pitch

        for i, dur in enumerate(rhythm):
            if i < len(intervals):
                current_pitch = root_pitch + intervals[i]
            # Stochastic micro-variation on pitch
            if temperature > 0.3 and rng.random() < temperature * 0.3:
                current_pitch += rng.choice([-1, 1])

            # Stochastic velocity variation
            vel = max(30, min(127, base_velocity + int(rng.gauss(0, 5 * temperature))))

            # Stochastic timing micro-variation (swing feel)
            timing_offset = rng.gauss(0, 0.02 * temperature)

            notes.append(
                Note(
                    pitch=max(0, min(127, current_pitch)),
                    start_beat=max(0.0, beat + timing_offset),
                    duration_beats=dur,
                    velocity=vel,
                    instrument=melody_instrument,
                )
            )
            beat += dur

        return notes

    def _choose_pitch_stochastic(
        self,
        chord_pitches: list[int],
        last_pitch: int,
        direction: int,
        rng: random.Random,
        temperature: float,
        key_root: str,
        scale_type: str,
    ) -> int:
        """Choose a pitch with temperature-controlled randomness."""
        from yao.constants.music import SCALE_INTERVALS

        if not chord_pitches:
            return last_pitch

        # Build candidate set: chord tones + scale passing tones based on temperature
        candidates: list[int] = []
        for p in chord_pitches:
            for octave_shift in (-12, 0, 12):
                c = p + octave_shift
                if 48 <= c <= 84:
                    candidates.append(c)

        # Add passing tones (non-chord scale degrees) based on temperature
        if temperature > 0.2 and scale_type in SCALE_INTERVALS:
            from yao.ir.notation import note_name_to_midi

            root = note_name_to_midi(f"{key_root}4")
            scale = SCALE_INTERVALS[scale_type]
            for interval in scale:
                for octave in (-12, 0, 12):
                    p = root + interval + octave
                    if 48 <= p <= 84 and p not in candidates and rng.random() < temperature * 0.5:
                        candidates.append(p)

        if not candidates:
            candidates = chord_pitches

        # Score and select
        scored: list[tuple[float, int]] = []
        for c in candidates:
            interval = abs(c - last_pitch)
            step_score = max(0.0, 5.0 - interval)
            dir_score = 0.0
            if direction > 0 and c > last_pitch or direction < 0 and c < last_pitch:
                dir_score = 2.0
            elif direction == 0:
                dir_score = 1.0
            # Chord tone bonus
            chord_bonus = 2.0 if c % 12 in [p % 12 for p in chord_pitches] else 0.0
            total = step_score + dir_score + chord_bonus
            # Temperature adds noise to scores
            total += rng.gauss(0, temperature * 3)
            scored.append((total, c))

        scored.sort(key=lambda x: -x[0])
        return scored[0][1]

    def _stochastic_duration(
        self,
        base_duration: float,
        rng: random.Random,
        temperature: float,
        beats_per_bar: float,
    ) -> float:
        """Generate a stochastic note duration."""
        # Possible durations: subdivisions and multiplications
        options = [base_duration * 0.5, base_duration, base_duration * 1.5, base_duration * 2.0]
        weights = [temperature * 0.3, 1.0 - temperature * 0.5, temperature * 0.2, temperature * 0.1]
        # Normalize weights
        total_w = sum(weights)
        weights = [w / total_w for w in weights]

        chosen = rng.choices(options, weights=weights, k=1)[0]
        return max(0.25, min(chosen, beats_per_bar))

    def _chord_at_beat(self, chords: list[ChordEvent], beat: float) -> ChordEvent | None:
        """Find the chord active at a given beat."""
        for chord in chords:
            if chord.start_beat <= beat < chord.end_beat():
                return chord
        preceding = [c for c in chords if c.start_beat <= beat]
        return preceding[-1] if preceding else (chords[0] if chords else None)

    def _realize_chord_pitches(self, chord_event: ChordEvent, key_root: str, scale_type: str) -> list[int]:
        """Convert a ChordEvent's roman numeral to MIDI pitches."""
        from yao.ir.harmony import diatonic_quality

        roman_map = {"i": 0, "ii": 1, "iii": 2, "iv": 3, "v": 4, "vi": 5, "vii": 6}
        cleaned = chord_event.roman.strip().replace("b", "").replace("#", "")
        base = cleaned.rstrip("7").rstrip("maj").rstrip("dim").rstrip("aug")
        degree = roman_map.get(base.lower(), 0)
        quality = diatonic_quality(degree, scale_type)
        if "7" in chord_event.roman:
            quality = "dom7" if quality == "maj" else "min7"

        try:
            return realize_chord(ChordFunction(degree=degree, quality=quality), key_root, scale_type, octave=4)
        except Exception:
            from yao.ir.notation import note_name_to_midi

            root = note_name_to_midi(f"{key_root}4")
            return [root, root + 4, root + 7]

    def _beats_per_bar(self, time_signature: str) -> float:
        """Extract beats per bar from time signature string."""
        parts = time_signature.split("/")
        return float(parts[0]) if len(parts) == 2 else 4.0
