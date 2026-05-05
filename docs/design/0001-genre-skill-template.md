# Design Note 0001 — Genre Skill Template Standardization

## Problem Statement

**Finding Q4** (Genre-Insensitive Feedback) and **partial C3** (Melody+Harmony+Bass Ensemble Bias):
Genre Skills currently lack a standard machine-readable format. The evaluator applies uniform
weights regardless of genre, causing blues to be penalized for dissonance and deep house to be
penalized for lack of melody. Skills need YAML frontmatter with evaluation weight adjustments,
ensemble templates, and anti-patterns so the system can be genre-conditional.

## Files to Add

- `.claude/skills/genres/_template.md` — the canonical template
- `.claude/skills/genres/cinematic.md` — refactored to v2.0 template
- `.claude/skills/genres/lo_fi_hiphop.md` — new Tier-1 Skill
- `.claude/skills/genres/pop_japan.md` — new Tier-1 Skill
- `.claude/skills/genres/pop_western.md` — new Tier-1 Skill
- `.claude/skills/genres/ambient.md` — refactored to v2.0 template
- `.claude/skills/genres/deep_house.md` — new Tier-1 Skill
- `src/yao/skills/genre_loader.py` — loads and validates Skill frontmatter
- `src/yao/schema/genre_skill.py` — Pydantic model for Skill frontmatter
- `tests/unit/test_genre_skill_loader.py` — loader and validation tests

## Files to Modify

- `src/yao/verify/evaluator.py` — apply genre weight adjustments when evaluating
- `src/yao/conductor/conductor.py` — load genre skill and pass to evaluator

## Backward Compatibility

- Existing specs without `genre` field continue to work (no genre skill loaded, base weights used)
- Existing genre skill files that lack frontmatter are ignored with a warning (not a crash)

## New Tests Required

- Skill frontmatter schema validation (valid/invalid cases)
- Every Tier-1 Skill passes schema validation
- Evaluator with genre weights produces different scores than without
- Switching genre on same spec produces measurably different evaluator scores

## Acceptance Criteria (from IMPROVEMENT.md)

- Five+ genres are first-class
- Switching genre on the same composition spec produces measurably different evaluator scores

## Risks and Rollback

- Low risk: additive change, no breaking modifications to existing evaluation
- Rollback: remove genre_loader, revert evaluator weight multiplication
