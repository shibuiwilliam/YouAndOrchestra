---
instrument_family: keyboard
default_legato_overlap: 0.0
default_accent_strength: 0.3
sustain_cc: 64
pedal_change_on_harmony: true
articulation_map:
  phrase_start: normal
  phrase_end: release
  strong_beat: accent
  chord_change: pedal_up_down
---

# Piano Pedaling Skill

## Default Character
Piano notes decay naturally. Sustain pedal (CC64) is the primary expressive tool.

## Pedaling
- **Legato pedaling**: Pedal changes on harmonic changes (chord boundaries).
- **Half pedaling**: Partial pedal (CC64 value 40-80) for clarity with sustain.
- **No pedal**: Staccato passages, fast runs.

## Pedal Curve Pattern
- On chord change: CC64 drops to 0, then back to 127 within 50ms
- Between changes: CC64 stays at 127 (full sustain)
- At phrase end: gradual release (127 → 0 over 0.5 beats)

## Articulation
- **Accent**: Strong beats. Velocity boost (accent_strength 0.3).
- **Staccato**: Short notes in rhythmic passages. No pedal.
- **Legato**: Pedal sustains across notes (no overlap needed).
