# Layer Architecture

YaO uses a strict 7-layer architecture with downward-only dependency flow. This is enforced at build time by `tools/architecture_lint.py`.

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 6: Verification (verify/)                             │
│   Linting, evaluation, constraint checking, score diffing   │
├─────────────────────────────────────────────────────────────┤
│ Layer 5: Rendering (render/)                                │
│   MIDI writing, audio rendering, stems, iteration mgmt      │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Perception (perception/) [planned]                 │
│   Reference matching, aesthetic judgment substitutes         │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Generation (generators/)                           │
│   Rule-based, stochastic, generator registry                │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Foundation (schema/ + ir/ + reflect/)              │
│   Pydantic specs, IR types, provenance — shared everywhere  │
├─────────────────────────────────────────────────────────────┤
│ Layer 0: Constants (constants/)                             │
│   Instrument ranges, MIDI mappings, scales, chords          │
└─────────────────────────────────────────────────────────────┘
```

## Dependency Rules

Lower layers cannot import upper layers. A module in `generators/` (Layer 2) can import from `schema/` (Layer 1) but never from `verify/` (Layer 6).

| Layer | May Import From |
|-------|----------------|
| 0 (constants) | nothing |
| 1 (schema, ir, reflect) | constants |
| 2 (generators) | constants, schema, ir, reflect |
| 4 (perception) | layers 0–2 |
| 5 (render) | layers 0–4 |
| 6 (verify) | layers 0–5 |

## Library Confinement

| Library | Allowed In |
|---------|-----------|
| `pretty_midi` | ir/, render/ |
| `music21` | ir/, verify/ |
| `librosa` | verify/ |

## Enforcement

```bash
make arch-lint   # Runs tools/architecture_lint.py
```

The linter uses AST parsing to check every import statement without executing code.
