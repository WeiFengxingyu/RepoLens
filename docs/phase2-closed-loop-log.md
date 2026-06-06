# RepoLens Phase 2 开发审核测试评测闭环记录

## 1. 文档用途

本文档用于记录 Phase 2 的开发、审核、测试和评测闭环。记录粒度与 `docs/p0-plus-development-plan.md` 中 P2-001 到 P2-011 对齐，保持简洁但可追溯。

## 2. 当前状态

- 当前阶段：Phase 2 - 代码图谱与混合检索
- 当前状态：已完成 P2-DESIGN、P2-001 至 P2-011
- 开始日期：2026-06-06
- 依据文档：`docs/phase2-detailed-design.md`

## 3. 任务闭环记录

| 编号 | 任务 | 开发状态 | 审核状态 | 测试状态 | 评测/指标状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| P2-DESIGN | Phase 2 详细设计 | 完成 | 通过 | 文档审查通过 | 完成 | 新增 Phase 2 详细设计，覆盖 BM25、embedding、Qdrant、NetworkX、Hybrid Retriever、Evidence、Context Builder 和 Evidence Panel |
| P2-001 | 实现 BM25 索引 | 完成 | 通过 | 通过 | 完成 | 新增轻量 tokenizer、BM25Document、BM25Index 和 chunk 构建 helper，支持关键词、文件名、函数名检索 |
| P2-002 | 实现 embedding adapter | 完成 | 通过 | 通过 | 完成 | 新增 OpenAI-compatible embedding adapter，支持配置读取、disabled 错误、请求响应校验、响应排序和维度校验 |
| P2-003 | 实现 Qdrant 写入 | 完成 | 通过 | 通过 | 完成 | 新增 Qdrant REST 写入服务和手动向量索引 API，支持 collection ensure、chunk embedding、UUID-compatible point id、payload upsert 和 disabled/error 返回 |
| P2-004 | 实现 Qdrant 检索 | 完成 | 通过 | 通过 | 完成 | 新增 query embedding + Qdrant search，强制 repository_id filter，支持 language/symbol_type/file_path 条件和 vector candidate 输出 |
| P2-005 | 实现 NetworkX 代码图 | 完成 | 通过 | 通过 | 完成 | 新增 NetworkX DiGraph 加载服务，从 SQLite chunks/relations 构建节点和双端关系边，并统计跳过关系 |
| P2-006 | 实现图邻域查询 | 完成 | 通过 | 通过 | 完成 | 新增 callers/callees/same_file/imports/一跳邻域和 graph expand，输出 GraphExpansionCandidate |
| P2-007 | 实现候选合并去重 | 完成 | 通过 | 通过 | 完成 | 新增 RetrievalCandidate 和 merge_candidates，按 chunk_id 合并 BM25/vector/graph_expand 来源与分数 |
| P2-008 | 实现轻量重排公式 | 完成 | 通过 | 通过 | 完成 | 新增 rerank_candidates 和 RankedRetrievalCandidate，按设计权重归一化 BM25/vector/graph/file/diff 分并计算 final_score |
| P2-009 | 实现 Evidence 输出 | 完成 | 通过 | 通过 | 完成 | 新增 Evidence、build_evidences、稳定 evidence_id 和 snippet 截断，结合 ranked candidate 与 SQLite chunk 元数据 |
| P2-010 | 实现 Context Builder | 完成 | 通过 | 通过 | 完成 | 新增 ContextPackage 和 build_context_package，支持 evidence 数量限制、字符预算和 context_text 组装 |
| P2-011 | 前端 Evidence Panel | 完成 | 通过 | 通过 | 完成 | 新增 Retrieval Debug API 和前端 Evidence Panel，展示 query、source toggles、debug counters、vector disabled 提示和 evidence list |

## 4. 审核记录

