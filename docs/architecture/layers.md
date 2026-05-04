# Layer Architecture

YaO uses a strict layered architecture with downward-only dependency flow. This is enforced at build time by `tools/architecture_lint.py`.

## Layer Diagram

```
+--------------------------------------------------------------+
| Conductor (conductor/)                                       |
|   Feedback loop: generate -> evaluate -> adapt -> regenerate |
+--------------------------------------------------------------+
| Layer 6: Verification (verify/)                              |
|   Linting, evaluation (6 dims), aesthetic metrics,           |
|   35 critique rules, ensemble constraints, acoustic          |
|   divergence, constraint checking, MetricGoal                |
+--------------------------------------------------------------+
| Layer 5: Rendering (render/)                                 |
|   MIDI, WAV, MusicXML, LilyPond, Reaper RPP, Strudel,       |
|   stems, iterations                                          |
+--------------------------------------------------------------+
| Layer 4: Perception (perception/)                            |
|   Audio features (LUFS, spectral), surprise scorer,          |
|   StyleVector, use-case eval, listening simulator            |
+--------------------------------------------------------------+
| Layer 3a: Musical Plan IR (MPIR) (ir/plan/)                  |
|   SongFormPlan, HarmonyPlan, MotifPlan, PhrasePlan,          |
|   ArrangementPlan, DrumPattern, HookPlan, ConversationPlan   |
+--------------------------------------------------------------+
| Layer 3b: Score IR (ir/)                                     |
|   Note, Part, Section, ScoreIR, harmony, motif, voicing,     |
|   hook, dynamics_shape, groove, conversation, tension_arc     |
+--------------------------------------------------------------+
| Layer 2: Generation (generators/)                            |
|   Plan generators, V2 note realizers, melodic strategies,    |
|   reactive fills, frequency clearance, groove applicator     |
+--------------------------------------------------------------+
| Layer 1: Specification (schema/, sketch/)                    |
|   Specs (v1+v2), NL compiler (EN+JP), hooks, groove,         |
|   conversation, tension_arcs, arrangement                    |
+--------------------------------------------------------------+
| Layer 0: Constants (constants/)                              |
|   46 instruments, 28 scales, 20 forms, 14 chords, MIDI maps |
+--------------------------------------------------------------+
```

The Conductor sits above all layers. It orchestrates the full generate-evaluate-adapt pipeline and can import from any layer.

### Layer 3a: Musical Plan IR (MPIR)

Layer 3a holds structural, harmonic, melodic, and arrangement decisions as a plan *before* any notes are placed. The key types are:

- **`SongFormPlan`** — Sections, bar counts, dynamics arcs, tension arcs
- **`HarmonyPlan`** — Chord events, progressions per section, tension arcs
- **`MotifPlan`** — Motif seeds with identity strength and placement strategies
- **`PhrasePlan`** — Phrase contours and directions per section
- **`HookPlan`** — Memorable fragments with deployment strategies
- **`ArrangementPlan`** — Instrument roles and register assignments
- **`ConversationPlan`** ��� Inter-instrument dialogue events
- **`MusicalPlan`** — Container combining all plan components

The v2 generation flow is:
```
CompositionSpec → PlanOrchestrator (9 steps) → MusicalPlan → Critic Gate
    → NoteRealizer V2 → GrooveApplicator → Performance → Renderer
```

## Dependency Rules

Lower layers cannot import upper layers. A module in `generators/` (Layer 2) can import from `schema/` (Layer 1) but never from `verify/` (Layer 6).

| Layer | May Import From |
|-------|----------------|
| 0 (constants) | nothing |
| 1 (schema, reflect) | constants |
| 2 (generators) | constants, schema, ir, reflect |
| 3b (ir) | constants |
| 3a (ir/plan) | constants, ir |
| 4 (perception) | layers 0-3a |
| 5 (render) | layers 0-4 |
| 6 (verify) | layers 0-5 |
| conductor | all layers |

## Library Confinement

| Library | Allowed In |
|---------|-----------|
| `pretty_midi` | ir/, render/ |
| `music21` | ir/, render/ |
| `librosa` | perception/, verify/acoustic/ |
| `pyloudnorm` | perception/, mix/ |
| `pedalboard` | mix/ |
| `anthropic` | agents/anthropic_api_backend.py |
| `sounddevice` | improvise/, cli (preview/watch) |
| `torch` | generators/neural/ |

## Enforcement

```bash
make arch-lint   # Runs tools/architecture_lint.py
```

The linter uses AST parsing to check every import statement without executing code. It now also enforces Layer 3a boundaries.
