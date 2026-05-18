# Node 19 — benchmark-image-semi-supervised-gt

## Role

Produce existing-benchmark image records plus official labels and semi-supervised GT candidates.

## Parents

```text
25, 27
```

## May read

- `WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/**`
- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/**`
- `schemas/semi_gt_record.schema.json`

## Must write

- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/semi_gt_manifest.jsonl`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/official_label_manifest.jsonl`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/annotations/`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/annotations/yoloe/`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/annotations/sam3/`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/annotations/depthanything3/`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/annotations/fused/`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/evidence/`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/conflict_report.md`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/quality_report.md`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/DONE.json`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/USED_INPUTS.json`

## Must not read

- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/**`
- `WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/**`

## 半监督 GT 规则

- YOLOE/检测器输出只能作为候选 box/class；
- SAM3 输出只能作为候选 mask；
- Depth Anything 3 输出默认是相对深度/深度排序候选，除非本地模型明确支持 metric depth；
- 小 VLM/LLM 只能做工具路由、候选解释、冲突说明，不能把纯文本判断写成最终 GT；
- 每个候选字段必须记录 `source_type`, `tool`, `tool_version`, `confidence`, `evidence`。

## 细节流程

对每张已有 benchmark 图像必须按以下半监督标注链路执行或记录失败原因：

1. 从 `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/tool_registry.json` 读取工具注册信息，工具 skill 路径必须来自 `BENCHCLAW_ROOT/annotation-tool/{yoloe,sam3,depthanything3,llm-local}/SKILL.md`。
2. 优先从官方 label/QA/metadata 中抽取候选类别词；不足时才允许小 VLM/LLM 产出 `routing_plan` 和 `candidate_terms`，且这些文本建议不能成为 GT。
3. 调用 YOLOE 生成候选 `semantic_label`、`bbox_xyxy`、`class_score`，写入 `annotations/yoloe/{record_id}.json`。
4. 将 YOLOE 的候选框或点提示传给 SAM3，生成候选 `mask_path`、`mask_score`、`mask_area_px`，写入 `annotations/sam3/{record_id}.json`。
5. 对整张图调用 Depth Anything 3，生成 `relative_depth_map_path`；再按 SAM3 mask 统计 `mean_depth`、`median_depth`、`min_depth`、`max_depth`、`depth_order_hint`，写入 `annotations/depthanything3/{record_id}.json`。
6. 以 `record_id + candidate_id` 对齐 YOLOE box/class、SAM3 mask 和 Depth Anything 3 深度统计，生成融合候选 `object_instances_with_depth`，写入 `annotations/fused/{record_id}.json` 并追加到 `semi_gt_manifest.jsonl`。
7. 与官方 label 冲突时，必须保留官方 label，并把工具候选写入 `conflict_report.md`；工具输出不得覆盖 `official_label_manifest.jsonl`。
8. 融合候选必须保留 `tool_chain`、`artifact_paths`、`quality_checks` 和全部证据路径；融合结果仍是 `tool_generated_candidate`，`is_final_gt` 必须为 `false`，除非后续人工审核节点显式提升。

## Completion

完成后必须写：

```json
{
  "node_id": "19",
  "status": "DONE",
  "output_dir": "WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt",
  "timestamp_utc": "<ISO-8601>"
}
```

并运行：

```bash
python scripts/check_used_inputs.py --node 19
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```
