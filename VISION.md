# VISION.md — YaO Target Architecture

> This document describes YaO's **target state** — the system we are building toward.
> For what actually works today, see [PROJECT.md](./PROJECT.md) and the Capability Matrix.
> For development rules, see [CLAUDE.md](./CLAUDE.md).

---

## 3. The Vertical Alignment Principle

YaO's architecture is governed by a sixth, meta-level principle that emerged from design review:

> **The expressiveness of the input, the depth of the processing, and the resolution of the evaluation must advance together. Deepening one alone is wasted.**

This principle resolves a real risk: every individual improvement (richer DSL, smarter generator, better critic) becomes ineffective if the other two layers cannot match it.

| Layer | Question |
|---|---|
| **Input** | Can the spec express what we want? |
| **Processing** | Can the pipeline transform that intent into a plan, then into notes? |
| **Output** | Can we evaluate and critique the result with the same precision? |

We commit to advancing all three layers in lockstep across every release.

---

## 6. Musical Plan IR — The Heart of YaO

### 6.1 Why a Plan IR exists

A musical plan answers questions that pure notes cannot:

- *Why* does this section exist? (form intent)
- *Why* does this chord follow that one? (functional role)
- *Why* does this phrase echo the earlier one? (motif lineage)
- *Why* does this drum pattern fit the arrangement? (groove role)

Notes are *what*. Plans are *why*. Critique without plans is shallow; critique with plans is precise.

### 6.2 Structure of MPIR

`src/yao/ir/plan/` defines the following frozen dataclasses:

```python
@dataclass(frozen=True)
class SongFormPlan:
    sections: list[SectionPlan]      # name, bars, role, dynamics
    climax_section_id: str
    energy_curve: TrajectoryCurve
    density_curve: TrajectoryCurve
    tension_curve: TrajectoryCurve
    predictability_curve: TrajectoryCurve

@dataclass(frozen=True)
class ChordEvent:
    section_id: str
    start_beat: float
    duration_beats: float
    roman: str                                  # e.g. "V7/V"
    function: HarmonicFunction                  # tonic / subdom / dom / predom
    tension_level: float                        # [0,1]
    cadence_role: CadenceRole | None            # half / authentic / plagal / deceptive

@dataclass(frozen=True)
class HarmonyPlan:
    chord_events: list[ChordEvent]
    cadences: dict[str, CadenceType]            # section_id → cadence type
    modulations: list[ModulationEvent]
    tension_resolution_points: list[TimePoint]

@dataclass(frozen=True)
class Motif:
    id: str
    rhythm_shape: tuple[float, ...]             # IOIs
    interval_shape: tuple[int, ...]             # semitone intervals
    identity_strength: float                    # how distinctive it is

@dataclass(frozen=True)
class MotifTransform:
    type: Literal["sequence", "inversion", "retrograde", "augmentation",
                  "diminution", "varied"]
    params: dict                                # transform-specific

@dataclass(frozen=True)
class MotifPlan:
    seeds: list[Motif]
    transformations: dict[str, list[MotifTransform]]  # motif_id → transforms

@dataclass(frozen=True)
class PhrasePlan:
    section_id: str
    bars_per_phrase: float
    motif_sequence: list[str]                   # motif ids in order
    contour: ContourShape
    cadence_strength: float
    call_response_role: Literal["call", "response", "none"]

@dataclass(frozen=True)
class DrumHit:
    time: Beat
    duration: Beat
    kit_piece: KitPiece                         # kick / snare / hat / ...
    velocity: int
    microtiming_ms: float = 0.0

@dataclass(frozen=True)
class DrumPattern:
    id: str
    genre: str
    time_signature: str
    hits: list[DrumHit]
    swing: float
    humanize: float
    fills_at: list[FillLocation]

@dataclass(frozen=True)
class ArrangementLayer:
    instrument: str
    role: Role                                  # melody / bass / harmony / counter / pad
    register: str                               # "low" | "mid" | "high"
    density_factor: float
    pattern_family: str
    active_sections: list[str]

@dataclass(frozen=True)
class ArrangementPlan:
    layers: list[ArrangementLayer]
    counter_melody_lines: list[CounterMelodySpec]
    drum_pattern: DrumPattern
    texture_curve: TrajectoryCurve

@dataclass(frozen=True)
class MusicalPlan:
    """The integrated middle representation. The crown jewel of v2.0."""
    intent_normalized: NormalizedIntent
    form: SongFormPlan
    harmony: HarmonyPlan
    motifs_phrases: MotifAndPhraseAssignment
    arrangement: ArrangementPlan
    drums: DrumPattern
    trajectory: MultiDimensionalTrajectory
    provenance: ProvenanceLog
```

