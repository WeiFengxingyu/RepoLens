# RepoLens-Java V1.1 分阶段执行计划书

## 1. 版本定位

V1.1 是 V1 冻结后的可信度增强版本，目标不是重做 Agent 或继续堆大功能，而是把 V1 的 pasted diff Review 升级为真实 PR/MR URL 只读 Review。

核心主线：

```text
PR/MR URL
  -> Change Request Provider 解析平台和编号
  -> 只读拉取 metadata / files / commits / diff
  -> Token 脱敏和限流错误归一化
  -> 复用 V1 ReviewService
  -> 前端展示 change request metadata + review report
  -> 离线 fixture / live smoke / release docs
```

V1.1 不改变 V1 的仓库导入、索引、检索、QA、MCP 和 Evaluation 主链路。

## 2. 阶段拆分

| 阶段 | 目标 | 交付 |
| --- | --- | --- |
| V1.1-P0 | 计划、共享详细设计、过程记录 | 分阶段计划书、共用详细设计、共用过程记录 |
| V1.1-P1 | Change Request 基础模型和 API | `change_requests` 表、URL parser、Provider SPI、review API |
| V1.1-P2 | 平台 Provider | GitHub / GitLab / Gitee 只读 provider、token 脱敏、错误归一化 |
| V1.1-P3 | Review 集成与前端 | PR/MR URL 输入、metadata 展示、review 结果复用 |
| V1.1-P4 | 演示与发布闭环 | fixture、真实案例清单、runbook、closure review、测试/构建 |

## 3. V1.1-P1：Change Request 基础模型和 API

### 工作项

| 编号 | 工作项 | 验收 |
| --- | --- | --- |
| P1-001 | 新增 `change_requests` migration | 空库 migration 通过 |
| P1-002 | 新增 ChangeRequest entity/repository | metadata 可持久化 |
| P1-003 | 新增 URL parser | GitHub/GitLab/Gitee URL 可解析 |
| P1-004 | 新增 Provider SPI | 可通过接口返回 metadata + diff |
| P1-005 | 新增 review API | `POST /api/repositories/{id}/change-requests/reviews` 可复用 Review |
| P1-006 | 新增 get API | 可按 id 查询 change request |

### 验收标准

- 输入 fixture PR URL 能生成 Review。
- 返回体包含 `change_request` 和 `review`。
- `change_request.task_id` 关联 review task。

## 4. V1.1-P2：平台 Provider

### 工作项

| 编号 | 工作项 | 验收 |
| --- | --- | --- |
| P2-001 | GitHub Provider | 支持 `https://github.com/{owner}/{repo}/pull/{number}` |
| P2-002 | GitLab Provider | 支持 `/-/merge_requests/{iid}` |
| P2-003 | Gitee Provider | 支持 `/pulls/{number}` |
| P2-004 | Token Provider | token 只从配置/env 读取，不入库、不返回前端 |
| P2-005 | HTTP 错误归一化 | 401/403/404/rate limit 有可读错误 |
| P2-006 | 离线 Fake Provider | 测试不依赖网络 |

### 验收标准

- 单测覆盖 URL parser 和 token redaction。
- API 测试默认走 fixture/fake provider。
- 真实 provider 代码存在，但测试不依赖外网。

## 5. V1.1-P3：Review 集成与前端

### 工作项

| 编号 | 工作项 | 验收 |
| --- | --- | --- |
| P3-001 | ReviewService 暴露复用入口 | Change Request flow 不复制 Review 逻辑 |
| P3-002 | 前端 Review Tab 增加 Diff / PR URL 模式 | 可切换 pasted diff 和 URL |
| P3-003 | Metadata Panel | 展示平台、标题、作者、分支、文件/commit 统计 |
| P3-004 | 错误态 | token/rate limit/not found 有清晰提示 |

### 验收标准

- 前端生产构建通过。
- URL 模式调用 Java API 并显示 metadata + review。

## 6. V1.1-P4：演示与发布闭环

### 工作项

| 编号 | 工作项 | 验收 |
| --- | --- | --- |
| P4-001 | 新增 fixture 数据 | 默认 demo 不依赖外网 |
| P4-002 | 新增 live case 文档 | 公开 GitHub/GitLab/Gitee 案例可选演示 |
| P4-003 | 新增 V1.1 runbook | 能按步骤演示 URL Review |
| P4-004 | 更新 release package | 明确 V1 与 V1.1 差异 |
| P4-005 | 闭环记录 | 过程记录包含测试命令和结果 |

### 验收标准

- 后端 `mvn test` 通过。
- 前端 `npm run build` 通过。
- V1.1 文档说明已实现、未实现、后续 V2 边界。

## 7. 最终产品原型

V1.1 完成后，Review Tab 应支持两个入口：

```text
Review
  [Diff] [PR/MR URL]

  URL: https://github.com/org/repo/pull/123
  -> Fetch metadata
  -> Reconstruct diff
  -> Run RepoLens Review
  -> Show:
     platform / title / author / branches / changed files / commits
     risks / citations / suggested tests / traces
```

## 8. 简历表达

V1.1 完成后可以在 V1 简历 bullet 后补一条：

```text
扩展真实 PR/MR 只读 Review 能力，设计平台无关 Change Request Provider，支持 GitHub/GitLab/Gitee URL 解析、metadata/diff 拉取、token 脱敏、限流错误处理和离线 fixture 回归测试，并复用既有检索增强 Review 链路生成证据化审查报告。
```
