# Vocal Support

YaO supports vocal-centric composition through the VocalSpec schema,
VocalNote IR, and vocal synthesis bridge.

## Composition with Vocals

Add a vocal lead to your composition spec:

```yaml
instruments:
  - name: alto_sax
    role: vocal_lead
    vocal:
      breathing_marks: true
      syllable_density: 0.6
      melisma_frequency: 0.1
```

### VocalSpec Options

| Field | Default | Description |
|-------|---------|-------------|
| `breathing_marks` | `true` | Insert breath rests automatically |
| `syllable_density` | `0.6` | Target notes per beat (0.3=sparse, 1.0=dense) |
| `melisma_frequency` | `0.1` | Probability of melismatic ornamentation |
| `range_override` | `None` | Optional vocal range as MIDI range |

## Vocal IR

The `VocalNote` dataclass wraps a standard `Note` with vocal-specific fields:

- `syllable`: The syllable text for this note
- `melisma_target_pitches`: Additional pitches on the same syllable
- `breath_after`: Whether to insert a breath rest after this note

## Singing Constraints

YaO automatically checks vocal lines for singability:

- **Minimum syllable duration**: 0.25 beats (16th note)
- **Breath rest**: Minimum 0.125 beats after breath marks
- **Accent alignment**: Accented syllables should fall on strong beats

## Vocal Synthesis Bridge

YaO provides a bridge interface for external vocal synthesis engines:

```python
from yao.render.vocal_synth_bridge import get_vocal_bridge

# MIDI fallback (always available)
bridge = get_vocal_bridge("midi_fallback")

# NEUTRINO (requires external installation)
bridge = get_vocal_bridge("neutrino")
```

### Supported Engines

| Engine | Status | Notes |
|--------|--------|-------|
| `midi_fallback` | Available | Renders vocals as GM Choir Aahs |
| `neutrino` | Stub | Requires NEUTRINO installation |

## Workflow

1. Set instrument role to `vocal_lead` in your spec
2. YaO generates a singable melody with breath marks
3. Lyrics can be aligned via `LyricsLine` objects
4. Render via MIDI fallback or external vocal engine
