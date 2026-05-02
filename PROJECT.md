# You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

> **Document version**: 2.0
> **Last updated**: 2026-05-02
> **Status**: This document supersedes PROJECT.md v1.0. It preserves the original design philosophy and metaphor while integrating concrete improvements identified through Phase 1 retrospective and gap analysis. For what works today, see [FEATURE_STATUS.md](./FEATURE_STATUS.md). For development rules, see [CLAUDE.md](./CLAUDE.md).

---

## 0. プロジェクトの本質

**You and Orchestra (YaO)** は、Claude Code を基盤として動作する **エージェント型音楽制作環境** です。一般的な「AI作曲ツール」とは異なり、YaO は単一のブラックボックスから音楽を吐き出すのではなく、**役割分担された複数の AI エージェント(Orchestra Members)を、人間(You = Conductor)が指揮する**という構造を取ります。

YaO のすべての設計は、次のひとつの命題に従属します。

> **音楽制作とは、感覚的な一回限りの作業ではなく、再現可能で改善可能な創作エンジニアリングである。**

このため YaO は、音楽を **音声ファイル**として扱う前に、**コード・仕様・テスト・差分・来歴**として扱います。これを Music-as-Code 哲学と呼びます。

### 0.1 v2.0 で目指す質的飛躍

v1.0 は「音楽制作をエンジニアリング規律下に置く」という第一の戦いに勝利しました。643 テスト、7 層厳格境界、MPIR(Musical Plan IR)、15 批評ルール、5 次元軌跡 — これらは商用ソフトウェアでも見られない水準です。

v2.0 は次の戦いに向かいます。

> **エンジニアリング規律を保ちながら、音楽として優れた多様性のある作品を生む。**

この戦いの勝利条件は 3 つです。

1. **音楽性の天井突破** — 構造指標を満たした上で、聴いて感動する楽曲を出す
2. **多様性の地理的・歴史的拡大** — 西洋ダイアトニック・12 平均律・4/4 という暗黙の前提を解除
3. **差別化要素の実体化** — Arrangement Engine、Perception Layer、Neural Integration、Live Improvisation を stub から実装へ

---

## 1. メタファー:You and Orchestra

YaO のすべての概念は、オーケストラの比喩に対応しています。この対応関係を内面化することが、YaO を正しく使う最短距離です。

| YaO の構成要素 | オーケストラの比喩 | 実装上の対応 |
|---|---|---|
| **You** | 指揮者 (Conductor) | プロジェクト所有者である人間 |
| **Score** | 楽譜 | `specs/*.yaml` に記述された作曲仕様 |
| **Plan** | リハーサル計画 | `MusicalPlan` (MPIR) — 音符の前の "なぜ" |
| **Orchestra Members** | 楽団員 | 各 Subagent(Composer, Critic, Theorist 等) |
| **Concertmaster** | コンサートマスター | Producer Subagent(全体調整役) |
| **Rehearsal** | リハーサル | 生成・評価・修正の反復ループ |
| **Library** | 楽団の楽譜庫 | `references/` 内の参照楽曲群 |
| **Performance** | 本番演奏 | レンダリングされた最終音源 |
| **Recording** | 録音 | `outputs/` 内の成果物 |
| **Critic / Reviewer** | 批評家 | Adversarial Critic Subagent |
| **Listener Panel** | 試聴会 | Perception Layer + ユーザフィードバック |
| **Cover Band** | カバー・編曲 | Arrangement Engine |

指揮者(You)はすべての音符を書くわけではありません。指揮者の仕事は、**意図を明確化し、楽団員に方向性を示し、リハーサルで判断を下し、本番の質を担保する**ことです。YaO はこの分業を AI に持ち込みます。

---

## 2. 設計原則

YaO のあらゆる実装判断は、以下の **6 つの不変原則** に照らして決定されます。これらは CLAUDE.md にも転記され、エージェントの判断基準として機能します。

v1.0 の 5 原則に、**第 6 原則「Vertical Alignment(垂直整合)」** を追加しました。

### 原則 1:エージェントは作曲家ではなく、作曲環境である
YaO は「曲を書く AI」ではなく、「人間の作曲を 10 倍速にする環境」を志向します。完全自動化ではなく、人間の創造的判断を加速・拡張することを目的とします。

### 原則 2:すべての判断に説明可能性を要求する
生成された音符・コード・編曲判断のすべてに、「なぜそうしたのか」という理由が記録されます。これは Provenance Graph として永続化され、追跡・レビュー・修正が可能です。

### 原則 3:制約は創造性を殺さず、むしろ解放する
明示的な仕様(YAML)・参照ライブラリ・否定空間(Negative Space)などの制約は、創造の足枷ではなく足場として機能します。無制限の自由は麻痺を生みます。

### 原則 4:時間軸の設計を音符の設計から分離する
楽曲は最初に「時間軸上の軌跡」(緊張度・密度・感情価のカーブ)として設計され、音符はその後に埋められます。これにより、構造的に意味のある音楽が生まれます。

### 原則 5:人間の耳を最後の真実とする
どれだけ自動評価指標が精緻でも、人間の聴取体験が最終判断者です。エージェントは判断を**置き換えるのではなく支援**します。

### 原則 6:垂直整合(Vertical Alignment)
**入力の表現力・処理の深度・評価の解像度は、共に進歩しなければならない。一つだけ深めても無駄になる。**

これは v1.0 設計レビューから抽出された原則です。リッチな DSL を作っても処理が貧弱なら無意味、優れた評価器を作っても入力が単純なら無意味、強力な生成器を作っても評価できなければ無意味。3 層を **同期して進化** させることをコミットします。

| 層 | 問いかけ |
|---|---|
| **入力** | 仕様は望むものを表現できるか? |
| **処理** | パイプラインは意図を計画に、計画を音符に変換できるか? |
| **出力** | 同じ精度で結果を評価・批評できるか? |

リリースごとに 3 層が同時に進歩することを保証します。

---

## 3. アーキテクチャ:8 層モデル

YaO は明確に分離された 8 つの層で構成されます。各層は独立した入出力契約を持ち、交換・テスト可能です。v1.0 の 7 層モデルに **Layer 4.5: Performance Expression** を追加し、より細密な音楽表現を可能にしました。

```
┌─────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                      │
│   制作履歴からの学習、ユーザ嗜好プロファイル更新       │
├─────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                    │
│   構造・和声・リズム・音響評価、敵対的批評(50+ ルール) │
├─────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                  │
│   MIDI / 音声 / 楽譜PDF / DAWプロジェクト / Strudel  │
├─────────────────────────────────────────────────────┤
│ Layer 4.5: Performance Expression  ★NEW             │
│   Articulation / Dynamics curve / Microtiming / CC  │
├─────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                      │
│   Audio Features / Use-Case Eval / Reference Match  │
├─────────────────────────────────────────────────────┤
│ Layer 3.5: Musical Plan IR (MPIR)                   │
│   SongFormPlan / HarmonyPlan / MotifPlan / etc.     │
├─────────────────────────────────────────────────────┤
│ Layer 3: Score IR                                   │
│   Note / Part / Section / Voicing / Timing          │
├─────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                        │
│   8+ generators (rule, stochastic, markov, neural,  │
│                  serial, spectral, process, L-sys)   │
├─────────────────────────────────────────────────────┤
│ Layer 1: Specification                              │
│   YAML 仕様 v2 / 対話 / スケッチ / Spec composability│
└─────────────────────────────────────────────────────┘
```

層間の依存は厳密に下から上へのみ流れます。AST ベースの `make arch-lint` で機械的に検証されます。

### 3.1 主要データフロー

```
[Spec] → [Plan Generators] → [MPIR] → [Critic Gate] → [Note Realizers] → [Score IR]
            ↓                    ↓                            ↓
       [Provenance]         [Critique]                [Performance Layer]
                                                            ↓
                                                     [Rendering]
                                                            ↓
                                                     [Audio / MIDI / Score]
                                                            ↓
                                                     [Perception Layer]
                                                            ↓
                                                  [Listening Simulation]
                                                            ↓
                                                  [Feedback to Conductor]
```

### 3.2 Critic Gate(批評関門)

