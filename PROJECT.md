# You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

---

## ドキュメントステータス

これは **PROJECT.md v1.1** です。v1.0 の哲学・アーキテクチャ・5 原則をすべて継承し、**9 つの漸進的改善**を組み込んだ実装可能な進化版です。

**v1.0 からの主な変更**:
- 既存の 7 層アーキテクチャを保持しつつ、各層を**漸進的に強化**
- 「動いているものを壊さない」原則を最上位に追加(原則 6)
- **Feature Status Matrix** をドキュメント整合性の単一の真実源として導入
- 9 つの優先改善項目を、効果 × コストの観点で整序
- 各改善が PROJECT.md の既存原則とどう整合するかを明示

**v2.0 大改造提案(MPIR 8 層化等)からの方針転換**:
v2.0 提案は構造として妥当でしたが、規模が大きすぎて実装に至りませんでした。本 v1.1 は**「実装される改善」を最優先**します。新しい層を作らず、既存層を磨き込みます。

---

## 0. プロジェクトの本質

**You and Orchestra (YaO)** は、Claude Code を基盤として動作する **エージェント型音楽制作環境** です。一般的な「AI作曲ツール」とは異なり、YaO は単一のブラックボックスから音楽を吐き出すのではなく、**役割分担された複数の AI エージェント(Orchestra Members)を、人間(You = Conductor)が指揮する**という構造を取ります。

YaO のすべての設計は、次のひとつの命題に従属します。

> **音楽制作とは、感覚的な一回限りの作業ではなく、再現可能で改善可能な創作エンジニアリングである。**

このため YaO は、音楽を **音声ファイル**として扱う前に、**コード・仕様・テスト・差分・来歴**として扱います。これを Music-as-Code 哲学と呼びます。

---

## 1. メタファー:You and Orchestra

YaO のすべての概念は、オーケストラの比喩に対応しています。この対応関係を内面化することが、YaO を正しく使う最短距離です。

| YaO の構成要素 | オーケストラの比喩 | 実装上の対応 |
|---|---|---|
| **You** | 指揮者 (Conductor) | プロジェクト所有者である人間 |
| **Score** | 楽譜 | `specs/*.yaml` に記述された作曲仕様 |
| **Orchestra Members** | 楽団員 | 各 Subagent(Composer, Critic, Theorist 等) |
| **Concertmaster** | コンサートマスター | Producer Subagent(全体調整役) |
| **Rehearsal** | リハーサル | 生成・評価・修正の反復ループ |
| **Library** | 楽団の楽譜庫 | `references/` 内の参照楽曲群 |
| **Performance** | 本番演奏 | レンダリングされた最終音源 |
| **Recording** | 録音 | `outputs/` 内の成果物 |
| **Critic / Reviewer** | 批評家 | Adversarial Critic Subagent |

指揮者(You)はすべての音符を書くわけではありません。指揮者の仕事は、**意図を明確化し、楽団員に方向性を示し、リハーサルで判断を下し、本番の質を担保する**ことです。YaO はこの分業を AI に持ち込みます。

---

## 2. 設計原則

YaO のあらゆる実装判断は、以下の **6つの不変原則** に照らして決定されます。これらは CLAUDE.md にも転記され、エージェントの判断基準として機能します。

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

### 原則6:漸進性 — 動いているものを壊さない(★ v1.1 で新設)
既存の動作する機能は、明確な代替が存在し、移行パスが用意されるまで保持されます。大規模な再設計よりも、**1〜2 週間で完了する小さな改善の累積**を優先します。各改善は単独で**音楽的に聴いて分かる効果**を持つこと、そして既存テスト・既存出力との後方互換性を保つことが要求されます。

---

## 3. アーキテクチャ:7層モデル

YaO は明確に分離された 7 つの層で構成されます。各層は独立した入出力契約を持ち、交換・テスト可能です。

```
┌─────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                      │
│   制作履歴からの学習、ユーザ嗜好の更新                  │
├─────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                    │
│   構造・和声・リズム・音響の自動評価、敵対的批評        │
├─────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                  │
│   MIDI→音声、楽譜PDF、ライブコード変換                 │
├─────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                      │
│   美的判断の代替機構(参照駆動・心理学マッピング)       │
├─────────────────────────────────────────────────────┤
│ Layer 3: Intermediate Representation (IR)           │
│   ScoreIR、DrumPattern、harmony、motif、voicing     │
├─────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                        │
│   生成アルゴリズム選択(規則/確率/ドラム/対旋律)       │
├─────────────────────────────────────────────────────┤
│ Layer 1: Specification                              │
│   YAML仕様、対話、スケッチ入力                         │
└─────────────────────────────────────────────────────┘
```

層間の依存は厳密に下から上へのみ流れます。下位層の変更は上位層に影響しますが、上位層を変えても下位層は影響を受けません。これにより、たとえば Generation Strategy(層2)を「規則ベース」から「確率モデル」に切り替えても、Specification(層1)はそのまま使えます。

**v1.1 における変更**:層構造そのものは変更しません。代わりに各層内で**漸進的拡張**を行います。例えば Layer 3 (IR) には DrumPattern を追加し、Layer 2 には counter_melody / drum_patterner ジェネレータを追加しますが、層境界は不変です。

---

## 4. Feature Status Matrix(★ v1.1 新設)

このマトリックスは **YaO の機能の実装状態に関する単一の真実源**です。README.md・CLAUDE.md は能力主張の代わりにここへリンクします。

ステータス記号: ✅ Stable · 🟢 Working but limited · 🟡 Partial · ⚪ Designed, not started · 🔴 Identified gap

最終確認: 2026-04-29(`tools/feature_status_check.py` で自動検証)

