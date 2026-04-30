# YaO v2.0 Improvement Plan

> Date: 2026-04-30
> Scope: Post Phase-alpha quality improvements
> Principle: Fix what's broken, strengthen what's weak, don't add Phase-beta features.

## Priority 1: Code Quality Violations

### P1.1 — Bare ValueError in orchestrator.py
- **File**: `src/yao/generators/plan/orchestrator.py:42`
- **Issue**: Uses `ValueError` instead of `SpecValidationError` (CLAUDE.md: "No bare ValueError")
- **Fix**: Replace with `SpecValidationError`

### P1.2 — Hardcoded tension-to-dynamics thresholds
- **File**: `src/yao/generators/note/rule_based.py:115-127`
- **Issue**: Magic numbers for tension→dynamics mapping (CLAUDE.md Rule #4)
- **Fix**: Move to `src/yao/constants/music.py` as `TENSION_TO_DYNAMICS`

### P1.3 — Inline `import re` in harmony_planner
- **File**: `src/yao/generators/plan/harmony_planner.py:193`
- **Issue**: `import re` inside function body
- **Fix**: Move to module level

## Priority 2: Missing Unit Tests

### P2.1 — Note realizer unit tests
- **Gap**: `tests/unit/generators/note/` has no test files
- **Fix**: Create `test_rule_based_realizer.py` and `test_stochastic_realizer.py`
- **Coverage**: Plan-to-v1 conversion, realize() with minimal plan, edge cases

### P2.2 — Plan orchestrator unit test
- **Gap**: Only tested via integration; no isolated unit test
- **Fix**: Add to existing plan test directory

## Priority 3: Architecture Lint Enhancement

### P3.1 — Detect note realizer → spec shortcut
- **Gap**: architecture_lint.py doesn't specifically catch note/ → schema/composition imports
- **Fix**: Add explicit rule for generators/note/ files

## Priority 4: Documentation Gaps

### P4.1 — Progress document
- Create `docs/migration/v2-progress.md` recording Phase-alpha completion status
