# Constraint System

Constraints define musical rules that must (or must not) be followed. They unify range checking, voice leading rules, density limits, ensemble constraints, and negative space into a single system.

## Constraint Types

| Type | Meaning |
|------|---------|
| `must` | Hard requirement -- violation is an error |
| `must_not` | Hard prohibition -- violation is an error |
| `prefer` | Soft preference -- violation is a hint |
| `avoid` | Soft prohibition -- violation is a warning |

## Scope

Constraints can be scoped to specific parts of the composition:

| Scope | Example | Applies To |
|-------|---------|-----------|
| `global` | All notes in the score | Everything |
| `section:chorus` | Notes in the "chorus" section | One section |
| `instrument:piano` | Notes for the piano instrument | One instrument |
| `bars:8-16` | Notes in bars 8-15 | Bar range |

## Available Rules

### Note-Level Rules

| Rule | Description |
|------|-------------|
| `no_parallel_fifths` | Detect parallel perfect fifths between voices |
| `no_parallel_octaves` | Detect parallel octaves between voices |
| `max_density:N` | Maximum simultaneous notes per beat |
| `note_above:C6` | Notes above the given pitch |
| `note_below:E2` | Notes below the given pitch |
| `min_rest_ratio:0.3` | Minimum ratio of silence to sound |

### Ensemble Constraints

These inter-part rules validate multi-instrument arrangements:

| Rule | Description |
|------|-------------|
| `register_separation` | Instruments maintain minimum distance in pitch |
| `downbeat_consonance` | Bass-melody consonance on strong beats |
| `no_frequency_collision` | Parts don't overlap excessively in pitch range |
| `bass_below_melody` | Bass stays in lower register than melody |

Ensemble constraints are automatically checked during the Critic Gate and by arrangement critique rules.

## Example

### Basic Constraints

```yaml
constraints:
  - type: must_not
    rule: no_parallel_fifths
    scope: global
    severity: warning
    description: "Avoid parallel fifths for classical voice leading"

  - type: must_not
    rule: note_above:C6
    scope: instrument:piano
    severity: error
    description: "Keep piano melody below C6 for warmth"

  - type: must_not
    rule: max_density:4
    scope: section:intro
    severity: warning
    description: "Keep intro sparse"
```

### Section-Scoped Constraints

```yaml
constraints:
  - type: prefer
    rule: min_rest_ratio:0.4
    scope: section:intro
    severity: warning
    description: "Intro should breathe with generous rests"

  - type: must_not
    rule: note_below:E2
    scope: instrument:cello
    severity: error
    description: "Keep cello above open E string"
```

### Bar-Range Constraints

```yaml
constraints:
  - type: avoid
    rule: max_density:6
    scope: bars:1-4
    severity: warning
    description: "Keep opening bars relatively simple"
```

## How Constraints Are Enforced

1. **At generation time** -- constraint_checker validates notes during realization
2. **At Critic Gate** -- 35 critique rules include constraint-related checks
3. **Post-generation** -- `yao validate` runs constraint checking on existing output
4. **In feedback loop** -- Conductor adapts spec when constraints are violated

Constraint violations raise `ConstraintViolationError` (for hard constraints) or emit warnings (for soft constraints). Silent clamping is never allowed -- all adjustments are logged via `RecoverableDecision`.
