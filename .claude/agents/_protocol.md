# Subagent Message Protocol

> Version: 2.0
> Status: Active
> Last updated: 2026-05-05

---

## Overview

Every subagent invocation in YaO must produce a `SubagentMessage`. This message
is the canonical format for inter-agent communication and is recorded in
Provenance verbatim.

---

## Message Format (YAML representation)

```yaml
agent: <agent_id>          # e.g., "harmony_theorist", "rhythm_architect"
phase: <Phase enum value>  # 1-6, corresponding to the six cognitive phases
input_hash: <sha256[:12]>  # Hash of the input data for reproducibility

decisions:
  - domain: <str>                    # e.g., "harmony", "rhythm", "texture"
    description: <str>               # What was decided
    rationale: <str>                  # Why this choice was made
    confidence: <float 0.0-1.0>      # How confident the subagent is
    alternatives_rejected:            # Other options considered
      - <str>
      - <str>

questions_to_other_agents:
  - target_agent: <agent_id>
    content: <str>                   # The question
    context: <str>                   # Additional context

flags:                               # Warning/status flags
  - <str>                            # e.g., "low_confidence", "needs_review"

artifacts:                           # Paths to produced artifacts
  - <path>
```

---

## Provenance Recording

When a subagent produces a `SubagentMessage`, the Conductor records each
decision as a `ProvenanceRecord` with these v2.0 fields:

| ProvenanceRecord Field | Source |
|---|---|
| `agent` | `SubagentMessage.agent` |
| `phase` | `SubagentMessage.phase.name` |
| `confidence` | `Decision.confidence` |
| `alternatives_rejected` | `Decision.alternatives_rejected` |
| `skill_referenced` | From active genre Skill (if any) |

---

## Rules

1. **Every subagent must emit a SubagentMessage.** A subagent that returns
   raw data without a message is a v1.0-style stub and must be upgraded.

2. **Decisions must have rationale.** A decision with empty `rationale` is
   rejected at validation time.

3. **Confidence must be honest.** A subagent that always returns 1.0 is
   not providing useful signal. Calibrate confidence to actual uncertainty.

4. **Questions are advisory.** A question to another subagent does not
   block execution. The Conductor may choose to route it or ignore it.

5. **Flags are actionable.** Only use flags that the Conductor can act on:
   - `low_confidence` — triggers re-evaluation
   - `needs_review` — flags for human attention
   - `constraint_tension` — a soft constraint was strained
   - `genre_boundary` — decision is at the edge of genre norms

6. **Input hash enables caching.** If `input_hash` matches a previous
   invocation, the Conductor may reuse the cached result.

---

## Agent IDs (canonical list)

| Agent ID | Role |
|---|---|
| `producer` | Final arbiter, manages workflow |
| `composer` | Melody and harmony generation |
| `harmony_theorist` | Chord progressions and voice leading |
| `rhythm_architect` | Rhythmic patterns and groove |
| `orchestrator` | Instrumentation and arrangement |
| `mix_engineer` | Mixing and spatial placement |
| `adversarial_critic` | Quality critique and anti-pattern detection |
| `conversation_director` | Human interaction management |
| `spec_compiler` | Spec interpretation and validation |
| `sound_designer` | Patches, effects, synthesis (v2.0) |
| `sample_curator` | Sample selection and layering (v2.0) |
| `texture_composer` | Textural evolution and density (v2.0) |
| `beatmaker` | Beat programming and groove design (v2.0) |
| `loop_architect` | Loop construction and variation (v2.0) |

---

## Example

```yaml
agent: harmony_theorist
phase: 3  # SKELETAL_GENERATION
input_hash: "a1b2c3d4e5f6"

decisions:
  - domain: harmony
    description: "Selected Dm7 - G7 - Cmaj7 progression for verse"
    rationale: "ii-V-I provides strong resolution; matches jazz genre Skill recommendation"
    confidence: 0.85
    alternatives_rejected:
      - "Dm - G - C (triads only, less idiomatic for jazz)"
      - "Dm7b5 - G7alt - Cmaj7#11 (too complex for verse, saving for bridge)"

questions_to_other_agents:
  - target_agent: rhythm_architect
    content: "Should the Dm7 land on beat 1 or anticipate on the 'and' of 4?"
    context: "Medium swing feel, 132 BPM"

flags:
  - genre_boundary

artifacts:
  - output/harmony_sketch.json
```
