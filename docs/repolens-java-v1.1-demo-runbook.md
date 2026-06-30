# RepoLens-Java V1.1 Demo Runbook

## 1. 目标

V1.1 demo 展示真实 PR/MR URL Review 能力。默认路径使用离线 fixture，不依赖网络和平台 token；live smoke 可选使用 GitHub/GitLab/Gitee 公开 PR/MR。

## 2. 启动

后端：

```powershell
cd F:\Desktop\agent\RepoLens\backend-java
& ..\scripts\use-java.ps1 21
mvn spring-boot:run
```

前端：

```powershell
cd F:\Desktop\agent\RepoLens\frontend
npm run dev
```

## 3. 默认离线演示路径

1. 导入一个包含 `src/main/java/com/demo/SecurityConfig.java` 的本地 Java demo 仓库。
2. 等待 repository 状态为 `ready`。
3. 打开 Review tab。
4. 切换到 `PR/MR URL`。
5. 输入：

```text
fixture://github/repolens-java/1
```

6. 点击 `Review URL`。
7. 验证页面显示：
   - `fixture-github / pull_request`
   - title、branch、changed files、commit count
   - Review summary
   - risks
   - citations
   - tool calls
   - traces

## 4. API Smoke

```http
POST /api/repositories/{repositoryId}/change-requests/reviews
```

```json
{
  "url": "fixture://github/repolens-java/1",
  "top_k": 5,
  "use_bm25": true,
  "use_vector": true,
  "use_graph": true,
  "run_static_check": false
}
```

查询 metadata：

```http
GET /api/change-requests/{changeRequestId}
GET /api/change-requests/tasks/{taskId}
```

## 5. 可选 Live Smoke

GitHub:

```text
https://github.com/{owner}/{repo}/pull/{number}
```

GitLab:

```text
https://gitlab.com/{group}/{project}/-/merge_requests/{iid}
```

Gitee:

```text
https://gitee.com/{owner}/{repo}/pulls/{number}
```

可选 token 环境变量：

```powershell
$env:REPOLENS_GITHUB_TOKEN="..."
$env:REPOLENS_GITLAB_TOKEN="..."
$env:REPOLENS_GITEE_TOKEN="..."
```

token 不入库、不返回前端、不写 review markdown。

## 6. 验证命令

```powershell
cd F:\Desktop\agent\RepoLens\backend-java
& ..\scripts\use-java.ps1 21
mvn test
```

```powershell
cd F:\Desktop\agent\RepoLens\frontend
npm run build
```
