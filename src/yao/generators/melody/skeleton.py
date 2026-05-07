"""Layer M2: Skeleton Generation.

Generates structural pitches that anchor the melody to the harmony.
Each skeleton note is a chord tone or voice-leading target placed at
a metrically important position. The skeleton is the bridge between
phrase structure (M1) and surface realization (M3).

See PROJECT.md §3.2 (Layer M2) and IMPROVEMENT.md §4.1.
"""

from __future__ import annotations

import random

from yao.constants.music import SCALE_INTERVALS
from yao.ir.harmonic_context import HarmonicContext
from yao.ir.notation import note_name_to_midi
from yao.ir.phrase import PhrasePlan
from yao.ir.skeleton import Skeleton, SkeletonNote
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.melodic_profile import MelodicProfile


class SkeletonGenerator:
    """Generates a melody skeleton from a phrase plan and harmonic context.

    The skeleton places chord-tone targets at metrically strong positions,
    respecting the genre's chord_tone_targeting parameter and the phrase
    contour archetypes planned in M1.
    """

    def generate(
        self,
        phrase_plan: PhrasePlan,
        spec: CompositionSpec,
        profile: MelodicProfile,
        provenance: ProvenanceLog,
        *,
        harmonic_contexts: list[HarmonicContext] | None = None,
        rng: random.Random | None = None,
    ) -> Skeleton:
        """Generate a skeleton from a phrase plan.

        Args:
            phrase_plan: The M1 output (phrase boundaries, functions, motifs).
            spec: Composition specification.
            profile: MelodicProfile for chord-tone targeting.
            provenance: Provenance log.
            harmonic_contexts: Per-beat harmonic contexts. If None,
                generates default contexts from the spec's key.
            rng: Random number generator.

        Returns:
            A Skeleton anchoring the melody to the harmony.
        """
        if rng is None:
            seed = spec.generation.seed if spec.generation.seed is not None else 42
            rng = random.Random(seed + 1)  # Different seed offset from M1

        key_parts = spec.key.split()
        root_name = key_parts[0] if key_parts else "C"
        scale_type = key_parts[1] if len(key_parts) > 1 else "major"
        root_midi = note_name_to_midi(f"{root_name}4")
        scale_intervals = list(SCALE_INTERVALS.get(scale_type, SCALE_INTERVALS["major"]))

        if harmonic_contexts is None:
            harmonic_contexts = self._default_contexts(spec, root_name)

        notes: list[SkeletonNote] = []
        target_pitches: dict[int, int] = {}

        for phrase_idx, phrase in enumerate(phrase_plan.phrases):
            phrase_notes = self._generate_phrase_skeleton(
                phrase_idx=phrase_idx,
                start_bar=phrase.start_bar,
                end_bar=phrase.end_bar,
                contour=phrase.contour_archetype,
                profile=profile,
                root_midi=root_midi,
                scale_intervals=scale_intervals,
                harmonic_contexts=harmonic_contexts,
                rng=rng,
            )
            notes.extend(phrase_notes)

            # Record phrase target pitch
            if phrase_notes:
                target_pitches[phrase.end_bar - 1] = phrase_notes[-1].midi_pitch

        skeleton = Skeleton(notes=tuple(notes), target_pitches=target_pitches)

        # Record provenance
        chord_tone_count = sum(1 for n in notes if n.chord_relation in ("root", "3rd", "5th", "7th"))
        total_notes = len(notes)
        actual_targeting = chord_tone_count / total_notes if total_notes > 0 else 0.0

        provenance.record(
            layer="M2_skeleton",
            operation="generate_skeleton",
            parameters={
                "phrase_count": len(phrase_plan.phrases),
                "skeleton_notes": total_notes,
                "chord_tone_targeting_target": profile.chord_tone_targeting,
                "chord_tone_targeting_actual": round(actual_targeting, 3),
            },
            source="SkeletonGenerator",
            rationale=(
                f"Generated {total_notes} skeleton notes across {len(phrase_plan.phrases)} "
                f"phrases. Chord-tone targeting: {actual_targeting:.1%} "
                f"(target: {profile.chord_tone_targeting:.1%})."
            ),
            agent="composer-subagent",
        )

        return skeleton

    def _generate_phrase_skeleton(
        self,
        *,
        phrase_idx: int,
        start_bar: int,
        end_bar: int,
        contour: str,
        profile: MelodicProfile,
        root_midi: int,
        scale_intervals: list[int],
        harmonic_contexts: list[HarmonicContext],
        rng: random.Random,
    ) -> list[SkeletonNote]:
        """Generate skeleton notes for a single phrase.

        Args:
            phrase_idx: Index of this phrase.
            start_bar: First bar.
            end_bar: Bar after last (exclusive).
            contour: Contour archetype.
            profile: MelodicProfile.
            root_midi: Root MIDI pitch.
            scale_intervals: Scale intervals in semitones.
            harmonic_contexts: All harmonic contexts.
            rng: Random number generator.

        Returns:
            List of SkeletonNote for this phrase.
        """
        length = end_bar - start_bar
        if length <= 0:
            return []

        # Build scale pitches across two octaves
        scale_pitches = [root_midi + iv for iv in scale_intervals]
        scale_pitches.extend(root_midi + 12 + iv for iv in scale_intervals)
        scale_pitches.extend(root_midi - 12 + iv for iv in scale_intervals)
        scale_pitches.sort()

        # Determine contour target sequence
        contour_offsets = self._contour_offsets(length, contour)

        notes: list[SkeletonNote] = []
        # Place one skeleton note per bar on the downbeat,
        # plus potentially a note on beat 3 for longer phrases
        for bar_offset in range(length):
            bar = start_bar + bar_offset
            beats_to_place = [0.0]
            if length >= 4 and rng.random() < 0.4:
                beats_to_place.append(2.0)

            for beat in beats_to_place:
                ctx = self._find_context(bar, beat, harmonic_contexts)
                pitch = self._select_skeleton_pitch(
                    bar=bar,
                    beat=beat,
                    contour_offset=contour_offsets[bar_offset],
                    root_midi=root_midi,
                    scale_pitches=scale_pitches,
                    ctx=ctx,
                    profile=profile,
                    rng=rng,
                )
                chord_relation = self._classify_chord_relation(pitch, ctx)

                # Determine structural role
                if bar_offset == 0 and beat == 0.0:
                    role = "phrase_start"
                elif bar_offset == length - 1 and beat == 0.0:
                    role = "cadence_target"
                elif contour_offsets[bar_offset] == max(contour_offsets):
                    role = "climax"
                else:
                    role = "passing"

                notes.append(
                    SkeletonNote(
                        bar=bar,
                        beat=beat,
                        midi_pitch=pitch,
                        chord_relation=chord_relation,
                        structural_role=role,
                        phrase_id=phrase_idx,
                    )
                )

        return notes

    def _select_skeleton_pitch(
        self,
        *,
        bar: int,
        beat: float,
        contour_offset: float,
        root_midi: int,
        scale_pitches: list[int],
        ctx: HarmonicContext | None,
        profile: MelodicProfile,
        rng: random.Random,
    ) -> int:
        """Select a pitch for a skeleton note considering harmony and contour.

        Args:
            bar: Bar number.
            beat: Beat position.
            contour_offset: Contour-derived pitch offset (in scale degree units).
            root_midi: Root MIDI pitch.
            scale_pitches: Available scale pitches.
            ctx: Harmonic context at this position.
            profile: MelodicProfile.
            rng: Random number generator.

        Returns:
            MIDI pitch for this skeleton note.
        """
        # Base pitch from contour
        target_midi = root_midi + int(contour_offset * 2)  # 2 semitones per contour unit

        # Find candidates near the target
        candidates: list[tuple[int, float]] = []
        for pitch in scale_pitches:
            distance = abs(pitch - target_midi)
            if distance > 12:
                continue

            # Proximity weight
            weight = max(0.01, 1.0 - distance / 12.0)

            # Chord tone bonus
            if ctx and ctx.is_chord_tone(pitch):
                weight *= 1.0 + profile.chord_tone_targeting * 3.0

            # Metric strength bonus for chord tones on downbeats
            if beat == 0.0 and ctx and ctx.is_chord_tone(pitch):
                weight *= 1.5

            candidates.append((pitch, weight))

        if not candidates:
            return self._nearest_scale_pitch(target_midi, scale_pitches)

        pitches, weights = zip(*candidates, strict=False)
        return int(rng.choices(pitches, weights=weights, k=1)[0])

    def _classify_chord_relation(self, pitch: int, ctx: HarmonicContext | None) -> str:
        """Classify a pitch's relationship to the current chord.

        Args:
            pitch: MIDI pitch.
            ctx: Harmonic context.

        Returns:
            Chord relation string.
        """
        if ctx is None:
            return "root"

        root_midi = note_name_to_midi(f"{ctx.chord_root}4")
        offset = (pitch - root_midi) % 12
        tones = ctx.chord_tones

        if offset == 0:
            return "root"
        if len(tones) > 1 and offset == tones[1]:
            return "3rd"
        if len(tones) > 2 and offset == tones[2]:
            return "5th"
        if len(tones) > 3 and offset == tones[3]:
            return "7th"
        return "tension"

    def _contour_offsets(self, length: int, contour: str) -> list[float]:
        """Generate contour offsets for each bar.

        Args:
            length: Number of bars.
            contour: Contour archetype name.

        Returns:
            List of float offsets (higher = higher pitch target).
        """
        if length <= 0:
            return []

        if contour == "arch":
            # Rise to peak at ~60%, then descend
            peak = int(length * 0.6)
            return [
                3.0 * i / max(peak, 1) if i <= peak else 3.0 * (length - 1 - i) / max(length - 1 - peak, 1)
                for i in range(length)
            ]
        elif contour == "ascending":
            return [3.0 * i / max(length - 1, 1) for i in range(length)]
        elif contour == "descending":
            return [3.0 * (length - 1 - i) / max(length - 1, 1) for i in range(length)]
        elif contour == "wave":
            import math

            return [1.5 * math.sin(2 * math.pi * i / max(length - 1, 1)) + 1.5 for i in range(length)]
        else:
            return [0.0] * length

    def _find_context(
        self,
        bar: int,
        beat: float,
        contexts: list[HarmonicContext],
    ) -> HarmonicContext | None:
        """Find the harmonic context for a given bar and beat.

        Args:
            bar: Bar number.
            beat: Beat within bar.
            contexts: Available contexts.

        Returns:
            Matching context, or None.
        """
        for ctx in contexts:
            if ctx.bar == bar and abs(ctx.beat - beat) < 0.5:
                return ctx
        # Fallback: find any context for this bar
        for ctx in contexts:
            if ctx.bar == bar:
                return ctx
        return contexts[0] if contexts else None

    def _default_contexts(
        self,
        spec: CompositionSpec,
        root_name: str,
    ) -> list[HarmonicContext]:
        """Generate default harmonic contexts when none provided.

        Creates a simple I chord context for each bar.

        Args:
            spec: Composition spec.
            root_name: Root note name.

        Returns:
            List of HarmonicContext, one per bar.
        """
        total_bars = sum(s.bars for s in spec.sections)
        return [
            HarmonicContext(
                bar=bar,
                beat=0.0,
                chord_root=root_name,
                chord_quality="maj",
            )
            for bar in range(total_bars)
        ]

    def _nearest_scale_pitch(self, target: int, scale_pitches: list[int]) -> int:
        """Find the nearest pitch in the scale to a target.

        Args:
            target: Target MIDI pitch.
            scale_pitches: Available scale pitches.

        Returns:
            Nearest scale pitch.
        """
        if not scale_pitches:
            return target
        return min(scale_pitches, key=lambda p: abs(p - target))
