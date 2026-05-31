# benchmark-stage2-data-collect

根据 Stage1 执行计划，分别采集并分析真实图片、已有 benchmark 和仿真器数据，并把后续阶段需要消费的媒体、元数据、标注需求与 GT 物化到 workspace。

该目录是生产 skill 定义，不包含总驱动脚本。节点由 `dag.json` 与 `skills/<node-id>/SKILL.md` 调度。
