# RepoLens-Java V0 详细执行计划书

## 1. 文档信息

| 字段 | 内容 |
| --- | --- |
| 项目 | RepoLens-Java |
| 版本 | V0：Java 后端最小可运行闭环 |
| 文档类型 | 可对照执行的详细阶段计划 |
| 创建日期 | 2026-06-28 |
| 依据文档 | `docs/repolens-java-requirements-outline-design.md`、`docs/repolens-java-development-roadmap.md` |
| V0 核心目标 | 用 Spring Boot 后端跑通“本地仓库导入 -> 扫描 -> Java 解析 -> Chunk -> BM25 检索 -> Evidence 展示” |

## 2. V0 定位

V0 是 RepoLens-Java 的最小产品原型，不追求 AI Agent、MCP、向量库、PR Review。它只验证一件关键事情：

> RepoLens 的核心后端能力可以由 Java/Spring Boot 独立承担，而不是旧 FastAPI 项目的外壳或网关。

V0 完成后，项目应具备以下最小闭环：

```text
启动 backend-java
  -> 前端或 API 创建本地仓库导入
  -> 后端扫描文件并过滤无关/敏感文件
  -> Java Parser 提取 class/method/annotation/line range
  -> Chunk Builder 生成 file/class/method chunk
  -> Lucene BM25 建立本地索引
  -> 用户输入 query 检索代码
  -> 返回 Evidence：文件路径、行号、symbol、snippet、score、source
  -> 前端显示仓库状态和 Evidence 列表
```

## 3. V0 不做什么

为了避免一开始失控，V0 明确不做：

- 不接 Spring AI。
- 不接大模型。
- 不做 MCP Server。
- 不做 Qdrant / PGvector。
- 不做 PR Review。
- 不做多用户登录。
- 不做复杂权限系统。
- 不做 GitHub/GitLab/Gitee PR/MR Provider。
- 不做自动代码修改、提交、推送、评论。
- 不强行支持所有语言；V0 只把 Java 解析做扎实，其他语言最多识别为文件级 chunk。

V0 的胜利标准不是“功能很多”，而是后端主链路清楚、可测、可演示。

## 4. 推荐周期

如果每天投入 3-5 小时，V0 推荐 7-10 天完成。

| 阶段 | 建议时间 | 目标 |
| --- | --- | --- |
| V0-0 | 0.5 天 | 开发准备、目录和环境确认 |
| V0-1 | 1 天 | Spring Boot 工程骨架 |
| V0-2 | 1 天 | 数据库与 Flyway |
| V0-3 | 1 天 | Repository API 与本地导入 |
| V0-4 | 1 天 | Scanner 文件扫描与过滤 |
| V0-5 | 1.5 天 | Java Parser |
| V0-6 | 1 天 | Chunk Builder |
| V0-7 | 1 天 | Lucene BM25 检索 |
| V0-8 | 1 天 | Evidence API 与前端适配 |
| V0-9 | 1 天 | 测试、Demo runbook、截图和收尾 |

若时间紧张，最小可演示版本可以只完成 V0-1 到 V0-8。

## 5. V0 最终交付物

### 5.1 代码交付

```text
RepoLens/
  backend-java/
    build.gradle 或 pom.xml
    src/main/java/com/repolens/
    src/main/resources/application.yml
    src/main/resources/db/migration/
    src/test/java/com/repolens/
  frontend/
    lib/api.ts                    # 适配 Java 后端
    types/workbench.ts 或新类型文件 # 补充 Java API 类型
  docs/
    repolens-java-v0-execution-plan.md
    repolens-java-v0-demo-runbook.md
```

### 5.2 产品交付

- 后端健康检查可访问。
- 可以通过 API 创建本地仓库导入任务。
- 可以查看仓库状态、文件数、chunk 数。
- 可以对 Java 代码进行 BM25 搜索。
- 搜索结果包含 evidence 信息。
- 前端能展示仓库列表、状态和 evidence。

### 5.3 文档交付

- V0 demo runbook。
- V0 已知限制。
- V0 截图清单。
- V0 测试结果。

## 6. V0-0：开发准备

### 6.1 目标

确认工作区、旧项目资产、Java 环境和前端复用边界。

### 6.2 执行步骤

1. 确认当前工作目录：

```powershell
cd F:\Desktop\agent\RepoLens
```

2. 确认旧项目结构：

```powershell
Get-ChildItem -Force
Get-ChildItem -Force frontend
Get-ChildItem -Force docs
```

3. 确认 Java、Maven 或 Gradle：

```powershell
java -version
mvn -version
gradle -version
```

4. 确认 Node 前端可以继续复用：

```powershell
cd frontend
npm run build
```

5. 确认端口规划：

| 服务 | 端口 |
| --- | --- |
| frontend | 3000 |
| backend-java | 8080 |
| PostgreSQL/MySQL | 5432 / 3306 |
| Redis | 6379 |
| Qdrant，V1 才用 | 6333 |

