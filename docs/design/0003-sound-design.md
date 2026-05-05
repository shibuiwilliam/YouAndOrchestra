# ADR-0003: Sound Design Layer (Layer 3.5)

**Status:** Accepted
**Date:** 2026-05-05
**Deciders:** YaO maintainers

## Context

YaO v1.0 rendered compositions as raw MIDI — timbre was entirely determined
by the downstream player or DAW. For genres where timbre *is* the defining
characteristic (lo-fi hip-hop, ambient, deep house, drum and bass), this is
insufficient. The system needs a declarative layer that specifies synthesis
patches and effect chains per voice, which the render layer can realize into
audio.

## Decision

Introduce **Layer 3.5 (Sound Design)** at `src/yao/sound_design/` with:

1. **`patches.py`** — frozen `Patch` dataclass defining synthesis kind and
   parameters. Five synthesis kinds: `sample_based`, `subtractive`, `fm`,
   `wavetable`, `physical`.

2. **`effects.py`** — frozen `Effect` and `EffectChain` dataclasses defining
   ordered signal processing chains. Eleven effect types: eq, compressor,
   limiter, reverb, convolution_reverb, delay, tape_saturation, bitcrusher,
   chorus, phaser, flanger.

3. **`src/yao/schema/sound_design.py`** — Pydantic `SoundDesignSpec` for YAML
   validation of the `sound_design:` section in composition specs.

### Layer Position

```
Layer 0  constants/
Layer 1  schema/, ir/, reflect/
Layer 2  generators/
Layer 3  sound_design/       ← NEW (conceptually "3.5")
Layer 4  perception/
Layer 5  render/
Layer 6  verify/
Layer 7  conductor/
```

Sound Design may import from: constants, schema, ir.
Render and verify may import from sound_design.

### pedalboard as Optional Dependency

The `pedalboard` library (Spotify's audio plugin host) is used at render time
to apply VST/AU effects. It is NOT a hard dependency:

- Import is lazy (try/except in `__init__.py`)
- `SOUND_DESIGN_AVAILABLE` flag indicates availability
- Missing pedalboard degrades to MIDI-only output
- CI runs without pedalboard; audio tests are marked `@pytest.mark.requires_pedalboard`

## Consequences

- Genre Skills can now declare per-voice patches and effects in their YAML
- The render layer gains a two-stage pipeline: MIDI first, then audio with FX
- Sound design specs are validated at load time, catching errors early
- No runtime crash if pedalboard is absent — graceful degradation