Layer 3.5 から Layer 3 への遷移時、**Adversarial Critic は MPIR レベルで動作** します。これは v1.0 からの大きな改善です。音符レベルではなく計画レベルで批評することで、「丁寧に実現された退屈な計画」を防ぎます。

Critic Gate での選択肢:
- **承認**: Note Realizer に進む
- **計画レベル修正の提案**: Step 1〜5 のいずれかにループバック
- **計画の却下**: 異なる候補を要求(Multi-Candidate モード)

---

## 4. ディレクトリ構造

v1.0 の構造を踏襲しつつ、新規層・新規機能を反映します。

```
yao/
├── CLAUDE.md                      # エージェントへの不変指示
├── PROJECT.md                     # 本ファイル(プロジェクト全体設計)
├── VISION.md                      # 目標アーキテクチャ
├── FEATURE_STATUS.md              # 単一の真実 = 何が実装済か
├── README.md                      # ユーザ向けクイックスタート
├── pyproject.toml
├── Makefile
│
├── .claude/
│   ├── commands/                  # Custom Commands (15+)
│   │   ├── compose.md
│   │   ├── arrange.md             # ★Phase 2 で実装
│   │   ├── critique.md
│   │   ├── morph.md
│   │   ├── improvise.md           # ★Phase 4 で実装
│   │   ├── explain.md
│   │   ├── regenerate-section.md
│   │   ├── sketch.md
│   │   ├── annotate.md            # ★NEW: ユーザ注釈
│   │   ├── branch.md              # ★NEW: Plan-level branching
│   │   ├── alternatives.md        # ★NEW: 代替案生成
│   │   ├── render.md
│   │   ├── preview.md
│   │   ├── watch.md
│   │   └── diff.md
│   ├── agents/                    # Subagent 定義 (.md prompts)
│   │   ├── composer.md
│   │   ├── harmony-theorist.md
│   │   ├── rhythm-architect.md
│   │   ├── orchestrator.md
│   │   ├── adversarial-critic.md
│   │   ├── mix-engineer.md
│   │   └── producer.md
│   ├── skills/                    # 専門知識モジュール
│   │   ├── genres/                # 30+ ジャンル(v1.0 は 8)
│   │   │   ├── western_popular/
│   │   │   ├── electronic/
│   │   │   ├── classical/
│   │   │   ├── world/             # ★NEW: ノンウェスタン
│   │   │   └── functional/        # ★NEW: 用途別
│   │   ├── theory/
│   │   │   ├── voice-leading.md
│   │   │   ├── reharmonization.md
│   │   │   ├── counterpoint.md
│   │   │   ├── modal-interchange.md
│   │   │   ├── secondary-dominants.md
│   │   │   ├── twelve-tone.md     # ★NEW
│   │   │   ├── spectralism.md     # ★NEW
│   │   │   └── microtonal.md      # ★NEW
│   │   ├── instruments/           # 38+ 楽器、各 Skill
│   │   │   ├── orchestral/
│   │   │   ├── popular/
│   │   │   ├── electronic/
│   │   │   └── world/             # ★NEW: 民族楽器
│   │   ├── psychology/
│   │   │   ├── tension-resolution.md
│   │   │   ├── emotion-mapping.md
│   │   │   ├── memorability.md
│   │   │   └── prediction-itpra.md  # ★NEW: Huron 予測理論
│   │   └── articulation/          # ★NEW: 演奏表情
│   │       ├── strings-articulation.md
│   │       ├── winds-articulation.md
│   │       ├── piano-pedaling.md
│   │       └── jazz-microtiming.md
│   ├── guides/                    # 開発者ガイド
│   │   ├── architecture.md
│   │   ├── coding-conventions.md
│   │   ├── music-engineering.md
│   │   ├── testing.md
│   │   ├── workflow.md
│   │   └── cultural-sensitivity.md  # ★NEW
│   └── hooks/
│       ├── pre-commit-lint.sh
│       ├── post-generate-render.sh
│       ├── post-generate-critique.sh
│       ├── update-provenance.sh
│       ├── spec-changed-show-diff.sh
│       └── ai-disclosure-stamp.sh   # ★NEW: AI 生成明示
│
├── specs/
│   ├── projects/                  # ユーザのプロジェクト
│   ├── templates/                 # 既製テンプレート(v1, v2, v3)
│   └── fragments/                 # ★NEW: Spec composability
│       ├── instruments/
│       ├── genres/
│       ├── trajectories/
│       └── intents/
│
├── src/
│   └── yao/
│       ├── conductor/             # オーケストレーション
│       ├── constants/             # 38 楽器、14+ スケール、14+ コード
│       ├── schema/                # Pydantic v2 + composability
│       ├── ir/
│       │   ├── score_ir.py
│       │   ├── plan/              # MPIR (Layer 3.5)
│       │   │   ├── form.py
│       │   │   ├── harmony.py
│       │   │   ├── motif.py
│       │   │   ├── phrase.py
│       │   │   ├── drum.py
│       │   │   ├── arrangement.py
│       │   │   └── musical_plan.py
│       │   ├── expression.py      # ★NEW: Layer 4.5
│       │   ├── timing.py
│       │   ├── notation.py
│       │   └── motif.py
│       ├── generators/
│       │   ├── rule_based.py
│       │   ├── stochastic.py
│       │   ├── markov.py          # ★Tier 1
│       │   ├── constraint_solver.py  # ★Tier 1
│       │   ├── twelve_tone.py     # ★Tier 3
│       │   ├── spectral.py        # ★Tier 3
│       │   ├── process_music.py   # ★Tier 3
│       │   ├── l_system.py        # ★Tier 3
│       │   ├── cellular_automata.py  # ★Tier 3
│       │   ├── neural/            # ★Tier 3
│       │   │   ├── magenta_bridge.py
│       │   │   ├── musicgen_bridge.py
│       │   │   └── stable_audio_bridge.py
│       │   ├── plan/              # Plan-level generators
│       │   ├── note/              # Note Realizers
│       │   └── performance/       # ★NEW: Performance Layer
│       │       ├── articulation_realizer.py
│       │       ├── dynamics_curve_renderer.py
│       │       ├── microtiming_injector.py
│       │       └── cc_curve_generator.py
│       ├── perception/            # ★Tier 1-2 で本格実装
│       │   ├── audio_features.py
│       │   ├── use_case_evaluator.py
│       │   ├── reference_matcher.py
│       │   ├── style_vector.py
│       │   └── psych_mapper.py
│       ├── render/
│       │   ├── midi_writer.py
│       │   ├── stems_writer.py
│       │   ├── audio_renderer.py
│       │   ├── musicxml_writer.py    # ★Tier 1
│       │   ├── lilypond_writer.py    # ★Tier 1
│       │   ├── strudel_emitter.py    # ★Tier 3
│       │   └── daw/                  # ★Tier 2
│       │       ├── reaper_writer.py
│       │       ├── ableton_writer.py
│       │       └── studio_one_writer.py
│       ├── mix/                   # ★Tier 1: Mix Chain
│       │   ├── mix_chain.py
│       │   ├── eq.py
│       │   ├── compression.py
│       │   ├── reverb.py
│       │   └── master_chain.py
│       ├── arrange/               # ★Tier 2: Arrangement Engine
│       │   ├── extractor.py       # MIDI → SourcePlan (MPIR)
│       │   ├── style_vector_ops.py
│       │   ├── preservation.py
│       │   ├── transformation.py
│       │   ├── diff_writer.py
│       │   └── critique_rules.py  # 編曲特化 Critic ルール
│       ├── verify/
│       │   ├── music_lint.py
│       │   ├── analyzer.py
│       │   ├── evaluator.py       # 拡張(構造+メロディ+和声+ +新次元)
│       │   ├── diff.py
│       │   ├── constraints.py
│       │   ├── critique/          # 50+ ルール(v1.0 は 15)
│       │   │   ├── structural/
│       │   │   ├── melodic/
│       │   │   ├── harmonic/
│       │   │   ├── rhythmic/
│       │   │   ├── arrangement/
│       │   │   ├── emotional/
│       │   │   ├── memorability/   # ★NEW
│       │   │   ├── genre_fitness/  # ★NEW
│       │   │   ├── performance/    # ★NEW
│       │   │   └── mix/            # ★NEW
│       │   └── perception/         # Perception 由来の評価
│       ├── reflect/
│       │   ├── provenance.py
│       │   ├── feedback_loop.py
│       │   ├── style_profile.py   # ★Tier 4: ユーザ別嗜好
│       │   ├── annotation.py      # ★Tier 4: 注釈統合
│       │   └── learning.py        # ★Tier 4: 集約と適用
│       ├── runtime/               # ★Tier 3: ProjectRuntime
│       │   ├── project_runtime.py
│       │   ├── generation_cache.py
│       │   ├── undo_stack.py
│       │   └── feedback_queue.py
│       ├── subagents/             # ★Tier 2: Python 実体
│       │   ├── base.py
│       │   ├── composer.py
│       │   ├── harmony_theorist.py
│       │   ├── rhythm_architect.py
│       │   ├── orchestrator.py
│       │   ├── adversarial_critic.py
│       │   ├── mix_engineer.py
│       │   └── producer.py
│       ├── agents/                # ★Tier 4: Backend-agnostic protocol
│       │   ├── protocol.py
│       │   ├── claude_code_backend.py
│       │   ├── anthropic_api_backend.py
│       │   ├── local_llm_backend.py
│       │   └── python_only_backend.py
│       ├── improvise/             # ★Tier 3: Live mode
│       │   ├── realtime_engine.py
│       │   ├── context_buffer.py
│       │   └── role_handlers.py
│       └── sketch/                # NL → spec
│           ├── compiler.py
│           └── dialogue.py
│
├── references/
│   ├── catalog.yaml
│   ├── midi/                      # 権利クリア済のみ
│   ├── musicxml/
│   └── extracted_features/        # スタイルベクトル事前計算
│
├── outputs/                       # 生成成果物
├── soundfonts/                    # SoundFont
├── drum_patterns/                 # ジャンル別ドラムパターン YAML
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── scenarios/
│   ├── music_constraints/
│   ├── golden/
│   ├── subjective/                # ★NEW: 主観品質テスト
│   │   ├── ratings/
│   │   └── test_listening_panel.py
│   └── properties/                # ★NEW: Property-based
│       ├── test_genre_invariants.py
│       └── test_trajectory_compliance.py
├── tools/
│   ├── architecture_lint.py
│   ├── feature_status_check.py
│   ├── sync_skills.py
│   ├── sync_docs.py               # ★NEW: ドキュメント整合
│   └── benchmark.py               # ★NEW: 性能測定
└── docs/
    ├── design/
    ├── tutorials/
    ├── for-musicians/             # ★NEW
    ├── for-developers/            # ★NEW
    ├── ethics/                    # ★NEW
    │   ├── cultural-sensitivity.md
    │   ├── ai-disclosure.md
    │   └── copyright.md
    └── glossary.md
```

