---
name: benchclaw-stage3-plan-generation
description: Use for the specific BenchClaw node skill `stage3-plan-generation` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — 本阶段执行计划生成

## 输入

- `data_13_execution_plan`
- `data_14_real_image_collection_bundle`
- `data_15_existing_benchmark_collection_bundle`
- `data_16_simulator_collection_bundle`

## 处理

1. 读取 Stage1 总执行计划和 Stage2 三类 collection bundle，不重写总目标。
2. 分解真实图片、已有 benchmark、仿真器三条 Stage3 数据源分支的 Data-Juicer 清洗规则、标注工具、复核策略、GT 来源和质量门。
3. 明确每条分支内部 `cleaning -> annotation` 的 work unit 粒度、输入路径、输出目录和阻塞条件。
4. 写明 `real-image-evidence-compilation` 与 `existing-benchmark-evidence-compilation` 必须调用 `BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md`；若默认标注所需服务不可用，分支必须 BLOCKED，不得跳过默认标注。
5. 写明三个 cleaning subskill 必须读取 `BENCHCLAW_ROOT/data-juicer_card/SKILL.md`，生成可运行 Data-Juicer YAML，并执行 `conda run -n data_juicer dj-process --config <config>` 或该卡允许的备用命令。
6. 写明每条分支和每个 work unit 的真实执行证明要求：Data-Juicer 配置、输入 manifest、执行命令、stdout/stderr 或日志、退出码、输出 manifest、默认标注命令或 GT 整理调用记录、工具版本、执行时间、输入/输出样本计数和失败样本计数。
7. 写明每个终端 bundle 的落盘要求：图像或观测媒体、文本字段、清洗样本、官方 label、默认标注候选、privileged GT、review queue 和 evidence manifest 都必须写入 `WORKSPACE_ROOT/stage3/artifacts/<data-id>/...`，并使用 workspace 相对路径供 Stage4 读取。
8. 将 Stage2 bundle 中发现到的每个数据源展开成显式并行 DAG work unit：每个 work unit 至少包含 `cleaning -> annotation` 两个内部 subskill 节点，仿真器的 `annotation` 节点负责 privileged GT 整理与可选额外视觉伪标注；不同 work unit 之间不得建立互相等待边。
9. 在 `stage3_execution_plan.yaml` 中写出 `parallel_dag.nodes[]` 与 `parallel_dag.edges[]`，精确声明每个 DAG 节点要调用的父节点 skill 名、类别 subskill skill 名、输入 bundle、输出目录、依赖和 ready group；源码路径只作为可追溯定位；不得只写“可以并行”。
10. 不创建任何 stage-level 清洗中间 artifact；清洗中间结果属于各数据源节点内部工作目录。
11. 所有 `substage: annotation` 节点必须写入半监督标注 tmux 监控字段：`tmux_required: true`、`monitor_interval_seconds: 15`、`monitor_until: session_finished`、`tmux_session_name`、`log_path`、`monitoring_log_path`。真实图片和已有 benchmark 的默认标注命令必须后台运行；仿真器若执行 GT 导出或额外视觉伪标注，也必须按同一策略后台运行和轮询。

## `stage3_execution_plan.yaml` 必填结构

`artifacts/stage3_execution_plan/stage3_execution_plan.yaml` 必须至少包含下列结构。字段可扩展，但不得删除真实执行、落盘和质量门字段。

