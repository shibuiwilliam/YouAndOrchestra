# Golden MIDI Tests

These tests detect unintended musical regression. A fixed spec + seed + realizer
combination must produce bit-exact MIDI output. If it doesn't, something changed.

## When tests fail

The first question: **was the change intentional?**

### If unintentional

The change broke something. Fix the code, not the goldens.

### If intentional (e.g., you fixed a bug, improved a generator)

1. Verify the new MIDI is musically better (listen to it)
2. Compare old vs new audio in your PR
3. Run: `python tests/golden/tools/regenerate_goldens.py --reason "Brief description" --confirm`
4. Commit updated goldens
5. PR description must include audio diff

## Running golden tests

```bash
make test-golden          # Run golden tests only
pytest tests/golden/ -v   # Same, with verbose output
```

## Adding new golden cases

Add to `GOLDEN_MATRIX` in `tests/golden/tools/regenerate_goldens.py`.
Requires PR review — each entry adds CI time and maintenance burden.

## Why bit-exact?

Determinism is the foundation of reproducible music creation.
If we lose bit-exact comparison, we lose the ability to verify
that "the same input gives the same output." Tolerance comparison
is allowed but treated as a degraded mode requiring justification.

## File structure

```
tests/golden/
  inputs/          Fixed v2 specs (never modify after initial commit)
  expected/        Golden MIDI files (committed, regenerated only intentionally)
  tools/           Regeneration script
  comparison.py    Comparison logic
  test_golden.py   Parameterized test
```
