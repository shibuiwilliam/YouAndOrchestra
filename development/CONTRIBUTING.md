# Contributing to YaO -- 5-Minute Guide

## Setup

```bash
git clone https://github.com/shibuiwilliam/YouAndOrchestra
cd YouAndOrchestra
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,sdk]"
# Optional: for cover art generation
pip install -e ".[cover-art]"
export GEMINI_API_KEY="your-key-here"  # from https://aistudio.google.com/apikey
make all-checks   # Should see ~4,000+ tests passing + 6 golden + 5 honesty tools
```

Requires **Python 3.11+**.

## Common Contributions

### Add an instrument

Edit `src/yao/constants/instruments.py`, add an `InstrumentRange` entry:
```python
InstrumentRange("my_instrument", midi_low=48, midi_high=84, program=0, family="keyboard"),
```

### Add a scale

Edit `src/yao/constants/scales.py`, add a `ScaleDefinition`:
```python
MY_SCALE = ScaleDefinition(
    name="my_scale",
    intervals_cents=(0, 200, 300, 500, 700, 800, 1100),
)
```

### Add a chord type

Edit `src/yao/constants/music.py`, add to `CHORD_INTERVALS`:
```python
"my_chord": [0, 4, 7, 11],  # semitone intervals from root
```

### Add a song form

Edit `src/yao/constants/forms.py`:
```python
_register(SongForm(
    id="my_form",
    name="My Form",
    sections=(
        FormSection(id="a", bars=8, role="verse", density=0.5, tension=0.5),
        FormSection(id="b", bars=8, role="chorus", density=0.8, tension=0.8),
    ),
    typical_genres=("pop",),
    description="My custom form.",
))
```

### Add a critique rule

Create in `src/yao/verify/critique/`, inherit `CritiqueRule`:
```python
class MyRuleDetector(CritiqueRule):
    rule_id = "category.my_rule"
    role = Role.STRUCTURE

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        ...
```
Then register in `src/yao/verify/critique/__init__.py`.

### Add a genre skill

1. Create `.claude/skills/genres/<name>.md` with rich front-matter
2. Run `make sync-skills` to generate YAML
3. Validate via `yao validate-genre <name>`
4. Add tests in `tests/genre_coverage/`
5. Run `make calibrate-genres` to verify output quality

### Add a test

```python
from __future__ import annotations
from tests.helpers import make_minimal_spec_v2

def test_my_feature() -> None:
    spec = make_minimal_spec_v2()
    assert spec.form.sections[0].id == "verse"
```

## Run Tests

```bash
make all-checks        # Full pipeline (lint + arch-lint + tests + golden + honesty)
make test              # All tests (~4,000+)
make lint              # ruff + mypy strict
make arch-lint         # Layer boundary enforcement (covers Layer 2.5 Coupling)
make format            # Auto-format code (ruff)
make test-melody       # Unit tests for the phrase-first melody pipeline
make test-coupling     # Combination Stack tests (Layer 2.5)
make test-genres       # Genre-specific scenario tests (30 genres)
make test-golden       # Golden MIDI regression
make test-diversity    # Diversity scenario tests
make test-acoustic     # Audio feature regression (weekly CI)
make test-genre-coverage  # Per-genre validation (30 genres)
make markov-validate   # Validate Markov model YAMLs
make device-validate   # Validate harmonic-device YAMLs
make gesture-validate  # Validate idiomatic-gesture YAMLs
make profile-perf      # Verify generation stays within performance budget
make calibrate-genres  # Genre profile parameter sweep
make sdk-test          # SDK-specific tests
make sdk-examples-test # Verify SDK reference applications
pytest tests/unit/test_foo.py::test_bar -v   # One test
```

## Generate a Piece

```bash
# Via CLI
yao compose specs/templates/minimal.yaml
yao conduct "a calm piano piece in D minor"

# Via Claude Code
claude
> /sketch a calm piano piece for studying
> /compose my-piece
> /critique my-piece
> /pin my-piece --location "section:chorus,bar:3" --note "too busy"
> /render my-piece
```

### Via Agent SDK
```python
import asyncio
from yao.sdk import YaoAgent

async def main():
    async with YaoAgent(project="my-piece") as agent:
        async for event in agent.conduct("a calm piano piece in D minor"):
            print(event)

asyncio.run(main())
```

## Before Submitting

```bash
make all-checks        # Must pass (4,000+ tests + 6 golden + 5 honesty tools)
```

## Code Standards

- Python 3.11+, `from __future__ import annotations`
- mypy strict -- all public functions have type hints and docstrings
- ruff for formatting (line length: 120)
- Custom exceptions only -- use `YaOError` subclasses, never bare `ValueError`
- Every generation function returns `(IR, ProvenanceLog)` -- no third option
- Frozen dataclasses for all IR types
- Layer boundaries enforced by `make arch-lint` -- lower layers never import upper
- No hardcoded musical values -- use `src/yao/constants/` or genre-aware lookups
- See [CLAUDE.md](../CLAUDE.md) for full development rules
