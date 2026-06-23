# RepoLens V1 Phase 7 最终收束审查

## 1. 审查目的

本文档用于正式收口 RepoLens V1 Phase 7：真正 MCP Server 化与工具权限系统增强。审查只覆盖 `docs/v1-development-plan.md` 与 `docs/phase7-detailed-design.md` 中定义的 Phase 7，不把 Phase 8 多 Agent 协作、Phase 9 benchmark、Phase 10 展示包装纳入本次验收。

## 2. 最终结论

Phase 7 已完成。RepoLens 已从 P0+ 的 MCP-style Tool Layer 升级为本地 FastAPI HTTP JSON-RPC MCP endpoint，具备基础 MCP 方法、工具注册表、权限策略、审计字段、前端 Tool Permissions Panel、MCP client smoke 和安全测试闭环。

## 3. 完成范围

| 范围 | 状态 | 证据 |
| --- | --- | --- |
| `POST /api/mcp` JSON-RPC endpoint | 完成 | 支持 `initialize`、`tools/list`、`tools/call` |
| Tool Registry | 完成 | `backend/app/services/mcp/registry.py` 统一 name、description、schema、permission_policy、enabled、handler |
| 权限策略 | 完成 | `read_only` 默认 allow，`safe_check` 默认 disabled，保留 deny/confirm_required 决策值 |
| 只读工具 | 完成 | `repository.list`、`repository.status`、`code.search`、`file.read_slice`、`symbol.context`、`diff.analyze` |
| 高阶工具 | 完成 | `repository.ask`、`review.diff` 复用既有 QA/Review service |
| 审计字段 | 完成 | `tool_calls` 记录 client/session/permission_policy/input_hash/output_hash |
| 前端面板 | 完成 | Workbench 展示 MCP registry、permission、enabled 状态、最近调用、hash 和失败原因 |
| 安全边界 | 完成 | 禁用工具、敏感文件、路径穿越、超大 diff 均有 MCP 层测试 |
| 旧 SQLite 兼容 | 完成 | `init_db()` 对 Phase 7 新增 `tool_calls` 列做幂等补列 |

## 4. 验证结果

| 验证项 | 命令/方式 | 结果 |
| --- | --- | --- |
| Phase 7 专项 Ruff | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\mcp app\\api\\mcp.py app\\schemas\\mcp.py app\\models\\tool_call.py app\\models\\task.py app\\db\\init_db.py app\\tests\\test_phase7_mcp_api.py app\\tests\\test_phase7_mcp_registry.py` | 通过 |
| Phase 7 专项测试 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase7_mcp_api.py app\\tests\\test_phase7_mcp_registry.py` | 7 passed，1 个 Starlette/httpx deprecation warning |
| 后端全量 Ruff | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 |
| 后端全量测试 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 239 passed，1 个 Starlette/httpx deprecation warning |
| 前端构建 | `npm run build` | 通过 |
| 前端类型检查 | `npm exec tsc -- --noEmit` | 通过 |
| Docker Compose 配置 | `docker compose config` | 通过 |
| 本地服务短跑 | 前台短跑 backend/frontend start 命令 | 通过，均输出 ready 后因测试超时终止 |
| Browser DOM smoke | 尝试后台保持服务并打开 Workbench | 未完成，当前环境后台服务进程会立即退出；未生成截图或 DOM 证据 |

## 5. 安全审查

| 风险 | Phase 7 处理 |
| --- | --- |
| MCP client 触发写操作 | Phase 7 不暴露写工具，不写回 PR/MR，不 approve/request changes，不 push |
| 任意 shell 执行 | 未提供 shell 工具；`run_safe_static_check` 仍 disabled by default |
| 路径穿越或敏感文件读取 | 复用 `read_file_slice` 安全校验，并由 MCP API 测试覆盖 |
| 超大输入拖垮 Review | `ReviewCreateRequest` 与 diff analyzer 限制 diff size，MCP 测试覆盖超大 diff |
| 审计缺失 | repository-scoped MCP tool call 会写入 `mcp_tool` task 与 `tool_calls` 审计 |
| 旧本地 SQLite 表结构不兼容 | `init_db()` 幂等补齐新增可空列与索引 |

## 6. 非目标确认

- 未实现公网 MCP 服务。
- 未实现 stdio MCP 进程。
- 未实现任意 shell 或命令执行。
- 未实现自动代码修改、patch application 或 push。
- 未实现 PR/MR comment、approve、request changes、merge、close。
- 未进入 Phase 8 真正多 Agent 协作。
- 未进入 Phase 9 benchmark/metrics 平台。
- 未进入 Phase 10 展示包装。

## 7. 最终判断

Phase 7 可以视为完成并收束。下一步若继续 V1，应从 Phase 8 开始，并在进入前重新编写 Phase 8 详细设计与闭环记录；不应把 Phase 8/9/10 的工作倒填进 Phase 7。
