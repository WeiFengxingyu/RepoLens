# RepoLens-Java 分阶段开发计划书

## 1. 文档信息

| 字段 | 内容 |
| --- | --- |
| 项目名称 | RepoLens-Java |
| 推荐简历名称 | RepoLens：基于 Spring AI 与 MCP 的仓库级 Code Agent 平台 |
| 文档类型 | 分阶段开发计划书 / 产品原型计划 |
| 创建日期 | 2026-06-28 |
| 依据文档 | `docs/repolens-java-requirements-outline-design.md` |
| 开发策略 | 复用旧 RepoLens 的前端、评测资产和产品设计；新增 `backend-java`，以 Java 后端核心能力作为简历主线 |

## 2. 总体开发策略

RepoLens-Java 不建议一次性做成“大而全”的系统。更稳妥的方式是按产品闭环逐步迭代：

```text
V0 可运行原型 -> V1 简历主版本 -> V1.1 真实平台增强 -> V2-Lite 分布式任务平台 -> V2 完整生产化预留
```

每个版本都必须有可运行、可演示、可验收的产品形态，避免只堆模块没有闭环。

核心原则：

1. 后端核心必须 Java 化，不能只做 Java 网关调用旧 FastAPI。
2. 前端工作台优先复用，接口适配 Java 后端。
3. 每阶段都保留测试、文档、截图和 demo runbook。
4. 先做只读 Code Agent，不做自动改代码、写 PR 评论、merge、push。
5. 先保证 Java Spring Boot 仓库深度解析，再扩展 Python/TypeScript/JavaScript。

## 3. 版本路线图

| 版本 | 建议周期 | 目标 | 可演示结果 |
| --- | --- | --- | --- |
| V0 | 1.5-2 周 | Java 后端最小可运行闭环 | 导入本地 Java 仓库，完成扫描、chunk、BM25 检索，前端展示证据 |
| V1 | 4-6 周 | 简历主版本 | Spring Boot + Spring AI + MCP + 混合检索 + QA + PR Review + Trace + Evaluation |
| V1.1 | 1.5-2 周 | 真实平台与面试增强 | GitHub/GitLab/Gitee PR/MR 只读 Provider、真实案例 runbook、截图包 |
| V2-Lite | 2-3 周，可选 | 分布式任务平台与传统后端能力补强 | ReviewHub：Job Center、RabbitMQ/Kafka、Redis 幂等/锁/限流、团队规则与配额、任务看板、Grafana |
| V2 | 3-5 周，可选 | 完整生产化扩展 | OpenSearch/PGvector 可替换、Neo4j 可选、LLM Judge、组织级 RBAC、CI/CD、镜像发布 |

推荐求职使用版本：**V1 完成即可作为简历重点项目**。V1.1 用于提高面试演示可信度。若还需要补传统 Java 后端能力，优先做 V2-Lite，而不是另起一个割裂的秒杀/商城项目。V2 完整版不必在投简历前完成。

## 4. 产品原型最终形态

最终产品不是 landing page，而是一个面向开发者的工作台。首屏就是可操作工具界面：

```text
┌─────────────────────────────────────────────────────────────────────┐
│ RepoLens-Java Workbench                                             │
├───────────────┬─────────────────────────────────┬───────────────────┤
│ Repository    │ Ask / Review Workspace           │ Evidence / Trace  │
│               │                                 │                   │
│ + Import Repo │ [Ask] [Review] [MCP] [Eval]      │ Evidence list     │
│ - java-demo   │                                 │ file:line         │
│ - ts-demo     │ Question / Diff input            │ symbol            │
│               │                                 │ score/source      │
│ Status        │ Answer / Review report           │                   │
│ READY         │ citations                        │ Agent Trace       │
│ files: 382    │ risks                            │ Planner           │
│ chunks: 945   │ tests                            │ Retriever         │
│ relations:2k  │ markdown export                  │ Tool Calls        │
│               │                                 │ Verifier          │
├───────────────┴─────────────────────────────────┴───────────────────┤
│ Evaluation: vector_only | bm25_vector | bm25_vector_graph            │
│ Hit@5 / MRR / Citation Coverage / Latency / Tool Success             │
└─────────────────────────────────────────────────────────────────────┘
```

