---
genre_id: funk
display_name: "Funk"
parent_genres: [soul, rhythm_and_blues, jazz]
related_genres: [disco, hip_hop, p_funk, jazz_funk, afrobeat]
typical_use_cases: [dance_music, groove_driven_scenes, party_atmosphere, retro_scoring]
ensemble_template: custom
default_subagents:
  active: [composer, rhythm_architect, mix_engineer, adversarial_critic, producer]
  inactive: [harmony_theorist, sound_designer, loop_architect]
---

# Funk — Genre Skill

## Defining Characteristics
- Tempo: 95-130 BPM (sweet spot 100-115)
- The groove is everything: every instrument serves the rhythmic pocket
- Syncopation-heavy: emphasis on the "one" (beat 1) and offbeats throughout
- Bass is the lead instrument: melodic, syncopated, driving the harmonic and rhythmic content
- Minimal harmonic movement: often one or two chords vamping for extended periods
- Sixteenth-note subdivision as the rhythmic grid
- Tight, interlocking parts: each instrument occupies a specific rhythmic slot
- Percussive guitar playing: "chicken scratch" muted strumming on offbeats
- Horn stabs and riffs as punctuation
- Dynamics within the groove: accents, ghost notes, and pocket define the feel

## Required Spec Patterns
```yaml
tempo_bpm: 108
time_signature: "4/4"
swing: 0.0
instruments:
  - name: electric_bass_finger
    role: bass
  - name: drums
    role: rhythm
  - name: electric_guitar_clean
    role: harmony
  - name: clavinet
    role: harmony
generation:
  strategy: phrase_aware
  temperature: 0.4
features:
  chord_aware_melody: true
  voice_leading_optimization: false
```

## Idiomatic Chord Progressions
- Single chord vamp on dom7 or min7 (e.g., E9 for 16 bars, ~35%)
- I7-IV7 two-chord vamp (~20%)
- i7-IV7 (minor tonic to major IV, ~15%)
- i7-bVII7 (minor funk, ~10%)
- I9-bVII9-I9 (mixolydian movement, ~8%)
- i7-iv7-bVI7-V7 (extended minor funk, ~7%)
- One-chord modal vamp with horn riffs providing harmonic color (~5%)

## Idiomatic Rhythms
```
KICK:   X . . . . . X . . . X . . . . .
SNARE:  . . . . X . . . . . . . X . . .
HIHAT:  X x X x X x X x X x X x X x X x
BASS:   X . . x . X . . x . X . . x . X
GUITAR: . x . x . x . x . x . x . x . x
```
(sixteenth-note grid)
- Kick: beat 1 emphasized ("the one"), syncopated patterns elsewhere
- Snare: beats 2 and 4 with ghost notes on sixteenth-note subdivisions
- Hi-hat: continuous sixteenths, open hats on offbeats for accents
- Bass: syncopated sixteenth-note patterns, ghost notes, slides, pops
- Guitar: muted "scratch" strumming on offbeats (the "chicken scratch")

## Anti-Patterns
- Straight, unsyncopated rhythm (funk lives on the offbeat)
- Sustained pad chords without rhythmic articulation (every part must groove)
- Walking bass lines (belongs to jazz; funk bass is riff-based and syncopated)
- Complex harmonic progressions (harmony is minimal; the groove is the feature)
- Swing feel (funk is straight sixteenths, not triplet-based)
- Sparse, empty beats (funk is dense with interlocking parts filling the rhythmic grid)
- Ignoring "the one" (beat 1 must be emphasized; it is the anchor of funk)
- Bass playing only root notes on downbeats (bass must be melodic and syncopated)
- Severity: HIGH for no syncopation and swing feel; MEDIUM for complex harmony and sparse texture

## Reference Tracks
- None yet (rights-cleared funk references needed)

## Default Sound Design
```yaml
instruments:
  electric_bass_finger: { synthesis: { kind: sample_based, pack: "funk_bass_slap_pop" }, effect_chain: [{ type: compressor, threshold_db: -12, ratio: 4 }, { type: eq, bands: [{ freq_hz: 100, gain_db: 3 }, { freq_hz: 800, gain_db: 2 }, { freq_hz: 3000, gain_db: 3 }] }] }
  drums: { synthesis: { kind: sample_based, pack: "funk_kit_tight" }, effect_chain: [{ type: compressor, threshold_db: -10, ratio: 5 }] }
  electric_guitar_clean: { synthesis: { kind: sample_based, pack: "strat_clean_funk" }, effect_chain: [{ type: auto_wah, sensitivity: 0.5 }, { type: compressor, threshold_db: -15, ratio: 3 }] }
  clavinet: { synthesis: { kind: sample_based, pack: "clavinet_d6" }, effect_chain: [{ type: auto_wah, sensitivity: 0.4 }, { type: phaser, rate: 0.3 }] }
```

## Evaluation Weight Adjustments
structure.section_contrast: 0.5
melody.contour_variety: 0.6
melody.chord_tone_targeting: 0.7
harmony.consonance_ratio: 0.8
rhythm.groove_consistency: 1.8
rhythm.syncopation_density: 1.6
rhythm.ghost_note_presence: 1.4
bass.melodic_interest: 1.5
arrangement.interlocking_density: 1.4

## Default Trajectories
```yaml
trajectories:
  tension:
    type: stepped
    sections: { intro: 0.3, groove_a: 0.5, groove_b: 0.6, breakdown: 0.3, groove_c: 0.7, horn_shout: 0.8, groove_d: 0.6, outro: 0.4 }
  density:
    type: stepped
    sections: { intro: 0.4, groove_a: 0.6, groove_b: 0.7, breakdown: 0.3, groove_c: 0.8, horn_shout: 0.85, groove_d: 0.7, outro: 0.4 }
```

