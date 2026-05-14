# You and Orchestra (YaO)

> *An agentic music production environment where you are the conductor, and the AI is your orchestra.*
> *Reachable through Claude Code, the command line, and the Claude Agent SDK — same orchestra, different venues.*

---

## 0. The Essence of the Project

**You and Orchestra (YaO)** is an **agentic music production environment** that runs on top of three peer surfaces — Claude Code, a Click-based CLI, and the Claude Agent SDK for Python. Unlike conventional "AI music tools" that emit a black-box result, YaO produces music through a **division of labor among role-specialized AI agents (Orchestra Members)**, conducted by a human (You = Conductor).

Every design decision in YaO is subordinate to a single proposition:

> **Music production is not a one-shot intuitive act; it is a reproducible, improvable engineering process.**

YaO therefore treats music as **code, specifications, tests, diffs, and provenance** *before* it becomes audio. We call this the **Music-as-Code** philosophy. The same orchestra, the same Conductor, and the same musical engine are reachable from a terminal, an interactive Claude Code session, a web app, a Discord bot, a CI pipeline, or a Jupyter notebook — without compromise.

---

## 1. The Metaphor: You and Orchestra

Every YaO concept maps onto an orchestral analogy. Internalizing this map is the shortest path to using YaO correctly.

| YaO component | Orchestral analogy | Implementation |
| --- | --- | --- |
| **You** | The Conductor | The human owner of the project |
| **Score** | Sheet music | The YAML specifications under `specs/` |
| **Orchestra Members** | Players | The seven Subagents (Composer, Critic, Theorist, …) |
| **Concertmaster** | First-chair coordinator | The Producer Subagent |
| **Rehearsal** | Iteration before performance | The Conductor loop (generate → evaluate → adapt) |
| **Library** | The orchestra's score library | The reference works under `references/` |
| **Performance** | The concert | The rendered final audio |
| **Recording** | A pressed record | The artifacts under `outputs/` |
| **Critic** | The reviewer in the press | The Adversarial Critic Subagent |
| **Venue** | The hall the orchestra plays in | The **Surface** (Claude Code, CLI, or Agent SDK) |

The Conductor (You) does not write every note. The Conductor's job is to **clarify intent, set direction, judge rehearsals, and guarantee performance quality**. YaO brings that division of labor to AI. Crucially, the same orchestra plays in different venues: a private rehearsal room (Claude Code), a public stage (Agent SDK in a web app), or a quick recording session (CLI).

---

## 2. Design Principles

Every implementation choice in YaO is checked against the following **five non-negotiable principles**. They are mirrored in `CLAUDE.md` and used as decision criteria by every agent in the system.

### Principle 1 — The agent is an environment, not a composer
YaO does not aim to "be the AI that writes the song." It aims to be the environment that makes a human compose **ten times faster**. We accelerate human creativity; we never replace human judgment.

### Principle 2 — Every decision is explainable
Every note, chord, and arrangement choice carries a **why**. This is persisted in the Provenance Graph and is queryable, reviewable, and revisable.

### Principle 3 — Constraints liberate
Explicit YAML specifications, reference libraries, and negative-space designs are **scaffolds, not cages**. Unconstrained freedom paralyzes; well-shaped constraints unlock creation.

### Principle 4 — Time-axis first
A piece is first designed as **trajectories on the time axis** (tension, density, valence, predictability). Notes are filled in only after the curves are right. This produces musically meaningful structure rather than dense local cleverness.

### Principle 5 — The human ear is the final truth
No automated metric, however sophisticated, beats the human ear. Agents inform; humans decide. Every workflow keeps a clear human approval point.

---

## 3. Architecture: Three Surfaces over Seven Layers

YaO is split into a 3-tier **Surfaces** stratum atop a strict **7-layer** engine. Surfaces are how users invoke YaO. Layers are how YaO does the music. The two are independent: a layer never knows which surface called it; a surface never reaches around the layer it sits above.

```
╔═══════════════════════════════════════════════════════════════════╗
║ Surfaces                                                          ║
║ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐    ║
║ │  Claude Code     │ │  CLI (Click)     │ │  Agent SDK       │    ║
║ │  (interactive)   │ │  (yao …)         │ │  (yao.sdk)       │    ║
║ └─────────┬────────┘ └─────────┬────────┘ └─────────┬────────┘    ║
║           │                    │                    │             ║
║           └────────────────────┴────────────────────┘             ║
║                                │                                  ║
║                           Conductor                               ║
╚═══════════════════════════════════════════════════════════════════╝
                                 │
┌─────────────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                              │
│   Provenance log, query, explain                            │
├─────────────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                            │
│   Music lint, analysis, evaluation, diff, constraints       │
├─────────────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                          │
│   MIDI writer, stems, audio (FluidSynth), iterations        │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                              │
│   Reference matching, psychology mapping, style vector      │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Intermediate Representation (IR)                   │
│   ScoreIR, harmony, motif, voicing, timing, notation        │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                                │
│   Rule-based, stochastic, (Markov, constraint-solver)       │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Specification                                      │
│   Pydantic schemas, YAML parsing                            │
├─────────────────────────────────────────────────────────────┤
│ Layer 0: Constants                                          │
│   Instrument ranges, MIDI maps, scales, chords, dynamics    │
└─────────────────────────────────────────────────────────────┘
```

