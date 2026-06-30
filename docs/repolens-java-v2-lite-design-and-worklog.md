# RepoLens-Java V2-Lite 设计与过程记录

## 1. 文档信息

| 字段 | 内容 |
| --- | --- |
| 文档类型 | V2-Lite P0-P7 共享过程记录 |
| 创建日期 | 2026-06-29 |
| 关联详细设计 | `docs/repolens-java-v2-lite-p0-p3-detailed-design.md`、`docs/repolens-java-v2-lite-p4-p5-detailed-design.md`、`docs/repolens-java-v2-lite-p6-p7-detailed-design.md` |
| 范围 | P0 环境配置、P1 Job Center、P2 Worker Runtime、P3 并发控制、P4 ReviewHub、P5 Webhook Review Pipeline、P6 Workbench、P7 Observability And Release |

## 2. 执行原则

1. 每个阶段先对照详细设计，再实现代码。
2. P0-P7 共用本记录文档，持续记录范围、取舍、验证和遗留问题。
3. 不回滚或覆盖 V1.1 已有改动。
4. 本阶段优先保证本地离线可测，RabbitMQ/Redis 用接口隔离，后续替换。
5. P4-P5 继续坚持“详细设计先行”，先补业务治理闭环，再接异步 Review 主链路。
6. P6-P7 聚焦 V2-Lite 产品化闭环：前端可演示、文档可复现、发布包可面试。

## 3. 阶段记录

### P0：基线收束与环境准备

| 项目 | 记录 |
| --- | --- |
| 状态 | DONE |
| 目标 | 增加 V2-Lite 配置、profile、包边界，保证不影响 V1/V1.1 |
| 设计取舍 | P0-P3 不强依赖真实 RabbitMQ/Redis，先使用本地 adapter |
| 产物 | `application-v2-lite.yml`、`RepoLensProperties.v2Lite`、`job` package、`V11__add_v2_lite_jobs.sql` |
| 验证 | `mvn test` 通过；Flyway 成功验证并应用 11 个 migration |

### P1：Job Center

| 项目 | 记录 |
| --- | --- |
| 状态 | DONE |
| 目标 | 新增 Job 数据模型、状态机、事件流、API 和幂等创建 |
| 设计取舍 | 任务结果以 DB 为准；事件只追加 |
| 产物 | `AnalysisJobEntity`、`JobAttemptEntity`、`JobEventEntity`、`DeadLetterJobEntity`、`JobStateMachine`、`JobService`、`JobController` |
| 验证 | `JobStateMachineTest`、`JobControllerTest.createsIdempotentNoopJobAndCompletesAsync` 通过 |

### P2：Worker Runtime

| 项目 | 记录 |
| --- | --- |
| 状态 | DONE |
| 目标 | 本地 worker queue、attempt、heartbeat、retry、dead letter |
| 设计取舍 | `JobDispatcher` 接口隔离本地队列与未来 RabbitMQ |
| 产物 | `LocalJobDispatcher`、`JobWorkerService`、`WorkerRegistry`、`JobExecutorRegistry`、`NoopJobExecutor`、`IndexRepositoryJobExecutor`、`ReviewDiffJobExecutor` |
| 验证 | `JobControllerTest.failedNoopJobMovesToDeadLetterAndCanBeListed`、`retryableNoopJobRetriesUntilDeadLetter` 通过；异步 NOOP job 可完成并写 attempt/event/result_ref，retryable 失败会按 max-attempts 重试后进入 dead letter |

### P3：并发控制

| 项目 | 记录 |
| --- | --- |
| 状态 | DONE |
| 目标 | 本地实现 Redis 语义的锁、幂等、限流、状态缓存 |
| 设计取舍 | `ConcurrencyControlService` 接口隔离本地实现与未来 Redis |
| 产物 | `ConcurrencyControlService`、`LocalConcurrencyControlService`、`LockHandle`、`RateLimitDecision` |
| 验证 | `LocalConcurrencyControlServiceTest` 覆盖 owner-token 锁释放、幂等、状态缓存、固定窗口限流 |

### P4：ReviewHub 业务域

| 项目 | 记录 |
| --- | --- |
| 状态 | DONE |
| 目标 | 新增组织、项目、仓库绑定、规则集、配额桶、审计日志，形成传统业务系统治理面 |
| 设计取舍 | 不引入完整登录态/RBAC；先以项目级治理和审计闭环支撑 Webhook 与简历表达 |
| 产物 | `V12__add_v2_lite_reviewhub.sql`、`reviewhub` package、ReviewHub API |
| 验证 | `ReviewHubControllerTest` 覆盖 organization/project/repository binding/ruleset/quota/audit API |

### P5：Webhook Review Pipeline

| 项目 | 记录 |
| --- | --- |
| 状态 | DONE |
| 目标 | 从 provider webhook 触发 `REVIEW_CHANGE_REQUEST` job，复用 V1.1 Change Request Review 能力完成异步评审 |
| 设计取舍 | Lite 版本支持 fixture webhook 和本地异步执行；真实公网验签、MQ、provider callback 留到 V2 完整版 |
| 产物 | `WebhookController`、`ReviewChangeRequestJobExecutor`、`JobType.REVIEW_CHANGE_REQUEST` |
| 验证 | `WebhookControllerTest` 覆盖 webhook -> quota -> idempotent job -> worker -> change request review -> result_ref |

