# RepoLens 开发过程记录

## 1. 文档用途

本文档用于概括记录 RepoLens 的开发过程，按 `docs/p0-plus-development-plan.md` 中的 Phase 和任务编号维护进度。记录保持简洁，重点匹配开发计划，不展开过多实现细节。

## 2. 当前阶段

- 当前阶段：Phase 5 - 评测、部署与简历包装
- 当前状态：Phase 5 已完成 P5-DESIGN、P5-CLOSED-LOOP、P5-001 至 P5-012，P0+ 闭环完成
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
