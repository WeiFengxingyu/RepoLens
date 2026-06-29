# RepoLens-Java V1-P3 详细设计：向量检索与混合召回

## 1. 阶段定位

V1-P3 将 V0 的 BM25 检索升级为 Hybrid Retrieval。为了保证本地闭环和测试稳定，本阶段先实现确定性的本地 mock embedding 与数据库向量存储，后续可替换为 Spring AI EmbeddingModel + Qdrant/PGvector。

## 2. 阶段目标

- 新增 `vector_chunks`。
- 为每个 chunk 生成确定性 embedding。
- 支持 vector-only 检索。
- 支持 BM25 + Vector 分数归一化和合并。
- 支持 Graph expansion，把相关 symbol 的 chunk 补充为 evidence。
- retrieval debug 显示 bm25/vector/graph/merged/evidence 数量。

## 3. 非目标

- 不调用外部 embedding API。
- 不引入真实向量数据库。
- 不做复杂 LLM rerank。
- 不做跨仓库检索。

## 4. 检索流程

```text
query
  -> BM25 recall
  -> query embedding
  -> vector recall
  -> merge by chunk id
  -> graph expansion from top symbols
  -> normalize score
  -> topK evidence
```

## 5. 数据模型

### 5.1 `vector_chunks`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | varchar(64) | vector row id |
| repository_id | varchar(64) | repo id |
| chunk_id | varchar(64) | chunk id |
| embedding_model | varchar(128) | mock/simple-hash-v1 |
| dimensions | integer | 维度 |
| vector | text | JSON float array |
| content_hash | varchar(128) | chunk content hash |
| created_at | timestamp | 创建时间 |

## 6. 后端设计

### 6.1 核心类

| 类 | 职责 |
| --- | --- |
| `ChunkVectorEntity` | 向量持久化 |
| `ChunkVectorJpaRepository` | 向量查询 |
| `EmbeddingProvider` | embedding 接口 |
| `HashEmbeddingProvider` | 确定性本地 embedding |
| `VectorIndexService` | 为 chunks 建向量索引 |
| `VectorSearchService` | cosine similarity 查询 |
| `HybridRetrievalService` | 合并 BM25/vector/graph |

### 6.2 Hash Embedding

本地 embedding 算法：

- 文本按非字母数字切 token。
- 每个 token 用 hash 映射到固定维度。
- 使用 token hash 的正负号累加。
- 最后做 L2 normalize。

优点：

- 不依赖网络。
- 测试结果稳定。
- 可以体现 embedding/vector pipeline 的工程设计。
- 后续替换真实 embedding 时接口不变。

### 6.3 Score Merge

| 分数 | 归一化 |
| --- | --- |
| BM25 | 除以当前 BM25 max score |
| Vector | cosine similarity 映射到 0-1 |
| Graph | relation 命中固定加权，默认 0.25 |

最终分数：

```text
score = 0.55 * bm25 + 0.35 * vector + 0.10 * graph
```

当只启用某一种检索时，未启用分数为 0，但 evidence source 仍准确标注。

## 7. API 设计

继续使用现有 API：

```http
POST /api/repositories/{repositoryId}/retrieve
```

请求：

```json
{
  "query": "where is JWT authentication checked",
  "top_k": 10,
  "use_bm25": true,
  "use_vector": true,
  "use_graph": true
}
```

响应中的 evidence：

- `source`：最高贡献来源。
- `sources`：包含 `BM25`、`VECTOR`、`GRAPH`。
- `bm25_score`
- `vector_score`
- `graph_score`
- `score`

## 8. 前端设计

P3 前端最小闭环：

- 检索表单保留 BM25/vector/graph 开关。
- evidence list 展示 source badge。
- debug panel 展示 bm25/vector/graph/merged/evidence count。
- vector 不再显示 V0 disabled reason。

## 9. 测试计划

- `HashEmbeddingProviderTest` 验证维度、归一化、确定性。
- `VectorSearchServiceTest` 验证相似文本可召回。
- `RetrievalControllerTest` 更新 vector/graph 断言。
- 新增 hybrid 检索测试，验证 sources 包含 `BM25`、`VECTOR` 或 `GRAPH`。

## 10. 验收标准

- 导入仓库后 `vector_chunks` 数量等于 chunk 数量。
- use_vector=true 时 debug.vector_count 大于 0。
- use_graph=true 时 graph expansion 可返回相关 evidence。
- response 不再显示 V0 vector disabled reason。
- 所有后端测试通过。

