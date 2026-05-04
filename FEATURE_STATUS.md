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
| Spec Composability (v3) | ✅ | tests/unit/schema/test_composition_v3.py (16 tests) | extends/overrides support; deep merge; fragment loading from specs/fragments/; circular detection; v2.0 PR 2.3 |
| Natural language → spec (`yao conduct`) | 🟢 | tests/unit/test_conductor.py | English keyword dict; explicit key regex ("in D minor"); no Japanese |
| trajectory.yaml multi-dim coupling | ✅ | tests/scenarios/test_trajectory_compliance.py | All 5 dims defined; GenerationParams derived per bar; both generators respond to tension (velocity+leaps), density (rhythm), register_height (octave) |
| constraints with scoping | ✅ | tests/unit/test_constraints.py | must / must_not / prefer / avoid with global, section, instrument, bars scopes |
| intent.md | ✅ | tests/unit/schema/test_intent.py | IntentSpec parsed; mood divergence checked by ListeningSimulator; IntentDivergenceDetector critique rule fires on plan/output mismatch |
| references.yaml | ✅ | tests/unit/perception/test_reference_matcher.py, test_style_vector.py | PrimaryReference + NegativeReference with rights_status validation; ALLOWED_FEATURES/FORBIDDEN_FEATURES allowlist/blocklist; StyleVector (6 abstract features, no melody/chords); ReferenceMatcher with sha256 cache; defense-in-depth at schema + runtime |
| negative-space.yaml | 🟡 | — | Schema exists; reflection mechanism incomplete |
| production.yaml | ✅ | tests/unit/render/test_mix_chain.py | ProductionSpec + ProductionManifest schemas; render/mix_chain.py MVP (RMS loudness, reverb, stereo width); mix/mix_chain.py full chain (per-track EQ/comp/reverb/gain/pan, master LUFS) |

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
| ScoreIR (Note, Part, Section) | ✅ | tests/unit/test_ir.py | Frozen dataclasses; Note has optional v2.0 fields: articulation, tuning_offset_cents, microtiming_offset_ms |
| Motif IR | ✅ | tests/unit/test_motif.py | Motif, invert, retrograde, transpose |
| Harmony IR | ✅ | tests/unit/test_harmony.py | diatonic_quality, chord functions |
| Voicing IR | ✅ | tests/unit/test_voicing.py | Voice-crossing detection |
| Timing IR | ✅ | tests/unit/test_ir.py | bars_to_beats, beats_to_bars |
| Notation IR | ✅ | tests/unit/test_ir.py | note_name_to_midi, midi_to_note_name |
| Trajectory IR (5-dim) | ✅ | tests/unit/test_trajectory_ir.py | MultiDimensionalTrajectory with TrajectoryCurve; bezier/stepped/linear |
| DrumPattern IR | ✅ | tests/unit/ir/test_drum.py | DrumHit, DrumPattern, KitPiece, GM_DRUM_MAP; 15 kit pieces mapped |
| TensionArc IR (Layer 3.5) | ✅ | tests/unit/ir/test_tension_arc.py | TensionArc, ArcLocation, ArcRelease, TensionPattern (5 patterns); 2–8 bar span; embedded in HarmonyPlan; round-trip serialization; Phase γ.1 |
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
| Evaluator (11 metrics, 3 dims) | ✅ | tests/unit/test_evaluator.py, tests/unit/test_evaluator_dynamic_weights.py (8 tests) | MetricGoal-based; structure / melody / harmony; genre-driven dynamic weights via UnifiedGenreProfile; percussion_centric mode; includes motif_recall_strength (TARGET_BAND 0.4-0.7) |
| MetricGoal type system | ✅ | tests/unit/verify/test_metric_goal.py | 7 goal types (AT_LEAST, BETWEEN, etc.) |
| Score diff | ✅ | tests/unit/test_diff.py | Modified notes tracking |
| Constraint checker | ✅ | tests/unit/test_constraints.py | Range / voice constraints |
| Critique rules (structured) | ✅ | tests/unit/verify/test_critique_rules.py | 19 rules across 6 roles (structural 3, harmonic 3, melodic 3, rhythmic 2, arrangement 2, emotional 2, memorability 2, genre_fitness 2) |
| Critique registry + Finding types | ✅ | tests/unit/verify/test_critique.py | CritiqueRule base, Finding dataclass, CritiqueRegistry |
| Surprise critique rules (3) | ✅ | tests/unit/verify/test_surprise_rules.py | surprise_deficit, surprise_overload (structural); tension_arc_unresolved (harmonic); brings total to 22 rules across 7+ categories |
| Hook critique rules (3) | ✅ | tests/unit/verify/test_hook_rules.py (8 tests) | hook_overuse, hook_underuse, hook_misplacement; withhold_then_release in intro detected; total critique rules now 26 |
| Dynamics critique rules (1) | ✅ | (integrated in test_hook_rules.py) | flat_phrase_dynamics; fires on sections ≥3 bars without dynamics_shape or accents |
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
| Unified GenreProfile Schema | ✅ | tests/unit/schema/test_unified_genre_profile.py (16 tests) | Pydantic model with 14 nested sections (identity/tempo/meter/tuning/groove/harmony/melody/drums/instrumentation/articulation/production/evaluation/generator_assignments/aesthetic_critique); parent inheritance; IncompleteGenreProfileError; adapters for both System 1 and System 2; v2.0 PR 1.1 |
| voice-leading theory Skill | 🟢 | — | .claude/skills/theory/voice-leading.md |
| piano instrument Skill | 🟢 | — | .claude/skills/instruments/piano.md |
| tension-resolution psychology Skill | 🟢 | — | .claude/skills/psychology/tension-resolution.md |

