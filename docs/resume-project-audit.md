# RepoLens 面向大厂简历的项目审核报告

## 1. 审核结论

结论：RepoLens 这个题目合理，且具备放入大厂大模型应用开发岗位简历的潜力。当前题目比普通知识库 RAG、论文总结 Bot、简历筛选 Bot 更有辨识度，因为它切中了 2026 年大模型应用开发中更高价值的方向：代码智能体、仓库级上下文理解、工具调用、GraphRAG、多智能体工作流、评测与可观测性。

但需要明确一点：如果最终只实现“上传仓库后调用大模型回答问题”，这个项目不够亮眼；如果实现为“基于代码结构图谱的仓库级 Code Agent 平台”，并提供量化评测和可演示的 PR Review 流程，则可以作为面向大厂的核心简历项目。

推荐保留题目，但优化简历表达。

推荐项目名称：

RepoLens：基于代码图谱 GraphRAG 的仓库级代码智能体平台

推荐英文副标题：

Repository-Level Code Agent for Codebase Understanding and PR Review

## 2. 大厂简历匹配度评分

| 维度 | 当前评分 | 强化后评分 | 说明 |
| --- | --- | --- | --- |
| 业务场景价值 | 9/10 | 9/10 | 代码理解和 PR Review 是开发者高频真实场景 |
| 技术辨识度 | 8/10 | 9/10 | GraphRAG、Agent、MCP-style tools、评测闭环能拉开差距 |
| 工程复杂度 | 8/10 | 9/10 | 前后端、索引、异步任务、trace、评测、部署都有体现 |
| 可展示性 | 8/10 | 9/10 | 输入真实仓库即可演示，适合面试现场展示 |
| 实现可控性 | 7/10 | 8/10 | 范围较大，需要控制 P0 边界 |
| 简历说服力 | 7/10 | 9/10 | 需要最终产出指标、截图、Demo、README 和评测报告 |

综合判断：

- 当前设计：可以做，但还处于“有潜力”的阶段。
- 达到 P0+ 后：足够作为大厂大模型应用开发岗位的亮点项目。
- 达到 P1 核心强化后：可以作为简历主项目和面试重点展开。

## 3. 为什么这个题目适合大厂

### 3.1 它不是普通聊天机器人

大厂面试官通常不缺“套 LangChain 做个问答机器人”的项目。RepoLens 的优势在于它处理的是代码仓库这种复杂、结构化、长上下文对象，需要解决检索、结构解析、任务规划、工具调用和结果验证问题。

这类问题更接近真实业务里的大模型应用落地，而不是简单 API 调用。

### 3.2 它覆盖岗位高频关键词

大模型应用开发和 AI Agent 岗位常见关键词包括：

- RAG
- Agent
- LangGraph
- Function Calling / Tool Use
- MCP
- 向量数据库
- 评测体系
- 可观测性
- Python 后端
- 前端工作台
- Docker 部署

RepoLens 当前设计已经覆盖其中大部分关键词。需要注意的是，简历中不要只堆关键词，而要写清楚每个关键词解决了什么工程问题。

### 3.3 它贴近代码智能体趋势

代码智能体是大模型应用中的强趋势方向。仓库级代码理解、PR Review、影响范围分析、新人 onboarding、自动测试建议，都是实际团队可能需要的能力。

相关研究已经在 2026 年关注本方向：

- RepoReviewer 提出本地优先的多智能体仓库级代码审查架构，使用 Python CLI、FastAPI、LangGraph 和 Next.js。
- Codebase-Memory 使用 Tree-sitter 构建代码知识图谱，并通过 MCP 暴露给 LLM coding agent，用更少 token 和工具调用支持仓库探索。

这说明方向不是冷门想象题，而是有现实技术趋势支撑。

## 4. 当前设计合理性审核

### 4.1 技术架构合理

当前概要设计采用：

- 前端：Next.js + TypeScript
- 后端：Python + FastAPI
- Agent：LangGraph
- 向量检索：Qdrant
- 关键词检索：BM25
- 代码解析：tree-sitter 或 AST
- 代码图：NetworkX
- 元数据存储：SQLite
- 部署：Docker Compose

这个组合对 P0 来说是合理的。它足够工程化，又不会过早引入复杂微服务、Neo4j、Kubernetes、分布式任务队列等重型组件。

### 4.2 SQLite 与 NetworkX 不会降低简历价值

P0 使用 SQLite 和 NetworkX 是合理选择。面试时可以这样解释：

