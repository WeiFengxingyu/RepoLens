# RepoLens-Java V2-Lite 分阶段执行计划书

## 1. 文档信息

| 字段 | 内容 |
| --- | --- |
| 项目名称 | RepoLens-Java |
| 版本名称 | V2-Lite / ReviewHub |
| 推荐简历名称 | RepoLens ReviewHub：面向团队代码仓库的分布式智能评审任务平台 |
| 文档类型 | 分阶段执行计划书 |
| 创建日期 | 2026-06-29 |
| 前置版本 | V1：仓库级 Code Agent 工作台；V1.1：真实 PR/MR URL Provider |
| 依据文档 | `docs/repolens-java-v2-lite-reviewhub-plan.md`、`docs/repolens-java-development-roadmap.md` |
| 开发策略 | 不另起项目，在 RepoLens-Java 原目录内补分布式任务、中间件、团队业务和可观测能力 |

## 2. V2-Lite 总目标

V2-Lite 的目标是把 RepoLens-Java 从“单人本地 Code Agent 工作台”升级为“团队级分布式智能评审任务平台”。它不追求完整企业 SaaS，而是围绕仓库索引和 PR/MR Review 两条真实业务链路，补齐传统 Java 后端面试中高频追问的能力：

```text
Webhook / 手动触发 / 批量重建
  -> Job Center 幂等创建任务
  -> RabbitMQ 异步削峰
  -> Worker 租约、心跳、重试、死信
  -> Redis 锁、限流、幂等、状态缓存
  -> 组织、项目、仓库、规则集、配额、审计
  -> Job Queue / Worker Monitor / Metrics Dashboard
```

核心原则：

1. 不替换 V1/V1.1 主链路，只把索引和 Review 包装为可调度、可恢复、可观测的任务。
2. 每个中间件都必须有明确业务落点，不能为了“技术栈好看”而堆组件。
3. 优先保证本地 Docker Compose 可复现，再考虑生产云环境。
4. 任务结果以数据库为准，MQ 只做触发，避免重复消息导致脏状态。
5. 默认不做自动改代码、自动评论 PR、自动 merge，只做只读分析和报告生成。

## 3. 版本边界

### 3.1 必做范围

| 方向 | 必做内容 |
| --- | --- |
| 分布式任务 | `analysis_job`、`job_attempt`、`job_event`、状态机、幂等、重试、死信、取消 |
| MQ | RabbitMQ 默认队列，消息发布、消费、ack/nack、重复消息安全 |
| Worker | Worker 注册、租约、心跳、执行器注册、超时恢复 |
| Redis | 仓库级锁、Webhook 幂等、用户/仓库级限流、任务状态缓存 |
| 业务系统 | 组织、项目、成员、仓库绑定、Review Ruleset、Quota |
| Webhook | GitHub/GitLab/Gitee 事件入口，签名校验可配置，生成 Review job |
| 前端 | Job Queue、Job Detail、Worker Monitor、Ruleset、Quota、Metrics |
| 可观测 | Actuator、Micrometer、Prometheus、Grafana，本地 dashboard 截图 |
| 验证 | 并发 webhook 去重、锁互斥、Worker 中断恢复、重复消息安全、限流 |

### 3.2 暂缓范围

| 内容 | 暂缓原因 |
| --- | --- |
| Kubernetes | 工程量大，简历阶段性价比低 |
| 企业收费/账单 | 偏商业系统，与技术主线弱相关 |
| 完整多租户隔离 | V2-Lite 只做轻量组织/项目边界 |
| 自动写回 PR 评论 | 涉及外部平台权限和误操作风险 |
| OpenSearch/PGvector/Neo4j 替换 | 保留给 V2 完整生产化版本 |
| LLM-as-a-Judge | 保留给 V2 完整评测增强 |

## 4. 和现有版本的复用关系

| 现有能力 | V2-Lite 复用方式 | 需要新增的封装 |
| --- | --- | --- |
| V1 索引 pipeline | 作为 `INDEX_REPOSITORY` job executor | Job payload、仓库锁、attempt event |
| V1 ReviewService | 作为 `REVIEW_DIFF` / `REVIEW_CHANGE_REQUEST` job executor | 异步执行、ruleset、quota、任务报告 |
| V1.1 ChangeRequestProvider | Webhook 或 URL Review 拉取 metadata/diff | provider idempotency key、平台限流 |
| MCP-style Tool Audit | 继续记录只读工具调用 | 增加组织/项目/仓库维度查询 |
| Evaluation | 继续跑检索/Review 指标 | 新增队列延迟、任务耗时、失败率指标 |
| Next.js Workbench | 扩展现有页面 | 增加 ReviewHub 运维/业务看板 |

