# RepoLens-Java V1-P1 详细设计：异步索引任务与状态机

## 1. 阶段定位

V1-P1 将 V0 的同步导入升级为任务化索引流水线。该阶段的重点是“可观测、可重试、可查询”，而不是追求真正分布式队列。

本轮实现采用本地线程池和 in-memory repository lock，保留 Redis lock 的接口边界。这样能在本机、CI 和面试 demo 中稳定闭环，后续再替换为 Redis。

## 2. 阶段目标

- 新增 `index_tasks` 和 `index_task_events`。
- 新增索引任务状态机。
- 将 V0 的 scan/parse/chunk/Lucene index 抽成可复用 pipeline。
- `POST /api/repositories` 创建仓库后触发索引任务。
- 新增任务查询和重试 API。
- 同一仓库同一时间只能有一个 active index task。

## 3. 非目标

- 不接真实消息队列。
- 不做分布式 worker。
- 不做增量索引。
- 不做取消任务的强中断。

## 4. 状态机

```text
CREATED
  -> VALIDATING
  -> SCANNING
  -> PARSING
  -> CHUNKING
  -> BM25_INDEXING
  -> VECTOR_INDEXING
  -> GRAPH_BUILDING
  -> READY

任意阶段异常 -> FAILED
FAILED -> retry -> CREATED
```

状态说明：

| 状态 | 说明 |
| --- | --- |
| CREATED | 任务已创建，尚未执行 |
| VALIDATING | 校验仓库路径和任务互斥 |
| SCANNING | 扫描文件和跳过文件 |
| PARSING | 解析代码符号 |
| CHUNKING | 构建 chunk |
| BM25_INDEXING | 重建 Lucene 索引 |
| VECTOR_INDEXING | P3 阶段构建本地向量索引 |
| GRAPH_BUILDING | P2 阶段构建代码图谱 |
| READY | 任务完成，仓库可检索 |
| FAILED | 任务失败，记录错误 |

## 5. 数据模型

### 5.1 `index_tasks`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | varchar(64) | task id |
| repository_id | varchar(64) | 仓库 id |
| status | varchar(64) | 任务状态 |
| current_stage | varchar(64) | 当前阶段 |
| progress_percent | integer | 0-100 |
| last_error | text | 失败原因 |
| started_at | timestamp | 开始时间 |
| finished_at | timestamp | 结束时间 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### 5.2 `index_task_events`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | varchar(64) | event id |
| task_id | varchar(64) | task id |
| repository_id | varchar(64) | repo id |
| stage | varchar(64) | 阶段 |
| status | varchar(32) | STARTED/SUCCEEDED/FAILED |
| message | text | 摘要 |
| file_count | integer | 文件数 |
| chunk_count | integer | chunk 数 |
| symbol_count | integer | symbol 数 |
| relation_count | integer | relation 数 |
| created_at | timestamp | 时间 |

## 6. 后端设计

### 6.1 核心类

| 类 | 职责 |
| --- | --- |
| `IndexTaskEntity` | 索引任务 JPA entity |
| `IndexTaskEventEntity` | 任务事件 JPA entity |
| `IndexTaskStatus` | 任务状态枚举 |
| `IndexTaskJpaRepository` | task repository |
| `IndexTaskEventJpaRepository` | event repository |
| `RepositoryIndexingService` | 创建任务、查询任务、重试任务 |
| `RepositoryIndexPipeline` | 执行 scan/parse/chunk/index |
| `RepositoryIndexLock` | 仓库级索引锁接口 |
| `InMemoryRepositoryIndexLock` | 本地锁实现 |
| `IndexTaskController` | `/api/index-tasks` API |

### 6.2 Pipeline 复用

V0 的 `RepositoryApplicationService.scanRepository` 会迁移到 `RepositoryIndexPipeline`。`RepositoryApplicationService` 只负责创建 repository 和发起任务。

为了保持 V0 API 兼容，本轮默认采用同步等待执行的策略：

- `RepositoryIndexingService.startIndex(repositoryId)` 创建 task。
- test/local profile 中任务立即执行，API 返回时大概率已 READY。
- 后续可以把 executor 替换成真正异步，不影响 task/event API。

## 7. API 设计

| Method | Path | 说明 |
| --- | --- | --- |
| POST | `/api/repositories/{repositoryId}/index` | 手动触发索引 |
| GET | `/api/index-tasks/{taskId}` | 查询任务详情 |
| GET | `/api/repositories/{repositoryId}/index-tasks/latest` | 查询仓库最新任务 |
| POST | `/api/index-tasks/{taskId}/retry` | 失败任务重试 |

任务响应包含：

```json
{
  "id": "task_xxx",
  "repository_id": "repo_xxx",
  "status": "READY",
  "current_stage": "READY",
  "progress_percent": 100,
  "last_error": null,
  "events": []
}
```

## 8. 前端设计

P1 前端最小闭环：

- 仓库状态继续用现有 status panel。
- 如果后端返回 task 信息，展示 current stage 和 progress。
- 失败时展示 last_error 和 retry action。

本轮可以先以后端 API 和测试闭环为主，前端在 P3 统一打磨。

## 9. 测试计划

- `RepositoryIndexingServiceTest`：创建任务、互斥、失败状态。
- `IndexTaskControllerTest`：查询 task、latest task、retry。
- 现有 `RepositoryControllerTest` 继续通过。
- 现有 `RetrievalControllerTest` 继续通过。

## 10. 验收标准

- 导入仓库会创建 index task。
- task events 中能看到 SCANNING、PARSING、CHUNKING、BM25_INDEXING。
- 查询 latest task 可以拿到 READY 状态。
- 同一仓库重复索引不会并发执行。
- 失败时 repository 和 task 都进入 FAILED。

