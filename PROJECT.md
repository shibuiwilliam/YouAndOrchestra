# You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

---

## 0. Project Essence

**You and Orchestra (YaO)** is an agentic music production environment built on Claude Code. Unlike a typical "AI music generator," YaO does not emit music from a single black box. Instead, **a team of role-specialized AI agents (the Orchestra) is conducted by a human (You)**.

All YaO design is subordinated to a single proposition:

> **Music production is not a one-time intuitive act; it is reproducible, improvable creative engineering.**

For this reason, YaO treats music — before it is audio — as **code, specifications, tests, diffs, and provenance**. We call this the **Music-as-Code** philosophy.

### 0.1 What Changed in Version 2.0

Version 1.0 established the foundation: a 7-layer architecture, 38 instruments, rule-based and stochastic generators, a Conductor feedback loop, full provenance, and 226 tests. It produced high-quality output for classical, chamber, cinematic, and simple BGM contexts.

Version 2.0 extends this foundation to make YaO a **universal, genre-diverse music production environment** supporting at least 30 primary genres across rock, pop, jazz, hip-hop, electronic, R&B, funk, Latin, world, metal, ambient, soundtrack, and beyond. The core philosophy is unchanged. The expansion is purely **additive** — every Version 1.0 capability remains intact and unchanged in behavior.

The five major additions in v2.0 are:

1. **Drum and Percussion System** (GM Channel 10) — the missing foundation for modern music
2. **Genre as a First-Class Concept** — schema, profiles, and pipeline-wide genre awareness
3. **Groove Engine** — micro-timing, swing, push/pull, and genre-specific feel
4. **Extended Harmonic and Melodic Vocabulary** — altered dominants, quartal, power chords, idiomatic phrases
5. **Genre-Aware Evaluation and Iteration** — Conductor adapts based on genre-specific quality criteria

### 0.2 The v2.x Quality Program (delivered 2026-07-26)

> A 19-increment program re-centered YaO on musical craft (see `PROJECT_IMPROVEMENT.md`,
> `IMPLEMENTATION_PLAN.md`, and the ground-truth ledger `docs/STATUS.md`). The core finding: the strongest
> generative "brain" (the plan-consuming realizer) was built but unplugged while a random-walk generator was the
> default. It is now the default for **every** command.

What the default pipeline now produces, and how it is judged:

- **States a theme and develops it** — cross-section thematic recall (`generation.thematic_development`), so
  return sections restate the theme instead of wandering.
- **Voice-led, density-aware arrangement** — melody + harmony + bass; harmony connects with minimal voice
  motion and no unexempted parallels; busier sections get busier accompaniment (section contrast).
- **Walking bass** for genres whose profile sets `bass_motion_style: walking` (jazz, blues, baroque).
- **Authentic V–I cadences** at the piece end (harmony planner) + descriptive half-cadence annotation;
  harmonic-minor **major-V** (leading tone) and **mode-correct** `diatonic_quality`.
- **Real, calibrated evaluation** — the aesthetic dimension is wired (was a placeholder); `motif_development_index`
  and `voice_leading_smoothness` are calibrated so an in-key random walk *fails* them; the directional metric
  bug is fixed; the loop keeps the best iteration and never logs a no-op adaptation as applied.
- **Genre-aware weighting** — `percussion_centric` (beat-driven genres), `static_texture` (ambient omits the
  contrast penalty).

The deprecated legacy note realizers were deleted; the legacy generators are `.. deprecated::` (test fixtures
only). Quality on representative specs rose from ~6.6 to ~8.0 and, more importantly, output is *musically
coherent* in ways surface statistics can't fake.

**Status note:** §10 (Perception Substitute Layer) and the Layer-7 learning claims are *designed, not
operational* — see the correction in §10 and `docs/STATUS.md`.

---

## 1. Metaphor: You and Orchestra

Every YaO concept maps to an orchestra metaphor. Internalizing this mapping is the shortest path to using YaO correctly.

| YaO Component | Orchestra Metaphor | Implementation |
|---|---|---|
| **You** | Conductor | The human project owner |
| **Score** | Sheet music | YAML specifications under `specs/` |
| **Orchestra Members** | Players | Subagents (Composer, Critic, Theorist, ...) |
| **Concertmaster** | Section leader | Producer Subagent |
| **Rehearsal** | Rehearsal | Generate → evaluate → adapt loop |
| **Library** | Music library | Reference works under `references/` |
| **Performance** | Concert | Rendered final audio |
| **Recording** | Recording | Outputs under `outputs/` |
| **Critic** | Reviewer | Adversarial Critic Subagent |
| **Repertoire** *(v2.0)* | Genre catalog | `.claude/skills/genres/` profile library |
| **Percussion section** *(v2.0)* | Drum kit | New `DrumPart` and Channel 10 |
| **Feel** *(v2.0)* | Time / groove | Groove Engine with micro-timing |

The Conductor does not write every note. Their job is to **clarify intent, direct the players, judge during rehearsal, and ensure the quality of the performance**. YaO brings this division of labor to AI.

---

## 2. Design Principles

All implementation decisions are made against five invariant principles. These are reproduced in CLAUDE.md and used as the agent's judgment criteria.

### Principle 1: The agent is an environment, not a composer
YaO does not aspire to be an "AI that writes songs." It aspires to be an "environment that makes the human composer 10× faster and more reproducible." Full automation is rejected; human creative judgment is accelerated and extended.

### Principle 2: Every decision must be explainable
Every generated note, chord, instrument assignment, and arrangement decision is accompanied by a recorded reason. These are persisted as a Provenance log and remain queryable, reviewable, and modifiable.

### Principle 3: Constraints liberate; they do not cage
Explicit specifications (YAML), reference libraries, negative space, and genre profiles act as scaffolding for creativity, not as restrictions. Unbounded freedom produces paralysis.

### Principle 4: Time-axis design precedes note design
A piece is designed first as **trajectories on the time axis** (tension, density, valence, predictability curves), and only afterwards are notes filled in. This produces structurally meaningful music.

### Principle 5: The human ear is the final truth
However precise automated evaluation becomes, the human listening experience is the ultimate judge. The agent **supports rather than replaces** human judgment.

### 2.1 How v2.0 Honors These Principles

The genre diversity expansion does **not** dilute the principles — it deepens them:

- **Principle 1**: Genre profiles describe environments (typical instruments, typical patterns), not authored compositions.
- **Principle 2**: Genre-driven decisions (chord palette choice, swing ratio, drum pattern) are recorded with explicit genre references in provenance.
- **Principle 3**: Genre profiles constrain choice in productive ways — they liberate the user from inventing every parameter from scratch.
- **Principle 4**: Genre profiles include typical trajectory shapes (e.g., EDM build-and-drop arcs, jazz solo-trading dynamics) informing Phase 2 design.
- **Principle 5**: Genre-aware evaluators flag issues, but the human still makes the final call on whether output is "right."

---

## 3. Architecture: The 7-Layer Model

YaO is structured as seven strictly separated layers. Each layer has an independent input/output contract and is exchangeable and testable in isolation.

```
+-----------------------------------------------------+
| Layer 7: Reflection & Learning                      |
|   Learning from history, user preference updates    |
+-----------------------------------------------------+
| Layer 6: Verification & Critique                    |
|   Structural / harmonic / rhythmic / acoustic eval  |
|   Adversarial critique                              |
|   (v2.0) Genre-aware evaluators                     |
+-----------------------------------------------------+
| Layer 5: Rendering                                  |
|   MIDI -> Audio, Score PDF, live code               |
|   (v2.0) GM Channel 10 output, CC automation        |
+-----------------------------------------------------+
| Layer 4: Perception Substitute                      |
|   Aesthetic judgment substitutes                    |
|   Reference matching, psychology mapping            |
|   Style vectors (v2.0: now implemented)             |
+-----------------------------------------------------+
| Layer 3: Intermediate Representation (IR)           |
|   ScoreIR, Harmony, Motif, Voicing                  |
|   (v2.0) DrumPart, ModulationCurve, PhraseTemplate  |
+-----------------------------------------------------+
| Layer 2: Generation Strategy                        |
|   Pluggable: rule-based, stochastic                 |
|   (v2.0) drum_generator, markov, ai_bridge          |
+-----------------------------------------------------+
| Layer 1: Specification                              |
|   YAML specs, dialogue, sketch input                |
|   (v2.0) GenreSpec, GrooveSpec, drum_kit, lyrics    |
+-----------------------------------------------------+
| Layer 0: Constants                                  |
|   Instrument ranges, MIDI maps, scales, chords      |
|   (v2.0) Drum maps, Genre profiles, Phrase library, |
|          Drum patterns, Groove templates            |
+-----------------------------------------------------+
```

