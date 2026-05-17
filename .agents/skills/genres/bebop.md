---
genre_id: bebop
display_name: "Bebop"
parent_genres: [jazz, swing]
related_genres: [hard_bop, cool_jazz, post_bop, jazz]
typical_use_cases: [jazz_performance, virtuosic_showcase, jazz_education, film_scoring]
ensemble_template: custom
default_subagents:
  active: [composer, rhythm_architect, harmony_theorist, mix_engineer, adversarial_critic, producer]
  inactive: [beatmaker, sound_designer, loop_architect]
---

# Bebop — Genre Skill

## Defining Characteristics
- Tempo: 180-320 BPM (sweet spot 220-280; slow bebop ballads 120-160 with double-time feel)
- Fast swing feel with driving ride cymbal and walking bass
- Harmonically dense: rapid ii-V progressions, chromatic substitutions, altered dominants
- Bebop scales: the major bebop scale adds a passing chromatic tone between scale degrees 5 and 6; the dominant bebop scale adds a passing tone between 7 and 8
- Long, flowing eighth-note lines with chromatic enclosures and arpeggiated chord tones
- Small combo format: typically 4-5 players (horn, piano, bass, drums, optional second horn)
- Head-solos-head structure with extended improvisation over the form
- Comping is interactive and conversational, not metronomic
- Rhythmic sophistication: accents on upbeats, across-the-bar phrasing, metric displacement

## Required Spec Patterns
```yaml
tempo_bpm: 240
time_signature: "4/4"
swing: 0.62
instruments:
  - name: trumpet
    role: melody
  - name: alto_sax
    role: melody
  - name: piano
    role: harmony
  - name: acoustic_bass
    role: bass
  - name: drums
    role: rhythm
generation:
  strategy: phrase_aware
  temperature: 0.6
features:
  chord_aware_melody: true
  voice_leading_optimization: true
```

## Idiomatic Chord Progressions
- ii7-V7-Imaj7 (the fundamental unit, ~30%)
- iii7-VI7-ii7-V7-Imaj7 (extended approach, ~15%)
- ii7-bII7-Imaj7 (tritone substitution, ~12%)
- Imaj7-#Idim7-ii7-V7 (chromatic connector, ~10%)
- Rhythm changes: Imaj7-vi7-ii7-V7 | I7-vi7-ii7-V7 | iii7-VI7-ii7-V7 | iii7-VI7-ii7-V7 (A section, ~10%)
- Rhythm changes bridge: III7-III7-VI7-VI7-II7-II7-V7-V7 (~8%)
- I7-IV7-#IVdim7-I7-VI7alt-ii7-V7alt-I7 (bird blues, ~8%)
- Back-cycling: iii7-VI7-ii7-V7-Imaj7 in rapid harmonic rhythm (~7%)

## Idiomatic Rhythms
```
RIDE:   X . x . X . x . X . x . X . x .
HIHAT:  . . . . F . . . . . . . F . . .
KICK:   x . . . . . . . x . . . . . . .
SNARE:  . . . x . . . . . . x . . . . x
```
- Ride cymbal: driving swing pattern, consistent quarter-note pulse with swung skip beats
- Hi-hat: foot on 2 and 4 (essential)
- Kick: light feathering on all four beats, or sparse accents ("dropping bombs")
- Snare: interactive comping, responding to soloist with accents and "kicks"
- Tempo is fast; the ride carries the time while snare and kick comp freely

## Anti-Patterns
- Simple triads (bebop demands 7ths minimum, plus extensions and alterations)
- Straight eighth notes (swing is non-negotiable, even at extreme tempos)
- Block chord comping on every beat (comping must be rhythmically varied and interactive)
- Slow, sustained melodic lines (bebop melodies are fast, flowing eighth-note runs)
- Root-position voicings (rootless voicings are standard; the bass provides the root)
- Predictable four-bar phrase boundaries (bebop phrases cross bar lines and play with metric expectation)
- Simple pentatonic melodies (bebop uses chromatic enclosures, bebop scales, and arpeggios)
- Loud, heavy drumming (bebop drumming is light, conversational, ride-cymbal driven)
- Severity: HIGH for straight eighths, triad harmony, and heavy drums; MEDIUM for simple melodies and rigid phrasing

