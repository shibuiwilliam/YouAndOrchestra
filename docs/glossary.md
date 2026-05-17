# YaO Glossary

Terms used throughout the YaO codebase and documentation.

---

**Adversarial Critic** — A subagent that intentionally attacks generated compositions to find weaknesses. Never praises. See `.claude/agents/adversarial-critic.md`.

**Aesthetic Reference Library** — A curated collection of reference compositions used as stylistic anchors. Stored in `references/` with metadata in `catalog.yaml`.

**Beat** — A musical pulse unit. One beat = one quarter note in common time. Distinct from Tick (MIDI resolution) and Seconds (wall-clock time). See `yao.types.Beat`.

**BPM (Beats Per Minute)** — Tempo measurement. See `yao.types.BPM`.

**Chord Function** — A chord described by its role within a key using Roman numeral notation (I, ii, V7, etc.). Concrete pitches are obtained via `yao.ir.harmony.realize()`.

**Composition** — A complete musical work. Preferred over "track" or "song" in YaO code.

**Cadenza** — A virtuosic solo passage, typically for a single instrument, with heightened dramatic intensity. In YaO, cadenza sections can be specified with high density/tension values and limited `active_instruments`. See the ambient-v4 project for a piano cadenza example.

**Conductor (human)** — The human project owner. Makes all final creative decisions (Principle 5).

**Conductor (engine)** — YaO's agentic orchestration engine that automates the generate-evaluate-adapt-regenerate loop. See `yao.conductor.conductor.Conductor`.

**ConversationPlan** — A plan specifying inter-instrument dialogue events (call-response, fill, tutti, solo break, trade). Produced by the ConversationDirector (Step 5.5). See `yao.ir.conversation`.

**Constraint Violation** — An error raised when a musical rule is broken (e.g., note out of instrument range). See `yao.errors.ConstraintViolationError`.

**Cover Art** — AI-generated album artwork for a composition. Generated via Google Gemini image generation, matched to the composition's mood, genre, and instruments. See `yao.render.cover_art` and `yao cover-art` CLI command.

**Critic Gate** — A validation step between CPIR completion and Note Realization. The Adversarial Critic evaluates the plan before any notes are placed, preventing "fundamentally weak plan, beautifully realized" outcomes.

**Finding** —  A structured critique result emitted by critique rules. Contains rule ID, severity (critical/major/minor/suggestion), evidence, location, and recommendation. Replaces free-text critique. See `yao.verify.critique.types.Finding`.

**Frozen Dataclass** — Python `@dataclass(frozen=True)`. Used for all IR domain objects to ensure immutability and provenance integrity.

**GrooveProfile** — Ensemble-wide microtiming and velocity pattern applied to all instruments. Defines 16th-position offsets, ghost probability, swing ratio, and jitter. See `yao.ir.groove`.

**HarmonyPlan** — A component of the Musical Plan IR that specifies chord events and progressions for each section, before notes are placed. See `yao.ir.plan.harmony.HarmonyPlan`.

**Multi-Act Structure** — A composition organized into distinct dramatic acts (e.g., ambient atmosphere → terrifying cadenza → tender return). Specified via section groupings in `composition.yaml` with contrasting density, tension, and active instruments per act. See the ambient-v4 project for a three-act example.

**Hook** — A memorable musical fragment with a deployment strategy (rare, frequent, withhold-then-release, ascending repetition). See `yao.ir.hook`.

**Iteration** — A versioned generation of a composition within a project. Numbered `v001`, `v002`, etc. Stored under `outputs/projects/<name>/iterations/`.

**Evaluation Report** — Quality scores across 6 dimensions (structure, melody, harmony, aesthetic, arrangement, acoustics) with pass/fail thresholds defined by MetricGoal objects. Used by the Conductor to decide whether to iterate. See `yao.verify.evaluator.EvaluationReport`.

**IR (Intermediate Representation)** — The internal data structures (`Note`, `Part`, `Section`, `ScoreIR`) that represent music between generation and rendering. Layer 3 in the architecture.

**MetricGoal** —  A typed evaluation goal specifying how a metric should be scored. Modes include binary (pass/fail), target (must exceed threshold), tolerance (within range), and comparison (against reference). See `yao.verify.metric_goal.MetricGoal`.

**MIDI Note Number** — Integer 0–127 representing pitch. C4 (middle C) = 60. See `yao.types.MidiNote`.

**Motif** — The smallest musically meaningful unit — a short melodic/rhythmic fragment. See `yao.ir.motif.Motif`.

**CPIR / MPIR (Musical Plan IR)** — The middle-layer abstraction between specification and note generation. Contains SongFormPlan, HarmonyPlan, MotifPlan, PhrasePlan, HookPlan, ArrangementPlan, ConversationPlan. Layer 3a in the architecture. See `yao.ir.plan.musical_plan.MusicalPlan`.