Layer dependency flows strictly **upward**. Lower layers do not import from higher layers. The Conductor is the engine entry point: it orchestrates the layered engine and is the **single point of truth** that all surfaces call. An AST-based architecture lint (`make arch-lint`) enforces these boundaries on every commit.

### 3.1 Why surfaces matter

Every surface offers a different latency / agency / persistence trade-off:

| | **Claude Code** | **CLI** | **Agent SDK** |
|---|---|---|---|
| Latency | Conversational | One-shot | Streaming |
| Agency | Full agentic loop | Stateless | Full agentic loop |
| Persistence | Session-bound | None | Resumable sessions |
| Best for | Day-to-day human composition | Scripts, smoke tests, CI shells | Web apps, bots, batch services, notebooks |

Crucially, **all three surfaces share the same `.claude/` directory** (subagents, slash commands, skills, CLAUDE.md). The SDK loads it via `setting_sources=["project"]`; Claude Code loads it natively; the CLI does not load it because the CLI does not run an agent loop. This means: **changing a subagent definition in `.claude/agents/composer.md` instantly affects both Claude Code and the SDK** — there is one source of truth.

---

## 4. Directory Structure

```
yao/
├── CLAUDE.md                      # Invariant rules for Claude Code
├── PROJECT.md                     # This file (full design)
├── README.md                      # User-facing quickstart
├── pyproject.toml                 # Dependencies (pretty_midi, music21, …, claude-agent-sdk)
├── Makefile                       # Top-level dev commands
│
├── .claude/
│   ├── commands/                  # Slash commands shared by Claude Code & SDK
│   │   ├── compose.md
│   │   ├── critique.md
│   │   ├── sketch.md
│   │   ├── regenerate-section.md
│   │   ├── render.md
│   │   ├── arrange.md             # planned (Phase 2)
│   │   └── explain.md
│   ├── agents/                    # Markdown subagent definitions (source of truth)
│   │   ├── producer.md
│   │   ├── composer.md
│   │   ├── harmony-theorist.md
│   │   ├── rhythm-architect.md
│   │   ├── orchestrator.md
│   │   ├── mix-engineer.md
│   │   └── adversarial-critic.md
│   ├── skills/                    # Specialized knowledge modules
│   │   ├── genres/
│   │   ├── theory/
│   │   ├── instruments/
│   │   └── psychology/
│   └── guides/                    # Developer guides referenced by CLAUDE.md
│       ├── architecture.md
│       ├── coding-conventions.md
│       ├── music-engineering.md
│       ├── sdk.md                 # SDK-specific dev guide
│       ├── testing.md
│       └── workflow.md
│
├── specs/                         # Composition specifications
│   ├── templates/                 # Ready-to-use templates
│   └── projects/                  # User compositions
│
├── src/
│   ├── yao/                       # Core engine (layers 0–7)
│   │   ├── constants/             # Layer 0
│   │   ├── schema/                # Layer 1
│   │   ├── generators/            # Layer 2
│   │   ├── ir/                    # Layer 3
│   │   ├── perception/            # Layer 4
│   │   ├── render/                # Layer 5
│   │   ├── verify/                # Layer 6
│   │   ├── reflect/               # Layer 7
│   │   ├── conductor/             # Engine entry point
│   │   ├── errors.py
│   │   ├── types.py
│   │   └── sdk/                   # SURFACE: Agent SDK integration
│   │       ├── __init__.py
│   │       ├── agent.py           # YaoAgent façade (Lane A)
│   │       ├── server.py          # In-process MCP server (Lane B core)
│   │       ├── tools.py           # @tool decorators
│   │       ├── agents.py          # AgentDefinition mirrors of .claude/agents/
│   │       ├── _frontmatter.py    # Internal Markdown parser
│   │       ├── hooks.py           # PreToolUse / PostToolUse hooks
│   │       ├── permissions.py     # CanUseTool callback
│   │       ├── events.py          # Streaming event types
│   │       ├── results.py         # Typed result objects
│   │       ├── schemas.py         # JSON Schema for output_format
│   │       ├── streaming.py       # Message → YaoEvent translator
│   │       ├── sessions.py        # Project-scoped session helpers
│   │       └── _options.py        # default_yao_options builder
│   └── cli/                       # SURFACE: Click-based CLI
│       ├── __init__.py
│       ├── compose.py
│       ├── conduct.py
│       ├── render.py
│       ├── …
│       ├── agent.py               # `yao agent "<prompt>"`
│       └── serve.py               # `yao serve`
│
├── references/                    # Aesthetic reference library (rights-cleared)
│   ├── catalog.yaml
│   ├── midi/
│   └── extracted_features/
│
├── outputs/                       # Generated artifacts (git-ignored)
│   └── projects/<name>/iterations/v001/…
│
├── soundfonts/                    # Audio rendering
│
├── tests/
│   ├── unit/                      # Per-module tests
│   ├── integration/               # Full pipeline tests
│   ├── music_constraints/         # Instrument-range, voice-leading, etc.
│   ├── scenarios/                 # End-to-end musical scenarios
│   └── sdk/                       # SDK-specific tests
│       ├── unit/
│       ├── integration/           # Includes G1–G5 parity tests
│       └── scenarios/
│
├── examples/
│   └── sdk/                       # Reference applications
│       ├── minimal.py             # 5-line YaoAgent example
│       ├── web/                   # FastAPI + HTML
│       ├── discord/               # discord.py bot
│       ├── ci/                    # GitHub Action
│       └── notebook/              # Jupyter
│
├── tools/
│   └── architecture_lint.py       # Layer-boundary AST checker
│
└── docs/
    ├── design/                    # Architecture decision records
    ├── tutorials/
    ├── glossary.md
    └── sdk/                       # SDK documentation site
        ├── overview.md
        ├── quickstart.md
        ├── api-reference.md
        ├── lane-a-vs-lane-b.md
        ├── deployment.md
        └── parity-with-claude-code.md
```