## Subagents / Commands

| Feature | Status | Tests | Notes |
|---|---|---|---|
| 7 Subagent definitions (.md) | ✅ | — | .claude/agents/ (composer, critic, harmony-theorist, mix-engineer, orchestrator, producer, rhythm-architect) |
| 7 Subagent Python implementations | ✅ | tests/unit/subagents/ (34 tests) | All 7 roles registered; Composer generates non-empty MotifPlan (Markov bigram + intent) with >= 3 placements per motif; PhrasePlan covers all sections; v3.0 Wave 1.1 complete |
| 10 slash commands | ✅ | — | .claude/commands/ (compose, conduct, critique, sketch, regenerate-section, explain, render, arrange, pin, feedback) |

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
| Genre calibration tool | ✅ | tests/tools/test_calibrate_genres.py (3 tests) | tools/calibrate_genres.py; `make calibrate-genres`; validates all 22 genres; v2.0 PR 5.2 |
| Document sync check | ✅ | tests/unit/test_sync_docs.py | tools/sync_docs.py; `make sync-docs`; FEATURE_STATUS ↔ CLAUDE.md Tier checklist; in all-checks pipeline |
| Subjective quality tests | ✅ | tests/subjective/test_listening_panel.py | Rating JSON schema; overall ≥ 6.0 threshold; `make test-subjective`; `pytest.mark.subjective` for CI skip |

