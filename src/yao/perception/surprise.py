"""Surprise Score — per-note prediction-vs-actual divergence.

Computes surprise using an n-gram predictor combined with the
Krumhansl tonal hierarchy. No ML dependencies — purely statistical.

Surprise Score addresses the Prosaic Output Problem (PROJECT.md §11.1):
spec-correct but boring music. A healthy piece has moderate overall
surprise with strategic peaks at tension points and hooks.

Belongs to Layer 4 (Perception).
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from yao.ir.score_ir import ScoreIR

# ---------------------------------------------------------------------------
# Krumhansl tonal hierarchy profiles (rights-clear: from published
# empirical research by Carol Krumhansl, 1990).
# Values represent stability ratings for each pitch class in context.
# Index 0 = tonic, 1 = minor 2nd, ..., 11 = major 7th.
# ---------------------------------------------------------------------------

KRUMHANSL_MAJOR: tuple[float, ...] = (
    6.35,
    2.23,
    3.48,
    2.33,
    4.38,
    4.09,
    2.52,
    5.19,
    2.39,
    3.66,
    2.29,
    2.88,
)

KRUMHANSL_MINOR: tuple[float, ...] = (
    6.33,
    2.68,
    3.52,
    5.38,
    2.60,
    3.53,
    2.54,
    4.75,
    3.98,
    2.69,
    3.34,
    3.17,
)


def _normalize_profile(profile: tuple[float, ...]) -> tuple[float, ...]:
    """Normalize a profile to sum to 1.0."""
    total = sum(profile)
    return tuple(v / total for v in profile)


MAJOR_PROFILE = _normalize_profile(KRUMHANSL_MAJOR)
MINOR_PROFILE = _normalize_profile(KRUMHANSL_MINOR)


def _parse_key(key: str) -> tuple[int, tuple[float, ...]]:
    """Parse a key string like 'C major' to (root_pc, profile).

    Args:
        key: Key string (e.g., "C major", "D minor", "F# major").

    Returns:
        Tuple of (root pitch class 0-11, normalized Krumhansl profile
        rotated to the key's root).
    """
    note_map = {
        "C": 0,
        "C#": 1,
        "Db": 1,
        "D": 2,
        "D#": 3,
        "Eb": 3,
        "E": 4,
        "Fb": 4,
        "E#": 5,
        "F": 5,
        "F#": 6,
        "Gb": 6,
        "G": 7,
        "G#": 8,
        "Ab": 8,
        "A": 9,
        "A#": 10,
        "Bb": 10,
        "B": 11,
        "Cb": 11,
    }
    parts = key.strip().split()
    root_name = parts[0] if parts else "C"
    mode = parts[1].lower() if len(parts) > 1 else "major"

    root_pc = note_map.get(root_name, 0)
    base_profile = MINOR_PROFILE if "min" in mode else MAJOR_PROFILE

    # Rotate profile so index 0 aligns with the key's root
    rotated = base_profile[-root_pc:] + base_profile[:-root_pc] if root_pc > 0 else base_profile
    return root_pc, rotated


@dataclass(frozen=True)
class NoteSurprise:
    """Surprise annotation for a single note.

    Attributes:
        pitch: MIDI pitch of the note.
        start_beat: Beat position.
        instrument: Instrument name.
        ngram_surprise: Surprise from n-gram context [0, 1].
        tonal_surprise: Surprise from tonal hierarchy [0, 1].
        combined_surprise: Weighted combination [0, 1].
    """

    pitch: int
    start_beat: float
    instrument: str
    ngram_surprise: float
    tonal_surprise: float
    combined_surprise: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "pitch": self.pitch,
            "start_beat": self.start_beat,
            "instrument": self.instrument,
            "ngram_surprise": round(self.ngram_surprise, 4),
            "tonal_surprise": round(self.tonal_surprise, 4),
            "combined_surprise": round(self.combined_surprise, 4),
        }


@dataclass(frozen=True)
class SurpriseAnalysis:
    """Full surprise analysis of a ScoreIR.

    Attributes:
        per_note: Per-note surprise annotations.
        moving_average: Windowed surprise curve (window=8 notes).
        peak_locations: Beat positions of surprise peaks (top 10%).
        overall_predictability: Mean surprise [0, 1]; lower = more predictable.
        surprise_variance: Variance of surprise scores.
    """

    per_note: tuple[NoteSurprise, ...]
    moving_average: tuple[float, ...]
    peak_locations: tuple[float, ...]
    overall_predictability: float
    surprise_variance: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize for evaluation.json."""
        return {
            "per_note_count": len(self.per_note),
            "moving_average_length": len(self.moving_average),
            "peak_locations": list(self.peak_locations),
            "overall_predictability": round(self.overall_predictability, 4),
            "surprise_variance": round(self.surprise_variance, 4),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SurpriseAnalysis:
        """Deserialize from dict (summary form — per_note not stored)."""
        return cls(
            per_note=(),
            moving_average=(),
            peak_locations=tuple(data.get("peak_locations", [])),
            overall_predictability=data.get("overall_predictability", 0.0),
            surprise_variance=data.get("surprise_variance", 0.0),
        )


class SurpriseScorer:
    """Computes surprise scores for a ScoreIR.

    Uses a bigram (n=2) pitch-class transition model combined with
    the Krumhansl tonal hierarchy to measure how unexpected each note is.

    Args:
        key: Key of the piece (e.g., "C major").
        ngram_order: N-gram order for transition model (default 2).
        tonal_weight: Weight for tonal hierarchy component [0, 1].
        window_size: Moving average window size.

    Example:
        >>> scorer = SurpriseScorer(key="C major")
        >>> analysis = scorer.analyze(score_ir)
        >>> analysis.overall_predictability
        0.35
    """

    def __init__(
        self,
        key: str = "C major",
        ngram_order: int = 2,
        tonal_weight: float = 0.4,
        window_size: int = 8,
    ) -> None:
        self.key = key
        self.ngram_order = ngram_order
        self.tonal_weight = tonal_weight
        self.window_size = window_size
        _, self.tonal_profile = _parse_key(key)

    def _tonal_surprise(self, pitch: int) -> float:
        """Compute tonal surprise for a single pitch.

        Lower stability in the Krumhansl profile = higher surprise.

        Args:
            pitch: MIDI note number.

        Returns:
            Surprise value [0, 1].
        """
        pc = pitch % 12
        stability = self.tonal_profile[pc]
        # Invert: high stability → low surprise
        max_stability = max(self.tonal_profile)
        if max_stability == 0:
            return 0.5
        return 1.0 - (stability / max_stability)

    def _build_ngram_model(
        self,
        pitch_classes: list[int],
    ) -> dict[tuple[int, ...], Counter[int]]:
        """Build an n-gram transition model from pitch class sequence.

        Args:
            pitch_classes: Ordered pitch classes (0-11).

        Returns:
            Context tuple → Counter of next pitch class occurrences.
        """
        model: dict[tuple[int, ...], Counter[int]] = defaultdict(Counter)
        ctx_len = self.ngram_order - 1
        for i in range(ctx_len, len(pitch_classes)):
            context = tuple(pitch_classes[i - ctx_len : i])
            model[context][pitch_classes[i]] += 1
        return dict(model)

    def _ngram_surprise(
        self,
        context: tuple[int, ...],
        pitch_class: int,
        model: dict[tuple[int, ...], Counter[int]],
    ) -> float:
        """Compute n-gram surprise for a pitch given context.

        Uses negative log probability normalized to [0, 1].

        Args:
            context: Previous pitch classes.
            pitch_class: Current pitch class.
            model: Pre-built n-gram model.

        Returns:
            Surprise value [0, 1].
        """
        counts = model.get(context)
        if counts is None or sum(counts.values()) == 0:
            return 0.5  # Unknown context → moderate surprise

        total = sum(counts.values())
        count = counts.get(pitch_class, 0)

        if count == 0:
            # Unseen transition: high surprise but not max
            return 0.9

        prob = count / total
        # -log2(p) normalized: max reasonable surprise ~3.32 (p=0.1)
        raw_surprise = -math.log2(prob)
        # Normalize to [0, 1] using log2(12) as practical max
        max_surprise = math.log2(12)
        return min(raw_surprise / max_surprise, 1.0)

    def analyze(self, score_ir: ScoreIR) -> SurpriseAnalysis:
        """Analyze surprise distribution across all notes.

        Collects all notes across all sections/parts, sorts by beat,
        builds an n-gram model, then scores each note.

        Args:
            score_ir: The score to analyze.

        Returns:
            Complete SurpriseAnalysis with per-note scores and summary.
        """
        # Collect all notes, sorted by start_beat
        all_notes: list[tuple[int, float, str]] = []
        for section in score_ir.sections:
            for part in section.parts:
                for note in part.notes:
                    all_notes.append((note.pitch, note.start_beat, note.instrument))

        all_notes.sort(key=lambda n: n[1])

        if not all_notes:
            return SurpriseAnalysis(
                per_note=(),
                moving_average=(),
                peak_locations=(),
                overall_predictability=0.0,
                surprise_variance=0.0,
            )

        # Build n-gram model from pitch classes
        pitch_classes = [p % 12 for p, _, _ in all_notes]
        model = self._build_ngram_model(pitch_classes)

        # Score each note
        ctx_len = self.ngram_order - 1
        note_surprises: list[NoteSurprise] = []

        for i, (pitch, beat, instrument) in enumerate(all_notes):
            tonal_s = self._tonal_surprise(pitch)

            if i >= ctx_len:
                context = tuple(pitch_classes[i - ctx_len : i])
                ngram_s = self._ngram_surprise(context, pitch_classes[i], model)
            else:
                ngram_s = 0.5  # Not enough context

            combined = self.tonal_weight * tonal_s + (1.0 - self.tonal_weight) * ngram_s

            note_surprises.append(
                NoteSurprise(
                    pitch=pitch,
                    start_beat=beat,
                    instrument=instrument,
                    ngram_surprise=ngram_s,
                    tonal_surprise=tonal_s,
                    combined_surprise=combined,
                )
            )

        # Moving average
        scores = [ns.combined_surprise for ns in note_surprises]
        moving_avg = self._moving_average(scores)

        # Peak locations (top 10%)
        if scores:
            sorted_scores = sorted(scores, reverse=True)
            threshold_idx = max(1, len(sorted_scores) // 10)
            threshold = sorted_scores[threshold_idx - 1]
            peaks = tuple(ns.start_beat for ns in note_surprises if ns.combined_surprise >= threshold)
        else:
            peaks = ()

        # Summary stats
        mean = sum(scores) / len(scores) if scores else 0.0
        variance = sum((s - mean) ** 2 for s in scores) / len(scores) if scores else 0.0

        return SurpriseAnalysis(
            per_note=tuple(note_surprises),
            moving_average=tuple(moving_avg),
            peak_locations=peaks,
            overall_predictability=mean,
            surprise_variance=variance,
        )

    def _moving_average(self, values: list[float]) -> list[float]:
        """Compute moving average with the configured window size.

        Args:
            values: Input values.

        Returns:
            Smoothed values (same length, padded at edges).
        """
        if not values:
            return []
        result: list[float] = []
        half = self.window_size // 2
        for i in range(len(values)):
            start = max(0, i - half)
            end = min(len(values), i + half + 1)
            window = values[start:end]
            result.append(sum(window) / len(window))
        return result