### 6.3 What MPIR enables

| Capability | Mechanism |
|---|---|
| **Plan-level critique** | Adversarial Critic operates on MPIR, not just final MIDI |
| **Multi-candidate selection** | Generate N plans; critic ranks; producer integrates |
| **Section-level surgery** | Edit one section's plan, re-realize only that section |
| **Arrangement engine** | Source MIDI → SourcePlan → operations → TargetPlan → notes |
| **Subagent division** | Composer owns MotifPlan, Harmony Theorist owns HarmonyPlan, etc. |
| **Style transfer** | Compute style vectors over plans, not over raw notes |
| **Provenance precision** | "Why this note?" → trace through plan, not just generator seed |

### 6.4 Plan ↔ Score relationship

The Score IR (Layer 3) remains. MPIR (Layer 3.5) does *not* replace it; it *plans* it.

```
MPIR  → (Note Realizer generators) → ScoreIR → (renderers) → MIDI/audio
```

The Score IR holds concrete notes; MPIR holds the rationale. Both are versioned; both are diffable.

---

## 8. Generation Pipeline (7 Steps)

YaO v2.0 replaces the v1.0 "spec → notes" leap with a **7-step pipeline** that produces the MPIR before any note is written.

```
[Step 1: Form Planner]      Spec + Trajectory  →  SongFormPlan
      ↓
[Step 2: Harmony Planner]                       →  HarmonyPlan
      ↓
[Step 3: Motif Developer]                       →  MotifPlan + PhrasePlan
      ↓
[Step 4: Drum Patterner]                        →  DrumPattern
      ↓
[Step 5: Arranger]                              →  ArrangementPlan
      ↓
═══ MUSICAL PLAN COMPLETE — Critic Gate ═══

      ↓
[Step 6: Note Realizer]     MPIR  →  ScoreIR
      ↓
[Step 7: Renderer]          ScoreIR  →  MIDI / Audio / Score
```

### Critic Gate

Between Step 5 and Step 6, the **Adversarial Critic operates on MPIR**. Findings can:

- Propose plan-level edits (loop back to Step 1–5)
- Reject the entire plan and request a different candidate
- Approve and pass to realization

This is where YaO's quality leap happens. Critique at the plan level prevents the system from carefully realizing a fundamentally weak plan.

### Step 6 Note Realizer

The existing rule_based and stochastic generators are **repositioned** as Note Realizers. They no longer consume the spec directly; they consume the MPIR. New realizers (Markov, constraint_satisfaction) can be added without changing earlier steps.

### Determinism

Every step is seeded; every step records its provenance. The combination `(spec, trajectory, seed_per_step)` is sufficient to reproduce any output bit-for-bit.

---

## 10. Perception Substitute Layer

YaO's most distinctive (and previously empty) layer. It exists because **LLMs cannot listen**. Layer 4 substitutes for hearing.

### 10.1 Three stages, three approaches

| Stage | Approach | Tools |
|---|---|---|
| **1. Audio features** | Empirical objective metrics | librosa, pyloudnorm |
| **2. Use-case targeting** | Purpose-driven evaluation | YaO domain rules |
| **3. Reference matching** | Style-vector comparison | Computed feature vectors |

### 10.2 Stage 1 (audio features)

After audio rendering, extract:
- LUFS (integrated, short-term, momentary)
- Peak, RMS, dynamic range
- Spectral centroid, rolloff, flatness
- Onset density per section
- Tempo stability (ms drift)
- Frequency band energy ratios

These produce a `PerceptualReport` that adds objective dimensions to the structural/symbolic evaluation.

### 10.3 Stage 2 (use-case targeting)

```yaml
use_case: youtube_bgm
  → vocal_space_score, loopability, fatigue_risk, lufs_target_match
use_case: game_bgm
  → loop_seam_smoothness, tension_curve_match, repetition_tolerance
use_case: advertisement
  → hook_entry_time (< 7s), energy_peak_position, short_form_memorability
use_case: study_focus
  → low_distraction_score, dynamic_stability, predictability
```

### 10.4 Stage 3 (reference matching, abstract only)

References are **abstract feature vectors**, never raw audio similarity. Allowed comparisons:
- tempo, density curve, spectral balance, section energy, groove profile

