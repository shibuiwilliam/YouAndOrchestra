"""MoodProfile — multi-dimensional mood representation.

Extends Russell's circumplex (arousal × valence) with genre-relevant
extra dimensions. Used as a target in composition specs and as an
estimated output from the PsychMapper estimators.

References:
    Russell (1980): "A circumplex model of affect."
    Zentner, Grandjean & Scherer (2008): "Emotions evoked by the sound
    of music: characterization, classification, and measurement."
    Juslin & Sloboda (2010): "Handbook of Music and Emotion."

Goodhart defense: MoodProfile.distance() can be gamed by matching
individual dimensions superficially. Cross-check with the PsychMapper's
per-bar tension estimate and the Programmatic Critic's emotional
coherence rules to ensure the mood is sustained, not just hit at one point.

Belongs to Layer 4 (Perception Substitute).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yao.ir.score_ir import ScoreIR


@dataclass(frozen=True)
class MoodProfile:
    """Multi-dimensional mood representation for composition targeting.

    The primary dimensions (arousal, valence) follow Russell's circumplex.
    Extended dimensions capture genre-relevant qualities that the
    circumplex alone cannot distinguish (e.g., "nostalgic" and "mysterious"
    occupy similar circumplex positions but differ in sophistication/intimacy).

    All values are in [-1.0, 1.0] for arousal/valence, [0.0, 1.0] for extended.

    Attributes:
        arousal: -1.0 (calm) to +1.0 (excited).
        valence: -1.0 (negative) to +1.0 (positive).
        tension: 0.0 (relaxed) to 1.0 (taut).
        intimacy: 0.0 (grand/public) to 1.0 (personal/close).
        grandeur: 0.0 (humble/small) to 1.0 (epic/massive).
        nostalgia: 0.0 (present-focused) to 1.0 (past-longing).
        aggression: 0.0 (gentle) to 1.0 (fierce).
        sophistication: 0.0 (simple/naive) to 1.0 (complex/refined).
    """

    arousal: float = 0.0
    valence: float = 0.0
    tension: float = 0.0
    intimacy: float = 0.0
    grandeur: float = 0.0
    nostalgia: float = 0.0
    aggression: float = 0.0
    sophistication: float = 0.0

    def distance(self, other: MoodProfile) -> float:
        """Euclidean distance to another MoodProfile.

        All dimensions are weighted equally. For genre-specific weighting,
        use the GenreAwareEvaluator's mood comparison instead.

        Args:
            other: The other MoodProfile.

        Returns:
            Euclidean distance (>= 0).
        """
        diffs = [
            self.arousal - other.arousal,
            self.valence - other.valence,
            self.tension - other.tension,
            self.intimacy - other.intimacy,
            self.grandeur - other.grandeur,
            self.nostalgia - other.nostalgia,
            self.aggression - other.aggression,
            self.sophistication - other.sophistication,
        ]
        return math.sqrt(sum(d * d for d in diffs))

    def to_dict(self) -> dict[str, float]:
        """Serialize to dict.

        Returns:
            Dict with all mood dimensions.
        """
        return {
            "arousal": self.arousal,
            "valence": self.valence,
            "tension": self.tension,
            "intimacy": self.intimacy,
            "grandeur": self.grandeur,
            "nostalgia": self.nostalgia,
            "aggression": self.aggression,
            "sophistication": self.sophistication,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> MoodProfile:
        """Deserialize from dict.

        Args:
            data: Dict with mood dimension values.

        Returns:
            MoodProfile.
        """
        return cls(
            arousal=data.get("arousal", 0.0),
            valence=data.get("valence", 0.0),
            tension=data.get("tension", 0.0),
            intimacy=data.get("intimacy", 0.0),
            grandeur=data.get("grandeur", 0.0),
            nostalgia=data.get("nostalgia", 0.0),
            aggression=data.get("aggression", 0.0),
            sophistication=data.get("sophistication", 0.0),
        )


def estimate_mood_from_score(score: ScoreIR) -> MoodProfile:
    """Estimate a MoodProfile from a generated ScoreIR.

    Uses the PsychMapper estimators for arousal and valence,
    and derives extended dimensions from musical features.

    Args:
        score: The ScoreIR to analyze.

    Returns:
        Estimated MoodProfile.
    """
    from yao.perception.psych_mapper import estimate_arousal, estimate_valence

    arousal = estimate_arousal(score)
    valence = estimate_valence(score)

    # Map arousal/valence (0-1) to MoodProfile range (-1 to 1)
    arousal_mapped = arousal * 2.0 - 1.0
    valence_mapped = valence * 2.0 - 1.0

    # Derive extended dimensions from arousal/valence + musical features
    notes = score.all_notes()
    if not notes:
        return MoodProfile(arousal=arousal_mapped, valence=valence_mapped)

    # Tension: high arousal + low valence
    tension = max(0.0, min(1.0, arousal * 0.6 + (1.0 - valence) * 0.4))

    # Intimacy: low density + low register + quiet
    avg_vel = sum(n.velocity for n in notes) / len(notes)
    density = len(notes) / max(max(n.start_beat + n.duration_beats for n in notes), 1.0)
    intimacy = max(0.0, min(1.0, 1.0 - (density / 4.0) * 0.5 - (avg_vel / 127.0) * 0.5))

    # Grandeur: high density + loud + wide register
    pitch_range = max(n.pitch for n in notes) - min(n.pitch for n in notes)
    grandeur = max(0.0, min(1.0, (avg_vel / 127.0) * 0.4 + (pitch_range / 48.0) * 0.3 + (density / 4.0) * 0.3))

    # Aggression: high arousal + low valence + loud
    aggression = max(0.0, min(1.0, arousal * 0.4 + (1.0 - valence) * 0.3 + (avg_vel / 127.0) * 0.3))

    return MoodProfile(
        arousal=arousal_mapped,
        valence=valence_mapped,
        tension=tension,
        intimacy=intimacy,
        grandeur=grandeur,
        nostalgia=0.0,  # Cannot be estimated from symbolic features alone
        aggression=aggression,
        sophistication=0.0,  # Requires harmonic analysis beyond current scope
    )
