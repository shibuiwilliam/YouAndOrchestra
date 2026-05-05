---
genre_id: pop_western
display_name: "Western Pop"
parent_genres: [pop]
related_genres: [indie_pop, synth_pop, dance_pop, power_pop]
typical_use_cases: [radio_single, streaming_playlist, commercial_sync, cover_song]
ensemble_template: classical_chamber
default_subagents:
  active: [composer, harmony_theorist, orchestrator, mix_engineer, adversarial_critic, producer]
  inactive: [texture_composer, sample_curator]
---

# Western Pop — Genre Skill

## Defining Characteristics
- Tempo: 100-130 BPM (ballads 60-90)
- Verse-chorus structure with strong hooks
- Simple, memorable melodies with repetition
- 4-chord progressions dominate (I-V-vi-IV, vi-IV-I-V, etc.)
- Production-forward sound (layered vocals, synth pads, programmed drums)
- Clear frequency separation between instruments
- Vocal-centric (melody designed for singability)

## Required Spec Patterns
```yaml
tempo_bpm: 120
time_signature: "4/4"
instruments:
  - name: piano
    role: harmony
  - name: electric_bass_finger
    role: bass
  - name: drums
    role: rhythm
  - name: synth_pad_warm
    role: pad
sections:
  - name: intro
    bars: 4
  - name: verse
    bars: 8
  - name: pre_chorus
    bars: 4
  - name: chorus
    bars: 8
  - name: verse_2
    bars: 8
  - name: chorus_2
    bars: 8
  - name: bridge
    bars: 8
  - name: final_chorus
    bars: 8
```

## Idiomatic Chord Progressions
- I-V-vi-IV (axis of awesome, ~35%)
- vi-IV-I-V (sensitive female chord progression, ~20%)
- I-IV-vi-V (optimistic pop, ~15%)
- I-vi-IV-V (50s progression modernized, ~10%)
- IV-I-V-vi (starting on IV for lift, ~10%)

## Idiomatic Rhythms
```
KICK:  X . . . X . . . X . . . X . . .
SNARE: . . . . X . . . . . . . X . . .
HAT:   X . X . X . X . X . X . X . X .
```
- Four-on-the-floor or standard pop backbeat
- Minimal syncopation in drums
- Bass follows kick pattern closely

## Anti-Patterns
- Complex time signatures (pop = 4/4 almost exclusively)
- Jazz chord extensions beyond 7ths (too complex for pop clarity)
- Melody with range > 1.5 octaves (singability constraint)
- Sections longer than 16 bars without repetition (attention span)
- Missing hook/chorus (pop demands a memorable refrain)
- Absence of repetition (pop thrives on familiarity)
- Tempo > 140 BPM for non-dance pop (too fast for vocal pop)

## Reference Tracks
- None yet (rights-cleared pop references needed)

## Default Sound Design
```yaml
instruments:
  piano: { synthesis: { kind: sample_based, pack: "pop_piano_bright" } }
  synth_pad_warm: { synthesis: { kind: subtractive, oscillators: [{ wave: saw, detune_cents: 5 }], filter: { type: low_pass, cutoff_hz: 3000 } } }
  drums: { synthesis: { kind: sample_based, pack: "modern_pop_kit" } }
  electric_bass_finger: { synthesis: { kind: sample_based, pack: "pop_bass" } }
```

## Evaluation Weight Adjustments
structure.section_contrast: 1.2
melody.contour_variety: 1.0
melody.motif_recall_strength: 1.5
harmony.consonance_ratio: 1.2
harmony.pitch_class_variety: 0.7
rhythm.groove_consistency: 1.2

## Default Trajectories
```yaml
trajectories:
  tension:
    type: stepped
    sections: { intro: 0.2, verse: 0.4, pre_chorus: 0.6, chorus: 0.8, bridge: 0.5, final_chorus: 0.9 }
  density:
    type: stepped
    sections: { intro: 0.3, verse: 0.5, pre_chorus: 0.6, chorus: 0.8, bridge: 0.4, final_chorus: 0.85 }
```
