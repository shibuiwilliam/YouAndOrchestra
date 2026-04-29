# YaO Glossary

Terms used throughout the YaO codebase and documentation.

---

**Adversarial Critic** — A subagent that intentionally attacks generated compositions to find weaknesses. Never praises. See `.claude/agents/adversarial-critic.md`.

**Aesthetic Reference Library** — A curated collection of reference compositions used as stylistic anchors. Stored in `references/` with metadata in `catalog.yaml`.

**Beat** — A musical pulse unit. One beat = one quarter note in common time. Distinct from Tick (MIDI resolution) and Seconds (wall-clock time). See `yao.types.Beat`.

**BPM (Beats Per Minute)** — Tempo measurement. See `yao.types.BPM`.

**Chord Function** — A chord described by its role within a key using Roman numeral notation (I, ii, V7, etc.). Concrete pitches are obtained via `yao.ir.harmony.realize()`.

**Composition** — A complete musical work. Preferred over "track" or "song" in YaO code.

**Conductor (human)** — The human project owner. Makes all final creative decisions (Principle 5).

**Conductor (engine)** — YaO's agentic orchestration engine that automates the generate-evaluate-adapt-regenerate loop. See `yao.conductor.conductor.Conductor`.

**Constraint Violation** — An error raised when a musical rule is broken (e.g., note out of instrument range). See `yao.errors.ConstraintViolationError`.

**Frozen Dataclass** — Python `@dataclass(frozen=True)`. Used for all IR domain objects to ensure immutability and provenance integrity.

**Iteration** — A versioned generation of a composition within a project. Numbered `v001`, `v002`, etc. Stored under `outputs/projects/<name>/iterations/`.

**Evaluation Report** — Quality scores across 5 dimensions (structure, melody, harmony, arrangement, acoustics) with pass/fail thresholds. Used by the Conductor to decide whether to iterate. See `yao.verify.evaluator.EvaluationReport`.

**IR (Intermediate Representation)** — The internal data structures (`Note`, `Part`, `Section`, `ScoreIR`) that represent music between generation and rendering. Layer 1 in the architecture.

**MIDI Note Number** — Integer 0–127 representing pitch. C4 (middle C) = 60. See `yao.types.MidiNote`.

**Motif** — The smallest musically meaningful unit — a short melodic/rhythmic fragment. See `yao.ir.motif.Motif`.

**Music Lint** — Automated detection of musical constraint violations (range errors, parallel fifths, etc.). See `yao.verify.music_lint`.

**Music-as-Code** — YaO's core philosophy: treating music as code, specifications, tests, diffs, and provenance rather than opaque audio files.

**Negative Space** — The intentional design of silence, frequency gaps, and texture reduction. What is NOT played is as important as what IS played.

**Orchestra** — The collection of all AI subagents. Metaphor for the multi-agent system.

**Orchestration** — Assigning musical parts to specific instruments. Distinct from "voicing" (chord arrangement).

**Phrase** — A musical sentence — a coherent sequence of notes forming a complete musical thought.

**Pitch Class** — A note name regardless of octave (C, D, E, etc.). Represented as 0–11 (C=0).

**PPQ (Pulses Per Quarter Note)** — MIDI timing resolution. YaO default: 220. See `yao.constants.midi.DEFAULT_PPQ`.

**Provenance** — The complete record of all generation decisions — what was decided, why, and by which component. Append-only. See `yao.reflect.provenance`.

**Score IR** — The central data structure: a complete composition represented as sections, parts, and notes. See `yao.ir.score_ir.ScoreIR`.

**Section** — A structural segment of a composition (intro, verse, chorus, bridge, outro, etc.).

**Sketch-to-Spec** — The interactive process of transforming a natural language description into a structured YAML specification.

**Style Vector** — A multi-dimensional numerical representation of a genre or style, enabling interpolation between styles.

**Tick** — The smallest time unit in MIDI. Resolution-dependent. Always convert via `yao.ir.timing`. See `yao.types.Tick`.

**Trajectory** — A time-axis curve describing how a musical parameter (tension, density, predictability) evolves over the composition. See `yao.schema.trajectory.TrajectorySpec`.

**Velocity** — MIDI note intensity (1–127). Never hardcoded — always derived from dynamics curves. See `yao.types.Velocity`.

**Voicing** — The specific pitch arrangement of a chord (which octave, which inversion, which doubling). Distinct from "orchestration" (instrument assignment).
