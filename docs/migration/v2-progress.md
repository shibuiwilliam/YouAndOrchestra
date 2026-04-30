# YaO v2.0 Migration Progress

> Append-only log. Each entry records a completed step.

## Phase Alpha (Steps 1–8)

### Step 1: Capability Matrix ✅ (2026-04-30)
- PROJECT.md §4 matrix factualised against code
- `tools/capability_matrix_check.py` + mapping.yaml
- `make matrix-check` target
- README/CLAUDE.md numeric claims replaced with matrix links

### Step 2: CompositionSpecV2 ✅ (2026-04-30)
- 11-section v2 schema in `src/yao/schema/composition_v2.py`
- 3 v2 templates in `specs/templates/v2/`
- v1→v2 migration tool in `tools/migrate_spec_v1_to_v2.py`
- 62 tests

### Step 3: Intent + Trajectory ✅ (2026-04-30)
- `src/yao/schema/intent.py` — IntentSpec with keyword extraction
- `src/yao/ir/trajectory.py` — 5-dimension MultiDimensionalTrajectory
- `src/yao/schema/project.py` — CompositionProject aggregator
- Trajectory compliance tests with 3 xfail (v1 limitations documented)
- 43 tests

### Step 4: CPIR (Layer 3a) ✅ (2026-04-30)
- `src/yao/ir/plan/` — SongFormPlan, HarmonyPlan, MusicalPlan
- Skeleton files for Phase beta (motif, phrase, drums, arrangement)
- Architecture lint updated for Layer 3a
- 27 tests

### Step 5: MetricGoal Type System ✅ (2026-04-30)
- `src/yao/verify/metric_goal.py` — 7 goal types
- Evaluator refactored to use MetricGoal internally
- Consonance "too high" absurdity fixed (now AT_LEAST, not TARGET_BAND)
- 34 tests

### Step 6: RecoverableDecision ✅ (2026-04-30)
- `src/yao/reflect/recoverable.py` + `recoverable_codes.py`
- ProvenanceLog extended with recoverable tracking
- 14 silent fallbacks converted in both generators
- 23 tests (unit + integration)

### Step 7: Generator Split ✅ (2026-04-30)
- `src/yao/generators/plan/` — PlanGeneratorBase, FormPlanner, HarmonyPlanner, Orchestrator
- `src/yao/generators/note/` — NoteRealizerBase, RuleBasedRealizer, StochasticRealizer
- Legacy adapter bridges v1 specs to v2 pipeline
- Full pipeline operational: Spec → CPIR → ScoreIR
- 21 tests

### Step 8: Golden MIDI Tests ✅ (2026-04-30)
- 6 golden baselines (3 specs × 2 realizers)
- Bit-exact comparison with MidiDiff reporting
- `make test-golden` target
- Regeneration script with --reason + --confirm required

### Post-Alpha Quality Pass ✅ (2026-04-30)
- Bare ValueError replaced with SpecValidationError in orchestrator
- Hardcoded tension thresholds extracted to constants/music.py
- Note realizer unit tests added (14 tests)
- Architecture lint enhanced: Rule A (note realizer → spec shortcut detection)
- Inline import cleaned up in harmony_planner

### Gap Closure Pass ✅ (2026-04-30)
- Created `src/yao/verify/critique/` — Finding, CritiqueRule, CritiqueRegistry (15 tests)
- Created `src/yao/sketch/__init__.py` stub (Phase delta)
- Created `src/yao/arrange/__init__.py` stub (Phase gamma)
- Created `tests/subagent_evals/` + `make test-subagent` target
- Fixed CLAUDE.md: RecoverableDecision path (verify/ → reflect/)
- Updated CLAUDE.md Phase alpha checklist (⏳ → ✅ for all completed items)
- Updated PROJECT.md §19.1 test count (linked to matrix, no hardcoded number)
- Updated `load_project_specs()` to auto-detect v1/v2
- Added `subagent` pytest marker to pyproject.toml

### Matrix Accuracy Pass ✅ (2026-04-30)
- Fixed stale Capability Matrix rows:
  - arrange/ note updated (stub exists now)
  - capability_matrix_check 🔴 → ✅ (tool exists and works)
  - Unit test count 212 → 436
  - Integration test count 2 → 15
  - Scenario test count 10 → 16
  - Evaluator description updated (now has quality_score + MetricGoal)
- Fixed recoverable.py path in PROJECT.md §20 directory tree (verify/ → reflect/)
- Fixed recoverable.py path in CLAUDE.md key directories (verify/ → reflect/)
- Aligned capability_matrix_mapping.yaml with renamed evaluator row

### Functional Quality Pass ✅ (2026-04-30)
- Harmony planner now tension-responsive: high tension prefers dominant/secondary-dominant
  chords; low tension prefers tonic/subdominant. Chord distribution varies with trajectory.
- Conductor wired to v2 pipeline: compose_from_spec() now calls generate_via_v2_pipeline()
  (Spec → CPIR → ScoreIR) instead of legacy get_generator() direct path.
- quality_score logged in conductor iteration output.
- 3 new harmony tension tests + conductor note realizer imports added.
- Lint fixes: stochastic contour ternaries, test line length.

## Current Totals
- Source files: 79
- Tests: 492 (486 main + 6 golden)
- Capability Matrix ✅ entries: 43