## Infrastructure

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Pre-commit hooks | ✅ | — | trailing-whitespace, ruff, ruff-format, mypy, arch-lint |
| CI (GitHub Actions) | ✅ | — | lint + type + arch-lint + tests + golden |
| Provenance logging | ✅ | tests/unit/reflect/test_causal_provenance.py (15 tests) | Append-only with causal graph: record_id + caused_by edges; get_causes/get_effects/trace_ancestry; backward-compatible; v2.0 PR 4.5 |
| Constants (46 instruments, 28 scales, 14 chords) | ✅ | — | src/yao/constants/ |

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
| Microtonal scale support | ✅ | tests/unit/ir/test_tuning.py, tests/unit/constants/test_scales.py (27 tests), tests/unit/constants/test_extended_scales.py (19 tests) | ScaleDefinition (cents-based); Tuning class; 28 scales (9 EDO + 6 Japanese + 5 maqam + 5 raga + 2 gamelan + 1 JI); cultural_context required for non-Western; Phase γ.7 extended |
| Custom instrument profiles (8) | ✅ | tests/unit/constants/test_custom_instruments.py (11 tests) | shakuhachi, koto, shamisen, taiko, sitar, tabla, oud, ney; CustomInstrument frozen dataclass; inline data (no external YAML); also registered in INSTRUMENT_RANGES (46 total); GM approx + custom_sf2_path; cultural_origin + idiomatic_techniques; Phase γ.7 |
| Culture Skills (3) | ✅ | — | .claude/skills/cultures/japanese.md, middle_eastern.md, indian_classical.md; academic source citations; jo-ha-kyū, maqam system, raga system documented; Phase γ.7 |
| Multilingual SpecCompiler (ja) | ✅ | tests/unit/sketch/test_multilingual.py (17 tests) | Japanese emotion vocabulary (50+ words); instrument/tempo/duration/genre keywords; language auto-detection; English backward compatible; provenance recorded; Phase γ.7 |
| Extended Time Signatures | ✅ | tests/unit/schema/test_time_signature.py, tests/unit/ir/test_timing_extended.py (32 tests) | TimeSignatureSpec with beat_groupings; compound auto-detection (6/8, 9/8, 12/8); PolymeterTrack with sync_at; parse/is_compound/beat_grouping/beats_to_bars utilities; backward compatible |
| MeterSpec IR (Layer 1) | ✅ | tests/unit/ir/test_meter.py (23 tests) | MeterSpec frozen dataclass; parse_meter_string(); grouping disambiguation (7/8 (3,2,2) != (2,2,3)); metric_accents; group_durations_beats(); meter_assumption_lint tool |
| Neural generator bridge (Stable Audio) | ✅ | tests/unit/generators/neural/test_stable_audio_bridge.py (8 tests) | StableAudioTextureGenerator; 5 provenance fields (model_version/prompt/seed/hash/rights); graceful ImportError → NeuralBackendUnavailableError; optional dep `pip install yao[neural]` |
| Project Runtime | ✅ | tests/unit/runtime/test_project_runtime.py (7 tests) | Context manager; undo/redo (max 50); generation cache (spec_hash+seed+strategy); lockfile |
| DAW project writer (Reaper RPP) | ✅ | tests/unit/render/test_reaper_writer.py (3 tests) | ScoreIR → .rpp text; per-instrument tracks; MIDI stem references |
| DAW MCP integration | 🟡 | tests/unit/render/test_daw_mcp.py (4 tests) | limitation: stub implementation, always returns disconnected/False/None; interface defined but no real MCP connection; Wave 3+ target |
| Strudel emitter | ✅ | tests/unit/render/test_strudel_emitter.py (4 tests) | ScoreIR → Strudel live-coding notation (.js); browser-side instant audition |
| Reflection Layer (Style Profile) | ✅ | tests/unit/reflect/test_style_profile.py (11 tests), tests/unit/cli/test_rate.py (4 tests) | `yao rate` interactive CLI; `yao reflect ingest` aggregates ratings; UserStyleProfile with update_from(feedback, score), bias(spec), save/load; preferences for density/dynamics/overall |
| Critique rules (26 total) | ✅ | tests/unit/verify/test_critique_rules.py, tests/unit/verify/test_surprise_rules.py, tests/unit/verify/test_groove_rules.py, tests/unit/verify/test_metric_drift.py | 22 prior + 3 groove + 1 metric_drift (v2.0); Phase γ.4 + v2.0 |
| Non-4/4 Drum Patterns (5) | ✅ | tests/unit/generators/test_drum_patterns_non44.py (34 tests) | waltz_3_4, compound_6_8, take_five_5_4, bulgarian_7_8, bartok_7_8; total 15 drum patterns |
| GrooveProfile IR (Layer 3.5) | ✅ | tests/unit/ir/test_groove.py (22 tests) | Frozen dataclass; 16th-position microtiming + velocity pattern; [-50,50]ms bounds; ghost_probability, swing_ratio, jitter_sigma; apply_to_all_instruments; Phase γ.4 |
| Groove Library (20 profiles) | ✅ | tests/unit/ir/test_groove.py (8 tests), tests/unit/ir/test_groove_expansion.py (49 tests) | 20 grooves: 12 original + waltz_viennese, shuffle_blues, samba, afrobeat, new_orleans_second_line, drum_n_bass, flamenco_bulerias, bollywood_filmi; grooves/*.yaml; Phase γ.4 + v2.0 |
| GrooveApplicator | ✅ | tests/unit/generators/test_groove_applicator.py (13 tests), tests/scenarios/test_groove_changes_feel.py (4 tests) | apply_groove(score_ir, groove) → (ScoreIR, ProvenanceLog); per-note 16th subdivision → offset+velocity; drums-only mode; seeded jitter; Phase γ.4 |
| GrooveSpec schema | ✅ | tests/unit/schema/test_groove.py (6 tests) | Pydantic model; base + overrides pattern; groove.yaml loading; Phase γ.4 |
| Surprise Score (Layer 4) | ✅ | tests/unit/perception/test_surprise.py (20 tests), tests/scenarios/test_surprise_distribution.py (3 tests) | SurpriseScorer (bigram n-gram + Krumhansl tonal hierarchy); SurpriseAnalysis with per-note scores, moving average, peaks, variance; no ML deps; Phase γ.1 |
| TensionArcs schema | ✅ | tests/unit/schema/test_tension_arcs.py (13 tests), tests/scenarios/test_tension_arc_realization.py (4 tests) | TensionArcsSpec Pydantic model; cross-spec validation against section names; 5 patterns (linear_rise, dip, plateau, spike, deceptive); Phase γ.1 |
| Genre Coverage Tests | ✅ | tests/genre_coverage/ (111 tests) | Per-genre schema validation, unified profile loading, tempo range, instruments, identity; all 22 genres covered; v2.0 PR 2.8 |
| Property-based tests | ✅ | tests/properties/test_genre_invariants.py | Key/range/section/provenance invariants across 4 strategies × 5 seeds |
| Curriculum Learning | ✅ | tests/unit/conductor/test_curriculum.py (11 tests) | CurriculumDictionary with FailurePattern tracking; record/lookup/save/load; genre-agnostic fallback; best-adaptation ranking; v2.0 PR 5.3 |
| Live improvisation mode | ✅ | tests/unit/improvise/ (21 tests) | RealtimeImprovisationEngine (50ms latency budget); ContextBuffer ring buffer (key/chord/tempo estimation); 4 roles (Bassist/Drummer/Accompanist/MelodyFollower); SessionLog; optional dep `pip install yao[live]` |
| A/B Audition UI | ✅ | tests/unit/audition/test_audition.py (11 tests) | AuditionResult + SectionPreference; FastAPI browser UI; side-by-side comparison; preference recording; save/load JSON; winner determination; optional dep `pip install yao[annotate]`; v2.0 PR 4.4 |
| Annotation UI | ✅ | tests/unit/annotate/ (12 tests) | FastAPI local server; Annotation + AnnotationFile Pydantic models; browser UI with audio player + time-range tagging; explicit save only; optional dep `pip install yao[annotate]` |
| Backend-Agnostic Agent Protocol | 🟡 | tests/unit/agents/ (29 tests) | limitation: ClaudeCodeBackend (is_stub=True) still falls back to PythonOnly; AnthropicAPIBackend is real (is_stub=False, requires ANTHROPIC_API_KEY, tool_use structured output, provenance with backend/model/prompt_hash/token_usage); Protocol and PythonOnlyBackend work; ClaudeCode is Wave 3+ target |
| Listening Simulator (Step 7.5) | ✅ | tests/unit/perception/test_listening_simulator.py (10 tests) | ListeningSimulator orchestrates post-render perception; persists perceptual.json; mood divergence detection via intent keywords; section boundary support |
| Acoustic Divergence Rules | ✅ | tests/unit/verify/test_acoustic_divergence.py (27 tests) | 5 rules: symbolic_acoustic_divergence, lufs_target_violation, spectral_imbalance, brightness_intent_mismatch (mood↔centroid), energy_trajectory_violation (tension↔LUFS correlation); Role.ACOUSTIC (7 roles total) |
| Audio Regression Tests | ✅ | tests/audio_regression/test_baseline.py (8 tests) | Synthetic baselines (sine, noise, two-section); deterministic extraction verification; `make test-acoustic` target; `audio_regression` pytest marker for weekly CI |
| Hook IR | ✅ | tests/unit/ir/test_hook.py (14 tests) | Hook frozen dataclass with DeploymentStrategy (rare/frequent/withhold_then_release/ascending_repetition); HookPlan; BarPosition; references MotifSeed by id; serialization round-trip |
| Phrase-Level Dynamics (DynamicsShape) | ✅ | tests/unit/ir/test_dynamics_shape.py (13 tests) | DynamicsShapeType (crescendo/decrescendo/arch/hairpin/steady); velocity_multiplier(position) curve; BarAccent; arch peak at specified position verified; intensity=0 means flat |
| HooksSpec schema | ✅ | tests/unit/schema/test_hooks.py (8 tests) | HooksSpec Pydantic model; YAML loading; unique ID validation; deployment strategy enum; distinctive_strength [0,1] validation |
| ConversationPlan IR | ✅ | tests/unit/ir/test_conversation.py (13 tests) | ConversationEvent (call_response/fill_in_response/tutti/solo_break/trade); BarRange; primary_voice_per_section; accompaniment mapping; serialization round-trip; Phase γ.5 |
| ConversationSpec schema | ✅ | tests/unit/schema/test_conversation.py (11 tests) | VoiceFocusSpec + ConversationEventSpec; YAML loading; unique section validation; fill_capable instruments; Phase γ.5 |
| Conversation Director (Step 5.5) | ✅ | tests/unit/generators/test_conversation_director.py (6 tests) | generate_conversation_plan from spec or inferred from ArrangementPlan; does NOT modify notes; produces ConversationPlan only; provenance recorded; Phase γ.5 |
| Reactive Fills | ✅ | tests/unit/generators/test_reactive_fills.py (9 tests) | detect_fill_opportunities (gap ≥ 1.0 beat); generate_reactive_fills (2-4 note fills, ≤ 1 bar, within range); ≥60% fill rate; provenance; Phase γ.5 |
| Frequency Clearance | ✅ | tests/unit/generators/test_frequency_clearance.py (10 tests) | Symbolic collision detection (±3 semitones + time overlap); octave displacement; never silences; primary voice unchanged; Phase γ.5 |
| Conversation Critique Rules (4) | ✅ | tests/unit/verify/test_conversation_rules.py (10 tests) | conversation_silence, primary_voice_ambiguity, fill_absence_at_phrase_ends, frequency_collision_unresolved; total critique rules now 34; Phase γ.5 |
| Form Library (20 forms) | ✅ | tests/unit/constants/test_forms.py (13 tests), tests/scenarios/test_diversity_sources.py (8 tests) | SongForm + FormSection frozen dataclasses; 20 forms (aaba_32bar, verse_chorus_bridge, rondo, through_composed, blues_12bar, j_pop, game_bgm, ambient, etc.); varying lengths (12-68 bars); 8+ genres covered; serialization round-trip; Phase γ.6 |
| Melodic Generation Strategies (8) | ✅ | tests/unit/generators/test_melodic_strategies.py (38 tests) | MelodicGenerationStrategy enum (contour_based/motif_development/linear_voice/arpeggiated/scalar_runs/call_response/pedal_tone/hocketing); generate_melody_pitches(); deterministic with seed; each strategy produces distinct character (verified); Phase γ.6 |
| Pin IR + PinsSpec | ✅ | tests/unit/feedback/test_pin.py (18 tests), tests/unit/feedback/test_pins_spec.py (7 tests) | Pin frozen dataclass; PinLocation (section/bar/beat/instrument); CLI string parsing; PinsSpec Pydantic model; YAML round-trip; immutable; Phase δ.2 |
| Pin-Aware Regenerator | ✅ | tests/unit/feedback/test_pin_aware_regenerator.py (9 tests), tests/scenarios/test_pin_localization.py (5 tests) | regenerate_with_pins(); affected region = pin bar ± 1 padding; unaffected notes bit-identical; provenance records pin_id; intent-based adjustment; Phase δ.2 |
| NL Feedback Translator | 🟢 | tests/unit/feedback/test_nl_translator.py (24 tests), tests/scenarios/test_nl_feedback_translation.py (5 tests) | 30 phrase→intent mappings; section/instrument detection; ambiguous input flagged; StructuredFeedback output; maintainable data table; Phase δ.2 |
