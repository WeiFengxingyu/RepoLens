# RepoLens Phase 5 开发审核测试评测闭环记录

## 1. 文档用途

本文档用于记录 Phase 5 的开发、审核、测试和评测闭环。记录粒度与 `docs/p0-plus-development-plan.md` 中 P5-001 到 P5-012 对齐，确保每个任务都有开发、审核、测试和评测记录。

## 2. 当前状态

- 当前阶段：Phase 5 - 评测、部署与简历包装
- 当前状态：Phase 5 已完成，P5-DESIGN、P5-CLOSED-LOOP、P5-001 至 P5-012 均已闭环
- 开始日期：2026-06-08
- 依据文档：`docs/phase5-detailed-design.md`

## 3. 任务闭环记录

| 编号 | 任务 | 开发状态 | 审核状态 | 测试状态 | 评测/指标状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| P5-DESIGN | Phase 5 详细设计 | 完成 | 通过 | 文档审查通过 | 完成 | 新增 Phase 5 详细设计，覆盖评测数据格式、50 条样例、三种策略、指标、Evaluation Panel、Docker Compose、README、演示材料、安全和验收标准 |
| P5-CLOSED-LOOP | Phase 5 闭环记录 | 完成 | 通过 | 文档审查通过 | 完成 | 新增本文件，按 P5-001 到 P5-012 建立开发、审核、测试和评测记录表 |
| P5-001 | 设计评测数据格式 | 完成 | 通过 | 通过 | 完成 | 新增 dataset schema、loader 和校验；不提前创建 50 条样例 |
| P5-002 | 准备 50 条评测样例 | 完成 | 通过 | 通过 | 完成 | 新增 `evals/datasets/p0_plus_eval.jsonl`，包含 20 定位、10 解释、10 架构、10 Review |
| P5-003 | 实现 vector_only 评测 | 完成 | 通过 | 通过 | 完成 | 新增 vector_only sample runner；只启用 vector，显式记录 vector disabled，不做指标计算 |
| P5-004 | 实现 bm25_vector 评测 | 完成 | 通过 | 通过 | 完成 | 新增 bm25_vector sample runner；启用 BM25 + vector，关闭 graph，vector disabled 时保留 BM25 证据和降级原因 |
| P5-005 | 实现 bm25_vector_graph 评测 | 完成 | 通过 | 通过 | 完成 | 新增 bm25_vector_graph sample runner；启用 BM25 + vector + graph，记录 graph_count、Evidence refs 和 vector disabled 降级原因 |
| P5-006 | 实现指标计算 | 完成 | 通过 | 通过 | 完成 | 新增 metrics 模块，计算 Hit@5、MRR、引用覆盖率、延迟聚合和 token 估算/真实 token 标记 |
| P5-007 | 实现 Evaluation Panel | 完成 | 通过 | 通过 | 完成 | 新增同步 Evaluation API、evaluation_runs/evaluation_results 表和前端 Evaluation Panel，展示策略对比表与样例结果表 |
| P5-008 | 完善 Docker Compose | 完成 | 通过 | 通过 | 完成 | 完善 frontend、backend、qdrant、volume、环境变量和构建上下文；实际启动被 Docker daemon 环境阻断 |
| P5-009 | 完善 README | 完成 | 通过 | 通过 | 完成 | README 覆盖定位、架构、启动、截图目标、指标、简历写法和面试讲法；未伪造未产出的截图和分数 |
| P5-010 | 准备演示仓库 | 完成 | 通过 | 通过 | 完成 | 新增 Python service 和 TS webapp 两个小型 demo repo，文件数均在 20-60，覆盖数据集 expected files |
| P5-011 | 准备演示问题 | 完成 | 通过 | 通过 | 完成 | 新增 Markdown 演示脚本和 JSON 演示问题集，覆盖架构、定位、解释、影响范围、Review |
| P5-012 | 录制或整理演示截图 | 完成 | 通过 | 通过 | 完成 | 新增 `docs/assets/screenshots/*.png`，覆盖 Repository、Evaluation、Ask/Trace、Review、Tool Calls 和 Evidence；README 写入真实 demo 指标 |

## 4. 审核记录

