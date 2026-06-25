# Stage4 Parent Runtime Code

本目录只放**数据集无关的父类模板代码**。Stage4 的 `template-compilation` 节点不得把这里当作固定 benchmark 生成器原样提交；所有执行模型的正确用法都是同一条：

1. 先读取 Stage3 数据与 GT，生成 `field_catalog.yaml` 与 `evidence_index.jsonl`；
2. 只在必要时生成一个很薄的 `GenericGTAdapter` 子类，改写字段映射；
3. 从 `build_default_template_registry()` 中选择可由当前 GT 唯一支撑的模板父类；
4. 生成 `scripts/generate_items.py`，该脚本导入本父类运行时并绑定当前数据集；
5. 立即运行 smoke / grey synthesis，至少真实产出 1 条 benchmark item 后才允许写 DONE。

父类运行时已经内置：异构 GT 读取、bbox/centroid/area/depth 规范化、overlay 标识、选择题契约校验、灰度 CLI、基础 exact-choice 评分。

本目录不包含任何模型特供逻辑；执行者能力差异只能表现为是否通过质量门，不能改变流程或放宽契约。
