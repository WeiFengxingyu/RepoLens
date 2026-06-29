# RepoLens-Java V1-P2 详细设计：多语言解析与代码图谱

## 1. 阶段定位

V1-P2 将 V0 的 chunk 级检索升级为 symbol/relation 级代码理解。该阶段不追求完整编译级调用图，而是构建对问答和 PR Review 有直接价值的轻量代码图谱。

## 2. 阶段目标

- 新增 `code_symbols` 和 `code_relations`。
- 将 Java parser 的 symbols 持久化。
- 增加 Python、TypeScript/JavaScript 的基础 symbol 解析。
- 从 imports、parent-child、route metadata 构建 relation。
- 新增 graph query API。
- repository 的 `relation_count` 由真实图谱结果更新。

## 3. 非目标

- 不做跨模块完整类型解析。
- 不做 Java 字节码/编译器级调用图。
- 不做复杂 TypeScript AST 解析。
- 不引入 Neo4j，V1 使用关系型表承载轻量图谱。

## 4. 语言范围

| 语言 | P2 实现 |
| --- | --- |
| Java | 复用 JavaParser，持久化 class/method/constructor/route |
| Python | 基于缩进和定义行提取 class/function/import/decorator |
| TypeScript/JavaScript | 基于结构模式提取 import/export/class/function/method/component |

## 5. 数据模型

### 5.1 `code_symbols`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | varchar(64) | symbol id |
| repository_id | varchar(64) | repo id |
| file_path | varchar(1024) | 文件路径 |
| language | varchar(64) | 语言 |
| symbol_name | varchar(512) | 短名 |
| qualified_name | varchar(1024) | 全名 |
| symbol_type | varchar(64) | CLASS/METHOD/FUNCTION 等 |
| parent_symbol_name | varchar(1024) | 父 symbol |
| start_line | integer | 起始行 |
| end_line | integer | 结束行 |
| signature | text | 声明 |
| metadata | text | route、annotations、imports 等 |
| created_at | timestamp | 创建时间 |

### 5.2 `code_relations`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | varchar(64) | relation id |
| repository_id | varchar(64) | repo id |
| relation_type | varchar(64) | CONTAINS/IMPORTS/ROUTE/REFERENCES |
| source_symbol_id | varchar(64) | 源 symbol，可为空 |
| target_symbol_id | varchar(64) | 目标 symbol，可为空 |
| source_name | varchar(1024) | 源名 |
| target_name | varchar(1024) | 目标名 |
| file_path | varchar(1024) | 发生文件 |
| metadata | text | 附加信息 |
| created_at | timestamp | 创建时间 |

## 6. 后端设计

### 6.1 核心类

| 类 | 职责 |
| --- | --- |
| `CodeSymbolEntity` | symbol 持久化 |
| `CodeRelationEntity` | relation 持久化 |
| `CodeSymbolJpaRepository` | symbol 查询 |
| `CodeRelationJpaRepository` | relation 查询 |
| `LanguageParserRegistry` | 按语言选择 parser |
| `SimplePythonParser` | Python 基础解析 |
| `SimpleTypeScriptParser` | TS/JS 基础解析 |
| `CodeGraphBuilder` | 从 ParsedFile 构建 symbol/relation |
| `CodeGraphService` | 查询 symbol 和 neighbors |
| `CodeGraphController` | graph API |

### 6.2 Relation 类型

| 类型 | 来源 | 用途 |
| --- | --- | --- |
| CONTAINS | parent_symbol_name | 类包含方法、类包含构造器 |
| IMPORTS | parsed imports | 解释依赖 |
| ROUTE | Java route metadata | Controller 路由定位 |
| SAME_FILE | 同文件 symbol | fallback impact expansion |

### 6.3 P1 Pipeline 集成

在 `RepositoryIndexPipeline` 的 PARSING 后、CHUNKING 前执行：

```text
parsedFiles -> CodeGraphBuilder -> save code_symbols/code_relations
```

执行前清理当前 repository 的旧 symbols/relations，保证重复索引结果一致。

## 7. API 设计

| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/api/repositories/{id}/symbols?query=UserService` | 搜索 symbol |
| GET | `/api/repositories/{id}/symbols/{symbolId}/neighbors` | 查询相邻 relation |
| GET | `/api/repositories/{id}/graph/summary` | 返回 symbol/relation/route 统计 |

## 8. 前端设计

P2 前端最小闭环：

- repository sidebar 展示 symbol_count/relation_count。
- Evidence metadata 中 route 仍可展示。
- 后续 Ask/Review 页面可调用 symbol search 和 neighbors。

本轮以后端 API 和 retrieval graph expansion 为主，前端可延后在 P3/P4 统一整合。

## 9. 测试计划

- `SimplePythonParserTest` 覆盖 class/function/import。
- `SimpleTypeScriptParserTest` 覆盖 import/export/function/class。
- `CodeGraphBuilderTest` 覆盖 CONTAINS、IMPORTS、ROUTE。
- `CodeGraphControllerTest` 覆盖 summary、symbol search、neighbors。
- 现有导入测试更新 relation_count 从 0 到真实值。

## 10. 验收标准

- 导入 Java Spring Boot demo 后 `code_symbols` 有 class/method。
- route method 会生成 ROUTE relation。
- repository `relation_count` 大于 0。
- 可以通过 API 查询 `UserController` 和其 neighbors。
- Python/TS 文件会生成基础 symbol 和 whole-file chunk。

