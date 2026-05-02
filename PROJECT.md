# You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

> **Document version**: 3.0 (Closing-the-Gap Edition)
> **Supersedes**: PROJECT.md v2.0
> **Effective date**: 2026-05-02
> **Status**: This revision is written **after a full implementation audit** of the YaO codebase. v2.0 set ambitious goals; v3.0 confronts the **gap between documented capability and actual capability** and lays out a disciplined plan to close it.

---

## 0. なぜ v3.0 が必要か — 監査結果の率直な要約

v2.0 は素晴らしい設計書でした。しかし実装監査の結果、**FEATURE_STATUS.md が ✅ と表示する多くの機能が、実態としては「動作するスタブ」に過ぎない**ことが判明しました。

監査で確認された主要なギャップ:

| 領域 | ドキュメントの主張 | 実装の実態 |
|---|---|---|
| **Subagent system** | 7 つの専門 Subagent が役割分担 | `MotifPlan(seeds=[], placements=[])` — Composer は空計画を返す |
| **LLM backends** | Anthropic API / Claude Code 接続済 | 両方とも PythonOnly に丸投げするスタブ |
| **V2 pipeline** | Plan → Note の二段アーキテクチャ | NoteRealizer が Plan を v1 spec に逆変換して旧 Generator を呼ぶ |
| **NL → spec** | 自然言語から仕様生成 | 24 キーワードのハードコード辞書、日本語非対応 |
| **Genre Skills (22)** | ジャンル知識が生成に反映 | 生成パイプラインから一切参照されていない |
| **Adversarial Critic** | 19 ルールで弱点検出 | MotifPlan が空のため、最重要な melodic memorability ルールが**沈黙する** |
| **Reference library** | 美的アンカー比較 | 楽曲 0 件、StyleVector に melody/harmony 情報なし |
| **Audio loop** | レンダリング後評価 → 修正 | MIDI 評価で完結、audio→adaptation のループは未実装 |
| **Subjective ratings** | 人間による品質ループ | 開発者の自己評価 1 件のみ |

**v3.0 のテーゼ**: 新機能を増やすのではなく、**既に「実装済」と称している機能の中身を本当に実装する**。設計書と実装の乖離を解消することが、次の質的飛躍の前提条件である。

---

## 1. 不変のもの:メタファーと哲学

v3.0 は v2.0 のメタファーと哲学を**変更しません**。これらは正しく、機能しているからです。

| YaO の構成要素 | オーケストラの比喩 | 実装上の対応 |
|---|---|---|
| **You** | 指揮者 (Conductor) | プロジェクト所有者である人間 |
| **Score** | 楽譜 | `specs/*.yaml` に記述された作曲仕様 |
| **Plan** | リハーサル計画 | `MusicalPlan` (MPIR) — 音符の前の "なぜ" |
| **Orchestra Members** | 楽団員 | 各 Subagent |
| **Concertmaster** | コンサートマスター | Producer Subagent |
| **Rehearsal** | リハーサル | 生成・評価・修正の反復ループ |
| **Library** | 楽団の楽譜庫 | `references/` |
| **Performance** | 本番演奏 | レンダリングされた最終音源 |
| **Critic** | 批評家 | Adversarial Critic Subagent |
| **Listener Panel** | 試聴会 | Perception Layer + ユーザラティング |
| **Cover Band** | カバー・編曲 | Arrangement Engine |

5 つの設計原則 + 第 6 原則「Vertical Alignment(垂直整合)」は v2.0 から継承します。

ただし、v3.0 では **第 7 原則** を新たに導入します。

### 原則 7:Status Honesty(ステータスの誠実さ)

**ある機能を「実装済」と表示することは、契約である。**

- ✅ は、ドキュメント化された全ての約束をコードが満たすことを意味する
- 🟡 は、部分実装で、欠けている部分が `limitation:` で明示されていることを意味する
- ⚪ は、設計だけ存在し、コードがないことを意味する
- スタブ実装に ✅ を付けることは、**プロジェクトの信頼性を毀損する重大な行為**である

v3.0 では、この原則を CI で機械的に強制します(§13)。

---

## 2. v3.0 の目標:3 つの大波

v3.0 は野心的な新機能の追加を**意図的に拒否**します。代わりに、3 つの「波」で既存機能の実体化を進めます。

### Wave 1:正直化(Honesty Wave)— 4〜6 週間

**目的**: ドキュメントとコードの乖離をゼロにする。スタブを実装に置き換える。

**主要成果**:
- Composer Subagent を本実装(モチーフ抽出と展開)
- Anthropic API バックエンドを本実装
- NL → spec 変換に LLM 統合
- StyleVector に抽象的旋律・和声情報を追加
- FEATURE_STATUS.md を実装に合わせて再採点

### Wave 2:整合化(Alignment Wave)— 8〜10 週間

**目的**: 7 層アーキテクチャを名実ともに機能させる。ジャンル Skill・Plan IR・評価指標を生成パイプラインに統合する。

**主要成果**:
- NoteRealizer V2 を本実装(MusicalPlan を直接消費)
- ジャンル Skill ローダの実装と生成器への統合
- 美的評価指標(意外性・記憶性・対比・ペーシング)
- Audio Loop を Conductor に組込

### Wave 3:深化(Depth Wave)— 8〜12 週間

**目的**: 多様な音楽表現と高品質な体験を実現する。ユーザフィードバックループを本格運用する。

**主要成果**:
- Performance Expression のパイプライン標準化
- アンサンブル制約と Orchestrator 実質化
- 参照楽曲ライブラリの整備
- Subjective rating CLI と style profile への反映
- `/sketch` 多段対話化

---

## 3. アーキテクチャ:8 層モデル(v2.0 から継承)

層構造そのものは v2.0 と同じですが、各層の **実装責任の明確化** と **層間契約の厳格化** を行います。

