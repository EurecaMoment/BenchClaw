# benchmark-pipeline

Stage1 到 Stage5 的总控 skill。该目录只做大阶段编排，不展开内部节点执行。内部 DAG 由各 stage 自己负责。

核心原则：椭圆是节点，编号是数据。

Workspace 隔离：若无用户显式授权，pipeline 只能使用本次冻结的 `WORKSPACE_ROOT`；除分配新编号所需的直属目录名扫描外，严禁查看其他 workspace 内容。
