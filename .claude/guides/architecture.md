# Architecture Guide

## 7-Layer Model

YaO uses strict downward-only dependency flow. Lower layers cannot import upper layers.

| Directory | Layer | Can Import From |
|-----------|-------|----------------|
| `constants/` | 0 | (nothing) |
| `schema/` | 1 | constants |
| `ir/` | 1 | constants |
| `reflect/` | 1 | constants (provenance types are cross-cutting) |
| `generators/` | 2 | constants, schema, ir, reflect |
| `perception/` | 4 | constants, schema, ir, generators |
| `render/` | 5 | constants, schema, ir, generators, perception |
| `verify/` | 6 | constants, schema, ir, generators, perception, render |

## Enforcement

Layer boundaries are checked by `tools/architecture_lint.py` (AST-based, no execution).
Run `make arch-lint` to check. If it fails, restructure your code — do NOT bypass.

## Which Layer?

- **Defines data structures or validates input?** → Layer 1 (schema/ or ir/)
- **Generates notes?** → Layer 2 (generators/)
- **Creates output files (MIDI, audio)?** → Layer 5 (render/)
- **Evaluates quality?** → Layer 6 (verify/)
- **Records decisions?** → Layer 1 (reflect/provenance.py — cross-cutting)

## Library Restrictions

| Library | Allowed In | Purpose |
|---------|-----------|---------|
| `pretty_midi` | ir/, render/ | MIDI creation and editing |
| `music21` | ir/, verify/ | Music theory analysis, MusicXML |
| `librosa` | verify/ only | Audio feature analysis |
| `pyloudnorm` | verify/ only | LUFS loudness measurement |
| `pydantic` | schema/ | YAML spec validation |
| `structlog` | anywhere | Structured logging |
| `click` | cli/ only | CLI framework |
| `numpy/scipy` | anywhere | Numerical computation |

**Never** use music21 for MIDI generation. **Never** use librosa for MIDI ops. **Never** use pretty_midi for theory.

## When to Use Which Library

| Need | Use | Module |
|------|-----|--------|
| Create MIDI notes/tracks | `pretty_midi` | `render/midi_writer.py` |
| Parse MusicXML | `music21` | `ir/` (future) |
| Analyze audio features | `librosa` | `verify/` only |
| Measure loudness (LUFS) | `pyloudnorm` | `verify/` only |
| Validate YAML specs | `pydantic` | `schema/` |
| Structured logging | `structlog` | everywhere |
| CLI commands | `click` | `cli/` |
| Numerical operations | `numpy`/`scipy` | anywhere |
| Timing conversions | `yao.ir.timing` | everywhere (NOT manual math) |
| Note name ↔ MIDI | `yao.ir.notation` | everywhere (NOT manual calc) |
| Chord realization | `yao.ir.harmony.realize()` | generators, verify |
