---
genre_id: pop_japan
display_name: "J-Pop"
parent_genres: [pop, east_asian_pop]
related_genres: [kpop, city_pop, anime_ost, jpop_rock]
typical_use_cases: [vocal_pop, anime_theme, commercial_jingle, idol_music]
ensemble_template: classical_chamber
default_subagents:
  active: [composer, harmony_theorist, orchestrator, mix_engineer, adversarial_critic, producer]
  inactive: [texture_composer, sample_curator]
---

# J-Pop — Genre Skill

## Defining Characteristics
- Tempo: 120-180 BPM (ballads 70-100)
- Complex song structure: verse / pre-chorus / chorus / D-melody (unique bridge)
- Frequent key changes (modulation up a half-step or whole-step at final chorus)
- Rich chord progressions with secondary dominants and borrowed chords
- Melody-first composition with wide vocal range
- Strong hooks in chorus (memorable within 1-2 listens)
- Mix of Western harmony and pentatonic-influenced melody

## Required Spec Patterns
```yaml
tempo_bpm: 140
time_signature: "4/4"
instruments:
  - name: piano
    role: harmony
  - name: electric_guitar_clean
    role: counter_melody
  - name: electric_bass_finger
    role: bass
  - name: drums
    role: rhythm
  - name: strings_ensemble
    role: pad
sections:
  - name: intro
    bars: 4
  - name: verse
    bars: 16
  - name: pre_chorus
    bars: 8
  - name: chorus
    bars: 16
  - name: d_melody
    bars: 8
  - name: final_chorus
    bars: 16
```

## Idiomatic Chord Progressions
- IV-V-iii-vi (royal road progression, ~30%)
- I-V-vi-IV (canon progression, ~20%)
- vi-IV-V-I (dramatic minor start, ~15%)
- IV-V-vi-I-IV-V-I (extended cadential, ~10%)
- IVmaj7-V7-iii7-vi7 (city pop jazzy variant, ~10%)
- bVI-bVII-I (borrowed chord climax approach)

## Idiomatic Rhythms
```
KICK:  X . . . X . . . X . . . X . . .
SNARE: . . . . X . . . . . . . X . . .
HAT:   X X X X X X X X X X X X X X X X
```
- Straight 8ths or 16ths, minimal swing
- Fills at section boundaries
- Syncopated bass patterns in chorus

## Anti-Patterns
- Monotone melody (J-pop requires wide melodic range)
- Simple 4-chord loops without development (too repetitive for J-pop form)
- Tempo below 110 for non-ballads (loses energy)
- Missing pre-chorus (structurally expected in J-pop)
- No key change or harmonic surprise (predictable = boring in J-pop context)
- Overuse of power chords (too rock for J-pop aesthetic)

## Reference Tracks
- None yet (rights-cleared J-pop references needed)

## Default Sound Design
```yaml
instruments:
  piano: { synthesis: { kind: sample_based, pack: "bright_grand" } }
  electric_guitar_clean: { synthesis: { kind: sample_based, pack: "strat_clean" } }
  strings_ensemble: { synthesis: { kind: sample_based, pack: "pop_strings" } }
  drums: { synthesis: { kind: sample_based, pack: "pop_kit_bright" } }
```

## Evaluation Weight Adjustments
structure.section_contrast: 1.3
melody.contour_variety: 1.4
melody.motif_recall_strength: 1.3
harmony.consonance_ratio: 0.8
harmony.pitch_class_variety: 1.2
rhythm.groove_consistency: 1.0

## Default Trajectories
```yaml
trajectories:
  tension:
    type: stepped
    sections: { intro: 0.2, verse: 0.4, pre_chorus: 0.6, chorus: 0.85, d_melody: 0.5, final_chorus: 0.95 }
  density:
    type: stepped
    sections: { intro: 0.3, verse: 0.5, pre_chorus: 0.65, chorus: 0.85, d_melody: 0.4, final_chorus: 0.9 }
```
