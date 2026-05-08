"""Layer 2.5: Combination & Coupling.

This package contains modules that transform, couple, blend, and optimize
already-generated material. Coupling modules sit between Layer 2 (raw
generation) and Layer 3 (IR).

Import rules (enforced by arch-lint):
- May import from: Layers 0 (constants), 1 (schema, ir), 2 (generators)
- May NOT import from: Layers 3+ (perception, render, verify, reflect, conductor)

All coupling modules follow these conventions:
1. Inputs are immutable IR objects — never mutated.
2. Outputs are new IR objects with full provenance.
3. Each module is gated by a feature flag in composition.features.

See CLAUDE.md Non-Negotiable Rule 9, PROJECT.md §3.4.
"""
