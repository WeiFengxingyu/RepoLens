# RepoLens V1 Phase 7 详细设计

## 1. 目标

Phase 7 的目标是把 P0+ 的 MCP-style Tool Layer 升级为可被 MCP client 调用的 RepoLens MCP Server，并补齐工具注册表、权限策略、审计日志和客户端 smoke。Phase 7 只暴露 RepoLens 已有只读能力，不进入 Phase 8 多 Agent、Phase 9 benchmark 或 Phase 10 发布包装。

## 2. 范围边界

### 2.1 In Scope

- 实现 FastAPI-adjacent MCP HTTP JSON-RPC endpoint。
- 支持 MCP 基础方法：`initialize`、`tools/list`、`tools/call`。
- 建立 Tool Registry，统一工具名、描述、input schema、权限级别和 handler。
- 建立权限策略：`allow`、`deny`、`disabled`、`confirm_required`、`read_only`、`safe_check`。
- 暴露只读工具：
  - `repository.list`
  - `repository.status`
  - `code.search`
  - `file.read_slice`
  - `symbol.context`
  - `diff.analyze`
- 暴露高阶工具：
  - `repository.ask`
  - `review.diff`
- 增强 `tool_calls` 审计字段：client、session、permission_policy、input_hash、output_hash。
- 前端增加 Tool Permissions Panel，展示工具权限和调用历史。
- 增加 MCP client smoke 测试，验证 list/call 和权限拒绝。

### 2.2 Out of Scope

- 不做远程公网 MCP 服务。
- 不做任意 shell、文件写入、代码修改、push 或外部平台写回。
- 不做 OAuth、多租户、用户级权限和 webhook。
- 不进入 Phase 8 多 Agent 协作、Phase 9 benchmark 或 Phase 10 演示包装。

## 3. Transport 选择

Phase 7 采用 FastAPI HTTP JSON-RPC endpoint：

```text
POST /api/mcp
```

请求/响应保持 JSON-RPC 2.0 结构：

```json
{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}
```

选择 HTTP endpoint 的原因：

- 与现有 FastAPI 测试、依赖注入、SQLite session 和 Docker Compose 更贴合。
- 不引入额外后台进程。
- 可用 TestClient 做 deterministic smoke。
- 后续仍可在此 registry 之上增加 stdio transport。

## 4. Tool Registry

核心对象：

- `MCPToolDefinition`
- `MCPToolContext`
- `MCPToolResult`
- `MCPToolRegistry`
- `MCPPermissionPolicy`

工具定义字段：

| 字段 | 说明 |
| --- | --- |
| `name` | MCP tool name |
| `description` | 工具说明 |
| `input_schema` | JSON Schema |
| `permission` | `read_only` 或 `safe_check` |
| `enabled` | 是否启用 |
| `handler` | 同步 handler，接收 db/settings/context/arguments |

## 5. 权限模型

默认策略：

| 工具 | 权限 | 默认决策 |
| --- | --- | --- |
| `repository.list` | read_only | allow |
| `repository.status` | read_only | allow |
| `code.search` | read_only | allow |
| `file.read_slice` | read_only | allow |
| `symbol.context` | read_only | allow |
| `diff.analyze` | read_only | allow |
| `repository.ask` | read_only | allow |
| `review.diff` | read_only | allow |
| `run_safe_static_check` | safe_check | disabled，除非配置启用 |

Phase 7 不实现需要人工确认的写操作。`confirm_required` 作为策略值保留，但本阶段没有默认工具使用它。

## 6. 审计设计

Phase 7 复用 `tool_calls` 表，并扩展字段：

- `client_name`
- `client_session_id`
- `permission_policy`
- `input_hash`
- `output_hash`

每个 `tools/call` 都写入审计记录。对于不需要 repository 的 `repository.list`，如果必须写 `repository_id`，使用请求中的 `repository_id` 时记录；否则 Phase 7 可先只返回结果并在 MCP response metadata 中记录未落库原因。为了保持闭环，主要审计要求覆盖带 repository 的工具。

审计 hash 使用 SHA-256，对 JSON canonical dump 计算，避免存储或暴露大 payload。

## 7. 工具行为

### 7.1 repository.list

输入：

```json
{}
```

输出 repository summary list。

### 7.2 repository.status

输入：

```json
{"repository_id":"..."}
```

输出 repository status、file/chunk/relation counts。

### 7.3 code.search

输入：

```json
{"repository_id":"...","query":"auth service","top_k":8,"use_bm25":true,"use_vector":true,"use_graph":true}
```

复用 `code_search`。

### 7.4 file.read_slice

输入：

```json
{"repository_id":"...","file_path":"src/app.py","start_line":1,"end_line":40}
```

复用 `read_file_slice`，必须通过 repository local_path 定位，保留路径穿越和敏感文件防护。

### 7.5 symbol.context

输入：

```json
{"repository_id":"...","symbol_name":"ReviewPanel","file_path":"src/app.tsx","max_neighbors":8}
```

复用 `get_symbol_context`。

### 7.6 diff.analyze

输入：

```json
{"repository_id":"...","diff_text":"diff --git ..."}
```

复用 `analyze_diff`。`repository_id` 用于审计归属，不改变 diff 解析结果。

### 7.7 repository.ask

输入：

```json
{"repository_id":"...","question":"Where is review logic?","top_k":8}
```

复用 `QAService`，同步生成 QA task。

### 7.8 review.diff

输入：

```json
{"repository_id":"...","diff_text":"diff --git ...","top_k":8}
```

复用 `ReviewService`，同步生成 Review task。

## 8. API 设计

新增：

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/mcp` | MCP JSON-RPC endpoint |
| `GET` | `/api/mcp/tools` | 前端读取 tool registry |
| `GET` | `/api/mcp/tool-calls` | 前端读取 MCP tool call audit history |

## 9. 前端设计

Workbench 增加 Tool Permissions Panel：

- 展示 tool name、permission、enabled、description。
- 展示最近 tool_calls，包括 tool_name、status、permission_decision、client、session、latency、created_at、error。
- 不提供写操作按钮。

## 10. 测试策略

| 测试文件 | 覆盖 |
| --- | --- |
| `test_phase7_mcp_registry.py` | registry、tool schemas、权限策略、禁用工具 |
| `test_phase7_mcp_api.py` | initialize、tools/list、tools/call、error mapping、audit |
| `test_phase7_mcp_security.py` | 路径穿越、敏感文件、禁用工具、超大输入 |
| 前端 build/type check | Tool Permissions Panel 类型和构建 |

## 11. 验收标准

- MCP client 能 `initialize`。
- MCP client 能 `tools/list`。
- MCP client 能调用 `code.search` 和 `file.read_slice` 并获得结构化结果。
- 权限策略可拒绝或禁用工具，拒绝原因可见。
- MCP tool call 能写入审计记录，包含 client/session/policy/input_hash/output_hash。
- 前端能展示工具权限和调用历史。
- `ruff check app`、`pytest app\tests`、`npm run build`、`npm exec tsc -- --noEmit`、`docker compose config` 通过。

