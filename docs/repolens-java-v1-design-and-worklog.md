# RepoLens-Java V1 共用过程记录

## 1. 记录规则

本文件记录 V1 从 P0 到 P6 的执行过程。每个阶段必须满足：

1. 执行前已有独立详细设计文档。
2. 实现后记录主要文件、测试命令、验收结果。
3. 若阶段有降级实现，必须说明保留的替换接口。
4. 不把 P0-P6 拆成新项目目录，继续在 `backend-java/` 和 `frontend/` 中增量开发。

## 2. 阶段文档索引

| 阶段 | 详细设计 |
| --- | --- |
| V1-P0 | `docs/repolens-java-v1-p0-detailed-design.md` |
| V1-P1 | `docs/repolens-java-v1-p1-detailed-design.md` |
| V1-P2 | `docs/repolens-java-v1-p2-detailed-design.md` |
| V1-P3 | `docs/repolens-java-v1-p3-detailed-design.md` |
| V1-P4 | `docs/repolens-java-v1-p4-detailed-design.md` |
| V1-P5 | `docs/repolens-java-v1-p5-detailed-design.md` |
| V1-P6 | `docs/repolens-java-v1-p6-detailed-design.md` |
| V1-P7 | `docs/repolens-java-v1-p7-detailed-design.md` |

## 3. V1-P0 执行记录

| 项目 | 状态 |
| --- | --- |
| 详细设计 | DONE |
| 实现 | DONE |
| 测试 | DONE |
| 验收 | DONE |

### 3.1 计划实现

- 增加 demo/local/test 配置约定。
- 更新文档索引。
- 保持 V0 测试通过。

### 3.2 完成记录

完成内容：

- 新增 `docs/repolens-java-v1-p0-detailed-design.md`。
- 新增 V1 共用过程记录 `docs/repolens-java-v1-design-and-worklog.md`。
- 更新 `docs/README.md`，补充 P0-P3 详细设计和过程记录入口。
- 将 `repolens.version` 默认值升级为 `v1`。
- 在 `application.yml` 中增加 `repolens.indexing` 和 `repolens.retrieval` 配置。
- 新增 `application-demo.yml`，为后续 demo profile 预留稳定配置。

涉及文件：

- `backend-java/src/main/resources/application.yml`
- `backend-java/src/main/resources/application-demo.yml`
- `backend-java/src/main/java/com/repolens/config/RepoLensProperties.java`
- `backend-java/src/test/java/com/repolens/status/StatusControllerTest.java`
- `docs/README.md`

验证：

```powershell
& ..\scripts\use-java.ps1 21; mvn test
```

结果：后续 P0-P3 完整验证中，25 个后端测试通过。

## 4. V1-P1 执行记录

| 项目 | 状态 |
| --- | --- |
| 详细设计 | DONE |
| 实现 | DONE |
| 测试 | DONE |
| 验收 | DONE |

### 4.1 计划实现

- 新增 index task/task event 表和 JPA entity。
- 抽出 `RepositoryIndexPipeline`。
- 新增 task 查询、latest、retry API。
- 现有 import API 触发索引任务并保持兼容。

### 4.2 完成记录

完成内容：

- 新增 Flyway migration `V3__add_v1_index_tasks.sql`。
- 新增 `IndexTaskEntity`、`IndexTaskEventEntity`、`IndexTaskStatus`、`IndexTaskEventStatus`。
- 新增 `IndexTaskJpaRepository`、`IndexTaskEventJpaRepository`。
- 新增 `RepositoryIndexLock` 和 `InMemoryRepositoryIndexLock`，保留后续 Redis lock 替换边界。
- 新增 `RepositoryIndexContext`，统一更新 task、event、progress。
- 新增 `RepositoryIndexPipeline`，承载 scan、parse、graph、chunk、BM25、vector 阶段。
- 新增 `RepositoryIndexingService`，提供 start、latest、get、retry。
- 新增 `IndexTaskController`：
  - `POST /api/repositories/{repositoryId}/index`
  - `GET /api/repositories/{repositoryId}/index-tasks/latest`
  - `GET /api/index-tasks/{taskId}`
  - `POST /api/index-tasks/{taskId}/retry`
