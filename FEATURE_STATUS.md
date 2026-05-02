# YaO Feature Status

> Last verified: 2026-05-03 by v3.0 implementation audit + `make honesty-check`
> This file is the **single source of truth** for what YaO can do.
> README.md, CLAUDE.md, and PROJECT.md link here instead of restating capabilities.
> **v3.0 audit**: 8 items downgraded from ✅ to 🟡, 1 upgraded 🟡 → ✅ (see docs/audit/2026-05-status-reaudit.md)

## Status Legend

- ✅ **Stable** — Working with tests, safe to depend on
- 🟢 **Working but limited** — Core works, check edge cases noted
- 🟡 **Partial** — Some paths work, read implementation before depending
- ⚪ **Designed, not started** — Specified but not yet built
- 🔴 **Identified gap** — Known need, no implementation

---

## Spec / Input

| Feature | Status | Tests | Notes |
|---|---|---|---|
| YAML spec parsing (Pydantic v1) | ✅ | tests/unit/test_schema.py | CompositionSpec, SectionSpec, InstrumentSpec; all 4 templates load |
| YAML spec parsing (Pydantic v2) | ✅ | tests/unit/schema/test_composition_v2.py | 22 Pydantic models, 11 sections |
| Natural language → spec (`yao conduct`) | 🟢 | tests/unit/test_conductor.py | English keyword dict; explicit key regex ("in D minor"); no Japanese |
| trajectory.yaml multi-dim coupling | ✅ | tests/scenarios/test_trajectory_compliance.py | All 5 dims defined; GenerationParams derived per bar; both generators respond to tension (velocity+leaps), density (rhythm), register_height (octave) |
| constraints with scoping | ✅ | tests/unit/test_constraints.py | must / must_not / prefer / avoid with global, section, instrument, bars scopes |
| intent.md | 🟡 | tests/unit/schema/test_intent.py | IntentSpec exists; not linked to auto-evaluation |
| references.yaml | ✅ | tests/unit/perception/test_reference_matcher.py, test_style_vector.py | PrimaryReference + NegativeReference with rights_status validation; ALLOWED_FEATURES/FORBIDDEN_FEATURES allowlist/blocklist; StyleVector (6 abstract features, no melody/chords); ReferenceMatcher with sha256 cache; defense-in-depth at schema + runtime |
| negative-space.yaml | 🟡 | — | Schema exists; reflection mechanism incomplete |
| production.yaml | 🟡 | — | Schema exists; mix chain not implemented |

## Generation

| Feature | Status | Tests | Notes |
|---|---|---|---|
| rule_based generator | ✅ | tests/unit/test_generator.py | Deterministic; trajectory: tension → velocity only |
| stochastic generator | ✅ | tests/unit/test_stochastic.py | seed / temperature / contour; trajectory: tension → pitch+leaps, density → rhythm, register_height → octave |
| Generator registry | ✅ | tests/unit/test_generator.py | @register_generator decorator |
| drum_patterner | ✅ | tests/unit/generators/test_drum_patterner.py | 8 genre patterns in drum_patterns/; swing, ghost notes, trajectory density |
| counter_melody | ✅ | tests/unit/generators/test_counter_melody.py | Species counterpoint; contrary motion preferred; density_factor control |
| markov generator | ✅ | tests/unit/test_markov.py | n-gram bigram transitions on scale degrees; diatonic + pentatonic models; temperature scaling; trajectory coupling (tension/density/register_height); lazy-loaded YAML models |
| twelve_tone generator | ✅ | tests/unit/generators/test_twelve_tone.py | 12-tone serial: P/I/R/RI row transformations; auto-generated or specified row; per-section transform cycling |
| process_music generator | ✅ | tests/unit/generators/test_process_music.py | Process music: phasing/additive/subtractive; cell auto-generation from key; temperature controls process type |
| constraint solver generator | ✅ | tests/unit/generators/test_constraint_solver.py | Backtracking CSP; key+range+stepwise constraints; 5s timeout; GenerationTimeoutError |

