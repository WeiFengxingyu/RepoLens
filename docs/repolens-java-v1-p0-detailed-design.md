# RepoLens-Java V1-P0 详细设计：基线固化与工程准备

## 1. 阶段定位

V1-P0 是 V1 的工程基线阶段，目标不是新增业务亮点，而是把 V0 的同步导入、BM25 检索、Java 解析能力整理成可继续演进的 V1 基座。

P0 完成后，后续 P1-P3 可以在现有 `backend-java/` 和 `frontend/` 上增量开发，不需要新建项目目录，也不需要重写 V0。

## 2. 阶段目标

- 保持 V0 API 和测试兼容。
- 明确 V1 后端模块边界。
- 增加 local/test/demo profile 约定。
- 建立 V1 共用过程记录文档。
- 为 P1 异步索引、P2 图谱、P3 混合检索预留配置和包结构。

## 3. 非目标

- P0 不引入真实 Redis、Qdrant、PGvector 或外部 LLM。
- P0 不改变前端产品形态。
- P0 不删除旧 Python 后端。
- P0 不做大规模重构。

## 4. 当前基线

| 能力 | 当前状态 |
| --- | --- |
| Java 版本 | Java 21 |
| 后端框架 | Spring Boot 3.3.5 |
| 数据库 | H2 local/test，PostgreSQL driver 已存在 |
| Migration | Flyway V1/V2 |
| 解析 | JavaParser，支持 Java class/method/route metadata |
| 检索 | Lucene BM25 |
| API | `/api/repositories`、`/api/repositories/{id}/retrieve` |
| 前端 | 已可调用 Java 后端并展示 evidence |

## 5. 后端设计

### 5.1 Profile

V1 采用三个 profile：

| Profile | 用途 | 数据/依赖策略 |
| --- | --- | --- |
| default/local | 本地开发 | H2 file、local index、mock vector |
| test | 自动化测试 | H2 memory、mock vector、同步 executor |
| demo | 面试演示 | H2 file、固定 demo data、mock provider 可复现 |

### 5.2 配置项

新增或确认以下配置：

```yaml
repolens:
  version: v1
  workspace-root: ./.repolens-java/repos
  index-root: ./.repolens-java/indexes
  indexing:
    async-enabled: true
    max-active-tasks-per-repository: 1
  retrieval:
    default-top-k: 10
    vector-enabled: true
    graph-enabled: true
```

### 5.3 包结构

```text
com.repolens
  common
  config
  repository
  scanner
  parser
  chunking
  indexing
    application
    domain
    infrastructure
    lexical
  graph
    application
    api
    domain
    infrastructure
  retrieval
    api
    application
    vector
  evaluation
```

P0 只建立配置和文档，不强行创建空包。P1-P3 按需新增。

## 6. API 兼容策略

V0 的 `POST /api/repositories` 已被前端使用，P1 改为异步后需要兼容：

| API | P0/P1 兼容策略 |
| --- | --- |
| `POST /api/repositories` | 继续返回 repository detail；P1 中会创建索引任务并快速返回 |
| `GET /api/repositories/{id}/status` | 继续返回 repository status，同时通过 progress 暴露任务状态 |
| `POST /api/repositories/{id}/retrieve` | P3 前仍支持 BM25；P3 后支持 vector/graph |

## 7. 文档设计

V1 采用一份共用过程记录：

```text
docs/repolens-java-v1-design-and-worklog.md
```

每个阶段执行前单独有详细设计：

```text
docs/repolens-java-v1-p0-detailed-design.md
docs/repolens-java-v1-p1-detailed-design.md
docs/repolens-java-v1-p2-detailed-design.md
docs/repolens-java-v1-p3-detailed-design.md
```

## 8. 测试计划

- 运行 `mvn test` 确认 V0 基线不破。
- 检查 `application.yml`、`application-demo.yml`、`src/test/resources/application.yml` profile 可加载。
- 检查 docs index 包含 V1 P0-P3 设计文档和 V1 worklog。

## 9. 验收标准

- P0 详细设计文档存在。
- V1 共用过程记录文档存在。
- 配置中有 V1 profile/配置入口。
- V0 测试仍通过。
- 后续 P1-P3 的执行记录有统一落点。

