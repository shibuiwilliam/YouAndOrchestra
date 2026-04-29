# Voice Leading — Theory Skill

## Core Principles

### 1. Smoothness (Minimal Motion)
- Each voice should move by the smallest interval possible
- Prefer stepwise motion (seconds) over leaps (thirds or larger)
- Common tones between chords should be retained in the same voice

### 2. Independence
- Each voice should have its own melodic identity
- Avoid all voices moving in the same direction simultaneously (direct/similar motion)
- At least one voice should move contrary to the others

### 3. Forbidden Parallels
- **Parallel fifths:** Two voices moving in parallel perfect fifths (e.g., C-G → D-A) are forbidden in classical style
- **Parallel octaves:** Two voices moving in parallel octaves (e.g., C-C → D-D) are forbidden
- **Hidden fifths/octaves:** Outer voices arriving at a fifth/octave by similar motion (acceptable with stepwise soprano)
- YaO detects these via `yao.ir.voicing.detect_parallel_fifths()` and `detect_parallel_octaves()`

### 4. Voice Spacing
- Adjacent upper voices should be within an octave of each other
- Bass may be more than an octave from the tenor
- Crossing (alto going below tenor) should be rare and brief

## Practical Rules for YaO Generators

### When Generating Chord Voicings
1. Keep common tones between consecutive chords
2. Move remaining voices stepwise
3. Resolve tendency tones: 7th resolves down, leading tone resolves up
4. Avoid doubling the leading tone (3rd of V chord in major)
5. Double the root preferentially, then fifth, last the third

### Cadences
| Cadence | Progression | Voice Leading |
|---------|-------------|---------------|
| Authentic | V → I | Leading tone → tonic, 7th → 3rd of I |
| Plagal | IV → I | Subdominant 4th → 3rd or stays, 6th → 5th |
| Deceptive | V → vi | Leading tone still resolves up, bass drops to vi |
| Half | any → V | Approach V with smooth motion, soprano on 2nd or 7th |

### Resolution Patterns
- **Tritone (augmented 4th):** Resolves outward (both voices move by step in opposite directions)
- **Diminished 5th:** Resolves inward
- **Dominant 7th chord:** 3rd (leading tone) resolves up, 7th resolves down
- **Suspension:** Preparation (consonance) → suspension (hold) → resolution (step down)

## Application in YaO
- The `voicing` module at `src/yao/ir/voicing.py` provides:
  - `Voicing` dataclass for multi-note chord configurations
  - `detect_parallel_fifths(voicing_a, voicing_b)` for parallel fifth detection
  - `detect_parallel_octaves(voicing_a, voicing_b)` for parallel octave detection
  - `voice_distance(voicing_a, voicing_b)` to measure voice-leading smoothness
- Constraint system can enforce: `must_not: parallel_fifths` in constraints.yaml
