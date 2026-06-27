# RepoLens V1 Release Package

## 1. Release Positioning

RepoLens V1 is an interview-ready repository-level Code Agent workbench. The release package demonstrates a full local loop: import repositories, build code knowledge, answer and review with citations, review PR/MR URLs across mainstream code platforms, expose read-only tools through an MCP endpoint, run bounded multi-agent review, and report V1 benchmark metrics.

## 2. P0+ Baseline vs V1 Upgrades

| Area | P0+ baseline | V1 upgrade |
| --- | --- | --- |
| Repository import | Local/Git URL import, scanner, parser, chunks | Provider-aware foundation for platform demos |
| Retrieval | BM25, vector, graph, evidence | Same evidence layer reused by PR/MR, MCP, Multi-Agent, benchmark |
| Review | Pasted diff review | PR/MR URL review through Change Request Providers |
| Tool layer | MCP-style internal tools | FastAPI HTTP JSON-RPC MCP endpoint with registry and audit |
| Agent flow | Single-main role workflow | Persisted multi-agent session with assignments, messages, dissent, Arbiter |
| Evaluation | 50 P0+ retrieval samples | 22 V1 PR/MR benchmark samples and Review/Multi-Agent/MCP metrics |
| Documentation | README, P0+ screenshots | V1 runbook, release package, V1 screenshots, resume/interview material |

## 3. Architecture Narrative

RepoLens keeps one predictable API surface while layering capability behind it:

1. Repository Service creates structured code knowledge from local/Git repositories.
2. Retrieval Service builds evidence through BM25, optional vector search, graph expansion, reranking, and context packaging.
3. Review Service and QA Service use evidence-grounded agents with trace records.
4. Change Request Provider normalizes GitHub PR, Gitee PR, GitLab.com MR, and self-hosted GitLab MR metadata, files, commits, and diff.
5. MCP Service exposes read-only tools through HTTP JSON-RPC with permission decisions and audit hashes.
6. Multi-Agent Service records bounded collaboration, dissent, and Arbiter decisions.
7. V1 Benchmark Runner reuses Review, Multi-Agent, and MCP services to produce comparable metrics.

## 4. Demo Assets

| Asset | Purpose |
| --- | --- |
| `docs/phase10-demo-runbook.md` | Main V1 walkthrough |
| `evals/demo_repos/python_service` | Python demo repository |
| `evals/demo_repos/ts_webapp` | TypeScript demo repository |
| `evals/change_requests/phase6_demo_prs.json` | Offline PR/MR Review fixture |
| `evals/change_requests/real_pr_mr_case_studies.json` | Public real PR/MR case-study candidates |
| `evals/datasets/v1_pr_mr_benchmark.jsonl` | V1 benchmark dataset |
| `scripts/seed_demo.ps1` | One-command local demo seed for import, retrieval, MCP, and V1 benchmark |
| `docs/interview/v1-real-pr-mr-case-studies.md` | GitHub/Gitee/GitLab/self-hosted GitLab interview case studies |
| `docs/interview/v1-evaluation-scorecard.md` | Retrieval ablation and V1 metric scorecard |
| `docs/interview/v1-interview-deep-dive-guide.md` | Structured Chinese deep-dive guide with product architecture, module principles, code anchors, boundaries, and interview talk tracks |
| `docs/assets/screenshots/change-request-review-panel.png` | PR/MR Review screenshot |
| `docs/assets/screenshots/mcp-tool-permissions-panel.png` | MCP permissions screenshot |
| `docs/assets/screenshots/multi-agent-trace-panel.png` | Multi-Agent trace screenshot |
| `docs/assets/screenshots/v1-benchmark-panel.png` | V1 benchmark screenshot |

## 5. Resume Bullets V2

- Built RepoLens, a repository-level Code Agent workbench that imports local/Git repositories, parses Python/TypeScript/JavaScript, builds SQLite metadata, BM25/vector indexes, and a NetworkX code graph for evidence-grounded QA and PR/MR review.
- Designed a hybrid retrieval and evidence layer combining BM25, Qdrant vector search, graph expansion, candidate deduplication, reranking, citations, and context budgets, enabling traceable answers and review reports.
- Implemented platform-neutral PR/MR URL review with read-only GitHub Pull Request, Gitee Pull Request, GitLab.com Merge Request, and self-hosted GitLab Merge Request providers for metadata, files, commits, and diff reconstruction.
- Exposed RepoLens tools through a real FastAPI HTTP JSON-RPC MCP endpoint with tool registry, read-only permissions, disabled execution-class safe check, client/session audit, input/output hashes, and Workbench visibility.
- Built bounded multi-agent review with persisted sessions, assignments, messages, independent Risk/Security/Test reviewers, Arbiter dissent handling, token/round guards, and single-main comparison payloads.
- Added evaluation rigor with a 50-sample retrieval dataset, a 22-sample V1 PR/MR benchmark, Review quality metrics, Multi-Agent dissent/arbiter/token metrics, MCP success/permission metrics, and reproducible Docker Compose deployment.

## 6. Interview Talk Track V2

1. Problem: repository-level code understanding needs evidence, not generic chatbot summaries.
2. Baseline: P0+ turns source code into parsed chunks, code graph edges, hybrid retrieval, citations, QA, Review, trace, evaluation, and local deployment.
3. V1 expansion: Phase 6 adds platform-neutral PR/MR URL review; Phase 7 turns tools into a real MCP endpoint; Phase 8 adds bounded multi-agent collaboration; Phase 9 adds benchmark metrics.
4. Engineering tradeoff: each complex capability is introduced behind a small contract and closed with tests before the next one begins.
5. Safety: all platform and MCP integrations are read-only, execution-class tools are disabled by default, secrets are environment-only, and unsupported claims are filtered or recorded as dissent.
6. Metrics: P0+ retrieval uses Hit@5, MRR, citation coverage, latency, and token estimates; V1 adds Review risk hits, unsupported claim rate, multi-agent dissent/arbiter metrics, and MCP permission correctness.
7. Demo: use the runbook to show PR/MR Review, MCP permissions/audit, Multi-Agent Trace, and V1 Benchmark without network or writeback risk.
8. Interview hardening: use the real PR/MR case studies for live-smoke credibility and the evaluation scorecard to explain BM25/vector/graph and single-main/multi-agent tradeoffs without overclaiming production quality.

## 7. Release Checklist

| Check | Evidence |
| --- | --- |
| README has V1 scope, architecture, APIs, demo flow, metrics, screenshots | `README.md` |
| Runbook has PR/MR, MCP, Multi-Agent, V1 Benchmark paths | `docs/phase10-demo-runbook.md` |
| Release package has resume and interview material | `docs/phase10-v1-release-package.md` |
| Interview hardening docs exist | `docs/interview/v1-real-pr-mr-case-studies.md`, `docs/interview/v1-evaluation-scorecard.md`, `docs/interview/v1-interview-deep-dive-guide.md` |
| Demo seed script exists | `scripts/seed_demo.ps1` |
| Screenshots exist | `docs/assets/screenshots/*.png` |
| Backend tests pass | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` |
| Backend Ruff passes | `.\\.venv\\Scripts\\python.exe -m ruff check app` |
| Frontend build/typecheck pass | `npm run build`, `npm exec tsc -- --noEmit` |
| Docker Compose config passes | `docker compose config` |
| Sensitive information scan passes | release checklist and closed-loop log |