Forbidden comparisons (hard-coded blocks):
- melody, chord progression, identifiable hooks

This is enforced by the schema (`do_not_copy:` is a fixed allowlist of comparison axes; deviating raises a schema error).

### 10.5 Listening Simulation

The Conductor's final phase invokes the Perception Layer to simulate listening. Divergence between the predicted experience and `intent.md` triggers regeneration of the offending sections.

---

## 11. Arrangement Engine

The arrangement engine is **YaO's single most differentiated capability**. Anyone can generate fresh music; few systems can read existing music, understand it, and transform it under explicit preservation/transformation contracts.

### 11.1 Pipeline

```
[Input]      MIDI / MusicXML / (optionally audio with stems)
   ↓
[Analyzer]   Section detection, melody extraction, chord estimation,
             motif detection, role classification
   ↓
[SourcePlan] = MPIR of input piece
   ↓
[Preservation Plan]   melody, hook rhythm, chord function, form
[Transformation Plan] genre, bpm, reharm, regroove, reorch
   ↓
[Style Vector Op]
   target_plan = source_plan
                 - vec(source_genre)
                 + vec(target_genre)
                 ⊕ preservation_constraints
   ↓
[TargetPlan] = MPIR of arranged piece
   ↓
[Note Realizer]  → ScoreIR → MIDI/audio
   ↓
[Arrangement Diff]   Markdown report: preserved / changed / risks
   ↓
[Evaluation]
```

### 11.2 Why MPIR enables arrangement

The decision to introduce MPIR (Layer 3.5) was driven significantly by arrangement's needs. Arrangement at the *note level* is brittle — pitch substitution, tempo stretching, instrument remapping. Arrangement at the *plan level* is robust — preserve the harmonic function, vary the voicing; preserve the motif identity, vary the rhythm shape.

### 11.3 Arrangement spec

```yaml
arrangement:
  input:
    file: "inputs/original.mid"
    rights_status: "owned_or_licensed"        # required field

  preserve:
    melody:        { enabled: true, similarity_min: 0.85 }
    hook_rhythm:   { enabled: true, similarity_min: 0.80 }
    chord_function:{ enabled: true, similarity_min: 0.75 }
    form:          { enabled: true }

  transform:
    target_genre: "lofi_hiphop"
    bpm: { mode: "set", value: 86 }
    harmony:
      reharmonization_level: 0.35
      add_7ths: true
    rhythm:
      swing: 0.35
      groove: "laid_back"
    orchestration:
      drums: "dusty_kit"
      bass: "warm_upright"

  evaluate:
    original_preservation_weight: 0.5
    transformation_strength_weight: 0.3
    musical_quality_weight: 0.2
```

### 11.4 Arrangement Diff

Every arrangement run produces a Markdown diff comparable to git diffs:

```markdown
# Arrangement Diff (v003)

## Preserved
- Main hook melodic similarity: 0.91 ✓
- Section form: unchanged ✓
- Chord function similarity: 0.82 ✓

## Changed
- BPM: 128 → 86
- Groove: straight pop → swung lo-fi
- Chords: triads → 7th/9th voicings (35% reharm depth)
- Bass: root → walking with passing tones
- Drums: four-on-floor → laid-back backbeat

## Risks (Adversarial Critic)
- chorus_energy_drop: dropped more than requested (target -20%, actual -38%)
- register_shift: melody preserved but feels lower due to instrumentation
```

---

## 13. The Orchestra: Subagent Design

### 13.1 The seven players

| Subagent | Owns | Inputs | Outputs |
|---|---|---|---|
| **Composer** | Motifs, phrases, themes | intent, spec, trajectory | MotifPlan, PhrasePlan |
| **Harmony Theorist** | Chord progressions, cadences | spec, motif plan | HarmonyPlan |
| **Rhythm Architect** | Drum patterns, grooves | spec, genre | DrumPattern |
| **Orchestrator** | Instruments, voicings, counter-melody | all plans above | ArrangementPlan |
| **Mix Engineer** | Production manifest | spec, ScoreIR | mix instructions |
| **Adversarial Critic** | Finding weaknesses | MPIR (or ScoreIR) | list[Finding] |
| **Producer** | Coordination, final judgment | all of the above + intent | decisions, escalations |

### 13.2 Critic is special

The Adversarial Critic **never praises**. Its sole purpose is to find weaknesses. Producer balances critique against intent.

### 13.3 Producer is the single point of authority

Only Producer can override another subagent's output. This prevents agent-agent infinite loops.

