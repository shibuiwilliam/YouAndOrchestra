# Silent Fallback Inventory

> Generated: 2026-04-30 (Step 6)
> Status: All items converted to RecoverableDecision

## Stochastic Generator (`src/yao/generators/stochastic.py`)

| Location | What | Code | Status |
|---|---|---|---|
| `_generate_melody` (rest insertion) | Bar skipped as stochastic rest | `REST_INSERTED` | Converted |
| `_generate_melody` (bounce back) | Melody pitch bounced into range | `MELODY_NOTE_OUT_OF_RANGE` | Converted |
| `_generate_melody` (skip after bounce) | Melody note skipped entirely | `MELODY_NOTE_SKIPPED` | Converted |
| `_generate_melody` (velocity humanization) | Velocity clamped to [1, 127] | `VELOCITY_CLAMPED` | Converted |
| `_generate_melody_from_motif` (octave adjust) | Transformed motif note octave-adjusted | `MOTIF_NOTE_OUT_OF_RANGE` | Converted |
| `_generate_melody_from_motif` (skip) | Transformed note skipped | `MOTIF_NOTE_OUT_OF_RANGE` | Converted |
| `_generate_bass` (root fallback) | Bass passing tone fell back to root | `BASS_NOTE_OUT_OF_RANGE` | Converted |
| `_generate_chords` (quality fallback) | Chord quality defaulted to major | `CHORD_QUALITY_UNDEFINED` | Converted |
| `_generate_chords` (note skip) | Chord note outside range, skipped | `CHORD_NOTE_OUT_OF_RANGE` | Converted |
| `_generate_pad` (quality fallback) | Pad chord quality defaulted | `CHORD_QUALITY_UNDEFINED` | Converted |
| `_generate_rhythm` (pitch fallback) | Rhythm pitches fell back to root only | `RHYTHM_PITCH_OUT_OF_RANGE` | Converted |
| `_compute_velocity` | Base velocity clamped to [1, 127] | `VELOCITY_CLAMPED` | Converted |

## Rule-Based Generator (`src/yao/generators/rule_based.py`)

| Location | What | Code | Status |
|---|---|---|---|
| `_generate_chords` (note skip) | Chord note outside range, skipped | `CHORD_NOTE_OUT_OF_RANGE` | Converted |
| `_compute_velocity` | Base velocity clamped to [1, 127] | `VELOCITY_CLAMPED` | Converted |

## Not Converted (intentional)

The following patterns are **not** RecoverableDecision candidates because they are
normal behavior, not compromises:

- `conductor/conductor.py`: Default duration (90s) — this is NL parsing, not a fallback
- `conductor/feedback.py`: Temperature clamping — these are intentional adaptation bounds
- `render/midi_reader.py`: Default BPM/key when reading MIDI — reader defaults are different from generation compromises
