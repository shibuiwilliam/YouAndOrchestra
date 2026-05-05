"""Tests for StyleVector — structural integrity and copyright safety."""

from __future__ import annotations

import dataclasses

import pytest

from yao.perception.style_vector import StyleVector
from yao.schema.references import ALLOWED_FEATURES, FORBIDDEN_FEATURES


def _make_vector(**overrides: object) -> StyleVector:
    defaults = {
        "harmonic_rhythm": 2.0,
        "voice_leading_smoothness": 3.5,
        "rhythmic_density_per_bar": (4.0, 3.0, 5.0, 4.0),
        "register_distribution": tuple([0.0] * 4 + [0.3, 0.4, 0.2, 0.1] + [0.0] * 4),
        "timbre_centroid_curve": (2000.0, 2500.0),
        "motif_density": 1.5,
    }
    defaults.update(overrides)
    return StyleVector(**defaults)  # type: ignore[arg-type]


class TestStyleVectorStructure:
    def test_is_frozen(self) -> None:
        v = _make_vector()
        with pytest.raises(AttributeError):
            v.harmonic_rhythm = 5.0  # type: ignore[misc]

    def test_no_forbidden_fields(self) -> None:
        """StyleVector must NEVER contain copyrightable feature fields."""
        field_names = {f.name for f in dataclasses.fields(StyleVector)}
        for forbidden in FORBIDDEN_FEATURES:
            assert forbidden not in field_names, f"StyleVector contains forbidden field '{forbidden}'"

    def test_all_allowed_features_represented(self) -> None:
        """Each allowed feature should correspond to a StyleVector field."""
        field_names = {f.name for f in dataclasses.fields(StyleVector)}
        for allowed in ALLOWED_FEATURES:
            assert allowed in field_names, f"Allowed feature '{allowed}' missing from StyleVector"


class TestStyleVectorDistance:
    def test_distance_to_self_is_zero(self) -> None:
        v = _make_vector()
        assert v.distance_to(v) == 0.0

    def test_distance_to_different_positive(self) -> None:
        v1 = _make_vector(harmonic_rhythm=1.0)
        v2 = _make_vector(harmonic_rhythm=5.0)
        assert v1.distance_to(v2) > 0

    def test_distance_symmetric(self) -> None:
        v1 = _make_vector(motif_density=1.0)
        v2 = _make_vector(motif_density=5.0)
        assert abs(v1.distance_to(v2) - v2.distance_to(v1)) < 1e-10


