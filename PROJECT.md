# You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

---

## 0. プロジェクトの本質

**You and Orchestra (YaO)** は、Claude Code を基盤として動作する **エージェント型音楽制作環境** です。一般的な「AI作曲ツール」とは異なり、YaO は単一のブラックボックスから音楽を吐き出すのではなく、**役割分担された複数の AI エージェント(Orchestra Members)を、人間(You = Conductor)が指揮する**という構造を取ります。

YaO のすべての設計は、次のひとつの命題に従属します。

> **音楽制作とは、感覚的な一回限りの作業ではなく、再現可能で改善可能な創作エンジニアリングである。そして、その中心には「計画」がある。**

このため YaO は、音楽を **音声ファイル**として扱う前に、**計画・コード・仕様・テスト・差分・来歴**として扱います。これを **Music-as-Plan 哲学** と呼びます(v1.0 の Music-as-Code 哲学からの進化)。

### v2.0 における核心的進化

v1.0 では「Music-as-Code」(コード・テスト・差分管理として扱う)を掲げました。Phase 1 を完成させた知見から、v2.0 はこれを **「Music-as-Plan」** へ深化させます。

| 観点 | v1.0(Music-as-Code) | v2.0(Music-as-Plan) |
|---|---|---|
| 中心概念 | spec(YAML)と code | spec → **plan** → notes |
| 核心抽象 | ScoreIR(具体音符) | **Composition Plan IR**(計画)+ ScoreIR(音符) |
| 批評の対象 | 最終 MIDI のみ | 計画と音符の両方 |
| 編曲 | 音符レベルの変換 | 計画レベルの構造化変換 |
| 哲学 | 音楽はコードである | 音楽の本質は計画にあり、コードはその実装である |

この進化は、Phase 1 で生成される音楽が「動くが浅い」状態から脱却するための構造的な打ち手です。

---

## 1. メタファー:You and Orchestra

YaO のすべての概念は、オーケストラの比喩に対応しています。この対応関係を内面化することが、YaO を正しく使う最短距離です。

| YaO の構成要素 | オーケストラの比喩 | 実装上の対応 |
| --- | --- | --- |
| **You** | 指揮者 (Conductor) | プロジェクト所有者である人間 |
| **Score** | 楽譜 | `specs/*.yaml` に記述された作曲仕様 |
| **Plan** ★v2.0 | 指揮者の書き込み入り楽譜 | Composition Plan IR(構造・和声・モチーフの計画) |
| **Orchestra Members** | 楽団員 | 各 Subagent(Composer, Critic, Theorist 等) |
| **Concertmaster** | コンサートマスター | Producer Subagent(全体調整役) |
| **Rehearsal** | リハーサル | 生成・評価・修正の反復ループ |
| **Library** | 楽団の楽譜庫 | `references/` 内の参照楽曲群 |
| **Performance** | 本番演奏 | レンダリングされた最終音源 |
| **Recording** | 録音 | `outputs/` 内の成果物 |
| **Critic / Reviewer** | 批評家 | Adversarial Critic Subagent |
| **Score Markings** | 演奏記号(強弱・スピード等) | Trajectory 軌跡 |

指揮者(You)はすべての音符を書くわけではありません。指揮者の仕事は、**意図を明確化し、楽団員に方向性を示し、リハーサルで判断を下し、本番の質を担保する**ことです。YaO はこの分業を AI に持ち込みます。

優れた指揮者が実際の演奏前に楽譜に書き込みを加えるように、YaO の Composition Plan IR は **演奏(音符)に先立つ指揮者の構想**を表現します。

---

## 2. 設計原則

YaO のあらゆる実装判断は、以下の **5つの不変原則** に照らして決定されます。これらは CLAUDE.md にも転記され、エージェントの判断基準として機能します。

### 原則1:エージェントは作曲家ではなく、作曲環境である

YaO は「曲を書く AI」ではなく、「人間の作曲を 10 倍速にする環境」を志向します。完全自動化ではなく、人間の創造的判断を加速・拡張することを目的とします。

### 原則2:すべての判断に説明可能性を要求する

生成された音符・コード・編曲判断のすべてに、「なぜそうしたのか」という理由が記録されます。これは Provenance Graph として永続化され、追跡・レビュー・修正が可能です。

### 原則3:制約は創造性を殺さず、むしろ解放する

明示的な仕様(YAML)・参照ライブラリ・否定空間(Negative Space)などの制約は、創造の足枷ではなく足場として機能します。無制限の自由は麻痺を生みます。

### 原則4:時間軸の設計を音符の設計から分離する

楽曲は最初に「時間軸上の軌跡」(緊張度・密度・感情価のカーブ)として設計され、音符はその後に埋められます。これにより、構造的に意味のある音楽が生まれます。

### 原則5:人間の耳を最後の真実とする

どれだけ自動評価指標が精緻でも、人間の聴取体験が最終判断者です。エージェントは判断を**置き換えるのではなく支援**します。

### 原則6 ★v2.0:垂直アラインメント

Input(spec の表現力)、Processing(生成パイプラインの深さ)、Evaluation(批評の解像度)は **同期して深化させる**。一層だけを深めても効果は無効化される。

これは v1.0 の 5 原則とは性質が異なる **メタ原則** です。具体的には:

- 仕様が豊かになっても、それを処理する generator がそれを使わなければ意味がない
- generator が深くなっても、批評がそれを評価できなければ品質保証ができない
- 批評が精密になっても、仕様にその精密さを表現できなければユーザは制御できない

リリースごとに、3 層が同じ深さで進化することを点検します。Capability Matrix(§5)がその実行手段です。

---

## 3. 開発フェーズ:現在地と方向

YaO は Phase 1(Parameter-driven symbolic composition)を完成させました。**v2.0 は Phase 1 完了後の進化を扱う設計書**です。

### Phase 1 の達成事項(v2.0 の出発点)

- 7-Layer architecture と layer-boundary lint
- Pydantic-based YAML 仕様(composition / trajectory / constraints / negative space / references / production)
- ScoreIR(frozen dataclass)
- rule_based + stochastic generators
- Conductor の generate-evaluate-adapt-regenerate loop
- 226 tests, mypy strict, architecture lint
- 7 Subagent definitions, 7 slash commands
- Section-level regeneration, score diff, provenance log

### Phase 1 で見えた課題(v2.0 が解消するもの)

| 課題 | 症状 | v2.0 の解 |
|---|---|---|
| **音楽的浅さ** | 出力がスケール内音符の連続止まり | Composition Plan IR(§7) |
| **Trajectory が velocity のみ** | 高 tension で音が大きくなるだけ | 多次元連動(§7.4) |
| **Adversarial Critic 未実装** | 定義のみで判定ロジック無し | Critic Rule Registry(§9) |
| **mood パーサが脆弱** | 日本語非対応、キーワード優先順位バグ | SpecCompiler の独立化(§10) |
| **ドキュメント・実装ズレ** | テスト数が文書間で異なる | Capability Matrix(§5) |
| **ジャンル極狭** | cinematic Skill のみ | Genre Skill 拡充(§11) |
| **DrumIR 不在** | リズムが粗粒度 | DrumIR 独立(§12) |

これらは個別の機能不足ではなく、**Phase 1 アーキテクチャの自然な限界**であり、Phase 2 への構造的進化を要求します。

### Phase 2 の核心:Composition Plan IR の導入

v2.0 が導入する最大の変更は、**Spec と ScoreIR の間に Composition Plan IR(以下 CPIR)を挟む**ことです。これにより:

- 計画と音符の責任が分離される
- Critic が計画を批評できる(現状は最終 MIDI のみ)
- 編曲が「計画レベルの変換」として実装できる
- Subagent の責任分担が実装上で活きる

CPIR の詳細は §7 で展開します。

---

## 4. アーキテクチャ:7+1 層モデル

v1.0 は 7 層モデルでした。v2.0 はこれを **完全に保持しつつ、Layer 3 内に Plan サブレイヤーを位置付ける**ことで、構造的混乱を避けて自然に拡張します。

```
┌─────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                      │
│   制作履歴からの学習、ユーザ嗜好の更新                │
├─────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                    │
│   構造・和声・リズム・音響の自動評価、敵対的批評       │
├─────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                  │
│   MIDI→音声、楽譜PDF、ライブコード変換                │
├─────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                      │
│   美的判断の代替機構(参照駆動・心理学マッピング)     │
├─────────────────────────────────────────────────────┤
│ Layer 3: Intermediate Representation (IR)           │
│   ┌──────────────────────────────────────────┐      │
│   │ Layer 3b: Score IR (concrete notes)      │      │
│   │   ScoreIR / Note / Section / Part        │      │
│   ├──────────────────────────────────────────┤      │
│   │ Layer 3a: Composition Plan IR ★v2.0      │      │
│   │   FormPlan / HarmonyPlan / MotifPlan /   │      │
│   │   PhrasePlan / DrumPattern / Arrangement │      │
│   └──────────────────────────────────────────┘      │
├─────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                        │
│   Plan generators(計画) + Note realizers(音符)      │
├─────────────────────────────────────────────────────┤
│ Layer 1: Specification                              │
│   YAML仕様、対話、スケッチ入力                        │
└─────────────────────────────────────────────────────┘
```

### v1.0 からの変更点

- **Layer 3 を 3a(Plan)と 3b(Score)に分割** — 既存の Layer 3(IR)はそのまま 3b として残り、3a が上に積まれる
- **Layer 2 が Plan Generator と Note Realizer の 2 段に分かれる** — 既存の rule_based / stochastic は Note Realizer に再分類
- **Layer 1, 4, 5, 6, 7 は変更なし** — Phase 1 の資産を維持

### 依存規則(変更なし)

層間の依存は厳密に下から上へのみ流れます。**Layer 3a(Plan)→ Layer 3b(Score)への変換は同層内**で行うため、層境界違反にはなりません。

architecture-lint は v2.0 で **`tools/architecture_lint.py` に Layer 3a/3b の細分ルールを追加**します。

---

## 5. Capability Matrix(透明性の核)★v2.0

YaO の最大の運用課題は、**設計の野心と実装の現状のズレ**です。v1.0 では README、CLAUDE.md、PROJECT.md がそれぞれ機能の状態を独立に記述しており、不整合が発生していました(例:テスト数が文書間で異なる)。

