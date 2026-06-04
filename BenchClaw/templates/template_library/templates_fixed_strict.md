# BenchClaw 严格修正版图文评测模板库

本文件是可直接给 agent 使用的修正版模板库。它不是审查报告：所有模板已经被固定为三种结果：可选、扩展条件可选、废弃锁定。agent 默认只读 `strict_core`，不会让人再手工判断。

## 全局硬约束

- 禁止三选不可答、无法判断、信息不足、是否可回答类题目。
- 禁止裸整数、裸浮点和 JSON 数字计数；所有数量/距离/深度/面积数值只能做区间选择。
- 禁止题干出现 GT、depth_median、object_id、可见物体列表等隐藏元数据字段。
- 所有实例候选题必须使用图像 overlay 的 A/B/C/D 标注，且候选项显示名不能重复到不可区分。
- 所有题目必须有唯一答案；排序题必须过滤并列，区间题必须过滤边界样本。

## 收束后的题型

| 题型 | 用途 |
|---|---|
| QT1_SINGLE_CHOICE | 单选候选选择 |
| QT2_MULTI_SELECT | 多选集合选择 |
| QT3_BINARY_OR_COMPARISON | 是/否、A/B 二选比较 |
| QT4_INTERVAL_CHOICE | 所有数值类问题的区间选择 |
| QT5_ORDERING | 无并列排序 |
| QT6_STRUCTURED_MATCH | 受限结构化匹配；默认不开放裸数字 JSON |

## 收束后的能力维度

| 维度 | 名称 |
|---|---|
| A1 | 可见对象/类别识别 |
| A2 | 计数与集合规模 |
| A3 | 图像平面空间关系 |
| A4 | 深度/远近/距离层次 |
| A5 | 可见尺度与 3D 尺寸 |
| A6 | 多帧时序与轨迹 |
| A7 | 自我中心/姿态/3D 坐标 |
| A8 | 证据冲突与组合约束 |

## 默认核心 strict_core

| ID | 状态 | 题型 | 能力 | 修正后题干/处理 |
|---|---|---|---|---|
| T001 | CORE_SELECTABLE | QT3_BINARY_OR_COMPARISON | A1_VISIBLE_OBJECT_CATEGORY | 当前图像中是否可见 `{object_category}`？ |
| T002 | CORE_SELECTABLE | QT2_MULTI_SELECT | A1_VISIBLE_OBJECT_CATEGORY | 从候选项中选择当前图像中可见的所有物体类别。 |
| T006 | CORE_SELECTABLE | QT3_BINARY_OR_COMPARISON | A1_VISIBLE_OBJECT_CATEGORY | 当前图像中是否同时可见 `{category_A}` 和 `{category_B}`？ |
| T008 | CORE_SELECTABLE | QT4_INTERVAL_CHOICE | A1_VISIBLE_OBJECT_CATEGORY | 当前图像中可见物体类别数量属于哪个区间？ |
| T012 | CORE_SELECTABLE | QT3_BINARY_OR_COMPARISON | A2_COUNTING_AND_SET_SIZE | 当前图像中 `{category_A}` 的可见实例数量是否多于 `{category_B}`？ |
| T013 | CORE_SELECTABLE | QT1_SINGLE_CHOICE | A2_COUNTING_AND_SET_SIZE | 当前图像中哪类物体的可见实例数量最多？ |
| T014 | CORE_SELECTABLE | QT5_ORDERING | A2_COUNTING_AND_SET_SIZE | 将候选物体类别按当前图像中的可见实例数量从多到少排序。 |
| T015 | CORE_SELECTABLE | QT4_INTERVAL_CHOICE | A2_COUNTING_AND_SET_SIZE | 当前图像中可见物体实例总数属于哪个区间？ |
| T021 | CORE_SELECTABLE | QT3_BINARY_OR_COMPARISON | A3_IMAGE_PLANE_SPATIAL | 在标注图的图像平面坐标中，物体 A 是否位于物体 B 的左侧？ |
| T022 | CORE_SELECTABLE | QT3_BINARY_OR_COMPARISON | A3_IMAGE_PLANE_SPATIAL | 在标注图的图像平面坐标中，物体 A 是否位于物体 B 的右侧？ |
| T023 | CORE_SELECTABLE | QT3_BINARY_OR_COMPARISON | A3_IMAGE_PLANE_SPATIAL | 在标注图的图像平面坐标中，物体 A 是否位于物体 B 的上方？ |
| T024 | CORE_SELECTABLE | QT3_BINARY_OR_COMPARISON | A3_IMAGE_PLANE_SPATIAL | 在标注图的图像平面坐标中，物体 A 是否位于物体 B 的下方？ |
| T030 | CORE_SELECTABLE | QT1_SINGLE_CHOICE | A3_IMAGE_PLANE_SPATIAL | 标注图中的物体 A 位于图像九宫格的哪个区域？ |
| T031 | CORE_SELECTABLE | QT1_SINGLE_CHOICE | A3_IMAGE_PLANE_SPATIAL | 从候选区域中选择包含标注物体 A 中心点的区域。 |
| T045 | CORE_SELECTABLE | QT3_BINARY_OR_COMPARISON | A8_COMPLEX_CONSTRAINT_CONSISTENCY | 当前图像中，距离相机最近的标注物体是否属于 `{object_category}`？ |
| T085 | CORE_SELECTABLE | QT1_SINGLE_CHOICE | A1_VISIBLE_OBJECT_CATEGORY | 下列哪一项与当前图像中的可见物体类别或空间证据冲突？ |

