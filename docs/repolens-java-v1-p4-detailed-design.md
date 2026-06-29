# RepoLens-Java V1-P4 详细设计：Agent QA 与 Trace

## 1. 阶段定位

V1-P4 在 P0-P3 的索引、图谱、混合检索基础上实现仓库级问答 Agent。当前阶段先做 deterministic local agent：不依赖外部 LLM key，用固定 Planner、Tool Registry、Answer Composer、Citation Verifier 跑通完整工程链路。

后续接入 Spring AI ChatClient 时，只替换 `AnswerComposer` 或 planner/model adapter，不改变 API、trace、citation 和工具接口。

## 2. 阶段目标

- 新增仓库问答 API：`POST /api/repositories/{repositoryId}/questions`。
- 新增问答任务查询 API：`GET /api/questions/{taskId}`。
- 实现工具链路：planner -> code.search -> verifier -> answer。
- 复用 P3 hybrid retrieval，生成 citations。
- 返回前端已有的 `QATaskResponse` 契约。
- 记录 agent traces，包含 step、tool call、evidence ids、latency、error。

## 3. 非目标

- 不调用真实外部 LLM。
- 不实现多轮对话记忆。
- 不执行代码、不修改文件。
- 不做复杂 prompt 模板管理。

## 4. 数据模型

### 4.1 `qa_tasks`

| 字段 | 说明 |
| --- | --- |
| id | task id |
| repository_id | 仓库 id |
| status | pending/running/completed/failed |
| question | 用户问题 |
| answer | 生成回答 |
| confidence | 置信度 |
| warnings | JSON 数组 |
| error_message | 失败原因 |
| created_at / completed_at | 时间 |

### 4.2 `agent_traces`

| 字段 | 说明 |
| --- | --- |
| id | trace id |
| task_id | QA 或 Review task id |
| repository_id | 仓库 id |
| step_name | planner/code.search/verifier/final_answer |
| step_order | 顺序 |
| status | completed/failed |
| input_summary | 输入摘要 |
| output_summary | 输出摘要 |
| evidence_ids | JSON 数组 |
| tool_calls | JSON 数组 |
| token_usage | JSON 对象，local agent 置空对象 |
| latency_ms | 耗时 |
| created_at / completed_at | 时间 |

## 5. 后端设计

| 类 | 职责 |
| --- | --- |
| `QATaskEntity` | QA task 持久化 |
| `AgentTraceEntity` | Agent trace 持久化 |
| `QuestionAnsweringService` | QA 主流程 |
| `QuestionController` | QA API |
| `QATaskResponse` | 前端响应 DTO |
| `QACitationResponse` | citation DTO |
| `AgentTraceResponse` | trace DTO |

## 6. QA 流程

```text
POST question
  -> create qa_task running
  -> planner: 选择 hybrid retrieval
  -> code.search: 调用 RetrievalService
  -> verifier: 检查 citations 非空、路径/行号存在
  -> answer: deterministic composer 生成引用回答
  -> persist task completed + traces
```

## 7. 回答策略

本地 composer 输出结构：

```text
根据当前仓库证据，最相关的位置是：
1. path:start-end symbol ...
2. ...

结论：...
```

若 evidence 为空：

- answer 说明“当前索引证据不足”。
- confidence 降低。
- warnings 包含 `NO_EVIDENCE`。

## 8. 测试计划

- 导入 demo repo 后调用 `/questions`。
- 断言 status 为 completed。
- 断言 citations 非空。
- 断言 traces 包含 planner、code.search、verifier、final_answer。
- 断言 answer 包含 evidence 文件路径。
- 断言 `GET /api/questions/{taskId}` 可查询同一结果。

## 9. 验收标准

- 问答 API 可本地稳定运行。
- response 符合前端 `QATaskResponse` 类型。
- citations 来自真实 retrieval evidence。
- trace 能解释 Agent 执行路径。
- 无 evidence 时不编造答案。

