# Music Theory Reference

Music theory constants used by YaO's generation and verification layers.

## Scales

YaO supports 28 scale types. The 14 standard scales are defined in `src/yao/constants/music.py`, and 14 extended/microtonal scales (EDO, Japanese, maqam, raga, gamelan, just intonation) are defined in `src/yao/constants/scales.py` as cents-based `ScaleDefinition` objects.

### Standard Scales (14)

| Scale | Intervals | Example (C root) |
|-------|-----------|-------------------|
| major | 0,2,4,5,7,9,11 | C D E F G A B |
| minor | 0,2,3,5,7,8,10 | C D Eb F G Ab Bb |
| harmonic_minor | 0,2,3,5,7,8,11 | C D Eb F G Ab B |
| melodic_minor | 0,2,3,5,7,9,11 | C D Eb F G A B |
| dorian | 0,2,3,5,7,9,10 | C D Eb F G A Bb |
| mixolydian | 0,2,4,5,7,9,10 | C D E F G A Bb |
| lydian | 0,2,4,6,7,9,11 | C D E F# G A B |
| phrygian | 0,1,3,5,7,8,10 | C Db Eb F G Ab Bb |
| locrian | 0,1,3,5,6,8,10 | C Db Eb F Gb Ab Bb |
| pentatonic_major | 0,2,4,7,9 | C D E G A |
| pentatonic_minor | 0,3,5,7,10 | C Eb F G Bb |
| blues | 0,3,5,6,7,10 | C Eb F F# G Bb |
| whole_tone | 0,2,4,6,8,10 | C D E F# G# A# |
| chromatic | 0,1,2,3,4,5,6,7,8,9,10,11 | All 12 notes |

### Extended / Microtonal Scales (14)

Defined in `src/yao/constants/scales.py` as `ScaleDefinition` with cents-based tuning:

| Category | Scales |
|----------|--------|
| EDO (equal division) | 19-EDO, 24-EDO (quarter-tone), 31-EDO, and more |
| Japanese | in, ritsu, hirajoshi, yo, miyako-bushi, minyo |
| Maqam | rast, bayati, hijaz, nahawand, kurd |
| Raga | yaman, bhairav, darbari, todi, bhairavi |
| Gamelan | slendro, pelog |
| Just Intonation | 5-limit JI |

All extended scales include `cultural_context` metadata.

## Chord Types

14 chord types defined as semitone intervals:

| Chord | Intervals | Example (C root) |
|-------|-----------|-------------------|
| maj | 0,4,7 | C E G |
| min | 0,3,7 | C Eb G |
| dim | 0,3,6 | C Eb Gb |
| aug | 0,4,8 | C E G# |
| maj7 | 0,4,7,11 | C E G B |
| min7 | 0,3,7,10 | C Eb G Bb |
| dom7 | 0,4,7,10 | C E G Bb |
| dim7 | 0,3,6,9 | C Eb Gb A |
| half_dim7 | 0,3,6,10 | C Eb Gb Bb |
| sus2 | 0,2,7 | C D G |
| sus4 | 0,5,7 | C F G |
| add9 | 0,4,7,14 | C E G D' |
| min9 | 0,3,7,10,14 | C Eb G Bb D' |
| maj9 | 0,4,7,11,14 | C E G B D' |

## Chord Function Notation

YaO uses **Roman numeral notation** for chord functions:

| Degree | Major Key | Minor Key |
|--------|-----------|-----------|
| 0 (I/i) | maj | min |
| 1 (II/ii) | min | dim |
| 2 (III/iii) | min | maj |
| 3 (IV/iv) | maj | min |
| 4 (V/v) | maj | min |
| 5 (VI/vi) | min | maj |
| 6 (VII/vii) | dim | maj |

Concrete pitches are realized via `yao.ir.harmony.realize()`. Never mix functional (Roman numeral) and concrete (C, Dm7) notation in the same context.

## Dynamics

| Marking | MIDI Velocity |
|---------|--------------|
| ppp | 16 |
| pp | 33 |
| p | 49 |
| mp | 64 |
| mf | 80 |
| f | 96 |
| ff | 112 |
| fff | 127 |