## 深度增强 strict_depth 额外模板

| ID | 状态 | 题型 | 能力 | 修正后题干/处理 |
|---|---|---|---|---|
| T036 | DEPTH_SELECTABLE | QT3_BINARY_OR_COMPARISON | A4_DEPTH_DISTANCE_LAYER | 观察标注图，物体 A 是否比物体 B 更靠近相机？ |
| T037 | DEPTH_SELECTABLE | QT1_SINGLE_CHOICE | A4_DEPTH_DISTANCE_LAYER | 在候选标注物体中，哪个物体离相机最近？ |
| T038 | DEPTH_SELECTABLE | QT1_SINGLE_CHOICE | A4_DEPTH_DISTANCE_LAYER | 在候选标注物体中，哪个物体离相机最远？ |
| T039 | DEPTH_SELECTABLE | QT5_ORDERING | A4_DEPTH_DISTANCE_LAYER | 将候选标注物体按从近到远排序。 |
| T040 | DEPTH_SELECTABLE | QT4_INTERVAL_CHOICE | A4_DEPTH_DISTANCE_LAYER | 观察标注图，标注物体 A 到相机的距离属于哪个区间？ |
| T041 | DEPTH_SELECTABLE | QT3_BINARY_OR_COMPARISON | A4_DEPTH_DISTANCE_LAYER | 当前图像中是否存在距离相机小于 `{threshold}` 的 `{object_category}`？ |
| T044 | DEPTH_SELECTABLE | QT1_SINGLE_CHOICE | A4_DEPTH_DISTANCE_LAYER | 在候选标注区域中，选择与“距离相机最近的 `{object_category}` 实例”对应的区域。 |
| T091 | DEPTH_SELECTABLE | QT3_BINARY_OR_COMPARISON | A4_DEPTH_DISTANCE_LAYER | 观察标注图，物体 A 是否比物体 B 更靠近相机？ |
| T092 | DEPTH_SELECTABLE | QT1_SINGLE_CHOICE | A4_DEPTH_DISTANCE_LAYER | 当两个候选物体的可见区域邻近或重叠时，哪个物体更靠近相机？ |
| T094 | DEPTH_SELECTABLE | QT1_SINGLE_CHOICE | A4_DEPTH_DISTANCE_LAYER | 在候选标注区域中，选择最靠近相机的前景物体。 |
| T095 | DEPTH_SELECTABLE | QT5_ORDERING | A4_DEPTH_DISTANCE_LAYER | 将候选标注物体按深度层次由近到远排序。 |
| T096 | DEPTH_SELECTABLE | QT1_SINGLE_CHOICE | A4_DEPTH_DISTANCE_LAYER | 在候选标注物体中，选择“位于图像左半区且距离相机最近的 `{object_category}` 实例”。 |
| T097 | DEPTH_SELECTABLE | QT1_SINGLE_CHOICE | A4_DEPTH_DISTANCE_LAYER | 在候选标注物体中，选择“位于图像右半区且可见面积最大的物体”。 |

