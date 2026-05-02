# YaO v3.0 開始時の実装監査レポート

> **監査実施日**: 2026-05-03
> **監査者**: Claude Code (v3.0 参画時オンボーディング監査)
> **対象バージョン**: PROJECT.md v3.0 (2026-05-02)
> **参照文書**: CLAUDE.md v3.0, FEATURE_STATUS.md (2026-04-30), VISION.md

---

## 0. 監査の目的と方法

### 目的

PROJECT.md v3.0 §0 は、v2.0 が「素晴らしい設計書」であったが、**FEATURE_STATUS.md が ✅ と表示する多くの機能が、実態としては「動作するスタブ」に過ぎない**ことを宣言している。v3.0 の開発はこの乖離の解消を最優先とする。

本監査は、v3.0 開発の出発点として、FEATURE_STATUS.md の全 ✅ 項目を実コードと突合し、乖離を定量的に記録することを目的とする。

### 方法

1. **ファイル読み (Read)**: CLAUDE.md §0 で指摘された 5 つの主要スタブを起点に、各ソースファイルを行単位で確認
2. **grep / コードトレース**: `skills/genres` の src/ からの参照有無、`_plan_to_v1_spec` / `legacy_adapter` の使用箇所を検索
3. **パイプライン追跡**: Composer → MotifPlan → Critic → NoteRealizer の流れを、実際のコードで追跡
4. **テストの実質検証**: テストファイルが「スタブの動作確認」に留まるか、「実機能の検証」かを判別

---

## 1. 監査結果サマリー

### 全体所感

YaO の 8 層アーキテクチャは設計として健全であり、Layer 0（Constants）、Layer 3（Score IR）、Layer 5（MIDI Rendering）は実装が充実している。しかし、**Layer 3.5（MPIR）から Layer 2（Generation Strategy）への接続が事実上断線**しており、v2 パイプラインの心臓部が機能していない。Composer Subagent が空の MotifPlan を返し、NoteRealizer がそれを無視して v1 に逆変換するため、MPIR の存在意義が現時点では設計上のものに留まる。ジャンル Skill（22 個）は生成パイプラインから一切参照されておらず、「Markdown を編集するだけで生成挙動を変えられる」という YaO の独自価値が未実現である。LLM バックエンド（Anthropic API / Claude Code）は両方ともスタブで、PythonOnly への silent fallback を行っている。

### 乖離件数

| Tier | 説明 | 件数 |
|------|------|------|
| **Tier 1** (致命的) | パイプラインの中核が機能していない | 3 件 |
| **Tier 2** (重大) | 主要機能がスタブまたは未統合 | 4 件 |
| **Tier 3** (軽微) | 機能の一部が未完成だが影響限定的 | 4 件 |
| **合計** | | **11 件** |

---

## 2. 個別ギャップ項目

### Gap-1: Composer Subagent が空の MotifPlan を返す

**Tier**: 1 (致命的)
**対応する Wave**: Wave 1.1
**FEATURE_STATUS.md での主張**: ✅ 7 Subagent Python implementations — "SubagentBase, AgentRole, AgentContext, AgentOutput; all 7 roles registered; dual consistency with .md"
**実装の実態**:

```python
# src/yao/subagents/composer.py:49-50
motif_plan = MotifPlan(seeds=[], placements=[])
phrase_plan = PhrasePlan(phrases=[], bars_per_phrase=4.0, pattern="")
```

Composer は入力（spec, intent, trajectory）を一切読まず、常に空の MotifPlan と PhrasePlan を返す。コメント（L47）にも `"Phase α stubs"` と明記されている。

**影響**: MusicalPlan の motif/phrase が常に空であるため:
- Adversarial Critic の `MotifAbsenceDetector`（`src/yao/verify/critique/memorability.py:26`）が `Severity.MINOR` の Finding を返すのみで、生成をブロックしない
- `MotifRecurrenceDetector` が「seeds なし → 即 return」で沈黙する
- 生成された楽曲に記憶可能なモチーフが存在しない

