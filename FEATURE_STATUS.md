# YaO Feature Status

> Last verified: 2026-05-05 by full codebase audit (208 source files, 213 test files, 2285 test functions)
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
| YAML spec parsing (Pydantic v1) | ✅ | tests/unit/test_schema.py (18 tests) | CompositionSpec, SectionSpec, InstrumentSpec; all 4 templates load |
| YAML spec parsing (Pydantic v2) | ✅ | tests/unit/schema/test_composition_v2.py (74 tests) | 22 Pydantic models, 11 sections, CadenceMap |
| Spec Composability (v3) | ✅ | tests/unit/schema/test_composition_v3.py (16 tests) | extends/overrides support; deep merge; fragment loading from specs/fragments/; circular detection |
| Natural language → spec (`yao conduct`) | 🟢 | tests/unit/test_conductor.py | English keyword dict; explicit key regex ("in D minor"); no Japanese (see SpecCompiler for Japanese) |
| trajectory.yaml multi-dim coupling | ✅ | tests/scenarios/test_trajectory_compliance.py (11 tests) | All 5 dims defined; GenerationParams derived per bar; both generators respond to tension (velocity+leaps), density (rhythm), register_height (octave) |
| constraints with scoping | ✅ | tests/unit/test_constraints.py (8 tests) | must / must_not / prefer / avoid with global, section, instrument, bars scopes |
| intent.md | ✅ | tests/unit/schema/test_intent.py (14 tests) | IntentSpec parsed; mood divergence checked by ListeningSimulator; IntentDivergenceDetector critique rule fires on plan/output mismatch |
| references.yaml | ✅ | tests/unit/perception/test_reference_matcher.py (29 tests), test_style_vector.py (24 tests) | PrimaryReference + NegativeReference with rights_status validation; ALLOWED_FEATURES/FORBIDDEN_FEATURES allowlist/blocklist; StyleVector (6 abstract features, no melody/chords); ReferenceMatcher with sha256 cache; defense-in-depth at schema + runtime |
| negative-space.yaml | 🟡 | — | Schema exists (NegativeSpaceSpec, SilenceRegion, FrequencyGap); reflection mechanism incomplete |
| production.yaml | ✅ | tests/unit/render/test_mix_chain.py (10 tests), tests/unit/mix/ (19 tests) | ProductionSpec + ProductionManifest schemas; render/mix_chain.py MVP (RMS loudness, reverb, stereo width); mix/mix_chain.py full chain (per-track EQ/comp/reverb/gain/pan, master LUFS) |
| TonalSystem schema | ✅ | tests/tonal_systems/test_tonal_system.py (15 tests), tests/unit/ir/test_tonal_system.py (23 tests) | 10 tonal system kinds (tonal_major_minor, modal, pentatonic, blues, microtonal, atonal, drone, raga, maqam, custom); backward-compatible key promotion |
| SoundDesignSpec | ✅ | tests/unit/test_sound_design.py (26 tests), tests/integration/test_d11_sound_design.py (4 tests) | 5 synthesis kinds (sample_based, subtractive, fm, wavetable, physical); 11 effect types; lazy pedalboard import |
| Field Applicability | ✅ | tests/unit/schema/test_applicability.py (13 tests) | FieldApplicability, FieldStatus; genre-conditional schema validation |
| Project schema | ✅ | tests/unit/schema/test_project.py (6 tests) | CompositionProject Pydantic model |
| Feedback schema | ✅ | tests/unit/schema/test_feedback.py (7 tests) | FeedbackSpec, FeedbackTag, FeedbackSeverity |

## Generation

