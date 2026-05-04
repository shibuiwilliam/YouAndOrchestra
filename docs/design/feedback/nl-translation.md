# Design: NL Feedback Translation (Phase δ.2)

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
- Intensity: weak, too loud, too quiet, overwhelming
- Dissonance: harsh, dissonant, clashing
- Boredom: boring, predictable, monotonous, repetitive
- Texture: muddy, too busy, too sparse, empty
- Rhythm: stiff, mechanical, no groove
- Melody: flat, not memorable
- Section-specific: chorus feels weak, intro too long, ending abrupt
