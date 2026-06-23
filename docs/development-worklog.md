# RepoLens 开发过程记录

## 1. 文档用途

本文档用于概括记录 RepoLens 的开发过程，按 `docs/p0-plus-development-plan.md` 中的 Phase 和任务编号维护进度。记录保持简洁，重点匹配开发计划，不展开过多实现细节。

## 2. 当前阶段

- 当前阶段：V1 Phase 7 - 真正 MCP Server 化与工具权限系统增强
- 当前状态：Phase 7 已完成；RepoLens 已具备 HTTP JSON-RPC MCP endpoint、Tool Registry、权限审计和 Tool Permissions Panel
- 开始日期：2026-06-05
- 完成日期：2026-06-14（Phase 7）

## 3. Phase 0 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P0-001 | 初始化 monorepo 目录 | 完成 | 创建 `backend`、`frontend`、`evals`，沿用根目录 `docs` |
| P0-002 | 初始化 FastAPI 后端 | 完成 | 创建 `backend/app`、API、core、db、services、models、schemas、prompts、tests |
| P0-003 | 初始化 Next.js 前端 | 完成 | 创建 `frontend/app` 工作台基础页面、配置和类型目录 |
| P0-004 | 建立配置管理 | 完成 | 创建 `.env.example` 和 `backend/app/core/config.py` |
| P0-005 | 建立 SQLite 连接 | 完成 | 创建 `backend/app/db/session.py`、`base.py`、`init_db.py` |
| P0-006 | 建立健康检查接口 | 完成 | 创建 `/health` 和 `/api/status` |
| P0-007 | 建立 Docker Compose 初版 | 完成 | 创建 `docker-compose.yml`，包含 backend、frontend、qdrant |
| P0-008 | README 初版 | 完成 | 创建根目录 `README.md` |

## 4. Phase 0 验收记录

| 验收项 | 状态 | 备注 |
| --- | --- | --- |
| 后端健康检查返回正常 | 完成 | 使用 FastAPI TestClient 验证 `/health` 和 `/api/status` |
| 前端能访问基础工作台页面 | 完成 | `npm run build` 通过，基础工作台页面可构建 |
| Docker Compose 能启动 Qdrant | 部分完成 | `docker compose config` 通过，服务定义包含 qdrant；尚未实际启动容器 |
| 项目目录符合概要设计 | 完成 | 已创建 backend、frontend、docs、evals 和核心子目录 |

## 5. Phase 0 验证记录

- 后端：创建 Python 3.11 虚拟环境，安装 FastAPI、Uvicorn、SQLAlchemy、pytest、httpx、ruff。
- 后端：`ruff check app` 通过。
- 后端：FastAPI TestClient 验证 `/health` 与 `/api/status` 返回正常。
- 前端：使用工作区内 npm cache 安装依赖，避免系统目录缓存权限问题。
- 前端：`npm run build` 通过。
- Docker Compose：`docker compose config` 通过。
- 注意：尚未实际执行 `docker compose up` 长时间启动服务，Phase 0 当前以配置校验和本地构建校验为准。

## 6. 下一步

进入 Phase 1 前，建议先确认是否补充详细接口/数据库设计文档；若直接继续开发，则按计划进入仓库导入与代码结构化。

## 7. Phase 1 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P1-DESIGN | Phase 1 详细设计 | 完成 | 创建 `docs/phase1-detailed-design.md` |
| P1-CLOSED-LOOP | Phase 1 闭环记录 | 完成 | 创建 `docs/phase1-closed-loop-log.md` |
| P1-001 | 实现 repositories 表 | 完成 | 新增 `backend/app/models/repository.py`，包含 Repository、RepositorySourceType、RepositoryStatus |
| P1-002 | 实现 code_chunks 表 | 完成 | 新增 `backend/app/models/code_chunk.py`，包含 CodeChunk、CodeLanguage、SymbolType |
| P1-003 | 实现 code_relations 表 | 完成 | 新增 `backend/app/models/code_relation.py`，包含 CodeRelation、RelationType |
| P1-004 | 实现仓库本地路径导入 | 完成 | 新增 Repository Provider、Repository Service 和 `/api/repositories`，本地路径可创建仓库记录 |
| P1-005 | 实现 Git URL 导入 | 完成 | 新增 GenericGitProvider，支持 GitHub/Gitee/GitLab/generic Git URL 识别并封装 clone 入口 |
| P1-006 | 实现目录扫描和过滤 | 完成 | 新增 `backend/app/services/scanner/scanner.py`，实现默认忽略目录、敏感文件、二进制文件和 1MB 文件上限过滤 |
| P1-007 | 实现语言识别 | 完成 | Scanner 识别 Python、TypeScript、JavaScript，并在导入服务中写入 repository 统计和 `language_summary` |
| P1-008 | 实现 Python 解析 | 完成 | 新增 `backend/app/services/parser/parser.py`，使用标准库 `ast` 提取 file/class/function/method/import/call |
| P1-009 | 实现 TS/JS 解析 | 完成 | 当前未引入 tree-sitter，按详细设计采用 fallback parser，提取 import/class/function/method/arrow function |
| P1-010 | 实现 chunk builder | 完成 | 新增 `backend/app/services/chunking/chunk_builder.py`，从 ParsedFile 生成 CodeChunkDraft，覆盖 method/function、class、file 和 parser failed fallback |
| P1-011 | 实现索引状态流转 | 完成 | RepositoryService 导入链路接入 scan/parse/chunk/save，状态流转为 scanning/parsing/chunking/ready/failed，并写入 chunk_count、relation_count、indexed_at |
| P1-012 | 前端展示仓库状态 | 完成 | 首页 Repository Panel 接入仓库导入、列表、详情、状态、语言统计和 file/parsed/skipped/chunk/relation 指标展示 |

## 8. Phase 1 验收记录

| 验收项 | 状态 | 备注 |
| --- | --- | --- |
| 本地路径导入可用 | 完成 | API 和前端均完成验证 |
| Git URL Provider 可识别 | 完成 | URL 识别和 clone 封装已测试；未联网拉真实仓库 |
| Scanner 过滤规则可用 | 完成 | 覆盖依赖目录、敏感文件、二进制文件和大小限制 |
| Python/TS/JS 结构解析可用 | 完成 | Python 使用 ast；TS/JS 使用 fallback parser |
| chunk 与 relation 落库可用 | 完成 | API 导入测试验证 code_chunks/code_relations |
| 前端展示仓库状态与统计 | 完成 | Browser 验证桌面与 390px 窄屏 |
| 后端测试通过 | 完成 | `pytest app\\tests` 25 passed |
| 前端构建通过 | 完成 | `npm run build` 通过 |

## 9. Phase 2 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P2-DESIGN | Phase 2 详细设计 | 完成 | 创建 `docs/phase2-detailed-design.md` |
| P2-CLOSED-LOOP | Phase 2 闭环记录 | 完成 | 创建 `docs/phase2-closed-loop-log.md` |
| P2-001 | 实现 BM25 索引 | 完成 | 新增 `backend/app/services/indexing/bm25.py`，实现轻量 tokenizer、BM25Document、BM25Index、document_from_chunk 和 build_bm25_index |
| P2-002 | 实现 embedding adapter | 完成 | 新增 `backend/app/services/indexing/embeddings.py`，实现 OpenAI-compatible adapter、配置读取、disabled 错误、请求响应校验、响应排序和维度校验 |
| P2-003 | 实现 Qdrant 写入 | 完成 | 新增 `backend/app/services/indexing/qdrant_store.py` 和向量索引 API，支持 collection ensure、chunk embedding、UUID-compatible point id、payload upsert、批量写入和明确错误返回 |
| P2-004 | 实现 Qdrant 检索 | 完成 | 新增 `QdrantVectorStore.search`、`VectorSearchFilters`、`VectorSearchResult` 和 `search_repository_chunks`，支持 query embedding、repository_id 强过滤、可选 filters 和 vector candidate 输出 |
| P2-005 | 实现 NetworkX 代码图 | 完成 | 新增 `backend/app/services/graph/code_graph.py`，引入 NetworkX DiGraph，从 SQLite chunks/relations 加载图节点和双端关系边 |
| P2-006 | 实现图邻域查询 | 完成 | 扩展 `backend/app/services/graph/code_graph.py`，新增 callers、callees、same_file、imports、一跳邻域和 graph expand 查询 |
| P2-007 | 实现候选合并去重 | 完成 | 新增 `backend/app/services/retrieval/candidates.py`，实现 `RetrievalCandidate` 和 `merge_candidates`，按 `chunk_id` 合并 BM25/vector/graph_expand 来源 |
| P2-008 | 实现轻量重排公式 | 完成 | 新增 `backend/app/services/retrieval/rerank.py`，实现 `RankedRetrievalCandidate` 和 `rerank_candidates`，按规则权重计算 final_score |
| P2-009 | 实现 Evidence 输出 | 完成 | 新增 `backend/app/services/retrieval/evidence.py`，实现 `Evidence`、稳定 evidence_id、snippet 截断和 ranked candidate 到 Evidence 的转换 |
| P2-010 | 实现 Context Builder | 完成 | 新增 `backend/app/services/retrieval/context.py`，实现 `ContextPackage` 和 `build_context_package`，支持 evidence 数量限制与字符预算 |
| P2-011 | 前端 Evidence Panel | 完成 | 新增 Retrieval Debug API、前端 Retrieval 类型/API helper 和首页 Evidence Panel，展示 source toggles、debug counters、vector disabled 提示和 evidence list |

## 10. Phase 2 基线验证记录

- 后端：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- 后端：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，25 个测试通过。
- 前端：`npm run build` 通过。
- 当前进入 P2-001 前，Phase 1 功能基线保持稳定。

## 11. Phase 2 验证记录

- P2-001：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-001：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，29 个测试通过。
- P2-001：新增 `backend/app/tests/test_phase2_bm25.py`，覆盖 tokenizer、chunk document 构建、BM25 排序、空 query 和 top_k 边界。
- P2-002：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-002：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，33 个测试通过。
- P2-002：新增 `backend/app/tests/test_phase2_embeddings.py`，覆盖 settings 配置读取、配置缺失错误、OpenAI-compatible 请求参数、响应排序和向量维度校验。
- P2-003：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-003：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，38 个测试通过。
- P2-003：新增 `backend/app/tests/test_phase2_qdrant_store.py`，覆盖稳定 UUID-compatible point id、collection 创建、upsert payload、空仓库、维度不匹配和 API disabled 错误。
- P2-004：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-004：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，42 个测试通过。
- P2-004：扩展 `backend/app/tests/test_phase2_qdrant_store.py`，覆盖 vector search 请求 payload、repository_id 强过滤、可选 filters、空 query/top_k、query embedding 数量异常和缺失 `chunk_id` 错误。
- P2-005：`backend/pyproject.toml` 新增 `networkx>=3.0.0` 依赖，并安装到后端 `.venv`。
- P2-005：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-005：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，44 个测试通过。
- P2-005：新增 `backend/app/tests/test_phase2_code_graph.py`，覆盖 NetworkX DiGraph 节点、边、跳过缺 target relation 和缺失仓库空图。
- P2-006：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-006：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，47 个测试通过。
- P2-006：扩展 `backend/app/tests/test_phase2_code_graph.py`，覆盖 callers、callees、same file、imports、一跳邻域、graph expand 去重截断和缺失/无效输入。
- P2-007：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-007：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，50 个测试通过。
- P2-007：新增 `backend/app/tests/test_phase2_candidates.py`，覆盖跨来源合并、重复来源最高分、matched terms 合并、sources 顺序和空输入。
- P2-008：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-008：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，53 个测试通过。
- P2-008：新增 `backend/app/tests/test_phase2_rerank.py`，覆盖分数归一化、权重公式、file/symbol relevance、top_k、稳定 tie order、空输入和零分输入。
- P2-009：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-009：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，57 个测试通过。
- P2-009：新增 `backend/app/tests/test_phase2_evidence.py`，覆盖 Evidence 字段、稳定 ID、snippet 截断、主 source、缺失 chunk 和跨仓库安全边界。
- P2-010：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-010：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，60 个测试通过。
- P2-010：新增 `backend/app/tests/test_phase2_context.py`，覆盖 context 格式化、数量限制、字符预算截断、空输入和无效限制。
- P2-011：新增 `backend/app/services/retrieval/hybrid.py` 和 `POST /api/repositories/{repository_id}/retrieve`，接通 BM25、vector disabled fallback、graph expand、merge、rerank、Evidence 和 Context Builder。
- P2-011：更新 `frontend/types/workbench.ts`、`frontend/lib/api.ts` 和 `frontend/app/page.tsx`，实现 Evidence Panel。
- P2-011：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P2-011：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，62 个测试通过。
- P2-011：`npm run build` 通过。
- P2-011：Browser 工具未暴露；后台 backend dev server 未能稳定保持，因此未完成浏览器截图验证，已用后端 API 集成测试和前端构建/类型检查覆盖主要风险。