| 領域 | 機能 | ステータス | 備考 |
|---|---|---|---|
| **Spec / Input** | YAML spec parsing (Pydantic) | ✅ | 全テンプレートで動作 |
| | 自然言語 → spec(`yao conduct`) | 🟢 | 英語キーワード辞書ベース、日本語非対応 |
| | trajectory.yaml(velocity 影響のみ) | 🟢 | 5 次元定義あるが velocity しか効かない |
| | constraints with scoping | ✅ | must/must_not/prefer/avoid |
| | intent.md as first-class artifact | 🟡 | 形式は存在、自動評価未連動 |
| **Generation** | rule_based generator | ✅ | 決定論的 |
| | stochastic generator | ✅ | seed/temperature/contour |
| | drum_patterner | 🔴 | **★1 で実装予定** |
| | counter_melody | 🔴 | **★2 で実装予定** |
| | trajectory 多次元連動 | 🔴 | **★3 で実装予定** |
| | markov / constraint_solver | ⚪ | 設計のみ |
| **IR** | ScoreIR (Note, Part, Section) | ✅ | frozen dataclass |
| | DrumPattern IR | 🔴 | **★1 で実装予定** |
| | harmony, motif, voicing | ✅ | functional 表記対応 |
| | trajectory(構造定義のみ) | 🟡 | 多次元定義あるが影響限定的 |
| **Rendering** | MIDI writer + per-instrument stems | ✅ | |
| | audio renderer (FluidSynth) | ✅ | SoundFont 必須 |
| | drum stems | 🔴 | ★1 完了後に追加 |
| | MusicXML writer | ⚪ | |
| | LilyPond / PDF score | ⚪ | |
| **Critique** | LLM 自由解釈による critique | 🟡 | `/critique` コマンドあり、再現性なし |
| | rule-based critique 機械検出(15+) | 🔴 | **★4 で実装予定** |
| | Adversarial Critic Subagent 定義 | ✅ | 定義のみ、実装は ★4 で |
| **Conductor** | basic generate-evaluate-adapt loop | ✅ | |
| | section-level regeneration | ✅ | |
| | RecoverableDecision-aware adaptation | 🔴 | **★8 後** |
| **Skills** | genre Skills | 🟡 | cinematic 1 個のみ |
| | 8+ genre Skills | 🔴 | **★7 で量産** |
| | theory Skills | 🟡 | 4 個 (voice-leading, piano, tension-resolution, cinematic) |
| **CLI / UX** | compose, conduct, render, validate, evaluate, diff, explain, regenerate-section | ✅ | |
| | yao preview(即時試聴) | 🔴 | **★6 で追加** |
| | yao watch(ホットリロード) | 🔴 | **★6 で追加** |
| **Verification** | music_lint, analyzer, evaluator, diff | ✅ | |
| | RecoverableDecision logging | 🔴 | **★8 で追加** |
| | golden MIDI tests | 🔴 | **★9 で追加** |
| **Audio Quality** | per-instrument stems | ✅ | |
| | mix chain (EQ, comp, reverb, pan) | ⚪ | |
| | LUFS targeting | ⚪ | |
| **Arrangement** | arrangement engine | ⚪ | Phase 2 設計のみ |
| **Perception** | reference matcher | ⚪ | |
| | psychology mapper | ⚪ | |
| **DAW / MCP** | Reaper integration | ⚪ | |
| **Live** | improvisation mode | ⚪ | |
| **Tests** | unit / integration / scenarios / music_constraints | ✅ | 226 テスト |
| | golden MIDI tests | 🔴 | **★9 で追加** |
| | subagent eval tests | ⚪ | |
| **Tooling** | architecture lint (AST-based) | ✅ | |
| | feature status check | 🔴 | **★5 で追加** |

機能を追加・変更する際は、**この表を同じ PR で更新**することが原則です。

---

## 5. ディレクトリ構造

```
yao/
├── CLAUDE.md                      # エージェントへの不変指示
├── PROJECT.md                     # 本ファイル(プロジェクト全体設計)
├── FEATURE_STATUS.md              # ★ v1.1 新設:Feature Status Matrix の詳細
├── README.md                      # ユーザ向けクイックスタート
├── pyproject.toml
├── Makefile
├── mkdocs.yml
│
├── .claude/
│   ├── commands/                  # /compose, /arrange, /critique, /sketch, etc.
│   ├── agents/                    # 7 Subagent 定義
│   ├── skills/
│   │   ├── genres/                # cinematic ✅ + 7 ジャンル(★7で追加)
│   │   ├── theory/                # voice-leading, reharmonization, counterpoint, modal-interchange
│   │   ├── instruments/
│   │   └── psychology/
│   ├── guides/                    # architecture, coding, music, testing, workflow
│   └── hooks/
│
├── specs/
│   ├── projects/                  # ユーザの楽曲プロジェクト
│   │   └── <project>/
│   │       ├── intent.md
│   │       ├── composition.yaml
│   │       ├── trajectory.yaml
│   │       ├── references.yaml
│   │       ├── negative-space.yaml
│   │       └── arrangement.yaml
│   └── templates/                 # 4+ ready-to-use templates
│
├── src/
│   ├── yao/
│   │   ├── constants/             # Layer 0
│   │   ├── schema/                # Layer 1
│   │   ├── ir/                    # Layer 3
│   │   │   ├── score_ir.py
│   │   │   ├── trajectory.py     # ★3 で多次元連動拡張
│   │   │   ├── motif.py
│   │   │   ├── harmony.py
│   │   │   ├── voicing.py
│   │   │   ├── drum.py            # ★1 新設
│   │   │   ├── timing.py
│   │   │   └── notation.py
│   │   ├── generators/            # Layer 2
│   │   │   ├── rule_based.py
│   │   │   ├── stochastic.py
│   │   │   ├── drum_patterner.py  # ★1 新設
│   │   │   └── counter_melody.py  # ★2 新設
│   │   ├── perception/            # Layer 4(将来)
│   │   ├── render/                # Layer 5
│   │   ├── verify/                # Layer 6
│   │   │   ├── music_lint.py
│   │   │   ├── analyzer.py
│   │   │   ├── evaluator.py
│   │   │   ├── diff.py
│   │   │   ├── recoverable.py     # ★8 新設
│   │   │   └── critique/          # ★4 新設(15+ ルール)
│   │   │       ├── base.py
│   │   │       ├── registry.py
│   │   │       ├── structural.py
│   │   │       ├── melodic.py
│   │   │       ├── harmonic.py
│   │   │       ├── rhythmic.py
│   │   │       ├── arrangement.py
│   │   │       └── emotional.py
│   │   ├── reflect/               # Layer 7
│   │   └── conductor/
│   └── cli/
│       ├── compose.py
│       ├── conduct.py
│       ├── render.py
│       ├── preview.py             # ★6 新設
│       └── watch.py               # ★6 新設
│
├── drum_patterns/                 # ★1 新設:8+ ジャンル別ドラムパターン YAML
│   ├── pop_8beat.yaml
│   ├── four_on_the_floor.yaml
│   ├── lofi_laidback.yaml
│   ├── trap_half_time.yaml
│   ├── rock_backbeat.yaml
│   ├── jazz_swing_ride.yaml
│   ├── ballad_brushed.yaml
│   └── game_drive_16bit.yaml
│
├── references/                    # 美的参照ライブラリ(将来)
├── outputs/                       # 生成成果物(gitignore)
├── soundfonts/                    # 音色ライブラリ(gitignore)
├── tests/
│   ├── unit/                      # 207 tests
│   ├── integration/               # 2 tests
│   ├── music_constraints/         # 7 tests
│   ├── scenarios/                 # 10 tests
│   └── golden/                    # ★9 新設
│       ├── inputs/
│       ├── expected/
│       ├── test_golden.py
│       └── tools/
│           └── regenerate_goldens.py
├── tools/
│   ├── architecture_lint.py
│   └── feature_status_check.py    # ★5 新設
└── docs/
    ├── design/
    ├── tutorials/
    └── glossary.md
```