v2.0 はこれを **Capability Matrix** で構造的に解消します。Matrix は **すべてのドキュメントが参照する単一の真実源** です。

### Matrix のステータス記号

| 記号 | 意味 |
|---|---|
| ✅ Implemented | 動作しテストあり、依存可能 |
| 🟢 Working | 主要機能は動作するがエッジケース要注意 |
| 🟡 Partial | 部分実装、Notes 列に limitation 必須 |
| ⚪ Designed | 設計済みだが未実装 |
| 🔴 Gap | 設計すら整理されていないギャップ |

### Capability Matrix(現時点)

#### Specification Layer

| Feature | Status | Notes |
|---|---|---|
| composition.yaml v1 | ✅ | Phase 1 で完成 |
| composition.yaml v2(11 セクション) | ✅ | 22 Pydantic モデル、3 テンプレート |
| intent.md(自然言語意図) | 🟢 | keyword extraction 実装済、NL→emotion 推論は未 |
| trajectory.yaml(5 次元) | 🟢 | 5 dims 定義済、generator は tension→velocity のみ |
| references.yaml | 🟡 | schema あり、reference matcher 未接続 |
| negative-space.yaml | 🟡 | schema あり、反映機構未完成 |
| production.yaml | 🟡 | schema あり、mix chain 未実装 |
| constraints + scope | ✅ | scope 機能完備 |

#### Generation Layer

| Feature | Status | Notes |
|---|---|---|
| rule_based generator(v1) | ✅ | 決定論的、NoteRealizer ラッパー実装済 |
| stochastic generator(v1) | ✅ | seed/temperature、NoteRealizer ラッパー実装済 |
| FormPlanner(rule_based) | ✅ | spec sections → SongFormPlan |
| HarmonyPlanner(rule_based) | ✅ | tension-responsive chord selection |
| PlanOrchestrator | ✅ | form → harmony → MusicalPlan 構築 |
| legacy adapter(v1→v2) | ✅ | CompositionSpec → v2 pipeline bridge |
| markov generator | ⚪ | 設計済 |
| constraint solver generator | ⚪ | 設計済 |
| MotifPlanner | 🔴 | Phase β |
| Drum Patterner | 🔴 | Phase β |
| Counter-melody generator | 🔴 | Phase β |

#### Critique & Verification

| Feature | Status | Notes |
|---|---|---|
| Music lint | ✅ | parallel fifths 等 |
| Score analyzer | ✅ | 構造・メロディ・和声 |
| Evaluator(5 次元 + quality score) | ✅ | structure / melody / harmony / rhythm、MetricGoal ベース |
| Score diff(modified notes) | ✅ | Phase 1 完成 |
| MetricGoal type system | ✅ | 7 types 実装済(AT_LEAST〜DIVERSITY) |
| RecoverableDecision logging | ✅ | 9 registered codes、ProvenanceLog 統合済 |
| Critique base types | ✅ | Finding, CritiqueRule, CritiqueRegistry 実装済 |
| Adversarial Critic 具体ルール(30+) | 🔴 | Phase β |

#### Perception Layer

| Feature | Status | Notes |
|---|---|---|
| Stage 1: 音響特徴抽出 | 🔴 | librosa 統合 |
| Stage 2: use-case 駆動評価 | 🔴 | BGM/Game/Ad 別 |
| Stage 3: 抽象特徴参照照合 | 🔴 | style vector |

#### Rendering Layer

| Feature | Status | Notes |
|---|---|---|
| MIDI writer + stems | ✅ | per-instrument |
| Audio renderer(FluidSynth) | ✅ | optional 依存 |
| MIDI reader | ✅ | MIDI → ScoreIR 変換 |
| Iteration management | ✅ | v001/v002/... バージョン管理 |
| MusicXML writer | ⚪ | music21 経由 |
| LilyPond writer | ⚪ | lilypond CLI |
| Strudel emitter | ⚪ | ブラウザ即試聴 |
| Production manifest + mix chain | 🔴 | pedalboard 経由 |

#### Conductor & Subagents

| Feature | Status | Notes |
|---|---|---|
| Conductor(v2 pipeline 経由) | ✅ | PlanOrchestrator → NoteRealizer 経由 |
| Multi-candidate Conductor | 🔴 | 5 候補生成→批評→選定 |
| 7 Subagent definitions | ✅ | Markdown 完備 |
| Composer 実装 | 🟡 | 既存 generator が部分代行 |
| Adversarial Critic 実装 | 🔴 | Rule Registry 経由 |
| Producer 実装 | 🔴 | 統合判断ロジック |
| Mix Engineer 実装 | 🔴 | 定義のみ |
| Section-level regeneration | ✅ | Phase 1 完成 |

#### CLI & Commands

| Feature | Status | Notes |
|---|---|---|
| yao compose / conduct / render | ✅ | Phase 1 完成 |
| yao validate / evaluate / diff / explain | ✅ | Phase 1 完成 |
| yao new-project / regenerate-section | ✅ | Phase 1 完成 |
| yao preview(in-memory 再生) | 🔴 | v2.0 で導入 |
| yao watch(hot reload) | 🔴 | v2.0 で導入 |
| yao annotate(時刻 tag UI) | 🔴 | v2.0 で導入 |
| 7 slash commands | ✅ | sketch/compose/critique/regenerate-section/explain/render/arrange |

#### Skills & Knowledge

| Feature | Status | Notes |
|---|---|---|
| cinematic genre skill | ✅ | 唯一実装済み |
| 12+ genre skills target | 🔴 | lo-fi, J-Pop, jazz, EDM, game BGM 等 |
| Theory skills(4) | 🟡 | voice-leading, piano, tension-resolution, cinematic |
| Instrument skills(38 楽器) | 🔴 | 音域定数のみ、奏法 skill 未整備 |
| Psychology skills | 🔴 | 経験的マッピング未実装 |

#### CPIR(Layer 3a)

| Feature | Status | Notes |
|---|---|---|
| SongFormPlan | ✅ | SectionPlan + section_at_bar + JSON round-trip |
| HarmonyPlan | ✅ | ChordEvent + HarmonicFunction + CadenceRole |
| MusicalPlan(統合) | 🟢 | form + harmony のみ、motif/drum/arrangement は None |
| MotifPlan | ⚪ | skeleton のみ |
| PhrasePlan | ⚪ | skeleton のみ |
| DrumPattern | ⚪ | skeleton のみ |
| ArrangementPlan | ⚪ | skeleton のみ |

#### QA

| Feature | Status | Notes |
|---|---|---|
| Unit tests | ✅ | ~448 tests |
| Integration tests | ✅ | ~15 tests(v2 pipeline 含む) |
| Scenario tests | ✅ | ~16 tests(trajectory compliance 含む) |
| Music constraint tests | ✅ | 7 tests |
| Golden MIDI tests | ✅ | 6 baselines(3 specs × 2 realizers) |
| Architecture lint | ✅ | Layer boundary + Rule A enforcement |
| Capability matrix check | ✅ | tools/capability_matrix_check.py |

#### QA

| Feature | Status | Notes |
|---|---|---|
| Unit tests | ✅ | 207 件 |
| Integration tests | ✅ | 2 件 |
| Music constraint tests | ✅ | 7 件 |
| Scenario tests | ✅ | 10 件 |
| Trajectory compliance tests | 🔴 | v2.0 で導入(§7.4 を保証) |
| Golden MIDI tests | 🔴 | v2.0 で導入(§13) |
| Subagent eval tests | 🔴 | LLM-as-Judge |
| Architecture lint(7+1 層対応) | 🟡 | 7 層は ✅、3a/3b 細分は 🔴 |
| Capability Matrix check | 🔴 | tools/capability_matrix_check.py 必須 |

### Matrix の運用

- **すべての PR は Matrix の該当行を更新する**(更新なき PR は CI で reject)
- **README / CLAUDE.md は Matrix にリンクする**(能力主張の重複を禁ず)
- **`tools/capability_matrix_check.py`** が ✅ ✅ エントリの実装存在を AST 検証
- **Matrix は PROJECT.md §5(本セクション)が唯一の正本**

---

## 6. ディレクトリ構造

