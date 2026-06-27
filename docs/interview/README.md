# RepoLens Interview Package

This folder contains interview-facing material only. The phase design and closed-loop records remain one level up in `docs/` so the implementation audit trail stays separate from candidate-facing preparation material.

## Recommended Preparation Order

1. Read `competitive-positioning.md` to lock the product positioning: RepoLens is not a Copilot clone; it is a transparent, evaluable repository-level Code Agent infrastructure prototype.
2. Read `v1-interview-deep-dive-guide.md` as the main study guide. Use each `【给你理解】` section to understand the system and each `【面试可说】` section to rehearse answers.
3. Read `v1-evaluation-scorecard.md` to explain retrieval ablation, Review metrics, Multi-Agent metrics, MCP metrics, and known limits.
4. Read `v1-real-pr-mr-case-studies.md` to prepare live-smoke examples across GitHub, Gitee, GitLab.com, and self-hosted GitLab.
5. Review `resume-project-audit.md` when polishing resume bullets and deciding which project depth points to emphasize.
6. Use `../phase10-demo-runbook.md` and `../../scripts/seed_demo.ps1` when rehearsing the actual local demo.

## Interview Documents

| Document | How To Use It |
| --- | --- |
| `docs/interview/v1-interview-deep-dive-guide.md` | Main Chinese deep-dive guide for product architecture, module principles, technical choices, code anchors, safety boundaries, Q&A, and final talk tracks |
| `docs/interview/competitive-positioning.md` | Use when asked why this project matters if Copilot, Codex, Claude, Gemini, or web-based repository analysis already exist |
| `docs/interview/resume-project-audit.md` | Use when refining resume bullets and choosing which project points show depth |
| `docs/interview/v1-evaluation-scorecard.md` | Use when asked for metrics, ablation evidence, evaluation limits, or whether GraphRAG/Multi-Agent/MCP are measured |
| `docs/interview/v1-real-pr-mr-case-studies.md` | Use when asked whether RepoLens maps to real PR/MR platforms beyond local fixtures |

## Supporting Demo Material

| Document Or Asset | Purpose |
| --- | --- |
| `docs/phase10-demo-runbook.md` | Step-by-step V1 demo route |
| `docs/phase10-v1-release-package.md` | Release positioning, resume bullets, and interview talk track |
| `docs/assets/screenshots/` | Workbench proof images for repository status, evidence, review, MCP, Multi-Agent, and benchmark panels |
| `evals/change_requests/phase6_demo_prs.json` | Deterministic offline PR/MR fixture |
| `evals/change_requests/real_pr_mr_case_studies.json` | Structured real PR/MR candidate list |
| `scripts/seed_demo.ps1` | Local seed script for import, retrieval, MCP, and V1 benchmark |

## Quick Answer Map

| Interview Question | Best Starting Document |
| --- | --- |
| "What is this project?" | `v1-interview-deep-dive-guide.md` |
| "How is this different from Copilot?" | `competitive-positioning.md` |
| "How does GraphRAG work here?" | `v1-interview-deep-dive-guide.md` and `v1-evaluation-scorecard.md` |
| "Have you tested real PRs or MRs?" | `v1-real-pr-mr-case-studies.md` |
| "How do you prove quality?" | `v1-evaluation-scorecard.md` |
| "What should go on the resume?" | `resume-project-audit.md` and `../phase10-v1-release-package.md` |

## Product Closure Note

RepoLens V1 is product-complete for interview presentation: repository ingestion, hybrid retrieval, evidence-grounded QA, PR/MR review, multi-platform Change Request Providers, MCP endpoint, bounded Multi-Agent Review, benchmark metrics, screenshots, seed demo, and interview material are all packaged. Further work should be treated as a new hardening or V2 track rather than extending V1 scope.
