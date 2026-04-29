# Spec Templates

YaO ships with ready-to-use templates in `specs/templates/`.

## Available Templates

| Template | Duration | Instruments | Sections |
|----------|----------|-------------|----------|
| `minimal.yaml` | ~16s | Piano | 1 (verse) |
| `bgm-90sec.yaml` | ~58s | Piano, bass | 4 (intro, verse, chorus, outro) |
| `cinematic-3min.yaml` | ~2.4min | Strings, piano, cello, horn | 6 (intro, build, chorus, verse, chorus, outro) |
| `trajectory-example.yaml` | — | — | Trajectory curves only |

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
