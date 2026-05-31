# benchmark-stage5-eval

读取 Stage4 全量 benchmark 数据集，完成真实模型评测或读取用户提供的已物化预测文件，生成最终评测报告。

该目录是生产 skill 定义，不包含总驱动脚本。节点由 `dag.json` 与 `skills/<node-id>/SKILL.md` 调度。
