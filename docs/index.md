# YaO — You and Orchestra

**An agentic music production environment built on Claude Code.**

YaO turns music composition into a structured, reproducible engineering process. You describe music in YAML, AI generates it following music theory rules, and every decision is tracked with full provenance.

> *Your vision. Your taste. Your soul. — and an Orchestra ready to serve.*

## What YaO Does

- **Spec-driven composition** — Describe your music in YAML and generate full MIDI scores
- **40+ instruments** across 9 families — piano, strings, brass, woodwinds, guitar, bass, synths, saxophone, percussion
- **Trajectory curves** — Shape tension, density, and emotion over time independently from notes
- **Two generator strategies** — Deterministic (rule-based) and stochastic (seed + temperature)
- **Quality evaluation** — Automated scoring across structure, melody, and harmony
- **Music linting** — Catches range violations, parallel fifths, velocity issues
- **Provenance tracking** — Every note has a recorded rationale
- **Per-instrument stems** — Individual MIDI files per instrument

## Quick Example

```bash
pip install -e ".[dev]"
yao compose specs/templates/bgm-90sec.yaml
```

This generates:
```
outputs/projects/untitled-bgm/iterations/v001/
  ├── full.mid           # Complete MIDI score
  ├── stems/piano.mid    # Per-instrument stems
  ├── stems/acoustic_bass.mid
  ├── analysis.json      # Quality analysis
  └── provenance.json    # Decision log
```

## Design Philosophy

1. **Agent = environment, not composer** — YaO accelerates human creativity, it doesn't replace it
2. **Explain everything** — Every note has a provenance record with a rationale
3. **Constraints liberate** — YAML specs and music theory rules are scaffolds, not cages
4. **Time-axis first** — Design trajectory curves before writing notes
5. **Human ear is truth** — Automated scores inform, humans decide