## 12. Phase 3 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P3-DESIGN | Phase 3 详细设计 | 完成 | 创建 `docs/phase3-detailed-design.md`，覆盖 tasks 表、agent_traces 表、QA API、单主 LangGraph Orchestrator、Planner/Retrieval/Answer Reviewer/Verifier/Report Writer、二次检索、Ask Panel、Trace Panel、Evidence 引用、安全边界、测试策略和验收标准 |
| P3-CLOSED-LOOP | Phase 3 闭环记录 | 完成 | 创建 `docs/phase3-closed-loop-log.md`，按 P3-001 到 P3-011 建立开发、审核、测试和评测记录表 |
| P3-001 | 实现 tasks 表 | 完成 | 新增 `backend/app/models/task.py`，实现 `Task`、`TaskType`、`TaskStatus`，包含 repository 外键、状态、input/output JSON payload、错误信息和时间戳 |
| P3-002 | 实现 agent_traces 表 | 完成 | 新增 `backend/app/models/agent_trace.py`，实现 `AgentTrace`、`AgentTraceStatus`，包含 task 外键、step、status、summary、evidence_ids、tool_calls、token_usage、latency 和错误信息 |
| P3-003 | 实现 QA API | 完成 | 新增 `backend/app/schemas/qa.py`、`backend/app/services/qa/service.py` 和 `backend/app/api/qa.py`；P3-003 先实现 pending task 与查询，P3-008/P3-009 后已升级为同步执行 Orchestrator |
| P3-004 | 实现 Planner Agent | 完成 | 新增 `backend/app/services/agent/state.py` 和 `backend/app/services/agent/qa_agents.py`，实现规则 `plan_question`，支持 5 类 QA 问题分类、最多 3 条检索 query、graph 使用建议和空问题校验 |
| P3-005 | 实现 Retrieval Agent | 完成 | 扩展 `backend/app/services/agent/state.py` 和 `backend/app/services/agent/qa_agents.py`，实现 `retrieve_for_plan`，复用 Phase 2 `retrieve_repository`，支持多 query 检索、evidence 去重、QA context 构建、warnings 和 tool call 摘要 |
| P3-006 | 实现 Answer Reviewer Agent | 完成 | 新增 `backend/app/services/agent/chat.py` 和 `review_answer`，支持 OpenAI-compatible chat JSON 输出、证据型 fallback、无 evidence 草稿、claims、used_evidence_ids、warnings 和 token_usage |
| P3-007 | 实现 Verifier Agent | 完成 | 扩展 `backend/app/services/agent/state.py` 和 `backend/app/services/agent/qa_agents.py`，实现 `VerificationResult` 和 `verify_draft`，检查 claim citation 是否存在、snippet 是否非空，并输出二次检索建议 |
| P3-008 | 实现二次检索机制 | 完成 | 新增 `backend/app/services/agent/orchestrator.py`，使用 LangGraph `StateGraph(QAAgentState)` 编排 Planner、Retriever、AnswerReviewer、Verifier、ReportWriter，证据不足时最多二次检索一次 |
| P3-009 | 实现 Report Writer Agent | 完成 | 新增 `write_report`，并升级 QA API 同步执行 Orchestrator，输出 answer、citations、confidence、warnings、verification 和 agent_traces |
| P3-010 | 实现 Trace Panel | 完成 | 更新 `frontend/types/workbench.ts`、`frontend/lib/api.ts` 和 `frontend/app/page.tsx`，展示 Agent trace 的 step、status、latency、token、evidence_count、input/output summary 和 tool_calls |
| P3-011 | 实现 Ask Panel | 完成 | 更新 `frontend/app/page.tsx`，新增 Ask Panel，支持问题输入、top_k、BM25/vector/graph toggles、answer、citations、confidence 和 warnings 展示 |

## 13. Phase 3 验证记录

- P3-DESIGN：完成 `docs/phase3-detailed-design.md` 和 `docs/phase3-closed-loop-log.md`，文档审查通过。
- P3-001/P3-002：新增 `backend/app/models/task.py`、`backend/app/models/agent_trace.py`，并更新 `backend/app/models/repository.py` 和 `backend/app/models/__init__.py`。
- P3-001/P3-002：新增 `backend/app/tests/test_phase3_models.py`，覆盖 `tasks`/`agent_traces` 表创建、任务与 trace JSON round-trip、repository 删除级联清理 task/trace。
- P3-001/P3-002：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P3-001/P3-002：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，65 个测试通过。
- P3-003：新增 `backend/app/schemas/qa.py`，定义 `QACreateRequest`、`QATaskResponse`、`QACitationResponse` 和 `AgentTraceResponse`。
- P3-003：新增 `backend/app/services/qa/service.py`，实现 QA task 创建、repository ready 校验、task 查询和 response 构建。
- P3-003：新增 `backend/app/api/qa.py`，实现 `POST /api/repositories/{repository_id}/questions` 和 `GET /api/tasks/{task_id}`，并在 `backend/app/main.py` 注册 router。
- P3-003/P3-008/P3-009：更新 `backend/app/tests/test_phase3_qa_api.py`，覆盖 ready repository 同步 QA answer/citations/traces、无 evidence 二次检索、未 ready 仓库拒绝和缺失 task 404。
- P3-003：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P3-003：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，68 个测试通过。
- P3-004：新增 `backend/app/services/agent/state.py`，定义 `QAQuestionType` 和 `QAPlan`。
- P3-004：新增 `backend/app/services/agent/qa_agents.py`，实现规则 Planner，支持 architecture、feature_location、function_explanation、call_relation、impact_scope 五类问题。
- P3-004：新增 `backend/app/tests/test_phase3_planner_agent.py`，覆盖五类问题分类、检索 query 上限、graph 使用建议和空问题校验。
- P3-004：自查时发现 `import` 会让 “repository import implemented” 误判为 call_relation，已将调用关系关键词收紧为 `imports` 等更明确触发词。
- P3-004：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P3-004：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，74 个测试通过。
- P3-005：扩展 `backend/app/services/agent/state.py`，新增 `RetrievalOptions`、`AgentToolCall` 和 `RetrievalAgentResult`。
- P3-005：扩展 `backend/app/services/agent/qa_agents.py`，新增 `retrieve_for_plan`，按 Planner query 调用 Phase 2 `retrieve_repository`，累计 debug counts 和 vector disabled warning。
- P3-005：Retrieval Agent 按 `chunk_id` 对多 query evidence 去重，保留最高 score，并用 `build_context_package` 生成 QA context。
- P3-005：新增 `backend/app/tests/test_phase3_retrieval_agent.py`，覆盖多 query 检索去重、context 生成、tool_calls 记录和 vector disabled warning。
- P3-005：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P3-005：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，76 个测试通过。
- P3-006：更新 `backend/app/core/config.py`，新增 chat base URL、API key、model、temperature 和 timeout 配置。
- P3-006：新增 `backend/app/services/agent/chat.py`，实现 `OpenAICompatibleChatAdapter`、`ChatConfig`、`ChatMessage`、`ChatResult`、disabled/request error 和 OpenAI-compatible `/v1/chat/completions` JSON 解析。
- P3-006：扩展 `backend/app/services/agent/state.py`，新增 `DraftClaim` 和 `DraftAnswer`。
- P3-006：扩展 `backend/app/services/agent/qa_agents.py`，新增 `review_answer`，支持 Chat Adapter JSON 草稿、证据型 fallback 和无 evidence 草稿。
- P3-006：新增 `backend/app/tests/test_phase3_chat_adapter.py`，覆盖配置缺失、fake transport 请求和非 JSON 响应错误。
- P3-006：新增 `backend/app/tests/test_phase3_answer_reviewer_agent.py`，覆盖 chat 输出、fallback、chat disabled 和 no evidence。
- P3-006：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P3-006：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，83 个测试通过。
- P3-007：扩展 `backend/app/services/agent/state.py`，新增 `VerificationResult`。
- P3-007：扩展 `backend/app/services/agent/qa_agents.py`，新增 `verify_draft`，检查 draft claims 的 evidence_id 是否存在且 snippet 非空，证据不足时生成一次 `second_retrieval_query`。
- P3-007：新增 `backend/app/tests/test_phase3_verifier_agent.py`，覆盖 evidence 支撑、缺 evidence 触发二次检索、第二次后不再请求第三次、无 claims 草稿拒绝。
- P3-007：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P3-007：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，87 个测试通过。
- P3-008/P3-009：后端 `.venv` 安装 `langgraph`；首次沙箱内安装因网络超时，随后通过授权联网安装成功。
- P3-008/P3-009：更新 `backend/pyproject.toml`，新增 `langgraph>=1.2.0` 依赖。
- P3-008：新增 `backend/app/services/agent/orchestrator.py`，使用 LangGraph `StateGraph(QAAgentState)` 编排 Planner、Retriever、AnswerReviewer、Verifier 和 ReportWriter。
- P3-008：Orchestrator 在 Verifier 判定 `needs_second_retrieval=True` 时回到 Retriever，使用 `second_retrieval_query` 最多补充检索一次；第二次 Verifier 后进入 ReportWriter。
- P3-008：Orchestrator 每个节点写入 `agent_traces`，记录 step、status、summary、evidence_ids、tool_calls、token_usage 和 latency。
- P3-009：扩展 `backend/app/services/agent/state.py`，新增 `QACitation`、`QAAnswer` 和 `QAAgentState`。
- P3-009：扩展 `backend/app/services/agent/qa_agents.py`，新增 `write_report`，输出 answer、citations、confidence、warnings 和 verification。
- P3-009：扩展 `backend/app/services/qa/service.py` 和 `backend/app/api/qa.py`，将 `POST /questions` 从 pending task 创建升级为同步执行 QA Orchestrator 并返回 completed/failed task。
- P3-009：新增 `backend/app/tests/test_phase3_report_writer_agent.py`，覆盖 Report Writer citations 和 unsupported confidence 降级。
- P3-008/P3-009：更新 `backend/app/tests/test_phase3_qa_api.py`，覆盖同步 QA answer/citations/traces、无 evidence 二次检索、未 ready 仓库拒绝和缺失 task 404。
- P3-008/P3-009：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P3-008/P3-009：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，90 个测试通过。
- P3-010/P3-011：更新 `frontend/types/workbench.ts`，新增 `QACreateRequest`、`QATaskResponse`、`QACitation` 和 `AgentTrace` 类型。
- P3-010/P3-011：更新 `frontend/lib/api.ts`，新增 `askRepositoryQuestion` API helper。
- P3-011：更新 `frontend/app/page.tsx`，新增 Ask Panel，支持 question、top_k、BM25/vector/graph toggles、answer、citations、confidence、warnings 和 failed state。
- P3-010：更新 `frontend/app/page.tsx`，新增 Trace Panel，展示 step order/name/status、latency、token、evidence count、input/output summary、tool_calls 和 error。
- P3-010/P3-011：`npm run build` 通过。
- P3-010/P3-011：当前线程未暴露 in-app Browser 控制工具，因此未完成浏览器截图验证；已用前端 build 和类型检查覆盖主要风险。

## 14. Phase 3 最终验证记录

- 后端：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- 后端：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，90 个测试通过，1 个 Starlette/httpx deprecation warning。
- 前端：`npm run build` 通过。
- Browser UI smoke：未完成，原因是当前线程未暴露 in-app Browser 控制工具。