最终 Demo 主线：

```text
导入 Java Spring Boot 仓库
  -> 索引完成，展示文件/chunk/relation
  -> 提问“JWT 鉴权逻辑在哪里？”
  -> 返回带文件路径、行号、方法名、证据片段的回答
  -> 粘贴一段 diff 做 PR Review
  -> 输出风险、影响范围、测试建议、引用证据
  -> 查看 MCP Tool Audit 和 Agent Trace
  -> 运行 Evaluation，展示三种检索策略对比
```

## 5. V0：Java 后端最小闭环

### 5.1 版本目标

V0 目标是证明 Java 后端可以替代旧 FastAPI 的核心入口，跑通最小产品链路：

```text
本地仓库导入 -> 文件扫描 -> Java 解析 -> Chunk 入库 -> BM25 检索 -> Evidence 展示
```

V0 不接大模型，不做 MCP，不做向量库。它解决两个问题：

1. Java 后端工程骨架是否可持续扩展。
2. 前端是否可以切到 Java API 并展示真实 evidence。

### 5.2 范围

必做：

- 新增 `backend-java` Spring Boot 工程。
- Docker Compose 增加 PostgreSQL/MySQL、Redis 可选。
- Flyway 初始化基础表。
- Repository API：创建、列表、详情、状态。
- Scanner：文件过滤、语言识别、敏感文件跳过。
- Java Parser：提取 package、import、class、method、annotation、start/end line。
- Chunk Builder：文件级、类级、方法级 chunk。
- Lucene/BM25 检索。
- Evidence API。
- Next.js 前端 API base 切换到 Java 后端。

暂不做：

- Spring AI。
- MCP Server。
- Vector Store。
- PR Review。
- Agent Workflow。

### 5.3 任务清单

| 编号 | 任务 | 说明 | 验收 |
| --- | --- | --- | --- |
| V0-001 | 初始化 `backend-java` | Gradle/Maven、Java 21、Spring Boot 3 | `/actuator/health` 可访问 |
| V0-002 | 配置 Flyway | repositories、files、chunks 表 | 空库自动建表 |
| V0-003 | Repository API | POST/GET/status | 前端能创建仓库记录 |
| V0-004 | 本地路径导入 | path normalize、workspace guard | 仅读取允许目录 |
| V0-005 | Scanner | 忽略目录、敏感文件、大文件、语言识别 | 输出 file_count 和 skip reasons |
| V0-006 | Java Parser | class/method/annotation/line range | demo Spring Boot 仓库能解析 Controller/Service |
| V0-007 | Chunk Builder | method/class/file chunk | chunk 带 path、symbol、line |
| V0-008 | Lucene BM25 | 建索引和搜索 | 查询方法名/API 路径可命中 |
| V0-009 | Evidence API | 返回 snippet、score、source | 前端 Evidence Panel 可展示 |
| V0-010 | 前端适配 | `frontend/lib/api.ts` 适配 Java 返回 | 页面能显示仓库和检索结果 |
| V0-011 | 单元测试 | Scanner、Parser、Chunk、BM25 | 核心测试通过 |
| V0-012 | V0 Demo 文档 | 记录启动、导入、检索流程 | 有 runbook |

### 5.4 交付物

- `backend-java/`
- Flyway migration
- Repository + Retrieval 基础 API
- Java demo repo
- V0 demo runbook
- V0 截图：仓库状态、检索证据

### 5.5 V0 验收标准

- 可以导入一个本地 Java Spring Boot demo 仓库。
- 可以识别至少 80% 的 Java class/method 起止行。
- 可以通过关键词搜索命中 Controller、Service、配置项。
- 前端能展示 repository status、file_count、chunk_count、evidence list。

## 6. V1：简历主版本

### 6.1 版本目标

V1 是求职简历主版本，目标是形成完整闭环：