## 5. 最终产品原型

### 5.1 首屏形态

V2-Lite 不做 landing page，首屏仍然是可操作工作台：

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ RepoLens ReviewHub                                                        │
├──────────────┬────────────────────────────────────┬───────────────────────┤
│ Team         │ Job Queue                          │ Metrics               │
│ Org          │ [All] [Index] [Review] [Dead]      │ Queue depth           │
│ Project      │ Status / Type / Priority / Repo    │ Success rate          │
│ Repositories │ Attempt timeline                   │ Retry rate            │
│ Rulesets     │ Retry / Cancel                     │ p95 duration          │
│ Quota        │ Error code / Last event            │ Worker heartbeat      │
├──────────────┼────────────────────────────────────┼───────────────────────┤
│ Webhook      │ Review Report                      │ Evidence / Trace      │
│ Recent PR/MR │ Risks / Tests / Citations          │ Tool audit            │
└──────────────┴────────────────────────────────────┴───────────────────────┘
```

### 5.2 Demo 主线

```text
启动 Docker Compose
  -> 创建组织、项目、仓库绑定
  -> 配置 Review Ruleset 和每日配额
  -> 模拟 100 个 PR/MR webhook
  -> Job Center 幂等生成 Review jobs
  -> RabbitMQ 削峰，Worker 并发消费
  -> Redis 防重复、限流和仓库锁生效
  -> 查看 Job Queue、attempt timeline、失败重试
  -> 查看 Review 报告、Evidence、Trace、Tool Audit
  -> 查看 Grafana：队列积压、成功率、p95 耗时、失败原因
```

### 5.3 最终截图清单

| 截图 | 内容 |
| --- | --- |
| Job Queue | 多个 Review/Index job 的状态、优先级、重试、死信 |
| Job Detail | attempt timeline、worker、heartbeat、错误原因、事件流 |
| Worker Monitor | worker 在线状态、当前任务、处理耗时 |
| Ruleset / Quota | 项目规则和每日 Review/Index 配额 |
| Grafana Dashboard | queue depth、success rate、p95 duration、failure reason |

## 6. 阶段总览

建议周期：2.5 到 4 周。若时间紧，至少完成 P0-P3；若要作为简历补强，建议完成 P0-P7。

| 阶段 | 建议周期 | 目标 | 可演示结果 |
| --- | --- | --- | --- |
| V2L-P0 | 0.5-1 天 | 基线收束、环境和分支准备 | V2-Lite profile、Docker Compose、中间件可启动 |
| V2L-P1 | 2-3 天 | Job Center 数据模型与状态机 | 可幂等创建、查询、取消、重试 job |
| V2L-P2 | 3-4 天 | RabbitMQ Worker 与失败恢复 | 创建 job 后异步执行，Worker 中断可恢复 |
| V2L-P3 | 2-3 天 | Redis 并发控制面 | 锁、幂等、限流、状态缓存生效 |
| V2L-P4 | 3-4 天 | ReviewHub 业务域 | 组织、项目、仓库、规则集、配额可用 |
| V2L-P5 | 3-4 天 | Webhook 与 Review job 集成 | 模拟 PR/MR webhook 自动生成 Review 报告 |
| V2L-P6 | 3-4 天 | 前端工作台 | Job Queue、Worker、Ruleset、Quota 页面可演示 |
| V2L-P7 | 2-3 天 | 可观测、压测、发布包装 | Grafana 截图、并发验证、README 和简历材料 |

## 7. V2L-P0：基线收束与环境准备

### 7.1 目标

确认 V2-Lite 基于 V1/V1.1 继续开发，不改变原主链路；准备本地运行所需的 profile、中间件和开发约束。

### 7.2 工作内容

| 编号 | 工作 | 说明 | 验收 |
| --- | --- | --- | --- |
| P0-001 | 分支准备 | 从 V1.1 稳定点创建 `repolens-java-v2-lite` | 分支干净，V1.1 仍可回溯 |
| P0-002 | profile 设计 | 新增 `application-v2-lite.yml` | 可通过 profile 开关 MQ/Redis/metrics |
| P0-003 | Docker Compose | 增加 PostgreSQL、Redis、RabbitMQ、Prometheus、Grafana | `docker compose up` 可启动依赖 |
| P0-004 | 依赖确认 | Spring AMQP、Spring Data Redis、Micrometer registry、Testcontainers | Maven 依赖可解析 |
| P0-005 | 包边界 | 新增 `job`、`worker`、`team`、`quota`、`webhook`、`ops` 包规划 | 目录和 README 说明一致 |
| P0-006 | 降级策略 | 明确没有 MQ/Redis 时是否禁用 V2-Lite API | 启动失败或降级行为明确 |

### 7.3 产物

- `backend-java/src/main/resources/application-v2-lite.yml`
- `docker-compose.v2-lite.yml` 或合并进现有 compose
- V2-Lite profile 说明
- 中间件连接配置和环境变量说明

### 7.4 验收标准

- 本地能启动后端和中间件。
- 不启用 V2-Lite profile 时，V1/V1.1 功能不受影响。
- 启用 V2-Lite profile 后，应用能连接 Redis/RabbitMQ，并暴露基础 health。

## 8. V2L-P1：Job Center 数据模型与状态机

### 8.1 目标

建立通用任务中心，把索引和 Review 抽象成统一 job，为后续 MQ Worker、重试、死信和前端看板打基础。

### 8.2 数据库设计

| 表 | 必要字段 |
| --- | --- |
| `analysis_job` | `id`、`job_type`、`status`、`priority`、`repository_id`、`project_id`、`idempotency_key`、`payload_json`、`created_by`、`next_run_at`、`created_at`、`updated_at` |
| `job_attempt` | `id`、`job_id`、`attempt_no`、`worker_id`、`status`、`started_at`、`heartbeat_at`、`finished_at`、`error_code`、`error_message` |
| `job_event` | `id`、`job_id`、`attempt_id`、`event_type`、`message`、`payload_json`、`created_at` |
| `dead_letter_job` | `job_id`、`reason`、`final_error`、`attempt_count`、`payload_json`、`created_at` |

### 8.3 状态机

```text
CREATED -> QUEUED -> RUNNING -> SUCCEEDED
                         ├── FAILED_RETRYABLE -> RETRY_SCHEDULED -> QUEUED
                         ├── DEAD
                         └── CANCELED
