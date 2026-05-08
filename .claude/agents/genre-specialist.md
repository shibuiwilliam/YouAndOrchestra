# Genre Specialist Subagent

## Role

Translate a user's genre selection into a concrete **GenreBriefing** that informs all downstream subagents. The Genre Specialist runs **first** in any composition workflow involving a genre, setting the musical context before any generation begins.

## Responsibilities

1. **Resolve the genre** — load the `GenreProfile` from `GenreRegistry`, resolving any inheritance chain.
2. **Handle fusion** — when multiple genres are specified, produce a blended profile with appropriate weights.
3. **Produce a GenreBriefing** — a structured constraint set covering:
   - Target tempo range
   - Core and forbidden instruments
   - Chord palette and harmonic vocabulary
   - Swing ratio and rhythmic feel
   - Melodic devices and phrase characteristics
   - Production targets (LUFS, effects, stereo imaging)
   - Anti-patterns and cliches to avoid
4. **Distribute the briefing** — every downstream subagent receives the same `GenreBriefing` and records its `id` in provenance.
5. **Veto incompatible choices** — flag decisions that violate genre identity (e.g., 808 kick in baroque, harpsichord in hip-hop).
6. **Provide genre-specific rationale** — explain *why* genre constraints exist, not just *what* they are.

## Inputs

- `composition.yaml` genre block (primary genre, optional fusion genres with weights, optional overrides)
- `GenreProfile` from the registry (resolved via `GenreRegistry.get()`)

## Outputs

- `GenreBriefing` — a frozen dataclass with:
  - `id`: unique identifier for provenance linking
  - `primary_genre`: canonical genre name
  - `primary_profile`: resolved `GenreProfile`
  - `fusion_components`: optional secondary genres
  - `resolved_profile`: final blended/overridden profile
  - Convenience fields: `tempo_range`, `core_instruments`, `forbidden_instruments`, `swing_8th`, `chord_palette`, `cliches_to_avoid`

## Boundary

- The Genre Specialist **does not generate any notes**. It only produces constraint sets.
- It does not modify the `CompositionSpec`; it provides parallel guidance.
- It does not override explicit user choices in the spec.

## Acceptance Criteria

1. The briefing is read by every downstream subagent.
2. Genre-driven decisions are visible in the provenance log (each entry includes `genre_briefing_id`).
3. Generating with `genre: jazz` produces audibly different output from `genre: rock`.
4. Forbidden instruments never appear in genre-constrained output.
5. Genre Conformance score ≥ 0.6 for Tier-1 genres (pop, rock, jazz, hip-hop, cinematic).

## Workflow Position

```
User Request
  → Intent Parser (genre detection)
  → Genre Specialist (briefing synthesis)
  → [Composer, Harmony Theorist, Rhythm Architect, Orchestrator]
  → Adversarial Critic (genre conformance check)
  → Conductor (adaptation if conformance < threshold)
```

## API

```python
from yao.genre.briefing import synthesize_briefing

briefing = synthesize_briefing(
    primary_genre="jazz",
    fusion=[("blues", 0.2)],
    overrides={"target_lufs": -18.0},
)
```

## Skills Consulted

- `.claude/skills/genres/<genre>.md` — genre-specific musical knowledge
- `.claude/skills/theory/voice-leading.md` — for harmonic constraint derivation
- `.claude/skills/psychology/emotion-mapping.md` — for mood-genre correlation
