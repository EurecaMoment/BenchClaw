# BenchClaw Reference Templates

这是一个**极简版参考模板文件夹**，只包含 `templates/`，没有指标代码、schema、测试脚本或复杂工程目录。

用途：

- 给每个 benchmark 制造流程设计独有题型时参考。
- 每个 JSON 都是一个可改写的题型模板。
- `answer_rule` 只描述 ground truth 应该如何由仿真器状态、几何、导航、渲染或轨迹计算得到。
- 不建议用 LLM 生成 ground truth。

字段说明：

- `template_id`: 模板唯一名称。
- `family`: 模板族，例如 `egocentric_spatial`、`counterfactual_egomotion`、`navigation_topology`。
- `question_template`: 可填槽的问题文本。
- `options`: 标准选项。
- `placeholders`: 问题文本中的变量示例。
- `required_state`: 生成和校验答案所需的仿真器状态。
- `answer_rule`: ground truth 计算逻辑描述。
- `quality_checks`: 生成样本时必须检查的质量约束。

当前包含 48 个模板。
