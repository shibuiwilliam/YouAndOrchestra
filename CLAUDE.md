# CLAUDE.md — YaO Core Rules (v3.0)

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > VISION.md > other docs.*
> *This is **v3.0 (Closing-the-Gap Edition)**, aligned with PROJECT.md v3.0.*
> *Until Wave 3 begins, **closing gaps takes priority over adding features**.*

---

## 0. v3.0 で何が変わったか

v3.0 は新機能を増やしません。**実装監査で発見した「✅ なのに動かない」状態の解消**に集中します。

このドキュメントを読んでいるあなた(Claude Code)は、v2.0 までのドキュメントが**現実より楽観的に書かれていた**事実を前提として開発します。具体的には:

- `MotifPlan(seeds=[], placements=[])` — Composer Subagent は空の計画を返している
- `AnthropicAPIBackend` は PythonOnly に丸投げするスタブ
- NoteRealizer は MusicalPlan を **v1 spec に逆変換** して旧 generator を呼んでいる
- 22 個のジャンル Skill は生成パイプラインから **1 度も参照されていない**
- StyleVector に melody/harmony 情報がない

**あなたの最重要任務は、これらのギャップを誠実に埋めること**です。新機能を提案したくなる衝動を抑え、まず既存の約束を実装してください。

---

## 1. Quick Reference

```bash
# 開発の基本
make test              # 全テスト
make test-unit         # 単体テストのみ
make test-golden       # ゴールデン MIDI 回帰テスト
make test-subjective   # 主観品質テスト
make lint              # ruff + mypy strict
make arch-lint         # 8 層境界チェック
make format            # 自動整形

# v3.0 で必須化される正直性チェック群
make honesty-check     # ★v3.0: ✅ 機能の実装が空でないかを検証
make plan-consumption  # ★v3.0: NoteRealizer が MusicalPlan を消費しているか
make skill-grounding   # ★v3.0: Skill 編集が生成挙動を変えるか
make critic-coverage   # ★v3.0: 各 Severity で意味のある検出が起こるか
make backend-honesty   # ★v3.0: Stub バックエンドが is_stub=True を返すか

# 既存
make feature-status    # FEATURE_STATUS.md と実コードの整合性
make sync-skills       # ジャンル Skill の YAML フロントマター同期
make sync-docs         # PROJECT/VISION/FEATURE_STATUS の数値整合
make audit-monthly     # ★v3.0: 月次の実装監査ダンプ

# まとめ
make all-checks        # lint + arch-lint + honesty-check + plan-consumption +
                       # skill-grounding + critic-coverage + backend-honesty +
                       # feature-status + sync-docs + test + golden
```

**Key directories:**

```
src/yao/constants/    → スケール、音域、MIDI、cents 値
src/yao/schema/       → Pydantic v1 + v2 + v3(★v3.0 で v3 spec を追加)
src/yao/ir/           → Score IR (Layer 3)
src/yao/ir/plan/      → Musical Plan IR / MPIR (Layer 3.5)
src/yao/ir/expression.py → Performance Expression IR (Layer 4.5)
src/yao/generators/   → Plan + Note Realizers + Performance Realizers
src/yao/perception/   → Audio features, use-case eval, reference matcher (Layer 4)
src/yao/render/       → MIDI / audio / MusicXML / LilyPond / DAW (Layer 5)
src/yao/mix/          → EQ / compression / reverb / mastering
src/yao/arrange/      → Arrangement Engine
src/yao/verify/       → Lint, evaluation, critique, diff, constraints (Layer 6)
src/yao/reflect/      → Provenance, style profile, annotation (Layer 7)
src/yao/subagents/    → Python Subagent 実装(★Wave 1.1 で本実装)
src/yao/agents/       → Backend-agnostic agent protocol(★Wave 1.2 で本実装)
src/yao/runtime/      → ProjectRuntime
src/yao/improvise/    → Live improvisation
src/yao/sketch/       → NL → spec compiler(★Wave 1.3 で LLM 化)
src/yao/skills/       → ★v3.0 NEW: Genre/Theory/Instrument Skill loader
src/yao/conductor/    → Multi-candidate orchestration + critic-gate
src/yao/errors.py     → 全カスタム例外
```

**Key types:**

```
Note              → src/yao/ir/note.py
ScoreIR           → src/yao/ir/score_ir.py
MusicalPlan       → src/yao/ir/plan/musical_plan.py    (Layer 3.5)
MotifPlan         → src/yao/ir/plan/motif.py            ★Wave 1.1: 空にしない
NoteExpression    → src/yao/ir/expression.py           (Layer 4.5)
CompositionSpec   → src/yao/schema/composition.py
ProvenanceLog     → src/yao/reflect/provenance.py
Finding           → src/yao/verify/critique/types.py
SubagentBase      → src/yao/subagents/base.py
GeneratorBase     → src/yao/generators/base.py
NoteRealizerBase  → src/yao/generators/note/base.py
GenreProfile      → src/yao/skills/loader.py            ★v3.0 NEW
StyleVector       → src/yao/perception/style_vector.py
PerceptualReport  → src/yao/perception/audio_features.py
AgentBackend      → src/yao/agents/protocol.py          ★Wave 1.2: スタブ表示徹底
```

