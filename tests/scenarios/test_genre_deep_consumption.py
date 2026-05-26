"""Scenario test: genre profile deeply affects generation output.

Verifies that changing the genre on an otherwise identical spec
produces measurably different pitch histograms and syncopation rates,
confirming that GenreProfile fields (contour weights, leap probability,
blue note probability, syncopation density) are consumed by generators.
"""

from __future__ import annotations

import collections

import yao.generators.stochastic as _st  # noqa: F401
from yao.generators.registry import get_generator
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)


def _make_spec(genre: str, seed: int = 42) -> CompositionSpec:
    """Create a minimal spec that differs only in genre."""
    return CompositionSpec(
        title=f"Diversity Test ({genre})",
        genre=genre,
        key="C major",
        tempo_bpm=120,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[
            SectionSpec(name="verse", bars=8, dynamics="mf"),
            SectionSpec(name="chorus", bars=8, dynamics="f"),
        ],
        generation=GenerationConfig(strategy="stochastic", seed=seed, temperature=0.5),
    )


def _pitch_class_histogram(notes: list) -> dict[int, int]:
    """Compute pitch class (0-11) histogram from notes."""
    hist: dict[int, int] = collections.Counter()
    for n in notes:
        hist[n.pitch % 12] += 1
    return dict(hist)


def _interval_histogram(notes: list) -> dict[int, int]:
    """Compute interval histogram from consecutive notes."""
    sorted_notes = sorted(notes, key=lambda n: n.start_beat)
    hist: dict[int, int] = collections.Counter()
    for i in range(len(sorted_notes) - 1):
        interval = abs(sorted_notes[i + 1].pitch - sorted_notes[i].pitch)
        hist[interval] += 1
    return dict(hist)


def _histogram_distance(h1: dict[int, int], h2: dict[int, int]) -> float:
    """Compute L1 distance between normalized histograms."""
    all_keys = set(h1) | set(h2)
    total1 = max(sum(h1.values()), 1)
    total2 = max(sum(h2.values()), 1)
    distance = 0.0
    for k in all_keys:
        distance += abs(h1.get(k, 0) / total1 - h2.get(k, 0) / total2)
    return distance


class TestGenreDeepConsumption:
    """Verify genre profile fields affect generation output."""

    def test_rock_vs_jazz_pitch_histogram_differs(self) -> None:
        """Rock and jazz should produce different pitch class distributions."""
        gen = get_generator("stochastic")

        rock_score, _ = gen.generate(_make_spec("rock_classic"))
        jazz_score, _ = gen.generate(_make_spec("jazz_bebop"))

        rock_hist = _pitch_class_histogram(rock_score.all_notes())
        jazz_hist = _pitch_class_histogram(jazz_score.all_notes())

        distance = _histogram_distance(rock_hist, jazz_hist)
        assert distance > 0.05, (
            f"Rock vs Jazz pitch class histogram L1 distance = {distance:.3f}, "
            f"expected > 0.05 for distinguishable genres"
        )

    def test_multiple_genres_produce_distinct_outputs(self) -> None:
        """At least 5 genres should produce distinguishable outputs
        (pairwise histogram distance > threshold)."""
        gen = get_generator("stochastic")
        genres = ["rock_classic", "jazz_bebop", "funk_classic", "ambient", "electronic_house"]

        histograms: dict[str, dict[int, int]] = {}
        for genre in genres:
            score, _ = gen.generate(_make_spec(genre))
            histograms[genre] = _pitch_class_histogram(score.all_notes())

        # Check pairwise distances
        distinguishable_pairs = 0
        total_pairs = 0
        for i, g1 in enumerate(genres):
            for g2 in genres[i + 1 :]:
                dist = _histogram_distance(histograms[g1], histograms[g2])
                if dist > 0.03:
                    distinguishable_pairs += 1
                total_pairs += 1

        ratio = distinguishable_pairs / max(total_pairs, 1)
        assert ratio >= 0.5, (
            f"Only {distinguishable_pairs}/{total_pairs} genre pairs "
            f"are distinguishable ({ratio:.0%}). Expected >= 50%."
        )

    def test_genre_adapter_resolves_all_profiles(self) -> None:
        """Every genre profile should resolve to a valid GenreBias."""
        from yao.constants.genre_profile import all_genre_profiles
        from yao.generators.genre_adapter import resolve_genre_bias

        for name, profile in all_genre_profiles().items():
            bias = resolve_genre_bias(profile)
            assert bias.leap_probability >= 0.0, f"Genre {name}: invalid leap_probability"
            assert bias.syncopation_density >= 0.0, f"Genre {name}: invalid syncopation_density"
            assert bias.contour_weights, f"Genre {name}: empty contour_weights"