**修正方針**: Sprint W2-3（Wave 1.1）で `src/yao/ir/motif_extraction.py`, `motif_generation.py`, `motif_placement.py` を新設し、`composer.py` を本実装する。完了条件: `MotifPlan.seeds` が常に 1 つ以上。

---

### Gap-2: NoteRealizer が MusicalPlan を捨てて v1 に逆変換

**Tier**: 1 (致命的)
**対応する Wave**: Wave 1.4
**FEATURE_STATUS.md での主張**: ✅ rule_based generator / ✅ stochastic generator — "Deterministic; trajectory: tension → velocity only" / "seed / temperature / contour"
**実装の実態**:

```python
# src/yao/generators/note/rule_based.py:54
v1_spec = original_spec if original_spec is not None else _plan_to_v1_spec(plan)

# src/yao/generators/note/rule_based.py:65-66
gen = RuleBasedGenerator()
score, gen_prov = gen.generate(v1_spec, trajectory=traj_spec)
```

```python
# src/yao/generators/note/stochastic.py:52
v1_spec = original_spec if original_spec is not None else _plan_to_v1_spec(plan)
```

`_plan_to_v1_spec()`（`rule_based.py:76-118`）は MusicalPlan から `global_context`（key, tempo, instruments）と `form.sections`（id, bars, target_tension）のみを抽出し、`motif`, `harmony_plan`, `phrase`, `arrangement` を**完全に無視**する。L8 のコメントに `"Phase β will rewrite this to read MusicalPlan directly"` と明記。

**影響**: MPIR（Layer 3.5）の存在意義が崩壊。7 ステップパイプラインの Step 1-5 で生成された計画（和声進行、モチーフ配置、アレンジメント）が Step 6 で捨てられる。事実上、v1 パイプラインが動作している。

**修正方針**: Sprint W5-6（Wave 1.4）で `RuleBasedNoteRealizerV2` を `src/yao/generators/note/rule_based_v2.py` に実装。`consumed_plan_fields` 宣言と AST scan で 80% 以上のフィールド消費を保証。

---

### Gap-3: ジャンル Skill（22 個）が生成パイプラインから参照されていない

**Tier**: 1 (致命的)
**対応する Wave**: Wave 2.1
**FEATURE_STATUS.md での主張**: ✅ Genre Skills (22) — "16 Western/electronic/classical + 4 world + 2 functional; world Skills have cultural_context"
**実装の実態**:

```bash
$ grep -r "skills/genres" src/
# (結果: 0 件)
```

22 個の `.claude/skills/genres/*.md` ファイルは存在するが、`src/` 配下の Python コードから一切 import も参照もされていない。テスト（`tests/unit/skills/test_genre_skills.py`）は YAML フロントマターの構造検証のみで、生成挙動への影響は未検証。

**影響**: 「ミュージシャンが Markdown を編集するだけで生成挙動を変えられる」という YaO の独自価値が未実現。ジャンル Skill の `chord_palette`, `typical_progressions`, `forbidden_cliches` 等が生成に反映されない。

**修正方針**: Wave 2.1 で `src/yao/skills/loader.py` に `SkillRegistry` を実装し、5 つの統合ポイント（SpecCompiler / HarmonyPlanner / DrumPatterner / Critique / PerformanceLayer）に接続。`make skill-grounding` で Skill 編集→出力変化を CI 検証。

---

### Gap-4: AnthropicAPIBackend が PythonOnly にサイレントフォールバック

**Tier**: 2 (重大)
**対応する Wave**: Wave 1.2
**FEATURE_STATUS.md での主張**: ✅ Backend-Agnostic Agent Protocol — "AnthropicAPIBackend + ClaudeCodeBackend (stubs with fallback)"
**実装の実態**:

```python
# src/yao/agents/anthropic_api_backend.py:27-28
def __init__(self) -> None:
    self._fallback = PythonOnlyBackend()

# src/yao/agents/anthropic_api_backend.py:46-51
logger.info(
    "anthropic_api_fallback",
    role=role.value,
    message="AnthropicAPIBackend not yet implemented, using PythonOnlyBackend.",
)
return self._fallback.invoke(role, context, config)
```

`YAO_AGENT_BACKEND=anthropic` を指定しても、ログメッセージを出力するだけで PythonOnly が動作する。`is_stub` 属性が定義されておらず、呼び出し側がスタブかどうかを判定できない。

**影響**: ユーザが LLM 統合を期待して設定しても、実際は PythonOnly が動作する。原則 3「No silent fallbacks」に違反。

**修正方針**: Sprint W3-4（Wave 1.2）で `anthropic` パッケージを使った本実装。API キー未設定時は `BackendNotConfiguredError` を発生させる（silent fallback 禁止）。

---

### Gap-5: ClaudeCodeBackend が PythonOnly にサイレントフォールバック

**Tier**: 2 (重大)
**対応する Wave**: Wave 1.2
**FEATURE_STATUS.md での主張**: ✅ Backend-Agnostic Agent Protocol（Gap-4 と同行）
**実装の実態**:

```python
# src/yao/agents/claude_code_backend.py:27-28
def __init__(self) -> None:
    self._fallback = PythonOnlyBackend()

# src/yao/agents/claude_code_backend.py:46-51
logger.info(
    "claude_code_fallback",
    role=role.value,
    message="ClaudeCodeBackend not yet implemented, using PythonOnlyBackend.",
)
return self._fallback.invoke(role, context, config)
```

AnthropicAPIBackend と同一パターン。`is_stub` 属性なし。

**影響**: Gap-4 と同様。LLM を使った対話的タスク（`/sketch` 多段対話、`/critique` 対話等）が実現不可能。

**修正方針**: Wave 1.2 で AnthropicAPIBackend と並行して整備。Claude Code SDK 経由のアダプタとして設計。

---

### Gap-6: SpecCompiler がキーワード辞書のみで日本語非対応

**Tier**: 2 (重大)
**対応する Wave**: Wave 1.3
**FEATURE_STATUS.md での主張**: ✅ SpecCompiler (NL → spec) — "Extracted from Conductor; mood → key, pace → tempo, explicit key regex"
**実装の実態**:

```python
# src/yao/sketch/compiler.py:30-54
_MOOD_TO_KEY: dict[str, str] = {
    "happy": "C major",
    "joyful": "D major",
    # ... 23 英語キーワードのみ。日本語ゼロ。
}
```

24 個の英語 mood キーワード、12 個のジャンルキーワード、10 個の楽器キーワードのハードコード辞書。LLM 統合なし。日本語入力は完全に無視される（`desc.lower()` で処理）。

**影響**: 「雨の夜のカフェで聴きたい少し切ない 90 秒のピアノ曲」のような豊かな意図が、ほぼ全て捨てられて `D minor / piano / 4 sections` に丸められる。YaO のエントリポイントとして致命的に貧弱。

**修正方針**: Sprint W4-5（Wave 1.3）で三段階フォールバック（LLM → Keyword → Default）を実装。日本語感情語彙 50+ を追加。

---

### Gap-7: DAW MCP Bridge がスタブ

**Tier**: 2 (重大)
**対応する Wave**: Wave 3+
**FEATURE_STATUS.md での主張**: ✅ DAW MCP integration — "MCPBridge stub; connect/push/pull interface; Reaper-first"
**実装の実態**:

```python
# src/yao/render/daw/mcp_bridge.py:38
"""Stub implementation. Full Reaper integration in future PR."""

# src/yao/render/daw/mcp_bridge.py:59-60
# Stub: always returns disconnected
self._status = MCPStatus(connected=False, daw_name=daw)

# src/yao/render/daw/mcp_bridge.py:79
return False  # push_score は常に失敗

# src/yao/render/daw/mcp_bridge.py:89
return None   # pull_changes は常に None
```

