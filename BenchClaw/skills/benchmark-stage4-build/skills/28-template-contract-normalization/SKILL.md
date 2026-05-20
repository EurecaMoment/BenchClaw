# Skill 28 — 模板契约规范化

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 父节点

`09`

## 任务

把 Stage1 的初版模板集与指标集改写为严格的工程契约：

1. `template_contracts.json`：每个模板必须声明 `template_id`、题型、目标能力、必需证据字段、可接受答案类型；
2. `metric_contracts.json`：每个指标必须声明输入、答案归一化、评分规则和异常处理；
3. `evidence_contracts.json`：每种题型需要哪些 GT 字段、哪些字段可由 simulator privileged GT / official label / tool candidate 支持；
4. `normalization_report.md`：记录删除、合并或保留的模板及原因。

## 禁止

不得在本节点读取 Stage3 数据；本节点只处理模板/指标契约。

## 输出

```text
WORKSPACE_ROOT/stage4/28-template-contract-normalization/template_contracts.json
WORKSPACE_ROOT/stage4/28-template-contract-normalization/metric_contracts.json
WORKSPACE_ROOT/stage4/28-template-contract-normalization/evidence_contracts.json
WORKSPACE_ROOT/stage4/28-template-contract-normalization/normalization_report.md
USED_INPUTS.json
DONE.json
```


---

## I/O 合同摘要

```text
node_id: 28
parents: ['09']
output_dir: WORKSPACE_ROOT/stage4/28-template-contract-normalization
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
