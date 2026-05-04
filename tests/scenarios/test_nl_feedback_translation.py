"""Scenario test: NL feedback produces structured suggestions.

Tests that natural-language feedback like "the chorus feels weak"
produces structured suggestions including increase_climax_intensity.
"""

from __future__ import annotations

from yao.feedback.nl_translator import NLFeedbackTranslator


class TestNLFeedbackScenarios:
    """Scenario: NL feedback → structured suggestions."""

    def test_chorus_feels_weak(self) -> None:
        """'the chorus feels weak' → increase_climax_intensity + target chorus."""
        translator = NLFeedbackTranslator()
        result = translator.translate("the chorus feels weak")

        assert "increase_climax_intensity" in result.intents
        assert "chorus" in result.target_sections
        assert not result.ambiguous

    def test_piano_too_loud_in_bridge(self) -> None:
        """'piano too loud in the bridge' → decrease_dynamics + piano + bridge."""
        translator = NLFeedbackTranslator()
        result = translator.translate("piano too loud in the bridge")

        assert "decrease_dynamics" in result.intents
        assert "piano" in result.target_instruments
        assert "bridge" in result.target_sections

    def test_mix_sounds_muddy(self) -> None:
        """'the mix sounds muddy' → frequency_clearance."""
        translator = NLFeedbackTranslator()
        result = translator.translate("the mix sounds muddy")

        assert "frequency_clearance" in result.intents
        assert result.parameter_adjustments.get("frequency_clearance") is True

    def test_completely_unrecognized(self) -> None:
        """Unrecognized feedback is marked ambiguous with help text."""
        translator = NLFeedbackTranslator()
        result = translator.translate("the vibes are off")

        assert result.ambiguous
        assert "Try phrases like" in result.ambiguity_reason

    def test_multiple_issues(self) -> None:
        """Multiple recognized phrases produce multiple intents."""
        translator = NLFeedbackTranslator()
        result = translator.translate("the intro is boring and the drums sound stiff")

        assert len(result.intents) >= 2
        assert "intro" in result.target_sections
        assert "drums" in result.target_instruments
