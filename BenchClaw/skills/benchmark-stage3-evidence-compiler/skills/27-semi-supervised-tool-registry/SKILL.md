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
