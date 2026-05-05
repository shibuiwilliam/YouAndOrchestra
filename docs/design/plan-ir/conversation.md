# Design: Conversation Plan

## Problem

Instruments generated independently with no inter-listening produce a mechanical ensemble. Real musicians listen and respond to each other.

## Solution

- **ConversationPlan IR**: primary voice per section, conversation events (call-response, fill, tutti, solo, trade)
- **Conversation Director**: Step 5.5 in the pipeline, produces plan only (does NOT modify notes)
- **Reactive Fills**: detect phrase-end silences (gap ≥ 1.0 beat), insert idiomatic 2-4 note fills
- **Frequency Clearance**: symbolic collision detection (±3 semitones + time overlap), octave displacement to reduce masking
- **4 critique rules**: conversation_silence, primary_voice_ambiguity, fill_absence_at_phrase_ends, frequency_collision_unresolved

## ConversationEvent Types

| Event | Description |
|-------|-------------|
| `call_response` | One voice states, another answers |
| `fill_in_response` | Background voice fills silence |
| `tutti` | All voices play together |
| `solo_break` | Single voice featured |
| `trade` | Voices alternate short phrases |

## Files

- `src/yao/ir/conversation.py` — ConversationPlan, ConversationEvent, BarRange
- `src/yao/generators/plan/conversation_director.py` — generate_conversation_plan
- `src/yao/generators/reactive_fills.py` — detect_fill_opportunities, generate_reactive_fills
- `src/yao/generators/frequency_clearance.py` — symbolic collision detection
- `src/yao/verify/critique/conversation_rules.py` — 4 critique rules