## 静态可选但非默认

| ID | 状态 | 题型 | 能力 | 修正后题干/处理 |
|---|---|---|---|---|
| T003 | STATIC_OPTIONAL_SELECTABLE | QT1_SINGLE_CHOICE | A1_VISIBLE_OBJECT_CATEGORY | 按可见 mask 面积合计，当前图像中主要可见的物体类别是哪一个？ |
| T004 | STATIC_OPTIONAL_SELECTABLE | QT1_SINGLE_CHOICE | A1_VISIBLE_OBJECT_CATEGORY | 按可见 mask 面积合计，当前图像中面积最大的可见物体类别是哪一个？ |
| T005 | STATIC_OPTIONAL_SELECTABLE | QT1_SINGLE_CHOICE | A1_VISIBLE_OBJECT_CATEGORY | 在标注图中，选择与给定 `{object_category}` 实例对应的标注区域。 |
| T007 | STATIC_OPTIONAL_SELECTABLE | QT1_SINGLE_CHOICE | A1_VISIBLE_OBJECT_CATEGORY | 下列哪一项描述与当前图像中可见的物体类别证据一致？ |
| T011 | STATIC_OPTIONAL_SELECTABLE | QT4_INTERVAL_CHOICE | A2_COUNTING_AND_SET_SIZE | 当前图像中可见的 `{object_category}` 数量属于哪个区间？ |
| T025 | STATIC_OPTIONAL_SELECTABLE | QT1_SINGLE_CHOICE | A3_IMAGE_PLANE_SPATIAL | 在候选标注物体中，哪个物体的中心点最靠近图像中心？ |
| T026 | STATIC_OPTIONAL_SELECTABLE | QT1_SINGLE_CHOICE | A3_IMAGE_PLANE_SPATIAL | 在候选标注物体中，哪个物体的中心点位于图像最左侧？ |
| T027 | STATIC_OPTIONAL_SELECTABLE | QT1_SINGLE_CHOICE | A3_IMAGE_PLANE_SPATIAL | 在候选标注物体中，哪个物体的中心点位于图像最右侧？ |
| T028 | STATIC_OPTIONAL_SELECTABLE | QT1_SINGLE_CHOICE | A3_IMAGE_PLANE_SPATIAL | 在候选标注物体中，哪个物体的中心点位于图像最上方？ |
| T029 | STATIC_OPTIONAL_SELECTABLE | QT1_SINGLE_CHOICE | A3_IMAGE_PLANE_SPATIAL | 在候选标注物体中，哪个物体的中心点位于图像最下方？ |
| T032 | STATIC_OPTIONAL_SELECTABLE | QT3_BINARY_OR_COMPARISON | A3_IMAGE_PLANE_SPATIAL | 在标注图中，物体 A 与物体 B 的可见外接框是否重叠？ |
| T033 | STATIC_OPTIONAL_SELECTABLE | QT3_BINARY_OR_COMPARISON | A3_IMAGE_PLANE_SPATIAL | 在标注图中，物体 A 与物体 B 的可见外接框是否相邻或接近？ |
| T034 | STATIC_OPTIONAL_SELECTABLE | QT5_ORDERING | A3_IMAGE_PLANE_SPATIAL | 将候选标注物体按图像中从左到右排序。 |
| T035 | STATIC_OPTIONAL_SELECTABLE | QT5_ORDERING | A3_IMAGE_PLANE_SPATIAL | 将候选标注物体按图像中从上到下排序。 |

