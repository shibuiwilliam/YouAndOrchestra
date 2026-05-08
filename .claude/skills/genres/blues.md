---
genre_id: blues
display_name: "Blues"
parent_genres: [work_songs, spirituals]
related_genres: [jazz, rock, rhythm_and_blues, soul, gospel]
typical_use_cases: [emotional_expression, bar_atmosphere, film_scoring, roots_music]
ensemble_template: custom
default_subagents:
  active: [composer, rhythm_architect, mix_engineer, adversarial_critic, producer]
  inactive: [sound_designer, loop_architect, harmony_theorist]
---

# Blues — Genre Skill

## Defining Characteristics
- Tempo: 60-140 BPM (slow blues 60-80; medium shuffle 90-120; up-tempo 120-140)
- Shuffle or swing feel based on triplet subdivision (swing ratio 0.62-0.70)
- 12-bar blues form as the foundational structure (~70% of blues pieces)
- Dominant 7th chords as the harmonic baseline (I7, IV7, V7)
- Blue notes: b3, b5, and b7 are defining melodic colors, used over major-key harmony
- Call-and-response phrasing between vocal/lead and rhythm section
- Expressive pitch bending, vibrato, and slides as core melodic devices
- Emotional directness: the music serves the feeling, not the technique
- Repetitive harmonic structure with melodic and rhythmic variation providing interest

## Required Spec Patterns
```yaml
tempo_bpm: 100
time_signature: "4/4"
swing: 0.65
instruments:
  - name: electric_guitar_clean
    role: melody
  - name: electric_bass_finger
    role: bass
  - name: drums
    role: rhythm
  - name: piano
    role: harmony
generation:
  strategy: phrase_aware
  temperature: 0.45
features:
  chord_aware_melody: true
  voice_leading_optimization: false
```

## Idiomatic Chord Progressions
- I7-I7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7 (standard 12-bar blues, ~40%)
- I7-IV7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7 (quick-change blues, ~20%)
- i7-iv7-i7-i7-iv7-iv7-i7-i7-V7-iv7-i7-V7 (minor blues, ~15%)
- I7-I7-I7-I7-IV7-IV7-I7-VI7-ii7-V7-I7-V7 (jazz blues, ~10%)
- 8-bar blues: I7-V7-IV7-IV7-I7-V7-I7-V7 (~8%)
- 16-bar blues (expanded form, ~7%)

## Idiomatic Rhythms
### Shuffle
```
KICK:   X . . X . . X . . X . .
SNARE:  . . . . . X . . . . . X
HIHAT:  X . x X . x X . x X . x
```
(triplet grid: each beat divided into 3)
### Slow Blues
```
KICK:   X . . . . . . . X . . . . . . .
SNARE:  . . . . X . . . . . . . X . . .
HIHAT:  X . X . X . X . X . X . X . X .
```
- Shuffle: triplet-based swing, ride or hi-hat playing shuffled pattern
- Snare on 2 and 4, with ghost notes between
- Kick: beats 1 and 3, or syncopated patterns in up-tempo blues
- Fills: simple, groove-oriented, serving the pocket

## Anti-Patterns
- Straight eighth notes in shuffle blues (the shuffle is the feel)
- Extended jazz voicings beyond dominant 7ths in traditional blues (keep it I7-IV7-V7)
- Avoiding blue notes (b3, b5, b7 are the soul of the melody)
- Perfect intonation on melodic bends (expressive pitch imprecision is desired)
- Complex harmonic substitutions in traditional blues (save those for jazz blues)
- Fast virtuosic passages without space (blues breathes; rests are notes)
- Busy, cluttered arrangements (simplicity and feel over complexity)
- Mechanical, quantized timing (human feel with push and pull is essential)
- Severity: HIGH for straight eighths in shuffle and no blue notes; MEDIUM for over-complexity

## Reference Tracks
- None yet (rights-cleared blues references needed)

## Default Sound Design
```yaml
instruments:
  electric_guitar_clean: { synthesis: { kind: sample_based, pack: "strat_clean_blues" }, effect_chain: [{ type: tube_overdrive, drive: 0.3 }, { type: spring_reverb, wet: 0.2 }, { type: eq, bands: [{ freq_hz: 3000, gain_db: 2 }] }] }
  electric_bass_finger: { synthesis: { kind: sample_based, pack: "p_bass_flatwound" }, effect_chain: [{ type: compressor, threshold_db: -15, ratio: 3 }] }
  drums: { synthesis: { kind: sample_based, pack: "blues_kit_warm" } }
  piano: { synthesis: { kind: sample_based, pack: "upright_piano_honky" }, effect_chain: [{ type: eq, bands: [{ freq_hz: 2500, gain_db: 2 }] }] }
```

## Evaluation Weight Adjustments
structure.section_contrast: 0.6
melody.contour_variety: 0.8
melody.blue_note_presence: 1.5
melody.chord_tone_targeting: 1.2
harmony.consonance_ratio: 0.8
harmony.voice_leading: 0.6
rhythm.groove_consistency: 1.5
rhythm.shuffle_accuracy: 1.5
expression.bend_presence: 1.3

## Default Trajectories
```yaml
trajectories:
  tension:
    type: arc
    sections: { intro: 0.2, verse_1: 0.4, turnaround_1: 0.5, verse_2: 0.5, turnaround_2: 0.6, solo: 0.7, verse_3: 0.6, turnaround_3: 0.4, outro: 0.2 }
  density:
    type: arc
    sections: { intro: 0.3, verse_1: 0.5, turnaround_1: 0.5, verse_2: 0.55, turnaround_2: 0.55, solo: 0.65, verse_3: 0.5, turnaround_3: 0.45, outro: 0.3 }
```

