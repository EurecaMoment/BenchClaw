# BenchClaw Stage2 Skill Pack

这是根据手绘 Stage2「数据采集」流程整理的 Opencode-ready Skill 包。

核心结构：

```text
13 执行计划入口
14 各仿真器 skill 注册/适配
15 真实图片数据采集
16 已有 benchmark 数据采集
17 仿真器多模态 GT 数据采集
```

依赖关系：

```text
13.parents = []
14.parents = []
15.parents = [13]
16.parents = [13]
17.parents = [13,14]
```

Stage2 终端输出为 15、16、17 三个独立数据源目录，不强行合并。
