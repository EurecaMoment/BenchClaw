---
name: benchclaw-stage2-plan-generation
description: Use for the specific BenchClaw node skill `stage2-plan-generation` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — 本阶段执行计划生成

## 输入

- `data_13_execution_plan`

## 硬约束

本节点生成的 `stage2_execution_plan.yaml` 是 Stage2 三条采集分支的唯一执行计划。计划必须把三类数据源锁定到各自类别的 card 根目录，不能把任一类别的数据源分配给其他分支，也不能引入未由对应 card 声明的数据源。

| 数据源类别 | 唯一允许 card 根目录 | 唯一消费节点 | 唯一输出 bundle |
|---|---|---|---|
| 真实图片 | `BENCHCLAW_ROOT/realDataCards` | `real-image-collection-analysis` | `data_14_real_image_collection_bundle` |
| 已有 benchmark | `BENCHCLAW_ROOT/benchmarkDatasetCards` | `existing-benchmark-collection-analysis` | `data_15_existing_benchmark_collection_bundle` |
| 仿真器 | `BENCHCLAW_ROOT/simulatorCards` | `simulator-collection-analysis` | `data_16_simulator_collection_bundle` |

执行计划必须遵守：

1. `existing-benchmark-collection-analysis` 的 `source_root`、`allowed_card_glob`、`work_units[*].card_skill` 只能来自 `BENCHCLAW_ROOT/benchmarkDatasetCards`。
2. `real-image-collection-analysis` 的 `source_root`、`allowed_card_glob`、`work_units[*].card_skill` 只能来自 `BENCHCLAW_ROOT/realDataCards`。
3. `simulator-collection-analysis` 的 `source_root`、`allowed_card_glob`、`work_units[*].card_skill` 只能来自 `BENCHCLAW_ROOT/simulatorCards`。
4. `benchmarkDatasetCards` 下的 card 不得进入真实图片或仿真器分支；`realDataCards` 下的 card 不得进入已有 benchmark 或仿真器分支；`simulatorCards` 下的 card 不得进入真实图片或已有 benchmark 分支。
5. 若 `data_13_execution_plan` 把来源放错类别、引用了上述三类 card 根目录之外的采集 card、或要求某分支读取其他类别 card，必须写 `BLOCKED.json` 与 `BLOCKED.md`，不得自动改类、复制 card、移动 card 或绕过 card 直接读取数据。
6. card 目录只读。Stage2 只能读取对应 card 的 `SKILL.md` 及该 card 明确声明的本地数据根、下载方式、replay 或仿真器入口；不得修改 `benchmarkDatasetCards`、`realDataCards`、`simulatorCards` 下任何文件。
7. 所有路径判断必须使用冻结的 `BENCHCLAW_ROOT` 解析后的实际路径；不得用字符串包含关系代替目录归属校验。若解析后的 card 路径不在所属类别根目录内，必须阻塞。
8. 空分支只有在 `data_13_execution_plan` 明确说明该类别不需要，并且 `stage2_execution_plan.yaml` 中把该类别标为 `enabled: false` 且写明原因时才允许；否则发现不到合法 card 或 work unit 必须阻塞。
9. `stage2_execution_plan.yaml` 必须显式写出各个数据源 work unit 的并行 DAG；不得只写“可以并行”、不得只写类别级 ready group、不得保留空的 `discovered_cards: []` 或 `work_units: []` 作为实际计划。除非某分支被显式禁用，每个发现到的数据源都必须有自己的 DAG 节点、边、并行组和隔离输出目录。
10. 每个并行 DAG 节点必须精确写明要调用的类别节点 skill 名与本类别 subskill skill 名；源码路径只作为可追溯目录说明。真实图片只能调用 `benchclaw-stage2-real-image-content-analysis` 与 `benchclaw-stage2-real-image-data-structure-normalization`；已有 benchmark 只能调用 `benchclaw-stage2-existing-benchmark-content-label-analysis` 与 `benchclaw-stage2-existing-benchmark-data-materialization`；仿真器只能调用 `benchclaw-stage2-simulator-data-acquisition` 与 `benchclaw-stage2-simulator-gt-materialization`。
11. 不同数据源的第一步 subskill 节点必须放入同一个跨类别 `parallel_group`，使真实图片、已有 benchmark 和仿真器数据源能实质并行启动；同一数据源内部的第二步 subskill 只能依赖自己的第一步，不得依赖其他数据源完成。
12. 根 bundle 汇总节点必须是每个类别内部的串行 barrier，只依赖本类别所有 work unit 的末端 subskill；不得让某一类别的汇总等待其他类别的 work unit，Stage2 的最终完成门才等待三类 terminal bundle。
13. 所有执行真实数据采集、扫描、下载、解压、复制、物化、仿真 replay/运行或 GT 导出的 DAG 节点都必须写入 `tmux_required: true`、`monitor_interval_seconds: 15`、`monitor_until: session_finished`、`tmux_session_name`、`log_path` 和 `monitoring_log_path`；计划不得把采集命令设计成前台长期运行。
14. 除非用户请求或 `data_13_execution_plan` 明确要求其他规模/禁用相关分支，计划必须写入 `collection_requirements.minimum_total_collected_images: 100`，并把该下限分解为各启用分支的目标或补采策略；若另有要求，写入对应数值与 `override_reason`，不得生成低于显式要求的采集计划。

