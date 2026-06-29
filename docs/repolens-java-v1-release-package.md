# RepoLens-Java V1 Release Package

## Positioning

RepoLens-Java is a local-first, read-only repository-level Code Agent workbench built with Java 21, Spring Boot, Lucene, deterministic vector retrieval, code graph expansion, MCP-style tools, and Next.js.

It is intended as a resume centerpiece for Java backend or Java full-stack roles. The project demonstrates engineering depth in indexing, parsing, retrieval, tool permissions, auditability, frontend workflow design, and evaluation.

## V1 Capabilities

| Area | Capability |
| --- | --- |
| Repository | Local path import, scanner, file metadata, language summary |
| Indexing | Task records, stage events, retry API, repository status |
| Parsing | Java parser plus Python/TypeScript baseline parsing |
| Graph | Symbol table, relation table, summary/search/neighbors API |
| Retrieval | BM25, deterministic vector recall, graph expansion, score merge |
| QA | Deterministic Agent QA, citations, confidence, warnings, traces |
| Review | Unified diff parser, deterministic risk rules, citations, tests, markdown |
| MCP | Tool registry, tools/call, permission guard, audit hashes |
| Evaluation | JSONL dataset runner, Hit@5, MRR, citation coverage, latency |
| Frontend | Repository, Search, Ask, Review, MCP, Eval workbench tabs |

## Main APIs

| Method | Path |
| --- | --- |
| POST | `/api/repositories` |
| GET | `/api/repositories` |
| GET | `/api/repositories/{repositoryId}/status` |
| POST | `/api/repositories/{repositoryId}/retrieve` |
| POST | `/api/repositories/{repositoryId}/questions` |
| POST | `/api/repositories/{repositoryId}/reviews` |
| GET | `/api/mcp/tools` |
| POST | `/api/mcp/tools/call` |
| GET | `/api/mcp/tool-calls` |
| POST | `/api/evaluations` |
| GET | `/api/evaluations` |
| GET | `/api/evaluations/{runId}` |

## Resume Bullets

```text
RepoLens：基于 Java 21、Spring Boot 与 MCP 的仓库级 Code Agent 工作台
- 设计并实现本地仓库导入、异步索引任务、Java/Python/TypeScript 解析、符号图谱构建和 Lucene BM25 检索，支撑仓库级代码理解。
- 构建 BM25、确定性向量检索和代码图谱扩展的混合召回链路，返回带文件路径、行号、symbol、source 和 score 的 evidence，并用离线评测量化 Hit@5、MRR、Citation Coverage 和 Latency。
- 实现带 citations 和 Agent Trace 的仓库问答，以及基于 unified diff、规则风险识别、检索证据和测试建议的 PR Review 工作流。
- 将 search、read_file、find_symbol、graph_neighbors、review_diff 暴露为 MCP-style 只读工具，加入路径穿越防护、敏感文件过滤、输入上限和 input/output hash 审计。
- 使用 Next.js 构建 V1 Workbench，整合 Repository、Search、Ask、Review、MCP、Eval 五条演示路径，形成可复现的全栈项目闭环。
```

## Known Tradeoffs

| Tradeoff | Reason |
| --- | --- |
| Deterministic hash embedding | Keeps local demo and tests stable without external model keys |
| In-memory repository lock | Preserves lock abstraction; Redis replacement is straightforward |
| MCP-style HTTP bridge | Keeps P6 demo local and testable; full stdio/SSE MCP transport can be added later |
| Deterministic QA/Review | Avoids LLM instability for resume demo; Spring AI adapter remains the planned replacement seam |
| Pasted diff review | Real PR/MR providers are V1.1 scope |

## Recommended Next Step

If the project needs to demonstrate more traditional Java backend depth after V1/V1.1, the preferred path is V2-Lite ReviewHub instead of a separate unrelated seckill or mall project.

V2-Lite turns RepoLens into a team-level distributed review task platform:

| Area | Planned Depth |
| --- | --- |
| Distributed jobs | `analysis_job` / `job_attempt` / `job_event`, state machine, retry, dead letter, cancellation |
| MQ | RabbitMQ-first worker queue, Kafka as a later replacement option, duplicate-message-safe consumers |
| Redis | Repository lock, webhook idempotency, user/repository rate limit, hot job status cache |
| Business system | Organization, project, repository binding, review ruleset, quota, audit |
| Observability | Actuator, Micrometer, Prometheus, Grafana dashboard, failure reason statistics |

Detailed plan: `docs/repolens-java-v2-lite-reviewhub-plan.md`.

## Final Verification

```powershell
cd F:\Desktop\agent\RepoLens\backend-java
& ..\scripts\use-java.ps1 21
mvn test
```

```powershell
cd F:\Desktop\agent\RepoLens\frontend
npm run build
```
