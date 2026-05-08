"""Tests for Genre Conformance evaluator."""

from __future__ import annotations

import pytest

from yao.genre.profile import GenreProfile, InstrumentRoleSpec
from yao.genre.registry import GenreRegistry
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.verify.genre_conformance import GenreConformanceScore, evaluate_genre_conformance


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    """Reset the registry before each test."""
    GenreRegistry._cache.clear()
    GenreRegistry._loaded = False


def _make_score(
    instruments: list[str],
    notes_per_part: int = 16,
    bars: int = 4,
) -> ScoreIR:
    """Create a minimal ScoreIR for testing."""
    parts = []
    for inst in instruments:
        notes = tuple(
            Note(
                pitch=60 + (i % 12),
                start_beat=float(i),
                duration_beats=1.0,
                velocity=80,
                instrument=inst,
            )
            for i in range(notes_per_part)
        )
        parts.append(Part(instrument=inst, notes=notes))
    sections = [Section(name="A", start_bar=0, end_bar=bars, parts=tuple(parts))]
    return ScoreIR(
        title="test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=tuple(sections),
    )


class TestGenreConformanceScore:
    """Test the conformance scoring system."""

    def test_perfect_instrumentation_match(self) -> None:
        """Score should be high when all core instruments are present."""
        profile = GenreProfile(
            name="test_genre",
            core_instruments=[
                InstrumentRoleSpec(name="piano"),
                InstrumentRoleSpec(name="bass"),
            ],
            forbidden_instruments=["sitar"],
        )
        score_ir = _make_score(["piano", "bass", "drums"])
        result = evaluate_genre_conformance(score_ir, "test_genre", tempo_bpm=120.0, profile=profile)
        assert result.instrumentation_match == 1.0

    def test_missing_core_instrument_lowers_score(self) -> None:
        """Score should drop when core instruments are missing."""
        profile = GenreProfile(
            name="test_genre",
            core_instruments=[
                InstrumentRoleSpec(name="piano"),
                InstrumentRoleSpec(name="bass"),
                InstrumentRoleSpec(name="drums"),
            ],
        )
        score_ir = _make_score(["piano"])  # Missing bass and drums
        result = evaluate_genre_conformance(score_ir, "test_genre", tempo_bpm=120.0, profile=profile)
        assert result.instrumentation_match < 0.5

    def test_forbidden_instrument_lowers_score(self) -> None:
        """Score should drop when forbidden instruments are present."""
        profile = GenreProfile(
            name="test_genre",
            forbidden_instruments=["sitar", "bagpipes"],
        )
        score_ir = _make_score(["piano", "sitar"])  # sitar is forbidden
        result = evaluate_genre_conformance(score_ir, "test_genre", tempo_bpm=120.0, profile=profile)
        assert result.instrumentation_match < 1.0

    def test_tempo_within_range(self) -> None:
        """Tempo within range should score 1.0."""
        profile = GenreProfile(
            name="test_genre",
            typical_tempo_range=(100.0, 140.0),
        )
        score_ir = _make_score(["piano"])
        result = evaluate_genre_conformance(score_ir, "test_genre", tempo_bpm=120.0, profile=profile)
        assert result.tempo_match == 1.0

    def test_tempo_outside_range(self) -> None:
        """Tempo outside range should score less than 1.0."""
        profile = GenreProfile(
            name="test_genre",
            typical_tempo_range=(180.0, 300.0),
        )
        score_ir = _make_score(["piano"])
        result = evaluate_genre_conformance(score_ir, "test_genre", tempo_bpm=90.0, profile=profile)
        assert result.tempo_match < 0.5

    def test_overall_score_is_weighted_average(self) -> None:
        """Overall score should be between 0.0 and 1.0."""
        profile = GenreProfile(
            name="test_genre",
            typical_tempo_range=(100.0, 140.0),
        )
        score_ir = _make_score(["piano"])
        result = evaluate_genre_conformance(score_ir, "test_genre", tempo_bpm=120.0, profile=profile)
        assert 0.0 <= result.overall <= 1.0

    def test_unknown_genre_returns_default_scores(self) -> None:
        """Unknown genre should return 0.5 defaults."""
        score_ir = _make_score(["piano"])
        result = evaluate_genre_conformance(score_ir, "nonexistent_xyz")
        assert result.overall == 0.5
        assert "not in registry" in result.details.get("note", "")

    def test_genre_conformance_with_registry(self) -> None:
        """Conformance should work with profiles loaded from registry."""
        score_ir = _make_score(["piano", "upright_bass", "drums_jazz_kit"])
        result = evaluate_genre_conformance(score_ir, "jazz", tempo_bpm=160.0)
        assert isinstance(result, GenreConformanceScore)
        assert result.genre == "jazz"
        assert result.tempo_match == 1.0  # 160 is within jazz range [60, 240]

    def test_details_dict_populated(self) -> None:
        """Details dict should have entries for each dimension."""
        profile = GenreProfile(name="test")
        score_ir = _make_score(["piano"])
        result = evaluate_genre_conformance(score_ir, "test", tempo_bpm=120.0, profile=profile)
        assert "instrumentation" in result.details
        assert "tempo" in result.details
        assert "rhythm" in result.details
        assert "harmony" in result.details
        assert "form" in result.details
