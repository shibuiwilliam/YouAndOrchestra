---
genre_id: cinematic
display_name: "Cinematic"
parent_genres: [orchestral, film_score]
related_genres: [epic_trailer, ambient, neoclassical]
typical_use_cases: [film_score, trailer, game_cutscene, advertisement]
ensemble_template: classical_chamber
default_subagents:
  active: [composer, harmony_theorist, orchestrator, mix_engineer, adversarial_critic, producer]
  inactive: [beatmaker, sample_curator, loop_architect]
---

## Defining Characteristics
- Tempo: 60-160 BPM (slow majestic 60-100, action 120-160)
- Wide dynamic range (pp to ff)
- Orchestral palette: strings, brass, piano, percussion
- Simple memorable motifs (singable themes)
- Gradual section transitions (no sudden cuts)
- Wide voicings spread across register
- Major-minor ambiguity is a strength

## Required Spec Patterns
```yaml
tempo_bpm: 80  # or 140 for action
time_signature: "4/4"
instruments:
  - name: strings_ensemble
    role: melody
  - name: french_horn
    role: counter_melody
  - name: piano
    role: harmony
  - name: cello
    role: bass
```

## Idiomatic Chord Progressions
- i-VI-III-VII (epic minor, ~35%)
- i-iv-VI-V (emotional minor, ~25%)
- I-V-vi-IV (heroic major, ~20%)
- i-i-iv-V (tension build, ~10%)
- V-vi (deceptive cadence for subverted expectation)

## Idiomatic Rhythms
- Orchestral percussion only (timpani rolls, cymbal swells)
- No drum kit patterns
- Legato string lines with sustained notes
- Horn stabs on downbeats for emphasis

## Anti-Patterns
- Rapid tempo changes (cinema needs steady pace for editing)
- Overly complex harmonies (clarity is paramount for emotional impact)
- Drum kit patterns (use timpani and orchestral percussion instead)
- Synth leads (breaks the orchestral illusion)
- Abrupt endings (cinematic music needs denouement)
- Staccato-only writing in strings (legato is the genre's voice)

## Reference Tracks
- None yet (rights-cleared orchestral references needed)

## Default Sound Design
```yaml
instruments:
  strings_ensemble: { synthesis: { kind: sample_based, pack: "orchestral_strings" } }
  french_horn: { synthesis: { kind: sample_based, pack: "orchestral_brass" } }
  piano: { synthesis: { kind: sample_based, pack: "concert_grand" } }
  timpani: { synthesis: { kind: sample_based, pack: "orchestral_percussion" } }
```

## Evaluation Weight Adjustments
structure.section_contrast: 1.3
melody.contour_variety: 1.2
melody.motif_recall_strength: 1.3
harmony.consonance_ratio: 1.0
rhythm.groove_consistency: 0.5
arrangement.texture_density_evolution: 1.4

## Default Trajectories
```yaml
trajectories:
  tension:
    type: bezier
    waypoints: [[0, 0.2], [0.3, 0.5], [0.7, 0.9], [1.0, 0.3]]
  density:
    type: stepped
    sections: { establishing: 0.2, build: 0.5, climax: 0.95, resolution: 0.3 }
```
