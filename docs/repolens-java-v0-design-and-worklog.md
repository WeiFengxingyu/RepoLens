# RepoLens-Java V0 轻量详细设计与执行记录

## 1. 文档信息

| 字段 | 内容 |
| --- | --- |
| 项目 | RepoLens-Java |
| 版本 | V0：Java 后端最小可运行闭环 |
| 文档类型 | V0 子阶段共用的轻量详细设计 + 执行记录 |
| 创建日期 | 2026-06-28 |
| 执行方式 | 每个子阶段先补轻量详细设计，再实施，再记录执行结果、验证结果和偏差 |
| 依据 | `docs/repolens-java-v0-execution-plan.md` |

## 2. V0 闭环目标

V0 闭环目标：

```text
本地仓库导入
  -> 文件扫描与过滤
  -> Java 类/方法解析
  -> 方法级 Chunk 构建
  -> Lucene BM25 索引
  -> Evidence 检索 API
  -> Next.js 工作台展示仓库状态和 Evidence
```

V0 明确不做 Spring AI、MCP、向量库、PR Review 和多用户权限。V0 的成功标准是 Java 后端可以独立跑通 RepoLens 的基础索引和检索链路。

## 3. 阶段执行规范

每个 V0 子阶段使用同一格式记录：

```text
目标
范围
设计决策
涉及文件 / 类 / API / 表
执行步骤
测试与验收
执行记录
偏差与后续处理
```

状态标记：

| 状态 | 说明 |
| --- | --- |
| `TODO` | 尚未开始 |
| `DESIGNED` | 已完成轻量详细设计，尚未实施 |
| `IN_PROGRESS` | 正在实施 |
| `DONE` | 已实施并完成该阶段验收 |
| `PARTIAL` | 已部分完成，有明确剩余项 |
| `BLOCKED` | 阻塞，需外部输入或环境变化 |

## 4. V0 子阶段总览

| 阶段 | 名称 | 状态 |
| --- | --- | --- |
| V0-0 | 开发准备 | DONE |
| V0-1 | Spring Boot 工程骨架 | DONE |
| V0-2 | 数据库与 Flyway | DONE |
| V0-3 | Repository API 与本地导入 | DONE |
| V0-4 | Scanner 文件扫描与过滤 | DONE |
| V0-5 | Java Parser | DONE |
| V0-6 | Chunk Builder | DONE |
| V0-7 | Lucene BM25 检索 | DONE |
| V0-8 | 前端适配与 Evidence 展示 | DONE |
| V0-9 | 测试、Demo Runbook 与收尾 | DONE |

## 5. V0-0：开发准备

### 5.1 目标

确认 RepoLens 当前目录、旧项目资产、Java/Maven/Node 工具链和 V0 开发目录策略，为后续 V0-1 开工提供事实依据。

### 5.2 范围

本阶段只做检查和记录，不写业务代码。

检查内容：

- RepoLens 根目录结构。
- docs 中 Java Edition 规划文档是否存在。
- Java、Maven、Gradle、Node 工具链。
- 后续开发目录策略。

### 5.3 设计决策

1. V0 在原 RepoLens 项目内开发，不新建独立 `RepoLens-Java` 仓库。
2. 新 Java 后端放在 `backend-java/`。
3. 旧 Python 后端 `backend/` 保留为 legacy/prototype，不在 V0 修改。
4. 前端继续复用 `frontend/`，V0-8 时适配 Java API。
5. V0 子阶段共用本文件作为“轻量详细设计 + 执行记录”。
6. 初始检查时本地只有 Java 17 + Maven 3.9.7，Gradle 不可用。随后已通过 Chocolatey 安装 Microsoft OpenJDK 21，并新增项目级 Java 版本切换脚本。V0 采用 Maven + Java 21 落地。

### 5.4 涉及文件 / 类 / API / 表

本阶段新增：

```text
docs/repolens-java-v0-design-and-worklog.md
```

本阶段不新增代码类、API 和数据表。

### 5.5 执行步骤

已执行检查命令：

```powershell
Get-ChildItem -Force
Get-ChildItem -Force docs
java -version
mvn -version
gradle -version
node -v
```

### 5.6 测试与验收

验收项：

- [x] 确认工作目录为 `F:\Desktop\agent\RepoLens`。
- [x] 确认旧 `backend/`、`frontend/`、`evals/`、`docs/` 存在。
- [x] 确认 Java Edition 规划文档存在。
- [x] 确认 Java 可用。
- [x] 确认 Maven 可用。
- [x] 确认 Node 可用。
- [x] 确认 Gradle 不可用，并决定 V0 使用 Maven。

### 5.7 执行记录

当前 RepoLens 根目录包含：

```text
backend/
frontend/
evals/
docs/
scripts/
docker-compose.yml
README.md
```

当前 Java Edition 文档已存在：

```text
docs/repolens-java-requirements-outline-design.md
docs/repolens-java-development-roadmap.md
docs/repolens-java-v0-execution-plan.md
```

工具链检查结果：

```text
Java: 初始为 17.0.11，后续已安装 21.0.11
Maven: 3.9.7
Gradle: not found
Node: v20.14.0
```

### 5.8 偏差与后续处理

偏差：

- 初始环境没有 Java 21，且 Chocolatey 安装 Temurin21 时 GitHub MSI 下载长时间 pending。

处理：

- 停止 pending 的 Temurin21 安装并清理 Chocolatey 记录。
- 改用 `choco install microsoft-openjdk-21 -y` 成功安装 Microsoft OpenJDK 21。
- 新增 `scripts/use-java.ps1`，支持当前 PowerShell 会话切换 Java 8、17、21。
- `backend-java` 已使用 Java 21 编译目标。

## 6. V0-1：Spring Boot 工程骨架

### 6.1 目标

创建 `backend-java` Maven/Spring Boot 工程，提供可启动后端、基础配置和状态 API，为后续数据库、Repository API、Scanner、Parser 等模块提供工程骨架。

### 6.2 范围

本阶段只实现工程基础能力：

- Maven `pom.xml`
- Spring Boot 启动类
- 配置属性类
- 统一 API 响应的最小错误处理
- `/health`
- `/api/status`
- 基础测试

本阶段不引入：

- 数据库
- Flyway
- Lucene
- JavaParser
- Repository 导入业务

### 6.3 设计决策

1. 使用 Maven，而不是 Gradle，因为当前本地 Maven 可用，Gradle 不可用。
2. 使用 Java 21 编译，贴合最终简历目标。
3. 包名使用 `com.repolens`。
4. 配置根为 `repolens`，通过 `@ConfigurationProperties` 绑定。
5. V0-1 的 `/api/status` 不检查数据库，只返回服务、版本、workspaceRoot、indexRoot。
6. V0-1 使用 Spring Boot Actuator 提供标准健康检查，同时额外提供 `/health` 兼容旧前端/旧后端习惯。

### 6.4 涉及文件 / 类 / API / 表

计划新增：

```text
backend-java/pom.xml
backend-java/src/main/java/com/repolens/RepoLensJavaApplication.java
backend-java/src/main/java/com/repolens/config/RepoLensProperties.java
backend-java/src/main/java/com/repolens/status/StatusController.java
backend-java/src/main/java/com/repolens/status/StatusResponse.java
backend-java/src/main/java/com/repolens/common/error/ApiErrorResponse.java
backend-java/src/main/java/com/repolens/common/error/GlobalExceptionHandler.java
backend-java/src/main/resources/application.yml
backend-java/src/test/java/com/repolens/RepoLensJavaApplicationTests.java
backend-java/src/test/java/com/repolens/status/StatusControllerTest.java
```

API：

```text
GET /health
GET /api/status
```

数据表：

```text
无
```

### 6.5 执行步骤

1. 新建 `backend-java` Maven 工程目录。
2. 编写 `pom.xml`，引入 Spring Web、Validation、Actuator、Configuration Processor、Test。
3. 编写启动类。
4. 编写 `RepoLensProperties` 和 `application.yml`。
5. 编写 `StatusController`。
6. 编写最小异常响应类。
7. 编写 Spring context 测试和 status API 测试。
8. 运行 `mvn test`。

### 6.6 测试与验收

验收项：

- [x] `backend-java` 目录存在。
- [x] Maven 工程可以编译。
- [x] Spring context 可以启动。
- [x] `GET /health` 返回 `{"status":"ok"}`。
- [x] `GET /api/status` 返回 service/version/status/storage。
- [x] `mvn test` 通过。

### 6.7 执行记录

已新增 `backend-java` Maven/Spring Boot 工程：