## Tempo
- Range: 60-140 BPM
- Slow blues: 60-80 BPM (deep, emotional, lots of space)
- Medium shuffle: 90-120 BPM (the classic blues sweet spot)
- Up-tempo: 120-140 BPM (boogie, jump blues energy)
- Time feel: shuffle/swing based on triplet grid; occasional straight-eighths in modern blues-rock

## Key Preferences
- E major/minor (guitar-friendly, open strings resonate)
- A major/minor (standard blues guitar and harmonica key)
- G major (acoustic blues, open tuning friendly)
- Bb, Eb (horn-friendly, jump blues keys)
- Blues scale and mixolydian mode are the melodic foundations
- Blue notes (b3, b5, b7) used regardless of whether the underlying key is major or minor

## Drum Pattern Family
- Default: blues_shuffle
- Shuffle feel: triplet-based subdivision with swung hi-hat or ride
- Snare on 2 and 4 with ghost notes (especially on the triplet "and-a")
- Kick: beats 1 and 3, simple and supportive
- Slow blues: half-time feel, sparse, lots of space
- Up-tempo: driving shuffle, more active kick pattern

## Instrumentation Defaults
- Core: electric_guitar_clean (with light overdrive), electric_bass_finger, drums
- Harmony: piano (boogie-woogie patterns, comping) or organ (B3 with Leslie)
- Common additions: harmonica, horns (trumpet, tenor_sax, trombone for jump blues)
- Avoid: synth_lead, synth_bass, synth_pad, drum_machine, heavily distorted guitar (unless blues-rock crossover)

## Section Structure
- 12-Bar Form (standard): I7(4)-IV7(2)-I7(2)-V7(1)-IV7(1)-I7(1)-V7(1) (turnaround)
- Intro: 4 bars, solo instrument or stop-time figure
- Verse 1: 12 bars, melody stated (often AAB lyric form)
- Verse 2: 12 bars, melody repeated with variation
- Solo: 1-3 choruses (12 bars each), guitar or harmonica improvisation
- Verse 3: 12 bars, return of vocal melody, often most intense
- Outro/Turnaround: 4-8 bars, final turnaround, ritardando, ending on I7 or V7

## Trajectory Patterns
- Classic Blues: tension 0.2 -> 0.4 -> 0.5 -> 0.6 -> 0.7 -> 0.5 -> 0.2
- Slow Burn: tension 0.15 -> 0.3 -> 0.4 -> 0.6 -> 0.75 -> 0.4 -> 0.15
- Jump Blues: tension 0.4 -> 0.5 -> 0.6 -> 0.7 -> 0.8 -> 0.6 -> 0.4

## Cadences
- V7-IV7-I7 (the blues turnaround, the signature cadence)
- V7-I7 (simple resolution)
- I7-IV7-I7-V7 (turnaround setting up the next chorus)
- Unresolved V7 (ending on dominant for open, unfinished feeling)
- Stop-time cadence (band stops, soloist plays the resolution alone)

## Cliches to AVOID
- Straight eighth notes in a shuffle context (the triplet feel is non-negotiable)
- Clean, precise intonation without bends (blues requires expressive pitch manipulation)
- Complex jazz substitutions in traditional blues (tritone subs and altered dominants belong to jazz blues)
- Filling every beat with notes (blues needs space to breathe)
- High-register pyrotechnics without emotional grounding (feel over flash)
- Ignoring the call-and-response structure (blues is conversational)
- Severity: HIGH = straight eighths in shuffle, no blue notes; MEDIUM = too complex, no space
- Fix recipe: add shuffle feel, incorporate b3/b5/b7 blue notes, leave rests, use bends and slides

## Quality Heuristics
- Melody: pentatonic/blues scale based, bends on b3 and b5, vibrato on sustained notes
- Harmony: dominant 7th chords on I, IV, and V; no major 7ths in traditional blues
- Bass: root-fifth patterns, walking lines in up-tempo, supportive and simple
- Drums: shuffle feel must be audible; ghost notes add groove
- Velocity: moderate with expressive accents (60-100 range), dynamic swells on phrases
- Swing ratio: 0.62-0.70 for shuffle feel
- Expression: bends, slides, vibrato are not ornaments -- they are core vocabulary
- Space: rests between phrases are as important as the notes

## Production Notes
- Target loudness: -14 to -10 LUFS (dynamic but present)
- Guitar: slightly overdriven (not clean, not heavily distorted), present in the mid-range
- Bass: warm, round, center, supportive
- Drums: natural, room sound, not overly compressed
- Reverb: medium room, simulating a juke joint or small club
- Stereo: guitar slightly off-center, bass center, drums natural panning
- Minimal processing: blues values rawness and authenticity

## References
- Titon, Jeff Todd. *Early Downhome Blues: A Musical and Cultural Analysis*. University of North Carolina Press, 1994.
- Kubik, Gerhard. *Africa and the Blues*. University Press of Mississippi, 1999.
- Evans, David. *Big Road Blues: Tradition and Creativity in the Folk Blues*. Da Capo Press, 1982.
- Gioia, Ted. *Delta Blues: The Life and Times of the Mississippi Masters Who Revolutionized American Music*. Norton, 2008.
- Herzhaft, Gerard. *Encyclopedia of the Blues*. University of Arkansas Press, 1992.

## Use Cases
- Emotional and introspective scenes in film
- Bar and juke joint atmosphere
- Roots music and Americana settings
- Late-night radio programming
- Foundation study for jazz and rock musicians
