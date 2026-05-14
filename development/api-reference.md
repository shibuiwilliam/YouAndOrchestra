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

    # optional fields
    articulation: Articulation | None = None
    tuning_offset_cents: float = 0.0
    microtiming_offset_ms: float = 0.0

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

The detailed spec format provides finer control over all aspects of a composition:

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
                                    # process_music, constraint_satisfaction,
                                    # phrase_aware, ai_seed, loop_evolution
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
    def get_causes(self, record_id: str) -> list[ProvenanceRecord]
    def get_effects(self, record_id: str) -> list[ProvenanceRecord]
    def trace_ancestry(self, record_id: str) -> list[ProvenanceRecord]
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
    sections: tuple[FormSection, ...]
```

### `HarmonyPlan` (`yao.ir.plan.harmony`)
```python
@dataclass(frozen=True)
class HarmonyPlan(PlanNode):
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

### `MeterSpec` (`yao.ir.meter`)
```python
@dataclass(frozen=True)
class MeterSpec:
    numerator: int
    denominator: int
    grouping: tuple[int, ...]
    is_compound: bool
    pulse_unit: str
    metric_accents: tuple[float, ...]

# Key functions:
parse_meter_string(s: str) -> MeterSpec       # "7/8 (2,2,3)" -> MeterSpec
group_durations_beats(meter: MeterSpec) -> tuple[float, ...]
```

### `GrooveProfile` (`yao.ir.groove`)
```python
@dataclass(frozen=True)
class GrooveProfile:
    name: str
    microtiming_offsets_ms: tuple[float, ...]   # 16th-position offsets [-50, 50]
    velocity_pattern: tuple[float, ...]          # 16th-position velocity multipliers
    swing_ratio: float
    ghost_probability: float
    jitter_sigma_ms: float

# Key function:
apply_groove(score_ir: ScoreIR, groove: GrooveProfile, seed: int) -> tuple[ScoreIR, ProvenanceLog]
```

### `NoteExpression` (`yao.ir.expression`)
```python
@dataclass(frozen=True)
class NoteExpression:
    legato_overlap: float = 0.0
    accent_strength: float = 0.0
    glissando_to: MidiNote | None = None
    pitch_bend_curve: tuple[tuple[float, float], ...] = ()
    cc_curves: dict[int, tuple[tuple[float, float], ...]] = field(default_factory=dict)
    micro_timing_ms: float = 0.0
    micro_dynamics: float = 0.0
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

## Verification Types

### `MetricGoal` (`yao.verify.metric_goal`)
```python
class MetricGoal:
    name: str
    mode: str              # AT_LEAST, BETWEEN, EXACTLY, TARGET, etc. (7 modes)
    target: float
    tolerance: float
    rationale: str
```

### `RecoverableDecision` (`yao.reflect.recoverable`)
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

Replaces silent fallbacks. Every compromise is logged, traceable, and fixable in future iterations. 9 registered codes cover all known fallback points.

### `Finding` (`yao.verify.critique.types`)
```python
@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str              # critical, major, minor, suggestion
    role: Role                 # STRUCTURE, HARMONY, MELODY, etc.
    issue: str
    evidence: dict
    location: str | None
    recommendation: str
