---
genre_id: deep_house
display_name: "Deep House"
parent_genres: [house, electronic_dance]
related_genres: [tech_house, lo_fi_house, garage, soulful_house]
typical_use_cases: [club_dance, late_night_chill, gym_workout, poolside]
ensemble_template: hip_hop_producer
default_subagents:
  active: [sound_designer, beatmaker, loop_architect, mix_engineer, adversarial_critic, producer]
  inactive: [composer, harmony_theorist, rhythm_architect]
---

# Deep House — Genre Skill

## Defining Characteristics
- Tempo: 118-125 BPM
- Four-on-the-floor kick on every beat
- Off-beat hi-hats (8th notes)
- Smooth sub-heavy bass, often syncopated
- Jazzy 7th/9th chords on Rhodes or warm pad
- Vocals: chopped, filtered, used as texture not lead
- Loop-based structure with filter/texture evolution
- Track-oriented (not song-oriented): no lead melody

## Required Spec Patterns
```yaml
tempo_bpm: 122
time_signature: "4/4"
instruments:
  - name: drums
    role: rhythm
  - name: electric_bass_finger
    role: bass
  - name: electric_piano
    role: harmony
  - name: synth_pad_warm
    role: pad
generation:
  strategy: loop_evolution
  temperature: 0.3
```

## Idiomatic Chord Progressions
- ii7-V7-Imaj7-vi7 (jazz influenced, ~30%)
- Imaj7-iiim7-vi7-IV7 (smooth cycle, ~25%)
- bVII-I (chromatic upward approach, ~15%)
- i7-iv7 (two-chord vamp, ~15%)
- Single chord sustained with filter movement (~10%)

## Idiomatic Rhythms
```
KICK:  X . . . X . . . X . . . X . . .
HAT:   . . X . . . X . . . X . . . X .
CLAP:  . . . . X . . . . . . . X . . .
PERC:  . . . X . . . . . . X . . . X .
```
- Kick strictly on grid (four-on-the-floor)
- Hi-hat on off-beats (8th notes between kicks)
- Clap/snare on 2 and 4
- Percussion: shaker, rim, congas for groove texture

## Anti-Patterns
- Tempo > 130 BPM (drifts into tech house territory)
- Prominent lead melody (deep house is track-oriented, not song-oriented)
- Excessive humanization on drums (deep house favors tight grids)
- Acoustic drum kit (breaks genre frame entirely)
- Complex chord voicings above 5 notes (muddiness in low-end-heavy mix)
- Absence of four-on-the-floor kick (defining feature of house)
- Tempo < 115 BPM (loses dance floor energy)
- Busy arrangements with many simultaneous elements

## Reference Tracks
- None yet (rights-cleared deep house references needed)

## Default Sound Design
```yaml
instruments:
  drums:
    kick: { pack: "tr909_kick", saturation: 0.2 }
    hat: { pack: "tr909_hh_closed" }
    clap: { pack: "tr909_clap" }
  electric_bass_finger: { synthesis: { kind: subtractive, oscillators: [{ wave: sine }, { wave: square, octave: -1 }], filter: { type: low_pass, cutoff_hz: 800 } } }
  electric_piano: { synthesis: { kind: sample_based, pack: "rhodes_mk1_tremolo" }, effect_chain: [{ type: chorus, rate_hz: 0.5 }, { type: reverb, wet: 0.25 }] }
  synth_pad_warm: { synthesis: { kind: subtractive, filter_cutoff_lfo_hz: 0.1 } }
```

## Evaluation Weight Adjustments
structure.section_contrast: 0.5
melody.contour_variety: 0.2
melody.motif_recall_strength: 0.3
harmony.consonance_ratio: 0.7
rhythm.groove_consistency: 1.5
arrangement.texture_density_evolution: 1.3

## Default Trajectories
```yaml
trajectories:
  tension:
    type: stepped
    sections: { intro: 0.3, build: 0.5, drop: 0.95, breakdown: 0.4, outro: 0.2 }
  density:
    type: stepped
    sections: { intro: 0.3, build: 0.5, drop: 0.9, breakdown: 0.35, outro: 0.2 }
  filter_cutoff:
    type: bezier
    waypoints: [[0, 0.3], [0.25, 0.5], [0.5, 0.9], [0.75, 0.4], [1.0, 0.95]]
```
