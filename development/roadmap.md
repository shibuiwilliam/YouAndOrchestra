# Development Roadmap

## Value-Driven Milestones

### Milestone 1: "Describe and Hear" — COMPLETE
**User value:** Describe what you want in YAML, generate it, hear it.

**Delivered:** CLI pipeline, 2 generators, 4 templates, trajectory dynamics, versioning, provenance.

### Milestone 2: "Iterate and Improve" — COMPLETE
**User value:** Tell YaO what you don't like, and it improves.

**Delivered:** Conductor loop, NL composition, section regeneration, 10-metric evaluation, 7 slash commands, 7 subagents.

### Milestone 3: "Richer Music" — COMPLETE
**User value:** Music sounds professional with proper harmony, rhythm, dynamics.

**Delivered:** Harmony IR, motif transforms, voice leading, constraints, v2 spec format, CPIR foundation, MetricGoal, RecoverableDecision.

---

## Phase γ: Eight Structural Improvements — COMPLETE (2026-05-04)

Delivered the eight improvements from PROJECT.md v2.0 §11:

| Phase | Feature | Key Deliverable |
|---|---|---|
| γ.1 | Surprise Score + Tension Arcs | SurpriseScorer, TensionArc IR, 3 critique rules |
| γ.2 | Acoustic Truth | PerceptualReport, ListeningSimulator, 7 use-case evaluators, 3 divergence rules |
| γ.3 | Hook IR + Phrase Dynamics | Hook with DeploymentStrategy, DynamicsShape, HooksSpec, 4 critique rules |
| γ.4 | Ensemble Groove | GrooveProfile IR, GrooveApplicator, GrooveSpec, 3 critique rules |
| γ.5 | Conversation Plan | ConversationPlan, reactive fills, frequency clearance, 4 critique rules |
| γ.6 | Diversity Sources | 20-form library, 8 melodic generation strategies |
| γ.7 | Multilingual | Japanese SpecCompiler (50+ emotion words, valence×arousal) |
| δ.1 | Arrangement Engine | SourcePlanExtractor, StyleVectorOps, PreservationContract, DiffWriter |

## Phase δ: Production Features — COMPLETE (2026-05-04)

| Phase | Feature | Key Deliverable |
|---|---|---|
| δ.1 | Arrangement Engine | MIDI→MusicalPlan extraction, style transfer, diff reports |
| δ.2 | Three-Tier Feedback | Pin IR (localized), NL translator (30 phrases), pin-aware regenerator |

---

## Test Coverage Growth

| Phase | Tests |
|---|---|
| Milestone 1 | ~200 |
| Milestone 2 | ~500 |
| Milestone 3 | ~1,094 |
| v3.0 Waves | ~1,150 |
| Phase γ complete | ~1,680 |
| Phase δ complete | **~1,748** |

---

## Future Directions

These are research directions, not committed roadmap items:

- **Live performance mode** — real-time MIDI controller input (prototype exists)
- **Neural generator bridge** — Stable Audio textures under YaO structural control (prototype exists)
- **DAW MCP integration** — real bidirectional MCP connection to Reaper (interface defined, stub impl)
- **Multi-model orchestration** — different LLMs for different subagents
- **Community reference library** — shared StyleVector format for collaboration
- **Backend-agnostic agents** — Claude Code as one adapter among many
- **Video sync** — align music to visual cues
- **Cloud API server** — expose YaO as a web service
