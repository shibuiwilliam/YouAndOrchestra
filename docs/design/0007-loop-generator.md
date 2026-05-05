# Design Note 0007: Loop-First Generator

## Summary

Introduces the `loop_evolution` generator strategy that builds compositions from a core loop, evolving it across sections through layer additions/subtractions and modular arrangement.

## Motivation

Many genres (lo-fi hip-hop, deep house, ambient, trip-hop, drum and bass) are structurally built on loops rather than through-composed sections. The existing rule-based and stochastic generators assume a linear section-by-section approach with independent material per section. A loop-first generator better serves these genres.

## Design

### Core Concepts

1. **Core Loop**: A short (default 4-bar) pattern generated per instrument
2. **Arrangement String**: A space-separated sequence of block tokens (e.g., "A B C drop A B C") that defines the macro structure
3. **Layer Evolution**: Instruments are added/removed across blocks to create dynamic interest
4. **Seamless Boundaries**: The loop is designed to repeat without audible seams

### Arrangement Tokens

- Letter tokens (A, B, C): Full instrument set with variation per repetition
- `drop`: Only bass/rhythm instruments active (creates tension/release)
- `build`: Gradual layering — instruments added incrementally

### Architecture

```
CompositionSpec
    → parse_arrangement() → list[ArrangementBlock]
    → generate_core_loops() → dict[instrument, list[Note]]
    → build_sections_from_blocks() → list[Section]
    → ScoreIR
```

### Seamlessness Evaluator

`src/yao/verify/seamlessness.py` provides `evaluate_seamlessness(score) -> float`:
- Checks no notes are cut off at boundaries (40% weight)
- Checks energy continuity (30% weight)
- Checks pitch continuity (30% weight)

## Files

- `src/yao/generators/loop_evolution.py` — Generator implementation
- `src/yao/verify/seamlessness.py` — Seamlessness evaluator
- `tests/unit/test_loop_evolution.py` — Unit tests

## Layer Placement

- Generator: Layer 2 (Generation)
- Seamlessness evaluator: Layer 6 (Verification)