## 15. Phase 4 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P4-DESIGN | Phase 4 详细设计 | 完成 | 创建 `docs/phase4-detailed-design.md`，覆盖 tool_calls 表、MCP-style Tool Layer、analyze_diff、read_file_slice、code_search、get_symbol_context、run_safe_static_check、Diff 到 symbol 映射、Review API、Review Agents、Review Panel、工具调用展示、安全边界、测试策略和验收标准 |
| P4-CLOSED-LOOP | Phase 4 闭环记录 | 完成 | 创建 `docs/phase4-closed-loop-log.md`，按 P4-001 到 P4-014 建立开发、审核、测试和评测记录表 |
| P4-001 | 实现 tool_calls 表 | 完成 | 新增 `backend/app/models/tool_call.py`，实现 `ToolCall`、`ToolCallStatus`、`ToolPermissionDecision`，并接入 Task、Repository、AgentTrace 关系 |
| P4-002 | 实现 analyze_diff 工具 | 完成 | 新增 `backend/app/services/tools/diff_analyzer.py`，解析 unified diff、git file header、hunk 行号、added/removed lines、change_type 和 binary 标记 |
| P4-003 | 实现 read_file_slice 工具 | 完成 | 新增 `backend/app/services/tools/file_reader.py`，读取仓库相对文件行范围并限制路径穿越、符号链接、敏感文件、blocked dir、二进制、行数和字符数 |
| P4-004 | 实现 code_search 工具 | 完成 | 新增 `backend/app/services/tools/code_search.py`，复用 Phase 2 `retrieve_repository`，输出 Evidence-compatible 结果、debug 计数和 vector disabled warning |
| P4-005 | 实现 get_symbol_context 工具 | 完成 | 新增 `backend/app/services/tools/symbol_context.py`，基于 `code_chunks` 和现有 NetworkX 代码图返回目标 symbol、入边、出边和 same-file 邻居 |
| P4-006 | 实现 run_safe_static_check 占位 | 完成 | 新增 `backend/app/services/tools/static_check.py`，默认 disabled；显式开启后仅校验 checker 白名单，所有分支均不执行 shell |
| P4-007 | 实现 Diff 到 symbol 映射 | 完成 | 新增 `backend/app/services/review/diff_mapper.py`，基于 diff hunk changed lines 匹配最小范围 `code_chunks`，并写入 `changed_by` 关系 |
| P4-008 | 实现 Review API | 完成 | 新增 `backend/app/schemas/review.py`、`backend/app/services/review/service.py` 和 `backend/app/api/reviews.py`；P4-009 到 P4-012 完成后升级为同步执行 Phase 4 Review 流水线并返回结构化报告 |
| P4-009 | 实现 Risk Reviewer Agent | 完成 | 新增 `backend/app/services/review/agents.py`，实现 `review_risks`、风险草稿 dataclass、chat JSON 分支和规则 fallback |
| P4-010 | 实现 Review Verifier | 完成 | 扩展 `backend/app/services/review/agents.py`，实现 `verify_review_risks`，检查 evidence/diff 支撑和 location 来源，降级或移除 unsupported risk |
| P4-011 | 实现 Test Suggestion Agent | 完成 | 扩展 `backend/app/services/review/agents.py`，实现 `suggest_review_tests`，基于 verified risks、impacted_symbols 和 changed files 生成测试建议 |
| P4-012 | 实现 Review Report Writer | 完成 | 扩展 `backend/app/services/review/agents.py`，实现 `write_review_report`，输出结构化 JSON 和 Markdown |
| P4-013 | 实现 Review Panel | 完成 | 更新 `frontend/types/workbench.ts`、`frontend/lib/api.ts` 和 `frontend/app/page.tsx`，支持 diff 输入、Review 选项、风险报告、测试建议、引用和 Markdown 展示 |
| P4-014 | 实现工具调用展示 | 完成 | 新增 Review Tool Calls Panel，并将 Trace Panel 中的 tool_calls 改为结构化展示 tool_name、status、permission_decision、latency、input/output summary 和 error |

## 16. Phase 4 验证记录

