# benchmark-stage4-build

读取 Stage1 的模板/指标初稿与执行计划，以及 Stage3 的三类已标注数据，生成模板、指标、代码，小批量合成灰度验证，并最终合成全量 benchmark 数据集。

该目录是生产 skill 定义，不包含总驱动脚本。节点由 `dag.json` 与 `skills/<node-id>/SKILL.md` 调度。
