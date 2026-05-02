# Testing Strategy

## Test Categories

| Category | Location | Purpose | Count |
|----------|----------|---------|-------|
| Unit | `tests/unit/` | Individual module behavior, V2 realizers, aesthetic metrics, ensemble constraints | ~1,000 |
| Integration | `tests/integration/` | Full pipeline, spec compiler (EN+JP), motif recurrence | ~40 |
| Music Constraints | `tests/music_constraints/` | Music theory rule enforcement | ~16 |
| Scenarios | `tests/scenarios/` | Prove musical value (not just mechanics) | ~16 |
| Golden | `tests/golden/` | Fixed output regression (V1 + V2 baselines) | 6 |
| Tools | `tests/tools/` | CI honesty tool unit tests | ~41 |
| LLM Quality | `tests/llm_quality/` | PythonOnly vs LLM comparison (optional, needs API key) | ~2 |
| Subjective | `tests/subjective/` | Human rating threshold validation | ~5 |
| **Total** | | | **~1,150** |

### Unit Test Coverage

| Test File | Covers |
|-----------|--------|
| test_ir.py | IR types, note/section/score structures |
| test_stochastic.py | Stochastic generator algorithm |
| test_schema.py | v1 YAML schema validation and parsing |
| test_motif.py | Motif generation and transformations |
| test_harmony.py | Chord/harmony rules |
| test_conductor.py | Conductor feedback loop |
| test_voicing.py | Voice leading and parallel fifths |
| test_verify.py | Linting and constraint verification |
| test_evaluator.py | Quality scoring |
| test_midi_reader.py | MIDI parsing back to ScoreIR |
| test_generator.py | Rule-based generator |
| test_diff.py | Score diffing |
| test_constraints.py | Constraint system |
| test_iteration.py | Iteration management |
| test_feedback.py | Feedback loop adaptations |
| test_render.py | MIDI/audio rendering |
| test_errors.py | Error handling |
| test_stem_writer.py | Per-instrument stem writing |
| test_trajectory_ir.py | Multi-dimensional trajectory IR |
| generators/test_form_planner.py | Form planning (v2.0) |
| generators/test_harmony_planner.py | Harmony planning (v2.0) |
| ir/plan/test_song_form_plan.py | SongFormPlan data structures (v2.0) |
| ir/plan/test_harmony_plan.py | HarmonyPlan data structures (v2.0) |
| ir/plan/test_musical_plan.py | MusicalPlan integration (v2.0) |
| schema/test_composition_v2.py | v2 spec schema validation (v2.0) |
| schema/test_intent.py | Intent spec (v2.0) |
| schema/test_project.py | Project spec loading (v2.0) |
| verify/test_metric_goal.py | MetricGoal typed evaluation (v2.0) |
| verify/test_recoverable.py | RecoverableDecision tracking (v2.0) |

## Running Tests

```bash
make test              # All ~1,094 tests
make test-unit         # Unit tests only
make test-integration  # Integration tests
make test-music        # Music constraint tests
make test-golden       # Golden MIDI regression tests
make all-checks        # lint + arch-lint + matrix-check + test + test-golden
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
| New plan generator | Produces valid plan, respects spec, records provenance |
| New note realizer | Produces notes from plan, respects ranges, seed reproducibility, trajectory compliance |
| New legacy generator | Generates notes, respects key/range, produces provenance, seed reproducibility |
| IR type change | Round-trip preservation (IR -> MIDI -> IR) |
| New evaluator metric | Known good/bad samples score differently, MetricGoal defines pass criteria |
| Bug fix | Minimal reproducing test case |
| Lint rule | True positive + true negative examples |
| Schema change | Valid acceptance + invalid rejection |
| Conductor adaptation | Failing metric triggers correct spec change |
| New critique rule | At least 2 tests (positive detection, negative silence) |
| CPIR type change | Plan generators produce valid plans, note realizers consume correctly |
| RecoverableDecision site | Decision is logged, not silently skipped |

## Scenario Tests

Scenario tests prove musical value, not just mechanical correctness:

- **Tension arc creates climax** — Rising trajectory -> louder peak section
- **Different keys produce different music** — C major != G major pitch classes
- **Different dynamics affect velocity** — pp << ff in average velocity
- **Seeds produce variation** — Different seeds -> different melodies
- **Same seed reproduces** — Identical seed -> identical output
- **Temperature affects variety** — High temp -> more pitch classes
- **Multi-instrument enriches** — More instruments -> more harmonic variety
- **Trajectory compliance** — When trajectory changes, generator output must change measurably

## Golden Test Protocol

When output stability matters (e.g., rule_based generator with a fixed spec):

1. Generate once and save as golden file in `tests/golden/expected/`
2. Test compares new output against golden file
3. When intentionally changing output, update golden file and document why in PR
4. Never auto-approve golden file changes
5. Run with `make test-golden`

Golden test infrastructure is located in `tests/golden/` with:
- `conftest.py` — fixtures for golden comparison
- `test_golden.py` — parameterized golden tests
- `tools/regenerate_goldens.py` — script to regenerate expected outputs
- `expected/` — committed expected output files
- `inputs/` — test input specs

## v2.0 Testing Additions

### CPIR Tests
- Plan generators produce valid `SongFormPlan` and `HarmonyPlan` objects
- `MusicalPlan` correctly combines all plan components
- Plans serialize/deserialize to JSON correctly

### MetricGoal Tests
- Each evaluation mode (binary, target, tolerance, comparison) works correctly
- MetricGoal integration with EvaluationReport

### RecoverableDecision Tests
- Decisions are properly recorded in ProvenanceLog
- Blocking vs non-blocking decision severity
- No silent fallbacks (integration test asserts all fallback sites use RecoverableDecision)

### Trajectory Compliance Tests
- Parameterized over each generator with high-tension and low-tension trajectories
- Asserts measurable difference in output (velocity, density, etc.)