---

## 5. The Orchestra: Subagent Design

YaO's orchestra has **seven members**. Each has a clearly bounded responsibility, an explicit input contract, an explicit output contract, and a tool allowlist that enforces role boundaries. The Producer Subagent is the only member with override authority over the others.

The seven members are defined in **two synchronized representations**:

1. **`.claude/agents/<name>.md`** — Markdown with YAML front matter. *Source of truth.* Used by Claude Code natively and loaded by the Agent SDK via `setting_sources=["project"]`.
2. **`yao.sdk.agents.yao_agent_definitions()`** — A function that parses the Markdown at module load time and returns `dict[str, AgentDefinition]`. Used when a host has no filesystem access (serverless, embedded deployments).

**The Markdown is authoritative.** The Python mirror is regenerated on import. There is no manual sync step; if the Markdown changes, the Python mirror changes too.

### 5.1 Composer
**Responsibility:** Generate melodies, motifs, themes, and structural outlines.
**Inputs:** `intent.md`, `composition.yaml`, `trajectory.yaml`, `references.yaml`.
**Outputs:** ScoreIR fragments (motifs, melodic lines, structure).
**Forbidden:** Instrument selection, final voicing (those belong to the Orchestrator).
**Evaluated on:** Motif memorability, repetition/variation balance, trajectory match.

### 5.2 Harmony Theorist
**Responsibility:** Chord progressions, modulations, secondary dominants, cadences, reharmonization.
**Inputs:** Composer's melodic seed, the `harmony` block of `composition.yaml`.
**Outputs:** Chord progression IR (functional notation + concrete voicing candidates).
**Evaluated on:** Functional integrity, tension–resolution shape, genre fit.

### 5.3 Rhythm Architect
**Responsibility:** Drum patterns, groove, syncopation, fills.
**Inputs:** `rhythm` block of `composition.yaml`, genre cues.
**Outputs:** Rhythm IR for all instruments.
**Evaluated on:** Groove, humanization, section contrast.

### 5.4 Orchestrator
**Responsibility:** Instrument assignment, voicings, register placement, countermelodies.
**Inputs:** Output of Composer, Harmony Theorist, Rhythm Architect.
**Outputs:** Complete ScoreIR with per-instrument parts.
**Evaluated on:** Frequency-space conflict avoidance, idiomatic instrument use, texture density.

### 5.5 Mix Engineer
**Responsibility:** Stereo placement, dynamics, frequency-mask resolution, loudness (LUFS).
**Inputs:** Orchestrator's output + `production.yaml` parameters.
**Outputs:** Mix instructions per track (EQ, compression, reverb, pan).
**Evaluated on:** LUFS target, frequency balance, stereo width.

### 5.6 Adversarial Critic
**Responsibility:** **Find every weakness.**
**Inputs:** Any artifact at any pipeline stage.
**Outputs:** `critique.md` with a severity-ranked list of issues.
**Distinguishing trait:** **Never praises.** Hunts for clichés, structural boredom, emotional misalignment, suspicious similarity to existing works.
**Tool restriction:** `disallowedTools = ["Write", "Edit"]`. The Critic reads, judges, and reports — it never modifies.
**Evaluated on:** Coverage and specificity of issues found.

### 5.7 Producer
**Responsibility:** Coordination, prioritization, dialogue with the human Conductor, final judgment.
**Inputs:** All Subagent outputs + human feedback.
**Outputs:** Final production decisions, instructions for the next iteration.
**Privilege:** *The only* Subagent who can reject or revise another's output.
**Evaluated on:** Fidelity to `intent.md`.

---

## 6. The Six-Phase Cognitive Protocol

YaO's `/compose`, `/conduct`, and `/arrange` commands all execute the following six phases **in order**. The protocol prevents the most common failure pattern: an agent who jumps straight to writing notes before deciding what the piece is about.

