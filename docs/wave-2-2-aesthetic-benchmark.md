# Wave 2.2 — Aesthetic Benchmark Report

> **Date**: 2026-05-03
> **Tool**: `src/yao/verify/aesthetic.py`
> **Metrics**: surprise, memorability, contrast, pacing

---

## Benchmark Results

### "Good" vs "Boring" separation test

| Metric | Boring | Good | Delta | Interpretation |
|---|---|---|---|---|
| **Surprise** | 0.906 | 0.677 | -0.229 | Good piece has more predictable (stepwise) motion |
| **Memorability** | 0.000 | 1.000 | +1.000 | 4 motif placements vs none |
| **Contrast** | 0.022 | 0.383 | +0.361 | Differentiated sections vs identical |
| **Pacing** | 0.844 | 0.886 | +0.042 | Both track velocity to tension well |
| **AGGREGATE** | **0.443** | **0.737** | **+0.293** | **1.7x separation** |

### Interpretation

- **Memorability** is the strongest discriminator (binary: has motifs or doesn't)
- **Contrast** clearly separates monotonous from structured pieces
- **Surprise** is inverted from naive expectation: the "boring" piece (same chord, same note density) actually produces higher surprise because the bigram model expects stepwise motion, and C→C self-transition is rare (p=0.05)
- **Pacing** is relatively similar because both pieces' generated velocity matches their plan tension

### Surprise Index Notes

The surprise metric measures deviation from diatonic bigram expectations. Key insight: a repeating-note pattern is **surprising** in bigram terms (self-transition p=0.05), while stepwise scales are **expected** (neighbor transition p=0.25-0.30). This aligns with Huron's ITPRA model — a repeated note violates melodic expectations just as much as a wild leap.

---

## V2 Pipeline Generated Pieces

| Piece | Surprise | Memorability | Contrast | Pacing | Aggregate |
|---|---|---|---|---|---|
| 雨の夜のカフェ (jazz_ballad, Dm) | 0.72 | 0.80 | 0.35 | 0.82 | **0.67** |
| Cinematic (D minor, 6 sections) | 0.65 | 0.75 | 0.41 | 0.88 | **0.67** |
| Minimal (C major, 8 bars) | 0.58 | 0.50 | 0.28 | 0.79 | **0.54** |
| Boring baseline (no motifs) | 0.91 | 0.00 | 0.02 | 0.84 | **0.44** |

All V2-generated pieces score above the boring baseline.

---

## Conductor Feedback Integration

| Metric Failure | Adaptation Applied |
|---|---|
| Surprise too low (<0.3) | temperature += 0.2 |
| Surprise too high (>0.8) | temperature -= 0.15 |
| Memorability too low (<0.3) | Request more motif placements |
| Contrast too low (<0.2) | Differentiate section dynamics |
| Pacing mismatch (<0.6) | Sharpen trajectory arc |

---

## Dimension Weight Update

```python
# Before (v2.0)
structure: 0.25, melody: 0.30, harmony: 0.25, arrangement: 0.10, acoustics: 0.10

# After (Wave 2.2)
structure: 0.20, melody: 0.25, harmony: 0.20, aesthetic: 0.20, arrangement: 0.10, acoustics: 0.05
```

The aesthetic dimension now accounts for 20% of the quality score.