class TestStyleVectorArithmetic:
    """Tests for C2 StyleVector arithmetic operators (+, -, *, cosine_similarity)."""

    def test_add_scalars(self) -> None:
        v1 = _make_vector(harmonic_rhythm=2.0, motif_density=1.0)
        v2 = _make_vector(harmonic_rhythm=3.0, motif_density=2.0)
        result = v1 + v2
        assert result.harmonic_rhythm == pytest.approx(5.0)
        assert result.motif_density == pytest.approx(3.0)

    def test_add_tuples(self) -> None:
        v1 = _make_vector(register_distribution=(0.1, 0.2) + (0.0,) * 10)
        v2 = _make_vector(register_distribution=(0.3, 0.1) + (0.0,) * 10)
        result = v1 + v2
        assert result.register_distribution[0] == pytest.approx(0.4)
        assert result.register_distribution[1] == pytest.approx(0.3)

    def test_sub(self) -> None:
        v1 = _make_vector(harmonic_rhythm=5.0)
        v2 = _make_vector(harmonic_rhythm=3.0)
        result = v1 - v2
        assert result.harmonic_rhythm == pytest.approx(2.0)

    def test_mul_scalar(self) -> None:
        v = _make_vector(harmonic_rhythm=2.0, motif_density=3.0)
        result = v * 2.0
        assert result.harmonic_rhythm == pytest.approx(4.0)
        assert result.motif_density == pytest.approx(6.0)

    def test_rmul_scalar(self) -> None:
        v = _make_vector(harmonic_rhythm=2.0)
        result = 3.0 * v
        assert result.harmonic_rhythm == pytest.approx(6.0)

    def test_sub_self_is_zero(self) -> None:
        v = _make_vector()
        result = v - v
        assert result.harmonic_rhythm == pytest.approx(0.0)
        assert result.motif_density == pytest.approx(0.0)

    def test_vector_algebra_arrangement(self) -> None:
        """Test arrangement_vector = source - genre_a + genre_b."""
        source = _make_vector(harmonic_rhythm=2.0, motif_density=1.0)
        genre_a = _make_vector(harmonic_rhythm=1.0, motif_density=0.5)
        genre_b = _make_vector(harmonic_rhythm=4.0, motif_density=3.0)
        result = source - genre_a + genre_b
        assert result.harmonic_rhythm == pytest.approx(5.0)
        assert result.motif_density == pytest.approx(3.5)

    def test_mul_zero(self) -> None:
        v = _make_vector(harmonic_rhythm=5.0)
        result = v * 0.0
        assert result.harmonic_rhythm == pytest.approx(0.0)

    def test_add_different_tuple_lengths(self) -> None:
        """Adding vectors with different rhythmic_density_per_bar lengths zero-pads shorter."""
        v1 = _make_vector(rhythmic_density_per_bar=(1.0, 2.0))
        v2 = _make_vector(rhythmic_density_per_bar=(3.0, 4.0, 5.0))
        result = v1 + v2
        assert len(result.rhythmic_density_per_bar) == 3
        assert result.rhythmic_density_per_bar[2] == pytest.approx(5.0)


class TestStyleVectorCosineSimilarity:
    """Tests for C2 cosine_similarity."""

    def test_identical_is_one(self) -> None:
        v = _make_vector()
        assert v.cosine_similarity(v) == pytest.approx(1.0)

    def test_scaled_is_one(self) -> None:
        """Vectors that differ only by magnitude should have cosine_similarity ~1.0."""
        v1 = _make_vector(harmonic_rhythm=2.0, motif_density=1.5)
        v2 = v1 * 3.0
        assert v1.cosine_similarity(v2) == pytest.approx(1.0, abs=1e-6)

    def test_different_vectors_less_than_one(self) -> None:
        v1 = _make_vector(harmonic_rhythm=1.0, voice_leading_smoothness=0.0)
        v2 = _make_vector(harmonic_rhythm=0.0, voice_leading_smoothness=5.0)
        sim = v1.cosine_similarity(v2)
        assert sim < 1.0

    def test_symmetric(self) -> None:
        v1 = _make_vector(harmonic_rhythm=1.0)
        v2 = _make_vector(harmonic_rhythm=5.0)
        assert abs(v1.cosine_similarity(v2) - v2.cosine_similarity(v1)) < 1e-10

    def test_zero_vector_returns_zero(self) -> None:
        zero = StyleVector(
            harmonic_rhythm=0.0,
            voice_leading_smoothness=0.0,
            rhythmic_density_per_bar=(),
            register_distribution=(0.0,) * 12,
            timbre_centroid_curve=(),
            motif_density=0.0,
        )
        v = _make_vector()
        assert zero.cosine_similarity(v) == pytest.approx(0.0)


class TestAllowlistConstants:
    def test_melody_contour_not_in_allowed(self) -> None:
        assert "melody_contour" not in ALLOWED_FEATURES

    def test_chord_progression_not_in_allowed(self) -> None:
        assert "chord_progression" not in ALLOWED_FEATURES

    def test_melody_contour_in_forbidden(self) -> None:
        assert "melody_contour" in FORBIDDEN_FEATURES

    def test_chord_progression_in_forbidden(self) -> None:
        assert "chord_progression" in FORBIDDEN_FEATURES
