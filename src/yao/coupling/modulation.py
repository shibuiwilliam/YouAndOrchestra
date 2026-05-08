"""Modulation Planner — key modulation strategies.

Implements 7 modulation strategies that produce ModulationPlan objects
consumed by the Harmony Theorist when populating HarmonyPlan.modulations.

Belongs to Layer 2.5 (Combination & Coupling).

See IMPROVEMENT.md §5.2, PROJECT.md §3.4.3, CLAUDE.md Phase 4.0.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum

from yao.constants.music import NOTE_NAMES


class ModulationStrategy(StrEnum):
    """The 7 modulation strategies."""

    PIVOT_CHORD = "pivot_chord"
    DIRECT = "direct"
    CHROMATIC = "chromatic"
    SEQUENTIAL = "sequential"
    ENHARMONIC = "enharmonic"
    COMMON_TONE = "common_tone"
    THIRD_RELATION = "third_relation"


@dataclass(frozen=True)
class ModulationEvent:
    """A planned key modulation.

    Attributes:
        at_bar: Bar number where the modulation occurs.
        from_key: Source key (e.g., "C major").
        to_key: Target key (e.g., "G major").
        strategy: Which modulation strategy is used.
        pivot_chord: Optional pivot chord symbol for pivot-chord modulation.
    """

    at_bar: int
    from_key: str
    to_key: str
    strategy: ModulationStrategy
    pivot_chord: str | None = None


@dataclass(frozen=True)
class ModulationPlan:
    """A complete modulation plan for a composition.

    Attributes:
        events: Tuple of planned ModulationEvents, ordered by bar.
        source_key: The starting key of the piece.
    """

    events: tuple[ModulationEvent, ...]
    source_key: str

    @property
    def modulation_count(self) -> int:
        """Number of modulations in the plan."""
        return len(self.events)


# Closely related keys by interval (in semitones) from the tonic
_CLOSE_KEY_INTERVALS: dict[str, list[int]] = {
    "major": [7, 5, 9, 2, -3],  # V, IV, vi, ii, relative minor
    "minor": [3, 7, 5, -2, 10],  # III, v, iv, VII, relative major
}

# Strategy preferences by genre (from IMPROVEMENT.md §5.2)
_GENRE_STRATEGY_WEIGHTS: dict[str, dict[ModulationStrategy, float]] = {
    "classical": {
        ModulationStrategy.PIVOT_CHORD: 0.40,
        ModulationStrategy.DIRECT: 0.10,
        ModulationStrategy.CHROMATIC: 0.15,
        ModulationStrategy.SEQUENTIAL: 0.15,
        ModulationStrategy.COMMON_TONE: 0.10,
        ModulationStrategy.THIRD_RELATION: 0.10,
        ModulationStrategy.ENHARMONIC: 0.00,
    },
    "jazz": {
        ModulationStrategy.PIVOT_CHORD: 0.15,
        ModulationStrategy.DIRECT: 0.20,
        ModulationStrategy.CHROMATIC: 0.20,
        ModulationStrategy.SEQUENTIAL: 0.10,
        ModulationStrategy.COMMON_TONE: 0.10,
        ModulationStrategy.THIRD_RELATION: 0.15,
        ModulationStrategy.ENHARMONIC: 0.10,
    },
    "cinematic": {
        ModulationStrategy.PIVOT_CHORD: 0.10,
        ModulationStrategy.DIRECT: 0.20,
        ModulationStrategy.CHROMATIC: 0.15,
        ModulationStrategy.SEQUENTIAL: 0.05,
        ModulationStrategy.COMMON_TONE: 0.10,
        ModulationStrategy.THIRD_RELATION: 0.35,
        ModulationStrategy.ENHARMONIC: 0.05,
    },
    "default": {
        ModulationStrategy.PIVOT_CHORD: 0.25,
        ModulationStrategy.DIRECT: 0.20,
        ModulationStrategy.CHROMATIC: 0.15,
        ModulationStrategy.SEQUENTIAL: 0.10,
        ModulationStrategy.COMMON_TONE: 0.10,
        ModulationStrategy.THIRD_RELATION: 0.15,
        ModulationStrategy.ENHARMONIC: 0.05,
    },
}


def plan_modulations(
    source_key: str,
    total_bars: int,
    section_boundaries: list[int],
    genre: str = "default",
    max_modulations: int = 3,
    rng: random.Random | None = None,
) -> ModulationPlan:
    """Plan modulations for a composition.

    Places modulations at section boundaries, choosing target keys
    and strategies based on the genre and current key.

    Args:
        source_key: Starting key (e.g., "C major").
        total_bars: Total number of bars in the piece.
        section_boundaries: Bar numbers where sections start.
        genre: Genre name for strategy selection.
        max_modulations: Maximum number of modulations.
        rng: Random number generator.

    Returns:
        A ModulationPlan with events ordered by bar.
    """
    if rng is None:
        rng = random.Random()

    strategy_weights = _GENRE_STRATEGY_WEIGHTS.get(genre, _GENRE_STRATEGY_WEIGHTS["default"])

    events: list[ModulationEvent] = []
    current_key = source_key

    # Only modulate at section boundaries after the first section
    candidate_bars = [b for b in section_boundaries if b > 0 and b < total_bars - 4]

    for bar in candidate_bars:
        if len(events) >= max_modulations:
            break

        # Decide whether to modulate (probability based on position)
        position_ratio = bar / total_bars
        mod_prob = 0.3 if position_ratio < 0.7 else 0.15
        if rng.random() > mod_prob:
            continue

        # Select strategy
        strategies = list(strategy_weights.keys())
        weights = [strategy_weights[s] for s in strategies]
        strategy = rng.choices(strategies, weights=weights, k=1)[0]

        # Select target key
        target_key = _select_target_key(current_key, strategy, rng)
        if target_key == current_key:
            continue

        # Determine pivot chord if applicable
        pivot = None
        if strategy == ModulationStrategy.PIVOT_CHORD:
            pivot = _find_pivot_chord(current_key, target_key)

        events.append(
            ModulationEvent(
                at_bar=bar,
                from_key=current_key,
                to_key=target_key,
                strategy=strategy,
                pivot_chord=pivot,
            )
        )
        current_key = target_key

    return ModulationPlan(
        events=tuple(sorted(events, key=lambda e: e.at_bar)),
        source_key=source_key,
    )


def _select_target_key(current_key: str, strategy: ModulationStrategy, rng: random.Random) -> str:
    """Select a target key based on the current key and strategy."""
    parts = current_key.split()
    if len(parts) < 2:
        return current_key

    root = parts[0]
    scale_type = parts[1]

    from yao.constants.music import ENHARMONIC_MAP

    # Normalize root
    normalized = root[0].upper() + root[1:] if len(root) > 1 else root.upper()
    if normalized in ENHARMONIC_MAP:
        normalized = ENHARMONIC_MAP[normalized]
    root_pc = NOTE_NAMES.index(normalized) if normalized in NOTE_NAMES else 0

    # Get related key intervals
    intervals = _CLOSE_KEY_INTERVALS.get(scale_type, _CLOSE_KEY_INTERVALS["major"])

    if strategy == ModulationStrategy.THIRD_RELATION:
        # Major 3rd relations (cinematic)
        interval = rng.choice([3, 4, 8, 9])
    elif strategy == ModulationStrategy.DIRECT:
        # Any closely related key
        interval = rng.choice(intervals)
    elif strategy == ModulationStrategy.CHROMATIC:
        # Half-step up or down
        interval = rng.choice([1, -1, 11])
    elif strategy == ModulationStrategy.SEQUENTIAL:
        # Step up
        interval = rng.choice([2, -2])
    else:
        # Default: closely related
        interval = rng.choice(intervals) if intervals else 7

    target_pc = (root_pc + interval) % 12
    target_root = NOTE_NAMES[target_pc]

    # Keep the same scale type for simplicity (modulating mode is separate)
    return f"{target_root} {scale_type}"


def _find_pivot_chord(from_key: str, to_key: str) -> str:
    """Find a common chord between two keys for pivot modulation."""
    # Simplified: use IV of the source key which often works as a pivot
    parts = from_key.split()
    if len(parts) < 2:
        return "IV"
    return "IV"
