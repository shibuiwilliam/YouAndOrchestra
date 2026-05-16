# A/B Testing

YaO includes a built-in A/B testing framework for comparing generation
configurations. Test hypotheses about parameter changes with statistical rigor.

## Quick Start

```bash
yao ab-test specs/templates/lofi-cafe.yaml \
  --param temperature --control 0.3 --treatment 0.7 \
  --metric overall --seeds 5
```

## Options

| Option | Required | Description |
|--------|----------|-------------|
| `spec_path` | Yes | Path to composition YAML |
| `--param` | Yes | Parameter to vary |
| `--control` | Yes | Control value |
| `--treatment` | Yes | Treatment value |
| `--metric` | No | Evaluation metric (default: `overall`) |
| `--seeds` | No | Number of seeds per variant (default: 5) |
| `--output` | No | Path to save results JSON |

## How It Works

1. Generates pieces under **control** config (N seeds)
2. Generates pieces under **treatment** config (N seeds)
3. Evaluates each piece on the specified metric
4. Computes **Cohen's d effect size** between groups
5. Reports winner with confidence level

## Output

```
==================================================
Hypothesis: Does temperature=0.7 outperform temperature=0.3?
Control (0.3):   mean=0.6234 +/- 0.0412
Treatment (0.7): mean=0.7012 +/- 0.0389
Winner: treatment
Effect size: 1.8234
Confidence: 0.625
```

## Saving Results

Use `--output results.json` to persist the full test result including
per-seed scores, effect size, and confidence.

## Programmatic API

```python
from yao.reflect.ab_test import Hypothesis, Variant, VariantResult, run_ab_test

hypothesis = Hypothesis(name="swing_test", description="...", metric="groove_pocket")
# ... collect scores ...
result = run_ab_test(hypothesis, variant_a, variant_b)
print(result.winner, result.effect_size)
```
