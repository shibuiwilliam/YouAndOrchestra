---
genre_id: hip_hop
display_name: "Hip Hop"
parent_genres: [funk, soul, rhythm_and_blues]
related_genres: [lo_fi_hiphop, trap, boom_bap, east_coast, west_coast, drill]
typical_use_cases: [beat_production, urban_scoring, energetic_scenes, commercial]
ensemble_template: hip_hop_producer
default_subagents:
  active: [beatmaker, sound_designer, loop_architect, mix_engineer, adversarial_critic, producer]
  inactive: [harmony_theorist, composer]
---

# Hip Hop — Genre Skill

## Defining Characteristics
- Tempo: 80-115 BPM (classic boom bap 85-100; modern trap 130-170 in half-time feel)
- Beat-driven: the drum pattern is the foundation and primary identity
- Sample-based or synthesized production with heavy emphasis on groove
- Strong kick-snare interplay, often with complex hi-hat patterns
- Bass-heavy mix with prominent sub-bass
- Loop-based structure with layered textures evolving over time
- Swing and humanization on some sub-genres (boom bap); quantized precision on others (trap)
- Melodic content secondary to rhythmic and textural content
- Four-bar and eight-bar loop units as the structural building blocks

## Required Spec Patterns
```yaml
tempo_bpm: 92
time_signature: "4/4"
swing: 0.0
instruments:
  - name: drums
    role: rhythm
  - name: synth_bass
    role: bass
  - name: sampler
    role: harmony
generation:
  strategy: loop_evolution
  temperature: 0.4
features:
  chord_aware_melody: false
  voice_leading_optimization: false
```

## Idiomatic Chord Progressions
- i-bVI-bVII-i (minor loop, ~25%)
- i-iv-bVII-bVI (dark minor cycle, ~20%)
- Imaj7-vi7-ii7-V7 (soul/jazz sample, ~15%)
- i-bIII-bVII-iv (modal minor, ~15%)
- Single chord vamp with textural variation (~10%)
- iv-i-V-i (minor blues feel, ~8%)
- Chromatic bass descent over pedal (~7%)

## Idiomatic Rhythms
### Boom Bap
```
KICK:   X . . . . . . X . . X . . . . .
SNARE:  . . . . X . . . . . . . X . . .
HIHAT:  X . X . X . X . X . X . X . X .
```
### Trap
```
KICK:   X . . . . . . . . . . . X . . .
SNARE:  . . . . . . . . X . . . . . . .
HIHAT:  X x X x X x X x X x X x X x X x
```
- Boom bap: swung, sample-based drums, kick-snare pocket
- Trap: rolling hi-hats (32nd notes), 808 sub-bass, sparse kick
- Hi-hat variations: open hats, rolls, pitch bends (trap)
- Side-chain compression common on bass from kick

## Anti-Patterns
- Live jazz drumming feel (hip hop drums are programmed, tight, and punchy)
- Extended chord voicings dominating the texture (harmony is backdrop, not feature)
- Acoustic bass (synth bass or sampled bass is the norm)
- Complex melodic development (loops and repetition are the aesthetic)
- Thin bass (sub-bass presence is non-negotiable)
- Clean, unprocessed sounds (hip hop production is heavily processed)
- Regular classical phrasing (hip hop phrases align with bar loops, not cadences)
- Severity: HIGH for thin bass and acoustic drums; MEDIUM for melodic complexity

## Reference Tracks
- None yet (rights-cleared hip hop references needed)

## Default Sound Design
```yaml
instruments:
  drums: { synthesis: { kind: sample_based, pack: "boom_bap_kit" }, effect_chain: [{ type: compressor, threshold_db: -8, ratio: 6 }, { type: eq, bands: [{ freq_hz: 60, gain_db: 3 }, { freq_hz: 5000, gain_db: 2 }] }] }
  synth_bass: { synthesis: { kind: subtractive, waveform: sine, filter_cutoff_hz: 200 }, effect_chain: [{ type: distortion, drive: 0.15 }, { type: compressor, threshold_db: -10, ratio: 5 }] }
  sampler: { synthesis: { kind: sample_based, pack: "vinyl_chops" }, effect_chain: [{ type: eq, bands: [{ freq_hz: 300, gain_db: -3 }, { freq_hz: 8000, gain_db: -2 }] }, { type: reverb, room_size: 0.3, wet: 0.15 }] }
```

## Evaluation Weight Adjustments
structure.section_contrast: 0.6
melody.contour_variety: 0.5
melody.chord_tone_targeting: 0.4
harmony.consonance_ratio: 0.7
rhythm.groove_consistency: 1.8
rhythm.kick_snare_pocket: 1.5
arrangement.texture_density_evolution: 1.0
bass.sub_presence: 1.5

## Default Trajectories
```yaml
trajectories:
  tension:
    type: stepped
    sections: { intro: 0.2, verse_1: 0.4, hook: 0.7, verse_2: 0.45, hook_2: 0.75, bridge: 0.5, hook_3: 0.8, outro: 0.3 }
  density:
    type: stepped
    sections: { intro: 0.3, verse_1: 0.5, hook: 0.7, verse_2: 0.55, hook_2: 0.75, bridge: 0.4, hook_3: 0.8, outro: 0.3 }
```

