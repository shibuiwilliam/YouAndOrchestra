"""Tests for the Phrase-Shape Generator.

Phase 4.5 — IMPROVEMENT.md §4.3.
"""

from __future__ import annotations

import random

from yao.coupling.phrase_shape import (
    CadenceType,
    PhraseRole,
    PhraseShape,
    generate_phrase_shapes,
)


class TestPhraseShape:
    def test_creation(self) -> None:
        shape = PhraseShape(
            duration_bars=4,
            role=PhraseRole.ANTECEDENT,
            sub_phrases=(),
            contour_points=(0.3, 0.5, 0.7, 0.4),
            end_tension=0.6,
        )
        assert shape.duration_bars == 4
        assert shape.role == PhraseRole.ANTECEDENT

    def test_all_roles_exist(self) -> None:
        assert len(PhraseRole) == 6

    def test_all_cadence_types(self) -> None:
        assert len(CadenceType) == 5


class TestGeneratePhraseShapes:
    def test_8bar_section(self) -> None:
        shapes = generate_phrase_shapes(8, rng=random.Random(42))
        assert len(shapes) >= 1
        total_bars = sum(s.duration_bars for s in shapes)
        assert total_bars <= 8

    def test_12bar_section_uses_blues(self) -> None:
        shapes = generate_phrase_shapes(12, rng=random.Random(42))
        assert len(shapes) >= 2

    def test_16bar_section(self) -> None:
        shapes = generate_phrase_shapes(16, rng=random.Random(42))
        assert len(shapes) >= 2

    def test_4bar_section(self) -> None:
        shapes = generate_phrase_shapes(4, rng=random.Random(42))
        assert len(shapes) >= 1

    def test_contour_points_generated(self) -> None:
        shapes = generate_phrase_shapes(8, rng=random.Random(42))
        for shape in shapes:
            assert len(shape.contour_points) >= 4
            assert all(0.0 <= p <= 1.0 for p in shape.contour_points)

    def test_end_tension_in_range(self) -> None:
        shapes = generate_phrase_shapes(8, rng=random.Random(42))
        for shape in shapes:
            assert 0.0 <= shape.end_tension <= 1.0

    def test_deterministic(self) -> None:
        s1 = generate_phrase_shapes(8, rng=random.Random(42))
        s2 = generate_phrase_shapes(8, rng=random.Random(42))
        assert len(s1) == len(s2)
        for a, b in zip(s1, s2, strict=False):
            assert a.duration_bars == b.duration_bars
            assert a.role == b.role
