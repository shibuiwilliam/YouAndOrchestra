# Testing Strategy

## Test Categories

| Category | Location | Purpose | Count |
|----------|----------|---------|-------|
| Unit | `tests/unit/` | Individual module behavior, V2 realizers, aesthetic metrics, ensemble constraints, perception, hooks, groove, conversation | ~1,500 |
| Integration | `tests/integration/` | Full pipeline, spec compiler (EN+JP), motif recurrence, skill grounding | ~40 |
| Music Constraints | `tests/music_constraints/` | Music theory rule enforcement | ~16 |
| Scenarios | `tests/scenarios/` | Prove musical value (trajectory compliance, surprise distribution, diversity, hook deployment, pin localization) | ~30 |
| Golden | `tests/golden/` | Fixed output regression (V1 + V2 baselines) | 6 |
| Audio Regression | `tests/audio_regression/` | Acoustic feature stability (weekly CI) | ~8 |
| Properties | `tests/properties/` | Property-based genre invariants | ~20 |
| Subjective | `tests/subjective/` | Human rating threshold validation | ~5 |
| **Total** | | | **~1,750** |

## Running Tests

```bash
make all-checks        # Full pipeline: lint + arch-lint + tests + golden + honesty
make test              # All ~1,748 tests
make lint              # ruff + mypy strict
make arch-lint         # Layer boundary enforcement
make test-acoustic     # Audio regression (weekly CI)
make test-golden       # Golden MIDI regression tests
make honesty-check     # Verify no stub ✅ features
make feature-status    # Verify FEATURE_STATUS.md alignment
make sync-docs         # Check doc sync
```

## Test Helpers (`tests/helpers.py`)

```python
make_minimal_spec_v2(**overrides)
# Create a valid CompositionSpecV2 for testing

assert_in_range(notes, instrument)
# Verify all notes within instrument's playable range

assert_no_parallel_fifths(voicings)
# Verify no parallel perfect fifths between consecutive voicings

assert_trajectory_match(score, trajectory, dimension="tension", tolerance=0.1)
# Verify dynamics approximately match trajectory curve
```

## What Must Be Tested

| Change Type | Required Tests |
|-------------|---------------|
| New plan generator | Produces valid plan, respects spec, records provenance |
| New note realizer | Produces notes from plan, respects ranges, seed reproducibility, trajectory compliance |
| New critique rule | At least 2 tests (positive detection + negative silence) |
| IR type change | Serialization round-trip, construction, frozen enforcement |
| New evaluator metric | Known good/bad samples score differently |
| New schema field | Valid acceptance + invalid rejection |
| Bug fix | Minimal reproducing test case |
| Acoustic feature | Synthetic signal verification (known LUFS, known centroid) |
| Conversation/groove | Plan-level check + note-level effect |
| Pin/feedback | Scope localization (affected region changes, surrounding preserved) |

## Golden Test Protocol

When output stability matters (e.g., rule_based generator with a fixed spec):

1. Generate once and save as golden file in `tests/golden/expected/`
2. Test compares new output against golden file
3. When intentionally changing output, update golden file and document why in PR
4. Never auto-approve golden file changes
5. Run with `make test-golden`

## Audio Regression Protocol

Acoustic feature regression runs weekly (too slow for every PR):

1. Synthetic test signals with known properties (sine, noise, two-section)
2. `make test-acoustic` runs deterministic feature extraction verification
3. CI workflow: `.github/workflows/audio-regression.yml` (Sunday 03:00 UTC)
4. Failed baselines uploaded as artifacts for investigation

## Scenario Tests

Scenario tests prove musical value, not just mechanical correctness:

- **Tension arc creates climax** — Rising trajectory → louder peak section
- **Surprise distribution** — Key context matters, chromatic notes score higher
- **Diversity sources** — 20 forms provide varying lengths + genres
- **Hook deployment** — withhold_then_release appears later than frequent
- **Pin localization** — Pin at bar 5 affects bars 4-6, preserves rest
- **NL feedback translation** — "more energy in chorus" → correct structured feedback
- **Trajectory compliance** — When trajectory changes, output changes measurably
- **Different seeds produce variation** — Same spec, different seed → different melody
