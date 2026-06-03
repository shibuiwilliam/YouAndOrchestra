"""Rule-based note realizer V2 — consumes MusicalPlan directly.

Unlike the v1 adapter (rule_based.py), this realizer reads MusicalPlan
fields directly without converting to v1 CompositionSpec. Every chord,
motif, phrase, and section parameter is consumed from the plan.

This is the true V2 pipeline implementation (Wave 1.4).

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from yao.generators.note.base import NoteRealizerBase, register_note_realizer
from yao.ir.harmony import ChordFunction
from yao.ir.harmony import realize as realize_chord
from yao.ir.note import Note
from yao.ir.plan.harmony import ChordEvent
from yao.ir.plan.motif import MotifPlacement, MotifTransform
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.phrase import Phrase, PhraseContour
from yao.ir.plan.song_form import SectionPlan
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog

if TYPE_CHECKING:
    from yao.schema.composition import CompositionSpec


def _parse_key(key_str: str) -> tuple[str, str]:
    """Parse 'C major' into ('C', 'major')."""
    parts = key_str.strip().split()
    if len(parts) >= 2:
        return parts[0], parts[1]
    return parts[0], "major"


def _tension_to_velocity(tension: float) -> int:
    """Map tension [0,1] to MIDI velocity [40, 110]."""
    return int(40 + tension * 70)


def _density_to_notes_per_beat(density: float) -> float:
    """Map density [0,1] to approximate notes per beat."""
    return 0.5 + density * 1.5  # range: 0.5 to 2.0 notes per beat


def _apply_motif_transform(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
    transform: MotifTransform,
    rng: random.Random | None = None,
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Apply a transformation to motif intervals and rhythm.

    Args:
        intervals: Interval pattern (semitones from first note).
        rhythm: Duration pattern (beats).
        transform: Which transformation to apply.
        rng: Random generator for stochastic transforms. None = deterministic.

    Returns:
        Transformed (intervals, rhythm) tuple.
    """
    if transform == MotifTransform.IDENTITY:
        return intervals, rhythm
    elif transform == MotifTransform.INVERSION:
        return tuple(-i for i in intervals), rhythm
    elif transform == MotifTransform.RETROGRADE:
        return tuple(reversed(intervals)), tuple(reversed(rhythm))
    elif transform == MotifTransform.AUGMENTATION:
        return intervals, tuple(r * 2.0 for r in rhythm)
    elif transform == MotifTransform.DIMINUTION:
        return intervals, tuple(r * 0.5 for r in rhythm)
    elif transform == MotifTransform.SEQUENCE_UP:
        return tuple(i + 2 for i in intervals), rhythm
    elif transform == MotifTransform.SEQUENCE_DOWN:
        return tuple(i - 2 for i in intervals), rhythm
    elif transform == MotifTransform.ORNAMENT_ADD:
        return _transform_ornament_add(intervals, rhythm, rng)
    elif transform == MotifTransform.ORNAMENT_REMOVE:
        return _transform_ornament_remove(intervals, rhythm)
    elif transform == MotifTransform.RHYTHM_DISPLACE:
        return _transform_rhythm_displace(intervals, rhythm, rng)
    elif transform == MotifTransform.INTERVAL_FILL:
        return _transform_interval_fill(intervals, rhythm)
    elif transform == MotifTransform.INTERVAL_LEAP:
        return _transform_interval_leap(intervals, rhythm)
    elif transform == MotifTransform.OCTAVE_DISPLACE:
        return _transform_octave_displace(intervals, rhythm, rng)
    elif transform == MotifTransform.EXPAND:
        return _transform_expand(intervals, rhythm)
    elif transform == MotifTransform.CONTRACT:
        return _transform_contract(intervals, rhythm, rng)
    elif transform == MotifTransform.FRAGMENT:
        return _transform_fragment(intervals, rhythm, rng)
    elif transform == MotifTransform.EXTEND:
        return _transform_extend(intervals, rhythm, rng)
    elif transform == MotifTransform.QUESTION_ANSWER:
        return _transform_question_answer(intervals, rhythm)
    else:
        return intervals, rhythm