---

## 2. Your Role(v3.0 で更新)

あなたは **YaO の共同開発者** であり、YaO そのものではありません。

ただし、v3.0 ではこの役割に **追加責任** があります。

### あなたが扱うべき態度

1. **監査人(Auditor)としての視点**: コードを読み、ドキュメントの主張と実装の現実が一致しているかを検証する。乖離を見つけたら報告し、修正する。
2. **実装者(Implementer)としての規律**: 新機能を提案したくなったら、まず既存のスタブを完成させる選択肢を吟味する。
3. **整合性の守護者(Guardian of Integrity)**: ✅ ステータスを軽々しく付けない。「動くテストがある」≠「機能が実装されている」。

### v3.0 で禁じられる態度

- 「テストが通っているのでヨシ」と判定する(テスト自体が空の契約しか検証していないかもしれない)
- スタブの上に新しい層を積む(土台が崩れる)
- 「他の機能も似たようなものだから」と乖離を放置する(原則 7 違反)

---

## 3. 7 Non-Negotiable Rules(★v3.0 で 6 → 7)

これらは絶対です。違反は CI または review で自動却下されます。

1. **Never break layer boundaries** — 8 層(0, 1, 2, 3, 3.5, 4, 4.5, 5, 6, 7)。`make arch-lint` で強制。
2. **Every generation function returns `(<output>, ProvenanceLog)`**
3. **No silent fallbacks** — 制約違反は明示的なエラー。意図的回復は `RecoverableDecision` で記録。
4. **No hardcoded musical values** — `src/yao/constants/` を使う。
5. **No public function without type hints and docstring** — `mypy --strict` で強制。
6. **Vertical alignment must be respected** — input / processing / evaluation のいずれを進めたかを PR で宣言。
7. **★v3.0 NEW: Status Honesty must be preserved** — ✅ ステータスは契約。スタブ実装に ✅ を付けることは却下事由。

### 第 7 原則の具体的意味

| 状況 | 正しい対応 |
|---|---|
| 新機能を実装した | テスト + 実機能パスで初めて ✅ |
| スタブを実装した | 🟡 with `limitation: stub implementation` |
| 別バックエンドに丸投げするコード | クラス名に `Stub` を含めるか、`is_stub=True` を返す |
| ドキュメントが「できる」と書いているが実コードがない | 🟡 → ⚪ にダウングレード(該当 PR を別途出す) |
| パイプラインに統合されていない実装 | 🟡 with `limitation: not integrated` |

`make honesty-check` がこれを機械的に強制します。

---

## 4. MUSTs(v3.0 で追加・強化)

### コード構造

- **Read existing code before writing new code**(`view` first)
- **Write tests before or alongside implementation**
- **Keep YAML schemas and Pydantic models in sync**(CI 強制)
- **Use `yao.ir.timing` for all tick/beat/second conversions**
- **Use `yao.ir.notation` for all note name/MIDI conversions**
- **Use `yao.ir.tuning` for all cents/microtonal conversions**
- **Derive velocity from dynamics curves**(never hardcode)
- **Register generators via `@register_generator("name")`**
- **Register critique rules via `@register_critique("rule_id")`**
- **Register subagents via `@register_subagent(AgentRole.X)`**

### v3.0 NEW: Layer Contracts(層間契約)

これらは PR マージ前に CI で検証されます。

- **Plan completeness**: Composer が返す `MotifPlan.seeds` は空であってはならない(Wave 1.1 以降)
- **Plan consumption**: NoteRealizer は `MusicalPlan` の主要フィールドの 80% 以上を読まなければならない(Wave 1.4 以降)
- **Skill grounding**: ジャンル Skill の `chord_palette` を変更すると生成 ChordEvent も変わらなければならない(Wave 2.1 以降)
- **Critic meaningfulness**: 空でない `MotifPlan` に対して `MotifRecurrenceDetector` は評価を返さなければならない
- **Backend honesty**: `AnthropicAPIBackend` を呼んだら、API キー設定時は本当に Anthropic を呼ばなければならない(Wave 1.2 以降)

### Provenance(継承+強化)

- **Every generation step records to `ProvenanceLog`**
- **Skill grounding records**: ジャンル Skill から取得した値を使った場合、`source_skill: "<genre_id>"` を Provenance に記録(★v3.0 NEW)
- **LLM call records**: LLM バックエンドを使った場合、`backend: "anthropic_api"`, `model: "<model>"`, `prompt_hash: "<sha256>"` を記録(★Wave 1.2 NEW)
- **Audit trail**: スタブ昇格やステータス変更は `docs/audit/` に永続化

### Testing(継承+強化)

- **Add to `tests/golden/`** if output should be bit-exact stable
- **Add to `tests/scenarios/`** if a musical scenario should be verified
- **Add to `tests/properties/`** for genre invariants
- **Add to `tests/subjective/ratings/`** if you generated and listened
- **★v3.0 NEW: Add to `tests/contracts/`** for layer contracts(Plan completeness, Skill grounding 等)

### Documentation(継承+厳格化)

