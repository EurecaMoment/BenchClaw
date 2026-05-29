# Stage1 中间文件契约

本文件是 Stage1 中间文件含义的单一维护点。各子 skill 可以保留简短摘要，但字段、章节和边界以本文为准，避免把同一套说明复制到多个文件里。

## 通用约定

- 每个节点只写自己的 `stage1/<node_dir>/` 目录。
- 每个业务产物都必须能追踪来源，`source_refs` 可以是用户输入、父节点文件路径、文献 ID、仿真器能力卡、工具能力卡或文件章节。
- Markdown 文件用于人读的判断、理由和风险；JSON/YAML/CSV/JSONL 文件用于后续节点稳定解析。
- 缺失信息要显式写成 `unknown`、空数组或待确认项，不能用猜测补齐。
- `DONE.json` 是调度状态文件，不承载新的业务结论。

## DONE.json

每个节点完成后都要写 `DONE.json`。它只说明该节点是否完成、读了哪些输入、写了哪些输出、是否被阻塞，以及质量门结果。格式由 `contracts/DONE.schema.json` 维护。

## 00 idea 接收与边界冻结

- `stage1/00_idea/idea_card.md`
  - 含义：冻结用户原始 benchmark idea 的人读卡片，是后续解释的基准。
  - 消费方：`01`、`12`。
  - 至少包含：用户原始表述、规范化摘要、目标领域、期望 benchmark 类型、显式约束、可用资源、禁区、开放问题、来源引用。
  - 边界：不做文献研究，不新增用户没有表达的研究方向。
- `stage1/00_idea/scope_seed.json`
  - 含义：供后续节点解析的机器可读范围种子。
  - 消费方：`01`、`12`。
  - 至少包含：`benchmark_domain`、`benchmark_type`、`target_subject`、`target_capabilities_seed`、`input_modalities`、`output_expectations`、`hard_constraints`、`available_resources`、`out_of_scope`、`open_questions`、`source_refs`。
  - 边界：只编码用户 idea 和显式约束，不编码推测出的最终能力维度。

## 01 意图理解

- `stage1/01_intent/intent_interpretation.md`
  - 含义：把冻结 idea 解释成后续分支共用的评测意图。
  - 消费方：`02`、`03`、`12`。
  - 至少包含：被评测主体、目标能力、输入模态、输出形式、评测约束、边界、失败模式、默认假设、来源引用。
  - 边界：不是最终能力维度，也不是 benchmark 草稿。
- `stage1/01_intent/ambiguity_log.md`
  - 含义：不阻塞流程的歧义登记表。
  - 消费方：`03`、`12`。
  - 至少包含：歧义 ID、歧义点、可能解释、影响范围、当前默认假设、需要用户确认的问题、来源引用、状态。
  - 边界：记录不确定性，不在这里解决全部歧义。

## 02 query 改写

- `stage1/02_query/query_pack.json`
  - 含义：可执行的检索 query 集合。
  - 消费方：`04`、`12`。
  - 至少包含：`query_id`、`query_text`、`language`、`query_type`、`intent_link`、`expected_evidence`、`priority`、`negative_terms`、`source_refs`。
  - 边界：query 不是事实证据，不能被后续直接当成文献结论。
- `stage1/02_query/search_strategy.md`
  - 含义：解释为什么这样检索，以及如何筛选。
  - 消费方：`04`、`12`。
  - 至少包含：检索空间、query 分组、纳入/排除标准、去重规则、优先级、停止条件、风险。
  - 边界：不评价具体文献内容。

## 03 意图理解扩写文档

- `stage1/03_intent_doc/expanded_intent.md`
  - 含义：把意图扩写成可供文献分析、能力拆解和模板设计共用的结构化文档。
  - 消费方：`07`、`08`、`12`。
  - 至少包含：construct、可测行为、输入输出、边界条件、预期证据类型、反例、默认假设、来源引用。
  - 边界：不做最终模板设计，也不作为数据/仿真器或标注工具能力来源。
- `stage1/03_intent_doc/construct_hypotheses.md`
  - 含义：候选 construct 假设清单，用于让后续分支验证或淘汰。
  - 消费方：`07`、`08`、`12`。
  - 至少包含：假设 ID、construct 名称、可测声明、形成理由、期望证据、可能证伪方式、相关歧义、来源引用。
  - 边界：是假设，不是已经确认的能力维度，也不是外部能力文档。

