# Testing Guide

## Test Layout
- `tests/unit/` — Unit tests: `test_<module>.py`
- `tests/integration/` — End-to-end pipeline tests
- `tests/music_constraints/` — Music theory constraint tests
- `tests/scenarios/` — Musical scenario tests (proving musical value)
- `tests/golden/` — Fixed output comparison tests

## Required Tests
- Generator → "generates notes, respects key/range, produces provenance"
- IR change → "round-trip (IR → MIDI → IR) preserves equivalence"
- Evaluator → "known good/bad samples score differently"
- Bug fix → "minimal reproducing case"

## Test Helpers (`tests/helpers.py`)
```python
from tests.helpers import assert_in_range, assert_no_parallel_fifths, assert_trajectory_match

assert_in_range(notes, "piano")           # all notes in piano range
assert_no_parallel_fifths(voicings)       # no parallel 5ths
assert_trajectory_match(score, traj)      # dynamics match trajectory
```

## Fixtures (`tests/conftest.py`)
- `minimal_spec` — 8-bar single piano C major
- `multi_instrument_spec` — piano + bass, 3 sections
- `sample_score_ir` — pre-built ScoreIR with 8 known notes
- `tmp_output_dir` — temporary output directory

## Running Tests
```bash
make test           # all tests
make test-unit      # unit only
make test-integration  # integration only
make test-music     # music constraints only
make all-checks     # lint + arch-lint + test
```

## Golden Tests
- Use for output stability (e.g., rule_based generator with fixed spec).
- Update golden files intentionally; document why in PR description.
