# RepoLens Phase 4 开发审核测试评测闭环记录

## 1. 文档用途

本文档用于记录 Phase 4 的开发、审核、测试和评测闭环。记录粒度与 `docs/p0-plus-development-plan.md` 中 P4-001 到 P4-014 对齐，确保每个任务都有开发、审核、测试和评测记录。

## 2. 当前状态

- 当前阶段：Phase 4 - PR Review、Multi-Agent 与 MCP-style 工具调用
- 当前状态：已完成 P4-DESIGN、P4-001 至 P4-014
- 开始日期：2026-06-06
- 依据文档：`docs/phase4-detailed-design.md`

## 3. 任务闭环记录

| 编号 | 任务 | 开发状态 | 审核状态 | 测试状态 | 评测/指标状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| P4-DESIGN | Phase 4 详细设计 | 完成 | 通过 | 文档审查通过 | 完成 | 新增 Phase 4 详细设计，覆盖 tool_calls、MCP-style 工具层、Diff 解析、工具权限、Review Agents、Review API、Review Panel、工具调用展示、安全、测试和验收 |
| P4-001 | 实现 tool_calls 表 | 完成 | 通过 | 通过 | 完成 | 新增 ToolCall 模型、枚举、关系和 round-trip 测试；保留 `AgentTrace.tool_calls` JSON 列，关系命名为 `tool_call_records` |
| P4-002 | 实现 analyze_diff 工具 | 完成 | 通过 | 通过 | 完成 | 新增纯解析服务，支持 unified diff、git header、hunk、added/modified/deleted/renamed、binary 和大小限制 |
| P4-003 | 实现 read_file_slice 工具 | 完成 | 通过 | 通过 | 完成 | 新增纯读取服务，限制仓库相对路径、符号链接、敏感文件、blocked dir、二进制、行数和字符数 |
| P4-004 | 实现 code_search 工具 | 完成 | 通过 | 通过 | 完成 | 新增纯工具包装，复用 Phase 2 混合检索并输出 Evidence-compatible 结果、debug 和 warnings |
| P4-005 | 实现 get_symbol_context 工具 | 完成 | 通过 | 通过 | 完成 | 新增纯工具服务，基于 code_chunks 和现有 NetworkX 图返回 symbol、入边、出边和 same-file 邻居 |
| P4-006 | 实现 run_safe_static_check 占位 | 完成 | 通过 | 通过 | 完成 | 默认 disabled；显式开启后仅校验白名单，仍不执行 shell 或 checker |
| P4-007 | 实现 Diff 到 symbol 映射 | 完成 | 通过 | 通过 | 完成 | 新增 diff mapper，按 changed line 命中最小范围 chunk，记录 unmatched_lines，并写入 `changed_by` 关系 |
| P4-008 | 实现 Review API | 完成 | 通过 | 通过 | 完成 | 新增 Review schema/service/router；P4-009 到 P4-012 完成后升级为同步执行 Phase 4 Review 流水线并返回报告 |
| P4-009 | 实现 Risk Reviewer Agent | 完成 | 通过 | 通过 | 完成 | 新增 `review_risks`，支持 chat JSON 分支和规则 fallback，输出风险草稿、diff_refs、evidence_ids 和 impacted_symbols |
| P4-010 | 实现 Review Verifier | 完成 | 通过 | 通过 | 完成 | 新增 `verify_review_risks`，校验 evidence/diff 支撑、location 来源，并降级 diff-only high risk |
| P4-011 | 实现 Test Suggestion Agent | 完成 | 通过 | 通过 | 完成 | 新增 `suggest_review_tests`，基于 verified risks 和 impacted_symbols 生成 unit/integration/regression 建议 |
| P4-012 | 实现 Review Report Writer | 完成 | 通过 | 通过 | 完成 | 新增 `write_review_report`，输出结构化 JSON 和 Markdown，仅包含 verified risks |
| P4-013 | 实现 Review Panel | 完成 | 通过 | 通过 | 完成 | 前端支持 diff 输入、top_k、BM25/vector/graph/static check toggles、风险报告、测试建议、引用和 Markdown 报告展示 |
| P4-014 | 实现工具调用展示 | 完成 | 通过 | 通过 | 完成 | Review Panel 和 Trace Panel 展示 tool_name、status、permission_decision、latency、input/output summary 和 error |

## 4. 审核记录

