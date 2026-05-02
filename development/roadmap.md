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

## v3.0 Waves

### Wave 1: Honesty — COMPLETE (2026-05-03)

Closed the gap between documented capability and actual implementation.

| Sprint | Deliverable |
|---|---|
| W1.0 | 5 CI honesty tools (honesty-check, backend-honesty, plan-consumption, skill-grounding, critic-coverage) |
| W1.1 | Composer Subagent — non-empty MotifPlan generation |
| W1.2 | AnthropicAPIBackend — real LLM calls, is_stub=False |
| W1.3 | SpecCompiler — Japanese support, 3-stage fallback |
| W1.4 | V2 Pipeline — rule_based_v2 + stochastic_v2 (100% plan consumption) |

### Wave 2: Alignment — COMPLETE (2026-05-03)

Made the architecture genuinely functional end-to-end.

| Sprint | Deliverable |
|---|---|
| W2.1 | V2 realizers registered as default candidates; Skill loader base |
| W2.2 | 4 aesthetic metrics (surprise, memorability, contrast, pacing); evaluator dimension |
| W2.3 | Audio feature extraction + MixChain foundation |

### Wave 3: Depth — IN PROGRESS

Expanding capabilities and user experience.

| Sprint | Status | Deliverable |
|---|---|---|
| W3.1 | Planned | Performance Layer auto-integration in Conductor |
| W3.2 | **Done** | EnsembleConstraint (5 inter-part rules, Orchestrator register assignment) |
| W3.3 | Planned | Reference library (public domain MIDI + StyleVector cache) |
| W3.4 | **Done** | StyleVector enhancement (4 copyright-safe histogram fields) |
| W3.5 | Planned | Subjective Rating CLI (multi-rater, append-only) |
| W3.6 | **Done** | /sketch 6-turn dialogue with state persistence |
| W3.7 | Planned | Microtonal/Polyrhythm in V2 realizers |
| W3.8 | Planned | Live Improvisation V2 pipeline integration |
| W3.9 | Planned | Arrangement Engine quality (transfer + extraction) |

### Wave 4+ (Post v3.0)

Future exploration — requires roadmap PR after Wave 3 completion:
- Multi-model orchestration
- Real-time collaboration
- VST3 host integration
- Cloud API server mode
- Video sync

---

## Test Coverage Growth

| Phase | Tests |
|---|---|
| Milestone 1 | ~200 |
| Milestone 2 | ~500 |
| Milestone 3 | ~1,094 |
| Wave 1 complete | ~1,074 |
| Wave 2 complete | ~1,104 |
| Wave 3 current | **~1,150** |