```
┌─────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                      │
│   ユーザ嗜好プロファイル、subjective rating の取込    │
├─────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                    │
│   構造・和声・リズム・音響評価、敵対的批評             │
├─────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                  │
│   MIDI / 音声 / 楽譜PDF / DAW / Strudel              │
├─────────────────────────────────────────────────────┤
│ Layer 4.5: Performance Expression                   │
│   Articulation / Dynamics / Microtiming / CC        │
├─────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                      │
│   Audio Features / Use-Case Eval / Reference Match  │
├─────────────────────────────────────────────────────┤
│ Layer 3.5: Musical Plan IR (MPIR)                   │
│   Form / Harmony / Motif / Phrase / Arrangement     │
├─────────────────────────────────────────────────────┤
│ Layer 3: Score IR                                   │
│   Note / Part / Section / Voicing / Timing          │
├─────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                        │
│   Plan generators + Note realizers                  │
├─────────────────────────────────────────────────────┤
│ Layer 1: Specification                              │
│   YAML 仕様 / 対話 / スケッチ                          │
└─────────────────────────────────────────────────────┘
```

### 3.1 v3.0 で強化される層間契約

各層の境界は v2.0 から存在しますが、v3.0 では**機能契約**を新設します。境界を破ることは禁止、契約を満たさないことも禁止。

| 契約 | 内容 | 強制方法 |
|---|---|---|
| **Plan completeness** | Composer が返す MotifPlan は `len(seeds) > 0` を保証 | `tests/integration/test_plan_completeness.py` |
| **Plan consumption** | Note Realizer は MusicalPlan の少なくとも 80% のフィールドを読む | AST scan で Plan 属性アクセスを計測 |
| **Skill grounding** | 生成器の振る舞いの少なくとも 1 つは、対応する Skill ファイルから来ている | `tests/integration/test_skill_grounding.py` |
| **Critic coverage** | 各 Severity レベルで、空のプランでない限り少なくとも 1 ルールが意味のある検出を行う | `tests/integration/test_critic_meaningful.py` |
| **Backend honesty** | Stub バックエンドは `is_stub=True` を返さねばならない | runtime assertion |

これらの契約は CI 必須で、違反は ✅ ステータスを失う条件です。

### 3.2 Critic Gate の機能化

Layer 3.5 から Layer 3 への遷移時、**Adversarial Critic は MPIR レベルで動作**します。これは v1.0 からの大きな改善ですが、v3.0 までは **MotifPlan が空** だったために実質機能していませんでした。Wave 1.1 後、初めて本来の機能を発揮できるようになります。

Critic Gate での選択肢:
- **承認**: Note Realizer に進む
- **計画レベル修正の提案**: Step 1〜5 のいずれかにループバック
- **計画の却下**: 異なる候補を要求(Multi-Candidate モード)

---

## 4. v3.0 の中核実装計画

ここからが v3.0 の心臓部です。各 Wave の主要実装を、**設計レベル**で詳述します。

---

## 5. Wave 1.1:Composer Subagent の本実装

### 5.1 現状の問題

```python
# src/yao/subagents/composer.py — 監査時点のコード
def process(self, context: AgentContext) -> AgentOutput:
    motif_plan = MotifPlan(seeds=[], placements=[])  # 常に空
    phrase_plan = PhrasePlan(phrases=[], bars_per_phrase=4.0, pattern="")
    return AgentOutput(motif_plan=motif_plan, phrase_plan=phrase_plan)
```

これは音楽的に致命的です。Adversarial Critic の `MotifRecurrenceDetector` は `if not plan.motif.seeds: return findings` と書かれており、**空の MotifPlan を見ると黙って通過**します。つまり、最重要な記憶可能性の検査が機能していません。

### 5.2 v3.0 での実装

Composer Subagent には**二段階の責任**を持たせます。

#### Stage A: Motif Generation(無から有)

**入力**: `IntentSpec`, `CompositionSpecV2`, `SongFormPlan`, `MultiDimensionalTrajectory`
**出力**: `MotifPlan` with `len(seeds) >= 1`

**アルゴリズム**:
1. `intent.keywords` から「motif character」を導出(例: "uplifting" → ascending interval pattern)
2. ジャンル Skill から typical motif length(beats)・interval set を取得
3. trajectory の peak position を考慮して、climax で展開可能な motif を生成
4. 各 motif について次のメタデータを記録:
   - `rhythm_shape: tuple[float, ...]` — ジャンル × 拍子 × tempo から導出
   - `interval_shape: tuple[int, ...]` — Markov モデル(`markov_models/diatonic_bigram.yaml` を再利用)で生成
   - `identity_strength: float` — 反復識別性の指標(rhythm 特異性 + interval 特異性)
   - `character: str` — 自然言語特性(「3 度上昇のリリカル」「シンコペートしたフック」)

#### Stage B: Motif Placement(構造への配置)

**入力**: `SongFormPlan`(各セクションの role と target_tension/density)、生成済 motifs
**出力**: `list[MotifPlacement]`(各 placement は section_id × bar offset × transform)

**配置戦略**:
- Verse: identity motif(主題)を使用、retrograde は使わない
- Chorus: identity motif + sequence_up での展開
- Bridge: inversion または varied_intervals(対比)
- Outro: identity motif の augmentation(時間拡大)

各 motif は**少なくとも 3 回**配置することを保証(`MotifRecurrenceDetector` の閾値と一致)。

### 5.3 実装単位

```
src/yao/subagents/composer.py            (本実装)
src/yao/ir/motif_extraction.py           (NEW: 既存スコアからの motif 抽出)
src/yao/ir/motif_generation.py           (NEW: 無からの motif 生成)
src/yao/ir/motif_placement.py            (NEW: section への配置戦略)
tests/unit/subagents/test_composer.py    (拡張: 空でないことを assert)
tests/integration/test_motif_recurrence.py (NEW: critic が検出することを確認)
```

### 5.4 完了条件

- 全テンプレート(`specs/templates/*.yaml`)で、生成後の `MotifPlan.seeds` が 1 つ以上
- `MotifRecurrenceDetector` が空のプランで silent 通過しない(critic が必ず動作する)
- 生成された MIDI の `motif_density`(StyleVector フィールド)が 0 でない

---

## 6. Wave 1.2:Anthropic API Backend の本実装

### 6.1 現状