```

状态转移必须集中在 `JobStateMachine` 或等价服务中，禁止业务代码随意改 status。

### 8.4 工作内容

| 编号 | 工作 | 说明 | 验收 |
| --- | --- | --- | --- |
| P1-001 | Flyway migration | 新增 job/attempt/event/dead letter 表和索引 | 空库迁移成功 |
| P1-002 | Entity/Repository | JPA entity 与 repository | 基础 CRUD 测试通过 |
| P1-003 | JobStateMachine | 合法转移、非法转移异常 | 单测覆盖所有状态 |
| P1-004 | JobService | 幂等创建、查询、取消、重试 | 重复 idempotency key 返回同一 job |
| P1-005 | JobEventService | 每次状态变化写事件 | Job detail 能看到事件流 |
| P1-006 | API | `POST /api/jobs`、`GET /api/jobs`、`GET /api/jobs/{id}`、`POST /api/jobs/{id}/cancel`、`POST /api/jobs/{id}/retry` | API 测试通过 |
| P1-007 | 索引任务适配 | 将 V1 索引入口包装成 `INDEX_REPOSITORY` job，但可先同步执行 | 原索引功能不回退 |

### 8.5 测试要求

- `JobStateMachineTest`：合法转移、非法转移、终态保护。
- `JobServiceIdempotencyTest`：同 idempotency key 并发创建只生成一个 job。
- `JobControllerTest`：创建、列表、详情、取消、重试 API。
- Migration 测试：空库能迁移，唯一索引生效。

### 8.6 验收标准

- 可以通过 API 创建 `INDEX_REPOSITORY` 和 `REVIEW_CHANGE_REQUEST` 两类 job。
- 重复请求不会重复创建 job。
- 每个 job 都有事件流。
- 取消和重试 API 有明确状态约束。

## 9. V2L-P2：RabbitMQ Worker 与失败恢复

### 9.1 目标

将 P1 的任务从“落库记录”升级为真正异步执行，支持 Worker 横向扩展、心跳、租约、超时恢复、重试和死信。

### 9.2 消息设计

MQ 消息只放引用 ID：

```json
{
  "job_id": "job_123",
  "job_type": "REVIEW_CHANGE_REQUEST",
  "priority": 5,
  "published_at": "2026-06-29T10:00:00Z"
}
```

| Exchange / Queue | 用途 |
| --- | --- |
| `repolens.job.exchange` | 统一任务交换机 |
| `repolens.index.requested` | 仓库索引任务 |
| `repolens.review.requested` | Review 任务 |
| `repolens.job.retry` | 延迟重试任务 |
| `repolens.job.dead` | 死信任务 |

### 9.3 工作内容

| 编号 | 工作 | 说明 | 验收 |
| --- | --- | --- | --- |
| P2-001 | RabbitMQ 配置 | exchange、queue、routing key、retry/dead queue | 启动后自动声明队列 |
| P2-002 | JobPublisher | job 创建后发布消息 | P1 job 进入 QUEUED |
| P2-003 | WorkerRegistry | 注册 worker id、hostname、started_at、heartbeat | Worker Monitor 可查询 |
| P2-004 | JobExecutorRegistry | 按 job_type 分发到 executor | 未知 job_type 被拒绝并记录事件 |
| P2-005 | Lease 机制 | Worker 领取 job 时创建 attempt 并写 heartbeat | 同一 job 不会被两个 worker 同时执行 |
| P2-006 | Heartbeat | 执行中定期刷新 `heartbeat_at` | 长任务不会被误回收 |
| P2-007 | Retry 策略 | 网络/限流/临时错误指数退避 | attempt 增加，事件可追踪 |
| P2-008 | Dead letter | 超过最大重试或不可恢复错误进入 DEAD | Dead job 可查询 |
| P2-009 | Worker 中断恢复 | 定时扫描 heartbeat 超时任务重新入队 | 模拟中断可恢复 |
| P2-010 | V1 服务接入 | `INDEX_REPOSITORY` 复用 V1 indexing，`REVIEW_DIFF` 复用 ReviewService | 异步执行结果可查 |

### 9.4 测试要求

- RabbitMQ Testcontainers 集成测试。
- 重复消息消费测试：同一 job 只成功执行一次。
- Worker 失败测试：executor 抛异常后进入 retry 或 dead。
- 超时恢复测试：heartbeat 过期后重新入队。
- ack/nack 测试：DB 状态更新失败时不误 ack。

### 9.5 验收标准

- 创建 job 后 API 立即返回，任务由 Worker 异步执行。
- Worker 中断不会导致 job 永久卡在 RUNNING。
- 可重试错误有指数退避和 attempt 记录。
- 不可恢复错误进入 DEAD，可人工 retry。

## 10. V2L-P3：Redis 并发控制面

### 10.1 目标

使用 Redis 解决高并发场景下的重复索引、重复 webhook、平台 API 过载和看板轮询压力。

### 10.2 Redis Key 设计

| 用途 | Key | TTL | 行为 |
| --- | --- | --- | --- |
| 仓库索引锁 | `lock:repo:{repositoryId}:index` | 30 min，可续期 | 同仓库只允许一个索引 job RUNNING |
| PR/MR 幂等 | `idem:cr:{provider}:{repo}:{number}:{sha}` | 24 h | 重复 webhook 返回已有 job |
| 用户限流 | `rate:user:{userId}:review:{minute}` | 2 min | 每分钟 Review 创建次数限制 |
| 仓库限流 | `rate:repo:{repoId}:provider:{minute}` | 2 min | 保护平台 API 和 LLM |
| 任务状态缓存 | `job:status:{jobId}` | 5 min | 前端轮询优先读缓存 |

### 10.3 工作内容

| 编号 | 工作 | 说明 | 验收 |
| --- | --- | --- | --- |
| P3-001 | RedisClient 封装 | 统一序列化、超时、异常处理 | Redis 不可用有明确错误 |
| P3-002 | DistributedLockService | `SET NX PX` 加锁，释放校验 owner token | 并发测试只有一个成功 |
| P3-003 | Lock renewal | 长索引任务自动续期 | 超长任务不被误释放 |
| P3-004 | IdempotencyService | Redis 快速挡重，DB 唯一索引兜底 | 100 个重复请求只创建一个 job |
| P3-005 | RateLimiter | 用户/仓库固定窗口限流 | 超限返回剩余时间和限制 |
| P3-006 | JobStatusCache | job 状态更新写缓存，查询优先读缓存 | 看板轮询减少 DB 查询 |
| P3-007 | 降级策略 | Redis 异常时走 DB 幂等，限流 fail-closed 或 fail-open 可配置 | 行为有测试覆盖 |

### 10.4 测试要求

- Redis Testcontainers 集成测试。
- 并发锁测试：多线程竞争同一 repository lock。
- 幂等测试：100 个相同 idempotency key 并发创建。
- 限流测试：窗口内超限、窗口过期恢复。
- Redis 断开测试：错误响应不泄露堆栈和敏感信息。

### 10.5 验收标准

- 同一仓库并发索引只有一个 job 可以进入 RUNNING。
- 同一 webhook 事件重复投递不会重复 Review。
- 限流错误可被前端展示。
- Redis 不可用不会造成重复扣配额或脏状态。

## 11. V2L-P4：ReviewHub 团队业务域

### 11.1 目标

把 RepoLens 从单仓库工具升级为有组织、项目、仓库、规则、配额的轻量业务系统，为全栈岗位补业务建模和权限能力。

### 11.2 数据模型

| 表 | 说明 |
| --- | --- |
| `organization` | 组织，包含名称、计划类型、状态 |
| `project` | 项目，归属于组织 |
| `team_member` | 成员与角色：OWNER、MAINTAINER、DEVELOPER、VIEWER |
| `repository_binding` | 项目和仓库绑定，记录 provider、external repo id、webhook secret hash |
| `review_ruleset` | 项目级 Review 规则，包含安全、测试、复杂度、路径规则 |
| `quota_bucket` | 组织/项目/用户/仓库级配额窗口 |
| `audit_log` | 关键业务操作审计 |

### 11.3 工作内容

| 编号 | 工作 | 说明 | 验收 |
| --- | --- | --- | --- |
| P4-001 | Team migration | 新增组织、项目、成员、仓库绑定表 | 空库迁移成功 |
| P4-002 | Seed 默认组织 | 本地 demo 自动创建 `demo-org` 和 `demo-project` | 启动后可直接演示 |
| P4-003 | 轻量 RBAC | OWNER/MAINTAINER 可配置，DEVELOPER 可触发任务，VIEWER 只读 | API 权限测试通过 |
| P4-004 | RepositoryBinding | 绑定 V1 repository 到 project | 项目页能看到仓库 |
| P4-005 | Ruleset API | 创建、启用、禁用、查询 ruleset | Review 前能读取规则 |
| P4-006 | Ruleset 接入 Review | 规则影响风险阈值、路径忽略或测试建议 | Review 报告体现规则 |
| P4-007 | Quota API | 查询、扣减、回滚每日配额 | 超限任务被拒绝 |
| P4-008 | AuditLog | 记录 ruleset 修改、quota 拒绝、job retry/cancel | 审计列表可查 |

### 11.4 API 建议

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/organizations` | 组织列表 |
| `POST` | `/api/organizations/{orgId}/projects` | 创建项目 |
| `POST` | `/api/projects/{projectId}/repositories/{repositoryId}/bind` | 绑定仓库 |
| `GET` | `/api/projects/{projectId}/rulesets` | 查询规则集 |
| `POST` | `/api/projects/{projectId}/rulesets` | 创建规则集 |
| `GET` | `/api/projects/{projectId}/quota` | 查询配额 |
| `GET` | `/api/audit-logs` | 查询审计日志 |

