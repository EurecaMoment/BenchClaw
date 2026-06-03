# Node Skill — 仿真器清洗与标注

## 内部层级

本节点包含两个内部 subskill，按仿真器、任务族或场景 work unit 独立运行：

```text
subskills/cleaning/SKILL.md
subskills/annotation/SKILL.md
```

## 输入

- `stage3_execution_plan`
- `data_16_simulator_collection_bundle`

## tmux 后台 GT/半监督标注监控硬约束

本节点内所有 privileged GT 导出、GT 整理、annotation record 物化，以及计划显式要求的额外视觉伪标注命令，都必须按 `stage3_execution_plan` 中对应 `substage: annotation` DAG 节点的 tmux 字段执行。

1. 每个 annotation DAG 节点必须用 `tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"` 后台启动，不得在前台长时间运行 GT 导出或默认标注。
2. 启动后立即用 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>` 检查一次。
3. 只要 tmux 会话仍存在，就必须每 15 秒检查一次 GT/标注状态；任一活跃 annotation 会话两次检查间隔不得超过 15 秒。检查内容至少包括会话是否存活、最近 pane 输出、最近 100 行日志、已产出 `privileged_gt.jsonl` 记录数、`annotation_records.jsonl` 记录数和失败/复核计数；若执行额外视觉伪标注，还必须记录 `result.json` 产出计数。
4. 每次检查必须追加写入 `monitoring_log_path`，记录 `timestamp`、`tmux_session_name`、`dag_node_id`、`status`、`log_tail_summary`、`artifact_counts`；直到 `tmux has-session` 显示会话结束为止。
5. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 `privileged_gt.jsonl`、`annotation_records.jsonl`、可选 `default_annotation_manifest.jsonl`、`review_queue.jsonl` 和 `evidence_manifest.json`；缺少 15 秒监控记录、最终日志或真实 GT/标注输出时，不得写 `DONE.json`。

## 每 work unit

从 `data_16_simulator_collection_bundle/scenario_manifest.json` 动态发现仿真器、任务族、场景和 seed；不要硬编码任何仿真器或任务名称。

执行时必须优先读取 `stage3_execution_plan` 的 `parallel_dag.nodes[]`，只选择 `category: simulator` 且 `parent_category_node: simulator-evidence-compilation` 的节点作为本节点内部 DAG。每个仿真器 work unit 必须在计划中存在以下两个具体 DAG 节点：

```text
simulator::<work_unit_id>::cleaning
simulator::<work_unit_id>::annotation
```

这两个节点必须分别精确调用：

```text
skills/simulator-evidence-compilation/subskills/cleaning/SKILL.md
skills/simulator-evidence-compilation/subskills/annotation/SKILL.md
```

如果 `stage3_execution_plan` 没有显式列出某个仿真器 work unit 的上述 DAG 节点、节点缺少 `subskill_path`、`subskill_path` 指向其他类别，或不同仿真器 work unit 之间被错误建立依赖，必须 BLOCKED，不得自行补一个隐式串行流程。

每个 work unit 必须依次运行：

1. `subskills/cleaning/SKILL.md`
2. `subskills/annotation/SKILL.md`

## Per-work-unit 输出目录

```text
artifacts/data_19_annotated_simulator_bundle/work_units/<work_unit_id>/
  observations/
  data_juicer/
  annotation_or_gt/
  cleaned_state_logs.jsonl
  cleaned_observation_index.jsonl
  text_items.jsonl
  privileged_gt.jsonl
  annotation_records.jsonl
  evidence_manifest.json
  WORK_UNIT_REPORT.md
```

## 处理

1. 动态发现仿真器观测、状态日志、privileged GT、场景配置和 seed。
2. 对每个 work unit 先调用 `subskills/cleaning/SKILL.md`，该 subskill 必须通过 `BENCHCLAW_ROOT/data-juicer_card/SKILL.md` 运行 Data-Juicer pipeline，不能只做手写清洗。
3. 从仿真器 privileged state 或可验证计算中整理 GT；不得用模型生成内容或默认标注替代仿真器 GT。
4. 只有当 `stage3_execution_plan` 明确要求额外视觉伪标注时，annotation subskill 才可调用 `BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md`，并且输出必须标记为辅助候选，不得覆盖 privileged GT。
5. 将每个 step/episode 的观测媒体、文本描述、清洗后状态、动作/场景字段和 privileged GT 完整写入 workspace：观测必须复制或链接到本 bundle 的 `observations/`，`text_items.jsonl` 必须包含任务描述、状态摘要、事件描述或可供 Stage4 合成的问题上下文。
6. 每个 work unit 的 `evidence_manifest.json` 必须记录 Data-Juicer 命令、配置、日志、退出码、输入/输出计数、GT 计算规则、privileged state 来源、tmux session、15 秒监控日志、环境/仿真器版本、seed、观测到 GT 的映射、媒体 sha256/尺寸和阻塞/复核原因。
7. 写 `DONE.json` 前必须检查 `cleaned_state_logs.jsonl`、`cleaned_observation_index.jsonl`、`text_items.jsonl`、`privileged_gt.jsonl` 非空，除非 `stage3_execution_plan` 显式允许该 work unit 为空；每条 GT 必须引用真实 Stage2 运行产物和本阶段 GT 整理记录。
8. 串行汇总 per-work-unit 结果到 `data_19` 根目录。

## 汇总输出

- `artifacts/data_19_annotated_simulator_bundle/observations/`
- `artifacts/data_19_annotated_simulator_bundle/work_units/<work_unit_id>/...`
- `artifacts/data_19_annotated_simulator_bundle/cleaned_state_logs.jsonl`
- `artifacts/data_19_annotated_simulator_bundle/cleaned_observation_index.jsonl`
- `artifacts/data_19_annotated_simulator_bundle/text_items.jsonl`
- `artifacts/data_19_annotated_simulator_bundle/privileged_gt.jsonl`
- `artifacts/data_19_annotated_simulator_bundle/annotation_records.jsonl`
- `artifacts/data_19_annotated_simulator_bundle/default_annotation_manifest.jsonl`，仅当计划要求额外视觉伪标注时产出
- `artifacts/data_19_annotated_simulator_bundle/evidence_manifest.json`
- 节点执行记录文件