- `POST /api/repositories` 继续返回 repository detail，同时背后创建索引任务和事件。

涉及文件：

- `backend-java/src/main/resources/db/migration/V3__add_v1_index_tasks.sql`
- `backend-java/src/main/java/com/repolens/indexing/**`
- `backend-java/src/main/java/com/repolens/repository/application/RepositoryApplicationService.java`
- `backend-java/src/test/java/com/repolens/repository/api/RepositoryControllerTest.java`

验证：

- 导入仓库后存在 latest index task。
- task status 为 `READY`，progress 为 100。
- task events 包含 `SCANNING`、`PARSING`、`GRAPH_BUILDING`、`BM25_INDEXING`、`VECTOR_INDEXING`、`READY`。
- 旧导入接口仍返回 `ready`。

## 5. V1-P2 执行记录

| 项目 | 状态 |
| --- | --- |
| 详细设计 | DONE |
| 实现 | DONE |
| 测试 | DONE |
| 验收 | DONE |

### 5.1 计划实现

- 新增 symbol/relation 表和 JPA entity。
- 增加基础 Python/TS parser。
- 在索引 pipeline 中构建图谱。
- 新增 graph summary/search/neighbors API。

### 5.2 完成记录

完成内容：

- 新增 Flyway migration `V4__add_v1_code_graph.sql`。
- 新增 `code_symbols`、`code_relations` 对应 entity 和 repository。
- 新增 `LanguageParserRegistry`。
- 新增 `SimplePythonParser`，支持 import、class、function、decorator 基础解析。
- 新增 `SimpleTypeScriptParser`，支持 import、class、function、const arrow function、class method 基础解析。
- 扩展 `Language`：`PYTHON`、`TYPESCRIPT`、`JAVASCRIPT`。
- 扩展 `SymbolType`：`FUNCTION`。
- 更新 `ChunkBuilder`，非 Java symbol 也可以生成 symbol chunk。
- 新增 `CodeGraphBuilder`，构建 `CONTAINS`、`IMPORTS`、`ROUTE` relation。
- 新增 `CodeGraphService` 和 `CodeGraphController`：
  - `GET /api/repositories/{id}/graph/summary`
  - `GET /api/repositories/{id}/symbols?query=...`
  - `GET /api/repositories/{id}/symbols/{symbolId}/neighbors`
- 索引 pipeline 中在 PARSING 后执行图谱构建，并更新 repository `relation_count`。

涉及文件：

- `backend-java/src/main/resources/db/migration/V4__add_v1_code_graph.sql`
- `backend-java/src/main/java/com/repolens/graph/**`
- `backend-java/src/main/java/com/repolens/parser/LanguageParserRegistry.java`
- `backend-java/src/main/java/com/repolens/parser/SimplePythonParser.java`
- `backend-java/src/main/java/com/repolens/parser/SimpleTypeScriptParser.java`
- `backend-java/src/main/java/com/repolens/scanner/Language.java`
- `backend-java/src/main/java/com/repolens/scanner/FileLanguageDetector.java`

验证：

- `SimplePythonParserTest` 覆盖 Python class/function/import/decorator。
- `SimpleTypeScriptParserTest` 覆盖 TS import/class/function/method。
- `CodeGraphControllerTest` 覆盖 graph summary、symbol search、neighbors。
- repository 导入后 symbol/relation count 大于 0。

## 6. V1-P3 执行记录

| 项目 | 状态 |
| --- | --- |
| 详细设计 | DONE |
| 实现 | DONE |
| 测试 | DONE |
| 验收 | DONE |

### 6.1 计划实现

