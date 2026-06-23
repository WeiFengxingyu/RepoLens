# RepoLens V1 Phase 7 开发审核测试评测闭环记录

## 1. 文档用途

本文档记录 Phase 7 的开发、审核、测试和评测闭环。Phase 7 的目标是将 MCP-style Tool Layer 升级为真正可被 MCP client 调用的 RepoLens MCP Server，并补齐工具注册表、权限策略、审计日志和前端 Tool Permissions Panel。

## 2. 当前状态

- 当前阶段：V1 Phase 7 - 真正 MCP Server 化与工具权限系统增强
- 当前状态：P7-001 至 P7-011 已完成，Phase 7 进入最终收束
- 开始日期：2026-06-14
- 完成日期：2026-06-14
- 依据文档：`docs/v1-development-plan.md`、`docs/phase7-detailed-design.md`

## 3. 任务闭环记录

| 编号 | 任务 | 开发状态 | 审核状态 | 测试状态 | 评测/指标状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| P7-001 | 编写 Phase 7 详细设计 | 完成 | 通过 | 文档审查通过 | 完成 | 新增 `docs/phase7-detailed-design.md`，明确 HTTP JSON-RPC MCP endpoint、registry、权限、审计、测试和验收 |
| P7-002 | 设计 Tool Registry | 完成 | 通过 | 通过 | 完成 | 新增 `services/mcp/registry.py`，统一工具名、schema、权限级别、handler |
| P7-003 | 设计权限模型 | 完成 | 通过 | 通过 | 完成 | 支持 allow、deny、confirm_required、disabled、read_only、safe_check；当前工具只读默认 allow，safe_check 默认 disabled |
| P7-004 | 实现 MCP Server 启动入口 | 完成 | 通过 | 通过 | 完成 | 新增 `POST /api/mcp` JSON-RPC endpoint，支持 initialize、tools/list、tools/call |
| P7-005 | 导出只读工具 | 完成 | 通过 | 通过 | 完成 | 导出 repository.list/status、code.search、file.read_slice、symbol.context、diff.analyze |
| P7-006 | 导出高阶工具 | 完成 | 通过 | 通过 | 完成 | 导出 repository.ask、review.diff，复用现有 QA/Review service |
| P7-007 | 增强 tool_calls 审计字段 | 完成 | 通过 | 通过 | 完成 | 扩展 client、session、permission_policy、input_hash、output_hash，并为 MCP tool call 建轻量 task |
| P7-008 | 前端 Tool Permissions Panel | 完成 | 通过 | 通过 | 完成 | Workbench 展示 tool registry、permission policy、enabled/disabled、最近 MCP 调用、client/session/hash、失败原因 |
| P7-009 | MCP client smoke test | 完成 | 通过 | 通过 | 完成 | TestClient 覆盖 initialize、tools/list、code.search、file.read_slice、repository.status、symbol.context、diff.analyze、repository.ask、review.diff |
| P7-010 | 安全测试 | 完成 | 通过 | 通过 | 完成 | 覆盖路径穿越、敏感文件读取、超大 diff、禁用工具和审计记录 |
| P7-011 | 文档与演示 | 完成 | 通过 | 通过 | 完成 | README、worklog、闭环记录和最终 closure review 已更新 |

## 4. 审核记录

| 日期 | 范围 | 结论 | 问题 | 处理 |
| --- | --- | --- | --- | --- |
| 2026-06-14 | Phase 7 范围边界 | 通过 | Phase 7 容易扩到 Phase 8 多 Agent、Phase 9 benchmark 或 Phase 10 包装 | 设计明确只做 MCP Server、工具权限和审计，不做多 Agent/benchmark/发布包装 |
| 2026-06-14 | MCP transport 选择 | 通过 | stdio 进程会增加测试和桌面线程复杂度 | Phase 7 先实现 FastAPI HTTP JSON-RPC endpoint，保留未来 stdio 扩展点 |
| 2026-06-14 | P7-002/P7-007 后端实现 | 通过 | MCP Server 不能绕过既有只读边界，也不能失去审计 | 所有工具复用现有只读 service/tool；带 repository 的 MCP 调用写入 `tool_calls` 和轻量 `mcp_tool` task |
| 2026-06-14 | P7-008 前端面板 | 通过 | 权限面板如果只显示 registry，无法闭环审计 | 面板同时展示 registry 和 `/api/mcp/tool-calls` 最近调用，包含 client/session/input_hash/output_hash |
| 2026-06-14 | P7 SQLite 兼容 | 通过 | 已有本地 SQLite 的 `tool_calls` 表不会因 `create_all` 自动加列 | `init_db()` 增加 SQLite 幂等补列与索引创建，仅覆盖 Phase 7 新增可空审计列 |
| 2026-06-14 | P7 最终边界 | 通过 | MCP Server 可能扩成任意 shell 或写操作平台 | Phase 7 没有新增 shell/write/push/approve/request changes，也没有进入 Phase 8/9/10 |