### P6：V2-Lite Workbench

| 项目 | 记录 |
| --- | --- |
| 状态 | DONE |
| 目标 | 在现有前端工作台新增 V2-Lite tab，打通 ReviewHub、Webhook、Job、Quota、Audit 可视化 |
| 设计取舍 | 保持单页工程工作台，不引入复杂组件树和登录态 |
| 产物 | `frontend/types/workbench.ts`、`frontend/lib/api.ts`、`frontend/app/page.tsx`、`frontend/app/v2-lite-panel.tsx` |
| 验证 | `npm run build` 通过，V2-Lite tab 类型检查和生产构建通过 |

### P7：Observability And Release

| 项目 | 记录 |
| --- | --- |
| 状态 | DONE |
| 目标 | 补充可观测入口、演示 runbook、release package、最终闭环审计 |
| 设计取舍 | Lite 版本记录可观测入口和 dashboard 升级路线，不启动真实 Grafana 容器 |
| 产物 | `repolens-java-v2-lite-demo-runbook.md`、`repolens-java-v2-lite-release-package.md`、`repolens-java-v2-lite-final-closure-review.md` |
| 验证 | 文档索引已更新；`mvn test` 与 `npm run build` 通过 |

## 4. 验证命令

```powershell
cd F:\Desktop\agent\RepoLens\backend-java
& ..\scripts\use-java.ps1 21
mvn test
```

## 5. 最终闭环记录

### 5.1 实现摘要

本次 P0-P3 已按“先详细设计，再实现，再验证”的工作流完成：

1. 新增 P0-P3 详细设计文档：`docs/repolens-java-v2-lite-p0-p3-detailed-design.md`。
2. 新增共享过程记录文档：`docs/repolens-java-v2-lite-design-and-worklog.md`。
3. 新增 V2-Lite 配置与 profile：`application-v2-lite.yml`。
4. 新增 Job Center migration：`V11__add_v2_lite_jobs.sql`。
5. 新增 `job` 包，实现任务状态机、幂等创建、事件流、attempt、dead letter、API。
6. 新增本地 Worker Runtime，实现本地队列、执行器注册、异步执行、失败处理。
7. 新增本地 Concurrency Control，实现 Redis 语义的锁、幂等、限流和状态缓存。

### 5.2 关键取舍

P0-P3 没有直接引入真实 RabbitMQ/Redis 依赖，而是先用接口加本地实现完成闭环：

- `JobDispatcher` 后续可替换为 RabbitMQ publisher/consumer。
- `ConcurrencyControlService` 后续可替换为 Redis adapter。
- 当前测试无需外部服务，适合简历项目本地复现和 CI。
- 业务语义已经按分布式任务平台设计，后续替换中间件不会推翻 API 和数据模型。

### 5.3 验证结果

验证命令：

```powershell
cd F:\Desktop\agent\RepoLens\backend-java
& ..\scripts\use-java.ps1 21
mvn test
```

结果：

```text
Tests run: 41, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

### 5.4 P0-P3 闭环结论

V2-Lite P0-P3 已完成最小任务平台闭环：

```text
Job API -> 幂等创建 -> QUEUED -> Local Worker -> RUNNING -> SUCCEEDED/RETRY_SCHEDULED/DEAD
          -> attempt/event/result_ref/dead_letter
          -> 本地锁/幂等/限流/状态缓存
```

后续 P6-P7 可以在此基础上继续接前端工作台和 Grafana 可观测。

## 6. P4-P5 执行记录

### 6.1 设计记录

P4-P5 详细设计已新增到 `docs/repolens-java-v2-lite-p4-p5-detailed-design.md`。本阶段的核心取舍：

1. ReviewHub 先做组织/项目/绑定/规则/配额/审计这些传统后端能力，不做完整登录态。
2. Webhook 入口先支持 fixture payload，通过 `provider + external_repo_id` 定位项目与本地 repository。
3. Webhook 不直接同步跑 Review，而是创建 `REVIEW_CHANGE_REQUEST` job，复用 P0-P3 的任务平台。
4. Review 执行复用 V1.1 的 `ChangeRequestReviewService`，避免重复实现 Provider/Diff/Review。

### 6.2 实现记录

本次 P4-P5 已按详细设计完成：

1. 新增 P4-P5 详细设计文档：`docs/repolens-java-v2-lite-p4-p5-detailed-design.md`。
2. 新增 V12 migration：`organizations`、`projects`、`team_members`、`repository_bindings`、`review_rulesets`、`quota_buckets`、`audit_logs`。
3. 新增 `reviewhub` 包，包含 JPA entity/repository、`ReviewHubService`、ReviewHub API DTO 与 Controller。
4. 新增 ReviewHub API：组织创建/查询、项目创建/查询、仓库绑定/查询、规则集创建/查询、项目配额查询、审计日志查询。
5. 扩展 `RepoLensProperties.v2Lite`：`review-hub.default-quota-limit`、`review-hub.quota-window-minutes`、`webhook.require-secret`。
6. 新增 `JobType.REVIEW_CHANGE_REQUEST` 和 `ReviewChangeRequestJobExecutor`，复用 `ChangeRequestReviewService.review(...)` 完成异步 PR/MR Review。
7. 新增 `webhook` 包和 `POST /api/webhooks/{provider}`，支持 `provider + external_repo_id` 解析绑定、项目配额消费、幂等 job 创建和 fixture webhook。
8. Webhook 重放先查 job 幂等键，命中时直接返回已有 job，不重复消耗 quota。
9. Webhook 测试中关闭本地自动 dispatcher，并显式调用同一个 `JobWorkerService`，避免全量测试中线程池时序导致偶发等待超时，同时仍完整验证 Worker/Executor/Review 主链路。

### 6.3 验证记录

后端验证命令：

```powershell
cd F:\Desktop\agent\RepoLens\backend-java
& ..\scripts\use-java.ps1 21
mvn test
```

结果：

```text
Tests run: 43, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