---

## 6. オーケストラの編成:Subagent 設計

YaO の楽団員(Subagents)は明確な役割と制約を持ちます。各 Subagent は専用コンテキスト・専用ツール許可・専用評価基準を持ち、独立して動作したのち Producer Subagent によって統合されます。

### 6.1 Composer(作曲家)
**責任:** メロディ・主題・構成の生成
**入力:** intent.md, composition.yaml, trajectory.yaml, references.yaml
**出力:** Score IR(モチーフ・旋律ライン・構成情報)
**禁止事項:** 楽器選択・最終ヴォイシング(これは Orchestrator の仕事)
**評価軸:** モチーフの記憶性・反復と変奏のバランス・軌跡への適合度

### 6.2 Harmony Theorist(和声理論家)
**責任:** コード進行・転調・代理コード・終止の設計
**入力:** Composer の主旋律案、composition.yaml の harmony セクション
**出力:** コード進行 IR(機能和声記述+具体ヴォイシング候補)
**評価軸:** 機能整合性・テンション解決・ジャンル適合性

### 6.3 Rhythm Architect(リズム設計者) ★ v1.1 で実体化
**責任:** ドラムパターン・グルーヴ・シンコペーション・フィル
**入力:** composition.yaml の rhythm/drums セクション、ジャンル指定、trajectory
**出力:** DrumPattern IR + 全楽器のリズム配置
**評価軸:** グルーヴ感・人間味・セクション間コントラスト
**実装担当ジェネレータ:** ★1 の `drum_patterner.py`

### 6.4 Orchestrator(編成者) ★ v1.1 で対旋律担当追加
**責任:** 楽器割り当て・ヴォイシング・音域配置・対旋律
**入力:** Composer/Harmony/Rhythm の出力すべて
**出力:** 完全な Score IR(楽器ごとの全パート、対旋律含む)
**評価軸:** 周波数空間の衝突回避・楽器の慣用的使用・テクスチャ密度
**実装担当ジェネレータ:** ★2 の `counter_melody.py`

### 6.5 Adversarial Critic(敵対的批評家) ★ v1.1 で機械検出ルール化
**責任:** あらゆる弱点の発見と指摘
**入力:** 生成された任意段階の成果物
**出力:** 構造化 Finding 列(critique.md にレンダリング)
**特性:** **賞賛しないことが原則**。クリシェ検出・構造的退屈さ・感情的不整合を厳しく評価
**評価軸:** 問題発見の網羅性と具体性
**実装:** ★4 の 15+ 機械検出ルール + LLM による文章レンダリング

### 6.6 Mix Engineer(ミックスエンジニア)
**責任:** ステレオ配置・ダイナミクス・周波数マスキング解消・ラウドネス管理
**入力:** Orchestrator の出力 + production パラメータ
**出力:** ミックス指示書(各トラックの EQ/コンプ/リバーブ/パン設定)
**評価軸:** LUFS 基準達成・周波数バランス・ステレオ広がり
**ステータス:** 定義のみ、実装は将来

### 6.7 Producer(プロデューサ)
**責任:** 全体統合・優先順位付け・指揮者(人間)との対話・最終判断
**入力:** すべての Subagent の出力 + 人間からのフィードバック
**出力:** 最終的な制作判断・次の反復への指示
**特権:** 唯一、他の Subagent の出力を却下・差し戻しできる
**評価軸:** 楽曲の意図(intent.md)への忠実度

---

## 7. 作曲認知プロトコル:6 相

YaO の `/compose` および `/arrange` コマンドは、Claude Code に以下の 6 相を**順序通り**実行させます。これは認知プロセスを構造化し、エージェントが「いきなり音符を書き始める」失敗パターンを防ぎます。

### Phase 1:Intent Crystallization(意図の結晶化)
ユーザ入力(対話・YAML・スケッチ)から、楽曲の本質を 1〜3 文で言語化します。曖昧さを許さず、`intent.md` に確定させます。

### Phase 2:Architectural Sketch(構造スケッチ)
時間軸軌跡(tension / density / valence / predictability / brightness / register_height)を**先に**描きます。音符はまだ書きません。`trajectory.yaml` を完成させます。**v1.1 では★3 により全次元が実際に効くようになる**ため、この相の意義が初めて活きます。

### Phase 3:Skeletal Generation(骨格生成)
Composer Subagent がコード進行と主旋律の「種」を生成。**多様性のため 5〜10 候補**を作ります。完成度は 60% で十分。

### Phase 4:Critic-Composer Dialogue(批評者-作曲者対話)
Adversarial Critic が全候補を攻撃。**v1.1 では★4 の 15+ 機械検出ルール**により、批評が再現性のあるものになります。Producer が判断し、最強の候補を選ぶか、複数の長所を統合した新候補を作らせます。

### Phase 5:Detailed Filling(詳細埋め)
選ばれた骨格に、Harmony / Rhythm / Orchestrator が詳細を埋めます。各判断は Provenance に記録されます。**v1.1 では DrumPattern と CounterMelody がここで生成**されます。

### Phase 6:Listening Simulation(聴取シミュレーション)
Perception Substitute Layer が完成品を「聴いて」、当初意図(Phase 1)との乖離を測定。乖離が閾値超なら該当箇所を再生成。最終的に `critique.md` と `analysis.json` が出力されます。**v1.1 では Perception Layer は未実装のため、評価器の数値判定 + 機械検出 Critique で代替**します。

---

## 8. パラメータ仕様

YaO は楽曲を、以下の **9 種類のファイル**で完全に記述します。すべて版管理対象であり、git diff で変更履歴が追えます。

### 8.1 `intent.md`(意図記述、自然言語)
楽曲の本質を 1〜3 文で記述。すべての判断の最終的な根拠となる文書です。`new-project` 時に自動生成され、ユーザが編集します。

### 8.2 `composition.yaml`(作曲パラメータ)
キー、テンポ、拍子、形式、ジャンル、楽器編成、各セクションの構造などの基礎仕様。