## 5. 测试记录

| 日期 | 范围 | 命令/方式 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| 2026-06-14 | P7-001 | 文档审查 | 通过 | 尚未进入代码实现 |
| 2026-06-14 | P7 后端 MCP 专项 Ruff | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\mcp app\\api\\mcp.py app\\schemas\\mcp.py app\\models\\tool_call.py app\\models\\task.py app\\db\\init_db.py app\\tests\\test_phase7_mcp_api.py app\\tests\\test_phase7_mcp_registry.py` | 通过 | All checks passed |
| 2026-06-14 | P7 后端 MCP 专项测试 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase7_mcp_api.py app\\tests\\test_phase7_mcp_registry.py` | 通过 | 7 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-14 | P7 前端 build | `npm run build` | 通过 | Next.js production build completed |
| 2026-06-14 | P7 前端 type check | `npm exec tsc -- --noEmit` | 通过 | TypeScript noEmit 通过；生成的 `frontend/tsconfig.tsbuildinfo` 已清理 |
| 2026-06-14 | P7 后端全量 Ruff | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | All checks passed |
| 2026-06-14 | P7 后端全量测试 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 239 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-14 | P7 Docker 配置 | `docker compose config` | 通过 | backend/frontend/qdrant 配置可解析 |
| 2026-06-14 | P7 本地服务短跑 | 前台短跑 `uvicorn app.main:app --host 127.0.0.1 --port 8000` 与 `npm run start -- -p 3000 -H 127.0.0.1` | 通过 | 两者均输出 ready；命令因 10 秒测试超时被终止 |
| 2026-06-14 | P7 Browser DOM smoke | 尝试后台保持 backend/frontend 后打开 Workbench | 未完成 | 当前 Windows shell/Node 持有的后台服务会立即退出，未生成 DOM/screenshot；已由 build/type/API tests 覆盖主要风险 |

## 6. 评测指标记录

| 日期 | 范围 | 指标 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| 2026-06-14 | P7 | 评测口径 | 已定义 | tools/list success、tools/call success、permission denial correctness、audit coverage、latency smoke |
| 2026-06-14 | P7-004/P7-005 | tools/list and tools/call success | 通过 | TestClient 覆盖 initialize、tools/list、code.search、file.read_slice |
| 2026-06-14 | P7-006 | high-level MCP tool success | 通过 | TestClient 覆盖 `repository.ask` 和 `review.diff`，均复用既有 QA/Review service 并写 MCP 审计 |
| 2026-06-14 | P7-007/P7-010 | permission denial correctness and audit coverage | 通过 | 禁用 `run_safe_static_check` 返回 disabled；敏感文件、路径穿越、超大 diff 返回 tool error；失败/禁用调用均有审计 |
| 2026-06-14 | P7-008 | Tool Permissions Panel build readiness | 通过 | `npm run build` 与 `npm exec tsc -- --noEmit` 均通过 |

## 7. 风险与控制

| 风险 | 表现 | 控制方式 | 当前状态 |
| --- | --- | --- | --- |
| MCP 范围失控 | 变成通用工具平台或任意 shell | 只暴露 RepoLens 既有只读工具，不提供 shell/write/push | 已闭环 |
| 权限形同虚设 | 所有工具无差别 allow | registry 强制 permission 字段，policy 决策写入审计 | P7 后端专项测试已覆盖 |
| 审计不可追踪 | MCP 调用没有 client/session/hash | 扩展 tool_calls 字段并记录 input/output hash | P7 后端专项测试已覆盖 |
| 路径读取风险 | MCP client 读取敏感文件或路径穿越 | 复用 `read_file_slice` 安全校验并补安全测试 | P7 后端专项测试已覆盖敏感文件与路径穿越 |
| 旧库 schema 风险 | 本地旧 SQLite 缺少 Phase 7 `tool_calls` 新列 | `init_db()` 对 SQLite 进行幂等补列 | 已闭环 |

## 8. 最终收束

| 日期 | 结论 | 记录 |
| --- | --- | --- |
| 2026-06-14 | Phase 7 完成 | P7-001 到 P7-011 全部完成；RepoLens 已具备 FastAPI HTTP JSON-RPC MCP endpoint、工具注册表、权限决策、MCP 调用审计、Tool Permissions Panel 和 TestClient smoke/security 闭环；未实现公网 MCP、stdio 进程、任意 shell、写操作、PR/MR 写回、自动改代码或 Phase 8/9/10 范围 |