- P4-DESIGN：完成 `docs/phase4-detailed-design.md` 和 `docs/phase4-closed-loop-log.md`，文档审查通过。
- P4-001：新增 `backend/app/models/tool_call.py`，更新 `backend/app/models/task.py`、`backend/app/models/repository.py`、`backend/app/models/agent_trace.py` 和 `backend/app/models/__init__.py`。
- P4-001：保留 `AgentTrace.tool_calls` 作为 Phase 3 JSON 文本列，新增关系属性命名为 `tool_call_records`，避免 ORM 属性冲突。
- P4-001：新增 `backend/app/tests/test_phase4_models.py`，覆盖 `tool_calls` 表创建、round-trip、task/repository/trace 关系、permission/status、payload/error/latency 字段。
- P4-001：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-001：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，93 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-002：新增 `backend/app/services/tools/diff_analyzer.py` 和 `backend/app/tests/test_phase4_diff_analyzer.py`。
- P4-002：`analyze_diff` 支持标准 unified diff、`diff --git`、`---`/`+++`、hunk header、added/removed 行号、added/modified/deleted/renamed 基础识别、binary 标记、diff 字符数限制和 hunk 行数限制。
- P4-002：实现结果保持为纯解析服务，不执行 patch、不写数据库、不接 Review API；Tool Layer 记录和 API 转换留给后续 P4 任务。
- P4-002：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\tools app\\tests\\test_phase4_diff_analyzer.py` 通过。
- P4-002：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_diff_analyzer.py` 通过，6 个测试通过。
- P4-002：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-002：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，99 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-003：新增 `backend/app/services/tools/file_reader.py` 和 `backend/app/tests/test_phase4_file_reader.py`。
- P4-003：`read_file_slice` 使用仓库根目录与相对路径读取指定行范围，拒绝绝对路径、`.`/`..`、符号链接路径、仓库外路径、敏感文件、blocked dir、二进制文件、缺失文件和非法行号。
- P4-003：读取结果最多 120 行或 12000 字符，超过限制时返回截断内容并设置 `truncated=true`。
- P4-003：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\tools app\\tests\\test_phase4_file_reader.py` 通过。
- P4-003：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_file_reader.py` 通过，6 个测试通过。
- P4-003：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-003：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，105 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-004：新增 `backend/app/services/tools/code_search.py` 和 `backend/app/tests/test_phase4_code_search.py`。
- P4-004：`code_search` 复用 Phase 2 `retrieve_repository`，输出 `CodeSearchResult`、`CodeSearchEvidence` 和 `CodeSearchDebug`，Evidence 字段与 Phase 2 `EvidenceResponse` 对齐。
- P4-004：校验空 query、`top_k` 范围和至少一个检索源；默认无 embedding 配置时将 vector disabled 转为 warning，不阻断 BM25/graph。
- P4-004：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\tools app\\tests\\test_phase4_code_search.py` 通过。
- P4-004：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_code_search.py` 通过，4 个测试通过。
- P4-004：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-004：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，109 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-005：新增 `backend/app/services/tools/symbol_context.py` 和 `backend/app/tests/test_phase4_symbol_context.py`。
- P4-005：`get_symbol_context` 从 `code_chunks` 查找目标 symbol，支持可选 `file_path` disambiguation；同名 symbol 未提供 file_path 时返回 warning。
- P4-005：邻域来自现有 `load_code_graph`，返回入边、出边和 same-file 邻居，按首次出现关系去重，不创建外部虚拟 symbol。
- P4-005：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\tools app\\tests\\test_phase4_symbol_context.py` 通过。
- P4-005：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_symbol_context.py` 通过，5 个测试通过。
- P4-005：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-005：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，114 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-006：更新 `backend/app/core/config.py` 和 `.env.example`，新增 `REPOLENS_SAFE_STATIC_CHECK_ENABLED` 与 `REPOLENS_SAFE_STATIC_CHECK_ALLOWED_CHECKERS`。
- P4-006：新增 `backend/app/services/tools/static_check.py` 和 `backend/app/tests/test_phase4_static_check.py`。
- P4-006：`run_safe_static_check` 默认返回 disabled；显式开启后非白名单 checker 返回 denied，白名单 checker 返回 completed placeholder；所有分支均 `executed=false`，不执行 shell、不启动子进程、不读取文件。
- P4-006：`.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\services\\tools app\\tests\\test_phase4_static_check.py` 通过。
- P4-006：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_static_check.py` 通过，4 个测试通过。
- P4-006：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-006：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，118 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-007：更新 `backend/app/models/code_relation.py`，新增 `RelationType.CHANGED_BY = "changed_by"`；更新 `backend/app/services/graph/code_graph.py`，为 `changed_by` 设置低权重。
- P4-007：新增 `backend/app/services/review/diff_mapper.py` 和 `backend/app/tests/test_phase4_diff_mapper.py`。
- P4-007：`map_diff_to_symbols` 基于 `DiffAnalysis` changed lines 和 `code_chunks` 行号范围匹配 symbol；多层命中时选择最小范围 chunk；未命中记录 `unmatched_lines`，不伪造 symbol。
- P4-007：`write_changed_by_relations` 按 task_id 删除旧 `changed_by` metadata 后写入新关系，metadata 包含 task_id、hunk_index、line、line_type 和 change_type。
- P4-007：`.\\.venv\\Scripts\\python.exe -m ruff check app\\models\\code_relation.py app\\services\\review app\\services\\graph\\code_graph.py app\\tests\\test_phase4_diff_mapper.py` 通过。
- P4-007：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_diff_mapper.py` 通过，5 个测试通过。
- P4-007：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，123 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-007：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-008：新增 `backend/app/schemas/review.py`，定义 `ReviewCreateRequest`、`ReviewToolCallResponse` 和 `ReviewTaskResponse`。
- P4-008：新增 `backend/app/services/review/service.py`，实现 Review task 创建、repository ready 校验、Review task 查询和 response 构建。
- P4-008：新增 `backend/app/api/reviews.py` 并在 `backend/app/main.py` 注册 router，支持 `POST /api/repositories/{repository_id}/reviews` 和 `GET /api/reviews/{task_id}`。
- P4-008：初始实现只创建 `status=pending` 的 Review task 和空报告结构，不提前实现 Risk Reviewer、Verifier、Test Suggestion 或 Report Writer；P4-009 到 P4-012 完成后已在 P4 收束阶段升级为同步报告流水线。
- P4-008：`.\\.venv\\Scripts\\python.exe -m ruff check app\\api\\reviews.py app\\schemas\\review.py app\\services\\review app\\tests\\test_phase4_review_api.py app\\main.py` 通过。
- P4-008：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_review_api.py` 通过，3 个测试通过。
- P4-008：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，126 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-008：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-009：新增 `backend/app/services/review/agents.py` 和 `backend/app/tests/test_phase4_risk_reviewer_agent.py`。
- P4-009：`review_risks` 有 chat adapter 时尝试解析 JSON 风险草稿；chat disabled/request error 或无 adapter 时使用规则 fallback。
- P4-009：fallback 基于 diff mapping 和 evidence 生成 conservative risk；每条风险草稿带 `diff_refs` 或 evidence_ids，并输出 impacted_symbols。
- P4-009：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\review app\\tests\\test_phase4_risk_reviewer_agent.py` 通过。
- P4-009：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_risk_reviewer_agent.py` 通过，4 个测试通过。
- P4-009：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-009：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，130 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-010：扩展 `backend/app/services/review/agents.py`，新增 `ReviewVerifierResult` 和 `verify_review_risks`。
- P4-010：Verifier 只过滤或降级风险草稿，不新增事实；风险必须具备有效 evidence_id 或 diff_refs，location 必须来自 diff/evidence/diff_refs。
- P4-010：新增 `backend/app/tests/test_phase4_review_verifier_agent.py`，覆盖有效 evidence、diff-only high 降级、unsupported risk 移除和 location 来源校验。
- P4-010：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\review app\\tests\\test_phase4_review_verifier_agent.py` 通过。
- P4-010：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_review_verifier_agent.py` 通过，4 个测试通过。
- P4-010：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-010：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，134 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-011：扩展 `backend/app/services/review/agents.py`，新增 `SuggestedReviewTest`、`TestSuggestionResult` 和 `suggest_review_tests`。
- P4-011：Test Suggestion Agent 不运行测试，只输出 target、reason、test_type、related_risk_titles 和 file_path；按 target/test_type 去重。
- P4-011：新增 `backend/app/tests/test_phase4_test_suggestion_agent.py`，覆盖 unit/integration 分类、重复风险合并和空输入/限制处理。
- P4-011：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\review app\\tests\\test_phase4_test_suggestion_agent.py` 通过。
- P4-011：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_test_suggestion_agent.py` 通过，4 个测试通过。
- P4-011：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-011：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，138 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-012：扩展 `backend/app/services/review/agents.py`，新增 `ReviewReport` 和 `write_review_report`。
- P4-012：Report Writer 只消费 verified risks 和 suggested_tests，输出 summary、risk_level、risks、impacted_symbols、suggested_tests、citations、markdown 和 warnings。
- P4-012：结构化 risks 不包含 `diff_refs`；citations 只包含风险实际引用的 evidence；Markdown 固定包含 Summary、Risk Level、Risks、Suggested Tests 和 Citations。
- P4-012：新增 `backend/app/tests/test_phase4_review_report_writer.py`，覆盖结构化 JSON、Markdown、空报告和 citation 过滤。
- P4-012：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\review app\\tests\\test_phase4_review_report_writer.py` 通过。
- P4-012：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_review_report_writer.py` 通过，3 个测试通过。
- P4-012：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4-012：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，141 个测试通过，1 个 Starlette/httpx deprecation warning。
- P4-008 收束：`ReviewService.run_review_task` 将 Phase 4 已实现能力串成同步 Review 流水线：analyze_diff、Diff 到 symbol 映射、code_search、最多 3 个 get_symbol_context、可选 run_safe_static_check、Risk Reviewer、Review Verifier、Test Suggestion Agent 和 Review Report Writer。
- P4-008 收束：Review API 仍不引入后台队列、完整 MCP Server、真实命令执行或 Phase 5 评测调度；tool_calls/traces 在同步流水线中写入。
- P4-008 收束：更新 `backend/app/tests/test_phase4_review_api.py`，覆盖 completed Review report、risks、markdown、tool_calls 和 traces。
- P4-013：更新 `frontend/types/workbench.ts`，新增 Review request/response/risk/test/citation/tool call 类型。
- P4-013：更新 `frontend/lib/api.ts`，新增 `createReview` 和 `getReview` helper。
- P4-013：更新 `frontend/app/page.tsx`，新增 Review Panel，支持粘贴 diff、top_k、BM25/vector/graph/static check toggles、summary、risk_level、risks、suggested_tests、citations 和 markdown 展示。
- P4-014：新增 Tool Calls Panel，并将 Trace Panel 的 tool_calls 从原始 JSON 改为结构化行展示。
- P4-013/P4-014：`npm run build` 通过。
- P4 最终验证：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P4 最终验证：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，141 个测试通过，1 个 Starlette/httpx deprecation warning。

## 17. Phase 4 最终验收记录

| 验收项 | 状态 | 备注 |
| --- | --- | --- |
| PR Diff 可解析并映射到 symbol | 完成 | analyze_diff、diff mapper、changed_by relation 已测试 |
| Review API 可创建并查询报告 | 完成 | POST 同步返回 completed/failed Review response，GET 可查询 |
| Review Agents 可输出风险、验证、测试建议和报告 | 完成 | P4-009 至 P4-012 单元测试覆盖 |
| 工具调用可记录和展示 | 完成 | `tool_calls` 表、Review response、Trace summary、前端 Tool Calls Panel 均完成 |
| run_safe_static_check 安全边界 | 完成 | 默认 disabled，所有分支 no execution |
| 前端 Review Panel | 完成 | Next.js build 和 TypeScript 校验通过 |
| 后端质量门禁 | 完成 | Ruff 通过，141 tests passed |

## 18. Phase 5 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P5-DESIGN | Phase 5 详细设计 | 完成 | 创建 `docs/phase5-detailed-design.md`，覆盖评测数据格式、50 条样例、vector_only、bm25_vector、bm25_vector_graph、Hit@5、MRR、引用覆盖率、延迟、token、Evaluation Panel、Docker Compose、README、演示仓库、演示问题、演示截图、安全边界、测试策略和验收标准 |
| P5-CLOSED-LOOP | Phase 5 闭环记录 | 完成 | 创建 `docs/phase5-closed-loop-log.md`，按 P5-001 到 P5-012 建立开发、审核、测试和评测记录表 |
| P5-001 | 设计评测数据格式 | 完成 | 新增 `backend/app/services/evaluation/dataset.py`，实现 EvaluationSampleType、EvaluationSample、EvaluationDataset、JSONL loader、schema 校验、重复 ID 校验、review_diff 必填和路径安全校验 |
| P5-002 | 准备 50 条评测样例 | 完成 | 新增 `evals/datasets/p0_plus_eval.jsonl`，包含 20 条定位、10 条解释、10 条架构、10 条 Review 样例，并新增 fixture 测试校验分布和 review diff |
| P5-003 | 实现 vector_only 评测 | 完成 | 新增 `backend/app/services/evaluation/runner.py`，实现 vector_only sample runner、结果结构、evidence refs、latency 和 vector disabled 记录 |
| P5-004 | 实现 bm25_vector 评测 | 完成 | 扩展 `backend/app/services/evaluation/runner.py`，实现 bm25_vector sample runner、BM25/vector 计数、evidence refs、latency 和 vector disabled 记录 |
| P5-005 | 实现 bm25_vector_graph 评测 | 完成 | 扩展 `backend/app/services/evaluation/runner.py`，实现 bm25_vector_graph sample runner、BM25/vector/graph 计数、evidence refs、latency 和 vector disabled 记录 |
| P5-006 | 实现指标计算 | 完成 | 新增 `backend/app/services/evaluation/metrics.py`，实现单样例指标和策略聚合指标，覆盖 Hit@5、MRR、引用覆盖率、延迟、token 估算和 error_count |
| P5-007 | 实现 Evaluation Panel | 完成 | 新增同步 Evaluation API、evaluation_runs/evaluation_results 表和前端 Evaluation Panel，展示策略对比表、样例结果表与 vector disabled warning |
| P5-008 | 完善 Docker Compose | 完成 | 完善 `docker-compose.yml`、`.env.example`、后端/前端 Dockerfile 和 `.dockerignore`，覆盖 frontend、backend、qdrant、volume 与环境变量 |
| P5-009 | 完善 README | 完成 | README 覆盖项目定位、架构图、启动、环境变量、API、评测方法、截图目标、指标表、简历 bullet 和面试讲法 |
| P5-010 | 准备演示仓库 | 完成 | 新增 `evals/demo_repos/python_service` 和 `evals/demo_repos/ts_webapp`，覆盖 50 条评测数据集引用的 demo files/symbols |
| P5-011 | 准备演示问题 | 完成 | 新增 `evals/demo_questions.md` 和 `evals/datasets/demo_questions.json`，覆盖架构、定位、解释、影响范围、Review |
| P5-012 | 录制或整理演示截图 | 完成 | 新增 `docs/assets/screenshots/` 下 6 张 Workbench 演示截图；README 写入真实 demo run 指标和截图路径；前端工作台阶段标识更新为 Phase 5 并修正长内容溢出 |

## 19. Phase 5 验证记录

- P5-DESIGN：完成 `docs/phase5-detailed-design.md`，文档审查通过，范围严格限定在 P0+ Phase 5。
- P5-CLOSED-LOOP：完成 `docs/phase5-closed-loop-log.md`，按 P5-001 到 P5-012 建立开发、审核、测试和评测记录。
- 自动化：创建 `repolens-phase-5`，每 10 分钟 heartbeat 继续推进 Phase 5。
- P5-001：新增 `backend/app/services/evaluation/dataset.py` 和更新 `backend/app/services/evaluation/__init__.py`，定义评测样例类型、dataclass、JSONL loader 与校验。
- P5-001：loader 校验 id/type/repository_key/question/expected_files，支持 expected_symbols、expected_answer_keywords、review_diff、tags、notes；review 类型必须有 review_diff。
- P5-001：路径安全校验拒绝绝对路径、Windows drive 前缀、`..`、空路径和非字符串列表；不创建 50 条样例，不接 Runner/API。
- P5-001：新增 `backend/app/tests/test_phase5_dataset.py`，覆盖正常 JSONL、字符串/路径规范化、review_diff 必填、重复 ID、非法 type、空 expected_files、非列表字段、路径穿越、绝对路径、非法 JSON、空数据集、缺失文件和目录输入。
- P5-001：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation app\\tests\\test_phase5_dataset.py` 通过。
- P5-001：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_dataset.py` 通过，14 个测试通过。
- P5-001：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-001：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，155 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-002：新增 `evals/datasets/p0_plus_eval.jsonl`，共 50 条样例，覆盖 `python_demo` 和 `ts_demo` 两个演示仓库 key。
- P5-002：样例分布为 20 条 `location`、10 条 `explanation`、10 条 `architecture`、10 条 `review`；每条包含 `expected_files`，大多数包含 `expected_symbols` 和 `expected_answer_keywords`。
- P5-002：10 条 Review 样例均包含合法 unified diff，覆盖 token 过期边界、折扣校验、retry cap、audit 写入、敏感文件过滤、前端错误处理、loading 状态、空 diff、localStorage fallback 和 score 展示。
- P5-002：新增 `backend/app/tests/test_phase5_dataset_fixture.py`，验证数据集总数、类型分布、repository_key 覆盖、expected_symbols 数量、review diff 格式和 ID 分组唯一性。
- P5-002：`.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase5_dataset_fixture.py` 通过。
- P5-002：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_dataset.py app\\tests\\test_phase5_dataset_fixture.py` 通过，18 个测试通过。
- P5-002：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-002：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，159 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-003：新增 `backend/app/services/evaluation/runner.py`，定义 `VECTOR_ONLY_STRATEGY`、`EvaluationEvidenceRef`、`VectorOnlyEvaluationResult` 和 `run_vector_only_sample`。
- P5-003：`run_vector_only_sample` 固定调用 `retrieve_repository(..., use_bm25=False, use_vector=True, use_graph=False)`，只实现 vector_only，不提前实现 bm25_vector、bm25_vector_graph、Hit@5/MRR 或 Evaluation API。
- P5-003：无 embedding 配置时保留 `vector_disabled_reason`，`vector_unavailable=true`，不使用 BM25 fallback 冒充 vector_only。
- P5-003：Review 样例 query 会拼接 question、expected_files 和 expected_symbols，便于后续 Review 评测检索；正式 Review metrics 留给 P5-006。
- P5-003：新增 `backend/app/tests/test_phase5_vector_only_runner.py`，覆盖 vector disabled、vector_only 参数、Review query 和检索异常失败结果。
- P5-003：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation app\\tests\\test_phase5_vector_only_runner.py` 通过。
- P5-003：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_vector_only_runner.py` 通过，4 个测试通过。
- P5-003：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-003：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，163 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-004：扩展 `backend/app/services/evaluation/runner.py`，定义 `BM25_VECTOR_STRATEGY`、`BM25_VECTOR_TOP_K`、`BM25VectorEvaluationResult` 和 `run_bm25_vector_sample`。
- P5-004：`run_bm25_vector_sample` 固定调用 `retrieve_repository(..., use_bm25=True, use_vector=True, use_graph=False)`，只实现 bm25_vector，不提前实现 bm25_vector_graph、Hit@5/MRR 或 Evaluation API。
- P5-004：无 embedding 配置时保留 `vector_disabled_reason`，但仍可返回 BM25 evidence；结果显式记录 `bm25_count`、`vector_count`、`evidence_count` 和 `latency_ms`。
- P5-004：Review 样例沿用 P5-003 的 query 增强；正式 Review metrics 留给 P5-006。
- P5-004：新增 `backend/app/tests/test_phase5_bm25_vector_runner.py`，覆盖 vector disabled 下 BM25 证据保留、bm25_vector 参数、Review query 和检索异常失败结果。
- P5-004：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation app\\tests\\test_phase5_bm25_vector_runner.py` 通过。
- P5-004：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_bm25_vector_runner.py` 通过，4 个测试通过。
- P5-004：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-004：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，167 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-005：扩展 `backend/app/services/evaluation/runner.py`，定义 `BM25_VECTOR_GRAPH_STRATEGY`、`BM25_VECTOR_GRAPH_TOP_K`、`BM25VectorGraphEvaluationResult` 和 `run_bm25_vector_graph_sample`。
- P5-005：`run_bm25_vector_graph_sample` 固定调用 `retrieve_repository(..., use_bm25=True, use_vector=True, use_graph=True)`，只实现 bm25_vector_graph，不提前实现 Hit@5/MRR 或 Evaluation API。
- P5-005：无 embedding 配置时保留 `vector_disabled_reason`，同时可通过 BM25 seed 执行 graph expansion；结果显式记录 `bm25_count`、`vector_count`、`graph_count`、`evidence_count` 和 `latency_ms`。
- P5-005：新增 `backend/app/tests/test_phase5_bm25_vector_graph_runner.py`，覆盖 vector disabled 下图扩展证据、bm25_vector_graph 参数、Review query 和检索异常失败结果。
- P5-005：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation app\\tests\\test_phase5_bm25_vector_graph_runner.py` 通过。
- P5-005：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_bm25_vector_graph_runner.py` 通过，4 个测试通过。
- P5-005：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-005：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，171 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-006：新增 `backend/app/services/evaluation/metrics.py`，定义 `EvaluationSampleMetric`、`EvaluationAggregateMetrics`、`compute_sample_metrics`、`compute_aggregate_metrics` 和 `estimate_token_count`。
- P5-006：单样例指标计算 Hit@5、MRR、引用覆盖率、matched_files、matched_symbols、latency、真实/估算 token 和 error_message；失败样例指标归零并计入 error。
- P5-006：聚合指标计算 hit_at_5、mrr、citation_coverage、avg/p50/p95 latency、avg_token_count、token_estimated_count 和 error_count；拒绝空列表和混合策略聚合。
- P5-006：新增 `backend/app/tests/test_phase5_metrics.py`，覆盖 Hit@5/MRR/coverage、expected_symbols 要求、Review additional citations、失败结果、top5 限制、聚合指标和 token 估算。
- P5-006：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation app\\tests\\test_phase5_metrics.py` 通过。
- P5-006：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_metrics.py` 通过，8 个测试通过。
- P5-006：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-006：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，179 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-007：新增 `backend/app/models/evaluation.py`，实现 `evaluation_runs` 和 `evaluation_results` 轻量持久化表，只保存指标、匹配文件、引用摘要和错误信息。
- P5-007：新增 `backend/app/schemas/evaluation.py`、`backend/app/services/evaluation/service.py` 和 `backend/app/api/evaluations.py`，支持 `POST /api/evaluations`、`GET /api/evaluations` 和 `GET /api/evaluations/{run_id}`。
- P5-007：Evaluation API 同步读取 dataset、校验 repository_map、执行 vector_only/bm25_vector/bm25_vector_graph 或 all、计算并聚合 metrics；单样例失败计入 error_count，不引入队列或后台调度。
- P5-007：更新 `frontend/types/workbench.ts`、`frontend/lib/api.ts` 和 `frontend/app/page.tsx`，新增 Evaluation Panel，支持 dataset path、strategy、repository_key、top_k、Run、策略对比表、样例结果表和 warnings 展示。
- P5-007：新增 `backend/app/tests/test_phase5_evaluation_api.py`，覆盖 all/single strategy、持久化查询、缺失 repository_map、repository 未 ready 和缺失 run 404。
- P5-007：`.\\.venv\\Scripts\\python.exe -m ruff check app\\api\\evaluations.py app\\models\\evaluation.py app\\schemas\\evaluation.py app\\services\\evaluation app\\tests\\test_phase5_evaluation_api.py` 通过。
- P5-007：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_evaluation_api.py` 通过，5 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-007：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-007：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，184 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-007：`npm run build` 通过。
- P5-008：更新 `docker-compose.yml`，保持 backend、frontend、qdrant 三服务，`repolens_data` 挂载 `/app/.repolens`，`qdrant_data` 挂载 `/qdrant/storage`。
- P5-008：更新 `.env.example`，补齐本地默认 `REPOLENS_DATABASE_URL`、`REPOLENS_WORKSPACE_ROOT`、`REPOLENS_QDRANT_URL`、`REPOLENS_EMBEDDING_*`、`REPOLENS_CHAT_*`、`REPOLENS_SAFE_STATIC_CHECK_*` 和 `NEXT_PUBLIC_API_BASE_URL`。
- P5-008：更新 `backend/Dockerfile`、`frontend/Dockerfile`、`backend/.dockerignore` 和 `frontend/.dockerignore`，前端容器改为生产 build/start，后端构建上下文排除测试缓存和本地数据。
- P5-008：`docker compose config` 通过。
- P5-008：`docker compose up -d --build` 已尝试但未完成，原因是当前环境无法连接 Docker Desktop Linux daemon：`dockerDesktopLinuxEngine` pipe 不存在。
- P5-008：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-008：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，184 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-008：`npm run build` 通过。
- P5-009：更新 `README.md`，从 Phase 0 骨架说明升级为 P0+ 完整版。
- P5-009：README 新增项目定位、简历亮点、Mermaid 架构图、技术栈、Phase 1-5 功能清单、本地启动、Docker Compose 启动、环境变量表和核心 API 表。
- P5-009：README 新增评测数据分布、三种策略、Hit@5、MRR、引用覆盖率、延迟、token、error_count 指标说明和 pending 指标表。
- P5-009：README 新增截图目标、安全边界、P0+ non-goals、Demo 计划、简历 bullet 和面试讲法。
- P5-009：未提前创建 P5-010 演示仓库、P5-011 演示问题或 P5-012 截图；未伪造真实评测分数，相关内容标记为 pending。
- P5-009：README 范围自查通过，确认已移除 Phase 0 旧说明并保留 pending 标记。
- P5-009：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-009：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，184 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-009：`npm run build` 通过。
- P5-009：`docker compose config` 通过。
- P5-010：新增 `evals/demo_repos/python_service`，包含 22 个文件，覆盖 API routes、service、repository、auth、billing、scanner、chunking、audit、retry、scheduler 和测试。
- P5-010：新增 `evals/demo_repos/ts_webapp`，包含 21 个文件，覆盖 Next.js-style dashboard、components、hooks、API clients、persistence、routes、workspace helper 和测试。
- P5-010：更新 `evals/README.md`，说明 Phase 5 dataset 与 demo repo 位置。
- P5-010：更新 `README.md` Demo Plan，将 P5-010 标记为 ready，P5-011/P5-012 继续 pending。
- P5-010：新增 `backend/app/tests/test_phase5_demo_repos.py`，验证 demo repo 目录、文件数、安全性、关键层文件和 50 条数据集 expected files 覆盖。
- P5-010：未提前创建演示问题、未截图、未伪造正式评测分数。
- P5-010：`.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase5_demo_repos.py` 通过。
- P5-010：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_demo_repos.py app\\tests\\test_phase5_dataset_fixture.py` 通过，8 个测试通过。
- P5-010：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-010：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，188 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-010：`npm run build` 通过。
- P5-010：`docker compose config` 通过。
- P5-011：新增 `evals/demo_questions.md`，包含 demo flow、10 条演示问题、2 条 Review diff 和 screenshot mapping。
- P5-011：新增 `evals/datasets/demo_questions.json`，每条包含 id、category、repository_key、repository_path、question、expected_answer_focus、suggested_demo_flow、screenshot_target、expected_files、expected_symbols 和 review_diff。
- P5-011：演示问题覆盖 architecture、location、explanation、impact、review 五类；覆盖 `python_demo` 和 `ts_demo`；4 条 impact/review 问题包含 unified diff。
- P5-011：更新 `README.md` Demo Plan，将 P5-011 标记为 ready；更新 `evals/README.md`，说明 demo questions 位置。
- P5-011：新增 `backend/app/tests/test_phase5_demo_questions.py`，验证问题字段、类别分布、repo 覆盖、文件引用、diff 格式和 Markdown/JSON 对齐。
- P5-011：未提前录制截图、未填写真正评测分数、未新增超出 P0+ 的演示流程。
- P5-011：`.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase5_demo_questions.py` 通过。
- P5-011：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_demo_questions.py app\\tests\\test_phase5_demo_repos.py` 通过，8 个测试通过。
- P5-011：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-011：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，192 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-011：`npm run build` 通过。
- P5-011：`docker compose config` 通过。
- P5-012：启动本地 backend/frontend，导入 `python_demo` 与 `ts_demo` 两个演示仓库；`ts_demo` ready，21 files、37 chunks、52 relations；`python_demo` ready，22 files、68 chunks、208 relations。
- P5-012：Workbench `all` strategy Evaluation demo run 通过，50 samples x 3 strategies；指标为 `vector_only` Hit@5 0%、MRR 0.000、coverage 0%；`bm25_vector` Hit@5 92%、MRR 0.787、coverage 85.2%；`bm25_vector_graph` Hit@5 90%、MRR 0.892、coverage 84.5%。
- P5-012：Workbench Ask/Review/Evidence demo 状态生成通过；Ask 展示 citations，Review 展示 medium risk、suggested tests、review citations，Tool Calls 展示 `analyze_diff`、`code_search`、`get_symbol_context`，Evidence 展示 BM25 + graph expansion debug counts。
- P5-012：新增截图 `docs/assets/screenshots/repository-status.png`、`evaluation-panel.png`、`ask-trace-panel.png`、`review-panel.png`、`tool-calls-panel.png`、`evidence-panel.png`，并完成视觉抽查。
- P5-012：修正 `frontend/app/page.tsx` 的 Phase 标识、demo 默认输入、长表格/长报告/代码块横向溢出；不新增 P0+ 外功能。
- P5-012：修正 `backend/app/services/evaluation/service.py` dataset path 解析，支持从 repo root 解析 `evals/datasets/p0_plus_eval.jsonl`；新增专项测试。
- P5-012：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation\\service.py app\\tests\\test_phase5_evaluation_api.py` 通过。
- P5-012：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_evaluation_api.py` 通过，6 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-012：最终全量 `.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P5-012：最终全量 `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，193 个测试通过，1 个 Starlette/httpx deprecation warning。
- P5-012：最终 `npm run build` 通过。
- P5-012：最终 `docker compose config` 通过。

## 20. Phase 6 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P6-DESIGN | Phase 6 详细设计 | 完成 | 创建 `docs/phase6-detailed-design.md`，覆盖多平台 Change Request Provider、GitHub 首个适配器、Gitee/GitLab/self-hosted GitLab 预留、API、数据模型、前端、安全、测试、评测和验收标准 |
| P6-CLOSED-LOOP | Phase 6 闭环记录 | 完成 | 创建 `docs/phase6-closed-loop-log.md`，按 P6-001 到 P6-012 建立开发、审核、测试和评测记录表 |
| P6-001 | 编写 Phase 6 详细设计 | 完成 | 已完成 Phase 6 详细设计和文档审查；尚未进入代码实现 |
| P6-002 | 新增多平台配置项 | 完成 | 更新 `backend/app/core/config.py` 和 `.env.example`，新增 `REPOLENS_CHANGE_REQUEST_*`、GitHub/Gitee/GitLab token 和 base URL 配置；新增 `test_phase6_config.py` |
| P6-003 | 实现 PR/MR URL parser | 完成 | 新增 `backend/app/services/change_request` 模块和 `test_phase6_change_request_parser.py`，支持 GitHub PR、Gitee PR、GitLab.com MR 和 self-hosted GitLab MR URL 解析 |
| P6-004 | 实现首个 Change Request client | 完成 | 实现 GitHub PR 只读 client、HTTP transport、错误映射和 fake transport 测试；Gitee/GitLab fetch 保持 not implemented |
| P6-005 | 新增 change_requests 数据模型 | 完成 | 新增 `backend/app/models/change_request.py`，注册 `ChangeRequest`、`ChangeRequestPlatform`、`ChangeRequestType`，保存脱敏外部变更 metadata 并关联 repository/review task |
| P6-006 | 新增 PR/MR Review API | 完成 | 新增 `backend/app/api/change_requests.py`、`backend/app/schemas/change_request.py`，支持 `POST /api/repositories/{repository_id}/change-requests/reviews`、GET by id 和 GET by task |
| P6-007 | 接入现有 Review pipeline | 完成 | 新增 `ChangeRequestReviewService`，provider fetch 后保存 `change_requests` 并复用现有 `ReviewService` 创建/运行 review task |
| P6-008 | 前端新增 PR/MR Review flow | 完成 | 更新 `frontend/types/workbench.ts`、`frontend/lib/api.ts` 和 `frontend/app/page.tsx`，新增 `Diff`/`PR/MR URL` 模式、平台无关 URL 输入、metadata 展示和报告复用 |
| P6-009 | 错误处理与安全边界 | 完成 | 补齐 service 层 diff limit guard、API 错误 detail 脱敏、前端错误归一化，并覆盖 token 脱敏、auth、rate limit、diff too large、fetch failure |
| P6-010 | 准备真实演示 PR/MR | 完成 | 新增 `evals/change_requests/phase6_demo_prs.json` 和 README，准备离线 synthetic GitHub PR fixture、unsupported provider URL 和 API smoke 测试 |
| P6-011 | 测试与评测 | 完成 | 新增 P6-011 smoke 评测断言和 `docs/phase6-smoke-evaluation.md`；全量 ruff/pytest、前端 build/type check、Docker config 和 UI DOM smoke 通过，截图命令受当前 Browser CDP 超时阻断 |
| P6-012 | 更新文档和演示材料 | 完成 | 更新 README、evals 文档、worklog、闭环记录和 `docs/phase6-final-closure-review.md`；截图 artifact 因 Browser CDP timeout 仍为环境阻断，已如实记录 |

## 21. Phase 6 验证记录

- P6-DESIGN：完成 `docs/phase6-detailed-design.md`，文档审查通过，范围限定为多代码平台 PR/MR 只读集成，不进入 Phase 7 MCP Server、Phase 8 真正多 Agent、Phase 9 benchmark 或 Phase 10 包装。
- P6-CLOSED-LOOP：完成 `docs/phase6-closed-loop-log.md`，按 P6-DESIGN、P6-CLOSED-LOOP 和 P6-001 到 P6-012 建立开发、审核、测试和评测记录。
- 自动化：更新 heartbeat 自动化 `repolens-phase-6`，每 10 分钟继续推进当前线程；prompt 已从 GitHub-only 调整为多平台 PR/MR Change Request Provider 方向。
- P6-001：设计明确 Phase 6 初始要求用户选择已索引 repository，再输入 PR/MR URL；外部平台 diff 转换为现有 `ReviewCreateRequest`，复用 `ReviewService`。
- P6-001：设计明确 GitHub PR 是首个落地适配器，Gitee Pull Request、GitLab Merge Request 和 self-hosted GitLab 必须有 parser/provider 契约或 unsupported/not implemented 错误。
- P6-001：本轮仅新增文档和更新 worklog，未修改业务代码，未提前实现 P6-002 到 P6-012。
- P6-002：扩展 `Settings`，新增 `change_request_timeout_seconds`、`change_request_max_diff_chars`、`github_token`、`github_base_url`、`gitee_token`、`gitee_base_url`、`gitlab_token` 和 `gitlab_base_url`。
- P6-002：更新 `.env.example`，补充多平台 PR/MR 配置项；token 默认留空，base URL 使用公开平台默认值。
- P6-002：新增 `backend/app/tests/test_phase6_config.py`，覆盖默认值和显式覆盖；未提前实现 URL parser、provider client、API 或数据模型。
- P6-002：`.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\tests\\test_phase6_config.py` 通过。
- P6-002：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py` 通过，2 个测试通过。
- P6-003：新增 `backend/app/services/change_request/models.py`，定义平台、change type 和 `ChangeRequestRef`。
- P6-003：新增 `backend/app/services/change_request/providers.py`，实现 `GitHubChangeRequestProvider`、`GiteeChangeRequestProvider`、`GitLabChangeRequestProvider`、`choose_change_request_provider` 和 `parse_change_request_url`。
- P6-003：parser 支持 `https://github.com/{owner}/{repo}/pull/{number}`、`https://gitee.com/{owner}/{repo}/pulls/{number}`、`https://gitlab.com/{namespace}/{repo}/-/merge_requests/{number}` 和 self-hosted GitLab MR；query/fragment 会被 canonicalize 掉。
- P6-003：新增 `backend/app/tests/test_phase6_change_request_parser.py`，覆盖成功解析、invalid URL、unsupported provider 和 provider 选择；未提前实现平台 API client、数据库模型、Review API 或前端。
- P6-003：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\change_request app\\tests\\test_phase6_change_request_parser.py` 通过。
- P6-003：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_change_request_parser.py` 通过，12 个测试通过。
- P6-002/P6-003 合并专项：`.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\services\\change_request app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py` 通过。
- P6-002/P6-003 合并专项：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py` 通过，14 个测试通过。
- P6-004：扩展 `backend/app/services/change_request/models.py`，新增 `ChangeRequest`、`ChangeRequestFile` 和 `ChangeRequestCommit`。
- P6-004：扩展 `backend/app/services/change_request/providers.py`，新增可注入 `HTTPTransport`、`HTTPResponse`、GitHub `fetch`、JSON/text request helper 和 auth/not found/rate limit/diff too large 错误映射。
- P6-004：GitHub client 读取 PR metadata、files、commits 和 diff，组装统一 `ChangeRequest`；`metadata` 只保存脱敏计数字段，不保存 token。
- P6-004：Gitee/GitLab provider 保持 URL parser 可用，但 `fetch` 继承默认 not implemented，避免一次性扩成多平台 API client。
- P6-004：新增 `backend/app/tests/test_phase6_github_provider.py`，使用 fake transport 覆盖成功拉取、无 token public request、404、auth、rate limit、diff too large 和非 GitHub provider not implemented。
- P6-004：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\change_request app\\tests\\test_phase6_github_provider.py` 通过。
- P6-004：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_github_provider.py` 通过，5 个测试通过。
- P6-002/P6-004 合并专项：`.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\services\\change_request app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py` 通过。
- P6-002/P6-004 合并专项：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py` 通过，19 个测试通过。
- P6-005：新增 `backend/app/models/change_request.py`，实现 `change_requests` 表、平台/type enum、repository/task 外键、统计字段、created/updated 时间和索引。
- P6-005：更新 `Repository.change_requests` 与 `Task.change_requests` relationship；只新增新表，不修改既有表字段，降低无 Alembic 场景下的迁移风险。
- P6-005：数据库列名保留 `metadata`，ORM 属性命名为 `metadata_payload`，避免踩 SQLAlchemy Declarative 的 `metadata` 保留属性。
- P6-005：新增 `backend/app/tests/test_phase6_change_request_models.py`，覆盖表创建、索引、repository/task round-trip、metadata 脱敏 JSON 和 repository 删除级联。
- P6-005：`.\\.venv\\Scripts\\python.exe -m ruff check app\\models\\change_request.py app\\models\\repository.py app\\models\\task.py app\\models\\__init__.py app\\tests\\test_phase6_change_request_models.py` 通过。
- P6-005：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_change_request_models.py` 通过，3 个测试通过。
- P6-006：新增 `backend/app/schemas/change_request.py`，定义 `ChangeRequestReviewCreateRequest`、`ChangeRequestMetadataResponse` 和 `ChangeRequestReviewResponse`；response 只返回脱敏展示字段，不返回 raw metadata。
- P6-006：新增 `backend/app/api/change_requests.py` 并挂载到 `backend/app/main.py`，支持创建 PR/MR Review、按 change_request_id 查询、按 task_id 查询。
- P6-006：API 错误映射覆盖 repository missing/not ready、invalid URL、unsupported provider、provider not implemented、auth、not found、rate limit、diff too large、fetch failure 和 Review validation。
- P6-007：新增 `backend/app/services/change_request/service.py`，`ChangeRequestReviewService` 负责选择 provider、fetch 统一 ChangeRequest、写入 `change_requests`、构造 `ReviewCreateRequest`。
- P6-007：`ChangeRequestReviewService` 调用现有 `ReviewService.create_review_task`、`ReviewService.run_review_task` 和 `ReviewService.build_task_response`；不复制 `analyze_diff`、`code_search`、`get_symbol_context`、risk/verifier/report writer 流水线。
- P6-007：新增 `backend/app/tests/test_phase6_change_request_api.py`，使用 fake provider 覆盖成功 PR/MR URL review、repository not ready、unsupported provider、invalid URL、Gitee not implemented、GET missing 和 token/Authorization 脱敏。
- P6-006/P6-007：`.\\.venv\\Scripts\\python.exe -m ruff check app\\api\\change_requests.py app\\schemas\\change_request.py app\\services\\change_request app\\models\\change_request.py app\\models\\repository.py app\\models\\task.py app\\models\\__init__.py app\\main.py app\\tests\\test_phase6_change_request_api.py app\\tests\\test_phase6_change_request_models.py` 通过。
- P6-006/P6-007：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py` 通过，6 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-002/P6-007 合并专项：`.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\api\\change_requests.py app\\schemas\\change_request.py app\\services\\change_request app\\models\\change_request.py app\\models\\repository.py app\\models\\task.py app\\models\\__init__.py app\\main.py app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py` 通过。
- P6-002/P6-007 合并专项：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py` 通过，25 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-008：扩展 `frontend/types/workbench.ts`，新增 `ChangeRequestReviewCreateRequest`、`ChangeRequestMetadata` 和 `ChangeRequestReviewResponse`。
- P6-008：扩展 `frontend/lib/api.ts`，新增 `createChangeRequestReview(repositoryId, payload)`，调用 `/api/repositories/{repository_id}/change-requests/reviews`。
- P6-008：更新 Workbench Review 面板，保留 `Diff` 粘贴模式，新增 `PR/MR URL` 模式、`Run PR/MR Review` 操作、平台/source/target branch/changed files/additions/deletions/commits metadata 展示。
- P6-008：Review 报告、risks、suggested tests、citations、tool_calls 和 traces 继续复用现有渲染；前端文案保持 PR/MR 和平台无关，不写成 GitHub-only。
- P6-008：`npm run build` 通过。
- P6-008：`npm exec tsc -- --noEmit` 第一次在 `.next/types` 尚未生成时失败；执行 build 后复跑通过。
- P6-008：in-app Browser 冒烟未完成，原因是当前工具会话中 `next dev` 前台可 Ready，但后台 dev server 不能稳定保持监听 3000；P6-011 需补浏览器截图/视觉验证。
- P6-009：更新 `backend/app/services/change_request/service.py`，在 provider fetch 后统一执行 `REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS` guard，防止 provider 绕过 diff limit。
- P6-009：更新 `backend/app/api/change_requests.py`，通过 Settings token 与 Bearer/Authorization 模式统一脱敏所有 PR/MR API 错误 detail；413 状态使用新 `HTTP_413_CONTENT_TOO_LARGE` 常量。
- P6-009：更新 `frontend/lib/api.ts`，把 FastAPI validation error 数组归一化为可读错误文本，并对 Bearer/Authorization 文本做前端二次脱敏。
- P6-009：扩展 `backend/app/tests/test_phase6_change_request_api.py`，覆盖 service diff limit、provider error token 脱敏、auth=400、rate limit=429、diff too large=413、fetch failure=502，并确认失败 fetch 不创建 `change_requests` 或 review task。
- P6-009：`.\\.venv\\Scripts\\python.exe -m ruff check app\\api\\change_requests.py app\\services\\change_request\\service.py app\\tests\\test_phase6_change_request_api.py` 通过。
- P6-009：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_change_request_api.py` 通过，6 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-009：`npm run build` 通过。
- P6-009：`npm exec tsc -- --noEmit` 与 build 并行时曾因 `.next/types` 生成竞态失败；build 完成后顺序复跑通过。
- P6-002/P6-009 合并专项：`.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\api\\change_requests.py app\\schemas\\change_request.py app\\services\\change_request app\\models\\change_request.py app\\models\\repository.py app\\models\\task.py app\\models\\__init__.py app\\main.py app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py` 通过。
- P6-002/P6-009 合并专项：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py` 通过，28 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-010：新增 `evals/change_requests/phase6_demo_prs.json`，准备 `phase6-cr-001` synthetic GitHub-style PR fixture，URL 为 `https://github.com/repolens-demo/ts_webapp/pull/42`，绑定 `evals/demo_repos/ts_webapp`。
- P6-010：fixture diff 只修改 `src/components/review-panel.tsx` 的 empty diff guard，体积小、引用真实 demo 文件、无 token/Authorization，适合离线演示 metadata、review output、tool_calls 和 traces。
- P6-010：fixture 同时提供 unsupported provider URL `https://bitbucket.org/repolens-demo/ts_webapp/pull-requests/42`，用于演示 unsupported provider 错误态。
- P6-010：新增 `evals/change_requests/README.md`，说明 synthetic PR、仓库路径、失败演示和无外部写回边界；更新 `evals/README.md`。
- P6-010：新增 `backend/app/tests/test_phase6_demo_change_requests.py`，覆盖 fixture 可解析、diff 文件存在、大小限制、无 token、安全失败 URL，以及 fixture provider 通过 PR/MR Review API 生成 completed Review task。
- P6-010：`.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase6_demo_change_requests.py` 通过。
- P6-010：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_demo_change_requests.py` 通过，5 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-002/P6-010 合并专项：`.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\api\\change_requests.py app\\schemas\\change_request.py app\\services\\change_request app\\models\\change_request.py app\\models\\repository.py app\\models\\task.py app\\models\\__init__.py app\\main.py app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py app\\tests\\test_phase6_demo_change_requests.py` 通过。
- P6-002/P6-010 合并专项：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py app\\tests\\test_phase6_demo_change_requests.py` 通过，33 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-010：`npm run build` 通过。
- P6-010：`npm exec tsc -- --noEmit` 与 build 并行时曾因 `.next/types` 生成竞态失败；build 完成后顺序复跑通过。
- P6-011：扩展 `backend/app/tests/test_phase6_demo_change_requests.py`，新增 `test_phase6_demo_change_request_smoke_records_metrics_citations_and_safety`，在内存库中插入已索引 `ReviewPanel` chunk，走 PR/MR Review API 并覆盖 completed task、citations、tool_calls latency、traces 和 token/Authorization 脱敏。
- P6-011：新增 `docs/phase6-smoke-evaluation.md`，记录 URL parse success、provider fetch success、review completion、citation coverage smoke、latency smoke、safety smoke、unsupported provider smoke、质量门禁和 UI smoke。
- P6-011：更新 `docker-compose.yml`，backend service 显式传入 `REPOLENS_CHANGE_REQUEST_TIMEOUT_SECONDS`、`REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS`、GitHub/Gitee/GitLab token 与 base URL，保证容器演示也有 Phase 6 配置入口。
- P6-011：`.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase6_demo_change_requests.py` 通过。
- P6-011：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_demo_change_requests.py` 通过，6 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-011：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P6-011：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，227 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-011：`npm run build` 通过，Next.js production build 正常。
- P6-011：`npm exec tsc -- --noEmit` 在 `npm run build` 之后顺序执行通过；生成的 `frontend/tsconfig.tsbuildinfo` 已清理。
- P6-011：`docker compose config` 通过，输出确认 backend service 包含 Phase 6 Change Request 配置项。
- P6-011：in-app Browser DOM smoke 通过：持久本地 `npm run start -- -p 3000` 返回 HTTP 200；点击 `PR/MR URL` 后 URL 输入框可见，`Run PR/MR Review` 按钮存在且在未选 ready repository 时保持 disabled。
- P6-011：UI screenshot 未完成，原因是当前 in-app Browser 的 CDP `Page.captureScreenshot` 对 full-page、viewport 和 clipped screenshot 均超时；未生成截图文件，P6-012 已将其作为环境阻断收束记录。
- P6-012：更新 README，补充 V1 Phase 6 当前范围、多平台 Change Request Provider、PR/MR Review Flow、Phase 6 环境变量、API、截图状态、安全边界、Demo Plan、Resume Bullets、Interview Talk Track 和文档索引。
- P6-012：更新 `evals/README.md` 和 `evals/change_requests/README.md`，说明 Phase 6 synthetic PR/MR fixture、平台无关契约、离线 smoke、unsupported provider 演示和无外部写回边界。
- P6-012：新增 `docs/phase6-final-closure-review.md`，记录交付能力、验收清单、验证结果、安全审查、已知限制和最终收束结论。
- P6-012：更新 `docs/phase6-smoke-evaluation.md`，将下一步改为收束用途，明确该 smoke 记录已被 README 和 final closure 使用。
- P6-012：更新 `docs/phase6-closed-loop-log.md`，将 P6-012 标记为完成，并补齐开发、审核、测试、评测和最终验收记录。
- P6-012：截图仍未生成，原因沿用 P6-011 已确认的 in-app Browser CDP `Page.captureScreenshot` timeout；README 和最终验收均将其标记为 pending/blocker，没有伪造截图产物。
- P6-012：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P6-012：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，227 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-012：`npm run build` 通过。
- P6-012：`npm exec tsc -- --noEmit` 在 `npm run build` 后顺序执行通过；生成的 `frontend/tsconfig.tsbuildinfo` 已清理。
- P6-012：`docker compose config` 通过，backend service 保留 Phase 6 Change Request 多平台配置项。

## 22. Phase 6 最终收束记录

| 日期 | 结论 | 记录 |
| --- | --- | --- |
| 2026-06-14 | Phase 6 完成 | P6-001 到 P6-012 全部完成；GitHub 是首个只读 fetch 适配器，Gitee Pull Request、GitLab Merge Request 和 self-hosted GitLab 通过 parser/provider contract 预留；未实现写回 PR/MR、approve/request changes、push、自动修改代码或后续 Phase 7/8/9/10 范围 |

## 23. Phase 6.5 / P6-EXT 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P6-EXT-001 | 现状审计 | 完成 | 确认 GitHub PR 已完成 fetch/API/UI/smoke 闭环；Gitee/GitLab/self-hosted GitLab 仅完成 parser/provider contract 和 not implemented 错误路径 |
| P6-EXT-002 | 编写详细设计与闭环记录 | 完成 | 新增 `docs/phase6-ext-detailed-design.md` 和 `docs/phase6-ext-closed-loop-log.md`，明确只读 fetch client、API smoke、安全和验收标准 |
| P6-EXT-003 | 实现 Gitee PR fetch client | 完成 | `GiteeChangeRequestProvider.fetch` 已实现 metadata/files/commits 只读拉取，使用 patch 重建 diff，token 通过 access_token query 传递且不写入 metadata |
| P6-EXT-004 | 实现 GitLab.com MR fetch client | 完成 | `GitLabChangeRequestProvider.fetch` 已实现 API v4 metadata/diffs/commits 只读拉取，使用 patch 重建 diff，token 通过 `PRIVATE-TOKEN` header 传递且不写入 metadata |
| P6-EXT-005 | 实现 self-hosted GitLab MR fetch client | 完成 | self-hosted GitLab 默认由 MR URL 派生 `{host}/api/v4`，也支持 `REPOLENS_GITLAB_BASE_URL` 覆盖 |
| P6-EXT-006 | API 闭环 smoke | 完成 | `test_phase6_change_request_api.py` 新增 Gitee/GitLab/self-hosted GitLab fake provider 循环，均通过现有 PR/MR Review API 生成 completed Review task |
| P6-EXT-007 | 安全与错误处理 | 完成 | `test_phase6_ext_providers.py` 覆盖 token safety、auth、not found、rate limit、diff too large、空 patch fetch failure |
| P6-EXT-008 | 更新文档和演示材料 | 完成 | README、evals README、Phase 6 smoke、Phase 6 final closure、P6-EXT closed-loop 和 worklog 已更新为 Phase 6.5 后状态 |
| P6-EXT-009 | 最终质量门禁 | 完成 | ruff、pytest、frontend build/type check、Docker config 全部通过 |

## 24. Phase 6.5 / P6-EXT 验证记录

- P6-EXT-003/P6-EXT-005：更新 `backend/app/services/change_request/providers.py`，Gitee/GitLab provider 不再继承默认 not implemented；均实现只读 fetch、payload 解析、diff 重建、diff limit 和统一 `FetchedChangeRequest` 输出。
- P6-EXT-003：新增 Gitee provider test，覆盖 metadata/files/commits 拉取、access_token query、patch diff 重建、统计字段和 token 不进入 metadata。
- P6-EXT-004：新增 GitLab.com provider test，覆盖 metadata/diffs/commits 拉取、`PRIVATE-TOKEN` header、patch diff 重建、统计字段和 token 不进入 metadata。
- P6-EXT-005：新增 self-hosted GitLab provider test，覆盖 URL 派生 `/api/v4` 和 configured base URL override。
- P6-EXT-006：扩展 `backend/app/tests/test_phase6_change_request_api.py`，验证 Gitee/GitLab/self-hosted GitLab fake provider 均可通过现有 PR/MR Review API 生成 completed Review task，并持久化 `change_requests` metadata。
- P6-EXT-007：扩展错误和安全测试，覆盖 auth、not found、rate limit、diff too large、空 patch fetch failure 和 token 不进入 metadata。
- P6-EXT：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\change_request app\\tests\\test_phase6_ext_providers.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_api.py` 通过。
- P6-EXT：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_ext_providers.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_change_request_api.py` 通过，27 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-EXT：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_change_request_api.py app\\tests\\test_phase6_ext_providers.py` 通过，12 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-EXT-008：更新 README、evals README、Phase 6 smoke evaluation、Phase 6 final closure review、P6-EXT closed-loop log 和 worklog；当前文档明确 Gitee/GitLab/self-hosted GitLab 已 fetch-capable，Phase 6 历史记录保留当时的 reserved/not implemented 事实。
- P6-EXT-009：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P6-EXT-009：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，232 个测试通过，1 个 Starlette/httpx deprecation warning。
- P6-EXT-009：`npm run build` 通过。
- P6-EXT-009：`npm exec tsc -- --noEmit` 在 `npm run build` 后顺序执行通过；生成的 `frontend/tsconfig.tsbuildinfo` 已清理。
- P6-EXT-009：`docker compose config` 通过，backend service 包含 GitHub/Gitee/GitLab Change Request env vars。

