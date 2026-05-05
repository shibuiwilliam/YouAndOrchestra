# Design Note 0008: Vocal Track Support

## Summary

Introduces singability evaluation for vocal lines, enabling YaO to validate that generated melodies are humanly performable when assigned to voice instruments.

## Motivation

Vocal parts have constraints that instrumental parts do not: limited breath capacity, physical difficulty of large interval leaps, and tessitura fatigue from sustained singing at range extremes. Without explicit checking, generators can produce lines that are technically valid MIDI but impractical for singers.

## Design

### SingabilityReport

A frozen dataclass containing:
- `awkward_leaps`: Count of intervals > 7 semitones
- `breath_violations`: Count of phrases > 8 beats without a rest opportunity
- `tessitura_strain`: Fraction [0.0, 1.0] of notes in the outer 20% of vocal range
- `total_notes`: Total notes analyzed
- `score`: Overall singability [0.0, 1.0]
- `issues`: Human-readable issue descriptions

### Metrics

1. **Awkward Leaps**: Any interval exceeding 7 semitones (perfect fifth) between consecutive notes. Contributes 40% to the penalty.

2. **Breath Violations**: A phrase (sequence of notes without a gap >= 0.5 beats) exceeding 8 beats. Contributes 30% to the penalty.

3. **Tessitura Strain**: Notes in the outer 20% of the instrument's range. Extended time in extreme registers causes fatigue. Contributes 30% to the penalty.

### Vocal Ranges

Supported vocal types with MIDI ranges:
- Soprano: C4-C6 (60-84)
- Mezzo-soprano: A3-A5 (57-81)
- Alto: F3-F5 (53-77)
- Tenor: C3-C5 (48-72)
- Baritone: A2-A4 (45-69)
- Bass voice: E2-E4 (40-64)
- Generic voice: C3-G5 (48-79)

## Files

- `src/yao/verify/singability.py` — Singability evaluator
- `tests/unit/test_vocal_track.py` — Unit tests

## Layer Placement

- Singability evaluator: Layer 6 (Verification)

## Future Extensions

- Integration with generators to constrain vocal line generation
- Lyric syllable alignment checking
- Vibrato and portamento marking suggestions