## 04 搜索可用文献

- `stage1/04_literature_search/literature.db`
  - 含义：候选文献、benchmark、指标或工具材料的规范化 SQLite 真相源，至少包含 `candidate_papers` 表，每行一条候选记录。
  - 消费方：`07`、`12`。
  - 表 `candidate_papers` 字段建议：`paper_id`(主键)、`title`、`year`、`venue`、`url_or_id`、`matched_query`、`candidate_use`、`risk_note`、`confidence`、`source_refs_json`。
  - 边界：只是候选召回真相源，不是设计证据。
- `stage1/04_literature_search/candidate_papers.sqlite_export.jsonl`
  - 含义：`literature.db.candidate_papers` 的兼容性 JSONL 导出，仅用于人工审阅或与不支持 SQLite 的下游互通；不是真相源。
  - 消费方：`07`、`12`（只读对照）。
  - 至少包含：`title`、`year`、`venue`、`url_or_id`、`matched_query`、`candidate_use`、`risk_note`、`confidence`、`source_refs`。
  - 边界：与 `literature.db` 内容不一致时以 DB 为准；不允许只产出 JSONL 而不写 DB。
- `stage1/04_literature_search/search_log.md`
  - 含义：检索过程审计记录。
  - 消费方：`07`、`12`。
  - 至少包含：执行的 query、检索源、结果数量、粗筛规则、去重决策、失败或空结果 query、偏差风险。
  - 边界：记录过程，不写综述结论。

## 05 数据/仿真器能力描述

优先输入来源：

- `BENCHCLAW_ROOT/simulatorCards`：仿真器能力描述 skill/card。
- `BENCHCLAW_ROOT/benchmarkDatasetCards`：已有 benchmark 数据集描述 skill/card。
- `BENCHCLAW_ROOT/realDataCards`：真实数据源描述 skill/card。

- `stage1/05_data_capability/simulator_capability_matrix.md`
  - 含义：从外部数据/仿真器能力文档整理出的可用数据源和仿真器能力人读矩阵。
  - 消费方：`08`、`10`、`12`。
  - 至少包含：来源类型（simulator、benchmark_dataset、real_data）、数据源/仿真器名称、场景、对象、动作、关系、数据模态、GT 字段、可观测变量、可复现实验变量、执行或复用限制、许可/访问限制、来源引用。
  - 边界：只描述外部文档支持的能力，不选择最终仿真器，不从 `03` 推断能力。
- `stage1/05_data_capability/observable_gt_fields.json`
  - 含义：从外部数据/仿真器能力文档整理出的可观测字段和 GT 字段机器可读清单。
  - 消费方：`08`、`10`、`12`。
  - 至少包含：`field_id`、`name`、`type`、`unit`、`source_type`、`source_simulator_or_dataset`、`availability`、`extraction_method`、`reliability`、`capability_links`、`limitations`、`license_or_access_constraints`、`source_refs`。
  - 边界：不声明输入材料未支持的字段，不从 `03` 推断字段。

## 06 标注能力描述

优先输入来源：

- `BENCHCLAW_ROOT/annotation-tool`：标注工具能力、I/O、部署和限制说明 skill 文档。

- `stage1/06_annotation_capability/annotation_capability_matrix.md`
  - 含义：从外部标注工具能力文档整理出的自动/半自动标注工具能力人读矩阵。
  - 消费方：`08`、`11`、`12`。
  - 至少包含：工具、支持任务、输入、输出、置信度语义、批处理方式、部署约束、失败条件、局限、来源引用。
  - 边界：只描述外部文档支持的能力，不做最终工具选择，不从 `03` 推断能力。
- `stage1/06_annotation_capability/tool_io_contracts.md`
  - 含义：从外部标注工具能力文档整理出的工具输入输出合同，描述后续如何调用和解释工具结果。
  - 消费方：`11`、`12`。
  - 至少包含：工具 ID、输入 schema、输出 schema、置信度解释、吞吐/部署约束、失败模式、后处理需求、来源引用。
  - 边界：不把大模型主观判断写成客观标注能力，不从 `03` 推断 I/O 能力。

## 07 文献调研分析报告