| 日期 | 范围 | 结论 | 问题 | 处理 |
| --- | --- | --- | --- | --- |
| 2026-06-06 | Phase 2 详细设计 | 通过 | 不应提前进入 QA/Agent/Review | 设计只覆盖检索、图扩展、evidence 和前端 Evidence Panel |
| 2026-06-06 | P2-001 BM25 索引 | 通过 | 不应引入外部搜索依赖或提前做缓存持久化 | 采用纯 Python 内存 BM25；本阶段优先保证从 SQLite chunk 可构建、可检索、可测试 |
| 2026-06-06 | P2-002 embedding adapter | 通过 | 不应伪造向量或把 API key 暴露到前端/数据库 | 采用 OpenAI-compatible adapter；配置缺失显式抛出 disabled，测试使用 fake transport，不联网调用真实 embedding 服务 |
| 2026-06-06 | P2-003 Qdrant 写入 | 通过 | 不应引入 qdrant-client 新依赖、使用不兼容的 point id 或提前实现向量检索 | 采用标准库 REST transport；sha256 稳定 hash 转 UUID-compatible point id，检索留给 P2-004 |
| 2026-06-06 | P2-004 Qdrant 检索 | 通过 | 不应提前实现候选合并、重排或 Evidence 输出 | 仅返回 vector candidates；强制 repository_id filter，候选合并与 evidence 留给 P2-007 到 P2-009 |
| 2026-06-06 | P2-005 NetworkX 代码图 | 通过 | 不应提前实现图邻域查询或创建虚拟外部节点 | 只加载 DiGraph 节点和双端 relation 边；邻域查询留给 P2-006 |
| 2026-06-06 | P2-006 图邻域查询 | 通过 | 不应提前实现候选合并或 Evidence 输出 | 仅输出 graph_expand candidates；合并去重和 evidence 留给 P2-007 到 P2-009 |
| 2026-06-06 | P2-007 候选合并去重 | 通过 | 不应提前实现最终重排公式或 Evidence 输出 | 只合并来源、分数和 metadata；final score 留给 P2-008，Evidence 留给 P2-009 |
| 2026-06-06 | P2-008 轻量重排公式 | 通过 | 不应提前生成 Evidence 或调用 LLM reranker | 仅使用规则加权公式；Evidence 输出留给 P2-009 |
| 2026-06-06 | P2-009 Evidence 输出 | 通过 | 不应提前实现 Context Builder 或前端 Evidence Panel | 仅输出结构化 Evidence；上下文裁剪留给 P2-010，前端展示留给 P2-011 |
| 2026-06-06 | P2-010 Context Builder | 通过 | 不应提前实现前端 Evidence Panel 或 QA prompt | 仅组装 evidence context_text；前端展示留给 P2-011，QA prompt 留给 Phase 3 |
| 2026-06-06 | P2-011 前端 Evidence Panel | 通过 | 不应进入 Phase 3 QA/Agent 或 PR Review | 只实现 retrieval debug API 和 Evidence Panel；回答生成、Agent trace、PR Review 均未实现 |

## 5. 测试记录

| 日期 | 范围 | 命令/方式 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| 2026-06-06 | Phase 2 详细设计 | 文档审查 | 通过 | 尚未进入 P2 代码开发 |
| 2026-06-06 | Phase 2 基线验证 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | Phase 2 基线验证 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 25 个 Phase 1 回归测试通过 |
| 2026-06-06 | Phase 2 基线验证 | `npm run build` | 通过 | 前端构建和类型检查通过 |
| 2026-06-06 | P2-001 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-001 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 29 个测试通过，含 BM25 tokenizer、document、ranking、empty query 测试 |
| 2026-06-06 | P2-002 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-002 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 33 个测试通过，含 embedding 配置读取、disabled、请求参数、响应排序和维度校验 |
| 2026-06-06 | P2-003 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-003 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 38 个测试通过，含 Qdrant collection 创建、upsert payload、空仓库、维度不匹配和 API disabled 错误 |
| 2026-06-06 | P2-004 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-004 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 42 个测试通过，含 Qdrant search payload、repository filter、可选 filters、空 query/top_k、query embedding 数量异常和缺失 chunk_id 错误 |
| 2026-06-06 | P2-005 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-005 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 44 个测试通过，含 NetworkX DiGraph 节点、边、跳过缺 target relation 和缺失仓库空图 |
| 2026-06-06 | P2-006 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-006 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 47 个测试通过，含 callers、callees、same file、imports、graph expand 去重截断和缺失/无效输入 |
| 2026-06-06 | P2-007 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-007 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 50 个测试通过，含跨来源合并、重复来源最高分、matched terms 合并、sources 顺序和空输入 |
| 2026-06-06 | P2-008 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-008 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 53 个测试通过，含分数归一化、权重公式、file/symbol relevance、top_k、tie order、空输入和零分输入 |
| 2026-06-06 | P2-009 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-009 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 57 个测试通过，含 Evidence 字段、稳定 ID、snippet 截断、主 source、缺失 chunk 和跨仓库安全边界 |
| 2026-06-06 | P2-010 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-010 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 60 个测试通过，含 context 格式化、数量限制、字符预算截断、空输入和无效限制 |
| 2026-06-06 | P2-011 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 后端 lint 通过 |
| 2026-06-06 | P2-011 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 62 个测试通过，含 Retrieval Debug API ready/未 ready 分支 |
| 2026-06-06 | P2-011 | `npm run build` | 通过 | 前端构建与类型检查通过 |
| 2026-06-06 | P2-011 | Browser/HTTP UI smoke | 未完成 | Browser 工具未暴露；后台 backend dev server 未能稳定保持，已用后端 API 集成测试和前端 build 覆盖主要风险 |

