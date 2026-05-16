# Drum Development Guide

How to add drum patterns and work with the drum system.

## Drum System Architecture

- **IR**: `src/yao/ir/drum.py` — `KitPiece`, `DrumHit`, `DrumPattern`, `GM_DRUM_MAP`
- **Patterns**: `drum_patterns/*.yaml` — 50+ genre-specific patterns
- **Generator**: `src/yao/generators/drum_patterner.py` — pattern loading and generation
- **Rendering**: `src/yao/render/midi_writer.py` — writes drum data on MIDI Channel 10

## Adding a Drum Pattern

### Step 1: Create the YAML file

Create `drum_patterns/<pattern_name>.yaml`:

```yaml
id: <pattern_name>
genre: <genre_tag>
time_signature: "4/4"
swing: 0.0
humanize_ms: 5
bars_per_pattern: 1
hits:
  - { time_beats: 0.0, kit_piece: kick, velocity: 110, duration_beats: 0.25 }
  - { time_beats: 1.0, kit_piece: snare, velocity: 100, duration_beats: 0.25 }
  - { time_beats: 0.0, kit_piece: closed_hat, velocity: 70, duration_beats: 0.25 }
  - { time_beats: 0.5, kit_piece: closed_hat, velocity: 60, duration_beats: 0.25 }
  - { time_beats: 1.0, kit_piece: closed_hat, velocity: 70, duration_beats: 0.25 }
  - { time_beats: 1.5, kit_piece: closed_hat, velocity: 60, duration_beats: 0.25 }
```

### Step 2: Available Kit Pieces

The `KitPiece` type supports these GM percussion sounds:

```
kick, snare, rim, closed_hat, open_hat, pedal_hat,
crash, ride, ride_bell, tom_high, tom_mid, tom_low,
tom_floor, clap, cowbell
```

All are mapped to standard GM MIDI numbers via `GM_DRUM_MAP`.

### Step 3: Pattern Guidelines

- **Always on Channel 10**: Drum data is always MIDI Channel 10 (0-indexed = 9)
- **Humanization**: Keep `humanize_ms` <= 50ms
- **Swing**: 0.0 = straight, 0.67 = triplet swing
- **Ghost notes**: Use lower velocities (30-50) for ghost notes
- **Genre tags**: Reference the pattern from at least one genre profile

### Step 4: Verify

```bash
python -c "from yao.generators.drum_patterner import load_pattern; p = load_pattern('<pattern_name>'); print(p.id, len(p.hits))"
make test
```

## Common Patterns

| Pattern | Description | Time Sig |
|---------|-------------|----------|
| `rock_backbeat` | Kick 1&3, snare 2&4, 8th hats | 4/4 |
| `jazz_swing_ride` | Ride pattern, kick/snare light | 4/4 |
| `four_on_the_floor` | Kick every beat, offbeat hats | 4/4 |
| `reggae_one_drop` | Kick+snare on beat 3 only | 4/4 |
| `bossa_nova` | Cross-stick + kick bossa pattern | 4/4 |
| `trap_half_time` | Half-time snare, hi-hat rolls | 4/4 |

## Rules

- Never use `Note` for drum data — use `DrumHit`
- Never write drum data on channels other than 9 (0-indexed)
- Never hardcode MIDI numbers — use `GM_DRUM_MAP`
- All patterns must pass through humanization (even with `humanize_ms=0`)