```python
# src/yao/agents/anthropic_api_backend.py
def invoke(self, role, context, config=None):
    logger.info("anthropic_api_fallback", message="not yet implemented")
    return self._fallback.invoke(role, context, config)  # PythonOnly に丸投げ
```

`YAO_AGENT_BACKEND=anthropic` を指定しても、ログが出るだけで実際は PythonOnly が動作。これは **ユーザを欺く** 状態です。

### 6.2 v3.0 での実装方針

LLM バックエンドは **2 つの異なる種類** に分けて実装します。

#### Type A:Stateless API Backend(Anthropic API)

- 1 回のリクエストで `.claude/agents/<role>.md` を system prompt として送信
- `AgentContext` を構造化した user message として送信
- 構造化出力(tool use 経由)で `AgentOutput` のフィールドをパース
- 失敗時は `BackendError` を投げる(silent fallback 禁止)

**実装スケルトン**:

```python
class AnthropicAPIBackend:
    is_stub = False  # 原則 7 の遵守

    def __init__(self, *, api_key: str | None = None, model: str = "claude-opus-4-7"):
        if not api_key and not os.environ.get("ANTHROPIC_API_KEY"):
            raise BackendNotConfiguredError(
                "AnthropicAPIBackend requires API key. "
                "Set ANTHROPIC_API_KEY or pass api_key=. "
                "Use PythonOnlyBackend if you do not have an API key."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._prompts = self._load_role_prompts()

    def invoke(self, role, context, config=None) -> AgentOutput:
        system = self._prompts[role]
        user = self._serialize_context(context)
        schema = self._output_schema_for(role)

        response = self._client.messages.create(
            model=self._model,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=config.max_tokens if config else 4096,
            tools=[self._schema_to_tool(schema)],
            tool_choice={"type": "tool", "name": "submit_output"},
        )

        return self._parse_output(response, role)
```

#### Type B:Long-Running Backend(Claude Code)

Claude Code は対話的・反復的・長時間タスクが可能です。これを活かす:

- `/sketch` の多段対話を Claude Code セッション内で処理
- `/critique` で批評者と作曲者の対話を実装
- 単発 API では困難な「修正提案 → 再評価 → 微修正」を Claude Code に任せる

`ClaudeCodeBackend` は Claude Code SDK 経由で `.claude/agents/<role>.md` を呼び出すアダプタとして設計します。

### 6.3 ベンチマーク要件

LLM 統合の効果を測定するため、新しいテストカテゴリを設置:

```
tests/llm_quality/
├── test_motif_quality.py        # PythonOnly vs LLM での motif 品質比較
├── test_critique_depth.py       # 批評の具体性と深さ
└── test_arrangement_naturalness.py
```

これらは optional dependency `yao[llm-eval]` でのみ実行され、CI ではスキップ(コスト・決定論性のため)。

### 6.4 完了条件

- `AnthropicAPIBackend.is_stub == False`
- API キー未設定時は明示的にエラー(silent fallback しない)
- Subjective rating で「LLM 有効時の overall ≥ PythonOnly 時 + 1.0」を達成

---

## 7. Wave 1.3:Spec Compiler の LLM 化

### 7.1 現状の致命的限界

```python
# src/yao/sketch/compiler.py
_MOOD_TO_KEY = {
    "happy": "C major", "sad": "D minor", ...
    # 24 キーワードのみ。日本語ゼロ。
}
```

「雨の夜のカフェで聴きたい少し切ない 90 秒のピアノ曲」というユーザ意図を、ほぼ全て捨てて `D minor / piano / 4 sections` に丸める。これは YaO のエントリポイントとして致命的に貧弱です。

### 7.2 v3.0 設計:三段階フォールバック

```python
class SpecCompiler:
    def compile(self, description: str, *, language: str = "auto") -> CompiledSpec:
        if self._llm_backend.is_stub:
            return self._compile_keyword(description, language)
        try:
            return self._compile_llm(description, language)
        except BackendError as e:
            logger.warning("llm_compile_failed", error=str(e))
            return self._compile_keyword(description, language)
```

#### Stage 1: LLM コンパイル(優先)

LLM に対して、**構造化出力**で以下を要求:
- `intent.md` の本文(1〜3 文)
- `composition.yaml` の必須フィールド
- `trajectory.yaml` の waypoints
- ジャンル候補(複数)と推薦理由
- 不明点(明示的に質問)

LLM 出力は schema validation を通って初めて採用。失敗時は keyword fallback。

#### Stage 2: Keyword Compile(現状維持 + 強化)

現状の辞書ベースを保持。ただし以下を強化:
- 日本語感情語彙を 50+ 追加
- ジャンル名から楽器セットを引くテーブルをジャンル Skill から自動構築
- 「短い」「長い」「ループ可能」等の修飾語を解釈

#### Stage 3: Default Fallback

Stage 1, 2 で何も抽出できない場合、`specs/templates/minimal.yaml` をベースに `intent.md` だけ自然言語で残す。

### 7.3 多言語対応

日本語感情語彙を構造化:

```yaml
# .claude/skills/psychology/emotion-mapping.md より抽出
emotions:
  ja:
    悲しい: { valence: -0.6, arousal: -0.3, suggestions: [minor, slow] }
    切ない: { valence: -0.4, arousal: 0.0, suggestions: [minor, moderate] }
    爽やか: { valence: 0.5, arousal: 0.4, suggestions: [major, lydian] }
    瑞々しい: { valence: 0.4, arousal: 0.3, suggestions: [major, pentatonic] }
    儚い: { valence: -0.2, arousal: -0.4, suggestions: [phrygian, slow] }
    勇壮: { valence: 0.7, arousal: 0.8, suggestions: [major, fast] }
```

valence × arousal 平面でクラスタリングして、key/tempo/mode を導出します。

### 7.4 完了条件

- 日本語入力で「切ない 90 秒のピアノ曲」が正しく `D minor`, `piano solo`, `tempo ~75` に変換される
- LLM 利用時、20 ターゲット記述で**人間 reviewer の合意率 ≥ 80%**(要 subjective test)

---

## 8. Wave 1.4:V2 Pipeline の本実装

