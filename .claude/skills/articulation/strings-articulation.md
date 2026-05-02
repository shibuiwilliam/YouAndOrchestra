---
instrument_family: strings
default_legato_overlap: 0.02
default_accent_strength: 0.4
vibrato_cc: 1
vibrato_default_depth: 64
articulation_map:
  phrase_start: legato
  phrase_end: tenuto
  strong_beat: accent
  weak_beat: legato
  ascending_leap: marcato
  descending_step: legato
---

# Strings Articulation Skill

## Default Character
Strings are inherently legato instruments. Notes connect smoothly unless explicitly separated.

## Articulation Mapping
- **Legato**: Default. Slight overlap (20ms) between consecutive notes.
- **Tenuto**: Phrase endings. Full duration, gentle release.
- **Accent**: Strong beats (beat 1, sometimes beat 3 in 4/4). Increased bow pressure.
- **Marcato**: Large ascending leaps. Strong attack with full value.
- **Staccato**: Rare in melodic lines. Used for rhythmic passages (pizzicato implied).

## Vibrato (CC1)
- Default depth: 64 (medium)
- Long notes (>1 beat): gradual onset, peak at 60% of duration
- Short notes (<0.5 beat): minimal or no vibrato
- Phrase climax: increased depth (80-100)

## Dynamic Response
- Strings respond naturally to dynamic curves
- Crescendo = increasing bow speed/pressure
- Sudden dynamics (sfz): accent_strength 0.7+