```text
backend-java/pom.xml
backend-java/.mvn/maven.config
backend-java/src/main/java/com/repolens/RepoLensJavaApplication.java
backend-java/src/main/java/com/repolens/config/RepoLensProperties.java
backend-java/src/main/java/com/repolens/status/HealthResponse.java
backend-java/src/main/java/com/repolens/status/StatusController.java
backend-java/src/main/java/com/repolens/status/StatusResponse.java
backend-java/src/main/java/com/repolens/common/error/ApiErrorResponse.java
backend-java/src/main/java/com/repolens/common/error/GlobalExceptionHandler.java
backend-java/src/main/resources/application.yml
backend-java/src/test/java/com/repolens/RepoLensJavaApplicationTests.java
backend-java/src/test/java/com/repolens/status/StatusControllerTest.java
```

为避免全局 Maven settings 将依赖写入不可写目录，新增：

```text
backend-java/.mvn/maven.config
```

内容：

```text
-Dmaven.repo.local=../.m2/repository
```

验证命令：

```powershell
.\scripts\use-java.ps1 21
cd backend-java
mvn -q test
```

验证结果：

```text
Java: Microsoft OpenJDK 21.0.11
Tests run: 3
Failures: 0
Errors: 0
```

### 6.8 偏差与后续处理

偏差：

- 全局 Maven settings 将 localRepository 固定到 `F:\apache-maven-3.9.7\repository`，沙箱不可写。

处理：

- 使用项目级 `backend-java/.mvn/maven.config` 将 Maven 本地仓库切到 `RepoLens/.m2/repository`。
- 已在 `.gitignore` 忽略 `.m2/` 和 `target/`。

偏差：

- Java 21 安装过程里 Temurin21 下载卡住。

处理：

- 改用 Microsoft OpenJDK 21，安装成功并通过测试。

## 7. V0-2：数据库与 Flyway

### 7.1 目标

建立 V0 最小数据库基础，支持仓库记录、扫描文件记录和代码 Chunk 持久化。引入 Flyway 管理 schema，确保后续 Repository Import、Scanner、Parser、Chunk Builder 都有稳定数据落点。

### 7.2 范围

本阶段实现：

- Spring Data JPA
- Flyway
- H2 测试/开发默认数据库
- PostgreSQL runtime driver，为后续 Docker Compose/PostgreSQL 预留
- `repositories` 表
- `repository_files` 表
- `code_chunks` 表
- 对应 JPA Entity 与 JpaRepository
- 数据库 smoke test

本阶段不实现：

- Repository API 导入逻辑
- Scanner 业务逻辑
- Parser 业务逻辑
- Lucene 检索
- `search_evidences` 持久化

### 7.3 设计决策

1. V0-2 使用 Flyway SQL migration，而不是 Hibernate 自动建表，保证 schema 可审计。
2. `spring.jpa.hibernate.ddl-auto=validate`，让 JPA 实体必须和 Flyway schema 对齐。
3. 默认 profile 使用 H2 file DB，降低 V0 启动门槛；后续 Docker/PostgreSQL 通过 profile/env 切换。
4. Entity 使用字符串 ID，后续可以统一接入 `IdGenerator` 生成 `repo_`、`file_`、`chunk_` 前缀 ID。
5. JSON 类字段 V0 暂用 `text` 存储，避免过早绑定 PostgreSQL `jsonb`。
6. 时间字段使用 `Instant`，由应用层写入，V0 不依赖数据库默认值。

### 7.4 涉及文件 / 类 / API / 表

计划新增或修改：

```text
backend-java/pom.xml
.gitignore
backend-java/src/main/resources/application.yml
backend-java/src/main/resources/db/migration/V1__init_v0_schema.sql
backend-java/src/main/java/com/repolens/repository/domain/RepositoryEntity.java
backend-java/src/main/java/com/repolens/repository/domain/RepositoryFileEntity.java
backend-java/src/main/java/com/repolens/repository/domain/RepositoryStatus.java
backend-java/src/main/java/com/repolens/repository/domain/RepositorySourceType.java
backend-java/src/main/java/com/repolens/repository/infrastructure/RepositoryJpaRepository.java
backend-java/src/main/java/com/repolens/repository/infrastructure/RepositoryFileJpaRepository.java
backend-java/src/main/java/com/repolens/chunking/domain/CodeChunkEntity.java
backend-java/src/main/java/com/repolens/chunking/domain/ChunkType.java
backend-java/src/main/java/com/repolens/chunking/infrastructure/CodeChunkJpaRepository.java
backend-java/src/test/resources/application.yml
backend-java/src/test/java/com/repolens/persistence/V0SchemaIntegrationTest.java
```

数据表：

```text
repositories
repository_files
code_chunks
```

API：

```text
本阶段不新增 API
```

### 7.5 执行步骤

1. 在 `pom.xml` 加入 Spring Data JPA、Flyway、H2、PostgreSQL。
2. 在 `application.yml` 配置 H2 datasource、Flyway、JPA validate。
3. 编写 `V1__init_v0_schema.sql`。
4. 编写 Repository/RepositoryFile/CodeChunk 实体。
5. 编写枚举与 JpaRepository。
6. 编写集成测试，验证 Flyway 建表、JPA save/find、实体字段映射。
7. 使用 Java 21 运行 `mvn test`。

### 7.6 测试与验收

验收项：

- [x] Maven 测试环境能启动 H2。
- [x] Flyway 自动执行 `V1__init_v0_schema.sql`。
- [x] JPA validate 通过。
- [x] 可以保存并查询 RepositoryEntity。
- [x] 可以保存并查询 RepositoryFileEntity。
- [x] 可以保存并查询 CodeChunkEntity。
- [x] `mvn test` 通过。

### 7.7 执行记录

已完成内容：

- `backend-java/pom.xml` 新增 JPA、Flyway、H2、PostgreSQL driver。
- `application.yml` 配置默认 H2 file DB、Flyway、JPA validate。
- `V1__init_v0_schema.sql` 创建 `repositories`、`repository_files`、`code_chunks`。
- 新增 Repository、RepositoryFile、CodeChunk 三组 Entity、Enum 和 JpaRepository。
- 新增 `V0SchemaIntegrationTest` 验证 Flyway migration、JPA save/find 和字段映射。
- 新增 `src/test/resources/application.yml`，测试使用内存 H2，避免本地 file DB 历史数据污染。
- `.gitignore` 忽略 `.repolens-java/`、`.m2/`、`target/`。

验证命令：

```powershell
.\scripts\use-java.ps1 21
cd backend-java
mvn -q test
```

验证结果：

```text
Java: Microsoft OpenJDK 21.0.11
Flyway: validated 1 migration, applied V1__init_v0_schema.sql
Spring Data JPA: found 3 JPA repository interfaces
Test result: 4 tests, 0 failures, 0 errors, 0 skipped
```

### 7.8 偏差与后续处理

偏差：

- 第一次引入测试配置时覆盖了 `repolens.version` 和 workspace/index 目录，导致 `StatusControllerTest` 失败。
- 默认应用配置使用 H2 file DB，会在本地生成 `.repolens-java/` 运行时数据。
- Flyway 对当前 H2 版本输出 upgrade recommended warning。

处理：

- 测试配置最终只覆盖 datasource/Flyway/JPA，不覆盖业务配置项。
- `.repolens-java/` 已加入 `.gitignore`，本地运行数据不进入版本控制。
- Flyway warning 不影响 V0 验收；后续引入 PostgreSQL profile 后以 PostgreSQL 作为更接近生产的验证环境。

## 8. V0-3：Repository API 与本地导入

### 8.1 目标

实现仓库管理最小 API，让前端或调用方可以把一个本地代码目录注册为 RepoLens 仓库记录，并为后续 Scanner、Parser、Chunk Builder、Lucene Indexer 提供稳定的 repositoryId 和数据库落点。

本阶段的“导入”定义为：完成本地路径校验、仓库元数据入库、状态可查询。扫描、解析、Chunk 构建和索引在 V0-4 到 V0-7 逐步接入，不在 V0-3 抢跑。

### 8.2 范围

本阶段实现：

- `POST /api/repositories`
- `GET /api/repositories`
- `GET /api/repositories/{repositoryId}`
- `GET /api/repositories/{repositoryId}/status`
- 本地路径规范化与安全校验。
- Repository 创建、列表、详情、状态查询。
- 与旧前端兼容的 snake_case 响应字段。
- 与计划文档兼容的 `sourceType/localPath` 请求字段。
- 与旧前端兼容的 `source/name/branch` 请求字段。

本阶段不实现：