## 处理

1. 读取 Stage1 执行计划，不重写总目标。
2. 从冻结的 `BENCHCLAW_ROOT` 派生三类唯一允许 card 根目录：

```text
real_image.source_root = BENCHCLAW_ROOT/realDataCards
existing_benchmark.source_root = BENCHCLAW_ROOT/benchmarkDatasetCards
simulator.source_root = BENCHCLAW_ROOT/simulatorCards
```

3. 对三类 card 根目录分别做运行时发现，只枚举直接子文件夹，并要求每个合法 work unit 都有自己的 `SKILL.md`：

```text
BENCHCLAW_ROOT/realDataCards/<dataset_id>/SKILL.md
BENCHCLAW_ROOT/benchmarkDatasetCards/<dataset_id>/SKILL.md
BENCHCLAW_ROOT/simulatorCards/<simulator_id>/SKILL.md
```

4. 分别生成真实图片、已有 benchmark、仿真器三条采集分支的数量、字段、工具、目录、质量门和阻塞条件。每条分支只能包含本类别的 `source_root`、`allowed_card_glob`、`discovered_cards`、`work_units` 和输出 bundle。
   默认情况下，三条分支汇总的有效图片媒体总数目标不得低于 100；如果 Stage1 或用户显式要求更少，必须在计划中记录 `explicit_scale_exception`、来源依据和允许的目标数量。
5. 将运行时发现到的每个数据源都展开成显式 DAG work unit：每个 work unit 至少包含两个串行 subskill 节点，节点之间只建立同一数据源内部的依赖边，不同数据源之间不建立互相等待边。
6. 为三条采集分支写入同一个跨类别 `parallel_group`，要求 `real-image-collection-analysis`、`existing-benchmark-collection-analysis`、`simulator-collection-analysis` 在 `stage2-plan-generation` 完成后作为同一 ready set 并行消费计划；同时在 `parallel_dag.nodes[]` 中把所有数据源第一步 subskill 节点标为同一 `ready_group: stage2-source-first-step`。只有资源、依赖或用户显式限制导致无法并行时，才可串行执行，并必须在节点报告中记录原因。
7. 为每个类别内部写明并行 work unit 粒度：

- 真实图片：按 `realDataCards` 的直接子文件夹并行，每个 work unit 写入 `artifacts/data_14_real_image_collection_bundle/datasets/<dataset_id>/`。
- 已有 benchmark：按 `benchmarkDatasetCards` 的直接子文件夹并行，每个 work unit 写入 `artifacts/data_15_existing_benchmark_collection_bundle/datasets/<dataset_id>/`。
- 仿真器：按 `simulatorCards` 的直接子文件夹和计划要求的 `task_family` 并行，每个 work unit 写入 `artifacts/data_16_simulator_collection_bundle/simulators/<simulator_id>/<task_family>/`。