```
yao/
├── CLAUDE.md                      # エージェントへの不変指示
├── PROJECT.md                     # 本ファイル(プロジェクト全体設計)
├── README.md                      # ユーザ向けクイックスタート
├── pyproject.toml                 # Python依存
├── Makefile                       # 主要コマンド
│
├── .claude/
│   ├── commands/                  # 13 スラッシュコマンド(後述)
│   ├── agents/                    # 7 Subagent定義(変更なし)
│   ├── skills/                    # 専門知識モジュール
│   │   ├── genres/                # ★12+ ジャンル(v2.0 拡充)
│   │   ├── theory/
│   │   ├── instruments/
│   │   ├── psychology/            # ★v2.0 で実装
│   │   └── articulations/         # ★v2.0 で導入(楽器奏法)
│   ├── guides/                    # 5 開発者ガイド
│   └── hooks/                     # ★v2.0 で実装
│       ├── pre-commit-lint.sh
│       ├── post-generate-render.sh
│       ├── post-generate-critique.sh
│       └── update-provenance.sh
│
├── specs/
│   ├── projects/                  # ユーザの曲(7 例)
│   │   └── <project>/
│   │       ├── intent.md          # ★v2.0 で first-class
│   │       ├── composition.yaml   # v2 schema
│   │       ├── trajectory.yaml    # 多次元
│   │       ├── references.yaml
│   │       ├── negative-space.yaml
│   │       ├── arrangement.yaml   # 編曲時のみ
│   │       └── production.yaml
│   ├── templates/                 # 4 テンプレート
│   └── fragments/                 # ★v2.0:再利用可能スペック断片
│
├── src/
│   └── yao/
│       ├── constants/             # Layer 0
│       ├── schema/                # Layer 1
│       ├── ir/
│       │   ├── score_ir.py        # Layer 3b(既存)
│       │   ├── plan/              # ★v2.0 Layer 3a
│       │   │   ├── form.py
│       │   │   ├── harmony.py
│       │   │   ├── motif.py
│       │   │   ├── phrase.py
│       │   │   ├── drums.py
│       │   │   ├── arrangement.py
│       │   │   └── composition_plan.py
│       │   ├── trajectory.py      # 5 次元化
│       │   ├── timing.py
│       │   ├── notation.py
│       │   ├── voicing.py
│       │   └── motif.py           # 既存(transformations)
│       ├── generators/
│       │   ├── plan/              # ★v2.0 Plan Generator
│       │   │   ├── form_planner.py
│       │   │   ├── harmony_planner.py
│       │   │   ├── motif_planner.py
│       │   │   ├── drum_patterner.py
│       │   │   └── arranger.py
│       │   └── note/              # 既存を再配置
│       │       ├── rule_based.py
│       │       ├── stochastic.py
│       │       ├── markov.py      # ★v2.0
│       │       └── constraint_solver.py # ★v2.0
│       ├── perception/            # Layer 4(★v2.0 で実装)
│       │   ├── audio_features.py  # Stage 1
│       │   ├── use_case_targets.py # Stage 2
│       │   ├── reference_matcher.py # Stage 3
│       │   ├── psych_mapper.py
│       │   └── style_vector.py
│       ├── render/                # Layer 5
│       │   ├── midi_writer.py
│       │   ├── audio_renderer.py
│       │   ├── musicxml_writer.py # ★v2.0
│       │   ├── lilypond_writer.py # ★v2.0
│       │   ├── strudel_emitter.py # ★v2.0
│       │   └── production/        # ★v2.0:mix chain
│       │       ├── manifest.py
│       │       ├── mix_chain.py
│       │       └── mastering.py
│       ├── verify/                # Layer 6
│       │   ├── lint.py
│       │   ├── analyzer.py
│       │   ├── evaluator.py
│       │   ├── diff.py
│       │   ├── critique/          # ★v2.0:Critic Rule Registry
│       │   │   ├── base.py
│       │   │   ├── registry.py
│       │   │   ├── structural.py
│       │   │   ├── melodic.py
│       │   │   ├── harmonic.py
│       │   │   ├── rhythmic.py
│       │   │   ├── bass.py
│       │   │   ├── arrangement.py
│       │   │   └── emotional.py
│       │   ├── metric_goal.py     # ★v2.0
│       │   └── recoverable.py     # ★v2.0
│       ├── arrange/               # ★v2.0:Layer 5.5(編曲)
│       │   ├── analyzer.py
│       │   ├── plan_extractor.py
│       │   ├── style_vector.py
│       │   ├── transformer.py
│       │   └── differ.py
│       ├── conductor/
│       │   ├── conductor.py       # 拡張:Critic 統合
│       │   ├── multi_candidate.py # ★v2.0
│       │   └── feedback.py
│       ├── sketch/                # ★v2.0:NL → spec 対話
│       │   ├── compiler.py
│       │   ├── dialogue.py
│       │   └── mood_lexicon.py
│       ├── reflect/               # Layer 7
│       │   ├── provenance.py
│       │   ├── feedback_loop.py
│       │   └── style_profile.py   # ★v2.0
│       ├── errors.py
│       └── types.py
│   └── cli/                       # CLI(13 commands)
│
├── drum_patterns/                 # ★v2.0:12+ ジャンル別ドラム
│   ├── pop_8beat.yaml
│   ├── four_on_the_floor.yaml
│   ├── lofi_laidback.yaml
│   ├── jazz_swing.yaml
│   ├── trap_half_time.yaml
│   ├── bossa_nova.yaml
│   └── ...
│
├── references/
│   ├── catalog.yaml               # 権利状態必須
│   ├── extracted_features/        # 事前計算特徴量
│   └── README.md
│
├── outputs/                       # gitignored
│
├── soundfonts/                    # gitignored
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── music_constraints/
│   ├── scenarios/
│   ├── golden/                    # ★v2.0:bit-exact MIDI
│   └── subagent_evals/            # ★v2.0:LLM-as-Judge
│
├── tools/
│   ├── architecture_lint.py       # 7+1 層対応に拡張
│   └── capability_matrix_check.py # ★v2.0
│
└── docs/
    ├── design/                    # ADR
    ├── for-musicians/             # ★v2.0:作曲家向け tutorial
    ├── for-developers/            # ★v2.0:開発者ガイド
    ├── showcase/                  # ★v2.0:dogfooded 楽曲
    └── glossary.md
```

---

## 7. Composition Plan IR(CPIR)— v2.0 の心臓部

### 7.1 なぜ計画 IR が必要か

Phase 1 の generator は spec から直接 ScoreIR を生成しています:

```
spec → Generator → ScoreIR(notes)
```

このパスには **計画という中間概念がありません**。結果として:

- メロディは「スケール内音符をコントゥール沿いに配置した連続」になる
- フレーズ構造(antecedent-consequent)が無い
- モチーフの展開(sequence / inversion / retrograde)が IR に定義されているのに使われない
- 対旋律が無い
- Critic が批評できるのは「最終 MIDI」だけ

これは個別の機能不足ではなく、**「計画」という抽象概念の欠如**による構造的な限界です。

v2.0 は以下のパスに進化します:

```
spec → PlanGenerator(s) → CompositionPlan → NoteRealizer → ScoreIR
                              ↑
                         批評可能・編集可能・差分可能
```

### 7.2 CPIR の構成要素

`src/yao/ir/plan/` 配下に、6 種類の Plan IR を配置します。すべて frozen dataclass、すべて Provenance 対応です。

#### FormPlan(楽曲全体の構造)

```python
@dataclass(frozen=True)
class SectionPlan:
    id: str                         # "intro", "verse", "chorus", ...
    start_bar: int
    bars: int
    role: SectionRole               # intro/verse/pre_chorus/chorus/bridge/outro/...
    target_density: float           # [0,1]
    target_tension: float           # [0,1]
    is_climax: bool = False

@dataclass(frozen=True)
class FormPlan:
    sections: list[SectionPlan]
    climax_section_id: str

    def section_at_bar(self, bar: int) -> SectionPlan | None: ...
    def total_bars(self) -> int: ...
```

#### HarmonyPlan(機能・終止・テンション)

```python
@dataclass(frozen=True)
class ChordEvent:
    section_id: str
    start_beat: float
    duration_beats: float
    roman: str                      # "I", "vi", "V/V", "bVII"
    function: HarmonicFunction      # tonic/subdom/dom/predom/other
    tension_level: float            # [0,1]
    cadence_role: CadenceRole | None # half/authentic/plagal/deceptive

@dataclass(frozen=True)
class HarmonyPlan:
    chord_events: list[ChordEvent]
    cadences: dict[str, CadenceRole]  # section_id → cadence
    modulations: list[ModulationEvent]
    tension_resolution_points: list[float]

    def chord_at_beat(self, beat: float) -> ChordEvent | None: ...
```

これにより、単に `[C, G, Am, F]` を並べるのではなく:
- サビ終端で強い終止(authentic cadence)
- B メロでドミナント方向に緊張(predom → dom 連鎖)
- A メロは曖昧な終止(half cadence)

といった**機能的な設計**が可能になります。

#### MotifPlan(主題と展開)

```python
@dataclass(frozen=True)
class Motif:
    id: str
    rhythm_shape: tuple[float, ...] # IOIs in beats
    interval_shape: tuple[int, ...] # semitones
    identity_strength: float        # how distinctive

@dataclass(frozen=True)
class MotifTransformation:
    type: Literal["sequence_up", "sequence_down", "inversion",
                  "retrograde", "augmentation", "diminution",
                  "varied_rhythm", "varied_intervals"]
    intensity: float

@dataclass(frozen=True)
class MotifPlan:
    seeds: list[Motif]              # 主要モチーフ群
    transformations: dict[str, list[MotifTransformation]]
```

これにより、出力が **「ランダムな音の連続」**から **「主題が記憶可能で、変奏で発展する楽曲」** に変わります。これが Phase 1 出力の「音楽的浅さ」を解消する最大の鍵です。

#### PhrasePlan(フレーズ構造)

```python
@dataclass(frozen=True)
class PhrasePlan:
    section_id: str
    bars_per_phrase: float
    pattern: Literal["AABA", "ABAC", "AB", "stand_alone"]
    motif_sequence: list[str]       # motif ids
    contour: ContourShape           # rise/fall/arch/wave
    cadence_strength: float
    call_response_role: Literal["call", "response", "none"]
```

これは antecedent-consequent(問いかけ-応答)構造を generator に強制する仕組みです。

#### DrumPattern(ドラムをファーストクラス市民に)

```python
class KitPiece(str, Enum):
    KICK = "kick"
    SNARE = "snare"
    RIM = "rim"
    CLOSED_HAT = "closed_hat"
    OPEN_HAT = "open_hat"
    CLAP = "clap"
    TOM_LOW = "tom_low"
    TOM_MID = "tom_mid"
    TOM_HIGH = "tom_high"
    CRASH = "crash"
    RIDE = "ride"
    SHAKER = "shaker"

@dataclass(frozen=True)
class DrumHit:
    time: Beat
    duration: Beat
    kit_piece: KitPiece
    velocity: int
    microtiming_ms: float = 0.0     # 正=後ノリ、負=前ノリ
    is_ghost: bool = False

@dataclass(frozen=True)
class DrumPattern:
    id: str
    genre: str
    time_signature: str
    bars: int
    hits: list[DrumHit]
    swing: float
    humanize: float
    fills_at: list[FillLocation]
```

これは Phase 1 で粗粒度だったリズム表現を **完全に独立した IR** に格上げします。`drum_patterns/` 配下に 12+ ジャンル分のテンプレートを整備します。

#### ArrangementPlan(楽器配置・対旋律)

```python
@dataclass(frozen=True)
class CounterMelodySpec:
    target_instrument: str
    follows: str                    # main melody instrument
    density_factor: float           # main の何割の密度か
    motion_preference: Literal["contrary", "oblique", "parallel"]

@dataclass(frozen=True)
class ArrangementLayer:
    instrument: str
    role: Role                      # melody/bass/harmony/counter/pad
    register: str                   # "low" | "mid" | "high"
    density_factor: float
    pattern_family: str
    active_sections: list[str]
    articulation: Articulation      # ★v2.0:奏法

@dataclass(frozen=True)
class ArrangementPlan:
    layers: list[ArrangementLayer]
    counter_melody_lines: list[CounterMelodySpec]
    drum_pattern: DrumPattern
    texture_curve: TrajectoryCurve
```