### 6.3 检查清单

- [ ] Java 21 可用。
- [ ] Maven 或 Gradle 至少一个可用。
- [ ] frontend 可 build。
- [ ] 确认 `backend-java` 不覆盖旧 `backend`。
- [ ] 确认 V0 不修改旧 Python 后端。

### 6.4 验收

能明确回答：

- Java 后端目录放在哪里。
- V0 使用 Maven 还是 Gradle。
- V0 使用 PostgreSQL、MySQL 还是先 H2/SQLite。
- 前端是否保留 Next.js。

建议：V0 优先使用 **Maven + PostgreSQL**。如果本地数据库阻碍进度，可以先用 H2 开发，但 Flyway schema 应兼容 PostgreSQL。

## 7. V0-1：Spring Boot 工程骨架

### 7.1 目标

新增 `backend-java`，建立可持续开发的 Spring Boot 工程。

### 7.2 推荐技术

| 类别 | 选型 |
| --- | --- |
| Java | Java 21 |
| Framework | Spring Boot 3.x |
| Build | Maven 或 Gradle |
| Web | Spring Web |
| Validation | Jakarta Validation |
| DB | Spring Data JPA 或 MyBatis Plus 二选一 |
| Migration | Flyway |
| Test | JUnit 5、AssertJ、Mockito |
| API Doc，可选 | springdoc-openapi |

### 7.3 推荐依赖

Maven 方向：

```xml
spring-boot-starter-web
spring-boot-starter-validation
spring-boot-starter-data-jpa
flyway-core
postgresql
spring-boot-starter-test
lucene-core
lucene-queryparser
lucene-analysis-common
```

V0 暂不加入：

```text
spring-ai-*
mcp-*
qdrant-client
spring-security
```

这些留到 V1。

### 7.4 目录结构

创建：

```text
backend-java/
  pom.xml
  src/main/java/com/repolens/RepoLensJavaApplication.java
  src/main/java/com/repolens/common/
  src/main/java/com/repolens/config/
  src/main/java/com/repolens/repository/
  src/main/java/com/repolens/scanner/
  src/main/java/com/repolens/parser/
  src/main/java/com/repolens/chunking/
  src/main/java/com/repolens/indexing/
  src/main/java/com/repolens/retrieval/
  src/main/resources/application.yml
  src/main/resources/db/migration/
  src/test/java/com/repolens/
```

### 7.5 基础 API

实现：

```text
GET /health
GET /api/status
```

`GET /api/status` 返回：

```json
{
  "service": "repolens-java",
  "version": "v0",
  "status": "ok",
  "storage": {
    "database": "ok",
    "workspaceRoot": ".repolens-java/repos",
    "indexRoot": ".repolens-java/indexes"
  }
}
```

### 7.6 配置项

`application.yml` 至少包含：

```yaml
server:
  port: 8080

repolens:
  workspace-root: ./.repolens-java/repos
  index-root: ./.repolens-java/indexes
  scanner:
    max-file-size-bytes: 1048576
```

### 7.7 测试

测试类：

```text
StatusControllerTest
ApplicationContextTest
```

测试内容：

- Spring context 可以启动。
- `/api/status` 返回 200。
- 响应中 service 为 `repolens-java`。

### 7.8 验收

- [ ] `backend-java` 可以独立启动。
- [ ] `/health` 返回 ok。
- [ ] `/api/status` 返回配置摘要。
- [ ] 后端测试通过。

## 8. V0-2：数据库与 Flyway

### 8.1 目标

建立 V0 所需最小数据模型，支撑仓库、文件、chunk 和 evidence。

### 8.2 V0 表清单

| 表 | 用途 |
| --- | --- |
| `repositories` | 仓库记录和索引状态 |
| `repository_files` | 扫描到的文件和跳过原因 |
| `code_chunks` | 解析生成的代码块 |
| `search_evidences` | 检索结果记录，V0 可选持久化 |

V0 可以不建：

- `agent_traces`
- `tool_call_audits`
- `code_relations`
- `tasks`

这些在 V1 加。

### 8.3 repositories 表

Flyway 文件：

```text
V1__init_v0_schema.sql
```

字段：

```sql
create table repositories (
    id varchar(64) primary key,
    name varchar(255) not null,
    source_type varchar(32) not null,
    source_url varchar(1024),
    local_path varchar(1024),
    branch_name varchar(255),
    status varchar(64) not null,
    file_count integer not null default 0,
    chunk_count integer not null default 0,
    skipped_file_count integer not null default 0,
    language_summary text,
    last_error text,
    created_at timestamp not null,
    updated_at timestamp not null,
    indexed_at timestamp
);
```

状态枚举：

```text
CREATED
SCANNING
PARSING
CHUNKING
INDEXING
READY
FAILED
```

### 8.4 repository_files 表

字段：