- P0 优先验证仓库级代码智能体闭环，减少运维依赖。
- SQLite 保存元数据和 trace，Qdrant 负责向量检索，职责清晰。
- NetworkX 用于本地代码关系图和图邻域扩展，足以支撑中小仓库演示。
- 如果进入生产化，可升级为 PostgreSQL、Redis/RQ、Neo4j 或图数据库。

这体现的是工程判断，而不是技术弱。

### 4.3 LangGraph 选型合理

RepoLens 的任务不是一次性问答，而是包含规划、检索、审查、验证、报告生成的多步骤流程。LangGraph 适合这种有状态、可追踪、可回退的 Agent 工作流。

设计中的 Planner、Retriever、Reviewer、Verifier、Report Writer 五个节点合理，但需要避免“为了多智能体而多智能体”。每个 Agent 必须有明确输入、输出和失败处理。

### 4.4 混合检索设计合理

代码检索不能只依赖向量：

- 函数名、类名、文件名等精确符号更适合 BM25 或关键词检索。
- “登录逻辑怎么实现”“这个模块负责什么”这类语义问题适合向量检索。
- 影响范围、调用链、邻近上下文适合代码图扩展。

因此 BM25 + 向量检索 + 图邻域扩展的设计是合理的，也是项目亮点之一。

### 4.5 安全设计方向正确

不默认执行仓库脚本、过滤 `.env` 和密钥文件、工具调用留 trace，这些设计是必要的。Agent 项目如果没有权限控制和审计记录，面向大厂会显得不成熟。

## 5. 目前最大风险

### 5.1 范围过大

RepoLens 涉及前端、后端、RAG、Agent、代码解析、评测、部署，范围不小。风险是每个模块都做一点，但都不深入。

应对策略：

- P0 必须聚焦：仓库导入、代码解析、混合检索、带引用问答、PR Review、trace 展示。
- P1 再加 GitHub API、静态检查、架构图和更完整评测。
- P2 再谈 MCP Server、权限、多用户和写回 PR。

### 5.2 容易被看成 CodeRabbit / Copilot 的简化仿品

如果项目只说“自动代码审查”，会被面试官拿来和成熟产品比较。

应对策略：

把定位从“替代代码审查工具”改为：

面向仓库级代码理解的 Code Agent 基础设施，核心能力是代码结构记忆、可追溯检索、影响范围分析和审查辅助。

这样就不再只是一个 Review 工具，而是一个代码智能体平台。

### 5.3 PR Review 准确性难证明

代码审查质量很难用口头说服，需要指标。

应对策略：

必须加入评测：

- 检索 Hit@K
- MRR
- 引用覆盖率
- Review 有效率
- 幻觉率
- 端到端延迟
- token 成本

简历中最好出现 2-3 个真实数字。

### 5.4 MCP 不要只停留在概念

如果简历写了 MCP，但项目里没有真实工具协议或 MCP-style 工具封装，会显得包装过度。

应对策略：

至少实现一个轻量 MCP-style Tool Layer，或者实现 2-3 个真正可被 Agent 调用的结构化工具：

- code_search
- read_file_slice
- get_symbol_context
- analyze_diff
- run_safe_static_check

## 6. 必须强化的亮点

为了面向大厂，建议把 P0 升级为 P0+，至少加入以下 6 个硬亮点。

### 6.1 代码结构图谱

必须真正从代码中提取：

- 文件包含关系
- class/function/method
- imports
- 简化调用关系
- diff 影响节点

这能让项目从“文本 RAG”升级为“代码 GraphRAG”。

### 6.2 可追溯证据链

所有回答和 Review 结论都必须带：

- 文件路径
- 起止行号
- symbol 名称
- 检索来源
- 证据片段

这是抗幻觉和工程可信度的关键。

### 6.3 Agent Trace 可视化

前端必须展示：

- Planner 拆解了什么任务
- Retriever 找到了哪些证据
- Reviewer 生成了哪些风险
- Verifier 驳回或通过了哪些结论
- 每一步耗时和 token 消耗

这比只展示最终回答更能打动面试官。

### 6.4 评测闭环

至少准备 50 条评测样例：

- 20 条代码定位
- 10 条函数解释
- 10 条架构理解
- 10 条 PR Review

输出指标表，最好在 README 中展示一次对比：

| 方法 | Hit@5 | 引用覆盖率 | 平均延迟 | token 成本 |
| --- | --- | --- | --- | --- |
| 向量检索 | 待测 | 待测 | 待测 | 待测 |
| BM25 + 向量 | 待测 | 待测 | 待测 | 待测 |
| BM25 + 向量 + 图扩展 | 待测 | 待测 | 待测 | 待测 |