## 时序扩展

| ID | 状态 | 题型 | 能力 | 修正后题干/处理 |
|---|---|---|---|---|
| T009 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | 在给定多帧图像中，`{object_category}` 是否至少可见过一次？ |
| T010 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 在候选帧中，哪一帧是 `{object_category}` 首次可见的帧？ |
| T016 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 在候选帧中，哪一帧的可见物体实例总数最多？ |
| T017 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | 在给定多帧图像中，`{object_category}` 的可见实例数量是否发生变化？ |
| T018 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 选择 `{object_category}` 可见实例数量最多的图像。 |
| T019 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | 判断描述“第 `{i}` 帧中的 `{object_category}` 可见实例数量多于第 `{j}` 帧”是否正确。 |
| T046 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 在候选帧中，哪一帧中相机/机器人/自车距离指定 `{object_category}` 实例最近？ |
| T047 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | 从第 `{i}` 帧到第 `{j}` 帧，机器人/自车是否在接近指定 `{object_category}` 实例？ |
| T048 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 从第 `{i}` 帧到第 `{j}` 帧，指定 `{object_category}` 与相机的距离变化趋势是什么？ |
| T049 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | 判断第 `{i}` 帧中，指定物体 A 是否比指定物体 B 更接近机器人/自车。 |
| T050 | TEMPORAL_EXTENDED_SELECTABLE | QT5_ORDERING | A6_TEMPORAL_TRAJECTORY | 将候选帧按机器人/自车到指定目标物体的距离从近到远排序。 |
| T066 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 机器人/自车从第一帧到最后一帧整体向哪个坐标方向移动？ |
| T067 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | 机器人/自车在序列中是否发生超过阈值的位移？ |
| T068 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 在候选相邻帧段中，哪一段机器人/自车位移最大？ |
| T070 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | 在序列中，`{category_A}` 首次可见是否早于 `{category_B}`？ |
| T071 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 在候选物体类别中，哪个类别在序列中最早首次可见？ |
| T072 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 在候选物体类别中，哪个类别在序列中最晚首次可见？ |
| T073 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | `{object_category}` 是否在整个序列的每一帧中都可见？ |
| T074 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | `{object_category}` 是否在序列中出现过由可见到不可见的变化？ |
| T075 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 选择 `{object_category}` 首次可见的图像。 |
| T076 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 选择 `{object_category}` 最后一次可见的图像。 |
| T077 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 从第 `{i}` 帧到第 `{j}` 帧，目标物体与机器人/自车的距离是变近、变远还是基本不变？ |
| T078 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 在候选物体中，哪个物体在序列中与机器人/自车的距离变化最大？ |
| T079 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | 判断描述“机器人/自车先接近物体 A，再接近物体 B”是否成立。 |
| T080 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 选择与机器人/自车运动轨迹最匹配的文字描述。 |
| T086 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | 在多帧序列中，`{object_category}` 是否从不可见变为可见？ |
| T087 | TEMPORAL_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A6_TEMPORAL_TRAJECTORY | 在多帧序列中，`{object_category}` 是否从可见变为不可见？ |
| T088 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 选择 `{object_category}` 从不可见变为可见的第一帧。 |
| T089 | TEMPORAL_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A6_TEMPORAL_TRAJECTORY | 选择 `{object_category}` 从可见变为不可见之前的最后一帧。 |

## 姿态/3D 扩展

