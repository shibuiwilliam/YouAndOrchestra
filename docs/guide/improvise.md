# Live Improvisation

YaO includes a real-time improvisation engine that listens for MIDI input
and generates musical responses via role-based handlers.

## Quick Start

```bash
yao improvise --role bassist --genre jazz --duration 120
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--role` | `accompanist` | Improvisation role (`accompanist`, `bassist`) |
| `--genre` | `default` | Genre for style guidance |
| `--duration` | `60` | Session duration in seconds |

## How It Works

1. The engine starts listening for MIDI input
2. Each incoming note is added to a rolling context buffer
3. A role-specific handler generates response notes based on context
4. Responses are output as MIDI
5. All events are logged with latency metrics

## Latency Budget

The engine targets **50ms** input-to-output latency. If processing exceeds
this budget, a warning is logged.

## Session Log

After the session ends, a summary is printed:

```
Session ended. Events: 342, Responses: 256, Avg latency: 3.2ms
```

## Roles

- **accompanist**: Generates harmonic accompaniment based on detected chord context
- **bassist**: Generates bass lines following the harmonic progression

## Notes

- Requires a MIDI controller connected to the system
- The engine uses `process_note()` for each incoming MIDI event
- No disk writes during the session — export is explicit after stop
