# API Reference

## Core Types

### `Note` (`yao.ir.note`)
```python
@dataclass(frozen=True)
class Note:
    pitch: MidiNote          # 0-127
    start_beat: Beat         # position in beats
    duration_beats: Beat     # length in beats
    velocity: Velocity       # 1-127
    instrument: str          # canonical instrument name

    def end_beat(self) -> Beat
    def validate_range(self, instrument_range=None) -> None
```

### `ScoreIR` (`yao.ir.score_ir`)
```python
@dataclass(frozen=True)
class ScoreIR:
    title: str
    tempo_bpm: BPM
    time_signature: str      # e.g., "4/4"
    key: str                 # e.g., "C major"
    sections: tuple[Section, ...]

    def all_notes(self) -> list[Note]
    def part_for_instrument(self, instrument: str) -> list[Note]
    def instruments(self) -> list[str]
    def total_bars(self) -> int
    def total_beats(self) -> Beat
    def duration_seconds(self) -> Seconds
```

### `CompositionSpec` (`yao.schema.composition`)
```python
class CompositionSpec(BaseModel):
    title: str
    genre: str = "general"
    key: str = "C major"
    tempo_bpm: float = 120.0       # 20.0-300.0
    time_signature: str = "4/4"
    total_bars: int = 0
    instruments: list[InstrumentSpec]
    sections: list[SectionSpec]
    generation: GenerationConfig = GenerationConfig()

    def computed_total_bars(self) -> int
    @classmethod
    def from_yaml(cls, path: Path) -> CompositionSpec
```

### `CompositionSpecV2` (`yao.schema.composition_v2`)

The v2 spec format provides finer control over all aspects of a composition:

```python
class CompositionSpecV2(BaseModel):
    identity: IdentitySpec       # title, purpose, duration_sec, loopable
    globals: GlobalSpec          # key, bpm, time_signature, genre
    emotion: EmotionSpec         # valence, energy, tension, warmth, nostalgia (0-1)
    form: FormSpec               # sections list with dynamic properties
    melody: MelodySpec           # contour, range, motifs
    harmony: HarmonySpec         # progressions, voicing rules, functional harmony
    rhythm: RhythmSpec           # patterns, syncopation, groove
    drums: DrumsSpec             # kit, patterns, dynamics
    arrangement: ArrangementSpec # instrumentation, layering, effects
    production: ProductionSpec   # LUFS target, stereo width, effects
    constraints: ConstraintsSpec # must/must_not/prefer/avoid rules
```

### `GenerationConfig` (`yao.schema.composition`)
```python
class GenerationConfig(BaseModel):
    strategy: str = "rule_based"    # rule_based, stochastic, markov, twelve_tone,
                                    # process_music, constraint_solver,
                                    # rule_based_v2, stochastic_v2
    seed: int | None = None         # for reproducibility
    temperature: float = 0.5        # 0.0=conservative, 1.0=adventurous
```

### `ProvenanceLog` (`yao.reflect.provenance`)
```python
class ProvenanceLog:
    def record(*, layer, operation, parameters, source, rationale) -> None
    def record_recoverable(decision: RecoverableDecision) -> None
    def query_by_operation(self, operation: str) -> list[ProvenanceRecord]
    def query_by_layer(self, layer: str) -> list[ProvenanceRecord]
    def explain_chain(self) -> str
    def to_json(self) -> str
    def save(self, path: Path) -> None
```

## Musical Plan IR Types (MPIR)

### `MusicalPlan` (`yao.ir.plan.musical_plan`)
```python
@dataclass(frozen=True)
class MusicalPlan:
    form: SongFormPlan
    harmony: HarmonyPlan
    trajectory: MultiDimensionalTrajectory
    intent: IntentSpec
    provenance: ProvenanceLog
    global_context: GlobalContext
    motif: MotifPlan | None = None
    phrase: PhrasePlan | None = None
    arrangement: ArrangementPlan | None = None
    drums: DrumPattern | None = None
    hook_plan: HookPlan | None = None
    conversation: ConversationPlan | None = None

    def to_json(self) -> str
    def from_json(cls, json_str, trajectory=None, provenance=None) -> MusicalPlan
```

### `SongFormPlan` (`yao.ir.plan.song_form`)
```python
@dataclass(frozen=True)
class SongFormPlan(PlanNode):
    # Structural decisions: section order, bar counts, dynamics arcs
    sections: tuple[FormSection, ...]
```

### `HarmonyPlan` (`yao.ir.plan.harmony`)
```python
@dataclass(frozen=True)
class HarmonyPlan(PlanNode):
    # Chord events: what chord plays at each beat, progressions per section
    events: tuple[ChordEvent, ...]
```

