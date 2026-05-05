---
genre_id: ambient
display_name: "Ambient"
parent_genres: [electronic, experimental]
related_genres: [drone, dark_ambient, new_age, soundscape]
typical_use_cases: [meditation, relaxation, art_installation, focus_music]
ensemble_template: ambient_solo
default_subagents:
  active: [texture_composer, sound_designer, mix_engineer, adversarial_critic, producer]
  inactive: [composer, harmony_theorist, rhythm_architect, beatmaker, loop_architect]
---

# Ambient — Genre Skill

## Defining Characteristics
- Tempo: 60-90 BPM (often felt rather than metronomic, or free time)
- Extremely sparse note density (1-4 notes sounding at any time)
- Long sustained tones (whole notes or longer, tied across bars)
- Very low velocity range (30-70, rarely above)
- Wide register spacing between voices (3+ octaves open voicings)
- Harmonic rhythm: one chord per 4-16 bars
- Slow attack and very long release envelopes
- Silence and space are compositional elements
- Textural variety through timbre, not rhythm or melody
- No traditional section boundaries; pieces evolve gradually

## Required Spec Patterns
```yaml
tempo_bpm: 72
time_signature: "4/4"  # or "free"
instruments:
  - name: synth_pad_warm
    role: pad
  - name: piano
    role: melody
  - name: strings_ensemble
    role: pad
generation:
  strategy: stochastic
  temperature: 0.2
```

## Idiomatic Chord Progressions
- Imaj7 sustained (single chord drone, ~30%)
- Imaj7-IVmaj7 (two-chord float, ~25%)
- Imaj7-IImaj7 (Lydian parallel movement, ~15%)
- i7-bVII7 (modal minor drift, ~15%)
- Imaj9-vi9-IVmaj9-Imaj9 (slow cycle, ~10%)

## Idiomatic Rhythms
- No rhythmic patterns; ambient avoids regular pulse
- Attacks should be spread irregularly
- Ghost-note texture only if any percussion is present

## Anti-Patterns
- Strong rhythmic patterns or beats (destroys the ambient quality)
- Short staccato notes (ambient requires sustained, evolving tones)
- Rapid harmonic rhythm (chords should last 4-16 bars minimum)
- Loud dynamics above mp (ambient lives in ppp to mp; mf is a climax)
- Melodic themes with clear contour (fragments, not melodies)
- Sudden changes in texture or dynamics (everything must be gradual)
- Drum kit patterns of any kind
- Bright brass or woodwind instruments

## Reference Tracks
- None yet (rights-cleared ambient references needed)

## Default Sound Design
```yaml
instruments:
  synth_pad_warm: { synthesis: { kind: subtractive, filter_cutoff_lfo_hz: 0.05 } }
  piano: { synthesis: { kind: sample_based, pack: "felt_piano_close_mic" }, effect_chain: [{ type: reverb, wet: 0.6 }] }
  strings_ensemble: { synthesis: { kind: sample_based, pack: "orchestral_strings" }, effect_chain: [{ type: reverb, wet: 0.7 }] }
```

## Evaluation Weight Adjustments
structure.section_contrast: 0.3
melody.contour_variety: 0.3
melody.stepwise_motion_ratio: 0.3
harmony.consonance_ratio: 0.8
harmony.pitch_class_variety: 0.3
rhythm.groove_consistency: 0.1
arrangement.texture_density_evolution: 1.5

## Default Trajectories
```yaml
trajectories:
  tension:
    type: bezier
    waypoints: [[0, 0.05], [0.3, 0.15], [0.6, 0.25], [0.85, 0.35], [1.0, 0.1]]
  density:
    type: bezier
    waypoints: [[0, 0.1], [0.4, 0.2], [0.7, 0.3], [1.0, 0.1]]
```

## Tempo
- Range: 60-90 BPM (often felt rather than metronomic)
- Sweet spot: 70-80 BPM or free time
- Pulse should be obscured; avoid strong downbeats
- Rubato and gradual tempo drift are desirable, not errors

## Key Preferences
- C major / A minor (neutral canvas)
- G major (open, natural), D major (warm, luminous)
- Lydian mode preferred over standard major (the raised 4th adds floating quality)
- Dorian for darker ambient (the raised 6th avoids heaviness of pure minor)
- Key center should be implied, not asserted; avoid strong tonal gravity

## Iconic Chord Progressions (frequency-ranked)
1. Imaj7 sustained (single chord drone, ~30%)
2. Imaj7-IVmaj7 (two-chord float, ~25%)
3. Imaj7-IImaj7 (Lydian parallel movement, ~15%)
4. i7-bVII7 (modal minor drift, ~15%)
5. Imaj9-vi9-IVmaj9-Imaj9 (slow cycle, ~10%)

## Drum Pattern Family
- Default: null (no drums)
- Percussion is antithetical to most ambient
- If texture is needed, use sustained pad swells or filtered noise
- Exception: dark ambient may use sparse, processed kick hits at very low volume

## Instrumentation Defaults
- Core: synth_pad_warm (foundation), piano (sparse melodic fragments), strings_ensemble (sustained texture)
- Common additions: cello (solo lyrical lines), vibraphone (bell-like accents)
- Harp for slow arpeggiated washes
- Avoid: all percussion, brass, staccato instruments, anything bright or cutting

## Section Structure
- Ambient pieces often lack traditional sections
- Opening: 8-16 bars, single pad or drone establishing tonal center
- Evolution A: 16-32 bars, gradual layering of textures
- Evolution B: 16-32 bars, subtle harmonic shift or new timbral element
- Dissolution: 8-16 bars, layers thin, return to near-silence
- Total duration: often 4-10 minutes; shorter pieces feel incomplete

## Trajectory Patterns
- Drift: tension 0.1 -> 0.15 -> 0.2 -> 0.15 -> 0.1
- Slow Bloom: tension 0.05 -> 0.1 -> 0.25 -> 0.35 -> 0.1
- Deep Meditation: tension 0.05 throughout (nearly flat)

## Cadences
- Avoid traditional cadences entirely
- Chord changes should overlap (crossfade, not cut)
- Resolution happens through thinning of texture, not harmonic motion
- If a cadence must occur, plagal (IV-I) is the least intrusive

## Cliches to AVOID
- Strong rhythmic patterns or beats (destroys the ambient quality)
- Short staccato notes (ambient requires sustained, evolving tones)
- Rapid harmonic rhythm (chords should last 4-16 bars minimum)
- Loud dynamics (ambient lives in ppp to mp; mf is a climax)
- Melodic themes with clear contour (fragments, not melodies)
- Sudden changes in texture or dynamics (everything must be gradual)

## Quality Heuristics
- Note density: extremely sparse (1-4 notes sounding at any time)
- Note duration: long (whole notes, tied across bars, or longer)
- Velocity: low and narrow range (30-70, rarely above)
- Register: wide spacing between voices (open voicings spanning 3+ octaves)
- Harmonic rhythm: one chord per 4-16 bars
- Dynamic envelope: attack should be slow (fade in), release very long
- Silence and space are compositional elements, not gaps to fill
- Textural variety through timbre, not rhythm or melody

## Use Cases
- Meditation and mindfulness apps
- Sleep and relaxation playlists
- Art installations and gallery spaces
- Film/game environmental soundscapes
- Focus music (even more background than lo-fi)
