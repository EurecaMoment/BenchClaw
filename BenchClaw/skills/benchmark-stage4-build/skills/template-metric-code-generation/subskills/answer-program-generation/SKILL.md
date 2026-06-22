---
name: benchclaw-stage4-answer-program-generation
description: Use for the specific BenchClaw subskill `stage4-answer-program-generation` only when its parent node explicitly dispatches to it.
---

# Subskill — 答案程序生成

## 目标

为每个 enabled 模板生成可运行的答案程序和批量合成代码，使 `grey-batch-validation` 能直接从 `data_20_template_metric_code_bundle` 生成小批量 item、验证标准答案、运行评分脚本并追溯每道题的证据来源。

本 subskill 必须把 GT 链式支撑写进答案程序：不仅能算出 gold answer，还要能返回紧凑、可审计的 `compute_reasoning_chain()` 结果，证明题目为何可回答、为何唯一、为何不依赖隐藏 GT 泄漏。

## 输入

- `templates/<template_id>.json`
- `metrics/<metric_id>.json`
- `selected_template_sources.jsonl`
- `metric_manifest.jsonl`
- `source_inventory.jsonl`
- `field_catalog.yaml`
- `evidence_index.jsonl`
- `gt_kinship/gt_distant_reasoning_chains.jsonl`
- 本 stage `templates/benchmark_item.schema.json`
- 本 skill `reference_library/answer_type_metric_registry.json`、`reference_library/template_family_registry.yaml` 和 `schema_patch_notes.md`
- `WORKSPACE_ROOT/path_resolution.json`

## 每模板答案程序接口

每个 `answer_programs/<template_id>.py` 必须暴露：

```python
TEMPLATE_ID = "<template_id>"

def supports(record, template_config):
    """Return (ok: bool, reason: str)."""

def build_item(record, template_config, *, rng=None, item_index=0):
    """Return a benchmark item dict compatible with benchmark_item.schema.json."""

def compute_answer(record, template_config):
    """Return the gold answer derived from GT/evidence."""

def evidence_refs(record, template_config):
    """Return stable evidence references used by this item."""

def compute_reasoning_chain(record, template_config):
    """
    Return an auditable, compact evidence reasoning chain.
    This is for benchmark auditing and answer derivation, not for forcing the
    evaluated model to reveal private chain-of-thought.
    """
```

`compute_reasoning_chain` 返回结构至少为：

```python
{
  "chain_id": "...",
  "hops": [
    {
      "hop_id": 1,
      "operation": "...",
      "input_evidence_refs": [],
      "output": "...",
      "verifiable": True
    }
  ],
  "final_answer": "...",
  "answerability_proof": {}
}
```

## `supports(record, template_config)` 新增硬约束

`supports` 必须检查：

- `record` 是否包含 `reasoning_chain_plan` 所需所有 GT
- 所有 `media_refs` 是否存在
- 每个 reasoning hop 是否可执行
- 最终答案是否唯一
- 题干是否不需要隐藏 GT 直接暴露
- 干扰项是否能构造
- 视觉可见性是否满足

任一失败都必须返回 `False`，并给出具体原因。

## `build_item` 新增字段

生成 item 时，必须新增或填充：

```json
{
  "answer_derivation": "...",
  "metadata": {
    "chain_id": "...",
    "reasoning_hop_count": 3,
    "gt_distance_level": "far",
    "reasoning_depth_score": 0.0,
    "gt_distance_score": 0.0,
    "human_language_quality": "PASS"
  }
}
```

注意：

- `answer_derivation` 是给 gold/audit 使用的简洁解释，不是要求被评测模型输出完整思维链。
- `metadata.chain_id` 必须与模板 `reasoning_chain_plan.chain_id` 一致。

媒体路径硬约束：

- `build_item` 写出的 `media` 必须是可直接访问的本地绝对路径。
- 所有 `media` 路径必须位于当前 `WORKSPACE_ROOT` 内；禁止继续输出 `stage3/...`、`../...`、裸相对路径，或指向其他 workspace 的绝对路径。
- 如果上游 evidence 只提供相对路径，答案程序必须先基于当前 `WORKSPACE_ROOT` 完成路径解析与规范化，再写入 item。
- 如果原始媒体不在当前 workspace 内，必须先复制或链接到当前 workspace 内稳定目录，再把该 workspace 内绝对路径写入 `media`。
- 多图题的 `media` 数组中每个元素都必须满足以上要求。
- 当启用 GT 图片标识处理时，item 还必须保留原始作图输入列。推荐保持：
  - `source_media`：原图绝对路径数组；
  - `media`：最终给模型作答使用的处理图绝对路径数组，可能是 overlay 图，也可能是在 GT 不足时回退到原图。
- 对需要对象指称消歧的题，答案程序或其下游 helper 必须把 label ↔ object_id ↔ GT evidence 的映射落到 sidecar 映射文件，并把映射路径写回 item 的 `metadata`。

## 题干自然语言约束

`build_item` 生成题干时必须符合：

- 像真人会问的问题
- 不暴露字段名和隐藏 GT 术语
- 不出现 `object_id`、`bbox`、`depth_median`、`json`、`metadata`、`annotation`、`privileged` 等 forbidden terms
- 多跳题干可以更长，但不能机械列步骤
- 默认 1 到 3 句话

示例导向：

- 好：`画面中更靠近桌子边缘的物体是哪一个？`
- 坏：`根据 object_id 判断 target_object 的 depth_median 是否大于 distractor_object。`

## 批量合成入口新增过滤参数

`scripts/generate_items.py` 必须支持：

```bash
--min-reasoning-hops 3
--min-gt-distance-level far
--depth-role high_depth
```

并且无论模板程序返回什么形式的媒体引用，`generate_items.py` 在落盘 `benchmark_items.jsonl`、`generated_items.jsonl` 或其他 item jsonl 前，都必须执行一次统一路径规范化，保证最终 item 的 `media` 字段只包含当前 `WORKSPACE_ROOT` 内的本地绝对路径。

若启用了 visual marker：

- `generate_items.py` 必须在“候选对象已确定、题干最终落盘之前”调用 GT 标识处理。
- 处理后若题干要求引用 label，则题干、答案、解析、评分和映射文件必须共用同一套 label-object 对应关系。
- 标识失败且题目又依赖 label 时，该样本必须进入 `filtered_items.jsonl` 或被显式降级，不能静默输出不可审计题。

并把被过滤样本写入 `filtered_items.jsonl`，每条至少包含：

```json
{
  "template_id": "...",
  "chain_id": "...",
  "source_sample_id": "...",
  "reason": "answer_not_unique | missing_gt_node | media_missing | reasoning_hops_failed | question_not_natural | distractor_not_available | gt_too_near"
}
```

## 失败与阻塞

以下情况必须向主节点报告阻塞：

- enabled 模板无法生成 `compute_reasoning_chain`
- 无法证明唯一答案
- 题干自然语言约束无法满足
- 只有隐藏 GT 泄漏才能把链走通
- `generate_items.py` 无法按 `min_reasoning_hops` / `min_gt_distance_level` / `depth_role` 过滤