8. 明确并行时共享输入只读、共享输出隔离：任何 work unit 不得同时追加写 bundle 根目录汇总文件；所有 per-dataset 或 per-simulator 输出完成后，所属分支再串行汇总。
9. 写入本阶段执行计划，供三条分支按类别并行消费，并确保大模型可以只读取 `parallel_dag` 就知道每个数据源该调用哪个已注册 skill、哪些节点可并行、哪些节点必须等待。

## `stage2_execution_plan.yaml` 必填结构

`nodes/stage2-plan-generation/stage2_execution_plan.yaml` 必须至少包含下列结构。字段可扩展，但不得删除这些来源白名单、并行组和分支约束字段。

```yaml
stage: stage2
generated_from: data_13_execution_plan
source_policy:
  enforce_category_roots: true
  path_check: realpath_under_frozen_benchclaw_root
  category_roots:
    real_image:
      source_root: BENCHCLAW_ROOT/realDataCards
      allowed_card_glob: BENCHCLAW_ROOT/realDataCards/*/SKILL.md
      forbidden_roots:
        - BENCHCLAW_ROOT/benchmarkDatasetCards
        - BENCHCLAW_ROOT/simulatorCards
      node_id: real-image-collection-analysis
      output_bundle: data_14_real_image_collection_bundle
    existing_benchmark:
      source_root: BENCHCLAW_ROOT/benchmarkDatasetCards
      allowed_card_glob: BENCHCLAW_ROOT/benchmarkDatasetCards/*/SKILL.md
      forbidden_roots:
        - BENCHCLAW_ROOT/realDataCards
        - BENCHCLAW_ROOT/simulatorCards
      node_id: existing-benchmark-collection-analysis
      output_bundle: data_15_existing_benchmark_collection_bundle
    simulator:
      source_root: BENCHCLAW_ROOT/simulatorCards
      allowed_card_glob: BENCHCLAW_ROOT/simulatorCards/*/SKILL.md
      forbidden_roots:
        - BENCHCLAW_ROOT/realDataCards
        - BENCHCLAW_ROOT/benchmarkDatasetCards
      node_id: simulator-collection-analysis
      output_bundle: data_16_simulator_collection_bundle
execution:
  collection_requirements:
    minimum_total_collected_images: 100
    override_reason: null
    scope: data_14_real_image_collection_bundle + data_15_existing_benchmark_collection_bundle + data_16_simulator_collection_bundle
    counted_media: real non-empty decodable image files or render frames
  collection_scale_policy:
    default_min_total_images: 100
    effective_min_total_images: 100
    count_scope: enabled terminal bundles combined
    count_unit: unique decodable image media paths with decode_status ok
    explicit_scale_exception: null
    per_category_targets:
      real_image: planned count or null
      existing_benchmark: planned count or null
      simulator: planned count or null
  tmux_collection_policy:
    required: true
    monitor_interval_seconds: 15
    monitor_until: session_finished
    session_name_template: benchclaw_s2_<category>_<work_unit_id>_<subskill>_<YYYYMMDDHHMMSS>
    log_path_template: WORKSPACE_ROOT/stage2/nodes/<parent_category_node>/run_logs/<dag_node_id>.log
    monitoring_log_path_template: WORKSPACE_ROOT/stage2/nodes/<parent_category_node>/run_logs/<dag_node_id>.monitoring.jsonl
    completion_evidence_required:
      - tmux_session_name
      - start_time
      - every_15_seconds_monitoring_records
      - final_log_tail
      - exit_status_or_exit_code_marker
      - output_manifest
  ready_groups:
    - id: stage2-category-collection
      after: stage2-plan-generation
      mode: parallel
      nodes:
        - real-image-collection-analysis
        - existing-benchmark-collection-analysis
        - simulator-collection-analysis
      shared_inputs_read_only: true
      isolated_outputs_required: true
    - id: stage2-source-first-step
      after: stage2-plan-generation
      mode: parallel
      node_selector: parallel_dag.nodes[?parents==[]]
      description: all first subskill nodes from all enabled data sources must start as the same ready set
  explicit_parallel_dag_required: true
parallel_dag:
  semantics:
    - only nodes listed here are executable data-source work-unit steps
    - nodes with no parents are ready together and must be scheduled in parallel when resources allow
    - a node may depend only on nodes from the same work_unit_id, except category summary barrier nodes
    - category summary barrier nodes wait only for their own category terminal work-unit nodes
  nodes:
    - dag_node_id: real_image::<dataset_id>::content-analysis
      category: real_image
      work_unit_id: real_image::<dataset_id>
      parent_category_node: real-image-collection-analysis
      parent_skill_name: benchclaw-stage2-real-image-collection-analysis
      skill_name: benchclaw-stage2-real-image-content-analysis
      skill_path: skills/real-image-collection-analysis/SKILL.md
      subskill_path: skills/real-image-collection-analysis/subskills/content-analysis/SKILL.md
      card_skill: BENCHCLAW_ROOT/realDataCards/<dataset_id>/SKILL.md
      parents: []
      ready_group: stage2-source-first-step
      output_dir: artifacts/data_14_real_image_collection_bundle/datasets/<dataset_id>/content-analysis/
      tmux_required: true
      monitor_interval_seconds: 15
      monitor_until: session_finished
      tmux_session_name: benchclaw_s2_real_image_<dataset_id>_content_analysis_<YYYYMMDDHHMMSS>
      log_path: WORKSPACE_ROOT/stage2/nodes/real-image-collection-analysis/run_logs/real_image::<dataset_id>::content-analysis.log
      monitoring_log_path: WORKSPACE_ROOT/stage2/nodes/real-image-collection-analysis/run_logs/real_image::<dataset_id>::content-analysis.monitoring.jsonl
    - dag_node_id: real_image::<dataset_id>::data-structure-normalization
      category: real_image
      work_unit_id: real_image::<dataset_id>
      parent_category_node: real-image-collection-analysis
      parent_skill_name: benchclaw-stage2-real-image-collection-analysis
      skill_name: benchclaw-stage2-real-image-data-structure-normalization
      skill_path: skills/real-image-collection-analysis/SKILL.md
      subskill_path: skills/real-image-collection-analysis/subskills/data-structure-normalization/SKILL.md
      card_skill: BENCHCLAW_ROOT/realDataCards/<dataset_id>/SKILL.md
      parents:
        - real_image::<dataset_id>::content-analysis
      output_dir: artifacts/data_14_real_image_collection_bundle/datasets/<dataset_id>/
      tmux_required: true
      monitor_interval_seconds: 15
      monitor_until: session_finished
      tmux_session_name: benchclaw_s2_real_image_<dataset_id>_data_structure_normalization_<YYYYMMDDHHMMSS>
      log_path: WORKSPACE_ROOT/stage2/nodes/real-image-collection-analysis/run_logs/real_image::<dataset_id>::data-structure-normalization.log
      monitoring_log_path: WORKSPACE_ROOT/stage2/nodes/real-image-collection-analysis/run_logs/real_image::<dataset_id>::data-structure-normalization.monitoring.jsonl
    - dag_node_id: existing_benchmark::<dataset_id>::content-label-analysis
      category: existing_benchmark
      work_unit_id: existing_benchmark::<dataset_id>
      parent_category_node: existing-benchmark-collection-analysis
      parent_skill_name: benchclaw-stage2-existing-benchmark-collection-analysis
      skill_name: benchclaw-stage2-existing-benchmark-content-label-analysis
      skill_path: skills/existing-benchmark-collection-analysis/SKILL.md
      subskill_path: skills/existing-benchmark-collection-analysis/subskills/content-label-analysis/SKILL.md
      card_skill: BENCHCLAW_ROOT/benchmarkDatasetCards/<dataset_id>/SKILL.md
      parents: []
      ready_group: stage2-source-first-step
      output_dir: artifacts/data_15_existing_benchmark_collection_bundle/datasets/<dataset_id>/content-label-analysis/
      tmux_required: true
      monitor_interval_seconds: 15
      monitor_until: session_finished
      tmux_session_name: benchclaw_s2_existing_benchmark_<dataset_id>_content_label_analysis_<YYYYMMDDHHMMSS>
      log_path: WORKSPACE_ROOT/stage2/nodes/existing-benchmark-collection-analysis/run_logs/existing_benchmark::<dataset_id>::content-label-analysis.log
      monitoring_log_path: WORKSPACE_ROOT/stage2/nodes/existing-benchmark-collection-analysis/run_logs/existing_benchmark::<dataset_id>::content-label-analysis.monitoring.jsonl
    - dag_node_id: existing_benchmark::<dataset_id>::data-materialization
      category: existing_benchmark
      work_unit_id: existing_benchmark::<dataset_id>
      parent_category_node: existing-benchmark-collection-analysis
      parent_skill_name: benchclaw-stage2-existing-benchmark-collection-analysis
      skill_name: benchclaw-stage2-existing-benchmark-data-materialization
      skill_path: skills/existing-benchmark-collection-analysis/SKILL.md
      subskill_path: skills/existing-benchmark-collection-analysis/subskills/data-materialization/SKILL.md
      card_skill: BENCHCLAW_ROOT/benchmarkDatasetCards/<dataset_id>/SKILL.md
      parents:
        - existing_benchmark::<dataset_id>::content-label-analysis
      output_dir: artifacts/data_15_existing_benchmark_collection_bundle/datasets/<dataset_id>/
      tmux_required: true
      monitor_interval_seconds: 15
      monitor_until: session_finished
      tmux_session_name: benchclaw_s2_existing_benchmark_<dataset_id>_data_materialization_<YYYYMMDDHHMMSS>
      log_path: WORKSPACE_ROOT/stage2/nodes/existing-benchmark-collection-analysis/run_logs/existing_benchmark::<dataset_id>::data-materialization.log
      monitoring_log_path: WORKSPACE_ROOT/stage2/nodes/existing-benchmark-collection-analysis/run_logs/existing_benchmark::<dataset_id>::data-materialization.monitoring.jsonl
    - dag_node_id: simulator::<simulator_id>::<task_family>::data-acquisition
      category: simulator
      work_unit_id: simulator::<simulator_id>::<task_family>
      parent_category_node: simulator-collection-analysis
      parent_skill_name: benchclaw-stage2-simulator-collection-analysis
      skill_name: benchclaw-stage2-simulator-data-acquisition
      skill_path: skills/simulator-collection-analysis/SKILL.md
      subskill_path: skills/simulator-collection-analysis/subskills/data-acquisition/SKILL.md
      card_skill: BENCHCLAW_ROOT/simulatorCards/<simulator_id>/SKILL.md
      parents: []
      ready_group: stage2-source-first-step
      output_dir: artifacts/data_16_simulator_collection_bundle/simulators/<simulator_id>/<task_family>/data-acquisition/
      tmux_required: true
      monitor_interval_seconds: 15
      monitor_until: session_finished
      tmux_session_name: benchclaw_s2_simulator_<simulator_id>_<task_family>_data_acquisition_<YYYYMMDDHHMMSS>
      log_path: WORKSPACE_ROOT/stage2/nodes/simulator-collection-analysis/run_logs/simulator::<simulator_id>::<task_family>::data-acquisition.log
      monitoring_log_path: WORKSPACE_ROOT/stage2/nodes/simulator-collection-analysis/run_logs/simulator::<simulator_id>::<task_family>::data-acquisition.monitoring.jsonl
    - dag_node_id: simulator::<simulator_id>::<task_family>::gt-materialization
      category: simulator
      work_unit_id: simulator::<simulator_id>::<task_family>
      parent_category_node: simulator-collection-analysis
      parent_skill_name: benchclaw-stage2-simulator-collection-analysis
      skill_name: benchclaw-stage2-simulator-gt-materialization
      skill_path: skills/simulator-collection-analysis/SKILL.md
      subskill_path: skills/simulator-collection-analysis/subskills/gt-materialization/SKILL.md
      card_skill: BENCHCLAW_ROOT/simulatorCards/<simulator_id>/SKILL.md
      parents:
        - simulator::<simulator_id>::<task_family>::data-acquisition
      output_dir: artifacts/data_16_simulator_collection_bundle/simulators/<simulator_id>/<task_family>/
      tmux_required: true
      monitor_interval_seconds: 15
      monitor_until: session_finished
      tmux_session_name: benchclaw_s2_simulator_<simulator_id>_<task_family>_gt_materialization_<YYYYMMDDHHMMSS>
      log_path: WORKSPACE_ROOT/stage2/nodes/simulator-collection-analysis/run_logs/simulator::<simulator_id>::<task_family>::gt-materialization.log
      monitoring_log_path: WORKSPACE_ROOT/stage2/nodes/simulator-collection-analysis/run_logs/simulator::<simulator_id>::<task_family>::gt-materialization.monitoring.jsonl
    - dag_node_id: real_image::summary
      category: real_image
      parent_category_node: real-image-collection-analysis
      barrier: serial_summary
      parents:
        - all real_image::*::data-structure-normalization nodes
      output_dir: artifacts/data_14_real_image_collection_bundle/
    - dag_node_id: existing_benchmark::summary
      category: existing_benchmark
      parent_category_node: existing-benchmark-collection-analysis
      barrier: serial_summary
      parents:
        - all existing_benchmark::*::data-materialization nodes
      output_dir: artifacts/data_15_existing_benchmark_collection_bundle/
    - dag_node_id: simulator::summary
      category: simulator
      parent_category_node: simulator-collection-analysis
      barrier: serial_summary
      parents:
        - all simulator::*::*::gt-materialization nodes
      output_dir: artifacts/data_16_simulator_collection_bundle/
  edges:
    - from: real_image::<dataset_id>::content-analysis
      to: real_image::<dataset_id>::data-structure-normalization
    - from: real_image::<dataset_id>::data-structure-normalization
      to: real_image::summary
    - from: existing_benchmark::<dataset_id>::content-label-analysis
      to: existing_benchmark::<dataset_id>::data-materialization
    - from: existing_benchmark::<dataset_id>::data-materialization
      to: existing_benchmark::summary
    - from: simulator::<simulator_id>::<task_family>::data-acquisition
      to: simulator::<simulator_id>::<task_family>::gt-materialization
    - from: simulator::<simulator_id>::<task_family>::gt-materialization
      to: simulator::summary
branches:
  real_image:
    enabled: true
    node_id: real-image-collection-analysis
    data_source_type: real_image
    source_root: BENCHCLAW_ROOT/realDataCards
    output_bundle: data_14_real_image_collection_bundle
    parallelism:
      group: stage2-category-collection
      work_unit_granularity: dataset_card
      internal_mode: parallel_per_direct_child_folder_then_serial_summary
    subskill_dag_template:
      - skills/real-image-collection-analysis/subskills/content-analysis/SKILL.md
      - skills/real-image-collection-analysis/subskills/data-structure-normalization/SKILL.md
    discovered_cards:
      - id: <dataset_id>
        card_skill: BENCHCLAW_ROOT/realDataCards/<dataset_id>/SKILL.md
        parallel_dag_nodes:
          - real_image::<dataset_id>::content-analysis
          - real_image::<dataset_id>::data-structure-normalization
    work_units:
      - work_unit_id: real_image::<dataset_id>
        card_skill: BENCHCLAW_ROOT/realDataCards/<dataset_id>/SKILL.md
        dag_nodes:
          - real_image::<dataset_id>::content-analysis
          - real_image::<dataset_id>::data-structure-normalization
        output_dir: artifacts/data_14_real_image_collection_bundle/datasets/<dataset_id>/
    quality_gates: []
    blocked_if_empty_without_explicit_disable: true
  existing_benchmark:
    enabled: true
    node_id: existing-benchmark-collection-analysis
    data_source_type: existing_benchmark
    source_root: BENCHCLAW_ROOT/benchmarkDatasetCards
    output_bundle: data_15_existing_benchmark_collection_bundle
    parallelism:
      group: stage2-category-collection
      work_unit_granularity: benchmark_dataset_card
      internal_mode: parallel_per_direct_child_folder_then_serial_summary
    subskill_dag_template:
      - skills/existing-benchmark-collection-analysis/subskills/content-label-analysis/SKILL.md
      - skills/existing-benchmark-collection-analysis/subskills/data-materialization/SKILL.md
    discovered_cards:
      - id: <dataset_id>
        card_skill: BENCHCLAW_ROOT/benchmarkDatasetCards/<dataset_id>/SKILL.md
        parallel_dag_nodes:
          - existing_benchmark::<dataset_id>::content-label-analysis
          - existing_benchmark::<dataset_id>::data-materialization
    work_units:
      - work_unit_id: existing_benchmark::<dataset_id>
        card_skill: BENCHCLAW_ROOT/benchmarkDatasetCards/<dataset_id>/SKILL.md
        dag_nodes:
          - existing_benchmark::<dataset_id>::content-label-analysis
          - existing_benchmark::<dataset_id>::data-materialization
        output_dir: artifacts/data_15_existing_benchmark_collection_bundle/datasets/<dataset_id>/
    quality_gates: []
    blocked_if_empty_without_explicit_disable: true
  simulator:
    enabled: true
    node_id: simulator-collection-analysis
    data_source_type: simulator
    source_root: BENCHCLAW_ROOT/simulatorCards
    output_bundle: data_16_simulator_collection_bundle
    parallelism:
      group: stage2-category-collection
      work_unit_granularity: simulator_card_and_task_family
      internal_mode: parallel_per_simulator_task_then_serial_summary
    subskill_dag_template:
      - skills/simulator-collection-analysis/subskills/data-acquisition/SKILL.md
      - skills/simulator-collection-analysis/subskills/gt-materialization/SKILL.md
    discovered_cards:
      - id: <simulator_id>
        card_skill: BENCHCLAW_ROOT/simulatorCards/<simulator_id>/SKILL.md
        parallel_dag_nodes:
          - simulator::<simulator_id>::<task_family>::data-acquisition
          - simulator::<simulator_id>::<task_family>::gt-materialization
    work_units:
      - work_unit_id: simulator::<simulator_id>::<task_family>
        simulator_id: <simulator_id>
        task_family: <task_family>
        card_skill: BENCHCLAW_ROOT/simulatorCards/<simulator_id>/SKILL.md
        requires_real_images: true
        zero_image_retry_policy: retry_until_at_least_one_image
        zero_image_may_complete: false
        dag_nodes:
          - simulator::<simulator_id>::<task_family>::data-acquisition
          - simulator::<simulator_id>::<task_family>::gt-materialization
        output_dir: artifacts/data_16_simulator_collection_bundle/simulators/<simulator_id>/<task_family>/
    quality_gates: []
    blocked_if_empty_without_explicit_disable: true
```