## IR (Intermediate Representation)

| Feature | Status | Tests | Notes |
|---|---|---|---|
| ScoreIR (Note, Part, Section) | ✅ | tests/unit/test_ir.py | Frozen dataclasses |
| Motif IR | ✅ | tests/unit/test_motif.py | Motif, invert, retrograde, transpose |
| Harmony IR | ✅ | tests/unit/test_harmony.py | diatonic_quality, chord functions |
| Voicing IR | ✅ | tests/unit/test_voicing.py | Voice-crossing detection |
| Timing IR | ✅ | tests/unit/test_ir.py | bars_to_beats, beats_to_bars |
| Notation IR | ✅ | tests/unit/test_ir.py | note_name_to_midi, midi_to_note_name |
| Trajectory IR (5-dim) | ✅ | tests/unit/test_trajectory_ir.py | MultiDimensionalTrajectory with TrajectoryCurve; bezier/stepped/linear |
| DrumPattern IR | ✅ | tests/unit/ir/test_drum.py | DrumHit, DrumPattern, KitPiece, GM_DRUM_MAP; 15 kit pieces mapped |
| Performance Expression IR (Layer 4.5) | ✅ | tests/unit/ir/test_expression.py | NoteExpression, PerformanceLayer, RubatoCurve, BreathMark, PedalCurve; integrated into Conductor pipeline and MIDI writer; micro_timing/dynamics/accents applied to MIDI output; v3.0 Wave 3.1 complete |
| Performance Realizers (4 subtypes) | ✅ | tests/unit/generators/performance/ (20 tests) | ArticulationRealizer, DynamicsCurveRenderer, MicrotimingInjector, CCCurveGenerator; pipeline.py merges them; called from Conductor after note realization; PerformanceLayer passed to MIDI writer; v3.0 Wave 3.1 complete |

## Rendering

| Feature | Status | Tests | Notes |
|---|---|---|---|
| MIDI writer + per-instrument stems | ✅ | tests/unit/test_render.py, test_stem_writer.py | |
| Audio renderer (FluidSynth) | ✅ | tests/unit/test_render.py | Optional dependency; requires SoundFont |
| MIDI reader | ✅ | tests/unit/test_midi_reader.py | MIDI → ScoreIR round-trip |
| Iteration management | ✅ | tests/unit/test_iteration.py | v001/v002/... auto-versioning |
| MusicXML writer | ✅ | tests/unit/render/test_musicxml_writer.py | ScoreIR → music21 → .musicxml; instruments, key, time sig, tempo, dynamics; PerformanceLayer accent/tenuto markings |
| LilyPond / PDF writer | ✅ | tests/unit/render/test_lilypond_writer.py | ScoreIR → .ly text; MIDI→LilyPond pitch/duration conversion; lilypond binary subprocess for PDF; warn-and-skip if not installed |

## Critique / Verification

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Music lint | ✅ | tests/unit/test_verify.py | Parallel fifths, voice leading |
| Score analyzer | ✅ | tests/unit/test_verify.py | Structure, melody, harmony analysis |
| Evaluator (10 metrics, 3 dims) | ✅ | tests/unit/test_evaluator.py | MetricGoal-based; structure / melody / harmony |
| MetricGoal type system | ✅ | tests/unit/verify/test_metric_goal.py | 7 goal types (AT_LEAST, BETWEEN, etc.) |
| Score diff | ✅ | tests/unit/test_diff.py | Modified notes tracking |
| Constraint checker | ✅ | tests/unit/test_constraints.py | Range / voice constraints |
| Critique rules (structured) | ✅ | tests/unit/verify/test_critique_rules.py | 15 rules across 6 roles (structural 3, harmonic 3, melodic 3, rhythmic 2, arrangement 2, emotional 2) |
| Critique registry + Finding types | ✅ | tests/unit/verify/test_critique.py | CritiqueRule base, Finding dataclass, CritiqueRegistry |
| RecoverableDecision logging | ✅ | tests/unit/verify/test_recoverable.py | 9 registered codes; all known silent fallbacks wrapped; check_silent_fallback.py for detection |

