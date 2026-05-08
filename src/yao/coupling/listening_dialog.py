"""Listening-Agent Dialog — turn-based ensemble generation.

Implements turn-based generation where later instruments respond to
what earlier instruments have already played, producing ensemble feel.

Default OFF (features.listening_agents=false). When enabled, generation
order is: bass -> drums -> harmony -> melody_primary -> melody_secondary -> fills.

Belongs to Layer 2.5 (Combination & Coupling).

See IMPROVEMENT.md §6.3, PROJECT.md §3.4.7, CLAUDE.md Phase 5.5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EnsembleRole(StrEnum):
    """Role priority for turn-based generation."""

    BASS = "bass"
    DRUMS = "drums"
    HARMONY = "harmony"
    MELODY_PRIMARY = "melody_primary"
    MELODY_SECONDARY = "melody_secondary"
    FILLS = "fills"


# Generation order: leaders first, followers last
GENERATION_ORDER: tuple[EnsembleRole, ...] = (
    EnsembleRole.BASS,
    EnsembleRole.DRUMS,
    EnsembleRole.HARMONY,
    EnsembleRole.MELODY_PRIMARY,
    EnsembleRole.MELODY_SECONDARY,
    EnsembleRole.FILLS,
)


class DialogRelation(StrEnum):
    """Rhythmic relationship between instruments."""

    COMPLEMENT = "complement"
    ECHO = "echo"
    SYNCOPATE_AGAINST = "syncopate_against"
    FILL_GAP = "fill_gap"
    UNISON = "unison"


@dataclass(frozen=True)
class RhythmicDialogEdge:
    """A causal edge: instrument_a's rhythm influences instrument_b.

    Attributes:
        leader: Instrument that plays first.
        follower: Instrument that responds.
        relation: How the follower relates to the leader.
        delay_beats: How long the follower waits before responding.
    """

    leader: str
    follower: str
    relation: DialogRelation
    delay_beats: float = 0.0


@dataclass(frozen=True)
class RhythmicDialogGraph:
    """Causal graph of rhythmic dialog between instruments.

    Attributes:
        edges: All dialog edges in the graph.
    """

    edges: tuple[RhythmicDialogEdge, ...]

    def followers_of(self, instrument: str) -> list[RhythmicDialogEdge]:
        """Return edges where this instrument is the leader."""
        return [e for e in self.edges if e.leader == instrument]

    def leaders_of(self, instrument: str) -> list[RhythmicDialogEdge]:
        """Return edges where this instrument is the follower."""
        return [e for e in self.edges if e.follower == instrument]

    @property
    def edge_count(self) -> int:
        """Number of dialog edges."""
        return len(self.edges)


@dataclass(frozen=True)
class EnsembleContext:
    """Context passed to a listening generator.

    Attributes:
        role: This instrument's ensemble role.
        ensemble_history: Map from instrument name to their generated notes
            (as beat positions). Earlier instruments' output is available.
        current_bar: Current bar being generated.
        chunk_size: Number of bars generated per turn.
    """

    role: EnsembleRole
    ensemble_history: dict[str, list[float]] = field(default_factory=dict)
    current_bar: int = 0
    chunk_size: int = 4


def build_default_dialog_graph(instruments: list[str]) -> RhythmicDialogGraph:
    """Build a default rhythmic dialog graph from instrument names.

    Creates complement/fill relationships based on common ensemble patterns.

    Args:
        instruments: List of instrument names.

    Returns:
        A RhythmicDialogGraph with default relationships.
    """
    edges: list[RhythmicDialogEdge] = []

    # Find instruments by common role names
    bass = next((i for i in instruments if "bass" in i.lower()), None)
    drums = next((i for i in instruments if "drum" in i.lower()), None)
    melody = next((i for i in instruments if i not in (bass, drums)), None)

    if bass and drums:
        edges.append(
            RhythmicDialogEdge(
                leader=bass,
                follower=drums,
                relation=DialogRelation.COMPLEMENT,
            )
        )

    if drums and melody:
        edges.append(
            RhythmicDialogEdge(
                leader=drums,
                follower=melody,
                relation=DialogRelation.FILL_GAP,
                delay_beats=0.0,
            )
        )

    if bass and melody:
        edges.append(
            RhythmicDialogEdge(
                leader=bass,
                follower=melody,
                relation=DialogRelation.COMPLEMENT,
            )
        )

    return RhythmicDialogGraph(edges=tuple(edges))


def topological_generation_order(
    instruments: list[str],
    dialog_graph: RhythmicDialogGraph,
) -> list[str]:
    """Order instruments so leaders precede followers.

    Args:
        instruments: All instrument names.
        dialog_graph: The dialog graph.

    Returns:
        Instruments ordered for turn-based generation.
    """
    # Build adjacency: leader -> followers
    leader_set: set[str] = set()
    follower_set: set[str] = set()
    for edge in dialog_graph.edges:
        leader_set.add(edge.leader)
        follower_set.add(edge.follower)

    # Leaders that are not followers go first
    pure_leaders = [i for i in instruments if i in leader_set and i not in follower_set]
    # Then instruments that are both leaders and followers
    mixed = [i for i in instruments if i in leader_set and i in follower_set]
    # Then pure followers
    pure_followers = [i for i in instruments if i in follower_set and i not in leader_set]
    # Then instruments not in the graph
    others = [i for i in instruments if i not in leader_set and i not in follower_set]

    return pure_leaders + mixed + pure_followers + others