上面 YAML 中的 `<dataset_id>`、`<simulator_id>`、`<task_family>` 只是 schema 说明占位符。真实写入 `stage2_execution_plan.yaml` 时，必须用运行时动态发现到的直接子文件夹名和计划解析出的任务族展开成具体节点；实际计划中不得保留尖括号占位符、空 `parallel_dag.nodes`、空 `parallel_dag.edges`、空 `work_units` 或空 `discovered_cards`，除非对应 branch 被显式写成 `enabled: false` 并给出可追溯原因。

每个 `discovered_cards[]` 条目必须包含：

```yaml
id: <direct_child_folder_name>
category: real_image | existing_benchmark | simulator
card_skill: BENCHCLAW_ROOT/<category_root>/<id>/SKILL.md
realpath_checked: true
```

每个 `work_units[]` 条目必须包含：

```yaml
work_unit_id: <stable id>
category: real_image | existing_benchmark | simulator
node_id: <matching node id>
card_skill: <matching category card skill path>
output_dir: <matching artifact subdirectory>
status: planned
```

每个 `work_units[]` 条目还必须包含 `dag_nodes`，且 `dag_nodes` 必须能在 `parallel_dag.nodes[]` 中逐一找到同名节点。每个可执行 `parallel_dag.nodes[]` 条目必须包含 `dag_node_id`、`category`、`work_unit_id`、`parent_category_node`、`skill_path`、`subskill_path`、`card_skill`、`parents`、`output_dir`、`tmux_required: true`、`monitor_interval_seconds: 15`、`monitor_until: session_finished`、`tmux_session_name`、`log_path`、`monitoring_log_path`；summary barrier 节点必须包含 `barrier: serial_summary` 且不得声明 `subskill_path`。