- Git clone。
- 文件扫描。
- JavaParser 解析。
- Chunk 构建。
- Lucene 索引。
- 异步任务进度。

### 8.3 设计决策

1. API 路径复用旧前端契约：`/api/repositories`。
2. 响应字段优先兼容旧前端，使用 `source_type`、`file_count`、`chunk_count`、`updated_at` 等 snake_case。
3. Java 内部继续使用 camelCase，DTO 字段通过 `@JsonProperty` 显式声明 JSON 名称，避免全局 Jackson 命名策略影响 `/api/status`。
4. 创建请求同时兼容两种格式：

```json
{
  "source": "F:/Desktop/agent/RepoLens/evals/demo_repos/java_service",
  "name": "java_service"
}
```

```json
{
  "sourceType": "LOCAL",
  "localPath": "F:/Desktop/agent/RepoLens/evals/demo_repos/java_service",
  "name": "java_service"
}
```

5. V0-3 只支持本地目录。`sourceType=GIT` 或明显的远程地址先返回 400，后续版本再接 Git provider。
6. 数据库中的 `RepositoryStatus.CREATED` 对外映射为 `pending`，保持前端类型兼容。
7. 通过 `IdGenerator` 生成 `repo_` 前缀 ID，避免将 UUID 生成逻辑散落在业务服务中。
8. 路径使用 `Path.toAbsolutePath().normalize()` 后再校验和持久化。
9. 不允许导入文件系统根目录或用户主目录，避免误扫整盘。
10. `repositories` 表补充 `commit_hash`、`parsed_file_count`、`relation_count`，通过 V2 migration 演进，不修改 V1。

### 8.4 涉及文件 / 类 / API / 表

计划新增或修改：

```text
backend-java/src/main/resources/db/migration/V2__extend_repository_api_fields.sql
backend-java/src/main/java/com/repolens/common/error/ResourceNotFoundException.java
backend-java/src/main/java/com/repolens/common/id/IdGenerator.java
backend-java/src/main/java/com/repolens/repository/api/RepositoryController.java
backend-java/src/main/java/com/repolens/repository/api/dto/CreateRepositoryRequest.java
backend-java/src/main/java/com/repolens/repository/api/dto/RepositoryDetailResponse.java
backend-java/src/main/java/com/repolens/repository/api/dto/RepositoryProgressResponse.java
backend-java/src/main/java/com/repolens/repository/api/dto/RepositoryStatusResponse.java
backend-java/src/main/java/com/repolens/repository/api/dto/RepositorySummaryResponse.java
backend-java/src/main/java/com/repolens/repository/application/RepositoryApplicationService.java
backend-java/src/main/java/com/repolens/repository/application/RepositoryImportCommand.java
backend-java/src/main/java/com/repolens/repository/application/RepositoryMapper.java
backend-java/src/main/java/com/repolens/repository/application/RepositoryPathValidator.java
backend-java/src/main/java/com/repolens/repository/domain/RepositoryEntity.java
backend-java/src/main/java/com/repolens/repository/infrastructure/RepositoryJpaRepository.java
backend-java/src/test/java/com/repolens/repository/api/RepositoryControllerTest.java
```

API：

```text
POST /api/repositories
GET /api/repositories
GET /api/repositories/{repositoryId}
GET /api/repositories/{repositoryId}/status
```

数据表变更：

```text
repositories.commit_hash
repositories.parsed_file_count
repositories.relation_count
```

### 8.5 执行步骤

1. 新增 V2 migration，扩展 Repository API 需要的统计字段。
2. 扩展 `RepositoryEntity` 字段和 getter/setter。
3. 扩展 `RepositoryJpaRepository`，支持按创建时间倒序查询。
4. 新增 `IdGenerator`。
5. 新增路径校验组件。
6. 新增 Repository DTO 和 mapper。
7. 新增 `RepositoryApplicationService`。
8. 新增 `RepositoryController`。
9. 扩展全局异常处理，支持 404。
10. 编写 MockMvc 测试覆盖创建、列表、详情、状态和错误路径。
11. 使用 Java 21 运行 `mvn test`。

### 8.6 测试与验收

验收项：

- [x] `POST /api/repositories` 可以用 `source/name` 创建本地仓库记录。
- [x] `POST /api/repositories` 可以用 `sourceType/localPath/name` 创建本地仓库记录。
- [x] 创建响应包含前端兼容的 snake_case 字段。
- [x] `GET /api/repositories` 返回列表。
- [x] `GET /api/repositories/{repositoryId}` 返回详情。
- [x] `GET /api/repositories/{repositoryId}/status` 返回状态和 progress。
- [x] 不存在的 repositoryId 返回 404。
- [x] 不存在路径、文件路径、根目录、用户主目录等非法路径返回 400。
- [x] `mvn test` 通过。

### 8.7 执行记录

已完成内容：

- 新增 `V2__extend_repository_api_fields.sql`，为 Repository API 补充 `commit_hash`、`parsed_file_count`、`relation_count`。
- 扩展 `RepositoryEntity` 和 `RepositoryJpaRepository`，支持前端所需统计字段和按创建时间倒序列表。
- 新增 `IdGenerator`，统一生成 `repo_` 前缀 ID。
- 新增 `RepositoryPathValidator`，完成本地路径规范化、存在性、目录、可读、根目录和用户主目录校验。
- 新增 Repository API DTO，响应字段显式使用 snake_case，兼容旧前端类型。
- 新增 `RepositoryApplicationService` 和 `RepositoryMapper`，将 HTTP DTO、领域实体和前端响应契约解耦。
- 新增 `RepositoryController`，提供创建、列表、详情、状态四个接口。
- 扩展全局异常处理，支持 400 参数错误和 404 资源不存在。
- 新增 `RepositoryControllerTest`，覆盖成功创建、兼容请求格式、查询接口、404、非法路径、Git 源拒绝等场景。

验证命令：

```powershell
.\scripts\use-java.ps1 21
cd backend-java
mvn -q test
```

验证结果：

```text
Java: Microsoft OpenJDK 21.0.11
Flyway: validated 2 migrations, schema version v2
RepositoryControllerTest: 8 tests, 0 failures, 0 errors, 0 skipped
V0SchemaIntegrationTest: 1 test, 0 failures, 0 errors, 0 skipped
StatusControllerTest: 2 tests, 0 failures, 0 errors, 0 skipped
RepoLensJavaApplicationTests: 1 test, 0 failures, 0 errors, 0 skipped
Total: 12 tests passed
```

### 8.8 偏差与后续处理

偏差：

- 原计划文档示例使用 camelCase 响应字段，但当前前端类型和旧 Python 后端使用 snake_case。
- 编写测试时辅助方法最初命名为 `jsonPath`，遮蔽了 MockMvc 的 `jsonPath` 断言方法，导致测试编译失败。

处理：

- V0-3 采用 snake_case JSON 响应，优先兼容现有前端；Java 内部仍保持 camelCase。
- DTO 使用 `@JsonProperty` 显式控制字段名，不启用全局 Jackson snake_case 策略，避免影响既有 `/api/status` 响应。
- 测试辅助方法改名为 `jsonEscapedPath`，编译问题已修复并通过全量测试。

## 9. V0-4：Scanner 文件扫描与过滤

### 9.1 目标

将 V0-3 创建的本地仓库记录推进到文件扫描阶段：遍历仓库目录，过滤依赖目录、缓存目录、敏感文件、大文件、二进制文件和符号链接，识别文件语言，计算内容 hash，写入 `repository_files`，并更新 `repositories` 的文件数、跳过文件数、语言统计和状态。

V0-4 完成后，系统应具备“仓库导入 -> 文件清单落库”的可运行链路，V0-5 Java Parser 可以直接消费 `repository_files` 中未跳过且语言为 `JAVA` 的文件。

### 9.2 范围

本阶段实现：

- `scanner/RepositoryScanner`
- `scanner/ScannedFile`
- `scanner/SkippedFile`
- `scanner/ScanResult`
- `scanner/FileLanguageDetector`
- `scanner/FileSkipPolicy`
- `scanner/ContentHashService`
- `scanner/SkipReason`
- `scanner/Language`
- Repository 导入时同步执行 scan。
- `repository_files` 写入扫描文件和跳过文件。
- 更新 Repository 状态：`CREATED -> SCANNING -> READY`。
- 更新 Repository 统计：`file_count`、`skipped_file_count`、`language_summary`、`updated_at`。

本阶段不实现：

- JavaParser 解析。
- Chunk 构建。
- Lucene 索引。
- 异步任务和进度百分比。
- Git clone。

### 9.3 设计决策