## Reference Tracks
- None yet (rights-cleared bebop references needed)

## Default Sound Design
```yaml
instruments:
  trumpet: { synthesis: { kind: sample_based, pack: "trumpet_jazz_bright" }, effect_chain: [{ type: reverb, room_size: 0.35, wet: 0.15 }] }
  alto_sax: { synthesis: { kind: sample_based, pack: "alto_sax_bright" }, effect_chain: [{ type: reverb, room_size: 0.35, wet: 0.15 }] }
  piano: { synthesis: { kind: sample_based, pack: "steinway_jazz" }, effect_chain: [{ type: eq, bands: [{ freq_hz: 250, gain_db: -2 }, { freq_hz: 3500, gain_db: 2 }] }] }
  acoustic_bass: { synthesis: { kind: sample_based, pack: "upright_bass_finger" }, effect_chain: [{ type: compressor, threshold_db: -18, ratio: 3 }] }
  drums: { synthesis: { kind: sample_based, pack: "bebop_kit_light" } }
```

## Evaluation Weight Adjustments
structure.section_contrast: 0.7
melody.contour_variety: 1.4
melody.chromatic_density: 1.5
melody.chord_tone_targeting: 1.6
harmony.consonance_ratio: 0.5
harmony.voice_leading: 1.5
harmony.chord_extension_density: 1.4
rhythm.groove_consistency: 1.0
rhythm.swing_accuracy: 1.5
rhythm.phrase_boundary_variety: 1.3

## Default Trajectories
```yaml
trajectories:
  tension:
    type: arc
    sections: { intro: 0.3, head_in: 0.5, solo_1: 0.6, solo_2: 0.75, solo_3: 0.85, trading_fours: 0.7, head_out: 0.5, coda: 0.3 }
  density:
    type: arc
    sections: { intro: 0.3, head_in: 0.5, solo_1: 0.6, solo_2: 0.7, solo_3: 0.8, trading_fours: 0.7, head_out: 0.5, coda: 0.3 }
```

## Tempo
- Range: 180-320 BPM (up-tempo bebop)
- Sweet spot: 220-280 BPM (the characteristic breakneck pace)
- Medium bebop: 160-200 BPM
- Bebop ballads: 60-80 BPM with double-time passages (effectively 120-160)
- Time feel: swing, with the ride cymbal driving at high speed

## Key Preferences
- Bb major (standard horn key, rhythm changes)
- F major, Eb major (alto sax and trumpet friendly)
- Ab major (common contrafact key)
- C minor, G minor (minor key bebop)
- Frequent modulation through ii-V chains to remote tonal centers
- Rapidly shifting tonal centers within a single chorus

## Drum Pattern Family
- Default: bebop_ride_driven
- Ride cymbal: the primary voice, steady swing pattern at tempo
- Hi-hat: foot pedal on 2 and 4, crisp and consistent
- Kick: feathered four-on-the-floor (barely audible) or "bombs" (accent drops)
- Snare: comping tool, not timekeeping; responds to and pushes the soloist
- The drum set is a melodic, interactive instrument in bebop, not a metronome

## Instrumentation Defaults
- Core: piano (rootless voicings, comping), acoustic_bass (walking lines at tempo), drums (ride-based)
- Melody: trumpet, alto_sax (the classic bebop front line)
- Common additions: tenor_sax, trombone (as second or third horn)
- Avoid: synth instruments, electric bass, drum machine, guitar (uncommon in classic bebop), strings, sustained pads

## Section Structure
- Intro: 4-8 bars, piano or drum vamp, or rubato horn
- Head In: 32 bars (AABA or ABAC form), melody stated in unison by horns
- Solo Choruses: 2-6 choruses per soloist (32 bars each), improvising over the changes
- Trading: 4-bar or 8-bar exchanges between soloists and drums ("trading fours")
- Head Out: 32 bars, melody restated, often with coda tag
- Coda: 2-8 bars, tag ending, often the last 4 bars of the tune repeated with ritardando

