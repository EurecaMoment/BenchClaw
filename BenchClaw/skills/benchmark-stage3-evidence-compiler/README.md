# BenchClaw Stage3 Opencode-ready Skill Pack

本包对应手绘图中的 **Stage3：数据清洗、统一格式与半监督 GT 标注**。

核心设计不是把 15/16/17/18/19/20 写成串行链，而是把三类 Stage2 输出作为三个并行输入源，分别执行：

```text
Stage2-15 -> 21 统一格式 -> 24 Data-Juicer清洗 -> 18 真实图+半监督GT
Stage2-16 -> 22 统一格式 -> 25 Data-Juicer清洗 -> 19 benchmark图+官方标签/半监督GT
Stage2-17 -> 23 统一格式 -> 26 Data-Juicer清洗 -> 20 仿真器+privileged GT
                                    ↑
                      27 半监督标注工具注册/契约
```

其中 `27` 与三个输入源并行准备；`18/19` 依赖 `27`，`20` 不依赖 `27`，因为仿真器 GT 不应被小模型覆盖。

运行前：

```bash
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```

结束检查：

```bash
python scripts/check_stage3_outputs.py --workspace WORKSPACE_ROOT
```
