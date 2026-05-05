"""Symbolic Feature Extractors — 7 extractors operating on ScoreIR data.

These extractors analyze the symbolic (MIDI-level) representation of music,
producing fixed-size numpy vectors suitable for distance computation and
reference matching.

All extractors are copyright-safe: they produce statistical summaries
that cannot reconstruct copyrightable musical content.

Belongs to Layer 4 (Perception).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

import numpy as np

from yao.ir.score_ir import ScoreIR
from yao.perception.feature_extractors import register_extractor


@dataclass
class VoiceLeadingSmoothness:
    """Average semitone movement between consecutive voicings.

    Analyzes each beat window and computes the average voice movement
    between consecutive vertical sonorities. Lower values indicate
    smoother voice leading.

    Feature dimension: 1 (scalar).
    """

    name: str = "voice_leading_smoothness"
    feature_dim: int = 1

    def extract(self, score: ScoreIR) -> np.ndarray:
        """Extract voice leading smoothness as average semitone movement.

        Args:
            score: The ScoreIR to analyze.

        Returns:
            Array of shape (1,) with the average semitone movement.
        """
        notes = score.all_notes()
        if len(notes) < 2:
            return np.array([0.0], dtype=np.float64)

        # Group notes by beat position (quantize to quarter-note grid)
        beat_groups: dict[int, list[int]] = {}
        for note in notes:
            beat_key = int(note.start_beat)
            if beat_key not in beat_groups:
                beat_groups[beat_key] = []
            beat_groups[beat_key].append(note.pitch)

        # Sort beat groups and compute voice movement between consecutive chords
        sorted_beats = sorted(beat_groups.keys())
        if len(sorted_beats) < 2:
            return np.array([0.0], dtype=np.float64)

        total_movement = 0.0
        movement_count = 0

        for i in range(1, len(sorted_beats)):
            prev_pitches = sorted(beat_groups[sorted_beats[i - 1]])
            curr_pitches = sorted(beat_groups[sorted_beats[i]])

            # Match voices by proximity (greedy nearest-neighbor)
            min_len = min(len(prev_pitches), len(curr_pitches))
            for j in range(min_len):
                total_movement += abs(curr_pitches[j] - prev_pitches[j])
                movement_count += 1

        avg_movement = total_movement / max(movement_count, 1)
        return np.array([avg_movement], dtype=np.float64)


@dataclass
class MotivicDensity:
    """Count of short motif (pitch-interval trigram) recurrences.

    Identifies recurring 3-note pitch-interval patterns and reports
    the density of recurrences normalized by piece length.

    Feature dimension: 1 (scalar).
    """

    name: str = "motivic_density"
    feature_dim: int = 1

    def extract(self, score: ScoreIR) -> np.ndarray:
        """Extract motivic density as recurring trigram count per 8 bars.

        Args:
            score: The ScoreIR to analyze.

        Returns:
            Array of shape (1,) with motivic density value.
        """
        notes = score.all_notes()
        total_bars = max(score.total_bars(), 1)

        if len(notes) < 3:
            return np.array([0.0], dtype=np.float64)

        # Use interval trigrams (more transposition-invariant than pitch trigrams)
        intervals = [notes[i + 1].pitch - notes[i].pitch for i in range(len(notes) - 1)]

        trigrams: Counter[tuple[int, int, int]] = Counter()
        for i in range(len(intervals) - 2):
            tri = (intervals[i], intervals[i + 1], intervals[i + 2])
            trigrams[tri] += 1

        # Count trigrams that recur (appear more than once)
        recurring = sum(1 for count in trigrams.values() if count > 1)
        density = recurring / (total_bars / 8.0)

        return np.array([density], dtype=np.float64)


@dataclass
class SurpriseIndex:
    """Entropy of pitch intervals — measures predictability.

    Higher entropy means more surprising/unpredictable interval choices.
    Normalized to [0, 1] where 0 is perfectly predictable and 1 is
    maximally entropic.

    Feature dimension: 1 (scalar).
    """

    name: str = "surprise_index"
    feature_dim: int = 1

    def extract(self, score: ScoreIR) -> np.ndarray:
        """Extract surprise index as normalized interval entropy.

        Args:
            score: The ScoreIR to analyze.

        Returns:
            Array of shape (1,) with entropy value in [0, 1].
        """
        notes = score.all_notes()
        if len(notes) < 2:
            return np.array([0.0], dtype=np.float64)

        # Compute intervals (mod 12 for pitch class intervals)
        intervals: list[int] = []
        for i in range(1, len(notes)):
            interval = (notes[i].pitch - notes[i - 1].pitch) % 12
            intervals.append(interval)

        if not intervals:
            return np.array([0.0], dtype=np.float64)

        # Count interval class occurrences
        counts: Counter[int] = Counter(intervals)
        total = len(intervals)

        # Shannon entropy
        entropy = 0.0
        for count in counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        # Normalize by max possible entropy (uniform over 12 interval classes)
        max_entropy = math.log2(12)
        normalized = entropy / max_entropy if max_entropy > 0 else 0.0

        return np.array([normalized], dtype=np.float64)


@dataclass
class RegisterDistribution:
    """Histogram of MIDI notes per octave (12 bins, C0-B0 through C9-B9).

    Captures the vertical spread and center of mass of the piece.
    Normalized to sum to 1.0.

    Feature dimension: 12.
    """

    name: str = "register_distribution"
    feature_dim: int = 12

    def extract(self, score: ScoreIR) -> np.ndarray:
        """Extract register distribution as 12-bin octave histogram.

        Args:
            score: The ScoreIR to analyze.

        Returns:
            Array of shape (12,) with normalized octave counts.
        """
        notes = score.all_notes()
        bins = np.zeros(12, dtype=np.float64)

        if not notes:
            return bins

        for note in notes:
            octave = min(max(note.pitch // 12, 0), 11)
            bins[octave] += 1.0

        total = bins.sum()
        if total > 0:
            bins /= total

        return bins


@dataclass
class TemporalCentroid:
    """Bar position of the energy (velocity-weighted) centroid.

    Indicates where the "center of mass" of musical energy lies
    within the piece. Normalized to [0, 1] where 0 = beginning, 1 = end.

    Feature dimension: 1 (scalar).
    """

    name: str = "temporal_centroid"
    feature_dim: int = 1

    def extract(self, score: ScoreIR) -> np.ndarray:
        """Extract temporal centroid as normalized position.

        Args:
            score: The ScoreIR to analyze.

        Returns:
            Array of shape (1,) with centroid in [0, 1].
        """
        notes = score.all_notes()
        if not notes:
            return np.array([0.5], dtype=np.float64)

        total_beats = score.total_beats()
        if total_beats <= 0:
            return np.array([0.5], dtype=np.float64)

        # Velocity-weighted centroid
        weighted_sum = sum(note.start_beat * note.velocity for note in notes)
        total_weight = sum(note.velocity for note in notes)

        if total_weight <= 0:
            return np.array([0.5], dtype=np.float64)

        centroid_beat = weighted_sum / total_weight
        normalized = centroid_beat / total_beats

        return np.array([max(0.0, min(1.0, normalized))], dtype=np.float64)


@dataclass
class GroovePocket:
    """Timing offset distribution analysis.

    Analyzes the distribution of note onsets relative to the quantized
    grid to characterize the "groove feel". Reports statistics of the
    sub-beat onset positions: mean offset, std deviation, and skewness.

    Feature dimension: 3 (mean_offset, std_offset, skewness).
    """

    name: str = "groove_pocket"
    feature_dim: int = 3

    def extract(self, score: ScoreIR) -> np.ndarray:
        """Extract groove pocket features from timing offsets.

        Args:
            score: The ScoreIR to analyze.

        Returns:
            Array of shape (3,) with [mean_offset, std_offset, skewness].
        """
        notes = score.all_notes()
        if not notes:
            return np.zeros(3, dtype=np.float64)

        # Compute sub-beat fractional positions (offset from nearest 16th note)
        # A 16th note = 0.25 beats
        grid_size = 0.25
        offsets: list[float] = []

        for note in notes:
            # microtiming_offset_ms is the explicit groove offset
            if note.microtiming_offset_ms != 0.0:
                offsets.append(note.microtiming_offset_ms)
            else:
                # Compute implicit offset from quantized grid
                nearest_grid = round(note.start_beat / grid_size) * grid_size
                offset = note.start_beat - nearest_grid
                offsets.append(offset)

        if not offsets:
            return np.zeros(3, dtype=np.float64)

        arr = np.array(offsets, dtype=np.float64)
        mean_offset = float(np.mean(arr))
        std_offset = float(np.std(arr))

        # Skewness (Fisher's definition)
        skewness = float(np.mean(((arr - mean_offset) / std_offset) ** 3)) if std_offset > 1e-10 else 0.0

        return np.array([mean_offset, std_offset, skewness], dtype=np.float64)


@dataclass
class ChordComplexity:
    """Average unique pitch classes per beat window.

    Measures harmonic density by counting how many distinct pitch classes
    sound within each beat-aligned window. Higher values indicate richer
    harmonic content.

    Feature dimension: 1 (scalar).
    """

    name: str = "chord_complexity"
    feature_dim: int = 1

    def extract(self, score: ScoreIR) -> np.ndarray:
        """Extract chord complexity as average pitch classes per beat.

        Args:
            score: The ScoreIR to analyze.

        Returns:
            Array of shape (1,) with average pitch class count.
        """
        notes = score.all_notes()
        if not notes:
            return np.array([0.0], dtype=np.float64)

        total_beats = score.total_beats()
        if total_beats <= 0:
            return np.array([0.0], dtype=np.float64)

        # Group by beat window (1-beat windows)
        num_windows = max(1, int(math.ceil(total_beats)))
        window_pcs: list[set[int]] = [set() for _ in range(num_windows)]

        for note in notes:
            # Note sounds from start_beat to start_beat + duration_beats
            start_window = int(note.start_beat)
            end_window = int(note.start_beat + note.duration_beats)
            pc = note.pitch % 12

            for w in range(max(0, start_window), min(num_windows, end_window + 1)):
                window_pcs[w].add(pc)

        # Average number of unique pitch classes per window
        total_pcs = sum(len(pcs) for pcs in window_pcs)
        avg_complexity = total_pcs / num_windows

        return np.array([avg_complexity], dtype=np.float64)


# --- Register all extractors ---

register_extractor(VoiceLeadingSmoothness())
register_extractor(MotivicDensity())
register_extractor(SurpriseIndex())
register_extractor(RegisterDistribution())
register_extractor(TemporalCentroid())
register_extractor(GroovePocket())
register_extractor(ChordComplexity())
