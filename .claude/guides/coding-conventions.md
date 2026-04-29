# Coding Conventions

## Python
- Python 3.11+, `from __future__ import annotations` everywhere
- `mypy --strict` for all public API
- Line length: 99 characters (ruff)

## Naming
- Modules: `snake_case`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Music acronyms uppercase: `load_midi_file`, `BpmEstimator`

## Domain Vocabulary
- "composition" or "piece" (not "track" or "song")
- `Section` for intro/verse/chorus/bridge
- `Motif` for short fragments, `Phrase` for longer ones
- `Tick` = MIDI resolution, `Beat` = musical pulse, `Seconds` = wall-clock — never mix
- `Voicing` = chord pitch arrangement, `Orchestration` = instrument assignment — never mix

## Data Model
- External input (YAML) → **Pydantic models** (in `schema/`)
- Internal domain objects → **frozen dataclasses** (in `ir/`)

## Error Handling
- All exceptions subclass `YaOError` (in `src/yao/errors.py`)
- **No bare `ValueError`** — use `SpecValidationError`, `RangeViolationError`, etc.
- **No silent fallback** — constraint violations must raise, not silently clamp
- Error messages follow the style guide below
- Logging: `structlog` (structured JSON output)

## Error Message Style Guide

Format: **{What happened}. {Why it's wrong}. {How to fix it}.**

```
WRONG: "RangeViolationError: 96"
RIGHT: "C7 (MIDI 96) is above the range for piano (A0=21 to C8=108).
        Consider: transpose down 12 semitones; assign to a higher-range instrument."

WRONG: "SpecValidationError: invalid tempo"
RIGHT: "Tempo must be between 20 and 300 BPM, got 0. Check composition.yaml 'tempo_bpm' field."

WRONG: "Unknown generator"
RIGHT: "Unknown generator 'magic'. Available: rule_based, stochastic"
```

Every error message must be actionable — the reader should know what to do next.

## Examples

```python
# WRONG: hardcoded velocity
note = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=100, instrument="piano")

# RIGHT: derive from dynamics
velocity = DYNAMICS_TO_VELOCITY[section.dynamics]
note = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=velocity, instrument="piano")
```

```python
# WRONG: manual tick calculation
tick = int(beat * 220)

# RIGHT: use timing module
from yao.ir.timing import beats_to_ticks
tick = beats_to_ticks(beat)
```

```python
# WRONG: silent range clamp
pitch = min(max(pitch, inst.midi_low), inst.midi_high)

# RIGHT: explicit error
note.validate_range()  # raises RangeViolationError
```
