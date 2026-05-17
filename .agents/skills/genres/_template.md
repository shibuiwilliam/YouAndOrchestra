---
genre_id: <snake_case_id>
display_name: "<Human Readable Name>"
parent_genres: [<parent1>, <parent2>]
related_genres: [<related1>, <related2>]
typical_use_cases: [<use1>, <use2>]
ensemble_template: <classical_chamber | hip_hop_producer | ambient_solo | custom>
default_subagents:
  active: [<subagent1>, <subagent2>, ...]
  inactive: [<subagent1>, <subagent2>, ...]
---

## Defining Characteristics
- (bullet list of canonical features that define this genre)

## Required Spec Patterns
(YAML fragment of expected composition.yaml settings for this genre)

## Idiomatic Chord Progressions
- (list with Roman-numeral notation; or modal cells, or sample-based notation)

## Idiomatic Rhythms
(ASCII drum-grid notation or rhythm description)

## Anti-Patterns
(used by Adversarial Critic — what would break the genre frame)

## Reference Tracks
(rights-cleared MIDI/MusicXML in references/ — or "none yet")

## Default Sound Design
(YAML fragment of sound_design.yaml defaults for this genre)

## Evaluation Weight Adjustments
(multipliers applied to base evaluator weights)

## Default Trajectories
(YAML fragment of trajectory.yaml defaults for this genre)
