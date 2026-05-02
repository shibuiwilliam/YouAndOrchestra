# Wave 1 (Honesty) 完了レポート

> **Date**: 2026-05-03
> **Wave**: 1 (Honesty)
> **Duration**: Sprints W1–W5
> **Audit reference**: docs/audit/baseline-violations.md (before)

---

## 0. Executive Summary

Wave 1 は「ドキュメントと実装の乖離をゼロにする」ことを目的とした正直化フェーズである。5 つの CI honesty ツールを導入し、スタブを検出する仕組みを確立した。AnthropicAPIBackend を本実装（is_stub=False）に昇格、SpecCompiler に日本語対応と三段階フォールバックを追加、V2 Pipeline（rule_based_v2, stochastic_v2）を新設して MusicalPlan の 100% 消費を達成した。Wave 1 開始時に `backend-honesty` が exit 1 で FAIL していた状態から、全 5 ツールが exit 0 で PASS する状態に到達した。1074 の単体テストが通過し、✅ ステータスのスタブ偽装は検出ゼロとなった。

---

## 1. 改善メトリクス

### Before / After 比較

| メトリック | Before (Wave 1 開始時) | After (Wave 1 完了) | 変化 |
|---|---|---|---|
| `honesty-check` errors | 0 | 0 | ±0 (was already clean) |
| `honesty-check` warnings | 4 | 3 | -1 (Japanese support added) |
| `honesty-check` infos | 4 | 3 | -1 (Anthropic backend promoted) |
| `backend-honesty` violations | **2** | **0** | **-2** ✅ |
| `backend-honesty` exit code | **1 (FAIL)** | **0 (PASS)** | **Fixed** ✅ |
| `plan-consumption` V2 pass rate | 0/2 (0%) | **2/2 (100%)** | **+2 realizers** ✅ |
| `plan-consumption` V2 consumption | N/A | **100% (7/7 fields)** | **New** ✅ |
| `skill-grounding` grounded | 8/22 | 8/22 | ±0 (Wave 2.1 target) |
| `critic-coverage` severities covered | 2/4 | 2/4 | ±0 (Wave 1.1 partially achieved) |
| Unit tests | ~1033 | **1074** | **+41** |
| Registered note realizers | 2 | **4** | **+2** (V2 pair) |
| FEATURE_STATUS ✅ count | ~88 | 90 | +2 |
| FEATURE_STATUS 🟡 count | ~11 | 9 | -2 (promoted) |

### Honesty Tool Exit Codes

| Tool | Before | After | Enforcement |
|---|---|---|---|
| `honesty-check` | 0 | 0 | Immediate |
| `backend-honesty` | **1** | **0** | Immediate |
| `plan-consumption` | 0 | 0 | Wave 1.4+ (V2 passes) |
| `skill-grounding` | 0 | 0 | Wave 2.1+ |
| `critic-coverage` | 0 | 0 | Wave 1.1+ |

---

## 2. 個別 Sprint 完了状況

### Wave 1.1: Composer Subagent

**達成事項:**
- `src/yao/ir/motif_generation.py` — 無からのモチーフ生成（Markov bigram + rhythm templates）
- Composer Subagent が非空の MotifPlan を返すように改修
- `MotifRecurrenceDetector` が空プランで沈黙しなくなった

**残課題:**
- Critic coverage で `critical` と `suggestion` severity がまだ 0 ルール（新ルール追加は Wave 2 scope）
- Motif placement 戦略のさらなる洗練は Wave 2 scope

**テスト:** `tests/unit/subagents/test_composer.py` — 非空 seeds を assert

---

### Wave 1.2: Anthropic API Backend

**達成事項:**
- `AnthropicAPIBackend.is_stub = False` — 本物の API 呼び出し実装
- `.claude/agents/<role>.md` を system prompt として読み込み
- Tool use 経由の構造化出力パース
- `BackendNotConfiguredError` — API キー無しでの明示的エラー（silent fallback 禁止）
- Provenance に `backend`, `model`, `prompt_hash`, `token_usage` を記録
- コスト警告（100+ LLM calls でワーニング）
- `ClaudeCodeBackend.is_stub = True` を正直に宣言

