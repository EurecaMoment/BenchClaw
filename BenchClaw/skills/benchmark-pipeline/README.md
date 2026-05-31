# benchmark-pipeline

Stage1 到 Stage5 的总控 skill。该目录只做大阶段编排，不展开内部节点执行。内部 DAG 由各 stage 自己负责。

核心原则：椭圆是节点，编号是数据。