---

## 5. オーケストラの編成:Subagent 設計

YaO の楽団員は **二重実装** されます。`.claude/agents/*.md` は Claude Code 経由の対話用 prompt、`src/yao/subagents/*.py` は自動パイプライン用の Python クラス。両者は同じ `AgentContext` / `AgentOutput` 契約を共有します。

### 5.1 二重実装の理由

v1.0 では Subagent が `.md` ファイルだけで定義されており、Conductor が「Composer がモチーフを作り、Critic が批評する」という流れを **Python 側でどう呼び出すか** が不透明でした。v2.0 では:

- **Python Subagent** = 構造化された判定処理(Critic ルール、ScoreIR 操作)
- **Claude Code prompt** = 創造的判断、自然言語対話、スケッチ→spec 変換

両者を同じインタフェースで扱うことで、自動化と対話の境界が滑らかになります。

```python
# src/yao/subagents/base.py
class SubagentBase(ABC):
    role: AgentRole

    @abstractmethod
    def process(self, context: AgentContext) -> AgentOutput: ...

    def explain(self) -> str:
        """自身の判断ロジックを自然言語で説明する。"""
        ...
```

### 5.2 7 つの楽団員

| Subagent | Owns | Inputs | Outputs |
|---|---|---|---|
| **Composer** | Motifs, phrases, themes | intent, spec, trajectory | MotifPlan, PhrasePlan |
| **Harmony Theorist** | Chord progressions, cadences, modulations | spec, motif plan | HarmonyPlan |
| **Rhythm Architect** | Drum patterns, grooves, microtiming | spec, genre | DrumPattern, GrooveProfile |
| **Orchestrator** | Instruments, voicings, counter-melody, frequency space | all plans above | ArrangementPlan |
| **Mix Engineer** | EQ, compression, reverb, panning, LUFS | spec, ScoreIR, audio stems | ProductionManifest |
| **Adversarial Critic** | Finding weaknesses (50+ rules) | MPIR or ScoreIR or audio | list[Finding] |
| **Producer** | Coordination, conflict resolution, final judgment | all of above + intent | decisions, escalations |

### 5.3 Subagent 設計の不変ルール

- **Composer は楽器を選ばない**: 楽器選択は Orchestrator の責務
- **Critic は称賛しない**: 弱点発見が唯一の使命
- **Producer のみ他者を override 可能**: エージェント間ループの原因を断つ
- **すべての Subagent は Provenance を残す**: 判断の追跡可能性を保つ

### 5.4 Subagent → Pipeline マッピング

```
Step 1 Form Planner       ← Producer (form は meta)
Step 2 Harmony Planner    ← Harmony Theorist
Step 3 Motif Developer    ← Composer
Step 4 Drum Patterner     ← Rhythm Architect
Step 5 Arranger           ← Orchestrator
═══ Critic Gate ═══       ← Adversarial Critic
Step 6 Note Realizer      ← Composer (low-level)
Step 6.5 Performance Realizer ← Composer + Orchestrator (★NEW)
Step 7 Mix Designer       ← Mix Engineer (★NEW: explicit step)
Step 8 Renderer           ← (output writers)
```

---

## 6. 作曲認知プロトコル:6 相 × 8 ステップ

YaO の `/compose` および `/arrange` コマンドは、Claude Code に **6 相の認知プロトコル** を **8 ステップのパイプライン** にマッピングして実行させます。

### 6.1 6 相認知プロトコル

エージェントが「いきなり音符を書き始める」失敗パターンを構造的に防ぎます。

#### Phase 1:Intent Crystallization(意図の結晶化)
ユーザ入力(対話・YAML・スケッチ)から、楽曲の本質を 1〜3 文で言語化します。曖昧さを許さず、`intent.md` に確定させます。

> 例:「初夏の朝、新しい挑戦に向かう前向きな期待感。ただし不安も微かに混じる。爽やかすぎず、感傷的すぎない、ニュートラルな高揚」

#### Phase 2:Architectural Sketch(構造スケッチ)
時間軸軌跡(tension / density / valence / predictability / brightness / register_height)を **先に** 描きます。音符はまだ書きません。`trajectory.yaml` を完成させます。

#### Phase 3:Skeletal Generation(骨格生成)
**5〜10 候補の MPIR を並列生成**。これは v2.0 の重要強化点です。多様性が確保されます。

#### Phase 4:Critic-Composer Dialogue(批評者-作曲者対話)
Adversarial Critic が全候補を MPIR レベルで攻撃。Producer が最強候補を選ぶか、複数候補の長所を統合した新候補を作らせます。

#### Phase 5:Detailed Filling(詳細埋め)
選ばれた骨格に、Note Realizer が音符を、Performance Realizer が表情を埋めます。

#### Phase 6:Listening Simulation(聴取シミュレーション)
Perception Substitute Layer が完成品を「聴いて」、当初意図(Phase 1)との乖離を測定。乖離が閾値超なら該当箇所を再生成。最終的に `critique.md`、`analysis.json`、`perceptual_report.json` が出力されます。

### 6.2 8 ステップ生成パイプライン

```
[Step 1: Form Planner]      Spec + Trajectory  →  SongFormPlan
      ↓
[Step 2: Harmony Planner]                       →  HarmonyPlan
      ↓
[Step 3: Motif Developer]                       →  MotifPlan + PhrasePlan
      ↓
[Step 4: Drum Patterner]                        →  DrumPattern
      ↓
[Step 5: Arranger]                              →  ArrangementPlan
      ↓
═══ MUSICAL PLAN COMPLETE — Critic Gate ═══

      ↓
[Step 6: Note Realizer]     MPIR  →  ScoreIR
      ↓
[Step 6.5: Performance Realizer]  ScoreIR  →  ScoreIR + PerformanceLayer  ★NEW
      ↓
[Step 7: Mix Designer]      ScoreIR + PerfLayer  →  ProductionManifest    ★NEW
      ↓
[Step 8: Renderer]          all above  →  MIDI / Audio / Score / DAW project
```

