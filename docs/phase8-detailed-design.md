# RepoLens V1 Phase 8 详细设计

## 1. 目标与边界

Phase 8 的目标是把 P0+/Phase 4 的“单主 orchestrator + 角色型 Agent 节点”升级为受控的真正多 Agent 协作工作流。核心交付不是增加 Agent 名称，而是落地可追踪的 Agent Session、Agent Message、Agent Assignment、分歧记录、Arbiter 仲裁、轮次限制、证据约束和前端 Multi-Agent Trace Panel。

Phase 8 只做多 Agent 协作与可观测增强，不进入 Phase 9 benchmark 平台，也不进入 Phase 10 发布包装。

## 2. 必做范围

- 新增 `agent_sessions` 表，保存一次多 Agent 协作会话。
- 新增 `agent_messages` 表，保存 Agent 间消息、证据引用、结论、置信度和 dissent。
- 新增 `agent_assignments` 表，保存任务分派、状态、输入输出和 token/latency。
- 新增多 Agent Review API，保留旧 Review API 不变。
- 实现 Coordinator Agent。
- 实现风险、安全、测试三个独立 Review 子任务。
- 实现 Arbiter Agent，合并结论、保留分歧、输出决策理由。
- 实现轮次限制、assignment 限制、evidence policy 和失败降级。
- 前端新增 Multi-Agent Trace Panel，展示角色、消息、分歧、仲裁和最终报告。
- 提供 Phase 8 smoke/evaluation 记录，对比单主 Review 与多 Agent Review。

## 3. 非目标

- 不做无限自治 Agent。
- 不做跨进程 Agent 网络。
- 不做长期个人记忆。
- 不让 Agent 自动执行代码修改、patch application 或 push。
- 不写回 PR/MR，不 approve/request changes。
- 不做 Phase 9 的 20+ 样例 benchmark 平台。
- 不做 Phase 10 截图/发布包装收束。

## 4. 数据模型

### 4.1 agent_sessions

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string uuid | session id |
| `task_id` | FK tasks.id | 关联 `TaskType.MULTI_AGENT_REVIEW` |
| `repository_id` | FK repositories.id | 仓库 |
| `status` | string | pending/running/completed/failed |
| `mode` | string | `multi_agent_review` |
| `round_limit` | int | 最大轮次 |
| `assignment_limit` | int | 最大 assignment 数 |
| `token_budget` | int nullable | 本阶段保留预算字段 |
| `summary` | text nullable | session 摘要 |
| `final_report` | text nullable | JSON 字符串 |
| `error_message` | text nullable | 错误信息 |
| `created_at/started_at/completed_at` | datetime | 生命周期 |

### 4.2 agent_assignments

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string uuid | assignment id |
| `session_id` | FK agent_sessions.id | session |
| `agent_name` | string | Agent 名称 |
| `role` | string | coordinator/risk/security/test/arbiter/report |
| `status` | string | pending/running/completed/failed/skipped |
| `round_index` | int | 第几轮 |
| `input_payload/output_payload` | text | JSON |
| `evidence_ids` | text | JSON list |
| `dissent` | text nullable | JSON dissent payload |
| `confidence` | int | 0-100 |
| `token_estimate` | int | 简单估算 |
| `latency_ms` | int nullable | 执行耗时 |
| `error_message` | text nullable | 错误 |

### 4.3 agent_messages

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string uuid | message id |
| `session_id` | FK agent_sessions.id | session |
| `assignment_id` | FK agent_assignments.id nullable | 来源 assignment |
| `sender` | string | coordinator/risk_reviewer/security_reviewer/test_strategist/arbiter/report_writer |
| `recipient` | string | all/arbiter/coordinator |
| `message_type` | string | assignment/analysis/dissent/arbitration/final |
| `round_index` | int | 第几轮 |
| `content` | text | 可读消息 |
| `evidence_ids` | text | JSON list |
| `claims` | text | JSON list |
| `confidence` | int | 0-100 |
| `requires_arbitration` | bool | 是否需要 Arbiter |
| `created_at` | datetime | 时间 |

## 5. Agent 协作协议

### 5.1 受控状态机

Phase 8 不让 Agent 自由长对话。一次多 Agent Review 固定为：

1. `CoordinatorAgent`
2. `RiskReviewerAgent`
3. `SecurityReviewerAgent`
4. `TestStrategistAgent`
5. `ArbiterAgent`
6. `ReportWriterAgent`

三个 reviewer assignment 在语义上独立，可在实现上顺序执行，记录为同一 round 的独立 assignment。这样先完成协议与可观测闭环，后续可替换为真实并行执行。

### 5.2 Evidence-grounded message policy

- 关键风险结论必须有 `evidence_ids` 或 `diff_refs`。
- 只有 diff 支撑、没有 evidence 的高风险结论必须被 Arbiter 降级或标记为 dissent。
- `SecurityReviewerAgent` 没有发现明确安全风险时必须发出低置信度 no-op 消息，而不是编造风险。
- `ArbiterAgent` 必须显式记录 accepted、downgraded、rejected 和 dissent。

### 5.3 限制策略