- **Update `FEATURE_STATUS.md`** when adding/completing a feature
- **Never set ✅ status if the implementation is a stub**(★v3.0 強制)
- **PR description must include the Vertical Alignment self-check**
- **Add ADRs** to `docs/design/NNNN-topic.md` for non-trivial choices
- **Wave audit references**: 各 Wave 完了時に `docs/audit/wave-N-completion.md` を作成

---

## 5. MUST NOTs(v3.0 で項目追加)

### Imports(継承)

- Import `pretty_midi` / `music21` / `librosa` / `pyloudnorm` / `pedalboard` outside their designated layers
- Import `torch` / `transformers` / `magenta` / `audiocraft` outside `src/yao/generators/neural/`
- Import `sounddevice` / `mido.ports` outside `src/yao/improvise/` and CLI preview/watch
- **★v3.0 NEW: Import `anthropic` outside `src/yao/agents/anthropic_api_backend.py`**

### コードパターン(継承+追加)

- 不明瞭な関数名(`make_it_sound_good`, `do_music_stuff`)を使わない
- Provenance 記録をスキップしない
- 生の `ValueError` を使わない(`YaOError` 子孫を使う)
- 音域違反を黙って clamp しない(`RangeViolationError`)
- 同じ関数内で `Beat`, `Tick`, `seconds` を明示的変換なしに混在させない
- 機能ローマ数字(`I`, `V7/V`)と具体コード(`C`, `G7`)を同じフィールドで混在させない
- **★v3.0 NEW: 空の Plan オブジェクト(`MotifPlan(seeds=[], placements=[])`)を返す Subagent を書かない**(Wave 1.1 以降)
- **★v3.0 NEW: スタブ実装に「Stub」をクラス名に含めず、かつ `is_stub=True` も返さないコードを書かない**

### 音楽データ(継承+追加)

- アーティスト名や著作権楽曲をハードコードしない
- `references/catalog.yaml` の rights status なしに reference MIDI を追加しない
- `references.yaml` の `forbidden_to_extract` を迂回しない
- AI-disclosure stamp Hook を完了させずに output を生成しない
- **★v3.0 NEW: ジャンル Skill のフロントマターを `make sync-skills` を実行せずにマージしない**

### V2 Pipeline 規律(★v3.0 NEW)

- **Wave 1.4 以降**: NoteRealizer に `MusicalPlan` を `_plan_to_v1_spec()` で逆変換するコードを新規追加してはならない
- **Wave 2.0 以降**: 旧 `RuleBasedNoteRealizer` / `StochasticNoteRealizer`(v1 経由)を新規パスから呼んではならない
- **Wave 2 完了時**: `legacy_adapter.py` を新コードから import してはならない

### Workflow(継承+追加)

- `TODO` / `FIXME` をコミットに残さない
- push 前に `make all-checks` をスキップしない
- main に force-push しない
- **★v3.0 NEW: ステータス昇格(✅ への変更)を、`make honesty-check` を通さずに行わない**
- **★v3.0 NEW: Wave 1, 2 期間中、新機能 PR を Wave 3 のロードマップに無断で追加しない**

---

## 6. 7 Design Principles (v3.0)

これらは絶対の羅針盤です。迷ったら戻ってください。

1. **Agent = environment, not composer** — 人間の創造性を加速する
2. **Explain everything** — すべての音符に来歴がある
3. **Constraints liberate** — 仕様と規則は枷ではなく足場
4. **Time-axis first** — trajectory を音符より先に設計
5. **Human ear is truth** — 自動評価は情報、人間が判断
6. **Vertical alignment** — input expressivity, processing depth, evaluation resolution は同期して進歩
7. **★v3.0 NEW: Status Honesty** — ✅ は契約、スタブを ✅ にすることはプロジェクトの信頼性毀損

各 PR に対し、**少なくとも 1 つの原則が前進** し、**どれも違反していない** ことを確認してください。

---

## 7. Architecture Reference(8 Layers — 継承)

```
Layer 7: Reflection & Learning      (reflect/, runtime/, agents/)
Layer 6: Verification & Critique    (verify/)
Layer 5: Rendering                  (render/, mix/)
Layer 4.5: Performance Expression   (ir/expression.py, generators/performance/)
Layer 4: Perception Substitute      (perception/)
Layer 3.5: Musical Plan IR (MPIR)   (ir/plan/, generators/plan/)
Layer 3: Score IR                   (ir/)
Layer 2: Generation Strategy        (generators/note/)
Layer 1: Specification              (schema/, sketch/)
Layer 0: Constants                  (constants/)
```

**依存規則**: 各層は **下位層のみ** に依存可能。Conductor は任意層を import 可能だが、下位層から import されてはならない。

**MPIR が心臓**: Plan generators(Steps 1-5)が MPIR を生成。Critic Gate は MPIR で動作。Note Realizer(Step 6)が MPIR を消費して ScoreIR を生成。Performance Realizer(Step 6.5)が ScoreIR に PerformanceLayer を重ねる。Mix Designer(Step 7)が ProductionManifest を生成。

**v3.0 で強化されること**: 上記の流れは v2.0 で**設計済み**でしたが、Wave 1.4 まで NoteRealizer は MPIR を捨てて v1 spec で生成していました。Wave 1.4 以降、この流れが**実態として**機能します。

---

