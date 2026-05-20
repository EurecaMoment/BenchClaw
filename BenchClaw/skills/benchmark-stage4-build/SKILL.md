# BenchClaw Stage4 Skill — 评测集合成、指标代码与质量过滤（Opencode-ready DAG 版）

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 路径入口校验

开始执行前必须先确认：

- 本次收到的 `BENCHCLAW_ROOT` 与 `WORKSPACE_ROOT` 与上游 pipeline 冻结值完全一致，禁止 Stage4 自行重新猜测或覆盖。
- `BENCHCLAW_ROOT` 必须解析为当前 BenchClaw 项目根目录。
- `WORKSPACE_ROOT` 必须是位于 BenchClaw 根外部的独立工作目录，不能落在 `BENCHCLAW_ROOT` 内，不能等于 `BENCHCLAW_ROOT`，不能写成 `BENCHCLAW_ROOT/workspace*`。
- 若路径校验失败，Stage4 必须立即阻塞并报错，不能继续读取 Stage1/Stage3 或写任何 Stage4 输出。

## 0. 任务边界

本 Skill 对应手绘图中的 **Stage4**。它接收：

1. `09`：Stage1 的初版模板集与指标集；
2. `18`：Stage3 的真实图片 + 半监督 GT；
3. `19`：Stage3 的已有 benchmark 图文/QA/标签 + 半监督 GT；
4. `20`：Stage3 的仿真器多模态数据 + privileged GT。

Stage4 的目标是把模板、证据、GT 和指标约束转成 **可评测、可追踪、可执行评分的最终 benchmark 数据包**。

按你的要求：

- `33 小批量合成`：**留空**；
- `34 灰度测试`：**留空**；
- 其他节点正常实现为 Opencode 可执行的子 Skill 契约。

严禁把本阶段写成 `09→18→19→20→28→...` 的串行链。编号是节点 ID，不是执行顺序。

---

## 1. DAG 结构

```text
        ┌────┐        ┌────┐        ┌────┐        ┌────┐
        │ 09 │        │ 18 │        │ 19 │        │ 20 │
        │模板│        │真图│        │旧bench│      │仿真GT│
        └─┬──┘        └──┬─┘        └──┬─┘        └──┬─┘
          │              └────────┬────┴─────────────┘
          v                       v
       ┌────┐                  ┌────┐
       │ 28 │                  │ 29 │
       │模板│                  │证据│
       │契约│                  │池  │
       └─┬──┘                  └─┬──┘
         └──────────────┬────────┘
                        v
                     ┌────┐
                     │ 30 │ 模板-证据绑定
                     └─┬──┘
              ┌────────┴────────┐
              v                 v
           ┌────┐            ┌────┐
           │ 31 │            │ 32 │
           │题型│            │答案│
           │扩展│            │程序│
           └──┬─┘            └─┬──┘
              └──────┬────────┘
                     v
                  ┌────┐
                  │ 33 │ 小批量合成：留空
                  └─┬──┘
                    v
                  ┌────┐
                  │ 34 │ 灰度测试：留空
                  └─┬──┘
                    v
                  ┌────┐
                  │ 35 │ 质量过滤/选择策略
                  └─┬──┘
                    v
                  ┌────┐
                  │ 36 │ 全量合成
                  └─┬──┘
                    v
                  ┌────┐
                  │ 37 │ 最终数据包
                  └────┘
```

等价依赖表：

```text
09.parents = []
18.parents = []
19.parents = []
20.parents = []
28.parents = [09]
29.parents = [18, 19, 20]
30.parents = [28, 29]
31.parents = [30]
32.parents = [30]
33.parents = [31, 32]    # 留空，只写 WAIVED.json
34.parents = [33]        # 留空，只写 WAIVED.json
35.parents = [31, 32, 34]
36.parents = [31, 32, 35]
37.parents = [36]
terminal_nodes = [37]
```

---

## 2. Opencode 调度要求

### 2.1 必须按 ready-set 执行

启动前执行：

```bash
cat dag.json
cat contracts/node_io_contracts.json
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```

初始 ready-set 必须是：

```text
READY: 09 18 19 20
```

如果 Opencode 支持 subagent，应并行启动：

```text
subagent-09 -> skills/09-stage1-template-metric-ingest/SKILL.md
subagent-18 -> skills/18-stage3-real-image-gt-ingest/SKILL.md
subagent-19 -> skills/19-stage3-benchmark-image-gt-ingest/SKILL.md
subagent-20 -> skills/20-stage3-simulator-clean-gt-ingest/SKILL.md
```

