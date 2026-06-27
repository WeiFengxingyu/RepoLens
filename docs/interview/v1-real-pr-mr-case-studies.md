# RepoLens V1 Real PR/MR Case Studies

## 1. Purpose

This document adds interview-facing real PR/MR evidence to the deterministic V1 demo package. The default RepoLens demo remains offline and read-only, but these public cases give an interviewer concrete URLs for live-smoke follow-up across GitHub, Gitee, GitLab.com, and self-hosted GitLab.

Structured source:

```text
evals/change_requests/real_pr_mr_case_studies.json
```

## 2. Scope And Honesty Boundary

- These are public case-study candidates, not mandatory release gates.
- The default demo remains offline through local repositories, fixtures, and synthetic benchmark data.
- The URLs and metadata were sampled through public read-only platform APIs on 2026-06-27.
- RepoLens must not comment, approve, request changes, merge, close, push, or modify source code while using these cases.
- Large repositories are intentionally included to explain scope guards, diff-size limits, and why the deterministic demo uses local fixtures.
- For a stable interview demo, use `scripts/seed_demo.ps1` and `evals/change_requests/phase6_demo_prs.json`; use this document when the interviewer asks whether the design can map to real platforms.

## 3. Case Matrix

| Case | Platform | URL | Why It Matters | Recommended Demo Use |
| --- | --- | --- | --- | --- |
| FastAPI PR 15840 | GitHub PR | https://github.com/fastapi/fastapi/pull/15840 | Small docs/link update; good low-risk baseline | Live smoke candidate after indexing FastAPI or as URL parser/fetch proof |
| FastAPI PR 15851 | GitHub PR | https://github.com/fastapi/fastapi/pull/15851 | Tutorial lifecycle API documentation update | Show review focus on API semantics without overclaiming security |
| openEuler kernel PR 19747 | Gitee PR | https://gitee.com/openeuler/kernel/pulls/19747 | Large systems PR on Gitee; stresses platform and diff-size boundaries | Provider/parser and safety-boundary case, not default full demo |
| GitLab MR 242806 | GitLab.com MR | https://gitlab.com/gitlab-org/gitlab/-/merge_requests/242806 | GitLab.com MR with AI documentation maintenance context | Metadata/files/diff live smoke candidate |
| GNOME Nautilus MR 2047 | self-hosted GitLab MR | https://gitlab.gnome.org/GNOME/nautilus/-/merge_requests/2047 | Public self-hosted GitLab instance, non-gitlab.com base URL | Demonstrate self-hosted GitLab base-url handling |

## 4. Interview Talk Track

If asked "Have you tried it on real PRs?", the clean answer is:

RepoLens V1 ships a deterministic offline benchmark so the demo is reproducible, and I also prepared real public PR/MR candidates across GitHub, Gitee, GitLab.com, and self-hosted GitLab. I would not make the live cases a CI gate because platform APIs, rate limits, and large diffs make them flaky. Instead, the architecture treats them as live smoke cases while the release gate uses local fixtures and synthetic benchmark data. That separation is intentional: stable evaluation for engineering confidence, live cases for product credibility.

## 5. What Each Case Proves

| Capability | Evidence From Cases |
| --- | --- |
| GitHub PR URL shape | FastAPI PRs use `https://github.com/{owner}/{repo}/pull/{number}` |
| Gitee PR URL shape | openEuler uses `https://gitee.com/{owner}/{repo}/pulls/{number}` |
| GitLab.com MR URL shape | GitLab uses `https://gitlab.com/{namespace}/{repo}/-/merge_requests/{number}` |
| self-hosted GitLab support | GNOME uses `https://gitlab.gnome.org/.../-/merge_requests/{number}` |
| Scope control | openEuler kernel is deliberately too large for the default demo and validates diff/repo size guard thinking |
| Product credibility | Cases map the V1 provider abstraction to public projects without introducing writeback risk |

## 6. Suggested Live Smoke Order

1. Start with FastAPI PR 15840 because it is small and low risk.
2. Try GitLab MR 242806 to show Merge Request support.
3. Try GNOME Nautilus MR 2047 to show self-hosted GitLab URL handling.
4. Use openEuler kernel PR 19747 only to discuss size limits and provider parsing; do not use it as the first live demo.

## 7. Failure Modes To Explain

| Failure | Good Explanation |
| --- | --- |
| Rate limit or auth failure | Tokens are optional environment variables; the product redacts secrets and returns safe platform errors |
| Huge diff rejected | V1 protects latency and context budget through `REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS` |
| Repository not indexed | PR/MR Review expects the target repo to be imported first so evidence citations can bind to indexed code |
| Low-value docs PR review | Correct behavior is a low-risk report with documentation/test suggestions, not invented high-severity findings |