### 6.3 多候補生成と選択

Step 3 の「5〜10 候補」は実装上の比喩ではなく、**実装そのもの** です。

```python
# src/yao/conductor/multi_candidate.py
class MultiCandidateOrchestrator:
    def generate_candidates(self, context, n=5) -> list[MusicalPlan]:
        # n 個の異なるシードで Step 2-5 を並列実行
        return [self._pipeline_seed(context, seed=i) for i in range(n)]

    def critic_rank(self, candidates: list[MusicalPlan]) -> list[CandidateScore]:
        # Critic が全候補に findings を生成し、severity weighted score
        return sorted(
            [self._score(c) for c in candidates],
            key=lambda s: s.weighted_critique_severity,
        )

    def producer_select(self, ranked: list[CandidateScore]) -> MusicalPlan:
        # Producer は単純に top1 を選ぶか、複数の長所を統合
        if self._candidates_complementary(ranked[:3]):
            return self._merge_strengths(ranked[:3])
        return ranked[0].plan
```

---

## 7. パラメータ仕様

YaO は楽曲を、以下の **9 種類の YAML/Markdown ファイル** で完全に記述します。すべて版管理対象であり、git diff で変更履歴が追えます。v1.0 の 8 種に **`use_case` 駆動の評価指定** を加えました。

### 7.1 `intent.md`(意図記述、自然言語+構造化メタデータ)

```markdown
---
use_case: youtube_bgm
target_listener: "creator filming travel videos"
emotional_target:
  primary: "uplifting expectation"
  secondary: "subtle uncertainty"
listening_context: "background, paired with narration"
duration_sec: 90
loopable: true
---

# Intent

初夏の朝、新しい挑戦に向かう前向きな期待感。ただし不安も微かに混じる。
爽やかすぎず、感傷的すぎない、ニュートラルな高揚を目指す。
```

`use_case` は **Perception Layer の評価ルールを切り替える** トリガーになります。

### 7.2 `composition.yaml`(作曲パラメータ、v2 スキーマ)

11 セクションの構造化スキーマ。v1.0 の単純版とは別系列で並存します。

### 7.3 `trajectory.yaml`(時間軸軌跡、5 次元 + 拡張)

```yaml
trajectories:
  tension:
    type: bezier
    waypoints: [[0, 0.2], [16, 0.4], [32, 0.85], [48, 0.6], [64, 0.3]]
  density:
    type: stepped
    sections: {intro: 0.3, verse: 0.5, chorus: 0.9, bridge: 1.0}
  predictability:
    target: 0.65
    variance: 0.15
  brightness:
    type: linear
    target: 0.7
  register_height:
    type: stepped
    sections: {verse: 0.4, chorus: 0.7}

# ★NEW: 予測理論ベースの拡張
prediction_dynamics:
  schema_familiarity:        # Huron ITPRA: 文化的典型への近さ
    type: bezier
    waypoints: [[0, 0.8], [16, 0.5], [32, 0.3]]
  veridical_familiarity:     # この曲内での反復
    type: stepped
    sections: {intro: 0.0, verse: 0.7, chorus: 0.9}
  surprise_density:
    type: linear
    target: 0.3
  surprise_magnitude:
    type: linear
    target: 0.5
```

### 7.4 `references.yaml`(美的参照ライブラリ)

正参照(似せる)と負参照(避ける)。**生メロディ・コード進行を直接コピーする経路は schema レベルで禁止** されており、抽象特徴量のみ抽出可能です。

```yaml
references:
  primary:
    - file: references/midi/bach_invention_1.mid    # 権利クリア済
      role: "voice leading reference"
      weight: 0.6
      extract_features:
        - voice_leading_smoothness
        - motif_density_distribution
        - harmonic_rhythm
      forbidden_to_extract:    # 著作権配慮の二重ロック
        - melody_contour
        - chord_sequence
  negative:
    - file: references/midi/typical_corporate_bgm.mid
      role: "what NOT to be"
      avoid_features:
        - predictable_progression
        - stock_drum_pattern
```

### 7.5 `negative-space.yaml`(否定空間)

休符・周波数ギャップ・テクスチャ削除など、「鳴らさない」設計。

```yaml
silence:
  between_phrases:
    required: true
    min_duration_beats: 0.5
  before_climax:
    required: true
    description: "breath before the storm"

frequency_gaps:
  vocal_range:
    range_hz: [200, 2000]
    reservation_strength: 0.7

textural_subtraction:
  - section: chorus_2
    bars: [0, 4]
    description: "drop drums for impact"
```

### 7.6 `arrangement.yaml`(編曲パラメータ、編曲時のみ)

```yaml
arrangement:
  input:
    file: "inputs/original.mid"
    rights_status: "owned_or_licensed"  # 必須フィールド

  preserve:
    melody:        { enabled: true, similarity_min: 0.85 }
    hook_rhythm:   { enabled: true, similarity_min: 0.80 }
    chord_function:{ enabled: true, similarity_min: 0.75 }
    form:          { enabled: true }

  transform:
    target_genre: "lofi_hiphop"
    bpm: { mode: "set", value: 86 }
    harmony:
      reharmonization_level: 0.35
      add_7ths: true
    rhythm:
      swing: 0.35
      groove: "laid_back"
    orchestration:
      drums: "dusty_kit"
      bass: "warm_upright"

  evaluate:
    original_preservation_weight: 0.5
    transformation_strength_weight: 0.3
    musical_quality_weight: 0.2
```

### 7.7 `production.yaml`(ミックス・マスタリング)

```yaml
production:
  master:
    target_lufs: -14
    true_peak_max_dbfs: -1.0
    stereo_width: 0.7

  per_track:
    piano:
      eq:
        - { freq: 100, gain: -2, q: 0.7, type: "high_pass" }
        - { freq: 3000, gain: 1, q: 1.5, type: "peak" }
      compression:
        threshold_db: -18
        ratio: 2.5
        attack_ms: 15
        release_ms: 80
      reverb:
        type: "hall"
        wet: 0.25
        decay_sec: 1.8
      pan: -0.2
      gain_db: 0
```

### 7.8 `provenance.json`(自動生成、追記専用)

すべての生成判断の来歴記録。

### 7.9 `annotations.json`(★NEW: ユーザフィードバック)

時間タグ付きの評価。Reflection Layer の入力。

```json
{
  "timestamp_iso": "2026-05-02T10:30:00Z",
  "iteration": "v005",
  "annotations": [
    {
      "time_start_sec": 12.4,
      "time_end_sec": 14.8,
      "bars": [4, 5],
      "sentiment": "positive",
      "tags": ["memorable_motif", "good_dynamics"]
    },
    {
      "time_start_sec": 32.1,
      "time_end_sec": 36.7,
      "bars": [12, 14],
      "sentiment": "negative",
      "tags": ["too_busy", "muddy_low_end"]
    }
  ]
}
```

### 7.10 Spec Composability(★NEW: v2.0 強化)

`extends:` と `overrides:` で再利用可能なスペック断片を組み立てます。

```yaml
# specs/projects/my-symphony/composition.yaml
extends:
  - specs/fragments/instruments/orchestral_strings.yaml
  - specs/fragments/genres/cinematic_dramatic.yaml
  - specs/fragments/trajectories/three_act_arc.yaml

overrides:
  tempo_bpm: 96
  key: D minor
```

---

## 8. Custom Commands(指揮者の指示棒)

ユーザは以下のコマンドで Orchestra を動かします。各コマンドは `.claude/commands/*.md` に定義されます。