| Phase | Purpose | Output |
|---|---|---|
| **1. Intent Crystallization** | Convert user input (chat, YAML, sketch) into 1–3 sentences capturing the essence of the piece. No vagueness allowed. | `intent.md` |
| **2. Architectural Sketch** | Draw the time-axis trajectories (tension, density, valence, predictability). No notes yet. | `trajectory.yaml` |
| **3. Skeletal Generation** | Composer generates 5–10 candidate seed melodies + chord skeletons. ~60% completeness suffices. | Candidate ScoreIRs |
| **4. Critic–Composer Dialogue** | Adversarial Critic attacks every candidate. Producer chooses the strongest, or instructs synthesis of a new candidate that combines strengths. | Selected ScoreIR |
| **5. Detailed Filling** | Harmony / Rhythm / Orchestrator fill in voicings, countermelodies, fills, dynamics. Every choice is recorded in provenance. | Full ScoreIR |
| **6. Listening Simulation** | The Perception Substitute Layer "listens" to the result and compares against intent. Sections that exceed the divergence threshold are regenerated. | `critique.md`, `evaluation.json` |

The same six-phase protocol is executed identically by all three surfaces. The SDK additionally emits a `PhaseStartedEvent` / `PhaseCompletedEvent` per phase so UIs can show progress.

---

## 7. Parameter Specification

Each YaO project is described by **eight YAML/JSON files**, all version-controllable so `git diff` works on music:

| File | Purpose | Authoring |
|---|---|---|
| `intent.md` | 1–3-sentence statement of essence | Human or Phase 1 |
| `composition.yaml` | Key, tempo, time signature, form, instruments, sections | Human or `/sketch` |
| `trajectory.yaml` | Tension / density / valence / predictability over time | Phase 2 |
| `references.yaml` | Positive (emulate) and negative (avoid) reference works | Human |
| `negative-space.yaml` | Rests, frequency gaps, textural subtractions | Human or Phase 5 |
| `arrangement.yaml` | (Arrange mode only) preserve / transform / avoid axes | Human |
| `production.yaml` | LUFS target, stereo width, reverb amount | Human |
| `provenance.json` | Append-only decision log | **Auto-generated, hand-edits forbidden** |

Trajectory specifications support three curve types — `bezier` (smooth), `stepped` (per-section flat), and `linear` (target with allowed variance) — with values in `[0.0, 1.0]`.

---

## 8. Custom Commands and SDK Methods

The user invokes the orchestra through **slash commands** (in Claude Code, defined in `.claude/commands/*.md`) or **`YaoAgent` methods** (in the SDK). The two are 1-to-1 by design: anyone fluent in slash commands can drive YaO from Python without learning a new vocabulary.

| Slash command | `YaoAgent` method | Primary subagent | What it does |
|---|---|---|---|
| `/sketch <description>` | `agent.sketch(desc)` | Producer | Interactive spec creation |
| `/compose <project|desc>` | `agent.compose(spec_or_desc)` | All seven | Generate one iteration via the Conductor loop |
| `/conduct <project|desc>` | `agent.conduct(spec_or_desc, max_iterations=3)` | All seven | Generate, evaluate, adapt, regenerate until quality passes |
| `/critique [iteration]` | `agent.critique(iteration)` | Adversarial Critic | Severity-ranked critique markdown |
| `/regenerate-section <section>` | `agent.regenerate_section(section, seed=…)` | Composer + Producer | Replace one section, preserve the rest |
| `/render [iteration]` | `agent.render(iteration)` | Mix Engineer | MIDI → WAV via FluidSynth |
| `/diff <iter_a> <iter_b>` | `agent.diff(a, b)` | (verify layer) | Musical diff with modified-note tracking |
| `/explain <query>` | `agent.explain(query)` | Producer (provenance) | Trace any decision back to its rationale |
| `/evaluate [iteration]` | `agent.evaluate(iteration)` | (verify layer) | Re-run quality scoring |
| `/arrange <project>` *(planned)* | `agent.arrange(project, …)` | Orchestrator + Critic | Reharmonize / regroove / reorchestrate |
| (free-form) | `agent.chat(prompt)` | All seven | Anything the orchestra can do |

The free-form `chat` method matches the experience of talking to Claude Code directly — describe what you want in natural language and the orchestra figures out which steps to take.

---

## 9. Skills

`.claude/skills/` holds structured knowledge modules referenced by Subagents. There are four categories:

- **Genres** — typical chord progressions, drum patterns, instrument combos, representative reference works, clichés to avoid.
- **Theory** — voice leading, counterpoint, reharmonization, modal interchange, with exception rules and genre dependencies explicit.
- **Instruments** — range, idiomatic playing techniques, timbre characteristics, physical constraints, signature phrase patterns.
- **Psychology** — empirical mappings from Juslin, Huron, Krumhansl: tempo↔arousal, mode↔valence, spectral centroid↔perceived brightness.

The Agent SDK loads skills automatically via `skills="all"` (or a whitelist for context-budget-constrained deployments). The Skill tool remains available so unloaded skills can be invoked on demand.

---

## 10. Hooks

Hooks make non-negotiable behaviors **infrastructure rather than discipline**. They run regardless of agent forgetfulness. YaO has **four standard hooks**, registered in two parallel forms:

