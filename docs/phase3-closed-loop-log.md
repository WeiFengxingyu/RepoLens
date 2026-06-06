# RepoLens Phase 3 开发审核测试评测闭环记录

## 1. 文档用途

本文档用于记录 Phase 3 的开发、审核、测试和评测闭环。记录粒度与 `docs/p0-plus-development-plan.md` 中 P3-001 到 P3-011 对齐，确保每个任务都有开发、审核、测试和评测记录。

## 2. 当前状态

- 当前阶段：Phase 3 - 带引用仓库问答
- 当前状态：已完成 P3-DESIGN、P3-001 至 P3-011
- 开始日期：2026-06-06
- 依据文档：`docs/phase3-detailed-design.md`

## 3. 任务闭环记录

| 编号 | 任务 | 开发状态 | 审核状态 | 测试状态 | 评测/指标状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| P3-DESIGN | Phase 3 详细设计 | 完成 | 通过 | 文档审查通过 | 完成 | 新增 Phase 3 详细设计，覆盖 tasks、agent_traces、QA API、单主 LangGraph Orchestrator、QA 角色型 Agent、二次检索、Ask Panel、Trace Panel、Evidence 引用、安全、测试和验收 |
| P3-001 | 实现 tasks 表 | 完成 | 通过 | 通过 | 完成 | 新增 `Task`、`TaskType`、`TaskStatus`，保存 QA 任务状态、输入、输出、错误和时间戳 |
| P3-002 | 实现 agent_traces 表 | 完成 | 通过 | 通过 | 完成 | 新增 `AgentTrace`、`AgentTraceStatus`，保存 Agent 节点步骤、耗时、token、工具调用、证据 ID 和错误 |
| P3-003 | 实现 QA API | 完成 | 通过 | 通过 | 完成 | 新增 QA schema、QAService、`POST /api/repositories/{id}/questions` 和 `GET /api/tasks/{task_id}`；P3-008/P3-009 后已升级为同步执行 Orchestrator |
| P3-004 | 实现 Planner Agent | 完成 | 通过 | 通过 | 完成 | 新增规则 Planner，支持 5 类 QA 问题分类、最多 3 条检索 query、graph 使用建议和空问题校验 |
| P3-005 | 实现 Retrieval Agent | 完成 | 通过 | 通过 | 完成 | 新增 Retrieval Agent，调用 Phase 2 Hybrid Retriever，支持多 query 检索、按 chunk_id 去重、QA context 构建、vector disabled warning 和 tool call 摘要 |
| P3-006 | 实现 Answer Reviewer Agent | 完成 | 通过 | 通过 | 完成 | 新增 OpenAI-compatible Chat Adapter 和 Answer Reviewer，支持模型 JSON 草稿、证据型 fallback、无 evidence 草稿、claims 和 token_usage |
| P3-007 | 实现 Verifier Agent | 完成 | 通过 | 通过 | 完成 | 新增规则 Verifier，检查 claim evidence_id 是否存在且 snippet 非空，证据不足时标记一次补充检索 |
| P3-008 | 实现二次检索机制 | 完成 | 通过 | 通过 | 完成 | 新增单主 LangGraph Orchestrator，Verifier 证据不足时最多触发一次补充 Retriever/AnswerReviewer/Verifier |
| P3-009 | 实现 Report Writer Agent | 完成 | 通过 | 通过 | 完成 | 新增 `write_report` 和 QA API 同步执行，输出 answer、citations、confidence、warnings、verification |
| P3-010 | 实现 Trace Panel | 完成 | 通过 | 通过 | 完成 | 前端展示 Agent step、status、latency、token、evidence_count、input/output summary 和 tool_calls |
| P3-011 | 实现 Ask Panel | 完成 | 通过 | 通过 | 完成 | 前端支持输入问题、top_k、BM25/vector/graph toggles，并展示 answer、citations、confidence、warnings |

## 4. 审核记录