| コマンド | 用途 | 主要 Subagent |
|---|---|---|
| `/compose <project>` | 仕様から新曲を生成 | Composer → 全員 |
| `/arrange <project>` | **既存曲を編曲** ★Tier 2 | Orchestrator + Adversarial Critic |
| `/critique <iteration>` | 既存生成物を批評 | Adversarial Critic |
| `/regenerate-section <project> <section>` | 特定セクションのみ再生成 | Composer + Producer |
| `/morph <from> <to> <bars>` | 2 つの楽曲調を補間 | Composer + Orchestrator |
| `/improvise <input>` | **リアルタイム伴奏** ★Tier 3 | Composer + Rhythm |
| `/explain <element>` | 特定要素の生成判断を説明 | Producer(Provenance 参照) |
| `/diff <iter_a> <iter_b>` | 2 イテレーション間の音楽差分 | Verifier |
| `/render <iteration>` | MIDI を音声・楽譜・DAW に変換 | Mix Engineer |
| `/sketch` | スケッチ→仕様対話モード | Producer |
| `/preview <spec>` | **インライン即時試聴** | Renderer |
| `/watch <spec>` | **ファイル変更検知 → 自動再生成** | Conductor |
| `/annotate <iteration>` | **時間タグ付きフィードバック UI** ★Tier 4 | Reflection |
| `/branch <project> <name>` | **Plan-level branching** ★Tier 3 | Producer |
| `/alternatives <project> <section>` | **代替案 N 個生成** ★Tier 2 | Composer |

---

## 9. Skills(楽団員の素養)

`.claude/skills/` には専門知識を構造化したモジュールが配置されます。Subagent は必要に応じてこれらを参照します。各 Skill は **Markdown 本体 + YAML front-matter** の形式で、front-matter は機械可読、Markdown 本体は人間と LLM が読みます。`make sync-skills` で両者の整合を保ちます。

### 9.1 ジャンル Skills(目標 30+)

v1.0 の 8 から大幅拡張。文化別カテゴリで整理。

```
.claude/skills/genres/
├── western_popular/        (15: pop, rock, jazz, blues, country, ...)
├── electronic/             (7:  house, techno, trance, dnb, idm, ...)
├── classical/              (6:  baroque, classical, romantic, ...)
├── world/                  (12: hindustani, carnatic, maqam, ...)
└── functional/             (8:  film_dramatic, game_rpg, ad_15sec, ...)
```

各ジャンルの YAML front-matter には文化的制約も含めます。

```yaml
---
genre: indian_classical_hindustani
scale_constraints:
  - raga_based:
      time_of_day_aware: true
  - microtonal: true
forbidden_in_pure_form:
  - chord_progressions
  - equal_temperament_strict
---
```

### 9.2 理論 Skills

和声法・対位法・リハーモナイゼーション・モーダルインターチェンジに加え、12 音技法・スペクトル楽派・微分音技法も追加。

### 9.3 楽器 Skills

各 38+ 楽器の音域・慣用奏法・音色特性・物理的制約・代表フレーズパターン。**演奏表情(articulation)** を専用カテゴリとして独立させました(`.claude/skills/articulation/`)。

### 9.4 心理学 Skills

Juslin・Huron・Krumhansl の経験的マッピング。特に **Huron の ITPRA 予測理論** は v2.0 で `prediction_dynamics` 軌跡の根拠として組み込まれました。

### 9.5 文化的配慮 Skill

ノンウェスタン音楽を扱う際のガイドライン(`.claude/skills/cultural-sensitivity.md`)。文化的盗用回避、伝統的文脈の尊重、専門家レビュープロセス。

---

## 10. Hooks(自動演奏指示)

Hooks は Claude Code への指示ではなく、**実行が保証されるスクリプト** です。v2.0 では 6 つのフックを設定します。

| Hook | タイミング | 内容 |
|---|---|---|
| `pre-commit-lint` | git commit 前 | YAML schema check, music21 lint, golden test smoke |
| `post-generate-render` | `/compose`/`/arrange` 後 | MIDI を音声・楽譜・DAW プロジェクトに自動変換 |
| `post-generate-critique` | 生成完了後 | Adversarial Critic を必ず起動、`critique.md` 永続化 |
| `update-provenance` | あらゆる変更後 | Provenance Graph を最新状態に更新 |
| `spec-changed-show-diff` | spec 編集後 | 何が音楽的に変わったか MPIR レベルで表示 |
| `ai-disclosure-stamp` ★NEW | レンダリング後 | 「YaO で生成」「使用モデル」をメタデータに刻印 |

これらにより、エージェントが指示を忘れても品質保証・透明性が破綻しません。

---

## 11. Perception Substitute Layer(差別化要素 1)

YaO の最も独自性の高い層。**LLM は音を聴けない** という根本的限界を、3 段階の代替機構で補います。v1.0 では stub だった部分を v2.0 で本格実装します。

### 11.1 Stage 1:Audio Features Extraction(Tier 1 で実装)

レンダリング後の音声から客観的指標を抽出。`librosa` + `pyloudnorm` を使用。

```python
@dataclass(frozen=True)
class PerceptualReport:
    # ラウドネス
    lufs_integrated: float
    lufs_short_term: list[tuple[float, float]]
    peak_dbfs: float
    dynamic_range_db: float

    # スペクトル
    spectral_centroid_mean: float
    spectral_centroid_per_section: dict[str, float]
    spectral_rolloff: float
    spectral_flatness: float

    # リズム
    onset_density_per_section: dict[str, float]
    tempo_stability_ms_drift: float

    # 周波数バンド
    frequency_band_energy: dict[BandName, float]
    masking_risk_score: float
```

### 11.2 Stage 2:Use-Case Targeted Evaluation(Tier 2 で実装)

`intent.md` の `use_case` フィールドに基づき、用途別評価ルールを切り替え。

```python
USE_CASE_EVALUATORS = {
    UseCase.YOUTUBE_BGM:    YouTubeBGMRules,    # vocal_space, loopability, fatigue
    UseCase.GAME_BGM:       GameBGMRules,        # loop_seam, tension_curve, repetition
    UseCase.ADVERTISEMENT:  AdvertisementRules,  # hook_entry_time<7s, peak_position
    UseCase.STUDY_FOCUS:    StudyFocusRules,     # low_distraction, stability
    UseCase.MEDITATION:     MeditationRules,     # gentle_dynamics, tempo<70
    UseCase.WORKOUT:        WorkoutRules,        # tempo>120, energy_consistency
    UseCase.CINEMATIC:      CinematicScoreRules, # arc_clarity, climax_position
}
```

### 11.3 Stage 3:Reference Matching(Tier 2 で実装)

スタイルベクトル空間での距離計算。**生のメロディ・コードは比較対象外**(著作権配慮、schema 強制)。

```python
class StyleVector:
    harmonic_rhythm: float
    melodic_contour_distribution: np.ndarray
    voice_leading_smoothness: float
    rhythmic_density_per_bar: np.ndarray
    register_distribution: np.ndarray
    timbre_centroid_curve: np.ndarray
    # 生メロディ・コード進行は含まない(allowlist で禁止)
```

### 11.4 Listening Simulation 統合

Conductor の Phase 6 で必ず実行。乖離が閾値超なら該当セクションの再生成をトリガー。

---

## 12. Performance Expression Layer(差別化要素 2)

Layer 4.5 として新設された層。「楽譜の音符」を「演奏」に変えます。

### 12.1 NoteExpression IR

```python
@dataclass(frozen=True)
class NoteExpression:
    legato_overlap: float = 0.0
    accent_strength: float = 0.0
    glissando_to: int | None = None
    pitch_bend_curve: list[tuple[float, float]] | None = None
    cc_curves: dict[int, list[tuple[float, float]]] | None = None
    micro_timing_ms: float = 0.0
    micro_dynamics: float = 0.0
```

### 12.2 4 つの Realizer

1. **ArticulationRealizer**: 楽器ごとの慣用奏法 Skill から legato/staccato/marcato 等を自動付与
2. **DynamicsCurveRenderer**: セクションの dynamic を音符列で滑らかなカーブに展開
3. **MicrotimingInjector**: ジャンル固有の microtiming プロファイル(jazz laid-back、reggae skanking 等)を適用
4. **CCCurveGenerator**: ヴィブラート(CC1)、ブレス(CC2/11)、ペダル(CC64) を生成

### 12.3 出力形式

- **MIDI**: CC・ピッチベンドとして書き出し
- **MPE MIDI**: 各ノート独立チャンネルでより細密に
- **DAW プロジェクト**: オートメーションレーンとして
- **MusicXML**: 表情記号として

---

