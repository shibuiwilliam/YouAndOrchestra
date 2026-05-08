"""Tests for the Genre Vector Space.

Phase 5.0 — IMPROVEMENT.md §6.1.
"""

from __future__ import annotations

from yao.coupling.genre_vector import GENRE_DIMENSIONS, GenreVector


class TestGenreVector:
    def test_creation(self) -> None:
        vec = GenreVector(coordinates=(0.5,) * 12, component_genres={"jazz": 1.0})
        assert vec.dimensionality == 12

    def test_from_profile_values(self) -> None:
        vec = GenreVector.from_profile_values(
            "jazz_ballad",
            swing_ratio=0.67,
            chord_complexity=0.8,
        )
        assert "jazz_ballad" in vec.component_genres
        assert vec.dimensionality == len(GENRE_DIMENSIONS)

    def test_blend_two_genres(self) -> None:
        jazz = GenreVector.from_profile_values("jazz", swing_ratio=0.67, chord_complexity=0.8)
        rock = GenreVector.from_profile_values("rock", swing_ratio=0.5, chord_complexity=0.3)
        blended = GenreVector.blend((jazz, 0.6), (rock, 0.4))
        assert blended.dimensionality == 12
        assert "jazz" in blended.component_genres
        assert "rock" in blended.component_genres
        # Swing ratio should be between jazz and rock values
        swing_idx = 0  # swing_ratio is first dimension
        assert 0.5 <= blended.coordinates[swing_idx] <= 0.67

    def test_blend_three_genres(self) -> None:
        a = GenreVector.from_profile_values("a", swing_ratio=0.5)
        b = GenreVector.from_profile_values("b", swing_ratio=0.6)
        c = GenreVector.from_profile_values("c", swing_ratio=0.7)
        blended = GenreVector.blend((a, 1.0), (b, 1.0), (c, 1.0))
        # Equal weights: average swing = 0.6
        assert abs(blended.coordinates[0] - 0.6) < 0.01

    def test_blend_empty(self) -> None:
        blended = GenreVector.blend()
        assert blended.dimensionality == len(GENRE_DIMENSIONS)

    def test_distance_to_self_is_zero(self) -> None:
        vec = GenreVector.from_profile_values("jazz", swing_ratio=0.67)
        assert vec.distance_to(vec) == 0.0

    def test_distance_increases_with_difference(self) -> None:
        a = GenreVector(coordinates=(0.0,) * 12)
        b = GenreVector(coordinates=(1.0,) * 12)
        c = GenreVector(coordinates=(0.5,) * 12)
        assert a.distance_to(b) > a.distance_to(c)

    def test_nearest_neighbors(self) -> None:
        target = GenreVector(coordinates=(0.5,) * 12)
        close = GenreVector(coordinates=(0.51,) * 12)
        far = GenreVector(coordinates=(0.9,) * 12)
        registry = [close, far]
        neighbors = target.nearest_neighbors(registry, k=1)
        assert len(neighbors) == 1
        assert neighbors[0][0] is close

    def test_blend_preserves_total_weight(self) -> None:
        a = GenreVector.from_profile_values("a")
        b = GenreVector.from_profile_values("b")
        blended = GenreVector.blend((a, 0.7), (b, 0.3))
        total = sum(blended.component_genres.values())
        assert abs(total - 1.0) < 0.01
