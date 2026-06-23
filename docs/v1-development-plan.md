# RepoLens V1 后续开发计划与阶段概要设计

## 1. 文档信息

- 项目名称：RepoLens
- 文档类型：V1 后续开发计划与阶段概要设计
- 当前版本：v0.2
- 创建日期：2026-06-13
- 依据基线：
  - `docs/requirements-analysis.md`
  - `docs/outline-design.md`
  - `docs/p0-plus-development-plan.md`
  - `docs/phase5-detailed-design.md`
  - `docs/phase5-closed-loop-log.md`
- 当前基线状态：P0+ Phase 0 至 Phase 5 已完成并形成稳定基线

## 2. V1 定位

V1 是 RepoLens 在 P0+ 完成后的下一大阶段，不再属于原 P0+ 必做范围。P0+ 已经完成仓库导入、结构化解析、GraphRAG、带引用问答、PR Review、MCP-style 工具调用、评测、Docker Compose 和演示包装。

V1 的目标是把 RepoLens 从“面试可展示的仓库级 Code Agent”推进到“更接近真实开发工作流的代码智能体平台”。V1 重点引入：

- 多代码平台 PR/MR 集成与真实项目演示增强。
- 真正 MCP Server 化。
- 更完整的工具权限系统。
- 真正多 Agent 协作，而不只是单主编排下的角色节点。
- 更强的安全、审计、可观测和评测闭环。

V1 不推翻 P0+ 架构，而是在 P0+ 的 Repository、Retrieval、Review、Tool、Trace、Evaluation 基础上扩展。

## 3. V1 开发策略

### 3.1 基本原则

- 继续采用按 Phase 垂直闭环交付。
- 每个 Phase 开发前必须先写详细设计文档。
- 每个 Phase 都必须维护开发、审核、测试、评测闭环记录。
- 每个 Phase 必须有可运行、可演示、可验收结果。
- 不在同一 Phase 同时引入过多基础设施变化。
- 不破坏 P0+ 已有 API、评测和演示路径。

### 3.2 文档策略

本文件只定义 V1 总体路线和各阶段概要设计。后续每个阶段再单独创建详细设计，例如：

- `docs/phase6-detailed-design.md`
- `docs/phase6-closed-loop-log.md`
- `docs/phase7-detailed-design.md`
- `docs/phase7-closed-loop-log.md`
- `docs/phase8-detailed-design.md`
- `docs/phase8-closed-loop-log.md`

开发时不得直接用本文件代替阶段详细设计。

### 3.3 范围边界

V1 可以做：

- 读取 GitHub/Gitee/GitLab 等代码平台的 PR/MR metadata、diff、files、commits。
- 用现有 Review pipeline 审查真实 PR/MR。
- 将 MCP-style Tool Layer 升级为真正 MCP Server。
- 增强工具权限模型、审批策略、审计日志和前端展示。
- 引入多 Agent 协作协议、消息记录、任务分派和仲裁机制。
- 增强评测数据、演示仓库和真实开源仓库演示。

V1 默认不做：

- 自动向代码平台 PR/MR 写评论，除非单独 Phase 明确加入人工确认和权限边界。
- 自动修改用户代码并 push。
- 任意命令执行。
- 多租户 SaaS、计费、团队权限。
- Kubernetes 或复杂云原生部署。
- 企业级大仓库分布式索引。

## 4. V1 总体阶段规划

| 阶段 | 建议周期 | 主题 | 核心交付 |
| --- | --- | --- | --- |
| Phase 6 | 1 周 | 多代码平台 PR/MR 集成与真实项目演示增强 | Change Request Provider、GitHub/Gitee/GitLab 适配器、真实 PR/MR Review demo |
| Phase 7 | 1-1.5 周 | 真正 MCP Server 化与工具权限系统增强 | MCP Server、工具注册表、权限策略、审计日志、客户端调用演示 |
| Phase 8 | 1-1.5 周 | 真正多 Agent 协作 | Agent 会话、消息总线、任务分派、并行审查、仲裁与反思 |
| Phase 9 | 0.5-1 周 | V1 评测与真实项目 Benchmark | 多平台 PR/MR 评测集、Review 质量指标、多 Agent 对比评测 |
| Phase 10 | 0.5-1 周 | V1 演示、文档与发布包装 | README V1、演示脚本、截图/视频、简历与面试材料升级 |

## 5. Phase 6：多代码平台 PR/MR 集成与真实项目演示增强