1. V0-4 复用旧 Python Scanner 的过滤思想，但用 Java NIO 实现。
2. 文件遍历使用 `Files.walkFileTree`，方便控制目录剪枝、符号链接和异常处理。
3. 默认不跟随 symlink；如果配置打开 `repolens.scanner.follow-symlinks`，V0 仍需防止相对路径逃逸。
4. 相对路径统一存储为 `/` 分隔，避免 Windows 路径影响后续 Lucene 和前端展示。
5. `file_count` 统计未跳过文件总数，`skipped_file_count` 统计跳过文件和跳过目录标记数。
6. `language_summary` 只统计未跳过文件中已识别语言的数量，V0 重点支持 `JAVA`，并识别 `XML`、`YAML`、`JSON`、`MARKDOWN`、`PROPERTIES`、`KOTLIN`、`UNKNOWN`。
7. `content_hash` 使用 SHA-256，后续可用于增量扫描和避免重复解析。
8. 忽略目录包括 `.git`、`node_modules`、`target`、`build`、`.gradle`、`.idea`、`.mvn/wrapper`、缓存目录等。
9. 敏感/二进制/产物文件通过 glob 文件名和扩展名过滤，例如 `.env`、`*.pem`、`*.key`、`*.crt`、`*.p12`、`*.class`、`*.jar`、图片、压缩包、数据库文件。
10. V0-4 同步扫描失败时将 repository 标记为 `FAILED` 并写入 `last_error`，API 返回失败详情而不是让后端崩溃。

### 9.4 涉及文件 / 类 / API / 表

计划新增或修改：

```text
backend-java/src/main/java/com/repolens/scanner/ContentHashService.java
backend-java/src/main/java/com/repolens/scanner/FileLanguageDetector.java
backend-java/src/main/java/com/repolens/scanner/FileSkipPolicy.java
backend-java/src/main/java/com/repolens/scanner/Language.java
backend-java/src/main/java/com/repolens/scanner/RepositoryScanner.java
backend-java/src/main/java/com/repolens/scanner/ScanResult.java
backend-java/src/main/java/com/repolens/scanner/ScannedFile.java
backend-java/src/main/java/com/repolens/scanner/ScannerException.java
backend-java/src/main/java/com/repolens/scanner/SkipReason.java
backend-java/src/main/java/com/repolens/scanner/SkippedFile.java
backend-java/src/main/java/com/repolens/repository/application/RepositoryApplicationService.java
backend-java/src/main/java/com/repolens/repository/application/RepositoryMapper.java
backend-java/src/main/java/com/repolens/repository/domain/RepositoryFileEntity.java
backend-java/src/main/java/com/repolens/repository/infrastructure/RepositoryFileJpaRepository.java
backend-java/src/test/java/com/repolens/scanner/RepositoryScannerTest.java
backend-java/src/test/java/com/repolens/repository/api/RepositoryControllerTest.java
```

API：

```text
POST /api/repositories
GET /api/repositories
GET /api/repositories/{repositoryId}
GET /api/repositories/{repositoryId}/status
```

数据表：

```text
repository_files
repositories.file_count
repositories.skipped_file_count
repositories.language_summary
repositories.status
```

### 9.5 执行步骤

1. 编写 scanner value objects、enum 和异常类。
2. 编写 `FileLanguageDetector`。
3. 编写 `FileSkipPolicy`，覆盖目录、文件名、大小、二进制、symlink。
4. 编写 `ContentHashService`。
5. 编写 `RepositoryScanner`，输出 `ScanResult`。
6. 扩展 `RepositoryFileJpaRepository`，支持按 repository 删除旧扫描结果、查询未跳过文件。
7. 扩展 `RepositoryApplicationService`，创建仓库后同步执行扫描并写入 `repository_files`。
8. 扩展 mapper/status，让创建响应和状态接口返回扫描后的统计。
9. 编写 `RepositoryScannerTest` 覆盖过滤、语言识别、hash、相对路径。
10. 扩展 `RepositoryControllerTest`，验证导入后状态为 `ready`、file/skipped/language summary 正确。
11. 使用 Java 21 运行 `mvn test`。

### 9.6 测试与验收

验收项：

- [x] Scanner 能扫描普通 Java 项目目录。
- [x] 相对路径统一使用 `/`。
- [x] 能识别 Java/XML/YAML/JSON/Markdown/Properties 等语言。
- [x] 能过滤 `.git`、`target`、`node_modules` 等目录。
- [x] 能过滤 `.env`、key/cert、图片、压缩包、class/jar 等文件。
- [x] 能过滤超过配置大小的文件。
- [x] 能过滤二进制文件。
- [x] 能为未跳过文件计算 SHA-256 hash。
- [x] `POST /api/repositories` 导入后写入 `repository_files`。
- [x] Repository 状态最终为 `ready`，并返回 file/skipped/language summary。
- [x] `mvn test` 通过。

### 9.7 执行记录

已完成内容：

- 新增 `scanner` 包，包含语言枚举、跳过原因、扫描结果对象、异常、语言检测、过滤策略、SHA-256 hash 和仓库遍历器。
- `RepositoryScanner` 使用 `Files.walkFileTree` 遍历目录，支持目录剪枝、失败文件记录和相对路径标准化。
- `FileSkipPolicy` 过滤 `.git`、`target`、`node_modules`、缓存目录、敏感文件、大文件、二进制文件和常见构建产物。
- `RepositoryApplicationService` 在创建本地仓库后同步执行扫描，写入 `repository_files`，并将仓库状态更新为 `READY`。
- `repository_files` 对未跳过文件保存 language、size、content hash；对跳过项保存 skip reason。
- `RepositoryControllerTest` 从 V0-3 的空仓库语义升级为真实扫描语义，验证导入响应、列表、详情和状态接口返回 file/skipped/language summary。
- 新增 `RepositoryScannerTest` 覆盖过滤规则、语言识别、hash 和相对路径。

验证命令：

```powershell
.\scripts\use-java.ps1 21
cd backend-java
mvn -q test
```

验证结果：

```text
Java: Microsoft OpenJDK 21.0.11
Flyway: validated 2 migrations, schema version v2
RepositoryScannerTest: 1 test, 0 failures, 0 errors, 0 skipped
RepositoryControllerTest: 8 tests, 0 failures, 0 errors, 0 skipped
V0SchemaIntegrationTest: 1 test, 0 failures, 0 errors, 0 skipped
StatusControllerTest: 2 tests, 0 failures, 0 errors, 0 skipped
RepoLensJavaApplicationTests: 1 test, 0 failures, 0 errors, 0 skipped
Total: 13 tests passed
```

### 9.8 偏差与后续处理

偏差：

- V0-3 中创建仓库后状态为 `pending`，V0-4 接入同步扫描后创建响应状态变为 `ready`。
- Scanner 记录跳过目录本身，例如 `.git`、`target`、`node_modules`，而不是记录这些目录内部每个文件。

处理：

- 已更新 Repository API 测试，明确 V0 同步导入完成后返回 `ready`。
- 跳过目录按目录级记录，减少无意义噪声；后续如果要展示更细粒度的 skip report，可在 V1 增加采样或统计字段。

## 10. V0-5：Java Parser

### 10.1 目标

基于 V0-4 扫描出的 Java 文件，使用 JavaParser 解析 Java 源码，提取包名、import、类型声明、方法/构造器声明、注解、修饰符、签名和起止行号，为 V0-6 Chunk Builder 提供结构化输入。

V0-5 不直接写入 `code_chunks`，只实现 parser 模型和解析服务，保持 Parser 与 Chunk Builder 解耦。

### 10.2 范围

本阶段实现：

- Maven 引入 `com.github.javaparser:javaparser-core:3.28.2`。
- `parser/CodeParser`
- `parser/JavaParserService`
- `parser/ParsedFile`
- `parser/ParsedSymbol`
- `parser/ParseError`
- `parser/SymbolType`
- 解析 Java class/interface/enum/record。
- 解析 method/constructor。
- 提取 package、imports、annotations、modifiers、signature、startLine、endLine。
- 轻量提取 Spring route metadata：类级 `@RequestMapping` + 方法级 mapping。
- 解析失败降级为带 errors 的 `ParsedFile`，不抛出到导入主流程。

本阶段不实现：

- 调用关系图谱。
- 完整类型求解和 symbol resolution。
- chunk 入库。
- Lucene 索引。
- 解析非 Java 语言。

### 10.3 设计决策

