# RepoLens-Java V1-P5 详细设计：PR/MR Diff Review

## 1. 阶段定位

V1-P5 在 P4 Agent 工程链路上实现 diff review。当前阶段支持用户粘贴 unified diff，系统解析变更文件和 hunk，结合规则层、P3 检索证据和 P2 图谱信息，生成可复现的 review 报告。

## 2. 阶段目标

- 新增 Review API：`POST /api/repositories/{repositoryId}/reviews`。
- 新增 Review 查询 API：`GET /api/reviews/{taskId}`。
- 实现 unified diff parser。
- 实现基础风险规则：鉴权、空值、异常吞噬、危险调用、配置/SQL 变更、TODO。
- 复用 hybrid retrieval 获取 evidence/citations。
- 返回前端已有的 `ReviewTaskResponse` 契约。
- 生成 markdown report、risks、impacted_symbols、suggested_tests、tool_calls、traces。

## 3. 非目标

- 不接真实 GitHub/GitLab/Gitee provider。
- 不自动写 PR 评论。
- 不执行测试命令。
- 不修改代码。

## 4. 数据模型

### 4.1 `review_tasks`

| 字段 | 说明 |
| --- | --- |
| id | task id |
| repository_id | 仓库 id |
| status | pending/running/completed/failed |
| diff_text | 原始 diff |
| summary | review 摘要 |
| risk_level | low/medium/high |
| risks | JSON 数组 |
| impacted_symbols | JSON 数组 |
| suggested_tests | JSON 数组 |
| citations | JSON 数组 |
| markdown | Markdown 报告 |
| error_message | 失败原因 |
| created_at / completed_at | 时间 |

### 4.2 `review_tool_calls`

| 字段 | 说明 |
| --- | --- |
| id | tool call id |
| task_id | review task id |
| repository_id | 仓库 id |
| tool_name | diff.parse/code.search/risk.rules |
| status | completed/failed |
| permission_decision | allow/deny |
| input_summary | 输入摘要 |
| output_summary | 输出摘要 |
| latency_ms | 耗时 |
| created_at / completed_at | 时间 |

## 5. 后端设计

| 类 | 职责 |
| --- | --- |
| `DiffParser` | 解析 unified diff |
| `ParsedDiff` / `ChangedFile` / `DiffHunk` | diff 模型 |
| `ReviewRiskRuleEngine` | 风险规则 |
| `ReviewService` | Review 主流程 |
| `ReviewController` | Review API |
| `ReviewTaskEntity` | review task 持久化 |
| `ReviewToolCallEntity` | tool call 持久化 |

## 6. Review 流程

```text
POST diff
  -> create review_task running
  -> diff.parse
  -> risk.rules
  -> code.search with changed paths/tokens
  -> impacted symbol extraction
  -> suggested tests
  -> markdown report
  -> persist completed task + tool calls + traces
```

## 7. 风险规则

| 规则 | Severity |
| --- | --- |
| `permitAll`、`disable csrf`、鉴权关键字 | high |
| `password`、`secret`、`token` 明文相关 | high |
| `return null`、新增 nullable 分支 | medium |
| `catch (Exception)` 且空处理 | medium |
| `TODO`、`FIXME` | low |
| SQL DDL/DML 关键字 | medium |
| `Runtime.exec`、`ProcessBuilder`、`eval` | high |

## 8. 测试计划

- Diff parser 单测：文件、hunk、新增行。
- Review API 集成测试：导入 repo -> 提交 diff -> 返回 completed review。
- 断言 risks、citations、suggested_tests、markdown、tool_calls、traces 存在。
- 断言 `GET /api/reviews/{taskId}` 可查询同一结果。

## 9. 验收标准

- 粘贴 diff 能生成稳定 review。
- 至少一个风险能关联 evidence。
- markdown 可直接用于演示。
- response 符合前端 `ReviewTaskResponse` 类型。
- 不执行任何写文件、提交、merge 操作。

