# Wave 3.5 Rating Collection Report

> **Date**: 2026-05-03
> **Composition**: demo-cinematic / v001
> **Raters**: 3 (musician_a, musician_b, listener_c)

## Individual Ratings

| Dimension | musician_a | musician_b | listener_c | Average |
|---|---|---|---|---|
| Memorability | 7.0 | 6.0 | 8.0 | **7.0** |
| Emotional fit | 8.0 | 7.5 | 7.0 | **7.5** |
| Technical quality | 6.5 | 7.0 | 6.0 | **6.5** |
| Genre fitness | 7.0 | 8.0 | 7.0 | **7.3** |
| Overall | 7.5 | 7.0 | 7.0 | **7.2** |

## Free-Text Notes

- **musician_a**: "Good emotional arc, but bridge section feels underdeveloped. Motif recurrence is effective."
- **musician_b**: "Genre-appropriate chord choices. Voice leading could be smoother in the chorus."
- **listener_c**: "Catchy hook in the verse. Would benefit from more dynamic contrast."

## Aggregated UserStyleProfile

After running `yao reflect ingest`:

| Dimension | Preferred Range | Confidence | Sources |
|---|---|---|---|
| memorability | [5.9, 7.9] | 0.6 | 6 |
| emotional_fit | [6.9, 7.9] | 0.6 | 6 |
| technical_quality | [5.9, 7.4] | 0.6 | 6 |
| genre_fitness | [6.7, 7.7] | 0.6 | 6 |
| overall | [6.9, 7.4] | 0.6 | 6 |

## Insights

1. **Strongest dimension**: Emotional fit (avg 7.5) — the composition matches its intended mood
2. **Weakest dimension**: Technical quality (avg 6.5) — voice leading and dynamic contrast need work
3. **Consensus**: Overall scores cluster tightly (7.0-7.5), indicating agreement among raters
4. **Actionable feedback**: Bridge section, voice leading, dynamic contrast are improvement targets

## Workflow Demonstrated

```
yao rate outputs/projects/demo-cinematic/iterations/v001 --rater musician_a
yao rate outputs/projects/demo-cinematic/iterations/v001 --rater musician_b
yao rate outputs/projects/demo-cinematic/iterations/v001 --rater listener_c
yao reflect ingest tests/subjective/ratings/
```

The rating → profile → generation loop is now operational. Future compositions can reference the UserStyleProfile to calibrate trajectory defaults toward the user's demonstrated preferences.
