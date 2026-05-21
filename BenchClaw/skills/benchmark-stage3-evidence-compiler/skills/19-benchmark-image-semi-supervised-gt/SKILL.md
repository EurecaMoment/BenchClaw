# Node 19 — benchmark-image-semi-supervised-gt

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## Role

Produce existing-benchmark image records plus official labels and semi-supervised GT candidates.

This node must execute the same shared semi-supervised annotation chain for existing-benchmark image data that node 18 uses for real-image data. Every eligible benchmark image must actually go through:

```text
input image
  |- YOLOE + LLM -> candidate semantic classes / detection boxes / SAM3 prompts
  |- SAM3 -> entity segmentation
  |- Depth Anything 3 -> depth map
  `- fuse segmentation + semantics + depth -> semantic/depth-aware entity segmentation candidates
```

## Parents

```text
25, 27
```

## May read

- `WORKSPACE_ROOT/stage3/25-benchmark-data-juicer-cleaning/**`
- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/**`
- `schemas/semi_gt_record.schema.json`

## Must write

- `WORKSPACE_ROOT/stage3/stage3.db`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/semi_gt_manifest.sqlite_export.jsonl`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/official_label_manifest.sqlite_export.jsonl`
- `WORKSPACE_ROOT/stage3/benchmarkdataset/`
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
3. 调用 YOLOE，并在需要时结合小 VLM/LLM 的 `candidate_terms`/`routing_plan`，生成候选 `semantic_label`、`bbox_xyxy`、`class_score` 以及供 SAM3 使用的 prompt 信息，写入 `annotations/yoloe/{record_id}.json`。
4. 将 YOLOE/LLM 产出的候选框、点或其他允许的提示传给 SAM3，生成实体分割结果 `mask_path`、`mask_score`、`mask_area_px`，写入 `annotations/sam3/{record_id}.json`。
5. 对整张图调用 Depth Anything 3，生成深度图 `relative_depth_map_path` 或等价 depth artifact；再按 SAM3 mask 统计 `mean_depth`、`median_depth`、`min_depth`、`max_depth`、`depth_order_hint`，写入 `annotations/depthanything3/{record_id}.json`。
6. 对每个保留样本，必须在 `WORKSPACE_ROOT/stage3/benchmarkdataset/<dataset_name>/<existing_dataset_split_or_category>/` 下全量落盘三类图像：
   - `original/`: 原图；
   - `semantic_entity_segmentation/`: 由 `YOLOE + LLM -> SAM3` 链路得到的语义实体分割图；
   - `depth/`: 由 Depth Anything 3 得到的深度图；
   同时将对应 GT/候选记录落盘到 `gt/`。
7. 以 `record_id + candidate_id` 对齐 YOLOE 语义/候选框、SAM3 实体分割和 Depth Anything 3 深度统计，生成“带语义/深度信息的实体分割结果” `object_instances_with_depth`，写入 `annotations/fused/{record_id}.json`，并把候选写入 `stage3.db.semi_gt_candidates`；如需导出清单，只能生成 `semi_gt_manifest.sqlite_export.jsonl` 兼容副本。
8. 与官方 label 冲突时，必须保留官方 label，并把工具候选写入 `conflict_report.md`；工具输出不得覆盖 `stage3.db.benchmark_label_records` 中的官方标签真相源；如需导出，只能生成 `official_label_manifest.sqlite_export.jsonl` 兼容副本。
9. 融合候选必须保留 `tool_chain`、`artifact_paths`、`quality_checks` 和全部证据路径；其中 `artifact_paths` 至少应能解析到 `original/`、`semantic_entity_segmentation/`、`depth/`、`gt/` 下的真实文件。融合结果仍是 `tool_generated_candidate`，`is_final_gt` 必须为 `false`，除非后续人工审核节点显式提升。

这里的“真实文件”不是只要求目录存在，而是要求每个保留样本逐样本拥有：

- 原图文件；
- 由 `YOLOE + LLM -> SAM3` 生成的语义实体分割图文件；
- 由 `Depth Anything 3` 生成的深度图文件；
- 对应 GT/融合候选文件；

且这些文件都必须通过 `artifact_paths` 与 `record_id + candidate_id` 回溯到具体样本。

数量上也必须闭合：凡是从 Stage2 node 16 被保留并流入 Stage3 的 benchmark 图像，都必须在本节点逐样本完成上述链路并产出四类文件。不得只处理其中一小部分样本后就写 `DONE.json`。

## Blocking Conditions

- 若 `annotations/yoloe/`、`annotations/sam3/`、`annotations/depthanything3/`、`annotations/fused/` 中缺少对应逐样本产物，则不得写 `DONE.json`。
- 若 benchmark image 分支没有对逐样本真实执行 `YOLOE(+LLM) -> SAM3 -> Depth Anything 3 -> 融合` 链路，而只是保留官方标签、写模板 JSON、健康检查结果或样例条目，则不得写 `DONE.json`。
- 若 `WORKSPACE_ROOT/stage3/benchmarkdataset/<dataset_name>/<existing_dataset_split_or_category>/` 下未对保留样本全量落盘 `original/`、`semantic_entity_segmentation/`、`depth/` 三类图像及 `gt/`，则不得写 `DONE.json`。
- 若 `stage3.db.semi_gt_candidates` 中完成闭环的 `record_id` 数量少于 Stage2 node 16 流入 Stage3 的保留 benchmark 图像数量，则不得写 `DONE.json`。
- `stage3.db.semi_gt_candidates` 中不得以 `pending`、`planned`、`to_be_generated` 或样例条目替代真实工具输出记录。
- 不允许只保留官方 label 和增强计划说明，就宣称已有 benchmark 图像的半监督增强已完成。

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

注意：本节点写出 `DONE.json` 不代表 Stage3 真正完成。只有当 `scripts/check_stage3_outputs.py` 生成的 `WORKSPACE_ROOT/stage3/STAGE3_VALIDATION_REPORT.json` 与 `.md` 明确证明 benchmarkdataset 分支数量闭合、逐样本四类产物闭合时，本节点产物才算有效完成。