## 8. Current Phase(v3.0 = 全面再採点フェーズ)

### Wave 1:正直化(現在の主活動、4〜6 週間)

進行中の作業項目(優先順):

#### Sprint W1:再採点(全プロジェクトの基礎)

- [ ] `tools/honesty_check.py` を実装
- [ ] FEATURE_STATUS.md を全項目再採点
- [ ] スタブ ✅ をすべて 🟡 with `limitation:` にダウングレード
- [ ] `docs/audit/2026-05-status-reaudit.md` を作成

#### Sprint W2-3:Composer Subagent 本実装(Wave 1.1)

- [ ] `src/yao/ir/motif_extraction.py` 新設(既存スコアからの motif 抽出)
- [ ] `src/yao/ir/motif_generation.py` 新設(無からの motif 生成)
- [ ] `src/yao/ir/motif_placement.py` 新設(section への配置戦略)
- [ ] `src/yao/subagents/composer.py` 本実装
- [ ] `tests/integration/test_motif_recurrence.py` で critic が検出することを確認
- [ ] FEATURE_STATUS の Composer 行を更新

#### Sprint W3-4:AnthropicAPIBackend 本実装(Wave 1.2)

- [ ] `src/yao/agents/anthropic_api_backend.py` を本実装
- [ ] `is_stub = False` を宣言できる状態にする
- [ ] `BackendNotConfiguredError` 例外を導入
- [ ] `.claude/agents/<role>.md` を system prompt として読む機構
- [ ] tool use 経由の構造化出力パーサ
- [ ] `tests/llm_quality/` を新設(optional dependency `yao[llm-eval]`)
- [ ] FEATURE_STATUS の AnthropicAPIBackend 行を更新

#### Sprint W4-5:SpecCompiler LLM 化(Wave 1.3)

- [ ] `src/yao/sketch/compiler.py` を三段階フォールバック化
- [ ] 日本語感情語彙 50+ を `.claude/skills/psychology/emotion-mapping.md` に追加
- [ ] LLM compile path で構造化出力(JSON schema)
- [ ] 失敗時の keyword fallback
- [ ] `tests/integration/test_spec_compiler_ja.py` で日本語入力テスト

#### Sprint W5-6:V2 Pipeline 実装着手(Wave 1.4)

- [ ] `RuleBasedNoteRealizerV2` を `src/yao/generators/note/rule_based_v2.py` に実装
- [ ] `consumed_plan_fields` 宣言と AST scan ツール
- [ ] `tools/check_plan_consumption.py` を実装
- [ ] 旧 Realizer を `@deprecated` マーク
- [ ] ゴールデンテストを v2 出力で更新

### Wave 2:整合化(2026 Q4、8〜10 週間、未着手)

- NoteRealizerV2 のデフォルト化と旧実装削除
- ジャンル Skill loader と生成器統合(Wave 2.1)
- 美的評価指標 4 種(Wave 2.2)
- Audio Loop の Conductor 統合(Wave 2.3)

### Wave 3:深化(2027 Q1-Q2、未着手)

- Performance Layer のパイプライン標準化
- EnsembleConstraint
- 参照楽曲ライブラリ整備
- StyleVector の表現力強化(著作権セーフな範囲で)
- Subjective rating CLI
- `/sketch` 多段対話

### v3.0 期間中、新機能の追加は **基本的に禁止**

例外:
- バグ修正
- 既存スタブの埋め合わせ
- ロードマップに明示された Wave 1〜3 の項目
- 重大な問題発見に対する緊急対応

新機能を提案したい場合、Wave 3 末以降のロードマップに追加する PR を別途出してください。

---

## 9. Wave 別の実装規律

各 Wave に固有のルールがあります。該当 Sprint で作業するときは、対応するルールセットに必ず従ってください。

### Wave 1.1 規律: Composer Subagent

- **MotifPlan は必ず非空**: `len(seeds) >= 1` を保証
- **各 motif は 3 回以上配置**: `MotifRecurrenceDetector` の閾値と一致させる
- **identity_strength の根拠を Provenance に記録**: 「rhythm 特異性 0.7 + interval 特異性 0.5 = 0.6」のような分解
- **既存の `markov_models/diatonic_bigram.yaml` を再利用**: 重複データセットを作らない
- **テスト**: `tests/unit/subagents/test_composer.py` で「empty input でも seeds が出る」「placement が SongFormPlan と整合」を assert

### Wave 1.2 規律: Anthropic API Backend

- **API キー未設定 → 即エラー**: `silent fallback` 禁止。ユーザに正しいバックエンド選択を促す。
- **構造化出力必須**: tool use 経由でフィールド型を保証
- **プロンプトファイルから system prompt 構築**: `.claude/agents/<role>.md` をパースして再利用
- **テスト戦略**:
  - Unit test: モック化した Anthropic クライアントで動作検証
  - Integration test(optional): 実 API キー必要、CI ではスキップ
  - Quality test: PythonOnly vs LLM の出力比較、subjective evaluation
- **コスト警告**: 1 セッションで 100 LLM calls を超えたら warning ログ

### Wave 1.3 規律: SpecCompiler LLM 化