仿真器 work unit 还必须包含 `simulator_id`、`task_family`、`requires_real_run: true`、`requires_real_images: true`、`zero_image_retry_policy: retry_until_at_least_one_image`、`zero_image_may_complete: false`、`run_outputs_required: [observations, state_logs, actions, privileged_gt, run_logs]`。计划不得允许仿真器以 0 张图像完成；若一轮采集没有图像，执行者必须继续重试该 work unit。

## 显式并行 DAG 调度规则

1. 读取 `parallel_dag.nodes[]`，选择 `parents: []` 的所有节点组成第一轮 ready set；这些节点必须跨类别并行执行，并且执行器必须优先调用各自 `skill_name`，`subskill_path` 只作源码定位和审计。
2. 某个 work unit 的第一步 subskill 完成后，只释放同一 `work_unit_id` 的第二步 subskill；不得因为其他数据源未完成而等待。
3. 某一类别的所有第二步 subskill 完成后，只释放该类别自己的 summary barrier；真实图片、已有 benchmark、仿真器三个 summary barrier 互不依赖。
4. Stage2 终止门只等待 `real_image::summary`、`existing_benchmark::summary`、`simulator::summary` 三个 barrier 全部完成并通过质量门。
5. 若执行者无法按 `parallel_dag` 并行调度，必须在 `NODE_REPORT.md` 中记录无法并行的具体资源或依赖原因；不得把“未写出显式 DAG”作为串行执行理由。
6. 每个可执行采集节点启动时必须使用计划中的 `tmux_session_name` 和 `log_path` 后台执行；启动后必须每 15 秒检查一次该 tmux 会话的采集状态，循环直到 `tmux has-session -t <session>` 显示会话结束。每次检查都要记录时间戳、会话是否仍在运行、`tmux capture-pane -pt <session>` 最近输出摘要、`tail -n 100 <log_path>` 摘要到 `monitoring_log_path`。
7. 采集节点结束后必须读取最后日志、确认退出码或 `EXIT_CODE` 标记、检查输出 manifest 与样本计数；缺少 15 秒监控记录、日志、退出状态或真实输出时，不得释放后续 DAG 节点。
8. 对仿真器 data-acquisition 节点，若检查到图像/渲染帧计数为 0，不得释放 `gt-materialization`，不得释放 `simulator::summary`，必须重新启动该 work unit 的采集尝试并继续监控，直到至少一个真实图像落盘。

