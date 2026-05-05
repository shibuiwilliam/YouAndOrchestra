---
genre_id: lo_fi_hiphop
display_name: "Lo-fi Hip Hop"
parent_genres: [hip_hop, jazz]
related_genres: [chillhop, boom_bap, jazzhop]
typical_use_cases: [study_focus, relaxation, cafe_atmosphere, late_night_coding]
ensemble_template: hip_hop_producer
default_subagents:
  active: [beatmaker, sound_designer, loop_architect, mix_engineer, adversarial_critic, producer]
  inactive: [composer, rhythm_architect]
---

# Lo-fi Hip Hop — Genre Skill

## Defining Characteristics
- Tempo: 70-95 BPM (sweet spot 80-85)
- Laid-back groove with humanized timing (kick slightly behind grid)
- Jazz-influenced chord voicings (7ths, 9ths)
- Lo-fi production aesthetic (tape saturation, vinyl crackle, bit reduction)
- Loop-based structure with textural variation
- Sparse density; fewer notes is better
- Low velocity range (50-85)
- Swung 8th notes (0.55-0.65 swing ratio)
- Close-position chord voicings in mid-register (C3-C5)

## Required Spec Patterns
```yaml
tempo_bpm: 82
time_signature: "4/4"
instruments:
  - name: electric_piano
    role: harmony
  - name: electric_bass_finger
    role: bass
  - name: drums
    role: rhythm
generation:
  strategy: loop_evolution
  temperature: 0.3
```

## Idiomatic Chord Progressions
- ii7-V7-Imaj7 (jazz turnaround, ~30%)
- i7-iv7-VII7-III7 (minor jazz cycle, ~25%)
- Imaj7-vi7-ii7-V7 (smooth major, ~15%)
- i7-bVI7-bVII7-i7 (modal minor drift, ~15%)
- iv7-i7-V7-i7 (simple minor blues, ~10%)

## Idiomatic Rhythms
```
KICK:  X . . . . . X . . . X . . . . .
SNARE: . . . . X . . . . . . . X . . .
HAT:   . X . X . X . X . X . X . X . X
```
- Kick slightly behind grid (+10-20ms humanization)
- Swung hi-hats with ghost notes
- Side-chain ducking on kick is stylistic

## Anti-Patterns
- Perfect loop quantization (needs humanized timing)
- Clean, dry signal (lo-fi requires saturation, bit reduction, or tape emulation)
- Complex chord voicings above 4 notes (muddiness in lo-fi mix)
- Fast passages or virtuosic lines (antithetical to the aesthetic)
- Hard-panned stereo effects (lo-fi is centered and intimate)
- Loud dynamics above mf (the genre lives in pp-mp range)
- Strong authentic cadences V-I (too resolved for the drifting aesthetic)

## Reference Tracks
- None yet (rights-cleared lo-fi references needed)

## Default Sound Design
```yaml
instruments:
  electric_piano: { synthesis: { kind: sample_based, pack: "rhodes_mk1_tremolo" }, effect_chain: [{ type: tape_saturation, drive: 0.3 }, { type: eq, bands: [{ freq_hz: 8000, gain_db: -4 }] }] }
  electric_bass_finger: { synthesis: { kind: sample_based, pack: "jazz_bass_finger" } }
  drums: { synthesis: { kind: sample_based, pack: "vinyl_drums_dusty" }, effect_chain: [{ type: bitcrusher, bit_depth: 12 }] }
```

## Evaluation Weight Adjustments
structure.section_contrast: 0.4
melody.contour_variety: 0.5
harmony.consonance_ratio: 0.7
rhythm.groove_consistency: 1.5
arrangement.texture_density_evolution: 0.6

## Default Trajectories
```yaml
trajectories:
  tension:
    type: flat
    value: 0.2
  density:
    type: stepped
    sections: { intro: 0.3, loop_a: 0.5, loop_b: 0.55, outro: 0.3 }
```

## Tempo
- Range: 70-95 BPM
- Sweet spot: 80-85 BPM (relaxed groove without dragging)
- Never rush; the laid-back feel is the genre's identity

## Key Preferences
- A minor (warm, default), E minor (melancholic), D minor (jazzy)
- Dorian mode adds warmth via the raised 6th (e.g., Am Dorian with F#)
- Avoid bright major keys; even "happy" lo-fi stays in minor territory

## Iconic Chord Progressions (frequency-ranked)
1. ii7-V7-Imaj7 (jazz turnaround, ~30%)
2. i7-iv7-VII7-III7 (minor jazz cycle, ~25%)
3. Imaj7-vi7-ii7-V7 (smooth major, ~15%)
4. i7-bVI7-bVII7-i7 (modal minor drift, ~15%)
5. iv7-i7-V7-i7 (simple minor blues, ~10%)

## Drum Pattern Family
- Default: lofi_laidback
- Kick slightly behind the grid (humanization offset +10-20ms)
- Snare/rim shot on beats 2 and 4, often with vinyl crackle layer
- Hi-hat patterns: swung 8ths with ghost notes, occasional open hat
- Side-chain ducking on kick is stylistic, not optional

## Instrumentation Defaults
- Core: electric_piano (Rhodes/Wurlitzer voicings), piano, electric_bass_finger
- Common additions: acoustic_guitar_nylon (gentle arpeggios), vibraphone
- Texture: vinyl noise, tape hiss (production layer, not instrument)
- Avoid: bright synth leads, brass stabs, distorted guitar, piccolo

## Section Structure
- Intro: 4 bars, filtered chords fading in, minimal drums
- Loop A: 8-16 bars, main chord progression with full beat
- Loop B: 8-16 bars, variation (add melody sample or switch voicing)
- Outro: 4 bars, filter sweep out or tape stop effect
- Note: lo-fi tracks are loop-based; "sections" are textural shifts

## Trajectory Patterns
- Chill Study: tension 0.2 throughout (minimal arc)
- Late Night: tension 0.15 -> 0.3 -> 0.2 -> 0.1
- Rainy Day: tension 0.25 -> 0.35 -> 0.25

## Cadences
- Avoid strong authentic cadences (V-I feels too resolved)
- ii7-V7 left unresolved is idiomatic
- Plagal motion (IV-I or iv-i) for gentle phrase endings
- Deceptive resolution (V7 to vi or bVI) to maintain drift

## Cliches to AVOID
- Perfect loop quantization (needs humanized timing)
- Clean, dry signal (lo-fi requires saturation, bit reduction, or tape emulation)
- Complex chord voicings above 4 notes (muddiness in lo-fi mix)
- Fast passages or virtuosic lines (antithetical to the aesthetic)
- Hard-panned stereo effects (lo-fi is centered and intimate)
- Loud dynamics above mf (the genre lives in pp-mp range)

## Quality Heuristics
- Velocity should be low and consistent (50-85 range, narrow spread)
- Swing must be audible but not exaggerated (0.55-0.65)
- Chord voicings: close position, mid-register (C3-C5 range)
- Bass: simple root-fifth patterns, occasional chromatic approach
- Overall density: sparse; fewer notes is almost always better
- Repetition is a feature, not a flaw

## Use Cases
- Study/focus playlists
- Relaxation and ambient background
- Cafe atmosphere
- Late-night coding sessions