## 25. Phase 6.5 / P6-EXT 最终收束记录

| 日期 | 结论 | 记录 |
| --- | --- | --- |
| 2026-06-14 | P6-EXT 完成 | Gitee Pull Request、GitLab.com Merge Request 和 self-hosted GitLab Merge Request 均已具备只读 fetch client，并通过 provider tests 与 PR/MR Review API smoke；仍不写回 PR/MR、不 approve/request changes、不 push、不自动修改代码、不进入 Phase 7 |

## 26. Phase 7 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P7-001 | 编写 Phase 7 详细设计 | 完成 | 新增 `docs/phase7-detailed-design.md`，明确 FastAPI HTTP JSON-RPC MCP endpoint、tool registry、权限模型、审计字段、前端面板、测试和验收标准 |
| P7-002 | 设计 Tool Registry | 完成 | 新增 `backend/app/services/mcp/registry.py`，统一工具名、description、input schema、permission_policy、enabled 和 handler |
| P7-003 | 设计权限模型 | 完成 | 实现 read_only 默认 allow、safe_check 默认 disabled，并保留 deny/confirm_required 策略值 |
| P7-004 | 实现 MCP Server 启动入口 | 完成 | 新增 `backend/app/api/mcp.py` 和 `MCPService`，`POST /api/mcp` 支持 JSON-RPC `initialize`、`tools/list`、`tools/call` |
| P7-005 | 导出只读工具 | 完成 | 导出 repository.list/status、code.search、file.read_slice、symbol.context、diff.analyze，复用既有只读 service/tool |
| P7-006 | 导出高阶工具 | 完成 | 导出 repository.ask 和 review.diff，复用 QAService 与 ReviewService |
| P7-007 | 增强 tool_calls 审计字段 | 完成 | `ToolCall` 新增 client/session/permission_policy/input_hash/output_hash；MCP 调用创建轻量 `mcp_tool` task 并写审计 |
| P7-008 | 前端 Tool Permissions Panel | 完成 | Workbench 新增 MCP Tool Permissions 面板，展示 registry、permission policy、enabled/disabled、最近 MCP 调用、client/session/hash 和失败原因 |
| P7-009 | MCP client smoke test | 完成 | TestClient 覆盖 initialize、tools/list、code.search、file.read_slice、repository.status、symbol.context、diff.analyze、repository.ask、review.diff |
| P7-010 | 安全测试 | 完成 | 覆盖路径穿越、敏感文件、超大 diff、禁用工具和审计记录 |
| P7-011 | 文档与演示 | 完成 | README、worklog、闭环记录、final closure review 和质量门禁已更新 |

