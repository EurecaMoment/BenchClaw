# BenchClaw
BenchClaw是一套面向 Benchmark 构建、评测与维护的 Codex/OpenCode 技能工作流集合。它通过将流程拆为草案设计、数据采集、数据清洗、评测集构建、模型评测和诊断维护六个阶段，并为每阶段规定输入输出、质量门禁、目录契约、lineage 与回滚策略。其目标是让智能体从粗略 benchmark idea 出发，标准化、可复现、可审计地生成评测方案、数据、指标、结果和报告，并在失败时定位最小回滚点，形成流程诊断与技能修订闭环。 

## 项目简介

本项目不是传统的软件应用，而是一组面向智能体的工作流规则。每个 `SKILL.md` 都描述了一个具体阶段或任务的执行方式，包括应该读取什么输入、生成什么输出、如何判断质量是否合格，以及失败时如何回退和修复。

项目的核心目标是让 benchmark 构建过程更加：

- 标准化
- 可复现
- 可审计
- 可维护
- 可回滚

## 流程概览

完整流程由顶层 `benchmark-pipeline` 编排，主要包括六个阶段：

1. **草案设计**  
   从 benchmark idea 出发，明确评测目标、能力维度、数据来源和整体执行计划。

2. **数据采集**  
   根据设计方案收集或接入所需数据，包括仿真数据、已有数据集和真实数据。

3. **数据清洗**  
   对采集到的数据进行清洗、筛选和整理，保留数据来源与处理记录。

4. **评测集构建**  
   生成正式评测样本、评测 schema 和指标代码，并完成基础验证。

5. **模型评测**  
   先进行小规模灰度评测，确认流程可靠后再执行全量评测并生成结果报告。

6. **诊断与维护**  
   对整个流程进行复盘，定位问题来源，必要时修订 skill 并进行回归验证。

## 目录结构

```text
.
+-- benchmark-pipeline/
+-- benchmark-stage1-draft/
+-- benchmark-stage2-data-collect/
+-- benchmark-stage3-data-clean/
+-- benchmark-stage4-build/
+-- benchmark-stage5-eval/
`-- benchmark-stage6-diagnosis-maintenance/
````

每个目录下的 `SKILL.md` 是对应阶段的主要说明文件。

## 使用方式

推荐从顶层 pipeline 开始：

```text
/benchmark-pipeline "你的 benchmark idea"
```

也可以单独调用某个阶段：

```text
/benchmark-stage1-draft "你的 benchmark idea"
/benchmark-stage2-data-collect "$STAGE1_DIR"
/benchmark-stage3-data-clean "$STAGE2_DIR"
/benchmark-stage4-build "$STAGE3_DIR"
/benchmark-stage5-eval "$STAGE4_DIR"
/benchmark-stage6-diagnosis-maintenance "$WORKSPACE_ROOT"
```

## 工作区约定

每次运行会使用独立工作区，避免不同 benchmark 任务之间相互污染：

```text
~/bench_workspace/workspace{i}/
```

典型输出包括阶段结果、质量报告、评测报告和最终 pipeline 报告。

## 质量控制

项目强调“先检查，再推进”。每个阶段都需要产生可检查的结果，只有通过质量门禁后才能进入下一阶段。

常见状态包括：

```text
PASS          可以继续
NEEDS_REVIEW 需要人工确认
FAIL          必须修复或回滚
```

如果某一阶段失败，流程应定位到具体阶段或产物进行修复，而不是默认从头重跑。

## 主要产物

流程完成后，通常会生成：

* benchmark 草案
* 数据 schema
* 数据质量报告
* 清洗后数据清单
* 评测集 schema
* 指标代码
* 灰度评测报告
* 全量评测报告
* 流程诊断报告
* 最终 pipeline 报告

## 维护原则

维护本项目时应优先保持流程清晰、规则稳定和阶段边界明确。修改 skill 时应尽量采用最小改动，并确保上下游阶段仍然能够正常衔接。

## 相关文档

* [项目描述](./DESCRIPTION.md)
* [顶层 Pipeline 技能](./benchmark-pipeline/SKILL.md)
* [Stage 1 技能](./benchmark-stage1-draft/SKILL.md)
* [Stage 2 技能](./benchmark-stage2-data-collect/SKILL.md)
* [Stage 3 技能](./benchmark-stage3-data-clean/SKILL.md)
* [Stage 4 技能](./benchmark-stage4-build/SKILL.md)
* [Stage 5 技能](./benchmark-stage5-eval/SKILL.md)
* [Stage 6 技能](./benchmark-stage6-diagnosis-maintenance/SKILL.md)

```
```
