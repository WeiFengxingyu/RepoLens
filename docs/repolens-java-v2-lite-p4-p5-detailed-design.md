# RepoLens-Java V2-Lite P4-P5 详细设计

## 1. 设计目标

P4-P5 在 P0-P3 的 Job Center / Worker / 并发控制内核之上，补齐传统 Java 后端项目需要展示的业务系统能力：

```text
P4 ReviewHub 业务域
  -> organization / project / repository binding
  -> review ruleset / quota bucket / audit log
P5 Webhook Review Pipeline
  -> provider webhook
  -> repository binding resolve
  -> quota + idempotency
  -> REVIEW_CHANGE_REQUEST job
  -> ChangeRequestReviewService
  -> review task / change request metadata
```

本阶段仍保持 V2-Lite 的本地可复现原则，不强依赖公网 Webhook 或真实 SaaS Provider。Webhook 支持 fixture payload，能完整演示“业务域治理 + 异步任务平台 + PR/MR Review”的主链路。

## 2. 范围边界

| 阶段 | 做什么 | 暂不做什么 |
| --- | --- | --- |
| P4 | ReviewHub 数据模型、项目绑定、规则集、配额、审计、API | 不做完整 RBAC 登录态和复杂计费系统 |
| P5 | Webhook 接入、幂等创建 Review job、异步执行 Change Request Review、事件闭环 | 不接公网回调验签平台和真实消息队列 |

## 3. P4 ReviewHub 业务域设计

### 3.1 数据模型

新增 migration `V12__add_v2_lite_reviewhub.sql`：

| 表 | 说明 |
| --- | --- |
| `organizations` | 租户组织，包含 plan/status |
| `projects` | 组织下的项目空间，承载仓库绑定、规则集和配额 |
| `team_members` | 组织成员与角色，先用于简历口径和审计，不接登录态 |
| `repository_bindings` | 项目与 RepoLens 本地 repository 的绑定，同时记录 provider/external_repo_id/webhook_secret_hash |
| `review_rulesets` | 项目级 Review 规则集，保存 JSON 配置 |
| `quota_buckets` | 固定窗口配额桶，支持 webhook_review 等 quota_type |
| `audit_logs` | 审计日志，只追加，不更新 |

关键约束：

- `repository_bindings(provider, external_repo_id)` 唯一，Webhook 可通过外部仓库 ID 定位项目与本地 repository。
- `repository_bindings(project_id, repository_id)` 唯一，避免同一项目重复绑定同一仓库。
- `quota_buckets(scope_type, scope_id, quota_type, window_start)` 唯一，支持固定窗口原子更新。
- `audit_logs` 只追加，记录 actor/action/scope/payload。

### 3.2 API

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/organizations` | 创建组织 |
| `GET` | `/api/organizations` | 查询组织列表 |
| `POST` | `/api/organizations/{organizationId}/projects` | 创建项目 |
| `GET` | `/api/organizations/{organizationId}/projects` | 查询组织下项目 |
| `POST` | `/api/projects/{projectId}/repositories/{repositoryId}/bind` | 绑定本地 repository 与 provider/external_repo_id |
| `GET` | `/api/projects/{projectId}/repositories` | 查询项目仓库绑定 |
| `POST` | `/api/projects/{projectId}/rulesets` | 创建 Review 规则集 |
| `GET` | `/api/projects/{projectId}/rulesets` | 查询项目规则集 |
| `GET` | `/api/projects/{projectId}/quota` | 查询项目配额桶 |
| `GET` | `/api/audit-logs` | 查询最近审计日志 |

### 3.3 服务边界

`ReviewHubService` 负责：

- 创建组织/项目，并写审计日志。
- 校验 repository 存在后创建 binding。
- 通过 `provider + external_repo_id` 解析 Webhook 归属。
- 创建和查询 ruleset。
- 固定窗口配额消费和查询。

配额消费使用数据库行保存当前窗口计数。Lite 版本先用单机事务闭环，V2 完整版可升级为 Redis Lua + DB 异步落账。

## 4. P5 Webhook Review Pipeline 设计

### 4.1 Webhook 入站协议

新增 `WebhookController`：

```text
POST /api/webhooks/{provider}
```

Lite payload：

```json
{
  "external_repo_id": "fixture/repolens-java",
  "change_url": "fixture://github/repolens-java/1",
  "event": "pull_request",
  "action": "opened",
  "commit_sha": "demo-sha",
  "sender": "demo-user",
  "top_k": 5,
  "use_bm25": true,
  "use_vector": true,
  "use_graph": true,
  "run_static_check": true
}
```

处理流程：

```text
WebhookController
  -> ReviewHubService.resolveBinding(provider, external_repo_id)
  -> ReviewHubService.consumeProjectQuota(projectId, "webhook_review")
  -> JobService.create(REVIEW_CHANGE_REQUEST, idempotency_key, payload_json)
  -> LocalJobDispatcher
  -> ReviewChangeRequestJobExecutor
  -> ChangeRequestReviewService.review(repositoryId, request)
```

### 4.2 幂等键

Webhook job 的幂等键：

```text
webhook:{provider}:{external_repo_id}:{change_url}:{commit_sha}:{action}
```

重复事件返回同一个 `analysis_job`，避免重复 Review。

### 4.3 Job Executor

新增 `JobType.REVIEW_CHANGE_REQUEST` 与 `ReviewChangeRequestJobExecutor`：

- 校验 `repository_id` 与 payload 中的 `change_url`。
- 复用 `ChangeRequestReviewService.review(...)`。
- 结果引用格式：

```text
change_request:{changeRequestId};review_task:{taskId}
```

该实现把 P5 与 V1.1 的真实 PR/MR URL Review 能力连接起来，避免重复实现 Provider、Diff 解析、风险规则与 Review 持久化。

## 5. 配置设计

扩展 `repolens.v2-lite`：

| 配置 | 默认值 | 说明 |
| --- | --- | --- |
| `review-hub.default-quota-limit` | `1000` | 项目级 webhook_review 默认固定窗口额度 |
| `review-hub.quota-window-minutes` | `60` | 配额窗口 |
| `webhook.require-secret` | `false` | Lite 默认不强制 header secret |

## 6. 验收标准

| 阶段 | 验收 |
| --- | --- |
| P4 | 能创建 organization/project，绑定 repository，创建 ruleset，查询 quota/audit |
| P5 | fixture webhook 能创建 `REVIEW_CHANGE_REQUEST` job，job 异步成功，结果关联 change request 与 review task |
| P5 幂等 | 重放同一个 webhook 返回同一个 job id |
| P5 配额 | webhook 触发前会消费 project quota，并能在 quota API 中查看 |

## 7. 测试计划

- `ReviewHubControllerTest`
  - 创建组织、项目、绑定仓库、创建 ruleset、查询配额、查询审计。
- `WebhookControllerTest`
  - fixture webhook 创建异步 Review job。
  - 重放同一 webhook 命中幂等。
  - job 最终 `SUCCEEDED`，`result_ref` 包含 `change_request` 与 `review_task`。

最终闭环以 `mvn test` 为准。
