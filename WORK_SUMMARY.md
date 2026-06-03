# Work Summary: Fix Genre Bias and Melody Repetition

## Bottlenecks Resolved

| ID | Issue | Resolution |
|----|-------|------------|
| F-1 | Genre ID mismatch SpecCompiler vs Registry | New `yao.genre.normalization` module with 60+ aliases |
| F-2 | Only 9 genre keywords in compiler | All 30 genres reachable via `_GENRE_ALIASES` |
| F-3 | Bigram lookups failed for short genre IDs | Resolved as side-effect of F-1 (normalized IDs match) |
| F-4 | Classical-biased instrument defaults | Genre-driven `_infer_instruments` uses profile.preferred_instruments |
| F-5 | Phantom instruments in genre profiles | 15 GM instruments added + 30 profiles normalized + validation script |
| F-6 | Drums missing for rock/pop/hiphop | SpecCompiler auto-attach + Conductor safety net |
| F-7 | No theme-and-variation in melody | Motif schedule (2-8 placements/section with role-specific transforms) |
| F-8 | Math-only motif transforms | 11 new paraphrase transforms (ornament, displace, fragment, etc.) |
| F-9 | Empty motif library | 10 genre-tagged seed motifs in catalog.yaml |
| F-10 | IntentParser dead code | Out of scope (future cleanup) |

## Key Metrics

| Metric | Before | After |
|--------|--------|-------|
| Genres reliably reaching full pipeline | 2 (cinematic, ambient) | 30 |
| Motif transforms available | 9 | 20 |
| Instruments in registry | 74 | 89 |
| Genre fidelity regression tests | 0 | 12 |
| Motif recurrence regression tests | 0 | 3 |
| Total tests | 3734 | 3921 (+187) |

## Files Changed

51 files changed, +2994 / -1536 lines

### New Files
- `src/yao/genre/normalization.py` — Genre ID normalization (60+ EN + 17 JA aliases)
- `src/yao/verify/melody_variation.py` — Section similarity + motif recurrence metrics
- `tools/validate_genre_instruments.py` — CI validation of profile instrument names
- `CHANGELOG.md` — Project changelog
- `tests/scenarios/test_genre_fidelity.py` — 12-case genre resolution regression test
- `tests/scenarios/test_motif_recurrence.py` — 3-case motif recurrence test
- `tests/unit/genre/test_normalization.py` — 67 normalization unit tests
- `tests/unit/ir/plan/test_motif_transforms.py` — 31 transform unit tests
- `tests/unit/conductor/test_drum_safety_net.py` — 8 drum safety net tests
- `tests/unit/constants/test_instrument_ranges_extended.py` — 60 instrument tests
- `tests/unit/generators/plan/test_motivic_planner_schedule.py` — 6 planner tests

### Core Changes
- `src/yao/sketch/compiler.py` — Rewired genre/instrument/drum/trajectory logic
- `src/yao/generators/note/rule_based_v2.py` — 11 new motif transform implementations
- `src/yao/generators/plan/motivic_planner.py` — Motif schedule with role-weighted transforms
- `src/yao/ir/plan/motif.py` — 11 new MotifTransform enum values
- `src/yao/conductor/conductor.py` — Drum safety net
- `src/yao/constants/instruments.py` — 15 new GM instruments
- `src/yao/constants/genre_profile.py` — motif_transformation_weights field
- `genre_profiles/*.yaml` (30 files) — Instrument normalization + motif weights