## IR Types

### `ChordFunction` (`yao.ir.harmony`)
```python
@dataclass(frozen=True)
class ChordFunction:
    degree: int                         # scale degree 0-6
    quality: str                        # "maj", "min", "dim", "aug", "dom7", etc.
    inversion: int = 0                  # 0=root, 1=first, 2=second
    applied_to: int | None = None       # secondary dominants (V/V -> applied_to=4)
    roman: str                          # "I", "ii", "V7/V", etc.

class ChordProgression:
    chords: tuple[ChordFunction, ...]
    key_root: str
    scale_type: str

# Key functions:
diatonic_quality(degree: int, scale_type: str) -> str
realize(chord: ChordFunction, key_root: str, scale_type: str, octave=4) -> list[MidiNote]
make_progression(degrees: list[int], key_root: str, scale_type: str) -> ChordProgression
```

### `Motif` (`yao.ir.motif`)
```python
@dataclass(frozen=True)
class Motif:
    notes: tuple[Note, ...]
    label: str = ""
    transformations_applied: tuple[str, ...] = ()

# Transformations:
transpose(motif, semitones: int) -> Motif
invert(motif, axis: MidiNote | None = None) -> Motif
retrograde(motif) -> Motif
augment(motif, factor: float = 2.0) -> Motif
diminish(motif, factor: float = 2.0) -> Motif
```

### `Voicing` (`yao.ir.voicing`)
```python
@dataclass(frozen=True)
class Voicing:
    pitches: tuple[MidiNote, ...]
    chord_function: ChordFunction | None = None

check_parallel_fifths(voicing_a, voicing_b) -> list[tuple[int, int]]
check_parallel_octaves(voicing_a, voicing_b) -> list[tuple[int, int]]
voice_distance(voicing_a, voicing_b) -> int
```

### `MultiDimensionalTrajectory` (`yao.ir.trajectory`)
```python
class MultiDimensionalTrajectory:
    dimensions: dict[str, TrajectoryDimension]

    def value_at(self, dimension: str, beat: Beat) -> float
    def tension_at(self, beat: Beat) -> float
    def density_at(self, beat: Beat) -> float
```

### Timing (`yao.ir.timing`)
```python
beats_to_ticks(beats: Beat, ppq=DEFAULT_PPQ) -> Tick
ticks_to_beats(ticks: Tick, ppq=DEFAULT_PPQ) -> Beat
beats_to_seconds(beats: Beat, bpm: BPM) -> Seconds
seconds_to_beats(seconds: Seconds, bpm: BPM) -> Beat
bars_to_beats(bars: int, time_signature: str = "4/4") -> Beat
```

### Notation (`yao.ir.notation`)
```python
note_name_to_midi(name: str) -> MidiNote     # "C4" -> 60
midi_to_note_name(midi: MidiNote) -> str     # 60 -> "C4"
parse_key(key: str) -> tuple[str, str]       # "C major" -> ("C", "major")
scale_notes(root: str, scale_type: str, octave: int = 4) -> list[MidiNote]
```

## Verification Types (v2.0)

### `MetricGoal` (`yao.verify.metric_goal`)
```python
class MetricGoal:
    name: str
    mode: str              # "binary", "target", "tolerance", "comparison"
    target: float
    tolerance: float
    rationale: str
```

Defines how each evaluation metric is scored. Modes:
- **binary** — pass/fail (e.g., section count matches)
- **target** — score must exceed a threshold
- **tolerance** — score must be within range of target
- **comparison** — score is compared to a reference

### `RecoverableDecision` (`yao.verify.recoverable` / `yao.reflect.recoverable`)
```python
@dataclass
class RecoverableDecision:
    code: str                    # e.g., "BASS_NOTE_OUT_OF_RANGE"
    severity: str                # "warning", "error"
    original_value: Any
    recovered_value: Any
    reason: str
    musical_impact: str
    suggested_fix: list[str]
```

Replaces silent fallbacks. Every compromise is logged, traceable, and fixable in future iterations.

## Generator API

### Legacy (v1, deprecated)

```python
class GeneratorBase(ABC):
    @abstractmethod
    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]: ...
```

Register with `@register_generator("name")`. Select at runtime with `get_generator("name")`.

Currently registered: `rule_based`, `stochastic`, `markov`, `twelve_tone`, `process_music`, `constraint_solver`.

### v2.0: Plan Generators

```python
class PlanGeneratorBase(ABC):
    @abstractmethod
    def plan(
        self,
        spec: CompositionSpec,
        trajectory: MultiDimensionalTrajectory,
        provenance: ProvenanceLog,
    ) -> PlanNode: ...
```

