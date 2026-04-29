# Supported Instruments

YaO supports 46 instruments across 9 families. Each has a defined MIDI range and General MIDI program number, centralized in `src/yao/constants/instruments.py`.

## Keyboard

| Instrument | Range | MIDI Low–High | GM Program |
|------------|-------|---------------|------------|
| piano | A0–C8 | 21–108 | 0 |
| electric_piano | E1–G7 | 28–103 | 4 |
| harpsichord | F1–F6 | 29–89 | 6 |
| celesta | C4–C8 | 60–108 | 8 |
| organ | C2–C7 | 36–96 | 19 |

## Strings

| Instrument | Range | MIDI Low–High | GM Program |
|------------|-------|---------------|------------|
| violin | G3–G7 | 55–103 | 40 |
| viola | C3–A6 | 48–93 | 41 |
| cello | C2–E5 | 36–76 | 42 |
| contrabass | E1–C4 | 28–60 | 43 |
| harp | C1–G7 | 24–103 | 46 |
| strings_ensemble | E1–G7 | 28–103 | 48 |

## Guitar

| Instrument | Range | MIDI Low–High | GM Program |
|------------|-------|---------------|------------|
| acoustic_guitar_nylon | E2–C6 | 40–84 | 24 |
| acoustic_guitar_steel | E2–C6 | 40–84 | 25 |
| electric_guitar_clean | E2–E6 | 40–88 | 27 |

## Bass

| Instrument | Range | MIDI Low–High | GM Program |
|------------|-------|---------------|------------|
| acoustic_bass | E1–C4 | 28–60 | 32 |
| electric_bass_finger | E1–F4 | 28–65 | 33 |
| electric_bass_pick | E1–F4 | 28–65 | 34 |
| synth_bass | C1–C5 | 24–72 | 38 |

## Brass

| Instrument | Range | MIDI Low–High | GM Program |
|------------|-------|---------------|------------|
| trumpet | G3–A#5 | 55–82 | 56 |
| trombone | E2–C5 | 40–72 | 57 |
| tuba | E1–A#3 | 28–58 | 58 |
| french_horn | A#1–F5 | 34–77 | 60 |

## Woodwind

| Instrument | Range | MIDI Low–High | GM Program |
|------------|-------|---------------|------------|
| oboe | A#3–G6 | 58–91 | 68 |
| clarinet | D3–G6 | 50–91 | 71 |
| flute | C4–C7 | 60–96 | 73 |
| piccolo | D5–C8 | 74–108 | 72 |
| bassoon | A#1–D#5 | 34–75 | 70 |

## Saxophone

| Instrument | Range | MIDI Low–High | GM Program |
|------------|-------|---------------|------------|
| alto_sax | C#3–G#5 | 49–80 | 65 |
| tenor_sax | G#2–D#5 | 44–75 | 66 |
| baritone_sax | C2–A4 | 36–69 | 67 |

## Synth

| Instrument | Range | MIDI Low–High | GM Program |
|------------|-------|---------------|------------|
| synth_lead_square | C1–C8 | 24–108 | 80 |
| synth_lead_saw | C1–C8 | 24–108 | 81 |
| synth_pad_warm | C1–C8 | 24–108 | 89 |

## Percussion (Pitched)

| Instrument | Range | MIDI Low–High | GM Program |
|------------|-------|---------------|------------|
| timpani | E2–A3 | 40–57 | 47 |
| vibraphone | F3–F6 | 53–89 | 11 |
| marimba | A2–C7 | 45–96 | 12 |
| xylophone | F4–C8 | 65–108 | 13 |
| glockenspiel | C5–C8 | 72–108 | 9 |