```sql
create table repository_files (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    relative_path varchar(1024) not null,
    language varchar(64) not null,
    size_bytes bigint not null,
    content_hash varchar(128),
    skipped boolean not null default false,
    skip_reason varchar(255),
    created_at timestamp not null
);
```

索引：

```sql
create index idx_repository_files_repo on repository_files(repository_id);
create index idx_repository_files_path on repository_files(repository_id, relative_path);
```

### 8.5 code_chunks 表

字段：

```sql
create table code_chunks (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    file_id varchar(64) not null,
    file_path varchar(1024) not null,
    language varchar(64) not null,
    symbol_name varchar(512),
    symbol_type varchar(64) not null,
    start_line integer not null,
    end_line integer not null,
    content_hash varchar(128),
    content text not null,
    token_estimate integer not null default 0,
    metadata text,
    created_at timestamp not null
);
```

索引：

```sql
create index idx_code_chunks_repo on code_chunks(repository_id);
create index idx_code_chunks_file on code_chunks(repository_id, file_path);
create index idx_code_chunks_symbol on code_chunks(repository_id, symbol_name);
```

### 8.6 search_evidences 表，V0 可选

如果想保留检索记录，可建：

```sql
create table search_evidences (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    query_text varchar(1024) not null,
    chunk_id varchar(64) not null,
    source varchar(64) not null,
    score double precision not null,
    file_path varchar(1024) not null,
    start_line integer not null,
    end_line integer not null,
    symbol_name varchar(512),
    snippet text,
    created_at timestamp not null
);
```

V0 如果赶进度，可以不持久化 evidence，只在搜索 API 直接返回。

### 8.7 实体与 Repository

建议包：

```text
com.repolens.repository.domain.RepositoryEntity
com.repolens.repository.domain.RepositoryFileEntity
com.repolens.chunking.domain.CodeChunkEntity
```

JPA Repository：

```text
RepositoryJpaRepository
RepositoryFileJpaRepository
CodeChunkJpaRepository
```

### 8.8 测试

测试：

- Flyway migration 可以跑通。
- repositories insert/select 正常。
- code_chunks insert/select 正常。

### 8.9 验收

- [ ] 空库启动后自动创建 V0 表。
- [ ] RepositoryEntity 可保存。
- [ ] CodeChunkEntity 可保存。
- [ ] migration 文件命名规范。

## 9. V0-3：Repository API 与本地导入

### 9.1 目标

实现仓库管理最小 API，让前端/用户可以创建本地仓库导入。

### 9.2 API

#### 创建仓库

```text
POST /api/repositories
```

请求：

```json
{
  "sourceType": "LOCAL",
  "localPath": "F:/Desktop/agent/RepoLens/evals/demo_repos/java_service",
  "name": "java_service"
}
```

响应：

```json
{
  "id": "repo_xxx",
  "name": "java_service",
  "sourceType": "LOCAL",
  "status": "READY",
  "fileCount": 128,
  "chunkCount": 382,
  "skippedFileCount": 14,
  "languageSummary": {
    "JAVA": 92,
    "YAML": 4,
    "XML": 2
  },
  "createdAt": "2026-06-28T16:00:00"
}
```

V0 可同步执行导入。V1 再异步化。

#### 仓库列表

```text
GET /api/repositories
```

#### 仓库详情

```text
GET /api/repositories/{repositoryId}
```

#### 仓库状态

```text
GET /api/repositories/{repositoryId}/status
```

响应：

```json
{
  "repositoryId": "repo_xxx",
  "status": "READY",
  "fileCount": 128,
  "chunkCount": 382,
  "skippedFileCount": 14,
  "lastError": null
}
```

### 9.3 类设计

```text
repository/api/RepositoryController
repository/api/dto/CreateRepositoryRequest
repository/api/dto/RepositoryResponse
repository/application/RepositoryApplicationService
repository/application/RepositoryImportService
repository/domain/RepositoryStatus
repository/domain/RepositorySourceType
```

### 9.4 本地路径安全

V0 即使不做完整权限，也必须做路径规范化：

```text
Path input = Paths.get(localPath).toAbsolutePath().normalize()
```

检查：

- 路径存在。
- 路径是目录。
- 路径可读。
- 不允许直接导入根目录，如 `C:\`、`F:\`。
- 不允许导入用户主目录整体。

V0 可先不做用户级 workspace 限制，但必须避免误扫整盘。

### 9.5 导入流程

V0 同步流程：

```text
create repository(status=CREATED)
  -> scan files(status=SCANNING)
  -> parse Java files(status=PARSING)
  -> build chunks(status=CHUNKING)
  -> build Lucene index(status=INDEXING)
  -> update stats(status=READY)
```

异常：

```text
catch exception
  -> repository.status = FAILED
  -> repository.last_error = exception summary
