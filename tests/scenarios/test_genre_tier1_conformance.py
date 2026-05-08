"""Tier-1 genre conformance scenario tests.

Validates that the 5 Tier-1 genres (pop, rock, jazz, hip_hop, cinematic)
have properly configured profiles and produce meaningful conformance scores.
"""

from __future__ import annotations

import pytest

from yao.genre.briefing import synthesize_briefing
from yao.genre.registry import GenreRegistry
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.production.profile import load_production_profile
from yao.verify.genre_conformance import evaluate_genre_conformance


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    """Reset the registry before each test."""
    GenreRegistry._cache.clear()
    GenreRegistry._loaded = False


def _make_genre_score(genre: str, instruments: list[str], tempo: float) -> ScoreIR:
    """Create a minimal ScoreIR matching genre expectations."""
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
            for i in range(32)
        )
        parts.append(Part(instrument=inst, notes=notes))
    sections = [Section(name="A", start_bar=0, end_bar=8, parts=tuple(parts))]
    return ScoreIR(
        title=f"test_{genre}",
        tempo_bpm=tempo,
        time_signature="4/4",
        key="C major",
        sections=tuple(sections),
    )


TIER_1_GENRES = ["pop", "rock", "jazz", "hip_hop", "cinematic"]


class TestTier1GenreProfiles:
    """Test that all Tier-1 genres have valid profiles."""

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_genre_in_registry(self, genre: str) -> None:
        """Each Tier-1 genre must be in the registry."""
        profile = GenreRegistry.get(genre)
        assert profile.name == genre

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_genre_has_tempo_range(self, genre: str) -> None:
        """Each Tier-1 genre must have a non-default tempo range."""
        profile = GenreRegistry.get(genre)
        assert profile.typical_tempo_range[0] > 0
        assert profile.typical_tempo_range[1] > profile.typical_tempo_range[0]

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_genre_has_chord_palette(self, genre: str) -> None:
        """Each Tier-1 genre must define a chord palette."""
        profile = GenreRegistry.get(genre)
        assert len(profile.chord_palette_extended) >= 3

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_genre_has_cliches_to_avoid(self, genre: str) -> None:
        """Each Tier-1 genre must list anti-patterns."""
        profile = GenreRegistry.get(genre)
        assert len(profile.cliches_to_avoid) >= 1


class TestTier1GenreConformance:
    """Test genre conformance scoring for Tier-1 genres."""

    def test_jazz_conformance_with_jazz_instruments(self) -> None:
        """Jazz score with jazz instruments should score well."""
        score_ir = _make_genre_score(
            "jazz",
            ["upright_bass", "drums_jazz_kit", "piano_acoustic"],
            tempo=160.0,
        )
        result = evaluate_genre_conformance(score_ir, "jazz", tempo_bpm=160.0)
        assert result.tempo_match == 1.0
        assert result.instrumentation_match >= 0.8

    def test_rock_conformance_with_rock_instruments(self) -> None:
        """Rock score with rock instruments should score well."""
        score_ir = _make_genre_score(
            "rock",
            ["distorted_electric_guitar_rhythm", "electric_bass_pick", "drums_rock_kit"],
            tempo=130.0,
        )
        result = evaluate_genre_conformance(score_ir, "rock", tempo_bpm=130.0)
        assert result.tempo_match == 1.0
        assert result.instrumentation_match >= 0.8

    def test_wrong_genre_instruments_score_lower(self) -> None:
        """Using jazz instruments for rock should score lower on instrumentation."""
        jazz_score = _make_genre_score(
            "jazz_for_rock",
            ["upright_bass", "drums_jazz_kit", "piano_acoustic"],
            tempo=130.0,
        )
        result = evaluate_genre_conformance(jazz_score, "rock", tempo_bpm=130.0)
        assert result.instrumentation_match <= 0.5

    def test_wrong_tempo_scores_lower(self) -> None:
        """Tempo far outside genre range should lower conformance."""
        score_ir = _make_genre_score("hip_hop", ["drums_808", "synth_bass_sub"], tempo=200.0)
        result = evaluate_genre_conformance(score_ir, "hip_hop", tempo_bpm=200.0)
        assert result.tempo_match < 0.5


class TestTier1GenreBriefing:
    """Test briefing synthesis for Tier-1 genres."""

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_briefing_synthesizes(self, genre: str) -> None:
        """Each Tier-1 genre should produce a valid briefing."""
        briefing = synthesize_briefing(genre)
        assert briefing.primary_genre == genre
        assert briefing.id.startswith("briefing_")
        assert briefing.tempo_range[0] < briefing.tempo_range[1]


class TestTier1ProductionProfiles:
    """Test that Tier-1 genres have matching production profiles."""

    def test_pop_has_production_profile(self) -> None:
        """Pop should have a production profile."""
        profile = load_production_profile("modern_pop")
        assert profile is not None

    def test_rock_has_production_profile(self) -> None:
        """Rock should have a production profile."""
        profile = load_production_profile("modern_rock")
        assert profile is not None

    def test_jazz_has_production_profile(self) -> None:
        """Jazz should have a production profile."""
        profile = load_production_profile("jazz_intimate")
        assert profile is not None

    def test_cinematic_has_production_profile(self) -> None:
        """Cinematic should have a production profile."""
        profile = load_production_profile("cinematic")
        assert profile is not None
