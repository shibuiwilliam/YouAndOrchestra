---
instrument_family: winds
default_legato_overlap: 0.01
default_accent_strength: 0.3
expression_cc: 11
breath_cc: 2
articulation_map:
  phrase_start: tongue_attack
  phrase_end: taper
  strong_beat: accent
  weak_beat: legato
  rest_before: breath_mark
---

# Winds Articulation Skill

## Default Character
Wind instruments articulate with tongue attacks. Legato requires conscious slurring.

## Articulation Mapping
- **Legato (slur)**: Connected notes within a phrase. Overlap 10ms.
- **Tongue attack**: Phrase starts and separated notes. Clean onset.
- **Taper**: Phrase endings. Gradual fade via CC11 (expression).
- **Accent**: Strong beats. Harder tongue attack.
- **Breath mark**: Before long phrases. Brief silence (0.25 beats).

## Expression (CC11)
- Sustain level: 80-100 during phrases
- Phrase shaping: slight dip at transitions
- Taper at phrase end: 100 → 40 over last beat

## Breath (CC2)
- Full value at phrase start
- Gradual decrease over long phrases
- Reset at breath marks