- **For Claude Code and CLI development workflows:** shell scripts under `.claude/hooks/`.
- **For the Agent SDK:** Python callbacks in `yao.sdk.hooks` registered via `HookMatcher`.

Both forms enforce the same four guarantees:

| Hook | When it fires | What it does |
|---|---|---|
| `pre-compose-validate` | Before `yao_compose` / `yao_conduct` | Validates spec via Pydantic; blocks the call if invalid |
| `post-iteration-provenance` | After any iteration-mutating tool | Appends a provenance event to the iteration's `provenance.json` |
| `post-compose-render` | After `yao_compose` / `yao_conduct` | Renders MIDI → WAV if a SoundFont is available |
| `post-compose-critique` | After `yao_compose` | Auto-invokes the Adversarial Critic |

The Python form has access to the in-process `Conductor` and runs without subprocess overhead.

---

## 11. MCP Integration

YaO connects to the broader Model Context Protocol ecosystem in two complementary ways.

### 11.1 In-process MCP server (Agent SDK only)
A built-in MCP server named `yao` is created via `create_sdk_mcp_server()` and registered in `default_yao_options()`. It exposes ~15 in-process tools that wrap every CLI verb plus a few primitives the agent loop needs:

- `yao_compose`, `yao_conduct`, `yao_critique`, `yao_regenerate_section`, `yao_render_audio`
- `yao_evaluate`, `yao_diff`, `yao_explain`
- `yao_validate_spec`, `yao_load_spec`, `yao_new_project`
- `yao_list_iterations`, `yao_read_iteration`
- `yao_arch_lint`, `yao_run_tests` *(useful for SDK-driven contributors)*

Because the server runs in the same process as the SDK client, there is no serialization between tool calls; the Conductor singleton, the provenance log, and the in-memory ScoreIR are all shared.

### 11.2 External MCP servers
YaO is designed to integrate with external MCP servers for capabilities that need their own runtimes:

| External MCP | Purpose |
|---|---|
| **DAW (Reaper preferred)** | Read/write project files, auto-layout tracks |
| **Sample libraries** | Search and fetch drum samples, one-shots, loops |
| **Reference catalog** | Query rights-cleared reference metadata + extracted features |
| **MIDI controllers** | Live improvisation input |
| **SoundFont/VST servers** | Timbre rendering |
| **Cloud storage** | Backup and team sharing of artifacts |

External servers use stdio or HTTP transports; the in-process server uses the SDK transport. No surface mixes the two.

---

## 12. Quality Evaluation

YaO scores every iteration on **five dimensions**, each with numerical targets and tolerance ranges:

### 12.1 Structure
Section contrast, climax position, density-curve fit, repetition balance, loopability.

### 12.2 Melody
Range fit, motif memorability, singability (leap distribution), phrase closure, contour variation.

### 12.3 Harmony
Functional integrity, tension–resolution shape, complexity match against spec, cadence strength.

### 12.4 Arrangement (when in arrange mode)
Instrument-role clarity, frequency-collision risk, original-preservation ratio, transformation strength.

### 12.5 Acoustics
BPM match, beat stability, LUFS target, spectral balance, onset density.

When any score falls outside its tolerance, the Adversarial Critic is invoked automatically and the Conductor adapts the spec for the next iteration.

---

## 13. The SDK Surface in Detail

The Agent SDK surface adds programmatic agentic access to YaO. It is **not** a separate engine — it is one of three peer entry points to the same Conductor and the same seven layers. This section describes its specific design.

### 13.1 Two lanes

We deliberately offer two API lanes:

- **Lane A — `YaoAgent` façade** *(used by ~90% of integrations)*: a single class that pre-configures the SDK for music production and exposes one method per slash command. Five lines suffice for most tasks.
- **Lane B — Raw SDK + `default_yao_options`** *(used by hosting platforms)*: the user constructs `ClaudeAgentOptions` manually, optionally overriding hooks, permissions, or the system prompt, and uses `query()` or `ClaudeSDKClient` directly.

Both lanes load the same `.claude/` directory, register the same in-process MCP server, and call the same Conductor.

### 13.2 Default Agent SDK options

`yao.sdk.default_yao_options(project)` returns a `ClaudeAgentOptions` with:

- `system_prompt={"type": "preset", "preset": "claude_code"}` — same prompt as Claude Code.
- `setting_sources=["project"]` — loads `.claude/` and `CLAUDE.md`.
- `mcp_servers={"yao": create_yao_mcp_server()}` — registers the in-process server.
- `agents=yao_agent_definitions()` — programmatic mirrors of the seven Subagents.
- `hooks=default_yao_hooks()` — auto-render, auto-critique, auto-provenance, pre-validate.
- `can_use_tool=default_yao_permission()` — refuses destructive operations on protected paths.
- `permission_mode="acceptEdits"` — autonomous edits within the project root.
- `effort="high"` — composition is reasoning-heavy by default.
- `skills="all"` — preload all four skill categories.

Power users override any of these via `extra_options`.

### 13.3 Streaming events

The SDK exposes a stream of typed events that mirror the six-phase protocol and the Conductor loop:

| Event | When emitted |
|---|---|
| `PhaseStartedEvent` | At the start of each of the six cognitive phases |
| `PhaseCompletedEvent` | At the end of each phase |
| `SubagentStartedEvent` | When a Subagent begins working |
| `IterationCompletedEvent` | After each Conductor iteration |
| `EvaluationReportEvent` | When `evaluation.json` is written |
| `CritiqueAvailableEvent` | When `critique.md` is written |
| `AudioReadyEvent` | When WAV rendering finishes |
| `ProvenanceUpdatedEvent` | After every provenance append |
| `ConductorFinishedEvent` | At the end of a `conduct()` run |

UIs subscribe to this stream to show progress at the granularity composers care about.

### 13.4 Structured outputs

Every SDK method that returns user-visible data uses `output_format={"type": "json_schema", "schema": …}` to guarantee well-typed results: `ComposeResult`, `ConductResult`, `CritiqueResult`, etc., all defined as Pydantic models. Front-ends consume them directly; no regex parsing of free text.

### 13.5 Permission policies for music production

A music session has narrower destructive boundaries than general coding. The default permission callback **denies** writes to:

- `outputs/projects/<name>/iterations/v*/` (iterations are append-only forever)
- `references/` (reference works are precious)
- `.claude/agents/`, `.claude/commands/`, `.claude/skills/` (dev-time concerns, not music-time)
- `CLAUDE.md`

It also denies Bash commands containing `rm -rf` against any protected directory. Users can override with `permission_mode="default"` (interactive approvals) or supply a custom `can_use_tool` for unusual deployments.

### 13.6 Sessions

Sessions are SDK-native: `list_sessions()`, `resume`, `fork_session=True`, `tag_session()`. YaO conventions add:

- One session directory per project, keyed by absolute project path.
- Auto-tagging: a finished session is tagged with the iteration it ended on (`v003`).
- Forks: when a user wants to explore "what if the bridge were in a different key," `fork_session=True` creates a branch tagged `fork-of-<original>`.

For team deployments, `session_store` mirrors transcripts to S3/Postgres.

### 13.7 Five parity guarantees (G1–G5)

Tests in `tests/sdk/integration/test_compose_parity.py` enforce that the same prompt produces identical (or musically equivalent for stochastic seeds) artifacts across all surfaces:

- **G1 — Same files:** All surfaces load `.claude/` and `CLAUDE.md` identically.
- **G2 — Same subagent reasoning:** Markdown definitions and Python mirrors produce identical traces.
- **G3 — Same Conductor loop:** Every surface calls `yao.conductor.Conductor`; no surface reimplements the loop.
- **G4 — Same provenance and outputs:** Identical paths and JSON schema across surfaces.
- **G5 — Same constraint and lint guarantees:** Identical music-lint and constraint-check results.

A failure of any G* test blocks release.

---

## 14. Hosted Application Patterns

The SDK enables four canonical applications, each with a minimal reference implementation in `examples/sdk/` and an integration test in CI.

### 14.1 Web app
A FastAPI server wraps `YaoAgent`. The browser front-end shows one progress card per cognitive phase, plus a play button when audio is ready. Streaming via Server-Sent Events. ~250 lines.

### 14.2 Discord/Slack bot
A bot listens for `!compose <description>`, calls `YaoAgent.conduct()`, replies with the WAV file and the critique markdown. Permission policy is locked down hard (no Bash, no Edit outside `outputs/`). ~150 lines.

### 14.3 CI music generation
A GitHub Action runs on push to a game-content repo. It reads `levels/*.yaml`, generates one YaO spec per level, and produces stems + WAV in a release artifact. Demonstrates `permission_mode="bypassPermissions"` in a sandboxed runner. ~100 lines.

### 14.4 Jupyter notebook
`yao_in_jupyter.ipynb` shows inline `display(Audio(wav_path))`, plots evaluation scores across iterations with matplotlib, and embeds the `YaoEvent` stream as a tqdm progress bar.

---

## 15. Quickstart: Four Ways to Use YaO

### 15.1 Setup

```bash
git clone https://github.com/shibuiwilliam/YouAndOrchestra.git
cd YouAndOrchestra
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,sdk]"
make setup-soundfonts                # one-time SoundFont setup
export ANTHROPIC_API_KEY=sk-…        # for Agent SDK
```

### 15.2 Path 1 — Natural-language CLI

```bash
yao conduct "a calm piano piece in D minor for studying, 90 seconds"
```

### 15.3 Path 2 — YAML CLI

```bash
yao new-project rainy-cafe
# edit specs/projects/rainy-cafe/composition.yaml
yao conduct --spec specs/projects/rainy-cafe/composition.yaml --project rainy-cafe
```

### 15.4 Path 3 — Claude Code (interactive)

```bash
claude                                # in the YaO directory
> /sketch a mysterious puzzle game BGM
> /compose
> /critique
> /regenerate-section bridge
```

### 15.5 Path 4 — Agent SDK (programmatic)