| ID | 状态 | 题型 | 能力 | 修正后题干/处理 |
|---|---|---|---|---|
| T051 | POSE_3D_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A7_EGOCENTRIC_POSE_3D | 在第 `{frame_id}` 帧，指定物体 A 位于机器人/自车身体坐标系的哪个相对方位？ |
| T052 | POSE_3D_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A7_EGOCENTRIC_POSE_3D | 在第 `{frame_id}` 帧，指定物体 A 是否位于机器人/自车身体坐标系前方？ |
| T053 | POSE_3D_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A7_EGOCENTRIC_POSE_3D | 在第 `{frame_id}` 帧，指定物体 A 是否位于机器人/自车身体坐标系左侧？ |
| T054 | POSE_3D_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A7_EGOCENTRIC_POSE_3D | 在候选物体中，哪个物体在机器人/自车身体坐标系中最靠前？ |
| T055 | POSE_3D_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A7_EGOCENTRIC_POSE_3D | 在候选物体中，哪个物体在机器人/自车身体坐标系中最靠左？ |
| T056 | POSE_3D_EXTENDED_SELECTABLE | QT4_INTERVAL_CHOICE | A7_EGOCENTRIC_POSE_3D | 在相机坐标系下，标注物体 A 与标注物体 B 的三维质心距离属于哪个区间？ |
| T057 | POSE_3D_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A7_EGOCENTRIC_POSE_3D | 在相机坐标系下，标注物体 A 是否比标注物体 B 更靠近标注物体 C？ |
| T059 | POSE_3D_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A7_EGOCENTRIC_POSE_3D | 在三维坐标中，标注物体 A 的垂直位置是否高于标注物体 B？ |
| T060 | POSE_3D_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A5_VISIBLE_SCALE_3D_SIZE | 在候选标注物体中，哪个物体的可见三维包围盒体积最大？ |
| T062 | POSE_3D_EXTENDED_SELECTABLE | QT3_BINARY_OR_COMPARISON | A5_VISIBLE_SCALE_3D_SIZE | 标注物体 A 的可见三维包围盒体积是否大于标注物体 B？ |
| T063 | POSE_3D_EXTENDED_SELECTABLE | QT5_ORDERING | A5_VISIBLE_SCALE_3D_SIZE | 将候选标注物体按可见三维包围盒体积从大到小排序。 |
| T065 | POSE_3D_EXTENDED_SELECTABLE | QT6_STRUCTURED_MATCH | A7_EGOCENTRIC_POSE_3D | 选择标注物体 A 相对机器人/自车的方位类别，并选择其距离区间。 |
| T098 | POSE_3D_EXTENDED_SELECTABLE | QT1_SINGLE_CHOICE | A7_EGOCENTRIC_POSE_3D | 在候选物体中，选择“位于机器人/自车身体坐标系前方且距离最近”的物体。 |

## 废弃锁定，不可被 agent 选择

| ID | 状态 | 题型 | 能力 | 修正后题干/处理 |
|---|---|---|---|---|
| T020 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：不再输出每类裸数字计数；使用 T011/T015 区间题或 T002/T012 代替。 |
| T042 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：多实例类别的“整体更靠近”口径不稳定；用 T036/T037/T040 替代。 |
| T043 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：“前方”措辞歧义；用 T036 或 T091 的“更靠近相机”替代。 |
| T058 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：指定目标点来源容易虚构；用目标物体实例作为参照。 |
| T061 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：3D bbox y 方向尺寸不是自然评测语义；用 T060/T063 替代。 |
| T064 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：世界坐标左侧不适合普通图文评测；用图像平面左右或身体坐标左右模板替代。 |
| T069 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：按帧序号排序容易泄漏时间元数据，不能作为视觉评测模板。 |
| T081 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：不可答/能否判断类三选题，不进入模板库。 |
| T082 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：无法由图像支持类模板会引入不可答判断；用 T085 证据冲突单选替代。 |
| T083 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：能否仅凭图像判断类三选题，不进入模板库。 |
| T084 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：元问题，不作为图文 benchmark 题干；用 T001 负例替代。 |
| T090 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：不可见目标距离是否可回答是不可答三选题，不进入模板库。 |
| T093 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：“可能遮挡”是弱因果推断，自动评测不稳定。 |
| T099 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：多属性 JSON 匹配容易一物多属性和隐藏评分噪声；拆成 T021/T022/T036/T095。 |
| T100 | DEPRECATED_LOCKED | DEPRECATED_LOCKED | DEPRECATED | 已废弃：输出 object_id/depth_median 属于隐藏元数据，不作为图文评测。 |