**v1.1 で追加されるフィールド**(★1 ドラム IR と連動):

```yaml
drums:                              # ★ v1.1 新設
  pattern_family: "lofi_laidback"   # drum_patterns/ から参照
  swing: 0.55
  humanize_ms: 8
  ghost_notes_density: 0.4
  fills_at: ["pre_chorus_end", "bridge_end"]

instruments:
  - name: violin
    role: melody
  - name: viola
    role: counter_melody             # ★ v1.1 新設の role
    counter_to: violin
    density_factor: 0.4
    sections: [chorus_2, bridge]
```

既存の v1.0 spec は変更不要で動作します(後方互換)。

### 8.3 `trajectory.yaml`(時間軸軌跡)
緊張度・密度・感情価・予測可能性の時間関数。Bezier 曲線または小節単位のステップ関数で記述。

```yaml
trajectories:
  tension:
    type: bezier
    waypoints: [[0, 0.2], [16, 0.4], [32, 0.85], [48, 0.6], [64, 0.3]]
  density:
    type: stepped
    sections: {intro: 0.3, verse: 0.5, chorus: 0.9, bridge: 1.0}
  predictability:
    type: linear
    target: 0.65
    variance: 0.15
  brightness:                         # ★ v1.1 で実装連動
    type: bezier
    waypoints: [[0, 0.4], [32, 0.85], [64, 0.5]]
  register_height:                    # ★ v1.1 で実装連動
    type: stepped
    sections: { verse: 0.45, chorus: 0.7 }
```

**重要な変更**:v1.0 では tension が velocity にしか影響しませんでしたが、v1.1 では★3 により**全次元が以下に影響**します:

| Trajectory 次元 | 影響範囲 |
|---|---|
| tension | velocity, chord extension(7th/9th), dissonance tolerance, leap probability |
| density | note density, rhythmic subdivision, register spread, chord change frequency |
| predictability | motif variation rate, harmonic novelty |
| brightness | register, instrument selection, voicing openness |
| register_height | overall pitch range positioning |

### 8.4 `references.yaml`(美的参照ライブラリ)
正参照(似せる)と負参照(避ける)の楽曲リスト。各参照について、「何を抽出するか」を指定。比較は**抽象特徴のみ**(tempo, density curve, spectral balance 等)で、メロディ・コード進行・hook の直接コピーは禁止(schema validator が enforce)。

### 8.5 `negative-space.yaml`(否定空間)
休符・周波数ギャップ・テクスチャ削除など、「鳴らさない」設計。

### 8.6 `arrangement.yaml`(編曲パラメータ、編曲時のみ)
原曲入力、保持項目、変換項目、回避項目の明示。Phase 2(将来)で本格実装。

### 8.7 `production.yaml`(ミックス・マスタリング)
LUFS 目標、ステレオ幅、リバーブ量など最終音響仕様。**v1.1 で `use_case` フィールド推奨追加**(将来の評価器駆動のため):

```yaml
production:
  use_case: "youtube_bgm"              # | "game_bgm" | "advertisement" | "study_focus" | "general"
  target_lufs: -16
  stereo_width: 0.7
  vocal_space_reserved: true
```

### 8.8 `provenance.json`(自動生成、手書き不可)
全ての生成判断の来歴記録。各音符・コード・楽器選択の「なぜ」を保持。**v1.1 で RecoverableDecision エントリが追加**されます(★8)。

### 8.9 `critique.json` および `critique.md` ★ v1.1 で構造化
Adversarial Critic の構造化された Finding 列(JSON)+ 人間可読レンダリング(Markdown)。`/critique` 実行で自動生成されます(★4)。

---

## 9. Custom Commands(指揮者の指示棒)

ユーザは以下のコマンドで Orchestra を動かします。各コマンドは `.claude/commands/*.md` に定義されます。

| コマンド | 用途 | ステータス |
|---|---|---|
| `/compose <project>` | 仕様から新曲を生成 | ✅ |
| `/arrange <project>` | 既存曲を編曲 | ⚪ Phase 2 |
| `/critique <iteration>` | 既存生成物を批評 | 🟡 → ✅ ★4で機械検出ルール化 |
| `/regenerate-section <project> <section>` | 特定セクションのみ再生成 | ✅ |
| `/morph <from> <to> <bars>` | 2 つの楽曲調を補間 | ⚪ |
| `/improvise <input>` | リアルタイム伴奏(ライブモード) | ⚪ |
| `/explain <element>` | 特定要素の生成判断を説明 | ✅ |
| `/diff <iter_a> <iter_b>` | 2 イテレーション間の音楽差分 | ✅ |
| `/render <iteration>` | MIDI を音声・楽譜に変換 | ✅ |
| `/sketch` | スケッチ→仕様対話モード | 🟡 |

### v1.1 で追加される CLI コマンド

| CLI コマンド | 用途 | 改善番号 |
|---|---|---|
| `yao preview <spec>` | 即時試聴(ファイル書き出し無し) | ★6 |
| `yao watch <spec>` | spec 編集監視 + 自動再生成 + 自動再生 | ★6 |

これらは slash command ではなく **CLI コマンドとして提供**されます(ホットリロード型 UX のため)。

---

## 10. Skills(楽団員の素養)

`.claude/skills/` には専門知識を構造化したモジュールが配置されます。Subagent は必要に応じてこれらを参照します。

### 10.1 ジャンル Skills(★ v1.1 で量産)

**現状**: cinematic 1 個のみ
**v1.1 目標**: 最低 8 ジャンル

| ジャンル | ステータス | 担当改善 |
|---|---|---|
| cinematic | ✅ | (既存) |
| lofi_hiphop | 🔴 | ★7 |
| j_pop | 🔴 | ★7 |
| neoclassical | 🔴 | ★7 |
| ambient | 🔴 | ★7 |
| jazz_ballad | 🔴 | ★7 |
| game_8bit_chiptune | 🔴 | ★7 |
| acoustic_folk | 🔴 | ★7 |

各 Skill は**標準スキーマ**(tempo / keys / progressions / drum patterns / instrumentation / cliches to avoid / use cases)を持ち、front-matter YAML から自動的に `src/yao/skills/genres/<name>.yaml` を生成して generator が機械参照可能にします。

### 10.2 理論 Skills

現状: voice-leading, reharmonization(プレースホルダ), counterpoint(プレースホルダ), modal-interchange(プレースホルダ), tension-resolution が定義済み。voice-leading と tension-resolution は内容充実。

### 10.3 楽器 Skills

現状: piano が充実。strings, drums, synths はプレースホルダ。

### 10.4 心理学 Skills