```

### 9.6 测试

测试：

- localPath 不存在，返回 400。
- localPath 是文件，返回 400。
- 导入 demo repo 后生成 repository record。
- 导入失败时 status 为 FAILED。

### 9.7 验收

- [ ] `POST /api/repositories` 可以导入本地 Java 仓库。
- [ ] `GET /api/repositories` 能看到导入记录。
- [ ] `GET /api/repositories/{id}/status` 能看到 file/chunk 统计。
- [ ] 错误路径不会导致后端崩溃。

## 10. V0-4：Scanner 文件扫描与过滤

### 10.1 目标

将仓库目录转换为可解析文件列表，并过滤依赖、缓存、二进制、大文件和敏感文件。

### 10.2 包设计

```text
scanner/RepositoryScanner
scanner/ScannedFile
scanner/FileLanguageDetector
scanner/FileSkipPolicy
scanner/ContentHashService
```

### 10.3 默认忽略目录

```text
.git
node_modules
dist
build
target
.next
.venv
venv
__pycache__
coverage
.idea
.vscode
out
bin
logs
```

### 10.4 默认忽略文件

```text
*.class
*.jar
*.war
*.zip
*.tar
*.gz
*.png
*.jpg
*.jpeg
*.gif
*.pdf
*.log
package-lock.json
pnpm-lock.yaml
yarn.lock
```

### 10.5 敏感文件规则

文件名命中以下规则则跳过：

```text
.env
.env.*
*.pem
*.key
id_rsa
id_dsa
*secret*
*token*
*credential*
application-prod.yml
application-prod.yaml
application-prod.properties
```

注意：V0 不需要内容级 secret 扫描，但文件名级必须有。

### 10.6 语言识别

| 扩展名 | language |
| --- | --- |
| `.java` | JAVA |
| `.kt` | KOTLIN，可先作为 TEXT |
| `.py` | PYTHON |
| `.ts` | TYPESCRIPT |
| `.tsx` | TYPESCRIPT |
| `.js` | JAVASCRIPT |
| `.jsx` | JAVASCRIPT |
| `.xml` | XML |
| `.yml` / `.yaml` | YAML |
| `.properties` | PROPERTIES |
| `.md` | MARKDOWN |
| 其他 | TEXT 或 UNKNOWN |

V0 只解析 JAVA，其余可生成文件级 chunk 或先跳过。

### 10.7 ScannedFile 字段

```text
repositoryId
relativePath
absolutePath
language
sizeBytes
contentHash
skipped
skipReason
```

### 10.8 统计输出

Scanner 返回：

```json
{
  "totalFiles": 145,
  "acceptedFiles": 112,
  "skippedFiles": 33,
  "languageSummary": {
    "JAVA": 86,
    "YAML": 5,
    "XML": 2,
    "MARKDOWN": 3
  },
  "skipSummary": {
    "IGNORED_DIRECTORY": 18,
    "SENSITIVE_FILE": 2,
    "BINARY_FILE": 6,
    "TOO_LARGE": 7
  }
}
```

### 10.9 测试 fixtures

创建测试目录：

```text
backend-java/src/test/resources/fixtures/scanner/sample-repo/
  src/main/java/com/demo/UserService.java
  src/main/resources/application.yml
  .env
  target/classes/Demo.class
  node_modules/pkg/index.js
  README.md
```

### 10.10 测试

- `.git`、`target`、`node_modules` 被跳过。
- `.env` 被标记 sensitive。
- `.java` 识别为 JAVA。
- 大文件被跳过。
- relative path 使用 `/` 或统一规范，不随 Windows 反斜杠混乱。

### 10.11 验收

- [ ] Scanner 能递归扫描 demo repo。
- [ ] 文件过滤符合预期。
- [ ] languageSummary 正确。
- [ ] repository_files 表记录 accepted 和 skipped 文件。

## 11. V0-5：Java Parser

### 11.1 目标

解析 Java 文件，提取包名、import、class、method、annotation、起止行号，为 chunk 和后续图谱打基础。

### 11.2 推荐库

优先选择：

```text
JavaParser
```

原因：

- 集成简单。
- 能获取 AST。
- 支持起止行号。
- 对 V0 足够。

Maven 依赖：

```xml
<dependency>
  <groupId>com.github.javaparser</groupId>
  <artifactId>javaparser-core</artifactId>
  <version>3.x.x</version>
