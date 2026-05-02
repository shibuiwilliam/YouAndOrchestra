# Baseline Violations — v3.0 Honesty Tooling

> **Date**: 2026-05-03
> **Run by**: Claude Code (Wave 1 Sprint W1)
> **Purpose**: Establish the "before" state for all v3.0 honesty checks.
> **All 5 tools pass execution** (exit 0 for non-strict tools, exit 1 for strict-now tools).

---

## Summary

| Tool | Exit Code | Violations | Status |
|---|---|---|---|
| `honesty-check` | 0 | 0 errors, 4 warnings, 4 infos | WARN (no ✅ stubs) |
| `backend-honesty` | 1 | 2 violations | FAIL (immediate) |
| `plan-consumption` | 0 | 2 failures (0% and 29%) | WARN (Wave 1.4) |
| `skill-grounding` | 0 | 14 ungrounded / 22 total | WARN (Wave 2.1) |
| `critic-coverage` | 0 | 2 severity gaps (critical, suggestion) | WARN (Wave 1.1) |

**Total violation count: 24**

---

## 1. honesty-check (exit 0)

Checked: 7 features | Passed: 1 | Errors: 0 | Warnings: 4 | Info: 4

No ✅ features are stubs (all known stubs already marked 🟡 in FEATURE_STATUS.md).

### Warnings (not blocking, but inform Wave priorities):
- SpecCompiler: No Japanese support (0 CJK characters)
- SpecCompiler: Only 23 mood keywords (keyword-only, no LLM)
- NoteRealizer: Converts MusicalPlan to v1 spec via _plan_to_v1_spec
- DAW MCP: Stub indicator in docstring

### Info (acknowledged 🟡, expected):
- AnthropicAPIBackend: Silent fallback to PythonOnly
- ClaudeCodeBackend: Silent fallback to PythonOnly
- Genre Skills: 22 files, 0 references from src/
- DAW MCP: Always returns disconnected

---

## 2. backend-honesty (exit 1 — IMMEDIATE FIX REQUIRED)

Backends: 3 | Passed: 1 | Violations: 2

| Backend | Violation |
|---|---|
| `AnthropicAPIBackend` | Uses fallback but missing `is_stub` attribute |
| `ClaudeCodeBackend` | Uses fallback but missing `is_stub` attribute |
| `PythonOnlyBackend` | PASS (no fallback, legitimate implementation) |

**Fix**: Add `is_stub = True` to both stub backends.

---

## 3. plan-consumption (exit 0, WARN)

Realizers: 2 | Passed: 0 | Failed: 2

| Realizer | Consumed | Ratio | Legacy Adapter |
|---|---|---|---|
| `RuleBasedNoteRealizer` | intent_normalized, form | 29% | YES |
| `StochasticNoteRealizer` | (none) | 0% | YES |

Both realizers use `_plan_to_v1_spec()` to convert MusicalPlan to v1 CompositionSpec.
This will become a hard failure after Wave 1.4 completes.

---

## 4. skill-grounding (exit 0, WARN)

Skills: 22 | Grounded: 8 | Ungrounded: 14

### Grounded (referenced from src/):
- ambient, cinematic, baroque, romantic, jazz_ballad, blues, funk, jazz_swing

### Ungrounded (no src/ references):
- acoustic_folk, edm_house, synthwave, film_score_dramatic, game_bgm_rpg,
  game_8bit_chiptune, j_pop, lofi_hiphop, neoclassical, rock_classic,
  arab_maqam, bossa_nova, celtic_traditional, indian_classical_hindustani

This will become a hard failure after Wave 2.1 completes.

---

## 5. critic-coverage (exit 0, WARN)

Rules: 19 | Severities covered: 2/4

| Severity | Rules | Effective | Status |
|---|---|---|---|
| critical | 0 | 0 | GAP |
| major | 9 | 8 (1 silent on empty) | OK |
| minor | 10 | 9 (1 silent on empty) | OK |
| suggestion | 0 | 0 | GAP |

No rules emit `critical` or `suggestion` severity findings.
2 rules are silent when MotifPlan is empty (MotifRecurrenceDetector, MotifAbsenceDetector).

This will become a hard failure after Wave 1.1 completes.

---

## Wave 1 Action Items (derived from baseline)

### Immediate (Sprint W1):
- [ ] Add `is_stub = True` to `AnthropicAPIBackend` and `ClaudeCodeBackend`

### Wave 1.1:
- [ ] Add at least 1 critique rule with `Severity.CRITICAL`
- [ ] Add at least 1 critique rule with `Severity.SUGGESTION`
- [ ] Ensure MotifRecurrenceDetector works when MotifPlan.seeds is non-empty

### Wave 1.4:
- [ ] `RuleBasedNoteRealizerV2`: consume 80%+ of MusicalPlan fields directly
- [ ] Remove _plan_to_v1_spec dependency from primary realization path

### Wave 2.1:
- [ ] Implement `src/yao/skills/loader.py` (GenreProfile, SkillRegistry)
- [ ] Integrate 14 ungrounded skills into generation pipeline

---

## Tracking

This file will be compared against future runs to measure gap closure.
Target: **0 violations** by end of Wave 2.