```yaml
stage: stage3
generated_from:
  execution_plan: data_13_execution_plan
  collection_bundles:
    - data_14_real_image_collection_bundle
    - data_15_existing_benchmark_collection_bundle
    - data_16_simulator_collection_bundle
execution_policy:
  require_real_data_juicer_run: true
  require_real_annotation_or_gt_run: true
  annotation_tmux_required: true
  annotation_monitor_interval_seconds: 15
  annotation_monitor_until: session_finished
  forbid_placeholders: true
  forbid_chat_context_outputs: true
  workspace_root: WORKSPACE_ROOT/stage3
  execution_proof_required:
    - data_juicer/input_manifest.jsonl
    - data_juicer/process.yaml
    - data_juicer/command.txt
    - data_juicer/stdout.log
    - data_juicer/stderr.log
    - data_juicer/exit_code.txt
    - data_juicer/cleaned_manifest.jsonl
    - annotation_or_gt/command_or_call.json
    - annotation_or_gt/run_manifest.json
execution:
  tmux_annotation_policy:
    required: true
    monitor_interval_seconds: 15
    monitor_until: session_finished
    session_name_template: benchclaw_s3_<category>_<work_unit_id>_annotation_<YYYYMMDDHHMMSS>
    log_path_template: WORKSPACE_ROOT/stage3/nodes/<parent_category_node>/run_logs/<dag_node_id>.log
    monitoring_log_path_template: WORKSPACE_ROOT/stage3/nodes/<parent_category_node>/run_logs/<dag_node_id>.monitoring.jsonl
    completion_evidence_required:
      - tmux_session_name
      - start_time
      - every_15_seconds_monitoring_records
      - final_log_tail
      - exit_status_or_exit_code_marker
      - default_annotation_output_or_gt_manifest
  ready_groups:
    - id: stage3-category-evidence
      after: stage3-plan-generation
      mode: parallel
      nodes:
        - real-image-evidence-compilation
        - existing-benchmark-evidence-compilation
        - simulator-evidence-compilation
    - id: stage3-source-cleaning
      after: stage3-plan-generation
      mode: parallel
      node_selector: "parallel_dag.nodes[?substage==cleaning && parents==[]]"
      description: all cleaning subskill nodes from all enabled data sources must start as the same ready set
  explicit_parallel_dag_required: true
parallel_dag:
  semantics:
    - only nodes listed here are executable data-source work-unit steps
    - cleaning nodes with no parents are ready together and must be scheduled in parallel when resources allow
    - annotation nodes depend only on the cleaning node from the same work_unit_id
    - category summary barrier nodes wait only for their own category terminal work-unit nodes
  nodes:
    - dag_node_id: real_image::<dataset_id>::cleaning
      category: real_image
      substage: cleaning
      work_unit_id: real_image::<dataset_id>
      parent_category_node: real-image-evidence-compilation
      parent_skill_name: benchclaw-stage3-real-image-evidence-compilation
      skill_name: benchclaw-stage3-real-image-cleaning
      skill_path: skills/real-image-evidence-compilation/SKILL.md
      subskill_path: skills/real-image-evidence-compilation/subskills/cleaning/SKILL.md
      input_bundle: data_14_real_image_collection_bundle
      input_dir: artifacts/data_14_real_image_collection_bundle/datasets/<dataset_id>/
      parents: []
      ready_group: stage3-source-cleaning
      output_dir: artifacts/data_17_annotated_real_image_bundle/datasets/<dataset_id>/data_juicer/
    - dag_node_id: real_image::<dataset_id>::annotation
      category: real_image
      substage: annotation
      work_unit_id: real_image::<dataset_id>
      parent_category_node: real-image-evidence-compilation
      parent_skill_name: benchclaw-stage3-real-image-evidence-compilation
      skill_name: benchclaw-stage3-real-image-annotation
      skill_path: skills/real-image-evidence-compilation/SKILL.md
      subskill_path: skills/real-image-evidence-compilation/subskills/annotation/SKILL.md
      input_bundle: data_14_real_image_collection_bundle
      parents:
        - real_image::<dataset_id>::cleaning
      output_dir: artifacts/data_17_annotated_real_image_bundle/datasets/<dataset_id>/
      tmux_required: true
      monitor_interval_seconds: 15
      monitor_until: session_finished
      tmux_session_name: benchclaw_s3_real_image_<dataset_id>_annotation_<YYYYMMDDHHMMSS>
      log_path: WORKSPACE_ROOT/stage3/nodes/real-image-evidence-compilation/run_logs/real_image::<dataset_id>::annotation.log
      monitoring_log_path: WORKSPACE_ROOT/stage3/nodes/real-image-evidence-compilation/run_logs/real_image::<dataset_id>::annotation.monitoring.jsonl
    - dag_node_id: existing_benchmark::<dataset_id>::cleaning
      category: existing_benchmark
      substage: cleaning
      work_unit_id: existing_benchmark::<dataset_id>
      parent_category_node: existing-benchmark-evidence-compilation
      parent_skill_name: benchclaw-stage3-existing-benchmark-evidence-compilation
      skill_name: benchclaw-stage3-existing-benchmark-cleaning
      skill_path: skills/existing-benchmark-evidence-compilation/SKILL.md
      subskill_path: skills/existing-benchmark-evidence-compilation/subskills/cleaning/SKILL.md
      input_bundle: data_15_existing_benchmark_collection_bundle
      input_dir: artifacts/data_15_existing_benchmark_collection_bundle/datasets/<dataset_id>/
      parents: []
      ready_group: stage3-source-cleaning
      output_dir: artifacts/data_18_annotated_existing_benchmark_bundle/datasets/<dataset_id>/data_juicer/
    - dag_node_id: existing_benchmark::<dataset_id>::annotation
      category: existing_benchmark
      substage: annotation
      work_unit_id: existing_benchmark::<dataset_id>
      parent_category_node: existing-benchmark-evidence-compilation
      parent_skill_name: benchclaw-stage3-existing-benchmark-evidence-compilation
      skill_name: benchclaw-stage3-existing-benchmark-annotation
      skill_path: skills/existing-benchmark-evidence-compilation/SKILL.md
      subskill_path: skills/existing-benchmark-evidence-compilation/subskills/annotation/SKILL.md
      input_bundle: data_15_existing_benchmark_collection_bundle
      parents:
        - existing_benchmark::<dataset_id>::cleaning
      output_dir: artifacts/data_18_annotated_existing_benchmark_bundle/datasets/<dataset_id>/
      tmux_required: true
      monitor_interval_seconds: 15
      monitor_until: session_finished
      tmux_session_name: benchclaw_s3_existing_benchmark_<dataset_id>_annotation_<YYYYMMDDHHMMSS>
      log_path: WORKSPACE_ROOT/stage3/nodes/existing-benchmark-evidence-compilation/run_logs/existing_benchmark::<dataset_id>::annotation.log
      monitoring_log_path: WORKSPACE_ROOT/stage3/nodes/existing-benchmark-evidence-compilation/run_logs/existing_benchmark::<dataset_id>::annotation.monitoring.jsonl
    - dag_node_id: simulator::<work_unit_id>::cleaning
      category: simulator
      substage: cleaning
      work_unit_id: simulator::<work_unit_id>
      parent_category_node: simulator-evidence-compilation
      parent_skill_name: benchclaw-stage3-simulator-evidence-compilation
      skill_name: benchclaw-stage3-simulator-cleaning
      skill_path: skills/simulator-evidence-compilation/SKILL.md
      subskill_path: skills/simulator-evidence-compilation/subskills/cleaning/SKILL.md
      input_bundle: data_16_simulator_collection_bundle
      input_dir: artifacts/data_16_simulator_collection_bundle/<source_work_unit_path>
      parents: []
      ready_group: stage3-source-cleaning
      output_dir: artifacts/data_19_annotated_simulator_bundle/work_units/<work_unit_id>/data_juicer/
    - dag_node_id: simulator::<work_unit_id>::annotation
      category: simulator
      substage: annotation
      work_unit_id: simulator::<work_unit_id>
      parent_category_node: simulator-evidence-compilation
      parent_skill_name: benchclaw-stage3-simulator-evidence-compilation
      skill_name: benchclaw-stage3-simulator-annotation
      skill_path: skills/simulator-evidence-compilation/SKILL.md
      subskill_path: skills/simulator-evidence-compilation/subskills/annotation/SKILL.md
      input_bundle: data_16_simulator_collection_bundle
      gt_source: privileged_state_or_verifiable_computation
      parents:
        - simulator::<work_unit_id>::cleaning
      output_dir: artifacts/data_19_annotated_simulator_bundle/work_units/<work_unit_id>/
      tmux_required: true
      monitor_interval_seconds: 15
      monitor_until: session_finished
      tmux_session_name: benchclaw_s3_simulator_<work_unit_id>_annotation_<YYYYMMDDHHMMSS>
      log_path: WORKSPACE_ROOT/stage3/nodes/simulator-evidence-compilation/run_logs/simulator::<work_unit_id>::annotation.log
      monitoring_log_path: WORKSPACE_ROOT/stage3/nodes/simulator-evidence-compilation/run_logs/simulator::<work_unit_id>::annotation.monitoring.jsonl
    - dag_node_id: real_image::summary
      category: real_image
      parent_category_node: real-image-evidence-compilation
      barrier: serial_summary
      parents:
        - all real_image::*::annotation nodes
      output_dir: artifacts/data_17_annotated_real_image_bundle/
    - dag_node_id: existing_benchmark::summary
      category: existing_benchmark
      parent_category_node: existing-benchmark-evidence-compilation
      barrier: serial_summary
      parents:
        - all existing_benchmark::*::annotation nodes
      output_dir: artifacts/data_18_annotated_existing_benchmark_bundle/
    - dag_node_id: simulator::summary
      category: simulator
      parent_category_node: simulator-evidence-compilation
      barrier: serial_summary
      parents:
        - all simulator::*::annotation nodes
      output_dir: artifacts/data_19_annotated_simulator_bundle/
  edges:
    - from: real_image::<dataset_id>::cleaning
      to: real_image::<dataset_id>::annotation
    - from: real_image::<dataset_id>::annotation
      to: real_image::summary
    - from: existing_benchmark::<dataset_id>::cleaning
      to: existing_benchmark::<dataset_id>::annotation
    - from: existing_benchmark::<dataset_id>::annotation
      to: existing_benchmark::summary
    - from: simulator::<work_unit_id>::cleaning
      to: simulator::<work_unit_id>::annotation
    - from: simulator::<work_unit_id>::annotation
      to: simulator::summary
branches:
  real_image:
    node_id: real-image-evidence-compilation
    input_bundle: data_14_real_image_collection_bundle
    output_bundle: data_17_annotated_real_image_bundle
    cleaning:
      tool_card: BENCHCLAW_ROOT/data-juicer_card/SKILL.md
      command_template: conda run -n data_juicer dj-process --config <work_unit>/data_juicer/process.yaml
      must_run: true
    annotation:
      tool_card: BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md
      must_run: true
      output_role: tool_generated_candidate
      needs_human_review_by_default: true
    required_landed_files:
      - media/
      - cleaned_items.jsonl
      - text_items.jsonl
      - annotation_records.jsonl
      - review_queue.jsonl
      - evidence_manifest.json
    work_units:
      - work_unit_id: real_image::<dataset_id>
        source_dataset_id: <dataset_id>
        dag_nodes:
          - real_image::<dataset_id>::cleaning
          - real_image::<dataset_id>::annotation
        output_dir: artifacts/data_17_annotated_real_image_bundle/datasets/<dataset_id>/
  existing_benchmark:
    node_id: existing-benchmark-evidence-compilation
    input_bundle: data_15_existing_benchmark_collection_bundle
    output_bundle: data_18_annotated_existing_benchmark_bundle
    cleaning:
      tool_card: BENCHCLAW_ROOT/data-juicer_card/SKILL.md
      command_template: conda run -n data_juicer dj-process --config <work_unit>/data_juicer/process.yaml
      must_run: true
    annotation:
      tool_card: BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md
      must_run_for_new_annotation_targets: true
      output_role: tool_generated_candidate
      may_not_overwrite_official_labels: true
    required_landed_files:
      - media/
      - cleaned_items.jsonl
      - text_items.jsonl
      - official_labels.jsonl
      - added_annotation_records.jsonl
      - review_queue.jsonl
      - evidence_manifest.json
    work_units:
      - work_unit_id: existing_benchmark::<dataset_id>
        source_dataset_id: <dataset_id>
        dag_nodes:
          - existing_benchmark::<dataset_id>::cleaning
          - existing_benchmark::<dataset_id>::annotation
        output_dir: artifacts/data_18_annotated_existing_benchmark_bundle/datasets/<dataset_id>/
  simulator:
    node_id: simulator-evidence-compilation
    input_bundle: data_16_simulator_collection_bundle
    output_bundle: data_19_annotated_simulator_bundle
    cleaning:
      tool_card: BENCHCLAW_ROOT/data-juicer_card/SKILL.md
      command_template: conda run -n data_juicer dj-process --config <work_unit>/data_juicer/process.yaml
      must_run: true
    gt_materialization:
      source: privileged_state_or_verifiable_computation
      must_run: true
      forbid_model_generated_gt: true
    optional_annotation:
      allowed_only_if_explicitly_requested: true
      output_role: auxiliary_tool_generated_candidate
      may_not_overwrite_privileged_gt: true
    required_landed_files:
      - observations/
      - cleaned_state_logs.jsonl
      - cleaned_observation_index.jsonl
      - text_items.jsonl
      - privileged_gt.jsonl
      - annotation_records.jsonl
      - evidence_manifest.json
    work_units:
      - work_unit_id: simulator::<work_unit_id>
        source_work_unit_id: <work_unit_id>
        dag_nodes:
          - simulator::<work_unit_id>::cleaning
          - simulator::<work_unit_id>::annotation
        output_dir: artifacts/data_19_annotated_simulator_bundle/work_units/<work_unit_id>/
quality_gates:
  before_done:
    - all_required_jsonl_exist_and_nonempty_unless_explicitly_disabled
    - every_workspace_media_path_exists_and_size_gt_zero
    - image_media_decode_checked_with_width_height_sha256
    - text_fields_present_for_stage4
    - gt_or_annotation_records_trace_to_stage2_and_stage3_run
    - evidence_manifest_covers_all_work_units_commands_logs_counts_outputs
```