Register with `@register_plan_generator("name")`.

Implemented: FormPlanner, HarmonyPlanner, Composer, DrumPatterner, Orchestrator, ConversationDirector.

### v2.0: Note Realizers

```python
class NoteRealizerBase(ABC):
    @abstractmethod
    def realize(
        self,
        plan: MusicalPlan,
        seed: int,
        temperature: float,
        provenance: ProvenanceLog,
    ) -> ScoreIR: ...
```

Register with `@register_note_realizer("name")`.

## Conductor API

```python
class Conductor:
    def compose_from_description(
        self, description: str,
        project_name: str | None = None,
        max_iterations: int = 3,
    ) -> ConductorResult

    def compose_from_spec(
        self, spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
        project_name: str | None = None,
        max_iterations: int = 3,
    ) -> ConductorResult

    def regenerate_section(
        self, current_score: ScoreIR,
        spec: CompositionSpec,
        section_name: str,
        trajectory: TrajectorySpec | None = None,
        project_name: str | None = None,
        seed_override: int | None = None,
    ) -> ConductorResult
```

### `ConductorResult`
```python
@dataclass
class ConductorResult:
    score: ScoreIR
    spec: CompositionSpec
    midi_path: Path
    stems: dict[str, Path]
    analysis: AnalysisReport
    evaluation: EvaluationReport
    provenance: ProvenanceLog
    iterations: int
    iteration_history: list[EvaluationReport]
    output_dir: Path
    adaptations_applied: list[str]
```

### Feedback (`yao.conductor.feedback`)
```python
suggest_adaptations(eval_report: EvaluationReport, spec: CompositionSpec) -> list[SpecAdaptation]
apply_adaptations(spec: CompositionSpec, adaptations: list[SpecAdaptation]) -> CompositionSpec
```

## Verification API

```python
# Linting
lint_score(score: ScoreIR) -> list[LintResult]

# Analysis
analyze_score(score: ScoreIR) -> AnalysisReport

# Evaluation (6 dimensions: structure, melody, harmony, aesthetic, arrangement, acoustics)
evaluate_score(score, spec, trajectory=None) -> EvaluationReport

# Diffing
diff_scores(score_a, score_b) -> ScoreDiff
format_diff(diff: ScoreDiff) -> str

# Constraints
check_constraints(score, constraints: ConstraintsSpec) -> list[LintResult]
```

### `EvaluationReport`
```python
class EvaluationReport:
    title: str
    scores: list[EvaluationScore]
    passed: bool           # all metrics within tolerance
    pass_rate: float       # fraction passed
    def summary(self) -> str
    def save(self, path: Path) -> None
```

## Rendering API

```python
# MIDI output
write_midi(score, output_path, ppq=220) -> Path
score_ir_to_midi(score, ppq=220) -> pretty_midi.PrettyMIDI
write_stems(score, output_dir, ppq=220) -> dict[str, Path]

# MIDI input (reverse: load existing MIDI back to ScoreIR)
load_midi_to_score_ir(midi_path, spec=None, title=None) -> ScoreIR

# Audio
render_midi_to_wav(midi_path, output_path, soundfont_path=None) -> Path

# Iteration management
next_iteration_dir(project_output_dir) -> Path
list_iterations(project_output_dir) -> list[Path]
current_iteration(project_output_dir) -> Path | None
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `yao conduct "<description>"` | Natural language to MIDI with auto-iteration |
| `yao conduct --spec <yaml> --project <name>` | Run Conductor on existing spec |
| `yao compose <spec> [options]` | Generate composition from YAML spec (single pass) |
| `yao regenerate-section <project> <section>` | Regenerate one section, preserve rest |
| `yao render <midi>` | Render MIDI to WAV |
| `yao validate <spec>` | Validate spec YAML |
| `yao evaluate <project>` | Evaluate latest iteration |
| `yao diff <spec> --seed-a N --seed-b M` | Compare two stochastic generations |
| `yao explain <spec> [--query op]` | Explain provenance decisions |
| `yao new-project <name>` | Create project skeleton |
| `yao preview <spec>` | In-memory generate + synthesize + play (no file output) |
| `yao watch <spec>` | Auto-regenerate on file change (500ms debounce) |
| `yao rate <project>` | Interactive 5-dimension rating |
| `yao reflect ingest [dir]` | Aggregate ratings into UserStyleProfile |

## Error Hierarchy

```
YaOError (base)
+-- SpecValidationError (field: str | None)
+-- ConstraintViolationError
|   +-- RangeViolationError (instrument, note, valid_low, valid_high)
+-- LayerViolationError
+-- RenderError
+-- VerificationError
+-- ProvenanceError
```
