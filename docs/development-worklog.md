# RepoLens 开发过程记录

## 1. 文档用途

本文档用于概括记录 RepoLens 的开发过程，按 `docs/p0-plus-development-plan.md` 中的 Phase 和任务编号维护进度。记录保持简洁，重点匹配开发计划，不展开过多实现细节。

## 2. 当前阶段

- 当前阶段：Phase 2 - 代码图谱与混合检索
- 当前状态：Phase 2 已完成，P2-DESIGN 与 P2-001 至 P2-011 均已闭环
- 开始日期：2026-06-05
- 完成日期：2026-06-05

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
