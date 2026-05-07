"""Layer M3: Surface Realization.

Fills in the surface notes that connect skeleton notes via passing tones,
neighbor tones, and other melodic decorations. Applies rhythm templates
and derives velocity from dynamics curves.

See PROJECT.md §3.2 (Layer M3) and IMPROVEMENT.md §4.1.
"""

from __future__ import annotations

import random

from yao.constants.music import DYNAMICS_TO_VELOCITY, SCALE_INTERVALS
from yao.ir.melody_line import MelodyLine, MelodyNote
from yao.ir.notation import note_name_to_midi
from yao.ir.skeleton import Skeleton, SkeletonNote
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.melodic_profile import MelodicProfile


class SurfaceRealizer:
    """Realizes the melody surface by connecting skeleton notes.

    Takes the structural skeleton from M2 and produces a complete
    MelodyLine by inserting passing tones, neighbor tones, and
    applying the genre's rhythm template.
    """

    def realize(
        self,
        skeleton: Skeleton,
        spec: CompositionSpec,
        profile: MelodicProfile,
        provenance: ProvenanceLog,
        *,
        rng: random.Random | None = None,
    ) -> MelodyLine:
        """Realize the melody surface from a skeleton.

        Args:
            skeleton: The M2 output (structural pitches).
            spec: Composition specification.
            profile: MelodicProfile for interval preferences.
            provenance: Provenance log.
            rng: Random number generator.

        Returns:
            A MelodyLine connecting all skeleton notes.
        """
        if rng is None:
            seed = spec.generation.seed if spec.generation.seed is not None else 42
            rng = random.Random(seed + 2)  # Different offset from M1, M2

        key_parts = spec.key.split()
        root_name = key_parts[0] if key_parts else "C"
        scale_type = key_parts[1] if len(key_parts) > 1 else "major"
        root_midi = note_name_to_midi(f"{root_name}4")
        scale_intervals = list(SCALE_INTERVALS.get(scale_type, SCALE_INTERVALS["major"]))

        # Build full scale across octaves
        scale_pitches = set()
        for octave_offset in range(-12, 25, 12):
            for iv in scale_intervals:
                p = root_midi + octave_offset + iv
                if 0 <= p <= 127:
                    scale_pitches.add(p)
        sorted_scale = sorted(scale_pitches)

        # Get dynamics velocity for the current section
        base_velocity = self._section_velocity(spec)

        # Realize surface between consecutive skeleton notes
        melody_notes: list[MelodyNote] = []
        sorted_skeleton = sorted(skeleton.notes, key=lambda n: (n.bar, n.beat))

        for i, skel_note in enumerate(sorted_skeleton):
            next_skel = sorted_skeleton[i + 1] if i + 1 < len(sorted_skeleton) else None

            # Add the skeleton note itself as a chord tone
            melody_notes.append(
                MelodyNote(
                    bar=skel_note.bar,
                    beat=skel_note.beat,
                    duration_beats=self._note_duration(skel_note, next_skel),
                    midi_pitch=skel_note.midi_pitch,
                    velocity=base_velocity,
                    note_type="chord_tone",
                    skeleton_id=i,
                )
            )

            # Fill between this and next skeleton note
            if next_skel is not None:
                fill_notes = self._fill_between(
                    current=skel_note,
                    target=next_skel,
                    current_idx=i,
                    sorted_scale=sorted_scale,
                    profile=profile,
                    base_velocity=base_velocity,
                    rng=rng,
                )
                melody_notes.extend(fill_notes)

        # Sort by position
        melody_notes.sort(key=lambda n: (n.bar, n.beat))
        melody = MelodyLine(notes=tuple(melody_notes))

        # Record provenance
        note_types: dict[str, int] = {}
        for n in melody_notes:
            note_types[n.note_type] = note_types.get(n.note_type, 0) + 1

        provenance.record(
            layer="M3_surface",
            operation="realize_surface",
            parameters={
                "skeleton_notes": skeleton.note_count,
                "surface_notes": len(melody_notes),
                "note_type_breakdown": note_types,
            },
            source="SurfaceRealizer",
            rationale=(
                f"Realized {len(melody_notes)} surface notes from "
                f"{skeleton.note_count} skeleton notes. "
                f"Types: {note_types}."
            ),
            agent="composer-subagent",
        )

        return melody

    def _fill_between(
        self,
        *,
        current: SkeletonNote,
        target: SkeletonNote,
        current_idx: int,
        sorted_scale: list[int],
        profile: MelodicProfile,
        base_velocity: int,
        rng: random.Random,
    ) -> list[MelodyNote]:
        """Fill the gap between two skeleton notes with surface notes.

        Args:
            current: Current skeleton note.
            target: Next skeleton note.
            current_idx: Index of current skeleton note.
            sorted_scale: Sorted scale pitches.
            profile: MelodicProfile.
            base_velocity: Base velocity.
            rng: Random number generator.

        Returns:
            List of surface MelodyNotes between the two skeleton notes.
        """
        # Calculate time gap
        current_abs = current.bar * 4.0 + current.beat
        target_abs = target.bar * 4.0 + target.beat
        gap_beats = target_abs - current_abs

        if gap_beats <= 0.5:
            return []

        # Determine how many fill notes based on gap and profile
        # Shorter gaps get fewer fills; genre syncopation affects density
        max_fills = max(0, int(gap_beats * (1.0 + profile.syncopation_level)) - 1)
        if max_fills <= 0:
            return []

        # Decide number of fills (1-3 typically)
        num_fills = rng.randint(1, min(max_fills, 3))

        # Generate pitches by stepping through scale between current and target
        fill_pitches = self._stepwise_fill(
            current.midi_pitch,
            target.midi_pitch,
            num_fills,
            sorted_scale,
            profile,
            rng,
        )

        # Place fill notes evenly in the gap
        notes: list[MelodyNote] = []
        fill_duration = gap_beats / (num_fills + 1)
        for j, pitch in enumerate(fill_pitches):
            fill_beat_abs = current_abs + fill_duration * (j + 1)
            fill_bar = int(fill_beat_abs // 4)
            fill_beat = fill_beat_abs % 4.0

            note_type = self._classify_fill_note(pitch, current.midi_pitch, target.midi_pitch, sorted_scale)

            notes.append(
                MelodyNote(
                    bar=fill_bar,
                    beat=round(fill_beat, 4),
                    duration_beats=round(fill_duration * 0.9, 4),
                    midi_pitch=pitch,
                    velocity=int(base_velocity * 0.9),
                    note_type=note_type,
                    skeleton_id=current_idx,
                )
            )

        return notes

    def _stepwise_fill(
        self,
        start_pitch: int,
        end_pitch: int,
        count: int,
        sorted_scale: list[int],
        profile: MelodicProfile,
        rng: random.Random,
    ) -> list[int]:
        """Generate fill pitches stepping through the scale.

        Args:
            start_pitch: Starting MIDI pitch.
            end_pitch: Target MIDI pitch.
            count: Number of fill notes to generate.
            sorted_scale: Available scale pitches.
            profile: MelodicProfile for interval weighting.
            rng: Random number generator.

        Returns:
            List of MIDI pitches for fill notes.
        """
        if count <= 0:
            return []

        if not sorted_scale:
            return [start_pitch] * count

        # Find scale indices
        start_idx = self._nearest_scale_index(start_pitch, sorted_scale)
        end_idx = self._nearest_scale_index(end_pitch, sorted_scale)

        # Determine direction
        direction = 1 if end_idx >= start_idx else -1

        pitches: list[int] = []
        current_idx = start_idx

        for i in range(count):
            # Step toward target, with some randomness
            steps_remaining = count - i
            idx_distance = abs(end_idx - current_idx)

            if idx_distance > 0 and steps_remaining > 0:
                # Average step size needed
                avg_step = idx_distance / steps_remaining
                step = max(1, int(avg_step + rng.uniform(-0.5, 0.5)))
                step = min(step, idx_distance)
            else:
                step = 1

            current_idx += direction * step
            current_idx = max(0, min(current_idx, len(sorted_scale) - 1))

            # Add some chromatic neighbor chance
            pitch = sorted_scale[current_idx]
            if rng.random() < profile.chromaticism_level * 0.3:
                chromatic_offset = rng.choice([-1, 1])
                pitch += chromatic_offset

            pitch = max(0, min(127, pitch))
            pitches.append(pitch)

        return pitches

    def _classify_fill_note(
        self,
        pitch: int,
        from_pitch: int,
        to_pitch: int,
        sorted_scale: list[int],
    ) -> str:
        """Classify a fill note by its melodic function.

        Args:
            pitch: Fill note pitch.
            from_pitch: Previous skeleton pitch.
            to_pitch: Next skeleton pitch.
            sorted_scale: Scale pitches.

        Returns:
            Note type string.
        """
        is_scale = pitch in sorted_scale

        # Check if stepwise motion (passing tone)
        if min(from_pitch, to_pitch) < pitch < max(from_pitch, to_pitch):
            return "passing" if is_scale else "appoggiatura"

        # Neighbor tone (returns to nearby pitch)
        if abs(pitch - from_pitch) <= 2:
            return "neighbor"

        # Anticipation (same as target)
        if pitch == to_pitch:
            return "anticipation"

        return "escape" if not is_scale else "passing"

    def _note_duration(
        self,
        current: SkeletonNote,
        next_note: SkeletonNote | None,
    ) -> float:
        """Calculate duration for a skeleton note.

        Args:
            current: Current skeleton note.
            next_note: Next skeleton note, or None.

        Returns:
            Duration in beats.
        """
        if next_note is None:
            return 1.0

        gap = (next_note.bar * 4.0 + next_note.beat) - (current.bar * 4.0 + current.beat)
        # Skeleton note gets about 40% of the gap (rest goes to fills)
        return max(0.25, min(2.0, gap * 0.4))

    def _section_velocity(self, spec: CompositionSpec) -> int:
        """Get base velocity from the first section's dynamics.

        Args:
            spec: Composition specification.

        Returns:
            MIDI velocity value.
        """
        if spec.sections:
            dyn = spec.sections[0].dynamics
            return DYNAMICS_TO_VELOCITY.get(dyn, 80)
        return 80

    def _nearest_scale_index(self, pitch: int, sorted_scale: list[int]) -> int:
        """Find the index of the nearest scale pitch.

        Args:
            pitch: Target MIDI pitch.
            sorted_scale: Sorted scale pitches.

        Returns:
            Index into sorted_scale.
        """
        best_idx = 0
        best_dist = abs(sorted_scale[0] - pitch) if sorted_scale else 999
        for i, p in enumerate(sorted_scale):
            d = abs(p - pitch)
            if d < best_dist:
                best_dist = d
                best_idx = i
        return best_idx