| 日期 | 范围 | 结论 | 问题 | 处理 |
| --- | --- | --- | --- | --- |
| 2026-06-06 | Phase 4 详细设计 | 通过 | 不应进入 Phase 5 评测部署；不应实现完整 MCP Server 或真实命令执行 | 设计限定为 PR Review 闭环、MCP-style 内部工具层和工具调用 trace；run_safe_static_check 默认 disabled |
| 2026-06-06 | P4-001 tool_calls 模型 | 通过 | 首次实现将 `AgentTrace.tool_calls` 关系与 Phase 3 JSON 文本列同名，导致 AgentTrace 构造和 QA API 回归失败 | 将关系改名为 `tool_call_records`，保留 `tool_calls` 文本列；重新运行后端检查和完整测试通过 |
| 2026-06-06 | P4-002 analyze_diff 工具 | 通过 | 首次测试从 `app.services.tools` 导入大小限制常量失败，说明统一入口导出不完整 | 补充导出 `DIFF_MAX_CHARS` 和 `HUNK_MAX_LINES`；针对性测试和全量后端测试通过 |
| 2026-06-06 | P4-003 read_file_slice 工具 | 通过 | 需要避免复用 Scanner 后遗漏工具级路径权限；读取工具必须独立拒绝绝对路径、路径穿越、符号链接和敏感文件 | 实现独立 `FileSliceError`、路径解析、symlink/blocked dir/sensitive file/binary 检查和截断逻辑 |
| 2026-06-06 | P4-004 code_search 工具 | 通过 | 工具包装不能重写 Phase 2 检索逻辑，也不能因默认无 embedding 配置阻断 BM25/graph | 复用 `retrieve_repository`，vector disabled 转为 warning；新增输入校验和 Evidence-compatible 输出 |
| 2026-06-06 | P4-005 get_symbol_context 工具 | 通过 | 不能为 Review 场景虚构外部 symbol，也不能在同名 symbol 时无提示地误选 | 仅基于 `code_chunks` 和现有代码图返回真实节点；同名 symbol 无 file_path 时返回 warning |
| 2026-06-06 | P4-006 run_safe_static_check 占位 | 通过 | 不应因为“static check”名称引入真实命令执行，也不应默认开启 | 新增默认关闭配置；工具只返回 disabled/denied/completed placeholder，所有分支 `executed=false` |
| 2026-06-06 | P4-007 Diff 到 symbol 映射 | 通过 | 多层 chunk 命中时不能被 file-level chunk 覆盖；未命中时不能伪造 symbol；重复 task 写入不能堆积旧 changed_by | 选择最小范围 chunk；未命中记录 `unmatched_lines`；写入前按 task_id 删除旧 `changed_by` metadata |
| 2026-06-06 | P4-008 Review API | 通过 | 不应提前实现 P4-009 到 P4-012 的 agent/report 逻辑；API 需要先稳定 task contract | 仅创建 pending review task 和空报告结构；保留 tool_calls/traces 字段供后续任务填充 |
| 2026-06-06 | P4-009 Risk Reviewer Agent | 通过 | 风险草稿不能成为最终报告；fallback 不能脱离 diff/evidence 自由发挥 | `review_risks` 仅输出 draft；fallback 风险必须带 diff_refs 或 evidence_ids，默认 conservative severity |
| 2026-06-06 | P4-010 Review Verifier | 通过 | Verifier 不能补写新事实；无证据风险不能进入 verified risk | 仅过滤/降级现有 draft；要求有效 evidence_id 或 diff_refs，并检查 location 来源 |
| 2026-06-06 | P4-011 Test Suggestion Agent | 通过 | 测试建议不能实际运行测试或探测环境；重复风险不能生成重复建议 | 只生成结构化建议；按 target/test_type 去重并合并 related_risk_titles |
| 2026-06-06 | P4-012 Review Report Writer | 通过 | Report Writer 不能把 missing/unsupported risks 写进最终报告；Markdown 与 JSON 需字段一致 | 只消费 verified risks；风险 payload 移除 diff_refs；citations 只保留被风险引用的 evidence |
| 2026-06-08 | P4-008 Review API 收束 | 通过 | 如果 Review API 仍停在 pending 空报告，P4-013 Review Panel 无法形成演示闭环 | 在不引入后台队列、完整 MCP Server 或真实命令执行的前提下，将已完成的 P4-002/P4-007/P4-009/P4-012 串成同步 Review 流水线并记录 tool_calls/traces |
| 2026-06-08 | P4-013 Review Panel | 通过 | 需要避免变成营销页或脱离现有工作台风格；长 diff 和报告内容不能撑破布局 | 复用现有工作台卡片风格，新增 diff textarea、检索选项、static check toggle、风险/测试/引用/Markdown 展示和失败态 |
| 2026-06-08 | P4-014 工具调用展示 | 通过 | Trace 中原始 JSON 可读性不足；工具调用必须展示权限和耗时 | 新增 Tool Calls Panel，并将 Trace tool_calls 渲染为结构化行，展示 tool_name/status/permission_decision/latency/input/output/error |

