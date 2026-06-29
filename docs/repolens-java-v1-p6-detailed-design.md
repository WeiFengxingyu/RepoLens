# RepoLens-Java V1-P6 Detailed Design: MCP Tool Registry, Permission Guard, And Audit

## 1. Phase Goal

V1-P6 turns the existing Java-side repository intelligence capabilities into a local, auditable MCP-style tool layer. The phase does not introduce a separate project directory. It continues to evolve `backend-java/` and `frontend/` so the same product can expose:

- tool discovery through `tools/list`
- tool invocation through `tools/call`
- repository-scoped read-only permission checks
- durable tool-call audit records visible to the frontend

The implementation is intentionally local-first and deterministic. It prepares the architecture for a later full MCP transport integration while keeping P6 independently demoable and testable.

## 2. Scope

### 2.1 In Scope

| Capability | Description |
| --- | --- |
| Tool Registry | Java registry for tool name, description, JSON schema, permission policy, enabled flag, and handler |
| `GET /api/mcp/tools` | Frontend-friendly tool discovery endpoint |
| `POST /api/mcp/tools/call` | HTTP bridge for local MCP-style tool calls |
| `GET /api/mcp/tool-calls` | Recent audit records for frontend panel and interview demo |
| Read-only tool execution | Search, file read, symbol search, graph neighbors, and review-diff tools |
| Permission Guard | Repository scope, path traversal defense, sensitive file deny list, argument bounds |
| Audit Log | Status, permission decision, hashes, summaries, latency, client/session metadata |
| Frontend Contract | TypeScript request/response types and API client function |

### 2.2 Out Of Scope

| Item | Reason |
| --- | --- |
| External MCP stdio/SSE server | P6 focuses on local HTTP bridge; transport adapter can be added later without changing registry |
| Write tools | Resume project should emphasize safe repository analysis, not mutation |
| Shell execution tools | Execution-class tools are deferred and should remain disabled by default |
| OAuth/multi-user auth | Current product is local single-user; audit schema reserves client/session fields |
| Real LLM tool routing | P6 exposes deterministic tools; later phases can let an agent choose tools dynamically |

## 3. Tool Contract

### 3.1 Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/mcp/tools` | Return enabled and disabled tool metadata |
| POST | `/api/mcp/tools/call` | Execute one tool by name with JSON arguments |
| GET | `/api/mcp/tool-calls?limit=50` | Return latest audit records |

The request body for `tools/call` is:

```json
{
  "name": "repolens.search",
  "arguments": {
    "repository_id": "repo_xxx",
    "query": "authentication filter",
    "top_k": 5
  },
  "client_name": "workbench",
  "client_session_id": "local-demo"
}
```

The response body is:

```json
{
  "id": "mcp_call_xxx",
  "tool_name": "repolens.search",
  "status": "completed",
  "permission_decision": "allow",
  "result": {},
  "error_message": null,
  "audit": {}
}
```

### 3.2 Tool List

| Tool | Permission | Input | Output |
| --- | --- | --- | --- |
| `repolens.search` | `read_only:repository` | `repository_id`, `query`, `top_k`, retrieval flags | P3 `RetrievalResponse` |
| `repolens.read_file` | `read_only:repository_file` | `repository_id`, `file_path`, optional `start_line`, `end_line` | bounded text slice |
| `repolens.find_symbol` | `read_only:code_graph` | `repository_id`, `query` | P2 symbol list |
| `repolens.graph_neighbors` | `read_only:code_graph` | `repository_id`, `symbol_id` | P2 neighbor response |
| `repolens.review_diff` | `read_only:analysis` | `repository_id`, `diff_text`, retrieval flags | P5 review response |
| `repolens.safe_static_check` | `disabled:execution_class` | reserved | disabled response |

The disabled tool is intentionally included so the frontend and interview demo can show the boundary between read-only analysis tools and execution-class tools.

## 4. Backend Design

### 4.1 Package Layout