### 11.5 验收标准

- 仓库能归属到项目，任务能按项目过滤。
- Ruleset 能影响 Review 输出。
- 配额超限时不会创建任务或会创建被拒绝事件。
- 关键操作有审计日志。

## 12. V2L-P5：Webhook 与 Review Job 集成

### 12.1 目标

让外部 PR/MR 事件能自动触发 Review job，形成真实团队 ReviewHub 的业务闭环。

### 12.2 支持范围

| 平台 | 事件 | V2-Lite 要求 |
| --- | --- | --- |
| GitHub | `pull_request` opened/synchronize/reopened | 解析 repo、number、sha、sender，校验签名可配置 |
| GitLab | merge request hook | 解析 project、iid、last_commit，支持 self-hosted base url |
| Gitee | pull request hook | 解析 repo、number、head sha，校验 token 可配置 |
| Fixture | 本地 JSON fixture | 无网络时可演示 |

### 12.3 工作内容

| 编号 | 工作 | 说明 | 验收 |
| --- | --- | --- | --- |
| P5-001 | WebhookController | `POST /api/webhooks/{provider}` | 能接收三类平台 fixture |
| P5-002 | SignatureVerifier | GitHub HMAC、GitLab/Gitee token 校验，可在 demo profile 关闭 | 签名错误返回 401 |
| P5-003 | EventParser | 平台 payload -> `ChangeRequestWebhookEvent` | 单测覆盖 GitHub/GitLab/Gitee |
| P5-004 | RepositoryBinding 匹配 | 根据 provider + external repo id 找到本地 repository | 未绑定返回明确错误 |
| P5-005 | Idempotency key | provider + repo + number + sha | 重复事件返回已有 job |
| P5-006 | Quota/RateLimit | 创建 job 前扣配额并限流 | 超限不投递 MQ |
| P5-007 | Review job payload | 保存 change request url/ref、ruleset id、trigger source | Worker 可拉取 diff |
| P5-008 | ReviewService 接入 | 复用 V1/V1.1 Provider 和 ReviewService | 生成 Review 报告 |
| P5-009 | Fixture Runbook | 无 token、无网络时可用 fixture 演示 | 本地 demo 可复现 |

