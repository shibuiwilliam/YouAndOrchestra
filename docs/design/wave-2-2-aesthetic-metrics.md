# Design: Wave 2.2 — Aesthetic Evaluation Metrics

> **Date**: 2026-05-03
> **Status**: Implementation
> **Sprint**: Wave 2.2

---

## 1. The Problem

Current evaluation (evaluator.py) measures **formal correctness**: pitch range, stepwise motion,
section count, consonance ratio. These metrics pass for music that is technically correct
but emotionally dead — a repeating C-E-G arpeggio scores well on consonance and structure.

## 2. Four Aesthetic Metrics

Based on Huron's ITPRA model (Imagination-Tension-Prediction-Reaction-Appraisal):

### 2.1 Surprise Index

**What**: Average information content (negative log probability) of melodic transitions.
**Formula**: `mean(-log2(P(note_i | note_{i-1})))` using diatonic bigram model.
**Range**: [0, ∞) but typical 1.0–4.0.
**Normalized**: `clamp(raw / 4.0, 0, 1)` → [0, 1].
**Target**: Should correlate with `1 - predictability_trajectory`.
**Interpretation**: 0.0 = completely predictable, 1.0 = maximally surprising.

### 2.2 Memorability Index

**What**: How recurring and distinctive the motifs are.
**Formula**: `mean(min(recurrence/4, 1.0) * identity_strength)` for all seeds.
**Range**: [0, 1].
**Target**: ≥ 0.5 for good pop, ≥ 0.3 for ambient.
**Interpretation**: 0.0 = no memorable themes, 1.0 = highly recurrent strong motifs.

### 2.3 Contrast Index

**What**: Mean distance between adjacent sections' characteristics.
**Formula**: `mean(euclidean_distance(style_vector(s_i), style_vector(s_{i+1})))` normalized.
**Range**: [0, 1].
**Target**: 0.3–0.7 (too low = monotonous, too high = incoherent).
**Interpretation**: 0.0 = all sections identical, 1.0 = extreme contrast.

### 2.4 Pacing Index

**What**: How well the tension arc matches the intended trajectory.
**Formula**: `1.0 - mean(|actual_tension(bar) - planned_tension(bar)|)`.
**Range**: [0, 1].
**Target**: ≥ 0.7.
**Interpretation**: 0.0 = tension completely wrong, 1.0 = perfect arc match.

## 3. Integration into EvaluationScore

New dimension: `"aesthetic"` added to `_DIMENSION_WEIGHTS`:
```
structure: 0.20, melody: 0.25, harmony: 0.20,
aesthetic: 0.20, arrangement: 0.10, acoustics: 0.05
```

## 4. Conductor Feedback

| Metric failure | Adaptation |
|---|---|
| Surprise too low | Increase temperature |
| Surprise too high | Decrease temperature |
| Memorability too low | Request more motif placements |
| Contrast too low | Differentiate section dynamics |
| Pacing mismatch | Adjust trajectory waypoints |
