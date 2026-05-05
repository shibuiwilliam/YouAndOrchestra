"""Tests for Reference Matcher — extraction, matching, and copyright safety.

Also tests the 7 symbolic feature extractors from the feature_extractors module.
"""

from __future__ import annotations

import numpy as np
import pytest

from yao.errors import ForbiddenExtractionError, MissingRightsStatusError
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.perception.feature_extractors import (
    extract_all,
    extract_concatenated,
    get_extractor,
    list_extractors,
)
from yao.perception.feature_extractors.symbolic import (
    ChordComplexity,
    GroovePocket,
    MotivicDensity,
    RegisterDistribution,
    SurpriseIndex,
    TemporalCentroid,
    VoiceLeadingSmoothness,
)
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


# ────────────────────────────────────────────────────────────────────────────
# Feature Extractor Tests
# ────────────────────────────────────────────────────────────────────────────


def _make_different_score() -> ScoreIR:
    """Create a score that differs meaningfully from _make_score()."""
    notes = tuple(
        Note(
            pitch=40 + (i * 5) % 24,  # wider jumps, lower register
            start_beat=float(i) * 0.5,
            duration_beats=0.5,
            velocity=40 + i * 5,
            instrument="bass",
        )
        for i in range(32)
    )
    return ScoreIR(
        title="Different Score",
        tempo_bpm=90.0,
        time_signature="4/4",
        key="A minor",
        sections=(Section(name="verse", start_bar=0, end_bar=4, parts=(Part(instrument="bass", notes=notes),)),),
    )


class TestFeatureExtractorRegistry:
    """Tests for the feature extractor registry."""

    def test_all_seven_extractors_registered(self) -> None:
        names = list_extractors()
        expected = [
            "chord_complexity",
            "groove_pocket",
            "motivic_density",
            "register_distribution",
            "surprise_index",
            "temporal_centroid",
            "voice_leading_smoothness",
        ]
        assert names == expected

    def test_get_extractor_by_name(self) -> None:
        ext = get_extractor("surprise_index")
        assert ext.name == "surprise_index"
        assert ext.feature_dim == 1

    def test_get_unknown_extractor_raises(self) -> None:
        with pytest.raises(KeyError, match="nonexistent"):
            get_extractor("nonexistent")


class TestFeatureExtraction:
    """Tests that feature extraction from ScoreIR produces valid vectors."""

    def test_extract_produces_vector(self) -> None:
        score = _make_score()
        features = extract_all(score)
        assert len(features) == 7
        for _name, vec in features.items():
            assert isinstance(vec, np.ndarray)
            assert vec.dtype == np.float64

    def test_extract_concatenated_correct_dim(self) -> None:
        score = _make_score()
        vec = extract_concatenated(score)
        # Total dim: 1+1+1+12+1+3+1 = 20
        assert vec.shape == (20,)

    def test_identical_scores_zero_distance(self) -> None:
        score = _make_score()
        v1 = extract_concatenated(score)
        v2 = extract_concatenated(score)
        distance = float(np.linalg.norm(v1 - v2))
        assert distance == 0.0

    def test_different_scores_positive_distance(self) -> None:
        v1 = extract_concatenated(_make_score())
        v2 = extract_concatenated(_make_different_score())
        distance = float(np.linalg.norm(v1 - v2))
        assert distance > 0.0

    def test_positive_reference_proximity_scored(self) -> None:
        """Closer scores have smaller feature distance."""
        base = _make_score(0)
        close = _make_score(1)  # 1 semitone offset — similar
        far = _make_score(24)  # 2 octaves — very different

        v_base = extract_concatenated(base)
        v_close = extract_concatenated(close)
        v_far = extract_concatenated(far)

        dist_close = float(np.linalg.norm(v_base - v_close))
        dist_far = float(np.linalg.norm(v_base - v_far))
        assert dist_close < dist_far


class TestAllExtractorsNonNaN:
    """Verify all 7 extractors produce non-NaN results for various inputs."""

    @pytest.mark.parametrize("pitch_offset", [0, 12, -12, 24])
    def test_all_extractors_non_nan(self, pitch_offset: int) -> None:
        score = _make_score(pitch_offset)
        features = extract_all(score)
        for name, vec in features.items():
            assert not np.any(np.isnan(vec)), f"Extractor '{name}' produced NaN"

    def test_all_extractors_non_nan_empty_score(self) -> None:
        """Empty score should not produce NaN."""
        score = ScoreIR(
            title="Empty",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(Section(name="intro", start_bar=0, end_bar=4, parts=()),),
        )
        features = extract_all(score)
        for name, vec in features.items():
            assert not np.any(np.isnan(vec)), f"Extractor '{name}' produced NaN for empty score"

    def test_all_extractors_non_nan_single_note(self) -> None:
        """Single-note score should not produce NaN."""
        notes = (Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),)
        score = ScoreIR(
            title="Single",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(Section(name="intro", start_bar=0, end_bar=1, parts=(Part(instrument="piano", notes=notes),)),),
        )
        features = extract_all(score)
        for name, vec in features.items():
            assert not np.any(np.isnan(vec)), f"Extractor '{name}' produced NaN for single note"


class TestIndividualExtractors:
    """Test individual extractor behavior."""

    def test_voice_leading_smoothness_stepwise(self) -> None:
        """Stepwise motion should have low smoothness value."""
        notes = tuple(
            Note(pitch=60 + i, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="piano")
            for i in range(8)
        )
        score = ScoreIR(
            title="Stepwise",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(Section(name="a", start_bar=0, end_bar=2, parts=(Part(instrument="piano", notes=notes),)),),
        )
        ext = VoiceLeadingSmoothness()
        result = ext.extract(score)
        # Stepwise = 1 semitone per step
        assert result[0] <= 2.0  # Should be close to 1.0

    def test_register_distribution_sums_to_one(self) -> None:
        ext = RegisterDistribution()
        result = ext.extract(_make_score())
        assert abs(result.sum() - 1.0) < 1e-9

    def test_temporal_centroid_in_range(self) -> None:
        ext = TemporalCentroid()
        result = ext.extract(_make_score())
        assert 0.0 <= result[0] <= 1.0

    def test_surprise_index_in_range(self) -> None:
        ext = SurpriseIndex()
        result = ext.extract(_make_score())
        assert 0.0 <= result[0] <= 1.0

    def test_chord_complexity_positive(self) -> None:
        ext = ChordComplexity()
        result = ext.extract(_make_score())
        assert result[0] >= 0.0

    def test_groove_pocket_dimension(self) -> None:
        ext = GroovePocket()
        result = ext.extract(_make_score())
        assert result.shape == (3,)

    def test_motivic_density_with_repetition(self) -> None:
        """A score with repeated patterns should have higher motivic density."""
        # Create a highly repetitive pattern
        pattern = [60, 62, 64]  # C D E repeated
        notes = tuple(
            Note(
                pitch=pattern[i % 3],
                start_beat=float(i),
                duration_beats=1.0,
                velocity=80,
                instrument="piano",
            )
            for i in range(24)
        )
        score = ScoreIR(
            title="Repetitive",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(Section(name="a", start_bar=0, end_bar=6, parts=(Part(instrument="piano", notes=notes),)),),
        )
        ext = MotivicDensity()
        result = ext.extract(score)
        assert result[0] > 0.0  # Should detect recurring patterns
