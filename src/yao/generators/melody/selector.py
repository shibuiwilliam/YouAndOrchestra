"""HarmonicMelodicSelector — pitch selection deeply coupled with harmony.

Provides a principled pitch-scoring algorithm that weights candidates by:
- Chord-tone affinity (stronger on metrically strong beats)
- Avoid-note penalty
- Tension-tone allowance (weaker beats, higher chromaticism)
- Voice-leading smoothness toward the next chord
- Interval distribution conformity to the genre profile

Used by SkeletonGenerator (M2) and OutlineGenerator for harmonically
grounded pitch decisions.

See IMPROVEMENT.md §4.4 and PROJECT.md §3.2 (Layer M2).
"""

from __future__ import annotations

import random

from yao.ir.harmonic_context import HarmonicContext
from yao.ir.notation import note_name_to_midi
from yao.schema.melodic_profile import MelodicProfile
from yao.types import MidiNote


class HarmonicMelodicSelector:
    """Selects pitches that respect both harmonic context and genre profile.

    The selector scores every candidate pitch on multiple axes and
    samples according to the combined weight. This replaces ad-hoc
    pitch selection in the skeleton generator with a principled,
    profile-parameterized algorithm.
    """

    def select_pitch(
        self,
        context: HarmonicContext,
        previous_pitch: MidiNote,
        scale_pitches: list[MidiNote],
        profile: MelodicProfile,
        rng: random.Random,
    ) -> MidiNote:
        """Select the best pitch given harmonic context and genre profile.

        Args:
            context: Harmonic state at this metric position.
            previous_pitch: The immediately preceding pitch.
            scale_pitches: Available pitches from the current scale.
            profile: MelodicProfile for genre parameterization.
            rng: Random number generator.

        Returns:
            Selected MIDI pitch.
        """
        metric_strength = self._metric_strength(context.beat)

        candidates: list[tuple[MidiNote, float]] = []
        for pitch in scale_pitches:
            score = self._score_pitch(
                pitch,
                context,
                previous_pitch,
                profile,
                metric_strength,
            )
            if score > 0:
                candidates.append((pitch, score))

        if not candidates:
            # Fallback: nearest scale pitch to previous
            nearest = min(scale_pitches, key=lambda p: abs(p - previous_pitch)) if scale_pitches else previous_pitch
            return nearest

        pitches, weights = zip(*candidates, strict=False)
        return int(rng.choices(pitches, weights=weights, k=1)[0])

    def score_pitch(
        self,
        pitch: MidiNote,
        context: HarmonicContext,
        previous_pitch: MidiNote,
        profile: MelodicProfile,
    ) -> float:
        """Score a single pitch (public API for testing/debugging).

        Args:
            pitch: Candidate MIDI pitch.
            context: Harmonic context.
            previous_pitch: Previous pitch.
            profile: MelodicProfile.

        Returns:
            Non-negative score (higher = better fit).
        """
        metric_strength = self._metric_strength(context.beat)
        return self._score_pitch(pitch, context, previous_pitch, profile, metric_strength)

    def _score_pitch(
        self,
        pitch: MidiNote,
        context: HarmonicContext,
        previous_pitch: MidiNote,
        profile: MelodicProfile,
        metric_strength: float,
    ) -> float:
        """Internal pitch scoring on multiple axes.

        Args:
            pitch: Candidate MIDI pitch.
            context: Harmonic context.
            previous_pitch: Previous pitch.
            profile: MelodicProfile.
            metric_strength: Beat strength (1.0 = downbeat, 0.0 = weakest).

        Returns:
            Combined score.
        """
        score = 0.1  # base score so all pitches have some chance

        # 1. Chord-tone affinity (stronger on strong beats)
        is_ct = context.is_chord_tone(pitch)
        if is_ct:
            score += profile.chord_tone_targeting * metric_strength * 3.0

        # 2. Avoid-note penalty
        root_midi = note_name_to_midi(f"{context.chord_root}4")
        pitch_class = (pitch - root_midi) % 12
        # Avoid notes are typically half-step above chord tones
        avoid_intervals = self._avoid_intervals(context.chord_quality)
        if pitch_class in avoid_intervals:
            score -= 3.0

        # 3. Tension allowance (weaker beats, higher chromaticism profile)
        if not is_ct and pitch_class not in avoid_intervals:
            score += (1.0 - metric_strength) * profile.chromaticism_level * 1.5

        # 4. Interval distribution conformity
        interval = abs(pitch - previous_pitch)
        dist = profile.interval_distribution.normalized()
        interval_weight = dist.get(interval, dist.get(interval % 12, 0.01))
        score += interval_weight * 2.0

        # 5. Voice-leading toward next chord
        if context.next_chord_root is not None:
            vl_targets = context.voice_leading_targets(octave=pitch // 12 - 1)
            min_dist = min((abs(pitch - t) for t in vl_targets), default=12)
            if min_dist <= 2:
                # Smooth voice leading bonus (half or whole step)
                score += (1.0 - metric_strength) * 1.0

        # 6. Range proximity bonus (prefer staying in typical range)
        if "melody" in profile.typical_ranges:
            low_name, high_name = profile.typical_ranges["melody"]
            low_midi = note_name_to_midi(low_name)
            high_midi = note_name_to_midi(high_name)
            if low_midi <= pitch <= high_midi:
                score += 0.5
            else:
                score -= 1.0

        return max(0.0, score)

    def _metric_strength(self, beat: float) -> float:
        """Compute metric strength for a beat position in 4/4 time.

        Args:
            beat: Beat position within the bar (0.0–3.99).

        Returns:
            Strength in [0.0, 1.0]. 1.0 = downbeat, 0.5 = beat 3,
            0.25 = beats 2/4, lower for off-beats.
        """
        beat_mod = beat % 4.0
        if abs(beat_mod) < 0.01:
            return 1.0
        if abs(beat_mod - 2.0) < 0.01:
            return 0.5
        if abs(beat_mod - 1.0) < 0.01 or abs(beat_mod - 3.0) < 0.01:
            return 0.25
        return 0.1

    def _avoid_intervals(self, chord_quality: str) -> set[int]:
        """Return pitch class intervals to avoid for a chord quality.

        Avoid notes are typically a half-step above a chord tone,
        creating a dissonant minor 9th.

        Args:
            chord_quality: Chord quality string.

        Returns:
            Set of pitch class intervals (semitones from root) to avoid.
        """
        # For major chords: avoid b2 (1) and #4 (6) on strong beats
        # For minor chords: avoid b2 (1) and natural 6 (9) in minor context
        if chord_quality in ("maj", "maj7"):
            return {1, 6}
        if chord_quality in ("min", "min7"):
            return {1}
        if chord_quality in ("dom7",):
            return {1}
        # For diminished/augmented, fewer avoid notes
        return {1}
