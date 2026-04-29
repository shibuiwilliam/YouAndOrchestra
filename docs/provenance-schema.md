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

## Implementation

See `yao.reflect.provenance.ProvenanceLog` for the Python API.

```python
from yao.reflect.provenance import ProvenanceLog

prov = ProvenanceLog()
prov.record(
    layer="generator",
    operation="generate_melody",
    parameters={"key": "C major", "bars": 8},
    source="MyGenerator.generate",
    rationale="Scale-based melody in C major.",
)
prov.save(Path("provenance.json"))
```
