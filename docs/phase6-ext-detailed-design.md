# RepoLens Phase 6.5 / P6-EXT 详细设计

## 1. 目标

Phase 6.5 / P6-EXT 用于补齐 Phase 6 中尚未完整闭环的多代码平台 PR/MR fetch 能力。Phase 6 已完成平台无关 Change Request Provider 抽象和 GitHub PR 只读 client；P6-EXT 在不进入 Phase 7 的前提下，把 Gitee Pull Request、GitLab.com Merge Request 和 self-hosted GitLab Merge Request 从 parser/provider contract 推进到真实只读 fetch client 与 API 闭环。

## 2. 范围边界

### 2.1 In Scope

- 实现 Gitee Pull Request 只读 fetch client。
- 实现 GitLab.com Merge Request 只读 fetch client。
- 实现 self-hosted GitLab Merge Request 只读 fetch client，默认从 MR URL 派生 `https://host/api/v4`，允许 `REPOLENS_GITLAB_BASE_URL` 覆盖。
- 复用 Phase 6 `ChangeRequestProvider`、`FetchedChangeRequest`、`ChangeRequestReviewService`、`change_requests` 表、PR/MR Review API 和前端 PR/MR URL flow。
- 补齐 provider 单元测试、API smoke、错误映射、安全脱敏、diff limit 和文档闭环。

### 2.2 Out of Scope

- 不进入 Phase 7 MCP Server。
- 不实现 GitHub App、Gitee 应用、GitLab OAuth、多用户授权或 webhook。
- 不写回 PR/MR 评论，不 approve/request changes，不 merge/close，不 push，不自动修改外部代码。
- 不做 Phase 9 大规模 benchmark；本阶段只做多平台 PR/MR fetch smoke。

## 3. 平台 API 策略

| 平台 | Metadata | Files / Diffs | Commits | Diff text 策略 |
| --- | --- | --- | --- | --- |
| GitHub | 已实现 `/repos/{owner}/{repo}/pulls/{number}` | 已实现 `/files` | 已实现 `/commits` | GitHub diff media type |
| Gitee | `/repos/{owner}/{repo}/pulls/{number}` | `/repos/{owner}/{repo}/pulls/{number}/files` | `/repos/{owner}/{repo}/pulls/{number}/commits` | 从 file patch 重建 unified diff |
| GitLab.com | `/projects/{project_id}/merge_requests/{iid}` | `/projects/{project_id}/merge_requests/{iid}/diffs` | `/projects/{project_id}/merge_requests/{iid}/commits` | 从 MR diff entries 重建 unified diff |
| self-hosted GitLab | 同 GitLab API v4 | 同 GitLab API v4 | 同 GitLab API v4 | 从 MR diff entries 重建 unified diff |

Gitee token 使用 `access_token` query 参数，避免在持久化 metadata、API response、tool calls 或 trace 中出现。GitLab token 使用 `PRIVATE-TOKEN` header。所有 provider 错误仍由 API 层统一脱敏。

## 4. 实现设计

### 4.1 Provider 复用

继续使用 `backend/app/services/change_request/providers.py` 中的 `ChangeRequestProvider` 抽象。Gitee 和 GitLab provider 从默认 not implemented 改为实现 `fetch(ref, settings)`。

Gitee fetch 流程：

1. 校验 `ref.platform == gitee`。
2. 用 `settings.gitee_base_url` 组装 API base。
3. 拉取 PR metadata、files、commits。
4. 解析 title、author、source branch、target branch、state、html_url。
5. 从 files payload 解析 `ChangeRequestFile`，并由 patch 重建 unified diff。
6. 检查 `REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS`。
7. 返回 `FetchedChangeRequest`，metadata 只保留平台、api_source 和统计字段。

GitLab fetch 流程：

1. 校验 `ref.platform in {gitlab, self_hosted_gitlab}`。
2. 计算 API base：
   - GitLab.com 使用 `settings.gitlab_base_url`。
   - self-hosted GitLab 如果显式配置了非默认 `REPOLENS_GITLAB_BASE_URL`，使用配置值；否则由 `ref.base_url + /api/v4` 派生。
3. 将 `{owner}/{repo}` URL encode 成 GitLab `project_id`。
4. 拉取 MR metadata、diffs、commits。
5. 从 diff entries 解析文件状态、patch、additions/deletions，并重建 unified diff。
6. 检查 diff limit，返回统一 `FetchedChangeRequest`。

### 4.2 Diff 重建

Gitee 和 GitLab 不依赖平台原始 `.diff` 下载能力。统一用文件级 patch 重建：

```text
diff --git a/{old_path} b/{new_path}
--- a/{old_path}
+++ b/{new_path}
{patch}
```

如果平台 files/diffs payload 没有任何 patch，provider 返回 `ChangeRequestFetchError`，避免生成空 diff 进入 Review pipeline。

### 4.3 错误和安全

- 401/403 映射为 `ChangeRequestAuthError`。
- 403 且 rate limit header 显示耗尽时映射为 `ChangeRequestRateLimitError`。
- 404 映射为 `ChangeRequestNotFoundError`。
- diff 超限映射为 `ChangeRequestDiffTooLargeError`。
- 其他非 2xx 映射为 `ChangeRequestFetchError`。
- token 不进入 `FetchedChangeRequest.metadata`，也不进入 `change_requests.metadata`。

## 5. 测试策略

| 测试文件 | 覆盖 |
| --- | --- |
| `test_phase6_ext_providers.py` | Gitee/GitLab/self-hosted GitLab fetch、headers/query token、diff 重建、diff limit、错误映射 |
| `test_phase6_change_request_api.py` | Gitee/GitLab provider 通过 PR/MR Review API 生成 completed Review task 并持久化 metadata |
| `test_phase6_change_request_parser.py` | 保持多平台 URL parser 兼容 |
| `test_phase6_demo_change_requests.py` | 保持 GitHub synthetic fixture smoke 兼容 |

## 6. 验收标准

- Gitee PR URL 不再返回 provider not implemented，可以通过 fake transport fetch metadata/files/commits/diff 并进入 Review pipeline。
- GitLab.com MR URL 不再返回 provider not implemented，可以通过 fake transport fetch metadata/diffs/commits 并进入 Review pipeline。
- self-hosted GitLab MR URL 使用派生或配置的 API base 完成 fetch。
- 多平台 token 不出现在持久化 metadata、API response、tool calls、traces 或文档示例输出中。
- `ruff check app`、`pytest app\tests`、`npm run build`、`npm exec tsc -- --noEmit`、`docker compose config` 通过。