#### CompositionPlan(統合)

```python
@dataclass(frozen=True)
class CompositionPlan:
    """The integrated middle representation. The crown jewel of v2.0."""
    intent: str                     # intent.md の正規化
    form: FormPlan
    harmony: HarmonyPlan
    motifs: MotifPlan
    phrases: list[PhrasePlan]       # per section
    drums: DrumPattern
    arrangement: ArrangementPlan
    trajectory: MultiDimensionalTrajectory
    provenance: ProvenanceLog

    def is_complete(self) -> bool: ...
    def to_json(self) -> str: ...
```

### 7.3 7 ステップ生成パイプライン

CPIR を中心に据えると、生成プロセスは 7 ステップに整理されます:

```
[Step 1: Form Planner]      Spec + Trajectory  →  FormPlan
      ↓
[Step 2: Harmony Planner]                       →  HarmonyPlan
      ↓
[Step 3: Motif Planner]                         →  MotifPlan + PhrasePlan
      ↓
[Step 4: Drum Patterner]                        →  DrumPattern
      ↓
[Step 5: Arranger]                              →  ArrangementPlan
      ↓
═══ Composition Plan COMPLETE ═══
═══ Critic Gate(§9 で詳述) ═══
      ↓
[Step 6: Note Realizer]     CompositionPlan  →  ScoreIR
      ↓
[Step 7: Renderer]          ScoreIR  →  MIDI / Audio / Score
```

### 7.4 Trajectory の真の活用

v2.0 では Trajectory を **全 Plan Generator が共通参照する制御信号** に格上げします。velocity だけを変えるのではなく、各次元が異なる音楽パラメータに連動します。

#### Trajectory の 5 次元

```yaml
trajectories:
  tension:                          # 緊張度
    type: bezier
    waypoints: [[0, 0.2], [16, 0.85], [32, 0.3]]

  density:                          # 音数密度
    type: stepped
    sections: { intro: 0.3, verse: 0.5, chorus: 0.9, outro: 0.3 }

  predictability:                   # 予測可能性
    type: linear
    target: 0.65
    variance: 0.15

  brightness:                       # ★v2.0:明るさ
    type: bezier
    waypoints: [[0, 0.4], [32, 0.85], [64, 0.5]]

  register_height:                  # ★v2.0:平均音高
    type: stepped
    sections: { verse: 0.45, chorus: 0.7 }
```

#### 各 Generator の応答ルール

| Generator | tension ↑ への応答 |
|---|---|
| **HarmonyPlanner** | secondary dominants(V/V)、borrowed chords(bVII)、suspensions、テンション音(7th/9th/11th)を増やす |
| **MotifPlanner** | より大きな跳躍、より高い音域、変奏度を上げる |
| **DrumPatterner** | subdivision を細分化(8分→16分)、ghost notes を増やす、syncopation 増加 |
| **Arranger** | 同時発音層を増やす、register spread 拡大 |
| **NoteRealizer** | velocity を上げる、articulation を marcato に |

| Generator | brightness ↑ への応答 |
|---|---|
| **HarmonyPlanner** | major chord 比率増、Lydian モード使用 |
| **Arranger** | 高音域楽器の比率増、ピッコロ・グロッケンシュピール等を呼ぶ |

これらは **Trajectory Compliance Test**(§13)で機械的に検証されます。velocity 以外への応答が無ければ test が fail します。

---

## 8. Subagent 設計(v1.0 から拡張)

YaO の楽団員は明確な役割と制約を持ちます。v2.0 では各 Subagent が **CPIR の特定ドメイン**を担当します(Phase 1 では役割が抽象的でしたが、CPIR で実装上の責任分担が明確になります)。

### 8.1 Composer(作曲家)

**責任:** モチーフ・フレーズ・主題の生成
**入力:** intent.md, composition.yaml, trajectory.yaml, references.yaml
**出力:** **MotifPlan + PhrasePlan**(v2.0 で明確化)
**禁止事項:** 楽器選択・最終ヴォイシング(これは Orchestrator の仕事)
**評価軸:** モチーフの記憶性・反復と変奏のバランス・軌跡への適合度

### 8.2 Harmony Theorist(和声理論家)

**責任:** コード進行・転調・代理コード・終止の設計
**入力:** Composer の主旋律案、composition.yaml の harmony セクション
**出力:** **HarmonyPlan**(機能和声・カデンツ・テンション解決)
**評価軸:** 機能整合性・テンション解決・ジャンル適合性

### 8.3 Rhythm Architect(リズム設計者)

**責任:** ドラムパターン・グルーヴ・シンコペーション・フィル
**入力:** composition.yaml の rhythm/drums セクション、ジャンル指定
**出力:** **DrumPattern**(v2.0 で IR が独立)
**評価軸:** グルーヴ感・人間味・セクション間コントラスト

### 8.4 Orchestrator(編成者)

**責任:** 楽器割り当て・ヴォイシング・音域配置・**対旋律**
**入力:** Composer/Harmony/Rhythm の出力すべて
**出力:** **ArrangementPlan**(対旋律含む)
**評価軸:** 周波数空間の衝突回避・楽器の慣用的使用・テクスチャ密度

### 8.5 Adversarial Critic(敵対的批評家)

**責任:** あらゆる弱点の発見と指摘
**入力:** **CompositionPlan**(主)+ ScoreIR(従)
**出力:** **list[Finding]**(構造化、§9 で詳述)
**特性:** **賞賛しないことが原則**
**評価軸:** 問題発見の網羅性と具体性

v2.0 における重要な変更:**Critic は計画レベルで批評する**。最終 MIDI ではなく CompositionPlan を見ることで、より深い問題(クリシェ進行、climax 不在、構造的退屈さ)を批評可能。

### 8.6 Mix Engineer(ミックスエンジニア)

**責任:** ステレオ配置・ダイナミクス・周波数マスキング解消・ラウドネス管理
**入力:** Orchestrator の出力 + production パラメータ
**出力:** ミックス指示書 + 実 audio 処理(pedalboard 経由)
**評価軸:** LUFS 基準達成・周波数バランス・ステレオ広がり

### 8.7 Producer(プロデューサ)

**責任:** 全体統合・優先順位付け・指揮者(人間)との対話・最終判断
**入力:** すべての Subagent の出力 + 人間からのフィードバック
**出力:** 最終的な制作判断・次の反復への指示
**特権:** 唯一、他の Subagent の出力を却下・差し戻しできる
**評価軸:** 楽曲の意図(intent.md)への忠実度

### 8.8 Subagent → Pipeline Step マッピング

```
Step 1 Form Planner       ← Producer(form は meta-decision)
Step 2 Harmony Planner    ← Harmony Theorist
Step 3 Motif Planner      ← Composer
Step 4 Drum Patterner     ← Rhythm Architect
Step 5 Arranger           ← Orchestrator
Critic Gate               ← Adversarial Critic
Step 6 Note Realizer      ← Composer(low-level)
Step 7 Renderer           ← Mix Engineer
```

これにより、Subagent 定義(`.claude/agents/*.md`)の責任が **実装上のステップに 1 対 1 対応** します。

---

## 9. 作曲認知プロトコル × Critic Gate

### 9.1 6 相認知プロトコル(v1.0 から維持)

YaO の `/compose` および `/arrange` コマンドは、Claude Code に以下の 6 相を**順序通り**実行させます。

| Phase | 内容 | v2.0 でのパイプライン対応 |
|---|---|---|
| 1. Intent Crystallization | intent.md を確定 | Pre-pipeline |
| 2. Architectural Sketch | trajectory.yaml を描く | Step 1 + trajectory.yaml |
| 3. Skeletal Generation | 5〜10 候補生成 | Steps 2-5 を 5 並列 |
| 4. Critic-Composer Dialogue | 批評と統合 | **Critic Gate** |
| 5. Detailed Filling | 詳細埋め | Steps 6-7 |
| 6. Listening Simulation | Perception 評価 | Layer 4 → Trajectory ループバック |

v1.0 では Phase 4「対話」の実装メカニズムが不明瞭でしたが、v2.0 では **Critic Gate** が具体的実装になります。

### 9.2 Critic Gate ★v2.0

Step 5 と Step 6 の間で、Adversarial Critic が CompositionPlan を批評します:

```python
def conduct_with_critic_gate(spec, max_iterations=3):
    for iteration in range(max_iterations):
        # Phase 3: Skeletal Generation(5 候補)
        candidates = [build_plan(spec, seed=base_seed+i) for i in range(5)]

        # Phase 4: Critic-Composer Dialogue
        critiques = [critic.critique(plan) for plan in candidates]
        winner_plan = producer.select(candidates, critiques, intent)

        if any(f.severity == "critical" for f in critiques[winner_idx]):
            # Critic が critical 問題を発見 → 計画を修正
            spec = adapt_for_critique(spec, critiques[winner_idx])
            continue

        # Phase 5: Detailed Filling
        score = realize_notes(winner_plan)

        # Phase 6: Listening Simulation
        if perception_layer_diverges(score, intent):
            continue

        return ConductorResult(...)
```

### 9.3 評価の三本柱

#### Pillar 1: MetricGoal type system ★v2.0

v1.0 の `passed = abs(score - target) <= tolerance` を多型化:

```python
class MetricGoalType(str, Enum):
    AT_LEAST       = "at_least"      # 高いほど良い
    AT_MOST        = "at_most"       # 低いほど良い
    TARGET_BAND    = "target_band"   # 目標値周辺
    BETWEEN        = "between"       # 範囲内
    MATCH_CURVE    = "match_curve"   # 曲線追従
    RELATIVE_ORDER = "relative_order" # セクション間順序
    DIVERSITY      = "diversity"     # 分散・エントロピー

@dataclass(frozen=True)
class MetricGoal:
    type: MetricGoalType
    # type に応じて使うフィールドが異なる
    target: float | None = None
    tolerance: float = 0.0
    min_value: float | None = None
    max_value: float | None = None
    target_curve: list[tuple[float, float]] | None = None
    expected_order: list[str] | None = None
```