### 13.4 Subagent → Pipeline mapping

```
Step 1 Form Planner       ← Producer (form is meta)
Step 2 Harmony Planner    ← Harmony Theorist
Step 3 Motif Developer    ← Composer
Step 4 Drum Patterner     ← Rhythm Architect
Step 5 Arranger           ← Orchestrator
Critic Gate               ← Adversarial Critic
Step 6 Note Realizer      ← Composer (low-level)
Step 7 Renderer           ← Mix Engineer
```

---

## 14. Cognitive Protocol: 6 Phases x 7 Steps

YaO v1.0 had a **6-phase cognitive protocol** (Intent → Architectural Sketch → Skeletal → Critic Dialogue → Filling → Listening). YaO v2.0 keeps this protocol and **maps it onto the 7-step pipeline**, resolving v1.0's ambiguity:

| Cognitive Phase | Pipeline Steps |
|---|---|
| 1. Intent Crystallization | (pre-pipeline) → finalize `intent.md` |
| 2. Architectural Sketch | Step 1 (Form Planner) + trajectory.yaml |
| 3. Skeletal Generation | Steps 2–5 produce 5 candidate plans |
| 4. Critic-Composer Dialogue | Critic Gate selects/integrates winning plan |
| 5. Detailed Filling | Steps 6–7 realize and render |
| 6. Listening Simulation | Perception Layer evaluates → divergence triggers replan |

This eliminates the v1.0 ambiguity where Phase 4 ("dialogue") had no concrete pipeline mechanism.

### Multi-candidate generation

Step 3's "5 candidates" is a real implementation, not a metaphor. The Conductor instantiates 5 parallel pipelines through Steps 2–5 with different seeds. The Critic ranks all five plans; the Producer either picks a winner or instructs Composer to merge strengths.

---

## 16. Skills & Knowledge

### 16.1 Genre Skills (target: 12 in Phase beta)

```
.claude/skills/genres/
├── cinematic.md          ✅
├── lofi_hiphop.md        🔴
├── j_pop.md              🔴
├── neoclassical.md       🔴
├── ambient.md            🔴
├── jazz.md               🔴
├── edm.md                🔴
├── folk.md               🔴
├── game_bgm.md           🔴
├── anime_bgm.md          🔴
├── rock.md               🔴
├── orchestral.md         🔴
```

Each genre Skill has both a **Markdown form** (for Subagent prompts) and a **YAML form** (for programmatic Generator use). They never desync because the YAML is generated from the Markdown front-matter.

### 16.2 Theory Skills

`.claude/skills/theory/` covers voice leading, reharmonization, counterpoint, modal interchange, secondary dominants, etc. Each entry has examples and counter-examples; rules are tagged with genre dependencies.

### 16.3 Instrument Skills

Each of the 38+ supported instruments has a Skill with range, idiomatic patterns, articulation, frequency profile, and characteristic phrases.

### 16.4 Psychology Skills

Empirical music-psychology mappings (Krumhansl, Huron, Juslin & Sloboda) for the Perception Layer's psych mapper.

---

## 17. Hooks & Automation

| Hook | Trigger | Action |
|---|---|---|
| `pre-commit-lint` | git commit | YAML schema check, music21 lint, golden test smoke |
| `post-generate-render` | after `compose`/`arrange` | Auto-render audio, auto-write critique |
| `post-generate-critique` | after generation | Run rule-based critique, persist `critique.json` |
| `update-provenance` | any plan/score change | Append to provenance log |
| `spec-changed-show-diff` | edit spec | Show what changed musically (MPIR-level) |

Hooks ensure the Capability Matrix discipline: even if an agent forgets, the hook does not.

---

## 18. MCP Integration

| MCP Target | Purpose | Status |
|---|---|---|
| **Reaper DAW** | Project file read/write, track layout | Phase gamma |
| **Sample library** | Search/fetch drum samples, one-shots | Phase gamma |
| **Reference DB** | Rights-cleared reference catalog | Phase gamma |
| **MIDI controller** | Live mode input | Phase delta |
| **SoundFont/VST host** | Tone rendering | Phase gamma |
| **Cloud storage** | Artifact backup, team share | Phase delta |

Each MCP integration is gated on the corresponding capability flag.

---

## 21. Roadmap (180-day Plan)

The roadmap is organized around the **vertical alignment principle**: each phase advances input, processing, and evaluation together.

### Phase alpha (Days 1–30): The Foundation of Alignment