```text
仓库导入
  -> Java/Python/TS 解析
  -> BM25 + Vector + Code Graph 混合检索
  -> Spring AI Tool Calling
  -> MCP Server
  -> 代码问答
  -> PR Review
  -> Agent Trace
  -> Evaluation Panel
```

### 6.2 V1 阶段拆分

V1 分为 7 个阶段，每阶段都能演示一部分能力。

| 阶段 | 目标 | 核心成果 |
| --- | --- | --- |
| V1-P1 | 异步索引与状态机 | Redis/任务状态/失败重试 |
| V1-P2 | 多语言解析与代码图谱 | Java 深度 + Python/TS 基础 + relation |
| V1-P3 | 向量检索与混合召回 | Spring AI VectorStore + Qdrant/PGvector |
| V1-P4 | Agent QA | Spring AI ChatClient + Tool Calling + Verifier |
| V1-P5 | PR Review | diff analyzer + risk reviewer + test suggestion |
| V1-P6 | MCP Server 与权限审计 | MCP tools/list/call + audit |
| V1-P7 | 评测、前端和发布包装 | benchmark、截图、README、简历材料 |

## 7. V1-P1：异步索引与任务状态

### 7.1 目标

把 V0 的同步导入升级为可追踪、可恢复的索引任务流水线。

### 7.2 工作内容

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P1-001 | Index Task 表设计 | tasks、task_events、index_progress |
| P1-002 | 状态机实现 | CREATED/CLONING/SCANNING/PARSING/CHUNKING/INDEXING/READY/FAILED |
| P1-003 | Redis Lock | 防止同一仓库重复索引 |
| P1-004 | 失败重试 | 从失败阶段重试，记录 last_error |
| P1-005 | 前端进度展示 | 展示当前阶段、耗时、错误 |
| P1-006 | Testcontainers | DB + Redis 集成测试 |

### 7.3 验收

- 索引任务可后台执行。
- 前端轮询状态可看到阶段变化。
- 失败后有错误原因和重试按钮。
- 同仓库重复导入不会产生并发冲突。

## 8. V1-P2：多语言解析与代码图谱

### 8.1 目标

建立仓库结构化理解能力，让项目从“文本检索”升级到“代码图谱检索”。

### 8.2 工作内容

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P2-001 | Java Parser 增强 | Spring 注解、route、Controller-Service-Repository 候选链 |
| P2-002 | Python Parser | class/function/import/call 基础解析 |
| P2-003 | TS/JS Parser | import、function、class、route/API handler |
| P2-004 | Code Relation 表 | contains/imports/calls/routes_to/tests |
| P2-005 | Graph Query Service | neighbors、callers、callees、file symbols |
| P2-006 | Graph API | `/api/repositories/{id}/symbols`、`/graph/neighbors` |
| P2-007 | 前端 Overview 增强 | relation_count、language summary、symbol list |
| P2-008 | Parser 测试集 | Java/Python/TS fixture |

### 8.3 验收

- Java Spring Boot demo 能识别 Controller route。
- 查询某个 method 能看到所在 class、同文件方法、调用候选。
- relation_count 在前端展示。
- 解析失败文件不影响整体索引。

## 9. V1-P3：向量检索与混合召回

### 9.1 目标

构建 BM25 + Vector + Graph 的核心检索链路，这是项目技术深度的主轴。

### 9.2 工作内容

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P3-001 | Spring AI VectorStore 配置 | Qdrant 或 PGvector |
| P3-002 | Embedding Adapter | 支持真实 provider 和 mock provider |
| P3-003 | Vector Indexer | 批量写入 chunk embedding |
| P3-004 | Vector Retrieval | topK 相似检索，带 metadata |
| P3-005 | Candidate Merge | BM25/vector 去重合并 |
| P3-006 | Graph Expansion | 对命中 chunk 扩展邻居 |
| P3-007 | Rerank Formula | bm25/vector/graph/file/diff 综合分 |
| P3-008 | Evidence Persistence | 保存 task evidence |
| P3-009 | 前端 Evidence Panel | 展示 source、score、reason |
| P3-010 | 检索评测脚本初版 | vector_only、bm25_vector、bm25_vector_graph |

