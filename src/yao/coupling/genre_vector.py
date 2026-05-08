"""Genre Vector Space — n-way genre blending.

Embeds genre profiles as points in a multi-dimensional feature space,
enabling blending, interpolation, and neighbor queries.

Belongs to Layer 2.5 (Combination & Coupling).

See IMPROVEMENT.md §6.1, PROJECT.md §3.4.4, CLAUDE.md Phase 5.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Dimensions of the genre vector space
GENRE_DIMENSIONS: tuple[str, ...] = (
    "swing_ratio",
    "syncopation_density",
    "chord_complexity",
    "chord_extension_avg",
    "rhythmic_subdivision",
    "dynamic_range",
    "timbral_brightness",
    "instrumental_density",
    "melodic_chromaticism",
    "phrase_length_avg",
    "tempo_typical",
    "structural_repetition",
)


@dataclass(frozen=True)
class GenreVector:
    """A point in genre feature space.

    Attributes:
        coordinates: Tuple of float values, one per dimension.
        component_genres: Map from genre name to blend weight.
    """

    coordinates: tuple[float, ...]
    component_genres: dict[str, float] = field(default_factory=dict)

    @property
    def dimensionality(self) -> int:
        """Number of dimensions."""
        return len(self.coordinates)

    @classmethod
    def from_profile_values(
        cls,
        genre_name: str,
        *,
        swing_ratio: float = 0.5,
        syncopation_density: float = 0.3,
        chord_complexity: float = 0.3,
        chord_extension_avg: float = 0.2,
        rhythmic_subdivision: float = 0.5,
        dynamic_range: float = 0.5,
        timbral_brightness: float = 0.5,
        instrumental_density: float = 0.5,
        melodic_chromaticism: float = 0.2,
        phrase_length_avg: float = 0.5,
        tempo_typical: float = 0.5,
        structural_repetition: float = 0.5,
    ) -> GenreVector:
        """Create a GenreVector from named profile values."""
        return cls(
            coordinates=(
                swing_ratio,
                syncopation_density,
                chord_complexity,
                chord_extension_avg,
                rhythmic_subdivision,
                dynamic_range,
                timbral_brightness,
                instrumental_density,
                melodic_chromaticism,
                phrase_length_avg,
                tempo_typical,
                structural_repetition,
            ),
            component_genres={genre_name: 1.0},
        )

    @classmethod
    def blend(cls, *weighted: tuple[GenreVector, float]) -> GenreVector:
        """Blend multiple genre vectors with weights.

        Args:
            *weighted: Tuples of (GenreVector, weight). Weights are
                normalized to sum to 1.0.

        Returns:
            A new blended GenreVector.
        """
        if not weighted:
            return cls(coordinates=tuple(0.5 for _ in GENRE_DIMENSIONS), component_genres={})

        total_weight = sum(w for _, w in weighted)
        if total_weight <= 0:
            total_weight = 1.0

        dim = weighted[0][0].dimensionality
        blended = [0.0] * dim
        components: dict[str, float] = {}

        for vec, weight in weighted:
            normalized_w = weight / total_weight
            for i in range(min(dim, vec.dimensionality)):
                blended[i] += vec.coordinates[i] * normalized_w
            for genre, gw in vec.component_genres.items():
                components[genre] = components.get(genre, 0.0) + gw * normalized_w

        return cls(coordinates=tuple(blended), component_genres=components)

    def distance_to(self, other: GenreVector) -> float:
        """Euclidean distance to another genre vector."""
        dim = min(self.dimensionality, other.dimensionality)
        squared_sum = 0.0
        for i in range(dim):
            squared_sum += (self.coordinates[i] - other.coordinates[i]) ** 2
        return float(squared_sum**0.5)

    def nearest_neighbors(
        self,
        registry: list[GenreVector],
        k: int = 3,
    ) -> list[tuple[GenreVector, float]]:
        """Find k nearest neighbors in a registry.

        Args:
            registry: List of GenreVectors to search.
            k: Number of neighbors.

        Returns:
            List of (vector, distance) tuples, sorted by distance.
        """
        distances = [(vec, self.distance_to(vec)) for vec in registry]
        distances.sort(key=lambda x: x[1])
        return distances[:k]
