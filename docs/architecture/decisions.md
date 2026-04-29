# Architecture Decision Records

## ADR-0001: IR and Provenance Types at Layer 1

**Status:** Accepted (2026-04-28)

**Context:** Generators (Layer 2) must produce `ScoreIR` objects and `ProvenanceLog` entries, which conceptually belong to Layer 3 (IR) and Layer 7 (Reflection).

**Decision:** IR data types and provenance types are treated as **foundational shared types** at Layer 1, not upper-layer components.

**Rationale:**

1. IR types are the lingua franca — every layer produces and consumes them
2. Provenance is a cross-cutting concern — all layers must participate
3. Layer numbers represent processing complexity, not data ownership

The architecture lint assigns `ir/` and `reflect/` to Layer 1.

**Consequences:** The `ir/` directory contains both Layer 1 data types (Note, ScoreIR) and future Layer 3 analysis code. Future analysis code should be clearly documented as higher-layer logic.

See full ADR at [docs/design/0001-layer-architecture.md](../design/0001-layer-architecture.md).