| Feature | Status | Tests | Notes |
|---|---|---|---|
| rule_based generator | ✅ | tests/unit/test_generator.py (9 tests) | Deterministic; trajectory: tension → velocity only |
| stochastic generator | ✅ | tests/unit/test_stochastic.py (28 tests) | seed / temperature / contour; trajectory: tension → pitch+leaps, density → rhythm, register_height → octave |
| Generator registry | ✅ | tests/unit/test_generator.py | @register_generator decorator |
| drum_patterner | ✅ | tests/unit/generators/test_drum_patterner.py (10 tests) | 15 genre patterns in drum_patterns/ (8 base + 5 non-4/4 + chiptune + game_drive); swing, ghost notes, trajectory density |
| counter_melody | ✅ | tests/unit/generators/test_counter_melody.py (8 tests) | Species counterpoint; contrary motion preferred; density_factor control |
| markov generator | ✅ | tests/unit/test_markov.py (24 tests) | n-gram bigram transitions on scale degrees; diatonic + pentatonic models; temperature scaling; trajectory coupling (tension/density/register_height); lazy-loaded YAML models |
| twelve_tone generator | ✅ | tests/unit/generators/test_twelve_tone.py (10 tests) | 12-tone serial: P/I/R/RI row transformations; auto-generated or specified row; per-section transform cycling |
| process_music generator | ✅ | tests/unit/generators/test_process_music.py (9 tests) | Process music: phasing/additive/subtractive; cell auto-generation from key; temperature controls process type |
| constraint solver generator | ✅ | tests/unit/generators/test_constraint_solver.py (6 tests) | Backtracking CSP; key+range+stepwise constraints; 5s timeout; GenerationTimeoutError |
| loop_evolution generator | ✅ | tests/unit/test_loop_evolution.py (20 tests) | Loop-first iterative design; core loop bars config; layer evolution across sections; arrangement string parsing ("A B C drop A B C"); @register_generator("loop_evolution") |
| ai_seed generator | ✅ | tests/unit/generators/test_ai_seed.py (22 tests) | AISeedGenerator with AnthropicMotifClient + DeterministicMotifClient; motif generation from intent; optional Anthropic API |
| Melodic Generation Strategies (8) | ✅ | tests/unit/generators/test_melodic_strategies.py (12 tests) | MelodicGenerationStrategy enum (contour_based/motif_development/linear_voice/arpeggiated/scalar_runs/call_response/pedal_tone/hocketing); generate_melody_pitches(); deterministic with seed; each strategy produces distinct character |
| Non-4/4 Drum Patterns (5) | ✅ | tests/unit/generators/test_drum_patterns_non44.py (11 tests) | waltz_3_4, compound_6_8, take_five_5_4, bulgarian_7_8, bartok_7_8; total 15 drum patterns |
| Reactive Fills | ✅ | tests/unit/generators/test_reactive_fills.py (9 tests) | detect_fill_opportunities (gap ≥ 1.0 beat); generate_reactive_fills (2-4 note fills, ≤ 1 bar, within range); ≥60% fill rate; provenance |
| Frequency Clearance | ✅ | tests/unit/generators/test_frequency_clearance.py (14 tests) | Symbolic collision detection (±3 semitones + time overlap); octave displacement; never silences; primary voice unchanged |
| Conversation Director | ✅ | tests/unit/generators/test_conversation_director.py (6 tests) | generate_conversation_plan from spec or inferred from ArrangementPlan; does NOT modify notes; produces ConversationPlan only; provenance recorded |
| GrooveApplicator | ✅ | tests/unit/generators/test_groove_applicator.py (12 tests), tests/scenarios/test_groove_changes_feel.py (4 tests) | apply_groove(score_ir, groove) → (ScoreIR, ProvenanceLog); per-note 16th subdivision → offset+velocity; drums-only mode; seeded jitter |

## Planning

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Form Planner | ✅ | tests/unit/generators/plan/test_form_planner.py (6 tests) | Song form selection from 20 forms; section planning with bar lengths |
| Harmony Planner | ✅ | tests/unit/generators/plan/test_harmony_planner.py (10 tests) | Chord progression generation; genre-aware chord palette; tension arc integration |
| Motivic Planner | ✅ | tests/unit/generators/plan/test_motivic_planner.py (9 tests) | Motif extraction and placement; MotifPlan with ≥3 placements per motif |
| Note Realizers (v2) | ✅ | tests/unit/generators/note/ (36 tests) | Rule-based v2 (11 tests), Stochastic v2 (8 tests), original realizers preserved |

## IR (Intermediate Representation)