**Music Lint** — Automated detection of musical constraint violations (range errors, parallel fifths, etc.). See `yao.verify.music_lint`.

**Music-as-Plan** — YaO's core philosophy: what makes music compelling is decided in the *planning* phase, before any note is written.

**MusicalPlan** —  The integrated container holding all plan components (SongFormPlan, HarmonyPlan, etc.). The central type of Layer 3a (CPIR). See `yao.ir.plan.musical_plan.MusicalPlan`.

**Negative Space** — The intentional design of silence, frequency gaps, and texture reduction. What is NOT played is as important as what IS played.

**Note Realizer** — A generator that takes a MusicalPlan and produces a ScoreIR (concrete notes). The second stage of generation (after plan generation). See `yao.generators.note.base.NoteRealizerBase`.

**Orchestra** — The collection of all AI subagents. Metaphor for the multi-agent system.

**Orchestration** — Assigning musical parts to specific instruments. Distinct from "voicing" (chord arrangement).

**Phrase** — A musical sentence — a coherent sequence of notes forming a complete musical thought.

**PerceptualReport** — Acoustic analysis output: LUFS (loudness), spectral features (centroid, rolloff, flatness, 7-band energy, masking risk), temporal features (onset density, tempo stability). Produced by the Listening Simulator. See `yao.perception.audio_features`.

**Pin** — A localized piece of user feedback attached to a specific position (section, bar, beat, instrument). See `yao.feedback.pin`.

**Pitch Class** — A note name regardless of octave (C, D, E, etc.). Represented as 0–11 (C=0).

**Plan Generator** — A generator that takes a CompositionSpec and produces a plan component (e.g., SongFormPlan, HarmonyPlan). The first stage of generation (before note realization). See `yao.generators.plan.base.PlanGeneratorBase`.

**PPQ (Pulses Per Quarter Note)** — MIDI timing resolution. YaO default: 220. See `yao.constants.midi.DEFAULT_PPQ`.

**Provenance** — The complete record of all generation decisions — what was decided, why, and by which component. Append-only. See `yao.reflect.provenance`.

**Quality Score** — A user-facing aggregate score from 1.0 to 10.0 across 6 dimensions: structure (20%), melody (25%), harmony (20%), aesthetic (20%), arrangement (10%), acoustics (5%). Computed by `EvaluationReport.quality_score`. See `yao.verify.evaluator`.

**RecoverableDecision** —  A logged, traceable fallback when a generator must compromise (e.g., note out of range). Replaces silent clamps. Records the original value, recovered value, reason, musical impact, and suggested fixes. See `yao.reflect.recoverable.RecoverableDecision`.

**Score IR** — The central data structure: a complete composition represented as sections, parts, and notes. See `yao.ir.score_ir.ScoreIR`.

**Section** — A structural segment of a composition (intro, verse, chorus, bridge, outro, etc.).

**Sketch-to-Spec** — The interactive process of transforming a natural language description into a structured YAML specification.

**SongFormPlan** —  A component of the Composition Plan IR (CPIR) that specifies section structure, bar counts, and dynamics arcs. See `yao.ir.plan.song_form.SongFormPlan`.

**StochasticConfig** — A frozen dataclass containing all tunable parameters for the stochastic generator (15 values: duration factors, velocity offsets, accent values, temperature thresholds, chord probability scales). Centralizes magic numbers that were previously scattered throughout the code. See `yao.generators.stochastic.StochasticConfig`.

**StyleVector** — A 6-field copyright-safe abstract style fingerprint (interval class histogram, chord quality histogram, cadence type distribution, rhythm complexity, harmonic rhythm, register distribution). Never includes melody, chord sequences, or hooks. See `yao.perception.style_vector`.

**SurpriseAnalysis** — Per-note information content based on bigram probabilities and Krumhansl tonal hierarchy. Higher surprise = less expected note. See `yao.perception.surprise`.

**Tick** — The smallest time unit in MIDI. Resolution-dependent. Always convert via `yao.ir.timing`. See `yao.types.Tick`.

**Trajectory** — A time-axis curve describing how a musical parameter (tension, density, predictability) evolves over the composition. See `yao.schema.trajectory.TrajectorySpec`.

**Velocity** — MIDI note intensity (1–127). Never hardcoded — always derived from dynamics curves. See `yao.types.Velocity`.

**Vertical Alignment** —  The principle that input expressiveness (specs), processing depth (generation), and evaluation resolution (critique) must advance together. Never deepen one layer alone.

**UserStyleProfile** — Aggregated preferences from subjective ratings, stored as preferred ranges and confidence per dimension (memorability, emotional fit, technical quality, genre fitness, overall). Built via `yao reflect ingest`.

**Voicing** — The specific pitch arrangement of a chord (which octave, which inversion, which doubling). Distinct from "orchestration" (instrument assignment).

---

## Combination Stack