### 8.1 監査で発見した茶番

```python
# src/yao/generators/note/rule_based.py
class RuleBasedNoteRealizer(NoteRealizerBase):
    def realize(self, plan: MusicalPlan, ...) -> ScoreIR:
        v1_spec = original_spec or _plan_to_v1_spec(plan)  # plan を捨てる!
        gen = RuleBasedGenerator()                          # v1 を呼ぶ
        return gen.generate(v1_spec, ...)
```

7 ステップパイプラインの中核は MusicalPlan ですが、Note Realizer は**それを使わず**、v1 spec に逆変換して旧 Generator に丸投げしています。これでは MPIR の存在意義が崩壊します。

### 8.2 v3.0 での真の Note Realizer

新しい `NoteRealizerV2` を実装します。MusicalPlan の**全フィールドを直接消費**します。

```python
@register_note_realizer("rule_based_v2")
class RuleBasedNoteRealizerV2(NoteRealizerBase):
    consumed_plan_fields = (
        "form.sections.target_tension",
        "form.sections.target_density",
        "harmony.chord_events.roman",
        "harmony.chord_events.tension_level",
        "harmony.chord_events.cadence_role",
        "motif.seeds",
        "motif.placements",
        "phrase.phrases",
        "arrangement.assignments",
        "global_context.key",
        "global_context.tempo_bpm",
        "trajectory.predictability",
    )

    def realize(self, plan, seed, temperature, provenance, original_spec=None):
        # 1. ChordEvent から各拍の harmonic context を作成
        chord_grid = self._build_chord_grid(plan.harmony, plan.form)

        # 2. MotifPlacement に従って motif を section に配置
        motif_grid = self._place_motifs(plan.motif, plan.form)

        # 3. Phrase から旋律輪郭を取得
        contour_grid = self._build_contour_grid(plan.phrase)

        # 4. ArrangementPlan から各楽器の役割を取得
        for instr_name, role in self._iter_assignments(plan.arrangement):
            for section in plan.form.sections:
                notes = self._realize_section(
                    instr_name=instr_name,
                    role=role,
                    section=section,
                    chord_grid=chord_grid,
                    motif_grid=motif_grid,
                    contour_grid=contour_grid,
                    tension=section.target_tension,
                    density=section.target_density,
                    seed=seed,
                    temperature=temperature,
                )

        return self._assemble_score(plan, all_notes, provenance)
```

### 8.3 マイグレーション戦略

旧実装を即座に削除しません。**段階的移行**:

| フェーズ | 期間 | 旧 Realizer | 新 Realizer V2 |
|---|---|---|---|
| **Coexist** | 4 週 | デフォルト、`@deprecated` | opt-in via `realizer: rule_based_v2` |
| **Switch** | 4 週 | opt-in | デフォルト |
| **Remove** | - | 削除 | 唯一 |

各フェーズでゴールデンテスト(`tests/golden/`)を更新し、旧→新の品質変化を可視化。

### 8.4 完了条件

- 新 Realizer の `consumed_plan_fields` が 80% 以上アクセスされる(AST scan で検証)
- ゴールデンテストで「ChordEvent.tension_level の変化が velocity に反映される」「MotifPlacement に従った同一モチーフが楽曲内で反復される」を確認
- `legacy_adapter.py` が削除可能になる

---

## 9. Wave 2.1:ジャンル Skill の生成パイプライン統合

### 9.1 現状の機会損失

監査で `grep -r "skills/genres" src/` を実行 → **何も見つからず**。22 個のジャンル Skill ファイルは Claude Code セッション内でのみ参照される設計で、`yao compose` 実行時の生成挙動には**一切影響しません**。

これは MOST IMPORTANT な機会損失です。「ミュージシャンが Markdown を編集するだけで生成挙動を変えられる」という YaO の独自価値が、現状では実現していません。

### 9.2 v3.0 設計:Skill Loader と Skill-Driven Generation

#### 9.2.1 Skill ファイル形式の標準化

各ジャンル Skill に YAML フロントマターを必須化:

```markdown
---
genre_id: cinematic
display_name: "Cinematic / Film Score"
extends: [orchestral_base]
typical_keys: [D minor, A minor, E minor, G minor]
typical_tempo_range: [60, 120]
typical_time_signatures: ["4/4", "3/4", "6/8"]
typical_instruments:
  - { name: strings_ensemble, role: pad, weight: 1.0 }
  - { name: french_horn, role: harmony, weight: 0.7 }
  - { name: piano, role: melody, weight: 0.6 }
  - { name: cello, role: bass, weight: 0.8 }
chord_palette: [i, iv, V7, VI, III, ii°, bII]
typical_progressions:
  - [i, VI, III, VII]
  - [i, iv, V7, i]
  - [i, bVI, bIII, bVII]
cadence_preferences:
  authentic: 0.6
  half: 0.2
  plagal: 0.15
  deceptive: 0.05
forbidden_cliches:
  - { id: "pachelbel_canon", description: "I-V-vi-iii-IV-I-IV-V" }
  - { id: "axis_progression", description: "I-V-vi-IV repeated" }
trajectory_defaults:
  tension:
    waypoints: [[0, 0.3], [0.4, 0.5], [0.7, 0.95], [1.0, 0.4]]
  predictability: { target: 0.6, variance: 0.15 }
microtiming_profile: legato_classical
articulation_defaults: { strings: legato, piano: pedaled }
references_recommended: ["public_domain/holst_jupiter"]
---

# Cinematic / Film Score Skill

(本文は人間向けの詳細な説明。現状の Skill ファイルそのまま)
```

#### 9.2.2 Skill Loader の実装

```python
# src/yao/skills/loader.py (NEW)

@dataclass(frozen=True)
class GenreProfile:
    genre_id: str
    typical_keys: tuple[str, ...]
    typical_instruments: tuple[InstrumentRecommendation, ...]
    chord_palette: tuple[str, ...]
    typical_progressions: tuple[tuple[str, ...], ...]
    cadence_preferences: dict[str, float]
    forbidden_cliches: tuple[ClicheDefinition, ...]
    trajectory_defaults: TrajectoryDefaults
    # ...

class SkillRegistry:
    def __init__(self, skills_dir: Path):
        self._genres: dict[str, GenreProfile] = {}
        self._load_all(skills_dir)

    def get_genre(self, genre_id: str) -> GenreProfile | None: ...
    def list_genres(self) -> list[str]: ...
    def reload(self) -> None: ...  # for hot-reloading during dev
```