### 5.1 目标

Phase 6 的目标是让 RepoLens 能从主流代码平台的 PR/MR URL 或仓库/变更编号中读取真实变更信息，复用 P0+ 的 Review pipeline 生成审查报告，从而把 P0+ 的“粘贴 diff 演示”升级为“真实代码平台 PR/MR 演示”。

Phase 6 的设计必须采用平台无关的 Change Request Provider 抽象。GitHub 可以作为第一个落地适配器，但 API、数据模型、前端文案和评测 schema 不应绑定为 GitHub-only。后续应能在同一契约下扩展 Gitee Pull Request、GitLab Merge Request 和自建 GitLab。

### 5.2 核心能力

- 多平台 PR/MR URL 解析。
- 平台 API Token 配置和安全读取。
- Change Request Provider 抽象和平台适配器注册。
- 首批适配 GitHub PR；预留 Gitee Pull Request、GitLab Merge Request 和 self-hosted GitLab。
- 拉取变更 metadata。
- 拉取变更 diff。
- 拉取 changed files。
- 拉取 commits 基础信息。
- 将 PR/MR diff 转换为现有 Review API 输入。
- 前端新增平台无关的 PR/MR Review 输入区。
- Review 报告显示平台、标题、作者、源/目标分支、文件列表和风险摘要。
- README 增加真实 PR/MR 演示流程。

### 5.3 任务清单

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P6-001 | 编写 Phase 6 详细设计 | 覆盖 Change Request Provider、平台适配器、API、前端、错误处理、安全边界、测试和验收 |
| P6-002 | 新增多平台配置项 | GitHub/Gitee/GitLab token、base URL、timeout、rate limit 配置 |
| P6-003 | 实现 PR/MR URL parser | 支持 GitHub PR URL，预留 Gitee PR 和 GitLab MR URL 解析契约 |
| P6-004 | 实现首个 Change Request client | 先落地 GitHub PR client，读取 metadata、files、diff、commits |
| P6-005 | 新增 change_requests 数据模型 | 保存外部平台、仓库、编号、metadata 与审查任务关联 |
| P6-006 | 新增 PR/MR Review API | 输入 PR/MR URL，返回或创建 Review task |
| P6-007 | 接入现有 Review pipeline | 复用 analyze_diff、code_search、symbol_context、Risk Reviewer |
| P6-008 | 前端新增 PR/MR Review flow | 平台 URL 输入、加载状态、metadata 和报告展示 |
| P6-009 | 错误处理与安全边界 | token 缺失、rate limit、private repo 权限、巨大 diff、平台不支持 |
| P6-010 | 准备真实演示 PR/MR | 选择公开小型 repo 或本仓库自造 PR/MR 示例 |
| P6-011 | 测试与评测 | mock 平台 API、真实 public PR/MR smoke、前端 build |
| P6-012 | 更新文档和演示材料 | README、worklog、截图 |

### 5.4 验收标准

- 用户输入受支持平台的 PR/MR URL 后能看到变更 metadata。
- 系统能拉取 diff 并生成 Review 报告。
- Review 报告仍包含 risks、suggested_tests、citations、tool_calls、trace。
- token 不写入日志、不进入数据库明文字段、不出现在截图。
- 平台 API 失败时有明确错误提示。
- 大 diff 被限制或截断，并给出原因。
- 暂不支持的平台 URL 有明确 unsupported provider 提示。

### 5.5 暂不做

- 不自动向 PR/MR 写评论。
- 不自动 approve/request changes。
- 不自动修改代码。
- 不做 GitHub App、Gitee 应用、GitLab App/OAuth 安装流程。

## 6. Phase 7：真正 MCP Server 化与工具权限系统增强

### 6.1 目标

Phase 7 的目标是把 P0+ 的 MCP-style Tool Layer 升级为真正可被 MCP client 调用的 RepoLens MCP Server，并建立更完整的工具权限系统。此阶段重点展示 RepoLens 不只是内部工具调用，而是能作为外部 Agent/IDE 的代码智能工具服务。

### 6.2 核心能力

- MCP Server 进程或 FastAPI-adjacent MCP endpoint。
- 工具注册表。
- 工具 schema 自动导出。
- 工具权限策略。
- 工具调用审计日志。
- 工具调用 replay/debug。
- MCP client smoke demo。
- 前端 Tool Permissions Panel。

### 6.3 工具范围

Phase 7 初始暴露以下工具：