## Conductor

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Generate-evaluate-adapt loop | ✅ | tests/unit/test_conductor.py | compose_from_description, compose_from_spec |
| Section-level regeneration | ✅ | tests/unit/test_conductor.py | regenerate_section via v2 pipeline |
| Critic integration in loop | ✅ | tests/unit/test_conductor.py | CRITIQUE_RULES.run_all() called; findings → adaptations |
| Feedback adaptations (evaluator) | ✅ | tests/unit/test_feedback.py | Temperature, strategy, dynamics adaptations |
| Feedback adaptations (critic findings) | ✅ | tests/unit/test_feedback.py | section_monotony, climax_absence, harmonic_monotony, cliche_progression, intent_divergence |
| SpecCompiler (NL → spec) | 🟢 | tests/unit/sketch/ (38 tests), tests/integration/test_spec_compiler_ja.py (22 tests) | Three-stage fallback (LLM → Keyword → Default); Japanese emotion vocabulary (50+ words, valence×arousal); English 23 keywords preserved; auto language detection; LLM stage ready but requires AnthropicAPIBackend (Wave 1.2); Provenance recorded |
| Multi-candidate Orchestrator | ✅ | tests/unit/conductor/test_multi_candidate.py | N candidates parallel via ThreadPool; critic severity ranking (critical=10,major=3,minor=1); producer top-1 select; opt-in via n_candidates param |
| ConductorResult with critic_findings | ✅ | tests/unit/test_conductor.py | Findings visible in summary() |
| Audio Loop (Conductor) | ✅ | tests/unit/conductor/test_audio_feedback.py (10 tests) | ConductorConfig with enable_audio_loop (opt-in, default OFF); AudioThresholds (LUFS target/tolerance, masking_risk_max); 3 adaptation types (dynamics_adjust, register_adjust, eq_adjust); max 2 audio iterations; requires SoundFont; v3.0 Wave 2.3 complete |

## CLI

| Feature | Status | Tests | Notes |
|---|---|---|---|
| yao compose | ✅ | — | Single-pass generation |
| yao conduct | ✅ | tests/unit/test_conductor.py | NL description or spec path |
| yao render | ✅ | — | MIDI → WAV |
| yao validate | ✅ | — | Spec validation and summary |
| yao evaluate | ✅ | — | Re-evaluate latest iteration |
| yao diff | ✅ | — | Compare two seeds |
| yao explain | ✅ | — | Provenance query |
| yao new-project | ✅ | — | Project skeleton |
| yao regenerate-section | ✅ | — | Section regeneration |
| yao preview | ✅ | tests/unit/cli/test_preview.py | In-memory generation + FluidSynth synthesis + sounddevice playback; no file output |
| yao watch | ✅ | tests/unit/cli/test_watch.py | File-watch via watchdog + auto-regenerate + auto-play; 500ms debounce |
| yao rate | ✅ | tests/unit/cli/test_rate.py (2 tests) | Interactive 5-dimension rating (memorability/emotional_fit/technical_quality/genre_fitness/overall) + free text; saves JSON; v3.0 Wave 3.5 |
| yao reflect ingest | ✅ | tests/unit/cli/test_rate.py (2 tests) | Aggregates rating files into UserStyleProfile; computes preferred_range/confidence per dimension; v3.0 Wave 3.5 |

## Skills / Knowledge

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Genre Skills (22) | ✅ | tests/unit/skills/ (26 tests), tests/integration/test_skill_grounding.py (6 tests) | 22 genres loaded by SkillRegistry; integrated into HarmonyPlanner (chord palette), SpecCompiler (instruments/keys/tempo), genre_fitness critique (tempo range, avoided instruments); Skill edit → output change verified; v3.0 Wave 2.1 complete |
| voice-leading theory Skill | 🟢 | — | .claude/skills/theory/voice-leading.md |
| piano instrument Skill | 🟢 | — | .claude/skills/instruments/piano.md |
| tension-resolution psychology Skill | 🟢 | — | .claude/skills/psychology/tension-resolution.md |