- **言語自動判定**: ascii ratio で英語/日本語を判定、明示指定も可能
- **schema validation 必須**: LLM 出力は `CompositionSpec.model_validate()` を通って初めて採用
- **fallback 順序の明示**: LLM → Keyword → Default、各段階の失敗を Provenance に記録
- **多言語感情ベクトル**: valence × arousal 平面でのマッピングを `tests/unit/sketch/test_emotion_mapping.py` で固定

### Wave 1.4 規律: V2 Pipeline

- **段階移行を厳守**: 旧実装を即削除しない、`Coexist → Switch → Remove` の 3 フェーズ
- **`consumed_plan_fields` の宣言義務**: NoteRealizer V2 は読むフィールドを class attribute で宣言
- **AST scan で実態検証**: 宣言フィールドが本当に読まれているか機械検証
- **ゴールデンテストの併走**: 旧→新の差分を可視化、品質低下があれば調査必須
- **`legacy_adapter.py` を新規パスから呼ばない**: import 検査で禁止

### Wave 2.1 規律: ジャンル Skill 統合

- **YAML フロントマターの schema**: `src/yao/skills/loader.py` の `GenreProfile` Pydantic モデルで validate
- **Skill 編集 → 再生成 → 出力差分** が必ず観測される: integration test で確認
- **5 つの統合ポイント**: SpecCompiler / HarmonyPlanner / DrumPatterner / Critique / PerformanceLayer
- **Hot reload は dev only**: production ではディスクポーリングしない
- **Skill 追加時のチェックリスト**: 必須フィールド、`forbidden_cliches`、文化的コンテキスト(non-Western のみ)

### Wave 2.2 規律: 美的評価指標

- **4 つの指標を `aesthetic` ディメンションに**: surprise / memorability / contrast / pacing
- **Surprise の計算**: bigram model from `markov_models/`、negative log likelihood
- **Memorability の計算**: motif recurrence × identity_strength
- **Contrast の計算**: 隣接セクションの StyleVector 距離
- **Pacing の計算**: tension trajectory の累積エントロピー
- **ベンチマーク必須**: 良楽曲 5 つ + 退屈楽曲 5 つでスコアが期待通りに分かれることを `tests/integration/test_aesthetic_metrics.py` で確認

### Wave 2.3 規律: Audio Loop

- **opt-in flag 経由**: `enable_audio_loop=True`、デフォルト False
- **CI 用最小 SoundFont**: `soundfonts/yao_minimal.sf2`(8MB 程度)を同梱
- **adaptation を 3 種類以上実装**: register 調整、dynamics 調整、EQ 調整
- **無限ループ防止**: max 2 audio iterations

---

## 10. v3.0 で必須化される CI チェック

```yaml
# .github/workflows/quality.yml
- name: All checks (v3.0 honesty pipeline)
  run: |
    make lint
    make arch-lint
    make honesty-check          # ★v3.0
    make plan-consumption       # ★v3.0(Wave 1.4 以降必須)
    make skill-grounding        # ★v3.0(Wave 2.1 以降必須)
    make critic-coverage        # ★v3.0(Wave 1.1 以降必須)
    make backend-honesty        # ★v3.0
    make feature-status
    make sync-docs
    make test
    make test-golden
```

各チェックの責任:

| チェック | 責任 | 失敗時の修正方針 |
|---|---|---|
| `honesty-check` | ✅ 機能の各ファイルが空でないこと | 実装を完成させる、または status を 🟡 にする |
| `plan-consumption` | NoteRealizer が MusicalPlan の 80% 以上のフィールドを読むこと | NoteRealizerV2 の `_realize_section` を拡張 |
| `skill-grounding` | ジャンル Skill の編集が出力に影響すること | Skill loader を該当ポイントに統合 |
| `critic-coverage` | 各 Severity で意味のある検出が起こること | Critique rule の閾値・対象データ確認 |
| `backend-honesty` | Stub backend が `is_stub=True` を返すこと | バックエンドクラスに `is_stub` 属性を追加 |

---

## 11. Automated Failure Prevention(v3.0 で項目追加)

| Pattern | 検出方法 | コマンド |
|---|---|---|
| Tick calculation error | `test_ir.py`, `test_timing.py` | `make test-unit` |
| Cents/microtonal arithmetic error | `test_tuning.py` | `make test-unit` |
| Range violation silence | `RangeViolationError`(no silent clamp) | `make test` |
| Velocity hardcode | `ruff` custom rule | `make lint` |
| Missing provenance | `GeneratorBase.generate()` の return 型 | `mypy` |
| Layer boundary breach | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | template loader integration test | `make test-integration` |
| Parallel fifths | Constraint checker + voicing | `make test` |
| MPIR contract violation | `test_plan_contracts.py` | `make test-unit` |
| Subagent contract violation | `test_subagent_contracts.py` | `make test-unit` |
| FEATURE_STATUS drift | `tools/feature_status_check.py` | `make feature-status` |
| Doc drift | `tools/sync_docs.py` | `make sync-docs` |
| Skill markdown/yaml drift | `tools/sync_skills.py` | `make sync-skills` |
| Neural call without provenance | unit test | `make test-unit` |
| AI-disclosure missing | `ai-disclosure-stamp` Hook | `make test-integration` |
| Copyright extraction breach | schema validator + runtime guard | `make test` |
| **★v3.0: Empty Plan returned by Subagent** | `tests/contracts/test_plan_completeness.py` | `make critic-coverage` |
| **★v3.0: Stub backend masquerading as real** | `tests/contracts/test_backend_honesty.py` | `make backend-honesty` |
| **★v3.0: Skill changes don't affect output** | `tests/integration/test_skill_grounding.py` | `make skill-grounding` |
| **★v3.0: NoteRealizer doesn't read MusicalPlan** | `tools/check_plan_consumption.py` | `make plan-consumption` |
| **★v3.0: ✅ status without real implementation** | `tools/honesty_check.py` | `make honesty-check` |