</dependency>
```

版本号实现时按可用最新稳定版选择。

### 11.3 包设计

```text
parser/CodeParser
parser/ParsedFile
parser/ParsedSymbol
parser/JavaParserService
parser/ParseError
parser/SymbolType
```

接口：

```java
public interface CodeParser {
    ParsedFile parse(Path file, String relativePath, String content);
    boolean supports(Language language);
}
```

### 11.4 ParsedFile

字段：

```text
relativePath
language
packageName
imports[]
symbols[]
errors[]
```

### 11.5 ParsedSymbol

字段：

```text
symbolName
qualifiedName
symbolType: CLASS / INTERFACE / ENUM / RECORD / METHOD / CONSTRUCTOR
parentSymbolName
startLine
endLine
annotations[]
modifiers[]
signature
metadata
```

### 11.6 必须提取的 Java 信息

类级：

- class name
- interface name
- enum name
- record name
- annotations
- start line
- end line

方法级：

- method name
- constructor name
- return type
- parameter types
- annotations
- modifiers
- start line
- end line

Spring 常见注解：

```text
@RestController
@Controller
@Service
@Repository
@Component
@Configuration
@Bean
@Transactional
@GetMapping
@PostMapping
@PutMapping
@DeleteMapping
@PatchMapping
@RequestMapping
```

V0 不要求构建调用关系，但可以把 method call names 放 metadata，为 V1 做准备。

### 11.7 Route 提取规则

V0 可以做轻量 route：

- 类上 `@RequestMapping("/api/users")`
- 方法上 `@GetMapping("/{id}")`
- 合成 route：`GET /api/users/{id}`

如果实现成本高，V0 至少把注解原文保存到 metadata。

### 11.8 解析失败降级

JavaParser 抛异常时：

- 记录 parse error。
- 不中断仓库导入。
- 该文件交给 file-level chunk fallback。

### 11.9 测试 fixtures

创建：

```text
backend-java/src/test/resources/fixtures/parser/java/UserController.java
backend-java/src/test/resources/fixtures/parser/java/UserService.java
backend-java/src/test/resources/fixtures/parser/java/BrokenJava.java
```

`UserController.java` 应包含：

```java
@RestController
@RequestMapping("/api/users")
public class UserController {
    private final UserService userService;

    @GetMapping("/{id}")
    public UserDto getUser(@PathVariable Long id) {
        return userService.getUser(id);
    }
}
```

### 11.10 测试

- 能提取 `UserController` class。
- 能提取 `getUser` method。
- method start/end line 正确。
- annotations 包含 `RestController` 和 `GetMapping`。
- broken file 不导致 parser service 失败。

### 11.11 验收

- [ ] Java class/method 解析稳定。
- [ ] Spring 注解进入 metadata。
- [ ] 起止行号可用于 snippet。
- [ ] 解析失败有 fallback。

## 12. V0-6：Chunk Builder

### 12.1 目标

把 parser 输出转换为可检索、可展示、可持久化的代码 chunk。

### 12.2 包设计

```text
chunking/ChunkBuilder
chunking/CodeChunk
chunking/ChunkType
chunking/LineSliceService
chunking/TokenEstimateService
```

### 12.3 Chunk 类型

| 类型 | 说明 |
| --- | --- |
| FILE | 整个小文件或解析失败 fallback |
| CLASS | 类、接口、枚举、record |
| METHOD | 方法、构造器 |
| CONFIG | YAML、properties、XML |
| TEXT | README 或普通文本 |

V0 重点：`CLASS` 和 `METHOD`。

### 12.4 构建规则

1. 对 Java 文件：
   - 每个 method 生成一个 METHOD chunk。
   - 每个 class 生成一个 CLASS chunk，但如果 class 内容太大，可以只保留 class signature + metadata。
   - 解析失败时生成 FILE chunk。

2. 对配置文件：
   - 小于最大字符数，生成 CONFIG chunk。
   - 过大则跳过或按固定行数切分。

3. 对 Markdown：
   - V0 可跳过，也可生成 TEXT chunk。

### 12.5 Chunk 内容

METHOD chunk 内容应该包含：

```text
// file: src/main/java/com/demo/UserController.java
// symbol: UserController#getUser
// lines: 12-15
@GetMapping("/{id}")
public UserDto getUser(@PathVariable Long id) {
    return userService.getUser(id);
}
```

这样 BM25 对 file/symbol/annotation 都更友好。

### 12.6 token 估算

V0 简化：

```text
tokenEstimate = max(1, content.length / 4)
```

### 12.7 content hash

每个 chunk 计算 hash：

```text
sha256(filePath + startLine + endLine + content)
```

用于 V1 增量索引。

### 12.8 数据保存

保存到 `code_chunks`：

- repository_id
- file_id
- file_path
- language
- symbol_name
- symbol_type
- start_line
- end_line
- content
- content_hash
- token_estimate
- metadata

### 12.9 测试

- 一个 Java class 产生 class chunk 和 method chunk。
- method chunk 内容包含注解和方法体。
- startLine/endLine 对应真实文件。
- broken file 生成 FILE chunk。
- chunk hash 稳定。

### 12.10 验收

- [ ] 导入 demo repo 后 `chunk_count > 0`。
- [ ] Java 方法级 chunk 可查。
- [ ] chunk 内容可用于 snippet。
- [ ] chunk 行号准确。

## 13. V0-7：Lucene BM25 检索

### 13.1 目标

建立本地关键词检索能力，完成 V0 的查询闭环。

### 13.2 包设计

```text
indexing/lexical/LuceneIndexService
indexing/lexical/LuceneDocumentMapper
indexing/lexical/LuceneIndexPathResolver
retrieval/RetrievalService
retrieval/SearchEvidence
retrieval/SearchRequest
retrieval/SearchResponse
```

### 13.3 索引目录

```text
.repolens-java/
  indexes/
    lucene/
      {repository_id}/
