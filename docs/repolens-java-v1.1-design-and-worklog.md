# RepoLens-Java V1.1 共用过程记录

## 1. 记录规则

V1.1 共用一份详细设计和一份过程记录。所有子阶段在当前 `backend-java/`、`frontend/`、`docs/` 中增量完成，不新建独立项目目录。

共享详细设计：

```text
docs/repolens-java-v1.1-shared-detailed-design.md
```

分阶段计划：

```text
docs/repolens-java-v1.1-phased-execution-plan.md
```

## 2. 阶段索引

| 阶段 | 状态 | 目标 |
| --- | --- | --- |
| V1.1-P0 | DONE | 计划、共享详细设计、过程记录 |
| V1.1-P1 | DONE | Change Request 模型/API/SPI |
| V1.1-P2 | DONE | GitHub/GitLab/Gitee Provider |
| V1.1-P3 | DONE | Review 集成和前端 URL 模式 |
| V1.1-P4 | DONE | fixture、runbook、发布闭环 |

## 3. V1.1-P0 执行记录

计划完成：

- 新增 V1.1 分阶段计划书。
- 新增 V1.1 共用详细设计。
- 新增 V1.1 共用过程记录。

完成记录：

- 新增 `docs/repolens-java-v1.1-phased-execution-plan.md`。
- 新增 `docs/repolens-java-v1.1-shared-detailed-design.md`。
- 新增 `docs/repolens-java-v1.1-design-and-worklog.md`。

验证：

- 文档结构满足“V1.1 共用一份详细设计和一份过程记录”的要求。

## 4. V1.1-P1 执行记录

计划完成：

- 新增 `change_requests` migration。
- 新增 Change Request entity/repository。
- 新增 URL parser、Provider SPI、fixture provider。
- 新增 Change Request Review API。
- API 复用 V1 `ReviewService`，不复制 Review 主逻辑。

完成记录：

- 新增 Flyway migration `V10__add_v11_change_requests.sql`。
- 新增 `ChangeRequestEntity` 和 `ChangeRequestJpaRepository`。
- 新增 `ChangeRequestUrlParser`、`ChangeRequestRef`、`ChangeRequestProvider`、`FetchedChangeRequest`。
- 新增 `FixtureChangeRequestProvider`，默认支持 `fixture://github/repolens-java/1`。
- 新增 `ChangeRequestReviewService`，复用 V1 `ReviewService.review(...)`。
- 新增 `ChangeRequestController`：
  - `POST /api/repositories/{repositoryId}/change-requests/reviews`
  - `GET /api/change-requests/{changeRequestId}`
  - `GET /api/change-requests/tasks/{taskId}`

验证：

- `ChangeRequestControllerTest` 覆盖 fixture URL Review、metadata 持久化、review task 关联和查询 API。

## 5. V1.1-P2 执行记录

计划完成：

- 新增 GitHub/GitLab/Gitee provider。
- 新增 token 配置和 redactor。
- 新增 provider 错误归一化。

完成记录：

- 新增 `RepoLensProperties.changeRequest` 配置。
- 新增 `HttpChangeRequestClient`、`SensitiveTextRedactor`、`ProviderFetchException`。
- 新增 `GitHubChangeRequestProvider`，支持 GitHub PR metadata/files/commits/diff 只读拉取。
- 新增 `GitLabChangeRequestProvider`，支持 GitLab MR metadata/changes/commits，并重构 unified diff。
- 新增 `GiteeChangeRequestProvider`，支持 Gitee PR metadata/files/commits，并重构 unified diff。
- Provider token 从 `REPOLENS_GITHUB_TOKEN`、`REPOLENS_GITLAB_TOKEN`、`REPOLENS_GITEE_TOKEN` 读取。
- metadata 入库前经过 redactor，不保存 token。

验证：

- `ChangeRequestUrlParserTest` 覆盖 GitHub/GitLab/Gitee/fixture URL。
- 后端全量测试通过。

## 6. V1.1-P3 执行记录

计划完成：

- Review Tab 增加 Diff / PR URL 模式。
- URL 模式调用 Java Change Request Review API。
- 展示 metadata + review report。

完成记录：

- `frontend/app/page.tsx` 的 Review tab 增加 `Diff` / `PR/MR URL` 模式。
- URL 模式调用 `createChangeRequestReview`。
- 右侧新增 `ChangeRequestMetadataPanel`，展示平台、类型、标题、分支、文件/commit 统计。
- `frontend/types/workbench.ts` 补齐 `provider_status`、`diff_hash`、`metadata`、`error_message`。

验证：

- `npm run build` 通过。

## 7. V1.1-P4 执行记录

计划完成：

- 新增 fixture 或真实案例文档。
- 新增 V1.1 demo runbook。
- 新增 V1.1 final closure review。
- 运行后端测试和前端构建。

完成记录：

- 新增 `evals/change_requests/repolens_java_v1_1_fixture_cases.json`。
- 新增 `docs/repolens-java-v1.1-demo-runbook.md`。
- 新增 `docs/repolens-java-v1.1-real-pr-mr-cases.md`。
- 新增 `docs/repolens-java-v1.1-final-closure-review.md`。

验证：

- 后端 `mvn test` 通过。
- 前端 `npm run build` 通过。
