# RepoLens Phase 6 开发审核测试评测闭环记录

## 1. 文档用途

本文档用于记录 V1 Phase 6 的开发、审核、测试和评测闭环。记录粒度与 `docs/v1-development-plan.md` 和 `docs/phase6-detailed-design.md` 中 P6-001 到 P6-012 对齐，确保每个任务都有开发、审核、测试和评测记录。

## 2. 当前状态

- 当前阶段：V1 Phase 6 - 多代码平台 PR/MR 集成与真实项目演示增强
- 当前状态：已完成 P6-DESIGN、P6-CLOSED-LOOP、P6-001 至 P6-012，Phase 6 已收束
- 开始日期：2026-06-13
- 收束日期：2026-06-14
- 依据文档：`docs/phase6-detailed-design.md`
- 自动化：`repolens-phase-6` heartbeat，每 10 分钟继续推进当前线程

## 3. 任务闭环记录

| 编号 | 任务 | 开发状态 | 审核状态 | 测试状态 | 评测/指标状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| P6-DESIGN | Phase 6 详细设计 | 完成 | 通过 | 文档审查通过 | 完成 | 新增 Phase 6 详细设计，明确多平台 Change Request Provider、GitHub 首个适配器、Gitee/GitLab 预留、API、数据模型、安全、测试和验收 |
| P6-CLOSED-LOOP | Phase 6 闭环记录 | 完成 | 通过 | 文档审查通过 | 完成 | 新增本文件，按 P6-001 到 P6-012 建立开发、审核、测试和评测记录表 |
| P6-001 | 编写 Phase 6 详细设计 | 完成 | 通过 | 文档审查通过 | 完成 | 本阶段只做详细设计，不进入代码实现 |
| P6-002 | 新增多平台配置项 | 完成 | 通过 | 通过 | 完成 | 新增 `REPOLENS_CHANGE_REQUEST_*`、GitHub/Gitee/GitLab token 和 base URL 配置；不提前实现 parser/client |
| P6-003 | 实现 PR/MR URL parser | 完成 | 通过 | 通过 | 完成 | 新增 Change Request 模型、provider registry 和 GitHub/Gitee/GitLab/self-hosted GitLab URL parser；不调用平台 API |
| P6-004 | 实现首个 Change Request client | 完成 | 通过 | 通过 | 完成 | 实现 GitHub PR 只读 client，读取 metadata、files、diff、commits；Gitee/GitLab fetch 仍保持 not implemented |
| P6-005 | 新增 change_requests 数据模型 | 完成 | 通过 | 通过 | 完成 | 新增 `change_requests` 表、Repository/Task 关系和模型测试；metadata 使用脱敏 JSON 字符串，不保存 token |
| P6-006 | 新增 PR/MR Review API | 完成 | 通过 | 通过 | 完成 | 新增 `POST /api/repositories/{repository_id}/change-requests/reviews`、GET by id、GET by task 和 response schema |
| P6-007 | 接入现有 Review pipeline | 完成 | 通过 | 通过 | 完成 | `ChangeRequestReviewService` fetch PR/MR 后构造 `ReviewCreateRequest` 并调用现有 `ReviewService`，不复制 Phase 4 pipeline |
| P6-008 | 前端新增 PR/MR Review flow | 完成 | 通过 | 通过 | 部分完成 | Workbench Review 面板新增 `Diff`/`PR/MR URL` 模式、平台无关 URL 输入、metadata 展示和报告复用；浏览器冒烟受当前会话后台 dev server 保持限制未完成 |
| P6-009 | 错误处理与安全边界 | 完成 | 通过 | 通过 | 完成 | service 层补充 diff limit guard，API 错误 detail 脱敏，前端错误数组/敏感文本归一化；覆盖 auth、rate limit、diff too large、fetch failure |
| P6-010 | 准备真实演示 PR/MR | 完成 | 通过 | 通过 | 完成 | 新增 `evals/change_requests/phase6_demo_prs.json` 离线 synthetic GitHub PR fixture，绑定 `ts_webapp` demo repo，并包含 unsupported provider 失败 URL |
| P6-011 | 测试与评测 | 完成 | 通过 | 通过 | 完成 | 新增 P6-011 smoke 评测断言和 `docs/phase6-smoke-evaluation.md`；全量 ruff/pytest、前端 build/type check、Docker config 和 UI DOM smoke 通过，截图命令受当前 Browser CDP 超时阻断 |
| P6-012 | 更新文档和演示材料 | 完成 | 通过 | 通过 | 完成 | README、evals 文档、worklog、闭环记录和最终验收完成；截图命令仍受 Browser CDP 超时阻断，已如实记录 |