上面 YAML 中的 `<dataset_id>`、`<work_unit_id>`、`<source_work_unit_path>` 只是 schema 说明占位符。真实写入 `stage3_execution_plan.yaml` 时，必须用 Stage2 bundle 中动态发现到的数据集、仿真器任务族或场景 work unit 展开成具体节点；实际计划中不得保留尖括号占位符、空 `parallel_dag.nodes`、空 `parallel_dag.edges` 或空 `work_units`，除非对应 branch 被显式写成 `enabled: false` 并给出可追溯原因。

每个 `parallel_dag.nodes[]` 条目必须包含 `dag_node_id`、`category`、`substage`、`work_unit_id`、`parent_category_node`、`skill_path`、`subskill_path`、`input_bundle`、`parents`、`output_dir`；其中 `substage: annotation` 节点还必须包含 `tmux_required: true`、`monitor_interval_seconds: 15`、`monitor_until: session_finished`、`tmux_session_name`、`log_path`、`monitoring_log_path`。summary barrier 节点必须包含 `barrier: serial_summary` 且不得声明 `subskill_path`。每个 `work_units[]` 条目必须包含 `dag_nodes`，且 `dag_nodes` 必须能在 `parallel_dag.nodes[]` 中逐一找到同名节点。

## 显式并行 DAG 调度规则

