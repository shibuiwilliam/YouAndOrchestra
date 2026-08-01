# Music Theory Reference

Music theory constants used by YaO's generation and verification layers.

## Scales

YaO supports 33 scale types. The 14 standard scales are defined in `src/yao/constants/music.py`, and 19 extended/microtonal scales (Japanese, maqam, raga, gamelan, just intonation) are defined in `src/yao/constants/scales.py` as cents-based `ScaleDefinition` objects.

### Standard Scales (15)

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
| aeolian | 0,2,3,5,7,8,10 | C D Eb F G Ab Bb (natural minor) |
| locrian | 0,1,3,5,6,8,10 | C Db Eb F Gb Ab Bb |
| pentatonic_major | 0,2,4,7,9 | C D E G A |
| pentatonic_minor | 0,3,5,7,10 | C Eb F G Bb |
| blues | 0,3,5,6,7,10 | C Eb F F# G Bb |
| whole_tone | 0,2,4,6,8,10 | C D E F# G# A# |
| chromatic | 0,1,2,3,4,5,6,7,8,9,10,11 | All 12 notes |

### Extended / Microtonal Scales (19)

Defined in `src/yao/constants/scales.py` as `ScaleDefinition` with cents-based tuning:

| Category | Scales |
|----------|--------|
| Japanese | in, yo, ritsu, minyo, hirajoshi, iwato |
| Maqam | rast, bayati, hijaz, nahawand, kurd |
| Raga | yaman, bhairav, darbari, marwa, todi |
| Gamelan | slendro, pelog |
| Just Intonation | just_intonation_major |

All extended scales include `cultural_context` metadata.

## Chord Types

30 chord types defined as semitone intervals:

| Chord | Intervals | Example (C root) |
|-------|-----------|-------------------|
| maj | 0,4,7 | C E G |
| min | 0,3,7 | C Eb G |
| dim | 0,3,6 | C Eb Gb |
| aug | 0,4,8 | C E G# |
| sus2 | 0,2,7 | C D G |
| sus4 | 0,5,7 | C F G |
| maj7 | 0,4,7,11 | C E G B |
| min7 | 0,3,7,10 | C Eb G Bb |
| dom7 | 0,4,7,10 | C E G Bb |
| dim7 | 0,3,6,9 | C Eb Gb A |
| half_dim7 | 0,3,6,10 | C Eb Gb Bb |
| aug7 | 0,4,8,10 | C E G# Bb |
| min_maj7 | 0,3,7,11 | C Eb G B |
| 7sus4 | 0,5,7,10 | C F G Bb |
| add9 | 0,4,7,14 | C E G D' |
| dom9 | 0,4,7,10,14 | C E G Bb D' |
| min9 | 0,3,7,10,14 | C Eb G Bb D' |
| maj9 | 0,4,7,11,14 | C E G B D' |
| add11 | 0,4,7,17 | C E G F' |
| min11 | 0,3,7,10,14,17 | C Eb G Bb D' F' |
| dom11 | 0,4,7,10,14,17 | C E G Bb D' F' |
| dom13 | 0,4,7,10,14,21 | C E G Bb D' A' |
| min13 | 0,3,7,10,14,21 | C Eb G Bb D' A' |
| maj13 | 0,4,7,11,14,21 | C E G B D' A' |
| maj6 | 0,4,7,9 | C E G A |
| min6 | 0,3,7,9 | C Eb G A |
| 6_9 | 0,4,7,9,14 | C E G A D' |
| 7alt | 0,4,8,10 | C E G# Bb |
| 7b9 | 0,4,7,10,13 | C E G Bb Db' |
| 7sharp9 | 0,4,7,10,15 | C E G Bb D#' |

## Chord Function Notation

YaO uses **Roman numeral notation** for chord functions:

| Degree | Major Key | Minor Key |
|--------|-----------|-----------|
| 0 (I/i) | maj | min |
| 1 (II/ii) | min | dim |
| 2 (III/iii) | min | maj |
| 3 (IV/iv) | maj | min |
| 4 (V/v) | maj | min¹ |
| 5 (VI/vi) | min | maj |
| 6 (VII/vii) | dim | maj |

¹ At **cadences**, the dominant in a minor key is realized as a **major V** (harmonic-minor,
raised leading tone) so it pulls to the tonic — `diatonic_quality` handles the diatonic case
and `accompaniment.chord_pitches` raises the leading tone for the dominant in minor keys.
`diatonic_quality` is also **mode-aware**: dorian/phrygian/lydian/mixolydian/aeolian/locrian get
their correct per-degree triad qualities (previously all modes collapsed to major).

Concrete pitches are realized via `yao.ir.harmony.realize()`. Never mix functional (Roman numeral) and concrete (C, Dm7) notation in the same context.

## Cadences & Voice-Leading (v2.x)

- **Authentic cadence:** the harmony planner ends the piece on the tonic (I), approached by the
  dominant (V), so compositions resolve home. Non-final sections ending on a dominant are annotated
  as **half cadences**.
- **Voice-leading:** the accompaniment voice-leads chords for minimal motion (nearest-tone) and
  repairs parallel fifths/octaves (`accompaniment.voice_lead_sequence`, reusing `ir/voicing.py`).
  Measured by the `voice_leading_smoothness` metric.
- **Walking bass:** genres whose profile sets `bass_motion_style: walking` (jazz, blues, baroque)
  get a quarter-note walking line (root → chord tones → chromatic approach) instead of a root pulse.

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
