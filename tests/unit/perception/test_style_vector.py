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


class TestAllowlistConstants:
    def test_melody_contour_not_in_allowed(self) -> None:
        assert "melody_contour" not in ALLOWED_FEATURES

    def test_chord_progression_not_in_allowed(self) -> None:
        assert "chord_progression" not in ALLOWED_FEATURES

    def test_melody_contour_in_forbidden(self) -> None:
        assert "melody_contour" in FORBIDDEN_FEATURES

    def test_chord_progression_in_forbidden(self) -> None:
        assert "chord_progression" in FORBIDDEN_FEATURES