Dependency direction is strictly upward: lower layers do not know about higher layers. Adding new modules first determines which layer they belong to, then they are placed in the corresponding directory. The AST-based `architecture-lint` enforces this boundary at CI time.

**Critical principle**: All v2.0 additions are **additions to existing layers** — none requires breaking layer boundaries. Drum support adds to Layers 0, 1, 3, and 5. Genre support adds to Layers 0, 1, 2, 6. Groove Engine adds to Layers 0, 1, 3, and 5. Perception Substitute Layer (4) is populated for the first time but its position in the architecture was already designed.

---

## 4. Genre as a First-Class Concept

This section is the centerpiece of v2.0. It explains why and how genre becomes a primary citizen of the schema, the generators, and the evaluators.

### 4.1 Why Genre Must Be First-Class

In v1.0, genre was implicit — inferred from instrument choices, mood keywords, or tempo. This worked for classical-adjacent music but failed for genre-specific music for three reasons:

1. **Different genres demand different chord vocabularies.** A "happy" jazz piece uses ii-V-I with altered tensions; a "happy" rock piece uses I-IV-V power chords; a "happy" EDM piece uses i-VI-VII modal vamps. Without knowing the genre, generators cannot make these choices well.

2. **Different genres demand different rhythmic feel.** "120 BPM 4/4" means radically different things in EDM (four-on-the-floor, sidechain pump), jazz (swung 8ths, ride pulse), and hip-hop (boom-bap or trap subdivision). The rhythm IR alone cannot communicate this.

3. **Different genres demand different evaluation criteria.** A jazz piece with no chord-tone targeting fails as jazz but might pass generic melody evaluation. An ambient piece with high section contrast fails as ambient. Generic evaluation flatters mediocre genre output.

### 4.2 The Genre Hierarchy

YaO defines a two-level genre hierarchy: **primary** (broad category) and **subgenre** (specific style). Optional **era** and **influences** fields allow finer specification.

The initial supported primary genres (v2.0 launch):

| Primary | Example Subgenres |
|---|---|
| **classical** | baroque, classical_era, romantic, modern, minimalist, neoclassical |
| **jazz** | dixieland, swing, bebop, cool, modal, fusion, smooth, free, latin_jazz |
| **rock** | classic, hard, alternative, indie, progressive, metal, punk, post_rock |
| **pop** | mainstream, synth, indie, j_pop, k_pop, dance |
| **hiphop** | boom_bap, trap, lofi, conscious, drill, phonk |
| **electronic** | house, techno, trance, ambient, idm, drum_and_bass, dubstep, synthwave, garage |
| **rnb** | classic, neo_soul, contemporary |
| **funk** | classic, p_funk, g_funk, electro_funk |
| **latin** | bossa_nova, samba, salsa, tango, reggaeton, cumbia, merengue |
| **world** | celtic, indian_classical, gamelan, african, middle_eastern, flamenco, klezmer |
| **country** | traditional, outlaw, bluegrass, modern |
| **blues** | delta, chicago, texas, british |
| **folk** | traditional, modern, singer_songwriter |
| **soundtrack** | cinematic, game_bgm, documentary, anime |
| **ambient** | dark, drone, new_age, soundscape |

This list expands based on community contributions. The hierarchy structure is designed to be extensible.

### 4.3 The GenreSpec Schema

```yaml
# composition.yaml — genre section
genre:
  primary: jazz                # required, one of the primary genres
  subgenre: bebop              # optional, must be a subgenre of primary
  era: 1940s                   # optional, free-form string
  influences:                  # optional, additional stylistic pulls
    - genre: blues
      weight: 0.3
    - genre: latin
      weight: 0.15
  fusion: false                # true if this is an intentional cross-genre blend
```

