---
topic: twelve_tone_serialism
applies_to: [generation]
---

# Twelve-Tone Technique — Theory Skill

## Overview
Twelve-tone technique (dodecaphony) organizes all 12 chromatic pitch classes
into a fixed ordering called a "tone row." The row and its transformations
provide all pitch material for the composition.

## The Tone Row
- A permutation of pitch classes 0-11 (C=0, C#=1, ..., B=11)
- Each pitch class appears exactly once
- The row is NOT a melody — it is a pitch reservoir

## Four Standard Transformations
1. **Prime (P)**: The original row
2. **Inversion (I)**: Intervals reversed in direction (up↔down)
3. **Retrograde (R)**: Row played backwards
4. **Retrograde-Inversion (RI)**: Inversion played backwards

## Transposition
Each form can be transposed to start on any pitch class (P0-P11, I0-I11, etc.)

## Compositional Usage
- Sections can use different forms
- Rhythm, dynamics, register are FREE (not determined by the row)
- Octave placement is the composer's choice
- The row ensures chromatic saturation (no pitch bias)

## Common Misconceptions
- Twelve-tone ≠ atonal noise — structure provides coherence
- Rows can be melodically beautiful (Berg, Webern)
- Rhythm and articulation create the character

## YaO Implementation
- `strategy: twelve_tone` in composition.yaml
- Row auto-generated from seed, or specify manually
- P/I/R/RI cycled per section by default