| 日期 | 范围 | 结论 | 问题 | 处理 |
| --- | --- | --- | --- | --- |
| 2026-06-08 | Phase 5 详细设计 | 通过 | Phase 5 容易扩展到完整 MCP Server、真实命令执行、复杂 Agent 协商或大规模 benchmark | 设计明确限定在 P0+ 评测、部署复现和简历包装，不新增完整 MCP Server、真实命令执行或复杂自治 Multi-Agent |
| 2026-06-08 | Phase 5 闭环记录 | 通过 | 需要确保 P5-001 到 P5-012 每项后续都有开发、审核、测试、评测记录 | 本文件已建立任务、审核、测试和评测表，后续每项按编号更新 |
| 2026-06-08 | P5-001 评测数据格式 | 通过 | P5-001 不能提前进入 P5-002 的 50 条样例或 P5-003 Runner；路径校验要兼容 Windows/POSIX | 仅实现 `EvaluationSample`、`EvaluationDataset`、JSONL loader 和 schema 校验；显式拒绝绝对路径、drive 前缀和路径穿越 |
| 2026-06-08 | P5-002 50 条评测样例 | 通过 | P5-002 只能准备数据，不应提前实现 Runner、指标计算或 API；样例不能包含真实密钥或外部专有代码 | 新增固定 JSONL 数据集，覆盖 `python_demo` 和 `ts_demo`，包含 20 location、10 explanation、10 architecture、10 review；Review 样例均为合法 unified diff |
| 2026-06-08 | P5-003 vector_only 评测 | 通过 | P5-003 不能提前实现 bm25_vector、bm25_vector_graph、Hit@5/MRR 或 Evaluation API；无 embedding 配置不能用 BM25 fallback 冒充 vector_only | 新增 `run_vector_only_sample`，固定 `use_bm25=false`、`use_vector=true`、`use_graph=false`，并把 `vector_disabled_reason` 写入结果 |
| 2026-06-08 | P5-004 bm25_vector 评测 | 通过 | P5-004 不能提前实现 bm25_vector_graph、Hit@5/MRR 或 Evaluation API；vector disabled 时不能让整个样例失败 | 新增 `run_bm25_vector_sample`，固定 `use_bm25=true`、`use_vector=true`、`use_graph=false`，保留 `bm25_count`、`vector_count`、Evidence refs 和 `vector_disabled_reason` |
| 2026-06-08 | P5-005 bm25_vector_graph 评测 | 通过 | P5-005 不能提前实现 Hit@5/MRR、Evaluation API 或 Evaluation Panel；必须确认 graph 扩展真实打开 | 新增 `run_bm25_vector_graph_sample`，固定 `use_bm25=true`、`use_vector=true`、`use_graph=true`，保留 `graph_count`、Evidence refs 和 `vector_disabled_reason` |
| 2026-06-08 | P5-006 指标计算 | 通过 | P5-006 不能提前实现 Evaluation API、Evaluation Panel 或正式 50 条策略运行；指标口径必须与详细设计一致 | 新增 `metrics.py`，实现单样例 Hit@5/MRR/citation_coverage/token/latency 指标和策略聚合指标 |
| 2026-06-08 | P5-007 Evaluation Panel | 通过 | P5-007 不能提前实现 Docker Compose、README、演示仓库或截图；同步 Runner 不应引入队列或后台调度 | 新增 Evaluation API、轻量持久化和前端 Panel；保持同步执行、单样例失败不阻断 run |
| 2026-06-08 | P5-008 Docker Compose | 通过 | P5-008 不能提前完善 README、演示仓库、演示问题或截图；Compose 不能挂载用户整盘或启用真实命令执行 | 完善 `docker-compose.yml`、`.env.example`、Dockerfile 和 `.dockerignore`；三服务与 volume 符合 P0+，实际启动失败原因已记录为 Docker daemon 未运行 |
| 2026-06-08 | P5-009 README | 通过 | P5-009 不能提前创建演示仓库、演示问题、截图或伪造真实评测分数；README 必须与已完成能力和 pending 项一致 | README 已覆盖定位、架构、启动、环境变量、API、评测、截图目标、安全边界、non-goals、简历 bullet 和面试讲法；P5-010/P5-011/P5-012 产物标记为 pending |
| 2026-06-08 | P5-010 演示仓库 | 通过 | P5-010 不能提前创建演示问题、截图或伪造评测结果；demo repo 不能包含真实密钥或脱离 50 条数据集路径 | 新增 `evals/demo_repos/python_service` 和 `evals/demo_repos/ts_webapp`，分别 22/21 个文件，覆盖数据集 expected files；P5-011/P5-012 保持 pending |
| 2026-06-08 | P5-011 演示问题 | 通过 | P5-011 不能提前录制截图、填写真正评测分数或扩展超出 P0+ 的演示流程；问题必须引用已存在 demo repo 文件 | 新增 `evals/demo_questions.md` 和 `evals/datasets/demo_questions.json`，10 条问题覆盖 architecture/location/explanation/impact/review，P5-012 保持 pending |
| 2026-06-08 | P5-012 演示截图 | 通过 | 截图必须来自真实本地 Workbench 状态；README 不得继续保留 pending 分数或伪造未跑过的指标；前端不能因长表格撑出横向滚动影响截图 | 已本地导入 demo repos，运行 Evaluation/Ask/Review/Evidence；保存 6 张截图；修正 Phase 5 标识、演示默认输入和长内容溢出；README 使用本次 demo run 指标 |

