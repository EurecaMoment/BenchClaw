# Skill 35 — 质量过滤与选择策略

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

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

必须额外执行并写入 `quality_filter_spec.json` 的结构性拒绝规则：

8. 拒绝模板壳题目：若题面仍然是泛化模板句、变量未实例化、或包含 `...`、`<var>`、`placeholder`、`TBD` 等未落地标记，则拒绝；
9. 拒绝占位 GT：若 `ground_truth_answer` 只是“computed from ...”“official label answer”“placeholder”一类说明文本，而不是真正可判分答案或可执行接口输入，则拒绝；
10. 拒绝构念错位：题面问题必须与 `question_type`、`template_id`、`capability_tags` 对齐，SLAM、mapping、conflict-resolution 等任务不得退化成导航最优路径题；
11. 拒绝输入变量缺失：若题面声称需要 start、goal、object、instruction、options 等变量，但最终 item 没有在 `input_fields` 或题面中给出具体实例值，则拒绝；
12. 拒绝模态错配：若题型或能力标签需要 depth、language 或 multimodal contrast，但 `modality_condition` 与实际媒体输入不支持该任务，则拒绝；
13. 拒绝过度重复：若大规模 item 中题面唯一率过低、单一题面或单一模板占比过高、或场景复用异常集中，则必须阻塞而不是继续产出正式 benchmark；
14. `evaluation_ready` 只能由上述检查通过后程序化赋值，不能默认全设为 `true`。

若上述任一规则被大规模触发，本节点的结论必须是“仅可作为 smoke test / metadata test，不可作为正式 benchmark”，并阻止 36/37 生成正式评测包。

规范真相源应把通过/拒绝结果写入 `eval_dataset.jsonl` 与 `quality_gate_report.md`；如需导出 rejection log，只能生成兼容性 `jsonl` 文本副本。

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