The `GenreSpec` Pydantic model enforces the primary/subgenre hierarchy and rejects invalid combinations at validation time. If `subgenre` is provided, it must belong to `primary`. If `fusion: true`, weighted influences must sum to at least 0.3 (otherwise it's not genuinely a fusion).

### 4.4 Genre Profile Library

For each primary genre and subgenre, YaO maintains a **GenreProfile** — a structured description of typical features.

```python
@dataclass(frozen=True)
class GenreProfile:
    name: str
    full_id: str                       # e.g., "jazz.bebop"
    typical_tempo_range: tuple[int, int]
    typical_time_signatures: list[str]
    typical_keys: list[str]
    preferred_scales: list[str]
    typical_chord_palette: list[str]   # Roman numeral
    typical_chord_extensions: list[Extension]
    typical_alterations: list[Alteration]
    preferred_voicing: VoicingStyle
    swing_ratio: float                 # 0.5 = straight, 0.67 = triplet swing
    typical_instrumentation: list[str]
    drum_patterns: list[str]           # references into drum_patterns library
    structure_templates: list[str]     # e.g., AABA_32, 12_bar_blues
    velocity_profile: dict[str, int]   # per-role default dynamics
    micro_timing: MicroTimingProfile
    avoid: list[str]                   # antipatterns this genre avoids
    references: list[str]              # abstract aesthetic descriptors
    default_constraints: list[ConstraintRule]
    evaluator: str                     # which Evaluator class to use
```

Profiles live in `src/yao/constants/genre_profiles.py` (machine-readable) and `.claude/skills/genres/<id>.md` (human-readable, for Subagents).

The Skill markdown for each genre describes a brief historical and cultural overview, typical instrumentation, tempo and time signature ranges, harmonic vocabulary (typical progressions, chord types, reharmonization techniques), melodic vocabulary (preferred scales, phrasing characteristics), rhythmic vocabulary (swing, groove, drum patterns), typical structure templates, genre-specific evaluation criteria, antipatterns to avoid, abstract aesthetic references (never named living artists), and a reference set of constraints.

### 4.5 Genre-Aware Generation

All generators in Layer 2 become **genre-aware**:

```python
class GeneratorBase:
    def generate(self, spec: CompositionSpec) -> tuple[ScoreIR, ProvenanceLog]:
        profile = (
            GENRE_PROFILES[spec.genre.full_id()]
            if spec.genre else DEFAULT_PROFILE
        )
        # Profile shapes:
        # - chord palette and extensions
        # - melodic scale selection
        # - rhythm pattern choice
        # - voicing style
        # - velocity defaults
        # - micro-timing application
        ...
```

Provenance records the genre profile reference used for each decision:

```json
{
  "decision": "chord_palette_selection",
  "value": ["ii", "V7", "I", "VI7"],
  "reason": "Selected from typical_chord_palette of profile jazz.bebop",
  "profile_id": "jazz.bebop",
  "profile_version": "2.0"
}
```

### 4.6 Genre Fusion

When `fusion: true`, the Conductor builds a **blended profile** from the primary and weighted influences:

```python
def build_fusion_profile(spec: GenreSpec) -> GenreProfile:
    base = GENRE_PROFILES[f"{spec.primary}.{spec.subgenre}"]
    blended = base.copy()
    for influence in spec.influences:
        influence_profile = GENRE_PROFILES[influence.genre.full_id()]
        blended = blend(blended, influence_profile, weight=influence.weight)
    return blended
```

Blending rules are documented per attribute (e.g., chord palettes are unioned with weights; drum patterns are chosen probabilistically by weight; swing_ratio is interpolated).

### 4.7 Adding a New Genre

The process is documented and partly automated. A musician contributor without Python knowledge can complete steps 1, 2, 5 below; only step 4 requires Python.

1. Write `.claude/skills/genres/<id>.md` following the template
2. Add an entry to `src/yao/constants/genre_profiles.py`
3. (Optional) Add genre-specific patterns to drum/phrase libraries
4. (Optional) Add a genre-specific evaluator subclass
5. Add at least one template under `specs/templates/genres/<primary>/`
6. Add scenario tests under `tests/scenarios/test_genre_<id>.py`

---

## 5. Drum and Percussion System

The most consequential addition in v2.0. v1.0 had **no drum kit**, only pitched percussion (timpani, marimba, etc.). This made the majority of modern genres effectively impossible. v2.0 introduces a full drum and percussion system.

### 5.1 Drum Map (GM Channel 10)

YaO supports the General MIDI percussion map on Channel 10. All standard drum and percussion pieces are exposed as the `DrumPiece` enum (MIDI notes 27–87):

```
Kick variants:        kick (36), kick_soft (35)
Snare variants:       snare (38), snare_rim (37), snare_electric (40), clap (39)
Hi-hat:               hi_hat_closed (42), hi_hat_pedal (44), hi_hat_open (46)
Toms:                 tom_low_floor (41), tom_floor (43), tom_low (45),
                      tom_low_mid (47), tom_mid (48), tom_high (50)
Cymbals:              crash_1 (49), crash_2 (57), ride (51), ride_bell (53),
                      splash (55), china (52)
Auxiliary:            cowbell (56), tambourine (54), woodblock (76, 77),
                      triangle (80, 81), guiro (73, 74), claves (75)
Latin percussion:     bongo_high (60), bongo_low (61), conga_high_mute (62),
                      conga_high_open (63), conga_low (64), timbale_high (65),
                      timbale_low (66), agogo_high (67), agogo_low (68),
                      cabasa (69), maracas (70), whistle_short (71),
                      whistle_long (72)
```

### 5.2 DrumPart IR

A drum part is a special kind of `Part` using `DrumNote` (no pitch class concept; the `piece` enum determines the sound):

```python
@dataclass(frozen=True)
class DrumNote:
    piece: DrumPiece
    onset_tick: Tick
    velocity: Velocity
    duration_tick: Tick = 60   # short fixed value (percussion convention)

@dataclass(frozen=True)
class DrumPart(Part):
    midi_channel: int = 9      # 0-indexed Channel 10
    notes: tuple[DrumNote, ...] = ()
```

A composition can have multiple `DrumPart` instances (e.g., a "main kit" plus a "percussion overlay" for Latin music).

### 5.3 Drum Pattern Library

YaO ships with 40+ drum patterns covering the principal feels of supported genres. Each pattern is a `DrumPatternSpec`:

```python
@dataclass(frozen=True)
class DrumPatternSpec:
    name: str
    time_signature: str
    grid: GridResolution                # 8ths, 16ths, triplets
    kick_pattern: list[int]             # 1 = hit, 0 = rest
    snare_pattern: list[int]
    hat_pattern: list[int]
    ride_pattern: list[int] | None = None
    extra: dict[DrumPiece, list[int]] = field(default_factory=dict)
    velocity_profile: dict[str, int]
    humanize_ms: int = 0
    velocity_humanize: int = 0
    swing_ratio: float = 0.5
    genre_tags: list[str] = field(default_factory=list)
```

Examples included at launch:

| Pattern Name | Genres |
|---|---|
| `rock_basic` | rock, classic_rock |
| `rock_halftime` | alternative, post_rock |
| `metal_double_kick` | metal |
| `hiphop_boom_bap` | hiphop_boom_bap, lofi |
| `hiphop_trap_triplet` | trap |
| `reggae_one_drop` | reggae, ska |
| `reggae_steppers` | dub, reggae |
| `edm_four_on_floor` | house, techno, trance |
| `edm_dnb_breakbeat` | drum_and_bass |
| `dubstep_halftime_140` | dubstep |
| `jazz_swing_ride` | jazz_swing, jazz_bebop |
| `jazz_brush_ballad` | jazz_ballad |
| `bossa_nova` | bossa_nova, samba |
| `samba_partido_alto` | samba |
| `funk_16th` | funk, p_funk |
| `funk_purdie_shuffle` | funk, neo_soul |
| `blues_shuffle_12_8` | blues |
| `country_train_beat` | country |
| `latin_clave_son_2_3` | salsa, latin_jazz |
| `latin_clave_son_3_2` | salsa, latin_jazz |
| `latin_montuno` | salsa |
| `disco_basic` | disco, pop_dance |
| `synthwave_gated` | synthwave, retro_pop |

Each pattern can be **modified at generation time** (humanization, velocity shaping, swing ratio adjustment, fill insertion at section boundaries).

### 5.4 Drum Generator (Layer 2)

A dedicated drum generator is registered in the generator registry:

```python
@register_generator("drum_pattern")
class DrumGenerator(GeneratorBase):
    """Generates drum parts based on genre profile and section trajectory."""

    def generate(self, spec: CompositionSpec,
                 section: Section) -> tuple[DrumPart, ProvenanceLog]:
        profile = resolve_genre_profile(spec)
        pattern_name = self._select_pattern(profile, section, spec.trajectory)
        pattern = DRUM_PATTERNS[pattern_name]
        notes = self._instantiate_pattern(pattern, section)
        notes = self._apply_humanization(notes, pattern, spec.groove)
        notes = self._insert_fills(notes, section, profile)
        notes = self._apply_section_dynamics(notes, section, spec.trajectory)
        return DrumPart(...), provenance
```

### 5.5 Fills, Breakdowns, and Drops

Section transitions are key musical moments. The drum generator detects them and inserts fills at the end of a section (last 1–2 bars, pattern-specific), breakdowns (density drop in build-up sections — kick removal, ride only), and drops (full kit explosion at chorus or EDM drop, all instruments rejoin). These follow the trajectory curves: tension peaks coincide with full-kit playing; tension valleys coincide with breakdowns.

### 5.6 Latin and World Percussion

Latin percussion (bongo, conga, timbale, agogo, cabasa, maracas, claves) and world percussion are first-class. The same `DrumPart` IR supports them via the `extra` field in `DrumPatternSpec`. Clave patterns (2-3, 3-2) are encoded for salsa and Latin jazz.

---

## 6. Groove Engine

A separate engine for **micro-timing** — the small deviations from the rigid grid that give music its feel.

### 6.1 The Groove Spec

```yaml
# trajectory.yaml or dedicated groove.yaml
groove:
  swing_ratio: 0.66                    # 0.5 = straight, 0.67 = triplet swing
  laid_back_ms:                        # per-instrument timing offset
    snare: 8                           # snare slightly behind
    bass: 0                            # bass on the grid
    melody: -3                         # melody slightly ahead (pushing)
  humanize:
    timing_jitter_ms: 6                # Gaussian SD
    velocity_jitter: 8
  push_pull:
    phrase_end_slowdown: 0.04          # 4% slowdown at phrase ends
  groove_template: "boom_bap"          # named profile, optional
```

### 6.2 Micro-Timing Profiles

Genre-specific profiles describe typical micro-timing patterns:

```python
MICRO_TIMING_LIBRARY["jazz_swing"] = MicroTimingProfile(
    swing_ratio=0.66,
    rules=[
        Rule(instrument="snare", beat_position=1.0, offset_ms=+8),
        Rule(instrument="snare", beat_position=3.0, offset_ms=+6),
        Rule(instrument="bass", beat_position="any", offset_ms=-3),
        Rule(instrument=None, beat_position="off_8ths",
             offset_ms=+25, velocity_delta=-10),
    ],
)

MICRO_TIMING_LIBRARY["boom_bap_hiphop"] = MicroTimingProfile(
    swing_ratio=0.55,                  # slight swing
    rules=[
        Rule(instrument="snare", beat_position=1.0, offset_ms=+12),
        Rule(instrument="hi_hat", beat_position="any", offset_ms=+3),
    ],
    velocity_humanize=15,
)

MICRO_TIMING_LIBRARY["edm_quantized"] = MicroTimingProfile(
    swing_ratio=0.5,                   # strictly straight
    rules=[],                          # rigid grid
    velocity_humanize=0,
)
```

### 6.3 Application Pipeline

Generators produce notes on the quantized grid. The Groove Engine is applied **at render time, just before MIDI write-out**:

```
Generation -> Grid-aligned Notes -> Groove Engine -> Micro-timed Notes -> MIDI
```

Provenance records both the pre-groove and post-groove tick of each note. This allows reproducible re-application of different grooves to the same underlying structure.

---

## 7. Extended Harmonic and Melodic Vocabulary

v2.0 expands the harmonic and melodic palette to support genres that v1.0's classical-leaning vocabulary could not serve.

### 7.1 ChordSpec Extensions

```python
@dataclass(frozen=True)
class ChordSpec:
    root: int                              # MIDI pitch class
    quality: ChordQuality                  # maj, min, dom7, dim, aug
    extensions: list[Extension] = []       # 9, 11, 13
    alterations: list[Alteration] = []     # b5, #5, b9, #9, #11, b13, sus2, sus4, add9
    bass: int | None = None                # slash chord support
    voicing_hint: VoicingStyle | None = None
```

### 7.2 Voicing Styles

```python
class VoicingStyle(Enum):
    CLOSED = "closed"                      # densely packed
    OPEN = "open"                          # spread across octaves
    DROP_2 = "drop2"                       # jazz piano tradition
    DROP_3 = "drop3"
    QUARTAL = "quartal"                    # stacked fourths (modal jazz)
    POWER = "power"                        # root + fifth (rock, metal)
    SHELL = "shell"                        # root + 3 + 7 (jazz comping)
    ROOTLESS = "rootless"                  # 3 + 5 + 7 + 9 (piano trio)
    CLUSTER = "cluster"                    # stacked seconds (contemporary)
    SPREAD = "spread"                      # wide spacing across registers
```

Each voicing has a realization function: `realize(chord_spec, voicing, target_range)` → `list[int]` (MIDI pitches).

### 7.3 Genre-Driven Chord Choice

The Harmony Theorist Subagent uses genre profile to constrain choices. Examples in practice:

| Genre | Typical Output for "V7" |
|---|---|
| `classical.baroque` | Plain V7 in closed voicing |
| `jazz.bebop` | V7(b9, #11) in drop-2 voicing |
| `rock.metal` | V5 power chord |
| `electronic.house` | V7sus4 in spread voicing |
| `latin.bossa_nova` | V7(b9, 13) in rootless voicing |

### 7.4 Scale Expansion

v1.0 had 14 scales. v2.0 adds genre-essential scales: bebop major, bebop dominant, altered (super-Locrian), diminished (half-whole, whole-half), Lydian dominant, Spanish Phrygian, Hirajoshi, In-sen, Yo, raga base scales (Indian), maqam base scales (Middle Eastern), klezmer (freygish).

### 7.5 Idiomatic Phrase Library

A library of **per-instrument, per-genre phrase templates**. Without this, instruments can be played but not "played idiomatically."

```python
@dataclass(frozen=True)
class PhraseTemplate:
    name: str
    instrument_class: str                  # "piano", "electric_guitar", ...
    genre_tags: list[str]
    rhythm_pattern: list[float]
    pitch_pattern: PitchPattern            # ChordTones, WalkingBass, etc.
    velocity_pattern: list[int]
    articulation: list[Articulation]       # legato, staccato, palm_mute, ...
    typical_length_bars: float
```

Initial library (~100 templates at launch, expanding via community contribution):

| Phrase | Instrument | Genres |
|---|---|---|
| `piano_jazz_comp_freddie_green` | piano | jazz_swing |
| `piano_stride_bass` | piano | ragtime, stride |
| `piano_arpeggio_alberti` | piano | classical |
| `piano_block_chord_pop` | piano | pop, ballad |
| `guitar_metal_chug` | electric_guitar_distorted | metal |
| `guitar_funk_16th_strum` | electric_guitar_clean | funk |
| `guitar_arpeggio_finger_pick` | acoustic_guitar | folk |
| `guitar_bossa_thumb_fingers` | acoustic_guitar_nylon | bossa_nova |
| `guitar_blues_double_stop` | electric_guitar_clean | blues |
| `bass_walking_chord_tone` | acoustic_bass | jazz |
| `bass_root_octave_pop` | electric_bass | pop |
| `bass_slap_funk` | electric_bass_finger | funk |
| `bass_reggae_skank` | electric_bass | reggae |
| `drum_fill_4_bar_classic` | drum_kit | rock, pop |
| `strings_pad_sustained` | strings_ensemble | cinematic, ambient |
| `strings_pizzicato_staccato` | strings_ensemble | classical, soundtrack |
| `sax_bebop_8th_line` | alto_sax, tenor_sax | jazz_bebop |
| `flute_celtic_ornament` | flute | celtic |

The Orchestrator Subagent consults this library when assigning material to instruments.

---

## 8. Time Signatures and Meter Flexibility

v1.0 was 4/4-centric. v2.0 supports any time signature, including compound and odd meters, with per-section variation.

### 8.1 Section-Level Meter Change

```yaml
sections:
  - name: intro
    bars: 4
    time_signature: "4/4"
    tempo: 80
  - name: verse_a
    bars: 8
    time_signature: "7/8"            # this section is in 7/8
    tempo: 80
  - name: bridge
    bars: 4
    time_signature: "4/4"
    tempo:
      start: 80
      end: 120                       # accelerando
      curve: linear
  - name: outro
    bars: 4
    time_signature: "4/4"
    rubato: true                     # free time
```

### 8.2 Compound Meter Recognition

```python
COMPOUND_METER_FEEL = {
    "6/8":  MeterFeel(groups=[3, 3], pulse="dotted_quarter"),
    "12/8": MeterFeel(groups=[3, 3, 3, 3], pulse="dotted_quarter"),
    "9/8":  MeterFeel(groups=[3, 3, 3], pulse="dotted_quarter"),  # jig
    "7/8":  MeterFeel(groups=[2, 2, 3], pulse="eighth"),
    "5/4":  MeterFeel(groups=[3, 2], pulse="quarter"),
    "5/8":  MeterFeel(groups=[3, 2], pulse="eighth"),
}
```

The Composer Subagent and Drum Generator both respect compound feel when generating rhythms.

### 8.3 Genre-Specific Meter Norms

Genre profiles declare typical meters. The Conductor refuses to silently apply an alien meter to a genre — if the user requests "rock in 7/8" and rock's typical meter is 4/4, the Conductor flags it as an intentional fusion choice and records it in provenance.

---

## 9. Synthesizer and Electronic Expansion

v1.0 had three synthesizers (square lead, saw lead, warm pad). v2.0 dramatically expands the electronic palette.

### 9.1 Expanded Synth Instruments

YaO maps the full General MIDI synth set (programs 80–103) and adds modern synth role concepts: leads (square, saw, calliope, chiff, charang, voice, fifths, bass_lead), pads (new_age, warm, polysynth, choir, bowed, metallic, halo, sweep), FX (rain, soundtrack, crystal, atmosphere, brightness, goblins, echoes, sci_fi), bass (synth_bass_1, synth_bass_2, acid_bass, wobble_bass, reese_bass, sub_bass), and role-based (pluck, arp, supersaw, fm_bell, brass_stab).

### 9.2 Modulation Curves

Synth realism requires modulation. v2.0 adds `ModulationCurve` to the IR:

```python
@dataclass(frozen=True)
class ModulationCurve:
    cc_number: int                     # 1=mod wheel, 11=expression,
                                       # 74=filter cutoff, 71=resonance
    waypoints: list[tuple[float, int]] # (beat, value 0-127)
    interpolation: str                 # "linear", "exponential", "step"

@dataclass(frozen=True)
class SynthPart(Part):
    modulation: list[ModulationCurve] = field(default_factory=list)
    pitch_bend: list[tuple[float, int]] = field(default_factory=list)
```

### 9.3 Genre-Specific Synth Patterns

```python
EDM_SYNTH_PATTERNS = {
    "house_pluck_arp": SynthPatternSpec(...),
    "trance_supersaw_chord": SynthPatternSpec(...),
    "dubstep_wobble": SynthPatternSpec(
        wobble_lfo_rate="dotted_8th",
        filter_cc_automation=...,
    ),
    "future_bass_chord_chop": SynthPatternSpec(...),
    "synthwave_pluck_octave": SynthPatternSpec(...),
}
```

### 9.4 Sidechain Compression (Notional)

For genres where sidechain pumping is signature (house, trance, future bass), the Production stage applies notional sidechain automation as a velocity envelope on long pad notes synchronized to the kick. This is encoded in provenance for users with DAW workflows to recreate accurately.

---

## 10. Perception Substitute Layer (Layer 4)

> ⚠️ **STATUS CORRECTION (2026-07-26): this layer is DESIGNED, NOT OPERATIONAL.**
> `perception/reference_matcher.py`, `style_vector.py`, and `psych_mapper.py`
> exist but are **inert** — reachable only from unit tests, never wired into the
> generation/selection loop. The reference library is self-generated (not a
> rights-cleared corpus). Layer 7 learning (`reflect/style_profile.py`
> `update_from_outcome`/`bias`) is likewise implemented-but-uncalled. Treat this
> section as *aspirational*; see `docs/STATUS.md`. Recommendation from the
> improvement program: either ingest a real public-domain corpus and wire
> `StyleVector` similarity into candidate selection, or formally descope this
> layer — do not ship a "hall of mirrors" that compares the system to itself.

v1.0 had this layer designed but empty. v2.0 implements it with three components.

### 10.1 Reference Library

Rights-cleared MIDI works (public domain classical, CC0 contributions, original works) are stored in `references/midi/` with metadata in `references/catalog.yaml`. Features are pre-extracted:

```python
@dataclass(frozen=True)
class ReferenceFeatures:
    midi_path: str
    genre: GenreSpec
    duration_sec: float
    chord_progression: list[ChordSpec]
    melodic_contour: ContourDescriptor
    rhythm_density_per_bar: list[float]
    pitch_class_histogram: list[float]    # 12-dim
    interval_histogram: list[float]
    spectral_centroid_mean: float | None
    tempo_estimate: float
```

### 10.2 Style Vectors

Each reference is projected into a 64-dimensional style space:

```python
def compute_style_vector(features: ReferenceFeatures) -> np.ndarray:
    return np.concatenate([
        features.pitch_class_histogram,        # 12
        features.interval_histogram[:12],      # 12
        features.rhythm_density_descriptors,   # 8
        features.contour_descriptors,          # 8
        features.dynamic_descriptors,          # 8
        features.section_descriptors,          # 8
        features.spectral_descriptors,         # 8
    ])  # 64 total
```

### 10.3 Reference-Driven Generation

Spec can include positive and negative references:

```yaml
references:
  positive:
    - id: ref_001_bach_invention_8
      weight: 0.6
      extract: [chord_progression, melodic_contour]
  negative:
    - id: ref_999_generic_corporate_bgm
      weight: 0.4
```

During multi-candidate stochastic generation, candidates are scored by style vector similarity to positive references and dissimilarity to negative references. The Conductor selects the best.

### 10.4 Psychological Mapping

Empirical rules from music psychology research (Juslin, Sloboda, Huron, Krumhansl):

```python
PSYCHOLOGICAL_RULES = [
    Rule(feature="tempo_bpm", threshold=120,
         above="perceived_high_energy", below="perceived_calm"),
    Rule(feature="mode",
         major="perceived_positive_valence",
         minor="perceived_introspective"),
    Rule(feature="spectral_centroid_mean", threshold=1500,
         above="perceived_bright", below="perceived_warm"),
    Rule(feature="dissonance_ratio", threshold=0.3,
         above="perceived_tense", below="perceived_resolved"),
]
```

These inform but never override generation. The Adversarial Critic uses them to flag perception-intent mismatches.

---

## 11. Directory Structure

```
yao/
+-- CLAUDE.md                          # Agent operational rules (v2.0)
+-- PROJECT.md                         # This file
+-- README.md                          # User quickstart
+-- pyproject.toml                     # Dependencies
+-- Makefile                           # Dev commands
|
+-- .claude/
|   +-- commands/                      # Custom slash commands
|   +-- agents/                        # 7 Subagent definitions
|   +-- skills/
|   |   +-- genres/                    # v2.0: 30+ profiles
|   |   |   +-- classical/             # baroque, romantic, minimalist...
|   |   |   +-- jazz/                  # bebop, modal, bossa-nova...
|   |   |   +-- rock/                  # classic, metal, progressive...
|   |   |   +-- pop/                   # mainstream, synth, j-pop...
|   |   |   +-- hiphop/                # boom-bap, trap, lofi...
|   |   |   +-- electronic/            # house, techno, ambient...
|   |   |   +-- rnb/                   # neo-soul, classic...
|   |   |   +-- funk/                  # classic, p-funk...
|   |   |   +-- latin/                 # bossa, salsa, samba...
|   |   |   +-- blues/                 # chicago, delta...
|   |   |   +-- country/               # traditional, bluegrass...
|   |   |   +-- reggae/                # roots, dub...
|   |   |   +-- world/                 # celtic, flamenco...
|   |   |   +-- soundtrack/            # cinematic, anime...
|   |   +-- theory/
|   |   |   +-- voice-leading.md
|   |   |   +-- reharmonization.md
|   |   |   +-- modal-interchange.md
|   |   |   +-- bebop-language.md      # v2.0
|   |   |   +-- power-chord-harmony.md # v2.0
|   |   |   +-- quartal-harmony.md     # v2.0
|   |   +-- instruments/
|   |   |   +-- piano.md
|   |   |   +-- guitar.md              # v2.0
|   |   |   +-- bass.md                # v2.0
|   |   |   +-- drums.md               # v2.0 NEW
|   |   |   +-- strings.md
|   |   |   +-- synths.md              # v2.0 expanded
|   |   |   +-- saxophone.md           # v2.0
|   |   +-- groove/                    # v2.0 NEW
|   |   |   +-- swing-feel.md
|   |   |   +-- hip-hop-pocket.md
|   |   |   +-- four-on-the-floor.md
|   |   |   +-- clave-patterns.md
|   |   +-- psychology/
|   +-- guides/                        # Developer guides
|   |   +-- architecture.md
|   |   +-- coding-conventions.md
|   |   +-- music-engineering.md
|   |   +-- testing.md
|   |   +-- workflow.md
|   |   +-- genre-development.md       # v2.0 NEW
|   |   +-- drum-development.md        # v2.0 NEW
|   +-- hooks/
|
+-- specs/
|   +-- templates/
|   |   +-- minimal.yaml
|   |   +-- bgm-90sec.yaml
|   |   +-- cinematic-3min.yaml
|   |   +-- trajectory-example.yaml
|   |   +-- genres/                    # v2.0 NEW: 30+ templates
|   |       +-- classical/, jazz/, rock/, pop/, hiphop/, electronic/,
|   |       +-- world/, soundtrack/, ...
|   +-- projects/                      # User compositions
|
+-- src/
|   +-- yao/
|   |   +-- conductor/                 # Orchestration engine
|   |   |   +-- conductor.py           # v2.0: genre-aware
|   |   |   +-- feedback.py            # v2.0: genre-specific adaptations
|   |   |   +-- mood_parser.py         # v2.0 NEW
|   |   |   +-- result.py
|   |   +-- constants/
|   |   |   +-- instruments.py
|   |   |   +-- drums.py               # v2.0 NEW
|   |   |   +-- drum_patterns.py       # v2.0 NEW
|   |   |   +-- groove_templates.py    # v2.0 NEW
|   |   |   +-- micro_timing.py        # v2.0 NEW
|   |   |   +-- genres.py              # v2.0 NEW
|   |   |   +-- genre_profiles.py      # v2.0 NEW
|   |   |   +-- phrase_library.py      # v2.0 NEW
|   |   |   +-- scales.py              # v2.0 expanded
|   |   |   +-- chords.py
|   |   |   +-- dynamics.py
|   |   +-- schema/
|   |   |   +-- composition.py         # v2.0: + genre, + drum_kit
|   |   |   +-- genre.py               # v2.0 NEW
|   |   |   +-- groove.py              # v2.0 NEW
|   |   |   +-- trajectory.py
|   |   |   +-- constraints.py
|   |   |   +-- references.py
|   |   |   +-- negative_space.py
|   |   |   +-- production.py
|   |   +-- ir/
|   |   |   +-- score_ir.py
|   |   |   +-- note.py
|   |   |   +-- drum_part.py           # v2.0 NEW
|   |   |   +-- synth_part.py          # v2.0 NEW
|   |   |   +-- harmony.py             # v2.0: extended
|   |   |   +-- voicing.py             # v2.0: + power, quartal, shell, ...
|   |   |   +-- phrase.py              # v2.0 NEW
|   |   |   +-- motif.py
|   |   |   +-- timing.py              # v2.0: groove application
|   |   |   +-- notation.py
|   |   +-- generators/
|   |   |   +-- base.py
|   |   |   +-- registry.py
|   |   |   +-- rule_based.py          # v2.0: genre-aware
|   |   |   +-- stochastic.py          # v2.0: genre-aware
|   |   |   +-- drum_generator.py      # v2.0 NEW
|   |   |   +-- markov.py              # v2.0 NEW
|   |   |   +-- ai_bridge.py           # v2.0 NEW (optional)
|   |   +-- perception/                # v2.0 NEW
|   |   |   +-- reference_matcher.py
|   |   |   +-- psych_mapper.py
|   |   |   +-- style_vector.py
|   |   +-- arrange/                   # v2.0 NEW
|   |   |   +-- operations.py
|   |   |   +-- reharmonize.py
|   |   |   +-- regroove.py
|   |   |   +-- reorchestrate.py
|   |   |   +-- genre_transfer.py
|   |   +-- render/
|   |   |   +-- midi_writer.py         # v2.0: + GM ch10
|   |   |   +-- audio_renderer.py
|   |   |   +-- stem_writer.py
|   |   |   +-- iteration.py
|   |   +-- verify/
|   |   |   +-- music_lint.py
|   |   |   +-- analyzer.py
|   |   |   +-- evaluator.py           # v2.0: base class
|   |   |   +-- evaluators/            # v2.0 NEW
|   |   |   |   +-- generic.py
|   |   |   |   +-- jazz.py
|   |   |   |   +-- rock.py
|   |   |   |   +-- edm.py
|   |   |   |   +-- ambient.py
|   |   |   |   +-- classical.py
|   |   |   |   +-- hiphop.py
|   |   |   +-- constraint_checker.py
|   |   |   +-- diff.py
|   |   +-- reflect/
|   |   |   +-- provenance.py
|   |   |   +-- style_profile.py       # v2.0
|   |   +-- errors.py
|   |   +-- types.py
|   +-- cli/                           # Click CLI
|
+-- references/                        # Aesthetic reference library
|   +-- catalog.yaml
|   +-- midi/                          # rights-cleared works only
|   +-- musicxml/
|   +-- extracted_features/            # pre-computed style vectors
|   +-- learned_models/                # v2.0: Markov models per genre
|
+-- outputs/                           # generated artifacts (gitignored)
+-- soundfonts/                        # GM SoundFonts (gitignored)
+-- tests/
|   +-- unit/
|   +-- integration/
|   +-- music_constraints/
|   +-- scenarios/
|   +-- genres/                        # v2.0 NEW: per-genre tests
|   +-- drums/                         # v2.0 NEW
|   +-- groove/                        # v2.0 NEW
+-- tools/                             # arch-lint and other dev tools
+-- docs/
```

---

## 12. Orchestra: Subagent Design

All seven Subagents from v1.0 are preserved, with v2.0 expansions noted.

### 12.1 Composer
**Responsibility**: Melody, motif, theme, structural outline generation.
**Inputs**: `intent.md`, `composition.yaml` (including `genre`), `trajectory.yaml`, `references.yaml`.
**Outputs**: ScoreIR draft (motifs, melody lines, structure).
**Forbidden**: Instrument selection, final voicing (those are Orchestrator's job).
**v2.0 additions**: Consults genre profile for typical melodic contour, preferred scales, motif length conventions, and idiomatic phrasing.

### 12.2 Harmony Theorist
**Responsibility**: Chord progression, modulation, secondary dominants, cadences, reharmonization.
**Inputs**: Composer's melody draft, `composition.yaml` harmony section, `genre` profile.
**Outputs**: Chord progression IR (Roman numerals + concrete voicings).
**v2.0 additions**: Genre-driven chord vocabulary (palette, extensions, alterations, voicing style). Supports power chords, quartal harmony, altered dominants, modal interchange per genre rules.

### 12.3 Rhythm Architect
**Responsibility**: Drum patterns, grooves, syncopation, fills, breakdowns.
**Inputs**: `composition.yaml`, genre profile, section structure, trajectory.
**Outputs**: Rhythm IR for all parts + DrumPart.
**v2.0 additions**: This Subagent receives the largest v2.0 expansion. It now generates full DrumPart instances from the drum pattern library, applies the Groove Engine, and inserts section-aware fills and breakdowns.

### 12.4 Orchestrator
**Responsibility**: Instrument assignment, voicing, range allocation, countermelody, idiomatic phrasing.
**Inputs**: Outputs of Composer, Harmony Theorist, Rhythm Architect.
**Outputs**: Complete ScoreIR with full parts per instrument.
**v2.0 additions**: Consults the Phrase Library to apply idiomatic phrasing per instrument and genre. Manages frequency space allocation in dense arrangements.

### 12.5 Adversarial Critic
**Responsibility**: Find every weakness. Never praises.
**Inputs**: Any-stage output.
**Outputs**: `critique.md` with severity-rated issues.
**v2.0 additions**: Uses genre-specific evaluators. For jazz, checks chord-tone targeting and chromatic approach. For EDM, checks drop intensity and hook repetition. For ambient, checks textural evolution. Flags genre antipattern matches (e.g., power chords in a jazz piece without fusion intent).

### 12.6 Mix Engineer
**Responsibility**: Stereo placement, dynamics, frequency balance, LUFS management.
**Inputs**: Orchestrator's output + production parameters.
**Outputs**: Mix instructions per track (EQ, compression, reverb, pan).
**v2.0 additions**: Per-genre LUFS targets (e.g., -14 LUFS for streaming pop, -23 LUFS for film). Sidechain compression notional automation for relevant genres.

### 12.7 Producer
**Responsibility**: Overall integration, prioritization, dialogue with the human conductor, final judgment.
**Inputs**: All Subagent outputs + human feedback.
**Outputs**: Final production decisions, next-iteration directives.
**Privilege**: Only one who can override others.
**v2.0 additions**: Genre-conscious tradeoffs. When evaluation flags a metric problem, the Producer considers whether the problem is a genre-specific concern or a generic one, and prioritizes accordingly.

---

## 13. Composition Cognitive Protocol: 6 Phases

The `/compose` and `/arrange` commands run Claude Code through six phases in strict order. This structures cognition and prevents the failure pattern of "starting to write notes immediately."

### Phase 1: Intent Crystallization
From user input (dialogue / YAML / sketch), distill the piece's essence to 1–3 sentences. Ambiguity is not tolerated. Saved as `intent.md`.

**v2.0 expansion**: Intent must now include or imply a genre. If absent, Phase 1 prompts the user for clarification before proceeding. Mood and genre together determine all downstream defaults.

### Phase 2: Architectural Sketch
Design the time-axis trajectories (tension, density, valence, predictability) **first**. No notes yet. Saved as `trajectory.yaml`.

**v2.0 expansion**: Genre profile provides default trajectory shapes (e.g., EDM's build-and-drop arc, jazz's solo trading dynamics, ambient's slow evolution). User can override.

### Phase 3: Skeletal Generation
Composer Subagent generates seeds of chord progression and main melody. **5–10 candidates for diversity.** Completion is 60% — details come later.

**v2.0 expansion**: Candidates respect the genre profile's chord palette and scale preferences. The pool diversity is genre-bounded — bebop candidates are not generated for an ambient request.

### Phase 4: Critic-Composer Dialogue
Adversarial Critic attacks all candidates. Producer decides — selects the strongest, or directs a new candidate combining strengths.

**v2.0 expansion**: The Adversarial Critic uses the genre-specific evaluator. Critique sections are organized by genre-relevant criteria.

### Phase 5: Detailed Filling
The chosen skeleton is fleshed out by Harmony Theorist, Rhythm Architect, and Orchestrator. Every decision is recorded in provenance.

**v2.0 expansion**: Rhythm Architect generates DrumPart. Orchestrator applies idiomatic phrases. Groove Engine applies micro-timing at the end of this phase.

### Phase 6: Listening Simulation
The Perception Substitute Layer "listens" to the finished piece and measures divergence from Phase 1 intent. Beyond a threshold, regenerate the offending section. Final outputs: `critique.md`, `analysis.json`, `evaluation.json`.

**v2.0 expansion**: This phase is now fully implemented. Reference library matching, psychological mapping, and style vector distance all feed into the divergence measurement.

---

## 14. Parameter Specifications

YaO completely describes a piece using YAML files. All are version-controlled and git-diff-friendly.

### 14.1 `intent.md` — Natural language intent
Stable from v1.0. The piece's essence in 1–3 sentences.

### 14.2 `composition.yaml` — Core composition parameters
v2.0 adds `genre`, `drum_kit` instrument support, and groove reference:

```yaml
title: My Song
genre:                              # v2.0 NEW
  primary: jazz
  subgenre: bebop
  era: 1940s
key: F major
tempo_bpm: 220
time_signature: "4/4"

instruments:
  - name: alto_sax
    role: melody
  - name: piano
    role: comping
  - name: acoustic_bass
    role: bass
  - name: drum_kit                  # v2.0 NEW
    role: drums
    kit_preset: jazz_brushes

sections:
  - name: head_in
    bars: 32
    structure: AABA
    dynamics: mp
  - name: solo_alto
    bars: 32
    structure: AABA
    dynamics: mf

generation:
  strategy: stochastic
  seed: 42
  temperature: 0.5

groove:                             # v2.0 NEW (or in trajectory.yaml)
  swing_ratio: 0.66
  groove_template: jazz_swing
  humanize:
    timing_jitter_ms: 8
    velocity_jitter: 12
```

### 14.3 `trajectory.yaml` — Time-axis trajectories
Stable from v1.0. Tension, density, valence, predictability curves.

### 14.4 `references.yaml` — Aesthetic reference library
v2.0: Now actively used by the Perception Substitute Layer.

### 14.5 `negative-space.yaml` — What not to sound
Stable from v1.0.

### 14.6 `arrangement.yaml` — Arrangement parameters
v2.0: Now actually implemented (was placeholder in v1.0).

### 14.7 `production.yaml` — Mix and master parameters
v2.0: Genre-aware LUFS targets and processing chains.

### 14.8 `provenance.json` — Auto-generated decision log
Stable from v1.0, content expanded for v2.0 decisions (genre profile choices, drum pattern selections, micro-timing applications).

---

## 15. Custom Commands

| Command | Purpose | Primary Subagents | v2.0 Status |
|---|---|---|---|
| `/compose <project>` | Generate from spec | Composer → all | Updated: genre-aware |
| `/conduct <description>` | Natural language → music | Producer + all | Updated: mood parser |
| `/arrange <project>` | Transform existing | Orchestrator + Critic | NEW implementation |
| `/critique <iteration>` | Adversarial review | Adversarial Critic | Updated: genre-aware |
| `/regenerate-section` | Fix one section | Composer + Producer | Stable |
| `/morph <from> <to>` | Style interpolation | Composer + Orchestrator | NEW |
| `/explain <element>` | Decision rationale | Producer (Provenance) | Stable |
| `/diff <a> <b>` | Compare iterations | Verifier | Stable |
| `/render <iteration>` | MIDI to audio | Mix Engineer | Stable |
| `/sketch` | Dialogue spec creation | Producer | Updated: genre prompting |

---

## 16. Skills Library

`.claude/skills/` contains structured knowledge modules consulted by Subagents. v2.0 dramatically expands this.

### 16.1 Genre Skills
30+ genre profiles, each authored to a fixed template (overview, instrumentation, tempo range, harmonic vocabulary, melodic vocabulary, rhythmic vocabulary, structure templates, evaluation criteria, antipatterns, abstract references, constraints).

### 16.2 Theory Skills
Voice leading, reharmonization, modal interchange, plus v2.0 additions: bebop language, power chord harmony, quartal harmony, blues progressions, modal jazz, polyharmony.

### 16.3 Instrument Skills
Per-instrument: range, idiomatic gestures, timbral characteristics, physical constraints, representative phrase patterns. v2.0 adds dedicated coverage for drums, guitar, bass, saxophone, and expanded synth coverage.

### 16.4 Groove Skills (NEW in v2.0)
Per-feel: swing feel, hip-hop pocket, four-on-the-floor, clave patterns, breakbeat, halftime, double-time, shuffle.

### 16.5 Psychology Skills
Empirical mappings from music psychology: tension/resolution, emotion mapping, memorability principles, expectation and surprise (Huron).

---

## 17. Hooks

Hooks are scripts whose execution is **guaranteed** (not just instructed). v2.0 retains v1.0's four hooks:

| Hook | Trigger | Action |
|---|---|---|
| `pre-commit-lint` | git commit | music21 theory lint, schema validation, **v2.0: genre validation** |
| `post-generate-render` | generation complete | Auto-render MIDI to audio and score |
| `post-generate-critique` | generation complete | Run Adversarial Critic |
| `update-provenance` | any change | Sync Provenance graph |

---

## 18. MCP Integration

| Connection | Purpose |
|---|---|
| **DAW (Reaper preferred)** | Project I/O, automatic track layout |
| **Sample libraries** | Drum samples, one-shots, loops (v2.0: actively used) |
| **Reference library DB** | Rights-cleared metadata search |
| **MIDI controller** | Live improvisation input |
| **SoundFont / VST server** | Audio rendering |
| **AI model APIs (optional)** | v2.0: MusicGen, Stable Audio bridges |

---

## 19. Quality Assurance: Genre-Aware Evaluation

The evaluation system from v1.0 (Structure, Melody, Harmony, Arrangement, Acoustics) is preserved. v2.0 adds:

### 19.1 Genre-Specific Evaluator Subclasses
A `GenericEvaluator` provides v1.0 metrics. Genre-specific subclasses add metrics:

- **JazzEvaluator**: swing_feel, chord_change_density, chromatic_approach_ratio, chord_tone_on_strong_beat
- **EDMEvaluator**: drop_intensity, sidechain_pump, buildup_arc, hook_repetition
- **AmbientEvaluator**: textural_evolution, harmonic_stasis_quality
- **MetalEvaluator**: gain_consistency, palm_mute_ratio, rhythmic_aggression
- **HipHopEvaluator**: pocket_consistency, hook_strength, beat_humanization
- **ClassicalEvaluator**: voice_leading_strictness, formal_clarity, counterpoint_quality

The Conductor selects the evaluator from genre. Falls back to GenericEvaluator if no genre is set or no subclass exists.

### 19.2 Genre-Aware Adaptation in Feedback Loop
When evaluation flags a metric problem, the adaptation chosen depends on genre:

```python
GENRE_ADAPTATIONS = {
    "jazz.bebop": [
        Adaptation(if_metric="chord_tone_on_strong_beat", below=0.4,
                   action="bias_generation_to_chord_tones"),
        Adaptation(if_metric="swing_feel", below=0.6,
                   action="set_swing_ratio_0.67"),
    ],
    "edm.house": [
        Adaptation(if_metric="drop_intensity", below=0.7,
                   action="amplify_density_jump_at_chorus"),
    ],
}
```

---

## 20. Development Roadmap

v1.0 completed Phase 0 (foundation) and Phase 1 (parameter-driven symbolic composition). v2.0 establishes Phases 2–4.

### Phase 2: Diversity Foundation (Months 1–3)
**Month 1**: Drum Kit System (A1), Genre schema (A2), Conductor genre-awareness initial (B5), 10 base-genre Skills.
**Month 2**: Groove Engine (B1), extended chord vocabulary (B2), time signature flexibility (B4), 10 mid-tier genre Skills, 15 genre templates.
**Month 3**: Idiomatic Phrase Library MVP (B3), genre-specific evaluators (C3) for 5 priority genres, Markov generator (C4), 10 expansion genre Skills.

**Phase 2 success criteria**: Production-quality output for jazz, rock, pop, hip-hop, EDM, funk, blues, country, reggae, Latin.

### Phase 3: Acoustic and Arrangement Maturity (Months 4–6)
- Synthesizer / Electronic expansion (C1)
- Perception Substitute Layer MVP (C2)
- Arrangement Engine MVP (D1)
- 30+ genre templates complete
- Reference Library reaches usable size (50+ works)

**Phase 3 success criteria**: Production-quality output for metal, progressive, world music, ambient. Cross-genre arrangement is functional.

### Phase 4: Ecosystem and Voice (Months 7–9)
- AI Bridge (D2)
- Vocal / Lead support (D3, stages 1–2)
- Reference Library community operations
- Cross-genre Arrangement advanced features

**Phase 4 success criteria**: Production-quality output for R&B, soul, vocal-centric genres.

### Phase 5+ (Continuous)
- Reflection & Learning Layer (Layer 7) full operation
- Per-user style profiles
- Community reference library sharing standard
- Live improvisation mode
- DAW deep integration

---

## 21. Quick Start

### 21.1 Setup
```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts
```

### 21.2 First Song via Genre Template
```bash
# Start from a genre template
yao new-project my-first-jazz --template jazz/bebop-32-bar

# Open Claude Code
claude

# Inside Claude Code
> /compose my-first-jazz
> /critique my-first-jazz
```

### 21.3 First Song via Natural Language
```bash
> /conduct "a slow lo-fi hip-hop beat for studying, with mellow piano chords, 90 seconds, looping"
```

### 21.4 Cross-Genre Arrangement
```bash
> /arrange my-first-jazz --target-genre electronic.synthwave
```

---

## 22. File Formats and Interoperability

| Use | Format | Reason |
|---|---|---|
| Symbolic music | MIDI (.mid), MusicXML (.xml) | Industry standard, all DAWs |
| Notation | LilyPond (.ly), PDF | High-quality engraving |
| Specifications | YAML | Human-readable, git-friendly |
| Intermediate representation | JSON | Schema-validatable |
| Provenance | JSON | Graph structure |
| Audio | WAV (working), FLAC/MP3 (distribution) | Standards |
| Live code | Strudel pattern strings | Browser-renderable |

No proprietary formats are created unless absolutely necessary.

---

## 23. Ethics and License

### 23.1 Training Data and References
References are **rights-cleared works only**. Each work has a license entry in `references/catalog.yaml`. Unknown-status works are not used. CI rejects PRs adding unverified works.

### 23.2 Artist Imitation
Naming living artists or specific copyrighted works as imitation targets is **prohibited**. Instead, **abstract feature descriptions** are required:

> ✗ "in the style of Famous Artist"
> ✓ "open-voiced strings, ascending motifs, major-minor ambiguity, meditative tempo"

This applies equally to genre profiles, reference selections, and prompts.

### 23.3 Generated Output Rights
Output rights belong to the user by default. If reference influence exceeds a threshold (high style-vector similarity), the system issues a warning recommending license review.

### 23.4 Transparency
Provenance always includes the genre profile reference, the references used, and any AI model invocations. Users distributing YaO-generated works are encouraged to credit the system.

---

## 24. Relation to CLAUDE.md

| File | Audience | Content |
|---|---|---|
| `PROJECT.md` (this file) | Humans + agents | Overall design, philosophy, architecture |
| `CLAUDE.md` | Agents (primary) | Invariant rules, prohibitions, skill references |
| `README.md` | Humans (primary) | Quickstart, basic usage |
| `docs/design/*.md` | Humans + agents | Individual design decision records |
| `.claude/guides/*.md` | Developer + agents | Technical guides (architecture, testing, music engineering) |

In case of conflict: **CLAUDE.md > PROJECT.md > others**.

---

## 25. Future Architecture Extensions

Items still under consideration for post-v2.0:

### 25.1 Session / Project Runtime
A `ProjectRuntime` enabling stateful iterative sessions, with section-level generation cache, feedback queue, and undo/redo at musical granularity.

### 25.2 Backend-Agnostic Agent Protocol
Currently `.claude/agents/*.md` is Claude Code-specific. A Python-level abstract protocol (`AgentRole`, `AgentContext`, `AgentOutput`) would allow alternative backends, with Claude Code as one adapter.

### 25.3 Immediate Audio Feedback
YAML → MIDI → WAV → external player latency is too high for iteration. Future:
- `yao preview` for inline MIDI playback
- Strudel emission for browser-based immediate audition
- `sounddevice` for direct WAV playback

### 25.4 Spec Composition
Reusable spec fragments under `specs/fragments/` with `extends:` / `overrides:` keywords for composition.

### 25.5 Live Improvisation
MIDI controller input → real-time analysis → constraint-aware generation → Strudel/SuperCollider output. Game soundtracks, live performance accompaniment.

---

## 26. Glossary

**Conductor** — The human owner of the project; the final decision-maker.

**Orchestra** — Collective term for the Subagents.

**Score** — YAML files under `specs/`; complete description of a piece.

**ScoreIR** — Internal intermediate representation of a Score.

**Trajectory** — Time-axis characteristic curves (tension, density, etc.).

**Aesthetic Reference Library** — The collection of reference works.

**Perception Substitute Layer** — Layer 4; AI's compensation for not being able to "hear."

**Provenance** — Traceable record of every generation decision.

**Adversarial Critic** — The Subagent that intentionally attacks output.

**Negative Space** — Designed silence and gaps.

**Style Vector** — Multi-dimensional feature-space representation of style.

**Iteration** — A versioned generation within a project (v001, v002, ...).

**Music Lint** — Automated theory and constraint violation detection.

**Sketch-to-Spec** — Dialogue-based conversion of natural language sketch into YAML spec.

**GenreSpec** *(v2.0)* — Schema element specifying primary genre, subgenre, era, and influences.

**GenreProfile** *(v2.0)* — Structured definition of typical features for a genre.

**DrumPart** *(v2.0)* — IR element for drum kit (GM Channel 10) parts.

**DrumPiece** *(v2.0)* — Enum of GM drum/percussion sounds.

**Drum Pattern** *(v2.0)* — Named rhythm template (e.g., `rock_basic`, `bossa_nova`).

**Groove Engine** *(v2.0)* — Subsystem applying micro-timing offsets to grid-aligned notes.

**Micro-Timing Profile** *(v2.0)* — Genre-specific timing offset rules.

**Voicing Style** *(v2.0)* — How a chord is realized in pitch space (closed, open, drop-2, quartal, power, shell, ...).

**Idiomatic Phrase** *(v2.0)* — A pattern that makes an instrument "sound like itself" in a given genre.

**Genre Fusion** *(v2.0)* — Intentional blending of multiple genres with weighted influences.

**Reference-Driven Generation** *(v2.0)* — Generation guided by similarity to reference style vectors.

---

## 27. Closing: The World YaO Aspires To

YaO is not "AI that makes music." It is **infrastructure for humans and AI to co-create music, each contributing their strengths**.

- Humans bring **intent, judgment, and feeling**.
- AI brings **theory knowledge, iteration speed, and exhaustive recordkeeping**.
- YaO is **the place that makes their collaboration structured and reproducible**.

v2.0 broadens this collaboration to the full range of human musical expression — from a Bach invention to a trap beat, from a bossa nova to a dubstep drop, from a Celtic jig to an ambient drone. Every genre is treated with respect: each has its own profile, its own evaluation criteria, its own idiomatic vocabulary.

Great music remains, ultimately, **a manifestation of the human soul**. YaO aims to make that manifestation **faster, deeper, and more reproducible** — across every musical world the user wishes to inhabit.

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve, in any genre.*

---

**Project: You and Orchestra (YaO)**
*Document version: 2.0*
*Targeting: Phase 2 — Diversity Foundation*
*Last updated: 2026-05-15*
