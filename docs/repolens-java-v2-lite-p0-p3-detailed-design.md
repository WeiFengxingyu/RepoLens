# RepoLens-Java V2-Lite P0-P3 详细设计

## 1. 设计目标

V2-Lite P0-P3 先完成分布式任务平台的最小可运行内核：

```text
P0 环境与配置边界
  -> P1 Job Center 数据模型、状态机、API、幂等创建
  -> P2 Worker Runtime、本地队列、租约、心跳、重试、死信
  -> P3 Redis 语义并发控制：锁、幂等、限流、状态缓存
```

本阶段不强依赖真实 RabbitMQ/Redis 服务，而是先落接口和本地实现，保证离线可测、可演示、可替换。后续 P4-P7 或 V2 完整版再把接口替换为 Spring AMQP / Redis adapter。

## 2. 范围边界

| 阶段 | 做什么 | 暂不做什么 |
| --- | --- | --- |
| P0 | `application-v2-lite.yml`、配置项、包边界、执行模式 | 不引入不可控外部服务依赖 |
| P1 | `analysis_job`、`job_attempt`、`job_event`、`dead_letter_job`、状态机、API | 不做团队业务域 |
| P2 | 本地 worker queue、executor registry、attempt、heartbeat、retry/dead | 不接真实 RabbitMQ |
| P3 | `ConcurrencyControlService`、本地锁、幂等、限流、状态缓存 | 不接真实 Redis |

## 3. 核心模型

### 3.1 Job 类型

| 类型 | 说明 | 执行器 |
| --- | --- | --- |
| `NOOP` | 测试与 smoke 用空任务 | `NoopJobExecutor` |
| `INDEX_REPOSITORY` | 触发仓库重建索引 | `IndexRepositoryJobExecutor` |
| `REVIEW_DIFF` | 触发 pasted diff Review | `ReviewDiffJobExecutor` |

### 3.2 Job 状态机

```text
CREATED -> QUEUED -> RUNNING -> SUCCEEDED
                         ├── FAILED_RETRYABLE -> RETRY_SCHEDULED -> QUEUED
                         ├── DEAD
                         └── CANCELED
```

状态变更必须走 `JobStateMachine`，并由 `JobEventService` 记录事件。

### 3.3 Attempt

每次 Worker 执行创建一条 `job_attempt`：

- `attempt_no` 从 1 递增。
- `worker_id` 记录本地 Worker。
- `heartbeat_at` 表示租约活跃时间。
- 执行失败时写 `error_code` / `error_message`。

### 3.4 Dead Letter

当任务超过最大重试次数，或执行器抛出不可恢复异常时：

- `analysis_job.status = DEAD`
- 写入 `dead_letter_job`
- 写入 `job_event`
- API 可以通过 retry 重新入队

## 4. P0 设计

### 4.1 配置

新增 `repolens.v2-lite` 配置：

| 配置 | 默认值 | 说明 |
| --- | --- | --- |
| `enabled` | `true` | 是否启用 V2-Lite API |
| `worker.local-enabled` | `true` | 是否启用本地 worker queue |
| `worker.pool-size` | `2` | 本地 worker 并发数 |
| `worker.max-attempts` | `3` | 最大尝试次数 |
| `worker.retry-backoff-seconds` | `2` | 重试退避基数 |
| `concurrency.lock-ttl-seconds` | `1800` | 本地锁 TTL |
| `concurrency.idempotency-ttl-seconds` | `86400` | 幂等记录 TTL |
| `concurrency.review-rate-limit-per-minute` | `60` | Review 创建限流 |

### 4.2 Profile

`application-v2-lite.yml` 用于声明 V2-Lite profile。P0-P3 默认使用本地实现，后续可以加入 RabbitMQ/Redis 连接配置。

## 5. P1 设计

### 5.1 数据库

新增 migration `V11__add_v2_lite_jobs.sql`：

- `analysis_jobs`
- `job_attempts`
- `job_events`
- `dead_letter_jobs`

关键约束：

- `analysis_jobs.idempotency_key` 唯一但允许为空。
- `analysis_jobs.repository_id` 允许为空，以支持 `NOOP` 测试任务。
- 所有事件只追加，不修改历史。

### 5.2 API

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/jobs` | 幂等创建任务，可立即 dispatch |
| `GET` | `/api/jobs` | 查询最近任务 |
| `GET` | `/api/jobs/{jobId}` | 查询任务详情 |
| `GET` | `/api/jobs/{jobId}/events` | 查询事件流 |
| `POST` | `/api/jobs/{jobId}/retry` | 失败/死信任务重新入队 |
| `POST` | `/api/jobs/{jobId}/cancel` | 取消非终态任务 |
| `GET` | `/api/workers` | 查询本地 worker 心跳 |

## 6. P2 设计

### 6.1 Worker Runtime

`LocalJobDispatcher` 使用 JVM 内线程池模拟 MQ：

```text
JobService.create()
  -> status: CREATED
  -> JobDispatchService.dispatch()
  -> status: QUEUED
  -> LocalJobDispatcher.enqueue(jobId)
  -> JobWorkerService.process(jobId)
```

该设计刻意保留 `JobDispatcher` 接口，后续可替换为 RabbitMQ。

### 6.2 执行器

| 执行器 | 复用服务 |
| --- | --- |
| `NoopJobExecutor` | 无，用于测试 |
| `IndexRepositoryJobExecutor` | `RepositoryIndexingService.startIndex()` |
| `ReviewDiffJobExecutor` | `ReviewService.review()` |

### 6.3 重试策略

- `RetryableJobException`：进入 `FAILED_RETRYABLE`，未超过次数则 `RETRY_SCHEDULED` 并重新 dispatch。
- 其他异常：超过次数后进入 `DEAD`。
- `maxAttempts` 从配置读取。

## 7. P3 设计

### 7.1 并发控制接口

`ConcurrencyControlService` 负责：

- 分布式锁语义：`tryAcquireLock` / `releaseLock`
- 幂等记录：`rememberIdempotency` / `findIdempotency`
- 固定窗口限流：`checkRateLimit`
- 状态缓存：`cacheJobStatus` / `getCachedJobStatus`

P0-P3 使用 `LocalConcurrencyControlService`，后续替换为 Redis。

### 7.2 使用点

| 使用点 | 行为 |
| --- | --- |
| Job 创建 | 先查本地幂等，再查 DB 唯一键 |
| Review job | 按 `created_by` 或 repository 做限流 |
| Index executor | 使用 `lock:repo:{repositoryId}:index` 防重复索引 |
| Job 查询 | 任务状态写入本地状态缓存 |

## 8. 验收标准

| 阶段 | 验收 |
| --- | --- |
| P0 | 后端可以用默认 profile 启动，V2-Lite 配置可绑定 |
| P1 | Job API 支持幂等创建、查询、事件流、取消、重试 |
| P2 | `NOOP` job 可异步完成，失败任务可重试并进入 dead letter |
| P3 | 重复 idempotency key 返回同一 job；限流、锁和状态缓存有测试覆盖 |

## 9. 测试计划

- `JobStateMachineTest`
- `LocalConcurrencyControlServiceTest`
- `JobControllerTest`
- `JobWorkerServiceTest`

最终 P0-P3 闭环以 `mvn test` 作为验证命令。