これにより「consonance ratio が高すぎて不合格」のような不合理な判定が消失します。

#### Pillar 2: Critic Rule Registry ★v2.0

30+ ルールを Role × Severity マトリクスで管理:

```python
@dataclass
class Finding:
    rule_id: str
    severity: Literal["critical", "major", "minor", "suggestion"]
    role: Role                       # melody/harmony/rhythm/bass/arrangement/structure/emotional
    issue: str                       # "chorus_lacks_lift"
    evidence: dict                   # 数値的証拠
    location: SongLocation | None
    recommendation: dict             # 各 role への具体的修正案
```

実装する 30+ ルール(role 別):

| Role | Rule(主要) |
|---|---|
| **Structural** | ClimaxAbsence, SectionMonotony, FormImbalance, LoopabilityFailure, BuildupAbsence |
| **Melodic** | ClicheMotif, PhraseClosureWeakness, ContourMonotony, MemorabilityProxy, ExcessiveLeaps, RangeTooNarrow |
| **Harmonic** | ClicheChordProgression, VoiceCrossing, CadenceWeakness, ParallelFifths, SecondaryDominantAbsence, ModalIntermixOpportunity |
| **Rhythmic** | RhythmicMonotony, SyncopationLack, DownbeatAmbiguity, GrooveInconsistency, FillsAbsence |
| **Bass** | RootSupportFailure, KickConflict, RegisterInstability, WalkingBassCliche |
| **Arrangement** | FrequencyCollision, TextureCollapse, LayerImbalance, CounterMelodyAbsence |
| **Emotional** | IntentDivergence, TrajectoryViolation, MoodIncongruence |

#### Pillar 3: RecoverableDecision ★v2.0

silent fallback を **記録された妥協** に置き換え:

```python
@dataclass(frozen=True)
class RecoverableDecision:
    code: str                        # "BASS_NOTE_OUT_OF_RANGE"
    severity: Literal["info", "warning", "error"]
    original_value: Any
    recovered_value: Any
    reason: str
    musical_impact: str              # 人間に伝わる影響記述
    suggested_fix: list[str]         # 上流での修正提案
```

既存コード内の silent な clamp/fallback(stochastic.py の bass note range fallback など)をすべてこの仕組みに置換。Provenance Log に記録され、評価レポートに露出。次反復の adapter が直接対処可能になります。

### 9.4 Use-case 駆動評価 ★v2.0

`production.yaml` の `use_case` フィールドが評価軸を切り替えます:

```yaml
production:
  use_case: "youtube_bgm"   # | "game_bgm" | "advertisement" | "study_focus" | "general"
```

| use_case | 追加される評価指標 |
|---|---|
| `youtube_bgm` | vocal_space_score, loopability, fatigue_risk, lufs_target_match |
| `game_bgm` | loop_seam_smoothness, tension_curve_match, repetition_tolerance |
| `advertisement` | hook_entry_time(< 7s), energy_peak_position, short_form_memorability |
| `study_focus` | low_distraction_score, dynamic_stability, predictability |
| `general` | 既存の汎用指標のみ |

これは現状の YaO に欠けている **「目的別の品質基準」** を構造化する仕組みです。

---

## 10. パラメータ仕様(v2.0 拡張)

YaO は楽曲を、以下の **8 種類の YAML/Markdown ファイル**で完全に記述します。

| File | Format | Role |
|---|---|---|
| `intent.md` | Markdown | 楽曲の魂を 1〜3 文で記述 |
| `composition.yaml` | YAML(v2 schema) | 詳細な作曲パラメータ |
| `trajectory.yaml` | YAML | 5 次元軌跡 |
| `references.yaml` | YAML | 美的参照(正・負)|
| `negative-space.yaml` | YAML | 否定空間設計 |
| `arrangement.yaml` | YAML | 編曲パラメータ(編曲時のみ) |
| `production.yaml` | YAML | ミックス・use_case |
| `provenance.json` | JSON | 自動生成、追記専用 |

### 10.1 composition.yaml v2 schema

v1 schema は基本要素のみでしたが、v2 は **11 セクション** に拡張:

```yaml
version: "2"

identity:
  title: "Neon Morning"
  purpose: "product demo bgm"
  duration_sec: 90
  loopable: true

global:
  key: "D major"
  bpm: 128
  time_signature: "4/4"
  genre: "future_pop"

emotion:                             # ★v2.0
  valence: 0.8                       # 明るさ
  energy: 0.75
  tension: 0.45
  warmth: 0.6
  nostalgia: 0.3

form:
  sections:
    - id: intro
      bars: 4
      density: 0.25
    - id: verse
      bars: 8
      density: 0.45
    - id: chorus
      bars: 8
      density: 0.9
      climax: true

melody:                              # ★v2.0:細密化
  range: { min: "A3", max: "E5" }
  contour: "arch"
  motif:
    length_beats: 2
    repetition_rate: 0.65
    variation_rate: 0.35
  intervals:
    stepwise_ratio: 0.7
    max_leap: "P5"
  phrase:
    bars_per_phrase: 4
    pattern: "AABA"
    call_response: true

harmony:                             # ★v2.0:機能重視
  complexity: 0.55
  chord_palette: [I, V, vi, IV, ii, "V/V"]
  cadence:
    verse: "half"
    chorus: "authentic"
  harmonic_rhythm:
    verse: "1 chord per bar"
    chorus: "2 chords per bar"

rhythm:
  groove: "four_on_the_floor"
  swing: 0.08
  syncopation: 0.35

drums:                               # ★v2.0:first-class
  pattern_family: "pop_8beat"
  swing: 0.1
  ghost_notes_density: 0.3
  fills_at: ["pre_chorus_end", "bridge_end"]

arrangement:                         # ★v2.0:奏法・対旋律
  instruments:
    drums: { role: rhythm, pattern_family: electro_pop }
    bass:  { role: bass, motion: "root_octave_passing" }
    pad:   { role: harmony, voicing: "wide", articulation: "legato" }
    lead:  { role: melody, articulation: "pluck" }
  counter_melody:
    enabled_sections: [chorus_repeat, bridge]

production:
  use_case: "youtube_bgm"            # ★v2.0:評価軸を駆動
  target_lufs: -16
  stereo_width: 0.7
  vocal_space_reserved: true

constraints:
  - { kind: must, rule: "melody_within_range", scope: global, severity: error }
  - { kind: must, rule: "chorus_density > verse_density", scope: section_relation }
  - { kind: prefer, rule: "motif_repetition_rate in [0.5, 0.8]", scope: "section:verse" }
  - { kind: avoid, rule: "consecutive_leaps > 2", scope: "instrument:violin" }

generation:
  plan_strategy: "rule_based"        # ★v2.0:Plan 戦略
  realize_strategy: "stochastic"     # ★v2.0:Note 戦略
  seed: 42
  temperature: 0.5
```

v1 spec との互換性は **legacy adapter** で維持します(Phase β 末で removed)。

### 10.2 trajectory.yaml(5 次元化)

§7.4 の通り、5 次元(tension / density / predictability / brightness / register_height)に拡張。

### 10.3 intent.md の first-class 化

`intent.md` は楽曲の魂を 1〜3 文で記す **第一級資産** です。自動評価指標が衝突した時の最終裁定者でもあります。

> 例:「初夏の朝、新しい挑戦に向かう前向きな期待感。ただし不安も微かに混じる。爽やかすぎず、感傷的すぎない、ニュートラルな高揚」

intent.md は SpecCompiler(§11)による spec 生成のシードでもあり、Adversarial Critic の `IntentDivergenceDetector` の判定基準でもあります。

### 10.4 spec composability ★v2.0

再利用可能な spec 断片を `specs/fragments/` に配置:

```yaml
# specs/projects/my-song/composition.yaml
extends:
  - "fragments/lofi_hiphop_base.yaml"
  - "fragments/90sec_bgm_form.yaml"

overrides:
  identity:
    title: "Coffee Cat"
  emotion:
    nostalgia: 0.8     # base からの差分
```

これにより、テンプレートの硬直を解消し、ユーザの再利用性を高めます。

---

## 11. SpecCompiler — 自然言語の昇華 ★v2.0

### 11.1 課題

Phase 1 の Conductor は、自然言語入力(`yao conduct "a calm piano piece in D minor"`)を mood キーワード辞書で解釈していました。これには以下の問題があります:

- 日本語非対応(「切ない」「儚い」「軽快な」「壮大」等)
- キーワード優先順位の脆弱性(「very fast」が「fast」に先にマッチ)
- 複合表現(「明るいが少し切ない」)の処理が単純化
- ambiguity(曖昧さ)を人間に確認する仕組みが無い

### 11.2 解:SpecCompiler の独立化

`src/yao/sketch/compiler.py` を独立モジュールとして実装:

```python
class SpecCompiler:
    """Compile natural language description into a CompositionSpec draft."""

    def compile(self, description: str, language: Literal["en", "ja", "auto"] = "auto") -> SpecDraft:
        normalized = self._normalize_text(description, language)
        facts = self._extract_explicit_facts(normalized)        # "90 seconds", "D minor"
        emotion = self._infer_emotion(normalized)               # valence/arousal vector
        instrumentation = self._infer_instrumentation(normalized, emotion)
        structure = self._infer_structure(normalized, facts.duration)
        trajectory = self._design_trajectory(emotion, structure)

        spec = self._assemble_spec(facts, emotion, instrumentation, structure)
        assumptions = self._record_assumptions(facts, emotion, instrumentation, structure)
        ambiguities = self._detect_ambiguities(facts, emotion)

        return SpecDraft(
            spec=spec,
            trajectory=trajectory,
            assumptions=assumptions,
            ambiguities=ambiguities,
            confidence_score=...
        )
```

### 11.3 多言語 Mood Lexicon

`src/yao/sketch/mood_lexicon.py`:

```python
JAPANESE_MOOD_TERMS = {
    "明るい": MoodVector(valence=0.85, energy=0.6),
    "切ない": MoodVector(valence=0.3, energy=0.4, nostalgia=0.7),
    "儚い": MoodVector(valence=0.4, energy=0.3, nostalgia=0.8, fragility=0.8),
    "軽快な": MoodVector(valence=0.75, energy=0.75),
    "壮大": MoodVector(valence=0.7, energy=0.8, scale=0.9),
    "不穏": MoodVector(valence=0.25, energy=0.5, tension=0.85),
    "疾走感": MoodVector(valence=0.6, energy=0.95, tempo_hint=140),
    "浮遊感": MoodVector(valence=0.6, energy=0.4, atmosphere=0.85),
    "透明感": MoodVector(valence=0.65, energy=0.4, brightness=0.85),
    "ゲーム音楽っぽい": MoodVector(use_case_hint="game_bgm"),
    "ナレーションを邪魔しない": MoodVector(use_case_hint="bgm_under_narration",
                                          frequency_avoid="vocal_range"),
    # ... 100+ entries
}

ENGLISH_MOOD_TERMS = { ... }  # 既存資産を統合
```

### 11.4 Ambiguity Resolution Dialogue

スケッチが曖昧な場合、SpecCompiler は確認質問を返します:

```yaml
# spec_draft.yaml(SpecCompiler 出力)
spec_draft:
  confident_fields:
    key: "D minor"
    duration_sec: 90
  inferred_fields:
    bpm: 90
    instrumentation: ["piano", "cello"]
  ambiguities:
    - field: "tempo"
      reason: "no tempo cue in description"
      options: [80, 90, 100]
    - field: "form"
      reason: "duration could be intro-A-B-A or just intro-A"
      options: ["intro-verse-chorus-outro", "AABA", "through-composed"]
  questions_to_ask_human:
    - "どのくらいのテンポをイメージしていますか?"
```

これは `/sketch` slash command が呼び出して、対話的に詰めていく仕組みです。

---

## 12. ジャンル拡張・楽器奏法 ★v2.0

### 12.1 ジャンル Skills の充実(目標 12+)

Phase 1 では cinematic Skill のみ。v2.0 では 12+ ジャンル:

```
.claude/skills/genres/
├── cinematic.md (✅ 実装済み)
├── lofi_hiphop.md
├── j_pop.md
├── neoclassical.md
├── ambient.md
├── jazz.md
├── edm.md
├── folk.md
├── game_bgm.md
├── anime_bgm.md
├── rock.md
├── orchestral.md
└── pairs/                          # ★Generator 用 YAML
    ├── lofi_hiphop.yaml
    ├── j_pop.yaml
    └── ...
```

各ジャンルは **Markdown(LLM 用) + YAML(Generator 用)** のペアで提供されます。YAML はマシン可読:

```yaml
# .claude/skills/genres/pairs/lofi_hiphop.yaml
genre: "lofi_hiphop"

tempo:
  median: 75
  range: [65, 95]

keys:
  major_preferred: ["F", "C", "G"]
  minor_preferred: ["Am", "Em", "Dm"]
  modal: ["Dorian", "Mixolydian"]

chord_progressions:
  - { progression: ["i", "VI", "III", "VII"], confidence: 0.30, sections: ["verse", "chorus"] }
  - { progression: ["ii", "V", "i"], confidence: 0.25, sections: ["bridge"] }
  - { progression: ["I", "vi", "IV", "V"], confidence: 0.10, sections: ["chorus"] }

drum_pattern: "lofi_laidback"        # references drum_patterns/lofi_laidback.yaml

instrumentation:
  core: ["felt_piano", "warm_upright_bass", "dusty_kit"]
  common_additions: ["rhodes", "vinyl_noise"]
  avoid: ["bright_synth_lead", "hi_hat_open_long"]

iconic_motif_shapes:
  - rhythm: [0.5, 0.5, 1.0, 1.0]
    intervals: [0, 2, 0, -2]

cadences:
  primary: "plagal"
  secondary: "modal_iv_to_i"

cliches_to_avoid:
  - description: "Vinyl crackle alone makes it Lo-fi"
    severity: warning

quality_heuristics:
  - "Avoid bright/clean sounds; embrace texture"
  - "Swing 0.55-0.65 feels right"
```

### 12.2 楽器奏法システム ★v2.0

Phase 1 では楽器は「名前 + GM プログラム + 音域」のみ。v2.0 で **奏法(Articulation)** を追加:

```python
class Articulation(str, Enum):
    # 弦楽器
    LEGATO = "legato"
    STACCATO = "staccato"
    PIZZICATO = "pizzicato"
    TREMOLO = "tremolo"
    SPICCATO = "spiccato"
    SUL_PONTICELLO = "sul_ponticello"
    HARMONICS = "harmonics"
    # 鍵盤
    SUSTAIN = "sustain"
    STACCATO_KEY = "staccato_key"
    # 管楽器
    FLUTTER = "flutter"
    GROWL = "growl"
    SUBTONE = "subtone"
    # 共通
    NORMAL = "normal"
    ACCENT = "accent"
    MARCATO = "marcato"
    LIGHT = "light"
```

スペックでの利用:

```yaml
instruments:
  - name: violin
    role: melody
    default_articulation: legato
    section_overrides:
      verse: legato
      chorus: marcato
      bridge: spiccato
      outro: pizzicato
```

### 12.3 DrumPattern Library

`drum_patterns/` 配下に 12+ ジャンル:

```
drum_patterns/
├── pop_8beat.yaml
├── four_on_the_floor.yaml
├── lofi_laidback.yaml
├── trap_half_time.yaml
├── rock_backbeat.yaml
├── jazz_swing_ride.yaml
├── bossa_nova.yaml
├── reggae_one_drop.yaml
├── funk_16th.yaml
├── ballad_brushed.yaml
├── game_16bit_drive.yaml
└── cinematic_orchestral.yaml
```

各ファイルは DrumPattern IR 構造の YAML 表現で、Drum Patterner が機械参照します。

---

## 13. 編曲エンジン(Arrangement Engine)★v2.0 強化

### 13.1 課題

新曲生成だけなら他の AI でもできます。**YaO の差別化要素は、既存曲を解析・構造化して、保持と変換を分離した編曲ができることです**。Phase 1 では `/arrange` slash command の定義のみで、エンジン本体は未実装でした。

### 13.2 パイプライン

```
[Input]      MIDI / MusicXML / (optional audio with stems)
   ↓
[Analyzer]   Section detection, melody extraction, chord estimation,
             motif detection, role classification
   ↓
[SourcePlan] = CPIR of input piece(★CPIR があるから可能)
   ↓
[Preservation Plan]   melody, hook rhythm, chord function, form
[Transformation Plan] genre, bpm, reharm, regroove, reorch
   ↓
[Style Vector Op]
   target_plan = source_plan
                 - vec(source_genre)
                 + vec(target_genre)
                 ⊕ preservation_constraints
   ↓
[TargetPlan] = CPIR of arranged piece
   ↓
[Note Realizer]  → ScoreIR → MIDI / audio
   ↓
[Arrangement Diff]  Markdown report:preserved / changed / risks
   ↓
[Evaluation]
```

### 13.3 なぜ CPIR が編曲を可能にするか

編曲を **音符レベル** で扱うと脆弱です:pitch substitution、tempo stretching、instrument remapping は表面的な操作。

編曲を **計画レベル** で扱うと堅牢です:harmonic function を保持してヴォイシングを変える、motif identity を保持してリズム形状を変える、form 構造を保持して dynamics curve を変える。

CPIR が無ければこの構造的編曲はできません。これが「v2.0 で編曲が初めて可能になる」根拠です。

### 13.4 編曲スペック

```yaml
arrangement:
  input:
    file: "inputs/original.mid"
    rights_status: "owned_or_licensed"  # 必須

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

### 13.5 Arrangement Diff

```markdown
# Arrangement Diff(v003)

## Preserved
- Main hook melodic similarity: 0.91 ✓
- Section form: unchanged ✓
- Chord function similarity: 0.82 ✓

## Changed
- BPM: 128 → 86
- Groove: straight pop → swung lo-fi
- Chords: triads → 7th/9th voicings(35% reharm depth)
- Bass: root → walking with passing tones
- Drums: four-on-floor → laid-back backbeat

## Risks(Adversarial Critic)
- chorus_energy_drop: dropped more than requested(target -20%, actual -38%)
- register_shift: melody preserved but feels lower due to instrumentation
```

---

## 14. 知覚代替層(Perception Substitute Layer)実装 ★v2.0

### 14.1 なぜ必要か

LLM は音楽を聴けません。しかし YaO は最終的に音響的成果物(WAV)を作ります。シンボリック評価だけでは、音色・空間・低域密度・耳障りさ・ナレーションとの干渉などを捉えられません。

### 14.2 3 段階実装

| Stage | 目的 | 技術 |
|---|---|---|
| **Stage 1: 音響特徴抽出** | LUFS, spectral, onset density | librosa, pyloudnorm |
| **Stage 2: use-case 駆動評価** | BGM/Game/Ad/Study 別の品質基準 | YaO ドメインルール |
| **Stage 3: 抽象特徴参照照合** | 参照楽曲との style vector 比較 | 自前計算 |

### 14.3 Stage 3 の倫理:抽象特徴のみ

Stage 3 の reference matching は、**抽象特徴のみ比較可能**で、メロディ・コード進行・identifiable hooks は **schema レベルでブロック**します:

```yaml
references:
  inspirations:
    - file: refs/anchor_a.wav
      compare:
        - tempo
        - density_curve
        - spectral_balance
        - section_energy
        - groove_profile
      do_not_copy:
        - melody                    # 禁止
        - chord_progression         # 禁止
        - identifiable_hook         # 禁止