## 6. 评测指标记录

Phase 2 先记录结构化检索指标，不做最终 QA 质量评测。

| 日期 | 仓库 | query | bm25_count | vector_count | graph_expand_count | final_evidence_count | latency_ms | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| - | - | - | - | - | - | - | - | 待开发后记录 |
| 2026-06-06 | BM25 unit fixtures | `import repository chunks` | 2 | 0 | 0 | 2 | - | BM25 可按 symbol/content/path token 召回并排序；vector/graph 尚未接入 |
| 2026-06-06 | Embedding unit fixtures | `alpha beta` | 0 | 2 | 0 | 0 | - | adapter 可生成并校验两条 OpenAI-compatible fake embedding；尚未写入 Qdrant |
| 2026-06-06 | Qdrant unit fixtures | `index repository chunks` | 0 | 2 | 0 | 0 | - | fake Qdrant 验证 2 条 chunk vector payload upsert；真实 Qdrant 连通性待配置后手动验证 |
| 2026-06-06 | Qdrant unit fixtures | `main flow` | 0 | 1 | 0 | 0 | - | fake Qdrant 验证 vector search 可返回 1 条 vector candidate；尚未进入 merge/evidence |
| 2026-06-06 | Code graph unit fixtures | `load code graph` | 0 | 0 | 1 | 0 | - | NetworkX DiGraph 可加载 2 个 chunk 节点和 1 条 calls 边；缺 target relation 被跳过 |
| 2026-06-06 | Code graph unit fixtures | `expand main neighbors` | 0 | 0 | 2 | 0 | - | graph expand 可按 same_file/calls/imports 权重去重并截断；尚未进入 candidate merge |
| 2026-06-06 | Candidate unit fixtures | `merge candidates` | 1 | 1 | 1 | 0 | - | BM25/vector/graph_expand 可按 chunk_id 合并为 1 条多来源 candidate；尚未计算 final score |
| 2026-06-06 | Rerank unit fixtures | `repository service` | 1 | 1 | 1 | 0 | - | 规则重排可输出 final_score=0.78 的 top candidate；尚未生成 evidence |
| 2026-06-06 | Evidence unit fixtures | `build evidences` | 1 | 1 | 1 | 1 | - | ranked candidate 可结合 SQLite chunk 生成 1 条带 snippet、line range 和稳定 evidence_id 的 evidence |
| 2026-06-06 | Context unit fixtures | `build context package` | 1 | 1 | 1 | 1 | - | Context Builder 可按 max_evidence_count/max_chars 生成 context_text 并标记 truncated |
| 2026-06-06 | Retrieval API fixtures | `main helper` | 1+ | 0 | 1+ | 1+ | - | Retrieval Debug API 可在 vector disabled 时返回 BM25/graph evidence 和 debug counts |

## 7. 下一步

Phase 2 已完成。下一步按 `docs/p0-plus-development-plan.md` 进入 Phase 3：带引用仓库问答。
