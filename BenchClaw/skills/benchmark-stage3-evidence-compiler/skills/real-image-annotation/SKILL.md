# Node Skill — 真实图片标注

## 输入

- `real_image_clean_bundle`

## 处理

1. 按 Stage3 执行计划处理输入数据。
2. 保持媒体、标注、GT、证据记录之间的可追溯关系。
3. 对低置信标注、字段冲突、缺失媒体、无效 GT 写入阻塞记录或人工复核队列。
4. 不把模型生成文本直接当作 GT；真实图片与已有 benchmark 的半监督标注必须带来源、置信与复核状态；仿真器 GT 必须来自仿真器状态或可验证计算。

## 输出

- `data_17_annotated_real_image_bundle`
- 节点执行记录文件
