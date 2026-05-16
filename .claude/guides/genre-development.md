# Genre Development Guide

How to add a new genre to YaO. Follow these steps in order.

## Prerequisites

- Read CLAUDE.md and PROJECT.md first
- Understand the existing genre profile format (`genre_profiles/*.yaml`)
- Understand the skill file format (`.claude/skills/genres/_template.md`)

## Step 1: Write the Skill File

Create `.claude/skills/genres/<category>/<genre_id>.md` using the template:

```markdown
---
genre: <genre_id>
tempo_range: [min, max]
typical_keys: [list]
modal_options: [list]
default_swing: 0.0
typical_drum_pattern: <pattern_name>
preferred_instruments: [list]
avoided_instruments: [list]
typical_chord_progressions:
  - [I, IV, V, I]
characteristic_rhythms: [list]
common_cliches_to_avoid:
  - description
representative_techniques:
  - technique
evaluation_weights:
  structure: 0.20
  melody: 0.25
  harmony: 0.20
  acoustics: 0.15
  groove_pocket: 0.20
default_groove: <groove_name>
default_melody_strategy: <strategy>
---

# <Genre Name> — Genre Skill

## Tempo
## Key Preferences
## Iconic Chord Progressions
## Drum Pattern Family
## Instrumentation
## Section Structure
## Cliches to AVOID
```

**Rules:**
- `genre` field MUST match the filename (without `.md`)
- No living artist names anywhere
- Use academic references only (Author, Year)
- All instruments must exist in `src/yao/constants/instruments.py`
- All drum patterns must exist in `drum_patterns/`

## Step 2: Add the Genre Profile YAML

Create `genre_profiles/<genre_id>.yaml`:

```yaml
# Genre Profile: <Name>
# References:
#   - <Academic reference> (<Author, Year>)

name: <genre_id>

chord_palette:
  - I
  - IV
  - V

progression_n_grams:
  "I,IV": 0.15
  "IV,V": 0.12

seventh_chord_probability: 0.3
secondary_dominant_probability: 0.1
modal_interchange_probability: 0.1

melodic_contour_weights:
  ascending: 0.25
  descending: 0.25
  arch: 0.25
  valley: 0.15
  flat: 0.10

leap_probability: 0.3
blue_note_probability: 0.0

swing_ratio: 0.5
syncopation_density: 0.3

rhythm_template_weights:
  eighth_notes: 0.30
  quarter_notes: 0.25

preferred_instruments:
  - piano

voicing_density_target: 4
bass_motion_style: root_fifth

typical_dynamics_range: [mp, f]
target_spectral_centroid: 0.5
tempo_range: [80, 140]
```

## Step 3: Add a Composition Template

Create `specs/templates/genres/<category>/<template-name>.yaml` with a ready-to-use composition spec.

## Step 4: Verify

```bash
python -c "from yao.constants.genre_profile import get_genre_profile; p = get_genre_profile('<genre_id>'); print(p.name)"
make test-genres
make all-checks
```

## Step 5: Adding a Primary Genre

If this is a **new primary genre** (not a subgenre of an existing one), **stop and ask the user first**. Primary genres are normative decisions.