```python
import asyncio
from yao.sdk import YaoAgent
from yao.sdk.events import IterationCompletedEvent, AudioReadyEvent

async def main():
    async with YaoAgent(project="rainy-cafe") as agent:
        async for event in agent.conduct(
            "a rainy-cafe BGM with piano and cello, melancholy",
            max_iterations=3,
        ):
            if isinstance(event, IterationCompletedEvent):
                print(f"iter {event.iteration} -> {event.iteration_path}")
            elif isinstance(event, AudioReadyEvent):
                print(f"audio: {event.wav_path}")

asyncio.run(main())
```

All four paths produce **identical artifacts** at `outputs/projects/rainy-cafe/iterations/v00N/`.

---

## 16. File Formats and Interoperability

YaO commits to industry-standard formats:

| Use | Format | Why |
|---|---|---|
| Music data | MIDI (`.mid`), MusicXML (`.xml`) | Industry standard; every DAW reads them |
| Notation | LilyPond (`.ly`), PDF | High-quality, automatable |
| Specifications | YAML | Human-readable, git-friendly |
| Intermediate representation | JSON | Programmatic, schema-validated |
| Provenance | JSON | Graph-friendly |
| Audio | WAV (production), FLAC/MP3 (distribution) | Universal |
| Live coding | Strudel pattern strings | Browser-playable |

Custom formats are introduced only when no standard suffices.

---

## 17. Ethics and Licensing

### 17.1 Training data and references
The reference library accepts **rights-cleared works only**. Each entry in `references/catalog.yaml` records its license; works with unknown status are not used.

### 17.2 Artist imitation
Naming a living artist as a target style is discouraged. Use **abstract feature descriptions** instead:

- ✗ "In the style of Joe Hisaishi"
- ✓ "Wide open string voicings, ascending motifs, major/minor flux, meditative tempo"

### 17.3 Generated rights
Music produced with YaO belongs to the user. When a single reference dominates the influence vectors, YaO emits a warning.

### 17.4 Transparency
Every artifact records "produced with YaO" plus the influencing aesthetic anchors in `provenance.json`. We recommend disclosure when distributing.

---

## 18. Document Hierarchy

| File | Audience | Purpose |
|---|---|---|
| `PROJECT.md` (this file) | Humans + agents | Full design, philosophy, architecture |
| `CLAUDE.md` | Agents (primarily) | Invariant rules, forbidden patterns, surface guides |
| `README.md` | New users | Quickstart, minimal usage |
| `docs/design/*.md` | Both | Individual design decision records (ADR-style) |
| `docs/sdk/*.md` | SDK users + agents | SDK-specific API reference and deployment |
| `.claude/guides/*.md` | Developing agents | Detailed dev guides referenced by CLAUDE.md |
| `development/*.md` | Developers | Internal technical docs |
| `mkdocs.yml` site | End users | Published documentation |

---

## 19. Roadmap

### 19.1 Technical phases (engine + surface)

| Phase | Duration | Deliverables |
|---|---|---|
| **Phase 0 — Bootstrap** | ✅ done | Project layout, CLAUDE.md, MVP MIDI generation |
| **Phase 1 — Symbolic composition** | ✅ done | Eight-spec parameter system, Conductor, two generators, evaluation, CLI, slash commands, four skills |
| **Phase 2A — SDK foundation** | 1–2 weeks | In-process MCP server, `default_yao_options`, Lane B raw access |
| **Phase 2B — SDK Lane A façade** | 1–2 weeks | `YaoAgent` class, streaming events, typed results |
| **Phase 2C — SDK hooks/permissions** | 1 week | Auto-render, auto-critique, auto-provenance, protected-path enforcement |
| **Phase 2D — Programmatic subagents** | 1 week | `yao_agent_definitions()`, parser tests, parity G2 |
| **Phase 2E — Sessions / streaming polish** | 1 week | Project-scoped sessions, JSON-Schema outputs, back-pressure |
| **Phase 2F — Reference applications** | 2 weeks | Web, Discord, CI, notebook, all in CI |
| **Phase 2G — Docs and SDK preview release** | 1 week | `docs/sdk/`, README path 4, CLAUDE.md SDK section |
| **Phase 3 — Arrangement engine + Style Vector** | 1 month | `/arrange`, reharmonization, regrooving, reorchestration |
| **Phase 4 — Perception layer + critique** | 1 month | Reference matching, psychology mapping, multi-resolution trajectory |
| **Phase 5 — Production integration** | 2–3 months | DAW (Reaper) MCP, AI music model bridges, live improvisation |
| **Phase 6 — Reflection & learning** | ongoing | User-style profiles, community reference sharing |

### 19.2 User-value milestones

| Milestone | User-facing value | Required features |
|---|---|---|
| **1. Describe & Hear** | "Describe in YAML, hear immediately" | CLI compose, two generators, templates, auto-versioning |
| **2. Iterate & Improve** | "Tell it what's wrong, get an improvement" | Score diff, evaluation, `/critique`, section regeneration |
| **3. Richer Music** | "Pro-quality harmony, rhythm, dynamics" | Harmony IR, constraints, walking bass, syncopation |
| **4. My Style** | "Learns my taste, generates in my voice" | Reference matching, style profile, spec composition |
| **5. Production Ready** | "Usable in real projects" | DAW integration, multi-format export, mix engineer |
| **6. Anywhere YaO Goes** | "Driveable from any program in any language" | **SDK in production: web apps, bots, CI, batch services** |

