# You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

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
│   music21 / MusicXML / 独自IR                        │
├─────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                        │
│   生成アルゴリズム選択(規則/確率/制約充足/AI連携)     │
├─────────────────────────────────────────────────────┤
│ Layer 1: Specification                              │
│   YAML仕様、対話、スケッチ入力                         │
└─────────────────────────────────────────────────────┘
```

層間の依存は厳密に下から上へのみ流れます。下位層の変更は上位層に影響しますが、上位層を変えても下位層は影響を受けません。これにより、たとえば Generation Strategy(層2)を「規則ベース」から「確率モデル」に切り替えても、Specification(層1)はそのまま使えます。

---

## 4. ディレクトリ構造

```
yao/
├── CLAUDE.md                      # エージェントへの不変指示
├── PROJECT.md                     # 本ファイル(プロジェクト全体設計)
├── README.md                      # ユーザ向けクイックスタート
├── pyproject.toml                 # Python依存(pretty_midi, music21, librosa等)
├── Makefile                       # 主要コマンド(make compose, make render等)
│
├── .claude/
│   ├── commands/                  # Custom Commands (/compose, /arrange, etc.)
│   │   ├── compose.md
│   │   ├── arrange.md
│   │   ├── critique.md
│   │   ├── morph.md
│   │   ├── improvise.md
│   │   ├── explain.md
│   │   └── regenerate-section.md
│   ├── agents/                    # Subagent定義
│   │   ├── composer.md
│   │   ├── harmony-theorist.md
│   │   ├── rhythm-architect.md
│   │   ├── orchestrator.md
│   │   ├── adversarial-critic.md
│   │   ├── mix-engineer.md
│   │   └── producer.md
│   ├── skills/                    # 専門知識モジュール
│   │   ├── genres/
│   │   │   ├── cinematic.md
│   │   │   ├── lofi-hiphop.md
│   │   │   ├── j-pop.md
│   │   │   ├── neoclassical.md
│   │   │   └── ambient.md
│   │   ├── theory/
│   │   │   ├── voice-leading.md
│   │   │   ├── reharmonization.md
│   │   │   ├── counterpoint.md
│   │   │   └── modal-interchange.md
│   │   ├── instruments/
│   │   │   ├── strings.md
│   │   │   ├── piano.md
│   │   │   ├── drums.md
│   │   │   └── synths.md
│   │   └── psychology/
│   │       ├── tension-resolution.md
│   │       ├── emotion-mapping.md
│   │       └── memorability.md
│   └── hooks/                     # 自動実行フック
│       ├── pre-commit-lint.sh
│       ├── post-generate-render.sh
│       ├── post-generate-critique.sh
│       └── update-provenance.sh
│
├── specs/                         # 楽曲仕様(指揮者が書く・対話で生成される)
│   ├── projects/
│   │   └── neon-morning/
│   │       ├── intent.md          # 楽曲の意図(自然言語)
│   │       ├── composition.yaml   # 作曲パラメータ
│   │       ├── trajectory.yaml    # 時間軸軌跡
│   │       ├── references.yaml    # 美的参照ライブラリ
│   │       ├── negative-space.yaml # 否定空間設計
│   │       └── arrangement.yaml   # 編曲パラメータ(編曲時)
│   └── templates/                 # 仕様テンプレート
│       ├── bgm-90sec.yaml
│       ├── cinematic-3min.yaml
│       └── loopable-game-bgm.yaml
│
├── src/                           # コアエンジン実装
│   ├── yao/
│   │   ├── __init__.py
│   │   ├── schema/                # 仕様バリデーション
│   │   ├── generators/            # Layer 2: 生成戦略
│   │   │   ├── rule_based.py
│   │   │   ├── markov.py
│   │   │   ├── constraint_solver.py
│   │   │   └── ai_bridge.py
│   │   ├── ir/                    # Layer 3: 中間表現
│   │   │   ├── score_ir.py
│   │   │   ├── trajectory.py
│   │   │   └── motif.py
│   │   ├── perception/            # Layer 4: 知覚代替
│   │   │   ├── reference_matcher.py
│   │   │   ├── psych_mapper.py
│   │   │   └── style_vector.py
│   │   ├── render/                # Layer 5: レンダリング
│   │   │   ├── midi_writer.py
│   │   │   ├── audio_renderer.py
│   │   │   ├── lilypond_writer.py
│   │   │   └── strudel_emitter.py
│   │   ├── verify/                # Layer 6: 検証
│   │   │   ├── music_lint.py
│   │   │   ├── analyzer.py
│   │   │   ├── evaluator.py
│   │   │   └── diff.py
│   │   └── reflect/               # Layer 7: 学習
│   │       ├── provenance.py
│   │       ├── feedback_loop.py
│   │       └── style_profile.py
│   └── cli/                       # コマンドラインインターフェース
│
├── references/                    # 美的参照ライブラリ
│   ├── catalog.yaml               # 参照楽曲のメタデータ
│   ├── midi/                      # MIDIファイル(権利クリア済のみ)
│   ├── musicxml/
│   └── extracted_features/        # 事前抽出された特徴量
│
├── outputs/                       # 生成成果物
│   └── projects/
│       └── neon-morning/
│           ├── iterations/
│           │   ├── v001/
│           │   │   ├── stems/     # 各楽器のMIDI
│           │   │   ├── full.mid
│           │   │   ├── score.musicxml
│           │   │   ├── score.pdf
│           │   │   ├── audio.wav
│           │   │   ├── analysis.json
│           │   │   ├── critique.md
│           │   │   └── provenance.json
│           │   ├── v002/
│           │   └── v003/
│           └── final/
│
├── soundfonts/                    # 音色ライブラリ
│   ├── orchestral/
│   ├── electronic/
│   └── README.md                  # SoundFont入手・配置ガイド
│
├── tests/                         # 音楽制約テスト
│   ├── test_voice_leading.py
│   ├── test_range_constraints.py
│   ├── test_trajectory_match.py
│   ├── test_section_contrast.py
│   └── test_motif_preservation.py
│
└── docs/
    ├── design/                    # 設計判断の記録
    ├── tutorials/                 # チュートリアル
    └── glossary.md                # 用語集
