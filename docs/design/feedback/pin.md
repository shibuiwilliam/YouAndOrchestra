# Design: Pin Feedback

## Problem

Users can only give feedback at spec-level (change YAML) or section-level (regenerate-section). No way to say "this specific bar on this instrument is wrong."

## Solution

Pins — immutable, localized user comments that drive targeted regeneration.

## Pin Structure

- `PinLocation`: section + bar + optional beat + optional instrument
- `Pin`: id, location, note (NL text), user_intent (parsed), severity, created_at
- `PinsSpec`: Pydantic schema for pins.yaml (CLI-managed, not hand-edited)

## CLI Usage

```bash
yao pin "verse:bar4:piano — too busy, simplify the left hand"
yao pin "chorus:bar2 — needs more energy"
```

## Regeneration Algorithm

1. Compute affected region: pin bar ± 1 bar padding
2. For each note in the region: apply intent-based adjustment
3. Notes outside the region: preserved exactly (bit-identical)

## Provenance

Every pin-driven regeneration records pin_id in the provenance log, linking the user's intent to the specific notes that changed.

## Files

- `src/yao/feedback/pin.py` — Pin, PinLocation
- `src/yao/feedback/pin_aware_regenerator.py` — regenerate_with_pins()
- `src/yao/schema/pins.py` — PinsSpec