1. 使用 JavaParser `StaticJavaParser.parse(Path)` 或 parser instance 读取源码，保留源码位置 range。
2. Parser 输出只用 immutable record，避免后续 Chunk Builder 修改解析结果。
3. 每个 Java 文件一定返回 `ParsedFile`；即使语法错误，也返回 package/imports 为空、symbols 为空、errors 非空的对象。
4. `ParsedFile` 保存 source content 和 line count，V0-6 可直接按 line range 截取 chunk 内容。
5. `ParsedSymbol` 区分 `CLASS`、`INTERFACE`、`ENUM`、`RECORD`、`METHOD`、`CONSTRUCTOR`。
6. `qualifiedName` 使用 `packageName + typeName + methodSignature` 的稳定格式；嵌套类型暂按 AST 路径拼父级。
7. method signature 使用 JavaParser declaration string，参数类型保留但不做符号求解。
8. 注解存短名，例如 `RestController`、`GetMapping`；metadata 保存 route、httpMethods、raw annotations 等轻量信息。
9. line range 缺失时降级为 `1..lineCount`，但测试样例要求正常源码必须有准确 range。
10. 解析错误使用 `ParseError(message, line, column)` 记录，后续 V0-6 可做 file-level fallback。

### 10.4 涉及文件 / 类 / API / 表

计划新增或修改：

```text
backend-java/pom.xml
backend-java/src/main/java/com/repolens/parser/CodeParser.java
backend-java/src/main/java/com/repolens/parser/JavaParserService.java
backend-java/src/main/java/com/repolens/parser/ParseError.java
backend-java/src/main/java/com/repolens/parser/ParsedFile.java
backend-java/src/main/java/com/repolens/parser/ParsedSymbol.java
backend-java/src/main/java/com/repolens/parser/SymbolType.java
backend-java/src/test/java/com/repolens/parser/JavaParserServiceTest.java
backend-java/src/test/resources/fixtures/parser/java/UserController.java
backend-java/src/test/resources/fixtures/parser/java/UserService.java
backend-java/src/test/resources/fixtures/parser/java/BrokenJava.java
```

API：

```text
本阶段不新增 HTTP API
```

数据表：

```text
本阶段不新增或修改表
```

### 10.5 执行步骤

1. 在 `pom.xml` 引入 JavaParser。
2. 新增 parser record/enums/interface。
3. 实现 `JavaParserService.supports(Language.JAVA)`。
4. 实现 package/import 提取。
5. 实现 type declaration 提取：class/interface/enum/record。
6. 实现 method/constructor 提取。
7. 实现 annotation、modifier、signature、line range 提取。
8. 实现 Spring route metadata 提取。
9. 实现 parse error 降级。
10. 添加 parser fixture。
11. 编写 `JavaParserServiceTest`。
12. 使用 Java 21 运行 `mvn test`。

### 10.6 测试与验收

验收项：

- [x] JavaParser 依赖可解析并参与 Maven 测试。
- [x] 能提取 package name。
- [x] 能提取 imports。
- [x] 能提取 `UserController` class。
- [x] 能提取 `getUser` method。
- [x] 能提取 constructor。
- [x] 能提取 `RestController`、`RequestMapping`、`GetMapping` 等注解。
- [x] 能提取 method signature、modifiers、start/end line。
- [x] 能提取轻量 route metadata。
- [x] 解析坏 Java 文件时返回 errors，不抛出到测试外层。
- [x] `mvn test` 通过。

### 10.7 执行记录

已完成内容：

- `pom.xml` 引入 `com.github.javaparser:javaparser-core:3.28.2`。
- 新增 parser 模型：`CodeParser`、`ParsedFile`、`ParsedSymbol`、`ParseError`、`SymbolType`。
- 新增 `JavaParserService`，支持 `Language.JAVA`。
- 实现 package、imports、class/interface/enum/record、method、constructor 提取。
- 实现 annotations、modifiers、signature、start/end line 提取。
- 实现轻量 Spring route metadata：类级 `@RequestMapping` 与方法级 `@GetMapping` 等合成 route。
- 解析失败时返回带 errors 的 `ParsedFile`，不向外抛出 `ParseProblemException`。
- 新增 parser fixtures：`UserController.java`、`UserService.java`、`BrokenJava.java`。
- 新增 `JavaParserServiceTest`，覆盖正常解析和坏文件降级。

验证命令：

```powershell
.\scripts\use-java.ps1 21
cd backend-java
mvn -q test
```

验证结果：

```text
Java: Microsoft OpenJDK 21.0.11
JavaParserServiceTest: 2 tests, 0 failures, 0 errors, 0 skipped
RepositoryScannerTest: 1 test, 0 failures, 0 errors, 0 skipped
RepositoryControllerTest: 8 tests, 0 failures, 0 errors, 0 skipped
V0SchemaIntegrationTest: 1 test, 0 failures, 0 errors, 0 skipped
StatusControllerTest: 2 tests, 0 failures, 0 errors, 0 skipped
RepoLensJavaApplicationTests: 1 test, 0 failures, 0 errors, 0 skipped
Total: 15 tests passed
```

### 10.8 偏差与后续处理

偏差：

- JavaParser 3.28.2 的 `TypeDeclaration<?>` 没有统一 `getDeclarationAsString(boolean, boolean, boolean)`，类型签名改为取节点源码第一行的紧凑文本。
- JavaParser 的 range 对注解类/方法会覆盖注解和完整声明块，测试断言改为接受实际 AST range。
- 构造器和方法 declaration string 默认保留参数类型，不保留参数名。
- `ParseProblemException` 的 location 类型在当前版本不直接暴露 line/column 字段，V0 先记录 `0/0`。

处理：

- 参数完整文本已放入 `metadata.parameters`，V0-6 构建 chunk 时可使用 metadata。
- line range 采用 JavaParser 原始 range，后续 `LineSliceService` 截取代码时做边界裁剪。
- parse error line/column 后续如需要更准，可单独适配 JavaParser problem location API。

## 11. V0-6：Chunk Builder

### 11.1 目标

将 V0-5 Parser 输出转换成可持久化、可检索、可展示的代码 chunk，写入 `code_chunks` 表，并更新 Repository 的 `parsed_file_count` 和 `chunk_count`。V0-6 完成后，本地 Java 仓库导入应具备 `scan -> parse -> chunk` 的后端闭环。

### 11.2 范围

本阶段实现：

- `chunking/CodeChunkDraft`
- `chunking/ChunkBuilder`
- `chunking/LineSliceService`
- `chunking/TokenEstimateService`
- chunk content hash。
- Java METHOD/CONSTRUCTOR -> `ChunkType.METHOD`。
- Java CLASS/INTERFACE/ENUM/RECORD -> `ChunkType.CLASS`。
- 解析失败或无 symbol 的 Java 文件 -> `ChunkType.FILE` fallback。
- CONFIG/TEXT chunk 的最小支持：XML/YAML/JSON/PROPERTIES/SQL -> `CONFIG`，Markdown/TEXT/UNKNOWN -> `TEXT`。
- Repository 导入链路接入 Parser 和 Chunk Builder。
- `code_chunks` 入库，Repository `chunk_count`、`parsed_file_count` 更新。

本阶段不实现：

- Lucene 索引。
- 向量 embedding。
- 图谱关系。
- 大文件分块策略的复杂优化。

### 11.3 设计决策

1. `ChunkBuilder` 不直接依赖 JPA，只输出 `CodeChunkDraft`；入库由应用服务处理。
2. `LineSliceService` 对 JavaParser range 做边界裁剪，避免 range 超出源码行数导致导入失败。
3. chunk 内容增加 header，包含 file、symbol、lines、annotations、route，提升 BM25 对路径/符号/注解的召回能力。
4. `METHOD` chunk 优先于 `CLASS` chunk；同一文件可同时生成 class chunk 和 method chunk。
5. `CLASS` chunk V0 先保留完整类型 range；如果后续大类过长，再改成 class signature + metadata。
6. 解析失败时生成 FILE fallback chunk，并在 metadata 中保存 parse errors。
7. 配置/文本文件只对未跳过文件生成一个 CONFIG/TEXT chunk，V0 暂不按段落切分。
8. `tokenEstimate=max(1, content.length()/4)`，用于后续检索上下文预算。
9. `contentHash=sha256(language + filePath + startLine + endLine + content)`，为 V1 增量索引预留。
10. 导入状态从 V0-4 的 `SCANNING -> READY` 扩展为 `SCANNING -> PARSING -> CHUNKING -> READY`。

### 11.4 涉及文件 / 类 / API / 表

计划新增或修改：

