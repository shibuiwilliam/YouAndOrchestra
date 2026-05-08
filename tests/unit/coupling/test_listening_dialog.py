"""Tests for the Listening-Agent Dialog system.

Phase 5.5 — IMPROVEMENT.md §6.3.
"""

from __future__ import annotations

from yao.coupling.listening_dialog import (
    GENERATION_ORDER,
    DialogRelation,
    EnsembleContext,
    EnsembleRole,
    RhythmicDialogEdge,
    RhythmicDialogGraph,
    build_default_dialog_graph,
    topological_generation_order,
)


class TestEnsembleRole:
    def test_all_roles(self) -> None:
        assert len(EnsembleRole) == 6

    def test_generation_order(self) -> None:
        assert GENERATION_ORDER[0] == EnsembleRole.BASS
        assert GENERATION_ORDER[-1] == EnsembleRole.FILLS


class TestDialogRelation:
    def test_all_relations(self) -> None:
        assert len(DialogRelation) == 5


class TestRhythmicDialogGraph:
    def test_empty_graph(self) -> None:
        graph = RhythmicDialogGraph(edges=())
        assert graph.edge_count == 0

    def test_followers_of(self) -> None:
        edge = RhythmicDialogEdge(
            leader="bass",
            follower="drums",
            relation=DialogRelation.COMPLEMENT,
        )
        graph = RhythmicDialogGraph(edges=(edge,))
        assert len(graph.followers_of("bass")) == 1
        assert len(graph.followers_of("drums")) == 0

    def test_leaders_of(self) -> None:
        edge = RhythmicDialogEdge(
            leader="bass",
            follower="drums",
            relation=DialogRelation.COMPLEMENT,
        )
        graph = RhythmicDialogGraph(edges=(edge,))
        assert len(graph.leaders_of("drums")) == 1
        assert len(graph.leaders_of("bass")) == 0


class TestBuildDefaultDialogGraph:
    def test_with_trio(self) -> None:
        graph = build_default_dialog_graph(["bass", "drums", "piano"])
        assert graph.edge_count >= 2

    def test_with_duo(self) -> None:
        graph = build_default_dialog_graph(["bass", "drums"])
        assert graph.edge_count >= 1

    def test_with_single(self) -> None:
        graph = build_default_dialog_graph(["piano"])
        assert graph.edge_count == 0


class TestTopologicalOrder:
    def test_leaders_before_followers(self) -> None:
        graph = RhythmicDialogGraph(
            edges=(
                RhythmicDialogEdge("bass", "drums", DialogRelation.COMPLEMENT),
                RhythmicDialogEdge("drums", "piano", DialogRelation.FILL_GAP),
            )
        )
        order = topological_generation_order(["piano", "bass", "drums"], graph)
        assert order.index("bass") < order.index("drums")
        assert order.index("drums") < order.index("piano")

    def test_unconnected_instruments_included(self) -> None:
        graph = RhythmicDialogGraph(edges=())
        order = topological_generation_order(["piano", "bass"], graph)
        assert len(order) == 2


class TestEnsembleContext:
    def test_creation(self) -> None:
        ctx = EnsembleContext(
            role=EnsembleRole.BASS,
            ensemble_history={"drums": [0.0, 1.0, 2.0]},
            current_bar=4,
        )
        assert ctx.role == EnsembleRole.BASS
        assert len(ctx.ensemble_history["drums"]) == 3
