# Skill 35 — 质量过滤与选择策略

## 父节点

`31`, `32`, `34`

## 任务

在灰度测试留空的前提下，只实现 **不依赖 pilot/model-response 的结构性过滤**，并输出后续可接入的统计 hooks。

正常执行的过滤：

1. required fields present；
2. answer must come from GT or answer program；
3. source trace completeness；
4. duplicate question / duplicate evidence binding 去重；
5. answer option leakage 检查；
6. option balance / capability balance / source branch balance 约束；
7. item ID、template ID、metric ID、answer_program_id 一致性检查。

仅声明、不执行的 deferred hooks：

- CTT：`p_i`、point-biserial / item-total correlation；
- IRT：difficulty / discrimination / Fisher information；
- CDM / Q-matrix：模板-能力映射校准；
- Qwen-scope：能力激活分布、benchmark 冗余度；
- Gemma-scope / Llama-scope：跨模型 scope 对照。

## 输出

```text
WORKSPACE_ROOT/stage4/35-quality-filter-and-selection/quality_filter_spec.json
WORKSPACE_ROOT/stage4/35-quality-filter-and-selection/selection_plan.json
WORKSPACE_ROOT/stage4/35-quality-filter-and-selection/deferred_pilot_hooks.md
WORKSPACE_ROOT/stage4/35-quality-filter-and-selection/quality_gate_report.md
USED_INPUTS.json
DONE.json
```


---

## I/O 合同摘要

```text
node_id: 35
parents: ['31', '32', '34']
output_dir: WORKSPACE_ROOT/stage4/35-quality-filter-and-selection
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