1. 读取 `parallel_dag.nodes[]`，选择 `substage: cleaning` 且 `parents: []` 的所有节点组成第一轮 ready set；这些节点必须跨类别并行执行，并且执行器必须优先调用各自 `skill_name`，`subskill_path` 只作源码定位和审计。
2. 某个 work unit 的 cleaning 完成后，只释放同一 `work_unit_id` 的 annotation 节点；不得因为其他数据源未完成而等待。
3. 某一类别的所有 annotation 节点完成后，只释放该类别自己的 summary barrier；真实图片、已有 benchmark、仿真器三个 summary barrier 互不依赖。
4. Stage3 终止门只等待 `real_image::summary`、`existing_benchmark::summary`、`simulator::summary` 三个 barrier 全部完成并通过质量门。
5. 若执行者无法按 `parallel_dag` 并行调度，必须在 `NODE_REPORT.md` 中记录无法并行的具体资源或依赖原因；不得把“未写出显式 DAG”作为串行执行理由。
6. 每个 annotation 节点启动默认标注、半监督候选生成、GT 导出或额外视觉伪标注时，必须使用计划中的 `tmux_session_name` 和 `log_path` 后台执行；启动后必须每 15 秒检查一次 tmux 标注状态，循环直到 `tmux has-session -t <session>` 显示会话结束。每次检查都要记录时间戳、会话是否仍在运行、`tmux capture-pane -pt <session>` 最近输出摘要、`tail -n 100 <log_path>` 摘要、已产出 `result.json`/GT/annotation record 计数到 `monitoring_log_path`。
7. annotation 节点结束后必须读取最终日志、确认退出码或 `EXIT_CODE` 标记、检查默认标注输出或 GT manifest 与样本计数；缺少 15 秒监控记录、日志、退出状态或真实输出时，不得释放 summary barrier 或写 `DONE.json`。

