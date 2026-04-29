# API Reference

## Core Types

### `Note` (`yao.ir.note`)
```python
@dataclass(frozen=True)
class Note:
    pitch: MidiNote          # 0–127
    start_beat: Beat         # position in beats
    duration_beats: Beat     # length in beats
    velocity: Velocity       # 1–127
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
    tempo_bpm: float = 120.0
    time_signature: str = "4/4"
    total_bars: int = 0
    instruments: list[InstrumentSpec]
    sections: list[SectionSpec]
    generation: GenerationConfig = GenerationConfig()

    def computed_total_bars(self) -> int
    @classmethod
    def from_yaml(cls, path: Path) -> CompositionSpec
```

### `GenerationConfig` (`yao.schema.composition`)
```python
class GenerationConfig(BaseModel):
    strategy: str = "rule_based"    # or "stochastic"
    seed: int | None = None         # for reproducibility
    temperature: float = 0.5        # 0.0=conservative, 1.0=adventurous
```

### `ProvenanceLog` (`yao.reflect.provenance`)
```python
class ProvenanceLog:
    def record(*, layer, operation, parameters, source, rationale) -> None
    def query_by_operation(self, operation: str) -> list[ProvenanceRecord]
    def query_by_layer(self, layer: str) -> list[ProvenanceRecord]
    def explain_chain(self) -> str
    def save(self, path: Path) -> None
```

## Generator API

All generators implement:
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

## Verification API

```python
# Linting
lint_score(score: ScoreIR) -> list[LintResult]

# Analysis
analyze_score(score: ScoreIR) -> AnalysisReport

# Evaluation
evaluate_score(score, spec, trajectory=None) -> EvaluationReport

# Diffing
diff_scores(score_a, score_b) -> ScoreDiff
format_diff(diff: ScoreDiff) -> str

# Constraints
check_constraints(score, constraints: ConstraintsSpec) -> list[LintResult]
```

## Rendering API

```python
# MIDI output
write_midi(score, output_path, ppq=220) -> Path
write_stems(score, output_dir, ppq=220) -> dict[str, Path]

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
| `yao compose <spec> [options]` | Generate composition from YAML spec |
| `yao render <midi>` | Render MIDI to WAV |
| `yao validate <spec>` | Validate spec YAML |
| `yao evaluate <project>` | Evaluate latest iteration |
| `yao diff <spec> --seed-a N --seed-b M` | Compare two stochastic generations |
| `yao explain <spec> [--query op]` | Explain provenance decisions |
| `yao new-project <name>` | Create project skeleton |