```

## Generator API

### Legacy (deprecated)

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

Currently registered: `rule_based`, `stochastic`, `markov`, `twelve_tone`, `process_music`, `constraint_satisfaction`, `phrase_aware`, `ai_seed`, `loop_evolution`.

### Plan Generators

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

Register with `@register_plan_generator("name")`. Implemented: `rule_based_form`, `rule_based_harmony`, `rule_based_motif`.

### Note Realizers

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

Register with `@register_note_realizer("name")`. Implemented: `rule_based`, `stochastic`, `rule_based_v2`, `stochastic_v2`.

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

# Evaluation (6 dimensions: structure 20%, melody 25%, harmony 20%, aesthetic 20%, arrangement 10%, acoustics 5%)
evaluate_score(score, spec, trajectory=None) -> EvaluationReport

# Diffing
diff_scores(score_a, score_b) -> ScoreDiff
format_diff(diff: ScoreDiff) -> str

# Constraints
check_constraints(score, constraints: ConstraintsSpec) -> list[LintResult]

# Critique (34 rules)
from yao.verify.critique import CRITIQUE_RULES
findings = CRITIQUE_RULES.run_all(plan, spec)
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

# MusicXML
write_musicxml(score, output_path) -> Path

# LilyPond
write_lilypond(score, output_path) -> Path

# Strudel
write_strudel(score, output_path) -> Path

# DAW (Reaper, MCP bridge)
# yao.render.daw.reaper_writer
write_reaper_project(score, output_path) -> Path
# yao.render.daw.mcp_bridge
send_to_daw(score, bridge_config) -> None

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
| `yao reharmonize <project>` | Apply reharmonization operations to a progression |
| `yao blend-genres <spec>` | Blend multiple genre profiles via GenreVector |
| `yao modulate <spec>` | Plan and apply modulation strategies |
| `yao agent "<prompt>"` | SDK-driven one-shot composition (like `claude -p` for music) |
| `yao serve [--host --port]` | Headless HTTP server (POST /compose, GET /health) |

## Error Hierarchy

```
YaOError (base)
+-- SpecValidationError (field: str | None)
+-- ConstraintViolationError
|   +-- RangeViolationError (instrument, note, valid_low, valid_high)
|   +-- ExpressionValidationError
+-- LayerViolationError
+-- RenderError
+-- VerificationError
+-- ProvenanceError
+-- MissingRightsStatusError
+-- ForbiddenExtractionError
+-- NeuralBackendUnavailableError
+-- NeuralGenerationTimeoutError
+-- BackendNotConfiguredError
+-- AgentBackendError
|   +-- AgentOutputParseError
+-- PhaseIncompleteError (phase, missing_artifacts)
+-- IncompleteGenreProfileError (genre_id, missing_sections)
```

## SDK API (`yao.sdk`)

### `YaoAgent` (`yao.sdk.agent`)
```python
class YaoAgent:
    def __init__(
        self,
        project: str,
        *,
        cwd: Path | None = None,
        permission_mode: str = "acceptEdits",  # default, acceptEdits, plan, bypassPermissions, dontAsk, auto
        extra_options: dict | None = None,
    ) -> None

    async def __aenter__(self) -> YaoAgent
    async def __aexit__(self, ...) -> None

    # 10 async-generator methods — each yields YaoEvent objects
    async def sketch(self, description: str) -> AsyncIterator[YaoEvent]
    async def compose(self, spec_or_desc: str | Path) -> AsyncIterator[YaoEvent]
    async def conduct(self, spec_or_desc: str | Path, *, max_iterations: int = 3) -> AsyncIterator[YaoEvent]
    async def critique(self, iteration: str | None = None) -> AsyncIterator[YaoEvent]
    async def regenerate_section(self, section: str, *, seed: int | None = None) -> AsyncIterator[YaoEvent]
    async def render(self, iteration: str | None = None) -> AsyncIterator[YaoEvent]
    async def diff(self, iter_a: str, iter_b: str) -> AsyncIterator[YaoEvent]
    async def evaluate(self, iteration: str | None = None) -> AsyncIterator[YaoEvent]
    async def explain(self, query: str) -> AsyncIterator[YaoEvent]
    async def chat(self, prompt: str) -> AsyncIterator[YaoEvent]

    # Lifecycle methods
    async def interrupt(self) -> None  # Abort current run; emits ConductorFinishedEvent(status="interrupted")
    def set_permission_mode(self, mode: str) -> None  # Change permission for subsequent operations
```

### Per-Subagent Configuration (`yao.sdk.agents`)
```python
# Per-role tool allowlists and effort tuning
_AGENT_TOOLS: dict[str, list[str]]   # role -> allowed tool names
_AGENT_EFFORT: dict[str, str]        # role -> "high" | "medium" | default

# Enriched in yao_agent_definitions():
# Each AgentDefinition gets tools, disallowedTools, and effort fields
```

### Structured Error Payloads (`yao.sdk.server`)
```python
# MCP tool errors carry domain-specific structured fields:
# RangeViolationError -> {instrument, note, valid_low, valid_high}
# SpecValidationError -> {field, message}
# ConstraintViolationError -> {constraint, details}
```

### Streaming Events (`yao.sdk.events`)
```python
class YaoEvent:
    iteration: str | None
    phase: str | None
    timestamp_ms: int

