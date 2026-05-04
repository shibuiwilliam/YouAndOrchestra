"""Human feedback to adaptation converter.

Translates bar-level tagged feedback (from feedback.yaml) into
concrete SpecAdaptation objects that the Conductor can apply.

Belongs to Layer 7 (Conductor).
"""

from __future__ import annotations

from yao.conductor.feedback import SpecAdaptation
from yao.schema.composition import CompositionSpec
from yao.schema.feedback import FeedbackSpec, FeedbackTag, HumanFeedbackEntry


def convert_feedback_to_adaptations(
    feedback: FeedbackSpec,
    spec: CompositionSpec,
) -> list[SpecAdaptation]:
    """Translate tagged human feedback into spec adaptations.

    Each feedback tag maps to one or more SpecAdaptation objects that
    the Conductor's ``apply_adaptations()`` can consume.

    Args:
        feedback: Parsed feedback.yaml with bar-level entries.
        spec: Current composition spec.

    Returns:
        List of SpecAdaptation objects.
    """
    adaptations: list[SpecAdaptation] = []

    for entry in feedback.human_feedback:
        adaptations.extend(_adapt_entry(entry, spec))

    return adaptations


def _adapt_entry(
    entry: HumanFeedbackEntry,
    spec: CompositionSpec,
) -> list[SpecAdaptation]:
    """Convert a single feedback entry to adaptations.

    Args:
        entry: One feedback entry.
        spec: Current spec.

    Returns:
        List of adaptations for this entry.
    """
    tag = entry.tag
    bars = entry.target_bars
    bar_desc = f"bar(s) {bars}" if bars else "global"

    if tag == FeedbackTag.WEAK_CLIMAX:
        return _adapt_weak_climax(entry, spec, bar_desc)
    if tag == FeedbackTag.BORING:
        return _adapt_boring(entry, spec, bar_desc)
    if tag == FeedbackTag.LOVED:
        return _adapt_loved(entry, spec, bar_desc)
    if tag == FeedbackTag.TOO_DENSE:
        return _adapt_too_dense(entry, spec, bar_desc)
    if tag == FeedbackTag.TOO_SPARSE:
        return _adapt_too_sparse(entry, spec, bar_desc)
    if tag == FeedbackTag.CLICHE:
        return _adapt_cliche(entry, spec, bar_desc)
    if tag == FeedbackTag.WRONG_EMOTION:
        return _adapt_wrong_emotion(entry, spec, bar_desc)
    if tag == FeedbackTag.CONFUSING:
        return _adapt_confusing(entry, spec, bar_desc)
    return []


def _adapt_weak_climax(
    entry: HumanFeedbackEntry,
    spec: CompositionSpec,
    bar_desc: str,
) -> list[SpecAdaptation]:
    """Strengthen climax: increase tension trajectory, add dynamics."""
    section = _find_section_at_bar(spec, entry.target_bars)
    adaptations = []
    if section:
        adaptations.append(
            SpecAdaptation(
                field=f"sections.{section}.dynamics",
                old_value="current",
                new_value="ff",
                reason=f"Weak climax at {bar_desc}: boosting dynamics to ff",
            )
        )
    adaptations.append(
        SpecAdaptation(
            field="generation.temperature",
            old_value=str(spec.generation.temperature),
            new_value=str(min(1.0, spec.generation.temperature + 0.1)),
            reason=f"Weak climax at {bar_desc}: increasing temperature for more intensity",
        )
    )
    return adaptations


def _adapt_boring(
    entry: HumanFeedbackEntry,
    spec: CompositionSpec,
    bar_desc: str,
) -> list[SpecAdaptation]:
    """Counter boredom: increase temperature, add rhythmic variation."""
    return [
        SpecAdaptation(
            field="generation.temperature",
            old_value=str(spec.generation.temperature),
            new_value=str(min(1.0, spec.generation.temperature + 0.15)),
            reason=f"Boring at {bar_desc}: increasing temperature for more variation",
        ),
    ]


