# Provenance JSON Schema

The `provenance.json` file records all generation decisions in an append-only log.

## File Location

`outputs/projects/<project>/iterations/v<NNN>/provenance.json`

## Schema

The file is a JSON array of provenance records:

```json
[
  {
    "timestamp": "2026-04-28T12:00:00+00:00",
    "layer": "generator",
    "operation": "generate_melody",
    "parameters": {
      "instrument": "piano",
      "root": "C",
      "scale": "major",
      "bars": 8,
      "note_count": 30
    },
    "source": "RuleBasedGenerator._generate_part_notes",
    "rationale": "Generated melody part for piano using rule-based approach."
  }
]
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (ISO 8601) | When the decision was made (UTC) |
| `layer` | string | Architectural layer that made the decision (e.g., "generator", "render") |
| `operation` | string | Specific operation performed (e.g., "generate_melody", "write_midi") |
| `parameters` | object | Input parameters that influenced the decision |
| `source` | string | Code location that produced this record (class.method) |
| `rationale` | string | Human-readable explanation of why this decision was made |

## Rules

1. **Append-only**: Existing records MUST NOT be deleted or modified (CLAUDE.md §3)
2. **Every generation decision** must produce at least one provenance record
3. The `rationale` field must be meaningful — not "because the code said so"
4. When merging provenance from multiple runs, concatenate the arrays

## RecoverableDecision Records (v2.0)

When a generator must compromise (e.g., a note falls outside an instrument's range), it emits a `RecoverableDecision` instead of silently clamping. These are stored in the provenance log with additional fields:

```json
{
  "timestamp": "2026-04-30T10:00:00+00:00",
  "layer": "generator",
  "operation": "recoverable_decision",
  "parameters": {
    "code": "BASS_NOTE_OUT_OF_RANGE",
    "severity": "warning",
    "original_value": 36,
    "recovered_value": 40,
    "musical_impact": "Bass line jumps up at this point",
    "suggested_fix": ["use synth_bass with wider range", "raise chord root"]
  },
  "source": "StochasticGenerator._generate_bass",
  "rationale": "Walking bass passing tone below upright bass range"
}
```

This makes every compromise visible and actionable in future iterations.

## Implementation

See `yao.reflect.provenance.ProvenanceLog` for the Python API.

```python
from yao.reflect.provenance import ProvenanceLog
from yao.reflect.recoverable import RecoverableDecision

prov = ProvenanceLog()
prov.record(
    layer="generator",
    operation="generate_melody",
    parameters={"key": "C major", "bars": 8},
    source="MyGenerator.generate",
    rationale="Scale-based melody in C major.",
)

# Log a compromise (v2.0)
decision = RecoverableDecision(
    code="NOTE_OUT_OF_RANGE",
    severity="warning",
    original_value=36,
    recovered_value=40,
    reason="Note below instrument range",
    musical_impact="Pitch shifted up",
    suggested_fix=["Use instrument with wider range"],
)
prov.record_recoverable(decision)

prov.save(Path("provenance.json"))
```
