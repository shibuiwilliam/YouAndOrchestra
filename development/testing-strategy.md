# Testing Strategy

## Test Categories

| Category | Location | Purpose | Count |
|----------|----------|---------|-------|
| Unit | `tests/unit/` | Individual module behavior | 207 |
| Integration | `tests/integration/` | Full pipeline end-to-end | 2 |
| Music Constraints | `tests/music_constraints/` | Music theory rule enforcement | 7 |
| Scenarios | `tests/scenarios/` | Prove musical value (not just mechanics) | 10 |
| Golden | `tests/golden/` | Fixed output regression | 0 (planned) |
| **Total** | | | **226** |

### Unit Test Coverage

| Test File | Tests | Covers |
|-----------|-------|--------|
| test_ir.py | 33 | IR types, note/section/score structures |
| test_stochastic.py | 22 | Stochastic generator algorithm |
| test_schema.py | 18 | YAML schema validation and parsing |
| test_motif.py | 15 | Motif generation and transformations |
| test_harmony.py | 15 | Chord/harmony rules |
| test_conductor.py | 15 | Conductor feedback loop |
| test_voicing.py | 11 | Voice leading and parallel fifths |
| test_verify.py | 11 | Linting and constraint verification |
| test_evaluator.py | 11 | Quality scoring |
| test_midi_reader.py | 9 | MIDI parsing back to ScoreIR |
| test_generator.py | 9 | Rule-based generator |
| test_diff.py | 9 | Score diffing |
| test_constraints.py | 8 | Constraint system |
| test_iteration.py | 7 | Iteration management |
| test_feedback.py | 7 | Feedback loop adaptations |
| test_render.py | 5 | MIDI/audio rendering |
| test_errors.py | 5 | Error handling |
| test_stem_writer.py | 2 | Per-instrument stem writing |

## Running Tests

```bash
make test              # All 226 tests
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
| IR type change | Round-trip preservation (IR -> MIDI -> IR) |
| New evaluator metric | Known good/bad samples score differently |
| Bug fix | Minimal reproducing test case |
| Lint rule | True positive + true negative examples |
| Schema change | Valid acceptance + invalid rejection |
| Conductor adaptation | Failing metric triggers correct spec change |

## Scenario Tests

Scenario tests prove musical value, not just mechanical correctness:

- **Tension arc creates climax** -- Rising trajectory -> louder peak section
- **Different keys produce different music** -- C major != G major pitch classes
- **Different dynamics affect velocity** -- pp << ff in average velocity
- **Seeds produce variation** -- Different seeds -> different melodies
- **Same seed reproduces** -- Identical seed -> identical output
- **Temperature affects variety** -- High temp -> more pitch classes
- **Multi-instrument enriches** -- More instruments -> more harmonic variety
- **Genre-specific** -- Rock, classical, ambient produce distinct characteristics

## Golden Test Protocol

When output stability matters (e.g., rule_based generator with a fixed spec):

1. Generate once and save as golden file
2. Test compares new output against golden file
3. When intentionally changing output, update golden file and document why
4. Never auto-approve golden file changes
