# Node Skill — 本阶段执行计划生成

## 输入

- `data_13_execution_plan`

## 处理

1. 读取 Stage1 执行计划，不重写总目标。
2. 分解出真实图片、已有 benchmark、仿真器三条采集分支的数量、字段、工具、目录和质量门。
3. 写入本阶段执行计划，供三条分支并行消费。

## 输出

- `nodes/stage2-plan-generation/stage2_execution_plan.yaml`
- 节点执行记录文件
