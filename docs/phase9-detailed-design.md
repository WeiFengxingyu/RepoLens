# RepoLens V1 Phase 9 详细设计

## 1. 目标

Phase 9 的目标是为 V1 的多代码平台 PR/MR 集成、MCP Server 和多 Agent 协作建立评测闭环。P0+/Phase 5 已有 50 条检索评测样例；Phase 9 需要新增面向 V1 能力的 benchmark dataset、runner、metrics、API、前端展示和报告文档。

Phase 9 只做 benchmark 与指标平台，不进入 Phase 10 的截图、发布包装、演示录制或简历最终润色。

## 2. 范围

### 2.1 本阶段必须完成

- 新增 V1 PR/MR benchmark schema。
- 准备至少 20 条 PR/MR Review 评测样例。
- 设计并实现 Review quality metrics：
  - risk hit rate
  - citation coverage
  - unsupported claim rate
  - latency
  - token estimate
- 设计并实现 Multi-Agent metrics：
  - dissent usefulness
  - arbiter resolution rate
  - token overhead
- 设计并实现 MCP metrics：
  - tool success rate
  - permission denial correctness
  - latency
- 新增 V1 Benchmark Runner，支持 single-main Review、multi-agent Review 和 MCP 工具评测。
- 前端 Evaluation Panel 展示 V1 benchmark 指标与结果。
- 输出 V1 benchmark report，并更新 README、worklog、closed-loop。

### 2.2 本阶段不做

- 不做 Phase 10 截图、录屏、发布包装或最终展示脚本。
- 不新增外部平台写回能力。
- 不 comment/approve/request changes/merge/close PR/MR。
- 不自动修改代码或 push。
- 不做跨进程 Agent 网络。
- 不做无限自治 Agent 或长期记忆。

## 3. 数据集设计

### 3.1 文件

新增：

```text
evals/datasets/v1_pr_mr_benchmark.jsonl
```

每行一个 JSON object。数据集默认使用本仓库 synthetic demo repositories，保证离线可复现。样例 URL 可以使用 GitHub/Gitee/GitLab/self-hosted GitLab 风格 URL，但 Phase 9 runner 不拉取外部网络，不写回平台。

### 3.2 Schema

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 唯一样例 id |
| `repository_key` | string | 是 | 映射到 imported repository |
| `platform` | string | 是 | `github`、`gitee`、`gitlab`、`self_hosted_gitlab`、`synthetic` |
| `change_type` | string | 是 | `pull_request` 或 `merge_request` |
| `url` | string | 是 | 示例 PR/MR URL |
| `title` | string | 是 | 样例标题 |
| `diff_text` | string | 是 | unified diff |
| `expected_risks` | list | 是 | 期望风险 |
| `expected_files` | list[string] | 是 | 期望被引用或命中的文件 |
| `expected_labels` | list[string] | 否 | 期望类别，如 `security`、`regression`、`permissions` |
| `mcp_tool_calls` | list | 否 | MCP 工具评测输入 |
| `notes` | string | 否 | 说明 |

`expected_risks` item：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `title_keywords` | list[string] | 风险标题/原因应覆盖的关键词 |
| `severity` | string | 期望严重度 |
| `file_path` | string | 期望风险文件 |
| `evidence_required` | bool | 是否要求 evidence/citation |

`mcp_tool_calls` item：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `tool_name` | string | MCP tool name |
| `arguments` | object | tool arguments，支持 `{repository_id}` placeholder |
| `expect_success` | bool | 是否应成功 |
| `expect_permission_decision` | string | `allow`、`disabled`、`deny` |

## 4. Runner 设计

新增 `backend/app/services/v1_benchmark/`：

| 文件 | 责任 |
| --- | --- |
| `dataset.py` | JSONL schema parser 与校验 |
| `metrics.py` | Review、Multi-Agent、MCP 指标计算 |
| `runner.py` | 调用 ReviewService、MultiAgentReviewService 和 MCPService |
| `service.py` | API service，创建同步 benchmark response |

