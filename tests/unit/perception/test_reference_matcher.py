"""Tests for Reference Matcher — extraction, matching, and copyright safety."""

from __future__ import annotations

import pytest

from yao.errors import ForbiddenExtractionError, MissingRightsStatusError
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.perception.reference_matcher import ReferenceMatcher, ReferenceMatchReport
from yao.perception.style_vector import StyleVector
from yao.schema.references import PrimaryReference, ReferencesSpec


def _make_score(pitch_offset: int = 0) -> ScoreIR:
    notes = tuple(
        Note(
            pitch=60 + pitch_offset + (i % 7),
            start_beat=float(i),
            duration_beats=1.0,
            velocity=80,
            instrument="piano",
        )
        for i in range(16)
    )
    return ScoreIR(
        title="Reference Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="verse", start_bar=0, end_bar=4, parts=(Part(instrument="piano", notes=notes),)),),
    )


class TestExtraction:
    def test_extract_produces_valid_vector(self) -> None:
        matcher = ReferenceMatcher()
        vector = matcher.extract_style_vector(_make_score())
        assert isinstance(vector, StyleVector)
        assert vector.harmonic_rhythm >= 0
        assert len(vector.register_distribution) == 12

    def test_forbidden_feature_raises(self) -> None:
        matcher = ReferenceMatcher()
        with pytest.raises(ForbiddenExtractionError, match="melody_contour"):
            matcher.extract_style_vector(_make_score(), requested_features=["melody_contour"])

    def test_allowed_feature_passes(self) -> None:
        matcher = ReferenceMatcher()
        vector = matcher.extract_style_vector(_make_score(), requested_features=["harmonic_rhythm"])
        assert vector.harmonic_rhythm >= 0


class TestSchemaValidation:
    def test_rights_unknown_raises(self) -> None:
        with pytest.raises(MissingRightsStatusError):
            PrimaryReference(
                file="test.mid",
                role="test",
                rights_status="unknown",
                extract_features=[],
            )

    def test_rights_valid_passes(self) -> None:
        ref = PrimaryReference(
            file="test.mid",
            role="test",
            rights_status="public_domain",
            extract_features=["harmonic_rhythm"],
        )
        assert ref.rights_status == "public_domain"

    def test_forbidden_feature_in_extract_raises(self) -> None:
        from yao.errors import SpecValidationError

        with pytest.raises(SpecValidationError, match="FORBIDDEN"):
            PrimaryReference(
                file="test.mid",
                role="test",
                rights_status="public_domain",
                extract_features=["melody_contour"],
            )


class TestDistance:
    def test_same_score_zero_distance(self) -> None:
        matcher = ReferenceMatcher()
        score = _make_score()
        v1 = matcher.extract_style_vector(score)
        v2 = matcher.extract_style_vector(score)
        assert v1.distance_to(v2) == 0.0

    def test_different_scores_positive_distance(self) -> None:
        matcher = ReferenceMatcher()
        v1 = matcher.extract_style_vector(_make_score(0))
        v2 = matcher.extract_style_vector(_make_score(12))
        assert v1.distance_to(v2) > 0


class TestReferenceMatchReport:
    def test_scores_in_range(self) -> None:
        matcher = ReferenceMatcher()
        refs = ReferencesSpec(
            primary=[
                PrimaryReference(
                    file="ref.mid",
                    role="voice leading",
                    weight=0.6,
                    rights_status="public_domain",
                    extract_features=["harmonic_rhythm"],
                )
            ],
        )
        report = matcher.evaluate_against_references(_make_score(), refs)
        assert isinstance(report, ReferenceMatchReport)
        assert 0.0 <= report.positive_proximity_score <= 1.0
        assert 0.0 <= report.negative_distance_score <= 1.0


class TestCache:
    def test_cache_key_deterministic(self) -> None:
        matcher = ReferenceMatcher()
        score = _make_score()
        k1 = matcher.cache_key(score)
        k2 = matcher.cache_key(score)
        assert k1 == k2

    def test_cache_round_trip(self, tmp_path: pytest.TempPathFactory) -> None:
        import yao.perception.reference_matcher as rm_mod

        # Temporarily redirect cache dir
        original = rm_mod._CACHE_DIR
        rm_mod._CACHE_DIR = tmp_path  # type: ignore[assignment]
        try:
            matcher = ReferenceMatcher()
            score = _make_score()
            vector = matcher.extract_style_vector(score)
            key = matcher.cache_key(score)

            matcher.save_cached_vector(key, vector)
            loaded = matcher.get_cached_vector(key)
            assert loaded is not None
            assert loaded.harmonic_rhythm == vector.harmonic_rhythm
            assert loaded.distance_to(vector) == 0.0
        finally:
            rm_mod._CACHE_DIR = original
