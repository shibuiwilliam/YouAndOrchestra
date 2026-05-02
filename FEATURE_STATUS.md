# YaO Feature Status

> Last verified: 2026-04-30 by automated check (`make feature-status`)
> This file is the **single source of truth** for what YaO can do.
> README.md, CLAUDE.md, and PROJECT.md link here instead of restating capabilities.

## Status Legend

- ✅ **Stable** — Working with tests, safe to depend on
- 🟢 **Working but limited** — Core works, check edge cases noted
- 🟡 **Partial** — Some paths work, read implementation before depending
- ⚪ **Designed, not started** — Specified but not yet built
- 🔴 **Identified gap** — Known need, no implementation

---

## Spec / Input

| Feature | Status | Tests | Notes |
|---|---|---|---|
| YAML spec parsing (Pydantic v1) | ✅ | tests/unit/test_schema.py | CompositionSpec, SectionSpec, InstrumentSpec; all 4 templates load |
| YAML spec parsing (Pydantic v2) | ✅ | tests/unit/schema/test_composition_v2.py | 22 Pydantic models, 11 sections |
| Natural language → spec (`yao conduct`) | 🟢 | tests/unit/test_conductor.py | English keyword dict; explicit key regex ("in D minor"); no Japanese |
| trajectory.yaml multi-dim coupling | ✅ | tests/scenarios/test_trajectory_compliance.py | All 5 dims defined; GenerationParams derived per bar; both generators respond to tension (velocity+leaps), density (rhythm), register_height (octave) |
| constraints with scoping | ✅ | tests/unit/test_constraints.py | must / must_not / prefer / avoid with global, section, instrument, bars scopes |
| intent.md | 🟡 | tests/unit/schema/test_intent.py | IntentSpec exists; not linked to auto-evaluation |
| references.yaml | 🟡 | — | Schema exists; matcher not connected |
| negative-space.yaml | 🟡 | — | Schema exists; reflection mechanism incomplete |
| production.yaml | 🟡 | — | Schema exists; mix chain not implemented |

## Generation

| Feature | Status | Tests | Notes |
|---|---|---|---|
| rule_based generator | ✅ | tests/unit/test_generator.py | Deterministic; trajectory: tension → velocity only |
| stochastic generator | ✅ | tests/unit/test_stochastic.py | seed / temperature / contour; trajectory: tension → pitch+leaps, density → rhythm, register_height → octave |
| Generator registry | ✅ | tests/unit/test_generator.py | @register_generator decorator |
| drum_patterner | ✅ | tests/unit/generators/test_drum_patterner.py | 8 genre patterns in drum_patterns/; swing, ghost notes, trajectory density |
| counter_melody | ✅ | tests/unit/generators/test_counter_melody.py | Species counterpoint; contrary motion preferred; density_factor control |
| markov generator | ⚪ | — | Designed, not started |
| constraint solver generator | ⚪ | — | Designed, not started |

## IR (Intermediate Representation)

| Feature | Status | Tests | Notes |
|---|---|---|---|
| ScoreIR (Note, Part, Section) | ✅ | tests/unit/test_ir.py | Frozen dataclasses |
| Motif IR | ✅ | tests/unit/test_motif.py | Motif, invert, retrograde, transpose |
| Harmony IR | ✅ | tests/unit/test_harmony.py | diatonic_quality, chord functions |
| Voicing IR | ✅ | tests/unit/test_voicing.py | Voice-crossing detection |
| Timing IR | ✅ | tests/unit/test_ir.py | bars_to_beats, beats_to_bars |
| Notation IR | ✅ | tests/unit/test_ir.py | note_name_to_midi, midi_to_note_name |
| Trajectory IR (5-dim) | ✅ | tests/unit/test_trajectory_ir.py | MultiDimensionalTrajectory with TrajectoryCurve; bezier/stepped/linear |
| DrumPattern IR | ✅ | tests/unit/ir/test_drum.py | DrumHit, DrumPattern, KitPiece, GM_DRUM_MAP; 15 kit pieces mapped |

## Rendering

| Feature | Status | Tests | Notes |
|---|---|---|---|
| MIDI writer + per-instrument stems | ✅ | tests/unit/test_render.py, test_stem_writer.py | |
| Audio renderer (FluidSynth) | ✅ | tests/unit/test_render.py | Optional dependency; requires SoundFont |
| MIDI reader | ✅ | tests/unit/test_midi_reader.py | MIDI → ScoreIR round-trip |
| Iteration management | ✅ | tests/unit/test_iteration.py | v001/v002/... auto-versioning |
| MusicXML writer | ⚪ | — | Designed, not started |
| LilyPond / PDF writer | ⚪ | — | Designed, not started |

## Critique / Verification

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Music lint | ✅ | tests/unit/test_verify.py | Parallel fifths, voice leading |
| Score analyzer | ✅ | tests/unit/test_verify.py | Structure, melody, harmony analysis |
| Evaluator (10 metrics, 3 dims) | ✅ | tests/unit/test_evaluator.py | MetricGoal-based; structure / melody / harmony |
| MetricGoal type system | ✅ | tests/unit/verify/test_metric_goal.py | 7 goal types (AT_LEAST, BETWEEN, etc.) |
| Score diff | ✅ | tests/unit/test_diff.py | Modified notes tracking |
| Constraint checker | ✅ | tests/unit/test_constraints.py | Range / voice constraints |
| Critique rules (structured) | ✅ | tests/unit/verify/test_critique_rules.py | 15 rules across 6 roles (structural 3, harmonic 3, melodic 3, rhythmic 2, arrangement 2, emotional 2) |
| Critique registry + Finding types | ✅ | tests/unit/verify/test_critique.py | CritiqueRule base, Finding dataclass, CritiqueRegistry |
| RecoverableDecision logging | ✅ | tests/unit/verify/test_recoverable.py | 9 registered codes; all known silent fallbacks wrapped; check_silent_fallback.py for detection |