#### 9.2.3 生成パイプラインへの統合

5 つの統合ポイントを設置:

| ポイント | Skill から取得する内容 | 統合先 |
|---|---|---|
| **SpecCompiler** | typical_instruments, typical_keys, typical_tempo_range | NL → spec 推論 |
| **HarmonyPlanner** | chord_palette, typical_progressions, cadence_preferences | コード進行候補 |
| **DrumPatterner** | typical drum patterns from `drum_patterns/<genre>.yaml` | リズム生成 |
| **Critique: cliche_detector** | forbidden_cliches | クリシェ検出 |
| **PerformanceLayer** | microtiming_profile, articulation_defaults | 演奏表現 |

### 9.3 ホットリロード機能

開発・利用中の体験向上のため:

```bash
# ジャンル Skill を編集 → 即座に生成挙動に反映
$ yao watch --skill-reload
> Editing .claude/skills/genres/cinematic.md ...
[Skill reloaded: cinematic]
```

### 9.4 完了条件

- 全 22 ジャンル Skill にフロントマターを追加
- `tests/integration/test_skill_grounding.py`:Skill を変更すると生成出力が変化することを確認
- Skill 編集だけで「映画音楽用」「lo-fi 用」の出力差が劇的に出ることを subjective rating で確認

---

## 10. Wave 2.2:美的評価指標の追加

### 10.1 現状の評価器の限界

現状の `evaluate_score()` の指標一覧:`pitch_range_utilization`, `stepwise_motion_ratio`, `consonance_ratio`, `pitch_class_variety`, `section_contrast`, ... 。

これらは**形式評価**には有効ですが、「**形式的に正しいが感情的に死んでいる音楽**」を検出できません。例:`pitch_class_variety = 0.95` でも、ハッとする瞬間が一つもない無味な音楽は普通に出てきます。

### 10.2 v3.0 で追加する 4 つの美的指標

#### 10.2.1 Surprise Index(意外性指標)

理論的根拠:Huron の予測モデル(ITPRA 理論)。各音符・各和音について、直前のコンテキストから期待される確率分布を Markov モデルで計算し、実際の選択の負対数尤度を「驚き」とする。

```python
def compute_surprise_index(score: ScoreIR, plan: MusicalPlan) -> float:
    """Returns mean -log P(note | context) across all notes."""
    bigram_model = load_bigram_model(plan.global_context.key)
    surprises = []
    for note, prev_note in pairs(score.melody_notes()):
        prob = bigram_model.transition_prob(prev_note, note)
        surprises.append(-math.log(max(prob, 1e-9)))
    return statistics.mean(surprises)
```

目標値:`predictability` 軌跡の (1 - target) と一致。低すぎ=退屈、高すぎ=混沌。

#### 10.2.2 Memorability Index(記憶可能性指標)

```python
def compute_memorability_index(plan: MusicalPlan) -> float:
    if not plan.motif or not plan.motif.seeds:
        return 0.0  # Composer が空ならスコアも 0
    score = 0.0
    for seed in plan.motif.seeds:
        recurrence = plan.motif.recurrence_count(seed.id)
        identity = seed.identity_strength
        score += min(recurrence / 4.0, 1.0) * identity
    return score / len(plan.motif.seeds)
```

#### 10.2.3 Contrast Index(対比指標)

隣接セクション間の StyleVector 距離。

```python
def compute_contrast_index(score: ScoreIR) -> float:
    distances = []
    for s1, s2 in pairs(score.sections):
        v1 = extract_section_style_vector(s1)
        v2 = extract_section_style_vector(s2)
        distances.append(v1.distance_to(v2))
    return statistics.mean(distances)
```

目標値:0.3 〜 0.6(過小=単調、過大=分裂)。

#### 10.2.4 Pacing Index(ペーシング指標)

tension trajectory の累積エントロピー。クライマックスが意図通りの位置にあるか、変化のテンポが適切か。

### 10.3 評価器への統合

```python
@dataclass(frozen=True)
class EvaluationScore:
    dimension: Literal[
        "structure", "melody", "harmony", "arrangement", "acoustics",
        "aesthetic"  # NEW
    ]
    metric: str
    score: float
    target: float
    tolerance: float
    detail: str
```

新しい `aesthetic` ディメンションに 4 つの指標を配置。重み付けは:`structure 0.20, melody 0.25, harmony 0.20, aesthetic 0.20, arrangement 0.10, acoustics 0.05`。

### 10.4 完了条件

- `tests/integration/test_aesthetic_metrics.py`: 既知の良楽曲 5 つで aesthetic ≥ 0.7、退屈な楽曲 5 つで aesthetic ≤ 0.4
- Conductor の feedback ループが aesthetic 失敗時に適切な adaptation(motif 増加・対比強化)を選ぶ

---

## 11. Wave 2.3:Audio Loop の Conductor 統合

### 11.1 現状

`PerceptualReport`(LUFS、spectral centroid、masking risk 等)は実装済みだが、`Conductor.compose_from_spec()` は MIDI 評価で完結。**audio render → audio 評価 → adaptation のループは存在しない**。これは「Listener Panel」のメタファーが半分しか実現していないことを意味します。

### 11.2 v3.0 設計

```python
@dataclass(frozen=True)
class ConductorConfig:
    enable_audio_loop: bool = False  # opt-in (CI で skip 可能)
    soundfont_path: Path | None = None
    audio_thresholds: AudioThresholds = field(default_factory=AudioThresholds)
```

audio loop 有効時の追加ステップ:

```
[Standard MIDI loop] → MIDI 合格
  ↓
[Audio Render] (FluidSynth)
  ↓
[Perceptual Analysis] (PerceptualReport)
  ↓
[Audio Evaluation]
  ├── LUFS target match (use case 別)
  ├── Frequency masking risk
  ├── Spectral balance
  └── Tempo stability
  ↓
[Audio Adaptations]
  ├── Masking → Orchestrator が register 調整
  ├── LUFS too quiet/loud → Mix Engineer が dynamics 調整
  └── Spectral imbalance → Mix Engineer が EQ 調整
  ↓
[Re-render & Re-evaluate] (max 2 iterations)
```

### 11.3 SoundFont 同梱戦略

audio loop には SoundFont が必須だが、サイズが大きい(140MB)。

- CI 用に**小型 SoundFont**(8MB、ピアノ・弦・ドラムのみ)を `soundfonts/yao_minimal.sf2` として同梱
- フル品質は別途ダウンロード(`make setup-soundfonts`)
- `enable_audio_loop=True` で SoundFont 不在時は `AudioBackendUnavailableError`

### 11.4 完了条件

- `yao conduct --enable-audio-loop` が動作
- audio adaptation が少なくとも 3 種類実装される(register, dynamics, EQ)
- minimum SoundFont で CI 統合テストが動作

---

## 12. Wave 3:深化フェーズ

Wave 3 は Wave 1, 2 が固まった後に着手します。各機能はそれぞれ独立した PR で進められます。

### 12.1 Performance Expression のパイプライン標準化

現状、`MicrotimingInjector`、`ArticulationRealizer`、`DynamicsCurveRenderer`、`CCCurveGenerator` は実装されているが**生成パイプラインで使われていない**。

統合方針:Note Realizer 後に **Performance Pipeline** を必ず実行する。ジャンルとアーティキュレーション Skill から profile を選択。

### 12.2 EnsembleConstraint の導入

各楽器パートが独立に生成されるのではなく、**部間の相互作用**を制約として記述:

```yaml
ensemble_constraints:
  - rule: melody_bass_consonance_on_downbeat
    severity: prefer
    detail: "On beat 1 of each bar, melody and bass form a consonant interval"

  - rule: chord_melody_compatibility
    severity: must
    detail: "Melody non-chord tones must be passing or neighbor tones"

  - rule: register_separation
    severity: must
    detail: "Melody and bass parts must not occupy the same octave for >2 bars"
```

これらは Orchestrator Subagent で考慮され、違反時は Critic が検出。

### 12.3 参照楽曲ライブラリの整備

- パブリックドメイン楽曲(Bach 4-part chorales、Mozart sonatas、Joplin rags 等)を `references/midi/public_domain/` に配置
- 各楽曲について `catalog.yaml` で license=PD を明記
- 抽象化された **GenreProfile**(具体楽曲の StyleVector を集約した結果のみ、再構成不可能)を `references/profiles/<genre>.yaml` で配布
- 著作権配慮:具体的な melody/chord progression は**抽出しない**

### 12.4 StyleVector の表現力強化

現状の StyleVector は melody/harmony 情報がゼロで貧弱。著作権リスクなしに表現力を上げる:

```python
@dataclass(frozen=True)
class StyleVector:
    # 既存フィールド
    harmonic_rhythm: float
    voice_leading_smoothness: float
    rhythmic_density_per_bar: tuple[float, ...]
    register_distribution: tuple[float, ...]
    timbre_centroid_curve: tuple[float, ...]
    motif_density: float

    # NEW(著作権セーフ:histogram 系のみ、復元不可能)
    interval_class_histogram: tuple[float, ...]  # 12 dims, 音程クラス頻度
    chord_quality_histogram: tuple[float, ...]   # 8 dims, M/m/dim/maj7 等の頻度
    cadence_type_distribution: tuple[float, ...] # 4 dims, 終止型分布
    rhythm_complexity_per_section: tuple[float, ...]  # シンコペート率等
```

`FORBIDDEN_FEATURES` には引き続き「具体的な melody contour」「具体的な chord sequence」を残す。

### 12.5 Subjective Rating の本格運用

現状、`tests/subjective/ratings/` には開発者の自己評価 1 件のみ。これを実用化:

```bash
# ユーザは生成された曲に対して対話的に評価
$ yao rate outputs/projects/my-song/iterations/v003
> Memorability: 1-10? [_]
> Emotional fit to intent: 1-10? [_]
> Technical quality: 1-10? [_]
> Genre fitness: 1-10? [_]
> Overall: 1-10? [_]
> Free-text notes: [_]

[Saved to ratings/my-song-v003-2026-05-15.json]
```

蓄積された rating は `Layer 7: Reflection & Learning` の `style_profile.py` に流れ込み、ユーザ嗜好プロファイルを更新します。次回の生成では、ユーザが好む傾向(密度、対比、複雑度)を `trajectory_defaults` に反映。

### 12.6 `/sketch` 多段対話化

`.claude/commands/sketch.md` を以下のフェーズで定義:

1. **Turn 1**: 核となる感情・目的・聴取コンテキストを聞く
2. **Turn 2**: 参照楽曲(知っているなら)・避けたい雰囲気を聞く
3. **Turn 3**: 楽器・尺・繰り返し性を確認
4. **Turn 4**: trajectory(緊張度カーブ)の素描を提示し、調整を求める
5. **Turn 5**: `intent.md` と `composition.yaml` の最終確認
6. **Turn 6**: `/compose` 起動

各ターンで Claude Code は提案を出し、ユーザは承認/修正。これにより Phase 1(Intent Crystallization)が真に実行されます。

---

## 13. CI とドキュメント整合性

### 13.1 v3.0 で必須化される CI チェック

```yaml
# .github/workflows/quality.yml
- name: Status Honesty Check
  run: make honesty-check
  # ✅ 機能の各 source/test ファイルが本当に存在し、実装が空でないことを確認

- name: Backend Honesty Check
  run: |
    python -c "from yao.agents.anthropic_api_backend import AnthropicAPIBackend; \
               assert not AnthropicAPIBackend().is_stub or 'stub' in AnthropicAPIBackend.__name__.lower()"

- name: Plan Completeness Check
  run: pytest tests/integration/test_plan_completeness.py
  # MotifPlan が空でないことを確認

- name: Skill Grounding Check
  run: pytest tests/integration/test_skill_grounding.py
  # ジャンル Skill 編集が生成挙動を変えることを確認

- name: Critic Coverage Check
  run: pytest tests/integration/test_critic_meaningful.py
  # 各 Severity で意味のある検出が起こることを確認

- name: V2 Pipeline Consumption Check
  run: python tools/check_plan_consumption.py
  # Note Realizer が MusicalPlan の 80% 以上のフィールドを消費することを確認
```

