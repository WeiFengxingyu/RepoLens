# RepoLens 设计阶段收口与项目深度评审

## 1. 文档信息

- 项目名称：RepoLens
- 文档类型：设计阶段收口评审
- 当前版本：v0.1
- 创建日期：2026-06-05
- 依据文档：
  - `docs/requirements-analysis.md`
  - `docs/outline-design.md`
  - `docs/p0-plus-development-plan.md`
  - `docs/resume-project-audit.md`

## 2. 当前项目架构结论

RepoLens 不是一个简单的 LangChain 应用，也不应该在简历中表述为“基于 LangChain 的代码问答系统”。

更准确的架构表述是：

RepoLens 采用 FastAPI + Next.js 的前后端分离单体架构，后端内部按 repository、parser、indexing、retrieval、graph、agent、review、tools、evaluation 等模块分层；Agent 编排层使用 LangGraph；检索层采用 BM25 + Qdrant 向量检索 + NetworkX 代码图扩展的 GraphRAG 混合检索架构；工具层采用 MCP-style Tool Layer 实现结构化工具调用、权限边界和调用日志。

## 3. LangChain 与 LangGraph 的关系

### 3.1 是否使用 LangChain

项目核心不依赖传统 LangChain chain 写法。项目可以使用 LangChain 生态中的部分基础能力，例如模型 adapter、prompt template 或文档结构工具，但不把 LangChain 作为项目主架构。

### 3.2 是否使用 LangGraph

P0+ 明确使用 LangGraph 作为 Agent Orchestrator，用于编排 Planner、Retriever、Reviewer、Verifier、Report Writer 多步骤工作流。

选择 LangGraph 的原因：

- 任务不是一次性问答，而是有状态的多步骤流程。
- 需要保存 Agent trace。
- 需要在证据不足时触发二次检索。
- 需要清晰表达 Agent 节点输入、输出和失败处理。

### 3.3 简历推荐说法

推荐说：

- 基于 LangGraph 编排多步骤 Code Agent 工作流。
- 设计 Planner、Retriever、Reviewer、Verifier、Report Writer 节点，实现任务拆解、混合检索、证据校验和报告生成。

不推荐说：

- 基于 LangChain 实现代码问答机器人。
- 使用 LangChain 搭建 RAG 项目。

## 4. 架构分层最终确认

P0+ 架构分层如下：

| 层级 | 技术/模块 | 作用 |
| --- | --- | --- |
| 前端展示层 | Next.js + TypeScript + Tailwind/shadcn | Web 工作台、证据、trace、评测展示 |
| API 层 | FastAPI | HTTP API、任务创建、状态查询 |
| 应用服务层 | Repository/QA/Review/Evaluation Service | 业务流程编排 |
| 代码理解层 | Scanner、Parser、Chunk Builder、Code Graph | 仓库扫描、代码解析、chunk、关系图 |
| 检索层 | BM25 + Qdrant + NetworkX | 混合检索、图邻域扩展、重排 |
| Agent 编排层 | LangGraph | 多步骤 Agent 状态机 |
| 工具层 | MCP-style Tool Layer | code_search、read_file_slice、get_symbol_context、analyze_diff |
| 数据层 | SQLite + Qdrant + 本地索引文件 | 元数据、向量、trace、证据 |
| 评测层 | 自建 eval scripts | Hit@5、MRR、引用覆盖率、幻觉率、延迟、token |
| 部署层 | Docker Compose | 本地可复现运行环境 |

## 5. 设计阶段是否可以结束

结论：主设计阶段可以结束。

理由：

- 项目定位已经明确：基于代码图谱 GraphRAG 的仓库级代码智能体平台。
- P0+ 功能范围已经明确：必须做、明确不做、P1/P2 延展均已写清。
- 软件架构已经明确：前后端分离单体架构，后端模块边界清晰。
- 核心模块已经明确：repository、scanner、parser、chunking、indexing、retrieval、graph、agent、review、tools、evaluation。
- 核心流程已经明确：仓库导入与索引、代码问答、PR Review、评测。
- 数据架构已经有概要设计：repositories、code_chunks、code_relations、tasks、evidences、agent_traces、tool_calls。
- API 已有概要设计。
- 安全、权限、错误处理、可观测性、部署和验收标准已经明确。
- 开发计划已经明确：按 Phase 垂直闭环推进。

因此，不建议继续扩展需求或继续增加技术概念。继续扩展会增加范围失控风险。

