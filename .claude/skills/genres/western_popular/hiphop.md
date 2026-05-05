---
genre: hiphop
tempo_range: [70, 110]
typical_keys: [Cm, Gm, Dm, Am, Fm, Bbm]
modal_options: [minor, dorian, phrygian, blues]
default_swing: 0.1
typical_drum_pattern: boom_bap_classic
preferred_instruments: [electric_bass_finger, piano, synth_pad_warm, strings_ensemble]
avoided_instruments: [harpsichord, piccolo, oboe, bagpipes, sitar, timpani]
evaluation_weights:
  structure: 0.15
  melody: 0.15
  harmony: 0.15
  acoustics: 0.15
  groove_pocket: 0.40
evaluation_thresholds:
  predictability_max: 0.90
  section_contrast_min: 0.15
default_groove: boom_bap_classic
default_melody_strategy: riff_based
---

# Hip-Hop — Genre Skill

## Tempo
- Range: 70-110 BPM (half-time feel at 140-170 BPM common)
- Boom bap: 85-95 BPM
- Trap: 130-160 BPM (felt as half-time 65-80 BPM)
- Tempo consistency is essential; no rubato

## Key Preferences
- Minor keys dominant (Cm, Gm, Dm, Am)
- Dorian for smoother feel (raised 6th adds warmth)
- Phrygian for aggressive/dark tracks (flat 2nd)
- Blues scale for melodic hooks
- Key center often implied through bass riff, not explicit harmony

## Iconic Chord Progressions (frequency-ranked)
1. i (single chord loop, ~30% — groove is the structure)
2. i-bVII (two-chord vamp, ~20%)
3. i-iv (minor movement, ~15%)
4. i-bVI-bVII (Aeolian cadence, ~15%)
5. i-bIII-bVII-iv (minor cycle, ~10%)
6. i-v-bVI-iv (dramatic minor, ~10%)

## Drum Pattern Family
- Default: boom_bap_classic (kick-snare-hat with laid-back feel)
- Boom bap: heavy kick on 1, snare on 3, hi-hat 8ths or 16ths
- Trap: rapid hi-hat rolls (32nds), 808 kick with long sustain, sparse snare/clap
- Lo-fi: vinyl-crackle texture, sidechain compression feel
- Swing is subtle but essential (5-15ms laid-back snare)

## Instrumentation Defaults
- Core: drum machine (not acoustic kit), electric_bass_finger or 808 bass
- Melodic: piano (sample chops), strings_ensemble (cinematic hooks)
- Texture: synth_pad_warm (atmospheric), vinyl noise
- Vocal samples and ad-libs as rhythmic elements
- Avoid: orchestral brass fanfares, harpsichord, overly clean acoustic sounds

## Section Structure
- Intro: 4-8 bars (beat intro, atmospheric)
- Verse: 16 bars (primary rhythmic focus)
- Hook/Chorus: 8 bars (melodic hook or vocal chant, high repetition)
- Verse 2: 16 bars
- Bridge: 4-8 bars (breakdown, stripped drums, sample manipulation)
- Outro: 4-8 bars
- Total: 3-4 minutes

## Melody Conventions
- Melodic content often minimal — riff-based, 2-4 bar loops
- Pentatonic minor or blues scale dominant
- Repetition is a virtue — hooks should repeat with minimal variation
- Pitch range narrow (one octave or less)
- Vocal rhythm is the primary "melodic" element

## Harmonic Conventions
- Harmony is secondary to groove and rhythm
- 1-2 chord loops are standard; more than 4 chords per section is unusual
- Bass drives harmony more than chord pads
- Sample-based harmony (chopped loops) creates non-functional progressions
- Avoid: functional cadences (V-I), complex voice leading

## Adversarial Critic Rules
- Deal-breaker: groove does not pocket (drums must swing or lay back)
- Warning: too many chord changes per section (>4 is unusual for hip-hop)
- Warning: melody too complex (hip-hop melodic lines should be simple, repetitive)
- Cliche: generic boom-bap pattern without personality → flag if no variation in 8+ bars
- Note: low section_contrast_min is intentional — repetition is the genre
