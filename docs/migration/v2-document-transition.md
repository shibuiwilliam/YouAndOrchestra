# Document Transition v1.0 → v2.0

## When
2026-04-30

## What changed
- PROJECT.md: v2.0 Japanese version with CPIR architecture, Capability Matrix §5, 6 principles
- CLAUDE.md: v2.0 with 7+6 rules, CPIR-aware directories, anti-patterns, cookbook
- Capability Matrix: Updated from aspirational (🔴 for implemented features) to reality-reflecting
- capability_matrix_mapping.yaml: Rewritten to match Japanese feature names in PROJECT.md v2.0

## Capability Matrix corrections (aspirational → reality)
- FormPlanner: 🔴 → ✅ (implemented in generators/plan/form_planner.py)
- HarmonyPlanner: 🔴 → ✅ (implemented in generators/plan/harmony_planner.py)
- MetricGoal type system: 🔴 → ✅ (7 types in verify/metric_goal.py)
- RecoverableDecision logging: 🔴 → ✅ (9 codes in reflect/recoverable.py)
- composition.yaml v2: ⚪ → ✅ (22 Pydantic models in schema/composition_v2.py)
- Evaluator: updated to reflect quality_score + MetricGoal basis
- Conductor: updated to reflect v2 pipeline routing
- Added CPIR and QA sections to matrix

## What does NOT change
- src/ — no code changes
- tests/ — no test changes
- .claude/agents/, .claude/commands/, .claude/skills/ — unchanged

## Verification
- [x] Capability matrix check passes with updated mapping
- [x] All internal markdown links verified
- [x] git diff src/ is empty
- [x] git diff tests/ is empty
- [x] make all-checks still green