**Goal**: Build the scaffolding so that the three layers can advance in lockstep.

- [ ] **Capability Matrix** introduced and adopted in README, PROJECT, CLAUDE
- [ ] **composition.yaml v2 schema** designed and Pydantic-implemented
- [ ] **intent.md and trajectory.yaml** integrated as first-class artifacts
- [ ] **Musical Plan IR (MPIR)** minimal version: SongFormPlan + HarmonyPlan
- [ ] **MetricGoal** type system implemented
- [ ] **RecoverableDecision** logging mechanism
- [ ] **Golden test infrastructure**

**Milestone**: existing rule_based generator works through composition v2 → MPIR(form+harmony) → Note Realizer 3-stage pipeline. Capability matrix accurate.

### Phase beta (Days 31–75): Plan-Layer Maturity & Mechanized Critique

**Goal**: Complete the Plan IR; mechanize critique.

- [ ] MotifPlan / PhrasePlan / DrumPattern / ArrangementPlan implemented
- [ ] Motif Developer Generator (plan-level)
- [ ] Drum Patterner + 12 `drum_patterns/*.yaml`
- [ ] Adversarial Critic: 30+ rules across 6 roles
- [ ] Trajectory wired as common control signal across all Plan Generators
- [ ] Multi-candidate Conductor (5 candidates → critic-rank → producer-pick)
- [ ] Markov + constraint_solver Note Realizers
- [ ] Subagent eval harness

**Milestone**: Adversarial Critic generates structured findings against MPIR (e.g., "chorus uses cliche I-V-vi-IV without secondary dominants — recommend V/V"). Multi-candidate conductor demonstrably picks better plans.

### Phase gamma (Days 76–120): Differentiation — Perception & Arrangement

**Goal**: Implement YaO's distinctive layers.

- [ ] Perception Stage 1 (audio features, librosa + pyloudnorm)
- [ ] Perception Stage 2 (use-case targeted: BGM/Game/Ad/Study)
- [ ] Counter-melody Generator
- [ ] 12 Genre Skills with paired Markdown + YAML
- [ ] **Arrangement Engine** (the marquee feature):
  - SourcePlan extractor
  - Style vector operations
  - Preservation/transformation contract
  - TargetPlan realizer
  - Arrangement Diff Markdown report
- [ ] MusicXML / LilyPond writers
- [ ] Reference Matcher (Stage 3, abstract features only)

**Milestone**: existing MIDI → arranged MIDI in different genre, with structured diff explaining what was preserved and what changed. Use-case driven evaluation switching observably.

### Phase delta (Days 121–180): Production Readiness

**Goal**: Real-project-grade output and operations.

- [ ] Production Manifest + Mix Chain (pedalboard)
- [ ] Sketch-to-Spec dialogue state machine
- [ ] Instant audition: `yao preview`, `yao watch`
- [ ] Strudel emitter (browser-side instant audition)
- [ ] `yao annotate` browser UI for time-tagged feedback
- [ ] mkdocs site complete: `for-musicians/`, `for-developers/`
- [ ] Showcase: 10+ canonical YaO pieces, weekly auto-updated
- [ ] Reaper MCP integration (initial)
- [ ] Spec composability (`extends:`, `overrides:`, `fragments/`)

**Milestone**: a commercial BGM creator can use YaO end-to-end and import the result into a DAW for finishing.

### Phase epsilon (Continuous): Reflection & Community

- Reflection Layer (Layer 7) for user style profiles
- Community reference library shared format
- Live improvisation mode
- AI music model bridges (Stable Audio, MusicGen) for texture

---

## 26. Future Architecture Extensions

### 26.1 Project runtime (stateful sessions)
Replace stateless CLI with a `ProjectRuntime` that holds generation cache, feedback queue, undo/redo stack. Phase epsilon.

### 26.2 Backend-agnostic agent protocol
Abstract `AgentRole`, `AgentContext`, `AgentOutput` Python protocols; Claude Code becomes one adapter among possible others. Phase epsilon.

### 26.3 Spec composability
`extends:`, `overrides:`, `specs/fragments/` for reusable spec parts. Phase delta.

### 26.4 Reflection layer (Layer 7)
User style profiles learned from feedback history; cross-project pattern mining. Phase epsilon.

### 26.5 Generic creative-domain framework
Abstract YaO patterns (intent-as-code, trajectory, plan IR, adversarial critic, provenance) into a domain-agnostic toolkit. Phase epsilon+.