全メソッドがスタブ。テスト（4 件）もスタブ動作の確認のみ（`test_default_disconnected`, `test_connect_stub_returns_disconnected` 等）。

**影響**: DAW 連携が一切機能しない。ただし、MIDI / WAV 出力は正常に動作するため、ユーザは手動で DAW にインポート可能。影響は限定的。

**修正方針**: Wave 3+ の対象。FEATURE_STATUS.md の Notes 欄に既に "stub" と記載があるが、ステータスは ✅ のまま。🟡 にダウングレードすべき。

---

### Gap-8: Adversarial Critic の memorability ルールが空 MotifPlan で沈黙

**Tier**: 3 (軽微 — Gap-1 解消で自動的に解決)
**対応する Wave**: Wave 1.1（Gap-1 に依存）
**FEATURE_STATUS.md での主張**: ✅ Critique rules (19 total) — "15 original + 4 new (memorability: MotifAbsence, HookWeakness)"
**実装の実態**:

```python
# src/yao/verify/critique/memorability.py:24-35
def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
    """Check if motif plan has any seeds."""
    if plan.motif is None or len(plan.motif.seeds) == 0:
        return [
            Finding(
                rule_id=self.rule_id,
                severity=Severity.MINOR,
                role=self.role,
                issue="No motif seeds defined — composition may lack memorable themes.",
            )
        ]
    return []
```

`MotifAbsenceDetector` は空の MotifPlan に対して `Severity.MINOR` の Finding を返すが、これは非ブロッキング。Conductor は MINOR を無視して生成を続行する。結果として、全楽曲が「モチーフなし」の MINOR 警告付きで通過する。

**影響**: Gap-1 が解消されれば（MotifPlan が非空になれば）、この問題は自動的に解消する。Critic ルール自体のロジックは正しい。

**修正方針**: Gap-1（Wave 1.1）の解消に依存。追加修正は不要。

---

### Gap-9: StyleVector に melody/harmony 情報がない

**Tier**: 3 (軽微 — 設計上の意図だが、拡張が計画済み)
**対応する Wave**: Wave 3
**FEATURE_STATUS.md での主張**: ✅ references.yaml — "StyleVector (6 abstract features, no melody/chords)"
**実装の実態**:

StyleVector（`src/yao/perception/style_vector.py`）は 6 つの抽象的フィールド（`harmonic_rhythm`, `voice_leading_smoothness`, `rhythmic_density_per_bar`, `register_distribution`, `timbre_centroid_curve`, `motif_density`）のみ。melody contour や chord progression の情報は著作権配慮で意図的に除外されている。

**影響**: 参照楽曲とのスタイル比較が限定的。ジャンル間の差異が十分に捉えられない。ただし、これは著作権上の正当な設計判断であり、PROJECT.md §12.4 で histogram 系フィールド（`interval_class_histogram`, `chord_quality_histogram` 等）の追加が計画されている。

**修正方針**: Wave 3 で著作権セーフな histogram フィールドを追加。現ステータスは ✅ を維持（Notes に制約を明記済み）。

---

### Gap-10: Performance Expression IR / Realizers がパイプライン未統合

**Tier**: 3 (軽微 — 実装は完全だが接続なし)
**対応する Wave**: Wave 3
**FEATURE_STATUS.md での主張**: ✅ Performance Expression IR / ✅ Performance Realizers (4 subtypes)
**実装の実態**:

`src/yao/ir/expression.py` の NoteExpression / PerformanceLayer と、`src/yao/generators/performance/` 配下の 4 つの Realizer（ArticulationRealizer, DynamicsCurveRenderer, MicrotimingInjector, CCCurveGenerator）は全て実装済みでテストも通る。`pipeline.py` がこれらをマージする機能も実装されている。

しかし、`conductor.py` からこれらが一切 import/呼出されておらず、生成パイプラインの最終出力に Performance Layer が適用されない。