### 6.5 真实仓库演示

不要只用 toy repo。至少准备 2 个演示仓库：

- 一个 Python FastAPI 项目
- 一个 TypeScript/Next.js 项目

演示问题建议：

- “这个项目的启动流程是什么？”
- “登录鉴权逻辑在哪些文件中？”
- “修改这个函数可能影响哪些调用方？”
- “请审查这段 PR Diff 的潜在风险。”

### 6.6 README 和演示视频

大厂筛简历时，项目链接非常重要。README 必须包含：

- 项目定位
- 架构图
- 技术栈
- 核心流程
- Demo 截图
- 评测结果
- 本地启动方式
- 设计取舍
- 简历版描述

## 7. 建议调整后的 P0+ 功能边界

### 7.1 必做

- 本地仓库导入
- Python + TypeScript/JavaScript 文件解析
- 函数级 chunk
- BM25 检索
- Qdrant 向量检索
- 代码图邻域扩展
- 带引用代码问答
- Diff 粘贴式 PR Review
- Agent trace 展示
- 评测脚本和指标输出
- Docker Compose 启动

### 7.2 可选但强烈建议

- GitHub URL 导入
- 简化架构图可视化
- 静态检查工具接入，例如 ruff 或 eslint
- 增量索引
- 结果导出 Markdown

### 7.3 暂缓

- 多用户系统
- GitHub PR 评论写回
- Neo4j
- Kubernetes
- 复杂权限系统
- 支持几十种语言

## 8. 最终简历推荐写法

项目名称：

RepoLens：基于代码图谱 GraphRAG 的仓库级代码智能体平台

简历 bullet 推荐：

- 构建仓库级代码智能体平台，基于 AST/tree-sitter 提取文件、类、函数、导入和调用关系，生成函数级代码 chunk 与代码关系图，支持 Python、TypeScript/JavaScript 仓库的结构化理解。
- 设计 BM25 + 向量检索 + 图邻域扩展的混合检索链路，结合 Qdrant 与 reranker 召回相关代码上下文，回答和审查结论均输出文件路径、行号和证据片段。
- 基于 LangGraph 编排 Planner、Retriever、Reviewer、Verifier、Report Writer 多节点 Agent 工作流，实现仓库问答、PR Diff 风险审查、影响范围分析和测试建议生成。
- 设计 Agent trace、工具调用日志、token/耗时统计和评测脚本，构建代码定位、函数解释、架构问答、PR Review 评测集，对比不同检索策略的 Hit@K、引用覆盖率、幻觉率和端到端延迟。
- 使用 FastAPI、Next.js、SQLite、Qdrant、Docker Compose 完成全栈实现和本地部署，提供可交互 Web Demo、架构图、评测报告和 Markdown 导出。

## 9. 面试时的讲法

建议用这条主线讲：

我没有做一个普通的代码聊天机器人，而是把仓库理解拆成四层：第一层用 AST/tree-sitter 把代码结构化；第二层用 BM25、向量和代码图做混合检索；第三层用 LangGraph 把规划、检索、审查、验证和报告生成拆成可追踪 Agent 节点；第四层用评测和 trace 去控制幻觉、延迟和成本。这个项目的重点不是模型本身，而是围绕大模型构建一个可靠、可观测、可评估的工程系统。

## 10. 最终判断

RepoLens 可以作为面向大厂的大模型应用开发简历项目，但必须按 P0+ 标准实现。

最低合格线：

- 能导入真实仓库。
- 能做代码结构化解析。
- 能完成混合检索。
- 能输出带证据引用的问答和 Review。
- 能展示 Agent trace。
- 能给出评测指标。

真正亮眼线：

- 有代码图谱和影响范围分析。
- 有对比评测结果。
- 有漂亮但克制的 Web 工作台。
- 有可复现 Docker 部署。
- 有 README、截图、演示视频和简历版总结。

如果按这个标准完成，它不是“学生玩具项目”，而是一个能体现大模型应用工程能力的完整系统，适合放入大厂简历。

## 11. 参考资料

- LangGraph 官方文档：https://docs.langchain.com/oss/python/langgraph/overview
- MCP 官方文档：https://modelcontextprotocol.io/docs/learn/server-concepts
- Qdrant Hybrid Queries 文档：https://qdrant.tech/documentation/search/hybrid-queries/
- tree-sitter GitHub 仓库：https://github.com/tree-sitter/tree-sitter
- RepoReviewer 论文：https://arxiv.org/abs/2603.16107
- Codebase-Memory 论文：https://arxiv.org/abs/2603.27277