Phase 9 不新增数据库表。V1 benchmark 作为同步评测响应返回，避免在已有 `evaluation_runs` 表上强行塞入异构 metrics。需要持久化时可在 Phase 10 或后续演进复用现有 EvaluationRun。

## 5. API 设计

新增：

| Method | Path | 用途 |
| --- | --- | --- |
| `POST` | `/api/v1-benchmarks` | 运行 V1 benchmark |

Request：

```json
{
  "name": "V1 benchmark",
  "dataset_path": "evals/datasets/v1_pr_mr_benchmark.jsonl",
  "repository_map": {"python_demo": "...", "ts_demo": "..."},
  "include_review": true,
  "include_multi_agent": true,
  "include_mcp": true,
  "top_k": 5
}
```

Response：

- `metrics.review`
- `metrics.multi_agent`
- `metrics.mcp`
- `results[]`
- `warnings[]`
- `report_markdown`

## 6. 指标定义

### 6.1 Review metrics

| 指标 | 计算方式 |
| --- | --- |
| `risk_hit_rate` | 每个样例至少命中一个 expected risk keyword/file 的比例 |
| `citation_coverage` | expected files 被 citations 覆盖的比例 |
| `unsupported_claim_rate` | 无 evidence 的高/中风险数 / 风险总数 |
| `avg_latency_ms` | single-main Review 平均延迟 |
| `avg_token_count` | markdown/risks/citations 字符估算 token |

### 6.2 Multi-Agent metrics

| 指标 | 计算方式 |
| --- | --- |
| `risk_hit_rate` | 与 Review 一致，用 Multi-Agent final report 计算 |
| `dissent_usefulness` | 有 expected security/permission label 的样例中，出现 dissent/arbitration 的比例 |
| `arbiter_resolution_rate` | Arbiter accepted/rejected/downgraded/dissent_count 总处理数大于 0 的比例 |
| `token_overhead_ratio` | multi-agent token estimate / single-main token estimate |
| `avg_latency_ms` | Multi-Agent 平均延迟 |

### 6.3 MCP metrics

| 指标 | 计算方式 |
| --- | --- |
| `tool_success_rate` | expect_success=true 的 tool call 成功比例 |
| `permission_denial_correctness` | expect_success=false 且 permission decision 符合预期的比例 |
| `avg_latency_ms` | tool call audit latency 平均值 |

## 7. 前端设计

Workbench Evaluation section 增加 `V1 Benchmark` 子面板：

- dataset path 默认 `evals/datasets/v1_pr_mr_benchmark.jsonl`
- repository keys 复用现有输入格式
- include Review / Multi-Agent / MCP toggles
- 展示 Review、Multi-Agent、MCP 三组 metrics
- 展示 sample results 表格和 markdown report

## 8. 测试策略

| 范围 | 测试 |
| --- | --- |
| dataset | schema、20+ 样例、platform/type/expected risk/mcp call 校验 |
| metrics | risk hit、citation coverage、unsupported claim、dissent usefulness、arbiter resolution、MCP success/deny |
| runner/API | 内存 repository + TestClient smoke，跑 review/multi-agent/mcp 三类 |
| frontend | TypeScript/build |
| docs | closed-loop、README、report、worklog |

## 9. 任务分解

| 编号 | 任务 | 交付 |
| --- | --- | --- |
| P9-001 | 编写 Phase 9 详细设计 | 本文档 |
| P9-002 | 设计 PR/MR benchmark schema | `v1_benchmark/dataset.py` |
| P9-003 | 准备 20-30 条 PR/MR 样例 | `evals/datasets/v1_pr_mr_benchmark.jsonl` |
| P9-004 | 设计 Review quality metrics | `v1_benchmark/metrics.py` |
| P9-005 | 设计 Multi-Agent metrics | `v1_benchmark/metrics.py` |
| P9-006 | 设计 MCP metrics | `v1_benchmark/metrics.py` |
| P9-007 | 实现 V1 Evaluation Runner | `v1_benchmark/runner.py`、`service.py`、API |
| P9-008 | 前端 Evaluation Panel 扩展 | Workbench V1 Benchmark panel |
| P9-009 | 生成 V1 benchmark report | README、docs report、closed-loop、worklog |