def _transform_ornament_add(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
    rng: random.Random | None,
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Add passing/neighbor tones before some notes."""
    if not intervals:
        return intervals, rhythm
    new_iv: list[int] = []
    new_rh: list[float] = []
    for i, (iv, r) in enumerate(zip(intervals, rhythm, strict=False)):
        if rng and rng.random() < 0.4 and r >= 0.5 and i > 0:
            mid = (intervals[i - 1] + iv) // 2
            new_iv.append(mid)
            new_rh.append(r * 0.25)
            new_iv.append(iv)
            new_rh.append(r * 0.75)
        else:
            new_iv.append(iv)
            new_rh.append(r)
    return tuple(new_iv), tuple(new_rh)


def _transform_ornament_remove(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Remove short ornamental notes, merging their duration."""
    if len(intervals) <= 2:  # noqa: PLR2004
        return intervals, rhythm
    new_iv: list[int] = []
    new_rh: list[float] = []
    for _i, (iv, r) in enumerate(zip(intervals, rhythm, strict=False)):
        if r < 0.5 and new_rh:
            new_rh[-1] += r
        else:
            new_iv.append(iv)
            new_rh.append(r)
    if not new_iv:
        return intervals, rhythm
    return tuple(new_iv), tuple(new_rh)


def _transform_rhythm_displace(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
    rng: random.Random | None,
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Keep pitches, replace rhythm pattern."""
    templates = [
        (1.5, 0.5, 1.0, 1.0),
        (0.5, 0.5, 0.5, 0.5, 1.0, 1.0),
        (1.0, 0.5, 0.5, 1.0, 1.0),
        (2.0, 1.0, 1.0),
    ]
    chosen = list(rng.choice(templates) if rng else templates[0])
    target_len = len(intervals)
    if len(chosen) >= target_len:
        chosen = chosen[:target_len]
    else:
        chosen.extend([1.0] * (target_len - len(chosen)))
    total_original = sum(rhythm)
    total_new = sum(chosen)
    if total_new > 0:
        scale = total_original / total_new
        chosen = [r * scale for r in chosen]
    return intervals, tuple(chosen)


def _transform_interval_fill(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Fill large leaps with passing tones."""
    if len(intervals) < 2:  # noqa: PLR2004
        return intervals, rhythm
    new_iv: list[int] = [intervals[0]]
    new_rh: list[float] = [rhythm[0]] if rhythm else [1.0]
    for i in range(1, len(intervals)):
        gap = intervals[i] - intervals[i - 1]
        r = rhythm[i] if i < len(rhythm) else 1.0
        if abs(gap) >= 4:  # noqa: PLR2004
            mid = intervals[i - 1] + gap // 2
            new_iv.append(mid)
            new_rh.append(r * 0.4)
            new_iv.append(intervals[i])
            new_rh.append(r * 0.6)
        else:
            new_iv.append(intervals[i])
            new_rh.append(r)
    return tuple(new_iv), tuple(new_rh)


def _transform_interval_leap(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Collapse small steps into leaps."""
    if len(intervals) < 3:  # noqa: PLR2004
        return intervals, rhythm
    new_iv: list[int] = [intervals[0]]
    new_rh: list[float] = [rhythm[0]] if rhythm else [1.0]
    i = 1
    while i < len(intervals):
        if (
            i + 1 < len(intervals)
            and abs(intervals[i] - intervals[i - 1]) <= 2  # noqa: PLR2004
            and abs(intervals[i + 1] - intervals[i]) <= 2  # noqa: PLR2004
        ):
            r1 = rhythm[i] if i < len(rhythm) else 0.5
            r2 = rhythm[i + 1] if i + 1 < len(rhythm) else 0.5
            new_iv.append(intervals[i + 1])
            new_rh.append(r1 + r2)
            i += 2
        else:
            new_iv.append(intervals[i])
            new_rh.append(rhythm[i] if i < len(rhythm) else 1.0)
            i += 1
    return tuple(new_iv), tuple(new_rh)


def _transform_octave_displace(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
    rng: random.Random | None,
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Displace some notes by an octave."""
    if not rng or not intervals:
        return intervals, rhythm
    new_iv = list(intervals)
    n_shift = max(1, len(intervals) // 3)
    indices = rng.sample(range(len(intervals)), min(n_shift, len(intervals)))
    for idx in indices:
        new_iv[idx] += rng.choice([-12, 12])
    return tuple(new_iv), rhythm


def _transform_expand(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Add passing tones between each note to expand the motif."""
    if len(intervals) < 2:  # noqa: PLR2004
        return intervals, rhythm
    new_iv: list[int] = []
    new_rh: list[float] = []
    for i, (iv, r) in enumerate(zip(intervals, rhythm, strict=False)):
        new_iv.append(iv)
        new_rh.append(r * 0.6)
        if i + 1 < len(intervals):
            mid = (iv + intervals[i + 1]) // 2
            new_iv.append(mid)
            new_rh.append(r * 0.4)
    return tuple(new_iv), tuple(new_rh)


def _transform_contract(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
    rng: random.Random | None,
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Remove some notes to contract the motif."""
    if len(intervals) <= 2:  # noqa: PLR2004
        return intervals, rhythm
    n_keep = max(2, len(intervals) // 2)
    indices = sorted(rng.sample(range(len(intervals)), n_keep)) if rng else list(range(0, len(intervals), 2))[:n_keep]
    new_iv = tuple(intervals[i] for i in indices)
    new_rh: list[float] = []
    last_idx = 0
    for idx in indices:
        accumulated = (
            sum(rhythm[last_idx : idx + 1])
            if idx >= last_idx and idx < len(rhythm)
            else (rhythm[idx] if idx < len(rhythm) else 1.0)
        )
        new_rh.append(accumulated)
        last_idx = idx + 1
    return new_iv, tuple(new_rh)


def _transform_fragment(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
    rng: random.Random | None,
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Extract the first or second half of the motif."""
    half = max(2, len(intervals) // 2)
    if rng and rng.random() < 0.5:
        return intervals[:half], rhythm[:half]
    return intervals[-half:], rhythm[-half:] if len(rhythm) >= half else rhythm


def _transform_extend(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
    rng: random.Random | None,
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Add 2 notes to extend the motif."""
    if not intervals:
        return intervals, rhythm
    last = intervals[-1]
    a1 = last + (rng.choice([-2, -1, 1, 2]) if rng else 1)
    a2 = last + (rng.choice([-3, -2, 2, 3]) if rng else 2)
    avg_r = sum(rhythm) / len(rhythm) if rhythm else 1.0
    return intervals + (a1, a2), rhythm + (avg_r * 0.7, avg_r * 0.7)


def _transform_question_answer(
    intervals: tuple[int, ...],
    rhythm: tuple[float, ...],
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Transform second half into a "response" by inverting direction."""
    if len(intervals) < 4:  # noqa: PLR2004
        return intervals, rhythm
    half = len(intervals) // 2
    first_half = intervals[:half]
    peak = max(first_half) if first_half else 0
    second_half = tuple(peak - (iv - intervals[half]) for iv in intervals[half:])
    return first_half + second_half, rhythm


def _contour_direction(contour: PhraseContour, position: float) -> int:
    """Get melodic direction bias for a contour at a given position [0,1].

    Returns: -1 (descend), 0 (neutral), 1 (ascend)
    """
    if contour == PhraseContour.RISE:
        return 1
    elif contour == PhraseContour.FALL:
        return -1
    elif contour == PhraseContour.ARCH:
        return 1 if position < 0.5 else -1
    elif contour == PhraseContour.INVERTED_ARCH:
        return -1 if position < 0.5 else 1
    elif contour == PhraseContour.WAVE:
        return 1 if (position * 4) % 2 < 1 else -1
    return 0


@register_note_realizer("rule_based_v2")
class RuleBasedNoteRealizerV2(NoteRealizerBase):
    """V2 note realizer that directly consumes MusicalPlan.

    No _plan_to_v1_spec(). No legacy_adapter. Every musical decision
    flows from plan fields to concrete notes with full provenance.
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
        """Realize a MusicalPlan into ScoreIR by direct plan consumption.

        Args:
            plan: The musical plan to realize.
            seed: Random seed for any stochastic choices.
            temperature: Not used in rule-based (deterministic).
            provenance: Provenance log.
            original_spec: Ignored in V2 (all data from plan).

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
                "realizer": "rule_based_v2",
                "seed": seed,
                "key": ctx.key,
                "tempo": ctx.tempo_bpm,
                "consumed_fields": list(self.consumed_plan_fields),
            },
            source="RuleBasedNoteRealizerV2.realize",
            rationale="V2 direct plan consumption — no legacy adapter.",
        )

        # Determine instruments from arrangement or global context
        if plan.arrangement and plan.arrangement.assignments:
            # Use arrangement plan for instrument roles
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

        # Record drum pattern consumption (affects rhythm density decisions)
        if plan.drums:
            provenance.record(
                layer="generator",
                operation="drum_pattern_acknowledged",
                parameters={"drum_genre": plan.drums.genre if hasattr(plan.drums, "genre") else "none"},
                source="RuleBasedNoteRealizerV2.realize",
                rationale="Drum pattern informs rhythmic density choices.",
            )

        # Build sections
        sections: list[Section] = []
        beats_per_bar = self._beats_per_bar(ctx.time_signature)

        carry_pitch = 60  # Carries across sections for melodic continuity
        for section_plan in plan.form.sections:
            section_notes, carry_pitch = self._realize_section(
                section_plan=section_plan,
                plan=plan,
                key_root=key_root,
                scale_type=scale_type,
                beats_per_bar=beats_per_bar,
                melody_instrument=melody_instrument,
                rng=rng,
                provenance=provenance,
                carry_pitch=carry_pitch,
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
        provenance: ProvenanceLog,
        carry_pitch: int = 60,
    ) -> tuple[list[Note], int]:
        """Realize a single section into notes.

        Returns:
            Tuple of (notes, last_pitch) where last_pitch is carried to the
            next section for melodic continuity.
        """
        notes: list[Note] = []
        section_start_beat = section_plan.start_bar * beats_per_bar
        section_end_beat = section_plan.end_bar() * beats_per_bar

        # Get chord events for this section
        section_chords = [ce for ce in plan.harmony.chord_events if ce.section_id == section_plan.id]

        # Get motif placements for this section
        motif_placements: list[MotifPlacement] = []
        if plan.motif:
            motif_placements = plan.motif.placements_in_section(section_plan.id)

        # Get phrases for this section
        section_phrases: list[Phrase] = []
        if plan.phrase:
            section_phrases = plan.phrase.phrases_in_section(section_plan.id)

        # Base velocity from section tension
        base_velocity = _tension_to_velocity(section_plan.target_tension)
        notes_per_beat = _density_to_notes_per_beat(section_plan.target_density)

        # Realize motif placements first (they have priority)
        motif_beats: set[float] = set()
        for placement in motif_placements:
            motif_notes = self._realize_motif_placement(
                placement=placement,
                plan=plan,
                key_root=key_root,
                scale_type=scale_type,
                base_velocity=base_velocity,
                melody_instrument=melody_instrument,
                section_chords=section_chords,
            )
            for n in motif_notes:
                motif_beats.add(n.start_beat)
            notes.extend(motif_notes)

        # Fill remaining beats with chord-based melody
        beat = section_start_beat
        note_duration = 1.0 / max(notes_per_beat, 0.5)
        last_pitch = carry_pitch

        while beat < section_end_beat:
            # Skip beats occupied by motifs
            if any(abs(beat - mb) < 0.25 for mb in motif_beats):
                beat += note_duration
                continue

            # Find current chord
            current_chord = self._chord_at_beat(section_chords, beat)
            if current_chord is None:
                beat += note_duration
                continue

            # Get chord tones
            chord_pitches = self._realize_chord_pitches(current_chord, key_root, scale_type)
            if not chord_pitches:
                beat += note_duration
                continue

            # Apply phrase contour
            direction = 0
            for phrase in section_phrases:
                if phrase.start_beat <= beat < phrase.end_beat():
                    position = (beat - phrase.start_beat) / max(phrase.length_beats, 1.0)
                    direction = _contour_direction(phrase.contour, position)
                    break

            # Choose pitch based on chord, contour, and voice leading
            pitch = self._choose_pitch(chord_pitches, last_pitch, direction, rng)

            # Velocity from chord tension_level
            velocity = int(base_velocity * (0.7 + 0.3 * current_chord.tension_level))
            velocity = max(30, min(127, velocity))

            # Cadence emphasis: longer notes at cadence points
            duration = note_duration
            if current_chord.cadence_role is not None:
                duration = min(note_duration * 1.5, beats_per_bar)
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
            beat += note_duration

        return notes, last_pitch

    def _realize_motif_placement(
        self,
        placement: MotifPlacement,
        plan: MusicalPlan,
        key_root: str,
        scale_type: str,
        base_velocity: int,
        melody_instrument: str,
        section_chords: list[ChordEvent],
    ) -> list[Note]:
        """Realize a single motif placement into concrete notes."""
        if plan.motif is None:
            return []

        seed_motif = plan.motif.seed_by_id(placement.motif_id)
        if seed_motif is None:
            return []

        # Apply transformation
        intervals, rhythm = _apply_motif_transform(
            seed_motif.interval_shape,
            seed_motif.rhythm_shape,
            placement.transform,
        )

        # Find chord at placement position for root pitch
        chord_at = self._chord_at_beat(section_chords, placement.start_beat)
        if chord_at:
            chord_pitches = self._realize_chord_pitches(chord_at, key_root, scale_type)
            root_pitch = chord_pitches[0] if chord_pitches else 60
        else:
            from yao.ir.notation import note_name_to_midi

            root_pitch = note_name_to_midi(f"{key_root}4")

        # Apply transposition
        root_pitch += placement.transposition

        # Generate notes from motif shape
        notes: list[Note] = []
        beat = placement.start_beat
        current_pitch = root_pitch

        for i, dur in enumerate(rhythm):
            if i < len(intervals):
                current_pitch = root_pitch + intervals[i]

            velocity = max(30, min(127, base_velocity))
            notes.append(
                Note(
                    pitch=max(0, min(127, current_pitch)),
                    start_beat=beat,
                    duration_beats=dur,
                    velocity=velocity,
                    instrument=melody_instrument,
                )
            )
            beat += dur

        return notes

    def _realize_chord_pitches(
        self,
        chord_event: ChordEvent,
        key_root: str,
        scale_type: str,
    ) -> list[int]:
        """Convert a ChordEvent's roman numeral to MIDI pitches."""
        try:
            chord_func = self._roman_to_chord_function(chord_event.roman, scale_type)
            return realize_chord(chord_func, key_root, scale_type, octave=4)
        except Exception:
            # Fallback: return basic triad on root
            from yao.ir.notation import note_name_to_midi

            root = note_name_to_midi(f"{key_root}4")
            return [root, root + 4, root + 7]

    def _roman_to_chord_function(self, roman: str, scale_type: str) -> ChordFunction:
        """Parse a Roman numeral string into a ChordFunction.

        Handles: I, ii, III, IV, V, vi, vii, bVII, and 7th variants.
        """
        from yao.ir.harmony import diatonic_quality

        # Map roman numeral text to degree
        roman_map = {
            "i": 0,
            "ii": 1,
            "iii": 2,
            "iv": 3,
            "v": 4,
            "vi": 5,
            "vii": 6,
        }

        cleaned = roman.strip().replace("b", "").replace("#", "")
        # Remove 7, maj7, etc. suffixes for degree lookup
        base = cleaned.rstrip("7").rstrip("maj").rstrip("dim").rstrip("aug")
        degree = roman_map.get(base.lower(), 0)

        # Determine quality from case and scale
        quality = diatonic_quality(degree, scale_type)
        if "7" in roman:
            if quality == "maj":
                quality = "dom7"
            elif quality == "min":
                quality = "min7"

        return ChordFunction(degree=degree, quality=quality)

    def _chord_at_beat(
        self,
        chords: list[ChordEvent],
        beat: float,
    ) -> ChordEvent | None:
        """Find the chord active at a given beat."""
        for chord in chords:
            if chord.start_beat <= beat < chord.end_beat():
                return chord
        # If no exact match, return the last chord before this beat
        preceding = [c for c in chords if c.start_beat <= beat]
        return preceding[-1] if preceding else (chords[0] if chords else None)

    def _choose_pitch(
        self,
        chord_pitches: list[int],
        last_pitch: int,
        direction: int,
        rng: random.Random,
    ) -> int:
        """Choose a pitch from chord tones with voice leading and contour."""
        if not chord_pitches:
            return last_pitch

        # Expand chord pitches to nearby octaves
        candidates: list[int] = []
        for p in chord_pitches:
            for octave_shift in (-12, 0, 12):
                candidate = p + octave_shift
                if 48 <= candidate <= 84:  # Reasonable melody range
                    candidates.append(candidate)

        if not candidates:
            candidates = chord_pitches

        # Score candidates by voice leading (prefer stepwise) and direction
        scored: list[tuple[float, int]] = []
        for c in candidates:
            interval = abs(c - last_pitch)
            # Prefer small intervals (stepwise = 1-2 semitones)
            step_score = max(0, 5 - interval)
            # Direction bonus
            dir_score = 0
            if direction > 0 and c > last_pitch or direction < 0 and c < last_pitch:
                dir_score = 2
            elif direction == 0:
                dir_score = 1
            scored.append((step_score + dir_score, c))

        # Pick best (deterministic for rule-based)
        scored.sort(key=lambda x: -x[0])
        return scored[0][1]

    def _beats_per_bar(self, time_signature: str) -> float:
        """Extract beats per bar from time signature string."""
        parts = time_signature.split("/")
        if len(parts) == 2:
            return float(parts[0])
        return 4.0
