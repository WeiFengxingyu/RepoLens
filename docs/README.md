# RepoLens Documentation Index

This directory keeps product design, phase records, release packaging, and interview material for RepoLens V1.

## Start Here

| Document | Purpose |
| --- | --- |
| `../README.md` | Project overview, architecture, quick start, APIs, feature map, and release positioning |
| `phase10-demo-runbook.md` | Repeatable V1 demo path for PR/MR Review, MCP, Multi-Agent, Benchmark, scorecard, and interview rehearsal |
| `phase10-v1-release-package.md` | V1 release package with architecture narrative, resume bullets, talk track, and checklist |
| `docs/interview/README.md` | Interview-only material package and recommended preparation order |
| `development-worklog.md` | Development process log and important implementation notes |

## Product And Planning

| Document | Purpose |
| --- | --- |
| `requirements-analysis.md` | Product requirements and scope analysis |
| `outline-design.md` | Overall architecture and module design |
| `repolens-java-requirements-outline-design.md` | Java Edition requirements and outline design for Spring Boot, Spring AI, MCP, hybrid retrieval, security, observability, and evaluation |
| `repolens-java-development-roadmap.md` | Java Edition staged development roadmap, version plan, phase deliverables, acceptance criteria, and final product prototype |
| `repolens-java-v0-execution-plan.md` | Detailed executable V0 plan for the Java backend minimum loop: repository import, scanner, Java parser, chunking, Lucene BM25 retrieval, frontend evidence display, tests, and demo runbook |
| `repolens-java-v1-phased-execution-plan.md` | Detailed executable V1 plan for async indexing, code graph, hybrid retrieval, Agent QA, PR Review, MCP, evaluation, frontend workbench, acceptance criteria, and resume positioning |
| `repolens-java-v1-design-and-worklog.md` | Shared V1 execution record for P0-P3 detailed-design-first implementation, verification, tradeoffs, and phase closure notes |
| `repolens-java-v1-p0-detailed-design.md` | V1-P0 detailed design for baseline hardening, profile strategy, module boundaries, and V1 process setup |
| `repolens-java-v1-p1-detailed-design.md` | V1-P1 detailed design for async indexing tasks, task events, repository lock, retry, and indexing pipeline extraction |
| `repolens-java-v1-p2-detailed-design.md` | V1-P2 detailed design for multi-language parsing, persisted symbols, code relations, graph queries, and parser diagnostics |
| `repolens-java-v1-p3-detailed-design.md` | V1-P3 detailed design for deterministic local embeddings, vector chunks, hybrid retrieval, score merge, and graph expansion |
| `repolens-java-v1-p4-detailed-design.md` | V1-P4 detailed design for deterministic Agent QA, tool calling, citations, verifier, trace persistence, and frontend response contract |
| `repolens-java-v1-p5-detailed-design.md` | V1-P5 detailed design for unified diff parsing, rule-based risk review, retrieval-backed citations, suggested tests, markdown report, and traces |
| `repolens-java-v1-p6-detailed-design.md` | V1-P6 detailed design for MCP-style tool registry, read-only tools/call, permission guard, audit hash, and frontend API contract |
| `repolens-java-v1-p7-detailed-design.md` | V1-P7 detailed design for evaluation metrics, V1 workbench polish, demo runbook, release package, and final closure review |
| `repolens-java-v1-demo-runbook.md` | Repeatable Java Edition V1 demo path for repository import, Search, Ask, Review, MCP, and Eval |
| `repolens-java-v1-release-package.md` | Java Edition V1 release package with capability map, APIs, resume bullets, tradeoffs, and verification commands |
| `repolens-java-v1-final-closure-review.md` | Final Java Edition V1 closure review and acceptance matrix |
| `repolens-java-v1.1-phased-execution-plan.md` | Java Edition V1.1 phased execution plan for real PR/MR URL Review, Provider SPI, frontend integration, and release closure |
| `repolens-java-v1.1-shared-detailed-design.md` | Shared V1.1 detailed design for Change Request Provider, metadata persistence, security, API, frontend, and tests |
| `repolens-java-v1.1-design-and-worklog.md` | Shared V1.1 execution record for P0-P4 implementation, verification, and phase closure notes |
| `repolens-java-v1.1-demo-runbook.md` | Repeatable Java Edition V1.1 demo path for fixture-backed PR/MR URL Review and optional live smoke |
| `repolens-java-v1.1-real-pr-mr-cases.md` | Real GitHub/GitLab/Gitee PR/MR live-smoke notes and boundaries |
| `repolens-java-v1.1-final-closure-review.md` | Final Java Edition V1.1 closure review and acceptance matrix |
| `repolens-java-v2-lite-p0-p3-detailed-design.md` | V2-Lite P0-P3 detailed design for local-first Job Center, Worker runtime, retry/dead-letter handling, and Redis-style concurrency control |
| `repolens-java-v2-lite-p4-p5-detailed-design.md` | V2-Lite P4-P5 detailed design for ReviewHub business domain, project governance, quota, audit, and webhook-driven async PR/MR review |
| `repolens-java-v2-lite-p6-p7-detailed-design.md` | V2-Lite P6-P7 detailed design for frontend workbench, observability entry points, demo runbook, release package, and final closure |
| `repolens-java-v2-lite-demo-runbook.md` | Repeatable Java V2-Lite demo path for ReviewHub, webhook-triggered async review, quota, audit, jobs, and frontend workbench |
| `repolens-java-v2-lite-release-package.md` | Java V2-Lite release package with architecture, API map, resume bullets, interview talk track, verification, and V2 Full roadmap |
| `repolens-java-v2-lite-final-closure-review.md` | Final Java V2-Lite closure review and acceptance matrix across P0-P7 |
| `repolens-java-v2-lite-design-and-worklog.md` | Shared V2-Lite P0-P7 process record with implementation notes, phase closure status, and verification results |
| `repolens-java-v0-design-and-worklog.md` | Shared lightweight detailed design and execution log for all Java Edition V0 sub-phases |
| `repolens-java-v0-demo-runbook.md` | Repeatable Java Edition V0 demo path for local import, Lucene BM25 retrieval, frontend evidence display, tests, and known limits |
| `repolens-java-environment.md` | Local Java environment notes and per-shell Java version switching instructions |
| `p0-plus-development-plan.md` | P0+ implementation plan |
| `v1-development-plan.md` | V1 phase plan and scope boundaries |
| `mcp-extension-design.md` | Early MCP extension design notes |
| `design-closure-review.md` | Design closure review |

