# ADR-0001: Layer Architecture and Dependency Rules

**Status:** Accepted
**Date:** 2026-04-28
**Author:** YaO Development Team

## Context

YaO's 7-layer architecture (PROJECT.md §3) defines strict downward-only dependency flow. However, during Phase 0 implementation, a design tension emerged: generators (Layer 2) must produce ScoreIR objects and ProvenanceLog entries, which nominally belong to Layer 3 (IR) and Layer 7 (Reflection) respectively.

## Decision

We treat IR data types and provenance types as **foundational shared types** (effectively Layer 1), not as upper-layer components:

- `ir/` module data structures (Note, Part, Section, ScoreIR) — Layer 1
- `reflect/provenance.py` types (ProvenanceRecord, ProvenanceLog) — Layer 1
- IR processing/analysis capabilities — Layer 3 (when added)
- Reflection learning capabilities — Layer 7 (when added)

The architecture lint (`tools/architecture_lint.py`) assigns:
```
constants: 0
schema: 1
ir: 1        # data types are shared
reflect: 1   # provenance types are cross-cutting
generators: 2
perception: 4
render: 5
verify: 6
```

## Rationale

1. **IR types are the lingua franca** — every layer produces or consumes them. Placing them at Layer 3 would mean generators (Layer 2) couldn't produce their own output.

2. **Provenance is a cross-cutting concern** — Principle 2 (explainability) requires ALL layers to record provenance. Making provenance Layer 7 would prevent any layer from logging.

3. **The layer number represents processing complexity, not data ownership** — Layer 3's identity is about IR *analysis and transformation*, not about owning the Note dataclass.

## Alternatives Considered

1. **Separate data types into a `models/` package at Layer 0** — Rejected because it would fragment related code and diverge from PROJECT.md's directory structure.

2. **Allow explicit exceptions in the lint tool** — Rejected because exception lists erode architectural discipline.

3. **Move generators to Layer 3+** — Rejected because it would invert the conceptual hierarchy (generators create; IR represents; verifiers evaluate).

## Consequences

- The `ir/` and `reflect/` directories contain both Layer-1 types and (future) higher-layer logic. The lint tool cannot distinguish between them at the directory level.
- Future IR analysis code (e.g., complex harmonic analysis using music21) should be clearly documented as Layer 3 logic, even though it lives in the `ir/` directory.
- This decision should be revisited if `ir/` grows to contain substantial analysis code that genuinely belongs at a higher layer.