若 Stage2 bundle 中没有任何可用样本，或计划允许某类为空，必须在对应 branch 写明 `enabled: false`、原因、上游证据路径和允许为空的来源；否则本节点必须 BLOCKED，不得生成会让下游写空 bundle 的计划。

出现以下任一情况时，本节点必须写 `nodes/stage3-plan-generation/BLOCKED.json` 与 `nodes/stage3-plan-generation/BLOCKED.md`，并停止 Stage3：

- `stage3_execution_plan.yaml` 没有显式 `parallel_dag.nodes[]` 与 `parallel_dag.edges[]`，或实际发现的数据源没有被展开成具体 DAG 节点。
- 任一 DAG 节点缺少精确 `subskill_path`，或 `subskill_path` 与数据源类别不匹配。
- 任一 `substage: annotation` 节点缺少 `tmux_required: true`、`monitor_interval_seconds: 15`、`tmux_session_name`、`log_path` 或 `monitoring_log_path`。
- 任一 DAG 边跨越不同 `work_unit_id` 且不是本类别 summary barrier，导致数据源之间被错误串行化。
- 实际计划中仍保留 `<dataset_id>`、`<work_unit_id>`、`<source_work_unit_path>` 等占位符。

## 输出

- `artifacts/stage3_execution_plan/stage3_execution_plan.yaml`
- 节点执行记录文件
