"""Automatic thematic recurrence — turn a form's "return" sections into
restatements of the theme (PROJECT_IMPROVEMENT §P1.2).

The legacy generator produces a fresh, memoryless melody for the *primary*
melodic instrument in every section, so a piece never states a theme and
brings it back. The generator already knows how to recall + develop a prior
section's melody when a section's ``recall_melody_from`` field is set
(``stochastic.py`` 275→327 realizes the primary melody from the recalled
theme via ``_generate_melody_from_motif``). That capability is simply never
triggered automatically.

This module fills that gap: given a spec, it identifies sections that are
*returns* of an earlier section — by matching a normalized name "stem"
(``A`` / ``A_prime`` / ``A_doublePrime`` → ``a``; ``verse`` / ``verse_2`` →
``verse``) — and points their ``recall_melody_from`` at the first section
sharing that stem. It never overrides a value the user set, and never makes a
section recall itself.

It is additive and only invoked when ``generation.thematic_development`` is
enabled, so default output is unchanged.

Belongs to Layer 2 (Generation Strategy).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from yao.schema.composition import CompositionSpec

# Variation markers appended to a base section name to denote a return.
# Sorted longest-first so compound markers ("doubleprime") are matched before
# their substrings ("prime").
_VARIATION_SUFFIXES: tuple[str, ...] = tuple(
    sorted(
        (
            "prime",
            "doubleprime",
            "tripleprime",
            "reprise",
            "recap",
            "return",
            "restate",
            "var",
            "alt",
        ),
        key=len,
        reverse=True,
    )
)

# Return markers sometimes prefixed instead (e.g. "return_a", "reprise_chorus").
_RETURN_PREFIXES: tuple[str, ...] = ("return_", "reprise_", "recap_", "restate_")

_TRAILING_NUMBER_RE = re.compile(r"[_\-\s]*\d+$")


@dataclass(frozen=True)
class RecallAssignment:
    """A single auto-recall decision (for provenance/reporting).

    Attributes:
        section: The return section that will recall a theme.
        recalls: The earlier section whose melody is restated.
        stem: The shared normalized name stem that matched them.
    """

    section: str
    recalls: str
    stem: str


def _section_stem(name: str) -> str:
    """Normalize a section name to its thematic stem.

    Strips return prefixes, variation suffixes, trailing digits, primes, and
    separators so that variants of the same material collapse to one stem.

    Args:
        name: The raw section name.

    Returns:
        The normalized stem (never empty — falls back to the lowercased,
        stripped original if normalization would empty it).
    """
    original = name.strip().lower()
    stem = original

    for prefix in _RETURN_PREFIXES:
        if stem.startswith(prefix):
            stem = stem[len(prefix) :]
            break

    changed = True
    while changed:
        changed = False
        candidate = stem.rstrip("'`´ _-")
        candidate = _TRAILING_NUMBER_RE.sub("", candidate)
        for suffix in _VARIATION_SUFFIXES:
            candidate = re.sub(rf"[_\-\s]*{suffix}$", "", candidate)
        candidate = candidate.rstrip("'`´ _-")
        if candidate and candidate != stem:
            stem = candidate
            changed = True

    return stem or original


def compute_thematic_recalls(spec: CompositionSpec) -> list[RecallAssignment]:
    """Compute auto-recall assignments for a spec's return sections.

    Pure and side-effect-free. Does not consider the ``thematic_development``
    flag — callers decide whether to apply the result.

    A section is a "return" when its stem matches an earlier section's stem.
    It recalls the *first* section with that stem. Sections whose
    ``recall_melody_from`` is already set are left untouched.

    Args:
        spec: The composition spec.

    Returns:
        Assignments in section order (may be empty).
    """
    first_by_stem: dict[str, str] = {}
    assignments: list[RecallAssignment] = []

    for section in spec.sections:
        stem = _section_stem(section.name)
        if stem not in first_by_stem:
            first_by_stem[stem] = section.name
            continue
        # This section is a return of an earlier one sharing the stem.
        source = first_by_stem[stem]
        if source == section.name:
            continue  # never self-recall
        if section.recall_melody_from is not None:
            continue  # respect an explicit user choice
        assignments.append(RecallAssignment(section=section.name, recalls=source, stem=stem))

    return assignments


def auto_thematic_recall(
    spec: CompositionSpec,
) -> tuple[CompositionSpec, list[RecallAssignment]]:
    """Return a spec with ``recall_melody_from`` set on return sections.

    Reuses the generator's proven recall path so the primary melody restates
    the theme in return sections instead of wandering independently.

    Args:
        spec: The composition spec.

    Returns:
        Tuple of (possibly-new spec, applied assignments). When there is
        nothing to do, the original spec is returned unchanged.
    """
    assignments = compute_thematic_recalls(spec)
    if not assignments:
        return spec, []

    recall_by_section = {a.section: a.recalls for a in assignments}
    new_sections = [
        section.model_copy(update={"recall_melody_from": recall_by_section[section.name]})
        if section.name in recall_by_section
        else section
        for section in spec.sections
    ]
    return spec.model_copy(update={"sections": new_sections}), assignments