- `list_repositories`
- `get_repository_status`
- `code_search`
- `read_file_slice`
- `get_symbol_context`
- `analyze_diff`
- `review_diff`
- `ask_repository`
- `run_safe_static_check`

其中 `run_safe_static_check` 仍默认关闭，只允许白名单 checker，不执行任意命令。

### 6.4 任务清单

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P7-001 | 编写 Phase 7 详细设计 | 覆盖 MCP Server、工具协议、权限模型、审计、测试 |
| P7-002 | 设计 Tool Registry | 统一工具名、schema、权限级别、handler |
| P7-003 | 设计权限模型 | allow、deny、confirm_required、disabled、read_only、safe_check |
| P7-004 | 实现 MCP Server 启动入口 | 支持本地 stdio 或 HTTP transport，按详细设计确定 |
| P7-005 | 导出只读工具 | list/status/search/read/symbol/analyze |
| P7-006 | 导出高阶工具 | ask_repository、review_diff |
| P7-007 | 增强 tool_calls 审计字段 | client、session、permission_policy、input_hash、output_hash |
| P7-008 | 前端 Tool Permissions Panel | 展示工具权限、调用历史、拒绝原因 |
| P7-009 | MCP client smoke test | 使用本地 client 调用 code_search/read_file_slice |
| P7-010 | 安全测试 | 路径穿越、敏感文件读取、超大输入、禁用工具 |
| P7-011 | 文档与演示 | README 增加 MCP Server 启动与调用示例 |

### 6.5 验收标准

- MCP client 能列出 RepoLens 工具。
- MCP client 能调用只读工具并获得结构化结果。
- 工具调用会写入审计记录。
- 权限拒绝有明确原因。
- 敏感文件和仓库目录外文件不能被读取。
- disabled 工具不可绕过。

### 6.6 暂不做

- 不暴露任意 shell。
- 不暴露文件写入工具。
- 不做远程公网 MCP 服务。
- 不做 OAuth 或多用户权限。

## 7. Phase 8：真正多 Agent 协作

### 7.1 目标

Phase 8 的目标是从 P0+ 的“单主 orchestrator + 角色型 Agent 节点”升级为更接近真实 Multi-Agent 协作的工作流。核心不是堆 Agent 名称，而是引入明确的协作协议、消息记录、任务分派、并行分析、冲突处理和仲裁机制。

### 7.2 多 Agent 设计方向

Phase 8 中每个 Agent 仍必须受到系统状态机约束，不能无限自由对话。新增能力包括：

- Agent Session。
- Agent Message。
- Agent Assignment。
- Agent Memory Snapshot。
- Debate/Review Round。
- Arbiter/Coordinator。
- Confidence and dissent tracking。
- 多 Agent trace 可视化。

### 7.3 建议 Agent 角色

| Agent | 职责 |
| --- | --- |
| Coordinator Agent | 拆解任务、分配角色、控制轮次 |
| Repository Analyst Agent | 负责仓库结构、模块关系、调用链 |
| Retrieval Specialist Agent | 负责检索计划、二次检索、证据覆盖 |
| Risk Reviewer Agent | 负责 PR 风险识别 |
| Security Reviewer Agent | 负责安全相关风险 |
| Test Strategist Agent | 负责测试缺口和测试建议 |
| Verifier Agent | 检查结论是否有证据 |
| Arbiter Agent | 处理 Agent 分歧，形成最终决策 |
| Report Writer Agent | 输出最终报告 |

### 7.4 任务清单

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P8-001 | 编写 Phase 8 详细设计 | 覆盖多 Agent 协议、状态、消息、UI、评测 |
| P8-002 | 新增 agent_sessions 表 | 保存一次多 Agent 协作会话 |
| P8-003 | 新增 agent_messages 表 | 保存 Agent 间消息、引用证据和结论 |
| P8-004 | 新增 agent_assignments 表 | 保存任务分派、状态、输入输出 |
| P8-005 | 实现 Coordinator Agent | 拆解问题并分配角色 |
| P8-006 | 实现并行 Review 子任务 | 风险、安全、测试三个视角独立分析 |
| P8-007 | 实现 Arbiter Agent | 合并分歧、保留 dissent、输出决策理由 |
| P8-008 | 实现多 Agent 轮次限制 | 防止无限循环和 token 失控 |
| P8-009 | 实现 Evidence-grounded message policy | Agent 消息中的关键结论必须绑定 evidence |
| P8-010 | 前端 Multi-Agent Trace Panel | 展示角色、消息、分歧、仲裁和最终报告 |
| P8-011 | 多 Agent 评测 | 对比单主角色流与多 Agent 协作流 |
| P8-012 | 文档与演示 | README 和截图增加多 Agent 协作讲解 |

