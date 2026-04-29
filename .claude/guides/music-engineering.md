# Music Engineering Guide

## Pitch
- MIDI note numbers: 0–127. C4 (middle C) = 60.
- All conversions via `yao.ir.notation` — never compute manually.
- Scientific pitch notation only: "C4", "F#3", "Bb5".

## Timing
- All tick/beat/second conversions via `yao.ir.timing` (failure pattern F1).
- Default PPQ: 220 (`yao.constants.midi.DEFAULT_PPQ`).
- Time signature changes only at section boundaries.

## Instrument Ranges
- Centralized in `yao.constants.instruments.INSTRUMENT_RANGES`.
- Range violations → `RangeViolationError` (never silent clamp — F2).
- The error message includes note name and fix suggestions.

## Velocity
- Never hardcode (`velocity=100` is forbidden — F3).
- Derive from `DYNAMICS_TO_VELOCITY[section.dynamics]` + trajectory tension modifier.
- Stochastic generators may add ±5 humanization.

## Chord Progressions
- Functional notation: Roman numerals (I, ii, V7/V).
- Concrete pitches only via `yao.ir.harmony.realize()`.
- Never mix functional and concrete in the same context.

## Voice Leading
- Check parallel fifths/octaves via `yao.ir.voicing.check_parallel_fifths()`.
- Minimize `voice_distance()` between consecutive voicings.

## Generators
- All generators extend `GeneratorBase` and return `(ScoreIR, ProvenanceLog)`.
- Register via `@register_generator("name")`.
- Select via `composition.yaml` `generation.strategy` field.
- Stochastic generators use `seed` for reproducibility + `temperature` for variation.

## Musical Correctness Checklist
For any change that generates or modifies notes:
- [ ] All notes within instrument range
- [ ] Velocity derived from dynamics, not hardcoded
- [ ] Timing uses `yao.ir.timing`, not manual arithmetic
- [ ] Provenance records created for all generated elements
- [ ] Integration test produces valid MIDI (readable by pretty_midi)