| Feature | Status | Tests | Notes |
|---|---|---|---|
| ScoreIR (Note, Part, Section) | ✅ | tests/unit/test_ir.py (39 tests) | Frozen dataclasses; Note has optional v2.0 fields: articulation, tuning_offset_cents, microtiming_offset_ms |
| Motif IR | ✅ | tests/unit/test_motif.py (27 tests) | Motif, MotifNetwork, MotifNode; invert, retrograde, transpose |
| Harmony IR | ✅ | tests/unit/test_harmony.py (15 tests) | diatonic_quality, chord functions, ChordProgression |
| Voicing IR | ✅ | tests/unit/test_voicing.py (11 tests) | Voice-crossing detection |
| Timing IR | ✅ | tests/unit/test_ir.py | bars_to_beats, beats_to_bars |
| Notation IR | ✅ | tests/unit/test_ir.py | note_name_to_midi, midi_to_note_name |
| Trajectory IR (5-dim) | ✅ | tests/unit/test_trajectory_ir.py (17 tests) | MultiDimensionalTrajectory with TrajectoryCurve; bezier/stepped/linear; 5 dims: tension, density, register_height, variation, instrumentation |
| DrumPattern IR | ✅ | tests/unit/ir/test_drum.py (8 tests) | DrumHit, DrumPattern, FillLocation, KitPiece, GM_DRUM_MAP; 15 kit pieces mapped |
| TensionArc IR (Layer 3.5) | ✅ | tests/unit/ir/test_tension_arc.py (17 tests) | TensionArc, ArcLocation, ArcRelease, TensionPattern (5 patterns); 2–8 bar span; embedded in HarmonyPlan; round-trip serialization |
| Performance Expression IR (Layer 4.5) | ✅ | tests/unit/ir/test_expression.py (47 tests) | NoteExpression, PerformanceLayer, RubatoCurve, BreathMark, PedalCurve; integrated into Conductor pipeline and MIDI writer; micro_timing/dynamics/accents applied to MIDI output |
| Performance Realizers (4 subtypes) | ✅ | tests/unit/generators/performance/ (20 tests) | ArticulationRealizer, DynamicsCurveRenderer, MicrotimingInjector, CCCurveGenerator; pipeline.py merges them; called from Conductor after note realization; PerformanceLayer passed to MIDI writer |
| Hook IR | ✅ | tests/unit/ir/test_hook.py (11 tests) | Hook frozen dataclass with DeploymentStrategy (rare/frequent/withhold_then_release/ascending_repetition); HookPlan; BarPosition; references MotifSeed by id; serialization round-trip |
| Phrase-Level Dynamics (DynamicsShape) | ✅ | tests/unit/ir/test_dynamics_shape.py (13 tests) | DynamicsShapeType (crescendo/decrescendo/arch/hairpin/steady); velocity_multiplier(position) curve; BarAccent; arch peak at specified position verified; intensity=0 means flat |
| ConversationPlan IR | ✅ | tests/unit/ir/test_conversation.py (13 tests) | ConversationEvent (call_response/fill_in_response/tutti/solo_break/trade); BarRange; primary_voice_per_section; accompaniment mapping; serialization round-trip |
| Vocal IR | ✅ | tests/unit/ir/test_vocal.py (19 tests) | VocalNote, LyricsLine, VocalConstraintViolation; lyrics + vocal range constraints |
| GrooveProfile IR (Layer 3.5) | ✅ | tests/unit/ir/test_groove.py (25 tests), tests/unit/ir/test_groove_expansion.py (7 tests) | Frozen dataclass; 16th-position microtiming + velocity pattern; [-50,50]ms bounds; ghost_probability, swing_ratio, jitter_sigma; apply_to_all_instruments |
| Groove Library (20 profiles) | ✅ | tests/unit/ir/test_groove.py, tests/unit/ir/test_groove_expansion.py | 20 grooves: 12 original + waltz_viennese, shuffle_blues, samba, afrobeat, new_orleans_second_line, drum_n_bass, flamenco_bulerias, bollywood_filmi; grooves/*.yaml |
| MeterSpec IR (Layer 1) | ✅ | tests/unit/ir/test_meter.py (23 tests) | MeterSpec frozen dataclass; parse_meter_string(); grouping disambiguation (7/8 (3,2,2) != (2,2,3)); metric_accents; group_durations_beats() |
| RhythmSystem IR | ✅ | tests/unit/ir/test_rhythm_system.py (24 tests) | RhythmSystem, IqaSystem, TalaSystem; cultural rhythmic frameworks |
| Tonal System IR | ✅ | tests/unit/ir/test_tonal_system.py (23 tests) | CommonPracticeTonality, ModalSystem, MaqamSystem; cultural tuning systems |
| Tuning IR (microtonal) | ✅ | tests/unit/ir/test_tuning.py (20 tests) | ScaleDefinition (cents-based); Tuning class; 28 scales (9 EDO + 6 Japanese + 5 maqam + 5 raga + 2 gamelan + 1 JI) |
| Plan IRs (8 modules) | ✅ | tests/unit/ir/plan/ (55 tests) | ArrangementPlan, DrumPlan, HarmonyPlan, MotifPlan, MusicalPlan, PhrasePlan, SongFormPlan, GlobalContext |

## Rendering

| Feature | Status | Tests | Notes |
|---|---|---|---|
| MIDI writer + per-instrument stems | ✅ | tests/unit/test_render.py (5 tests), test_stem_writer.py (2 tests) | PerformanceLayer-aware MIDI output |
| Audio renderer (FluidSynth) | ✅ | tests/unit/render/test_audio_renderer.py (8 tests) | Optional dependency; requires SoundFont |
| MIDI reader | ✅ | tests/unit/test_midi_reader.py (9 tests) | MIDI → ScoreIR round-trip |
| Iteration management | ✅ | tests/unit/test_iteration.py (7 tests) | v001/v002/... auto-versioning |
| MusicXML writer | ✅ | tests/unit/render/test_musicxml_writer.py (6 tests) | ScoreIR → music21 → .musicxml; instruments, key, time sig, tempo, dynamics; PerformanceLayer accent/tenuto markings |
| LilyPond / PDF writer | ✅ | tests/unit/render/test_lilypond_writer.py (10 tests) | ScoreIR → .ly text; MIDI→LilyPond pitch/duration conversion; lilypond binary subprocess for PDF; warn-and-skip if not installed |
| Strudel emitter | ✅ | tests/unit/render/test_strudel_emitter.py (4 tests) | ScoreIR → Strudel live-coding notation (.js); browser-side instant audition |
| DAW project writer (Reaper RPP) | ✅ | tests/unit/render/test_reaper_writer.py (3 tests) | ScoreIR → .rpp text; per-instrument tracks; MIDI stem references |
| DAW MCP integration | 🟡 | tests/unit/render/test_daw_mcp.py (4 tests) | limitation: stub implementation, always returns disconnected/False/None; interface defined but no real MCP connection; Wave 3+ target |
| Mix chain (full) | ✅ | tests/unit/mix/ (19 tests: eq 4, compression 3, reverb 4, master 4, mix_chain 4) | Per-track EQ/comp/reverb/gain/pan + master LUFS/limiter; pedalboard-based processing |
| Playback (sounddevice) | ✅ | tests/unit/render/test_playback.py (10 tests) | In-memory synthesis + playback; used by yao preview |
| Note Expression Rendering | ✅ | tests/unit/render/test_note_expression_rendering.py (11 tests) | PerformanceLayer → MIDI articulation/dynamics/microtiming application |

## Critique / Verification

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Music lint | ✅ | tests/unit/test_verify.py (11 tests) | Parallel fifths, voice leading |
| Score analyzer | ✅ | tests/unit/test_verify.py | Structure, melody, harmony analysis |
| Evaluator (11 metrics, 3 dims) | ✅ | tests/unit/test_evaluator.py (20 tests), tests/unit/test_evaluator_dynamic_weights.py (8 tests) | MetricGoal-based; structure / melody / harmony; genre-driven dynamic weights via UnifiedGenreProfile; percussion_centric mode; includes motif_recall_strength (TARGET_BAND 0.4-0.7) |
| MetricGoal type system | ✅ | tests/unit/verify/test_metric_goal.py (34 tests) | 7 goal types (AT_LEAST, BETWEEN, etc.) |
| Score diff | ✅ | tests/unit/test_diff.py (9 tests) | Modified notes tracking |
| Constraint checker | ✅ | tests/unit/test_constraints.py (8 tests) | Range / voice constraints |
| Ensemble constraints | ✅ | tests/unit/verify/test_ensemble_constraints.py (9 tests) | EnsembleConstraint validation |
| Critique rules (structured) | ✅ | tests/unit/verify/test_critique_rules.py (32 tests) | 35 rules across 8 roles (structural 3, harmonic 3, melodic 3, rhythmic 2, arrangement 3, emotional 2, memorability 2, genre_fitness 2, groove 3, surprise 2, tension 1, hook 3, dynamics 1, conversation 4, metric_drift 1) |
| Critique registry + Finding types | ✅ | tests/unit/verify/test_critique.py (12 tests) | CritiqueRule base, Finding dataclass, CritiqueRegistry |
| Surprise critique rules (2) | ✅ | tests/unit/verify/test_surprise_rules.py (10 tests) | surprise_deficit, surprise_overload (structural) |
| Tension critique rules (1) | ✅ | — | tension_arc_unresolved (harmonic) |
| Hook critique rules (3) | ✅ | tests/unit/verify/test_hook_rules.py (8 tests) | hook_overuse, hook_underuse, hook_misplacement; withhold_then_release in intro detected |
| Dynamics critique rules (1) | ✅ | (integrated in test_hook_rules.py) | flat_phrase_dynamics; fires on sections ≥3 bars without dynamics_shape or accents |
| Groove critique rules (3) | ✅ | tests/unit/verify/test_groove_rules.py (10 tests) | GrooveInconsistencyDetector, MicrotimingFlatnessDetector, EnsembleGrooveConflictDetector |
| Conversation critique rules (4) | ✅ | tests/unit/verify/test_conversation_rules.py (9 tests) | conversation_silence, primary_voice_ambiguity, fill_absence_at_phrase_ends, frequency_collision_unresolved |
| Metric drift rule (1) | ✅ | tests/unit/verify/test_metric_drift.py (3 tests) | MetricDriftDetector |
| Arrangement critique rules (3) | ✅ | tests/unit/verify/test_critique_rules.py, tests/unit/arrange/test_critique_rules.py (8 tests) | FrequencyCollisionDetector, TextureCollapseDetector, EnsembleRegisterViolationDetector |
| Acoustic Divergence Rules (5) | ✅ | tests/unit/verify/test_acoustic_divergence.py (27 tests) | symbolic_acoustic_divergence, lufs_target_violation, spectral_imbalance, brightness_intent_mismatch (mood↔centroid), energy_trajectory_violation (tension↔LUFS correlation); Role.ACOUSTIC (8 roles total) |
| Loopability Validator | ✅ | tests/unit/verify/test_loopability.py (8 tests) | LoopabilityValidator, LoopabilityReport; boundary continuity; overall loopability score |
| Singability Evaluator | ✅ | tests/unit/test_vocal_track.py (12 tests) | SingabilityReport; awkward_leaps, breath_violations, tessitura_strain evaluation |
| Seamlessness Evaluator | ✅ | tests/integration/test_v2_definition_of_done.py | Section boundary, energy, pitch continuity evaluation |
| Aesthetic Evaluator | ✅ | tests/unit/verify/test_aesthetic.py (17 tests) | AestheticReport; multi-dimension aesthetic scoring |
| RecoverableDecision logging | ✅ | tests/unit/verify/test_recoverable.py (19 tests) | 9 registered codes; all known silent fallbacks wrapped; check_silent_fallback.py for detection |

## Conductor

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Generate-evaluate-adapt loop | ✅ | tests/unit/test_conductor.py (16 tests) | compose_from_description, compose_from_spec |
| Section-level regeneration | ✅ | tests/unit/test_conductor.py | regenerate_section via v2 pipeline |
| Critic integration in loop | ✅ | tests/unit/test_conductor.py | CRITIQUE_RULES.run_all() called; findings → adaptations |
| Feedback adaptations (evaluator) | ✅ | tests/unit/test_feedback.py (13 tests) | Temperature, strategy, dynamics adaptations |
| Feedback adaptations (critic findings) | ✅ | tests/unit/test_feedback.py | section_monotony, climax_absence, harmonic_monotony, cliche_progression, intent_divergence |
| SpecCompiler (NL → spec) | 🟢 | tests/unit/sketch/ (74 tests), tests/integration/test_spec_compiler_ja.py (3 tests) | Three-stage fallback (LLM → Keyword → Default); Japanese emotion vocabulary (50+ words, valence×arousal); English 23 keywords preserved; auto language detection; LLM stage ready but requires AnthropicAPIBackend (Wave 1.2); Provenance recorded |
| Multi-candidate Orchestrator | ✅ | tests/unit/conductor/test_multi_candidate.py (11 tests) | N candidates parallel via ThreadPool; critic severity ranking (critical=10,major=3,minor=1); producer top-1 select; opt-in via n_candidates param |
| ConductorResult with critic_findings | ✅ | tests/unit/test_conductor.py | Findings visible in summary() |
| Audio Loop (Conductor) | ✅ | tests/unit/conductor/test_audio_feedback.py (10 tests) | ConductorConfig with enable_audio_loop (opt-in, default OFF); AudioThresholds (LUFS target/tolerance, masking_risk_max); 3 adaptation types (dynamics_adjust, register_adjust, eq_adjust); max 2 audio iterations; requires SoundFont |
| Curriculum Learning | ✅ | tests/unit/conductor/test_curriculum.py (11 tests) | CurriculumDictionary with FailurePattern tracking; record/lookup/save/load; genre-agnostic fallback; best-adaptation ranking |
| Human Feedback Processing | ✅ | tests/unit/conductor/test_human_feedback.py (9 tests) | Structured human feedback integration |
| Six-Phase Protocol | ✅ | tests/unit/test_phase_protocol.py (28 tests) | Phase IntEnum (1-6); PHASE_REQUIRED_ARTIFACTS; check_phase_artifacts(); validate_phase_transition(); PhaseIncompleteError |
| Subagent Message Protocol | ✅ | tests/unit/test_subagent_protocol.py (12 tests) | SubagentMessage dataclass (agent, phase, input_hash, decisions, questions, flags, artifacts); Provenance integration |

## CLI

| Feature | Status | Tests | Notes |
|---|---|---|---|
| yao compose | ✅ | — | Single-pass generation |
| yao conduct | ✅ | tests/unit/test_conductor.py | NL description or spec path |
| yao render | ✅ | — | MIDI → WAV |
| yao validate | ✅ | tests/unit/cli/test_validate_applicability.py (4 tests) | Spec validation and summary with applicability checking |
| yao evaluate | ✅ | — | Re-evaluate latest iteration |
| yao diff | ✅ | — | Compare two seeds |
| yao explain | ✅ | — | Provenance query |
| yao new-project | ✅ | — | Project skeleton |
| yao regenerate-section | ✅ | — | Section regeneration |
| yao preview | ✅ | tests/unit/cli/test_preview.py (2 tests), tests/integration/test_preview_pipeline.py (2 tests) | In-memory generation + FluidSynth synthesis + sounddevice playback; no file output |
| yao watch | ✅ | tests/unit/cli/test_watch.py (2 tests) | File-watch via watchdog + auto-regenerate + auto-play; 500ms debounce |
| yao rate | ✅ | tests/unit/cli/test_rate.py (4 tests) | Interactive 5-dimension rating (memorability/emotional_fit/technical_quality/genre_fitness/overall) + free text; saves JSON |
| yao reflect ingest | ✅ | tests/unit/cli/test_rate.py | Aggregates rating files into UserStyleProfile; computes preferred_range/confidence per dimension |
| yao critique | ✅ | tests/unit/cli/test_critique.py (3 tests) | CLI adversarial critique interface |

## Perception

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Audio Perception (Stage 1) | ✅ | tests/unit/perception/test_audio_features.py (19 tests) | PerceptualReport (frozen); LUFS (pyloudnorm.Meter), spectral (centroid/rolloff/flatness), onset density, tempo stability, 7-band energy, masking risk; section boundaries support |
| Listening Simulator (Step 7.5) | ✅ | tests/unit/perception/test_listening_simulator.py (10 tests) | ListeningSimulator orchestrates post-render perception; persists perceptual.json; mood divergence detection via intent keywords; section boundary support |
| Reference Matcher | ✅ | tests/unit/perception/test_reference_matcher.py (29 tests), test_reference_library.py (10 tests) | SHA256-cached style matching; ReferenceMatchReport; ALLOWED_FEATURES/FORBIDDEN_FEATURES |
| Style Vector | ✅ | tests/unit/perception/test_style_vector.py (24 tests), test_style_vector_extended.py (13 tests) | StyleVector (6 abstract features); no melody/chords copying |
| Surprise Score (Layer 4) | ✅ | tests/unit/perception/test_surprise.py (18 tests), tests/scenarios/test_surprise_distribution.py (3 tests) | SurpriseScorer (bigram n-gram + Krumhansl tonal hierarchy); SurpriseAnalysis with per-note scores, moving average, peaks, variance; no ML deps |
| Mood Classifier | ✅ | tests/unit/perception/test_mood.py (13 tests) | MoodProfile classification from musical features |
| Psych Mapper | ✅ | tests/unit/perception/test_psych_mapper.py (29 tests) | FeatureProfile, Articulation, Dynamics; symbolic→psychological mapping |
| Use-Case Targeted Evaluators (7) | ✅ | tests/unit/perception/test_use_case_evaluator.py (10 tests) | YouTube BGM, Game BGM, Advertisement, Study Focus, Meditation, Workout, Cinematic; all scores [0,1]; per-use-case scoring keys |
| Symbolic Feature Extractors | ✅ | tests/integration/test_v2_definition_of_done.py | 7 extractors: voice_leading_smoothness, motivic_density, surprise_index, register_distribution, temporal_centroid, groove_pocket, chord_complexity |

## Skills / Knowledge

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Genre Skills (29) | ✅ | tests/unit/skills/ (36 tests), tests/integration/test_skill_grounding.py (6 tests) | 29 genre .md files loaded by SkillRegistry; integrated into HarmonyPlanner (chord palette), SpecCompiler (instruments/keys/tempo), genre_fitness critique (tempo range, avoided instruments); Skill edit → output change verified |
| Unified GenreProfile Schema | ✅ | tests/unit/schema/test_unified_genre_profile.py (16 tests) | Pydantic model with 14 nested sections (identity/tempo/meter/tuning/groove/harmony/melody/drums/instrumentation/articulation/production/evaluation/generator_assignments/aesthetic_critique); parent inheritance; IncompleteGenreProfileError; adapters for both System 1 and System 2 |
| Genre Profiles (constants) | ✅ | tests/unit/constants/test_genre_profile.py (25 tests) | GenreProfile, BassStyle, ContourType constants per genre |
| Culture Skills (3) | ✅ | — | .claude/skills/cultures/japanese.md, middle_eastern.md, indian_classical.md; academic source citations; jo-ha-kyū, maqam system, raga system documented |
| Theory Skills (4) | ✅ | — | .claude/skills/theory/voice-leading.md, microtonal.md, process-music.md, twelve-tone.md |
| Psychology Skills (2) | ✅ | — | .claude/skills/psychology/tension-resolution.md, emotion-mapping.md |
| Instrument Skills (1) | 🟢 | — | .claude/skills/instruments/piano.md |
| Articulation Skills (4) | ✅ | — | .claude/skills/articulation/jazz-microtiming.md, piano-pedaling.md, strings-articulation.md, winds-articulation.md |

## Subagents / Commands

| Feature | Status | Tests | Notes |
|---|---|---|---|
| 9 Subagent definitions (.md) | ✅ | — | .claude/agents/ (composer, adversarial-critic, harmony-theorist, mix-engineer, orchestrator, producer, rhythm-architect, conversation-director, spec-compiler) + _protocol.md |
| 7 Subagent Python implementations | ✅ | tests/unit/subagents/ (34 tests) | All 7 roles registered; Composer generates non-empty MotifPlan (Markov bigram + intent) with >= 3 placements per motif; PhrasePlan covers all sections |
| 10 slash commands | ✅ | tests/integration/test_slash_commands.py (8 tests) | .claude/commands/ (compose, conduct, critique, sketch, regenerate-section, explain, render, arrange, pin, feedback) |

## Feedback System

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Pin IR + PinsSpec | ✅ | tests/unit/feedback/test_pin.py (18 tests), tests/unit/feedback/test_pins_spec.py (7 tests) | Pin frozen dataclass; PinLocation (section/bar/beat/instrument); CLI string parsing; PinsSpec Pydantic model; YAML round-trip; immutable |
| Pin-Aware Regenerator | ✅ | tests/unit/feedback/test_pin_aware_regenerator.py (9 tests), tests/scenarios/test_pin_localization.py (5 tests) | regenerate_with_pins(); affected region = pin bar ± 1 padding; unaffected notes bit-identical; provenance records pin_id; intent-based adjustment |
| NL Feedback Translator | 🟢 | tests/unit/feedback/test_nl_translator.py (24 tests), tests/scenarios/test_nl_feedback_translation.py (5 tests) | 30 phrase→intent mappings; section/instrument detection; ambiguous input flagged; StructuredFeedback output; maintainable data table |

## Arrangement

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Arrangement Engine | ✅ | tests/unit/arrange/ (35 tests), tests/integration/test_arrange_pipeline.py (3 tests) | SourcePlanExtractor (MIDI→MusicalPlan, confidence scores); StyleVectorOps (transfer + PreservationContract); DiffWriter (markdown); ArrangementSpec with rights_status |
| Arrangement Operations | ✅ | tests/unit/arrange/test_operations.py (15 tests) | ArrangementOperation, Preservable base classes |

## Sound Design (Layer 3.5)

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Sound Design Layer | ✅ | tests/unit/test_sound_design.py (26 tests), tests/integration/test_d11_sound_design.py (4 tests) | Patch + EffectChain + Effect classes; SoundDesignSpec schema; 5 synthesis kinds; 11 effect types; lazy pedalboard import; graceful degradation without pedalboard |

## Live / Realtime

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Live improvisation mode | ✅ | tests/unit/improvise/ (21 tests) | RealtimeImprovisationEngine (50ms latency budget); ContextBuffer ring buffer (key/chord/tempo estimation); 4 roles (Bassist/Drummer/Accompanist/MelodyFollower); SessionLog; optional dep `pip install yao[live]` |

## A/B Testing & Annotation

| Feature | Status | Tests | Notes |
|---|---|---|---|
| A/B Audition UI | ✅ | tests/unit/audition/test_audition.py (11 tests) | AuditionResult + SectionPreference; FastAPI browser UI; side-by-side comparison; preference recording; save/load JSON; winner determination; optional dep `pip install yao[annotate]` |
| Annotation UI | ✅ | tests/unit/annotate/ (12 tests) | FastAPI local server; Annotation + AnnotationFile Pydantic models; browser UI with audio player + time-range tagging; explicit save only; optional dep `pip install yao[annotate]` |

## Agent Backends

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Backend-Agnostic Agent Protocol | 🟡 | tests/unit/agents/ (29 tests) | limitation: ClaudeCodeBackend (is_stub=True) still falls back to PythonOnly; AnthropicAPIBackend is real (is_stub=False, requires ANTHROPIC_API_KEY, tool_use structured output, provenance with backend/model/prompt_hash/token_usage); Protocol and PythonOnlyBackend work; ClaudeCode is Wave 3+ target |

## Reflection / Learning

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Provenance logging | ✅ | tests/unit/reflect/test_causal_provenance.py (15 tests) | Append-only with causal graph: record_id + caused_by edges; get_causes/get_effects/trace_ancestry; backward-compatible |
| Reflection Layer (Style Profile) | ✅ | tests/unit/reflect/test_style_profile.py (11 tests), tests/unit/reflect/test_style_bias.py (4 tests) | UserStyleProfile with update_from(feedback, score), bias(spec), save/load; preferences for density/dynamics/overall |

## Runtime

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Project Runtime | ✅ | tests/unit/runtime/test_project_runtime.py (7 tests) | Context manager; undo/redo (max 50); generation cache (spec_hash+seed+strategy); lockfile |

## Constants / Data

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Instruments (46 + 8 custom) | ✅ | tests/unit/constants/test_custom_instruments.py (11 tests) | 46 INSTRUMENT_RANGES + 8 custom cultural: shakuhachi, koto, shamisen, taiko, sitar, tabla, oud, ney; GM approx + custom_sf2_path; cultural_origin + idiomatic_techniques |
| Scales (28) | ✅ | tests/unit/constants/test_scales.py (7 tests), tests/unit/constants/test_extended_scales.py (20 tests) | 9 EDO + 6 Japanese + 5 maqam + 5 raga + 2 gamelan + 1 JI; ScaleDefinition cents-based; cultural_context required for non-Western |
| Forms (20) | ✅ | tests/unit/constants/test_forms.py (13 tests), tests/scenarios/test_diversity_sources.py (8 tests) | SongForm + FormSection frozen dataclasses; 20 forms (aaba_32bar, verse_chorus_bridge, rondo, through_composed, blues_12bar, j_pop, game_bgm, ambient, etc.); varying lengths (12-68 bars); 8+ genres covered |
| Drum Patterns (15) | ✅ | drum_patterns/*.yaml | 8 base patterns + 5 non-4/4 + chiptune + game_drive; in YAML data files |
| Groove Library (20) | ✅ | grooves/*.yaml | 20 groove YAML files with microtiming + velocity patterns |

## Schema Extensions

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Extended Time Signatures | ✅ | tests/unit/schema/test_time_signature.py (9 tests), tests/unit/ir/test_timing_extended.py (23 tests) | TimeSignatureSpec with beat_groupings; compound auto-detection (6/8, 9/8, 12/8); PolymeterTrack with sync_at; parse/is_compound/beat_grouping/beats_to_bars utilities; backward compatible |
| TensionArcs schema | ✅ | tests/unit/schema/test_tension_arcs.py (13 tests), tests/scenarios/test_tension_arc_realization.py (4 tests) | TensionArcsSpec Pydantic model; cross-spec validation against section names; 5 patterns (linear_rise, dip, plateau, spike, deceptive) |
| HooksSpec schema | ✅ | tests/unit/schema/test_hooks.py (9 tests) | HooksSpec Pydantic model; YAML loading; unique ID validation; deployment strategy enum; distinctive_strength [0,1] validation |
| GrooveSpec schema | ✅ | tests/unit/schema/test_groove.py (6 tests) | Pydantic model; base + overrides pattern; groove.yaml loading |
| ConversationSpec schema | ✅ | tests/unit/schema/test_conversation.py (11 tests) | VoiceFocusSpec + ConversationEventSpec; YAML loading; unique section validation; fill_capable instruments |

## Neural / AI Integration

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Neural generator bridge (Stable Audio) | ✅ | tests/unit/generators/neural/test_stable_audio_bridge.py (8 tests) | StableAudioTextureGenerator; 5 provenance fields (model_version/prompt/seed/hash/rights); graceful ImportError → NeuralBackendUnavailableError; optional dep `pip install yao[neural]` |

## Tests / QA

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Unit tests | ✅ | tests/unit/ (172 files) | ~1800+ tests |
| Integration tests | ✅ | tests/integration/ (14 files) | ~66 tests |
| Scenario tests | ✅ | tests/scenarios/ (9 files) | ~54 tests |
| Music constraint tests | ✅ | tests/music_constraints/ | 7 parameterized tests |
| Golden MIDI tests | ✅ | tests/golden/ | 6 baselines (3 specs x 2 realizers); comparison.py; regenerate_goldens.py |
| Genre coverage tests | ✅ | tests/genre_coverage/ (3 files) | 111 tests covering all 22 unified genre profiles |
| Property-based tests | ✅ | tests/properties/test_genre_invariants.py | Key/range/section/provenance invariants across 4 strategies × 5 seeds |
| Tonal systems tests | ✅ | tests/tonal_systems/ | 15 tests; v2.0 tonal system abstraction acceptance |
| Audio regression tests | ✅ | tests/audio_regression/test_baseline.py (8 tests) | Synthetic baselines (sine, noise, two-section); deterministic extraction verification; `make test-acoustic` target; `audio_regression` pytest marker for weekly CI |
| Subjective quality tests | ✅ | tests/subjective/test_listening_panel.py | Rating JSON schema; overall ≥ 6.0 threshold; `make test-subjective`; `pytest.mark.subjective` for CI skip |
| LLM quality tests | ✅ | tests/llm_quality/test_motif_quality.py | PythonOnly vs Anthropic API comparison; requires ANTHROPIC_API_KEY |
| Tools tests | ✅ | tests/tools/ (6 files) | calibrate_genres, honesty_check, backend_honesty, critic_coverage, plan_consumption, skill_grounding |
| Architecture lint | ✅ | — | tools/architecture_lint.py; `make arch-lint` |
| Feature status check | ✅ | — | tools/feature_status_check.py; `make feature-status` |
| Genre calibration tool | ✅ | tests/tools/test_calibrate_genres.py (3 tests) | tools/calibrate_genres.py; `make calibrate-genres`; validates all 22 genres |
| Document sync check | ✅ | tests/unit/test_sync_docs.py (4 tests) | tools/sync_docs.py; `make sync-docs`; FEATURE_STATUS ↔ CLAUDE.md Tier checklist; in all-checks pipeline |
| Honesty check | ✅ | tests/tools/test_honesty_check.py (12 tests) | tools/honesty_check.py; `make honesty-check`; architecture consistency verification |
| Capability matrix check | ✅ | — | tools/capability_matrix_check.py; `make matrix-check` |

## Infrastructure

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Pre-commit hooks | ✅ | — | trailing-whitespace, ruff, ruff-format, mypy, arch-lint |
| CI (GitHub Actions) | ✅ | — | lint + type + arch-lint + tests + golden |
| Error system | ✅ | tests/unit/test_errors.py (5 tests) | YaOError hierarchy; PhaseIncompleteError, RangeViolationError, GenerationTimeoutError, NeuralBackendUnavailableError, etc. |
| Constants (46+8 instruments, 28 scales, 14 chords) | ✅ | — | src/yao/constants/ |
| MkDocs documentation site | ✅ | — | mkdocs.yml configured; docs/ with design, tutorials, reference, migration guides |
| Spec templates (5) | ✅ | tests/integration/test_all_templates.py (2 tests) | bgm-90sec, cinematic-3min, lofi-cafe, minimal, trajectory-example |
| Example projects (110+) | ✅ | — | specs/projects/ with anime, baroque, cinematic, dance, flamenco, game, jazz, lofi, orchestra, piano, string quartet, and more |

## Sketch / Dialogue

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Sketch Dialogue (6-turn) | ✅ | tests/unit/sketch/test_dialogue_state.py (9 tests) | SketchState state machine; 6-turn interactive spec building |
| Emotion Vocabulary | ✅ | tests/unit/sketch/test_emotion_vocabulary.py (12 tests) | 50+ Japanese emotion words (valence×arousal); EmotionEntry dataclass |
| Language Detection | ✅ | tests/unit/sketch/test_language_detect.py (10 tests) | Auto language detection (Japanese/English) |
| Multilingual SpecCompiler (ja) | ✅ | tests/unit/sketch/test_multilingual.py (17 tests) | Japanese instrument/tempo/duration/genre keywords; English backward compatible; provenance recorded |

---

## Summary Statistics

| Category | Count |
|---|---|
| Source files (src/yao/) | 208 |
| Test files | 213 |
| Test functions | ~2285 |
| Genre Skills (.md) | 29 |
| Culture/Theory/Other Skills | 14 |
| Subagent definitions | 9 + protocol |
| Slash commands | 10 |
| Critique rules | 35 |
| Drum patterns (YAML) | 15 |
| Groove profiles (YAML) | 20 |
| Song forms | 20 |
| Instruments | 54 (46 standard + 8 custom) |
| Scales | 28 |
| Generators (note-level) | 8 |
| Melodic strategies | 8 |
| Example projects | 110+ |