## 27. Phase 7 验证记录

- P7-001：完成 `docs/phase7-detailed-design.md` 和 `docs/phase7-closed-loop-log.md`，明确 Phase 7 只做 MCP Server、工具权限和审计，不进入 Phase 8/9/10。
- P7-002/P7-003：新增 `backend/app/services/mcp/registry.py`，Tool Registry 暴露工具 schema、permission policy、enabled 状态和 handler；safe_check 工具默认 disabled。
- P7-004：新增 `backend/app/services/mcp/service.py`、`backend/app/api/mcp.py`、`backend/app/schemas/mcp.py`，实现 HTTP JSON-RPC endpoint。
- P7-005：导出 `repository.list`、`repository.status`、`code.search`、`file.read_slice`、`symbol.context`、`diff.analyze`。
- P7-006：导出 `repository.ask` 和 `review.diff`，复用现有同步 QA/Review pipeline。
- P7-007：扩展 `ToolCall` 模型，新增 `client_name`、`client_session_id`、`permission_policy`、`input_hash`、`output_hash`；新增 `TaskType.MCP_TOOL` 用于 MCP tool call 审计归属。
- P7-008：扩展 `frontend/types/workbench.ts`、`frontend/lib/api.ts` 和 `frontend/app/page.tsx`，接入 `/api/mcp/tools` 与 `/api/mcp/tool-calls`，新增 Tool Permissions Panel。
- P7-009：`test_phase7_mcp_api.py` 覆盖 `initialize`、`tools/list`、`tools/call`，并 smoke `code.search`、`file.read_slice`、`repository.status`、`symbol.context`、`diff.analyze`、`repository.ask`、`review.diff`。
- P7-010：MCP 安全测试覆盖禁用 `run_safe_static_check`、敏感文件 `.env`、路径穿越 `../outside.py` 和超大 diff。
- P7-011：更新 README、`docs/phase7-closed-loop-log.md` 和 `docs/phase7-final-closure-review.md`，明确 Phase 7 完成边界和非目标。
- P7 SQLite 兼容：更新 `backend/app/db/init_db.py`，对已有 SQLite `tool_calls` 表幂等补齐 Phase 7 新增审计列和索引。
- P7 后端专项：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\mcp app\\api\\mcp.py app\\schemas\\mcp.py app\\models\\tool_call.py app\\models\\task.py app\\db\\init_db.py app\\tests\\test_phase7_mcp_api.py app\\tests\\test_phase7_mcp_registry.py` 通过。
- P7 后端专项：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase7_mcp_api.py app\\tests\\test_phase7_mcp_registry.py` 通过，7 个测试通过，1 个 Starlette/httpx deprecation warning。
- P7 前端：`npm run build` 通过。
- P7 前端：`npm exec tsc -- --noEmit` 通过；生成的 `frontend/tsconfig.tsbuildinfo` 已清理。
- P7 全量：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过。
- P7 全量：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，239 个测试通过，1 个 Starlette/httpx deprecation warning。
- P7 Docker：`docker compose config` 通过。

