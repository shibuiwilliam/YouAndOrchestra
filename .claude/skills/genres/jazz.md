---
genre_id: jazz
display_name: "Jazz"
parent_genres: [blues, ragtime]
related_genres: [jazz_ballad, bebop, cool_jazz, hard_bop, modal_jazz, latin_jazz]
typical_use_cases: [jazz_club, dinner_music, film_scoring, background_ambience]
ensemble_template: custom
default_subagents:
  active: [composer, rhythm_architect, harmony_theorist, mix_engineer, adversarial_critic, producer]
  inactive: [beatmaker, sound_designer, loop_architect]
---

# Jazz — Genre Skill

## Defining Characteristics
- Tempo: 100-220 BPM (medium swing sweet spot 130-160)
- Swing eighth-note feel with triplet subdivision (swing ratio 0.60-0.70)
- Extended chord harmony: 7ths are the baseline; 9ths, 11ths, 13ths are standard
- Improvisation-oriented form: head-solos-head structure over repeating changes
- ii-V-I progressions as the fundamental harmonic currency
- Walking bass lines providing both harmonic and rhythmic foundation
- Ride cymbal as the primary timekeeping voice
- Dynamic interplay between rhythm section and soloists
- Blue notes (b3, b5, b7) used as expressive coloring

## Required Spec Patterns
```yaml
tempo_bpm: 145
time_signature: "4/4"
swing: 0.65
instruments:
  - name: piano
    role: harmony
  - name: acoustic_bass
    role: bass
  - name: drums
    role: rhythm
  - name: tenor_sax
    role: melody
generation:
  strategy: phrase_aware
  temperature: 0.5
features:
  chord_aware_melody: true
  voice_leading_optimization: true
```

## Idiomatic Chord Progressions
- ii7-V7-Imaj7 (fundamental jazz cadence, ~35%)
- iii7-VI7-ii7-V7 (extended turnaround, ~15%)
- Imaj7-vi7-ii7-V7 (rhythm changes turnaround, ~15%)
- I7-IV7-I7-V7 (blues form, ~10%)
- Imaj7-bVII7-bVImaj7-V7 (chromatic descent, ~10%)
- ii7-bII7-Imaj7 (tritone substitution cadence, ~8%)
- i7-bVImaj7-ii7b5-V7b9 (minor key turnaround, ~7%)

## Idiomatic Rhythms
```
RIDE:   X . x . X . x . X . x . X . x .
HIHAT:  . . . . F . . . . . . . F . . .
KICK:   X . . . . . . x . . X . . . . .
SNARE:  . . . . . . . . . . . . x . . .
```
- Ride cymbal: swing pattern with variable accent (quarter-note pulse with swung skip beat)
- Hi-hat: foot pedal on beats 2 and 4
- Kick: feathered four-on-the-floor or sparse accents
- Snare: comping accents, ghost notes, cross-stick on ballads
- Brushes standard below 120 BPM

## Anti-Patterns
- Triads without extensions (jazz demands at least 7th chords)
- Straight eighth notes in a swing context (destroys the feel)
- Root-position block chords on every beat (comping must be rhythmically varied)
- Predictable four-bar phrasing without variation (jazz phrasing is asymmetric)
- Quantized-to-grid timing (human feel and slight push/pull is essential)
- Power chords or open-fifth voicings (harmonically empty for jazz)
- Repeating an exact loop without development (jazz is conversational)
- Severity: HIGH for straight eighths and triad-only harmony; MEDIUM for rigid phrasing

## Reference Tracks
- None yet (rights-cleared jazz references needed)

## Default Sound Design
```yaml
instruments:
  piano: { synthesis: { kind: sample_based, pack: "steinway_jazz" }, effect_chain: [{ type: eq, bands: [{ freq_hz: 200, gain_db: -2 }, { freq_hz: 3000, gain_db: 2 }] }] }
  acoustic_bass: { synthesis: { kind: sample_based, pack: "upright_bass_finger" }, effect_chain: [{ type: compressor, threshold_db: -18, ratio: 3 }] }
  drums: { synthesis: { kind: sample_based, pack: "jazz_kit_brushes" } }
  tenor_sax: { synthesis: { kind: sample_based, pack: "tenor_sax_warm" }, effect_chain: [{ type: reverb, room_size: 0.4, wet: 0.2 }] }
```

## Evaluation Weight Adjustments
structure.section_contrast: 0.8
melody.contour_variety: 1.2
melody.chord_tone_targeting: 1.5
harmony.consonance_ratio: 0.6
harmony.voice_leading: 1.4
rhythm.groove_consistency: 1.2
rhythm.swing_accuracy: 1.5
arrangement.texture_density_evolution: 1.0

## Default Trajectories
```yaml
trajectories:
  tension:
    type: arc
    sections: { intro: 0.2, head_in: 0.4, solo_1: 0.6, solo_2: 0.75, shout_chorus: 0.85, head_out: 0.5, coda: 0.2 }
  density:
    type: arc
    sections: { intro: 0.3, head_in: 0.5, solo_1: 0.6, solo_2: 0.7, shout_chorus: 0.8, head_out: 0.5, coda: 0.3 }
```

## Tempo
- Range: 100-220 BPM
- Medium swing sweet spot: 130-160 BPM
- Up-tempo: 200-280 BPM (bebop territory)
- Ballad: 60-90 BPM (see jazz_ballad skill)
- Time feel shifts with tempo: brushes below 120, sticks above

