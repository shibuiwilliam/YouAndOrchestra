# Testing Strategy

## Test Categories

| Category | Location | Purpose | Approx Count |
|----------|----------|---------|------|
| Unit | `tests/unit/` | Individual module behavior across all layers | ~1,500 |
| Integration | `tests/integration/` | Full pipeline, spec compiler (EN+JP), motif recurrence, skill grounding | ~40 |
| Music Constraints | `tests/music_constraints/` | Music theory rule enforcement | ~16 |
| Scenarios | `tests/scenarios/` | Prove musical value (trajectory compliance, surprise distribution, diversity, hook deployment, pin localization, groove changes feel, NL feedback) | ~30 |
| Golden | `tests/golden/` | Fixed output regression (V1 + V2 baselines) | 6 |
| Audio Regression | `tests/audio_regression/` | Acoustic feature stability (weekly CI) | ~8 |
| Genre Coverage | `tests/genre_coverage/` | Per-genre schema validation, profile loading, all 22 genres | ~111 |
| Properties | `tests/properties/` | Property-based genre invariants across strategies and seeds | ~20 |
| Subjective | `tests/subjective/` | Human rating threshold validation | ~5 |
| **Total** | | | **~2,157** |

## Running Tests

```bash
make all-checks        # Full pipeline: lint + arch-lint + tests + golden + honesty
make test              # All ~2,157 tests
make test-unit         # Unit tests only
make test-integration  # Integration tests
make test-golden       # Golden MIDI regression tests
make test-acoustic     # Audio feature regression (weekly CI)
make test-genre-coverage  # Per-genre validation (22 genres)
make test-subjective   # Human rating tests (skipped in CI)
make lint              # ruff + mypy strict
make arch-lint         # Layer boundary enforcement
make meter-lint        # Non-4/4 meter support validation
make honesty-check     # Verify no stub features marked as complete
make feature-status    # Verify FEATURE_STATUS.md alignment
make sync-docs         # Check doc sync
make calibrate-genres  # Genre profile parameter sweep
pytest tests/unit/test_foo.py::test_bar -v   # One specific test
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
| New genre skill | Genre coverage tests + calibrate-genres pass |
| New drum pattern | Meter-aware validation + fills |

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

- **Tension arc creates climax** -- Rising trajectory produces louder peak section
- **Surprise distribution** -- Key context matters, chromatic notes score higher
- **Diversity sources** -- 20 forms provide varying lengths + genres
- **Hook deployment** -- withhold_then_release appears later than frequent
- **Pin localization** -- Pin at bar 5 affects bars 4-6, preserves rest
- **NL feedback translation** -- "more energy in chorus" maps to correct structured feedback
- **Trajectory compliance** -- When trajectory changes, output changes measurably
- **Different seeds produce variation** -- Same spec, different seed produces different melody
- **Groove changes feel** -- Applying groove profile measurably shifts microtiming and velocity

## Honesty Tools

5 CI tools verify implementation integrity:

| Tool | Command | What It Checks |
|---|---|---|
| Honesty check | `make honesty-check` | No features marked stable that are actually stubs |
| Backend honesty | `make backend-honesty` | Stub backends declare `is_stub=True` |
| Plan consumption | `make plan-consumption` | V2 realizers consume 80%+ of plan fields |
| Skill grounding | `make skill-grounding` | Genre skills referenced from src/ |
| Critic coverage | `make critic-coverage` | All severity levels have effective rules |

## pytest Markers

Use these markers to select specific test subsets:

- `@pytest.mark.integration` -- Full pipeline tests
- `@pytest.mark.golden` -- Regression tests
- `@pytest.mark.music_constraints` -- Music theory enforcement
- `@pytest.mark.subagent` -- Subagent evaluation
- `@pytest.mark.subjective` -- Human rating (skipped in CI)
- `@pytest.mark.audio_regression` -- Acoustic features (weekly CI)
- `@pytest.mark.genre_coverage` -- Per-genre validation
