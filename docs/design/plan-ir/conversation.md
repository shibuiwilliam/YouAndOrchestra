# Design: Conversation Plan (Phase γ.5)

## Problem
Instruments are generated independently with no inter-listening. The ensemble sounds mechanical.

## Solution
- ConversationPlan IR: primary voice per section, conversation events (call-response, fill, tutti, solo, trade)
- Conversation Director Subagent: new Step 5.5, produces plan only (no notes)
- Reactive Fills: detect phrase-end silences, insert idiomatic fills
- Frequency Clearance: symbolic collision detection, octave displacement to reduce masking
- 4 critique rules: conversation_silence, primary_voice_ambiguity, fill_absence, frequency_collision_unresolved
