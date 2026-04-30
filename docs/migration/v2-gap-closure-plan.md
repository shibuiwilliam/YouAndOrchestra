# YaO v2.0 Gap Closure Plan

> Date: 2026-04-30
> Scope: Close gaps between PROJECT.md/CLAUDE.md specs and current code

## Priority 1: Structural gaps (missing packages that specs reference)

### 1a. Create critique/ package with Finding + CritiqueRule base types
CLAUDE.md describes the critique system in detail. The types must exist even
if the 30+ rules are Phase beta. The base infrastructure is Phase alpha.

### 1b. Create sketch/ and arrange/ stub packages
CLAUDE.md lists these directories. They should exist as stubs with docstrings
explaining their Phase beta/gamma status.

### 1c. Add make test-subagent target + stub directory
CLAUDE.md Quick Reference lists this target. It should exist and pass (0 tests).

## Priority 2: Document accuracy (CLAUDE.md drift from implementation)

### 2a. Fix RecoverableDecision path in CLAUDE.md
Currently says verify/recoverable.py; actual is reflect/recoverable.py.

### 2b. Update Phase alpha checklist in CLAUDE.md
Mark completed items, fix claims about what's "being built" vs done.

### 2c. Update PROJECT.md §19.1 test count

## Priority 3: Functional improvements

### 3a. Wire load_project_specs() to support v2 specs
The loader currently only returns v1 CompositionSpec. Should auto-detect.

### 3b. Enhance harmony planner trajectory response
Currently tension only affects chord event tension_level field. Should also
influence chord complexity (more secondary dominants at high tension).
