# Wave 1.4 — V1 vs V2 Comparison Report

> **Date**: 2026-05-03
> **Status**: Phase Coexist (V2 is opt-in via `--realizer rule_based_v2` or `stochastic_v2`)

---

## Architectural delta

| Aspect | V1 (rule_based) | V2 (rule_based_v2 / stochastic_v2) |
|---|---|---|
| Plan consumption | 29%–43% (via _plan_to_v1_spec) | **100%** (direct) |
| Chord events | Converted to coarse dynamics string | Each ChordEvent → MIDI pitches via `realize()` |
| Tension level | Lost in conversion | Maps to velocity (40–110 range) |
| Cadence role | Completely lost | Longer notes + velocity boost at cadences |
| Motif placements | Completely lost | Placed at exact beat positions with transforms |
| Phrase contours | Completely lost | Melodic direction constrained per phrase |
| Section density | Lost (only dynamics preserved) | Controls notes-per-beat rate |
| Arrangement | Lost | Instrument selection from arrangement layers |
| Drums | Lost | Acknowledged in provenance (rhythmic density) |
| Temperature | Passed to legacy generator | Controls non-chord-tone probability + rhythmic variety |

---

## Quantitative comparison (24-bar pop piece, seed=42)

| Metric | V1 rule_based | V2 rule_based_v2 | V2 stochastic_v2 (temp=0.5) |
|---|---|---|---|
| **Note count** | 90 | 130 | 117 |
| **Pitch range** | 72–83 (11 semitones) | 57–69 (12 semitones) | 55–84 (29 semitones) |
| **Velocity range** | 43–125 | 41–96 | 33–101 |
| **Pitch class diversity** | 7 | 9 | 8 |

### Section-level velocity (V2 rule_based_v2):

| Section | Role | Avg Velocity | Notes |
|---|---|---|---|
| intro | intro | 41 | 16 |
| verse | verse | 66 | 42 |
| chorus | chorus (climax) | **92** | 56 |
| outro | outro | 41 | 16 |

This shows proper tension-to-velocity mapping: chorus is loudest, intro/outro are softest.

---

## Musical observations

### V2 improvements:
- **Chord-aware melody**: Notes are actual chord tones (not random scale notes)
- **Motif recurrence**: Same motif appears 3 times with transformations (SEQUENCE_UP, INVERSION)
- **Dynamic arc**: Velocity smoothly follows section tension (intro 41 → chorus 92 → outro 41)
- **Phrase shaping**: Ascending/descending patterns follow contour declarations
- **Cadence emphasis**: End-of-phrase notes are longer and stronger
- **Density control**: Intro has 16 notes, chorus has 56 (reflecting target_density)

### V2 current limitations:
- Only generates single melody line (no harmony/bass parts yet)
- Drum pattern not yet realized into drum notes
- Arrangement layers not fully utilized for multi-instrument texture

---

## Registered realizers (Phase Coexist)

```
['rule_based', 'rule_based_v2', 'stochastic', 'stochastic_v2']
```

- `rule_based` (V1): default, deprecated, unchanged behavior
- `rule_based_v2` (V2): opt-in, 100% plan consumption, deterministic
- `stochastic` (V1): deprecated, unchanged
- `stochastic_v2` (V2): opt-in, 100% plan consumption, seed+temperature controlled

---

## plan-consumption results

```
[FAIL] RuleBasedNoteRealizer:    43% (3/7 fields, uses legacy adapter) ← deprecated
[PASS] RuleBasedNoteRealizerV2:  100% (7/7 fields, no legacy adapter)
[FAIL] StochasticNoteRealizer:   0% (uses legacy adapter) ← deprecated
[PASS] StochasticNoteRealizerV2: 100% (7/7 fields, no legacy adapter)
```

---

## Vertical Alignment Assessment

- **Input**: △ (spec unchanged, but plan now fully consumed)
- **Processing**: ✅✅ (the biggest structural improvement — MPIR is no longer decorative)
- **Evaluation**: △ (golden tests can now have meaningful V2 baselines)

---

## Next steps

### Phase Switch (next):
1. Make `rule_based_v2` the default in Conductor pipeline
2. Update golden test baselines for V2 output
3. Audio rendering comparison
4. User feedback collection

### Phase Remove (Wave 2):
1. Delete `src/yao/generators/note/rule_based.py`
2. Delete `src/yao/generators/note/stochastic.py`
3. Delete `src/yao/generators/legacy_adapter.py`
4. Verify zero imports of `_plan_to_v1_spec`