- `stage1/07_literature_analysis/literature_analysis_report.md`
  - 含义：围绕 benchmark 设计问题组织的文献分析报告。
  - 消费方：`08`、`09`、`12`。
  - 至少包含：已有 benchmark、construct 定义、任务模板、指标、质量控制、失效模式、缺口、对本项目的影响、来源引用。
  - 边界：不是泛泛综述，不能用文献替代用户意图。
- `stage1/07_literature_analysis/benchmark_design_evidence.md`
  - 含义：可被能力拆解和模板设计引用的证据账本。
  - 消费方：`08`、`09`、`12`。
  - 至少包含：证据 ID、支持的设计决策类型、文献来源、证据强度、限制、关联 construct 或能力维度、风险。
  - 边界：每条证据必须说明支持哪个设计决策。

## 08 能力拆解文档

- `stage1/08_capability_decomposition/capability_dimensions.md`
  - 含义：确认后的可测能力维度说明，并索引该维度下的细粒度能力考点。
  - 消费方：`09`、`10`、`11`、`12`。
  - 至少包含：维度 ID、construct definition、用户意图链接、文献证据、可观测证据/GT 字段、所需标注能力、候选任务族、测量风险、依赖关系、checkpoint_refs。
  - 边界：不能产生没有 GT 或标注支撑的维度。
- `stage1/08_capability_decomposition/capability_checkpoints.yaml`
  - 含义：细粒度能力考点清单，用于把能力维度进一步拆成可被题目模板覆盖、可被证据字段观测、可被评分规则测量的最小单元。
  - 消费方：`09`、`12`。
  - 至少包含：`checkpoint_id`、`dimension_id`、`checkpoint_name`、`measurable_behavior`、`required_evidence`、`candidate_template_affordances`、`scoring_observation`、`measurement_risk`、`source_refs`。
  - 边界：每个考点必须且只能属于一个能力维度；考点不是题目模板，也不是指标本身。
- `stage1/08_capability_decomposition/capability_dependency_graph.json`
  - 含义：能力维度和细粒度能力考点之间依赖关系的机器可读图。
  - 消费方：`09`、`10`、`11`、`12`。
  - 至少包含：`nodes` 列表和 `edges` 列表；节点含 `id`、`node_type`（dimension 或 checkpoint）、`label`、`evidence_refs`，边含 `from`、`to`、`type`、`reason`、`source_refs`。
  - 边界：只表达能力依赖，不表达执行排期。

## 09 初版模板集与指标集

- `stage1/09_templates_metrics/template_set.yaml`
  - 含义：初版评测 item/template 集合。
  - 消费方：`12`，并通过 `12` 间接供 `13` 使用。
  - 至少包含：`template_id`、`capability_dimension`、`checkpoint_refs`、`task_family`、`question_form`、`required_gt_fields`、`required_annotation_outputs`、`anti_shortcut_constraints`、`validity_checks`、`metric_refs`。
  - 边界：每个模板必须且只能属于一个能力维度；一个模板可以覆盖多个考点，考点可以被多个模板复用；模板不应无根据绑定单一仿真器。
- `stage1/09_templates_metrics/metric_set.yaml`
  - 含义：可计算指标或待淘汰指标候选集合。
  - 消费方：`12`，并通过 `12` 间接供 `13` 使用。
  - 至少包含：`metric_id`、`capability_dimension`、`target_behavior`、`input_fields`、`score_type`、`computation`、`failure_cases`、`calibration_need`。
  - 边界：主观评分必须标为待淘汰或需人工审计，不得伪装成可计算指标。
- `stage1/09_templates_metrics/evidence_contracts.yaml`
  - 含义：模板和指标运行时所需证据的机器可读合同。
  - 消费方：`12`，并通过 `12` 间接供 `13` 使用。
  - 至少包含：`contract_id`、`capability_dimension`、`checkpoint_refs`、`template_refs`、`metric_refs`、`required_gt_fields`、`required_annotation_outputs`、`validation_checks`、`provenance_requirements`、`fallback_policy`、`source_refs`。
  - 边界：只声明证据需求，不选择具体执行工具。