之后按 ready-set 推进：

```text
L0: 09 | 18 | 19 | 20
L1: 28 | 29
L2: 30
L3: 31 | 32
L4: 33   # blank / waived
L5: 34   # blank / waived
L6: 35
L7: 36
L8: 37
```

### 2.2 不支持 subagent 时的降级

允许在同一 ready-set 内顺序执行，但不得改变依赖关系。尤其禁止：

```text
09 -> 18 -> 19 -> 20 -> 28 -> 29
```

---

## 3. 总输入

默认读取：

```text
WORKSPACE_ROOT/stage1/09-initial-template-metric-set/
WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/
WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/
WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/
```

如果路径不同，在以下文件声明映射：

```text
WORKSPACE_ROOT/config/stage4_input_paths.json
```

---

## 4. 总输出

```text
WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/
  EVALSET_DATASET/
    README.md
    data/
      test.jsonl
    images/
    metrics/
      evaluate.py
  FINAL_BENCHMARK_CARD.md
  STAGE4_REPORT.md
  DONE.json
```

其中 `EVALSET_DATASET/` 是最终 benchmark 的类 HuggingFace 落盘目录，要求如下：

1. `README.md` 用于描述 benchmark 任务边界、数据字段、媒体组织、评测入口和许可证/限制；
2. `data/test.jsonl` 是面向评测消费的主数据文件；
3. `images/` 存放 `data/test.jsonl` 所引用的图像媒体资产，必须在 workspace 内真实落盘；
4. `metrics/evaluate.py` 提供可执行的本地评测入口，但不得是空文件、占位文件或只写 TODO。

最终完成条件：

```bash
python scripts/check_stage4_outputs.py --workspace WORKSPACE_ROOT
```

---

## 5. 关键原则

1. **GT 不得由题面生成**：答案必须来自 Stage3 evidence/GT 或可执行 answer program。
2. **模板必须绑定证据**：每道题必须有 `item -> blueprint -> binding -> evidence -> source_gt` 追踪链。
3. **小批量合成与灰度测试留空**：`33` 和 `34` 只能输出 `WAIVED.json`，不得偷偷实现。
4. **pilot 依赖指标不得伪造**：CTT/IRT、CDM/Q-matrix、Qwen-scope/Gemma-scope/Llama-scope 等需要模型响应或 pilot 数据的指标只能写成 deferred hooks。
5. **全量合成必须可复现**：每个 item 必须记录 seed、template_id、source_record_id、gt_source_type、answer_program_id、metric_id。
6. **评测资产必须可消费**：Stage4 不能只生成 `eval_dataset.jsonl`、路径字符串和说明文档；凡被 benchmark item 引用的图像、视频、深度图、官方标签或融合证据，必须在 workspace 内有稳定可读的物化副本或可直接消费的打包路径。
7. **不得凭空补题**：若上游 Stage2/Stage3 没有真实落盘的媒体、标注或 GT 证据，Stage4 必须阻塞，不能凭模板、样例、摘要、外部绝对路径或人工编造答案继续合成 item。
8. **最终 benchmark 必须落成类 HuggingFace 文件夹**：`WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/EVALSET_DATASET/` 必须包含 `README.md`、`data/test.jsonl`、`images/`、`metrics/evaluate.py`，并可被科研评测流程直接消费。

---

## 6. 子 Skill 列表

```text
skills/09-stage1-template-metric-ingest/SKILL.md
skills/18-stage3-real-image-gt-ingest/SKILL.md
skills/19-stage3-benchmark-image-gt-ingest/SKILL.md
skills/20-stage3-simulator-clean-gt-ingest/SKILL.md
skills/28-template-contract-normalization/SKILL.md
skills/29-evidence-pool-normalization/SKILL.md
skills/30-template-evidence-binding/SKILL.md
skills/31-question-form-expansion/SKILL.md
skills/32-answer-program-metric-code/SKILL.md
skills/33-small-batch-synthesis-placeholder/SKILL.md
skills/34-gray-test-placeholder/SKILL.md
skills/35-quality-filter-and-selection/SKILL.md
skills/36-full-scale-synthesis/SKILL.md
skills/37-benchmark-artifact-pack/SKILL.md
```

---

## 7. 强制检查

```bash
python scripts/validate_dag.py dag.json
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
python scripts/check_stage4_outputs.py --workspace WORKSPACE_ROOT
```

若 `validate_dag.py` 发现该图被改写为单链串行图，本 Skill 必须停止执行。
