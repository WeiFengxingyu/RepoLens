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
