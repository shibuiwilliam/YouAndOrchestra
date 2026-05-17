---
genre_id: rock
display_name: "Rock"
parent_genres: [blues, rhythm_and_blues]
related_genres: [hard_rock, classic_rock, alternative_rock, indie_rock, punk_rock]
typical_use_cases: [energy_driven_scenes, stadium_anthem, driving_music, workout]
ensemble_template: custom
default_subagents:
  active: [composer, rhythm_architect, mix_engineer, adversarial_critic, producer]
  inactive: [harmony_theorist, sound_designer, loop_architect]
---

# Rock — Genre Skill

## Defining Characteristics
- Tempo: 100-160 BPM (sweet spot 115-135)
- Straight eighth-note feel; no swing
- Guitar-driven sound: power chords, riffs, and distortion are core identity
- Strong backbeat on beats 2 and 4 (snare emphasis)
- Simple to moderately complex harmony: triads, power chords (root-5th), and dominant 7ths
- Riff-based melodic construction rather than long-form melody
- High energy and dynamic contrast between verse and chorus
- Pentatonic and blues-scale melodic vocabulary
- Bass locks with kick drum to form the rhythmic backbone

## Required Spec Patterns
```yaml
tempo_bpm: 125
time_signature: "4/4"
swing: 0.0
instruments:
  - name: electric_guitar_distorted
    role: harmony
  - name: electric_bass_pick
    role: bass
  - name: drums
    role: rhythm
  - name: vocals
    role: melody
generation:
  strategy: phrase_aware
  temperature: 0.4
features:
  chord_aware_melody: true
  voice_leading_optimization: false
```

## Idiomatic Chord Progressions
- I-IV-V (foundational rock cadence, ~25%)
- I-bVII-IV (mixolydian rock, ~20%)
- i-bVI-bVII (aeolian rock, ~15%)
- I-V-vi-IV (pop-rock anthem, ~15%)
- I-IV-bVII-IV (classic rock shuffle, ~10%)
- i-bIII-bVII-IV (minor rock, ~8%)
- 12-bar blues form adapted with power chords (~7%)

## Idiomatic Rhythms
```
KICK:   X . . . . . X . X . . . . . X .
SNARE:  . . . . X . . . . . . . X . . .
HIHAT:  X . X . X . X . X . X . X . X .
```
- Strong backbeat on 2 and 4 (snare)
- Kick drum: varied patterns, often syncopated with guitar riff
- Hi-hat: straight eighths, occasionally opening on upbeats
- Crash cymbal: section downbeats, fills
- Fills at section transitions (typically beat 4 of final bar)

## Anti-Patterns
- Swing feel (rock is straight eighths; swing destroys the drive)
- Extended jazz chords (9ths, 11ths, 13ths feel out of place)
- Walking bass lines (belongs to jazz, not rock)
- Brush drumming (rock requires sticks and attack)
- Overly complex chord voicings (power chords and triads are the vocabulary)
- Low velocity throughout (rock needs dynamic punch, especially on accents)
- No backbeat (the snare on 2 and 4 is non-negotiable)
- Severity: HIGH for swing feel and missing backbeat; MEDIUM for jazz voicings

## Reference Tracks
- None yet (rights-cleared rock references needed)

## Default Sound Design
```yaml
instruments:
  electric_guitar_distorted: { synthesis: { kind: sample_based, pack: "electric_guitar_crunch" }, effect_chain: [{ type: distortion, drive: 0.6 }, { type: cabinet_sim, model: "4x12_british" }, { type: reverb, room_size: 0.3, wet: 0.15 }] }
  electric_bass_pick: { synthesis: { kind: sample_based, pack: "bass_pick_bright" }, effect_chain: [{ type: compressor, threshold_db: -15, ratio: 4 }, { type: eq, bands: [{ freq_hz: 80, gain_db: 3 }, { freq_hz: 800, gain_db: -2 }] }] }
  drums: { synthesis: { kind: sample_based, pack: "rock_kit_standard" }, effect_chain: [{ type: compressor, threshold_db: -12, ratio: 4 }] }
```

## Evaluation Weight Adjustments
structure.section_contrast: 1.3
melody.contour_variety: 0.8
melody.chord_tone_targeting: 0.9
harmony.consonance_ratio: 1.0
harmony.voice_leading: 0.5
rhythm.groove_consistency: 1.3
rhythm.backbeat_strength: 1.5
arrangement.texture_density_evolution: 1.2

## Default Trajectories
```yaml
trajectories:
  tension:
    type: arc
    sections: { intro: 0.3, verse_1: 0.4, pre_chorus: 0.6, chorus_1: 0.85, verse_2: 0.45, chorus_2: 0.9, bridge: 0.7, chorus_3: 0.95, outro: 0.5 }
  density:
    type: arc
    sections: { intro: 0.4, verse_1: 0.5, pre_chorus: 0.6, chorus_1: 0.8, verse_2: 0.5, chorus_2: 0.85, bridge: 0.6, chorus_3: 0.9, outro: 0.4 }
```