## Conductor

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Generate-evaluate-adapt loop | ✅ | tests/unit/test_conductor.py | compose_from_description, compose_from_spec |
| Section-level regeneration | ✅ | tests/unit/test_conductor.py | regenerate_section via v2 pipeline |
| Critic integration in loop | ✅ | tests/unit/test_conductor.py | CRITIQUE_RULES.run_all() called; findings → adaptations |
| Feedback adaptations (evaluator) | ✅ | tests/unit/test_feedback.py | Temperature, strategy, dynamics adaptations |
| Feedback adaptations (critic findings) | ✅ | tests/unit/test_feedback.py | section_monotony, climax_absence, harmonic_monotony, cliche_progression, intent_divergence |
| SpecCompiler (NL → spec) | ✅ | tests/unit/sketch/test_compiler.py | Extracted from Conductor; mood → key, pace → tempo, explicit key regex |
| ConductorResult with critic_findings | ✅ | tests/unit/test_conductor.py | Findings visible in summary() |

## CLI

| Feature | Status | Tests | Notes |
|---|---|---|---|
| yao compose | ✅ | — | Single-pass generation |
| yao conduct | ✅ | tests/unit/test_conductor.py | NL description or spec path |
| yao render | ✅ | — | MIDI → WAV |
| yao validate | ✅ | — | Spec validation and summary |
| yao evaluate | ✅ | — | Re-evaluate latest iteration |
| yao diff | ✅ | — | Compare two seeds |
| yao explain | ✅ | — | Provenance query |
| yao new-project | ✅ | — | Project skeleton |
| yao regenerate-section | ✅ | — | Section regeneration |
| yao preview | ✅ | tests/unit/cli/test_preview.py | In-memory generation + FluidSynth synthesis + sounddevice playback; no file output |
| yao watch | ✅ | tests/unit/cli/test_watch.py | File-watch via watchdog + auto-regenerate + auto-play; 500ms debounce |

## Skills / Knowledge

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Genre Skills (8) | ✅ | tests/unit/skills/test_genre_skills.py | cinematic, lofi_hiphop, j_pop, neoclassical, ambient, jazz_ballad, game_8bit_chiptune, acoustic_folk |
| voice-leading theory Skill | 🟢 | — | .claude/skills/theory/voice-leading.md |
| piano instrument Skill | 🟢 | — | .claude/skills/instruments/piano.md |
| tension-resolution psychology Skill | 🟢 | — | .claude/skills/psychology/tension-resolution.md |

## Subagents / Commands

| Feature | Status | Tests | Notes |
|---|---|---|---|
| 7 Subagent definitions | ✅ | — | .claude/agents/ (composer, critic, harmony-theorist, mix-engineer, orchestrator, producer, rhythm-architect) |
| 7 slash commands | ✅ | — | .claude/commands/ (compose, critique, sketch, regenerate-section, explain, render, arrange) |

## Tests / QA

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Unit tests | ✅ | tests/unit/ (39 files) | ~500 tests |
| Integration tests | ✅ | tests/integration/ (3 files) | ~15 tests |
| Scenario tests | ✅ | tests/scenarios/ (2 files) | ~16 tests (trajectory compliance) |
| Music constraint tests | ✅ | tests/music_constraints/ | 7 parameterized tests |
| Golden MIDI tests | ✅ | tests/golden/ | 6 baselines (3 specs x 2 realizers); comparison.py; regenerate_goldens.py |
| Architecture lint | ✅ | — | tools/architecture_lint.py; `make arch-lint` |
| Feature status check | ✅ | — | tools/feature_status_check.py; `make feature-status` |

## Infrastructure

| Feature | Status | Tests | Notes |
|---|---|---|---|
| Pre-commit hooks | ✅ | — | trailing-whitespace, ruff, ruff-format, mypy, arch-lint |
| CI (GitHub Actions) | ✅ | — | lint + type + arch-lint + tests + golden |
| Provenance logging | ✅ | — | Append-only, queryable, JSON persistence |
| Constants (38 instruments, 14 scales, 14 chords) | ✅ | — | src/yao/constants/ |

## Not Yet Implemented

| Feature | Status | Notes |
|---|---|---|
| Drum pattern generator | ✅ | ★1 complete; 8 genre patterns, swing, ghost notes, trajectory density |
| Counter-melody generator | ✅ | ★2 complete; consonance + contrary motion + parallel avoidance |
| Trajectory multi-dim coupling | ✅ | ★3 complete; both generators respond via GenerationParams |
| yao preview / yao watch | ✅ | ★6 complete |
| 7 additional genre Skills | ✅ | ★7 complete |
| Perception layer | ⚪ | Phase 3 |
| Arrangement engine | ⚪ | Phase 2 |
| Mix chain (EQ, comp, reverb) | ⚪ | |
| MusicXML / LilyPond output | ⚪ | |
| DAW MCP integration | ⚪ | |
| Live improvisation mode | ⚪ | |