音楽心理学(Juslin, Huron, Krumhansl 等)の経験的マッピング。Phase 3 (Perception Layer) と連動して活性化予定。

---

## 11. Hooks(自動演奏指示)

Hooks は Claude Code への指示ではなく、**実行が保証されるスクリプト**です。

| Hook | タイミング | 内容 | ステータス |
|---|---|---|---|
| `pre-commit-lint` | git commit 前 | music21 で楽理リント、仕様 YAML スキーマ検証、★5 feature status チェック | 🟡 |
| `post-generate-render` | 生成完了後 | MIDI を自動的に音声と楽譜にレンダリング | ⚪ |
| `post-generate-critique` | 生成完了後 | ★4 機械検出 Critique を必ず起動 | ⚪ → 🟢 (★4 後) |
| `update-provenance` | あらゆる変更後 | Provenance Graph を最新状態に更新 | ✅ |

これらにより、エージェントが指示を忘れても品質保証が破綻しません。

---

## 12. MCP 連携

YaO は以下の MCP サーバとの接続を想定して設計されています。**v1.1 では MCP 連携の優先度を下げ**、まず★1〜★9 の音楽品質改善を優先します。

| MCP 接続先 | 用途 | 優先度 |
|---|---|---|
| **DAW(Reaper 優先)** | プロジェクトファイル読み書き、トラック自動レイアウト | 中(Phase 2 後半) |
| **サンプルライブラリ** | ドラムサンプル・ワンショット・ループ | 低 |
| **参照楽曲 DB** | 権利クリア済参考楽曲メタデータ | 低 |
| **MIDI コントローラ** | ライブ即興モード入力 | 低 |
| **SoundFont/VST サーバ** | 音色レンダリング | 低 |
| **クラウドストレージ** | バックアップとチーム共有 | 低 |

---

## 13. 品質保証:評価指標

YaO は生成物を以下の 5 領域で自動評価します。スコアは `evaluation.json` に保存されます。

### 13.1 構造評価
セクションコントラスト、クライマックス位置、密度カーブ適合度、反復バランス、ループ性。

### 13.2 メロディ評価
音域適合度、モチーフ記憶性、歌唱可能性、フレーズ終止感、輪郭変化。

### 13.3 和声評価
コード機能整合性、テンション解決、和声複雑度のパラメータ適合、終止強度。

### 13.4 編曲評価(編曲モード時)
楽器役割の明確性、周波数衝突リスク、原曲保持率、変換強度。

### 13.5 音響評価
BPM 一致、ビート安定性、LUFS 目標達成、スペクトルバランス、オンセット密度。

### 13.6 構造化 Critique(★4 v1.1 新設)
評価指標の数値判定とは別に、**Adversarial Critic** が役割別の機械検出ルール(15+)を実行し、構造化 Finding 列を出力します。これは「評価が pass しても感じが悪い」を検出する第二の品質保証層です。

各指標には**数値目標と許容範囲**が設定され、目標逸脱時は Adversarial Critic が自動的に問題提起します。

---

## 14. 9 つの漸進的改善(★ v1.1 の核心)

v1.0 から v1.1 への移行は、**規模の大きな再設計ではなく、9 つの独立した小改善の累積**として実装されます。各改善は:

- 1〜2 週間で完了可能
- 既存の動作を破壊しない(後方互換)
- 単独で**音楽的に聴いて分かる効果**がある
- Feature Status Matrix の特定エントリを ✅ に進める

### 14.1 改善一覧と優先度

```
高効果 × 低コスト                        高効果 × 中コスト                   中効果 × 低コスト
   (即実行)                                (Phase α)                          (磨き込み)

★5 Feature Status Matrix                ★1 DrumPattern IR + drum_patterner   ★7 ジャンル Skill 量産
★9 Golden MIDI tests                    ★2 Counter-melody generator           ★8 RecoverableDecision
★6 yao preview / watch                  ★3 Trajectory 多次元連動
                                         ★4 Adversarial Critic 機械化(15+)
```

### 14.2 改善ごとの詳細

#### ★1 DrumPattern IR とドラムジェネレータ
**目的**: ポップス・EDM・ロック・ヒップホップ・ローファイ・ゲーム BGM の制作を可能にする。
**実装**: `src/yao/ir/drum.py`(DrumHit, DrumPattern dataclass), `src/yao/generators/drum_patterner.py`, `drum_patterns/` ディレクトリに最低 8 ジャンル分の YAML パターン。`composition.yaml` に `drums:` セクション追加。
**効果**: 音楽幅が 2〜3 倍に拡大。
**コスト**: 中(2 週間)。
**前提**: なし。即着手可能。

#### ★2 Counter-melody / Inner-voice ジェネレータ
**目的**: 「メロディ + ベース + コード」の薄い 3 声体から、対旋律と内声を持つ厚い音楽へ。
**実装**: `src/yao/generators/counter_melody.py`。`composition.yaml` の楽器 role に `counter_melody` を追加。種別対位法(species counterpoint)の原則に従い、強拍コードトーン優先・反進行優先・密度ファクター制御で対旋律を生成。
**効果**: cinematic / neoclassical / J-Pop / オーケストラ系の出力が劇的に厚くなる。
**コスト**: 中(1.5 週間)。
**前提**: 既存の voicing module(parallel fifths 検出)を活用。

#### ★3 Trajectory 多次元連動
**目的**: 原則 4(時間軸第一)を実装で活かす。tension が上がったら velocity だけでなく、和声複雑度・音域・密度・リズム緻密度すべてが連動。
**実装**: `src/yao/ir/trajectory.py` に `derive_generation_params()` を追加。既存の rule_based / stochastic generator を改修して、各小節で `derive_generation_params(trajectory, bar)` を呼び出して全パラメータを動的調整。compliance test を `tests/scenarios/test_trajectory_compliance.py` で検証。
**効果**: 同じ trajectory.yaml で生成物の音楽的差異が劇的に拡大。セクション間コントラストが鮮明に。
**コスト**: 中(1.5 週間)。
**前提**: なし。

#### ★4 Adversarial Critic の機械検出ルール(15+)
**目的**: `/critique` を LLM の自由解釈ではなく、再現性のある機械検出に。
**実装**: `src/yao/verify/critique/` パッケージ新設。`CritiqueRule` プロトコルと `Finding` dataclass。役割別(structural / melodic / harmonic / rhythmic / arrangement / emotional)に最低 15 ルール実装(ClimaxAbsenceDetector, ClicheChordProgressionDetector, ContourMonotonyDetector, FrequencyCollisionDetector, IntentDivergenceDetector 等)。`/critique` コマンドはこれらの結果を整形するだけになる。
**効果**: 同じ生成物に対する批評の再現性確保。conductor の adapt 機構が**問題コードに基づく具体的修正**を生成可能に。
**コスト**: 大(3〜4 週間、1 ルール = 半日 × 15)。並列開発可能。
**前提**: なし。

