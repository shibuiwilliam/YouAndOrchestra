# Design: Pin Feedback (Phase δ.2)

## Problem
Users can only give feedback at spec-level (change YAML) or section-level (regenerate-section). No way to say "this specific bar on this instrument is wrong."

## Solution
Pins — immutable, localized user comments that drive targeted regeneration.

## Pin Structure
- `PinLocation`: section + bar + optional beat + optional instrument
- `Pin`: id, location, note (NL text), user_intent (parsed), severity, created_at
- `PinsSpec`: Pydantic schema for pins.yaml (CLI-managed, not hand-edited)

## Regeneration Algorithm
1. Compute affected region: pin bar ± 1 bar padding
2. For each note in the region: apply intent-based adjustment
3. Notes outside the region: preserved exactly (bit-identical)

## Provenance
Every pin-driven regeneration records pin_id in the provenance log.