```

`do_not_copy` は固定 allowlist。これにより「Joe Hisaishi 風」のような名指し模倣が **schema レベルで** 禁止されます。

### 14.4 Listening Simulation

Conductor の Phase 6 で Perception Layer を起動し、**生成物が intent.md と乖離していないか**を測定。乖離が閾値超えなら該当セクションを再生成します。

これにより、「数値スコアは良いが intent と違う」状態を構造的に検出できます。

---

## 15. Custom Commands(指揮者の指示棒)

| Command | Status v2.0 target | Purpose |
|---|---|---|
| `/sketch` | Full impl | NL → spec dialogue(状態機械) |
| `/compose <project>` | Multi-candidate | フルパイプラインで生成 |
| `/critique <iteration>` | Plan-level + Rule-based | 構造化 Findings |
| `/regenerate-section <project> <section>` | Plan-aware | 該当 section の plan のみ再構築 |
| `/morph <from> <to> <bars>` | Plan-vector op | 2 計画間の補間 |
| `/improvise <input>` | Live mode | リアルタイム伴奏 |
| `/explain <element>` | Plan-traced | CPIR Provenance を辿る |
| `/diff <iter_a> <iter_b>` | Plan + score | 計画と音符の両レベル diff |
| `/render <iteration>` | Production-aware | manifest 適用、audio 出力 |
| `/arrange <project>` | Full engine | 編曲パイプライン |
| `/preview` ★new | In-memory 即時再生 | sounddevice 経由 |
| `/watch <spec>` ★new | File watch + auto-regenerate | hot reload |
| `/annotate <iteration>` ★new | 時刻 tag 付き feedback | ブラウザ UI |

各コマンドは `.claude/commands/<name>.md` に定義。**Capability Matrix のステータスを反映**して、🟡 Partial の機能はユーザに明示します(誤魔化しません)。

---

## 16. Hooks(自動演奏指示)★v2.0 で実装

`.claude/hooks/` は v1.0 で言及されていましたが空でした。v2.0 で実装:

| Hook | Trigger | Action |
|---|---|---|
| `pre-commit-lint.sh` | git commit | YAML schema check, music21 lint, capability matrix check |
| `post-generate-render.sh` | compose/arrange 後 | 自動 audio render、自動 critique |
| `post-generate-critique.sh` | 生成後 | Adversarial Critic を必ず起動、critique.json 永続化 |
| `update-provenance.sh` | plan/score 変更後 | provenance log に追記 |
| `spec-changed-show-diff.sh` | spec 編集後 | CPIR レベルでの音楽的差分表示 |

これらは Claude Code への指示ではなく **実行が保証されるシェルスクリプト**として、Capability Matrix 規律を強制します。

---

## 17. MCP 連携

| MCP 接続先 | 用途 | Phase |
|---|---|---|
| **Reaper DAW** | プロジェクトファイル読み書き、トラックレイアウト | Phase γ |
| **サンプルライブラリ** | ドラムサンプル・ワンショット検索 | Phase γ |
| **参照楽曲 DB** | 権利クリア済参考楽曲メタデータ | Phase γ |
| **MIDI コントローラ** | ライブ即興入力 | Phase δ |
| **SoundFont/VST サーバ** | 音色レンダリング | Phase γ |
| **クラウドストレージ** | バックアップ・チーム共有 | Phase δ |

各 MCP 連携は対応する Capability flag に gating されます。

---

## 18. 開発ロードマップ(180 日計画)

v1.0 のフェーズ計画(Phase 0〜6)を、垂直アラインメント原則(原則 6)に従って **Phase α〜ε** に再編成:

### Phase α(Days 1–30):基盤の正直化

**目的**:野心と現実のズレを解消、次の段階の足場を作る

- [ ] **Capability Matrix を PROJECT.md §5 に正式導入**(本書がそれ)
- [ ] **`tools/capability_matrix_check.py`** 実装、`make matrix-check` ターゲット
- [ ] **README / CLAUDE.md を Matrix にリンク化**
- [ ] **composition.yaml v2 schema** 設計と Pydantic 実装
- [ ] **intent.md と trajectory.yaml の first-class 化**
- [ ] **MetricGoal 型システム** 実装
- [ ] **RecoverableDecision** 機構導入と既存 silent fallback の置換
- [ ] **Golden MIDI tests** 基盤導入(初期 5 case)

**マイルストーン**:既存テストを green 維持しつつ、Matrix が真実を反映、v2 schema が動く

### Phase β(Days 31–75):CPIR と音楽的深さ

**目的**:出力を「動く」から「魅力的」へ

- [ ] **Layer 3a(CPIR)実装**:FormPlan + HarmonyPlan の minimal version
- [ ] **Plan Generator vs Note Realizer の分離**(generators/plan/, generators/note/)
- [ ] **既存 rule_based / stochastic を Note Realizer に再分類**
- [ ] **MotifPlanner 実装**(主題と展開)
- [ ] **PhrasePlan 実装**(antecedent-consequent 構造)
- [ ] **DrumPattern IR** 独立、`drum_patterns/` ライブラリ整備(12 ジャンル)
- [ ] **Counter-melody Generator** 追加
- [ ] **Trajectory を全 Plan Generator の制御信号化**
- [ ] **Trajectory Compliance Tests** 追加
- [ ] **Adversarial Critic Rule Registry** 実装(30+ ルール)
- [ ] **Multi-candidate Conductor**(5 候補 → critique → select)

**マイルストーン**:CPIR 経由で出力品質が体感的に向上、Critic Gate が動く

### Phase γ(Days 76–120):差別化機能(Perception + Arrangement)

**目的**:YaO 独自の価値を実装

- [ ] **Perception Layer Stage 1**(音響特徴、librosa + pyloudnorm)
- [ ] **Perception Layer Stage 2**(use_case 駆動評価)
- [ ] **12 ジャンル Skills** 完備(Markdown + YAML pair)
- [ ] **楽器奏法(Articulation)システム**
- [ ] **Markov chain generator** 実装
- [ ] **constraint solver generator** 実装
- [ ] **Arrangement Engine 本実装**(SourcePlan extractor → Style vector → TargetPlan → Diff report)
- [ ] **MusicXML / LilyPond writers**
- [ ] **Reference Matcher**(Stage 3、抽象特徴のみ)

**マイルストーン**:既存 MIDI を異ジャンルに編曲できる、use_case 別評価が機能する

### Phase δ(Days 121–180):プロダクション化と運用

**目的**:実プロジェクトで使えるレベル

- [ ] **Production Manifest + Mix Chain**(pedalboard 経由)
- [ ] **SpecCompiler 独立化**(Conductor から分離)
- [ ] **多言語対応**(日本語 mood lexicon)
- [ ] **`yao preview` / `yao watch`** 実装
- [ ] **Strudel emitter**(ブラウザ即試聴)
- [ ] **`yao annotate`** ブラウザ UI(時刻 tag feedback)
- [ ] **Sketch-to-Spec dialogue 状態機械**
- [ ] **Spec composability**(extends:, fragments/)
- [ ] **mkdocs サイト完成**:`for-musicians/`, `for-developers/`
- [ ] **Showcase**:10+ canonical YaO 楽曲、weekly auto-update
- [ ] **Hooks 5 種すべて実装**

**マイルストーン**:商業 BGM 制作者が YaO で 90 秒 BGM を制作 → DAW 仕上げ可能

### Phase ε(継続):反映と進化

- Reflection Layer(Layer 7)実運用、ユーザ別 style profile
- Reaper MCP integration
- Live improvisation mode
- AI music model bridges(Stable Audio, MusicGen)
- Community reference library 共有規格

### 18.2 ユーザ価値ドリブン マイルストーン(v1.0 から維持)

| マイルストーン | ユーザ価値 | v2.0 主要機能 |
|---|---|---|
| **1. Describe & Hear** | 「YAML で記述し、即座に聴ける」 | Phase 1 完了済み |
| **2. Iterate & Improve** | 「不満点を伝えると改善される」 | Critic Rule Registry, multi-candidate |
| **3. Richer Music** | 「プロ品質のハーモニー・リズム・対旋律」 | CPIR, MotifPlanner, Counter-melody, DrumIR |
| **4. My Style** | 「好みを学習し、自分のスタイルで生成」 | Reference Matcher, style profile |
| **5. Production Ready** | 「実プロジェクトで使える出力」 | Mix Chain, MusicXML, DAW MCP |

### 18.3 戦略的洞察(v1.0 から維持・拡張)

YaO の設計パターンは音楽に限定されない、**構造化された人間-AI 創造的協働の汎用フレームワーク**です。

| YaO パターン | 汎用パターン | 他ドメインへの応用 |
|---|---|---|
| Score(YAML 仕様) | **Intent-as-Code** | UI デザイン仕様、ナラティブ構造 |
| Plan(CPIR)★v2.0 | **Plan IR** | 脚本構造、シーン構成、動画ペーシング |
| Trajectory(軌跡) | **時間品質曲線** | プレゼン構成、UX ジャーニー |
| Adversarial Critic | **敵対的レビュー** | コードレビュー、デザイン批評 |
| Provenance Graph | **意思決定系譜** | AI 支援創造作業全般 |
| 6 相認知プロトコル | **構造化創造プロトコル** | 「いきなり実装しない」が重要なすべて |

### 18.4 開発プロセス指針(v1.0 から強化)

- **Sound-First 文化**:生成・レンダリングに影響する変更には、変更前後の音声サンプルを PR に含める(必須)
- **ドキュメント予算**:設計文書 1 行あたり、実働コード 3 行以上を維持
- **Dogfooding**:YaO で制作した音楽をプロジェクトのデモ動画や発表に使用
- **ミュージシャン向け貢献ガイド**:ジャンル Skill 追加、テンプレート作成、参照楽曲分析は Python 不要で貢献可能
- **Showcase 更新規律**:GitHub Actions で `docs/showcase/` を自動更新、視覚的退行を即発見

---

## 19. クイックスタート

### 19.1 環境構築

```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts      # SoundFont 配置(初回のみ)
```

### 19.2 最初の曲を作る

```bash
# 1. プロジェクト作成
make new-project NAME=my-first-song

# 2. Claude Code 起動して対話
claude

# 3. プロンプト例
> /sketch
> "雨の夜のカフェで聴きたい、少し切ない 90 秒のピアノ曲"
> (対話で仕様が固まる、SpecCompiler が動く)
> /compose my-first-song

# 4. 結果確認
> /preview            # ★v2.0:in-memory 再生
> /critique my-first-song  # ★v2.0:Rule Registry で 30+ 観点