```

### 13.4 Lucene Fields

| Field | Stored | Indexed | 说明 |
| --- | --- | --- | --- |
| `chunk_id` | yes | no | chunk id |
| `repository_id` | yes | yes | 仓库 |
| `file_path` | yes | yes | 文件路径 |
| `language` | yes | yes | 语言 |
| `symbol_name` | yes | yes | 符号 |
| `symbol_type` | yes | yes | 类型 |
| `content` | yes | yes | 代码内容 |
| `metadata` | yes | yes | 注解、route 等 |

### 13.5 Analyzer

V0 使用：

```text
StandardAnalyzer
```

后续可以针对代码加自定义 analyzer：

- camelCase split
- snake_case split
- path tokenization
- symbol boost

### 13.6 查询策略

V0 使用 MultiFieldQueryParser：

权重建议：

```text
symbol_name: 3.0
file_path: 2.5
metadata: 2.0
content: 1.0
```

查询字段：

```text
symbol_name
file_path
metadata
content
```

### 13.7 检索 API

```text
POST /api/repositories/{repositoryId}/retrieve
```

请求：

```json
{
  "query": "JWT authentication filter",
  "topK": 10
}
```

响应：

```json
{
  "repositoryId": "repo_xxx",
  "query": "JWT authentication filter",
  "items": [
    {
      "evidenceId": "ev_xxx",
      "chunkId": "chunk_xxx",
      "source": "BM25",
      "score": 12.38,
      "filePath": "src/main/java/com/demo/security/JwtAuthenticationFilter.java",
      "startLine": 21,
      "endLine": 68,
      "symbolName": "JwtAuthenticationFilter#doFilterInternal",
      "symbolType": "METHOD",
      "snippet": "protected void doFilterInternal(...) { ... }",
      "reason": "Matched symbol/content terms: JWT authentication filter"
    }
  ]
}
```

### 13.8 snippet 规则

V0 简化：

- snippet 取 chunk content 前 600 字符。
- 高亮可后续做。
- 返回时去掉过长空白。

### 13.9 测试

- 索引 3 个 chunk，查询方法名能命中正确 chunk。
- 查询文件路径片段能命中文件。
- 查询 Spring 注解能命中 Controller 方法。
- topK 生效。
- 不存在 repository 返回 404。

### 13.10 验收

- [ ] 导入完成后自动建立 Lucene 索引。
- [ ] 搜索 API 返回 BM25 evidence。
- [ ] 搜索结果包含 path、line、symbol、snippet。
- [ ] 查询常见关键词可命中正确方法。

## 14. V0-8：前端适配与 Evidence 展示

### 14.1 目标

复用旧 Next.js 工作台，让用户能在界面上看到 Java 后端 V0 闭环。

### 14.2 前端改动范围

优先只改：

```text
frontend/lib/api.ts
frontend/types/workbench.ts 或 frontend/types/api.ts
frontend/components/repository-list.tsx
frontend/components/evidence-panel.tsx
frontend/app/page.tsx
```

如果旧组件命名不完全一致，按现有结构适配。

### 14.3 环境变量

新增或复用：

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

### 14.4 Repository Panel

V0 展示：

- 仓库名称
- status
- fileCount
- chunkCount
- skippedFileCount
- languageSummary
- lastError

### 14.5 Import Form

字段：

- name
- localPath

提交到：

```text
POST /api/repositories
```

### 14.6 Retrieval / Evidence Panel

输入：

- query
- topK

调用：

```text
POST /api/repositories/{id}/retrieve
```

展示：

- score
- source = BM25
- filePath
- startLine-endLine
- symbolName
- snippet

### 14.7 V0 UI 原型

```text
左侧：Repository List + Import
中间：Search Box + Evidence Results
右侧：Repository Status / Language Summary
```

V0 不需要 Ask Panel 生成自然语言回答。检索证据本身就是原型核心。

### 14.8 前端构建验证

```powershell
cd frontend
npm run build
```

### 14.9 验收

- [ ] 前端能连 Java 后端。
- [ ] 能提交本地路径导入。
- [ ] 能看到 repository status。
- [ ] 能输入 query 并看到 evidence。
- [ ] 前端 build 通过。

## 15. V0-9：测试、Demo Runbook 与收尾

### 15.1 目标

把 V0 从“开发完成”收束成“可复现演示版本”。

### 15.2 后端测试清单

| 测试 | 覆盖 |
| --- | --- |
| `StatusControllerTest` | `/api/status` |
| `RepositoryControllerTest` | 创建仓库、列表、状态 |
| `RepositoryScannerTest` | 文件过滤、语言识别、敏感文件 |
| `JavaParserServiceTest` | class/method/annotation/line range |
| `ChunkBuilderTest` | method chunk、fallback chunk |
| `LuceneIndexServiceTest` | index/search |
| `RetrievalControllerTest` | retrieve API |

### 15.3 集成测试

V0 可以用 H2 或 Testcontainers PostgreSQL：

```text
RepositoryImportIntegrationTest
```

验证完整流程：

```text
given sample Java repo
when import repository
then repository status READY
and chunk_count > 0
and retrieve("UserService") returns evidence
```

### 15.4 Demo 仓库

建议创建：

```text
evals/demo_repos/java_service/
  README.md
  pom.xml
  src/main/java/com/repolens/demo/
    DemoApplication.java
    user/UserController.java
    user/UserService.java
    user/UserRepository.java
    security/JwtAuthenticationFilter.java
    task/TaskScheduler.java
  src/test/java/com/repolens/demo/
    user/UserServiceTest.java
