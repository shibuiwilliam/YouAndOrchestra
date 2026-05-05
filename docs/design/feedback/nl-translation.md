# Design: NL Feedback Translation

## Problem

Users describe musical issues in natural language ("too muddy", "chorus feels weak"). The system needs structured intents to act on.

## Solution

NLFeedbackTranslator with a maintainable mapping table of ~30 phrase → intent mappings.

## Architecture

- `FEEDBACK_MAPPINGS`: tuple of FeedbackMapping (phrase, intent, parameter_adjustments, preserve)
- `NLFeedbackTranslator.translate(text)` → `StructuredFeedback`
- Detects target sections ("chorus", "intro") and instruments ("piano", "drums")
- When no mapping matches: marks as ambiguous with suggestion phrases

## Mapping Categories

| Category | Example Phrases |
|----------|----------------|
| Intensity | weak, too loud, too quiet, overwhelming |
| Dissonance | harsh, dissonant, clashing |
| Boredom | boring, predictable, monotonous, repetitive |
| Texture | muddy, too busy, too sparse, empty |
| Rhythm | stiff, mechanical, no groove |
| Melody | flat, not memorable |
| Section-specific | chorus feels weak, intro too long, ending abrupt |

## Files

- `src/yao/feedback/nl_translator.py` — NLFeedbackTranslator, FEEDBACK_MAPPINGS
- `tests/unit/feedback/test_nl_translator.py` — 24 tests
- `tests/scenarios/test_nl_feedback_translation.py` — 5 scenario tests
