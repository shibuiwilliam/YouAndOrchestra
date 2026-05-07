"""Phrase-level IR types for the phrase-first melody pipeline.

A phrase is a musical sentence — it has a function (statement, question,
answer), a cadence type, and optionally a motif assignment. Phrases are
planned in Layer M1 before any pitches are chosen.

See PROJECT.md §3.2 (Layer M1) and IMPROVEMENT.md §4.1.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yao.ir.motif import Motif


class PhraseFunction(Enum):
    """The rhetorical function of a phrase within a section.

    Musical phrases, like sentences, can make statements, ask questions,
    or provide answers. These functions determine cadence placement,
    motif transformation choice, and contour direction.
    """

    STATEMENT = "statement"
    QUESTION = "question"
    ANSWER = "answer"
    DEVELOPMENT = "development"
    RECAPITULATION = "recapitulation"
    CODA = "coda"


class CadenceType(Enum):
    """The type of cadence at the end of a phrase.

    Cadences provide the sense of punctuation in music. Authentic cadences
    are like periods; half cadences are like commas; deceptive cadences
    are like plot twists.
    """

    AUTHENTIC = "authentic"
    HALF = "half"
    PLAGAL = "plagal"
    DECEPTIVE = "deceptive"
    PHRYGIAN = "phrygian"
    NONE = "none"


@dataclass(frozen=True)
class Phrase:
    """A single phrase in the melody plan.

    Attributes:
        start_bar: First bar of the phrase (0-indexed).
        end_bar: Bar after the last bar of the phrase (exclusive).
        function: Rhetorical function of the phrase.
        cadence: Cadence type at the end of the phrase.
        motif_id: ID of the motif assigned to this phrase, or None.
        motif_transformation: Transformation applied to the motif, or None.
        target_pitch: MIDI pitch the phrase aims toward, or None if unset.
        contour_archetype: Contour shape ('arch', 'descending', 'wave', 'ascending').
    """

    start_bar: int
    end_bar: int
    function: PhraseFunction
    cadence: CadenceType
    motif_id: str | None = None
    motif_transformation: str | None = None
    target_pitch: int | None = None
    contour_archetype: str = "arch"

    @property
    def length_bars(self) -> int:
        """Number of bars in this phrase."""
        return self.end_bar - self.start_bar


@dataclass(frozen=True)
class PhrasePlan:
    """A complete phrase plan for a section or piece.

    The phrase plan is the output of Layer M1 and the primary input to
    Layer M2. It defines the logical structure of the melody before
    any pitches are chosen.

    Attributes:
        phrases: Ordered tuple of phrases covering the entire section.
        motif_library: Mapping of motif IDs to Motif objects used in this plan.
    """

    phrases: tuple[Phrase, ...]
    motif_library: dict[str, Motif] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Initialize motif_library if not provided."""
        if self.motif_library is None:
            object.__setattr__(self, "motif_library", {})

    @property
    def total_bars(self) -> int:
        """Total number of bars covered by the plan."""
        if not self.phrases:
            return 0
        return max(p.end_bar for p in self.phrases) - min(p.start_bar for p in self.phrases)

    @property
    def phrase_count(self) -> int:
        """Number of phrases in the plan."""
        return len(self.phrases)