### 13.2 ドキュメント整合性ツール

```
tools/
├── honesty_check.py          # NEW: ✅ ステータスと実装の整合性
├── doc_drift_check.py        # NEW: README/PROJECT/FEATURE_STATUS 数値整合
├── plan_consumption_check.py # NEW: V2 pipeline 利用率
└── skill_grounding_check.py  # NEW: Skill が実際に使われているか
```

### 13.3 ステータス再採点ポリシー

v3.0 開始時に FEATURE_STATUS.md を**全項目再採点**します。判定基準:

| 現ステータス | 実装審査結果 | 新ステータス |
|---|---|---|
| ✅ | スタブ・空実装 | 🟡 with `limitation: stub implementation` |
| ✅ | テストはあるが実機能不在 | 🟡 with `limitation: no real-world impact` |
| ✅ | パイプライン未統合 | 🟡 with `limitation: not integrated into generation` |
| ✅ | 真に動作 | ✅ 維持 |

審査結果は `docs/audit/2026-05-status-reaudit.md` として永続化。

---

## 14. 開発プロセスの規律

### 14.1 Sound-First 文化の強化

v2.0 から導入されているが、v3.0 で**強制化**:

- 生成・レンダリングに影響する PR は、**before/after の audio sample**(30 秒以上)を PR 説明に添付必須
- audio sample なしの該当 PR はマージ不可
- `make pr-audio-samples PROJECT=<name>` ヘルパで簡単に作れるようにする

### 14.2 Dogfooding の強化

YaO で制作した楽曲を:
- プロジェクトのデモ動画 BGM
- リリースノートの「今月の音」
- PR レビュー時の「主観評価サンプル」
として継続的に使用。

### 14.3 ミュージシャン貢献ガイド

Python 不要な貢献経路を**明示的に支援**:

| 貢献領域 | 必要スキル | ファイル |
|---|---|---|
| ジャンル Skill 追加 | 音楽知識 + Markdown | `.claude/skills/genres/<name>.md` |
| テンプレート作成 | YAML + 音楽知識 | `specs/templates/<name>.yaml` |
| 参照楽曲分析 | MIDI + YAML | `references/profiles/<genre>.yaml` |
| Subjective rating | 楽曲を聴く | `tests/subjective/ratings/<id>.json` |
| 翻訳 | 言語スキル | `.claude/skills/psychology/emotion-mapping.md` の i18n |

`docs/contributing-as-musician.md` を充実させます。

### 14.4 Documentation Budget(継承+強化)

v2.0 の「設計文書 1 行あたり実働コード 3 行以上」を継承。違反警告を `tools/doc_drift_check.py` で出します。

### 14.5 Vertical Alignment(原則 6)の運用

v3.0 では各 PR について以下を自己宣言:

```markdown
## Vertical Alignment Self-Check

- [ ] Input layer: this PR enriches what users can express (or N/A)
- [ ] Processing layer: this PR uses richer input or makes better decisions (or N/A)
- [ ] Output layer: this PR enables more precise evaluation/critique (or N/A)

If only one box is checked: justify why imbalance is acceptable.
```

---

## 15. ロードマップ:Wave とマイルストーン

### 15.1 Wave 1:正直化(2026 Q3、4〜6 週間) ✅ 完了 2026-05-03

**目標**: 「✅ なのに動いていない」状態の解消

| 週 | マイルストーン | 完了基準 | 状態 |
|---|---|---|---|
| W1 | FEATURE_STATUS.md の再採点 | スタブ ✅ がゼロ | ✅ |
| W1 | 5 CI honesty ツール実装 | make all-checks pass | ✅ |
| W2-3 | Composer Subagent 本実装 | MotifPlan が常に非空 | ✅ |
| W3-4 | AnthropicAPIBackend 本実装 | API キー有り時に実 LLM 呼出 | ✅ |
| W4-5 | SpecCompiler LLM 化 | 日本語 50 語彙、三段階フォールバック | ✅ |
| W5-6 | V2 Pipeline 本実装 | plan-consumption 100% | ✅ |
| W6 | Wave 1 統合テスト | 全ツール exit 0、1074 tests pass | ✅ |

### 15.2 Wave 2:整合化(2026 Q4、8〜10 週間) ✅ 完了 2026-05-03

**目標**: アーキテクチャの名実一致

| 週 | マイルストーン | 完了基準 | 状態 |
|---|---|---|---|
| W7-9 | NoteRealizerV2 デフォルト化 | 100% フィールド消費 | ✅ |
| W9-11 | ジャンル Skill loader | 基盤実装、8/22 grounded | ✅ (partial) |
| W11-13 | 美的評価指標 4 つ追加 | aesthetic dimension + 1.7x separation | ✅ |
| W13-15 | Audio Loop 基盤 | MixChain + audio features 動作 | ✅ (partial) |
| W15-16 | Wave 2 統合テスト | 1104 tests pass、全ツール exit 0 | ✅ |

### 15.3 Wave 3:深化(2027 Q1-Q2、8〜12 週間)

**目標**: 多様性・体験・文化的拡張

主な作業項目:
- Performance Layer の自動適用
- Ensemble Constraint
- 参照ライブラリ整備
- StyleVector 拡張
- Subjective rating CLI
- `/sketch` 多段対話
- Microtonal/Polyrhythm の拡充
- Live Improvisation の実装移行
- Arrangement Engine の品質向上

### 15.4 Continuous(常時並行)

- Subjective rating の蓄積
- ジャンル Skill の追加(目標: 22 → 50)
- 参照楽曲の追加
- ミュージシャンコミュニティ形成
- ドキュメント国際化(英・日・中・西)

---