## Tempo
- Range: 100-160 BPM
- Sweet spot: 115-135 BPM (energetic without rushing)
- Slow rock / power ballad: 70-100 BPM
- Punk-adjacent: 160-200 BPM
- Time feel: straight, driving, locked to grid more than jazz

## Key Preferences
- E major/minor (open guitar strings, natural resonance)
- A major/minor (standard guitar key)
- G major, D major (open chord friendly)
- Drop-D tuning pieces center on D
- Minor keys for darker, heavier material
- Pentatonic and blues scale vocabulary regardless of key

## Drum Pattern Family
- Default: rock_straight_8th
- Snare: beats 2 and 4, no exceptions for standard rock
- Kick: variable, from four-on-the-floor to syncopated patterns
- Hi-hat: straight eighths, open on & of 4 for drive
- Crash: section downbeats
- Toms: used in fills, especially descending patterns at transitions
- Ride cymbal: used in verses for lower intensity

## Instrumentation Defaults
- Core: electric_guitar_distorted (riffs and power chords), electric_bass_pick, drums
- Melody: vocals (primary), lead_guitar (solos and hooks)
- Common additions: rhythm_guitar (second guitar), keyboard/organ (textural)
- Avoid: orchestral_strings (unless epic rock), synth_lead, vibraphone, acoustic_bass, brushes

## Section Structure
- Intro: 4-8 bars, guitar riff or drum count-in
- Verse: 8-16 bars, lower intensity, vocal melody with guitar riff underneath
- Pre-Chorus: 4-8 bars, building tension (harmonic departure, rising energy)
- Chorus: 8-16 bars, maximum energy, hook-driven, full band
- Bridge: 8 bars, contrasting section (different key, texture, or rhythm)
- Solo: 8-16 bars, guitar solo over verse or chorus changes
- Outro: 4-16 bars, fade-out, riff repeat, or hard ending

## Trajectory Patterns
- Classic Verse-Chorus: tension 0.3 -> 0.4 -> 0.6 -> 0.85 -> 0.4 -> 0.9 -> 0.5
- Slow Build: tension 0.2 -> 0.3 -> 0.5 -> 0.7 -> 0.85 -> 0.95 -> 0.4
- Punk Energy: tension 0.7 -> 0.8 -> 0.85 -> 0.9 -> 0.8 -> 0.9

## Cadences
- V-I (authentic cadence, standard rock resolution)
- bVII-I (mixolydian resolution, very common)
- IV-I (plagal, "amen" cadence, used in endings)
- bVI-bVII-I (aeolian approach, epic rock resolution)
- Riff-based endings (the riff is the cadence)

## Cliches to AVOID
- Swing feel or jazz timing (rock is straight)
- Extended jazz voicings (keep chords simple and powerful)
- Walking bass (use riff-based or root-fifth bass lines)
- Sparse, quiet dynamics throughout (rock needs energy and punch)
- Overly complex arrangements (clarity and power over sophistication)
- Missing the backbeat (snare on 2 and 4 is the genre's pulse)
- Severity: HIGH = no backbeat, swing feel; MEDIUM = jazz harmony, sparse dynamics
- Fix recipe: add distortion, lock snare to 2 and 4, simplify chord voicings to triads/power chords

## Quality Heuristics
- Guitar: power chords (root-5th-octave) or open chords; distortion level appropriate to sub-genre
- Bass: locked with kick drum, root-based with occasional fills
- Drums: tight, punchy, snare crack on 2 and 4
- Melody: pentatonic-based, syllabic, hook-oriented
- Velocity: high overall (75-120), with accent patterns on downbeats
- Dynamics: contrast between verse (moderate) and chorus (loud)
- Energy: should feel physical and driving

## Production Notes
- Target loudness: -12 to -9 LUFS (loud, compressed, punchy)
- Guitar: panned wide (rhythm L/R), lead center
- Bass: center, compressed, locked with kick
- Drums: natural stereo image, compressed bus
- Reverb: short-to-medium on snare and vocals; dry guitars
- Stereo width: wide in chorus, narrower in verse for contrast

## References
- Everett, Walter. *The Foundations of Rock*. Oxford University Press, 2009.
- Temperley, David. *The Musical Language of Rock*. Oxford University Press, 2018.
- Moore, Allan F. *Rock: The Primary Text*. Ashgate, 2001.
- Covach, John and Andrew Flory. *What's That Sound? An Introduction to Rock and Its History*. Norton, 2018.

## Use Cases
- High-energy scenes in film and games
- Workout and exercise playlists
- Driving and road trip music
- Stadium and arena atmosphere
- Emotional intensity and catharsis