## Subagents / Commands

| Feature | Status | Tests | Notes |
|---|---|---|---|
| 7 Subagent definitions (.md) | ✅ | — | .claude/agents/ (composer, critic, harmony-theorist, mix-engineer, orchestrator, producer, rhythm-architect) |
| 7 Subagent Python implementations | ✅ | tests/unit/subagents/ (34 tests) | All 7 roles registered; Composer generates non-empty MotifPlan (Markov bigram + intent) with >= 3 placements per motif; PhrasePlan covers all sections; v3.0 Wave 1.1 complete |
| 7 slash commands | ✅ | — | .claude/commands/ (compose, critique, sketch, regenerate-section, explain, render, arrange) |

## Tests / QA

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Unit tests | ✅ | tests/unit/ (70+ files) | ~1000+ tests |
| Integration tests | ✅ | tests/integration/ (3 files) | ~15 tests |
| Scenario tests | ✅ | tests/scenarios/ (2 files) | ~16 tests (trajectory compliance) |
| Music constraint tests | ✅ | tests/music_constraints/ | 7 parameterized tests |
| Golden MIDI tests | ✅ | tests/golden/ | 6 baselines (3 specs x 2 realizers); comparison.py; regenerate_goldens.py |
| Architecture lint | ✅ | — | tools/architecture_lint.py; `make arch-lint` |
| Feature status check | ✅ | — | tools/feature_status_check.py; `make feature-status` |
| Document sync check | ✅ | tests/unit/test_sync_docs.py | tools/sync_docs.py; `make sync-docs`; FEATURE_STATUS ↔ CLAUDE.md Tier checklist; in all-checks pipeline |
| Subjective quality tests | ✅ | tests/subjective/test_listening_panel.py | Rating JSON schema; overall ≥ 6.0 threshold; `make test-subjective`; `pytest.mark.subjective` for CI skip |

## Infrastructure

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Pre-commit hooks | ✅ | — | trailing-whitespace, ruff, ruff-format, mypy, arch-lint |
| CI (GitHub Actions) | ✅ | — | lint + type + arch-lint + tests + golden |
| Provenance logging | ✅ | — | Append-only, queryable, JSON persistence |
| Constants (38 instruments, 14 scales, 14 chords) | ✅ | — | src/yao/constants/ |

## Not Yet Implemented

