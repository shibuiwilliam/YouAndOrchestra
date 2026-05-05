"""StyleVector — abstract feature representation for style comparison.

Captures only non-copyrightable, abstract musical features.
**NEVER** includes melody contour, chord progression, or other
copyrightable elements. This is enforced at the type level.

Belongs to Layer 4 (Perception Substitute).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yao.ir.plan.musical_plan import MusicalPlan
    from yao.ir.score_ir import ScoreIR


@dataclass(frozen=True)
class StyleVector:
    """Abstract style features for reference matching.

    All fields represent statistical/structural properties, not
    copyrightable musical content. This dataclass must NEVER contain
    fields like ``melody``, ``chord_progression``, ``chord_sequence``,
    ``melody_contour``, or ``lyrics``.

    Attributes:
        harmonic_rhythm: Average chord changes per bar.
        voice_leading_smoothness: Average semitone distance between
            consecutive chord voicings (lower = smoother).
        rhythmic_density_per_bar: Onsets per bar for each bar.
        register_distribution: MIDI pitch histogram (12 octave bins,
            C1 through C8, normalized to sum to 1.0).
        timbre_centroid_curve: Spectral centroid per section (Hz).
        motif_density: Average motif recurrences per 8 bars.
        interval_class_histogram: Distribution of interval classes 0-11
            (how often each interval size appears, normalized). 12 dims.
            Copyright-safe: represents statistical tendency, not sequence.
        chord_quality_histogram: Distribution of chord qualities
            (maj, min, dim, aug, dom7, min7, maj7, sus). 8 dims.
            Copyright-safe: aggregate quality counts, not progression.
        cadence_type_distribution: Proportion of cadence types
            (authentic, half, plagal, deceptive). 4 dims.
            Copyright-safe: cadence preference, not position.
        rhythm_complexity: Normalized entropy of onset pattern (0=uniform, 1=complex).
            Copyright-safe: single statistical value.
    """

    harmonic_rhythm: float
    voice_leading_smoothness: float
    rhythmic_density_per_bar: tuple[float, ...]
    register_distribution: tuple[float, ...]
    timbre_centroid_curve: tuple[float, ...]
    motif_density: float
    # Wave 3.4: melody/harmony abstract features (copyright-safe histograms)
    interval_class_histogram: tuple[float, ...] = (0.0,) * 12
    chord_quality_histogram: tuple[float, ...] = (0.0,) * 8
    cadence_type_distribution: tuple[float, ...] = (0.0,) * 4
    rhythm_complexity: float = 0.0

    def _to_flat(self) -> list[float]:
        """Flatten all features into a single vector for arithmetic.

        Returns:
            List of all scalar and tuple element values in a fixed order.
        """
        parts: list[float] = [
            self.harmonic_rhythm,
            self.voice_leading_smoothness,
            self.motif_density,
            self.rhythm_complexity,
        ]
        parts.extend(self.rhythmic_density_per_bar)
        parts.extend(self.register_distribution)
        parts.extend(self.timbre_centroid_curve)
        parts.extend(self.interval_class_histogram)
        parts.extend(self.chord_quality_histogram)
        parts.extend(self.cadence_type_distribution)
        return parts

    def _tuple_lengths(self) -> tuple[int, int, int, int, int, int]:
        """Return lengths of the six variable-length tuple fields."""
        return (
            len(self.rhythmic_density_per_bar),
            len(self.register_distribution),
            len(self.timbre_centroid_curve),
            len(self.interval_class_histogram),
            len(self.chord_quality_histogram),
            len(self.cadence_type_distribution),
        )

    @staticmethod
    def _from_flat(
        values: list[float],
        lengths: tuple[int, int, int, int, int, int],
    ) -> StyleVector:
        """Reconstruct a StyleVector from a flat value list and tuple lengths.

        Args:
            values: Flat list of all feature values.
            lengths: Lengths of the six tuple fields.

        Returns:
            Reconstructed StyleVector.
        """
        idx = 0
        harmonic_rhythm = values[idx]
        idx += 1
        voice_leading_smoothness = values[idx]
        idx += 1
        motif_density = values[idx]
        idx += 1
        rhythm_complexity = values[idx]
        idx += 1

        rhythmic_density = tuple(values[idx : idx + lengths[0]])
        idx += lengths[0]
        register_dist = tuple(values[idx : idx + lengths[1]])
        idx += lengths[1]
        timbre_curve = tuple(values[idx : idx + lengths[2]])
        idx += lengths[2]
        interval_hist = tuple(values[idx : idx + lengths[3]])
        idx += lengths[3]
        chord_hist = tuple(values[idx : idx + lengths[4]])
        idx += lengths[4]
        cadence_dist = tuple(values[idx : idx + lengths[5]])
        idx += lengths[5]

        return StyleVector(
            harmonic_rhythm=harmonic_rhythm,
            voice_leading_smoothness=voice_leading_smoothness,
            rhythmic_density_per_bar=rhythmic_density,
            register_distribution=register_dist,
            timbre_centroid_curve=timbre_curve,
            motif_density=motif_density,
            interval_class_histogram=interval_hist,
            chord_quality_histogram=chord_hist,
            cadence_type_distribution=cadence_dist,
            rhythm_complexity=rhythm_complexity,
        )

    @staticmethod
    def _align_lengths(
        a: StyleVector,
        b: StyleVector,
    ) -> tuple[list[float], list[float], tuple[int, int, int, int, int, int]]:
        """Align two StyleVectors to the same tuple lengths by zero-padding shorter tuples.

        Args:
            a: First StyleVector.
            b: Second StyleVector.

        Returns:
            Tuple of (flat_a, flat_b, max_lengths).
        """
        a_lens = a._tuple_lengths()
        b_lens = b._tuple_lengths()
        max_lens = tuple(max(al, bl) for al, bl in zip(a_lens, b_lens, strict=True))

        def _pad_and_flatten(sv: StyleVector, target_lens: tuple[int, ...]) -> list[float]:
            parts: list[float] = [
                sv.harmonic_rhythm,
                sv.voice_leading_smoothness,
                sv.motif_density,
                sv.rhythm_complexity,
            ]
            tuples = [
                sv.rhythmic_density_per_bar,
                sv.register_distribution,
                sv.timbre_centroid_curve,
                sv.interval_class_histogram,
                sv.chord_quality_histogram,
                sv.cadence_type_distribution,
            ]
            for t, tl in zip(tuples, target_lens, strict=True):
                parts.extend(t)
                parts.extend([0.0] * (tl - len(t)))
            return parts

        return (
            _pad_and_flatten(a, max_lens),
            _pad_and_flatten(b, max_lens),
            max_lens,  # type: ignore[return-value]
        )

    def __add__(self, other: StyleVector) -> StyleVector:
        """Element-wise addition of two StyleVectors.

        Args:
            other: StyleVector to add.

        Returns:
            New StyleVector with summed values.
        """
        flat_a, flat_b, lengths = StyleVector._align_lengths(self, other)
        result = [a + b for a, b in zip(flat_a, flat_b, strict=True)]
        return StyleVector._from_flat(result, lengths)

    def __sub__(self, other: StyleVector) -> StyleVector:
        """Element-wise subtraction of two StyleVectors.

        Args:
            other: StyleVector to subtract.

        Returns:
            New StyleVector with differenced values.
        """
        flat_a, flat_b, lengths = StyleVector._align_lengths(self, other)
        result = [a - b for a, b in zip(flat_a, flat_b, strict=True)]
        return StyleVector._from_flat(result, lengths)

    def __mul__(self, scalar: float) -> StyleVector:
        """Scalar multiplication of a StyleVector.

        Args:
            scalar: The scalar to multiply by.

        Returns:
            New StyleVector with scaled values.
        """
        flat = self._to_flat()
        result = [v * scalar for v in flat]
        return StyleVector._from_flat(result, self._tuple_lengths())

    def __rmul__(self, scalar: float) -> StyleVector:
        """Right-hand scalar multiplication.

        Args:
            scalar: The scalar to multiply by.

        Returns:
            New StyleVector with scaled values.
        """
        return self.__mul__(scalar)

    def cosine_similarity(self, other: StyleVector) -> float:
        """Compute cosine similarity to another StyleVector.

        Cosine similarity measures the angle between two vectors,
        independent of magnitude. Returns 1.0 for identical direction,
        0.0 for orthogonal, -1.0 for opposite.

        Goodhart defense: cosine similarity alone can be gamed by matching
        feature ratios without matching absolute values. Always pair with
        Euclidean distance_to() to catch magnitude divergence.

        Args:
            other: The other StyleVector.

        Returns:
            Cosine similarity in [-1.0, 1.0].
        """
        flat_a, flat_b, _ = StyleVector._align_lengths(self, other)
        dot = sum(a * b for a, b in zip(flat_a, flat_b, strict=True))
        mag_a = math.sqrt(sum(a * a for a in flat_a))
        mag_b = math.sqrt(sum(b * b for b in flat_b))
        if mag_a < 1e-12 or mag_b < 1e-12:
            return 0.0
        return dot / (mag_a * mag_b)

    def distance_to(self, other: StyleVector) -> float:
        """Compute Euclidean distance to another StyleVector.

        All dimensions are normalized to [0, 1] before distance
        calculation to prevent any single feature from dominating.

        Args:
            other: The other StyleVector.

        Returns:
            Euclidean distance (>= 0).
        """
        diffs: list[float] = []

        # Scalar features: normalize by reasonable max values
        diffs.append(_norm_diff(self.harmonic_rhythm, other.harmonic_rhythm, max_val=8.0))
        diffs.append(_norm_diff(self.voice_leading_smoothness, other.voice_leading_smoothness, max_val=12.0))
        diffs.append(_norm_diff(self.motif_density, other.motif_density, max_val=10.0))
        diffs.append(_norm_diff(self.rhythm_complexity, other.rhythm_complexity, max_val=1.0))

        # Tuple features: average element-wise differences
        diffs.append(_tuple_distance(self.rhythmic_density_per_bar, other.rhythmic_density_per_bar, max_val=16.0))
        diffs.append(_tuple_distance(self.register_distribution, other.register_distribution, max_val=1.0))
        diffs.append(_tuple_distance(self.timbre_centroid_curve, other.timbre_centroid_curve, max_val=10000.0))
        diffs.append(_tuple_distance(self.interval_class_histogram, other.interval_class_histogram, max_val=1.0))
        diffs.append(_tuple_distance(self.chord_quality_histogram, other.chord_quality_histogram, max_val=1.0))
        diffs.append(_tuple_distance(self.cadence_type_distribution, other.cadence_type_distribution, max_val=1.0))

        return math.sqrt(sum(d * d for d in diffs))


def extract_style_vector_from_score(score: ScoreIR, plan: MusicalPlan | None = None) -> StyleVector:
    """Extract a StyleVector from a ScoreIR (and optional MusicalPlan).

    All extracted features are copyright-safe: histograms and statistics
    that cannot reconstruct the original melody or chord sequence.

    Args:
        score: The score to analyze.
        plan: Optional MusicalPlan for harmony/cadence info.

    Returns:
        StyleVector with all fields populated.
    """

    notes = score.all_notes()
    if not notes:
        return StyleVector(
            harmonic_rhythm=0.0,
            voice_leading_smoothness=0.0,
            rhythmic_density_per_bar=(),
            register_distribution=(0.0,) * 12,
            timbre_centroid_curve=(),
            motif_density=0.0,
        )

    # --- Interval class histogram (12 dimensions) ---
    interval_counts = [0] * 12
    sorted_notes = sorted(notes, key=lambda n: n.start_beat)
    for i in range(1, len(sorted_notes)):
        interval = abs(sorted_notes[i].pitch - sorted_notes[i - 1].pitch) % 12
        interval_counts[interval] += 1
    total_intervals = sum(interval_counts) or 1
    interval_hist = tuple(c / total_intervals for c in interval_counts)

    # --- Register distribution (12 octave bins) ---
    octave_counts = [0] * 12
    for n in notes:
        octave = min(max(n.pitch // 12, 0), 11)
        octave_counts[octave] += 1
    total_notes = len(notes)
    register_dist = tuple(c / total_notes for c in octave_counts)

    # --- Rhythmic density per bar ---
    from collections import Counter

    bar_counts: Counter[int] = Counter()
    beats_per_bar = 4.0  # assume 4/4
    for n in notes:
        bar = int(n.start_beat / beats_per_bar)
        bar_counts[bar] += 1
    max_bar = max(bar_counts.keys()) if bar_counts else 0
    density_per_bar = tuple(float(bar_counts.get(b, 0)) for b in range(max_bar + 1))

    # --- Rhythm complexity (onset pattern entropy) ---
    beat_positions = [n.start_beat % beats_per_bar for n in notes]
    # Quantize to 16th note grid
    grid_counts = [0] * 16
    for bp in beat_positions:
        slot = int(bp * 4) % 16
        grid_counts[slot] += 1
    total_onsets = sum(grid_counts) or 1
    entropy = 0.0
    for c in grid_counts:
        if c > 0:
            p = c / total_onsets
            entropy -= p * math.log2(p)
    max_entropy = math.log2(16)  # uniform distribution
    rhythm_complexity = entropy / max_entropy if max_entropy > 0 else 0.0

    # --- Chord quality histogram (8 dims) ---
    chord_quality_hist = [0.0] * 8
    cadence_dist = [0.0] * 4
    harmonic_rhythm_val = 0.0

    if plan and plan.harmony:
        quality_map = {"maj": 0, "min": 1, "dim": 2, "aug": 3, "dom7": 4, "min7": 5, "maj7": 6, "sus": 7}
        total_chords = len(plan.harmony.chord_events) or 1
        for ce in plan.harmony.chord_events:
            # Infer quality from roman numeral case
            roman = ce.roman.strip()
            quality_map_key = "maj" if roman[0].isupper() else "min"
            if "7" in roman:
                quality_map_key = "dom7" if roman[0].isupper() else "min7"
            idx = quality_map.get(quality_map_key, 0)
            chord_quality_hist[idx] += 1
        chord_quality_hist = [c / total_chords for c in chord_quality_hist]

        # Harmonic rhythm
        total_bars = max(1, sum(s.bars for s in plan.form.sections))
        harmonic_rhythm_val = total_chords / total_bars

        # Cadence distribution
        cadence_map = {"authentic": 0, "half": 1, "plagal": 2, "deceptive": 3}
        cadence_count = 0
        for ce in plan.harmony.chord_events:
            if ce.cadence_role:
                idx = cadence_map.get(ce.cadence_role.value, 0)
                cadence_dist[idx] += 1
                cadence_count += 1
        if cadence_count > 0:
            cadence_dist = [c / cadence_count for c in cadence_dist]

    # --- Motif density ---
    motif_density_val = 0.0
    if plan and plan.motif and plan.motif.placements:
        total_bars_p = max(1, sum(s.bars for s in plan.form.sections))
        motif_density_val = len(plan.motif.placements) / (total_bars_p / 8.0)

    return StyleVector(
        harmonic_rhythm=harmonic_rhythm_val,
        voice_leading_smoothness=0.0,  # requires chord voicing analysis
        rhythmic_density_per_bar=density_per_bar,
        register_distribution=register_dist,
        timbre_centroid_curve=(),  # requires audio
        motif_density=motif_density_val,
        interval_class_histogram=tuple(interval_hist),
        chord_quality_histogram=tuple(chord_quality_hist),
        cadence_type_distribution=tuple(cadence_dist),
        rhythm_complexity=rhythm_complexity,
    )


def _norm_diff(a: float, b: float, max_val: float) -> float:
    """Normalized absolute difference in [0, 1]."""
    if max_val <= 0:
        return 0.0
    return min(abs(a - b) / max_val, 1.0)


def _tuple_distance(
    a: tuple[float, ...],
    b: tuple[float, ...],
    max_val: float,
) -> float:
    """Average normalized element-wise difference between two tuples."""
    if not a and not b:
        return 0.0
    # Pad shorter to match longer
    max_len = max(len(a), len(b))
    a_padded = a + (0.0,) * (max_len - len(a))
    b_padded = b + (0.0,) * (max_len - len(b))
    total = sum(_norm_diff(ai, bi, max_val) for ai, bi in zip(a_padded, b_padded, strict=True))
    return total / max_len