class PhaseStartedEvent(YaoEvent):      phase_name: str
class PhaseCompletedEvent(YaoEvent):    phase_name: str
class SubagentStartedEvent(YaoEvent):   agent_name: str
class IterationCompletedEvent(YaoEvent): iteration_path: str; pass_status: bool; evaluation: dict
class EvaluationReportEvent(YaoEvent):  scores: dict
class CritiqueAvailableEvent(YaoEvent): severity_counts: dict
class AudioReadyEvent(YaoEvent):        wav_path: str; duration_seconds: float
class ProvenanceUpdatedEvent(YaoEvent): record_count: int
class ConductorFinishedEvent(YaoEvent): final_iteration_path: str; total_iterations: int
```

### Lane B Building Blocks (`yao.sdk`)
```python
# Pre-configured ClaudeAgentOptions
default_yao_options(project: str, *, cwd: Path | None = None, extra_options: dict | None = None) -> dict

# In-process MCP server (15 tools)
create_yao_mcp_server() -> McpSdkServerConfig

# Subagent definitions from .claude/agents/*.md
yao_agent_definitions() -> dict[str, AgentDefinition]

# Standard hooks (auto-render, auto-critique, auto-provenance, pre-validate)
default_yao_hooks() -> list[HookMatcher]

# Permission callback (protects iterations, references, agent defs)
default_yao_permission(tool_name: str, input_data: dict, context: dict) -> bool

# Session helpers
session_key_for_project(project: str) -> str
list_sessions(project: str) -> list[SessionInfo]
tag_session(session_id: str, tag: str) -> None
```

### MCP Tools (15)
| Tool | Purpose |
|---|---|
| `yao_compose` | Single-pass composition |
| `yao_conduct` | Multi-iteration composition with feedback |
| `yao_critique` | Adversarial critique |
| `yao_regenerate_section` | Regenerate one section |
| `yao_render_audio` | MIDI → WAV rendering |
| `yao_evaluate` | Quality evaluation |
| `yao_diff` | Musical diff between iterations |
| `yao_explain` | Provenance query |
| `yao_validate_spec` | Spec validation |
| `yao_load_spec` | Load and parse a spec |
| `yao_new_project` | Create project skeleton |
| `yao_list_iterations` | List project iterations |
| `yao_read_iteration` | Read iteration artifacts |
| `yao_arch_lint` | Architecture boundary check |
| `yao_run_tests` | Run test suite |

---

## Combination Stack Types

### `HarmonicMelodyConstraints` (`yao.ir.harmonic_melody_constraints`)
```python
@dataclass(frozen=True)
class HarmonicMelodyConstraints:
    chord_tones: tuple[MidiNote, ...]
    available_extensions: tuple[MidiNote, ...]
    avoid_notes: tuple[MidiNote, ...]
    target_resolutions: dict[MidiNote, MidiNote]
    style: CouplingStyle

    def score_pitch(self, pitch: MidiNote, position: PositionLabel) -> float:
        """0.0 = serious clash; 1.0 = excellent fit."""

class CouplingStyle(StrEnum):
    COMMON_PRACTICE = "common_practice"
    JAZZ = "jazz"
    BLUES = "blues"
    MODAL = "modal"
    RAGA = "raga"
    MAQAM = "maqam"
```

### `FeatureFlags` (`yao.schema.features`)
```python
class FeatureFlags(BaseModel):
    chord_aware_melody: bool = True
    voice_leading_optimization: bool = True
    reharmonization: bool = False
    modulation_planner: bool = False
    listening_agents: bool = False
    genre_blend: bool = False
    rhythm_markov: bool = False
    polyrhythm: bool = False
    theme_recurrence: bool = False
```

### Coupling Module API (`yao.coupling`) — 11 modules
```python
# Harmonic-Melody Coupling (harmonic_melody.py)
derive_constraints(chord, key, scale_type, style) -> HarmonicMelodyConstraints

# Voice-Leading Optimizer (voice_leading.py)
optimal_voicing_transition(prev_voicing, next_chord, voice_count, constraints) -> list[MidiNote]

# Reharmonization Engine (reharmonization.py)
reharmonize(progression, operations, intensity, style, constraints, rng) -> ChordProgression

# Harmonic Devices (harmonic_devices.py)
# Modulation Planner (modulation.py)
# Rhythm Markov Generator (rhythm_markov.py)
# Phrase Shape Generator (phrase_shape.py)
# Theme Recurrence (theme_recurrence.py)
# Polyrhythm Composer (polyrhythm.py)
# Genre Vector Space (genre_vector.py)
# Listening-Agent Dialog (listening_dialog.py)
```

### Verification Metrics

```python
# yao.verify.melody_harmony_alignment
melody_harmony_alignment(score: ScoreIR) -> float  # Target: ≥ 0.7

# yao.verify.voice_leading_smoothness
voice_leading_smoothness(score: ScoreIR) -> float  # Target: ≤ 1.5× minimum
```
