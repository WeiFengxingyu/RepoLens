# RepoLens V1 Phase 8 Smoke Evaluation

## 1. Purpose

This document records the focused Phase 8 evaluation for controlled multi-agent collaboration. It does not replace the Phase 9 benchmark platform. The goal is to prove that one review can produce traceable independent agent analyses, preserve dissent, arbitrate conflicts, and expose a comparable result next to the legacy single-main Review flow.

## 2. Scope

Covered:

- `POST /api/repositories/{repository_id}/multi-agent-reviews`
- `GET /api/multi-agent-reviews/{task_id}`
- `GET /api/agent-sessions/{session_id}`
- `agent_sessions`, `agent_assignments`, and `agent_messages`
- Coordinator, Risk Reviewer, Security Reviewer, Test Strategist, Arbiter, Report Writer
- Workbench Multi-Agent Trace Panel build and type validation

Not covered:

- Large benchmark suite
- Cross-process agent network
- Infinite agent conversation
- Long-term memory
- PR/MR writeback, approval, request changes, merge, close, push, or code modification

## 3. Smoke Cases

| Case | Signal | Result |
| --- | --- | --- |
| Model persistence | Tables create and cascade through task/session/assignment/message | Passed |
| Multi-agent review happy path | Completed task creates 1 session, 6 assignments, 6 messages, final markdown, Arbiter decision | Passed |
| Round/assignment/token guard | Response records limits and token estimate stays within configured budget | Passed |
| Evidence-grounded dissent | Security-sensitive diff for an unindexed file records `security_evidence_gap` dissent and arbitration flag | Passed |
| Query endpoints | GET by task id and session id return the persisted session graph | Passed |
| Single-main comparison | Same diff can run through legacy `/reviews` and new `/multi-agent-reviews`; multi-agent response records `baseline=single_main_review` and `variant=multi_agent_review` | Passed |
| Frontend panel | Workbench has `Multi-Agent` review mode and renders session, assignments, messages, Arbiter, dissent, comparison, risks, tests, citations, markdown | Passed by build/type check |

## 4. Validation Commands

| Command | Result |
| --- | --- |
| `.\\.venv\\Scripts\\python.exe -m ruff check app\\schemas\\multi_agent.py app\\services\\multi_agent app\\api\\multi_agent.py app\\main.py app\\tests\\test_phase8_multi_agent_api.py app\\tests\\test_phase8_multi_agent_models.py` | Passed |
| `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase8_multi_agent_models.py app\\tests\\test_phase8_multi_agent_api.py` | 7 passed, 1 Starlette/httpx deprecation warning |
| `npm run build` | Passed |
| `npm exec tsc -- --noEmit` | Passed after `npm run build` generated `.next/types` |

## 5. Evaluation Notes

- Phase 8 evaluation is intentionally small and deterministic. It validates collaboration mechanics and evidence policy rather than aggregate retrieval quality.
- The new comparison payload is a smoke-level bridge to Phase 9 metrics: assignment count, message count, dissent count, token estimate, round limit, assignment limit, and Arbiter resolution.
- Disagreements are not collapsed into the final risk list. The final report keeps `dissent` and `arbiter_decision`, and the Workbench panel renders both.

## 6. Current Limits

- The multi-agent reviewers are coordinated inside the existing FastAPI process. Phase 8 does not implement distributed agent workers.
- The parallel Review subtasks are semantically independent but executed sequentially in the synchronous API request path.
- Browser screenshot capture has not been added for the Multi-Agent panel in this session; frontend closure relies on production build and TypeScript validation.
