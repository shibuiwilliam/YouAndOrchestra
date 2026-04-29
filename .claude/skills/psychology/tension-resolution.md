# Tension and Resolution — Psychology Skill

## Theoretical Foundation

Musical tension is a listener's expectation of what comes next. When expectations are violated or delayed, tension increases. When expectations are fulfilled, tension resolves. The interplay between these creates the emotional narrative of music.

Key researchers: Leonard Meyer (expectation theory), David Huron (ITPRA theory), Fred Lerdahl (tonal tension theory).

## Tension Factors

### 1. Harmonic Tension (strongest effect)
| Element | Low Tension | High Tension |
|---------|------------|-------------|
| Chord function | I (tonic) | V7, vii° (dominant) |
| Dissonance | Consonant (3rds, 5ths, octaves) | Dissonant (2nds, tritones, 7ths) |
| Distance from tonic | Close (IV, V) | Far (bII, #IV) |
| Chromatic alteration | Diatonic | Chromatic, borrowed chords |
| Modulation | Home key | Remote key |

### 2. Melodic Tension
| Element | Low Tension | High Tension |
|---------|------------|-------------|
| Contour | Descending or stable | Ascending (especially stepwise) |
| Range | Near center of range | Extremes of range |
| Interval size | Steps (2nds, 3rds) | Leaps (6ths, 7ths, octaves+) |
| Resolution | Scale degree 1, 3, 5 | Scale degree 7, 4, 6 |

### 3. Rhythmic Tension
| Element | Low Tension | High Tension |
|---------|------------|-------------|
| Note density | Sparse, long notes | Dense, short notes |
| Syncopation | On-beat | Off-beat, unexpected accents |
| Tempo | Stable | Accelerating |
| Meter | Clear downbeats | Displaced or ambiguous meter |

### 4. Textural Tension
| Element | Low Tension | High Tension |
|---------|------------|-------------|
| Density | Solo or duo | Full ensemble |
| Register spread | Narrow | Wide (bass + high treble) |
| Dynamics | pp-p | f-ff |
| Articulation | Legato, sustained | Staccato, marcato |

## Tension Curve Design (trajectory.yaml)

### Common Patterns
```
Arch (most natural):      0.2 → 0.5 → 0.8 → 0.4 → 0.2
Ramp:                     0.2 → 0.4 → 0.6 → 0.8 → 0.9
Wave:                     0.3 → 0.7 → 0.3 → 0.8 → 0.3
Plateau:                  0.2 → 0.7 → 0.7 → 0.7 → 0.3
Sawtooth:                 0.2 → 0.8 → 0.3 → 0.9 → 0.2
Inverse arch (rare):      0.7 → 0.4 → 0.2 → 0.4 → 0.7
```

### Mapping Tension to YaO Parameters
| Tension Level | Dynamics | Note Density | Instruments | Harmonic Complexity |
|--------------|----------|-------------|-------------|-------------------|
| 0.0 - 0.2 | pp | Sparse (1-3 notes/bar) | 1-2, solo | I, IV chords only |
| 0.2 - 0.4 | p-mp | Light (4-6 notes/bar) | 2-3 | Diatonic triads |
| 0.4 - 0.6 | mp-mf | Medium (6-10 notes/bar) | 3-4 | 7th chords, secondary dominants |
| 0.6 - 0.8 | mf-f | Dense (10-15 notes/bar) | 4-6 | Chromatic chords, suspensions |
| 0.8 - 1.0 | f-ff | Very dense (15+ notes/bar) | Full ensemble | Diminished, augmented, clusters |

## Resolution Principles

### The Rule of Expectation
- Tension must eventually resolve, or listeners feel frustrated
- The longer tension is sustained, the more satisfying the resolution
- Resolution to tonic (I chord) is the strongest resolution
- Deceptive resolution (V → vi) maintains interest while partially resolving

### Climax Placement
- **2/3 rule:** The climax is most satisfying at approximately 2/3 through the piece (the "golden section")
- Early climax (1/3): creates a sense of aftermath and reflection
- Late climax (4/5): creates intense build with short resolution — dramatic, cinematic
- YaO default: peak_bar = total_bars * 2 // 3

### Emotional Valence Mapping
| Emotion | Tension Pattern | Key | Tempo |
|---------|----------------|-----|-------|
| Joy | Low-medium, wave-like | Major | 110-140 |
| Sadness | Low-medium, descending | Minor | 60-90 |
| Fear | High, sustained, unresolved | Minor, diminished | 80-120 |
| Anger | High, sharp peaks | Minor, chromatic | 120-160 |
| Serenity | Very low, flat | Major, lydian | 60-80 |
| Triumph | Rising to high peak with full resolution | Major | 100-130 |
| Nostalgia | Medium, wave with gradual descent | Minor → major | 80-100 |

## Application in YaO
- The `trajectory.yaml` spec controls tension, density, and predictability curves
- Trajectory values at each bar influence velocity (via `_compute_velocity` in generators)
- Tension 0.5 is neutral; above increases velocity, below decreases
- The Conductor's feedback loop evaluates whether the generated music's actual tension matches the intended trajectory