### 7.5 验收标准

- 一次 Review 可产生多个 Agent 的独立分析。
- Agent 间消息可追踪。
- 分歧不会被静默丢弃，必须由 Arbiter 记录处理。
- 最终报告能说明哪些结论来自哪些 Agent 和证据。
- 多 Agent 流程有轮次限制、token 限制和失败降级。
- 前端能展示多 Agent 协作过程。

### 7.6 暂不做

- 不做无限自治 Agent。
- 不做跨进程 Agent 网络。
- 不做长期个人记忆。
- 不让 Agent 自动执行代码修改或 push。

## 8. Phase 9：V1 评测与真实项目 Benchmark

### 8.1 目标

Phase 9 的目标是为 V1 的多代码平台 PR/MR 集成、MCP Server 和多 Agent 协作建立评测闭环。P0+ 已有 50 条检索评测样例，V1 需要新增真实 PR/MR 场景和多 Agent 质量评测。

### 8.2 核心能力

- 多平台 PR/MR benchmark dataset。
- Review quality rubric。
- 单 Agent vs 多 Agent 对比。
- MCP tool reliability metrics。
- 权限拒绝/安全测试集。
- 真实开源仓库演示报告。

### 8.3 任务清单

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P9-001 | 编写 Phase 9 详细设计 | 覆盖评测数据、指标、运行器、报告 |
| P9-002 | 设计 PR/MR benchmark schema | platform、URL、diff、expected risk、expected files、labels |
| P9-003 | 准备 20-30 条 PR/MR 样例 | public repo 或本仓库 synthetic PR/MR |
| P9-004 | 设计 Review quality metrics | risk hit、citation coverage、unsupported claim rate |
| P9-005 | 设计 Multi-Agent metrics | dissent usefulness、arbiter resolution、token overhead |
| P9-006 | 设计 MCP metrics | tool success rate、permission denial correctness、latency |
| P9-007 | 实现 V1 Evaluation Runner | 支持 PR Review 和 MCP tool eval |
| P9-008 | 前端 Evaluation Panel 扩展 | 展示 V1 指标和对比结果 |
| P9-009 | 生成 V1 benchmark report | README 和 docs 报告 |

### 8.4 验收标准

- 至少 20 条 PR/MR Review 评测样例。
- 能对比 P0+ Review flow 与 V1 multi-agent flow。
- 能输出 Review 命中、引用覆盖、无证据结论比例、延迟、token。
- 能输出 MCP tool success/deny metrics。
- README 中有 V1 指标表。

## 9. Phase 10：V1 演示、文档与发布包装

### 9.1 目标

Phase 10 的目标是把 V1 能力整理为可展示、可复现、可面试讲解的完整材料。它不是堆新功能，而是收束多代码平台 PR/MR 集成、MCP Server 和多 Agent 协作的故事线。

### 9.2 核心能力

- README V1 升级。
- V1 架构图。
- PR/MR demo script。
- MCP client demo script。
- Multi-Agent trace demo。
- V1 screenshots。
- 面试讲稿。
- 简历 bullet v2。

### 9.3 任务清单

| 编号 | 任务 | 说明 |
| --- | --- | --- |
| P10-001 | 编写 Phase 10 详细设计 | 覆盖文档、截图、演示、验收 |
| P10-002 | README V1 更新 | 加入多代码平台 PR/MR、MCP Server、多 Agent |
| P10-003 | V1 架构图更新 | 展示代码平台/MCP/Multi-Agent 新链路 |
| P10-004 | 准备演示脚本 | 三条演示路径：PR/MR、MCP、多 Agent |
| P10-005 | 录制或整理截图 | Workbench、MCP client、Multi-Agent trace |
| P10-006 | 更新简历 bullet | 强调 V1 能力和指标 |
| P10-007 | 更新面试讲法 | 讲清为什么分 Phase 引入复杂能力 |
| P10-008 | 最终测试与发布检查 | 全量测试、build、compose、敏感信息扫描 |

### 9.4 验收标准