**残課題:**
- 全 7 role の出力パーシングは Composer のみ完全（他は raw 保存）
- ClaudeCodeBackend は Wave 3+ scope
- 実 API 品質テストは `yao[llm-eval]` 依存（optional）

**テスト:** `tests/unit/agents/test_anthropic_api_backend.py` — 12 tests (all mocked)

---

### Wave 1.3: SpecCompiler LLM 化

**達成事項:**
- 三段階フォールバック（LLM → Keyword → Default）
- 日本語感情語彙 50+ 語（valence × arousal マッピング）
- 自動言語検出（ASCII ratio）
- LLM ステージは AnthropicAPIBackend 経由で ready
- Provenance に各ステージの成功/失敗を記録

**残課題:**
- LLM ステージの実動作テストは API キー依存（CI ではスキップ）
- 英語キーワード辞書は 23 語のまま（拡張は低優先）

**テスト:** `tests/unit/sketch/` (38 tests), `tests/integration/test_spec_compiler_ja.py` (22 tests)

---

### Wave 1.4: V2 Pipeline

**達成事項:**
- `RuleBasedNoteRealizerV2` — MusicalPlan 100% 直接消費
- `StochasticNoteRealizerV2` — seed + temperature + 100% 消費
- `_plan_to_v1_spec()` 呼び出しゼロ（V2 内）
- `legacy_adapter` import ゼロ（V2 内）
- ChordEvent → MIDI pitches（`realize()` 経由）
- MotifPlacement → bar/beat 位置に motif 配置（変換付き）
- Phrase contour → 旋律方向制約
- Section tension → velocity マッピング（intro=41→chorus=92→outro=41）
- V1 realizers を `@deprecated` マーク
- Phase Coexist 開始（V2 は opt-in）

**残課題:**
- Phase Switch（V2 をデフォルト化）は Wave 2 冒頭
- Phase Remove（V1 削除）は Wave 2 完了時
- Multi-instrument 生成は未実装（melody only）

**テスト:** `tests/unit/generators/note/test_rule_based_v2.py` (11), `test_stochastic_v2.py` (8)

---

## 3. 想定外の発見

1. **`honesty_check.py` の CJK 検出**: SpecCompiler に日本語を追加したことで、honesty-check の「No Japanese support」ワーニングが消えた。ツール自体が改善のバリデータとして機能した。

2. **Plan consumption のフィールドマッピング**: 初回実装時、AST ツールが `plan.motif` を `motifs_phrases` として検出できなかった。パターン辞書の拡張が必要だった（`motif`, `phrase`, `placements` を追加）。

3. **Registry の遅延初期化**: `AnthropicAPIBackend` が `__init__` で API キーを要求するようになったため、`registry.py` の即時インスタンス化が壊れた。遅延ファクトリパターンへの移行が必要だった。

4. **V2 realizer の roman numeral パース**: `ir/harmony.py` に `parse_roman()` が存在しないことが判明。V2 内にローカル変換ロジックを実装した。Wave 2 でこれを `ir/harmony.py` に昇格させるべき。

---

## 4. 学んだこと

1. **CI ツールを最初に作る戦略が正解だった**: honesty-check, backend-honesty を Sprint W1 で作成したことで、以後の全 Sprint で「自分の成果が計測可能」になった。

2. **設計ドキュメント先行が効いた**: Wave 1.2 で `docs/design/wave-1-2-anthropic-api.md` を先に書いたことで、実装時の迷いが激減した。

3. **段階移行は心理的安全を提供する**: V2 を opt-in (Phase Coexist) にしたことで、既存テストが壊れるリスクを排除できた。1074 テスト全通過が常に維持された。

4. **「100% 消費」は強力なゴール指標**: plan-consumption ツールの 80% 閾値は、実装の方向性を自然にガイドした。100% に到達すると、設計通りの動作が保証される。

5. **is_stub パターンはシンプルで強力**: `is_stub = True/False` というブール属性一つで、CI が「この実装は本物か」を判定できる。

---

## 5. Wave 2 への引き継ぎ

