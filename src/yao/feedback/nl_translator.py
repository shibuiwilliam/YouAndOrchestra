"""NL Feedback Translator — maps natural language to structured changes.

Converts user feedback phrases into structured musical intents and
parameter adjustments. Uses a maintainable data table (not hardcoded
logic) for phrase → intent mapping.

Belongs to Layer 1.5 (Feedback).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FeedbackMapping:
    """Maps a phrase pattern to a structured intent.

    Attributes:
        phrase: Keyword or phrase to match (case-insensitive).
        intent: The structured intent code.
        parameter_adjustments: Suggested parameter changes.
        preserve: Aspects to keep unchanged.
    """

    phrase: str
    intent: str
    parameter_adjustments: dict[str, Any] = field(default_factory=dict)
    preserve: tuple[str, ...] = ()


@dataclass(frozen=True)
class StructuredFeedback:
    """Structured interpretation of NL feedback.

    Attributes:
        original_text: The raw user input.
        target_sections: Which sections are affected (empty = all).
        target_instruments: Which instruments are affected (empty = all).
        intents: List of parsed intents.
        parameter_adjustments: Aggregated parameter changes.
        preserve: Aspects the user wants to keep.
        ambiguous: True if the feedback could not be confidently parsed.
        ambiguity_reason: Why the feedback is ambiguous.
    """

    original_text: str
    target_sections: list[str] = field(default_factory=list)
    target_instruments: list[str] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)
    parameter_adjustments: dict[str, Any] = field(default_factory=dict)
    preserve: list[str] = field(default_factory=list)
    ambiguous: bool = False
    ambiguity_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize for feedback JSON persistence."""
        return {
            "original_text": self.original_text,
            "target_sections": self.target_sections,
            "target_instruments": self.target_instruments,
            "intents": self.intents,
            "parameter_adjustments": self.parameter_adjustments,
            "preserve": self.preserve,
            "ambiguous": self.ambiguous,
            "ambiguity_reason": self.ambiguity_reason,
        }


# ---------------------------------------------------------------------------
# Mapping table: ~30 phrase → intent mappings
# This is the maintainable data table (not hardcoded logic).
# ---------------------------------------------------------------------------

FEEDBACK_MAPPINGS: tuple[FeedbackMapping, ...] = (
    # Intensity / energy
    FeedbackMapping("weak", "increase_climax_intensity", {"tension_boost": 0.2, "velocity_boost": 10}),
    FeedbackMapping("not strong enough", "increase_climax_intensity", {"tension_boost": 0.15, "velocity_boost": 8}),
    FeedbackMapping("more impact", "increase_climax_intensity", {"tension_boost": 0.2, "velocity_boost": 12}),
    FeedbackMapping("more energy", "increase_climax_intensity", {"tension_boost": 0.15, "velocity_boost": 10}),
    FeedbackMapping("too quiet", "increase_dynamics", {"velocity_boost": 15}),
    FeedbackMapping("too loud", "decrease_dynamics", {"velocity_reduction": 15}),
    FeedbackMapping("too intense", "decrease_climax_intensity", {"tension_reduction": 0.2, "velocity_reduction": 10}),
    FeedbackMapping("overwhelming", "decrease_climax_intensity", {"tension_reduction": 0.25}),
    # Dissonance / harshness
    FeedbackMapping("harsh", "smooth_voice_leading", {"dissonance_reduction": 0.3}),
    FeedbackMapping("dissonant", "soften_dissonance", {"dissonance_reduction": 0.4}),
    FeedbackMapping("too dissonant", "soften_dissonance", {"dissonance_reduction": 0.5}),
    FeedbackMapping("clashing", "soften_dissonance", {"dissonance_reduction": 0.4, "frequency_clearance": True}),
    # Boredom / predictability
    FeedbackMapping("boring", "introduce_surprise", {"surprise_boost": 0.2, "tension_arc_count": 1}),
    FeedbackMapping("predictable", "introduce_surprise", {"surprise_boost": 0.15}),
    FeedbackMapping("monotonous", "vary_dynamics", {"dynamics_contrast": 0.3, "section_differentiation": True}),
    FeedbackMapping("repetitive", "add_variation", {"variation_amount": 0.3}),
    FeedbackMapping("needs variety", "add_variation", {"variation_amount": 0.25}),
    # Texture / density
    FeedbackMapping("muddy", "frequency_clearance", {"frequency_clearance": True, "thin_arrangement": True}),
    FeedbackMapping("too busy", "thin_arrangement", {"density_reduction": 0.3}),
    FeedbackMapping("cluttered", "thin_arrangement", {"density_reduction": 0.25, "frequency_clearance": True}),
    FeedbackMapping("too sparse", "thicken_arrangement", {"density_boost": 0.3}),
    FeedbackMapping("empty", "thicken_arrangement", {"density_boost": 0.25}),
    FeedbackMapping("thin", "thicken_arrangement", {"density_boost": 0.2}),
    # Rhythm
    FeedbackMapping("stiff", "add_groove", {"swing_boost": 0.1, "humanize_boost": 0.15}),
    FeedbackMapping("mechanical", "add_groove", {"swing_boost": 0.1, "humanize_boost": 0.2}),
    FeedbackMapping("no groove", "add_groove", {"swing_boost": 0.15, "humanize_boost": 0.2}),
    # Melody
    FeedbackMapping("melody is flat", "improve_contour", {"contour_variety_boost": 0.3}),
    FeedbackMapping("not memorable", "strengthen_hook", {"hook_repetition": True, "motif_clarity": True}),
    # Section-specific
    FeedbackMapping(
        "chorus feels weak", "increase_climax_intensity", {"tension_boost": 0.2}, preserve=("verse", "intro")
    ),
    FeedbackMapping("intro too long", "shorten_section", {"bar_reduction": 2}),
    FeedbackMapping("ending abrupt", "extend_section", {"bar_addition": 2, "fade_out": True}),
)