- README 能清晰区分 P0+ 与 V1。
- 有 PR/MR Review 真实演示路径。
- 有 MCP Server 调用演示路径。
- 有 Multi-Agent trace 演示截图。
- 有 V1 benchmark 指标。
- 敏感信息扫描通过。
- 远程仓库展示完整。

## 10. V1 模块演进图

| 模块 | P0+ 状态 | V1 演进 |
| --- | --- | --- |
| Repository Provider | 本地/Git URL 导入 | 多平台 Change Request metadata/files/commits Provider |
| Review Service | 粘贴 diff 审查 | PR/MR URL 审查，真实变更 Review demo |
| Tool Layer | MCP-style 内部工具 | 真正 MCP Server + tool registry |
| Tool Permissions | allow/deny/placeholder | policy、confirm_required、audit、input/output hash |
| Agent System | 单主 orchestrator + 角色节点 | Agent sessions、messages、assignments、arbiter |
| Trace | Agent trace + tool calls | 多 Agent trace、dissent、仲裁记录 |
| Evaluation | 50 条检索样例 | PR/MR benchmark、MCP metrics、multi-agent metrics |
| Frontend | Workbench panels | PR/MR Review Panel、Tool Permissions Panel、Multi-Agent Trace Panel |
| Docs | P0+ README 和截图 | V1 README、真实 PR/MCP/Multi-Agent 演示 |

## 11. V1 风险与控制

| 风险 | 表现 | 控制方式 |
| --- | --- | --- |
| 多平台集成过早复杂化 | token、权限、rate limit、private repo/self-hosted 差异拖慢开发 | Phase 6 先定义平台无关契约，首个适配器可先落地 GitHub；只读 PR/MR，不写评论，不做平台 App |
| MCP Server 范围失控 | 变成通用工具平台 | Phase 7 只暴露 RepoLens 已有工具，不新增写操作 |
| 多 Agent 概念空转 | Agent 多但没有质量提升 | Phase 8 必须记录 dissent、arbiter、证据和对比评测 |
| 安全风险 | 路径穿越、敏感文件、任意命令执行 | 工具权限策略、敏感文件过滤、默认禁用执行类工具 |
| Token 成本失控 | 多 Agent 多轮对话导致成本爆炸 | 轮次限制、context budget、evidence budget、token 记录 |
| 评测不可信 | 指标只靠人工演示 | Phase 9 建立 PR/MR benchmark 和 MCP metrics |
| 文档复杂难懂 | 面试官看不懂版本演进 | Phase 10 明确 P0+ baseline 与 V1 upgrades |

## 12. V1 最终验收总清单

### 12.1 功能验收

- 支持受支持平台的 PR/MR URL 输入。
- 支持拉取 PR/MR metadata、diff、changed files。
- 支持基于真实 PR/MR 生成 Review 报告。
- 支持启动 RepoLens MCP Server。
- 支持 MCP client 调用核心只读工具。
- 支持工具权限策略和审计日志。
- 支持多 Agent 协作会话。
- 支持 Agent message、assignment、dissent 和 arbiter 记录。
- 支持 V1 benchmark 评测。

### 12.2 展示验收

- 前端可展示 PR/MR Review flow。
- 前端可展示 Tool Permissions 和 MCP tool calls。
- 前端可展示 Multi-Agent Trace。
- README 有 V1 架构、启动、演示、指标和截图。
- 有真实 PR 或 public repo 演示材料。

### 12.3 安全验收

- 平台 token 不落日志、不入截图。
- 工具不能读取仓库目录外文件。
- 敏感文件默认拒绝读取。
- 执行类工具默认禁用。
- MCP Server 不提供任意 shell。
- 自动写回代码平台必须默认不启用。

### 12.4 评测验收

- 至少 20 条 PR/MR Review benchmark。
- 至少一组单主角色流 vs 多 Agent 协作流对比。
- 输出 Review risk hit、citation coverage、unsupported claim rate。
- 输出 MCP tool success rate 和 permission denial correctness。
- 输出 latency 和 token overhead。

## 13. 推荐执行顺序

1. Phase 6：多代码平台 PR/MR 集成与真实项目演示增强。
2. Phase 7：真正 MCP Server 化与工具权限系统增强。
3. Phase 8：真正多 Agent 协作。
4. Phase 9：V1 评测与真实项目 Benchmark。
5. Phase 10：V1 演示、文档与发布包装。

执行时必须先为当前 Phase 写详细设计，再开发。当前文件只作为 V1 路线图，不作为直接开发依据。
