# benchmark-stage3-evidence-compiler

读取 Stage2 已物化数据，按真实图片、已有 benchmark、仿真器三类数据源分别完成清洗、标注与 GT 整理。

该目录是生产 skill 定义，不包含总驱动脚本。外显节点由 `dag.json` 与已注册的显式 skill 名调度；清洗和标注只作为每个数据源节点内部的已注册子 skill 执行。`skills/<node-id>/SKILL.md` 与 `subskills/.../SKILL.md` 只作为源码落盘位置，不作为 opencode 运行时的首选调度键。
