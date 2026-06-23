# RepoLens V1 Demo Runbook

## 1. Purpose

This runbook gives a deterministic V1 demo path for RepoLens. It is designed for README verification, GitHub project review, and interview walkthroughs. The default path is offline and read-only.

## 2. Preparation

Start the backend and frontend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

Import and index both demo repositories:

| Repository key | Source path |
| --- | --- |
| `python_demo` | `F:\Desktop\agent\agent\evals\demo_repos\python_service` |
| `ts_demo` | `F:\Desktop\agent\agent\evals\demo_repos\ts_webapp` |

The screenshots and benchmark scripts assume both repositories are ready.

## 3. Demo Path A: PR/MR Review

Goal: show the platform-neutral Change Request Provider flow and PR/MR Review output.

Steps:

1. Select the ready `ts_demo` repository.
2. Open the Review panel.
3. Select `PR/MR URL`.
4. Use the deterministic fixture URL from `evals/change_requests/phase6_demo_prs.json`:

```text
https://github.com/repolens-demo/ts_webapp/pull/42
```

5. Run PR/MR Review.
6. Show metadata, changed files, risks, suggested tests, citations, tool calls, and trace.

Screenshot:

```text
docs/assets/screenshots/change-request-review-panel.png
```

Safety note: the offline fixture is covered by tests and does not write back to GitHub. Live demos may use GitHub, Gitee, GitLab.com, or self-hosted GitLab URLs, but tokens remain optional environment variables and must not be shown.

## 4. Demo Path B: MCP Client

Goal: show the real RepoLens MCP HTTP JSON-RPC endpoint and permission/audit model.

Smoke request:

```json
{
  "jsonrpc": "2.0",
  "id": "tools",
  "method": "tools/list",
  "params": {}
}
```

Read-only tool call:

```json
{
  "jsonrpc": "2.0",
  "id": "search",
  "method": "tools/call",
  "params": {
    "name": "code.search",
    "arguments": {
      "repository_id": "<ready-repository-id>",
      "query": "repository import flow",
      "top_k": 5,
      "use_vector": false
    },
    "client": {"name": "phase10-demo"},
    "session_id": "phase10-demo-session"
  }
}
```

Workbench proof:

1. Open MCP Tool Permissions.
2. Show registry tools and permission labels.
3. Show recent audit rows with client/session, input hash, output hash, status, latency, and disabled safe-check behavior.

Screenshot:

```text
docs/assets/screenshots/mcp-tool-permissions-panel.png
```

## 5. Demo Path C: Multi-Agent Trace

Goal: show bounded multi-agent collaboration and Arbiter handling.

Steps:

1. Select the ready `ts_demo` repository.
2. Open the Review panel.
3. Select `Multi-Agent`.
4. Use the default dashboard diff in the Workbench or the `demo-review-002` diff in `evals/demo_questions.md`.
5. Run Multi-Agent Review.
6. Show session status, assignments, agent messages, dissent, Arbiter decision, comparison, risks, tests, citations, and final markdown report.

Screenshot:

```text
docs/assets/screenshots/multi-agent-trace-panel.png
```

## 6. Demo Path D: V1 Benchmark

Goal: show aggregate V1 metrics that back the demo claims.

Steps:

1. Ensure `python_demo` and `ts_demo` repositories are ready.
2. Open Evaluation.
3. Use dataset path:

```text
evals/datasets/v1_pr_mr_benchmark.jsonl
```

4. Set repository keys to:

```text
python_demo,ts_demo
```

5. Run V1 Benchmark.
6. Show Review, Multi-Agent, MCP metrics and sample rows.

Screenshot:

```text
docs/assets/screenshots/v1-benchmark-panel.png
```

## 7. Closing Talk Track

The recommended closing line:

RepoLens starts from a P0+ repository intelligence baseline, then adds V1 capabilities in controlled phases: PR/MR platform integration, MCP tool serving and audit, bounded multi-agent review, benchmark metrics, and finally a reproducible demo package. The project emphasizes evidence, permissions, traceability, and measurable behavior rather than autonomous write actions.