#### ★5 Feature Status Matrix
**目的**: README/CLAUDE.md/PROJECT.md 間の能力主張のズレを単一の真実源で解消。
**実装**: PROJECT.md §4(本文書)+ `FEATURE_STATUS.md`(詳細)+ `tools/feature_status_check.py`(README の能力主張と実装の自動照合、warning レベル)。
**効果**: ユーザが 30 秒で「これはどこまで動くか」を把握可能。ドキュメント維持コスト低下。
**コスト**: 小(2〜3 日)。
**前提**: なし。**最初に着手すべき**。

#### ★6 yao preview / yao watch(即時試聴)
**目的**: 「YAML 編集 → compose → render → 外部プレイヤー」の遅さを解消。反復速度を 10 倍にする。
**実装**: `src/cli/preview.py`(FluidSynth + sounddevice によるメモリ上即時再生)。`src/cli/watch.py`(watchdog による spec ファイル監視 + 自動再生成 + 自動再生)。
**効果**: 反復制作の集中力が切れない。「ちょっと変えて聴く」が成立する。
**コスト**: 小〜中(1 週間)。`sounddevice` と `watchdog` 依存追加のみ。
**前提**: なし。

#### ★7 ジャンル Skill 量産(8+)
**目的**: cinematic 1 個から、最低 8 ジャンルへ拡大。
**実装**: 標準スキーマ(tempo / keys / progressions / drum_patterns / instrumentation / cliches / use cases)で 7 ジャンル追加。front-matter YAML から `src/yao/skills/genres/<name>.yaml` を自動生成。**Python 不要、Markdown のみで貢献可能**(ミュージシャン貢献者向け)。
**効果**: ユーザがジャンルを指定できる範囲が 8 倍に。Claude Code の `/sketch` 対話で具体的指針が得られる。
**コスト**: 中(各 Skill 半日 × 7 = 3〜4 日)。並列実行可能。
**前提**: なし。ただし★1 のドラムパターンライブラリと連動するため、★1 完了後がスムーズ。

#### ★8 RecoverableDecision(silent fallback の解消)
**目的**: 原則 2(説明可能性)を完全実装。silent な clamp/fallback を全てログ化。
**実装**: `src/yao/verify/recoverable.py`(`RecoverableDecision` dataclass)。`ProvenanceLog.record_recoverable()` メソッド追加。既存の silent fallback 群(stochastic.py の bass range fallback 等)を inventory 化(`docs/migration/silent-fallback-inventory.md`)、順次置換。`tools/check_silent_fallback.py` で AST ベース静的検出。
**効果**: provenance.json から「妥協の履歴」が読み取れる。conductor の adapt が根本修正を試みられる。
**コスト**: 中(1.5 週間)。
**前提**: ★4(Critique 機械化)後だと、recoverable decision を Finding と統合しやすい。

#### ★9 Golden MIDI テスト
**目的**: 生成器変更時の意図しない音楽的退行を自動検出。
**実装**: `tests/golden/`(inputs / expected / test_golden.py / regenerate_goldens.py)。最低 6 つの golden(minimal × {rule_based, stochastic} + pop_basic + cinematic_basic)。`make test-golden` ターゲット。`regenerate_goldens.py` は `--reason` 必須・`--confirm` 必須。
**効果**: ★1〜★8 の各実装後、「以前と同じ品質を保ちつつ機能が増えた」が証明可能。
**コスト**: 小(1 週間)。
**前提**: なし。**早期に着手すべき**(他改善の安全網になる)。

### 14.3 推奨実装順序

```
Week 1:    ★5 Feature Status Matrix(2-3 日)+ ★9 Golden MIDI tests 基盤(残り)
Week 2:    ★6 yao preview / yao watch
Week 3-4:  ★3 Trajectory 多次元連動
Week 5-6:  ★1 DrumPattern IR + drum_patterner
Week 7-8:  ★2 Counter-melody generator
Week 9-12: ★4 Adversarial Critic 機械検出ルール(15+、並列開発)
Week 9-12: ★7 ジャンル Skill 量産(★4 と並行、ミュージシャン貢献者担当)
Week 13-14: ★8 RecoverableDecision
```

3〜4 か月で全 9 改善が完了。これは**前回の v2.0 大改造提案(180 日)より短く、はるかに実装可能性が高い**プランです。

### 14.4 各改善の Pull Request 規約

各改善は独立した PR として完結すること。PR description に以下を含める:

- 担当する改善番号(★N)
- 該当する Feature Status Matrix のエントリ更新
- 後方互換性の確認(既存 spec / 既存 MIDI が動くこと)
- 音声サンプル(★1, ★2, ★3 等、生成出力に影響するもの)
- 追加・更新したテスト

---

## 15. 開発ロードマップ

### v1.1 マイルストーン(本ドキュメントの目標)

3〜4 か月で 9 改善完了。Feature Status Matrix の以下が ✅ になる:

- DrumPattern IR + drum_patterner
- Counter-melody generator
- Trajectory 多次元連動
- Adversarial Critic 機械検出ルール(15+)
- Feature Status Matrix
- yao preview / yao watch
- ジャンル Skill 8+
- RecoverableDecision
- Golden MIDI tests

### v1.1 完了時に達成される品質

- **ジャンル幅**: 1 (cinematic) → 8+
- **音楽の厚み**: 3声体 → ドラム + 対旋律 + 内声で 6声体以上
- **trajectory の効果**: 1 次元(velocity) → 5 次元連動
- **Critic の精度**: 自由解釈 → 15+ ルール機械検出
- **反復速度**: 数十秒 → リアルタイム
- **回帰検出**: 無 → ゴールデン MIDI 自動比較
- **ドキュメント整合性**: 微小ズレあり → Feature Status Matrix で一元化

### Phase 2(v1.1 完了後)— 編曲エンジン

YaO の最大の差別化要素である**編曲エンジン**を実装。MIDI を入力として読み込み、構造解析・保持/変換契約・ジャンル変換・差分レポート生成。

主な機能:
- Source MIDI 解析(セクション検出、メロディ抽出、コード推定、モチーフ検出)
- Preservation Plan(melody similarity ≥ 0.85 等の保持契約)
- Transformation Plan(target genre, BPM, reharmonization level 等)
- Style Vector 演算(genre 間の特徴量ベクトル演算)
- Arrangement Diff(Markdown レポート:何が保持され、何が変わったか)