### 12.4 测试要求

- 三个平台 payload parser 单测。
- 签名校验成功/失败测试。
- 重复 webhook 幂等测试。
- 未绑定仓库、配额不足、限流三类失败测试。
- Review job 端到端测试：webhook -> job -> worker -> review report。

### 12.5 验收标准

- 模拟公开 PR/MR webhook 能自动生成 Review job。
- 重复 webhook 不会重复生成 Review 报告。
- Review 报告仍然带 evidence、risk、test suggestion、trace。
- 外部 token、webhook secret 不出现在日志、响应和截图中。

## 13. V2L-P6：前端 ReviewHub 工作台

### 13.1 目标

把后端任务、团队业务和可观测能力做成可演示的全栈界面，让项目不只是后端 API。

### 13.2 页面设计

| 页面/区域 | 内容 |
| --- | --- |
| Team Sidebar | 组织、项目、仓库切换 |
| Job Queue | job 列表、状态筛选、类型筛选、优先级、仓库、耗时 |
| Job Detail | payload 摘要、attempt timeline、event list、retry/cancel |
| Worker Monitor | worker id、状态、heartbeat、当前 job、处理数量 |
| Ruleset | 规则列表、启用状态、路径规则、风险阈值 |
| Quota | 每日配额、已用、剩余、最近拒绝原因 |
| Webhook Events | 最近事件、平台、PR/MR、幂等结果 |
| Metrics | 队列积压、成功率、失败原因、p95 duration |

