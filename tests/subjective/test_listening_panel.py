"""Subjective listening panel tests — human-rated quality assertions.

These tests verify that human ratings meet minimum quality thresholds.
They are SKIPPED in CI by default (requires pytest.mark.subjective).

To run: ``make test-subjective`` or ``pytest tests/subjective/ -m subjective``
"""

from __future__ import annotations

import json

import pytest

from tests.subjective.conftest import (
    RATINGS_DIR,
    REQUIRED_FIELDS,
    available_rating_files,
    load_rating_file,
)

_MINIMUM_OVERALL = 6.0


def _rating_ids() -> list[str]:
    """Get list of rating file stems for parametrize."""
    return [p.stem for p in available_rating_files()]


@pytest.mark.subjective
class TestRatingSchema:
    @pytest.mark.parametrize("rating_stem", _rating_ids())
    def test_rating_fields_complete(self, rating_stem: str) -> None:
        """All required fields must be present in each rating."""
        path = RATINGS_DIR / f"{rating_stem}.json"
        data = json.loads(path.read_text())
        for rating in data["ratings"]:
            for field in REQUIRED_FIELDS:
                assert field in rating, f"Missing field '{field}' in {rating_stem}"

    @pytest.mark.parametrize("rating_stem", _rating_ids())
    def test_rating_schema_valid(self, rating_stem: str) -> None:
        """Rating file must parse without errors."""
        path = RATINGS_DIR / f"{rating_stem}.json"
        rf = load_rating_file(path)
        assert rf.template_name == rating_stem
        assert len(rf.ratings) > 0


@pytest.mark.subjective
class TestQualityThresholds:
    @pytest.mark.parametrize("rating_stem", _rating_ids())
    def test_overall_above_threshold(self, rating_stem: str) -> None:
        """Average overall rating must meet minimum threshold."""
        path = RATINGS_DIR / f"{rating_stem}.json"
        rf = load_rating_file(path)
        avg = rf.average_overall
        assert avg >= _MINIMUM_OVERALL, f"{rating_stem}: average overall {avg:.1f} < {_MINIMUM_OVERALL}"


@pytest.mark.subjective
class TestNoRatingSkips:
    def test_skip_if_no_ratings(self) -> None:
        """This test documents that templates without ratings are skipped."""
        files = available_rating_files()
        if not files:
            pytest.skip("No rating files found")
        assert len(files) > 0
