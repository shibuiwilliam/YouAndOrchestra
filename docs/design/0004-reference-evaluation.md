# Design Note 0004: Reference-Driven Evaluation

**Status:** Implemented (Phase 1.5, PR-4)
**Layer:** 4 (Perception)
**Date:** 2026-05-05

## Summary

Reference-Driven Evaluation allows YaO to measure how closely a generated piece
matches the stylistic characteristics of positive reference works, and how far it
deviates from negative references. This operates entirely on symbolic (ScoreIR)
data, not audio.

## Architecture

```
ScoreIR ──┐
           ├──→ FeatureExtractors ──→ FeatureVector (np.ndarray)
           │         │
Reference ─┘         ├──→ ReferenceMatcher ──→ ReferenceMatchReport
                     │         (weighted Euclidean distance)
                     │
                     └──→ Conductor (Phase 6: Listening Simulation)
```

## Feature Extractors

Seven symbolic extractors produce a concatenated feature vector:

| Extractor | Dim | Description |
|-----------|-----|-------------|
| voice_leading_smoothness | 1 | Avg semitone movement between consecutive voicings |
| motivic_density | 1 | Recurring interval-trigram count per 8 bars |
| surprise_index | 1 | Normalized Shannon entropy of pitch intervals |
| register_distribution | 12 | Octave histogram (MIDI notes binned by octave) |
| temporal_centroid | 1 | Velocity-weighted position centroid in [0,1] |
| groove_pocket | 3 | Timing offset stats: mean, std, skewness |
| chord_complexity | 1 | Avg unique pitch classes per beat window |

Total concatenated dimension: 20.

All extractors implement the `FeatureExtractor` protocol and are registered
in `src/yao/perception/feature_extractors/__init__.py`.

## Distance Computation

The `ReferenceMatcher` (already existed) computes StyleVector-based distances.
The new `feature_extractors` module provides a parallel, numpy-based path for
more granular per-feature analysis. Both approaches coexist:

- **StyleVector path:** Used for backward-compatible reference evaluation via
  `ReferenceMatcher.evaluate_against_references()`.
- **FeatureExtractor path:** Used for new per-feature distance computation
  and weighted reference matching.

Weighted Euclidean distance between feature vectors:

```
d(gen, ref) = sqrt(sum(w_i * (gen_i - ref_i)^2))
```

Weights come from the active Genre Skill's evaluation weight adjustments.

## Copyright Safety

- Extractors produce only statistical summaries (histograms, entropy, averages).
- No extractor can reconstruct melody, chord progression, or lyrics.
- The `FORBIDDEN_FEATURES` blocklist in `schema/references.py` prevents
  requesting copyrightable features at both schema and runtime levels.

## Integration with Conductor

During Phase 6 (Listening Simulation), the Conductor calls:

```python
from yao.perception.feature_extractors import extract_all, extract_concatenated

features = extract_all(generated_score)
ref_features = extract_all(reference_score)
# Compare per-feature or concatenated
```

The feature distances feed into the adaptation strategy selector.

## Files

- `src/yao/perception/feature_extractors/__init__.py` — Registry and protocol
- `src/yao/perception/feature_extractors/symbolic.py` — 7 extractors
- `src/yao/perception/reference_matcher.py` — StyleVector-based matcher (pre-existing)
- `src/yao/schema/references.py` — ReferencesSpec Pydantic model (pre-existing)
- `references/catalog.yaml` — Reference library catalog (pre-existing)
- `tests/unit/perception/test_reference_matcher.py` — Tests

## Future Work

- Audio-based extractors (requires `librosa`, gated on availability)
- Feature vector caching with content-addressed storage
- Per-genre feature weight profiles loaded from Genre Skills