- 新增 vector chunk 表和 JPA entity。
- 实现 deterministic hash embedding。
- 在索引 pipeline 中构建向量。
- 检索服务支持 BM25 + Vector + Graph hybrid。

### 6.2 完成记录

完成内容：

- 新增 Flyway migration `V5__add_v1_vector_chunks.sql`。
- 新增 `ChunkVectorEntity`、`ChunkVectorJpaRepository`。
- 新增 `EmbeddingProvider` 接口和 `HashEmbeddingProvider`。
- 新增 `VectorIndexService`，索引时为每个 chunk 生成本地 deterministic embedding。
- 新增 `VectorSearchService`，使用 cosine similarity 做 vector recall。
- 更新 `RetrievalService`：
  - 支持 BM25 recall。
  - 支持 vector recall。
  - 支持 graph expansion。
  - 支持 score merge：BM25/vector/graph 三路分数。
  - response 中 `sources`、`bm25_score`、`vector_score`、`graph_score` 真实生效。
- 前端类型和页面已有对应字段，无需本阶段额外改动。

涉及文件：

- `backend-java/src/main/resources/db/migration/V5__add_v1_vector_chunks.sql`
- `backend-java/src/main/java/com/repolens/retrieval/vector/**`
- `backend-java/src/main/java/com/repolens/retrieval/application/RetrievalService.java`
- `backend-java/src/main/java/com/repolens/chunking/infrastructure/CodeChunkJpaRepository.java`

验证：

- `HashEmbeddingProviderTest` 验证 embedding 确定性和归一化。
- `RetrievalControllerTest` 验证 `use_vector=true`、`use_graph=true` 时 vector/graph count 和分数大于 0。
- repository 导入后 `vector_chunks` 数量等于 chunk 数量。

## 6.3 完整测试记录

最终验证命令：

```powershell
& ..\scripts\use-java.ps1 21; mvn test
```

最终结果：