## Tempo
- Range: 80-115 BPM (boom bap, classic)
- Trap: 130-170 BPM (felt as half-time, so effectively 65-85 BPM feel)
- Sweet spot: 88-96 BPM (classic hip hop pocket)
- Drill: 140-145 BPM (half-time feel)
- Time feel: tight, programmed, either swung (boom bap) or straight (trap)

## Key Preferences
- C minor, D minor, G minor (dark, brooding)
- A minor, E minor (versatile minor keys)
- Minor keys dominate (~80% of hip hop production)
- Phrygian and aeolian modes for darker textures
- Major keys used for uplifting or nostalgic tracks

## Drum Pattern Family
- Default: boom_bap_classic or trap_808
- Boom bap: sampled breaks, swung feel, thick snare
- Trap: 808 patterns, rolling hi-hats, sparse kick, tuned 808 bass
- Kick: the anchor, often filtered and compressed
- Snare/Clap: beats 2 and 4, layered with clap samples
- Hi-hat: defines sub-genre (simple eighths = boom bap; rolling 32nds = trap)

## Instrumentation Defaults
- Core: drums (programmed kit), synth_bass or 808_bass, sampler (chops, pads, stabs)
- Melody: synth_lead (simple hooks), piano (sampled loops), vocal_chop
- Common additions: strings (sampled, dramatic), brass_stab, bell, pad
- Avoid: acoustic_bass, vibraphone, oboe, classical ensemble, brushed drums

## Section Structure
- Intro: 4-8 bars, beat builds in with filtered elements
- Verse: 16 bars, full beat with vocal space (melodic interest in the beat)
- Hook/Chorus: 8 bars, catchiest element, maximum energy
- Verse 2: 16 bars, same beat or slight variation
- Bridge: 8 bars, breakdown or stripped section (optional)
- Hook: 8 bars, repeat with potential additions
- Outro: 4-8 bars, beat stripped down, elements removed

## Trajectory Patterns
- Classic Hip Hop: tension 0.2 -> 0.4 -> 0.7 -> 0.45 -> 0.75 -> 0.8 -> 0.3
- Trap Build: tension 0.3 -> 0.5 -> 0.7 -> 0.85 -> 0.5 -> 0.9 -> 0.4
- Boom Bap Steady: tension 0.4 -> 0.5 -> 0.6 -> 0.5 -> 0.65 -> 0.4

## Cadences
- Loop-based resolution (the loop repeating IS the cadence)
- i-bVII-bVI descent for phrase endings
- Drum break or drop as structural punctuation
- Sub-bass drop as arrival point
- No traditional cadential patterns (V-I is foreign to hip hop)

## Cliches to AVOID
- Live acoustic drum sounds (programmed, punchy drums are the standard)
- Thin, bass-light mixes (sub-bass is mandatory)
- Complex melodic development and counterpoint (simplicity and repetition are strengths)
- Classical voice leading concerns (parallel motion is fine)
- Swing feel in trap beats (trap is quantized and precise)
- Overly clean production without texture (vinyl noise, saturation, and character are valued)
- Severity: HIGH = no sub-bass, acoustic drums; MEDIUM = complex harmony, too clean
- Fix recipe: add 808 or sub-bass, program drums with appropriate samples, simplify harmony to 2-4 chord loop, add texture and saturation

## Quality Heuristics
- Drums: punchy, present, defining the groove; kick and snare must cut through
- Bass: sub-bass felt physically; 808s tuned to key
- Harmony: simple loops, often sampled; serves as backdrop
- Melody: hooks are short, repetitive, memorable
- Velocity: high on kicks and snares (90-127), varied on hi-hats for groove
- Production: layered, textured, processed; nothing sounds "raw" or "natural"
- Space: leave room for vocals in the mix (mid-range carve)

## Production Notes
- Target loudness: -8 to -6 LUFS (loud, competitive, impactful)
- Sub-bass: present and powerful, typically 30-60 Hz sine wave
- Kick and bass: side-chain compressed to avoid masking
- Stereo: drums center, pads and textures wide, bass mono below 100 Hz
- Effects: reverb on snare and vocals; delay on vocal hooks; saturation on master
- Mix: vocal-forward when present, beat-forward for instrumentals

## References
- Schloss, Joseph G. *Making Beats: The Art of Sample-Based Hip-Hop*. Wesleyan University Press, 2004.
- Katz, Mark. *Groove Music: The Art and Culture of the Hip-Hop DJ*. Oxford University Press, 2012.
- D'Errico, Mike. "Off the Grid: Instrumental Hip-Hop and Experimentalism After the Golden Age." In *The Cambridge Companion to Hip-Hop*, 2015.
- Williams, Justin A. *Rhymin' and Stealin': Musical Borrowing in Hip-Hop*. University of Michigan Press, 2013.

## Use Cases
- Beat production and instrumental hip hop
- Urban and street scene scoring
- Energetic commercial and advertising music
- Workout and sports playlists
- Background for spoken word and poetry
