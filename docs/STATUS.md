# STATUS.md — What Actually Exists on Disk

> **Read this before trusting file/type references in CLAUDE.md or PROJECT.md.**
> Those docs describe a more-finished (and partly fictional) system. This ledger
> is the ground truth as of the v2.x improvement program (Increments 1–16).
> When they conflict, **this file wins** for "does X exist / how does it work."

---

## Generation pipeline (the important part)

- **Default path is the plan-consuming v2 realizer.** `note.base.resolve_realizer_name`
  routes `stochastic`→`stochastic_v2`, `rule_based`→`rule_based_v2`, and any
  unknown strategy → `rule_based_v2`. Only `stochastic_v2` / `rule_based_v2` are
  registered in `NOTE_REALIZERS`.
- **The legacy *note realizers* were deleted** (`note/stochastic.py`,
  `note/rule_based.py`). The random-walk `StochasticGenerator` /
  `RuleBasedGenerator` (`generators/stochastic.py`, `generators/rule_based.py`)
  still exist but are **`.. deprecated::` — NOT in the production path**. Every
  user-facing command (`compose`, `conduct`, `evaluate`, `ab-test`, `explain`,
  `regenerate-section`, `morph`) routes through
  `generators/legacy_adapter.generate_via_v2_pipeline`. The legacy generators
  are retained only as **test fixtures** and as the **random-walk baseline** in
  metric-discrimination tests — do not use them for generation.
- The v2 realizers produce, by default: theme statement + cross-section thematic
  recall (`recall_melody_from` honored via `original_spec`), full voice-led,
  density-aware arrangement (melody + harmony + bass), walking bass for genres
  with `bass_motion_style: walking`, and an authentic V–I cadence at the end.

## IR types (correct names)

- Drums: **`DrumHit` / `DrumPattern`** in `ir/drum.py` (GM map at `ir/drum.py`).
  There is **no** `DrumNote`/`DrumPart`/`DrumPiece` (CLAUDE.md is wrong).
- Voicing: `ir/voicing.py` has `Voicing`, parallel-motion detectors, and
  `voice_distance`. There is **no** `VoicingStyle` enum and no
  quartal/shell/rootless/power realization. Voice-leading for accompaniment
  lives in `generators/note/accompaniment.py` (`voice_lead_sequence`).
- Harmony: `ir/harmony.py` `realize()` + `diatonic_quality()` (now mode-aware —
  church modes get correct triad qualities, not all-major).

## Genre system

- Canonical registry: **`genre_profiles/*.yaml`** (30), loaded by
  `constants/genre_profile.py::get_genre_profile` (a frozen `GenreProfile`).
- A separate `UnifiedGenreProfile` (schema) is loaded by
  `schema/genre_profile_loader.load_unified_genre_profile(id)` and carries an
  optional `evaluation:` block (weights / `percussion_centric`) used for
  genre-aware scoring. There is **no** `constants/genre_profiles.py` or
  `constants/genres.py`.

## Evaluation (`verify/evaluator.py`)

- `evaluate_score(score, spec, trajectory, genre_profile=None, plan=None)`.
- Base metrics (structure/melody/harmony/rhythm) always run. When `plan` is
  passed (conductor + compose do): aesthetic dimension (surprise/memorability/
  contrast/pacing via `verify/aesthetic.py`), `motif_development_index`, and
  `voice_leading_smoothness` are added. `genre_profile` applies genre weights /
  `percussion_centric` reweighting.
- Genre evaluators as *subclasses* (`verify/evaluators/`, `JazzEvaluator`, …)
  described in CLAUDE.md §19 **do not exist**; genre-awareness is via weights.

## Known-fictional in CLAUDE.md / PROJECT.md (do not build on these)

- `constants/{drums,drum_patterns,groove_templates,micro_timing,genres,genre_profiles,phrase_library}.py`
  — real equivalents: `ir/drum.py`, top-level `drum_patterns/*.yaml`,
  `grooves/*.yaml`, `genre_profiles/*.yaml`.
- `phrase_library.py` / `PhraseTemplate` / `PHRASE_LIBRARY` — not present.
- `perception/*` and `reflect/style_profile.py` learning loop — implemented but
  not wired into the default loop (inert).
- "Trained per-genre Markov models" / licensed corpus — the models are
  hand-authored CC0 tables; the reference library is self-generated.

## Improvement program delivered (Increments 1–16)

Integrity (keep-best iteration, no silent no-op adaptations, swing applied,
directional metric pass) → thematic recurrence → v2 realizers arrange →
voice-leading → **default flip to the plan realizer** → aesthetic dimension
wired → density-aware arrangement → `motif_development_index` →
`voice_leading_smoothness` → resolver hardening → genre-aware evaluation +
legacy realizer retirement → authentic cadences → walking bass → minor-key
harmonic-V → modal diatonic-quality fix → `yao compose` routed through v2.

See `PROJECT_IMPROVEMENT.md` and `IMPLEMENTATION_PLAN.md` for details and the
remaining backlog.