## 6. 进入开发前是否还需要补文档

不是必须，但建议在进入正式编码前补两份轻量设计文档：

1. 详细接口与数据库设计文档。
2. 评测集设计文档。

这两份文档不是重新设计项目，而是把编码时最容易反复确认的 schema、接口字段和评测数据格式提前定下来。

如果用户希望尽快开始开发，也可以先进入 Phase 0，并在 Phase 0 中同步补这两份轻量文档。

## 7. 项目深度评审

### 7.1 当前深度是否足够

结论：如果按 P0+ 标准实现，项目深度足够作为大厂大模型应用开发简历主项目。

原因：

- 不是普通 RAG，而是代码 GraphRAG。
- 不是普通聊天机器人，而是仓库级 Code Agent。
- 不是黑盒回答，而是证据引用 + Verifier 校验。
- 不是简单 prompt demo，而是前后端、索引、图谱、Agent、工具、trace、评测、部署的完整系统。
- 不是只讲概念 MCP，而是落地 MCP-style 工具 schema、权限控制和工具调用日志。
- 有评测闭环，能用指标证明检索策略和生成质量。

### 7.2 技术深度构成

| 深度维度 | 当前设计是否覆盖 | 说明 |
| --- | --- | --- |
| 代码结构化解析 | 覆盖 | Python ast、tree-sitter、函数/类/导入/调用关系 |
| GraphRAG | 覆盖 | BM25 + 向量 + 图邻域扩展 |
| Agent 工作流 | 覆盖 | LangGraph 多节点状态机 |
| 工具调用 | 覆盖 | MCP-style Tool Layer |
| 可追溯性 | 覆盖 | evidence、citation、trace |
| 评测体系 | 覆盖 | Hit@5、MRR、引用覆盖率、幻觉率、延迟、token |
| 工程化 | 覆盖 | FastAPI、Next.js、SQLite、Qdrant、Docker Compose |
| 安全意识 | 覆盖 | 敏感文件过滤、默认不执行脚本、权限决策日志 |

### 7.3 当前项目与普通项目的差距

普通项目：

- 上传文档。
- 向量检索。
- 调模型回答。
- 展示答案。

RepoLens P0+：

- 导入真实代码仓库。
- 解析函数、类、导入、调用关系。
- 构建代码图和函数级 chunk。
- BM25 + 向量 + 图扩展混合检索。
- LangGraph 多步骤 Agent。
- Verifier 检查证据。
- 工具调用有 schema、权限和日志。
- PR Diff 映射到 changed symbols。
- Review 报告有风险、影响范围、测试建议。
- 评测不同检索策略。
- 前端展示证据、trace、指标。

这个深度明显高于常见学生项目。

## 8. 仍需控制的风险

### 8.1 实现不要缩水

如果最终只做到“代码切块 + 向量检索 + 问答”，深度会明显下降。P0+ 必须保住这些底线：

- 代码图谱。
- 混合检索。
- 证据引用。
- LangGraph trace。
- PR Review。
- 评测指标。

### 8.2 不要过度追求大而全

P0+ 不做：

- 多用户。
- 完整 MCP Server。
- Neo4j。
- Kubernetes。
- GitHub PR 写回。
- 全语言支持。

这些放入 P1/P2，不影响 P0+ 简历价值。

### 8.3 评测必须真实

简历中最好出现真实数字，例如：

- Hit@5 从 vector_only 的某个值提升到 bm25_vector_graph 的某个值。
- 引用覆盖率达到某个比例。
- 平均响应延迟控制在某个范围。

没有评测数字，项目说服力会弱一档。

## 9. 收口结论

设计阶段可以结束，但要带着两个明确前提进入开发：

1. 不再扩 P0+ 范围。
2. 开发时严格按 `docs/p0-plus-development-plan.md` 的 Phase 顺序推进。

最终架构定稿：

FastAPI + Next.js 前后端分离单体架构，LangGraph 负责多步骤 Agent 编排，BM25 + Qdrant + NetworkX 组成代码 GraphRAG 混合检索层，SQLite 保存元数据和 trace，MCP-style Tool Layer 负责结构化工具调用和权限日志，Docker Compose 提供本地可复现部署。

最终项目深度判断：

P0+ 实现后，项目深度足够面向大厂大模型应用开发岗位；如果能按计划补齐评测结果、Demo 截图和 README，它可以作为简历主项目。