- `stage1/09_templates_metrics/q_matrix.csv`
  - 含义：模板-考点 Q-matrix，供后续教育学分析使用。
  - 消费方：`12`，并通过 `12` 间接供 `13` 使用。
  - 至少包含：第一列 `template_id`，第二列 `capability_dimension`，后续每列为一个 `checkpoint_id`，单元格取值为 `0` 或 `1`。
  - 边界：行必须覆盖 `template_set.yaml` 中所有模板；列必须来自 `capability_checkpoints.yaml`；模板不得跨维度覆盖考点，跨维度设计必须拆成多个模板。

## 10 选择的模拟器

- `stage1/10_simulator_selection/selected_simulators.md`
  - 含义：仿真器选择理由、覆盖范围和缺口说明。
  - 消费方：`12`。
  - 至少包含：选中仿真器、排除仿真器、覆盖的能力维度、缺口、回退方案、风险、来源引用。
  - 边界：不能因知名度选择，必须能提供必要 GT 或可观测变量。
- `stage1/10_simulator_selection/simulator_routing.json`
  - 含义：能力维度或模板到仿真器的机器可读路由表。
  - 消费方：`12`，并通过 `12` 间接供 `13` 使用。
  - 至少包含：`route_id`、`capability_dimension`、`template_refs`、`simulator_id`、`required_gt_fields`、`supported_variables`、`fallback_simulator_ids`、`unsupported_notes`、`source_refs`。
  - 边界：不声明能力矩阵未支持的路由。

## 11 选择的标注工具

- `stage1/11_annotation_tool_selection/selected_annotation_tools.md`
  - 含义：标注工具选择理由、用途和回退说明。
  - 消费方：`12`。
  - 至少包含：选中工具、排除工具、覆盖的能力维度或证据字段、I/O、置信度用法、失败回退、风险、来源引用。
  - 边界：不是模型推荐清单。
- `stage1/11_annotation_tool_selection/tool_routing.json`
  - 含义：证据字段、模板或能力维度到标注工具的机器可读路由表。
  - 消费方：`12`，并通过 `12` 间接供 `13` 使用。
  - 至少包含：`route_id`、`capability_dimension`、`evidence_field_or_output`、`template_refs`、`tool_id`、`input_contract_ref`、`output_contract_ref`、`confidence_use`、`fallback_tool_ids`、`human_review_needed`、`source_refs`。
  - 边界：不能绕过 `06` 的工具能力合同。

## 12 benchmark 草稿

- `stage1/12_benchmark_draft/benchmark_draft.md`
  - 含义：Stage1 的 benchmark 设计草稿，是 `13` 的唯一业务输入。
  - 消费方：`13`。
  - 至少包含：benchmark 名称、目标、范围、能力维度、细分能力考点、模板与指标、模板-考点 Q-matrix 摘要、数据/仿真器方案、证据合同、标注工具方案、质量门、风险、未解歧义、追踪摘要。
  - 边界：汇总 `00` 到 `11`，不重新发明能力维度。
- `stage1/12_benchmark_draft/design_traceability_table.csv`
  - 含义：设计决策到来源证据的追踪表。
  - 消费方：`13`。
  - 至少包含列：`decision_id`、`design_decision`、`decision_type`、`source_nodes`、`evidence_files`、`evidence_ids_or_sections`、`risk`、`confidence`、`downstream_stage`。
  - 边界：只记录可追踪的设计决策，不补写无来源结论。

## 13 执行计划

- `stage1/13_execution_plan/execution_plan.md`
  - 含义：Stage2/Stage3/Stage4 的可执行任务计划。
  - 消费方：Stage1 最终交付和后续阶段。
  - 至少包含：工作包、依赖关系、并行任务、阻塞任务、质量门、失败回退、里程碑、输入输出合同。
  - 边界：必须从 `12` 抽取，不直接读取 `08`、`09`、`10`、`11`。
- `stage1/13_execution_plan/stage2_handoff.yaml`
  - 含义：交给 Stage2 的机器可读合同。
  - 消费方：Stage2 调度器或实现者。
  - 至少包含：`benchmark_name`、`capability_dimensions`、`capability_checkpoints`、`simulator_routing`、`annotation_tool_routing`、`template_routing`、`q_matrix_ref`、`evidence_contracts`、`quality_gates`、`parallel_jobs`、`blocking_jobs`。
  - 边界：其中 routing、Q-matrix 引用和 evidence contracts 必须来自 `12` 的草稿和追踪表。