### 13.3 工作内容

| 编号 | 工作 | 说明 | 验收 |
| --- | --- | --- | --- |
| P6-001 | API Client | 新增 jobs、workers、rulesets、quota、webhooks API 封装 | TypeScript 类型完整 |
| P6-002 | Job Queue tab | 表格、筛选、状态 badge、操作按钮 | 可查看和操作 job |
| P6-003 | Job Detail panel | attempt timeline 和 event stream | 可定位失败原因 |
| P6-004 | Worker Monitor | worker 心跳和当前任务展示 | Worker 中断后 UI 反映 |
| P6-005 | Ruleset form | 新建/启用/禁用规则集 | 表单校验和错误提示 |
| P6-006 | Quota panel | 显示配额使用和拒绝记录 | 超限状态清楚 |
| P6-007 | Webhook simulator | 本地 fixture 一键触发 webhook | Demo 不依赖外网 |
| P6-008 | Metrics cards | queue depth、success rate、p95、dead count | 与后端指标一致 |

### 13.4 交互要求

- Job 状态 badge 使用固定宽度，避免刷新时布局跳动。
- Retry/Cancel 使用图标按钮并有 tooltip。
- 错误信息只展示可理解摘要，详细堆栈不直接暴露。
- 长 payload 默认折叠，避免页面被 JSON 撑开。
- 前端轮询要有退避，不能每秒打爆后端。

### 13.5 验收标准

- 前端能完成一次“模拟 webhook -> 观察 job -> 查看 review report -> 查看 metrics”的完整演示。
- 所有关键操作有 loading、success、error 状态。
- `npm run build` 通过。

## 14. V2L-P7：可观测、压测与发布包装

### 14.1 目标

把 V2-Lite 收束为可展示、可验证、可写进简历的版本，重点证明高并发和分布式设计真的有效。

### 14.2 指标设计