---

## 12. Performance Expectations(継承)

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec | <100ms | Pydantic validation |
| Generate 8-bar piece (rule_based) | <1s | Deterministic |
| Generate 8-bar piece (stochastic) | <1s | Deterministic given seed |
| Generate 8-bar piece (markov) | <2s | |
| Generate 8-bar piece (constraint_satisfaction) | <5s | timeout at 5s |
| Generate 64-bar piece (any non-neural) | <5s | Stochastic may vary |
| Generate via neural texture | <60s | CPU mode allowed |
| Plan critic gate (50+ rules) | <2s | |
| Multi-candidate generation (5 parallel) | <15s | concurrent.futures |
| Audio feature extraction (90s WAV) | <3s | librosa + pyloudnorm |
| Use-case evaluator | <500ms | |
| Reference style vector extraction | <2s | cached after first run |
| Mix chain (90s, 5 stems) | <10s | pedalboard offline |
| MusicXML write | <1s | |
| LilyPond render to PDF | <30s | subprocess |
| Write MIDI file | <200ms | pretty_midi |
| Run full lint | <500ms | |
| Run all unit tests | <10s | |
| Architecture lint | <2s | AST parsing |
| **★v3.0: Honesty check** | <5s | grep + import scan |
| **★v3.0: Plan consumption check** | <3s | AST scan |
| **★v3.0: Skill grounding test** | <30s | requires generation |

予算超過は事前議論必須。`pytest.mark.slow` を活用。

---

## 13. v3.0 特有の失敗パターン

v1.0、v2.0 のパターンを継承しつつ、v3.0 で**特に警戒すべきパターン**を追加します。

### F11: Status 上げ抜け道(★v3.0 NEW)

スタブ実装を「テストがある」「形式的に動く」と理由付けて ✅ にしようとする。

**回避**: `make honesty-check` を必ず通す。`is_stub=True` を返すコードに ✅ は付けない。

### F12: 「とりあえず legacy_adapter で」誘惑(★v3.0 NEW)

新機能を実装するとき、すでに動いている v1 generator を呼ぶ方が早いので、`_plan_to_v1_spec()` を再び呼びたくなる。

**回避**: Wave 1.4 以降、`legacy_adapter` を新規 import するコードは PR で reject。

### F13: Skill ファイルを書いて満足する(★v3.0 NEW)

`.claude/skills/genres/<new>.md` を作成して、生成パイプラインに統合せず満足する。Skill が孤立する。

**回避**: 新規 Skill PR は必ず integration test を伴う。`make skill-grounding` を通すこと。

### F14: 主観的評価の自己完結(★v3.0 NEW)

開発者が自分で生成・評価して「いい音楽だ」と判定する。これは subjective rating ではなく自慰。

**回避**: Subjective rating は最低 2 名(できれば 3 名以上)。開発者の自評価は補助情報。

### F15: AnthropicAPIBackend の silent activation(★v3.0 NEW)

PythonOnly でテストが通っているのに、本番で勝手に Anthropic API が呼ばれる。コストとレイテンシの問題。

**回避**: バックエンド選択は **明示的な opt-in 必須**。env var or config で。

### F16: 監査結果の埃化(★v3.0 NEW)

`docs/audit/` を一度書いて、その後参照されない。教訓化されない。

**回避**: 月次の `make audit-monthly` で過去の audit を参照、新しい乖離があれば追記。

### 既存パターン F1〜F10 も継承

- F1: 「Just one more conditional」in generators
- F2: MPIR-Score divergence
- F3: Layer 4.5 leaking into Layer 3
- F4: Neural calls hidden in synchronous code
- F5: Microtonal scale assumed semitone
- F6: Cultural insensitivity by omission
- F7: Silent capability drift
- F8: Subagent definition drift
- F9: References used as input training data
- F10: Provenance entry without rationale

---

## 14. Workflow for Adding a v3.0 Feature(再構成)

v3.0 期間中、新機能と既存機能の埋め合わせは扱いが異なります。

### A. 既存スタブの埋め合わせ(推奨パス)

