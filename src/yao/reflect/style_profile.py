"""User Style Profile — cross-project pattern mining from annotations.

Aggregates listening annotations to build a user preference profile.
Profile influence on generation is opt-in via spec ``style_profile.use: true``.

Belongs to Layer 7 (Reflection).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from yao.ir.score_ir import ScoreIR
from yao.schema.feedback import FeedbackTag, HumanFeedbackEntry

if TYPE_CHECKING:
    from yao.schema.composition import CompositionSpec


@dataclass
class StylePreference:
    """A single learned preference.

    Attributes:
        dimension: What aspect (e.g., "tempo", "density", "harmony_complexity").
        preferred_range: Preferred value range [low, high].
        confidence: How confident the preference is (0.0-1.0).
        source_count: Number of annotations contributing to this preference.
    """

    dimension: str
    preferred_range: tuple[float, float]
    confidence: float
    source_count: int


@dataclass
class UserStyleProfile:
    """Aggregated user preference profile.

    Built from annotations across projects. Updated explicitly
    via ``yao reflect ingest <annotations>`` — never automatically.

    Attributes:
        user_id: User identifier (default: "local").
        preferences: Learned preferences.
        total_annotations: Total annotations ingested.
    """

    user_id: str = "local"
    preferences: list[StylePreference] = field(default_factory=list)
    total_annotations: int = 0

    def add_preference(self, pref: StylePreference) -> None:
        """Add or update a preference dimension.

        Args:
            pref: The preference to add.
        """
        # Replace existing preference for same dimension
        self.preferences = [p for p in self.preferences if p.dimension != pref.dimension]
        self.preferences.append(pref)

    def get_preference(self, dimension: str) -> StylePreference | None:
        """Look up a preference by dimension.

        Args:
            dimension: The dimension name.

        Returns:
            StylePreference or None.
        """
        for p in self.preferences:
            if p.dimension == dimension:
                return p
        return None

    def update_from(self, feedback: list[HumanFeedbackEntry], score: ScoreIR) -> None:
        """Update preferences from human feedback and the associated score.

        Analyzes feedback tags in relation to the score's musical features
        to learn user preferences. Accumulates across calls with decayed
        running averages.

        Args:
            feedback: List of feedback entries for a single iteration.
            score: The ScoreIR that was evaluated.
        """
        if not feedback:
            return

        self.total_annotations += len(feedback)
        all_notes = score.all_notes()
        if not all_notes:
            return

        # Extract score features for preference learning
        velocities = [n.velocity for n in all_notes]
        avg_velocity = sum(velocities) / len(velocities)
        note_density = len(all_notes) / max(score.total_bars(), 1)

        # Count positive vs negative feedback
        positive_count = sum(1 for f in feedback if f.tag == FeedbackTag.LOVED)
        negative_count = sum(
            1 for f in feedback if f.tag in (FeedbackTag.BORING, FeedbackTag.CLICHE, FeedbackTag.CONFUSING)
        )
        density_low = sum(1 for f in feedback if f.tag == FeedbackTag.TOO_SPARSE)
        density_high = sum(1 for f in feedback if f.tag == FeedbackTag.TOO_DENSE)

        # Update density preference
        if density_low > 0 or density_high > 0 or positive_count > 0:
            existing = self.get_preference("density")
            if density_low > density_high:
                preferred = (note_density, note_density * 1.5)
            elif density_high > density_low:
                preferred = (note_density * 0.5, note_density)
            elif existing:
                preferred = existing.preferred_range
            else:
                preferred = (note_density * 0.8, note_density * 1.2)

            count = (existing.source_count if existing else 0) + len(feedback)
            confidence = min(1.0, count / 10.0)
            self.add_preference(StylePreference("density", preferred, confidence, count))

        # Update dynamics preference from velocity patterns
        if positive_count > 0:
            existing = self.get_preference("dynamics")
            preferred = (max(1.0, avg_velocity - 15), min(127.0, avg_velocity + 15))
            count = (existing.source_count if existing else 0) + positive_count
            confidence = min(1.0, count / 5.0)
            self.add_preference(StylePreference("dynamics", preferred, confidence, count))

        # Update overall quality signal
        total = positive_count + negative_count
        if total > 0:
            quality_signal = positive_count / total * 10.0
            existing = self.get_preference("overall")
            if existing:
                # Decayed running average
                old_weight = existing.source_count
                new_weight = total
                old_avg = (existing.preferred_range[0] + existing.preferred_range[1]) / 2.0
                blended = (old_avg * old_weight + quality_signal * new_weight) / (old_weight + new_weight)
                preferred = (max(0.0, blended - 1.0), min(10.0, blended + 1.0))
                count = old_weight + new_weight
            else:
                preferred = (max(0.0, quality_signal - 1.0), min(10.0, quality_signal + 1.0))
                count = total
            confidence = min(1.0, count / 10.0)
            self.add_preference(StylePreference("overall", preferred, confidence, count))

    def update_from_outcome(
        self,
        score: ScoreIR,
        accepted: bool,
        evaluation_scores: dict[str, float] | None = None,
    ) -> None:
        """Update preferences from a generation outcome (accept/reject).

        Learns from whether the user accepted or rejected a generated piece,
        and optionally from automated evaluation scores. This enables
        automated preference learning without explicit annotation.

        Args:
            score: The generated ScoreIR.
            accepted: True if user accepted, False if rejected.
            evaluation_scores: Optional dict of metric_name -> score (0.0-1.0).
        """
        all_notes = score.all_notes()
        if not all_notes:
            return

        self.total_annotations += 1
        weight = 1 if accepted else -1

        # Learn tempo preference
        tempo = score.tempo_bpm if hasattr(score, "tempo_bpm") else 120.0
        existing_tempo = self.get_preference("tempo")
        if existing_tempo:
            old_avg = (existing_tempo.preferred_range[0] + existing_tempo.preferred_range[1]) / 2.0
            old_count = existing_tempo.source_count
            if accepted:
                blended = (old_avg * old_count + tempo) / (old_count + 1)
                margin = max(10.0, abs(tempo - blended) + 10.0)
            else:
                blended = old_avg
                margin = max(10.0, (existing_tempo.preferred_range[1] - existing_tempo.preferred_range[0]) / 2.0)
            count = old_count + 1
        else:
            blended = tempo
            margin = 20.0
            count = 1
        confidence = min(1.0, count / 8.0)
        self.add_preference(StylePreference("tempo", (blended - margin, blended + margin), confidence, count))

        # Learn density preference from outcome
        note_density = len(all_notes) / max(score.total_bars(), 1)
        existing_density = self.get_preference("density")
        if accepted:
            if existing_density:
                old_count = existing_density.source_count
                old_avg = (existing_density.preferred_range[0] + existing_density.preferred_range[1]) / 2.0
                blended_d = (old_avg * old_count + note_density) / (old_count + 1)
                count_d = old_count + 1
            else:
                blended_d = note_density
                count_d = 1
            margin_d = blended_d * 0.3
            confidence_d = min(1.0, count_d / 6.0)
            self.add_preference(
                StylePreference("density", (blended_d - margin_d, blended_d + margin_d), confidence_d, count_d)
            )

        # Learn from evaluation scores
        if evaluation_scores:
            for metric, value in evaluation_scores.items():
                existing_metric = self.get_preference(f"eval_{metric}")
                if existing_metric:
                    old_count = existing_metric.source_count
                    old_avg = (existing_metric.preferred_range[0] + existing_metric.preferred_range[1]) / 2.0
                    blended_m = (old_avg * old_count + value * weight) / (old_count + abs(weight))
                    count_m = old_count + 1
                else:
                    blended_m = value if accepted else 0.5
                    count_m = 1
                confidence_m = min(1.0, count_m / 5.0)
                self.add_preference(
                    StylePreference(
                        f"eval_{metric}",
                        (max(0.0, blended_m - 0.15), min(1.0, blended_m + 0.15)),
                        confidence_m,
                        count_m,
                    )
                )

    def save(self, path: Path) -> None:
        """Save profile to JSON.

        Args:
            path: Output path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "user_id": self.user_id,
            "total_annotations": self.total_annotations,
            "preferences": [
                {
                    "dimension": p.dimension,
                    "preferred_range": list(p.preferred_range),
                    "confidence": p.confidence,
                    "source_count": p.source_count,
                }
                for p in self.preferences
            ],
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> UserStyleProfile:
        """Load profile from JSON.

        Args:
            path: Path to profile JSON.

        Returns:
            Loaded profile, or empty profile if file doesn't exist.
        """
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        prefs = [
            StylePreference(
                dimension=p["dimension"],
                preferred_range=tuple(p["preferred_range"]),
                confidence=p["confidence"],
                source_count=p["source_count"],
            )
            for p in data.get("preferences", [])
        ]
        return cls(
            user_id=data.get("user_id", "local"),
            preferences=prefs,
            total_annotations=data.get("total_annotations", 0),
        )

    def bias(self, spec: CompositionSpec) -> CompositionSpec:
        """Apply learned preferences as soft biases on a spec.

        Only adjusts generation parameters where the profile has
        sufficient confidence (>= 0.5). Spec-explicit values always
        take priority over profile biases.

        Args:
            spec: The composition spec to bias.

        Returns:
            A potentially modified CompositionSpec.
        """
        if not self.preferences:
            return spec

        gen_updates: dict[str, object] = {}

        # Bias temperature based on overall quality preference
        overall = self.get_preference("overall")
        if overall and overall.confidence >= 0.5:
            # High overall scores correlate with current temperature
            # Low scores suggest more exploration needed
            avg = (overall.preferred_range[0] + overall.preferred_range[1]) / 2.0
            if avg < 5.0:  # noqa: PLR2004
                # User rates low — try more variation
                gen_updates["temperature"] = min(1.0, spec.generation.temperature + 0.1)

        # Bias tempo from memorability preferences
        memorability = self.get_preference("memorability")
        if memorability and memorability.confidence >= 0.5:
            avg_mem = (memorability.preferred_range[0] + memorability.preferred_range[1]) / 2.0
            if avg_mem < 5.0:  # noqa: PLR2004
                # Low memorability → tighter temperature for more repetition
                gen_updates["temperature"] = max(0.1, spec.generation.temperature - 0.1)

        if gen_updates:
            new_gen = spec.generation.model_copy(update=gen_updates)
            return spec.model_copy(update={"generation": new_gen})
        return spec