| 日期 | 范围 | 结论 | 问题 | 处理 |
| --- | --- | --- | --- | --- |
| 2026-06-06 | Phase 3 详细设计 | 通过 | 不应提前进入 PR Review、MCP Server、复杂自治 Multi-Agent 或完整评测集 | 设计限定为 QA 闭环，采用单主 LangGraph Orchestrator + 角色型 Agent 节点，只落地 P3-001 到 P3-011 |
| 2026-06-06 | P3-001/P3-002 数据模型 | 通过 | 需要避免 SQLAlchemy 保留名和循环导入；不应提前实现 QA API 或 Agent 逻辑 | `input`/`output` 数据库列映射为 `input_payload`/`output_payload` 属性；仅新增模型、关系、索引和 round-trip 测试 |
| 2026-06-06 | P3-003 QA API | 通过 | 不应伪造尚未实现的 Agent 回答；不应提前进入 Planner/Retriever/Verifier 逻辑 | P3-003 先实现 pending task 骨架；P3-008/P3-009 已升级为同步执行 Orchestrator 并返回 completed/failed task |
| 2026-06-06 | P3-004 Planner Agent | 通过 | `import` 容易被误判为调用关系；不应调用 LLM 增加成本 | 调用关系规则收紧为 `imports`/caller/callee/call 等更明确触发词；Planner 采用规则实现，不调用模型 |
| 2026-06-06 | P3-005 Retrieval Agent | 通过 | 不应重新实现检索链路或绕过 repository_id 过滤；多 query 可能产生重复 evidence | 复用 Phase 2 `retrieve_repository`；按 `chunk_id` 保留最高分 evidence，并重建 QA context |
| 2026-06-06 | P3-006 Answer Reviewer Agent | 通过 | 不应联网调用真实模型测试；chat 配置缺失时不应伪装成 LLM 输出 | 新增 OpenAI-compatible Chat Adapter，单元测试使用 fake transport；缺配置时输出 `disabled_fallback` 并写 warning/token_usage=0 |
| 2026-06-06 | P3-007 Verifier Agent | 通过 | Verifier 不应补写新事实或直接修改回答；二次检索不应无限循环 | Verifier 只校验 claim citation，输出 missing_claims、valid_evidence_ids 和最多一次 second_retrieval_query |
| 2026-06-06 | P3-008/P3-009 Orchestrator 与 Report Writer | 通过 | 必须真实接入 LangGraph；证据不足不能无限循环；Report Writer 不应输出无 citation 高 confidence 回答 | 安装并写入 `langgraph` 依赖；使用 `StateGraph(QAAgentState)`；二次检索最多一次；无 citation confidence 降到 0.2 |
| 2026-06-06 | P3-010/P3-011 前端 Ask/Trace Panel | 通过 | 不应把 Phase 2 Evidence Debug 替代 QA；Trace 长文本不能撑破布局 | 保留 Evidence Debug；新增独立 Ask Panel 和 Trace Panel；长文本使用 `pre`/break/scroll 控制 |

## 5. 测试记录

| 日期 | 范围 | 命令/方式 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| 2026-06-06 | Phase 3 详细设计 | 文档审查 | 通过 | 尚未进入 P3 代码开发 |
| 2026-06-06 | P3-001/P3-002 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P3-001/P3-002 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 65 个测试通过，含新增 Phase 3 模型表创建、任务/trace round-trip 和 repository cascade |
| 2026-06-06 | P3-003 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P3-003 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 68 个测试通过，含 QA task 创建、任务查询、未 ready 仓库拒绝和缺失 task 404 |
| 2026-06-06 | P3-004 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P3-004 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 74 个测试通过，含 Planner 五类问题分类、query 上限、graph 建议和空问题校验 |
| 2026-06-06 | P3-005 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P3-005 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 76 个测试通过，含 Retrieval Agent 多 query 检索去重、context 生成、tool_calls 和 vector disabled warning |
| 2026-06-06 | P3-006 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P3-006 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 83 个测试通过，含 Chat Adapter disabled、fake transport、JSON 校验、Answer Reviewer chat/fallback/no evidence |
| 2026-06-06 | P3-007 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P3-007 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 87 个测试通过，含 valid claim、missing evidence、二次检索触发、二次后不再重试和无 claims |
| 2026-06-06 | P3-008/P3-009 | `.\\.venv\\Scripts\\python.exe -m pip install "langgraph>=0.2.0"` | 通过 | 首次沙箱内安装因网络超时，随后经授权联网安装成功；`backend/pyproject.toml` 已记录 `langgraph>=1.2.0` |
| 2026-06-06 | P3-008/P3-009 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P3-008/P3-009 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 90 个测试通过，含同步 QA API、LangGraph trace、二次检索、Report Writer citations/confidence |
| 2026-06-06 | P3-010/P3-011 | `npm run build` | 通过 | 前端 build 和类型检查通过 |
| 2026-06-06 | P3-010/P3-011 | Browser UI smoke | 未完成 | 当前线程未暴露 in-app Browser 控制工具；已用前端 build/type check 覆盖类型和编译风险 |
| 2026-06-06 | Phase 3 最终验证 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | Phase 3 最终验证 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 90 个测试通过，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | Phase 3 最终验证 | `npm run build` | 通过 | 前端生产构建通过 |