## 4. 审核记录

| 日期 | 范围 | 结论 | 问题 | 处理 |
| --- | --- | --- | --- | --- |
| 2026-06-13 | Phase 6 详细设计 | 通过 | Phase 6 容易退化为 GitHub-only 或扩成全平台一次性实现 | 设计明确采用平台无关 Change Request Provider；GitHub 是首个落地适配器，Gitee/GitLab/self-hosted GitLab 预留契约 |
| 2026-06-13 | Phase 6 范围边界 | 通过 | PR/MR URL 审查可能引入自动 clone、自动写评论、自动 approve 或 push 风险 | 设计限定为只读平台 API，要求用户选择已索引 repository，不写回平台，不修改代码 |
| 2026-06-13 | Phase 6 闭环记录 | 通过 | 需要保持 P6-001 到 P6-012 每项都有开发、审核、测试、评测记录 | 本文件已建立任务、审核、测试和评测表，后续每项按编号更新 |
| 2026-06-13 | P6-002 多平台配置项 | 通过 | 配置项不能引入平台 API 行为，也不能让 `config.py` 与 tools 模块形成循环依赖 | 仅扩展 `Settings` 和 `.env.example`；diff 默认值用本地常量保持与 Phase 4 `DIFF_MAX_CHARS` 对齐，不导入 tools |
| 2026-06-13 | P6-003 PR/MR URL parser | 通过 | P6-003 只能实现纯解析和 provider registry，不能提前发起网络请求、写数据库或接 Review API | 新增 `services/change_request` 模块，只包含 dataclass、provider detect/parse 和错误类型；平台 API client 留给 P6-004 |
| 2026-06-13 | P6-004 GitHub provider client | 通过 | P6-004 只能实现首个 GitHub 只读 client，不应接 API、写数据库、写回平台或实现 Gitee/GitLab client | 新增可注入 HTTP transport 的 GitHub fetch；测试全部使用 fake transport，无真实网络；Gitee/GitLab 继续返回 not implemented |
| 2026-06-13 | P6-005 change_requests 数据模型 | 通过 | 新增模型不能修改既有表字段，且 SQLAlchemy `metadata` 是保留属性，不能直接作为 ORM 属性名 | 仅新增 `change_requests` 表；数据库列名保留 `metadata`，ORM 属性使用 `metadata_payload`；关联 Repository/Task，不保存 token |
| 2026-06-13 | P6-006 PR/MR Review API | 通过 | API 文案和 schema 不能 GitHub-only，错误映射必须脱敏且不能写回平台 | 新增平台无关 `change-requests` API 和 schema；只读 fetch，unsupported/not implemented/auth/not found/rate limit/diff too large 均映射为明确 HTTP 错误 |
| 2026-06-13 | P6-007 Review pipeline 接入 | 通过 | 新服务不能复制 Phase 4 Review pipeline，也不能绕过 tool_calls/traces | `ChangeRequestReviewService` 只负责 provider fetch、metadata 入库和构造 `ReviewCreateRequest`；实际审查仍由 `ReviewService.create_review_task/run_review_task/build_task_response` 完成 |
| 2026-06-13 | P6-008 前端 PR/MR Review flow | 通过 | 前端不能写成 GitHub-only，也不能替换已有粘贴 diff Review flow | Review 面板保留 `Diff` 模式，新增 `PR/MR URL` 模式；按钮和 metadata 使用 PR/MR/Platform/Source branch/Target branch 等平台无关文案 |
| 2026-06-13 | P6-009 错误处理与安全边界 | 通过 | Provider 可能返回超限 diff 或带 token 的异常文本，不能依赖单个 provider 自律 | service 层统一执行 diff limit guard；API detail 统一按 Settings token 与 Bearer/Authorization 模式脱敏；失败 fetch 不创建 `change_requests` 或 review task |
| 2026-06-13 | P6-010 演示 PR/MR fixture | 通过 | 当前环境不应依赖外网 public PR，也不能触发任何平台写回 | 新增 synthetic GitHub-style PR fixture 和 README；URL/metadata/diff 可离线演示，unsupported provider URL 可演示失败态；测试确认可走 PR/MR Review API |
| 2026-06-13 | P6-011 测试与评测 | 通过 | smoke 指标必须可复现，不能只写手工结论；UI 截图失败也不能伪装为通过 | 新增自动化 smoke 断言，覆盖 URL parse、provider fetch、review completion、citations、latency 和 token safety；UI DOM smoke 通过，截图通道超时作为环境阻断记录 |
| 2026-06-14 | P6-012 文档和演示材料收束 | 通过 | README 不能夸大为完整多平台 live fetch，也不能把截图阻断写成已完成截图 | README 明确 GitHub 是首个只读 fetch 适配器，Gitee/GitLab/self-hosted GitLab 是 parser/provider contract；截图阻断写入 smoke、README、闭环和最终验收 |