## Tempo
- Range: 95-130 BPM
- Sweet spot: 100-115 BPM (the optimal pocket for sixteenth-note grooves)
- Slow funk: 85-95 BPM (deep, swampy groove)
- Up-tempo funk: 120-135 BPM (dance energy, approaching disco territory)
- Time feel: straight sixteenths, tight and precise, with humanized ghost notes

## Key Preferences
- E minor/major (guitar resonance, bass range)
- A minor/major (standard funk center)
- Bb, Eb (horn-friendly keys for horn-driven funk)
- Mixolydian mode on dominant 7th vamps
- Dorian mode on minor 7th vamps
- One key per song is typical; modulation is rare in funk

## Drum Pattern Family
- Default: funk_sixteenth
- Hi-hat: continuous sixteenths with accent variation and open-hat accents
- Snare: beats 2 and 4 strong, ghost notes on e and a subdivisions
- Kick: beat 1 ("the one") is sacred; syncopated elsewhere
- Toms: occasional fills, but the groove rarely breaks
- Ghost notes on snare are critical -- they define the funk pocket
- Fills are short and serve the groove; never flashy for their own sake

## Instrumentation Defaults
- Core: electric_bass_finger (slap, pop, fingerstyle), drums, electric_guitar_clean (scratch, wah)
- Harmony: clavinet, organ (B3 with Leslie), piano (staccato comping)
- Horns: trumpet, tenor_sax, trombone (riffs and stabs, not sustained pads)
- Common additions: congas, bongos, tambourine (percussion layers)
- Avoid: synth_pad (too sustained), acoustic_guitar, orchestral_strings, vibraphone

## Section Structure
- Intro: 4-8 bars, establishing the groove (often just bass and drums)
- Groove A: 8-16 bars, full band groove with primary riff
- Groove B: 8-16 bars, variation (add horns, change guitar pattern)
- Breakdown: 4-8 bars, stripped to bass and drums or single instrument
- Build: 4 bars, instruments re-enter one by one
- Groove C: 8-16 bars, maximum intensity, all elements firing
- Horn Shout: 4-8 bars, horn-led section (if horns are present)
- Outro: 4-16 bars, groove vamp with gradual strip-down or hard stop

## Trajectory Patterns
- Classic Funk: tension 0.3 -> 0.5 -> 0.6 -> 0.3 -> 0.7 -> 0.8 -> 0.5 -> 0.4
- Parliament Build: tension 0.2 -> 0.4 -> 0.6 -> 0.8 -> 0.9 -> 0.6 -> 0.3
- Tight Groove: tension 0.5 -> 0.55 -> 0.6 -> 0.55 -> 0.6 -> 0.5 (minimal arc, groove-focused)

## Cadences
- Vamp resolution: the groove ending IS the cadence (stop on beat 1)
- Drum break as punctuation (all instruments drop, drums fill, band re-enters on "the one")
- Horn stab on beat 1 as arrival
- Bass fill leading to beat 1 of next section
- Hard stop (all instruments cut together, often on beat 1)
- No traditional V-I cadences; funk cadences are rhythmic, not harmonic

## Cliches to AVOID
- Playing on the beat without syncopation (funk is about the offbeat)
- Sustained, legato playing on harmonic instruments (articulate and percussive)
- Walking bass or simple root-note patterns (funk bass is a lead instrument)
- Complex chord progressions with many changes (one or two chords is enough)
- Swing or triplet feel (funk is straight sixteenths)
- No ghost notes on drums (they define the pocket)
- Breaking the groove for flashy fills (the groove is sacred)
- Severity: HIGH = no syncopation, no ghost notes, swing feel; MEDIUM = complex harmony, sparse texture
- Fix recipe: add sixteenth-note grid, syncopate bass and guitar, add ghost notes to snare, simplify harmony to 1-2 chord vamp

## Quality Heuristics
- Bass: syncopated, melodic, using slap/pop/ghost notes; the most important instrument
- Drums: tight pocket, ghost notes audible, hi-hat consistency, solid kick on "the one"
- Guitar: percussive, muted scratching, wah-wah on solos
- Horns: short stabs and riffs, not sustained legato lines
- Velocity: varied within parts for groove articulation (ghost notes 30-50, accents 90-120)
- Rhythmic density: high, but every note serves the groove
- Interlocking: parts must fit together like puzzle pieces; no two instruments on the same subdivision

## Production Notes
- Target loudness: -12 to -8 LUFS (punchy, dynamic, present)
- Bass: center, bright (slap harmonics present), compressed for consistency
- Guitar: slightly off-center, wah-wah or envelope filter is signature
- Drums: tight, close-miked, punchy (minimal room ambience)
- Horns: panned in section (trumpet L, trombone C, sax R)
- Stereo: bass and kick center; guitars and keys slightly wide; percussion wide
- Compression: moderate; preserve the dynamic pocket of ghost notes vs. accents

## References
- Danielsen, Anne. *Presence and Pleasure: The Funk Grooves of James Brown and Parliament*. Wesleyan University Press, 2006.
- Stewart, Alexander. "Funky Drummer: New Orleans, James Brown and the Rhythmic Transformation of American Popular Music." *Popular Music* 19, no. 3 (2000): 293-318.
- Hughes, Timothy S. "Groove and Flow: Six Analytical Essays on the Music of Stevie Wonder." PhD diss., University of Washington, 2003.
- Vincent, Rickey. *Funk: The Music, the People, and the Rhythm of the One*. St. Martin's Griffin, 1996.

## Use Cases
- Dance and party scenes
- Retro and 1970s period scoring
- Commercial music with groove and energy
- Workout and high-energy playlists
- Rhythmic foundation study for producers