### 9.3 验收

- 支持无 embedding 配置时 BM25-only 降级。
- 支持有 embedding 配置时向量召回。
- Graph expansion 能补充同类、同文件或调用相关 evidence。
- 评测脚本能输出 Hit@5、MRR、citation coverage。

## 10. V1-P4：Agent QA

### 10.1 目标

实现带证据引用、工具调用、Verifier 和 Trace 的代码问答。

### 10.2 工作内容

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P4-001 | AgentState 设计 | taskId、plan、evidence、toolCalls、claims、trace |
| P4-002 | Planner | 判断 location/explanation/architecture/impact |
| P4-003 | Tool Registry | code.search、file.read_slice、symbol.context |
| P4-004 | Spring AI Tool Calling | 使用 `@Tool` 或 ToolCallback |
| P4-005 | QA Draft Writer | 基于 evidence 生成回答 |
| P4-006 | Verifier | supported/partial/unsupported |
| P4-007 | Repair Retrieval | 证据不足时补检索一次 |
| P4-008 | Trace Store | Planner/Retriever/Tool/Verifier/Writer |
| P4-009 | Ask Panel 适配 | 展示答案、citation、trace |
| P4-010 | QA 集成测试 | mock chat model + deterministic fallback |

### 10.3 验收

- 问“JWT 鉴权在哪里？”能返回文件、方法、行号和解释。
- 每个关键结论有 citation。
- 无证据结论被 Verifier 标记 partial/unsupported。
- Trace Panel 能看到工具调用和耗时。

## 11. V1-P5：PR Review

### 11.1 目标

实现面试最有展示力的 PR Review 工作流。

### 11.2 工作内容

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P5-001 | Diff Parser | 解析 changed file、hunk、line range |
| P5-002 | Changed Symbol Mapper | diff 映射到 chunk/method |
| P5-003 | Review Retriever | 加权 diff 相关 evidence |
| P5-004 | Risk Reviewer | 生成风险草稿 |
| P5-005 | Impact Analyzer | callers/callees/tests 影响范围 |
| P5-006 | Test Suggestion | 基于变更路径和测试候选给建议 |
| P5-007 | Review Verifier | 风险必须绑定 evidence |
| P5-008 | Markdown Export | 导出 Review 报告 |
| P5-009 | Review Panel | 风险、影响、测试、citation、markdown |
| P5-010 | Review fixture | Java demo diff + TS demo diff |

### 11.3 验收

- 粘贴 diff 后能输出结构化 Review。
- 风险包含 severity、file、line、reason、evidence。
- 能给出相关测试建议。
- 无证据高风险被降级或标记 unsupported。

## 12. V1-P6：MCP Server 与工具权限审计

### 12.1 目标

把 RepoLens 的能力升级为标准工具服务，这是“足够新”的核心亮点。

### 12.2 工作内容

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P6-001 | MCP Server 配置 | Spring AI MCP Server / MCP Java SDK |
| P6-002 | tools/list | 返回工具 schema 和权限 |
| P6-003 | tools/call | 执行只读工具 |
| P6-004 | ToolPermissionPolicy | 仓库访问、敏感文件、最大输出限制 |
| P6-005 | PathGuard | 防路径穿越、仓库外读取 |
| P6-006 | Tool Audit 表 | inputHash、outputHash、client、session |
| P6-007 | MCP Smoke Client | 本地调用 tools/list/code.search/file.read_slice |
| P6-008 | MCP Panel | 展示工具、权限、审计记录 |
| P6-009 | Security Tests | 越权路径、敏感文件、禁用工具 |

### 12.3 验收

- MCP client 可以列出工具。
- MCP client 可以调用 `code.search` 和 `file.read_slice`。
- 越权文件读取被拒绝。
- 前端能看到 permission decision、input/output hash、latency。

