# RepoLens-Java V1.1 真实 PR/MR 案例清单

## 1. 用途

本文件用于面试前 live smoke 准备。默认 demo 仍使用离线 fixture；真实平台案例用于网络可用、平台 API 未限流时展示可信度。

## 2. URL 类型

| 平台 | URL 格式 | Provider |
| --- | --- | --- |
| GitHub | `https://github.com/{owner}/{repo}/pull/{number}` | `GitHubChangeRequestProvider` |
| GitLab | `https://gitlab.com/{group}/{project}/-/merge_requests/{iid}` | `GitLabChangeRequestProvider` |
| Gitee | `https://gitee.com/{owner}/{repo}/pulls/{number}` | `GiteeChangeRequestProvider` |

## 3. Live Smoke 原则

- 优先选择公开仓库、小型 PR/MR、变更文件数少于 20。
- 先导入并索引目标仓库的对应本地代码版本。
- token 只通过环境变量设置。
- 不在截图中展示 token、Authorization header 或平台后台页面。
- live smoke 失败时回退到 `fixture://github/repolens-java/1`。

## 4. 可讲边界

V1.1 已实现：

- URL parser。
- GitHub/GitLab/Gitee 只读 provider。
- metadata/diff/commit/files 拉取。
- token 脱敏。
- diff hash 和 metadata 持久化。
- 复用 V1 ReviewService 生成 evidence-grounded review。

V1.1 不做：

- PR 评论写回。
- approve/request changes。
- merge/close/reopen。
- OAuth 登录。
- webhook 同步。