### 19.3 Strategic insight

YaO's design pattern is, beneath the music, a **general framework for structured human-AI creative collaboration**. The `Surface ↔ Engine ↔ Layers` decomposition we use here generalizes:

| YaO pattern | General pattern | Other domains |
|---|---|---|
| Score (YAML) | **Intent-as-Code** | UI design, narrative structure, game-level design |
| Trajectory | **Time-axis quality curves** | Video pacing, presentation flow, UX journeys |
| Adversarial Critic | **Adversarial review** | Code review, design critique, writing feedback |
| Provenance Graph | **Decision genealogy** | All AI-assisted creative work |
| 6-phase protocol | **Structured creative protocol** | Any domain where "don't jump to implementation" matters |
| **Three surfaces / one engine** | **Surface ↔ Engine ↔ Layers** | Any system that needs interactive, scriptable, and programmatic access |

These abstractions are designed for future extraction; current scope remains music.

### 19.4 Development culture

- **Sound-first culture:** Changes that affect generation or rendering must include before/after audio samples in the PR.
- **Documentation budget:** Maintain ≥ 3 lines of working code per 1 line of design documentation.
- **Dogfooding:** Music made with YaO is used in our demo videos and presentations.
- **Contribution paths for musicians:** Genre skills, templates, and reference analyses are Python-free contribution paths.
- **Surface parity is non-negotiable:** Every PR that touches any surface runs G1–G5 in CI.

---

## 20. Future Architectural Extensions

### 20.1 Session/project runtime layer
The SDK already covers the session use case. A future enhancement is to add a **`ProjectRuntime`** that caches per-section regeneration, manages a feedback queue (critique → revision loop), and supports musical undo/redo across iterations.

### 20.2 Abstract agent protocol
The seven Subagents are currently coupled to Claude Code via Markdown and to the SDK via Python `AgentDefinition`. A backend-neutral Python protocol (`AgentRole`, `AgentContext`, `AgentOutput`) would let other agentic backends (e.g., other LLMs or future Anthropic platforms) be plugged in. Claude Code becomes one adapter; the SDK becomes another.

### 20.3 Real-time feedback paths
The current YAML → MIDI → WAV → external player pipeline has too much latency for live work. Future work:

- `yao preview` command for inline MIDI playback
- Strudel pattern emission for browser-based real-time auditioning
- `sounddevice` direct WAV playback

### 20.4 Spec composition
Reusable spec fragments under `specs/fragments/` with `extends:` / `overrides:` keys for spec composition.

### 20.5 Live improvisation mode
A `/improvise` flow that listens to MIDI input via an external MCP server and the in-process MCP server emits accompaniment in real time.

---

## 21. Glossary

**Conductor** — the human owner of the project; final authority.
**Engine** — the seven-layer musical core (`yao.conductor` plus layers 0–7).
**Surface** — one of three peer entry points: Claude Code, CLI, Agent SDK.
**Score** — the YAML specifications under `specs/`.
**ScoreIR** — frozen-dataclass intermediate representation of a score.
**Trajectory** — a time-axis curve over a musical attribute (tension, density, etc.).
**Aesthetic Reference Library** — the rights-cleared works in `references/`.
**Perception Substitute Layer** — Layer 4, which compensates for AI's inability to actually hear.
**Provenance** — the append-only, queryable log of every generation decision.
**Adversarial Critic** — the never-praising Subagent that hunts for weaknesses.
**Negative Space** — the deliberately-silent parts of a piece.
**Style Vector** — multi-dimensional feature representation of genre/style.
**Iteration** — a versioned generation under `outputs/projects/<name>/iterations/v<NNN>/`.
**Music Lint** — automated detection of theory and constraint violations.
**Sketch-to-Spec** — the dialogue that turns natural language into a YAML spec.
**Lane A** — high-level SDK access via `YaoAgent`.
**Lane B** — low-level SDK access via raw `query()` / `ClaudeSDKClient` plus `default_yao_options()`.
**`YaoAgent`** — the high-level Agent SDK façade class.
**In-process MCP server** — the `yao` MCP server registered via `create_sdk_mcp_server()`.

---

## 22. Closing

YaO does not aim to be "the AI that makes music." It aims to be **the place where humans and AI make music together**, and to make that place reachable from anywhere.

- Humans bring **intent, taste, and soul.**
- AI brings **theory knowledge, iteration speed, and exhaustive recordkeeping.**
- YaO provides **the structured collaborative process** that turns the two into a piece of music.

Whether the conductor is a hobbyist on a laptop typing slash commands, a developer wiring `YaoAgent` into a Discord bot, or a CI pipeline regenerating game music on every push — they are conducting **the same orchestra**, in different venues. Great music remains, in the end, an expression of the human soul. YaO exists to make that expression **faster, deeper, and reproducible.**

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve, anywhere you need it.*

---

**Project:** You and Orchestra (YaO)
**Document:** PROJECT.md
**Document version:** 2.0 (SDK Surface integrated)
**Last updated:** 2026-05-10