**影響**: 生成された楽曲にアーティキュレーション、ダイナミクスカーブ、マイクロタイミング、CC カーブが付与されない。音楽的には「平坦な演奏」になる。

**修正方針**: Wave 3（Performance Layer のパイプライン標準化）で conductor に統合。

---

### Gap-11: Reflection Layer (Style Profile) がパイプライン未統合

**Tier**: 3 (軽微 — データ層は動作、生成への反映なし)
**対応する Wave**: Wave 3
**FEATURE_STATUS.md での主張**: ✅ Reflection Layer (Style Profile) — "UserStyleProfile; StylePreference per dimension; save/load JSON; opt-in"
**実装の実態**:

`src/yao/reflect/style_profile.py` の UserStyleProfile は save/load JSON が動作し、テスト 5 件が通る。しかし conductor や生成器から参照されておらず、保存されたユーザ嗜好プロファイルが次回の生成パラメータに反映されない。

**影響**: Layer 7（Reflection & Learning）の学習ループが閉じていない。ユーザの主観評価が蓄積されても生成傾向に反映されない。

**修正方針**: Wave 3（Subjective rating CLI と style profile への反映）で統合。

---

## 3. 改善ロードマップへの反映

PROJECT.md §15 のロードマップとの対応関係:

| Gap | Tier | ロードマップ上の位置 | Sprint |
|-----|------|---------------------|--------|
| Gap-1: Composer 空 Plan | 1 | Wave 1, W2-3 | Sprint W2-3 |
| Gap-2: NoteRealizer v1 逆変換 | 1 | Wave 1, W5-6 | Sprint W5-6 |
| Gap-3: Genre Skill 未統合 | 1 | Wave 2, W9-11 | Sprint W9-11 |
| Gap-4: AnthropicAPI スタブ | 2 | Wave 1, W3-4 | Sprint W3-4 |
| Gap-5: ClaudeCode スタブ | 2 | Wave 1, W3-4 | Sprint W3-4 |
| Gap-6: SpecCompiler 貧弱 | 2 | Wave 1, W4-5 | Sprint W4-5 |
| Gap-7: DAW MCP スタブ | 2 | Wave 3+ | 未スケジュール |
| Gap-8: Critic 沈黙 | 3 | Wave 1, W2-3 (Gap-1 依存) | Gap-1 解消で自動解決 |
| Gap-9: StyleVector 限定 | 3 | Wave 3 | 未スケジュール |
| Gap-10: Performance IR/Realizers 未統合 | 3 | Wave 3 | 未スケジュール |
| Gap-11: Reflection Layer 未統合 | 3 | Wave 3 | 未スケジュール |

**Wave 1 で解消される Gap**: 1, 2, 4, 5, 6, 8（6 件）
**Wave 2 で解消される Gap**: 3（1 件）
**Wave 3 で解消される Gap**: 7, 9, 10, 11（4 件）

---

## 4. 監査の再実施スケジュール

### 月次 `make audit-monthly` で確認する項目

| チェック項目 | 確認方法 | 期待結果 |
|---|---|---|
| ✅ ステータスの正当性 | `make honesty-check` | 全 ✅ がスタブでないこと |
| MotifPlan の非空性 | `make critic-coverage` | Composer が seeds >= 1 を返すこと |
| NoteRealizer のフィールド消費率 | `make plan-consumption` | consumed_plan_fields >= 80% |
| Skill の生成統合 | `make skill-grounding` | Skill 編集で出力が変化すること |
| Backend の誠実性 | `make backend-honesty` | スタブが `is_stub=True` を返すこと |
| 新たな乖離の有無 | docs/audit/ への追記 | 未報告の乖離がないこと |

### スケジュール

- **2026-06**: Wave 1.1 完了後の中間監査（Gap-1, 8 の解消確認）
- **2026-07**: Wave 1 完了時の監査（Gap-1, 2, 4, 5, 6, 8 の解消確認）
- **2026-09**: Wave 2 完了時の監査（Gap-3 の解消確認）
- **2026-12**: Wave 3 完了時の最終監査（全 Gap の解消確認）