## Key Preferences
- Bb major (horn-friendly, classic jazz center)
- F major, Eb major (standard horn keys)
- C minor, G minor (common minor keys)
- Frequent modulation through ii-V chains to remote keys
- Dorian mode for modal jazz passages
- Mixolydian for dominant vamps and blues-inflected sections

## Iconic Chord Progressions (frequency-ranked)
1. ii7-V7-Imaj7 (the fundamental jazz cadence, ~35%)
2. iii7-VI7-ii7-V7 (extended turnaround, ~15%)
3. Imaj7-vi7-ii7-V7 (rhythm changes A section, ~15%)
4. I7-IV7-I7-V7 (12-bar blues form, ~10%)
5. Imaj7-bVII7-bVImaj7-V7 (backdoor cadence area, ~10%)
6. ii7-bII7-Imaj7 (tritone sub cadence, ~8%)
7. i7-bVImaj7-iiO7-V7b9 (minor turnaround, ~7%)

## Drum Pattern Family
- Default: jazz_swing_ride
- Ride cymbal carries the time with quarter-note pulse and swung skip beats
- Hi-hat: foot on 2 and 4 (the heartbeat of jazz drumming)
- Kick: feathered or used for accents, never driving
- Snare: conversational comping, responding to soloists
- Brushes on ballads and medium tempos; sticks for up-tempo

## Instrumentation Defaults
- Core: piano (comping and soloing), acoustic_bass (walking lines), drums (ride-based timekeeping)
- Melody: tenor_sax, alto_sax, trumpet, trombone
- Common additions: vibraphone, guitar (archtop, clean), organ (B3)
- Avoid: synth_lead, synth_bass, distorted_guitar, drum_machine, synth_pad

## Section Structure
- Intro: 4-8 bars, rubato or vamp establishing key and mood
- Head In: 16-32 bars, melody stated by horn(s) over rhythm section (AABA or ABAC form)
- Solo Choruses: 1-4 choruses per soloist, improvising over the form
- Trading Fours: 4-bar exchanges between soloist and drums
- Shout Chorus: optional arranged climax before final head
- Head Out: melody restated, often with variations
- Coda/Tag: 2-8 bars, final cadence or vamp to fade

## Trajectory Patterns
- Standard Set: tension 0.2 -> 0.4 -> 0.6 -> 0.8 -> 0.5 -> 0.2
- Burning: tension 0.4 -> 0.6 -> 0.8 -> 0.9 -> 0.6 -> 0.3
- Cool: tension 0.15 -> 0.3 -> 0.45 -> 0.35 -> 0.2

## Cadences
- ii7-V7-Imaj7 (standard resolution)
- ii7-bII7-Imaj7 (tritone substitution)
- iii7-VI7-ii7-V7-I (long approach)
- ii7-V7-vi7 (deceptive, extends the phrase)
- Tag ending: repeated ii-V-I with ritardando
- Unresolved dominant (V7sus4 or V7#11) for open endings

## Cliches to AVOID
- Triads without 7ths (harmonically thin for jazz)
- Straight eighth notes (swing is non-negotiable in traditional jazz)
- Root-position voicings exclusively (use inversions, rootless voicings, shell voicings)
- Mechanical quantization (the human feel of jazz is its identity)
- Resolving every phrase conclusively (leave harmonic tension to create forward motion)
- Four-on-the-floor kick drum (rock/pop pattern, not jazz)
- Severity levels: HIGH = straight eighths, triad-only; MEDIUM = rigid phrasing, over-resolution
- Fix recipe: enable swing, add 7th/9th extensions, vary phrase lengths, use rootless voicings

## Quality Heuristics
- Chord voicings: 7ths minimum, 9ths/13ths standard; rootless voicings in left-hand piano
- Walking bass: mostly quarter notes with chromatic approaches, targeting chord tones on beat 1
- Melody: behind-the-beat phrasing, enclosures, bebop scales, blue notes
- Velocity: moderate with dynamic contrast (55-100 range), accent patterns reflecting swing
- Swing ratio: 0.60-0.70 (not mechanical triplets, not straight)
- Voice leading: smooth, stepwise, common tones held between chords
- Space: rests and breathing points are critical; do not fill every beat

## Production Notes
- Target loudness: -18 to -14 LUFS (dynamic, not compressed)
- Reverb: medium room or small hall, simulating a club environment
- Stereo: piano slightly left, bass center, drums slightly right, horns center
- Minimal compression; preserve natural dynamics
- EQ: warm low-mids, present high-mids for horn clarity

## References
- Levine, Mark. *The Jazz Theory Book*. Sher Music, 1995.
- Levine, Mark. *The Jazz Piano Book*. Sher Music, 1989.
- Coker, Jerry. *Elements of the Jazz Language*. Alfred Music, 1991.
- Berliner, Paul F. *Thinking in Jazz*. University of Chicago Press, 1994.
- Mehegan, John. *Jazz Improvisation*. Watson-Guptill, 1959-1965 (4 vols).

## Use Cases
- Jazz club atmosphere
- Restaurant and cocktail lounge background
- Film and television scoring (noir, urban, sophisticated scenes)
- Background for creative work
- Live performance simulation