## 5. 测试记录

| 日期 | 范围 | 命令/方式 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| 2026-06-08 | Phase 5 详细设计 | 文档审查 | 通过 | 尚未进入 P5 代码开发 |
| 2026-06-08 | Phase 5 闭环记录 | 文档审查 | 通过 | 建立 P5-001 到 P5-012 的闭环记录表 |
| 2026-06-08 | P5-001 评测数据格式 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation app\\tests\\test_phase5_dataset.py` | 通过 | Ruff 无问题 |
| 2026-06-08 | P5-001 评测数据格式 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_dataset.py` | 通过 | 14 passed |
| 2026-06-08 | P5-001 评测数据格式 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-001 评测数据格式 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 155 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-002 50 条评测样例 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase5_dataset_fixture.py` | 通过 | Ruff 无问题 |
| 2026-06-08 | P5-002 50 条评测样例 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_dataset.py app\\tests\\test_phase5_dataset_fixture.py` | 通过 | 18 passed |
| 2026-06-08 | P5-002 50 条评测样例 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-002 50 条评测样例 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 159 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-003 vector_only 评测 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation app\\tests\\test_phase5_vector_only_runner.py` | 通过 | Ruff 无问题 |
| 2026-06-08 | P5-003 vector_only 评测 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_vector_only_runner.py` | 通过 | 4 passed |
| 2026-06-08 | P5-003 vector_only 评测 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-003 vector_only 评测 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 163 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-004 bm25_vector 评测 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation app\\tests\\test_phase5_bm25_vector_runner.py` | 通过 | Ruff 无问题 |
| 2026-06-08 | P5-004 bm25_vector 评测 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_bm25_vector_runner.py` | 通过 | 4 passed |
| 2026-06-08 | P5-004 bm25_vector 评测 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-004 bm25_vector 评测 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 167 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-005 bm25_vector_graph 评测 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation app\\tests\\test_phase5_bm25_vector_graph_runner.py` | 通过 | Ruff 无问题 |
| 2026-06-08 | P5-005 bm25_vector_graph 评测 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_bm25_vector_graph_runner.py` | 通过 | 4 passed |
| 2026-06-08 | P5-005 bm25_vector_graph 评测 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-005 bm25_vector_graph 评测 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 171 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-006 指标计算 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation app\\tests\\test_phase5_metrics.py` | 通过 | Ruff 无问题 |
| 2026-06-08 | P5-006 指标计算 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_metrics.py` | 通过 | 8 passed |
| 2026-06-08 | P5-006 指标计算 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-006 指标计算 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 179 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-007 Evaluation API/Panel | `.\\.venv\\Scripts\\python.exe -m ruff check app\\api\\evaluations.py app\\models\\evaluation.py app\\schemas\\evaluation.py app\\services\\evaluation app\\tests\\test_phase5_evaluation_api.py` | 通过 | Ruff 无问题 |
| 2026-06-08 | P5-007 Evaluation API/Panel | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_evaluation_api.py` | 通过 | 5 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-007 Evaluation API/Panel | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-007 Evaluation API/Panel | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 184 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-007 Evaluation API/Panel | `npm run build` | 通过 | Next.js build、lint 和类型检查通过 |
| 2026-06-08 | P5-008 Docker Compose | `docker compose config` | 通过 | 配置解析包含 backend、frontend、qdrant、`repolens_data` 和 `qdrant_data` |
| 2026-06-08 | P5-008 Docker Compose | `docker compose up -d --build` | 未通过（环境阻断） | Docker Desktop Linux daemon 未运行，无法连接 `dockerDesktopLinuxEngine` pipe；未完成实际容器启动 |
| 2026-06-08 | P5-008 Docker Compose | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-008 Docker Compose | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 184 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-008 Docker Compose | `npm run build` | 通过 | Next.js build、lint 和类型检查通过 |
| 2026-06-08 | P5-009 README | `rg -n "Current phase:\|Phase 0 Scope\|pending\|P5-010\|P5-011\|P5-012\|docker compose up\|Hit@5\|Resume Bullets\|Interview Talk Track" README.md` | 通过 | 确认 README 移除 Phase 0 旧说明，保留 pending 标记、评测指标、启动命令、简历与面试内容 |
| 2026-06-08 | P5-009 README | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-009 README | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 184 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-009 README | `npm run build` | 通过 | Next.js build、lint 和类型检查通过 |
| 2026-06-08 | P5-009 README | `docker compose config` | 通过 | README 启动说明引用的 compose 配置仍可解析 |
| 2026-06-08 | P5-010 演示仓库 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase5_demo_repos.py` | 通过 | 新增 demo repo 测试 Ruff 无问题 |
| 2026-06-08 | P5-010 演示仓库 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_demo_repos.py app\\tests\\test_phase5_dataset_fixture.py` | 通过 | 8 passed；验证 demo repo 覆盖数据集 expected files |
| 2026-06-08 | P5-010 演示仓库 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-010 演示仓库 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 188 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-010 演示仓库 | `npm run build` | 通过 | Next.js build、lint 和类型检查通过 |
| 2026-06-08 | P5-010 演示仓库 | `docker compose config` | 通过 | Compose 配置仍可解析 |
| 2026-06-08 | P5-011 演示问题 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\tests\\test_phase5_demo_questions.py` | 通过 | 新增 demo questions 测试 Ruff 无问题 |
| 2026-06-08 | P5-011 演示问题 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_demo_questions.py app\\tests\\test_phase5_demo_repos.py` | 通过 | 8 passed；验证问题字段、文件引用、diff 和 Markdown/JSON 对齐 |
| 2026-06-08 | P5-011 演示问题 | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-011 演示问题 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 192 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-011 演示问题 | `npm run build` | 通过 | Next.js build、lint 和类型检查通过 |
| 2026-06-08 | P5-011 演示问题 | `docker compose config` | 通过 | Compose 配置仍可解析 |
| 2026-06-08 | P5-012 演示截图专项 | 浏览器截图与人工视觉抽查 | 通过 | `repository-status.png`、`evaluation-panel.png`、`ask-trace-panel.png`、`review-panel.png`、`tool-calls-panel.png`、`evidence-panel.png` 均可打开且内容正确 |
| 2026-06-08 | P5-012 Evaluation demo | Workbench `all` strategy run | 通过 | 50 samples x 3 strategies；vector_only 0% Hit@5，bm25_vector 92% Hit@5，bm25_vector_graph 90% Hit@5 |
| 2026-06-08 | P5-012 演示路径修复 | `.\\.venv\\Scripts\\python.exe -m ruff check app\\services\\evaluation\\service.py app\\tests\\test_phase5_evaluation_api.py` | 通过 | dataset path 支持从 repo root 解析，专项 Ruff 无问题 |
| 2026-06-08 | P5-012 演示路径修复 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests\\test_phase5_evaluation_api.py` | 通过 | 6 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-012 最终后端 Ruff | `.\\.venv\\Scripts\\python.exe -m ruff check app` | 通过 | 全量 Ruff 无问题 |
| 2026-06-08 | P5-012 最终后端测试 | `.\\.venv\\Scripts\\python.exe -m pytest app\\tests` | 通过 | 193 passed，1 个 Starlette/httpx deprecation warning |
| 2026-06-08 | P5-012 最终前端构建 | `npm run build` | 通过 | Next.js build、lint 和类型检查通过 |
| 2026-06-08 | P5-012 最终 Compose 校验 | `docker compose config` | 通过 | 配置解析包含 backend、frontend、qdrant、named volumes 和环境变量 |

