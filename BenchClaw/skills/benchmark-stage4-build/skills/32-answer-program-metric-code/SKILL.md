# Skill 32 — 答案程序与指标代码

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 父节点

`30`

## 任务

生成可执行评分与答案计算接口：

- `answer_programs.py`：只从 evidence/GT 计算答案；
- `metric_registry.json`：指标 ID、答案类型、归一化规则、评分规则；
- `scoring_interface.md`：Stage5 如何调用；
- `unit_test_plan.md`：每个 answer program 的最小单元测试。

## 关键约束

LLM 可以生成代码初稿，但答案逻辑必须由字段、几何、仿真器状态或官方标签驱动，不能由题面文本反推。

## 输出

```text
WORKSPACE_ROOT/stage4/32-answer-program-metric-code/answer_programs.py
WORKSPACE_ROOT/stage4/32-answer-program-metric-code/metric_registry.json
WORKSPACE_ROOT/stage4/32-answer-program-metric-code/scoring_interface.md
WORKSPACE_ROOT/stage4/32-answer-program-metric-code/unit_test_plan.md
USED_INPUTS.json
DONE.json
```


---

## I/O 合同摘要

```text
node_id: 32
parents: ['30']
output_dir: WORKSPACE_ROOT/stage4/32-answer-program-metric-code
```

完整白名单以 `contracts/node_io_contracts.json` 为准。