```

V0 demo 查询：

| Query | 预期命中 |
| --- | --- |
| `JWT authentication filter` | `JwtAuthenticationFilter#doFilterInternal` |
| `create user service` | `UserService#createUser` |
| `GET /api/users` | `UserController#getUser` |
| `scheduled task` | `TaskScheduler` |
| `repository save user` | `UserRepository` 或 `UserService#createUser` |

### 15.5 Demo Runbook

新增：

```text
docs/repolens-java-v0-demo-runbook.md
```

内容：

1. 启动数据库。
2. 启动 backend-java。
3. 启动 frontend。
4. 导入 `evals/demo_repos/java_service`。
5. 查看 status。
6. 查询 3 个问题。
7. 截图。
8. 常见错误处理。

### 15.6 截图清单

V0 最少 3 张：

1. `java-v0-repository-status.png`
2. `java-v0-evidence-search.png`
3. `java-v0-language-summary.png`

目录：

```text
docs/assets/screenshots/
```

### 15.7 README 更新

V0 完成后，README 应增加：

- Java Edition V0 状态。
- 启动命令。
- V0 Demo 步骤。
- V0 已完成能力。
- V0 不包含 AI/MCP，V1 规划中。

### 15.8 验收

- [ ] 后端测试通过。
- [ ] 前端 build 通过。
- [ ] runbook 可复现。
- [ ] 至少 3 张截图。
- [ ] README 更新。

## 16. V0 API 汇总

| Method | Path | 用途 | 状态 |
| --- | --- | --- | --- |
| GET | `/health` | 健康检查 | 必做 |
| GET | `/api/status` | 服务状态 | 必做 |
| POST | `/api/repositories` | 导入本地仓库 | 必做 |
| GET | `/api/repositories` | 仓库列表 | 必做 |
| GET | `/api/repositories/{id}` | 仓库详情 | 必做 |
| GET | `/api/repositories/{id}/status` | 仓库状态 | 必做 |
| POST | `/api/repositories/{id}/retrieve` | BM25 检索 | 必做 |
| GET | `/api/repositories/{id}/files` | 文件列表 | 可选 |
| GET | `/api/repositories/{id}/chunks` | chunk 列表 | 可选 |

## 17. V0 后端包与类清单

### 17.1 common

```text
common/id/IdGenerator
common/error/ApiException
common/error/GlobalExceptionHandler
common/time/TimeProvider
common/hash/HashService
```

### 17.2 config

```text
config/RepoLensProperties
config/WebConfig
```

### 17.3 repository

```text
repository/api/RepositoryController
repository/api/dto/CreateRepositoryRequest
repository/api/dto/RepositoryResponse
repository/api/dto/RepositoryStatusResponse
repository/application/RepositoryApplicationService
repository/application/RepositoryImportService
repository/domain/RepositoryEntity
repository/domain/RepositoryFileEntity
repository/domain/RepositoryStatus
repository/domain/RepositorySourceType
repository/infrastructure/RepositoryJpaRepository
repository/infrastructure/RepositoryFileJpaRepository
```

### 17.4 scanner

```text
scanner/RepositoryScanner
scanner/ScannedFile
scanner/FileLanguageDetector
scanner/FileSkipPolicy
scanner/ContentHashService
scanner/SkipReason
scanner/Language
```

### 17.5 parser

```text
parser/CodeParser
parser/JavaParserService
parser/ParsedFile
parser/ParsedSymbol
parser/SymbolType
parser/ParseError
```

### 17.6 chunking

```text
chunking/ChunkBuilder
chunking/CodeChunkEntity
chunking/ChunkType
chunking/LineSliceService
chunking/TokenEstimateService
chunking/infrastructure/CodeChunkJpaRepository
```

### 17.7 indexing / retrieval

```text
indexing/lexical/LuceneIndexService
indexing/lexical/LuceneDocumentMapper
indexing/lexical/LuceneIndexPathResolver
retrieval/api/RetrievalController
retrieval/api/dto/RetrievalRequest
retrieval/api/dto/RetrievalResponse
retrieval/application/RetrievalService
retrieval/domain/SearchEvidence
```

