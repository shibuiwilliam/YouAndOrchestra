# Gallery

Pre-generated examples showcasing YaO's capabilities across different genres. Each piece includes the full composition spec, trajectory, and intent used for generation.

## Examples

| Audio | Spec | Generator | Notes | Description |
|-------|------|-----------|-------|-------------|
| [short-anime-v1.mp3](https://drive.google.com/file/d/1GRhr3dlH41BJ4krFNCKvYfLiWLQif0fR/view?usp=drive_link) | [short-anime-v1](https://github.com/shibuiwilliam/YouAndOrchestra/tree/main/gallery/short-anime-v1/) | stochastic (seed=42, temp=0.5) | 681 | 28-second anime J-rock opening in Bb major, 165 BPM. Electric guitar lead with driving energy. |
| [short-string-v1.mp3](https://drive.google.com/file/d/1Kex9F1l6jbAROb7GIS4NM9a4ILApJuwm/view?usp=drive_link) | [short-string-v1](https://github.com/shibuiwilliam/YouAndOrchestra/tree/main/gallery/short-string-v1/) | stochastic (seed=42, temp=0.4) | 113 | 29-second Romantic-era string ensemble miniature in A major, 90 BPM. Elegant and tender. |
| [short-jazz-v1.mp3](https://drive.google.com/file/d/1KXKeYuJo9H2OpNybEmV8OSM7nCiFh6nN/view?usp=drive_link) | [short-jazz-v1](https://github.com/shibuiwilliam/YouAndOrchestra/tree/main/gallery/short-jazz-v1/) | stochastic (seed=42, temp=0.4) | 169 | 30-second cool jazz for a midnight bar in Bb minor, 80 BPM. Tenor sax melody with piano, contrabass, drums, and bell. |
| [puzzle-light.mp3](https://drive.google.com/file/d/1Pq8btcpo1iOjKxffWGm1IhSksUxxOynu/view?usp=drive_link) | [puzzle-light](https://github.com/shibuiwilliam/YouAndOrchestra/tree/main/gallery/puzzle-light/) | stochastic (seed=42, temp=0.4) | 229 | 29-second light puzzle game BGM in C major, 90 BPM. Loopable and cheerful. |

## Extended Compositions

These larger-scale pieces demonstrate multi-act structures, section regeneration, and the full sketch-to-conduct workflow:

| Project | Genre | Tempo | Duration | Instruments | Description |
|---------|-------|-------|----------|-------------|-------------|
| [primal-trio](https://github.com/shibuiwilliam/YouAndOrchestra/tree/main/specs/projects/primal-trio/) | world.percussion_ensemble | 174 BPM | 96 bars | bass drum, snare, tenor drum | Primal percussion trio — interlocking polyrhythmic patterns inspired by drumline, West African ensemble, and taiko traditions. Builds from solo bass drum through layered call-and-response to 32-bar compression ramp converging to unison climax. |
| [ambient-v4](https://github.com/shibuiwilliam/YouAndOrchestra/tree/main/specs/projects/ambient-v4/) | ambient.space | 50 BPM | 240s (50 bars) | oboe, flute, french horn, cello, strings, synth pad, piano (duo), percussion | Three-act ambient soundscape for planetarium. Act I: cosmic drone evolution. Act II: terrifying piano cadenza. Act III: tender return to silence. Cover art generated via Gemini. |

## What's in Each Spec

Each gallery project directory contains:

- **`composition.yaml`** — instruments, sections, tempo, key, constraints, generation config
- **`trajectory.yaml`** — tension, density, brightness, register curves over time
- **`intent.md`** — the creative brief describing emotion, purpose, and references
- **`cover.png`** — AI-generated cover art (if `/cover-art` was run)
- **`sketch_state.json`** — dialogue state from `/sketch` (if used)

## Regenerate

You can regenerate these examples locally:

```bash
yao conduct --spec gallery/short-anime-v1/composition.yaml --project short-anime-v1
yao conduct --spec gallery/short-string-v1/composition.yaml --project short-string-v1
yao conduct --spec gallery/short-jazz-v1/composition.yaml --project short-jazz-v1
yao conduct --spec gallery/puzzle-light/composition.yaml --project puzzle-light
```

Or create your own from a description:

```bash
yao conduct "a mysterious puzzle game BGM, minimal and looping"
```

## Create Your Own

Use the `/sketch` command for an interactive 6-turn dialogue that builds a spec from your musical idea:

```bash
yao sketch "dreamy ambient piano for a rainy afternoon"
```