```text
Tests run: 25, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 7. 当前已知取舍

| 主题 | 取舍 |
| --- | --- |
| Redis | P1 先用 in-memory lock，保留接口，后续替换 Redis |
| VectorStore | P3 先用 DB + JSON vector，后续替换 Qdrant/PGvector |
| Embedding | P3 先用 hash embedding，后续替换 Spring AI EmbeddingModel |
| Python/TS Parser | P2 先做基础结构解析，Java 保持深度主线 |

这些取舍不影响 P0-P3 的本地闭环：当前版本已经能完成导入、任务记录、图谱持久化、向量索引和 Hybrid+Graph 检索。

## 8. V1-P4 执行记录

| 项目 | 状态 |
| --- | --- |
| 详细设计 | DONE |
| 实现 | DONE |
| 测试 | DONE |
| 验收 | DONE |

### 8.1 计划实现

- 新增 QA task 和 agent trace 表。
- 新增 deterministic Agent QA 服务。
- 复用 hybrid retrieval 作为 `code.search` 工具。
- 返回 citations、answer、confidence、warnings、traces。
- 新增 `/api/repositories/{repositoryId}/questions` 和 `/api/questions/{taskId}`。

### 8.2 完成记录

完成内容：

- 新增详细设计 `docs/repolens-java-v1-p4-detailed-design.md`。
- 新增 Flyway migration `V6__add_v1_agent_qa.sql`。
- 新增 `qa_tasks` 和 `agent_traces` 表。
- 新增通用 trace 层：
  - `AgentTraceEntity`
  - `AgentTraceJpaRepository`
  - `AgentTraceRecorder`
  - `AgentTraceResponse`
- 新增 QA 模块：
  - `QATaskEntity`
  - `QATaskJpaRepository`
  - `QACreateRequest`
  - `QACitationResponse`
  - `QATaskResponse`
  - `QuestionAnsweringService`
  - `QuestionController`
- `QuestionAnsweringService` 复用 P3 `RetrievalService` 作为 `code.search` 工具。
- 返回 deterministic answer、citations、confidence、warnings、traces。
- Trace 阶段包含 `planner`、`code.search`、`verifier`、`final_answer`。
- 新增 API：
  - `POST /api/repositories/{repositoryId}/questions`
  - `GET /api/questions/{taskId}`

涉及文件：

- `backend-java/src/main/resources/db/migration/V6__add_v1_agent_qa.sql`
- `backend-java/src/main/java/com/repolens/agent/**`
- `backend-java/src/main/java/com/repolens/qa/**`
- `backend-java/src/test/java/com/repolens/qa/api/QuestionControllerTest.java`

验证：

- `QuestionControllerTest` 验证导入仓库后可问答。
- 响应 status 为 `completed`。
- citations 非空且来自真实 evidence。
- traces 包含 `planner`、`code.search`、`verifier`、`final_answer`。
- `GET /api/questions/{taskId}` 可查回同一任务。

## 9. V1-P5 执行记录

| 项目 | 状态 |
| --- | --- |
| 详细设计 | DONE |
| 实现 | DONE |
| 测试 | DONE |
| 验收 | DONE |

### 9.1 计划实现

- 新增 review task 和 review tool call 表。
- 实现 unified diff parser。
- 实现规则层风险识别。
- 复用 hybrid retrieval 补充 citations。
- 返回 risks、impacted_symbols、suggested_tests、markdown、tool_calls、traces。
- 新增 `/api/repositories/{repositoryId}/reviews` 和 `/api/reviews/{taskId}`。

### 9.2 完成记录

完成内容：

- 新增详细设计 `docs/repolens-java-v1-p5-detailed-design.md`。
- 新增 Flyway migration `V7__add_v1_review_tasks.sql`。
- 新增 `review_tasks` 和 `review_tool_calls` 表。
- 新增 Review 持久化层：
  - `ReviewTaskEntity`
  - `ReviewToolCallEntity`
  - `ReviewTaskJpaRepository`
  - `ReviewToolCallJpaRepository`
- 新增 unified diff parser：
  - `DiffParser`
  - `ParsedDiff`
  - `ChangedFile`
  - `DiffHunk`
  - `DiffLine`
  - `DiffLineType`
- 新增 deterministic 风险规则：
  - `ReviewRiskRuleEngine`
  - 规则覆盖鉴权放宽、明文 secret/token、危险命令执行、return null、宽泛异常、SQL 变更、TODO/FIXME。
- 新增 review tool call 记录器：
  - `ReviewToolCallRecorder`
- 新增 Review 服务和 API：
  - `ReviewService`
  - `ReviewController`
  - `ReviewCreateRequest`
  - `ReviewTaskResponse`
  - `ReviewToolCallResponse`
- 返回 `risks`、`impacted_symbols`、`suggested_tests`、`citations`、`markdown`、`tool_calls`、`traces`。
- Trace 阶段包含 `diff.parse`、`code.search`、`risk.rules`、`final_report`。
- 新增 API：
  - `POST /api/repositories/{repositoryId}/reviews`
  - `GET /api/reviews/{taskId}`

涉及文件：

- `backend-java/src/main/resources/db/migration/V7__add_v1_review_tasks.sql`
- `backend-java/src/main/java/com/repolens/review/**`
- `backend-java/src/test/java/com/repolens/review/application/DiffParserTest.java`
- `backend-java/src/test/java/com/repolens/review/api/ReviewControllerTest.java`

验证：

- `DiffParserTest` 验证 unified diff 文件、hunk、新增行解析。
- `ReviewControllerTest` 验证导入仓库后提交 diff 可生成 review。
- 响应 status 为 `completed`。
- `risk_level` 可识别 high。
- risks、citations、suggested_tests、markdown、tool_calls、traces 均存在。
- `GET /api/reviews/{taskId}` 可查回同一任务。

## 10. P0-P5 完整测试记录

最终验证命令：

```powershell
& ..\scripts\use-java.ps1 21; mvn test
```

最终结果：

```text
Tests run: 28, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

前端验证命令：

```powershell
npm run build
```

## 11. V1-P6 执行记录

| 项目 | 状态 |
| --- | --- |
| 详细设计 | DONE |
| 实现 | DONE |
| 测试 | DONE |
| 验收 | DONE |

### 11.1 计划实现

- 新增 MCP-style tool registry。
- 新增 `GET /api/mcp/tools`、`POST /api/mcp/tools/call`、`GET /api/mcp/tool-calls`。
- 暴露只读工具：search、read_file、find_symbol、graph_neighbors、review_diff。
- 保留 disabled execution-class tool，展示安全边界。
- 新增 permission guard，覆盖 repository scope、路径穿越、敏感文件和输入上限。
- 新增 MCP audit 表，记录 status、permission、hash、summary、latency、client/session。
- 补齐前端 TypeScript 调用契约。

### 11.2 完成记录

完成内容：

- 新增详细设计 `docs/repolens-java-v1-p6-detailed-design.md`。
- 新增 Flyway migration `V8__add_v1_mcp_audit.sql`。
- 新增 `mcp_tool_call_audits` 表，记录 tool、status、permission、input/output hash、summary、latency、client/session。
- 新增 MCP 模块：
  - `McpController`
  - `McpToolService`
  - `McpToolRegistry`
  - `McpPermissionGuard`
  - `McpAuditService`
  - `McpToolCallAuditEntity`
  - `McpToolCallAuditJpaRepository`
- 新增工具：
  - `repolens.search`
  - `repolens.read_file`
  - `repolens.find_symbol`
  - `repolens.graph_neighbors`
  - `repolens.review_diff`
  - `repolens.safe_static_check`，默认 disabled，用于展示 execution-class 边界。
- 新增 API：
  - `GET /api/mcp/tools`
  - `POST /api/mcp/tools/call`
  - `GET /api/mcp/tool-calls`
- 权限守卫覆盖：
  - repository 必须存在且 READY。
  - `read_file` 只允许仓库内相对路径。
  - 拒绝路径穿越、绝对路径、secret/key/cert/env 类敏感文件。
  - 文件读取限制 200 行。
  - `top_k` 限制到 20。
  - `diff_text` 限制到 20,000 字符。
- 前端补齐：
  - `McpToolCallRequest`
  - `McpToolCallResponse`
  - `callMcpTool(payload)`

涉及文件：

- `backend-java/src/main/resources/db/migration/V8__add_v1_mcp_audit.sql`
- `backend-java/src/main/java/com/repolens/mcp/**`
- `backend-java/src/test/java/com/repolens/mcp/api/McpControllerTest.java`
- `frontend/types/workbench.ts`
- `frontend/lib/api.ts`

验证：

- `McpControllerTest` 覆盖 `tools/list`、`tools/call`、search、read_file、路径穿越拒绝、disabled 工具、audit list。
- audit 记录包含 `input_hash`、`output_hash`、`client_name`、`status`、`permission_decision`。

后端最终验证命令：

```powershell
& ..\scripts\use-java.ps1 21; mvn test
```

后端最终结果：

```text
Tests run: 29, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

前端最终验证命令：

```powershell
npm run build
```

前端最终结果：

```text
Compiled successfully
Linting and checking validity of types passed
```

## 12. P0-P6 完整测试记录

最终验证命令：

```powershell
& ..\scripts\use-java.ps1 21; mvn test
npm run build
```

最终结果：

```text
Backend: Tests run: 29, Failures: 0, Errors: 0, Skipped: 0, BUILD SUCCESS
Frontend: Next.js production build compiled successfully
```

## 13. V1-P7 执行记录

| 项目 | 状态 |
| --- | --- |
| 详细设计 | DONE |
| 实现 | DONE |
| 测试 | DONE |
| 验收 | DONE |

### 13.1 计划实现

- 新增 Evaluation run/result 表。
- 新增 Evaluation API：create/list/get。
- 支持 `vector_only`、`bm25_vector`、`bm25_vector_graph` 和 `all`。
- 计算 Hit@5、MRR、Citation Coverage、Latency、token estimate、error count。
- 新增 Java V1 评测数据集。
- 前端工作台整合 Search、Ask、Review、MCP、Eval tabs。
- 新增 Java V1 demo runbook、release package、final closure review。

### 13.2 完成记录

完成内容：

- 新增详细设计 `docs/repolens-java-v1-p7-detailed-design.md`。
- 新增 Flyway migration `V9__add_v1_evaluations.sql`。
- 新增 `evaluation_runs` 和 `evaluation_results` 表。
- 新增 Evaluation 模块：
  - `EvaluationController`
  - `EvaluationService`
  - `EvaluationDatasetReader`
  - `EvaluationMetricCalculator`
  - `EvaluationRunEntity`
  - `EvaluationResultEntity`
  - `EvaluationRunJpaRepository`
  - `EvaluationResultJpaRepository`
- 新增 API：
  - `POST /api/evaluations`
  - `GET /api/evaluations`
  - `GET /api/evaluations/{runId}`
- 支持评测策略：
  - `vector_only`
  - `bm25_vector`
  - `bm25_vector_graph`
  - `all`
- 评测指标包含 Hit@5、MRR、Citation Coverage、平均延迟、P50/P95 延迟、token estimate、error count。
- 新增 Java V1 数据集 `evals/datasets/repolens_java_v1_eval.jsonl`。
- 前端从 V0 检索页升级为 V1 Workbench：
  - `Search`
  - `Ask`
  - `Review`
  - `MCP`
  - `Eval`
- 新增 Java V1 发布文档：
  - `docs/repolens-java-v1-demo-runbook.md`
  - `docs/repolens-java-v1-release-package.md`
  - `docs/repolens-java-v1-final-closure-review.md`

涉及文件：

- `backend-java/src/main/resources/db/migration/V9__add_v1_evaluations.sql`
- `backend-java/src/main/java/com/repolens/evaluation/**`
- `backend-java/src/test/java/com/repolens/evaluation/api/EvaluationControllerTest.java`
- `evals/datasets/repolens_java_v1_eval.jsonl`
- `frontend/app/page.tsx`
- `docs/repolens-java-v1-p7-detailed-design.md`
- `docs/repolens-java-v1-demo-runbook.md`
- `docs/repolens-java-v1-release-package.md`
- `docs/repolens-java-v1-final-closure-review.md`

验证：

- `EvaluationControllerTest` 覆盖导入仓库、运行 `all` 三策略、持久化 metrics/results、list/get 查询。
- 前端 `npm run build` 覆盖 V1 Workbench tabs 的 TypeScript 和生产构建。

后端最终验证命令：

```powershell
& ..\scripts\use-java.ps1 21; mvn test
```

后端最终结果：

```text
Tests run: 30, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

前端最终验证命令：

```powershell
npm run build
```

前端最终结果：

```text
Compiled successfully
Linting and checking validity of types passed
```

## 14. Java V1 最终闭环记录

最终验证命令：

```powershell
& ..\scripts\use-java.ps1 21; mvn test
npm run build
```

最终结果：

```text
Backend: Tests run: 30, Failures: 0, Errors: 0, Skipped: 0, BUILD SUCCESS
Frontend: Next.js production build compiled successfully
```

Java V1 当前已经形成完整闭环：

```text
仓库导入 -> 索引状态机 -> 多语言解析/代码图谱 -> BM25+Vector+Graph 检索
-> Agent QA/Trace -> PR Review -> MCP tools/audit -> Evaluation -> V1 Workbench/Release Docs
```
