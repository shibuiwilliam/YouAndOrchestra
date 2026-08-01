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

from yao.constants.genre_profile import GenreProfile, get_genre_profile
from yao.generators.note.accompaniment import (
    build_recall_map,
    develop_melody,
    genre_melodic_variation,
    instrument_roles,
    realize_accompaniment_for_role,
)
from yao.generators.note.base import NoteRealizerBase, register_note_realizer
from yao.generators.note.rule_based_v2 import (
    _apply_motif_transform,
    _contour_direction,
    _density_to_notes_per_beat,
    _parse_key,
    _tension_to_velocity,
)
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

        # Load genre profile for genre-specific biases
        genre_name = ""
        if hasattr(ctx, "genre") and ctx.genre:
            genre_name = ctx.genre.lower()
        genre_profile = get_genre_profile(genre_name) if genre_name else None

        provenance.record(
            layer="generator",
            operation="note_realization_v2",
            parameters={
                "realizer": "stochastic_v2",
                "seed": seed,
                "temperature": temperature,
                "key": ctx.key,
                "tempo": ctx.tempo_bpm,
                "genre_profile": genre_name if genre_profile else None,
                "consumed_fields": list(self.consumed_plan_fields),
            },
            source="StochasticNoteRealizerV2.realize",
            rationale=f"V2 stochastic plan consumption (seed={seed}, temp={temperature}).",
        )

        # Determine instruments WITH roles so non-melody instruments get
        # accompaniment rendered from the chord plan (not dropped).
        roster = instrument_roles(plan)
        melody_names = [name for name, role in roster if role == "melody"]
        melody_instrument = melody_names[0] if melody_names else roster[0][0]

        if plan.drums:
            provenance.record(
                layer="generator",
                operation="drum_pattern_acknowledged",
                parameters={"drum_genre": plan.drums.genre if hasattr(plan.drums, "genre") else "none"},
                source="StochasticNoteRealizerV2.realize",
                rationale="Drum pattern informs rhythmic density choices.",
            )

        beats_per_bar = self._beats_per_bar(ctx.time_signature)

        # Cross-section thematic recall: return sections restate the theme
        # (honors ``recall_melody_from`` from the v1 spec, matching the legacy
        # generator so ``thematic_development`` works on the v2 path too).
        recall_map = build_recall_map(original_spec)
        realized_melodies: dict[str, tuple[list[Note], float]] = {}
        recall_counts: dict[str, int] = {}
        allow_blue = bool(genre_profile and genre_profile.blue_note_probability > 0.0)

        sections: list[Section] = []
        carry_pitch = 60  # Carries across sections for continuity
        for section_plan in plan.form.sections:
            section_start_beat = section_plan.start_bar * beats_per_bar
            recall_source = recall_map.get(section_plan.id)
            if recall_source is not None and recall_source in realized_melodies:
                src_notes, src_start = realized_melodies[recall_source]
                recall_counts[recall_source] = recall_counts.get(recall_source, 0) + 1
                variation = genre_melodic_variation(genre_profile, recall_counts[recall_source])
                recall_chords = [ce for ce in plan.harmony.chord_events if ce.section_id == section_plan.id]
                # Develop the theme (genre-aware variation) rather than copying it
                # note-for-note — an exact restatement reads as monotony. The
                # opening/closing notes anchor the theme so it stays recognizable.
                section_notes = develop_melody(
                    src_notes,
                    src_start,
                    section_start_beat,
                    melody_instrument,
                    key_root=key_root,
                    scale_type=scale_type,
                    section_chords=recall_chords,
                    variation=variation,
                    rng=rng,
                    allow_blue=allow_blue,
                )
                if section_notes:
                    carry_pitch = section_notes[-1].pitch
                provenance.record(
                    layer="generator",
                    operation="thematic_recall_v2",
                    parameters={
                        "section": section_plan.id,
                        "recalls": recall_source,
                        "variation": round(variation, 3),
                        "recall_index": recall_counts[recall_source],
                    },
                    source="StochasticNoteRealizerV2.realize",
                    rationale=(
                        f"Section '{section_plan.id}' develops the theme from "
                        f"'{recall_source}' (variation={variation:.2f})."
                    ),
                )
            else:
                section_notes, carry_pitch = self._realize_section(
                    section_plan=section_plan,
                    plan=plan,
                    key_root=key_root,
                    scale_type=scale_type,
                    beats_per_bar=beats_per_bar,
                    melody_instrument=melody_instrument,
                    rng=rng,
                    temperature=temperature,
                    provenance=provenance,
                    genre_profile=genre_profile,
                    carry_pitch=carry_pitch,
                )
            realized_melodies[section_plan.id] = (section_notes, section_start_beat)

            section_chords = [ce for ce in plan.harmony.chord_events if ce.section_id == section_plan.id]
            base_velocity = _tension_to_velocity(section_plan.target_tension)

            walking_bass = bool(genre_profile and getattr(genre_profile, "bass_motion_style", "") == "walking")
            velocity_boosts: dict[str, int] = (
                {i.name: i.velocity_boost for i in original_spec.instruments} if original_spec else {}
            )
            parts: list[Part] = [Part(instrument=melody_instrument, notes=tuple(section_notes))]
            for name, role in roster:
                if name == melody_instrument:
                    continue  # already rendered as the lead melody
                acc_notes = realize_accompaniment_for_role(
                    role=role,
                    instrument=name,
                    section_chords=section_chords,
                    key_root=key_root,
                    scale_type=scale_type,
                    base_velocity=base_velocity,
                    beats_per_bar=beats_per_bar,
                    density=section_plan.target_density,
                    walking_bass=walking_bass,
                    velocity_boost=velocity_boosts.get(name, 0),
                )
                parts.append(Part(instrument=name, notes=tuple(acc_notes)))

            sections.append(
                Section(
                    name=section_plan.id,
                    start_bar=section_plan.start_bar,
                    end_bar=section_plan.end_bar(),
                    parts=tuple(parts),
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
        genre_profile: GenreProfile | None = None,
        carry_pitch: int = 60,
    ) -> tuple[list[Note], int]:
        """Realize a section with stochastic variation and motif-driven fill.

        Returns:
            Tuple of (notes, last_pitch) where last_pitch is carried to the
            next section for melodic continuity.
        """
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

        # Extract motif interval shape for fill continuation, scaled by the
        # genre leap factor so the fill matches the (compressed/expanded) motif
        # and doesn't reintroduce wide leaps the motif realization removed.
        leap_prob = float(getattr(genre_profile, "leap_probability", 0.3)) if genre_profile else 0.3
        leap_scale = max(0.5, min(1.2, 0.5 + leap_prob * 1.6))
        motif_intervals: list[int] = []
        if plan.motif and plan.motif.seeds:
            primary_seed = plan.motif.seeds[0]
            motif_intervals = [int(round(iv * leap_scale)) for iv in primary_seed.interval_shape]

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
                genre_profile,
            )
            for n in motif_notes:
                motif_beats.add(n.start_beat)
            notes.extend(motif_notes)

        # Fill with motif-shape-aware melody (not random walk)
        beat = section_start_beat
        last_pitch = carry_pitch
        base_duration = 1.0 / max(notes_per_beat, 0.5)
        fill_step_index = 0  # Cycles through motif intervals for fill

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

            # Motif-driven pitch choice: use motif intervals to bias fill
            pitch = self._choose_pitch_motif_aware(
                chord_pitches=chord_pitches,
                last_pitch=last_pitch,
                direction=direction,
                rng=rng,
                temperature=temperature,
                key_root=key_root,
                scale_type=scale_type,
                motif_intervals=motif_intervals,
                fill_step_index=fill_step_index,
                genre_profile=genre_profile,
            )
            fill_step_index += 1

            # Stochastic velocity
            vel_base = int(base_velocity * (0.7 + 0.3 * current_chord.tension_level))
            vel_variation = int(rng.gauss(0, 8 * temperature))
            velocity = max(30, min(127, vel_base + vel_variation))

            # Stochastic duration
            duration = self._stochastic_duration(base_duration, rng, temperature, beats_per_bar)
            if current_chord.cadence_role is not None:
                duration = min(duration * 1.5, beats_per_bar)
                velocity = min(velocity + 10, 127)

            # Genre-biased swing: offset off-beat notes by swing ratio
            swing_offset = 0.0
            if genre_profile and genre_profile.swing_ratio > 0.51:
                beat_fraction = beat % 1.0
                if 0.4 < beat_fraction < 0.6:
                    swing_offset = (genre_profile.swing_ratio - 0.5) * 0.5

            notes.append(
                Note(
                    pitch=pitch,
                    start_beat=max(0.0, beat + swing_offset),
                    duration_beats=duration,
                    velocity=velocity,
                    instrument=melody_instrument,
                )
            )

            last_pitch = pitch
            beat += duration

        return notes, last_pitch

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
        genre_profile: GenreProfile | None = None,
    ) -> list[Note]:
        """Realize a motif with stochastic micro-variations.

        The motif's interval shape is scaled by a genre leap factor so the same
        seed reads as gentle and stepwise in ambient/downtempo genres and as
        wide and angular in jazz/classical — without changing the motif's
        contour (direction of each interval is preserved), so the theme and its
        recalls stay recognizably the same idea.
        """
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

        # Genre leap factor: compress interval magnitudes for stepwise genres,
        # keep them wide for leapy ones (contour/sign preserved).
        leap_prob = float(getattr(genre_profile, "leap_probability", 0.3)) if genre_profile else 0.3
        leap_scale = max(0.5, min(1.2, 0.5 + leap_prob * 1.6))

        notes: list[Note] = []
        beat = placement.start_beat
        current_pitch = root_pitch

        for i, dur in enumerate(rhythm):
            if i < len(intervals):
                scaled_iv = int(round(intervals[i] * leap_scale))
                # Preserve contour: never let scaling flip a real interval to 0.
                if intervals[i] != 0 and scaled_iv == 0:
                    scaled_iv = 1 if intervals[i] > 0 else -1
                current_pitch = root_pitch + scaled_iv
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

    def _choose_pitch_motif_aware(
        self,
        chord_pitches: list[int],
        last_pitch: int,
        direction: int,
        rng: random.Random,
        temperature: float,
        key_root: str,
        scale_type: str,
        motif_intervals: list[int],
        fill_step_index: int,
        genre_profile: GenreProfile | None = None,
    ) -> int:
        """Choose a pitch biased by motif interval shape for thematic continuity.

        When motif intervals are available, the fill preferentially follows the
        motif's interval contour (cycling through it with variations controlled
        by temperature). This keeps the fill thematically related rather than
        producing a random walk. Falls back to chord-tone-biased selection when
        no motif is available.

        Genre character is layered on top: ``leap_probability`` decides whether
        this step reaches for a wider interval (jazz leaps vs. ambient steps),
        and ``blue_note_probability`` adds b3/b5/b7 candidates with a bonus so
        blues/jazz melodies pick up idiomatic colour. Both are no-ops when the
        genre profile is absent, so non-genre generation is unchanged.
        """
        from yao.constants.music import SCALE_INTERVALS
        from yao.ir.notation import note_name_to_midi

        if not chord_pitches:
            return last_pitch

        leap_prob = float(getattr(genre_profile, "leap_probability", 0.0)) if genre_profile else 0.0
        blue_prob = float(getattr(genre_profile, "blue_note_probability", 0.0)) if genre_profile else 0.0
        blue_pcs: set[int] = set()
        if blue_prob > 0.0:
            root_pc = note_name_to_midi(f"{key_root}4") % 12
            blue_pcs = {(root_pc + off) % 12 for off in (3, 6, 10)}

        # Build candidate set: chord tones + scale passing tones
        candidates: list[int] = []
        for p in chord_pitches:
            for octave_shift in (-12, 0, 12):
                c = p + octave_shift
                if 48 <= c <= 84:
                    candidates.append(c)

        root = note_name_to_midi(f"{key_root}4")
        if temperature > 0.2 and scale_type in SCALE_INTERVALS:  # noqa: PLR2004
            scale = SCALE_INTERVALS[scale_type]
            for interval in scale:
                for octave in (-12, 0, 12):
                    p = root + interval + octave
                    if 48 <= p <= 84 and p not in candidates and rng.random() < temperature * 0.5:  # noqa: PLR2004
                        candidates.append(p)

        # Blue-note candidates (b3/b5/b7) for genres that use them.
        for off in (3, 6, 10) if blue_pcs else ():
            for octave in (-12, 0, 12):
                p = root + off + octave
                if 48 <= p <= 84 and p not in candidates:  # noqa: PLR2004
                    candidates.append(p)

        if not candidates:
            candidates = chord_pitches

        # Genre leap character: decide once per note whether to reach for a
        # wider interval instead of the default stepwise preference.
        want_leap = leap_prob > 0.0 and rng.random() < leap_prob

        # Compute motif-suggested target pitch
        motif_target: int | None = None
        if motif_intervals:
            idx = fill_step_index % len(motif_intervals)
            suggested_interval = motif_intervals[idx]
            # Add temperature-scaled variation to the interval
            if temperature > 0.1 and rng.random() < temperature * 0.4:  # noqa: PLR2004
                suggested_interval += rng.choice([-1, 0, 1])
            # Register fold: an all-ascending motif shape cycled as a target
            # marches the fill up to the ceiling (a monotony/leap artifact).
            # Reflect the interval's direction when we drift out of a central
            # tessitura so the melody breathes up and down instead.
            if last_pitch >= 71 and suggested_interval > 0 or last_pitch <= 55 and suggested_interval < 0:  # noqa: PLR2004
                suggested_interval = -suggested_interval
            motif_target = last_pitch + suggested_interval

        # Score candidates
        chord_pcs = {p % 12 for p in chord_pitches}
        scored: list[tuple[float, int]] = []
        # Target interval size: leaping notes reach for ~a fifth, otherwise
        # stepwise. Scoring the *distance from target* (not just "small is
        # good") means low-leap genres genuinely favour steps and octave-
        # displaced candidates are penalised — so ambient stays stepwise while
        # jazz/classical leap. Previously all intervals >=5 scored equally,
        # which let every genre leap indiscriminately.
        target_interval = 6 if want_leap else 2
        for c in candidates:
            interval = abs(c - last_pitch)
            step_score = max(0.0, 5.0 - abs(interval - target_interval))
            dir_score = 0.0
            if direction > 0 and c > last_pitch or direction < 0 and c < last_pitch:
                dir_score = 2.0
            elif direction == 0:
                dir_score = 1.0
            chord_bonus = 2.0 if c % 12 in chord_pcs else 0.0
            # Motif proximity bonus: reward candidates near motif target
            motif_bonus = 0.0
            if motif_target is not None:
                dist = abs(c - motif_target)
                motif_bonus = max(0.0, 4.0 - dist)  # Strong bonus for exact match
            # Blue-note colour bonus (scaled by how bluesy the genre is).
            blue_bonus = blue_prob * 4.0 if c % 12 in blue_pcs else 0.0
            total = step_score + dir_score + chord_bonus + motif_bonus + blue_bonus
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
        """Convert a ChordEvent's roman numeral to MIDI pitches.

        Delegates to the shared ``accompaniment.chord_pitches`` so melody,
        harmony, and bass agree on chord content (including the harmonic-minor
        major-V) — avoiding a melody/harmony clash at cadences.
        """
        from yao.generators.note.accompaniment import chord_pitches

        return chord_pitches(chord_event, key_root, scale_type)

    def _beats_per_bar(self, time_signature: str) -> float:
        """Extract beats per bar from time signature string."""
        parts = time_signature.split("/")
        return float(parts[0]) if len(parts) == 2 else 4.0
