"""Tests for NL Feedback Translator (Phase δ.2).

Tests cover:
- Known phrases produce correct intents
- Section detection in text
- Instrument detection in text
- Ambiguous input is flagged
- Pin note translation
"""

from __future__ import annotations

from yao.feedback.nl_translator import NLFeedbackTranslator


class TestNLFeedbackTranslator:
    """Tests for NLFeedbackTranslator."""

    def setup_method(self) -> None:
        self.translator = NLFeedbackTranslator()

    def test_weak_produces_increase_intensity(self) -> None:
        result = self.translator.translate("the chorus feels weak")
        assert "increase_climax_intensity" in result.intents
        assert not result.ambiguous

    def test_boring_produces_introduce_surprise(self) -> None:
        result = self.translator.translate("this part is boring")
        assert "introduce_surprise" in result.intents

    def test_muddy_produces_frequency_clearance(self) -> None:
        result = self.translator.translate("the mix sounds muddy")
        assert "frequency_clearance" in result.intents

    def test_harsh_produces_smooth_voice_leading(self) -> None:
        result = self.translator.translate("this sounds harsh")
        assert "smooth_voice_leading" in result.intents

    def test_too_busy_produces_thin_arrangement(self) -> None:
        result = self.translator.translate("too busy here")
        assert "thin_arrangement" in result.intents

    def test_too_sparse_produces_thicken(self) -> None:
        result = self.translator.translate("the bridge is too sparse")
        assert "thicken_arrangement" in result.intents

    def test_stiff_produces_add_groove(self) -> None:
        result = self.translator.translate("drums sound stiff")
        assert "add_groove" in result.intents

    def test_too_loud_produces_decrease_dynamics(self) -> None:
        result = self.translator.translate("piano is too loud")
        assert "decrease_dynamics" in result.intents

    def test_section_detection_chorus(self) -> None:
        result = self.translator.translate("the chorus feels weak")
        assert "chorus" in result.target_sections

    def test_section_detection_intro(self) -> None:
        result = self.translator.translate("the intro is boring")
        assert "intro" in result.target_sections

    def test_section_detection_ending(self) -> None:
        result = self.translator.translate("the ending is abrupt")
        assert "outro" in result.target_sections

    def test_instrument_detection_piano(self) -> None:
        result = self.translator.translate("piano is too loud")
        assert "piano" in result.target_instruments

    def test_instrument_detection_drums(self) -> None:
        result = self.translator.translate("drums sound stiff")
        assert "drums" in result.target_instruments

    def test_ambiguous_input(self) -> None:
        result = self.translator.translate("I don't know what to change")
        assert result.ambiguous
        assert result.ambiguity_reason != ""

    def test_empty_input(self) -> None:
        result = self.translator.translate("")
        assert result.ambiguous

    def test_multiple_intents(self) -> None:
        """Multiple matching phrases produce multiple intents."""
        result = self.translator.translate("the chorus feels weak and boring")
        assert len(result.intents) >= 2

    def test_parameter_adjustments(self) -> None:
        result = self.translator.translate("too loud")
        assert "velocity_reduction" in result.parameter_adjustments

    def test_serialization(self) -> None:
        result = self.translator.translate("the chorus feels weak")
        data = result.to_dict()
        assert data["original_text"] == "the chorus feels weak"
        assert "increase_climax_intensity" in data["intents"]


class TestPinNoteTranslation:
    """Tests for translate_pin_note."""

    def setup_method(self) -> None:
        self.translator = NLFeedbackTranslator()

    def test_dissonant(self) -> None:
        assert self.translator.translate_pin_note("too dissonant") == "soften_dissonance"

    def test_harsh(self) -> None:
        assert self.translator.translate_pin_note("harsh sound") == "soften_dissonance"

    def test_loud(self) -> None:
        assert self.translator.translate_pin_note("too loud") == "too_loud"

    def test_busy(self) -> None:
        assert self.translator.translate_pin_note("too busy here") == "too_busy"

    def test_boring(self) -> None:
        assert self.translator.translate_pin_note("boring passage") == "add_variation"

    def test_unknown(self) -> None:
        assert self.translator.translate_pin_note("something weird") == "unclear"