```

---

## 5. オーケストラの編成:Subagent 設計

YaO の楽団員(Subagents)は明確な役割と制約を持ちます。各 Subagent は専用コンテキスト・専用ツール許可・専用評価基準を持ち、独立して動作したのち Producer Subagent によって統合されます。

### 5.1 Composer(作曲家)
**責任:** メロディ・主題・構成の生成
**入力:** intent.md, composition.yaml, trajectory.yaml, references.yaml
**出力:** Score IR(モチーフ・旋律ライン・構成情報)
**禁止事項:** 楽器選択・最終ヴォイシング(これは Orchestrator の仕事)
**評価軸:** モチーフの記憶性・反復と変奏のバランス・軌跡への適合度

### 5.2 Harmony Theorist(和声理論家)
**責任:** コード進行・転調・代理コード・終止の設計
**入力:** Composer の主旋律案、composition.yaml の harmony セクション
**出力:** コード進行 IR(機能和声記述+具体ヴォイシング候補)
**評価軸:** 機能整合性・テンション解決・ジャンル適合性

### 5.3 Rhythm Architect(リズム設計者)
**責任:** ドラムパターン・グルーヴ・シンコペーション・フィル
**入力:** composition.yaml の rhythm セクション、ジャンル指定
**出力:** リズム IR(全楽器のリズム配置)
**評価軸:** グルーヴ感・人間味・セクション間コントラスト

### 5.4 Orchestrator(編成者)
**責任:** 楽器割り当て・ヴォイシング・音域配置・対旋律
**入力:** Composer/Harmony/Rhythm の出力すべて
**出力:** 完全な Score IR(楽器ごとの全パート)
**評価軸:** 周波数空間の衝突回避・楽器の慣用的使用・テクスチャ密度

### 5.5 Adversarial Critic(敵対的批評家)
**責任:** あらゆる弱点の発見と指摘
**入力:** 生成された任意段階の成果物
**出力:** critique.md(問題点リストと深刻度評価)
**特性:** **賞賛しないことが原則**。クリシェ検出・構造的退屈さ・感情的不整合・既存曲類似度を厳しく評価
**評価軸:** 問題発見の網羅性と具体性

### 5.6 Mix Engineer(ミックスエンジニア)
**責任:** ステレオ配置・ダイナミクス・周波数マスキング解消・ラウドネス管理
**入力:** Orchestrator の出力 + production パラメータ
**出力:** ミックス指示書(各トラックの EQ/コンプ/リバーブ/パン設定)
**評価軸:** LUFS 基準達成・周波数バランス・ステレオ広がり

### 5.7 Producer(プロデューサ)
**責任:** 全体統合・優先順位付け・指揮者(人間)との対話・最終判断
**入力:** すべての Subagent の出力 + 人間からのフィードバック
**出力:** 最終的な制作判断・次の反復への指示
**特権:** 唯一、他の Subagent の出力を却下・差し戻しできる
**評価軸:** 楽曲の意図(intent.md)への忠実度

---

## 6. 作曲認知プロトコル:6 相

YaO の `/compose` および `/arrange` コマンドは、Claude Code に以下の 6 相を**順序通り**実行させます。これは認知プロセスを構造化し、エージェントが「いきなり音符を書き始める」失敗パターンを防ぎます。

### Phase 1:Intent Crystallization(意図の結晶化)
ユーザ入力(対話・YAML・スケッチ)から、楽曲の本質を 1〜3 文で言語化します。曖昧さを許さず、`intent.md` に確定させます。

> 例:「初夏の朝、新しい挑戦に向かう前向きな期待感。ただし不安も微かに混じる。爽やかすぎず、感傷的すぎない、ニュートラルな高揚」

### Phase 2:Architectural Sketch(構造スケッチ)
時間軸軌跡(tension / density / valence / predictability)を**先に**描きます。音符はまだ書きません。`trajectory.yaml` を完成させます。

### Phase 3:Skeletal Generation(骨格生成)
Composer Subagent がコード進行と主旋律の「種」を生成。**多様性のため 5〜10 候補**を作ります。完成度は 60% で十分。

### Phase 4:Critic-Composer Dialogue(批評者-作曲者対話)
Adversarial Critic が全候補を攻撃。Producer が判断し、最強の候補を選ぶか、複数の長所を統合した新候補を作らせます。

### Phase 5:Detailed Filling(詳細埋め)
選ばれた骨格に、Harmony / Rhythm / Orchestrator が詳細を埋めます。各判断は Provenance に記録されます。

### Phase 6:Listening Simulation(聴取シミュレーション)
Perception Substitute Layer が完成品を「聴いて」、当初意図(Phase 1)との乖離を測定。乖離が閾値超なら該当箇所を再生成。最終的に `critique.md` と `analysis.json` が出力されます。

---

## 7. パラメータ仕様

YaO は楽曲を、以下の **8 種類の YAML ファイル**で完全に記述します。すべて版管理対象であり、git diff で変更履歴が追えます。

### 7.1 `intent.md`(意図記述、自然言語)
楽曲の本質を 1〜3 文で記述。すべての判断の最終的な根拠となる文書です。

### 7.2 `composition.yaml`(作曲パラメータ)
キー、テンポ、拍子、形式、ジャンル、楽器編成、各セクションの構造などの基礎仕様。

### 7.3 `trajectory.yaml`(時間軸軌跡)
緊張度・密度・感情価・予測可能性の時間関数。Bezier 曲線または小節単位のステップ関数で記述。

```yaml
trajectories:
  tension:
    type: bezier
    waypoints: [[0, 0.2], [16, 0.4], [32, 0.85], [48, 0.6], [64, 0.3]]
  information_density:
    type: stepped
    sections: {intro: 0.3, verse: 0.5, chorus: 0.9, bridge: 1.0}
  predictability:
    target: 0.65
    variance: 0.15