1. **対象を選ぶ**: FEATURE_STATUS.md で 🟡 with `limitation:` のものから
2. **読む**: 該当 Skill、関連 Subagent、PROJECT.md v3.0 の該当 Wave セクション
3. **失敗テストを書く**: 「現状ではこのテストが失敗する」状態を作る
4. **層を確認**: 該当 layer (0〜7) を再確認
5. **既存パターン参照**: 類似実装を `view` する
6. **契約を設計**: 入力型・出力型・例外・Provenance フィールド
7. **実装**: 最小限でテストを通す
8. **ステータス昇格**: 🟡 → ✅(`make honesty-check` を通す)
9. **`make all-checks`**: 全チェック通過
10. **音を生成して確認**(Sound-First)
11. **PR**:
    - What/Why/How
    - Music impact(該当時)
    - Tests added
    - Vertical Alignment self-check
    - **Status change justification**(★v3.0)
    - Audio sample(該当時)

### B. 新機能の追加(原則 Wave 3 末以降のみ)

Wave 1〜2 期間中は**禁止**。Wave 3 末以降のみ。

1. **ロードマップ追加 PR**: PROJECT.md v3.0 §15 に追加する別 PR
2. **設計レビュー**: human approval 必須
3. **その後** A の手順を踏む

### C. バグ修正(常時可能)

1. 失敗するテストを書く
2. 修正
3. PR

---

## 15. Recent Changes(v3.0 起点での更新)

最新が上:

- **2026-05-03 (Wave 2 完了)**: Alignment Wave 完了 — 美的評価指標 4 種(surprise/memorability/contrast/pacing)追加、evaluator に aesthetic dimension(weight 0.20)統合、Conductor feedback に 5 aesthetic adaptations、boring vs good 1.7x 分離達成、Skill loader 基盤、1104 tests pass
- **2026-05-03 (Wave 1 完了)**: Honesty Wave 完了 — 5 CI honesty ツール導入、AnthropicAPIBackend 本実装(is_stub=False)、SpecCompiler 日本語対応+三段階フォールバック、RuleBasedNoteRealizerV2+StochasticNoteRealizerV2(100% plan consumption)、backend-honesty FAIL→PASS、1074 tests all pass
- **2026-05-02 (PROJECT.md v3.0)**: Closing-the-Gap Edition — 監査結果に基づき Wave 1〜3 を策定、原則 7「Status Honesty」追加、新機能添加を Wave 3 末まで原則禁止、CI チェックの honesty 系統が必須化
- **2026-05-02 (PROJECT.md v2.0)**: 8-layer architecture, Layer 4.5, 6th principle (Vertical Alignment), Tier 1-4 roadmap formalized
- **2026-04-30**: FEATURE_STATUS.md as single source of truth
- **2026-04-29**: MIDI reader, section regeneration, evaluation.json persistence
- **2026-04-29**: Constraint system, CLI diff/explain, stochastic unit tests
- **2026-04-28**: Stochastic generator, generator registry, queryable provenance
- **2026-04-28**: Phase 0+1 complete: 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI
- **2026-04-27**: Project initialized

---

## 16. Escalation(v3.0 で項目追加)

人間に確認すべきケース:

- **Music theory judgment** — 進行が「voice-leading clean」か、スタイル的に適切か不確かな時
- **Cultural sensitivity** — 世界ジャンル Skill 追加、翻訳、命名
- **Copyright / rights** — reference 素材追加、neural model 統合
- **Architectural boundaries** — layer 変更、新 layer 追加
- **Adding new external dependencies** — heavyweight 特に(torch, magenta, vst3 hosts)
- **Deleting files or rewriting git history**
- **Any change touching 5+ files in different layers**
- **Changes that would require updating PROJECT.md or VISION.md**
- **Performance regressions** that exceed budgets
- **Subjective quality evaluation** — 生成して merge 前に人耳確認したい時
- **Neural model selection** — Stable Audio version, MusicGen size 等
- **★v3.0 NEW: Status 昇格(🟡 → ✅)で `honesty-check` が通っているが、実機能に確信がない場合**
- **★v3.0 NEW: 新機能を Wave 1〜2 期間中に提案したい場合**
- **★v3.0 NEW: 監査結果に新たな乖離を発見した場合(自分で勝手に修正せず報告)**
- **★v3.0 NEW: legacy_adapter を一時的にでも使いたい時(代替案を必ず議論)**

人間が指揮者、あなたは Subagent。不確実なら譲る。

---

## 17. Wave 別 Cheat Sheet

各 Sprint で常に手元に置くべき早見表。

### Wave 1.1 Composer 開発時

```
✓ MotifPlan.seeds が必ず非空(len >= 1)
✓ 各 motif は section に 3 回以上配置
✓ identity_strength の根拠を Provenance に記録
✓ tests/unit/subagents/test_composer.py で空でないことを assert
✓ tests/integration/test_motif_recurrence.py で critic が動作することを確認
```

### Wave 1.2 Anthropic API 開発時

```
✓ is_stub = False
✓ API キー未設定で silent fallback しない(BackendNotConfiguredError)
✓ .claude/agents/<role>.md を system prompt として読む
✓ tool use 経由で構造化出力
✓ Provenance に backend, model, prompt_hash 記録
✓ tests/llm_quality/ は optional(yao[llm-eval] extra)
```

### Wave 1.3 SpecCompiler 開発時

```
✓ 三段階フォールバック(LLM → Keyword → Default)
✓ LLM 出力は schema validate を通る
✓ 日本語感情語彙 50+ を追加
✓ tests/integration/test_spec_compiler_ja.py で日本語入力テスト
```

