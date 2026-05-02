# Layer Architecture

YaO uses a strict layered architecture with downward-only dependency flow. This is enforced at build time by `tools/architecture_lint.py`.

## Layer Diagram

```
+--------------------------------------------------------------+
| Conductor (conductor/)                                       |
|   Feedback loop: generate -> evaluate -> adapt -> regenerate |
+--------------------------------------------------------------+
| Layer 6: Verification (verify/)                              |
|   Linting, evaluation (10 metrics + quality score),          |
|   critique (15 rules), constraints, diffing, MetricGoal      |
+--------------------------------------------------------------+
| Layer 5: Rendering (render/)                                 |
|   MIDI writing/reading, audio rendering, stems, iterations   |
+--------------------------------------------------------------+
| Layer 4: Perception (perception/) [planned]                  |
|   Reference matching, aesthetic judgment substitutes         |
+--------------------------------------------------------------+
| Layer 3a: Composition Plan IR (CPIR) (ir/plan/) [v2.0]       |
|   SongFormPlan, HarmonyPlan, MusicalPlan                     |
|   Structural/harmonic decisions BEFORE notes are placed      |
+--------------------------------------------------------------+
| Layer 3b: Score IR (ir/)                                     |
|   Note, Part, Section, ScoreIR, harmony, motif, voicing      |
+--------------------------------------------------------------+
| Layer 2: Generation (generators/)                            |
|   Plan generators + note realizers, pluggable registry       |
+--------------------------------------------------------------+
| Layer 1: Foundation (schema/ + reflect/)                     |
|   Pydantic specs (v1 + v2), provenance, recoverable decisions|
+--------------------------------------------------------------+
| Layer 0: Constants (constants/)                              |
|   Instrument ranges, MIDI mappings, scales, chords           |
+--------------------------------------------------------------+
```

The Conductor sits above all layers. It orchestrates the full generate-evaluate-adapt pipeline and can import from any layer.

### Layer 3a: Composition Plan IR (CPIR) (v2.0)

Layer 3a is the central addition in v2.0. It sits between the Score IR (Layer 3b) and Perception (Layer 4), holding structural and harmonic decisions as a plan *before* any notes are placed. The key types are:

- **`SongFormPlan`** — Sections, bar counts, dynamics arcs
- **`HarmonyPlan`** — Chord events, progressions per section
- **`MusicalPlan`** — Container combining all plan components

Future additions (Phase beta): `MotifPlan`, `PhrasePlan`, `DrumPlan`, `ArrangementPlan`.

The v2.0 generation flow is:
```
CompositionSpec → PlanGenerator → MusicalPlan → NoteRealizer → ScoreIR
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
| `music21` | ir/, verify/ |
| `librosa` | verify/, perception/ |
| `pyloudnorm` | verify/, perception/ |
| `pedalboard` | render/production/ |

## Enforcement

```bash
make arch-lint   # Runs tools/architecture_lint.py
```

The linter uses AST parsing to check every import statement without executing code. It now also enforces Layer 3a boundaries.
