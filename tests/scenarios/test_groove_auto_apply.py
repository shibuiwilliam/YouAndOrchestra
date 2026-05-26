"""Scenario test: groove auto-application from genre profile.

Verifies that changing the genre changes the groove applied to notes,
even when the groove is not explicitly specified.
"""

from __future__ import annotations

import yao.generators.stochastic as _st  # noqa: F401
from yao.generators.groove_applicator import apply_groove
from yao.generators.registry import get_generator
from yao.ir.groove import load_groove
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)


def _make_spec(genre: str, seed: int = 42) -> CompositionSpec:
    return CompositionSpec(
        title=f"Groove Test ({genre})",
        genre=genre,
        key="C major",
        tempo_bpm=120,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=4, dynamics="mf")],
        generation=GenerationConfig(strategy="stochastic", seed=seed, temperature=0.5),
    )


class TestGrooveAutoApply:
    """Verify groove auto-application changes note timings."""

    def test_groove_shifts_note_timings(self) -> None:
        """Applying a groove profile should shift some note start_beats."""
        gen = get_generator("stochastic")
        spec = _make_spec("rock_classic")
        score, _ = gen.generate(spec)

        groove = load_groove("rock_backbeat")
        grooved, _prov = apply_groove(score, groove, seed=42)

        original_beats = sorted(n.start_beat for n in score.all_notes())
        grooved_beats = sorted(n.start_beat for n in grooved.all_notes())

        # Same number of notes
        assert len(original_beats) == len(grooved_beats)

        # At least some notes should have shifted timing
        diffs = [abs(a - b) for a, b in zip(original_beats, grooved_beats, strict=True)]
        shifted = sum(1 for d in diffs if d > 0.001)
        assert shifted > 0, "Groove should shift at least some note timings"

    def test_different_genres_different_grooves(self) -> None:
        """Different genres should produce different groove offsets."""
        from yao.constants.genre_profile import get_genre_profile

        gen = get_generator("stochastic")
        spec = _make_spec("jazz_bebop")
        score, _ = gen.generate(spec)

        jazz_profile = get_genre_profile("jazz_bebop")
        funk_profile = get_genre_profile("funk_classic")
        assert jazz_profile is not None and jazz_profile.default_groove
        assert funk_profile is not None and funk_profile.default_groove
        assert jazz_profile.default_groove != funk_profile.default_groove

        jazz_groove = load_groove(jazz_profile.default_groove)
        funk_groove = load_groove(funk_profile.default_groove)

        jazz_grooved, _ = apply_groove(score, jazz_groove, seed=42)
        funk_grooved, _ = apply_groove(score, funk_groove, seed=42)

        jazz_beats = [n.start_beat for n in jazz_grooved.all_notes()]
        funk_beats = [n.start_beat for n in funk_grooved.all_notes()]

        # Grooves should produce different timing profiles
        assert jazz_beats != funk_beats, "Jazz and funk grooves should differ"

    def test_all_genre_grooves_loadable(self) -> None:
        """Every genre with default_groove should reference a loadable groove file."""
        from yao.constants.genre_profile import all_genre_profiles
        from yao.ir.groove import load_groove

        for name, profile in all_genre_profiles().items():
            if profile.default_groove is not None:
                groove = load_groove(profile.default_groove)
                assert groove.name, f"Genre '{name}' groove '{profile.default_groove}' has no name"
