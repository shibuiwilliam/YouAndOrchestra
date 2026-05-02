"""StyleVector — abstract feature representation for style comparison.

Captures only non-copyrightable, abstract musical features.
**NEVER** includes melody contour, chord progression, or other
copyrightable elements. This is enforced at the type level.

Belongs to Layer 4 (Perception Substitute).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


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
    """

    harmonic_rhythm: float
    voice_leading_smoothness: float
    rhythmic_density_per_bar: tuple[float, ...]
    register_distribution: tuple[float, ...]
    timbre_centroid_curve: tuple[float, ...]
    motif_density: float

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

        # Tuple features: average element-wise differences
        diffs.append(_tuple_distance(self.rhythmic_density_per_bar, other.rhythmic_density_per_bar, max_val=16.0))
        diffs.append(_tuple_distance(self.register_distribution, other.register_distribution, max_val=1.0))
        diffs.append(_tuple_distance(self.timbre_centroid_curve, other.timbre_centroid_curve, max_val=10000.0))

        return math.sqrt(sum(d * d for d in diffs))


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