### Phase 3 — Perception Substitute Layer

「LLM が音楽を聴けない」問題への構造的解答。

- Stage 1: Audio features(LUFS, spectral, onset density)
- Stage 2: Use-case targeted evaluation(BGM/Game/Ad/Study 別評価軸)
- Stage 3: Reference matching(抽象特徴のみで著作権リスク回避)

### Phase 4 — プロダクション統合

- Production Manifest + Mix Chain(pedalboard 経由の EQ/comp/reverb/limiter)
- Multi-format output(MusicXML, LilyPond/PDF, Strudel)
- Sketch-to-Spec 対話状態機械
- Reaper MCP 連携

### Phase 5 — 学習と進化

- Reflection Layer(Layer 7)の本格運用:ユーザ別スタイルプロファイル
- AI 音楽モデル連携(Stable Audio, MusicGen)
- ライブ即興モード

### ユーザ価値ドリブン マイルストーン

| マイルストーン | ユーザ価値 | v1.1 で実現 |
|---|---|---|
| **1. Describe & Hear** | 「YAMLで記述し、即座に聴ける」 | ✅ + ★6 で大幅強化 |
| **2. Iterate & Improve** | 「不満点を伝えると改善される」 | ✅ + ★4 で精度向上 |
| **3. Richer Music** | 「プロ品質のハーモニー・リズム・ダイナミクス」 | ★1 + ★2 + ★3 で初めて達成 |
| **4. My Style** | 「好みを学習し、自分のスタイルで生成」 | Phase 2-3 |
| **5. Production Ready** | 「実プロジェクトで使える出力」 | Phase 4 |

### 戦略的洞察

YaO の設計パターンは音楽に限定されない、**構造化された人間-AI 創造的協働の汎用フレームワーク**です。

| YaO パターン | 汎用パターン | 他ドメインへの応用 |
|---|---|---|
| Score (YAML仕様) | **Intent-as-Code** | UIデザイン仕様, ナラティブ構造, ゲームレベル設計 |
| Trajectory (軌跡) | **時間品質曲線** | 動画ペーシング, プレゼンテーション構成, UXジャーニー |
| Adversarial Critic | **敵対的レビュー** | コードレビュー, デザイン批評, 文章フィードバック |
| Provenance Graph | **意思決定系譜** | AI支援の創造的作業全般 |
| 6相認知プロトコル | **構造化創造プロトコル** | 「いきなり実装しない」が重要なすべてのドメイン |

これらの抽象化は将来的に抽出可能に設計されていますが、現在のスコープは音楽制作に限定します。

### 開発プロセス指針

- **Sound-First 文化**: 生成・レンダリングに影響する変更には、変更前後の音声サンプルを含める
- **ドキュメント予算**: 設計文書 1 行あたり、実働コード 3 行以上を維持する
- **Dogfooding**: YaO で制作した音楽をプロジェクトのデモ動画や発表に使用する
- **ミュージシャン向け貢献ガイド**: ジャンル Skill 追加(★7)、テンプレート作成、参照楽曲分析は Python 不要で貢献可能
- **漸進性原則(★ v1.1)**: 1 PR = 1 改善 = 1〜2 週間。野心的な大改造より、検証可能な小さな勝利の累積を選ぶ

---

## 16. クイックスタート

### 16.1 環境構築

```bash
git clone https://github.com/shibuiwilliam/YouAndOrchestra
cd YouAndOrchestra
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts   # SoundFont 配置(初回のみ)
```

### 16.2 最初の曲を作る

```bash
# 1. プロジェクト作成
make new-project NAME=my-first-song

# 2. (★6 v1.1 後)即時試聴で反復制作
yao watch specs/projects/my-first-song/composition.yaml
# → spec を編集して保存するたびに自動再生成・自動再生

# 3. または Claude Code 起動して対話
claude

# 4. プロンプト例
> /sketch
> "雨の夜のカフェで聴きたい、少し切ない 90 秒のピアノ曲"
> (対話で仕様が固まる)
> /compose my-first-song

# 5. 結果確認
open outputs/projects/my-first-song/iterations/v001/full.mid

# 6. 反復
> /critique my-first-song              # ★4 v1.1 後:機械検出 Finding が出る
> /regenerate-section my-first-song chorus
```

### 16.3 (Phase 2)既存曲を編曲する

```bash
cp my_song.mid specs/projects/my-first-song/source.mid
> /arrange my-first-song
```

### 16.4 ドラム付きの曲を作る(★ v1.1 新機能)

`composition.yaml` に `drums:` セクションを追加するだけ:

```yaml
drums:
  pattern_family: "lofi_laidback"
  swing: 0.55
  ghost_notes_density: 0.4
```

```bash
yao compose specs/projects/lofi-cafe/composition.yaml
# outputs/.../stems/drums.mid が生成される
```

---

## 17. ファイル形式と相互運用性

YaO は以下の標準フォーマットを採用し、外部ツールとの相互運用性を担保します。

| 用途 | 形式 | 理由 |
|---|---|---|
| 楽曲データ | MIDI (.mid) | 業界標準・全 DAW 対応 |
| 楽曲データ(将来) | MusicXML (.xml) | Phase 4 で実装 |
| 楽譜(将来) | LilyPond (.ly), PDF | Phase 4 で実装 |
| 仕様 | YAML | 人間可読・git 管理向き |
| 中間表現 | JSON | プログラム可読・スキーマ検証 |
| 来歴 | JSON | グラフ構造の表現 |
| 音声 | WAV(制作中)、FLAC/MP3(配布) | 標準対応 |
| ライブコード(将来) | Strudel パターン文字列 | Phase 4 でブラウザ即試聴 |

独自フォーマットは原則として作りません。既存の標準で表現できないものだけを最小限定義します。

---

## 18. 倫理とライセンス指針

### 18.1 学習データと参照
参照ライブラリには **権利クリア済楽曲のみ**を配置します。各楽曲には `references/catalog.yaml` でライセンス状態を記録し、不明な楽曲は使用しません。

### 18.2 アーティスト模倣
「特定の現役アーティスト風」の指定は推奨しません。代わりに、以下のような**抽象的特徴記述**を推奨します。

> ✗ 「Joe Hisaishi 風」
> ✓ 「広いオープンヴォイシングの弦楽、上昇するモチーフ、長短調の揺らぎ、瞑想的なテンポ」