### Wave 1.4 NoteRealizerV2 開発時

```
✓ consumed_plan_fields を class attribute で宣言
✓ MusicalPlan を直接消費(_plan_to_v1_spec 禁止)
✓ tools/check_plan_consumption.py で AST scan
✓ ゴールデンテスト併走
✓ 旧 Realizer は @deprecated(削除はしない)
```

### Wave 2.1 Skill 統合開発時

```
✓ YAML フロントマターを GenreProfile schema で validate
✓ 5 つの統合ポイント(SpecCompiler/HarmonyPlanner/DrumPatterner/Critique/PerformanceLayer)
✓ tests/integration/test_skill_grounding.py で確認
✓ Hot reload は dev only(production はポーリングなし)
✓ make sync-skills で md ↔ yaml 整合
```

### Wave 2.2 美的評価開発時

```
✓ 4 指標を aesthetic dimension に
✓ Surprise: bigram NLL
✓ Memorability: motif recurrence × identity
✓ Contrast: section 間 StyleVector 距離
✓ Pacing: tension entropy
✓ ベンチマーク 10 楽曲(良 5 + 退屈 5)で分離確認
```

### Wave 2.3 Audio Loop 開発時

```
✓ opt-in flag(enable_audio_loop)
✓ CI 用最小 SoundFont を同梱
✓ adaptation 3 種類以上
✓ max 2 audio iterations(無限ループ防止)
```

---

## 18. Guides(継承+v3.0 NEW 項目)

| Guide | When to read |
|---|---|
| [Architecture](./.claude/guides/architecture.md) | Working across layers |
| [Coding Conventions](./.claude/guides/coding-conventions.md) | Writing any code |
| [Music Engineering](./.claude/guides/music-engineering.md) | Generating notes, MPIR, microtonal |
| [Testing](./.claude/guides/testing.md) | Writing or running tests |
| [Workflow](./.claude/guides/workflow.md) | Planning a change |
| [Cultural Sensitivity](./.claude/guides/cultural-sensitivity.md) | Adding world genres |
| [Subagent Implementation](./.claude/guides/subagents.md) | Implementing Python Subagents |
| [Performance Layer](./.claude/guides/performance-layer.md) | Layer 4.5 design |
| [Arrangement Engine](./.claude/guides/arrangement.md) | MIDI extraction, style ops |
| [Neural Integration](./.claude/guides/neural.md) | Bridging to neural models |
| **[Auditing](./.claude/guides/auditing.md)** | **★v3.0 NEW: Implementation auditing methodology** |
| **[Honesty Tooling](./.claude/guides/honesty-tooling.md)** | **★v3.0 NEW: How honesty-check, plan-consumption, skill-grounding work** |
| **[Wave 1 Playbook](./.claude/guides/wave-1-playbook.md)** | **★v3.0 NEW: Step-by-step for closing identified gaps** |

Full design documentation: [PROJECT.md](./PROJECT.md)
Target architecture: [VISION.md](./VISION.md)
Capability matrix: [FEATURE_STATUS.md](./FEATURE_STATUS.md)
Audit log: [docs/audit/](./docs/audit/)

---

## 19. When in Doubt(v3.0 で更新)

順番に問いかけてください。

1. **Which of the 7 principles does this advance?** None なら再考。
2. **Which of input/processing/evaluation does this advance?** 1 つだけなら、なぜ整合がないかを記述。
3. **Which layer does this belong to?** 正しく配置。
4. **What is the contract?** 入力、出力、エラー、provenance フィールド。
5. **What is the test?** Unit, integration, scenario, contract, subjective?
6. **★v3.0: Will FEATURE_STATUS.md show ✅ or 🟡 after this lands?** ✅ にするなら honesty-check を通すこと。
7. **★v3.0: Is this in the current Wave's scope?** Wave 1〜2 期間中、新機能なら escalate。
8. **★v3.0: Have I read the relevant Wave Playbook?** Wave 1.1〜2.3 には個別の playbook あり。
9. **What does FEATURE_STATUS.md say after this lands?**
10. **Has the human asked for this, or am I scope-creeping?**

明確に答えられなければ、**stop and escalate**。

---

## 20. v3.0 期間中の最大のメッセージ

> **新機能を作りたい衝動を、既存機能を完成させる規律に変換せよ。**

設計が立派でも、コードがスタブなら音は鳴りません。8 層アーキテクチャが美しくても、Composer が空 Plan を返すなら音楽は生まれません。22 のジャンル Skill があっても、生成器に届かないなら無意味です。

v3.0 が終わるとき、YaO は **本当に動く** プロジェクトになります。それまでの間、あなたの作業はしばしば地味で、目立たず、ヒーロー的でないかもしれません。しかしこれが、YaO を「設計上素晴らしい」から「**実際に素晴らしい**」へ移行させる唯一の道です。

> *Build the orchestra well, so the conductor can lead it freely.*
> *— this time, build it for real.*

---

**CLAUDE.md version: 3.0 (Closing-the-Gap Edition)**
**Last updated: 2026-05-02**
**Aligned with: PROJECT.md v3.0**
**Wave: 1 (Honesty)**
**Audit reference: docs/audit/2026-05-status-reaudit.md**
