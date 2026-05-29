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

- `WORKSPACE_ROOT/stage3/<node>/manifest.jsonl`
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

本节点**禁止自行编排**半监督标注调用。所有 real-image 样本必须通过统一的标准脚本执行：

```text
BENCHCLAW_ROOT/skills/benchmark-stage3-evidence-compiler/scripts/run_semi_supervised_annotation.py
```

- 运行环境必须是 `conda activate sam3`（该环境已包含调用四个本地服务所需依赖）。
- 该脚本封装了固定链路 `VLM/LLM 候选词 -> YOLOE 验证 -> SAM3 实体分割 -> Depth Anything 3 深度`，并在 out-dir 下产出 `result.json` + `semantic_entity_segmentation.png` + `depth_map.png` + `da3_export/`。
- 必须同时传入 `--workspace-root` `--branch realdata` `--group-name <real_scene_or_source>` `--record-id <record_id>`，由脚本把样本自动落进 Stage3 四件套目录树、追加 `semi_gt_manifest.jsonl`、写入 `semi_gt_manifest.jsonl`。如果忽略这些参数，本节点会因为 contract 未闭合而被 checker 判失败。
- 调用方式（每张图）：

  ```bash
  conda activate sam3
  python BENCHCLAW_ROOT/skills/benchmark-stage3-evidence-compiler/scripts/run_semi_supervised_annotation.py \
    --image <ABS_IMAGE_PATH> \
    --out-dir WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/scratch/<record_id> \
    --workspace-root WORKSPACE_ROOT \
    --branch realdata \
    --group-name <real_scene_or_source> \
    --record-id <record_id>
  ```

对每张真实图片必须按以下步骤执行：

1. 从 `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/tool_registry.json` 读取工具注册与端口健康状态；4 个服务必须 healthy，否则本节点必须阻塞。
2. 对节点 24 输出的每条保留 record，调用上述脚本一次。`--out-dir` 用于该样本的脚本工作目录（如 `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/scratch/<record_id>/`），脚本会另外按 contract 在 `WORKSPACE_ROOT/stage3/realdata/<real_scene_or_source>/<record_id>/` 下落四件套。
3. 标准脚本会在 out-dir 下生成 `result.json`（含 `instances[*]` 的 `semantic_label` + `segmentation` + `depth` 四件套）、`semantic_entity_segmentation.png`、`depth_map.png`、`da3_export/`。本节点必须把这些产物原样保留，**不得用模板 JSON、占位或样例 JSON 替代**。
4. 把脚本产出的逐样本制品归档到本节点目录：
   - `annotations/yoloe/{record_id}.json`、`annotations/sam3/{record_id}.json`、`annotations/depthanything3/{record_id}.json`、`annotations/fused/{record_id}.json`：均从该样本 `result.json` 中抽取对应工具部分写出，原始合并 JSON 也保留在 `evidence/{record_id}.result.json`。
   - 同时把该样本 `result.json` 内的 `instances[*]` 候选写入 `semi_gt_manifest.jsonl`，每条候选的 `artifact_paths` 必须解析到该样本目录下的 `original/`、`semantic_entity_segmentation/`、`depth/`、`gt/` 真实文件；如需导出清单，只能生成 `semi_gt_manifest.jsonl` 兼容副本。
5. 候选的 `source_type` 固定为 `tool_generated_candidate`、`is_final_gt=false`，不得覆盖人工标注或仿真器 privileged GT。任何缺失工具输出都必须进入 `conflict_report.md` 或 `quality_report.md`，而不是补造数据。

这里的“真实文件”不是只要求目录存在，而是要求每个保留样本逐样本拥有：

- 原图文件；
- 由 `YOLOE + LLM -> SAM3` 生成的语义实体分割图文件；
- 由 `Depth Anything 3` 生成的深度图文件；
- 对应 GT/融合候选文件；

且这些文件都必须通过 `artifact_paths` 与 `record_id + candidate_id` 回溯到具体样本。

数量上也必须闭合：凡是从 Stage2 node 15 被保留并流入 Stage3 的真实图像，都必须在本节点逐样本完成上述链路并产出四类文件。不得只处理其中一小部分样本后就写 `DONE.json`。

## Blocking Conditions

- 若没有通过 `BENCHCLAW_ROOT/skills/benchmark-stage3-evidence-compiler/scripts/run_semi_supervised_annotation.py` 真实执行，而是手写或拼装 JSON，则不得写 `DONE.json`。
- 脚本必须在 `conda activate sam3` 环境下运行；本节点不得使用其它环境冒充。
- 若 `annotations/yoloe/`、`annotations/sam3/`、`annotations/depthanything3/`、`annotations/fused/` 中缺少对应逐样本产物，则不得写 `DONE.json`。
- 若 `WORKSPACE_ROOT/stage3/realdata/<real_scene_or_source>/<record_id>/` 下未对保留样本全量落盘 `original/`、`semantic_entity_segmentation/`、`depth/` 三类图像及 `gt/`，则不得写 `DONE.json`。
- 若 `semi_gt_manifest.jsonl` 中完成闭环的 `record_id` 数量少于 Stage2 node 15 流入 Stage3 的保留真实图像数量，则不得写 `DONE.json`。
- `semi_gt_manifest.jsonl` 中不得出现仅描述"expected pipeline"、"pending tool output"、"sample only"而没有真实 `artifact_paths` 的记录。
- 不允许仅凭候选条目模板、样例 JSON、健康检查结果或工具说明文档宣称真实图像已经完成半监督处理。

## Completion

完成后必须写：

```json
{
  "node_id": "18",
  "status": "done",
  "output_dir": "WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt",
  "timestamp_utc": "<ISO-8601>"
}
```

并运行：

```bash
python scripts/check_used_inputs.py --node 18
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```

注意：本节点写出 `DONE.json` 不代表 Stage3 真正完成。只有当 `scripts/check_stage3_outputs.py` 生成的 `WORKSPACE_ROOT/stage3/STAGE3_VALIDATION_REPORT.json` 与 `.md` 明确证明 realdata 分支数量闭合、逐样本四类产物闭合时，本节点产物才算有效完成。
