# benchmark-stage3-evidence-compiler

读取 Stage2 已物化数据，分别完成真实图片、已有 benchmark、仿真器数据的清洗、标注与 GT 整理。

该目录是生产 skill 定义，不包含总驱动脚本。节点由 `dag.json` 与 `skills/<node-id>/SKILL.md` 调度。