## 28. Phase 7 最终收束记录

| 日期 | 结论 | 记录 |
| --- | --- | --- |
| 2026-06-14 | Phase 7 完成 | P7-001 到 P7-011 全部完成；RepoLens 已将 MCP-style Tool Layer 升级为 FastAPI HTTP JSON-RPC MCP endpoint，具备 Tool Registry、权限策略、MCP tool call 审计字段、前端 Tool Permissions Panel 和 TestClient smoke/security 闭环；未实现公网 MCP、stdio transport、任意 shell、写操作、PR/MR 写回、自动改代码或 Phase 8/9/10 范围 |

## 29. Phase 8 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P8-001 | 编写 Phase 8 详细设计 | 完成 | 新增 `docs/phase8-detailed-design.md` 和 `docs/phase8-closed-loop-log.md`，明确真正多 Agent 协作只做受控 session/message/assignment/arbiter，不进入 Phase 9/10 |
| P8-002 | 新增 `agent_sessions` 表 | 完成 | 新增 `AgentSession`，保存 task/repository、status、mode、round limit、assignment limit、token budget、summary、final report |
| P8-003 | 新增 `agent_messages` 表 | 完成 | 新增 `AgentMessage`，保存 sender/recipient/type/content/evidence/claims/confidence/requires_arbitration |
| P8-004 | 新增 `agent_assignments` 表 | 完成 | 新增 `AgentAssignment`，保存 agent_name、role、status、round、input/output、evidence、dissent、confidence、token_estimate、latency |
| P8-005 | 实现 Coordinator Agent | 完成 | Multi-Agent service 创建 Coordinator assignment/message，生成 changed files、query、reviewer plan 和 limits |
| P8-006 | 实现并行 Review 子任务 | 完成 | Risk Reviewer、Security Reviewer、Test Strategist 形成独立 assignment/message；实现上保持同步顺序执行、语义上独立分析 |
| P8-007 | 实现 Arbiter Agent | 完成 | Arbiter 合并 accepted/rejected/downgraded/dissent，保留处理理由并写入 final report |
| P8-008 | 实现轮次限制 | 完成 | session 记录并 guard `round_limit`、`assignment_limit`、`token_budget`，API smoke 校验 token 估算未越界 |
| P8-009 | 实现 evidence-grounded message policy | 完成 | 安全敏感风险缺 evidence 时进入 `security_evidence_gap` dissent，并标记 requires_arbitration |
| P8-010 | 前端 Multi-Agent Trace Panel | 完成 | Workbench Review 新增 `Multi-Agent` 模式，展示 session、assignments、messages、dissent、Arbiter、comparison、risks、tests、citations 和 markdown |
| P8-011 | 多 Agent 评测 | 完成 | 新增 single-main `/reviews` vs `/multi-agent-reviews` smoke comparison，并验证 dissent/arbitration |
| P8-012 | 文档与演示 | 完成 | 更新 README、closed-loop log、development worklog，新增 `docs/phase8-smoke-evaluation.md` 和 `docs/phase8-final-closure-review.md` |

