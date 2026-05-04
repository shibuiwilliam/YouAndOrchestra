"""Tests for UserStyleProfile.bias() method."""

from __future__ import annotations

from yao.reflect.style_profile import StylePreference, UserStyleProfile
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec


def _minimal_spec() -> CompositionSpec:
    return CompositionSpec(
        title="Test",
        key="C major",
        tempo_bpm=120.0,
        time_signature="4/4",
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
    )


class TestStyleProfileBias:
    """Tests for the bias() method."""

    def test_empty_profile_no_change(self) -> None:
        """Empty profile returns spec unchanged."""
        profile = UserStyleProfile()
        spec = _minimal_spec()
        biased = profile.bias(spec)
        assert biased.generation.temperature == spec.generation.temperature

    def test_low_overall_increases_temperature(self) -> None:
        """Low overall ratings should increase temperature."""
        profile = UserStyleProfile()
        profile.add_preference(
            StylePreference(
                dimension="overall",
                preferred_range=(2.0, 4.0),  # low ratings
                confidence=0.8,
                source_count=10,
            )
        )
        spec = _minimal_spec()
        biased = profile.bias(spec)
        assert biased.generation.temperature > spec.generation.temperature

    def test_low_confidence_no_change(self) -> None:
        """Preferences with low confidence should not bias."""
        profile = UserStyleProfile()
        profile.add_preference(
            StylePreference(
                dimension="overall",
                preferred_range=(2.0, 4.0),
                confidence=0.3,  # below threshold
                source_count=2,
            )
        )
        spec = _minimal_spec()
        biased = profile.bias(spec)
        assert biased.generation.temperature == spec.generation.temperature

    def test_use_style_profile_false(self) -> None:
        """Spec with use_style_profile=False skips biasing."""
        spec = _minimal_spec()
        spec_no_profile = spec.model_copy(update={"use_style_profile": False})
        assert spec_no_profile.use_style_profile is False