## 6. 评测指标记录

Phase 3 先记录 5 类 QA smoke 样例，不建设完整 50 条评测集。完整评测留给 Phase 5。

| 日期 | 问题类型 | query | evidence_count | citation_count | verifier_result | confidence | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-06 | architecture | `Explain the overall architecture and module flow.` | - | - | planner classified | - | Planner 可识别 architecture 并生成 architecture/module/flow 检索计划 |
| 2026-06-06 | feature_location | `Where is repository import implemented?` | 2 | 1+ | supported | 0.65 | QA API fixture 可返回 answer/citations/traces |
| 2026-06-06 | function_explanation | `What does RepositoryService.import_repository do?` | - | - | planner classified | - | Planner 可识别 function_explanation 并保留 symbol query |
| 2026-06-06 | call_relation | `How does main call helper?` | 2+ | - | planner/retrieval covered | - | Planner 开启 graph；Retrieval Agent fixture 可召回调用关系 evidence |
| 2026-06-06 | impact_scope | `What is impacted if parser output changes?` | - | - | planner classified | - | Planner 可识别 impact_scope，开启 graph，并生成 affected/callers/callees query |
| 2026-06-06 | data_model | `tasks + agent_traces round-trip` | - | - | - | - | SQLite 表创建、JSON payload、trace token_usage 和级联删除通过单元测试 |
| 2026-06-06 | qa_api | `POST /questions + GET /tasks` | - | - | - | - | ready 仓库可同步执行 QA Orchestrator；未 ready 仓库返回 400 |
| 2026-06-06 | planner | 5 类 fixture questions | - | - | - | - | architecture、feature_location、function_explanation、call_relation、impact_scope 均可分类并生成检索计划 |
| 2026-06-06 | retrieval_agent | `How does main call helper?` | 2+ | - | - | - | 多 query 调用 Hybrid Retriever 后可去重 evidence、生成 context 并记录 code_search tool call |
| 2026-06-06 | answer_reviewer | `Where is repository import implemented?` | 1 | 1 | - | - | fake evidence 可生成带 evidence_id claim 的草稿；chat disabled fallback 不消耗 token |
| 2026-06-06 | verifier | `Repository import uses an async queue.` | 1 | 0 | missing evidence | - | 缺 citation claim 可触发 second_retrieval_query；retrieval_attempts=2 后不再重试 |
| 2026-06-06 | qa_orchestrator | `Where is repository import implemented?` | 2 | 1+ | supported | 0.65 | fixture 仓库可同步返回 answer/citations/traces；chat disabled fallback 限制最高 confidence |
| 2026-06-06 | second_retrieval | `Where is repository import implemented?` on empty repo | 0 | 0 | unsupported | 0.2 | 无 evidence 时 Trace 中出现 2 次 Retriever，最终降级 confidence 并输出 warning |
| 2026-06-06 | frontend_build | Ask/Trace Panel | - | - | - | - | 前端类型检查和生产构建通过；浏览器截图验证待 Browser 工具可用后补 |

## 7. 下一步

Phase 3 已完成。下一步按 `docs/p0-plus-development-plan.md` 进入 Phase 4：PR Review、Multi-Agent 与 MCP-style 工具调用；进入前应先创建 Phase 4 详细设计和闭环记录。
