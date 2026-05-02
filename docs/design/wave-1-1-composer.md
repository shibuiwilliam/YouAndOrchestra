# Wave 1.1: Composer Subagent 本実装 — 設計ドキュメント

> **Status**: 実装完了 (2026-05-03)
> **Files**: `motif_generation.py`, `motif_placement.py`, `composer.py`
> **Audit ref**: docs/audit/2026-05-status-reaudit.md Gap-1

---

## 1. 概要

Composer Subagent は v2.0 以来 `MotifPlan(seeds=[], placements=[])` を返す
スタブだった。Wave 1.1 でこれを本実装に置き換え、以下を保証する:

- `len(MotifPlan.seeds) >= 1` (空 Plan 禁止)
- 各 motif が 3 回以上配置される (MotifRecurrenceDetector 閾値と一致)
- identity_strength の根拠が Provenance に記録される

---

## 2. 2 段階生成フロー

```
AgentContext
├── intent (IntentSpec)      ─┐
├── form_plan (SongFormPlan)  ├──► Stage A: Motif Generation
├── spec.generation.seed      │      │
│                              │      ├── _derive_character(intent)
│                              │      │     └── keywords → direction + rhythm template
│                              │      ├── _generate_interval_sequence(bigram, direction)
│                              │      │     └── Markov chain with directional bias
│                              │      └── _compute_identity_strength(rhythm, intervals)
│                              │            └── rhythm_specificity * 0.4 + interval_specificity * 0.6
│                              │
│                              └──► Stage B: Motif Placement
│                                     │
│                                     ├── Origin placement (IDENTITY, beat 0 of origin section)
│                                     ├── Priority section walk (chorus > verse > outro > bridge)
│                                     ├── Transform selection (section.role → MotifTransform)
│                                     ├── Transposition from tension (>= 0.8 → +2, >= 0.6 → +1)
│                                     └── Guarantee: len(placements) >= min_recurrences (3)
│
└──► PhrasePlan generation
       └── Section walk → antecedent/consequent pairs
           with contour/cadence from tension targets
```

---

## 3. Motif Generation アルゴリズム

### 3.1 入力

| 入力 | 用途 |
|------|------|
| `IntentSpec.keywords` | motif character (direction, rhythm style) を決定 |
| `IntentSpec.text` | keywords が空の場合のフォールバック |
| `SongFormPlan.sections` | motif 数を form 複雑度から決定 (1-3) |
| `spec.generation.seed` | 再現性のための乱数シード |

### 3.2 Motif 数の決定

```
sections <= 2  → 1 motif
sections <= 4  → 2 motifs
sections >= 5  → min(3, sections // 2)
```

### 3.3 rhythm_shape の生成

8 種類の rhythm テンプレートから intent character に基づいて選択:

| Character | Template | Beats |
|-----------|----------|-------|
| calm/gentle | lyrical_long | (2.0, 1.0, 1.0) |
| energetic | syncopated | (0.5, 1.0, 0.5, 1.0, 1.0) |
| epic/heroic | punchy | (0.5, 0.5, 1.0, 0.5, 0.5, 1.0) |
| dreamy | slow_ballad | (2.0, 2.0) |
| default | even_quarter | (1.0, 1.0, 1.0, 1.0) |

Secondary motifs は対比のため別テンプレートを選択。

### 3.4 interval_shape の生成 (Markov bigram 再利用)

`markov_models/diatonic_bigram.yaml` のスケール度数遷移確率に
方向バイアスを適用:

- **ascending**: 上方遷移の確率を 1.5 倍
- **descending**: 下方遷移の確率を 1.5 倍
- **stepwise**: 隣接度数の確率を 2.0 倍
- **wide**: 3 度以上離れた遷移を 1.8 倍

生成されたスケール度数列をメジャースケールのセミトーン値に変換。

### 3.5 identity_strength の計算

```
rhythm_specificity = CV(durations)  # 係数変動 (0-1)
interval_specificity = (unique_ratio * 0.5) + (range_ratio * 0.5)
identity_strength = rhythm_spec * 0.4 + interval_spec * 0.6
```

---

## 4. Motif Placement 戦略

### 4.1 セクション Role → Transform マッピング

| Role | Preferred Transforms |
|------|---------------------|
| verse | IDENTITY, SEQUENCE_UP |
| chorus | IDENTITY, SEQUENCE_UP, SEQUENCE_DOWN |
| bridge | INVERSION, VARIED_INTERVALS |
| outro | AUGMENTATION, IDENTITY |
| intro | IDENTITY, AUGMENTATION |

### 4.2 3 回保証ロジック

1. Origin section に IDENTITY で 1 回配置
2. Priority 順 (chorus > verse > outro > bridge > ...) に候補 section を走査
3. `len(placements) >= min_recurrences + 1` まで配置
4. まだ足りない場合、既存 section の後半位置に追加配置

### 4.3 Transposition

`section.target_tension >= 0.8` → +2 semitones (climax)
`section.target_tension >= 0.6` → +1 semitone (building)

---

## 5. 失敗ケースの扱い

| ケース | 対応 |
|--------|------|
| form_plan が None | spec.total_bars から単一 verse セクションを生成 |
| intent が空 | DEFAULT_CHARACTER (mixed direction, even_quarter) を使用 |
| section が 1 つだけ | 同一 section 内に複数回配置 (位置をずらす) |
| melody 楽器なし | motif 生成自体は楽器非依存 (NoteRealizer が解決) |

---

## 6. テスト戦略

### Unit tests (tests/unit/subagents/test_composer.py)

- `test_motif_seeds_never_empty` — 核心契約
- `test_each_motif_placed_at_least_3_times` — recurrence 閾値
- `test_motif_seeds_have_valid_rhythm` — 正のデュレーション
- `test_motif_seeds_have_valid_intervals` — 長さ一致
- `test_phrase_plan_covers_all_sections` — 全 section カバー
- `test_provenance_records_identity_strength` — Provenance 記録
- `test_deterministic_with_same_seed` — 再現性
- `test_empty_intent_still_produces_seeds` — 空入力耐性
- `test_single_section_produces_seeds` — 最小構造
- `test_many_sections_produces_multiple_motifs` — 複雑構造
- `test_different_keywords_produce_different_motifs` — intent 反映

### Integration test (tests/integration/test_motif_recurrence.py)

- `test_critic_detects_recurrence_with_real_composer` — Composer → Critic フロー
- `test_no_silent_pass_on_non_empty_plan` — MotifAbsenceDetector が沈黙しない

---

## 7. Vertical Alignment

- **Input**: △ (intent keywords → motif character 推論)
- **Processing**: ✅ (motif 生成 + 配置の本実装)
- **Evaluation**: ✅ (MotifRecurrenceDetector が機能するようになる)
