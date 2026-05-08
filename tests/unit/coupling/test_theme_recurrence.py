"""Tests for the Theme Recurrence Graph.

Phase 4.5 — IMPROVEMENT.md §6.4.
"""

from __future__ import annotations

import random

from yao.coupling.theme_recurrence import (
    ThemeRecurrence,
    ThemeRecurrenceGraph,
    ThemeTransformation,
    plan_theme_recurrences,
)


class TestThemeTransformation:
    def test_all_transformations(self) -> None:
        assert len(ThemeTransformation) == 8

    def test_identity(self) -> None:
        assert ThemeTransformation.IDENTITY == "identity"


class TestThemeRecurrenceGraph:
    def test_empty_graph(self) -> None:
        graph = ThemeRecurrenceGraph(edges=())
        assert graph.recurrence_count == 0

    def test_themes_in_section(self) -> None:
        edge = ThemeRecurrence(
            source_section="verse",
            source_bars=(0, 8),
            target_section="verse2",
            target_bars=(16, 24),
            transformation=ThemeTransformation.IDENTITY,
            transformation_params={},
        )
        graph = ThemeRecurrenceGraph(edges=(edge,))
        assert len(graph.themes_in_section("verse2")) == 1
        assert len(graph.themes_in_section("bridge")) == 0


class TestPlanThemeRecurrences:
    def test_verse_chorus_form(self) -> None:
        graph = plan_theme_recurrences(
            section_names=["verse", "chorus", "verse2", "chorus2"],
            section_bars=[8, 8, 8, 8],
            form="verse_chorus",
            rng=random.Random(42),
        )
        assert isinstance(graph, ThemeRecurrenceGraph)
        assert graph.recurrence_count >= 1

    def test_aaba_form(self) -> None:
        graph = plan_theme_recurrences(
            section_names=["verse", "verse2", "bridge", "verse3"],
            section_bars=[8, 8, 8, 8],
            form="AABA",
            rng=random.Random(42),
        )
        assert graph.recurrence_count >= 1

    def test_through_composed(self) -> None:
        graph = plan_theme_recurrences(
            section_names=["verse", "verse2", "outro"],
            section_bars=[8, 8, 4],
            form="through_composed",
            rng=random.Random(42),
        )
        assert isinstance(graph, ThemeRecurrenceGraph)

    def test_recurrence_bars_valid(self) -> None:
        graph = plan_theme_recurrences(
            section_names=["verse", "chorus", "verse2", "chorus2"],
            section_bars=[8, 8, 8, 8],
            form="verse_chorus",
            rng=random.Random(42),
        )
        for edge in graph.edges:
            assert edge.source_bars[0] < edge.source_bars[1]
            assert edge.target_bars[0] < edge.target_bars[1]

    def test_deterministic(self) -> None:
        kwargs = dict(
            section_names=["verse", "chorus", "verse2", "chorus2"],
            section_bars=[8, 8, 8, 8],
            form="verse_chorus",
        )
        g1 = plan_theme_recurrences(**kwargs, rng=random.Random(42))
        g2 = plan_theme_recurrences(**kwargs, rng=random.Random(42))
        assert g1.recurrence_count == g2.recurrence_count
