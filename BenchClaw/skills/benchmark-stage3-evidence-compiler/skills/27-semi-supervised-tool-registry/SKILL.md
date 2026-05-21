# Node 27 — semi-supervised-tool-registry

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## Role

Register semi-supervised annotation tools such as YOLOE, SAM3, Depth Anything 3, and small VLM/LLM routers with explicit output contracts.

For tools exposed as local services, this node must register how to attach to already-running localhost endpoints; it must not treat service startup or redeployment as part of Stage3 normal workflow.

This node also defines the shared semi-supervised annotation chain contract that nodes 18 and 19 must execute on images:

```text
input image
  |- YOLOE + LLM -> candidate semantic classes / detection boxes / SAM3 prompts
  |- SAM3 -> entity masks from YOLOE/LLM prompts
  |- Depth Anything 3 -> full-image depth map
  `- fuse masks + semantics + depth -> semantic/depth-aware entity segmentation candidates
```

Important: node 27 registers the tools, endpoints, health checks, and I/O contracts for this chain, but it does not itself perform per-image annotation. Actual execution for real-image data must happen in node 18, and actual execution for existing-benchmark image data must happen in node 19.

This shared chain is mandatory, not optional, for every non-simulator image collected by Stage2. In other words: except for simulator data handled by node 20, all image-bearing records produced by Stage2 node 15 and Stage2 node 16 must pass through this fixed chain before they can be treated as Stage3-ready GT candidates.

## Parents

```text
(none)
```

## May read

- `BENCHCLAW_ROOT/annotation-tool/**`

## Must write

- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/tool_registry.json`
- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/annotation_tool_contracts.json`
- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/tool_probe_report.md`
- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/fixed_chain_runner_contract.md`
- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/DONE.json`
- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/USED_INPUTS.json`

## Must not read

- `(none)`

## 工具注册范围

至少尝试发现/登记以下能力类别：

- detection：YOLOE，skill 路径为 `BENCHCLAW_ROOT/annotation-tool/yoloe/SKILL.md`；
- segmentation：SAM3，skill 路径为 `BENCHCLAW_ROOT/annotation-tool/sam3/SKILL.md`；
- depth：Depth Anything 3，skill 路径为 `BENCHCLAW_ROOT/annotation-tool/depthanything3/SKILL.md`；
- router：本地小 VLM/LLM，skill 路径为 `BENCHCLAW_ROOT/annotation-tool/llm-local/SKILL.md`。

登记失败也要写入 `tool_probe_report.md`，不能伪造工具可用性。

若工具 skill 明示了本地 endpoint，注册信息中应优先记录该 endpoint 与健康检查方式，而不是“自动启动工具服务”的步骤。

## 共享半监督链路契约

`tool_registry.json` 与 `annotation_tool_contracts.json` 必须足以支撑 18/19 两个节点执行以下共享链路：

1. 对输入图像，YOLOE 在 LLM 产生或路由的 `candidate_terms` 支持下输出候选 `semantic_label`、`bbox_xyxy`、`class_score`，并在需要时输出 SAM3 可消费的 mask/box/point prompts。
2. SAM3 必须消费 YOLOE/LLM 提供的候选框、点或文本相关提示，输出实体级分割结果：至少包含 `mask_path` 或等价 mask 表示、`mask_score`、`mask_area_px`。
3. Depth Anything 3 必须对整张图输出深度图；若模型不提供 metric depth，至少输出可用于排序和区域统计的 depth map。
4. 融合阶段必须按 `record_id + candidate_id` 对齐 YOLOE 语义/候选框、SAM3 实体分割、Depth Anything 3 深度图，生成“带语义/深度信息的实体分割结果”，即 `object_instances_with_depth` 或等价结构。
5. 上述链路必须同时适用于 real-image 分支和 existing-benchmark image 分支；不得只为其中一个分支登记工具契约。
6. 若某工具不可用、endpoint 不健康、I/O 契约不闭合或无法支撑上述融合结果，27 必须阻塞并在 `tool_probe_report.md` 中写明缺口，而不是把不完整链路交给 18/19。
7. 这条链路的目标不是“做一个候选标签演示”，而是尽可能把非仿真器图像推进到接近 simulator 分支可消费程度的证据形态：至少要产出可追溯的 GT 候选记录、深度图、语义实体分割图，以及它们之间可对齐的融合结果。
8. 27 必须把上述链路落成一个可执行参考入口，并在 contract 中显式引用 `scripts/run_fixed_semi_supervised_chain.py`，使 18/19 不需要根据抽象文字自行猜测 `original/`、`semantic_entity_segmentation/`、`depth/`、`gt/` 以及 `artifact_paths` 的组织方式。

## 非仿真器图像的强制处理范围

对来自 Stage2 的非仿真器图像，本节点必须把处理范围定义为全覆盖，而不是样例覆盖：

1. `WORKSPACE_ROOT/stage2/15-real-image-acquisition/realdata/**` 中被保留进入 Stage3 的全部图像，必须经过 `LLM/YOLOE -> SAM3 -> Depth Anything 3 -> 融合` 的固定链路。
2. `WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/benchmarkdataset/**` 中被保留进入 Stage3 的全部图像，必须经过同一条固定链路。
3. 不允许把上述处理降级为“只对一小部分图像跑半监督链路，再把其余图像留空或沿用占位字段”。
4. 若 realdata 或 benchmarkdataset 分支中的某批图像未经过该固定链路，则这些图像不得被宣称已经具备与 simulator 分支相媲美的 GT、深度图或语义实体分割图准备度。

## 可执行参考入口

27 必须在 `annotation_tool_contracts.json` 与 `fixed_chain_runner_contract.md` 中明确引用以下可执行参考脚本：

```text
scripts/run_fixed_semi_supervised_chain.py
```

该脚本的职责是把以下固定链路接口写清楚并稳定落盘：

1. 输入：原图、LLM 输出、YOLOE 输出、SAM3 输出、Depth Anything 3 输出；
2. 产物：
   - `original/` 原图；
   - `semantic_entity_segmentation/` 由 `YOLOE + LLM -> SAM3` 得到的语义实体分割图；
   - `depth/` 由 `Depth Anything 3` 得到的深度图；
   - `gt/` 带 `source_type`、`tool_chain`、`artifact_paths`、`quality_checks` 的 GT 候选或融合记录；
3. SQLite 映射：把上述四类产物通过 `artifact_paths` 写入 `stage3.db.semi_gt_candidates`；如需导出 `semi_gt_manifest`，只能生成 `sqlite_export` 兼容副本。

27 自身不执行逐图推理，但必须把 18/19 所需的可执行参考脚本路径、输入参数语义、以及输出文件组织方式写进 contract，避免实现方把固定链路理解成仅输出抽象 JSON 说明。

## 与 simulator 分支的对齐目标

本节点定义的非仿真器固定链路，目标是让 realdata 与 benchmarkdataset 分支尽可能逼近 simulator 分支的证据形态，而不是停留在弱标签层面。对每个最终保留样本，18/19 必须至少能够产出：

1. 原图 `original/`；
2. 由 `YOLOE + LLM -> SAM3` 得到的语义实体分割图 `semantic_entity_segmentation/`；
3. 由 `Depth Anything 3` 得到的深度图 `depth/`；
4. 带 `source_type`、`tool_chain`、`artifact_paths`、`quality_checks` 的 GT 候选或融合记录 `gt/`。

这并不意味着非仿真器分支可以伪造 simulator privileged GT；它的含义是：非仿真器分支必须把可获得的图像证据、分割证据、深度证据与融合结果全部实跑并落盘，尽可能形成可与 simulator 分支并列消费的结构化证据集。Stage3 最终目录树与各分支落盘要求由 Stage3 根 skill 以及 18/19/20 各自节点负责定义和执行，27 不代替这些终端节点声明最终产物树。

## Blocking Conditions

27 还必须把以下情况定义为阻塞，而不是“后面节点自己想办法”：

1. 只登记了 YOLOE/SAM3/Depth Anything 3 的名字，但没有形成可闭合的固定链路 I/O 契约；
2. 没有把 non-simulator 图像的全覆盖处理要求写进 contract；
3. 工具可用性无法支撑“原图 -> 语义实体分割图 -> 深度图 -> 融合 GT 候选”这一整条固定链路；
4. 任何试图把 non-simulator 图像降级成只保留原图、只保留文本候选、只保留样例条目、或只保留部分融合结果的方案。
5. 没有把固定链路的可执行参考入口 `scripts/run_fixed_semi_supervised_chain.py` 写入 contract，导致 18/19 只能依赖抽象描述自行猜测落盘组织方式的情况。

## Completion

完成后必须写：

```json
{
  "node_id": "27",
  "status": "DONE",
  "output_dir": "WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry",
  "timestamp_utc": "<ISO-8601>"
}
```

并运行：

```bash
python scripts/check_used_inputs.py --node 27
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```