```text
backend-java/src/main/java/com/repolens/chunking/application/ChunkBuilder.java
backend-java/src/main/java/com/repolens/chunking/application/CodeChunkDraft.java
backend-java/src/main/java/com/repolens/chunking/application/LineSliceService.java
backend-java/src/main/java/com/repolens/chunking/application/TokenEstimateService.java
backend-java/src/main/java/com/repolens/chunking/infrastructure/CodeChunkJpaRepository.java
backend-java/src/main/java/com/repolens/repository/application/RepositoryApplicationService.java
backend-java/src/test/java/com/repolens/chunking/application/ChunkBuilderTest.java
backend-java/src/test/java/com/repolens/repository/api/RepositoryControllerTest.java
```

API：

```text
POST /api/repositories
GET /api/repositories
GET /api/repositories/{repositoryId}
GET /api/repositories/{repositoryId}/status
```

数据表：

```text
code_chunks
repositories.parsed_file_count
repositories.chunk_count
```

### 11.5 执行步骤

1. 新增 chunk draft 和服务类。
2. 实现 line slice 边界裁剪。
3. 实现 token 估算。
4. 实现 Java parsed symbols 到 chunk draft 的映射。
5. 实现 parse error/file fallback。
6. 实现配置和文本文件 chunk。
7. 扩展 `CodeChunkJpaRepository`，支持按 repository 删除旧 chunk。
8. 扩展 Repository 导入链路：扫描后解析 Java 文件，构建 chunk，入库。
9. 更新 Repository 状态、parsed_file_count、chunk_count。
10. 编写 `ChunkBuilderTest`。
11. 扩展 Repository API 测试，验证导入后 `chunk_count > 0`。
12. 使用 Java 21 运行 `mvn test`。

### 11.6 测试与验收

验收项：

- [x] 一个 Java class 产生 CLASS chunk。
- [x] 一个 Java method 产生 METHOD chunk。
- [x] method chunk 内容包含注解、方法体、file/symbol/line header。
- [x] chunk startLine/endLine 对应 parser range 并可裁剪。
- [x] broken Java 生成 FILE fallback chunk。
- [x] 配置文件生成 CONFIG chunk。
- [x] chunk hash 稳定。
- [x] 导入本地 Java 仓库后 `chunk_count > 0`。
- [x] Repository 状态最终为 `ready`，并返回 parsed/chunk 统计。
- [x] `mvn test` 通过。

### 11.7 执行记录

已完成内容：

- 新增 `chunking/application` 包：`CodeChunkDraft`、`ChunkBuilder`、`LineSliceService`、`TokenEstimateService`。
- `ChunkBuilder` 支持 Java CLASS/METHOD/CONSTRUCTOR chunk，解析失败 FILE fallback，以及 CONFIG/TEXT whole-file chunk。
- chunk 内容增加 file/symbol/lines/annotations/route header，增强后续 BM25 可检索性。
- chunk hash 使用 SHA-256，token 估算使用 `max(1, content.length()/4)`。
- `CodeChunkJpaRepository` 支持按 repository 删除旧 chunk。
- Repository 导入链路接入 `PARSING -> CHUNKING`：扫描后解析 Java 文件，构建 chunk，写入 `code_chunks`。
- Repository 响应现在返回 `parsed_file_count` 和 `chunk_count`。
- 新增 `ChunkBuilderTest`，覆盖 class/method/fallback/config/hash。
- 扩展 `RepositoryControllerTest`，验证导入后 chunk 入库且类型包含 CLASS/METHOD/CONFIG。

验证命令：

```powershell
.\scripts\use-java.ps1 21
cd backend-java
mvn -q test
```

验证结果：

```text
Java: Microsoft OpenJDK 21.0.11
ChunkBuilderTest: 3 tests, 0 failures, 0 errors, 0 skipped
JavaParserServiceTest: 2 tests, 0 failures, 0 errors, 0 skipped
RepositoryScannerTest: 1 test, 0 failures, 0 errors, 0 skipped
RepositoryControllerTest: 8 tests, 0 failures, 0 errors, 0 skipped
V0SchemaIntegrationTest: 1 test, 0 failures, 0 errors, 0 skipped
StatusControllerTest: 2 tests, 0 failures, 0 errors, 0 skipped
RepoLensJavaApplicationTests: 1 test, 0 failures, 0 errors, 0 skipped
Total: 18 tests passed
```

### 11.8 偏差与后续处理

偏差：

- `Map.copyOf` 不允许 value 为 null，顶层 class metadata 中的 `parentSymbol=null` 曾导致 NPE。
- Repository API 测试样例一开始只写了空 class，没有 method，导致 METHOD chunk 验收不成立。
- JavaParser method signature 不包含 `public` 修饰符，chunk header 使用 parser 的稳定 signature。

处理：

- metadata 构建时跳过 null parent symbol。
- 测试 fixture 补充简单方法，导入后可验证 CLASS/METHOD/CONFIG chunk。
- method modifiers 仍保存在 metadata 中，后续前端或检索展示可单独使用。

## 12. V0-7：Lucene BM25 检索

### 12.1 目标

在 V0-6 已生成 `code_chunks` 的基础上，建立本地 Lucene BM25 索引，并提供与旧前端兼容的 Evidence 检索 API。完成后，RepoLens-Java 可以独立跑通：

```text
本地仓库导入 -> scan -> parse -> chunk -> Lucene index -> retrieve evidence
```

### 12.2 范围

本阶段实现：

- Maven 引入 Lucene 10.x：`lucene-core`、`lucene-analysis-common`、`lucene-queryparser`。
- `indexing/lexical/LuceneIndexPathResolver`
- `indexing/lexical/LuceneDocumentMapper`
- `indexing/lexical/LuceneIndexService`
- `indexing/lexical/LexicalSearchHit`
- Repository 导入完成 chunk 入库后自动重建 Lucene 索引。
- Repository 状态增加 `INDEXING` 阶段，索引完成后写入 `indexed_at`。
- `POST /api/repositories/{repositoryId}/retrieve`
- 与旧前端兼容的 `RetrievalRequest`、`RetrievalResponse`、`EvidenceResponse`、`RetrievalDebugResponse`。
- BM25-only evidence：`source=BM25`、`sources=["BM25"]`、`bm25_score>0`、`vector_score=0`、`graph_score=0`。

本阶段不实现：

- 向量 embedding。
- Qdrant / pgvector。
- 图谱扩展。
- Rerank 模型。
- 高亮片段。
- search_evidences 持久化。

### 12.3 设计决策

1. 使用 Apache Lucene 10.x，匹配 Java 21 定位；V0 采用默认 BM25Similarity。
2. 每个 repository 单独一个 FSDirectory：`.repolens-java/indexes/lucene/{repositoryId}`，便于重建和删除。
3. 索引只由 `code_chunks` 构建，数据库仍是权威数据源；检索命中后回查 chunk 组装 evidence。
4. Lucene document 只存检索必要字段和 chunkId；path、line、symbol、snippet 以数据库 chunk 为准。
5. 字段权重采用：

```text
symbol_name: 4.0
file_path: 2.5
metadata: 2.0
content: 1.0
```

6. 查询用 `MultiFieldQueryParser`，先对用户 query 做 `QueryParser.escape`，避免特殊字符导致解析失败。
7. `top_k` 允许 1 到 50，默认 10；V0 不让一次检索返回过大结果。
8. `use_bm25=false` 时返回空 evidence，但仍返回 debug；`use_vector/use_graph=true` 暂不执行，debug 中说明 V0 未启用。
9. evidenceId 使用 repositoryId、chunkId、source、rank 做 SHA-256 截断，保证同一检索结果基本稳定。
10. snippet 取 chunk content 前 600 字符，保留换行，超长时追加 `...`。

### 12.4 涉及文件 / 类 / API / 表

计划新增或修改：

```text
backend-java/pom.xml
backend-java/src/main/java/com/repolens/indexing/lexical/LuceneIndexPathResolver.java
backend-java/src/main/java/com/repolens/indexing/lexical/LuceneDocumentMapper.java
backend-java/src/main/java/com/repolens/indexing/lexical/LuceneIndexService.java
backend-java/src/main/java/com/repolens/indexing/lexical/LexicalSearchHit.java
backend-java/src/main/java/com/repolens/retrieval/api/RetrievalController.java
backend-java/src/main/java/com/repolens/retrieval/api/dto/RetrievalRequest.java
backend-java/src/main/java/com/repolens/retrieval/api/dto/RetrievalResponse.java
backend-java/src/main/java/com/repolens/retrieval/api/dto/EvidenceResponse.java
backend-java/src/main/java/com/repolens/retrieval/api/dto/RetrievalDebugResponse.java
backend-java/src/main/java/com/repolens/retrieval/application/RetrievalService.java
backend-java/src/main/java/com/repolens/retrieval/application/SnippetBuilder.java
backend-java/src/main/java/com/repolens/retrieval/application/EvidenceIdFactory.java
backend-java/src/main/java/com/repolens/chunking/infrastructure/CodeChunkJpaRepository.java
backend-java/src/main/java/com/repolens/repository/application/RepositoryApplicationService.java
backend-java/src/test/java/com/repolens/indexing/lexical/LuceneIndexServiceTest.java
backend-java/src/test/java/com/repolens/retrieval/api/RetrievalControllerTest.java
```

