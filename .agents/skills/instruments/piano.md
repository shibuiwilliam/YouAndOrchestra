# Piano — Instrument Skill

## Physical Characteristics
- **Range:** A0 (MIDI 21) to C8 (MIDI 108) — 88 keys
- **YaO constant:** `INSTRUMENT_RANGES["piano"]` = midi_low=21, midi_high=108, program=0
- **Type:** Keyboard, percussive string
- **Polyphony:** Up to 10 voices simultaneously (practical limit)

## Idiomatic Ranges
| Register | MIDI Range | Character |
|----------|-----------|-----------|
| Deep bass | 21-40 (A0-E2) | Rumbling, dramatic, use sparingly |
| Bass | 40-52 (E2-E3) | Warm foundation, left hand bass |
| Tenor | 52-64 (E3-E4) | Rich, full body, accompaniment |
| Alto | 64-76 (E4-E5) | Sweet spot for melody and harmony |
| Soprano | 76-88 (E5-E6) | Bright, singing, melodic peak |
| Upper | 88-108 (E6-C8) | Brilliant, ethereal, use for special effect |

## Common Patterns

### Left Hand (Bass + Harmony)
- **Alberti bass:** Broken chord (C-G-E-G) in eighth notes — classical
- **Root-fifth:** Alternating root and fifth — folk, pop
- **Block chords:** Sustained chord voicings — ballads
- **Octave bass:** Root in octaves on beats 1 and 3 — rock, pop
- **Walking bass:** Stepwise quarter notes — jazz

### Right Hand (Melody + Harmony)
- **Single-line melody:** One note at a time — lead voice
- **Melody with thirds:** Melody doubled a third below — romantic
- **Chord melody:** Melody as top note of chord — jazz
- **Arpeggiated chords:** Broken chords ascending — dreamy, ambient

### Two-Hand Coordination
- Typical split: left hand below C4 (MIDI 60), right hand at or above C4
- Hands should not cross frequently
- Total interval between lowest left and highest right: usually within 3 octaves for comfortable playing

## YaO Generation Tips
- When piano is **melody** role: target octave 5 (C5-C6), use stepwise motion with occasional thirds
- When piano is **harmony** role: target octave 4 (C4-C5), use block or broken chords
- When piano is **pad** role: target octave 3-4, sustained notes with open voicing
- Velocity range: pp=30, p=50, mp=65, mf=80, f=95, ff=110, fff=127
- Duration: staccato=0.25 beats, normal=0.85 beats, legato=0.95 beats, sustained=full duration

## Genre Adaptations
| Genre | Typical Pattern | Tempo | Dynamics |
|-------|----------------|-------|----------|
| Classical | Alberti bass + melodic right hand | 80-120 | pp-ff, wide dynamic range |
| Jazz | Walking bass + chord melody | 100-160 | mp-f, swing feel |
| Pop/Rock | Block chords + melodic hooks | 100-140 | mf-f, consistent |
| Ambient | Sustained arpeggios, wide voicing | 60-90 | pp-mp, gentle |
| Cinematic | Sparse, wide intervals, building | 70-100 | pp-ff, dramatic arc |