前端验证命令：

```powershell
cd F:\Desktop\agent\RepoLens\frontend
npm run build
```

结果：

```text
Compiled successfully
Generating static pages (4/4)
```

### 6.4 P4-P5 闭环结论

P4-P5 已完成 V2-Lite 的业务系统闭环：

```text
Organization/Project
  -> Repository Binding
  -> Review Ruleset
  -> Webhook Provider Event
  -> Project Quota + Idempotency
  -> REVIEW_CHANGE_REQUEST Job
  -> Worker Attempt/Event
  -> ChangeRequestReviewService
  -> change_request + review_task + result_ref
  -> Audit Log
```

当前版本已经具备“代码智能 + 异步任务平台 + 传统业务系统治理”的组合表达。后续 P6/P7 可继续补前端 ReviewHub 工作台、Webhook 演示页面、Prometheus/Grafana 可观测与 release runbook。

## 7. P6-P7 执行记录

### 7.1 设计记录

P6-P7 详细设计已新增到 `docs/repolens-java-v2-lite-p6-p7-detailed-design.md`。本阶段的核心取舍：

1. P6 不新建独立前端项目，继续在现有 `frontend/` 工作台中增加 `V2-Lite` tab。
2. P6 前端覆盖 ReviewHub、Webhook、Job、Quota、Audit、Worker 这些 V2-Lite 主链路，不做完整团队成员/RBAC 管理。
3. P7 不引入真实 Prometheus/Grafana 运行时，先以 Actuator、Job Center、Quota、Audit 作为可观测入口，并在 release package 中说明升级路线。
4. P7 文档面向演示和简历投递，补 runbook、release package、final closure review。

### 7.2 实现记录

本次 P6-P7 已按详细设计完成：

1. 新增 P6-P7 详细设计文档：`docs/repolens-java-v2-lite-p6-p7-detailed-design.md`。
2. 扩展前端类型：`OrganizationResponse`、`ProjectResponse`、`RepositoryBindingResponse`、`ReviewRulesetResponse`、`QuotaBucketResponse`、`AuditLogResponse`、`JobResponse`、`WebhookJobResponse`、`WorkerResponse`。
3. 扩展前端 API helper：ReviewHub、Webhook、Job、Worker、Quota、Audit 相关调用。
4. 新增 `frontend/app/v2-lite-panel.tsx`，封装 V2-Lite tab 的 ReviewHub setup、Webhook trigger、Async Job、Governance、Recent Jobs 面板。
5. 更新 `frontend/app/page.tsx`，新增 `V2-Lite` tab，并保持原 Search/Ask/Review/MCP/Eval 路径不变。
6. 新增 P7 文档：V2-Lite demo runbook、release package、final closure review。
7. 更新 `docs/README.md`，登记 P6-P7 详细设计、runbook、release package、final closure review。

### 7.3 验证记录

后端验证命令：

```powershell
cd F:\Desktop\agent\RepoLens\backend-java
& ..\scripts\use-java.ps1 21
mvn test
```

结果：

```text
Tests run: 43, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

前端验证命令：

```powershell
cd F:\Desktop\agent\RepoLens\frontend
npm run build
```

结果：

```text
Compiled successfully
Linting and checking validity of types passed
Generating static pages (4/4)
```

### 7.4 P6-P7 闭环结论

P6-P7 已完成 V2-Lite 的产品化闭环：

```text
V2-Lite Workbench
  -> ReviewHub setup
  -> repository binding
  -> ruleset
  -> webhook fixture trigger
  -> async job detail
  -> quota / audit / worker visibility
  -> demo runbook / release package / final closure review
```

至此，V2-Lite P0-P7 已从后端任务内核、业务域、Webhook Review Pipeline 延伸到前端工作台和发布包装，满足“同样工作流闭环 V2-Lite”的目标。