## Interview Package

Interview-facing material is archived under `interview/` so it can be reviewed without mixing it with phase implementation records.

| Document | Purpose |
| --- | --- |
| `docs/interview/README.md` | Interview package table of contents and rehearsal order |
| `docs/interview/v1-interview-deep-dive-guide.md` | Detailed Chinese architecture and technical explanation guide with ready-to-say talk tracks |
| `docs/interview/competitive-positioning.md` | Differentiation from GitHub Copilot and general model-based repository analysis |
| `docs/interview/resume-project-audit.md` | Resume and project audit notes |
| `docs/interview/v1-evaluation-scorecard.md` | Retrieval ablation and V1 Review/Multi-Agent/MCP metric scorecard |
| `docs/interview/v1-real-pr-mr-case-studies.md` | Public GitHub, Gitee, GitLab.com, and self-hosted GitLab PR/MR live-smoke candidates |

## Phase Records

Phase records stay at the top level to preserve the development audit trail. Each phase has a detailed design and closed-loop log, with final closure reviews where applicable.

| Phase | Main Records |
| --- | --- |
| Phase 1 | `phase1-detailed-design.md`, `phase1-closed-loop-log.md` |
| Phase 2 | `phase2-detailed-design.md`, `phase2-closed-loop-log.md` |
| Phase 3 | `phase3-detailed-design.md`, `phase3-closed-loop-log.md` |
| Phase 4 | `phase4-detailed-design.md`, `phase4-closed-loop-log.md` |
| Phase 5 | `phase5-detailed-design.md`, `phase5-closed-loop-log.md` |
| Phase 6 | `phase6-detailed-design.md`, `phase6-closed-loop-log.md`, `phase6-smoke-evaluation.md`, `phase6-final-closure-review.md` |
| Phase 6.5 | `phase6-ext-detailed-design.md`, `phase6-ext-closed-loop-log.md` |
| Phase 7 | `phase7-detailed-design.md`, `phase7-closed-loop-log.md`, `phase7-final-closure-review.md` |
| Phase 8 | `phase8-detailed-design.md`, `phase8-closed-loop-log.md`, `phase8-smoke-evaluation.md`, `phase8-final-closure-review.md` |
| Phase 9 | `phase9-detailed-design.md`, `phase9-closed-loop-log.md`, `phase9-v1-benchmark-report.md`, `phase9-final-closure-review.md` |
| Phase 10 | `phase10-detailed-design.md`, `phase10-demo-runbook.md`, `phase10-v1-release-package.md`, `phase10-closed-loop-log.md`, `phase10-final-closure-review.md` |

## Demo And Evaluation Assets

| Location | Purpose |
| --- | --- |
| `../evals/README.md` | Evaluation datasets, demo repositories, PR/MR fixtures, and benchmark assets |
| `../evals/datasets/p0_plus_eval.jsonl` | 50-sample retrieval evaluation dataset |
| `../evals/datasets/v1_pr_mr_benchmark.jsonl` | 22-sample V1 PR/MR benchmark dataset |
| `../evals/change_requests/phase6_demo_prs.json` | Offline PR/MR demo fixture |
| `../evals/change_requests/repolens_java_v1_1_fixture_cases.json` | Java Edition V1.1 offline fixture-backed PR/MR URL Review case |
| `../evals/change_requests/real_pr_mr_case_studies.json` | Structured real PR/MR case-study candidates |
| `../scripts/seed_demo.ps1` | One-command local demo seed for import, retrieval, MCP, and V1 benchmark |
| `assets/screenshots/` | Workbench screenshots for README, demo, and interview packaging |

## Process Logs

| Document | Purpose |
| --- | --- |
| `conversation-worklog.md` | Conversation-level implementation history |
| `development-worklog.md` | Development worklog and checkpoint notes |
| `p0-plus-final-closure-review.md` | P0+ closure review |
| `phase10-final-closure-review.md` | Final V1 closure review |