スキーマレベルで強制(references.yaml の `do_not_copy:` フィールドは melody / chord_progression / identifiable_hook を含むことが必須)。

### 18.3 生成物の権利
YaO で生成した楽曲の権利は、原則としてユーザに帰属します。ただし、参照楽曲の影響度が極端に高い場合は警告を出します(将来の Reference Matcher 連動)。

### 18.4 透明性
すべての生成物には「YaO で生成した」旨と、参照した美的アンカーのリストを `provenance.json` に記録することを推奨します。

---

## 19. CLAUDE.md との関係

`CLAUDE.md` は **エージェントへの不変指示**を含む短い文書です。本 PROJECT.md は**人間とエージェント双方が参照する全体設計書**です。

役割分担:

| ファイル | 対象 | 内容 |
|---|---|---|
| `PROJECT.md` (本書) | 人間 + エージェント | 全体設計・哲学・アーキテクチャ・改善計画 |
| `CLAUDE.md` | エージェント中心 | 不変ルール・禁止事項・Skill 参照ポインタ |
| `FEATURE_STATUS.md` (★ v1.1 新設) | 人間 + エージェント | 機能の実装状態の単一の真実源 |
| `README.md` | 人間中心 | クイックスタート・最低限の使用法(能力主張は FEATURE_STATUS.md にリンク) |
| `docs/design/*.md` | 人間 + エージェント | 個別の設計判断記録(ADR) |
| `development/*.md` | 開発者 + エージェント | 技術的開発ドキュメント |
| `docs/` (mkdocs) | ユーザ + 開発者 | mkdocs 構成のドキュメントサイト |

**規律**: 機能の実装状態に関する記述は、PROJECT.md・README.md・CLAUDE.md には書かず、FEATURE_STATUS.md にだけ書く。他文書からはリンクのみ。これにより v1.0 で発生した「README に 226 tests、CLAUDE.md に ~190 tests」のような微小なズレを防ぐ。

---

## 20. 将来のアーキテクチャ拡張計画

以下は**v1.1 完了後**の検討項目です。実装は各マイルストーンの必要性に応じて行います。

### 20.1 セッション/プロジェクト ランタイム層
現在のCLIはステートレスです。将来的に、反復的な制作セッションを支援する `ProjectRuntime` を導入します:
- 生成キャッシュ(セクション単位の再生成を高速化)
- フィードバックキュー(批評→修正のループ)
- undo/redo(音楽レベルでの取り消し・やり直し)

### 20.2 抽象エージェントプロトコル
`.claude/agents/*.md` の Subagent 定義は Claude Code に結合しています。将来的に、バックエンド非依存の Python プロトコル (`AgentRole`, `AgentContext`, `AgentOutput`) を定義し、Claude Code 実装を 1 つのアダプターとして扱います。

### 20.3 スペック合成(Composability)
`specs/fragments/` による再利用可能なスペック断片と、`extends:` / `overrides:` キーワードによるスペック合成を導入します。

### 20.4 Reflection Layer の本格運用
Layer 7 を活性化し、ユーザ別スタイルプロファイル、コミュニティ参照ライブラリ共有規格を実装。

---

## 21. 用語集

**Conductor(指揮者)** — プロジェクトの所有者である人間。最終判断者。

**Orchestra(楽団)** — Subagent 群の総称。

**Score(楽譜)** — `specs/` 内の YAML 群。楽曲の完全な記述。

**Score IR** — Score を実装が扱える中間表現に変換したもの。

**DrumPattern** — ★ v1.1 新設。ドラム楽器のヒット列(kick/snare/hat/etc.)の中間表現。

**Trajectory(軌跡)** — 楽曲の時間軸上の特性曲線(緊張度・密度・予測可能性・明度・音域高さ)。★ v1.1 で多次元連動が実装される。

**Aesthetic Reference Library** — 美的アンカーとなる楽曲群。抽象特徴のみで比較。

**Perception Substitute Layer** — AI が音楽を「聴けない」ことを補う層(Phase 3 で本格実装)。

**Provenance(来歴)** — すべての生成判断の追跡可能な記録。

**Adversarial Critic** — 生成物を意図的に攻撃する批評 Subagent。★ v1.1 で 15+ 機械検出ルール化。

**Finding** — ★ v1.1 新設。Adversarial Critic が出す構造化された問題報告(rule_id, severity, role, issue, evidence, location, recommendation)。

**RecoverableDecision** — ★ v1.1 新設。silent fallback ではなく、明示的に記録された妥協。

**Negative Space(否定空間)** — 鳴らさない部分の設計。

**Style Vector** — ジャンルやスタイルを多次元特徴量空間のベクトルとして表現したもの(Phase 2)。

**Iteration(反復)** — 同一プロジェクト内の生成版。`v001`, `v002`, ... と版管理される。

**Music Lint** — 音楽理論・制約違反の自動検出機構。

**Sketch-to-Spec** — 自然言語スケッチから YAML 仕様への対話的変換プロセス。

**Feature Status Matrix** — ★ v1.1 新設。機能の実装状態の単一の真実源(PROJECT.md §4)。

**Golden MIDI Test** — ★ v1.1 新設。固定 spec × 固定 seed × 固定生成戦略 → 期待 MIDI の bit-exact 比較による退行検出。

**漸進性原則(原則 6)** — ★ v1.1 新設。動いているものを壊さず、小さな改善の累積で品質を上げる方針。

---

## 22. 最後に:YaO が目指す世界

YaO は「AI が音楽を作る」プロジェクトではありません。**人間と AI が、それぞれの長所を活かして音楽を共創する**ためのインフラです。

- 人間は **意図と判断と感性** を提供します。
- AI は **理論知識・反復速度・記録の網羅性** を提供します。
- YaO は **両者を構造化された協働プロセスとして成立させる場** です。

優れた音楽は、最終的には **人間の魂の発露** であり続けます。YaO はその発露を **より速く、より深く、より再現可能に** することを目指します。

### v1.1 の核心メッセージ

v1.0 で築かれた基盤は、Phase 1 完了の整然とした骨組みです。v1.1 では、この骨組みに**音楽的な肉付け**を行います:

- ドラムが鳴り、対旋律が絡み、軌跡が全パラメータに効く
- 批評が再現性を持ち、即時に試聴でき、複数ジャンルが扱える
- 後方互換性が守られ、退行が機械検出され、ドキュメントが整合する

これらが揃って初めて、YaO は「より高い品質で幅広く多様に柔軟に音楽制作できる」環境となります。**野心的な再設計より、地に足のついた漸進的進化を**。これが v1.1 の本質です。

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve.*