```text
backend-java/src/main/java/com/repolens/mcp
  api/
  api/dto/
  application/
  domain/
  infrastructure/
```

### 4.2 Main Classes

| Class | Responsibility |
| --- | --- |
| `McpController` | REST endpoints for tools/list, tools/call, audit list |
| `McpToolRegistry` | Registers metadata and dispatch names to handlers |
| `McpToolService` | Orchestrates validation, permission, execution, audit |
| `McpPermissionGuard` | Validates repository scope, disabled tools, path and size bounds |
| `McpAuditService` | Creates durable audit records with hashes and summaries |
| `McpToolCallAuditEntity` | JPA entity for `mcp_tool_call_audits` |
| `McpToolCallAuditJpaRepository` | Recent audit query |

### 4.3 Persistence

Migration `V8__add_v1_mcp_audit.sql` adds:

```text
mcp_tool_call_audits
  id
  task_id
  repository_id
  tool_name
  status
  permission_decision
  permission_policy
  client_name
  client_session_id
  input_hash
  output_hash
  input_summary
  output_summary
  latency_ms
  error_message
  created_at
  completed_at
```

`task_id` is generated for every MCP call to keep the audit shape compatible with frontend workbench panels. For tools that create their own domain task, such as `repolens.review_diff`, the MCP audit still has a separate MCP task id and stores the produced review task id in output summary/result.

## 5. Permission Model

### 5.1 Decisions

| Decision | Meaning |
| --- | --- |
| `allow` | The request is repository-scoped, tool is enabled, and arguments are bounded |
| `deny` | The tool is known but violates repository/path/input constraints |
| `disabled` | The tool is registered but execution-class or intentionally unavailable |

### 5.2 Guard Rules

- Every enabled tool requires `repository_id`.
- `repository_id` must reference an existing READY repository.
- `read_file` requires a relative path that stays inside repository root after normalization.
- `read_file` denies absolute paths, `..`, `.env`, key/certificate extensions, and secret-looking filenames.
- `read_file` caps output to 200 lines.
- `search` and `review_diff` cap `top_k` to 20.
- `review_diff` caps input length to 20,000 characters.
- Unknown tools are recorded as denied, not executed.

## 6. Audit Design

Each call records:

- immutable call id and generated task id
- repository id if available
- tool name and permission policy
- `status`: `completed`, `failed`, `denied`, or `disabled`
- `permission_decision`: `allow`, `deny`, or `disabled`
- SHA-256 hashes of normalized input and output payloads
- short input/output summaries for UI display
- client name and session id
- latency in milliseconds
- error message when denied or failed

This gives the project an interview-visible safety story: a tool call is not only functional, it is explainable and auditable.

## 7. Frontend Design

P6 keeps frontend changes small because the workbench already has MCP registry and audit types. This phase adds:

- `McpToolCallRequest`
- `McpToolCallResponse`
- `callMcpTool(payload)`

The endpoint is enough for a future MCP panel to invoke tools without changing backend contracts.

## 8. Testing Plan

| Test | Expected Result |
| --- | --- |
| `GET /api/mcp/tools` | Returns registered tools, including disabled static check |
| `repolens.search` call | Completes and returns retrieval evidence |
| `repolens.read_file` valid path | Completes and returns bounded content |
| `repolens.read_file` path traversal | Returns denied response and writes audit |
| `repolens.safe_static_check` | Returns disabled response and writes audit |
| `GET /api/mcp/tool-calls` | Returns latest completed/denied/disabled audit rows |

Final verification:

```powershell
& ..\scripts\use-java.ps1 21; mvn test
npm run build
```

## 9. Acceptance Criteria

- P6 has independent detailed design before implementation.
- Java backend exposes tools/list, tools/call, and audit list.
- Tool calls reuse P2/P3/P5 services rather than duplicating intelligence logic.
- Permission denied and disabled calls are recorded, not silently dropped.
- Backend test suite passes.
- Frontend build passes with the new API contract.
