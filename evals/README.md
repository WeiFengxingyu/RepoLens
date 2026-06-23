# RepoLens Evaluation And Demo Assets

Evaluation and demo assets:

- `datasets/p0_plus_eval.jsonl`: fixed 50-sample P0+ dataset.
- `datasets/v1_pr_mr_benchmark.jsonl`: Phase 9 V1 PR/MR benchmark dataset with 22 synthetic samples.
- `datasets/demo_questions.json`: structured walkthrough questions for demos.
- `change_requests/phase6_demo_prs.json`: Phase 6 synthetic PR/MR demo fixture.
- `demo_questions.md`: human-readable walkthrough script and screenshot mapping.
- `demo_repos/python_service`: synthetic Python service demo repository.
- `demo_repos/ts_webapp`: synthetic TypeScript webapp demo repository.
- `../docs/assets/screenshots`: workbench screenshots for README, GitHub, and resume packaging.
- `../docs/phase10-demo-runbook.md`: V1 release walkthrough for PR/MR Review, MCP client, Multi-Agent Trace, and V1 Benchmark.
- `../docs/phase10-v1-release-package.md`: V1 release positioning, resume bullets, interview talk track, and final checklist.

P5-012 screenshots cover repository status, Evaluation Panel, Ask + Trace, Review Panel, Tool Calls, and Evidence Panel.

Phase 6 PR/MR demos can use `change_requests/phase6_demo_prs.json` with the
`ts_webapp` repository to demonstrate PR/MR URL review metadata, review output,
tool calls, traces, and unsupported provider handling without external writeback.

Phase 6 does not require a live external PR/MR for automated validation. The
synthetic fixture mirrors a GitHub-style pull request, but all tests run through
the platform-neutral Change Request Provider contract and a fixture provider.
Phase 6.5 / P6-EXT adds offline provider/API smoke coverage for Gitee PR,
GitLab.com MR, and self-hosted GitLab MR fetch clients. For a live UI demo,
import/index the matching repository first, then use the Workbench Review
panel's `PR/MR URL` mode with a reachable supported PR/MR URL and configure the
matching platform token when the API requires authentication or higher rate
limits.

Phase 9 V1 benchmark demos use `datasets/v1_pr_mr_benchmark.jsonl` with
`python_demo` and `ts_webapp`. The benchmark runner is offline and read-only:
it executes local diff Review, Multi-Agent Review, and MCP tool calls against
already-indexed demo repositories, then reports Review, Multi-Agent, and MCP
metrics without fetching live PR/MR data or writing back to any platform.

Phase 10 packages the complete V1 demo story. Use the runbook for the four
release paths and keep screenshots under `../docs/assets/screenshots/`:
PR/MR URL Review, MCP Tool Permissions, Multi-Agent Trace, and V1 Benchmark.
