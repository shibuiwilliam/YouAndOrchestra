# Testing Strategy

## Test Categories

| Category | Location | Purpose | Count |
|----------|----------|---------|-------|
| Unit | `tests/unit/` | Individual module behavior | ~140 |
| Integration | `tests/integration/` | Full pipeline end-to-end | ~5 |
| Music Constraints | `tests/music_constraints/` | Music theory rule enforcement | ~10 |
| Scenarios | `tests/scenarios/` | Prove musical value (not just mechanics) | ~15 |
| Golden | `tests/golden/` | Fixed output regression | 0 (planned) |

## Running Tests

```bash
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests
make test-music        # Music constraint tests
make all-checks        # lint + mypy + arch-lint + all tests
```

## Test Helpers (`tests/helpers.py`)

```python
assert_in_range(notes, instrument)
# Verify all notes within instrument's playable range

assert_no_parallel_fifths(voicings)
# Verify no parallel perfect fifths between consecutive voicings

assert_trajectory_match(score, trajectory, dimension="tension", tolerance=0.1)
# Verify dynamics approximately match trajectory curve
```

## Fixtures (`tests/conftest.py`)

| Fixture | Description |
|---------|-------------|
| `minimal_spec` | 8-bar, single piano, C major, 120 BPM |
| `multi_instrument_spec` | Piano + bass, 3 sections, G major |
| `sample_score_ir` | Pre-built ScoreIR with 8 known notes |
| `tmp_output_dir` | Temporary directory for output files |
| `spec_template_dir` | Path to specs/templates/ |

## What Must Be Tested

| Change Type | Required Tests |
|-------------|---------------|
| New generator | Generates notes, respects key/range, produces provenance, seed reproducibility |
| IR type change | Round-trip preservation (IR → MIDI → IR) |
| New evaluator metric | Known good/bad samples score differently |
| Bug fix | Minimal reproducing test case |
| Lint rule | True positive + true negative examples |
| Schema change | Valid acceptance + invalid rejection |

## Scenario Tests

Scenario tests prove musical value, not just mechanical correctness:

- **Tension arc creates climax** — Rising trajectory → louder peak section
- **Different keys produce different music** — C major ≠ G major pitch classes
- **Different dynamics affect velocity** — pp ≪ ff in average velocity
- **Seeds produce variation** — Different seeds → different melodies
- **Same seed reproduces** — Identical seed → identical output
- **Temperature affects variety** — High temp → more pitch classes
- **Multi-instrument enriches** — More instruments → more harmonic variety

## Golden Test Protocol

When output stability matters (e.g., rule_based generator with a fixed spec):

1. Generate once and save as golden file
2. Test compares new output against golden file
3. When intentionally changing output, update golden file and document why
4. Never auto-approve golden file changes
