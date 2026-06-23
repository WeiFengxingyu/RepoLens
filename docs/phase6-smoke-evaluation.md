# RepoLens Phase 6 Smoke Evaluation

## 1. Scope

- Date: 2026-06-13
- Phase: V1 Phase 6 - multi-platform PR/MR integration and real project demo enhancement
- Fixture: `evals/change_requests/phase6_demo_prs.json`
- Demo change request: `phase6-cr-001`
- Demo URL: `https://github.com/repolens-demo/ts_webapp/pull/42`
- Demo repository: `evals/demo_repos/ts_webapp`

This smoke evaluation stays inside Phase 6. It uses the platform-neutral Change Request Provider contract, does not write back to PR/MR platforms, does not approve/request changes, does not push code, and does not auto-modify external repositories.

## 2. Automated Smoke Coverage

| Metric | Result | Evidence |
| --- | --- | --- |
| URL parse success | Passed | `test_phase6_demo_change_request_fixture_is_small_safe_and_parseable` parses the synthetic GitHub-style PR URL through the platform-neutral parser |
| Provider fetch success | Passed | `FixtureProvider` returns a unified `FetchedChangeRequest` with metadata, files, commits and diff without network dependency |
| Review completion | Passed | `test_phase6_demo_change_request_smoke_records_metrics_citations_and_safety` creates a PR/MR Review through `POST /api/repositories/{repository_id}/change-requests/reviews` and receives a completed Review task |
| Citation coverage smoke | Passed | The smoke test inserts an indexed `ReviewPanel` code chunk and asserts the Review report includes a citation for `src/components/review-panel.tsx` |
| Latency smoke | Passed | The smoke test records end-to-end API latency locally and asserts every returned tool call has a non-negative `latency_ms` |
| Safety smoke | Passed | The smoke test injects fake `github_token` and `Authorization: Bearer secret-token` provider metadata and asserts API response plus persisted metadata do not contain the secret, `authorization`, or `github_token` |
| Unsupported provider smoke | Passed | The fixture includes `https://bitbucket.org/repolens-demo/ts_webapp/pull-requests/42`; parser returns unsupported provider in Phase 6 |

## 3. Quality Gates

| Area | Command | Result |
| --- | --- | --- |
| Backend lint | `.\\.venv\\Scripts\\python.exe -m ruff check app` | Passed, all checks passed |
| Backend tests | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | Passed, 227 tests passed, 1 Starlette/httpx deprecation warning |
| Frontend build | `npm run build` | Passed, Next.js production build completed |
| Frontend type check | `npm exec tsc -- --noEmit` | Passed when run after `npm run build`; running build and tsc in parallel can race on `.next/types` generation |
| Docker config | `docker compose config` | Passed; Phase 6 Change Request env vars are present in backend service config |

## 4. UI Smoke

| Check | Result | Notes |
| --- | --- | --- |
| Local frontend availability | Passed | A persistent local `npm run start -- -p 3000` process returned HTTP `200 OK` |
| PR/MR mode switch | Passed | in-app Browser DOM check found one `PR/MR URL` button; after click, one URL input with placeholder `https://github.com/owner/repo/pull/123` and one `Run PR/MR Review` button were present |
| Disabled state without ready repository | Passed | `Run PR/MR Review` remained disabled when no ready repository was selected |
| Screenshot capture | Blocked | Browser DOM verification passed, but the in-app Browser CDP `Page.captureScreenshot` command timed out for full-page, viewport, and clipped screenshots; no screenshot artifact was generated in this run |

## 5. Review Notes

- GitHub remains the first implemented read-only provider.
- Phase 6.5 / P6-EXT extends this baseline with Gitee Pull Request, GitLab.com Merge Request, and self-hosted GitLab read-only fetch clients plus offline provider/API smoke tests.
- Public network smoke was not required for this run because the synthetic fixture covers deterministic Phase 6 behavior without external platform dependency.
- Phase 9 remains the correct place for larger PR/MR benchmark datasets and quality metrics.

## 6. Closure Use

P6-012 used this smoke evaluation to update README, demo material, the closed-loop log, and the final closure review. As of 2026-06-14, Phase 6 is accepted as complete with screenshot capture still recorded as an environment blocker rather than a delivered artifact.

If the Browser screenshot channel becomes available later, `docs/assets/screenshots/change-request-review-panel.png` can be added as a supplemental demo asset. That follow-up must not change the Phase 6 scope or introduce PR/MR platform writeback behavior.