## 5. 测试记录

| 日期 | 范围 | 命令/方式 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| 2026-06-13 | P6-DESIGN | 文档审查 | 通过 | 尚未进入代码实现 |
| 2026-06-13 | P6-CLOSED-LOOP | 文档审查 | 通过 | 建立闭环记录表 |
| 2026-06-13 | P6-002 配置项专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\tests\\test_phase6_config.py` | 通过 | All checks passed |
| 2026-06-13 | P6-002 配置项专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py` | 通过 | 2 passed |
| 2026-06-13 | P6-003 parser 专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\change_request app\\tests\\test_phase6_change_request_parser.py` | 通过 | All checks passed |
| 2026-06-13 | P6-003 parser 专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_change_request_parser.py` | 通过 | 12 passed |
| 2026-06-13 | P6-002/P6-003 合并专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\services\\change_request app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py` | 通过 | All checks passed |
| 2026-06-13 | P6-002/P6-003 合并专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py` | 通过 | 14 passed |
| 2026-06-13 | P6-004 GitHub provider 专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\change_request app\\tests\\test_phase6_github_provider.py` | 通过 | All checks passed |
| 2026-06-13 | P6-004 GitHub provider 专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_github_provider.py` | 通过 | 5 passed |
| 2026-06-13 | P6-002/P6-004 合并专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\services\\change_request app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py` | 通过 | All checks passed |
| 2026-06-13 | P6-002/P6-004 合并专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py` | 通过 | 19 passed |
| 2026-06-13 | P6-005 模型专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\models\\change_request.py app\\models\\repository.py app\\models\\task.py app\\models\\__init__.py app\\tests\\test_phase6_change_request_models.py` | 通过 | All checks passed |
| 2026-06-13 | P6-005 模型专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_change_request_models.py` | 通过 | 3 passed |
| 2026-06-13 | P6-005/P6-007 API 专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\api\\change_requests.py app\\schemas\\change_request.py app\\services\\change_request app\\models\\change_request.py app\\models\\repository.py app\\models\\task.py app\\models\\__init__.py app\\main.py app\\tests\\test_phase6_change_request_api.py app\\tests\\test_phase6_change_request_models.py` | 通过 | All checks passed |
| 2026-06-13 | P6-005/P6-007 API 专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py` | 通过 | 6 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-13 | P6-002/P6-007 合并专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\api\\change_requests.py app\\schemas\\change_request.py app\\services\\change_request app\\models\\change_request.py app\\models\\repository.py app\\models\\task.py app\\models\\__init__.py app\\main.py app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py` | 通过 | All checks passed |
| 2026-06-13 | P6-002/P6-007 合并专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py` | 通过 | 25 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-13 | P6-008 前端类型检查 | `npm exec tsc -- --noEmit` | 通过 | 第一次在 `.next/types` 生成前失败；执行 `npm run build` 后复跑通过 |
| 2026-06-13 | P6-008 前端构建 | `npm run build` | 通过 | Next.js production build 通过 |
| 2026-06-13 | P6-008 浏览器冒烟 | in-app Browser 打开 `http://127.0.0.1:3000` | 阻断 | `next dev` 前台可 Ready，但当前工具会话中后台 dev server 不能稳定保持监听 3000；已记录为环境验证阻断，后续 P6-011 再补截图/浏览器验证 |
| 2026-06-13 | P6-009 后端安全专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\api\\change_requests.py app\\services\\change_request\\service.py app\\tests\\test_phase6_change_request_api.py` | 通过 | All checks passed |
| 2026-06-13 | P6-009 后端安全专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_change_request_api.py` | 通过 | 6 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-13 | P6-009 前端构建 | `npm run build` | 通过 | Next.js production build 通过 |
| 2026-06-13 | P6-009 前端类型检查 | `npm exec tsc -- --noEmit` | 通过 | 与 build 并行时曾因 `.next/types` 生成竞态失败；build 完成后顺序复跑通过 |
| 2026-06-13 | P6-002/P6-009 合并专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\api\\change_requests.py app\\schemas\\change_request.py app\\services\\change_request app\\models\\change_request.py app\\models\\repository.py app\\models\\task.py app\\models\\__init__.py app\\main.py app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py` | 通过 | All checks passed |
| 2026-06-13 | P6-002/P6-009 合并专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py` | 通过 | 28 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-13 | P6-010 demo fixture 专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase6_demo_change_requests.py` | 通过 | All checks passed |
| 2026-06-13 | P6-010 demo fixture 专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_demo_change_requests.py` | 通过 | 5 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-13 | P6-002/P6-010 合并专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\core\\config.py app\\api\\change_requests.py app\\schemas\\change_request.py app\\services\\change_request app\\models\\change_request.py app\\models\\repository.py app\\models\\task.py app\\models\\__init__.py app\\main.py app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py app\\tests\\test_phase6_demo_change_requests.py` | 通过 | All checks passed |
| 2026-06-13 | P6-002/P6-010 合并专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_config.py app\\tests\\test_phase6_change_request_parser.py app\\tests\\test_phase6_github_provider.py app\\tests\\test_phase6_change_request_models.py app\\tests\\test_phase6_change_request_api.py app\\tests\\test_phase6_demo_change_requests.py` | 通过 | 33 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-13 | P6-010 前端构建 | `npm run build` | 通过 | Next.js production build 通过 |
| 2026-06-13 | P6-010 前端类型检查 | `npm exec tsc -- --noEmit` | 通过 | 与 build 并行时出现 `.next/types` 生成竞态；build 完成后顺序复跑通过 |
| 2026-06-13 | P6-011 demo smoke 专项 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase6_demo_change_requests.py` | 通过 | All checks passed；测试文件新增 citation/latency/safety smoke 断言 |
| 2026-06-13 | P6-011 demo smoke 专项 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase6_demo_change_requests.py` | 通过 | 6 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-13 | P6-011 后端全量 Ruff | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | All checks passed |
| 2026-06-13 | P6-011 后端全量测试 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 227 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-13 | P6-011 前端构建 | `npm run build` | 通过 | Next.js production build 通过；主页静态产物生成正常 |
| 2026-06-13 | P6-011 前端类型检查 | `npm exec tsc -- --noEmit` | 通过 | 顺序执行于 `npm run build` 之后，避免 `.next/types` 竞态；生成的 `frontend/tsconfig.tsbuildinfo` 已清理 |
| 2026-06-13 | P6-011 Docker 配置 | `docker compose config` | 通过 | compose 配置解析通过，backend service 已包含 Phase 6 Change Request env vars |
| 2026-06-13 | P6-011 UI DOM smoke | in-app Browser 打开 `http://127.0.0.1:3000` 并切换 `PR/MR URL` 模式 | 通过 | 持久本地 `npm run start -- -p 3000` 返回 HTTP 200；DOM 验证 URL 输入、`Run PR/MR Review` 按钮和未选 ready repository 时 disabled 状态 |
| 2026-06-13 | P6-011 UI screenshot | in-app Browser `Page.captureScreenshot` | 阻断 | full-page、viewport 和 clipped screenshot 均在当前 Browser CDP 层超时；未生成截图文件，P6-012 已将其作为环境阻断收束记录 |
| 2026-06-14 | P6-012 文档审查 | README、evals 文档、worklog、闭环记录、final closure review | 通过 | PR/MR 平台范围、API、环境变量、安全边界、demo fixture 和截图阻断均已写入收束材料 |
| 2026-06-14 | P6-012 后端全量 Ruff | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | All checks passed |
| 2026-06-14 | P6-012 后端全量测试 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 227 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-14 | P6-012 前端构建 | `npm run build` | 通过 | Next.js production build 通过 |
| 2026-06-14 | P6-012 前端类型检查 | `npm exec tsc -- --noEmit` | 通过 | 顺序执行于 `npm run build` 之后，避免 `.next/types` 竞态；生成的 `frontend/tsconfig.tsbuildinfo` 已清理 |
| 2026-06-14 | P6-012 Docker 配置 | `docker compose config` | 通过 | compose 配置解析通过，backend service 仍包含 Phase 6 Change Request env vars |

