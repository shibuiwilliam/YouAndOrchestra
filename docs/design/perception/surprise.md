# Design: Surprise Score

## Problem

YaO generates spec-correct music that can be predictable and flat — the Prosaic Output Problem. Listeners need a balance of predictability and novelty.

## Solution

Per-note surprise scoring via n-gram + Krumhansl tonal hierarchy. No ML dependencies.

## Components

- `SurpriseScorer` — bigram pitch-class transition model + tonal stability
- `SurpriseAnalysis` — frozen result: per-note scores, moving average, peaks, summary
- `NoteSurprise` — per-note annotation with ngram + tonal + combined scores

## Algorithm

1. Collect all notes across sections/parts, sorted by beat
2. Build bigram transition model from pitch classes
3. For each note: tonal surprise = 1 - (stability / max_stability)
4. For each note: ngram surprise = -log2(transition probability) normalized
5. Combined = tonal_weight * tonal + (1 - tonal_weight) * ngram

## Integration

- Surfaced in evaluation.json under `structure.surprise_distribution`
- Consumed by `surprise_deficit` and `surprise_overload` critique rules
- Note Realizers can query surprise to inject variation

## Thresholds

- Deficit: overall_predictability < 0.15
- Overload: overall_predictability > 0.65
- Healthy range: 0.2–0.6

## Files

- `src/yao/perception/surprise.py` — SurpriseScorer, SurpriseAnalysis
- `src/yao/verify/critique/surprise_rules.py` — SurpriseDeficitDetector, SurpriseOverloadDetector
