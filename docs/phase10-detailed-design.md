# RepoLens V1 Phase 10 详细设计

## 1. 目标

Phase 10 的目标是把 RepoLens V1 整理成可展示、可复现、可面试讲解的发布包。它不新增平台能力、不扩展 Agent 范围、不写回代码平台，而是收束 Phase 6 到 Phase 9 已完成的能力：多代码平台 PR/MR Review、RepoLens MCP endpoint、真正多 Agent 协作、V1 benchmark 和安全边界。

Phase 10 必须让项目在 README、演示脚本、截图、简历 bullet、面试讲法和最终质量门禁上形成闭环。

## 2. 范围边界

### 2.1 本阶段包含

- README V1 完整更新。
- V1 架构图和模块演进说明。
- PR/MR Review、MCP client、Multi-Agent trace 三条演示路径。
- Workbench V1 截图整理。
- 简历 bullet v2。
- 面试讲法 v2。
- 最终测试、构建、Docker Compose 和敏感信息扫描。
- Phase 10 闭环记录和最终收束审查。

### 2.2 本阶段不包含

- 新增 PR/MR 平台或外部写回能力。
- 评论、approve、request changes、merge、close、push。
- 自动修改代码或应用 patch。
- 公网 MCP service、stdio MCP transport、任意 shell 执行。
- 跨进程自治 Agent 网络、长期记忆或无限轮次协作。
- 生产登录、租户、计费、云部署流水线。

## 3. 任务拆分

| 编号 | 任务 | 交付物 | 验证方式 |
| --- | --- | --- | --- |
| P10-001 | 编写 Phase 10 详细设计 | `docs/phase10-detailed-design.md` | 文档审查 |
| P10-002 | README V1 更新 | `README.md` | release package 测试、人工审查 |
| P10-003 | V1 架构图更新 | README Mermaid 图、`docs/phase10-v1-release-package.md` | release package 测试 |
| P10-004 | 准备演示脚本 | `docs/phase10-demo-runbook.md` | release package 测试 |
| P10-005 | 录制或整理截图 | `docs/assets/screenshots/*` | PNG 存在性和大小检查 |
| P10-006 | 更新简历 bullet | README、`docs/phase10-v1-release-package.md` | release package 测试 |
| P10-007 | 更新面试讲法 | README、`docs/phase10-v1-release-package.md` | release package 测试 |
| P10-008 | 最终测试与发布检查 | `docs/phase10-final-closure-review.md` | Ruff、pytest、build、typecheck、compose、敏感信息扫描 |

## 4. 发布包结构

```text
README.md
docs/phase10-demo-runbook.md
docs/phase10-v1-release-package.md
docs/phase10-closed-loop-log.md
docs/phase10-final-closure-review.md
docs/assets/screenshots/
evals/demo_repos/
evals/change_requests/phase6_demo_prs.json
evals/datasets/v1_pr_mr_benchmark.jsonl
```

## 5. 演示路径设计

### 5.1 PR/MR Review

使用 `evals/demo_repos/ts_webapp` 和 `evals/change_requests/phase6_demo_prs.json` 展示平台无关 Change Request Provider、PR/MR metadata、diff review、风险、测试建议、引用、工具调用和 trace。线上演示可替换为支持平台的公开 PR/MR URL，但默认发布包使用离线 fixture，避免网络和 token 风险。

### 5.2 MCP Client

使用 `/api/mcp` 执行 `initialize`、`tools/list` 和 `tools/call`。展示 Tool Registry、permission、disabled safe-check、client/session audit、input/output hash 和 Workbench MCP Tool Permissions panel。演示只调用只读工具。

### 5.3 Multi-Agent Trace

使用 Review 面板的 `Multi-Agent` 模式运行固定 diff，展示 Coordinator、Risk Reviewer、Security Reviewer、Test Strategist、Arbiter、Report Writer、dissent、arbiter decision、comparison payload、risks、tests、citations 和 final markdown。

### 5.4 V1 Benchmark

使用 `evals/datasets/v1_pr_mr_benchmark.jsonl` 跑 `POST /api/v1-benchmarks`，展示 Review quality、Multi-Agent 和 MCP 三组指标。它是发布包中的指标证据，不替代人工演示路径。

## 6. 截图清单

| 截图 | 目标 |
| --- | --- |
| `docs/assets/screenshots/change-request-review-panel.png` | PR/MR URL Review flow |
| `docs/assets/screenshots/mcp-tool-permissions-panel.png` | MCP Tool Registry、permission、audit |
| `docs/assets/screenshots/multi-agent-trace-panel.png` | Multi-Agent session、assignment、message、Arbiter |
| `docs/assets/screenshots/v1-benchmark-panel.png` | V1 benchmark metrics |

保留 Phase 5 的 P0+ 截图，Phase 10 只补 V1 新能力截图。

## 7. 安全设计

- 演示默认使用本地 synthetic fixture 和 demo repositories。
- 所有 PR/MR provider、MCP tools 和 Multi-Agent flows 均保持只读。
- 发布包和截图不得包含真实 token、Authorization header、cookie、private URL 或个人路径凭据。
- `.env.example` 只保留空 token 占位。
- 敏感信息扫描覆盖 README、docs、evals、backend、frontend 和 Docker 配置。

## 8. 验收标准

- README 清晰区分 P0+ baseline 与 V1 upgrades。
- README 包含 V1 架构、核心 API、演示路径、指标、截图和安全边界。
- `docs/phase10-demo-runbook.md` 覆盖 PR/MR、MCP、Multi-Agent、V1 Benchmark。
- V1 截图存在且可用于 README/GitHub/面试展示。
- 简历 bullet 和面试讲法能解释为什么分 Phase 引入复杂能力。
- release package 测试通过。
- Ruff、backend pytest、frontend build、frontend typecheck、Docker Compose config 和敏感信息扫描通过。

