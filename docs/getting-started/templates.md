# Spec Templates

YaO ships with ready-to-use templates in `specs/templates/`.

## Available Templates

### Simple Format

| Template | Duration | Instruments | Sections |
|----------|----------|-------------|----------|
| `minimal.yaml` | ~16s | Piano | 1 (verse) |
| `bgm-90sec.yaml` | ~58s | Piano, bass | 4 (intro, verse, chorus, outro) |
| `cinematic-3min.yaml` | ~2.4min | Strings, piano, cello, horn | 6 (intro, build, chorus, verse, chorus, outro) |
| `trajectory-example.yaml` | -- | -- | Trajectory curves only |
| `lofi-cafe.yaml` | -- | Piano, bass | Lo-fi cafe vibe |

### Detailed Format (11-section spec)

| Template | Duration | Description |
|----------|----------|-------------|
| `v2/cinematic-3min.yaml` | ~2.4min | Full cinematic with emotion, hooks, groove |
| `v2/bgm-90sec-pop.yaml` | ~58s | Pop BGM with melody/harmony sections |
| `v2/loopable-game-bgm.yaml` | -- | Game background music, loop-friendly |

## Using a Template

```bash
# Copy to your project
cp specs/templates/bgm-90sec.yaml specs/projects/my-song/composition.yaml

# Or generate directly from a template
yao compose specs/templates/cinematic-3min.yaml
```

## Creating Your Own Template

Templates are standard composition YAML files. Save any spec as a template:

```bash
cp specs/projects/my-song/composition.yaml specs/templates/my-template.yaml
```
