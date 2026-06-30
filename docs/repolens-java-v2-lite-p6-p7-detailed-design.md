# RepoLens-Java V2-Lite P6-P7 详细设计

## 1. 设计目标

P6-P7 用于完成 V2-Lite 的产品化闭环：

```text
P6 V2-Lite Workbench
  -> ReviewHub organization/project/repository binding/ruleset
  -> Webhook fixture trigger
  -> Job/Event/Quota/Audit visibility

P7 Observability And Release
  -> local observability view and metrics entry
  -> demo runbook
  -> release package
  -> final closure review
```

本阶段不引入真实 RabbitMQ、Redis、Prometheus Server 或 Grafana 容器。V2-Lite 的目标是保留生产化接口边界，同时保证本地离线可演示、可测试、可写入简历。真实中间件接入保留给 V2 完整版。

## 2. 范围边界

| 阶段 | 做什么 | 暂不做什么 |
| --- | --- | --- |
| P6 | 前端新增 V2-Lite tab、ReviewHub 表单、Webhook fixture 表单、Job/Quota/Audit 展示、API types/helpers | 不做复杂团队成员管理、登录态、RBAC 页面 |
| P7 | 可观测入口说明、演示 runbook、release package、最终闭环审计 | 不接真实 Prometheus/Grafana 部署，不生成截图资产 |

## 3. P6 Workbench 设计

### 3.1 用户路径

P6 在现有首页工作台中新增 `V2-Lite` tab，保持首页就是工具工作台，不做 landing page。

推荐演示路径：

```text
导入或选择 ready repository
  -> 创建 Organization
  -> 创建 Project
  -> 绑定当前 Repository 到 fixture-github / fixture/repolens-java
  -> 创建 Review Ruleset
  -> 触发 fixture Webhook
  -> 查看 Job 状态/result_ref
  -> 刷新 Quota 和 Audit
```

### 3.2 前端 API

新增 `frontend/lib/api.ts` helpers：

| helper | API |
| --- | --- |
| `createOrganization` | `POST /api/organizations` |
| `listOrganizations` | `GET /api/organizations` |
| `createProject` | `POST /api/organizations/{organizationId}/projects` |
| `listProjects` | `GET /api/organizations/{organizationId}/projects` |
| `bindRepositoryToProject` | `POST /api/projects/{projectId}/repositories/{repositoryId}/bind` |
| `listProjectBindings` | `GET /api/projects/{projectId}/repositories` |
| `createReviewRuleset` | `POST /api/projects/{projectId}/rulesets` |
| `listReviewRulesets` | `GET /api/projects/{projectId}/rulesets` |
| `listProjectQuota` | `GET /api/projects/{projectId}/quota` |
| `listAuditLogs` | `GET /api/audit-logs` |
| `triggerWebhookReview` | `POST /api/webhooks/{provider}` |
| `listJobs` | `GET /api/jobs` |
| `getJob` | `GET /api/jobs/{jobId}` |
| `listWorkers` | `GET /api/workers` |

### 3.3 UI 状态

P6 tab 使用紧凑运维工作台布局：

- `ReviewHub Setup`：组织、项目、绑定、规则集操作。
- `Webhook`：fixture provider/external_repo_id/change_url/commit_sha/sender 输入。
- `Async Job`：最新 webhook job、状态、result_ref、attempt/event。
- `Governance`：quota bucket、audit log、worker snapshot。

UI 不使用营销型 hero，不嵌套卡片，保持当前 V1 工作台风格。

## 4. P7 Observability And Release 设计

### 4.1 可观测入口

V2-Lite 不启动真实 Prometheus/Grafana，但提供可观测数据入口：

- Spring Boot Actuator：`/actuator/health`、`/actuator/info`、`/actuator/metrics`
- Job Center：`/api/jobs`、`/api/jobs/{jobId}`、`/api/workers`
- Governance：`/api/projects/{projectId}/quota`、`/api/audit-logs`

这些入口可支撑面试中解释：

- 任务状态机与事件流如何定位异步任务问题。
- quota/audit 如何定位 Webhook 入站治理问题。
- 未来如何替换为 Prometheus/Grafana dashboard。

### 4.2 文档产物

新增：

- `docs/repolens-java-v2-lite-demo-runbook.md`
- `docs/repolens-java-v2-lite-release-package.md`
- `docs/repolens-java-v2-lite-final-closure-review.md`

更新：

- `docs/README.md`
- `docs/repolens-java-v2-lite-design-and-worklog.md`

### 4.3 Release Package 内容

Release package 必须覆盖：

- 项目定位
- V2-Lite 架构图
- API 能力图
- 简历写法
- 面试讲法
- 验证命令
- 已知限制与 V2 完整版升级路线

## 5. 验收标准

| 阶段 | 验收 |
| --- | --- |
| P6 | 前端 V2-Lite tab 可构造 ReviewHub + Webhook 主链路请求，并展示 job/quota/audit/workers |
| P6 | TypeScript 类型覆盖新增 API response/request |
| P7 | runbook 能从启动、导入仓库、配置 ReviewHub、触发 Webhook 到验证 Job 完成 |
| P7 | release package 能直接服务简历和面试表达 |
| P7 | final closure review 明确 P0-P7 验收矩阵、验证命令、已知边界 |

## 6. 测试计划

- 后端：`mvn test`
- 前端：`npm run build`
- 文档审计：确认 docs index 包含 P6/P7 新文档
- 工作流审计：共享过程记录包含 P6/P7 状态、产物、验证结果