def _adapt_loved(
    entry: HumanFeedbackEntry,
    spec: CompositionSpec,
    bar_desc: str,
) -> list[SpecAdaptation]:
    """Preserve loved sections: mark for preservation during regeneration."""
    return [
        SpecAdaptation(
            field="preserve_bars",
            old_value="none",
            new_value=str(entry.target_bars),
            reason=f"Loved at {bar_desc}: preserving these bars in regeneration",
        ),
    ]


def _adapt_too_dense(
    entry: HumanFeedbackEntry,
    spec: CompositionSpec,
    bar_desc: str,
) -> list[SpecAdaptation]:
    """Reduce density: lower temperature."""
    return [
        SpecAdaptation(
            field="generation.temperature",
            old_value=str(spec.generation.temperature),
            new_value=str(max(0.1, spec.generation.temperature - 0.15)),
            reason=f"Too dense at {bar_desc}: reducing temperature for simpler texture",
        ),
    ]


def _adapt_too_sparse(
    entry: HumanFeedbackEntry,
    spec: CompositionSpec,
    bar_desc: str,
) -> list[SpecAdaptation]:
    """Increase density: raise temperature."""
    return [
        SpecAdaptation(
            field="generation.temperature",
            old_value=str(spec.generation.temperature),
            new_value=str(min(1.0, spec.generation.temperature + 0.15)),
            reason=f"Too sparse at {bar_desc}: increasing temperature for more notes",
        ),
    ]


def _adapt_cliche(
    entry: HumanFeedbackEntry,
    spec: CompositionSpec,
    bar_desc: str,
) -> list[SpecAdaptation]:
    """Counter cliches: increase temperature and change seed."""
    seed = spec.generation.seed or 42
    return [
        SpecAdaptation(
            field="generation.temperature",
            old_value=str(spec.generation.temperature),
            new_value=str(min(1.0, spec.generation.temperature + 0.2)),
            reason=f"Cliche at {bar_desc}: increasing temperature for less predictable output",
        ),
        SpecAdaptation(
            field="generation.seed",
            old_value=str(seed),
            new_value=str(seed + 7),
            reason=f"Cliche at {bar_desc}: changing seed to explore different harmonic space",
        ),
    ]


def _adapt_wrong_emotion(
    entry: HumanFeedbackEntry,
    spec: CompositionSpec,
    bar_desc: str,
) -> list[SpecAdaptation]:
    """Wrong emotion: change seed, note user's description."""
    seed = spec.generation.seed or 42
    note_info = f" (user note: {entry.note})" if entry.note else ""
    return [
        SpecAdaptation(
            field="generation.seed",
            old_value=str(seed),
            new_value=str(seed + 13),
            reason=f"Wrong emotion at {bar_desc}{note_info}: changing seed",
        ),
    ]


def _adapt_confusing(
    entry: HumanFeedbackEntry,
    spec: CompositionSpec,
    bar_desc: str,
) -> list[SpecAdaptation]:
    """Confusing: simplify by reducing temperature."""
    return [
        SpecAdaptation(
            field="generation.temperature",
            old_value=str(spec.generation.temperature),
            new_value=str(max(0.1, spec.generation.temperature - 0.2)),
            reason=f"Confusing at {bar_desc}: reducing temperature for clearer structure",
        ),
    ]


def _find_section_at_bar(spec: CompositionSpec, bars: list[int]) -> str | None:
    """Find which section contains the given bar(s).

    Args:
        spec: Composition spec with sections.
        bars: List of 1-indexed bar numbers.

    Returns:
        Section name, or None if not found.
    """
    if not bars:
        return None
    target_bar = bars[0]
    current_bar = 1
    for section in spec.sections:
        end_bar = current_bar + section.bars
        if current_bar <= target_bar < end_bar:
            return section.name
        current_bar = end_bar
    return None


def summarize_adaptations(adaptations: list[SpecAdaptation]) -> str:
    """Format adaptations for CLI display.

    Args:
        adaptations: List of adaptations.

    Returns:
        Multi-line summary string.
    """
    if not adaptations:
        return "No adaptations generated."
    lines = [f"  - {a.reason}" for a in adaptations]
    return "\n".join(lines)