| Feature | Status | Notes |
|---|---|---|
| Drum pattern generator | ✅ | ★1 complete; 8 genre patterns, swing, ghost notes, trajectory density |
| Counter-melody generator | ✅ | ★2 complete; consonance + contrary motion + parallel avoidance |
| Trajectory multi-dim coupling | ✅ | ★3 complete; both generators respond via GenerationParams |
| yao preview / yao watch | ✅ | ★6 complete |
| 7 additional genre Skills | ✅ | ★7 complete |
| Audio Perception Stage 1 | ✅ | PerceptualReport (frozen); LUFS (pyloudnorm.Meter), spectral (centroid/rolloff/flatness), onset density, tempo stability, 7-band energy, masking risk; section boundaries support |
| Use-Case Targeted Evaluators | ✅ | tests/unit/perception/test_use_case_evaluator.py (22 tests) | 7 use cases (YouTube BGM, Game BGM, Advertisement, Study Focus, Meditation, Workout, Cinematic); all scores [0,1]; per-use-case scoring keys documented |
| Arrangement Engine MVP | ✅ | tests/unit/arrange/ (20 tests) | SourcePlanExtractor (MIDI→MusicalPlan, confidence scores); StyleVectorOps (transfer + PreservationContract); DiffWriter (markdown); 4 critique rules; ArrangementSpec with rights_status |
| Production Manifest + Mix Chain | ✅ | ProductionManifest schema (per-track EQ/comp/reverb/gain/pan + master LUFS/limiter); MixChainProcessor; pedalboard-based EQ/Compressor/Reverb/Limiter; pyloudnorm LUFS normalization; true-peak -1.0 dBFS cap |
| Microtonal scale support | ✅ | tests/unit/ir/test_tuning.py, tests/unit/constants/test_scales.py (27 tests) | ScaleDefinition (cents-based); Tuning class; 17 scales (9 EDO + 3 raga + 2 maqam + 2 gamelan + 1 JI); cultural_context required for non-Western; microtonal theory Skill |
| Extended Time Signatures | ✅ | tests/unit/schema/test_time_signature.py, tests/unit/ir/test_timing_extended.py (32 tests) | TimeSignatureSpec with beat_groupings; compound auto-detection (6/8, 9/8, 12/8); PolymeterTrack with sync_at; parse/is_compound/beat_grouping/beats_to_bars utilities; backward compatible |
| Neural generator bridge (Stable Audio) | ✅ | tests/unit/generators/neural/test_stable_audio_bridge.py (8 tests) | StableAudioTextureGenerator; 5 provenance fields (model_version/prompt/seed/hash/rights); graceful ImportError → NeuralBackendUnavailableError; optional dep `pip install yao[neural]` |
| Project Runtime | ✅ | tests/unit/runtime/test_project_runtime.py (7 tests) | Context manager; undo/redo (max 50); generation cache (spec_hash+seed+strategy); lockfile |
| DAW project writer (Reaper RPP) | ✅ | tests/unit/render/test_reaper_writer.py (3 tests) | ScoreIR → .rpp text; per-instrument tracks; MIDI stem references |
| DAW MCP integration | 🟡 | tests/unit/render/test_daw_mcp.py (4 tests) | limitation: stub implementation, always returns disconnected/False/None; interface defined but no real MCP connection; Wave 3+ target |
| Strudel emitter | ✅ | tests/unit/render/test_strudel_emitter.py (4 tests) | ScoreIR → Strudel live-coding notation (.js); browser-side instant audition |
| Reflection Layer (Style Profile) | ✅ | tests/unit/reflect/test_style_profile.py (5 tests), tests/unit/cli/test_rate.py (4 tests) | `yao rate` interactive CLI for 5-dimension rating; `yao reflect ingest` aggregates ratings into UserStyleProfile; preferences stored as (range, confidence, source_count); v3.0 Wave 3.5 complete |
| Critique rules (19 total) | ✅ | tests/unit/verify/test_critique_rules.py | 15 original + 4 new (memorability: MotifAbsence, HookWeakness; genre_fitness: TempoOutOfRange, InstrumentMismatch) |
| Property-based tests | ✅ | tests/properties/test_genre_invariants.py | Key/range/section/provenance invariants across 4 strategies × 5 seeds |
| Live improvisation mode | ✅ | tests/unit/improvise/ (21 tests) | RealtimeImprovisationEngine (50ms latency budget); ContextBuffer ring buffer (key/chord/tempo estimation); 4 roles (Bassist/Drummer/Accompanist/MelodyFollower); SessionLog; optional dep `pip install yao[live]` |
| Annotation UI | ✅ | tests/unit/annotate/ (12 tests) | FastAPI local server; Annotation + AnnotationFile Pydantic models; browser UI with audio player + time-range tagging; explicit save only; optional dep `pip install yao[annotate]` |
| Backend-Agnostic Agent Protocol | 🟡 | tests/unit/agents/ (29 tests) | limitation: ClaudeCodeBackend (is_stub=True) still falls back to PythonOnly; AnthropicAPIBackend is real (is_stub=False, requires ANTHROPIC_API_KEY, tool_use structured output, provenance with backend/model/prompt_hash/token_usage); Protocol and PythonOnlyBackend work; ClaudeCode is Wave 3+ target |
