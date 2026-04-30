# Contributing to YaO — 5-Minute Guide

## Setup

```bash
git clone <repo-url>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make test   # Should see ~486 tests passing
```

## Common Contributions

### Add an instrument

Edit `src/yao/constants/instruments.py`, add an `InstrumentRange` entry:
```python
InstrumentRange("my_instrument", midi_low=48, midi_high=84, program=0, family="keyboard"),
```

### Add a scale

Edit `src/yao/constants/music.py`, add to `SCALE_INTERVALS`:
```python
"my_scale": [0, 2, 3, 5, 7, 8, 11],  # semitone intervals from root
```

### Add a chord type

Edit `src/yao/constants/music.py`, add to `CHORD_INTERVALS`:
```python
"my_chord": [0, 4, 7, 11],  # semitone intervals from root
```

### Add a rhythm pattern

Edit `src/yao/generators/stochastic.py`, add to `_MELODY_RHYTHM_POOL`:
```python
[0.75, 0.25, 1.0, 1.0, 1.0],  # dotted eighth + sixteenth + quarters
```

### Add a test

Create `tests/unit/test_my_feature.py`:
```python
from __future__ import annotations
from yao.schema.composition import CompositionSpec

def test_my_feature(minimal_spec: CompositionSpec) -> None:
    # minimal_spec is a pytest fixture: 8-bar piano in C major
    assert minimal_spec.title == "Test Piece"
```

## Run Tests

```bash
make test              # All tests
pytest tests/unit/test_foo.py::test_bar -v   # One test
make test-golden       # Golden MIDI regression
make lint              # ruff + mypy
make all-checks        # Everything
```

## Generate a Piece

```bash
yao compose specs/templates/minimal.yaml
yao conduct "a calm piano piece in D minor"
```

## Before Submitting

```bash
make all-checks        # Must pass
```

## Code Standards

- Python 3.11+, `from __future__ import annotations`
- mypy strict — all public functions have type hints and docstrings
- ruff for formatting (line length: 99)
- Custom exceptions only — use `YaOError` subclasses, never bare `ValueError`
- See [CLAUDE.md](../CLAUDE.md) for full development rules