## 阻塞条件

出现以下任一情况时，本节点必须写 `nodes/stage2-plan-generation/BLOCKED.json` 与 `nodes/stage2-plan-generation/BLOCKED.md`，并停止 Stage2：

- 冻结的 `BENCHCLAW_ROOT` 缺失，或不能解析到 BenchClaw 根目录。
- 计划需要的类别根目录不存在或不可读。
- 直接子文件夹缺少 `SKILL.md`，且该类别未被执行计划显式禁用。
- 任一 `card_skill` 解析后不在所属类别根目录内。
- 任一来源被分配到了错误类别或错误输出 bundle。
- 任一分支计划要求从其他类别 card 根目录读取数据。
- 三条采集分支没有被写入同一个并行 ready group，或 work unit 没有隔离输出目录。
- `stage2_execution_plan.yaml` 没有显式 `parallel_dag.nodes[]` 与 `parallel_dag.edges[]`，或实际发现的数据源没有被展开成具体 DAG 节点。
- 任一 DAG 节点缺少精确 `subskill_path`，或 `subskill_path` 与数据源类别不匹配。
- 任一可执行采集 DAG 节点缺少 `tmux_required: true`、`monitor_interval_seconds: 15`、`tmux_session_name`、`log_path` 或 `monitoring_log_path`。
- 任一 DAG 边跨越不同 `work_unit_id` 且不是本类别 summary barrier，导致数据源之间被错误串行化。
- 实际计划中仍保留 `<dataset_id>`、`<simulator_id>`、`<task_family>` 等占位符。

## 输出

- `nodes/stage2-plan-generation/stage2_execution_plan.yaml`
- 节点执行记录文件