## 6. 评测指标记录

Phase 6 不建立大规模 benchmark，正式 benchmark 放入 Phase 9。本阶段只记录 PR/MR URL Review smoke 指标。

| 日期 | 范围 | 指标 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| 2026-06-13 | P6-DESIGN | 评测口径 | 已定义 | URL parse success、provider fetch success、review completion、citation coverage smoke、latency smoke、safety smoke |
| 2026-06-13 | P6-002 | 配置可用性 | 通过 | 多平台 token/base URL、timeout 和 diff limit 均可由 `Settings` 默认值或显式覆盖读取 |
| 2026-06-13 | P6-003 | URL parse success | 通过 | 覆盖 GitHub PR、Gitee PR、GitLab.com MR、self-hosted GitLab MR、invalid URL 和 unsupported provider |
| 2026-06-13 | P6-004 | provider fetch success | 通过 | fake GitHub transport 覆盖 metadata、files、commits、diff 拉取和 ChangeRequest 组装 |
| 2026-06-13 | P6-004 | provider safety smoke | 通过 | token 只用于 Authorization header，不写入 ChangeRequest metadata；覆盖 public request 无 token 分支 |
| 2026-06-13 | P6-005 | metadata persistence smoke | 通过 | `change_requests.metadata` 列可 round-trip 脱敏 JSON；测试确认不包含 `github_token` 或 `Authorization` |
| 2026-06-13 | P6-006 | API error smoke | 通过 | 覆盖 unsupported provider、invalid URL、Gitee provider not implemented、missing change request by id/task |
| 2026-06-13 | P6-007 | review completion smoke | 通过 | fake provider PR URL 通过 API 创建 completed Review task，并保留 `analyze_diff`、`code_search` tool_calls 和 traces |
| 2026-06-13 | P6-007 | response safety smoke | 通过 | API response 不包含 raw metadata，不包含 fake `secret-token`；数据库 metadata 入库前过滤 token/Authorization |
| 2026-06-13 | P6-008 | UI build smoke | 通过 | 前端新增 PR/MR URL flow 后 production build 和 TypeScript check 均通过；视觉/截图 smoke 留到 P6-011 补齐 |
| 2026-06-13 | P6-009 | diff limit smoke | 通过 | fake provider 绕过 provider 层限制返回超限 diff 时，service 层仍以 413 拒绝，且不创建 `change_requests`/`tasks` |
| 2026-06-13 | P6-009 | error safety smoke | 通过 | provider 异常包含 `Authorization: Bearer secret-token` 与 `github_token=secret-token` 时，API response 只返回 redacted 文本 |
| 2026-06-13 | P6-009 | error mapping smoke | 通过 | auth=400、rate limit=429、diff too large=413、fetch failure=502 均覆盖 |
| 2026-06-13 | P6-010 | demo PR fixture smoke | 通过 | `phase6-cr-001` GitHub-style PR URL 可解析，diff 引用 `ts_webapp` 真实文件，fixture 无 token/Authorization |
| 2026-06-13 | P6-010 | demo review completion smoke | 通过 | 使用 fixture provider 通过 PR/MR Review API 生成 completed Review task，并保留 `analyze_diff`、`code_search` tool_calls |
| 2026-06-13 | P6-010 | unsupported provider demo smoke | 通过 | fixture 包含 Bitbucket-style unsupported URL，可演示 unsupported provider 错误，不触发平台写回 |
| 2026-06-13 | P6-011 | URL parse success | 通过 | `phase6-cr-001` synthetic GitHub-style PR URL 通过平台无关 parser 解析 |
| 2026-06-13 | P6-011 | provider fetch success | 通过 | fixture provider 离线返回统一 `FetchedChangeRequest`，包含 metadata、files、commits 和 diff；不依赖外网 |
| 2026-06-13 | P6-011 | review completion | 通过 | PR/MR Review API 返回 completed Review task |
| 2026-06-13 | P6-011 | citation coverage smoke | 通过 | smoke test 插入已索引 `ReviewPanel` chunk，Review report 返回 `src/components/review-panel.tsx` citation |
| 2026-06-13 | P6-011 | latency smoke | 通过 | smoke test 记录本地 API 总耗时，并断言所有 tool_calls 返回非负 `latency_ms` |
| 2026-06-13 | P6-011 | safety smoke | 通过 | provider metadata 注入 fake `github_token` 和 `Authorization: Bearer secret-token` 后，API response 与持久化 metadata 均不泄露 |
| 2026-06-13 | P6-011 | UI flow smoke | 通过 | in-app Browser DOM 验证 `PR/MR URL` 模式可切换、URL 输入可见、未选 ready repository 时提交按钮 disabled |
| 2026-06-14 | P6-012 | documentation coverage | 通过 | README、evals 文档、worklog、闭环记录和 final closure review 均覆盖 Phase 6 多平台范围、GitHub 首个适配器、保留平台、API、配置、安全和 demo fixture |
| 2026-06-14 | P6-012 | final closure gate | 通过 | ruff、pytest、frontend build、frontend type check 和 Docker config 均通过；截图 artifact 因 Browser CDP 超时仍为环境阻断，不作为伪造完成项 |

