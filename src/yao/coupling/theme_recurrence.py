"""Theme Recurrence Graph — long-form thematic coherence.

Plans theme returns and transformations across a composition, ensuring
that long-form pieces have measurable thematic unity.

Belongs to Layer 2.5 (Combination & Coupling).

See IMPROVEMENT.md §6.4, PROJECT.md §3.4.6, CLAUDE.md Phase 4.5.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum


class ThemeTransformation(StrEnum):
    """How a theme is transformed when it recurs."""

    IDENTITY = "identity"
    TRANSPOSE = "transpose"
    INVERT = "invert"
    AUGMENT = "augment"
    DIMINISH = "diminish"
    ORNAMENT = "ornament"
    FRAGMENT = "fragment"
    SEQUENCE = "sequence"


@dataclass(frozen=True)
class ThemeRecurrence:
    """A planned recurrence of a theme with transformation.

    Attributes:
        source_section: Section where the theme first appears.
        source_bars: (start_bar, end_bar) of the original theme.
        target_section: Section where the theme recurs.
        target_bars: (start_bar, end_bar) of the recurrence.
        transformation: How the theme is transformed.
        transformation_params: Additional parameters (e.g., transpose interval).
    """

    source_section: str
    source_bars: tuple[int, int]
    target_section: str
    target_bars: tuple[int, int]
    transformation: ThemeTransformation
    transformation_params: dict[str, int | float | str]


@dataclass(frozen=True)
class ThemeRecurrenceGraph:
    """All planned theme recurrences across the composition.

    Attributes:
        edges: Tuple of ThemeRecurrence edges.
    """

    edges: tuple[ThemeRecurrence, ...]

    def themes_in_section(self, section_id: str) -> list[ThemeRecurrence]:
        """Return all theme recurrences targeting this section."""
        return [e for e in self.edges if e.target_section == section_id]

    @property
    def recurrence_count(self) -> int:
        """Number of recurrence edges."""
        return len(self.edges)


# Form-specific recurrence patterns
_FORM_PATTERNS: dict[str, list[tuple[str, str, ThemeTransformation]]] = {
    "AABA": [
        ("verse", "verse2", ThemeTransformation.IDENTITY),
        ("verse", "verse3", ThemeTransformation.ORNAMENT),
    ],
    "verse_chorus": [
        ("chorus", "chorus2", ThemeTransformation.IDENTITY),
        ("verse", "verse2", ThemeTransformation.TRANSPOSE),
    ],
    "rondo": [
        ("theme", "theme2", ThemeTransformation.IDENTITY),
        ("theme", "theme3", ThemeTransformation.ORNAMENT),
        ("theme", "theme4", ThemeTransformation.IDENTITY),
    ],
    "sonata": [
        ("exposition", "recapitulation", ThemeTransformation.TRANSPOSE),
        ("exposition", "development", ThemeTransformation.FRAGMENT),
    ],
    "through_composed": [
        ("verse", "verse2", ThemeTransformation.SEQUENCE),
    ],
}


def plan_theme_recurrences(
    section_names: list[str],
    section_bars: list[int],
    form: str = "verse_chorus",
    rng: random.Random | None = None,
) -> ThemeRecurrenceGraph:
    """Plan theme recurrences based on the song form.

    Args:
        section_names: List of section names in order.
        section_bars: List of bar counts per section.
        form: Song form identifier.
        rng: Random number generator.

    Returns:
        A ThemeRecurrenceGraph with planned recurrences.
    """
    if rng is None:
        rng = random.Random()

    edges: list[ThemeRecurrence] = []

    # Find matching section pairs
    section_starts: dict[str, int] = {}
    current_bar = 0
    for name, bars in zip(section_names, section_bars, strict=False):
        section_starts[name] = current_bar
        current_bar += bars

    # Get form-specific patterns
    patterns = _FORM_PATTERNS.get(form, _FORM_PATTERNS["verse_chorus"])

    for source_name, target_name, transformation in patterns:
        if source_name in section_starts and target_name in section_starts:
            source_start = section_starts[source_name]
            source_idx = section_names.index(source_name)
            source_end = source_start + section_bars[source_idx]

            target_start = section_starts[target_name]
            target_idx = section_names.index(target_name)
            target_end = target_start + section_bars[target_idx]

            params: dict[str, int | float | str] = {}
            if transformation == ThemeTransformation.TRANSPOSE:
                params["interval"] = rng.choice([5, 7, -5, -7])
            elif transformation == ThemeTransformation.FRAGMENT:
                params["fragment_ratio"] = 0.5

            edges.append(
                ThemeRecurrence(
                    source_section=source_name,
                    source_bars=(source_start, source_end),
                    target_section=target_name,
                    target_bars=(target_start, target_end),
                    transformation=transformation,
                    transformation_params=params,
                )
            )

    return ThemeRecurrenceGraph(edges=tuple(edges))
