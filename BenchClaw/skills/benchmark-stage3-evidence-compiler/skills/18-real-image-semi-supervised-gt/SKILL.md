# Node 18 — real-image-semi-supervised-gt

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## Role

Produce real-image records plus semi-supervised GT candidates with confidence, provenance, and audit reports.

This node must execute the full shared semi-supervised annotation chain for real-image data. It is not enough to register tools in node 27; every eligible real-image record must actually go through:

```text
input image
  |- YOLOE + LLM -> candidate semantic classes / detection boxes / SAM3 prompts
  |- SAM3 -> entity segmentation
  |- Depth Anything 3 -> depth map
  `- fuse segmentation + semantics + depth -> semantic/depth-aware entity segmentation candidates
```

## Parents

```text
24, 27
```

## May read

- `WORKSPACE_ROOT/stage3/24-real-image-data-juicer-cleaning/**`
- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/**`
- `schemas/semi_gt_record.schema.json`

## Must write

- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/semi_gt_manifest.jsonl`
- `WORKSPACE_ROOT/stage3/realdata/`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/annotations/`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/annotations/yoloe/`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/annotations/sam3/`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/annotations/depthanything3/`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/annotations/fused/`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/evidence/`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/conflict_report.md`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/quality_report.md`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/DONE.json`
- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/USED_INPUTS.json`

## Must not read

- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/**`
- `WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/**`

## 半监督 GT 规则

- YOLOE/检测器输出只能作为候选 box/class；
- SAM3 输出只能作为候选 mask；
- Depth Anything 3 输出默认是相对深度/深度排序候选，除非本地模型明确支持 metric depth；
- 小 VLM/LLM 只能做工具路由、候选解释、冲突说明，不能把纯文本判断写成最终 GT；
- 每个候选字段必须记录 `source_type`, `tool`, `tool_version`, `confidence`, `evidence`。

## 细节流程

对每张真实图片必须按以下半监督标注链路执行或记录失败原因：

1. 从 `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/tool_registry.json` 读取工具注册信息，工具 skill 路径必须来自 `BENCHCLAW_ROOT/annotation-tool/{yoloe,sam3,depthanything3,llm-local}/SKILL.md`。
2. 从样本 metadata、Stage1/Stage2 目标字段、模板证据需求或小 VLM/LLM 路由建议中确定候选类别词；小 VLM/LLM 只可产出 `routing_plan` 和 `candidate_terms`。
3. 调用 YOLOE，并在需要时结合小 VLM/LLM 的 `candidate_terms`/`routing_plan`，生成候选 `semantic_label`、`bbox_xyxy`、`class_score` 以及供 SAM3 使用的 prompt 信息，写入 `annotations/yoloe/{record_id}.json`。
4. 将 YOLOE/LLM 产出的候选框、点或其他允许的提示传给 SAM3，生成实体分割结果 `mask_path`、`mask_score`、`mask_area_px`，写入 `annotations/sam3/{record_id}.json`。
5. 对整张图调用 Depth Anything 3，生成深度图 `relative_depth_map_path` 或等价 depth artifact；再按 SAM3 mask 统计 `mean_depth`、`median_depth`、`min_depth`、`max_depth`、`depth_order_hint`，写入 `annotations/depthanything3/{record_id}.json`。
6. 对每个保留样本，必须在 `WORKSPACE_ROOT/stage3/realdata/<real_scene_or_source>/` 下全量落盘三类图像：
   - `original/`: 原图；
   - `semantic_entity_segmentation/`: 由 `YOLOE + LLM -> SAM3` 链路得到的语义实体分割图；
   - `depth/`: 由 Depth Anything 3 得到的深度图；
   同时将对应 GT/候选记录落盘到 `gt/`。
7. 以 `record_id + candidate_id` 对齐 YOLOE 语义/候选框、SAM3 实体分割和 Depth Anything 3 深度统计，生成“带语义/深度信息的实体分割结果” `object_instances_with_depth`，写入 `annotations/fused/{record_id}.json` 并追加到 `semi_gt_manifest.jsonl`。
8. 融合候选必须保留 `tool_chain`、`artifact_paths`、`quality_checks` 和全部证据路径；其中 `artifact_paths` 至少应能解析到 `original/`、`semantic_entity_segmentation/`、`depth/`、`gt/` 下的真实文件。任何缺失工具输出都不得补写，必须进入 `conflict_report.md` 或 `quality_report.md`。
9. 融合结果仍是 `tool_generated_candidate`，`is_final_gt` 必须为 `false`，不得覆盖人工标注或仿真器 privileged GT。

## Blocking Conditions

- 若 `annotations/yoloe/`、`annotations/sam3/`、`annotations/depthanything3/`、`annotations/fused/` 中缺少对应逐样本产物，则不得写 `DONE.json`。
- 若 real-image 分支没有对逐样本真实执行 `YOLOE(+LLM) -> SAM3 -> Depth Anything 3 -> 融合` 链路，而只是登记工具、写模板 JSON、健康检查结果或样例条目，则不得写 `DONE.json`。
- 若 `WORKSPACE_ROOT/stage3/realdata/<real_scene_or_source>/` 下未对保留样本全量落盘 `original/`、`semantic_entity_segmentation/`、`depth/` 三类图像及 `gt/`，则不得写 `DONE.json`。
- `semi_gt_manifest.jsonl` 中不得出现仅描述“expected pipeline”“pending tool output”“sample only”而没有真实 `artifact_paths` 的记录。
- 不允许仅凭候选条目模板、样例 JSON、健康检查结果或工具说明文档宣称 6201 张真实图像已经完成半监督处理。

## Completion

完成后必须写：

```json
{
  "node_id": "18",
  "status": "DONE",
  "output_dir": "WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt",
  "timestamp_utc": "<ISO-8601>"
}
```

并运行：

```bash
python scripts/check_used_inputs.py --node 18
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```