| 指标 | 名称建议 | 说明 |
| --- | --- | --- |
| 队列积压 | `repolens_job_queue_depth` | 按 queue/job_type/status 维度 |
| 任务耗时 | `repolens_job_duration_seconds` | histogram，统计 p50/p95/p99 |
| 任务成功率 | `repolens_job_completed_total` | 按 status/job_type |
| 重试次数 | `repolens_job_retry_total` | 按 error_code |
| 死信数量 | `repolens_job_dead_total` | 排障入口 |
| Worker 心跳 | `repolens_worker_heartbeat_age_seconds` | 判断 worker 是否健康 |
| 限流拒绝 | `repolens_rate_limit_rejected_total` | 按 scope_type |
| 幂等命中 | `repolens_idempotency_hit_total` | 证明重复 webhook 被挡住 |

### 14.3 工作内容

| 编号 | 工作 | 说明 | 验收 |
| --- | --- | --- | --- |
| P7-001 | Actuator 配置 | health、metrics、prometheus endpoint | Prometheus 可抓取 |
| P7-002 | Micrometer 埋点 | job、worker、redis、webhook、quota 指标 | 指标带合理 tag |
| P7-003 | Prometheus 配置 | scrape backend-java | 本地可查询指标 |
| P7-004 | Grafana Dashboard | 队列积压、成功率、失败原因、p95、worker heartbeat | 可截图 |
| P7-005 | 并发验证脚本 | 模拟 100 个重复/不同 webhook | 输出成功/幂等/限流统计 |
| P7-006 | 故障演示 | Worker 中断、Redis 断开、RabbitMQ 重复消息 | 有 runbook |
| P7-007 | 文档更新 | README、demo runbook、release package、简历 bullets | 材料可直接使用 |
| P7-008 | 最终验证 | 后端测试、前端 build、敏感信息扫描 | 全部通过或记录风险 |

### 14.4 压测与故障场景

| 场景 | 目标 |
| --- | --- |
| 100 个相同 webhook | 只创建 1 个 Review job，其余命中幂等 |
| 100 个不同 webhook | API 快速返回，任务进入队列，Worker 按并发度消费 |
| 同仓库 20 个索引任务 | 只有 1 个持有锁，其余排队或被拒绝 |
| Worker 执行中停止 | heartbeat 超时后 job 重新入队 |
| RabbitMQ 重复投递 | 不重复扣配额，不重复生成最终报告 |
| Redis 短暂不可用 | 返回明确错误或走 DB 兜底，不产生脏数据 |

### 14.5 发布包装

新增或更新：

- `docs/repolens-java-v2-lite-demo-runbook.md`
- `docs/repolens-java-v2-lite-final-closure-review.md`
- `docs/repolens-java-v2-lite-design-and-worklog.md`
- README V2-Lite section
- Grafana dashboard JSON
- 前端截图包
- 简历 bullet 和面试讲解稿

### 14.6 验收标准

- Grafana 至少有 4 个核心图表：queue depth、success rate、p95 duration、failure reason。
- 并发验证脚本能证明幂等、限流、锁互斥、Worker 恢复。
- README 能让别人按步骤启动和演示。
- 简历能新增 2-3 条传统 Java 后端深度 bullet。

## 15. 全局 API 汇总

| Method | Path | 阶段 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/api/jobs` | P1 | 创建通用 job |
| `GET` | `/api/jobs` | P1/P6 | 查询 job 列表 |
| `GET` | `/api/jobs/{jobId}` | P1/P6 | 查询 job 详情 |
| `GET` | `/api/jobs/{jobId}/events` | P1/P6 | 查询事件流 |
| `POST` | `/api/jobs/{jobId}/cancel` | P1 | 取消任务 |
| `POST` | `/api/jobs/{jobId}/retry` | P1/P2 | 重试任务 |
| `GET` | `/api/workers` | P2/P6 | Worker 列表 |
| `GET` | `/api/organizations` | P4 | 组织列表 |
| `POST` | `/api/organizations/{orgId}/projects` | P4 | 创建项目 |
| `POST` | `/api/projects/{projectId}/repositories/{repositoryId}/bind` | P4 | 绑定仓库 |
| `GET` | `/api/projects/{projectId}/rulesets` | P4/P6 | 查询规则集 |
| `POST` | `/api/projects/{projectId}/rulesets` | P4/P6 | 创建规则集 |
| `GET` | `/api/projects/{projectId}/quota` | P4/P6 | 查询配额 |
| `POST` | `/api/webhooks/{provider}` | P5 | 接收平台 webhook |
| `GET` | `/api/ops/queue-metrics` | P7/P6 | 查询任务指标摘要 |

## 16. 目录规划

建议新增目录：

```text
backend-java/src/main/java/com/repolens/
  job/
    api/
    application/
    domain/
    infrastructure/
  worker/
    application/
    infrastructure/
  team/
    api/
    application/
    domain/
  quota/
  ruleset/
  webhook/
  ops/