```

### 7.4 `references.yaml`(美的参照ライブラリ)
正参照(似せる)と負参照(避ける)の楽曲リスト。各参照について、「何を抽出するか」を指定。

### 7.5 `negative-space.yaml`(否定空間)
休符・周波数ギャップ・テクスチャ削除など、「鳴らさない」設計。

### 7.6 `arrangement.yaml`(編曲パラメータ、編曲時のみ)
原曲入力、保持項目、変換項目、回避項目の明示。

### 7.7 `production.yaml`(ミックス・マスタリング)
LUFS 目標、ステレオ幅、リバーブ量など最終音響仕様。

### 7.8 `provenance.json`(自動生成、手書き不可)
全ての生成判断の来歴記録。各音符・コード・楽器選択の「なぜ」を保持。

---

## 8. Custom Commands(指揮者の指示棒)

ユーザは以下のコマンドで Orchestra を動かします。各コマンドは `.claude/commands/*.md` に定義されます。

| コマンド | 用途 | 主要 Subagent |
|---|---|---|
| `/compose <project>` | 仕様から新曲を生成 | Composer → 全員 |
| `/arrange <project>` | 既存曲を編曲 | Orchestrator + Adversarial Critic |
| `/critique <iteration>` | 既存生成物を批評 | Adversarial Critic |
| `/regenerate-section <project> <section>` | 特定セクションのみ再生成 | Composer + Producer |
| `/morph <from> <to> <bars>` | 2 つの楽曲調を補間 | Composer + Orchestrator |
| `/improvise <input>` | リアルタイム伴奏(ライブモード) | Composer + Rhythm |
| `/explain <element>` | 特定要素の生成判断を説明 | Producer(Provenance 参照) |
| `/diff <iter_a> <iter_b>` | 2 イテレーション間の音楽差分 | Verifier |
| `/render <iteration>` | MIDI を音声・楽譜に変換 | Mix Engineer |
| `/sketch` | スケッチ→仕様対話モード | Producer |

---

## 9. Skills(楽団員の素養)

`.claude/skills/` には専門知識を構造化したモジュールが配置されます。Subagent は必要に応じてこれらを参照します。

### 9.1 ジャンル Skills
各ジャンルが 1 つの Skill として定義されます。内容は、典型的なコード進行・リズムパターン・楽器編成・代表参照楽曲・回避すべきクリシェなど。

### 9.2 理論 Skills
和声法・対位法・リハーモナイゼーション・モーダル・インターチェンジ等。例外規則とジャンル依存性も明記。

### 9.3 楽器 Skills
各楽器の音域・慣用的奏法・音色特性・物理的制約・代表的フレーズパターン。

### 9.4 心理学 Skills
音楽心理学(Juslin, Huron, Krumhansl 等)の経験的マッピング。テンポと覚醒度、長短調と感情価、スペクトル重心と明るさ知覚など。

---

## 10. Hooks(自動演奏指示)

Hooks は Claude Code への指示ではなく、**実行が保証されるスクリプト**です。以下の 4 つを必ず設定します。

| Hook | タイミング | 内容 |
|---|---|---|
| `pre-commit-lint` | git commit 前 | music21 で楽理リント、仕様 YAML スキーマ検証 |
| `post-generate-render` | 生成完了後 | MIDI を自動的に音声と楽譜にレンダリング |
| `post-generate-critique` | 生成完了後 | Adversarial Critic を必ず起動 |
| `update-provenance` | あらゆる変更後 | Provenance Graph を最新状態に更新 |

これらにより、エージェントが指示を忘れても品質保証が破綻しません。

---

## 11. MCP 連携

YaO は以下の MCP サーバとの接続を想定して設計されています。

| MCP 接続先 | 用途 |
|---|---|
| **DAW(Reaper 優先)** | プロジェクトファイル読み書き、トラック自動レイアウト |
| **サンプルライブラリ** | ドラムサンプル・ワンショット・ループの検索と取得 |
| **参照楽曲 DB** | 権利クリア済の参考楽曲メタデータ・特徴量検索 |
| **MIDI コントローラ** | ライブ即興モードの入力 |
| **SoundFont/VST サーバ** | 音色レンダリング |
| **クラウドストレージ** | 生成物のバックアップとチーム共有 |

---

## 12. 品質保証:評価指標

YaO は生成物を以下の 5 領域で自動評価します。スコアは `analysis.json` に保存されます。

### 12.1 構造評価
セクションコントラスト、クライマックス位置、密度カーブ適合度、反復バランス、ループ性。

### 12.2 メロディ評価
音域適合度、モチーフ記憶性、歌唱可能性、フレーズ終止感、輪郭変化。

### 12.3 和声評価
コード機能整合性、テンション解決、和声複雑度のパラメータ適合、終止強度。

### 12.4 編曲評価(編曲モード時)
楽器役割の明確性、周波数衝突リスク、原曲保持率、変換強度。

### 12.5 音響評価
BPM 一致、ビート安定性、LUFS 目標達成、スペクトルバランス、オンセット密度。

各指標には**数値目標と許容範囲**が設定され、目標逸脱時は Adversarial Critic が自動的に問題提起します。

---

## 13. 開発ロードマップ

### Phase 0(2 週間):環境構築と MVP 骨格
プロジェクト構造、CLAUDE.md、依存環境、最小 pretty_midi 生成、SoundFont レンダリング、簡易レポート出力。

### Phase 1(1 ヶ月):パラメータ駆動シンボリック作曲
8 種パラメータ仕様の完全実装、6 相認知プロトコル、Composer/Harmony/Rhythm Subagent、music21 ベース解析、最初の評価器。

### Phase 2(1 ヶ月):編曲エンジンと差分
編曲操作群(reharmonization, regrooving, reorchestration 等)、Style Vector 実装、Arrangement Diff、Provenance 完全実装。

### Phase 3(1 ヶ月):知覚代替層と批評
Perception Substitute Layer、参照ライブラリ機構、Adversarial Critic Subagent、Multi-Resolution Trajectory。

### Phase 4(1〜2 ヶ月):高度機能
Sketch-to-Spec 対話、Music Theory KG、ジャンル Skills 充実、ライブコーディング統合(Strudel/Sonic Pi)、進化的多候補生成。

### Phase 5(2〜3 ヶ月):プロダクション統合
DAW 連携(Reaper)、AI 音楽モデル連携(Stable Audio 等)、ライブ即興モード、ユーザ嗜好学習。

### Phase 6(継続):学習と進化
Reflection & Learning Layer の本格運用、ユーザ別スタイルプロファイル、コミュニティ参照ライブラリ共有規格。

### 13.2 ユーザ価値ドリブン マイルストーン

上記の技術フェーズと並行して、以下のユーザ価値中心のマイルストーンで進捗を測定します。

| マイルストーン | ユーザ価値 | 主要機能 |
|---|---|---|
| **1. Describe & Hear** | 「YAMLで記述し、即座に聴ける」 | CLI compose, 2つの生成戦略, テンプレート, 自動バージョニング |
| **2. Iterate & Improve** | 「不満点を伝えると改善される」 | Score diff, 評価レポート, `/critique`, セクション再生成 |
| **3. Richer Music** | 「プロ品質のハーモニー・リズム・ダイナミクス」 | Harmony IR, 制約システム, 歩くベース, シンコペーション |
| **4. My Style** | 「好みを学習し、自分のスタイルで生成」 | 参照ライブラリ照合, スペック合成, スタイルプロファイル |
| **5. Production Ready** | 「実プロジェクトで使える出力」 | DAW連携, マルチフォーマット出力, ミックスエンジニア |

### 13.3 戦略的洞察

YaO の設計パターンは音楽に限定されない、**構造化された人間-AI 創造的協働の汎用フレームワーク**です。

| YaO パターン | 汎用パターン | 他ドメインへの応用 |
|---|---|---|
| Score (YAML仕様) | **Intent-as-Code** | UIデザイン仕様, ナラティブ構造, ゲームレベル設計 |
| Trajectory (軌跡) | **時間品質曲線** | 動画ペーシング, プレゼンテーション構成, UXジャーニー |
| Adversarial Critic | **敵対的レビュー** | コードレビュー, デザイン批評, 文章フィードバック |
| Provenance Graph | **意思決定系譜** | AI支援の創造的作業全般 |
| 6相認知プロトコル | **構造化創造プロトコル** | 「いきなり実装しない」が重要なすべてのドメイン |

これらの抽象化は将来的に抽出可能に設計されていますが、現在のスコープは音楽制作に限定します。

### 13.4 開発プロセス指針

- **Sound-First 文化**: 生成・レンダリングに影響する変更には、変更前後の音声サンプルを含める
- **ドキュメント予算**: 設計文書1行あたり、実働コード3行以上を維持する
- **Dogfooding**: YaO で制作した音楽をプロジェクトのデモ動画や発表に使用する
- **ミュージシャン向け貢献ガイド**: ジャンルSkill追加、テンプレート作成、参照楽曲分析はPython不要で貢献可能

---

## 14. クイックスタート

### 14.1 環境構築

```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts   # SoundFont 配置(初回のみ)
```

### 14.2 最初の曲を作る

```bash
# 1. プロジェクト作成
make new-project NAME=my-first-song

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

### 14.3 既存曲を編曲する

```bash
cp my_song.mid specs/projects/my-first-song/source.mid
> /arrange my-first-song
```

---

## 15. ファイル形式と相互運用性

YaO は以下の標準フォーマットを採用し、外部ツールとの相互運用性を担保します。

| 用途 | 形式 | 理由 |
|---|---|---|
| 楽曲データ | MIDI (.mid), MusicXML (.xml) | 業界標準・全 DAW 対応 |
| 楽譜 | LilyPond (.ly), PDF | 高品質楽譜・自動レンダリング |
| 仕様 | YAML | 人間可読・git 管理向き |
| 中間表現 | JSON | プログラム可読・スキーマ検証 |
| 来歴 | JSON | グラフ構造の表現 |
| 音声 | WAV (制作中), FLAC/MP3 (配布) | 標準対応 |
| ライブコード | Strudel パターン文字列 | ブラウザ即試聴可能 |

独自フォーマットは原則として作りません。既存の標準で表現できないものだけを最小限定義します。

---

## 16. 倫理とライセンス指針

### 16.1 学習データと参照
参照ライブラリには **権利クリア済楽曲のみ**を配置します。各楽曲には `references/catalog.yaml` でライセンス状態を記録し、不明な楽曲は使用しません。

### 16.2 アーティスト模倣
「特定の現役アーティスト風」の指定は推奨しません。代わりに、以下のような**抽象的特徴記述**を推奨します。

> ✗ 「Joe Hisaishi 風」
> ✓ 「広いオープンヴォイシングの弦楽、上昇するモチーフ、長短調の揺らぎ、瞑想的なテンポ」

### 16.3 生成物の権利
YaO で生成した楽曲の権利は、原則としてユーザに帰属します。ただし、参照楽曲の影響度が極端に高い場合は警告を出します。

### 16.4 透明性
すべての生成物には「YaO で生成した」旨と、参照した美的アンカーのリストを `provenance.json` に記録することを推奨します。

---

## 17. CLAUDE.md との関係

`CLAUDE.md` は **エージェントへの不変指示**を含む短い文書です。本 PROJECT.md は**人間とエージェント双方が参照する全体設計書**です。

役割分担:

| ファイル | 対象 | 内容 |
|---|---|---|
| `PROJECT.md` (本書) | 人間 + エージェント | 全体設計・哲学・アーキテクチャ |
| `CLAUDE.md` | エージェント中心 | 不変ルール・禁止事項・Skill 参照ポインタ |
| `README.md` | 人間中心 | クイックスタート・最低限の使用法 |
| `docs/design/*.md` | 人間 + エージェント | 個別の設計判断記録 |
| `development/*.md` | 開発者 + エージェント | 技術的開発ドキュメント(API, アーキテクチャ, テスト戦略) |
| `docs/` (mkdocs) | ユーザ + 開発者 | mkdocs構成のドキュメントサイト |

---

## 18. 将来のアーキテクチャ拡張計画

以下は検討中の将来拡張です。実装は各マイルストーンの必要性に応じて行います。

### 18.1 セッション/プロジェクト ランタイム層

現在のCLIはステートレスです。将来的に、反復的な制作セッションを支援する `ProjectRuntime` を導入します:
- 生成キャッシュ(セクション単位の再生成を高速化)
- フィードバックキュー(批評→修正のループ)
- undo/redo(音楽レベルでの取り消し・やり直し)

### 18.2 抽象エージェントプロトコル

`.claude/agents/*.md` のSubagent定義は Claude Code に結合しています。将来的に、バックエンド非依存の Python プロトコル (`AgentRole`, `AgentContext`, `AgentOutput`) を定義し、Claude Code 実装を1つのアダプターとして扱います。

### 18.3 即時フィードバックパス

YAML → MIDI → WAV → 外部プレイヤーのパイプラインはレイテンシが高すぎます。将来的に:
- `yao preview` コマンドによるインラインMIDI再生
- Strudel パターン出力によるブラウザベース即時試聴
- `sounddevice` による直接WAV再生

### 18.4 スペック合成(Composability)

`specs/fragments/` による再利用可能なスペック断片と、`extends:` / `overrides:` キーワードによるスペック合成を導入します。

---

## 19. 用語集

**Conductor(指揮者)** — プロジェクトの所有者である人間。最終判断者。

**Orchestra(楽団)** — Subagent 群の総称。

**Score(楽譜)** — `specs/` 内の YAML 群。楽曲の完全な記述。

**Score IR** — Score を実装が扱える中間表現に変換したもの。

**Trajectory(軌跡)** — 楽曲の時間軸上の特性曲線(緊張度・密度等)。

**Aesthetic Reference Library** — 美的アンカーとなる楽曲群。

**Perception Substitute Layer** — AI が音楽を「聴けない」ことを補う層。

**Provenance(来歴)** — すべての生成判断の追跡可能な記録。

**Adversarial Critic** — 生成物を意図的に攻撃する批評 Subagent。

**Negative Space(否定空間)** — 鳴らさない部分の設計。

**Style Vector** — ジャンルやスタイルを多次元特徴量空間のベクトルとして表現したもの。

**Iteration(反復)** — 同一プロジェクト内の生成版。`v001`, `v002`, ... と版管理される。

**Music Lint** — 音楽理論・制約違反の自動検出機構。

**Sketch-to-Spec** — 自然言語スケッチから YAML 仕様への対話的変換プロセス。

---

## 20. 最後に:YaO が目指す世界

YaO は「AI が音楽を作る」プロジェクトではありません。**人間と AI が、それぞれの長所を活かして音楽を共創する**ためのインフラです。

- 人間は **意図と判断と感性** を提供します。
- AI は **理論知識・反復速度・記録の網羅性** を提供します。
- YaO は **両者を構造化された協働プロセスとして成立させる場** です。

優れた音楽は、最終的には **人間の魂の発露** であり続けます。YaO はその発露を **より速く、より深く、より再現可能に** することを目指します。

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve.*

---

**Project: You and Orchestra (YaO)**
*Document version: 1.0*
*Last updated: 2026-04-27*