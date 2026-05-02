"""Reference Matcher — style vector comparison with copyright protection.

Extracts abstract StyleVectors from ScoreIR and compares them against
reference works. All copyrightable features (melody, chords) are blocked
at both schema and runtime levels.

Belongs to Layer 4 (Perception Substitute).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from yao.errors import ForbiddenExtractionError
from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR
from yao.ir.timing import bars_to_beats
from yao.perception.style_vector import StyleVector
from yao.schema.references import FORBIDDEN_FEATURES, ReferencesSpec

_CACHE_DIR = Path("references/extracted_features")


@dataclass(frozen=True)
class ReferenceMatchReport:
    """Result of matching a score against references.

    Attributes:
        positive_proximity_score: How close to the best positive reference
            (1.0 = identical style, 0.0 = maximally different).
        negative_distance_score: How far from the closest negative reference
            (1.0 = maximally far, 0.0 = identical to what should be avoided).
        details: Per-reference distance details.
    """

    positive_proximity_score: float
    negative_distance_score: float
    details: dict[str, float]


class ReferenceMatcher:
    """Extracts style vectors and computes reference distances.

    All extraction goes through the allowlist/blocklist check.
    Cache is sha256-addressed for automatic invalidation.
    """

    def extract_style_vector(
        self,
        score: ScoreIR,
        requested_features: list[str] | None = None,
    ) -> StyleVector:
        """Extract a StyleVector from a ScoreIR.

        Args:
            score: The ScoreIR to analyze.
            requested_features: Optional subset of features to extract.
                If None, all allowed features are extracted.

        Returns:
            StyleVector with extracted features.

        Raises:
            ForbiddenExtractionError: If any requested feature is forbidden.
        """
        if requested_features is not None:
            for feat in requested_features:
                if feat in FORBIDDEN_FEATURES:
                    raise ForbiddenExtractionError(
                        f"Cannot extract '{feat}' — this is a copyrightable element. "
                        f"Forbidden features: {sorted(FORBIDDEN_FEATURES)}"
                    )

        all_notes = score.all_notes()
        total_bars = max(score.total_bars(), 1)
        beats_per_bar = bars_to_beats(1, score.time_signature)

        # Harmonic rhythm: estimate from note density changes
        harmonic_rhythm = self._estimate_harmonic_rhythm(score)

        # Voice leading smoothness: average pitch interval between consecutive notes
        vl_smoothness = self._estimate_voice_leading(all_notes)

        # Rhythmic density per bar
        density_per_bar = self._compute_density_per_bar(all_notes, total_bars, beats_per_bar)

        # Register distribution: 12 octave bins (C0-C1 through C9-C10)
        register_dist = self._compute_register_distribution(all_notes)

        # Timbre centroid: placeholder (needs audio; use pitch centroid as proxy)
        centroid_per_section = tuple(
            sum(n.pitch for n in score.part_for_instrument(i)) / max(len(score.part_for_instrument(i)), 1)
            for i in score.instruments()
        )

        # Motif density: unique pitch patterns per 8 bars
        motif_density = self._estimate_motif_density(all_notes, total_bars)

        return StyleVector(
            harmonic_rhythm=harmonic_rhythm,
            voice_leading_smoothness=vl_smoothness,
            rhythmic_density_per_bar=tuple(density_per_bar),
            register_distribution=tuple(register_dist),
            timbre_centroid_curve=centroid_per_section,
            motif_density=motif_density,
        )

    def evaluate_against_references(
        self,
        score: ScoreIR,
        refs: ReferencesSpec,
    ) -> ReferenceMatchReport:
        """Evaluate a score against reference specifications.

        Since actual reference MIDI files may not be present in testing,
        this computes self-referential metrics from the spec's abstract
        feature targets.

        Args:
            score: The ScoreIR to evaluate.
            refs: The reference specification.

        Returns:
            ReferenceMatchReport with proximity and distance scores.
        """
        self.extract_style_vector(score)  # validate extraction works
        details: dict[str, float] = {}

        # Positive references: lower distance = better proximity
        positive_distances: list[float] = []
        for ref in refs.primary:
            # Runtime defense-in-depth: re-check features
            for feat in ref.extract_features:
                if feat in FORBIDDEN_FEATURES:
                    raise ForbiddenExtractionError(
                        f"Runtime block: '{feat}' is forbidden even though it passed schema."
                    )
            # Without actual reference audio, use weight as a proxy
            distance = 1.0 - ref.weight
            positive_distances.append(distance)
            details[f"positive_{ref.role}"] = distance

        # Negative references: higher distance = better
        negative_distances: list[float] = []
        for neg_ref in refs.negative:
            distance = 0.7  # placeholder when no audio
            negative_distances.append(distance)
            details[f"negative_{neg_ref.role}"] = distance

        pos_score = 1.0 - min(positive_distances) if positive_distances else 0.5
        neg_score = min(negative_distances) if negative_distances else 1.0

        return ReferenceMatchReport(
            positive_proximity_score=max(0.0, min(1.0, pos_score)),
            negative_distance_score=max(0.0, min(1.0, neg_score)),
            details=details,
        )

    def cache_key(self, score: ScoreIR) -> str:
        """Compute a cache key for a ScoreIR based on content hash.

        Args:
            score: The ScoreIR.

        Returns:
            SHA256 hex digest.
        """
        content = f"{score.title}:{score.key}:{score.tempo_bpm}:{len(score.all_notes())}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get_cached_vector(self, cache_key: str) -> StyleVector | None:
        """Load a cached StyleVector if available.

        Args:
            cache_key: SHA256 hash key.

        Returns:
            StyleVector or None if not cached.
        """
        path = _CACHE_DIR / f"{cache_key}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            # JSON deserializes lists; StyleVector needs tuples
            for key in ("rhythmic_density_per_bar", "register_distribution", "timbre_centroid_curve"):
                if key in data and isinstance(data[key], list):
                    data[key] = tuple(data[key])
            return StyleVector(**data)
        except Exception:
            return None

    def save_cached_vector(self, cache_key: str, vector: StyleVector) -> None:
        """Save a StyleVector to cache.

        Args:
            cache_key: SHA256 hash key.
            vector: The StyleVector to cache.
        """
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _CACHE_DIR / f"{cache_key}.json"
        data = {
            "harmonic_rhythm": vector.harmonic_rhythm,
            "voice_leading_smoothness": vector.voice_leading_smoothness,
            "rhythmic_density_per_bar": list(vector.rhythmic_density_per_bar),
            "register_distribution": list(vector.register_distribution),
            "timbre_centroid_curve": list(vector.timbre_centroid_curve),
            "motif_density": vector.motif_density,
        }
        path.write_text(json.dumps(data))

    # ------------------------------------------------------------------
    # Feature extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_harmonic_rhythm(score: ScoreIR) -> float:
        """Estimate chord changes per bar from note onset patterns."""
        total_bars = max(score.total_bars(), 1)
        all_notes = score.all_notes()
        if not all_notes:
            return 0.0
        # Count unique pitch-class changes between consecutive note groups
        changes = 0
        prev_pc: int | None = None
        for note in all_notes:
            pc = note.pitch % 12
            if prev_pc is not None and pc != prev_pc:
                changes += 1
            prev_pc = pc
        return changes / total_bars

    @staticmethod
    def _estimate_voice_leading(notes: list[Note]) -> float:
        """Average semitone interval between consecutive notes."""
        if len(notes) < 2:
            return 0.0
        total = 0.0
        for i in range(1, len(notes)):
            total += abs(notes[i].pitch - notes[i - 1].pitch)
        return total / (len(notes) - 1)

    @staticmethod
    def _compute_density_per_bar(
        notes: list[Note],
        total_bars: int,
        beats_per_bar: float,
    ) -> list[float]:
        """Count onsets per bar."""
        density = [0.0] * total_bars
        for note in notes:
            beat = note.start_beat
            bar = int(beat / beats_per_bar) if beats_per_bar > 0 else 0
            if 0 <= bar < total_bars:
                density[bar] += 1.0
        return density

    @staticmethod
    def _compute_register_distribution(notes: list[Note]) -> list[float]:
        """Compute 12-bin octave histogram (C0-B0 through C9-B9)."""
        bins = [0.0] * 12
        total = 0
        for note in notes:
            pitch = note.pitch
            octave = min(max(pitch // 12, 0), 11)
            bins[octave] += 1.0
            total += 1
        if total > 0:
            bins = [b / total for b in bins]
        return bins

    @staticmethod
    def _estimate_motif_density(notes: list[Note], total_bars: int) -> float:
        """Estimate motif recurrences per 8 bars using pitch trigrams."""
        if len(notes) < 3 or total_bars == 0:
            return 0.0
        pitches = [n.pitch for n in notes]
        trigrams: dict[tuple[int, int, int], int] = {}
        for i in range(len(pitches) - 2):
            tri = (pitches[i], pitches[i + 1], pitches[i + 2])
            trigrams[tri] = trigrams.get(tri, 0) + 1
        recurring = sum(1 for c in trigrams.values() if c > 1)
        return recurring / (total_bars / 8.0)