## 5. 测试记录

| 日期 | 范围 | 命令/方式 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| 2026-06-06 | Phase 4 详细设计 | 文档审查 | 通过 | 尚未进入 P4 代码开发 |
| 2026-06-06 | P4-001 tool_calls 模型 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-001 tool_calls 模型 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 93 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-002 analyze_diff 工具 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\tools app\\tests\\test_phase4_diff_analyzer.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-002 analyze_diff 工具 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_diff_analyzer.py` | 通过 | 6 passed |
| 2026-06-06 | P4-002 analyze_diff 工具 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-002 analyze_diff 工具 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 99 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-003 read_file_slice 工具 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\tools app\\tests\\test_phase4_file_reader.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-003 read_file_slice 工具 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_file_reader.py` | 通过 | 6 passed |
| 2026-06-06 | P4-003 read_file_slice 工具 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-003 read_file_slice 工具 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 105 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-004 code_search 工具 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\tools app\\tests\\test_phase4_code_search.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-004 code_search 工具 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_code_search.py` | 通过 | 4 passed |
| 2026-06-06 | P4-004 code_search 工具 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-004 code_search 工具 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 109 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-005 get_symbol_context 工具 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\tools app\\tests\\test_phase4_symbol_context.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-005 get_symbol_context 工具 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_symbol_context.py` | 通过 | 5 passed |
| 2026-06-06 | P4-005 get_symbol_context 工具 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-005 get_symbol_context 工具 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 114 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-006 run_safe_static_check 占位 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\services\\tools app\\tests\\test_phase4_static_check.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-006 run_safe_static_check 占位 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_static_check.py` | 通过 | 4 passed |
| 2026-06-06 | P4-006 run_safe_static_check 占位 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-006 run_safe_static_check 占位 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 118 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-007 Diff 到 symbol 映射 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\models\\code_relation.py app\\services\\review app\\services\\graph\\code_graph.py app\\tests\\test_phase4_diff_mapper.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-007 Diff 到 symbol 映射 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_diff_mapper.py` | 通过 | 5 passed |
| 2026-06-06 | P4-007 Diff 到 symbol 映射 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 123 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-007 Diff 到 symbol 映射 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-008 Review API | `.\\.venv\\Scripts\\python.exe -m ruff check app\\api\\reviews.py app\\schemas\\review.py app\\services\\review app\\tests\\test_phase4_review_api.py app\\main.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-008 Review API | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_review_api.py` | 通过 | 3 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-008 Review API | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 126 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-008 Review API | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-009 Risk Reviewer Agent | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\review app\\tests\\test_phase4_risk_reviewer_agent.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-009 Risk Reviewer Agent | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_risk_reviewer_agent.py` | 通过 | 4 passed |
| 2026-06-06 | P4-009 Risk Reviewer Agent | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-009 Risk Reviewer Agent | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 130 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-010 Review Verifier | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\review app\\tests\\test_phase4_review_verifier_agent.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-010 Review Verifier | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_review_verifier_agent.py` | 通过 | 4 passed |
| 2026-06-06 | P4-010 Review Verifier | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-010 Review Verifier | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 134 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-011 Test Suggestion Agent | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\review app\\tests\\test_phase4_test_suggestion_agent.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-011 Test Suggestion Agent | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_test_suggestion_agent.py` | 通过 | 4 passed |
| 2026-06-06 | P4-011 Test Suggestion Agent | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-011 Test Suggestion Agent | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 138 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-06 | P4-012 Review Report Writer | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\review app\\tests\\test_phase4_review_report_writer.py` | 通过 | Ruff 无问题 |
| 2026-06-06 | P4-012 Review Report Writer | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_review_report_writer.py` | 通过 | 3 passed |
| 2026-06-06 | P4-012 Review Report Writer | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-06 | P4-012 Review Report Writer | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 141 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P4-008 Review API 收束 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\review\\service.py app\\api\\reviews.py app\\tests\\test_phase4_review_api.py` | 通过 | Ruff 无问题 |
| 2026-06-08 | P4-008 Review API 收束 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase4_review_api.py` | 通过 | 3 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P4-013/P4-014 前端 | `npm run build` | 通过 | Next.js build、lint 和 TypeScript 校验通过 |
| 2026-06-08 | Phase 4 最终后端 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | Phase 4 最终后端 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 141 passed，1 个 Starlette/httpx deprecation warning |

## 6. 评测指标记录

Phase 4 先记录 Review smoke 样例，不建设完整 50 条评测集。完整评测留给 Phase 5。

| 日期 | 样例 | 工具调用 | 风险数 | citation_count | verifier_result | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-06 | tool_calls round-trip | 1 | - | - | 模型完整性通过 | 覆盖 task/repository/trace 关系、permission/status、payload/error/latency 字段 |
| 2026-06-06 | modified/added/deleted/renamed/binary diff | - | - | - | diff 解析通过 | 覆盖文件级 change_type、hunk 行号、汇总计数、to_dict 输出和大小限制 |
| 2026-06-06 | file slice safety | - | - | - | 读取边界通过 | 覆盖仓库相对路径、路径穿越拒绝、敏感文件拒绝、blocked dir 拒绝、二进制拒绝和截断；实现包含符号链接拒绝逻辑 |
| 2026-06-06 | code_search BM25/graph fallback | 1 | - | - | 检索包装通过 | 覆盖 Evidence-compatible 输出、debug 计数、vector disabled warning、空仓库和输入校验 |
| 2026-06-06 | symbol context neighborhood | - | - | - | 图邻域通过 | 覆盖目标 symbol、callers、callees、imports、same-file 去重、同名 symbol file_path 过滤和 max_neighbors |
| 2026-06-06 | static check disabled/whitelist | 1 | - | - | 权限占位通过 | 覆盖默认 disabled、白名单 allow placeholder、非白名单 deny、路径校验和 `executed=false` |
| 2026-06-06 | diff changed lines to symbols | 2 | - | - | 映射通过 | 覆盖 added/removed 行映射、最小范围 chunk、file-level fallback、unmatched_lines、changed_by 去重写入 |
| 2026-06-06 | review task API smoke | - | 0 | 0 | pending contract 通过 | 覆盖创建 Review task、查询 Review response、未 ready 仓库拒绝、空 diff 422 和缺失 task 404 |
| 2026-06-06 | risk reviewer fallback/chat | - | 1 | 1 | 风险草稿通过 | 覆盖 mapped symbol 风险、unmatched file 风险、chat JSON 分支和 max_risks |
| 2026-06-06 | review verifier evidence/diff support | - | 1 | 1 | 校验通过 | 覆盖有效 evidence、diff-only high 降级、unsupported risk 移除和 location 来源校验 |
| 2026-06-06 | test suggestion generation | - | 1 | 1 | 建议通过 | 覆盖 unit/integration 分类、target 去重、related_risk_titles 合并和空输入 warning |
| 2026-06-06 | review report JSON/Markdown | - | 1 | 1 | 报告通过 | 覆盖结构化 JSON、Markdown、空报告和 citation 过滤 |
| 2026-06-08 | review API completed report smoke | 2 | 1 | 0 | completed report 通过 | POST Review 返回 completed、summary、risk_level、risks、markdown、tool_calls 和 traces；样例仓库无 chunk，按 unmatched file 生成 conservative risk |
| 2026-06-08 | Review Panel build smoke | - | - | - | 前端类型/构建通过 | 覆盖 Review 类型、API helper、diff 输入、报告展示、Tool Calls Panel 和 Trace tool call 结构化展示 |
| 2026-06-08 | static check 默认关闭展示 | 1 | - | - | disabled contract 保留 | run_safe_static_check 仍为默认 disabled/no-execution placeholder，未引入真实命令执行 |

## 7. 下一步

Phase 4 已完成。下一步按 `docs/p0-plus-development-plan.md` 进入 Phase 5：评测、部署与简历包装。