API：

```text
POST /api/repositories/{repositoryId}/retrieve
```

数据表：

```text
不新增表。
更新 repositories.status、repositories.indexed_at。
```

### 12.5 执行步骤

1. 在 `pom.xml` 加入 Lucene 10.x 依赖。
2. 新增 Lucene index path resolver，统一索引目录。
3. 新增 Lucene document mapper，定义字段名、stored/indexed 策略。
4. 新增 Lucene index service，实现 rebuild 和 search。
5. Repository 导入流程在 chunk 入库后进入 `INDEXING`，重建索引，设置 `indexed_at` 后进入 `READY`。
6. 新增 retrieval DTO，JSON 字段使用 `@JsonProperty` 对齐旧前端 snake_case。
7. 新增 retrieval service，校验 repository 存在且 ready，执行 BM25 检索，回查 chunk，组装 evidence/debug。
8. 新增 retrieval controller，暴露 `/api/repositories/{repositoryId}/retrieve`。
9. 编写 Lucene 单元/集成测试，覆盖方法名、文件路径、注解 metadata、topK。
10. 编写 Retrieval API 测试，覆盖导入后自动索引、检索返回 evidence、不存在 repository 404。
11. 使用 Java 21 运行 `mvn test`。

### 12.6 测试与验收

验收项：

- [x] 导入完成后自动建立 Lucene 索引。
- [x] Repository 最终状态为 `ready`，且 `indexed_at` 非空。
- [x] 搜索 API 返回 BM25 evidence。
- [x] evidence 包含 chunkId、repositoryId、filePath、startLine、endLine、symbolName、symbolType、language、source、sources、score、bm25Score、snippet、metadata。
- [x] 查询方法名能命中正确 METHOD chunk。
- [x] 查询文件路径片段能命中对应文件 chunk。
- [x] 查询 Spring 注解或 route metadata 能命中 Controller chunk。
- [x] `top_k` 生效。
- [x] 不存在 repository 返回 404。
- [x] `mvn test` 通过。

### 12.7 执行记录

已完成内容：

- `pom.xml` 新增 Lucene 10.4.0 依赖：`lucene-core`、`lucene-analysis-common`、`lucene-queryparser`。
- 新增项目级 Maven settings，将当前工程依赖解析固定到 HTTPS Maven Central，绕开全局 HTTP mirror 被 Maven blocker 拦截的问题。
- 新增 `indexing/lexical` 包：
  - `LuceneIndexPathResolver`
  - `LuceneDocumentMapper`
  - `LuceneIndexService`
  - `LexicalSearchHit`
  - `LuceneIndexException`
- Lucene 索引目录为：

```text
.repolens-java/indexes/lucene/{repositoryId}
```

- 索引字段覆盖 `chunk_id`、`repository_id`、`file_path`、`language`、`symbol_name`、`symbol_type`、`content`、`metadata`。
- 查询使用 `MultiFieldQueryParser` + `StandardAnalyzer`，字段 boost 为 symbol/path/metadata/content 分层权重。
- Repository 导入链路升级为 `SCANNING -> PARSING -> CHUNKING -> INDEXING -> READY`。
- chunk 入库后自动调用 `LuceneIndexService.rebuildIndex`，完成后写入 `indexed_at`。
- 新增 `retrieval` 包，提供：
  - `POST /api/repositories/{repositoryId}/retrieve`
  - `RetrievalRequest`
  - `RetrievalResponse`
  - `EvidenceResponse`
  - `RetrievalDebugResponse`
  - `RetrievalService`
  - `EvidenceIdFactory`
  - `SnippetBuilder`
- 检索响应与旧前端契约对齐，使用 snake_case 字段：`repository_id`、`evidences`、`bm25_score`、`vector_score`、`graph_score`、`debug` 等。
- V0 检索为 BM25-only。当前端传入 `use_vector=true` 或 `use_graph=true` 时不会失败，debug 中返回 vector disabled reason，graph count 为 0。
- 新增 `LuceneIndexServiceTest`，覆盖方法名、文件路径、Spring 注解 metadata 和 topK。
- 新增 `RetrievalControllerTest`，覆盖导入后自动索引、BM25 evidence 响应、未知 repository 404。
- 更新 `RepositoryControllerTest`，导入详情中的 `indexed_at` 由空升级为非空。

验证命令：

```powershell
.\scripts\use-java.ps1 21
cd backend-java
mvn test
```

验证结果：

```text
Java: Microsoft OpenJDK 21.0.11
ChunkBuilderTest: 3 tests, 0 failures, 0 errors, 0 skipped
LuceneIndexServiceTest: 1 test, 0 failures, 0 errors, 0 skipped
JavaParserServiceTest: 2 tests, 0 failures, 0 errors, 0 skipped
V0SchemaIntegrationTest: 1 test, 0 failures, 0 errors, 0 skipped
RepositoryControllerTest: 8 tests, 0 failures, 0 errors, 0 skipped
RetrievalControllerTest: 2 tests, 0 failures, 0 errors, 0 skipped
RepositoryScannerTest: 1 test, 0 failures, 0 errors, 0 skipped
StatusControllerTest: 2 tests, 0 failures, 0 errors, 0 skipped
RepoLensJavaApplicationTests: 1 test, 0 failures, 0 errors, 0 skipped
Total: 21 tests passed
```

### 12.8 偏差与后续处理

偏差：

- 全局 Maven mirror 指向 HTTP 阿里仓库，新增 Lucene 依赖时被 Maven default HTTP blocker 拦截。
- Lucene 10 在 Windows 下对 `@TempDir` 指向的用户临时目录使用 MMapDirectory 时出现 `AccessDeniedException`。
- Parser 当前输出的 method `symbol_name` 是完整限定名和签名，例如 `demo.UserController#String getUser(String)`，不是简写 `UserController#getUser`。
- route metadata 已经是结构化对象，不是字符串。
- Lucene 输出 warning：未启用 `jdk.incubator.vector`，会影响最优向量化性能，但不影响 BM25 检索正确性。

处理：

- 新增 `backend-java/.mvn/settings.xml`，项目级固定 HTTPS Maven Central；不修改全局 Maven settings。
- Lucene 单测索引目录改到项目 `target/` 下的临时目录，符合当前工作区写权限。
- Retrieval API 保留完整 `symbol_name`，因为它更稳定、更可定位；前端展示可直接显示或后续做短名派生。
- 测试断言更新为 `metadata.route.path`，保留结构化 route 对象。
- `jdk.incubator.vector` warning 暂作为性能提示处理，V0 不额外调整 JVM 参数。

## 13. V0-8：前端适配与 Evidence 展示

### 13.1 目标

复用现有 Next.js 工作台，适配 RepoLens-Java V0 后端，使浏览器可以完整演示：

```text
填写本地路径 -> 导入仓库 -> 查看扫描/解析/chunk/索引状态 -> 输入查询 -> 展示 BM25 Evidence
```

### 13.2 范围

本阶段实现：

- 前端默认 API 地址从 Python 后端 `8000` 改为 Java 后端 `8080`。
- Java 后端增加本地开发 CORS，允许 Next.js `3000` 调用。
- 前端 RepositoryStatus 类型增加 `indexing`。
- 前端错误解析兼容 Java 后端 `{ code, message, path, timestamp }`。
- 页面标题、默认 query、导入表单文案改为 RepoLens-Java V0。
- 页面主流程收敛为 Repository、状态统计、语言统计、Lucene BM25 Evidence。
- 隐藏/移除 V0 未实现的 QA、Review、Evaluation、MCP 面板，避免演示时持续打未实现接口。
- Evidence card 展示 source、score、BM25/vector/graph 分数、metadata route/annotations。

本阶段不实现：

- QA、Review、多 Agent、MCP、Evaluation 的 Java 后端 API。
- 文件树/源码浏览器。
- 代码高亮。
- 登录权限。

### 13.3 设计决策