## Trajectory Patterns
- Classic Bebop: tension 0.3 -> 0.5 -> 0.7 -> 0.85 -> 0.7 -> 0.5 -> 0.3
- Burning Session: tension 0.5 -> 0.7 -> 0.85 -> 0.95 -> 0.8 -> 0.5
- Trading Build: tension 0.4 -> 0.6 -> 0.7 -> 0.8 (trading) -> 0.5 -> 0.3

## Cadences
- ii7-V7-Imaj7 (standard, but often altered: ii7-V7alt-Imaj7)
- ii7-bII7-Imaj7 (tritone substitution)
- iii7-VI7alt-ii7-V7-I (long cadential approach)
- Deceptive: ii7-V7-iii7 or ii7-V7-bVImaj7 (extending the solo)
- Tag endings: repeating the final ii-V-I with decreasing intensity
- Turnaround: I-vi-ii-V leading back to the top of the form

## Cliches to AVOID
- Triads or simple chord voicings (extensions and alterations are mandatory)
- Straight eighth notes at any tempo (swing is the rhythmic identity)
- Root-position piano voicings (rootless and shell voicings are the norm)
- Metronomic comping on every beat (comping is conversational and irregular)
- Simple pentatonic melodies (bebop demands chromaticism, enclosures, and arpeggiation)
- Predictable phrase lengths (phrases should cross bar lines and challenge metric expectations)
- Heavy, loud drumming (light touch is essential at bebop tempos)
- Slow, sustained melodic phrasing (eighth-note runs are the melodic currency)
- Severity: HIGH = straight eighths, triad harmony, heavy drumming; MEDIUM = simple melodies, rigid 4-bar phrasing
- Fix recipe: add swing, use rootless voicings with extensions, write flowing eighth-note lines with chromatic enclosures, make drumming ride-cymbal driven with comping snare

## Quality Heuristics
- Melody: continuous eighth-note lines with chromatic enclosures, targeting chord tones on strong beats
- Bebop scales: major bebop (added b6), dominant bebop (added natural 7) for continuous eighth-note flow
- Harmony: rapidly moving ii-V-Is, tritone substitutions, altered dominants (b9, #9, #11, b13)
- Piano: rootless voicings (LH) with melodic lines (RH); comping rhythm irregular and interactive
- Bass: walking quarter notes, chromatic approaches, strong beat-1 arrivals
- Drums: ride cymbal is the engine; snare and kick are conversational accents
- Velocity: moderate overall (60-95), with phrase-level dynamic contour
- Swing ratio: 0.58-0.65 (at fast tempos, swing ratio naturally approaches even eighths)
- Phrase structure: asymmetric, crossing bar lines, building in intensity across a solo

## Production Notes
- Target loudness: -18 to -14 LUFS (natural, dynamic, uncompressed)
- Minimal processing: the sound is the instrument in the room
- Reverb: small club or studio room, minimal (presence, not wash)
- Stereo: piano slightly left, bass center, drums slightly right, horns center
- No compression on drums (natural dynamics are essential)
- EQ: minimal; just enough to prevent masking between instruments
- The aesthetic is live performance, not studio production

## References
- DeVeaux, Scott. *The Birth of Bebop: A Social and Musical History*. University of California Press, 1997.
- Owens, Thomas. *Bebop: The Music and Its Players*. Oxford University Press, 1995.
- Koch, Lawrence O. *Yardbird Suite: A Compendium of the Music and Life of Charlie Parker*. Bowling Green State University Popular Press, 1999.
- Baker, David. *The Jazz Style of Clifford Brown*. Alfred Music, 1982.
- Levine, Mark. *The Jazz Theory Book*. Sher Music, 1995 (bebop harmony chapters).

## Use Cases
- Jazz performance and concert simulation
- Virtuosic instrumental showcase
- Jazz education and pedagogical examples
- Film scoring for mid-century and urban settings
- Advanced harmony study and contrafact generation