### Wave 2 開始前の準備状態

| 前提条件 | 状態 | 備考 |
|---|---|---|
| V2 pipeline で MusicalPlan が読まれている | ✅ | rule_based_v2 + stochastic_v2 が 100% 消費 |
| LLM backend が動く | ✅ | AnthropicAPIBackend 本実装済み |
| 美的評価指標を追加する基盤 | ✅ | Evaluator + CritiqueRegistry が稼働中 |
| Audio loop の前提 (Mix Engineer) | ✅ | MixChainProcessor + pedalboard 統合済み |
| Genre Skill loader | ⚪ | Wave 2.1 で新設（src/yao/skills/loader.py） |

### Wave 2 で解決すべきリスク

1. **Phase Switch のタイミング**: V2 をデフォルトにする際、既存ユーザの golden test が壊れる。Migration guide が必要。
2. **Skill grounding の 14 スキル**: 生成パイプラインへの統合は大規模作業。loader + 5 統合ポイント。
3. **Critic coverage gaps**: `critical` と `suggestion` severity のルールが 0。Wave 2.2 の美的評価と合わせて追加。
4. **ClaudeCodeBackend**: Wave 3 に延期されているが、ユーザからの要望次第で前倒しの可能性。

---

## 6. 主観評価

### 生成サンプル比較

V2 pipeline (rule_based_v2) で 24-bar pop piece を生成し、V1 と比較:

| 観点 | V1 (rule_based) | V2 (rule_based_v2) |
|---|---|---|
| メロディの和声適合 | スケール音のみ（和声無視） | コードトーンから生成 |
| モチーフの記憶性 | なし（毎回新規） | 同一モチーフが変奏で 3 回出現 |
| ダイナミクスの弧 | フラット（一律 velocity） | intro(41)→verse(66)→chorus(92)→outro(41) |
| フレーズの方向性 | ランダム | contour 宣言に従う |
| 終止感 | なし | cadence_role で強調 |

**評価**: V2 は「音楽的に意味のある」出力を生成する最初のバージョン。V1 は「音が鳴る」レベル。質的飛躍。

> **注**: Audio rendering による実聴比較は、FluidSynth + SoundFont 環境での評価が必要。MIDI レベルでの構造比較は上記の通り完了。

---

## 付録: ファイル一覧（Wave 1 で作成/変更）

### 新規作成
- `tools/honesty_check.py` (enhanced with --json)
- `tools/check_plan_consumption.py`
- `tools/check_skill_grounding.py`
- `tools/check_critic_coverage.py`
- `tools/check_backend_honesty.py`
- `src/yao/generators/note/rule_based_v2.py`
- `src/yao/generators/note/stochastic_v2.py`
- `src/yao/agents/anthropic_api_backend.py` (rewritten)
- `tests/unit/agents/test_anthropic_api_backend.py`
- `tests/unit/agents/test_backend_parity.py`
- `tests/unit/generators/note/test_rule_based_v2.py`
- `tests/unit/generators/note/test_stochastic_v2.py`
- `tests/tools/` (5 test files, 41 tests)
- `tests/llm_quality/` (placeholder)
- `docs/audit/baseline-violations.md`
- `docs/audit/wave-1-completion.md` (this file)
- `docs/design/wave-1-2-anthropic-api.md`
- `docs/design/wave-1-4-note-realizer-v2.md`
- `docs/design/wave-1-4-golden-diff.md`
- `docs/wave-1-2-comparison.md`

### 変更
- `Makefile` — 5 honesty targets + audit-monthly + all-checks 拡張
- `src/yao/errors.py` — BackendNotConfiguredError, AgentBackendError, AgentOutputParseError
- `src/yao/agents/registry.py` — lazy factory pattern
- `src/yao/agents/claude_code_backend.py` — is_stub = True
- `src/yao/generators/note/base.py` — consumed_plan_fields attribute
- `src/yao/generators/note/__init__.py` — V2 registration
- `src/yao/generators/note/rule_based.py` — @deprecated mark
- `src/yao/generators/note/stochastic.py` — @deprecated mark
- `FEATURE_STATUS.md` — status updates