backend-java/src/main/resources/db/migration/
frontend/app/
  # 继续复用现有工作台页面，新增 ReviewHub tabs/components
docs/
  repolens-java-v2-lite-phased-execution-plan.md
  repolens-java-v2-lite-demo-runbook.md
  repolens-java-v2-lite-design-and-worklog.md
  repolens-java-v2-lite-final-closure-review.md
```

## 17. 阶段间依赖

```text
P0 环境
  -> P1 Job Center
    -> P2 MQ Worker
      -> P3 Redis 控制面
        -> P4 业务域
          -> P5 Webhook Review
            -> P6 前端工作台
              -> P7 观测与发布
```

可以并行的部分：

- P4 的组织/项目/仓库模型可以在 P2 后半段开始。
- P6 前端类型和静态页面可以在 P4 API 稳定后开始。
- P7 指标命名可以在 P2 完成后提前设计。

不建议并行的部分：

- P2 不应在 P1 状态机未稳定前开始大量接入业务。
- P5 不应在 P3 幂等和限流未完成前接真实 webhook。
- P7 压测不应在 P2/P3 未闭环前进行。

## 18. 风险与规避

| 风险 | 影响 | 规避 |
| --- | --- | --- |
| 范围膨胀 | V2-Lite 变成完整 SaaS | 严格不做计费、K8s、复杂租户 |
| MQ 重复消息 | 重复 Review、重复扣配额 | DB 状态机 + idempotency key + executor 幂等 |
| Redis 锁误释放 | 并发索引冲突 | owner token 校验释放，长任务续期 |
| Worker 卡死 | job 长期 RUNNING | heartbeat 超时回收 |
| 外部 webhook 不稳定 | Demo 失败 | 默认使用 fixture simulator |
| 权限设计过重 | 开发周期变长 | V2-Lite 只做轻量角色，不接复杂认证 |
| 前端看板过散 | 演示不聚焦 | Job Queue 作为主屏，其他页面为辅助 |

## 19. 最小可交付与推荐可交付

### 19.1 最小可交付

```text
P0 + P1 + P2 + P3
```

能力：

- 有 Job Center。
- 有 RabbitMQ Worker。
- 有 Redis 锁、幂等、限流。
- 能证明异步削峰、重复消息安全、Worker 恢复。

适合：时间紧，但想补传统 Java 后端深度。

### 19.2 推荐可交付

```text
P0 + P1 + P2 + P3 + P4 + P5 + P6 + P7
```

能力：

- ReviewHub 业务闭环完整。
- 有团队、规则、配额、Webhook、看板、Grafana。
- 简历和面试表现力明显增强。

适合：把 RepoLens-Java 作为唯一或最核心简历项目。

## 20. 简历表达

V2-Lite 完成后，建议在 RepoLens-Java 主项目下增加 2-3 条：

```text
- 设计 ReviewHub 分布式任务中心，将仓库索引与 PR/MR Review 抽象为 analysis_job / job_attempt / job_event 状态机，通过 RabbitMQ 异步削峰、Worker 租约心跳、指数退避重试和死信队列支撑批量仓库分析与 Webhook 并发触发。
- 基于 Redis 实现仓库级分布式锁、Webhook 幂等、用户/仓库级限流和任务状态缓存，结合数据库唯一约束保证重复消息安全，避免重复索引、重复 Review 和外部平台 API 过载。
- 建立组织、项目、仓库、Review Ruleset、Quota 和审计日志模型，并通过 Actuator、Micrometer、Prometheus、Grafana 观测队列积压、任务成功率、失败原因和 p95 耗时，形成团队级智能评审平台闭环。
```

## 21. 最终判断

V2-Lite 应当作为 RepoLens-Java 的生产化增强版本，而不是新的独立项目。它保留 RepoLens 原有 AI Code Review 的新度，同时补上 Java 后端岗位非常看重的任务调度、MQ、Redis、幂等、限流、业务建模、可观测和故障恢复能力。

完成 V2-Lite 后，项目叙事可以从：

```text
仓库级 Code Agent 工作台
```

升级为：

```text
面向团队代码仓库的分布式智能评审任务平台
```

这条路线的关联度、技术深度和实用性都比另做一个普通高并发项目更强。