## 16. 成功の判定:v3.0 の完了条件

v3.0 は次の条件**全て**を満たすときに完了とみなされます。

### 16.1 Honesty(正直さ)
- FEATURE_STATUS.md の全 ✅ エントリが、`tools/honesty_check.py` をパス
- スタブと実装の混同が一切ない
- LLM バックエンドが本実装(stub フォールバックのみ存在)

### 16.2 Integration(統合)
- Note Realizer V2 が MusicalPlan の主要フィールド 80% 以上を消費
- ジャンル Skill 編集で生成出力が変化することがテストで確認される
- Audio loop が opt-in で動作する

### 16.3 Aesthetic(美的)
- 4 つの美的指標(surprise/memorability/contrast/pacing)が評価器に統合
- ベンチマーク用 10 楽曲(良 5 + 退屈 5)で指標が期待通りに分かれる
- subjective rating で overall ≥ 7.0(50 件以上の評価で)

### 16.4 Vertical Alignment(垂直整合)
- 各 Wave で input/processing/output の 3 層が同時に進化したことを宣言
- doc/code 比が 3:1 を超えていない
- 過去半年の PR の 80% 以上が Vertical Alignment セルフチェックを完了

### 16.5 Cultural Sensitivity(文化的感受性)
- 非西洋ジャンル Skill(maqam, hindustani, gamelan 等)に文化的コンテキストが明記
- microtonal scale 対応がドキュメントと実装で一致

---

## 17. リスクとミティゲーション

### 17.1 「もうテストは通っているから良いのでは?」リスク

**リスク**: 監査結果を読んだ貢献者が、「自分のセクションも 🟡 → ✅ に格上げしたい」と短絡し、不十分な実装でステータス上げを試みる。

**ミティゲーション**:
- `make honesty-check` で機械的にチェック
- ステータス変更は専用 PR とし、レビュー必須
- 過去のスタブ昇格事例を `docs/audit/honesty-violations.md` に記録(教訓化)

### 17.2 LLM 統合のコスト膨張

**リスク**: Anthropic API 統合により開発コスト・CI コストが膨れ上がる

**ミティゲーション**:
- LLM テストは optional、CI ではスキップ
- `yao[llm-eval]` extra で明示
- subjective rating で「LLM ありが本当に PythonOnly より良い」を証明できなければ、デフォルトを LLM にしない

### 17.3 設計書と実装の再乖離

**リスク**: v3.0 完了後、また同じ乖離が起きる

**ミティゲーション**:
- 原則 7「Status Honesty」を CI で常時強制
- 月次の audit run(`make audit-monthly`)
- 新規 PR で ✅ を宣言する場合、`tools/honesty_check.py` を必ず通すフック

### 17.4 「機能を増やしたい」誘惑

**リスク**: 開発者は新機能の方が楽しい。既存機能の埋め合わせは地味で動機が湧きにくい。

**ミティゲーション**:
- v3.0 期間中は **新機能追加禁止**(Wave 3 までは)
- ロードマップで「面白い新機能(microtonal expansion 等)は Wave 3 末以降」と明示
- 完了時の達成感を共有(リリースノート、デモ動画)

---

## 18. 用語集(v2.0 から継承+追加)

v2.0 の用語集を継承。追加用語:

**Honesty Check** — `tools/honesty_check.py` による、ステータスと実装の整合性検証。

**Skill Grounding** — ジャンル Skill が生成パイプラインに統合され、Skill 編集が生成挙動を変える性質。

**Plan Consumption Rate** — Note Realizer が MusicalPlan のどれだけのフィールドを実際に読むかの比率。

**Stub Backend** — 形式的に Backend Protocol を満たすが、実際の処理を別バックエンドに丸投げするもの。`is_stub=True` で識別。

**Audit** — 実装監査。コードを読み、ドキュメントの主張と実装の乖離を測定する作業。

**Wave** — v3.0 の開発フェーズ単位。Wave 1〜3 を順序立てて実行。

**Aesthetic Dimension** — 評価器の新ディメンション。surprise/memorability/contrast/pacing の 4 指標。

**Listener Panel** — 試聴会のメタファー。Perception Layer + Subjective Rating の総体。

---

## 19. 結語:v3.0 が約束するもの

v1.0 は YaO の魂(メタファーと哲学)を確立しました。
v2.0 は YaO の骨格(8 層アーキテクチャと MPIR)を設計しました。
v3.0 は YaO の**筋肉**を作ります。

設計が立派でも、コードがスタブなら音は鳴りません。骨格が美しくても、筋肉がなければ動きません。

v3.0 は派手な新機能の追加を**意図的に拒否**します。代わりに、既に「できる」と書かれている機能を、本当に**できるようにする**ことに集中します。これは地味で、目立ちません。しかし、これがなければ YaO は永遠に「論文プロジェクト」のままです。

v3.0 完了時、YaO は次のことができるようになります:

- ユーザが日本語で「梅雨明けの朝の喜び」と書けば、それが正しく `intent.md` になり、ジャンル Skill が**本当に**生成挙動を導き、Composer Subagent が**本当に**モチーフを生成し、Adversarial Critic が**本当に**弱点を検出し、Audio Loop で LUFS が**本当に**揃う。
- ユーザが「これ、最後のサビの密度をもう少し下げたい」と言えば、Section regeneration が**本当に**必要箇所だけ書き換える。
- 開発者が `.claude/skills/genres/lofi.md` を編集すれば、次の生成で**本当に** lofi らしさが変わる。
- ユーザの主観評価が**本当に**蓄積され、次回の生成傾向に反映される。

これらは v2.0 で「できる」と書かれていたが、実際には**できなかった**ことです。v3.0 はそれを**本当にできるようにします**。

> *Build the orchestra well, so the conductor can lead it freely.*
> *— and this time, build it for real.*

---

**Project: You and Orchestra (YaO)**
*PROJECT.md version: 3.0 (Closing-the-Gap Edition)*
*Last updated: 2026-05-02*
*Audit reference: docs/audit/2026-05-status-reaudit.md (to be created)*
*Supersedes: PROJECT.md v2.0 (2026-04-29)*