# 5. 反復
> /regenerate-section my-first-song chorus
> /diff v001 v002    # plan + score 両レベル
```

### 19.3 既存曲を編曲する

```bash
cp my_song.mid specs/projects/my-arrangement/source.mid
> /arrange my-arrangement --target-genre lofi_hiphop --preserve melody
```

---

## 20. ファイル形式と相互運用性

YaO は以下の標準フォーマットを採用し、外部ツールとの相互運用性を担保します。

| 用途 | 形式 | 理由 |
|---|---|---|
| 楽曲データ | MIDI (.mid), MusicXML (.xml) | 業界標準・全 DAW 対応 |
| 楽譜 | LilyPond (.ly), PDF | 高品質楽譜・自動レンダリング |
| 仕様 | YAML | 人間可読・git 管理向き |
| 中間表現(CPIR)| JSON | プログラム可読・スキーマ検証 |
| 来歴 | JSON | グラフ構造の表現 |
| 音声 | WAV(制作中), FLAC/MP3(配布) | 標準対応 |
| ライブコード | Strudel パターン文字列 | ブラウザ即試聴 |

独自フォーマットは原則として作りません。CPIR JSON も Pydantic schema で検証可能な汎用 JSON です。

---

## 21. 倫理とライセンス指針

### 21.1 学習データと参照

参照ライブラリには **権利クリア済楽曲のみ** を配置。`references/catalog.yaml` で `rights_status` フィールドが必須(pre-commit hook で強制)。

### 21.2 アーティスト模倣の禁止

schema レベルで artist 名指し模倣を **拒否**:

```yaml
# ✗ Schema validation エラー
style: "Joe Hisaishi style"

# ✓ 必須形式
style:
  features:
    - "wide open string voicings"
    - "ascending stepwise motifs"
    - "major-minor ambiguity"
    - "meditative tempos"
```

### 21.3 生成物の権利

YaO で生成した楽曲の権利は、原則としてユーザに帰属。`provenance.json` で参照影響度が極端に高い場合(>0.85 on multiple axes)は警告。

### 21.4 透明性

すべての生成物には `provenance.json` で:
- Generator strategy + seed
- Reference influences(類似度スコア付き)
- Subagent decisions
- Recoverable decisions taken

を記録。これは原則 2(説明可能性)の運用実装です。

---

## 22. CLAUDE.md との関係

`CLAUDE.md` は **エージェントへの不変指示** を含む短い文書です。本 PROJECT.md は **人間とエージェント双方が参照する全体設計書** です。

役割分担:

| ファイル | 対象 | 内容 | 禁止内容 |
|---|---|---|---|
| `PROJECT.md`(本書) | 人間 + エージェント | 全体設計・哲学・アーキテクチャ | 実装状況の数値主張(Matrix へリンク) |
| `CLAUDE.md` | エージェント中心 | 不変ルール・禁止事項・Skill 参照 | 実装状況リスト(Matrix へリンク) |
| `README.md` | 人間中心 | 30 秒クイックスタート | 哲学・原則(本書へリンク) |
| **Capability Matrix(§5)** | 人間 + エージェント | 機能の実装状態の唯一の真実源 | aspirational なエントリ |
| `docs/design/*.md` | 人間 + エージェント | 個別の設計判断記録(ADR) | (制限なし)|
| `docs/for-musicians/` | 作曲家ユーザ | チュートリアル | 内部詳細 |
| `docs/for-developers/` | 開発者 | 開発ガイド | ユーザ向け話題 |
| `docs/showcase/` | 全員 | dogfooded 楽曲 | マーケコピー |
| `development/*.md` | 開発者 + エージェント | 技術的開発ドキュメント | (制限なし) |

---

## 23. 将来のアーキテクチャ拡張計画

以下は v2.0 の Phase ε 以降の検討項目です。

### 23.1 セッション/プロジェクト ランタイム層

現在の CLI はステートレスです。将来的に、反復制作セッションを支援する `ProjectRuntime` を導入:

- 生成キャッシュ(セクション単位の再生成を高速化)
- フィードバックキュー(批評→修正のループ)
- undo/redo(音楽レベルでの取り消し・やり直し)

### 23.2 抽象エージェントプロトコル

`.claude/agents/*.md` の Subagent 定義は Claude Code に結合しています。将来的に、バックエンド非依存の Python プロトコル(`AgentRole`, `AgentContext`, `AgentOutput`)を定義し、Claude Code 実装を 1 つのアダプターとして扱います。

### 23.3 Reflection Layer 本格運用

Layer 7(Reflection)を実装:

- ユーザ別 style profile 学習(過去の feedback から好みを抽出)
- Cross-project pattern mining(同じユーザの全 project から共通モチーフを発見)
- Critique 履歴学習(どの critique が修正に繋がったかをモデル化)

### 23.4 Generic Creative Domain Framework

§18.3 の戦略的洞察に基づき、YaO のパターン(intent-as-code, trajectory, plan IR, adversarial critic, provenance)を **音楽に限定しない汎用 toolkit** として抽出。Phase ε+ の検討。

### 23.5 AI Music Model Bridges

Stable Audio、MusicGen、Magenta RT などのオーディオ生成モデルとの連携:

- 「シネマティック・ストリングス・パッド」のような textural element だけ AI 生成
- YaO の CPIR は構造を担当、AI モデルは音色/質感を担当

---

## 24. 用語集

**Conductor(指揮者)** — プロジェクトの所有者である人間。最終判断者。

**Orchestra(楽団)** — Subagent 群の総称。

**Score(楽譜)** — `specs/` 内の YAML 群。楽曲の完全な記述。

**Score IR(Layer 3b)** — 具体的音符の中間表現。Note / Section / Part を保持。

**Composition Plan IR(CPIR、Layer 3a)★v2.0** — 計画の中間表現。FormPlan / HarmonyPlan / MotifPlan / PhrasePlan / DrumPattern / ArrangementPlan を統合。

**Trajectory(軌跡)** — 楽曲の時間軸上の特性曲線(tension/density/predictability/brightness/register_height)。

**Aesthetic Reference Library** — 美的アンカーとなる楽曲群。

**Perception Substitute Layer** — AI が音楽を「聴けない」ことを補う層。

**Provenance(来歴)** — すべての生成判断の追跡可能な記録。

**Adversarial Critic** — 生成物を意図的に攻撃する批評 Subagent。

**Negative Space(否定空間)** — 鳴らさない部分の設計。

**Style Vector** — ジャンルやスタイルを多次元特徴量空間のベクトルとして表現。

**Iteration(反復)** — 同一プロジェクト内の生成版。`v001`, `v002`, ...

**Music Lint** — 音楽理論・制約違反の自動検出機構。

**Sketch-to-Spec** — 自然言語スケッチから YAML 仕様への対話的変換プロセス。

**MetricGoal ★v2.0** — 評価判定の多型(AT_LEAST / TARGET_BAND / MATCH_CURVE 等)。

**RecoverableDecision ★v2.0** — silent fallback を置換する、記録された妥協。

**Capability Matrix ★v2.0** — 機能の実装状態の唯一の真実源(§5)。

**Vertical Alignment ★v2.0** — Input / Processing / Evaluation を同期して深化させる原則。

**Music-as-Plan ★v2.0** — 音楽の本質は計画にあり、コードはその実装である哲学。

**Critic Gate ★v2.0** — Step 5 と Step 6 の間で Adversarial Critic が CPIR を批評するゲート。

---

## 25. 最後に:YaO が目指す世界

YaO は「AI が音楽を作る」プロジェクトではありません。**人間と AI が、それぞれの長所を活かして音楽を共創する**ためのインフラです。

- 人間は **意図と判断と感性** を提供します。
- AI は **理論知識・反復速度・記録の網羅性** を提供します。
- YaO は **両者を構造化された協働プロセスとして成立させる場** です。

優れた音楽は、最終的には **人間の魂の発露** であり続けます。YaO はその発露を **より速く、より深く、より再現可能に** することを目指します。

### v2.0 で更に明確になった主張

> **音楽の本質は計画にある。コードはその実装にすぎない。**

ブラックボックス的 AI 生成が出せない驚きを、YaO は出せます。なぜならその驚きは、**理由のある計画**から生まれるからです。理由は、人間が議論し、共有し、磨き、伝承できるものです。

CPIR を心臓部に据えることで、YaO は次のような環境になります:

- 指揮者(あなた)は、音符が一つも書かれる前に、計画を点検・編集・批判できる
- 楽団員(Subagents)は、計画の構造に沿って役割分担する
- 批評家(Critic)は、計画レベルで外科的に問題を発見する
- 編曲は、ピッチ操作ではなく、原則に従った変換になる
- 来歴(Provenance)は意味を持つ — 各音符の「なぜ」が計画要素まで遡れる

これが「Music-as-Plan」の具体的な意味です。これが YaO を、これまでのいかなる AI 音楽ツールとも異なるものにします。

---

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to plan, perform, and grow with you.*

---

**Project: You and Orchestra (YaO)**
*Document version: 2.0*
*Supersedes: PROJECT.md v1.0(2026-04-27)*
*Last revised: 2026-04-30*

### Changelog from v1.0

| 章 | 変更内容 |
|---|---|
| §0 | Music-as-Code → Music-as-Plan への進化を明記 |
| §1 | メタファーに Plan(指揮者の書き込み入り楽譜)を追加 |
| §2 | 原則 6(垂直アラインメント)を追加 |
| §3 | 新規章「開発フェーズ:現在地と方向」を追加 |
| §4 | 7+1 層モデルへ(Layer 3 を 3a/3b に分割) |
| §5 | 新規章「Capability Matrix」追加 |
| §6 | ディレクトリ構造を v2.0 拡張に合わせ更新 |
| §7 | 新規章「Composition Plan IR(CPIR)」追加 — v2.0 の心臓部 |
| §8 | Subagent → Pipeline Step マッピングを明確化 |
| §9 | 新規章「Critic Gate と評価三本柱」 |
| §10 | composition.yaml v2 schema を 11 セクションに拡張 |
| §11 | 新規章「SpecCompiler — 自然言語の昇華」 |
| §12 | ジャンル拡張・楽器奏法・DrumPattern Library |
| §13 | 編曲エンジンを CPIR ベースに強化 |
| §14 | Perception Layer を 3 段階で実装 |
| §15 | Custom Commands に preview/watch/annotate 追加 |
| §16 | Hooks を 5 種実装する計画 |
| §18 | 180 日ロードマップを Phase α〜ε に再編成 |
| §22 | ドキュメント役割表を厳格化 |
| §24 | 用語集を v2.0 概念で拡張 |
