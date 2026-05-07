"""OutlineGenerator — chord-progression-outlining skeleton strategy.

An alternative skeleton generation approach that creates the melodic
skeleton by directly outlining the chord progression: chord tones on
downbeats, smooth voice-leading at chord boundaries, and contour
shaped by the phrase plan.

Best suited for genres with strong harmonic outlining: bebop jazz,
classical, bossa nova. The genre's `chord_tone_targeting` determines
how strictly the outline follows chord tones.

See IMPROVEMENT.md §4.4 and PROJECT.md §3.2 (Layer M2).
"""

from __future__ import annotations

import random

from yao.constants.music import SCALE_INTERVALS
from yao.generators.melody.selector import HarmonicMelodicSelector
from yao.ir.harmonic_context import HarmonicContext
from yao.ir.notation import note_name_to_midi
from yao.ir.phrase import PhrasePlan
from yao.ir.skeleton import Skeleton, SkeletonNote
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.melodic_profile import MelodicProfile
from yao.types import MidiNote


class OutlineGenerator:
    """Generates a skeleton by outlining the chord progression.

    Each chord gets at least one skeleton note (its most prominent
    chord tone), and voice-leading connects successive chords smoothly.
    The HarmonicMelodicSelector scores candidates; this generator
    provides the structural framework.
    """

    def __init__(self) -> None:
        """Initialize with a HarmonicMelodicSelector."""
        self._selector = HarmonicMelodicSelector()

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
        """Generate a chord-outlining skeleton.

        Args:
            phrase_plan: The M1 output.
            spec: Composition specification.
            profile: MelodicProfile.
            provenance: Provenance log.
            harmonic_contexts: Per-bar harmonic contexts.
            rng: Random number generator.

        Returns:
            A Skeleton with strong chord-tone anchoring.
        """
        if rng is None:
            seed = spec.generation.seed if spec.generation.seed is not None else 42
            rng = random.Random(seed + 10)

        key_parts = spec.key.split()
        root_name = key_parts[0] if key_parts else "C"
        scale_type = key_parts[1] if len(key_parts) > 1 else "major"
        root_midi = note_name_to_midi(f"{root_name}4")
        scale_intervals = list(SCALE_INTERVALS.get(scale_type, SCALE_INTERVALS["major"]))

        # Build scale across octaves
        scale_pitches: list[MidiNote] = []
        for octave_offset in range(-12, 25, 12):
            for iv in scale_intervals:
                p = root_midi + octave_offset + iv
                if 0 <= p <= 127:
                    scale_pitches.append(p)
        scale_pitches.sort()

        total_bars = sum(s.bars for s in spec.sections)
        if harmonic_contexts is None:
            harmonic_contexts = [HarmonicContext(bar=b, beat=0.0, chord_root=root_name) for b in range(total_bars)]

        notes: list[SkeletonNote] = []
        target_pitches: dict[int, MidiNote] = {}
        prev_pitch = root_midi

        for phrase_idx, phrase in enumerate(phrase_plan.phrases):
            for bar in range(phrase.start_bar, phrase.end_bar):
                ctx = self._find_context(bar, harmonic_contexts)
                if ctx is None:
                    continue

                # Downbeat: select pitch via harmonic selector
                pitch = self._selector.select_pitch(
                    ctx,
                    prev_pitch,
                    scale_pitches,
                    profile,
                    rng,
                )

                # Determine structural role
                bar_in_phrase = bar - phrase.start_bar
                if bar_in_phrase == 0:
                    role = "phrase_start"
                elif bar == phrase.end_bar - 1:
                    role = "cadence_target"
                else:
                    role = "chord_outline"

                chord_relation = self._classify(pitch, ctx)
                notes.append(
                    SkeletonNote(
                        bar=bar,
                        beat=0.0,
                        midi_pitch=pitch,
                        chord_relation=chord_relation,
                        structural_role=role,
                        phrase_id=phrase_idx,
                    )
                )
                prev_pitch = pitch

                # Optional mid-bar note on beat 2 for longer phrases
                if phrase.length_bars >= 4 and rng.random() < profile.chord_tone_targeting:
                    ctx_mid = HarmonicContext(
                        bar=bar,
                        beat=2.0,
                        chord_root=ctx.chord_root,
                        chord_quality=ctx.chord_quality,
                        next_chord_root=ctx.next_chord_root,
                        next_chord_quality=ctx.next_chord_quality,
                    )
                    mid_pitch = self._selector.select_pitch(
                        ctx_mid,
                        pitch,
                        scale_pitches,
                        profile,
                        rng,
                    )
                    notes.append(
                        SkeletonNote(
                            bar=bar,
                            beat=2.0,
                            midi_pitch=mid_pitch,
                            chord_relation=self._classify(mid_pitch, ctx),
                            structural_role="passing",
                            phrase_id=phrase_idx,
                        )
                    )
                    prev_pitch = mid_pitch

            # Record phrase target
            if notes:
                target_pitches[phrase.end_bar - 1] = notes[-1].midi_pitch

        skeleton = Skeleton(notes=tuple(notes), target_pitches=target_pitches)

        # Compute chord-tone ratio
        ct_count = sum(1 for n in notes if n.chord_relation in ("root", "3rd", "5th", "7th"))
        total = len(notes)
        ct_ratio = ct_count / total if total > 0 else 0.0

        provenance.record(
            layer="M2_skeleton",
            operation="outline_chord_progression",
            parameters={
                "total_notes": total,
                "chord_tone_ratio": round(ct_ratio, 3),
                "target_ratio": profile.chord_tone_targeting,
                "phrases": len(phrase_plan.phrases),
            },
            source="OutlineGenerator",
            rationale=(
                f"Outlined chord progression with {total} skeleton notes. "
                f"Chord-tone ratio: {ct_ratio:.1%} "
                f"(target: {profile.chord_tone_targeting:.1%})."
            ),
            agent="composer-subagent",
        )

        return skeleton

    def _find_context(
        self,
        bar: int,
        contexts: list[HarmonicContext],
    ) -> HarmonicContext | None:
        """Find harmonic context for a bar."""
        for ctx in contexts:
            if ctx.bar == bar:
                return ctx
        return contexts[0] if contexts else None

    def _classify(self, pitch: MidiNote, ctx: HarmonicContext) -> str:
        """Classify pitch's chord relation."""
        root_midi = note_name_to_midi(f"{ctx.chord_root}4")
        offset = (pitch - root_midi) % 12
        tones = ctx.chord_tones
        if offset == 0:
            return "root"
        if len(tones) > 1 and offset == tones[1]:
            return "3rd"
        if len(tones) > 2 and offset == tones[2]:  # noqa: PLR2004
            return "5th"
        if len(tones) > 3 and offset == tones[3]:  # noqa: PLR2004
            return "7th"
        return "tension"
