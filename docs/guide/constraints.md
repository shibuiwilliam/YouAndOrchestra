# Constraint System

Constraints define musical rules that must (or must not) be followed. They unify range checking, voice leading rules, density limits, and negative space into a single system.

## Constraint Types

| Type | Meaning |
|------|---------|
| `must` | Hard requirement — violation is an error |
| `must_not` | Hard prohibition — violation is an error |
| `prefer` | Soft preference — violation is a hint |
| `avoid` | Soft prohibition — violation is a warning |

## Scope

Constraints can be scoped to specific parts of the composition:

| Scope | Example | Applies To |
|-------|---------|-----------|
| `global` | All notes in the score | Everything |
| `section:chorus` | Notes in the "chorus" section | One section |
| `instrument:piano` | Notes for the piano instrument | One instrument |
| `bars:8-16` | Notes in bars 8–15 | Bar range |

## Available Rules

| Rule | Description |
|------|-------------|
| `no_parallel_fifths` | Detect parallel perfect fifths between voices |
| `max_density:N` | Maximum simultaneous notes per beat |
| `note_above:C6` | Notes above the given pitch |
| `note_below:E2` | Notes below the given pitch |
| `min_rest_ratio:0.3` | Minimum ratio of silence to sound |

## Example

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
