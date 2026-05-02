# Design: Wave 1.4 — NoteRealizer V2

> **Date**: 2026-05-03
> **Status**: Implementation
> **Sprint**: Wave 1.4

---

## 1. What the current realizers throw away

`_plan_to_v1_spec()` discards the following MusicalPlan fields:

| Field | Discarded Information |
|---|---|
| `harmony.chord_events[].tension_level` | Only converted to coarse dynamics string |
| `harmony.chord_events[].cadence_role` | Completely lost |
| `harmony.chord_events[].function` | Completely lost |
| `harmony.chord_events[].roman` | Lost (only key preserved) |
| `motif.seeds` | Completely lost (not even read) |
| `motif.placements` | Completely lost |
| `phrase.phrases` | Completely lost |
| `phrase.phrases[].contour` | Completely lost |
| `arrangement` | Completely lost |
| `drums` | Completely lost |
| `trajectory` (multi-dim) | Only tension waypoints kept |

The v1 spec conversion only preserves: key, tempo, time_signature, genre, instruments, section names+bars+dynamics.

## 2. consumed_plan_fields for V2

```python
consumed_plan_fields = (
    "global_context.key",
    "global_context.tempo_bpm",
    "global_context.time_signature",
    "global_context.instruments",
    "form.sections",
    "harmony.chord_events",
    "motif.seeds",
    "motif.placements",
    "phrase.phrases",
    "trajectory",
)
```

This gives 7/7 major fields accessed (100%).

## 3. Field → Note translation algorithms

| Plan Field | Musical Effect |
|---|---|
| `ChordEvent.roman` | → `harmony.realize()` to get MIDI pitches for chord tones |
| `ChordEvent.tension_level` | → velocity scaling (0.3→pp=40, 1.0→ff=110) + non-chord-tone probability |
| `ChordEvent.cadence_role` | → last beat rhythmic emphasis, longer note values |
| `ChordEvent.function` | → voice leading rules (dominant → resolution tendency) |
| `MotifSeed.rhythm_shape` | → literal note durations at placement positions |
| `MotifSeed.interval_shape` | → literal intervals from chord root at placements |
| `MotifPlacement.transform` | → apply transformation before placement |
| `MotifPlacement.section_id/start_beat` | → bar/beat position for motif |
| `Phrase.contour` | → melodic direction constraint per phrase span |
| `Phrase.cadence` | → final note resolution strength |
| `SectionPlan.target_tension` | → overall velocity + register height |
| `SectionPlan.target_density` | → notes per beat (rhythm density) |

## 4. Migration plan

- **Phase Coexist** (now): V2 registered as "rule_based_v2", opt-in via `--realizer`
- **Phase Switch** (after golden comparison): V2 becomes default
- **Phase Remove** (end of Wave 2): V1 realizers deleted