## 13. V1-P7：评测、前端完善与发布包装

### 13.1 目标

把项目从“能跑”收束成“能投简历、能面试演示、能被追问”的版本。

### 13.2 工作内容

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P7-001 | Java 评测集 | 至少 30 条 Java 场景 |
| P7-002 | 综合评测集 | Java + TS + Review，总计 50+ |
| P7-003 | Evaluation API | 运行策略、保存结果 |
| P7-004 | Evaluation Panel | 展示指标表和样例命中 |
| P7-005 | README Java Edition | 架构图、技术栈、启动方式、Demo |
| P7-006 | Demo Runbook | 主线演示步骤 |
| P7-007 | 截图包 | Repository、Ask、Review、MCP、Eval |
| P7-008 | 简历 bullet | 中文/英文版本 |
| P7-009 | 面试深挖文档 | 架构、检索、MCP、安全、评测 |
| P7-010 | Release Checklist | 测试、敏感信息扫描、Docker 启动 |

### 13.3 验收

- Evaluation 至少对比三种检索策略。
- README 有可复现启动步骤。
- 截图可以直接放项目链接或简历附件。
- 面试能按 60 秒、3 分钟、10 分钟讲清楚。

## 14. V1 最终验收清单

### 14.1 产品验收

| 项目 | 标准 |
| --- | --- |
| 仓库导入 | 能导入 Java Spring Boot demo 和 TS demo |
| 索引状态 | 前端展示阶段、耗时、失败原因 |
| Java 解析 | Controller/Service/Repository/method/route 可识别 |
| 混合检索 | BM25、vector、graph 三路有来源展示 |
| 代码问答 | 回答带 file path、line、symbol、snippet |
| PR Review | 输出风险、影响范围、测试建议、citation |
| MCP | tools/list 和 tools/call 可用 |
| 权限审计 | 工具调用有 permission、hash、latency |
| 评测 | 有 Hit@5、MRR、citation coverage、latency |

### 14.2 工程验收

| 项目 | 标准 |
| --- | --- |
| 后端测试 | 核心单测和集成测试通过 |
| Docker | Compose 一键启动主要服务 |
| Migration | 空库可初始化 |
| 安全 | 敏感文件和仓库外路径无法读取 |
| 降级 | embedding 不可用时 BM25-only 可运行 |
| 日志 | 不输出 API key 和敏感文件全文 |

### 14.3 简历验收

| 项目 | 标准 |
| --- | --- |
| 项目名 | RepoLens：基于 Spring AI 与 MCP 的仓库级 Code Agent 平台 |
| 技术栈 | Spring Boot、Spring AI、MCP、VectorStore、Lucene、Redis、DB、Next.js |
| 亮点 | 混合检索、MCP 工具、权限审计、Agent Trace、评测 |
| 可演示 | 5 分钟内跑完主线 Demo |
| 可追问 | Parser、Graph、Retriever、Tool Calling、MCP、安全、Evaluation 都有设计和代码 |

## 15. V1.1：真实平台与面试增强

### 15.1 目标

V1.1 不是必须版本，但能显著提升项目可信度。目标是把 pasted diff 扩展成真实 PR/MR URL 只读 Review，并准备真实案例。

### 15.2 工作内容

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| V1.1-001 | Change Request Provider 接口 | 平台无关 contract |
| V1.1-002 | GitHub PR Provider | metadata、files、commits、diff |
| V1.1-003 | GitLab MR Provider | gitlab.com + self-hosted |
| V1.1-004 | Gitee PR Provider | 国内平台补充 |
| V1.1-005 | Token 脱敏 | token 不入库、不出日志 |
| V1.1-006 | Rate Limit Handling | 明确错误和提示 |
| V1.1-007 | Real Case Runbook | 真实公开 PR/MR 案例 |
| V1.1-008 | Live Smoke 文档 | 网络可用时演示，默认仍离线 fixture |

### 15.3 验收

- 输入公开 GitHub PR URL 可以只读拉取 metadata 和 diff。
- 平台 token 不出现在响应、日志、trace、截图。
- 离线 fixture 仍然可作为默认 Demo。