**Combination Stack** — Coupling layer modules that combine, couple, blend, and dialogue across the existing material library. Never replaces existing generators; always additive and feature-flagged. See `src/yao/coupling/`.

**Coupling Style** — How strictly melody-harmony coupling is enforced. One of: `COMMON_PRACTICE`, `JAZZ`, `BLUES`, `MODAL`, `RAGA`, `MAQAM`. See `CouplingStyle` in `yao.ir.harmonic_melody_constraints`.

**Feature Flags** — Boolean flags in `composition.features` that gate Combination Stack modules. Default-ON: `chord_aware_melody`, `voice_leading_optimization`. Default-OFF: `reharmonization`, `listening_agents`, etc. See `yao.schema.features.FeatureFlags`.

**Genre Vector** — Multi-dimensional embedding of a genre profile, enabling n-way blending and neighbor queries. See `yao.coupling.genre_vector`.

**Harmonic Device** — A genre-typical harmonic gesture (jazz turnaround, gospel walk-up, Coltrane changes, etc.). 15 defined in `src/yao/constants/harmonic_devices/`.

**Harmonic Melody Constraints** — Per-position chord-derived rules for melody pitch selection. `score_pitch()` returns 0.0 (clash) to 1.0 (excellent fit). See `yao.ir.harmonic_melody_constraints`.

**Idiomatic Gesture** — An instrument-specific body-language pattern (violin trill, sax altissimo, sitar meend, etc.). See `yao.coupling.idiomatic_gestures`.

**Listening Agent** — A generator that produces notes based on what other instruments have already played. Gated by `features.listening_agents`. See `yao.coupling.listening_dialog`.

**Melody-Harmony Alignment** — Average chord-conditioned pitch score across a piece. Target: ≥ 0.7, ≥ 0.85 on downbeats. See `yao.verify.melody_harmony_alignment`.

**Modulation Planner** — Subagent that plans key modulations using 7 strategies (pivot chord, direct, chromatic, sequential, enharmonic, common tone, third relation).

**Polyrhythm Texture** — Multiple rhythmic cycles at different ratios (3:4, 4:5, hemiola, etc.). See `yao.coupling.polyrhythm`.

**Reharmonization** — Replacing chords with substitutes (12 operations: secondary dominant, tritone sub, modal interchange, etc.) while preserving melody. See `yao.coupling.reharmonization`.

**Theme Recurrence Graph** — Plan for theme returns and transformations across a piece. Auto-generated from song form. See `yao.coupling.theme_recurrence`.

**Voice-Leading Smoothness** — Total voice motion across consecutive chords / Hungarian-optimal minimum. Target: ≤ 1.5× minimum for common-practice. See `yao.verify.voice_leading_smoothness`.

---

## SDK Surface

**Agent SDK** — The third peer surface for YaO, providing programmatic access via the Claude Agent SDK for Python. Enables web apps, bots, CI pipelines, and notebooks to drive the same orchestra. See `src/yao/sdk/`.

**In-process MCP Server** — An MCP server created via `create_sdk_mcp_server()` that runs in the same process as the SDK client. Exposes 15 tools wrapping every CLI verb. No serialization overhead between tool calls. See `yao.sdk.server`.

**Lane A** — High-level SDK access via the `YaoAgent` facade class. Pre-configures the SDK for music production and exposes one async-generator method per slash command. Five lines suffice for most tasks. See `yao.sdk.agent`.

**Lane B** — Low-level SDK access via raw `query()` / `ClaudeSDKClient` plus `default_yao_options()`. For hosting platforms and power users who need to override hooks, permissions, or the system prompt. See `yao.sdk._options`.

**Parity Guarantees (G1--G5)** — Five testable guarantees that the same prompt produces identical artifacts across all three surfaces: same files (G1), same subagent reasoning (G2), same Conductor loop (G3), same provenance and outputs (G4), same constraint and lint results (G5). See `tests/sdk/integration/`.

**Surface** — One of three peer entry points to YaO: Claude Code (interactive), CLI (scriptable), Agent SDK (programmatic). All surfaces call the same Conductor and share the same `.claude/` directory.

**YaoAgent** — The high-level Agent SDK facade class (`yao.sdk.agent.YaoAgent`). Exposes 10 async-generator methods (`sketch`, `compose`, `conduct`, `critique`, `regenerate_section`, `render`, `diff`, `evaluate`, `explain`, `chat`) that mirror slash commands. See `yao.sdk.agent`.

**YaoEvent** — Base class for typed streaming events emitted by the SDK. Nine event types: `PhaseStartedEvent`, `PhaseCompletedEvent`, `SubagentStartedEvent`, `IterationCompletedEvent`, `EvaluationReportEvent`, `CritiqueAvailableEvent`, `AudioReadyEvent`, `ProvenanceUpdatedEvent`, `ConductorFinishedEvent`. See `yao.sdk.events`.