## 18. V0 配置清单

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/repolens_java
    username: repolens
    password: repolens
  flyway:
    enabled: true

repolens:
  workspace-root: ./.repolens-java/repos
  index-root: ./.repolens-java/indexes
  scanner:
    max-file-size-bytes: 1048576
    follow-symlinks: false
  retrieval:
    default-top-k: 10
    max-top-k: 30
```

如果 V0 暂时使用 H2：

```yaml
spring:
  datasource:
    url: jdbc:h2:file:./.repolens-java/repolens
```

但文档和最终方案应以 PostgreSQL 为目标。

## 19. V0 Docker Compose 建议

V0 最小服务：

```text
postgres
backend-java
frontend
```

V0 可以暂不启动 Redis/Qdrant。

`docker-compose.java-v0.yml` 可选：

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: repolens_java
      POSTGRES_USER: repolens
      POSTGRES_PASSWORD: repolens
    ports:
      - "5432:5432"
    volumes:
      - repolens_java_pg:/var/lib/postgresql/data

volumes:
  repolens_java_pg:
```

## 20. V0 风险与处理

| 风险 | 表现 | 处理 |
| --- | --- | --- |
| JavaParser 对部分源码失败 | 解析异常 | 降级为 FILE chunk，记录 parse error |
| Windows 路径混乱 | 反斜杠/斜杠不一致 | 存储 relative path 时统一 `/` |
| 扫描误扫大目录 | 导入耗时过长 | 拒绝根目录和用户主目录，限制文件数可选 |
| Lucene 索引损坏 | 查询失败 | 删除该 repo index 后重建 |
| 前端旧类型不匹配 | build 失败 | 新增 Java V0 API adapter，不大改组件 |
| 数据库配置阻碍进度 | 启动失败 | 开发期用 H2，验收前切 PostgreSQL |

## 21. V0 完成后的 README 表达

可以写：

> Java Edition V0 has completed the local repository indexing and lexical retrieval loop. The Spring Boot backend can import a local Java repository, scan and filter files, parse Java classes and methods, build method-level chunks, create a Lucene BM25 index, and return evidence results with file paths, line ranges, symbols, snippets, and scores. The Next.js workbench can display repository status and retrieval evidence from the Java backend.

中文：

> RepoLens-Java V0 已完成本地仓库索引与关键词检索闭环。Spring Boot 后端支持导入本地 Java 仓库、扫描过滤文件、解析 Java 类和方法、构建方法级 Chunk、建立 Lucene BM25 索引，并返回带文件路径、行号、符号、片段和分数的 Evidence。Next.js 工作台已能展示 Java 后端的仓库状态和检索证据。

## 22. V0 到 V1 的衔接

V0 完成后，V1 不需要推倒重来。各模块扩展方式：

| V0 模块 | V1 扩展 |
| --- | --- |
| Repository 同步导入 | 异步索引任务、Redis lock、失败重试 |
| Scanner | 增加 Git clone、更多语言、内容级 secret hint |
| Java Parser | 增加调用关系、测试映射、Spring route graph |
| Chunk Builder | 增量 hash、上下文合并、token budget |
| Lucene BM25 | 加入向量召回和 graph expansion |
| Retrieval API | 输出 hybrid evidence 和 score breakdown |
| Evidence Panel | 接入 QA/Review citation |
| 无 Agent | 增加 Spring AI Tool Calling 和 Verifier |
| 无 MCP | 增加 MCP Server 和 Tool Audit |

## 23. V0 最终验收表

| 编号 | 验收项 | 是否必须 |
| --- | --- | --- |
| A01 | `backend-java` 可启动 | 必须 |
| A02 | `/api/status` 正常 | 必须 |
| A03 | Flyway 初始化 V0 schema | 必须 |
| A04 | 可以导入本地 Java demo repo | 必须 |
| A05 | Scanner 有过滤和 language summary | 必须 |
| A06 | Java Parser 提取 class/method/annotation/line | 必须 |
| A07 | Chunk Builder 生成 method chunk | 必须 |
| A08 | Lucene 建索引并可搜索 | 必须 |
| A09 | Retrieve API 返回 evidence | 必须 |
| A10 | 前端展示 repository status | 必须 |
| A11 | 前端展示 evidence list | 必须 |
| A12 | 后端核心测试通过 | 必须 |
| A13 | 前端 build 通过 | 必须 |
| A14 | V0 demo runbook 完成 | 必须 |
| A15 | V0 截图至少 3 张 | 建议 |

## 24. 最终结论

V0 的核心不是 AI，而是 Java 后端基础能力：

```text
仓库导入 -> 安全扫描 -> Java 结构解析 -> 方法级 Chunk -> BM25 索引 -> Evidence API -> 前端展示
```

只要 V0 稳定完成，RepoLens-Java 就已经从“想法”变成了可运行产品原型。后续 V1 的 Spring AI、MCP、向量检索、PR Review 和评测，都可以沿着 V0 的模块边界自然扩展。