## 13. Arrangement Engine(差別化要素 3)

VISION で「YaO の単一最大の差別化能力」と位置付けられた機能。v2.0 で本実装します。

### 13.1 パイプライン

```
[Input MIDI] → [Source Plan Extractor] → [SourcePlan (MPIR)]
                                                 ↓
                              [Preservation Contract] + [Transformation Contract]
                                                 ↓
                                      [Style Vector Operations]
                                                 ↓
                                          [TargetPlan (MPIR)]
                                                 ↓
                                      [Note Realizer] → [ScoreIR]
                                                 ↓
                                  [Arrangement Diff Markdown]
                                                 ↓
                                      [Arrangement Critique]
```

### 13.2 Source Plan Extractor の現実

完全な自動採譜は不可能なので、以下の妥協を取ります。

- **コード推定**: Chordino アルゴリズムベース
- **セクション検出**: librosa.segment.recurrence_matrix の自己相似行列
- **メロディ抽出**: 最高音追跡 + ML(オプション)
- **ドラム抽出**: GM ドラムマップに基づくチャンネル 10 抽出

不完全な抽出結果を、ユーザが対話的に修正できる UI(`/arrange --interactive`)を提供します。

### 13.3 Style Vector Operations

```python
target_plan = (
    source_plan
    - source_genre_vector
    + target_genre_vector
    ⊕ preservation_constraints
)
```

ベクトル演算として透明に記述され、Provenance に記録されます。

### 13.4 Arrangement Diff(成果物)

```markdown
# Arrangement Diff (v003)

## Preserved
- Main hook melodic similarity: 0.91 ✓
- Section form: unchanged ✓
- Chord function similarity: 0.82 ✓

## Changed
- BPM: 128 → 86
- Groove: straight pop → swung lo-fi
- Chords: triads → 7th/9th voicings (35% reharm)
- Bass: root → walking with passing tones
- Drums: four-on-floor → laid-back backbeat

## Risks (Adversarial Critic)
- chorus_energy_drop: dropped more than requested (target -20%, actual -38%)
```

---

## 14. Neural Generator Integration(差別化要素 4)

YaO の説明可能性原則と、ニューラル生成器のブラックボックス性は緊張関係にあります。v2.0 ではこの矛盾を以下の原則で解消します。

> **構造・計画レベルは YaO 自前ロジック(説明可能性確保)、音色・テクスチャ・微細装飾はニューラルに委譲(品質向上)。**

### 14.1 統合パターン

| パターン | バックエンド | 用途 |
|---|---|---|
| **A. Texture Layer** | Stable Audio Open | アンビエント・パッド・環境音 |
| **B. Performance Enhancement** | MusicGen Melody | 単旋律楽器の表情豊かな演奏 |
| **C. Counter-Melody Suggest** | Magenta MelodyRNN | 対旋律候補提案 |
| **D. Drum Groove Variation** | Magenta DrumsRNN | ドラムグルーヴのバリエーション |
| **E. Chord Color Suggest** | Custom (将来) | コード色彩のニューラル提案 |

### 14.2 Provenance での透明性

ニューラル生成も完全に追跡可能にします。

```json
{
  "step": "neural_texture_generation",
  "method": "stable_audio_open",
  "model_version": "1.0.3",
  "prompt": "warm analog synth pad, slow attack, lush reverb, in D minor",
  "seed": 42,
  "output_audio_hash": "sha256:abc123...",
  "rationale": "Atmospheric pad layer requested by spec.texture_layers[0]",
  "rights_status": "user_owned (Stable Audio Open License)",
  "ai_disclosure_required": true
}
```

`ai-disclosure-stamp` Hook により、最終成果物のメタデータに必ず明記されます。

### 14.3 オプショナル依存

GPU・大規模モデルは多くのユーザにとって障壁。すべてのニューラル統合は **オプショナル依存** とし、ローカル GPU が無い環境でもコア機能はフル動作します。

```toml
[project.optional-dependencies]
neural = [
    "transformers>=4.40",
    "torch>=2.0",
]
neural-magenta = [
    "magenta>=2.1",
]
neural-musicgen = [
    "audiocraft>=1.3",
]
```

---

## 15. 多様性の地理的・歴史的拡大

v1.0 の暗黙の前提(西洋ダイアトニック・12 平均律・4/4)を v2.0 で解除します。

### 15.1 Microtonal & Non-Western Scales

スケール定義をセント単位に拡張。

```python
@dataclass(frozen=True)
class ScaleDefinition:
    name: str
    intervals_cents: tuple[int, ...]  # 半音単位ではなくセント単位
    is_octave_repeating: bool = True
    cultural_context: str | None = None
    typical_instruments: tuple[str, ...] = ()

# 例
RAGA_YAMAN = ScaleDefinition(
    name="raga_yaman",
    intervals_cents=(0, 200, 400, 600, 700, 900, 1100),
    cultural_context="north_indian_classical",
)

MAQAM_RAST = ScaleDefinition(
    name="maqam_rast",
    intervals_cents=(0, 200, 350, 500, 700, 900, 1050),  # 1/4 音含む
    cultural_context="arab_classical",
)

PELOG = ScaleDefinition(
    name="pelog",
    intervals_cents=(0, 120, 270, 540, 670, 790, 950),
    cultural_context="javanese_gamelan",
)
```

MIDI 出力では MPE モードでノート別ピッチベンドとして表現。

### 15.2 Extended Time Signatures

複合拍子・変拍子・ポリメーターを第一級でサポート。

```yaml
time_signature:
  primary: "7/8"
  beat_groupings: [3, 2, 2]   # バルカン的 7/8
  alternates:
    - bars: [16, 24]
      signature: "4/4"
  polymeter:
    - instrument: drums
      signature: "3/4"
    - instrument: piano
      signature: "4/4"
    - sync_at: "every 12 beats"
```

### 15.3 Algorithmic Composition Paradigms

20 世紀以降の作曲手法を Generator として追加。

| Generator | パラダイム | 代表作曲家 |
|---|---|---|
| `twelve_tone` | 12 音技法 | Schoenberg, Webern |
| `spectral` | スペクトル楽派 | Grisey, Murail |
| `process_music` | プロセス音楽 | Reich, Glass |
| `aleatoric` | 偶然性音楽 | Cage, Lutosławski |
| `l_system` | 形式文法 | (algorithmic music) |
| `cellular_automata` | セル・オートマタ | Xenakis, Wolfram |

これらはすべて `@register_generator(...)` で登録され、`generation: { strategy: twelve_tone }` で利用可能。

---

## 16. 評価指標の音楽性向上

v1.0 は **3 次元 10 メトリクス**(Structure, Melody, Harmony)。v2.0 は **10 次元 30+ メトリクス** に拡張。

### 16.1 拡張された評価次元

| Dimension | v1.0 | v2.0 |
|---|---|---|
| Structure | ✓ | ✓ + section_form_balance, climax_clarity |
| Melody | ✓ | ✓ + phrase_closure, leap_smoothness |
| Harmony | ✓ | ✓ + cadence_strength, modulation_smoothness |
| Rhythm | partial | full + groove_consistency, syncopation_density |
| **Memorability** | — | hook_distinctiveness, motif_recall_strength |
| **Emotional Coherence** | — | intent_match, valence_arc_alignment |
| **Genre Fitness** | — | typical_features_present, cliche_avoidance |
| **Performance Feasibility** | — | playable_by_human, breath_marks_adequate |
| **Mix Readiness** | — | frequency_collision, masking_risk |
| **Loop Integrity** | — | seam_smoothness (use_case=game_bgm のみ) |
| **Vocal Compatibility** | — | range, breath_lines, syllable_friendly |

### 16.2 Memorability の例

```python
class MemorabilityEvaluator:
    def evaluate(self, score: ScoreIR, intent: IntentSpec) -> dict[str, float]:
        return {
            "motif_recall_strength": self._motif_recall_strength(score),
            "hook_distinctiveness": self._hook_distinctiveness(score),
            "structural_anchor_clarity": self._structural_anchor_clarity(score),
            "rhythmic_signature_strength": self._rhythmic_signature_strength(score),
        }
```

### 16.3 用途別評価の重み調整

`use_case` ごとに評価重みを切り替え。例:

- `youtube_bgm` → memorability より vocal_compatibility 重視
- `cinematic` → memorability・emotional_coherence 重視
- `study_focus` → predictability・low_distraction 重視

---

## 17. 開発ロードマップ

### 17.1 Tier 別優先順位

#### Tier 1:即効性の高い基本機能(2-4 週間)
- Perception Layer Stage 1(audio features)
- Markov Generator
- Production Manifest + pedalboard 統合
- Genre Skills 拡張(8 → 16)
- MusicXML/LilyPond Writer

#### Tier 2:差別化要素の確立(1-3 ヶ月)
- Arrangement Engine MVP
- Performance Expression Layer
- Use-Case Targeted Evaluation
- Reference Matcher 実装
- Subagent の Python 実体化

#### Tier 3:多様性と独自性の拡大(3-6 ヶ月)
- Microtonal & Non-Western Scale Support
- Extended Time Signatures
- Algorithmic Composition Paradigms
- Neural Generator Integration
- Live Improvisation Mode
- Project Runtime

#### Tier 4:プラットフォーム成熟(継続)
- Genre Skills 30 種への拡張
- Annotation UI と Reflection Layer
- Backend-Agnostic Agent Protocol
- DAW MCP Integration (Reaper)
- Subjective Quality Test Suite

### 17.2 Phase 別マイルストーン

#### Phase α(完了):基盤構築
- 7 層アーキテクチャ、MPIR、rule_based + stochastic、643 テスト

#### Phase β(進行中):Plan-Layer Maturity
- 30+ 批評ルール、Multi-candidate Conductor、Markov + constraint_solver、Subagent eval harness

#### Phase γ(次)Differentiation
- Perception Stage 1-2、Counter-melody Generator、12 Genre Skills、**Arrangement Engine**(マーキー機能)、MusicXML/LilyPond、Reference Matcher

#### Phase δ:Production Readiness
- Production Manifest + Mix Chain、Sketch-to-Spec dialogue state machine、`yao preview`/`yao watch`、Strudel emitter、`yao annotate` UI、mkdocs サイト完成、Reaper MCP、Spec composability

#### Phase ε(継続)Reflection & Community
- Reflection Layer、コミュニティ参照ライブラリ規格、Live improvisation、AI music model bridges

### 17.3 ユーザ価値ドリブン マイルストーン

技術フェーズと並行する、ユーザ視点の到達点。

| マイルストーン | ユーザ価値 | 主要機能 |
|---|---|---|
| **1. Describe & Hear** ✓ | 「YAML で記述し、即座に聴ける」 | CLI compose, generators, templates |
| **2. Iterate & Improve** ✓ | 「不満を伝えると改善される」 | diff, critique, regenerate-section |
| **3. Richer Music** | 「プロ品質のハーモニー・リズム・表現」 | Performance Layer, mix chain, advanced harmony |
| **4. My Style** | 「好みを学習、自分のスタイルで生成」 | reference, annotation, reflection |
| **5. Cover & Remix** | 「既存曲を別ジャンルに編曲」 | **Arrangement Engine** |
| **6. Production Ready** | 「実プロジェクトで使える出力」 | DAW 連携, multi-format, mix engineer |
| **7. Live & Interactive** | 「ライブで AI が伴奏」 | Improvisation mode |
| **8. Global Music** | 「世界中の音楽文化に対応」 | Microtonal, world genres, polyrhythm |

### 17.4 開発プロセス指針

- **Sound-First 文化**: 生成・レンダリングに影響する変更は、変更前後の音声サンプルを PR に含める
- **ドキュメント予算**: 設計文書 1 行あたり、実働コード 3 行以上を維持
- **Dogfooding**: YaO で制作した音楽をプロジェクトのデモ動画・発表に使用
- **ミュージシャン向け貢献ガイド**: ジャンル Skill 追加・テンプレート作成・参照楽曲分析は Python 不要で貢献可能
- **垂直整合チェック**: 各 PR は「入力・処理・評価のどの 3 層を進歩させるか」を明記

---

## 18. クイックスタート

### 18.1 環境構築

```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts
make setup-hooks
```

### 18.2 最初の曲を作る

```bash
# 1. プロジェクト作成
yao new-project my-first-song

# 2. Claude Code 起動して対話
claude

# 3. プロンプト例
> /sketch
> "雨の夜のカフェで聴きたい、少し切ない 90 秒のピアノ曲"
> (対話で仕様が固まる)
> /compose my-first-song

# 4. 結果確認
open outputs/projects/my-first-song/iterations/v001/score.pdf
afplay outputs/projects/my-first-song/iterations/v001/audio.wav

# 5. 反復
> /critique my-first-song v001
> /regenerate-section my-first-song chorus
```

### 18.3 既存曲を編曲する(Phase γ で可能)

```bash
yao import-midi my_song.mid --project rainy-cafe-arrangement
yao sketch-arrangement rainy-cafe-arrangement
> "lo-fi hip-hop 風にしたい。メロディは保ちつつ、ジャジーなコードに"
yao arrange rainy-cafe-arrangement
```

### 18.4 ライブ即興セッション(Phase ε で可能)

```bash
yao improvise --input-midi-port "USB MIDI Keyboard" \
              --output-midi-port "Reaper Virtual" \
              --style "jazz_ballad" \
              --role "accompanist"
```

---

## 19. ファイル形式と相互運用性

| 用途 | 形式 | 理由 |
|---|---|---|
| 楽曲データ | MIDI (.mid), MusicXML (.xml) | 業界標準・全 DAW 対応 |
| 楽譜 | LilyPond (.ly), PDF | 高品質楽譜・自動レンダリング |
| 仕様 | YAML | 人間可読・git 管理向き |
| 中間表現 | JSON | プログラム可読・スキーマ検証 |
| 来歴 | JSON | グラフ構造の表現 |
| 注釈 | JSON | 時間タグ付きフィードバック |
| 音声 | WAV (制作中), FLAC/MP3 (配布) | 標準対応 |
| ライブコード | Strudel パターン文字列 | ブラウザ即試聴可能 |
| DAW プロジェクト | .RPP / .als / .song | Reaper/Ableton/Studio One 直接対応 |
| MPE 拡張 | MIDI 1.0 with MPE convention | 微分音・連続制御対応 |

独自フォーマットは原則として作りません。既存標準で表現できないものだけを最小限定義します。

---

## 20. 倫理とライセンス指針

### 20.1 学習データと参照
参照ライブラリには **権利クリア済楽曲のみ** を配置します。各楽曲には `references/catalog.yaml` でライセンス状態を記録。**生メロディ・コード進行を直接コピーする経路は schema レベルで禁止** されています。

### 20.2 アーティスト模倣
特定の現役アーティスト名指定は推奨しません。代わりに抽象的特徴記述を推奨します。

### 20.3 文化的配慮 ★NEW
ノンウェスタン音楽(インド古典・アラブ・ガムラン等)を扱う際は、`docs/ethics/cultural-sensitivity.md` のガイドラインに従います。

- **専門家レビュー**: 民族音楽 Skill の追加には、可能な限りその文化の専門家のレビューを得る
- **文化的文脈の尊重**: 伝統的様式と「Fusion」を明確に区別し、混同しない
- **商用利用の警告**: 文化的セレモニー音楽など、商用利用が不適切なジャンルには警告を表示
- **正しい呼称**: 楽器名・スケール名は、可能な限り元の文化での呼称を使用

### 20.4 AI 生成の透明性 ★NEW
ストリーミングプラットフォームでの AI 生成楽曲取り扱いが厳格化しています。

- **メタデータ刻印**: `ai-disclosure-stamp` Hook で MIDI/オーディオに「YaO 生成」を必須刻印
- **使用モデル明示**: ニューラル生成器使用時は、モデル名・バージョン・プロンプトを Provenance に記録
- **生成物権利**: YaO 生成物の権利は基本ユーザに帰属するが、参照楽曲影響度が極端に高い場合は警告

### 20.5 生成物の権利
ユーザに帰属。ただしニューラル生成器使用時は、各モデルのライセンスに従います。

---

## 21. CLAUDE.md・VISION.md・FEATURE_STATUS.md との関係