P6-011 详细 smoke 评测记录见 `docs/phase6-smoke-evaluation.md`。

## 7. 风险与控制

| 风险 | 表现 | 控制方式 | 当前状态 |
| --- | --- | --- | --- |
| GitHub-only 锁死 | API、schema、前端都只写 GitHub | 统一 Change Request Provider 和 PR/MR 文案 | P6-003/P6-008 已覆盖 URL parser 多平台预留和前端平台无关文案 |
| 范围膨胀 | 同时完整实现 GitHub/Gitee/GitLab/self-hosted GitLab | Phase 6 先落地 GitHub client，其他平台保留 parser/contract/unsupported 错误 | P6-004 已完成 GitHub client；Gitee/GitLab fetch 仍为 not implemented |
| 安全泄露 | token 进入数据库、trace、前端 response 或截图 | token 只从环境变量读取，metadata 脱敏 | P6-011 已覆盖 provider metadata、数据库 metadata、API response、tool_calls/traces 相关 response 和前端错误文本脱敏；P6-012 未生成截图 artifact，避免把不可验证截图纳入交付 |
| Review pipeline 分叉 | 新 API 复制 Phase 4 审查逻辑 | ChangeRequestReviewService 必须调用现有 ReviewService | P6-007 API 测试确认 PR/MR URL flow 产生现有 Review task、tool_calls 和 traces |
| 大 diff 失控 | 外部 PR/MR diff 过大导致超时或 UI 崩溃 | `REPOLENS_CHANGE_REQUEST_MAX_DIFF_CHARS` 限制 | P6-004 provider 层和 P6-009 service/API 层均已覆盖 diff limit |
| 平台 API 不稳定 | rate limit、权限、网络错误影响演示 | mock provider 单元测试 + public PR smoke 可选 | P6-011 使用离线 synthetic PR fixture 完成 deterministic smoke；真实 public PR smoke 可在网络允许时作为补充，不作为 Phase 6 阻断 |

## 8. 待办队列

Phase 6 无剩余必做项。`docs/assets/screenshots/change-request-review-panel.png` 可在 Browser screenshot 通道恢复后补充，但不阻断 Phase 6 收束。

## 9. 最终验收结论

| 日期 | 结论 | 说明 |
| --- | --- | --- |
| 2026-06-14 | 通过 | P6-001 到 P6-012 均已完成；Phase 6 保持平台无关 Change Request Provider，GitHub 为首个只读落地适配器，Gitee/GitLab/self-hosted GitLab 保留 parser/provider contract；未实现任何 PR/MR 写回、approve/request changes、push 或自动修改代码能力 |