# Section keywords for target detection
_SECTION_KEYWORDS = {
    "intro": "intro",
    "verse": "verse",
    "chorus": "chorus",
    "bridge": "bridge",
    "outro": "outro",
    "ending": "outro",
    "beginning": "intro",
    "hook": "chorus",
}

# Instrument keywords for target detection
_INSTRUMENT_KEYWORDS = {
    "piano": "piano",
    "drums": "drums",
    "bass": "acoustic_bass",
    "guitar": "acoustic_guitar_nylon",
    "strings": "strings_ensemble",
    "vocals": "vocal_lead",
    "synth": "synth_pad_warm",
}


class NLFeedbackTranslator:
    """Translates natural-language feedback into structured changes.

    Uses a maintainable mapping table. When input is ambiguous
    (no mapping matches), marks the result as ambiguous rather
    than guessing.

    Example:
        >>> translator = NLFeedbackTranslator()
        >>> result = translator.translate("the chorus feels weak")
        >>> result.intents
        ['increase_climax_intensity']
        >>> result.target_sections
        ['chorus']
    """

    def translate(self, text: str) -> StructuredFeedback:
        """Translate NL feedback to structured form.

        Args:
            text: User's natural-language feedback.

        Returns:
            StructuredFeedback with parsed intents and parameters.
        """
        text_lower = text.lower().strip()

        if not text_lower:
            return StructuredFeedback(
                original_text=text,
                ambiguous=True,
                ambiguity_reason="Empty feedback text",
            )

        # Detect target sections
        sections = self._detect_sections(text_lower)

        # Detect target instruments
        instruments = self._detect_instruments(text_lower)

        # Match against mapping table
        matched_intents: list[str] = []
        all_adjustments: dict[str, Any] = {}
        all_preserve: list[str] = []

        for mapping in FEEDBACK_MAPPINGS:
            if mapping.phrase in text_lower:
                matched_intents.append(mapping.intent)
                all_adjustments.update(mapping.parameter_adjustments)
                all_preserve.extend(mapping.preserve)

        # Deduplicate
        matched_intents = list(dict.fromkeys(matched_intents))
        all_preserve = list(dict.fromkeys(all_preserve))

        if not matched_intents:
            return StructuredFeedback(
                original_text=text,
                target_sections=sections,
                target_instruments=instruments,
                ambiguous=True,
                ambiguity_reason=(
                    "No recognized feedback pattern found. "
                    "Try phrases like 'too loud', 'boring', 'muddy', "
                    "'chorus feels weak', 'too dissonant'."
                ),
            )

        return StructuredFeedback(
            original_text=text,
            target_sections=sections,
            target_instruments=instruments,
            intents=matched_intents,
            parameter_adjustments=all_adjustments,
            preserve=all_preserve,
        )

    def _detect_sections(self, text: str) -> list[str]:
        """Detect section references in text."""
        found: list[str] = []
        for keyword, section in _SECTION_KEYWORDS.items():
            if keyword in text and section not in found:
                found.append(section)
        return found

    def _detect_instruments(self, text: str) -> list[str]:
        """Detect instrument references in text."""
        found: list[str] = []
        for keyword, instrument in _INSTRUMENT_KEYWORDS.items():
            if keyword in text and instrument not in found:
                found.append(instrument)
        return found

    def translate_pin_note(self, note: str) -> str:
        """Translate a pin note to a user_intent code.

        Args:
            note: The pin's natural-language comment.

        Returns:
            A PinIntent string.
        """
        text_lower = note.lower().strip()

        # Direct intent mappings for pin notes
        intent_keywords: dict[str, str] = {
            "dissonant": "soften_dissonance",
            "harsh": "soften_dissonance",
            "clashing": "soften_dissonance",
            "loud": "too_loud",
            "soft": "too_soft",
            "quiet": "too_soft",
            "busy": "too_busy",
            "cluttered": "too_busy",
            "sparse": "too_sparse",
            "empty": "too_sparse",
            "boring": "add_variation",
            "repetitive": "add_variation",
            "monoton": "add_variation",
            "intense": "decrease_intensity",
            "weak": "increase_intensity",
            "strong": "decrease_intensity",
            "simple": "simplify",
            "complex": "simplify",
            "rhythm": "change_rhythm",
            "chord": "change_harmony",
            "harmony": "change_harmony",
            "melody": "change_melody",
        }

        for keyword, intent in intent_keywords.items():
            if keyword in text_lower:
                return intent

        return "unclear"