## 6. 评测指标记录

Phase 5 的核心产出是正式评测指标表。本节先定义记录格式，后续 P5-003 到 P5-006 完成后填入真实结果。

| 日期 | 策略 | sample_count | Hit@5 | MRR | citation_coverage | avg_latency_ms | p95_latency_ms | avg_token_count | error_count | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-08 | vector_only runner smoke | 1 | - | - | - | 记录 | - | - | 0 | P5-003 仅记录 vector_count、evidence_count、latency 和 vector_disabled_reason；Hit@5/MRR 留给 P5-006 |
| 2026-06-08 | bm25_vector runner smoke | 1 | - | - | - | 记录 | - | - | 0 | P5-004 仅记录 bm25_count、vector_count、evidence_count、latency 和 vector_disabled_reason；Hit@5/MRR 留给 P5-006 |
| 2026-06-08 | bm25_vector_graph runner smoke | 1 | - | - | - | 记录 | - | - | 0 | P5-005 仅记录 bm25_count、vector_count、graph_count、evidence_count、latency 和 vector_disabled_reason；Hit@5/MRR 留给 P5-006 |
| 2026-06-08 | metrics unit smoke | 3 | 0.3333 | 0.5 | 0.5 | 433.3333 | 900 | 30.0 | 1 | P5-006 使用单元样例验证 Hit@5、MRR、引用覆盖率、p50/p95 latency、token 估算和 error_count；正式策略对比留给后续 Evaluation run |
| 2026-06-08 | evaluation api/panel smoke | 2 x 3 strategies | 1.0 | 1.0 | 1.0 | 记录 | 记录 | 估算 | 0 | P5-007 使用 monkeypatched runner 验证 API、持久化、策略对比和前端 build；真实 50 条演示评测留给 P5-010/P5-011 后运行 |
| 2026-06-08 | dataset schema smoke | 2 | - | - | - | - | - | - | 0 | P5-001 loader 可读取 location/review 样例，count_by_type 和 to_dict 通过；正式 50 条样例留给 P5-002 |
| 2026-06-08 | p0_plus_eval fixture | 50 | - | - | - | - | - | - | 0 | 20 location、10 explanation、10 architecture、10 review；覆盖 `python_demo` 和 `ts_demo`；10 条 Review diff 均通过 loader 校验 |
| 2026-06-08 | docker compose config smoke | - | - | - | - | - | - | - | 0 | P5-008 配置校验通过；实际 `up --build` 因 Docker daemon 未运行而未完成，不计入检索质量指标 |
| 2026-06-08 | README packaging smoke | - | - | - | - | - | - | - | 0 | P5-009 README 覆盖评测方法、pending 指标表、截图目标、安全边界、简历 bullet 和面试讲法；未产生正式检索质量分数 |
| 2026-06-08 | demo repo coverage smoke | 2 repos | - | - | - | - | - | - | 0 | P5-010 Python demo 22 文件、TS demo 21 文件；50 条评测样例 expected files 均可在对应 repo 中找到 |
| 2026-06-08 | demo questions smoke | 10 questions | - | - | - | - | - | - | 0 | P5-011 覆盖 architecture/location/explanation/impact/review；4 条 impact/review 问题带 unified diff；不产生正式检索质量分数 |
| 2026-06-08 | P5-012 demo run vector_only | 50 | 0% | 0.000 | 0% | 0.2 | 1 | 14.9 est | 0 | 默认本地环境未配置 embedding provider，vector_only 预期无命中，warnings 已在 UI 展示 |
| 2026-06-08 | P5-012 demo run bm25_vector | 50 | 92% | 0.787 | 85.2% | 4.6 | 7 | 66.4 est | 0 | Workbench `all` strategy run，结果写入 README score table |
| 2026-06-08 | P5-012 demo run bm25_vector_graph | 50 | 90% | 0.892 | 84.5% | 9.6 | 20 | 64.8 est | 0 | Workbench `all` strategy run，BM25 seed + graph expansion 可用 |

## 7. 下一步

Phase 5 已完成。下一步仅在用户明确要求时进入 P0+ 外扩展或后续版本规划。