| ファイル | 対象 | 内容 |
|---|---|---|
| `PROJECT.md`(本書) | 人間 + エージェント | 全体設計・哲学・アーキテクチャ |
| `VISION.md` | 人間 + エージェント | 目標アーキテクチャ・ロードマップ |
| `FEATURE_STATUS.md` | 人間 + エージェント | **単一の真実**:何が今動くか |
| `CLAUDE.md` | エージェント中心 | 不変ルール・禁止事項・Skill 参照ポインタ |
| `README.md` | 人間中心 | クイックスタート・最低限の使用法 |
| `docs/design/*.md` | 人間 + エージェント | 個別の設計判断記録 |
| `.claude/guides/*.md` | 開発者 + エージェント | 技術的開発ドキュメント |
| `docs/`(mkdocs) | ユーザ + 開発者 | mkdocs 構成のドキュメントサイト |

**規律**: PROJECT.md は「**何を作りたいか**」、FEATURE_STATUS.md は「**何が今動くか**」、VISION.md は「**どこに向かうか**」。三者が乖離すると混乱の原因になるため、`make sync-docs` で整合を機械的にチェックします。

---

## 22. リスクと注意点

### 22.1 技術リスク

- **Arrangement Engine の MIR 困難性**: 自動採譜・コード推定は完全には不可能。妥協と対話的修正 UI を組み合わせる
- **ニューラルモデル統合の依存膨張**: GPU 必須は障壁。オプショナル依存として隔離
- **Microtonal 対応の MIDI 制約**: MIDI 1.0 の根本的限界。MPE 対応シンセが必要 → ターゲット環境を明示
- **Performance Expression の表現力過多**: すべての CC・ピッチベンドを書き出すと MIDI が肥大化。圧縮・簡略化オプションを用意

### 22.2 プロジェクト運営リスク

- **ジャンル Skill の文化的妥当性**: 外部専門家レビューなしには文化的に不適切な内容になる懸念
- **規模拡大によるコード複雑度**: 89 ファイル → 200+ ファイルになる見込み。層境界 lint をさらに厳密に
- **ドキュメント維持コスト**: 自動同期ツールの整備が不可欠

### 22.3 倫理リスク

- **著作権リスクの再評価**: ニューラル生成器は学習データの著作権問題がある。生成物に明記必須
- **文化的盗用リスク**: 商用利用を想定したガイドライン整備
- **AI 生成楽曲の透明性**: ストリーミングプラットフォームの規約変化に追従

---

## 23. 将来のアーキテクチャ拡張

実装は各マイルストーンの必要性に応じて行います。

### 23.1 Project Runtime(状態を持つセッション)
現在の CLI はステートレス。`ProjectRuntime` で生成キャッシュ・フィードバックキュー・undo/redo を保持。

### 23.2 Backend-Agnostic Agent Protocol
Claude Code への結合を抽象化。`AgentRole`, `AgentContext`, `AgentOutput` の Python プロトコル定義。Anthropic API、ローカル LLM、Python のみのバックエンドを切り替え可能に。

### 23.3 Spec Composability(本書 7.10)
`extends:` / `overrides:` / `specs/fragments/` で再利用可能な spec 断片。

### 23.4 Reflection Layer(Layer 7)
ユーザ別嗜好プロファイル、注釈集約、クロスプロジェクトのパターン抽出。

### 23.5 Generic Creative-Domain Framework
YaO のパターン(intent-as-code、trajectory、plan IR、adversarial critic、provenance)をドメイン非依存ツールキットに抽象化。UI デザイン・ナラティブ構造・ゲームレベル設計などへの応用。

---

## 24. 戦略的洞察

YaO の設計パターンは音楽に限定されない、**構造化された人間-AI 創造的協働の汎用フレームワーク** です。

| YaO パターン | 汎用パターン | 他ドメインへの応用 |
|---|---|---|
| Score (YAML 仕様) | **Intent-as-Code** | UI デザイン仕様、ナラティブ構造、ゲームレベル設計 |
| Trajectory (軌跡) | **時間品質曲線** | 動画ペーシング、プレゼンテーション構成、UX ジャーニー |
| MPIR (Plan IR) | **構造化計画 IR** | 複雑な創作タスクの「なぜ」を扱う中間表現 |
| Adversarial Critic | **敵対的レビュー** | コードレビュー、デザイン批評、文章フィードバック |
| Provenance Graph | **意思決定系譜** | AI 支援の創造的作業全般 |
| 6 相認知プロトコル | **構造化創造プロトコル** | 「いきなり実装しない」が重要なすべてのドメイン |
| Perception Substitute | **代替知覚機構** | LLM が直接体験できないドメインの評価 |
| Vertical Alignment | **垂直整合原則** | あらゆる多層システム設計 |

これらの抽象化は将来的に抽出可能に設計されていますが、現在のスコープは音楽制作に限定します。

---

## 25. 用語集

**Conductor(指揮者)** — プロジェクトの所有者である人間。最終判断者。

**Orchestra(楽団)** — Subagent 群の総称。

**Score(楽譜)** — `specs/` 内の YAML 群。楽曲の完全な記述。

**Score IR** — Layer 3。具体的音符レベルの中間表現。

**MPIR(Musical Plan IR)** — Layer 3.5。音符の前の "なぜ"。形式・和声・モチーフ・編成の計画。

**Performance Layer** — Layer 4.5。楽譜から演奏への変換層。

**Trajectory(軌跡)** — 楽曲の時間軸上の特性曲線(緊張度・密度等)。

**Aesthetic Reference Library** — 美的アンカーとなる楽曲群。

**Perception Substitute Layer** — AI が音楽を「聴けない」ことを補う層。

**Provenance(来歴)** — すべての生成判断の追跡可能な記録。

**Adversarial Critic** — 生成物を意図的に攻撃する批評 Subagent。称賛しない。

**Negative Space(否定空間)** — 鳴らさない部分の設計。

**Style Vector** — ジャンルやスタイルを多次元特徴量空間のベクトルとして表現したもの。

**Iteration(反復)** — 同一プロジェクト内の生成版。`v001`, `v002`, ... と版管理。

**Music Lint** — 音楽理論・制約違反の自動検出機構。

**Sketch-to-Spec** — 自然言語スケッチから YAML 仕様への対話的変換プロセス。

**Vertical Alignment(垂直整合)** — 入力・処理・評価の 3 層が同期して進歩すべきという原則。

**Critic Gate(批評関門)** — MPIR から Score IR への遷移前の批評ステップ。

**Plan-Level Branching** — Git ブランチに似た MPIR 単位の分岐機構。

**Use-Case Targeted Evaluation** — 用途(BGM・ゲーム・広告等)に応じた評価ルール切替。

**Microtonal** — 12 平均律以外の音律。セント単位で表現。

**MPE(MIDI Polyphonic Expression)** — 各ノートに独立 CC を送れる MIDI 1.0 規約拡張。

**Algorithmic Composition Paradigm** — 12 音技法・スペクトル・プロセス音楽など、特定の作曲手法。

---

## 26. 最後に:YaO が目指す世界

YaO は「AI が音楽を作る」プロジェクトではありません。**人間と AI が、それぞれの長所を活かして音楽を共創する** ためのインフラです。

- 人間は **意図と判断と感性** を提供します。
- AI は **理論知識・反復速度・記録の網羅性** を提供します。
- YaO は **両者を構造化された協働プロセスとして成立させる場** です。

優れた音楽は、最終的には **人間の魂の発露** であり続けます。YaO はその発露を **より速く、より深く、より再現可能に**、そして **より多様に** することを目指します。

v1.0 で「エンジニアリング規律」を確立し、v2.0 で「音楽性と多様性」を獲得します。次の v3.0 では、世界中のミュージシャンがそれぞれの文化と感性で YaO を使い、互いの作品から学び合うコミュニティが形成されることを期待しています。

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve, in any language, any genre, any time.*

---

**Project: You and Orchestra (YaO)**
*Document version: 2.0*
*Last updated: 2026-05-02*

**Quick links**:
- [VISION.md](./VISION.md) — 目標アーキテクチャ
- [FEATURE_STATUS.md](./FEATURE_STATUS.md) — 何が今動くか
- [CLAUDE.md](./CLAUDE.md) — 開発者向け不変ルール
- [README.md](./README.md) — クイックスタート
- [docs/](./docs/) — 詳細ドキュメント
