# Node 27 — semi-supervised-tool-registry

## Role

Register semi-supervised annotation tools such as YOLOE, SAM3, Depth Anything 3, and small VLM/LLM routers with explicit output contracts.

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