1. V0 前端继续复用 `frontend/`，不新建前端目录。
2. V0 页面保持工作台风格，不做营销页。
3. 默认 `NEXT_PUBLIC_API_BASE_URL` 改为 `http://localhost:8080`；仍允许环境变量覆盖。
4. 导入请求继续发旧字段 `{ source, branch }`，Java 后端已兼容。
5. Retrieve 请求继续发旧字段 `top_k/use_bm25/use_vector/use_graph`，Java 后端已兼容。
6. V0 默认关闭 Vector/Graph toggle，只打开 BM25，减少“未启用”提示噪声。
7. 页面只保留已落地能力，V1 能力不在 V0 主界面展示。
8. 后端 CORS 仅用于本地开发，允许 `localhost/127.0.0.1` 的 3000/3001/5173。

### 13.4 涉及文件 / 类 / API / 表

计划新增或修改：

```text
backend-java/src/main/java/com/repolens/config/CorsConfig.java
frontend/lib/api.ts
frontend/types/workbench.ts
frontend/app/page.tsx
docs/repolens-java-v0-design-and-worklog.md
```

API：

```text
GET /health
GET /api/status
POST /api/repositories
GET /api/repositories
GET /api/repositories/{repositoryId}
GET /api/repositories/{repositoryId}/status
POST /api/repositories/{repositoryId}/retrieve
```

### 13.5 执行步骤

1. 新增 Java 后端 CORS 配置。
2. 修改前端默认 API 地址为 `8080`。
3. 修改前端 error parser，优先读取 Java `message`，兼容 Python `detail`。
4. `RepositoryStatus` 加入 `indexing`。
5. 精简 `page.tsx` import、state、effect、handler 和 JSX，只保留 V0 主流程。
6. 改写 EvidenceCard，展示 BM25 分数和 metadata。
7. 运行 Java 后端测试。
8. 运行前端 build。
9. 如 build 通过，启动 Java 后端和前端 dev server，给出本地 URL。

### 13.6 测试与验收

验收项：

- [x] Next.js 前端默认请求 Java 后端 `8080`。
- [x] 浏览器跨端口请求不被 CORS 拦截。
- [x] 前端可以导入本地仓库。
- [x] 前端可以展示 file/parsed/skipped/chunk/relation 指标。
- [x] 前端可以展示 language summary。
- [x] 前端可以展示 indexed_at。
- [x] 前端可以调用 retrieve API。
- [x] Evidence card 展示 path、line、symbol、source、score、snippet、metadata。
- [x] `npm run build` 通过。

### 13.7 执行记录

已完成内容：

- 新增 `CorsConfig`，允许本地 Next.js dev server 从 `localhost/127.0.0.1` 的 3000、3001、5173 访问 Java 后端。
- `frontend/lib/api.ts` 默认 API 地址从 `http://localhost:8000` 改为 `http://localhost:8080`。
- 前端错误解析兼容 Java 后端 `{ code, message, path, timestamp }`，优先展示 `message`。
- `frontend/types/workbench.ts` 的 `RepositoryStatus` 增加 `indexing`。
- `frontend/app/page.tsx` 重构为 V0 专用工作台，保留：
  - 本地仓库导入。
  - 仓库列表。
  - 仓库状态和 index 状态。
  - 文件、解析、跳过、chunk、relation 指标。
  - language summary。
  - BM25 evidence 检索。
- 移除 V0 主界面上的 QA、Review、Evaluation、MCP 面板，避免调用 Java V0 尚未实现的 API。
- Evidence card 增强展示 source、score、BM25 score、route、annotations、snippet。
- Vector/Graph toggle 默认关闭；用户打开时 Java 后端会在 debug 中提示 V0 未启用。

验证命令：

```powershell
.\scripts\use-java.ps1 21
cd backend-java
mvn test

cd ..\frontend
npm run build
```

验证结果：

```text
Backend: 21 tests passed, 0 failures, 0 errors
Frontend: next build compiled successfully; type check passed
```

### 13.8 偏差与后续处理

偏差：

- 原前端是 Phase 10/V1 工作台，包含 QA、Review、Evaluation、MCP 等大量 V0 未实现功能。
- Java 后端最初没有 CORS 配置，浏览器直接跨端口调用会被拦截。
- 旧前端错误解析只读取 Python/FastAPI 风格的 `detail`。

处理：

- V0 页面收敛为可演示的 Java 检索闭环，V1 面板后续再按 Java 后端能力逐步恢复。
- 新增本地开发 CORS，保证 `localhost:3000 -> localhost:8080` 可用。
- 错误解析同时兼容 Java `message` 与 Python `detail`。

## 14. V0-9：测试、Demo Runbook 与收尾

### 14.1 目标

完成 V0 最终交付收尾，让 RepoLens-Java 具备可复现的启动、测试、演示和讲解材料。V0-9 的重点不是增加新业务能力，而是补齐交付可信度。

### 14.2 范围

本阶段实现：

- `docs/repolens-java-v0-demo-runbook.md`
- V0 最终能力清单。
- 本地启动步骤。
- API smoke 步骤。
- 前端演示步骤。
- 已知限制。
- 最终测试记录。
- 如果可行，启动本地 dev server 并提供 URL。

本阶段不实现：

- 新业务 API。
- 新前端页面。
- Docker Compose/PostgreSQL 部署。
- 截图自动化。

### 14.3 设计决策

1. Runbook 面向面试/demo 场景，命令可直接复制执行。
2. V0 使用 H2 file DB 作为默认本地存储，减少安装门槛。
3. Demo 路径推荐导入当前 RepoLens 或临时 Java fixture。
4. 因当前工具环境会清理跨工具调用的后台长进程，自动 smoke 使用“同一命令启动后端、请求真实 API、最后停止进程”的方式验证。
5. 前端使用 `npm run build` 作为稳定验收；实际交互由用户本机运行两个 dev 脚本。

### 14.4 涉及文件 / 类 / API / 表

计划新增或修改：

```text
docs/repolens-java-v0-demo-runbook.md
docs/repolens-java-v0-design-and-worklog.md
docs/README.md
```

### 14.5 执行步骤

1. 新增 demo runbook。
2. 在 docs README 中挂载 runbook。
3. 记录 V0 最终能力与限制。
4. 运行后端全量测试。
5. 运行前端 build。
6. 运行真实后端 HTTP smoke。
7. 尝试启动 dev server，若受工具环境限制，记录用户本机启动方式。

### 14.6 测试与验收

验收项：

- [x] Runbook 包含环境、启动、导入、检索、测试、清理步骤。
- [x] Runbook 包含 V0 已知限制。
- [x] 后端 `mvn test` 通过。
- [x] 前端 `npm run build` 通过。
- [x] 真实 HTTP smoke 通过。
- [x] 文档状态更新为 V0-9 DONE。

### 14.7 执行记录

已完成内容：

- 新增 `docs/repolens-java-v0-demo-runbook.md`。
- 更新 `docs/README.md`，挂载 V0 demo runbook。
- 新增 `scripts/dev-backend-java.ps1`，一条命令启动 Java 后端。
- 新增 `scripts/dev-frontend.ps1`，一条命令启动 Next.js 前端。
- Runbook 覆盖：
  - 环境检查。
  - Java 21 切换。
  - 后端启动。
  - 前端启动。
  - UI demo flow。
  - API smoke。
  - 测试命令。
  - runtime files。
  - known limits。
  - interview talk track。
- 最终执行后端全量测试。
- 最终执行前端 production build。
- 最终执行真实 HTTP smoke：启动 Spring Boot，调用 `/health`，导入临时 Java 仓库，调用 retrieve API，确认 evidence 返回 BM25 命中。

最终验证命令：

```powershell
.\scripts\use-java.ps1 21
cd backend-java
mvn test

cd ..\frontend
npm run build
```

最终验证结果：

```text
Backend: 21 tests passed, 0 failures, 0 errors
Frontend: Next.js production build succeeded, type check passed
HTTP smoke:
  health=ok
  repository_status=ready
  file_count=1
  chunk_count=2
  indexed_at=true
  evidence_count=2
  first_source=BM25
```

### 14.8 偏差与后续处理

偏差：

- 当前 Codex 工具调用环境会清理跨工具调用启动的后台长进程，导致无法在本轮中把 dev server 常驻到最后再交付 URL。

处理：

- 已用“单次命令内启动后端、等待健康检查、执行真实 API smoke、最后停止进程”的方式验证真实 HTTP 链路。
- 已提供 `scripts/dev-backend-java.ps1` 和 `scripts/dev-frontend.ps1`，用户在本机 PowerShell 中运行后即可分别访问：

```text
Backend: http://localhost:8080
Frontend: http://localhost:3000
```
