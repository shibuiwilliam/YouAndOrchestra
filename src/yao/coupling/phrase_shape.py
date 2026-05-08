"""Phrase-Shape Generator — antecedent/consequent phrase structures.

Generates PhraseShape plans that define intra-section structure
(8-bar period, 8-bar sentence, 12-bar blues, 16-bar ballad).

Belongs to Layer 2.5 (Combination & Coupling).

See IMPROVEMENT.md §4.3, PROJECT.md §3.4.6, CLAUDE.md Phase 4.5.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum


class PhraseRole(StrEnum):
    """Structural role of a phrase."""

    ANTECEDENT = "antecedent"
    CONSEQUENT = "consequent"
    CONTINUATION = "continuation"
    BASIC_IDEA = "basic_idea"
    CODETTA = "codetta"
    EXTENSION = "extension"


class CadenceType(StrEnum):
    """Types of cadences that end phrases."""

    HALF = "half"
    AUTHENTIC = "authentic"
    PLAGAL = "plagal"
    DECEPTIVE = "deceptive"
    IMPERFECT = "imperfect"


@dataclass(frozen=True)
class SubPhrase:
    """A sub-phrase within a PhraseShape.

    Attributes:
        start_bar: Starting bar (relative to phrase start).
        duration_bars: Length in bars.
        role: Structural role.
        cadence: Cadence type at the end of this sub-phrase.
    """

    start_bar: int
    duration_bars: int
    role: PhraseRole
    cadence: CadenceType


@dataclass(frozen=True)
class PhraseShape:
    """A planned phrase structure with internal organization.

    Attributes:
        duration_bars: Total phrase length in bars.
        role: Overall phrase role (antecedent, consequent, etc.).
        sub_phrases: Internal sub-phrase structure.
        contour_points: 4-8 control points for melodic contour [0.0-1.0].
        end_tension: Tension level at the end of the phrase [0.0-1.0].
    """

    duration_bars: int
    role: PhraseRole
    sub_phrases: tuple[SubPhrase, ...]
    contour_points: tuple[float, ...]
    end_tension: float


# Common phrase templates
_TEMPLATES: dict[str, list[tuple[int, PhraseRole, CadenceType]]] = {
    "period_8bar": [
        (4, PhraseRole.ANTECEDENT, CadenceType.HALF),
        (4, PhraseRole.CONSEQUENT, CadenceType.AUTHENTIC),
    ],
    "sentence_8bar": [
        (2, PhraseRole.BASIC_IDEA, CadenceType.HALF),
        (2, PhraseRole.BASIC_IDEA, CadenceType.HALF),
        (4, PhraseRole.CONTINUATION, CadenceType.AUTHENTIC),
    ],
    "blues_12bar": [
        (4, PhraseRole.ANTECEDENT, CadenceType.HALF),
        (4, PhraseRole.ANTECEDENT, CadenceType.HALF),
        (4, PhraseRole.CONSEQUENT, CadenceType.AUTHENTIC),
    ],
    "ballad_16bar": [
        (4, PhraseRole.ANTECEDENT, CadenceType.HALF),
        (4, PhraseRole.CONSEQUENT, CadenceType.IMPERFECT),
        (4, PhraseRole.ANTECEDENT, CadenceType.HALF),
        (4, PhraseRole.CONSEQUENT, CadenceType.AUTHENTIC),
    ],
    "through_composed": [
        (4, PhraseRole.CONTINUATION, CadenceType.HALF),
    ],
}


def generate_phrase_shapes(
    section_bars: int,
    section_name: str = "verse",
    genre: str = "default",
    rng: random.Random | None = None,
) -> list[PhraseShape]:
    """Generate phrase shapes for a section.

    Args:
        section_bars: Number of bars in the section.
        section_name: Section name for template selection.
        genre: Genre for template preferences.
        rng: Random number generator.

    Returns:
        List of PhraseShape objects covering the section.
    """
    if rng is None:
        rng = random.Random()

    # Select template based on section length
    if section_bars == 12:
        template_name = "blues_12bar"
    elif section_bars >= 16:
        template_name = "ballad_16bar"
    elif section_bars >= 8:
        template_name = rng.choice(["period_8bar", "sentence_8bar"])
    else:
        template_name = "through_composed"

    template = _TEMPLATES[template_name]

    shapes: list[PhraseShape] = []
    current_bar = 0

    for duration, role, cadence in template:
        if current_bar + duration > section_bars:
            break

        sub = SubPhrase(
            start_bar=0,
            duration_bars=duration,
            role=role,
            cadence=cadence,
        )

        # Generate contour points
        contour = _generate_contour(role, duration, rng)

        # End tension depends on cadence type
        end_tension = _cadence_tension(cadence)

        shapes.append(
            PhraseShape(
                duration_bars=duration,
                role=role,
                sub_phrases=(sub,),
                contour_points=tuple(contour),
                end_tension=end_tension,
            )
        )
        current_bar += duration

    return shapes


def _generate_contour(role: PhraseRole, duration: int, rng: random.Random) -> list[float]:
    """Generate melodic contour control points for a phrase role."""
    n_points = min(max(4, duration), 8)

    if role == PhraseRole.ANTECEDENT:
        # Rise to a question — arch shape
        return [0.3 + 0.5 * (i / (n_points - 1)) for i in range(n_points)]
    elif role == PhraseRole.CONSEQUENT:
        # Answer — arch then descend
        peak = n_points // 2
        return [0.7 * (i / peak) if i <= peak else 0.7 * (1 - (i - peak) / (n_points - peak)) for i in range(n_points)]
    elif role == PhraseRole.CONTINUATION:
        # Gradually building
        return [0.2 + 0.6 * (i / (n_points - 1)) for i in range(n_points)]
    elif role == PhraseRole.BASIC_IDEA:
        # Short, moderate
        return [0.4 + 0.2 * rng.random() for _ in range(n_points)]
    else:
        return [0.5] * n_points


def _cadence_tension(cadence: CadenceType) -> float:
    """Return the tension level for a cadence type."""
    return {
        CadenceType.HALF: 0.6,
        CadenceType.AUTHENTIC: 0.1,
        CadenceType.PLAGAL: 0.2,
        CadenceType.DECEPTIVE: 0.7,
        CadenceType.IMPERFECT: 0.4,
    }.get(cadence, 0.5)