---

## 5. 教訓

### なぜ v2.0 で乖離が起きたか

1. **ステータスの定義が曖昧だった**: ✅ の基準が「テストがある」「形式的に動く」で十分とされ、「実機能が動作する」との区別がなかった。FEATURE_STATUS.md の Notes 欄に "stubs with fallback" と書かれていても、ステータスは ✅ のまま放置された（Gap-4, 5, 7）。

2. **パイプラインの接続テストがなかった**: 各モジュール単体のテストは存在するが、「Composer が生成した MotifPlan を NoteRealizer が消費する」という**端から端までの流れ**を検証するテストがなかった。そのため、Composer が空 Plan を返しても、NoteRealizer がそれを無視しても、テストは通過した。

3. **設計と実装の同時進行による楽観バイアス**: v2.0 では 8 層アーキテクチャの設計と基盤実装が同時に進み、「設計が存在する = 実装が完了に近い」という心理的錯覚が生まれた。ジャンル Skill 22 個の作成は成果に見えるが、生成器との接続がなければ無意味である。

4. **スタブの意図的な使用が長期化した**: `"Phase α stubs"`, `"Phase β will rewrite"` というコメントは、段階的開発の合理的な判断だった。しかし、Phase α の完了後にスタブが ✅ として残り続け、Phase β への移行が着手されなかった。

### 再発防止策

1. **原則 7「Status Honesty」の CI 強制**: `make honesty-check` でスタブ ✅ を機械的に検出。ステータス昇格は専用 PR + レビュー必須。

2. **層間契約テスト**: `tests/contracts/` に Plan completeness, Plan consumption, Skill grounding, Backend honesty のテストを配置。各層が「約束通りにデータを受け渡しているか」を検証。

3. **スタブの明示**: スタブ実装にはクラス名に `Stub` を含めるか、`is_stub = True` 属性を持たせる。これを `make backend-honesty` で強制。

4. **月次監査の制度化**: `make audit-monthly` を実行し、結果を `docs/audit/` に蓄積。過去の教訓を参照可能にする。

5. **Documentation Budget の遵守**: 設計文書 1 行あたり実働コード 3 行以上。設計だけが先行する状態を `tools/doc_drift_check.py` で検出。

---

## 付録: FEATURE_STATUS.md ダウングレード対象

本監査の結果、以下の項目を ✅ → 🟡 にダウングレードすることを勧告する:

| 項目 | 現ステータス | 推奨ステータス | limitation |
|---|---|---|---|
| 7 Subagent Python implementations | ✅ | 🟡 | Composer returns empty MotifPlan/PhrasePlan |
| Backend-Agnostic Agent Protocol | ✅ | 🟡 | AnthropicAPI/ClaudeCode are stubs with silent fallback, no is_stub attribute |
| SpecCompiler (NL → spec) | ✅ | 🟡 | Keyword-only (24 English words), no Japanese, no LLM |
| Genre Skills (22) | ✅ | 🟡 | Not integrated into generation pipeline (0 references from src/) |
| DAW MCP integration | ✅ | 🟡 | Stub: always disconnected, push/pull return False/None |

以下の項目は ✅ を維持するが、Notes の更新を勧告する:

| 項目 | 理由 |
|---|---|
| rule_based generator | v1 generator 自体は実装済み。NoteRealizer のアダプタ問題は Gap-2 で別管理 |
| stochastic generator | 同上 |
| Critique rules (19 total) | ルール自体は正しい。Gap-8 は Gap-1 の解消で自動解決 |
| references.yaml / StyleVector | 著作権配慮による意図的な制限。Wave 3 で拡張予定 |

---

**監査完了**: 2026-05-03
**次回監査予定**: 2026-06（Wave 1.1 完了後）
**本文書のバージョン**: 1.0
