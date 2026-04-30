# Common Tasks Cookbook

Step-by-step instructions for frequent development tasks in YaO.

---

## Add a New Genre Skill

1. Create `.claude/skills/genres/<name>.md` with genre template (front-matter for YAML extraction)
2. Add at least one example spec in `specs/templates/` if the genre requires distinct parameters
3. Update Capability Matrix in PROJECT.md §3: Skills row
4. Test: `yao compose` with a spec using the genre

## Add a New Critique Rule

1. Inherit `CritiqueRule` in `src/yao/verify/critique/<role>.py`
2. Implement `detect(plan, spec) -> list[Finding]`
3. Register in `src/yao/verify/critique/registry.py`
4. Write 2+ tests (positive case detects, negative case is silent)
5. If severity=critical, add a Conductor adapter in `feedback.py`
6. Update Capability Matrix: Critique row

## Add a New Note Realizer

1. Inherit `NoteRealizerBase` in `src/yao/generators/note/<name>.py`
2. Decorate with `@register_note_realizer("<name>")`
3. Realize from `MusicalPlan`, not from `CompositionSpec`
4. Emit `RecoverableDecision` for any compromise
5. Add tests in `tests/unit/`
6. Update golden MIDI fixtures if needed
7. Update Capability Matrix: Generation row

## Add a New Plan Generator Step

This is rare and architectural. Escalate to the human first.

1. Confirm the plan component exists in `src/yao/ir/plan/`
2. Create `src/yao/generators/plan/<name>_planner.py`
3. Inherit `PlanGeneratorBase`, decorate with `@register_plan_generator("<name>")`
4. Wire into `src/yao/generators/plan/orchestrator.py`
5. Add tests
6. Update Capability Matrix: Plan IR row

## Edit the composition.yaml Schema

1. Make additive changes only when possible
2. Update Pydantic model in `src/yao/schema/composition.py` (v1) or `composition_v2.py` (v2)
3. Update at least one template in `specs/templates/`
4. Add validation test in `tests/unit/schema/`
5. If non-additive (breaking change): escalate first, add migration logic

## Add a New Evaluation Metric

1. Create evaluation function in `src/yao/verify/evaluator.py`
2. Return `list[EvaluationScore]` using `_score_via_goal()` helper
3. Wire into `evaluate_score()` at the end
4. Choose an existing dimension (`structure`, `melody`, `harmony`, `arrangement`, `acoustics`)
5. Add tests: metric exists, value is in [0,1], empty score returns empty list
6. Note: new metrics affect `pass_rate` and `quality_score` calculations

## Regenerate Golden MIDI Tests

When output changes intentionally (new contour, voicing, etc.):

```bash
python tests/golden/tools/regenerate_goldens.py \
  --reason "Description of what changed and why" \
  --confirm
```

Then verify: `make test-golden`

## PR Workflow

```bash
# 1. Make your changes
# 2. Run full validation
make all-checks

# 3. If you touched generators or rendering, regenerate goldens
make test-golden

# 4. Describe your changes
# - What changed
# - Why
# - Which Capability Matrix entries affected
# - Whether golden tests were updated (and why)
```