## 16. V2-Lite：ReviewHub 分布式任务平台

V2-Lite 是在 V1/V1.1 基础上的生产化增强，用来补高并发、分布式、中间件和业务系统能力。它不新建独立项目，而是把 RepoLens 的索引与 Review 主链路升级成团队级 ReviewHub。

### 16.1 定位

V2-Lite 解决的不是抽象的“我要用 MQ/Redis”，而是 RepoLens 的真实业务压力：

```text
GitHub/GitLab/Gitee Webhook 并发触发
  -> API 幂等落库
  -> MQ 异步削峰
  -> Worker 并行执行索引或 Review
  -> Redis 控制仓库锁、限流和幂等
  -> PostgreSQL 记录任务、attempt、事件和审计
  -> 前端 Job Queue + Grafana 展示任务健康度
```

### 16.2 核心模块

| 模块 | 关键能力 | 和 V1 的关联 |
| --- | --- | --- |
| Job Center | `analysis_job`、`job_attempt`、`job_event`、状态机、重试、死信 | 承接 V1 索引任务和 V1.1 PR/MR Review |
| MQ Worker | RabbitMQ 默认，Kafka 可替换；Worker lease、heartbeat、超时恢复 | 将同步/单机后台任务升级为可横向扩展 |
| Redis 控制面 | 仓库级锁、Webhook 幂等、用户/仓库限流、任务状态缓存 | 保护索引、平台 API、LLM 和数据库 |
| ReviewHub 业务域 | 组织、项目、仓库、成员、规则集、配额、审计 | 把工具升级成团队内部业务系统 |
| 可观测性 | Actuator、Micrometer、Prometheus、Grafana、失败原因统计 | 支撑面试中的可运维和可排障追问 |

### 16.3 分阶段建议

| 阶段 | 目标 | 验收 |
| --- | --- | --- |
| V2L-P0 | Docker Compose 与 profile 收束 | PostgreSQL、Redis、RabbitMQ、Prometheus、Grafana 可启动 |
| V2L-P1 | 通用任务中心 | 任务幂等创建、状态机、attempt、event、重试 API |
| V2L-P2 | MQ Worker | 创建索引/Review job 后异步执行，Worker 中断可恢复 |
| V2L-P3 | Redis 并发控制 | 同仓库索引互斥、Webhook 去重、用户/仓库限流 |
| V2L-P4 | 团队业务域 | 组织、项目、仓库绑定、Ruleset、Quota |
| V2L-P5 | 看板与观测 | Job Queue、Worker Monitor、Grafana 截图 |

### 16.4 简历价值

V2-Lite 能补足传统 Java 后端面试最常追问的内容：

- MQ 异步削峰、重复消息、死信和重试。
- Redis 分布式锁、幂等、限流和缓存。
- PostgreSQL 任务状态机、attempt 追踪和审计日志。
- RBAC、规则集、配额等业务系统建模。
- Actuator、Micrometer、Prometheus、Grafana 可观测性。

详细执行方案见 `docs/repolens-java-v2-lite-reviewhub-plan.md`。

## 17. V2：完整生产化预留版本

V2 是可选增强，不建议在求职前强行完成。它主要用于面试追问“生产化怎么做”时展示路线。

### 17.1 增强方向

| 模块 | 增强 |
| --- | --- |
| 索引 | 增量索引、文件 hash diff、定时重建 |
| 搜索 | Lucene 替换 OpenSearch/Elasticsearch |
| 向量 | Qdrant/PGvector 多租户 collection |
| 图谱 | JGraphT/关系表升级 Neo4j 可选 |
| 任务 | V2-Lite 的 RabbitMQ/Kafka Worker 扩展为多队列、多优先级、多租户调度 |
| 评测 | LLM-as-a-Judge、人工标注 Review 风险 |
| 权限 | 组织、项目、仓库级 RBAC |
| 观测 | Grafana Dashboard、trace sampling |
| 部署 | 多环境 profile、CI/CD、镜像发布 |

