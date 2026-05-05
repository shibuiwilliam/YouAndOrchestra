# Design: Form Library + Diversity Sources

## Problem

Mode collapse: every piece sounds structurally similar regardless of intent. Without a library of forms, the system defaults to the same AABA or verse-chorus structure.

## Solution

### Form Library (20 forms)

SongForm + FormSection frozen dataclasses with varying lengths (12–68 bars):

| Form | Bars | Genre Context |
|------|------|--------------|
| aaba_32bar | 32 | Jazz standards |
| verse_chorus | 32 | Pop, rock |
| verse_chorus_bridge | 40 | Pop, J-pop |
| rondo | 40 | Classical |
| through_composed | 32 | Art music |
| blues_12bar | 12 | Blues, jazz |
| sonata_allegro | 68 | Classical |
| binary | 16 | Baroque |
| ternary | 24 | Classical |
| strophic | 32 | Folk |
| j_pop | 48 | J-pop |
| game_bgm | 16 | Game music (loopable) |
| ambient | 32 | Ambient, drone |
| edm_build_drop | 32 | Electronic |
| hip_hop_verse_hook | 32 | Hip-hop |
| progressive | 64 | Prog rock |
| theme_variation | 40 | Classical |
| call_response | 16 | World music |
| minimalist | 32 | Minimal music |
| free_form | 24 | Jazz, experimental |

### Melodic Generation Strategies (8)

Each strategy produces distinct melodic character, verified by tests:

| Strategy | Character |
|----------|-----------|
| `contour_based` | Shape-driven (arch, ascending, descending) |
| `motif_development` | Variation on seed motif |
| `linear_voice` | Stepwise voice leading |
| `arpeggiated` | Chord-tone based |
| `scalar_runs` | Scale passages |
| `call_response` | Question-answer phrasing |
| `pedal_tone` | Sustained pitch with moving harmony |
| `hocketing` | Alternating between voices |

## Files

- `src/yao/constants/forms.py` — SongForm, FormSection, FORM_LIBRARY
- `src/yao/generators/melodic_strategies.py` — MelodicGenerationStrategy enum, generate_melody_pitches()
- `src/yao/generators/plan/form_planner.py` — FormPlanner
