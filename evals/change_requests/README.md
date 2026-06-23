# RepoLens Phase 6 Change Request Demo Fixtures

These fixtures support the Phase 6 PR/MR Review demo without depending on
private repositories, platform write permissions, or a live PR/MR being
available during local validation.

## Synthetic GitHub PR

- Fixture: `phase6_demo_prs.json`
- Demo item: `phase6-cr-001`
- Platform: GitHub-style pull request
- URL: `https://github.com/repolens-demo/ts_webapp/pull/42`
- RepoLens repository path: `evals/demo_repos/ts_webapp`
- Focus: `src/components/review-panel.tsx`

The fixture mirrors the shape of a small public PR and uses a tiny unified diff
that is already aligned with the Phase 5 TypeScript demo repository. It is safe
for local demos because it contains no token, no private URL, and no platform
writeback instructions.

## Failure Demo

The same fixture also includes an unsupported-provider URL:

```text
https://bitbucket.org/repolens-demo/ts_webapp/pull-requests/42
```

Use it to show the Phase 6 unsupported provider error path without touching any
external code platform.

## Smoke Validation

The fixture is covered by `backend/app/tests/test_phase6_demo_change_requests.py`.
The smoke test inserts an indexed `ReviewPanel` chunk for the TypeScript demo
repository, calls the PR/MR Review API through a fixture provider, and verifies:

- URL parsing through the platform-neutral provider registry.
- metadata/files/commits/diff conversion into a unified Change Request.
- completed Review task with tool calls and traces.
- citation coverage for `src/components/review-panel.tsx`.
- non-negative tool call latency values.
- token and `Authorization` metadata are filtered from API response and stored
  `change_requests.metadata`.

No test writes back to GitHub, Gitee, GitLab, or any other code platform.