- `round_limit` 默认 2，本阶段实际执行 1 轮 reviewer + 1 轮 arbiter。
- `assignment_limit` 默认 8。
- `token_budget` 默认 8000，本阶段记录估算 token，不调用额外 LLM 时不消耗真实 token。
- 任一 reviewer 失败时 session 降级：记录 failed assignment，其他 assignment 继续，Arbiter 在 final report 中标出缺口。

## 6. 多 Agent Review API

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/repositories/{repository_id}/multi-agent-reviews` | 创建并同步执行多 Agent Review |
| `GET` | `/api/multi-agent-reviews/{task_id}` | 按 task id 查询结果 |
| `GET` | `/api/agent-sessions/{session_id}` | 查询 session、assignment、message |

请求复用 `ReviewCreateRequest`：

```json
{
  "diff_text": "diff --git ...",
  "top_k": 8,
  "use_bm25": true,
  "use_vector": false,
  "use_graph": true,
  "run_static_check": false
}
```

响应新增：

- `session`
- `assignments`
- `messages`
- `dissent`
- `arbiter_decision`
- `review`
- `comparison`

## 7. 实现策略

### 7.1 复用现有 Review 能力

Phase 8 复用：

- `analyze_diff`
- `map_diff_to_symbols`
- `code_search`
- `get_symbol_context`
- `review_risks`
- `verify_review_risks`
- `suggest_review_tests`
- `write_review_report`

旧 `ReviewService` 不改语义。新增 `MultiAgentReviewService` 在独立文件中编排多 Agent session。

### 7.2 Agent 职责

| Agent | 输入 | 输出 |
| --- | --- | --- |
| Coordinator | diff summary、repository id | reviewer assignments、review focus |
| Risk Reviewer | diff、mapping、evidence | functional risk candidates |
| Security Reviewer | diff、mapping、evidence | security-specific risk candidates |
| Test Strategist | verified/draft risks、diff | focused tests |
| Arbiter | reviewer outputs | accepted/downgraded/rejected/dissent |
| Report Writer | arbiter decision、tests、evidence | final report |

### 7.3 Security Reviewer 规则

本阶段采用规则型安全 reviewer：

- 关注 auth、token、secret、permission、path traversal、SQL/string interpolation、unsafe eval/exec、network call。
- 若 diff 或 evidence 没有相关信号，输出 no-op message。
- 对有 diff 支撑但无 evidence 的安全结论标记为 dissent candidate。

### 7.4 Arbiter 规则

- 接受 Verifier 支撑的风险。
- 将高风险但仅 diff 支撑的结论降级为 medium。
- 拒绝无 diff_refs 且无 evidence 的结论。
- 记录 dissent，不静默丢弃。

## 8. 前端设计

Workbench 在 Review 区域新增 `Multi-Agent` 模式或独立 Multi-Agent Panel：

- 可触发多 Agent Review。
- 展示 session status、round limit、assignment count。
- 展示 assignment 列表：role、agent、status、confidence、latency、evidence count。
- 展示 message 列表：sender、type、content、evidence、requires arbitration。
- 展示 Arbiter decision：accepted/downgraded/rejected/dissent。
- 复用 Review 风险、测试、citation、markdown 展示。

## 9. 测试策略

| 类型 | 覆盖 |
| --- | --- |
| model tests | agent_sessions/messages/assignments 表创建、关系、cascade |
| service tests | Coordinator、reviewer、Arbiter、evidence policy、round/assignment limit |
| API tests | POST/GET multi-agent review、repo not ready、missing task/session |
| frontend tests | `npm run build`、`npm exec tsc -- --noEmit` |
| regression | 全量 `ruff check app`、`pytest app/tests`、`docker compose config` |

## 10. 验收标准映射

| V1 P8 验收 | 证明方式 |
| --- | --- |
| 一次 Review 可产生多个 Agent 独立分析 | API/service test 检查 risk/security/test assignments |
| Agent 间消息可追踪 | DB/API response 包含 messages |
| 分歧不会静默丢弃 | Arbiter decision 包含 dissent/downgraded/rejected |
| 最终报告说明结论来源 | final report 包含 source_agents/evidence_ids |
| 流程有轮次/token/失败降级 | session 字段、service tests |
| 前端能展示协作过程 | Multi-Agent Trace Panel build/type check |

## 11. 任务清单

| 编号 | 任务 | 交付 |
| --- | --- | --- |
| P8-001 | 编写 Phase 8 详细设计 | 本文档 |
| P8-002 | 新增 agent_sessions 表 | `models/agent_session.py` |
| P8-003 | 新增 agent_messages 表 | `models/agent_message.py` |
| P8-004 | 新增 agent_assignments 表 | `models/agent_assignment.py` |
| P8-005 | 实现 Coordinator Agent | `services/multi_agent/agents.py` |
| P8-006 | 实现并行 Review 子任务 | risk/security/test assignments |
| P8-007 | 实现 Arbiter Agent | accepted/downgraded/rejected/dissent |
| P8-008 | 实现多 Agent 轮次限制 | round/assignment/token guard |
| P8-009 | 实现 Evidence-grounded message policy | evidence/diff support 校验 |
| P8-010 | 前端 Multi-Agent Trace Panel | Workbench 面板 |
| P8-011 | 多 Agent 评测 | 单主 vs 多 Agent smoke comparison |
| P8-012 | 文档与演示 | README、worklog、closed-loop、final closure |
