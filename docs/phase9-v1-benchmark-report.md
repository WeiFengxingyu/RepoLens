# RepoLens V1 Phase 9 Benchmark Report

## 1. Purpose

This report closes the V1 benchmark work for Phase 9. It covers the benchmark dataset, metrics, runner/API, Workbench panel, and validation evidence for PR/MR Review, Multi-Agent Review, and MCP tool reliability.

Phase 9 does not include Phase 10 screenshots, recordings, release packaging, or final demo scripts.

## 2. Dataset

Dataset:

```text
evals/datasets/v1_pr_mr_benchmark.jsonl
```

Coverage:

| Dimension | Coverage |
| --- | --- |
| Sample count | 22 |
| Repository keys | `python_demo`, `ts_demo` |
| Platforms | GitHub, Gitee, GitLab.com, self-hosted GitLab, synthetic |
| Change types | Pull Request, Merge Request |
| Labels | security, auth, billing, regression, repository, validation, reliability, frontend, data, audit, mcp |
| MCP expectations | allow/success, disabled/deny-style safety cases, safe failure cases |

The dataset is synthetic and offline by design. The runner reads local diff text and does not fetch live PR/MR data or write back to any platform.

## 3. Metrics

### Review

| Metric | Meaning |
| --- | --- |
| `risk_hit_rate` | Share of samples where expected risk keyword/file is matched by single-main Review |
| `citation_coverage` | Share of expected files covered by review citations |
| `unsupported_claim_rate` | Medium/high risks without evidence ids divided by medium/high risks |
| `avg_latency_ms` | Average single-main Review latency |
| `avg_token_count` | Estimated token count from structured output |

### Multi-Agent

| Metric | Meaning |
| --- | --- |
| `risk_hit_rate` | Same risk hit definition applied to Multi-Agent final report |
| `citation_coverage` | Expected file coverage in Multi-Agent citations |
| `dissent_usefulness` | Security/permission samples with useful dissent/arbitration signal |
| `arbiter_resolution_rate` | Samples where Arbiter records accepted/rejected/downgraded/dissent handling |
| `token_overhead_ratio` | Multi-Agent token estimate divided by single-main Review token estimate |
| `avg_latency_ms` | Average Multi-Agent latency |

### MCP

| Metric | Meaning |
| --- | --- |
| `tool_success_rate` | Whether success/failure matched each expected tool call |
| `permission_denial_correctness` | Whether permission decision matched expectation |
| `avg_latency_ms` | Average audited tool call latency |
| `error_count` | MCP tool calls returning error/isError |

## 4. Runner And API

API:

```text
POST /api/v1-benchmarks
```

The runner reuses existing services:

- `ReviewService` for single-main Review.
- `MultiAgentReviewService` for V1 Multi-Agent Review.
- `MCPService` for MCP `tools/call` reliability and permission metrics.

It returns:

- `metrics.review`
- `metrics.multi_agent`
- `metrics.mcp`
- per-sample results
- warnings
- `report_markdown`

## 5. Validation

| Check | Result |
| --- | --- |
| Dataset fixture parser | 8 passed |
| Metrics unit tests | 4 passed |
| V1 benchmark API smoke | 3 passed |
| Phase 9 backend专项 | 15 passed, 1 Starlette/httpx warning |
| Frontend build/type check | Passed |

The API smoke uses an in-memory repository and a 20-sample benchmark fixture. It runs single-main Review, Multi-Agent Review, and 40 MCP tool calls, then verifies all three metric groups and markdown report output.

## 6. Safety

- No PR/MR comment, approve, request changes, merge, close, or writeback.
- No external PR/MR fetch during benchmark execution.
- No code modification or push.
- MCP safe-check remains disabled by default and is evaluated as a permission/safety metric.
- Benchmark result is read-only and synchronous.

## 7. Known Limits

- The dataset is synthetic rather than live public PR/MR traffic.
- The runner is synchronous and intended for V1-scale local evaluation, not long-running benchmark farms.
- Metrics are deterministic smoke/quality indicators, not human-rated review quality labels.
- Phase 10 can add screenshots and polished demo scripts, but Phase 9 deliberately stops at benchmark/metrics/report closure.