## 30. Phase 8 验证记录

- P8 模型专项：`.\\.venv\\Scripts\\python.exe -m ruff check app\\models\\agent_session.py app\\models\\task.py app\\models\\repository.py app\\models\\__init__.py app\\tests\\test_phase8_multi_agent_models.py` 通过。
- P8 模型专项：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase8_multi_agent_models.py` 通过，3 个测试通过。
- P8 后端专项：`.\\.venv\\Scripts\\python.exe -m ruff check app\\schemas\\multi_agent.py app\\services\\multi_agent app\\api\\multi_agent.py app\\main.py app\\tests\\test_phase8_multi_agent_api.py app\\tests\\test_phase8_multi_agent_models.py` 通过。
- P8 后端专项：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase8_multi_agent_models.py app\\tests\\test_phase8_multi_agent_api.py` 通过，7 个测试通过，1 个 Starlette/httpx deprecation warning。
- P8 API smoke 覆盖 1 个 completed multi-agent task、1 个 session、6 个 assignments、6 条 messages、Arbiter decision、GET task/session 查询和 comparison payload。
- P8 dissent smoke 覆盖未索引安全 diff，确认 `security_evidence_gap` dissent、`dissent_count` 和 `requires_arbitration` 不丢失。
- P8 comparison smoke 覆盖同一 diff 的旧单主 Review 和 Multi-Agent Review，确认 multi-agent response 记录 `baseline=single_main_review` 与 `variant=multi_agent_review`。
- P8 前端：`npm run build` 通过。
- P8 前端：`npm exec tsc -- --noEmit` 通过；第一次与 build 并行时因 `.next/types` 尚未生成失败，build 后顺序复跑通过，生成的 `frontend/tsconfig.tsbuildinfo` 已清理。

## 31. Phase 8 最终收束记录

| 日期 | 结论 | 记录 |
| --- | --- | --- |
| 2026-06-14 | Phase 8 完成 | P8-001 到 P8-012 全部完成；RepoLens 已具备受控真正多 Agent 协作流、持久化 session/assignment/message、独立 reviewer 输出、Arbiter dissent 处理、轮次/token guard、Multi-Agent Trace Panel 和 single-main comparison smoke；未实现跨进程 Agent 网络、无限自治 Agent、长期记忆、PR/MR 写回、自动改代码、Phase 9 benchmark 或 Phase 10 展示包装 |

## 32. Phase 9 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P9-001 | 编写 Phase 9 详细设计 | 完成 | 新增 `docs/phase9-detailed-design.md` 和 `docs/phase9-closed-loop-log.md`，明确 Phase 9 只做 benchmark/metrics，不进入 Phase 10 包装 |
| P9-002 | 设计 PR/MR benchmark schema | 完成 | 新增 `backend/app/services/v1_benchmark/dataset.py`，覆盖 platform/change_type/expected_risks/expected_files/mcp_tool_calls |
| P9-003 | 准备 20-30 条 PR/MR 样例 | 完成 | 新增 `evals/datasets/v1_pr_mr_benchmark.jsonl`，22 条 synthetic PR/MR 样例，覆盖 GitHub/Gitee/GitLab/self-hosted GitLab/synthetic |
| P9-004 | 设计 Review quality metrics | 完成 | 实现 risk hit、citation coverage、unsupported claim rate、latency、token estimate |
| P9-005 | 设计 Multi-Agent metrics | 完成 | 实现 dissent usefulness、arbiter resolution rate、token overhead、latency |
| P9-006 | 设计 MCP metrics | 完成 | 实现 tool success rate、permission denial correctness、latency、error count |
| P9-007 | 实现 V1 Evaluation Runner | 完成 | 新增 `POST /api/v1-benchmarks`，复用 ReviewService、MultiAgentReviewService、MCPService |
| P9-008 | 前端 Evaluation Panel 扩展 | 完成 | Workbench Evaluation section 新增 V1 Benchmark 子面板、三组指标、样例表和 markdown report |
| P9-009 | 生成 V1 benchmark report | 完成 | 新增 `docs/phase9-v1-benchmark-report.md`、`docs/phase9-final-closure-review.md`，更新 README、evals README、worklog |

## 33. Phase 9 验证记录

- P9-002/P9-003：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\v1_benchmark app\\tests\\test_phase9_v1_benchmark_dataset.py` 通过。
- P9-002/P9-003：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase9_v1_benchmark_dataset.py` 通过，8 个测试通过。
- P9-004/P9-006：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\v1_benchmark app\\tests\\test_phase9_v1_benchmark_dataset.py app\\tests\\test_phase9_v1_benchmark_metrics.py` 通过。
- P9-004/P9-006：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase9_v1_benchmark_dataset.py app\\tests\\test_phase9_v1_benchmark_metrics.py` 通过，12 个测试通过。
- P9-007：`.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\v1_benchmark app\\schemas\\v1_benchmark.py app\\api\\v1_benchmarks.py app\\main.py app\\schemas\\__init__.py app\\tests\\test_phase9_v1_benchmark_dataset.py app\\tests\\test_phase9_v1_benchmark_metrics.py app\\tests\\test_phase9_v1_benchmark_api.py` 通过。
- P9-007：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase9_v1_benchmark_dataset.py app\\tests\\test_phase9_v1_benchmark_metrics.py app\\tests\\test_phase9_v1_benchmark_api.py` 通过，15 个测试通过，1 个 Starlette/httpx deprecation warning。
- P9-008：`npm run build` 通过。
- P9-008：`npm exec tsc -- --noEmit` 通过。
- P9-final：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过，All checks passed。
- P9-final：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，261 个测试通过，1 个 Starlette/httpx deprecation warning。
- P9-final：`npm run build` 通过；`npm exec tsc -- --noEmit` 顺序复跑通过；并行 build 时曾因 `.next/types` 重建出现瞬时缺文件。
- P9-final：`docker compose config` 通过，Compose 配置可展开。

## 34. Phase 9 最终收束记录

| 日期 | 结论 | 记录 |
| --- | --- | --- |
| 2026-06-14 | Phase 9 完成并闭环 | P9-001 到 P9-009 全部完成；RepoLens 已具备 V1 PR/MR benchmark dataset、Review/Multi-Agent/MCP 三组指标、V1 Benchmark API、Workbench V1 Benchmark panel 和 benchmark report；最终 Ruff、backend tests、frontend build/typecheck、docker compose config 均通过；未进入 live PR/MR benchmark farm、平台写回、自动改代码或 Phase 10 截图/发布包装 |

## 35. Phase 10 任务记录

| 编号 | 任务 | 状态 | 记录 |
| --- | --- | --- | --- |
| P10-001 | 编写 Phase 10 详细设计 | 完成 | 新增 `docs/phase10-detailed-design.md` 和 `docs/phase10-closed-loop-log.md`，明确 Phase 10 只做演示、文档与发布包装 |
| P10-002 | README V1 更新 | 完成 | README 当前范围切换为 V1 complete path，补充 Phase 10、V1 Demo Runbook、release package、截图和发布说明 |
| P10-003 | V1 架构图更新 | 完成 | README 架构图已包含 Change Request Provider、MCP endpoint、Multi-Agent 和 V1 Benchmark Runner |
| P10-004 | 准备演示脚本 | 完成 | 新增 `docs/phase10-demo-runbook.md`，覆盖 PR/MR Review、MCP Client、Multi-Agent Trace、V1 Benchmark 四条演示路径 |
| P10-005 | 录制或整理截图 | 完成 | 新增 `change-request-review-panel.png`、`mcp-tool-permissions-panel.png`、`multi-agent-trace-panel.png`、`v1-benchmark-panel.png`，并统一 10 张 README 截图为 PNG |
| P10-006 | 更新简历 bullet | 完成 | README 和 `docs/phase10-v1-release-package.md` 已新增 V1 release packaging bullet |
| P10-007 | 更新面试讲法 | 完成 | README 和 `docs/phase10-v1-release-package.md` 已新增 Phase 10 release decision/talk track |
| P10-008 | 最终测试与发布检查 | 完成 | 新增 `backend/app/tests/test_phase10_release_package.py` 并完成最终质量门禁、compose、敏感信息扫描 |

## 36. Phase 10 验证记录

- P10-001：文档审查通过，详细设计和闭环日志已创建。
- P10 release package：新增测试 `backend/app/tests/test_phase10_release_package.py`，用于校验 README、runbook、release package 和截图资产。
- P10 release package Ruff：`.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase10_release_package.py` 通过。
- P10 release package 测试：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase10_release_package.py` 通过，5 个测试通过。
- P10 final：`.\\.venv\\Scripts\\python.exe -m ruff check app` 通过，All checks passed。
- P10 final：`.\\.venv\\Scripts\\python.exe -m pytest app\\tests` 通过，266 个测试通过，1 个 Starlette/httpx deprecation warning。
- P10 final：`npm run build` 通过。
- P10 final：`npm exec tsc -- --noEmit` 通过，生成的 `frontend/tsconfig.tsbuildinfo` 已清理。
- P10 final：`docker compose config` 通过。
- P10 final：敏感信息扫描通过；仅命中 redaction 测试/文档样例，无实值密钥。

## 37. Phase 10 最终收束记录

| 日期 | 结论 | 记录 |
| --- | --- | --- |
| 2026-06-15 | Phase 10 完成并闭环 | P10-001 到 P10-008 全部完成；RepoLens V1 已具备 README、V1 架构叙事、demo runbook、release package、PR/MR/MCP/Multi-Agent/V1 Benchmark 截图、简历 bullet、面试讲法、release package 测试和最终质量门禁；未新增平台写回、自动改代码、公网 MCP、跨进程 Agent 网络或生产化范围 |