### 17.2 不建议提前做的内容

- Kubernetes 全套部署。
- 自动代码修改和提交。
- 企业多租户收费系统。
- 支持几十种语言。
- 复杂自治多 Agent 讨论系统。

## 18. 目录规划

推荐最终目录：

```text
RepoLens/
  backend/                  # 旧 FastAPI 版，legacy/prototype
  backend-java/             # Java Edition 主后端
    build.gradle / pom.xml
    src/main/java/com/repolens/
    src/main/resources/db/migration/
    src/test/java/com/repolens/
  frontend/                 # 复用 Next.js 工作台
  evals/                    # 复用并扩展评测集
    datasets/
    demo_repos/
    change_requests/
  docs/
    repolens-java-requirements-outline-design.md
    repolens-java-development-roadmap.md
    repolens-java-demo-runbook.md
    repolens-java-interview-guide.md
  docker-compose.yml
  README.md
```

## 19. 开发优先级建议

如果时间有限，优先级如下：

| 优先级 | 必做内容 | 原因 |
| --- | --- | --- |
| P0 | Java 后端骨架、仓库导入、Java parser、BM25、前端展示 | 没有这个就不是 Java 项目 |
| P1 | 代码图谱、向量检索、混合检索、Evidence | 技术深度核心 |
| P2 | Agent QA、Tool Calling、Verifier、Trace | AI 应用工程核心 |
| P3 | PR Review、测试建议、Markdown | 面试演示最强 |
| P4 | MCP Server、权限审计 | 新度和差异化 |
| P5 | Evaluation、README、截图、面试材料 | 简历可信度 |

最小可投递版本：

```text
V0 + V1-P1 + V1-P2 + V1-P3 + V1-P4
```

强推荐投递版本：

```text
完整 V1
```

锦上添花版本：

```text
V1 + V1.1
```

补传统 Java 后端能力版本：

```text
V1 + V1.1 + V2-Lite
```

## 20. 最终产品原型描述

最终原型可以这样对外描述：

> RepoLens-Java 是一个本地优先、只读安全的仓库级 Code Agent 工作台。用户导入 Java/Spring Boot 或 TypeScript 仓库后，系统会自动扫描、解析、切分代码，构建 BM25 索引、向量索引和代码关系图。用户可以在工作台中进行代码问答、PR Diff Review、MCP 工具调用和评测对比。所有回答和 Review 结论都带文件路径、行号、symbol 和 evidence snippet；所有工具调用都经过权限校验并记录审计 hash；所有 Agent 步骤都在 Trace 面板中可观测。

这个原型最终应该能支撑 5 个截图：

1. Repository Import / Status：展示 Java 仓库已索引。
2. Ask + Evidence：展示带 citation 的代码问答。
3. PR Review：展示风险、影响范围、测试建议。
4. MCP Tool Audit：展示工具权限和 hash 审计。
5. Evaluation：展示检索策略指标对比。

## 21. 结论

RepoLens-Java 的开发应以 V1 为简历主版本目标。V0 用来快速证明 Java 后端闭环，V1 用来形成完整简历竞争力，V1.1 用来增强真实平台可信度，V2-Lite 用来补传统 Java 后端能力，V2 作为完整生产化路线储备。

如果简历需要进一步补高并发、分布式、中间件和业务系统能力，优先把 V2-Lite 做成 ReviewHub 分布式任务平台。它与 RepoLens 主线高度相关，能自然覆盖 MQ、Redis、任务状态机、团队权限、配额和可观测性，比另做一个割裂的传统项目更实用。

最重要的交付不是代码量，而是一个能讲清楚、能跑通、能截图、能评测、能被追问的产品原型：

```text
仓库导入 -> 结构化解析 -> 混合检索 -> Agent 工具调用 -> 证据问答/PR Review -> MCP 审计 -> 评测展示
```

完成 V1 后，RepoLens-Java 就足够作为 985 研究生面向 Java 全栈开发岗位的简历重点项目。
