# RepoLens-Java V1-P7 Detailed Design: Evaluation, Workbench Polish, And Release Package

## 1. Phase Goal

V1-P7 closes RepoLens-Java V1 as an interview-ready Java full-stack project. P0-P6 already provide repository import, indexing, graph, hybrid retrieval, Agent QA, PR review, MCP-style tools, and audit. P7 adds the final proof layer:

- offline evaluation run/result persistence
- strategy comparison metrics
- frontend workbench tabs for Ask, Review, MCP, and Eval
- Java Edition demo/release documentation
- final V1 acceptance matrix

The phase keeps the existing directories: `backend-java/`, `frontend/`, `evals/`, and `docs/`.

## 2. Scope

### 2.1 In Scope

| Capability | Description |
| --- | --- |
| Evaluation dataset schema | JSONL samples with query, repository key, expected files, expected symbols, and category |
| Evaluation API | Create/list/get evaluation runs |
| Strategy runner | `vector_only`, `bm25_vector`, `bm25_vector_graph`, and `all` |
| Metrics | Hit@5, MRR, citation coverage, latency, token estimate, error count |
| Persistence | `evaluation_runs` and `evaluation_results` tables |
| Frontend polish | V1 workbench tabs for Search, Ask, Review, MCP, Eval |
| Release docs | Java V1 demo runbook, release package, final closure review |

### 2.2 Out Of Scope

| Item | Reason |
| --- | --- |
| LLM-as-a-judge | V1 local deterministic evaluation should not depend on paid model calls |
| Real benchmark leaderboard | This is a resume/demo project, not a public benchmark service |
| Screenshot automation | Existing screenshots belong to the Python V1 package; Java V1 closes with runnable UI and docs |
| Multi-agent Java implementation | Java V1 focuses on single-agent QA, PR review, MCP, and evaluation |
| External Git PR provider | Java V1 uses pasted diff; provider integration is V1.1 |

## 3. Evaluation Contract

### 3.1 Dataset JSONL

Each line is one sample:

```json
{
  "id": "java-auth-001",
  "repository_key": "java_demo",
  "sample_type": "location",
  "query": "Where is the authentication check implemented?",
  "expected_files": ["src/main/java/com/demo/SecurityConfig.java"],
  "expected_symbols": ["demo.SecurityConfig#void configure()"]
}
```

`repository_map` in API request maps dataset keys to actual imported repository ids.

### 3.2 APIs

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/evaluations` | Run one or all strategies |
| GET | `/api/evaluations` | List recent runs |
| GET | `/api/evaluations/{runId}` | Fetch run, metrics, and sample results |

Create request:

```json
{
  "name": "java-v1-demo",
  "dataset_path": "evals/datasets/repolens_java_v1_eval.jsonl",
  "strategy": "all",
  "repository_map": {
    "java_demo": "repo_xxx"
  },
  "top_k": 5
}
```

### 3.3 Strategies

| Strategy | BM25 | Vector | Graph |
| --- | --- | --- | --- |
| `vector_only` | false | true | false |
| `bm25_vector` | true | true | false |
| `bm25_vector_graph` | true | true | true |

`all` expands to the three strategies above.

## 4. Metrics

| Metric | Definition |
| --- | --- |
| Hit@5 | At least one expected file appears in the top 5 evidence items |
| MRR | Reciprocal rank of the first expected file hit |
| Citation Coverage | Share of expected files and symbols covered by retrieved evidence |
| Average Latency | Mean retrieval latency in milliseconds |
| P50/P95 Latency | Percentile latency across samples |
| Token Estimate | Sum of snippet token estimates based on whitespace approximation |
| Error Count | Samples that fail due to missing repository, invalid data, or retrieval error |

## 5. Backend Design

### 5.1 Package Layout

```text
backend-java/src/main/java/com/repolens/evaluation
  api/
  api/dto/
  application/
  domain/
  infrastructure/
```

### 5.2 Main Classes

| Class | Responsibility |
| --- | --- |
| `EvaluationController` | REST endpoints |
| `EvaluationService` | Dataset load, strategy expansion, runner, persistence |
| `EvaluationDatasetReader` | JSONL parsing and validation |
| `EvaluationMetricCalculator` | Metric aggregation |
| `EvaluationRunEntity` | Run metadata and aggregate status |
| `EvaluationResultEntity` | Sample-level result |
| `EvaluationRunJpaRepository` | Run persistence |
| `EvaluationResultJpaRepository` | Result persistence |

### 5.3 Persistence

Migration `V9__add_v1_evaluations.sql` adds:

- `evaluation_runs`
- `evaluation_results`

Large payload fields are stored as JSON text so V1 can remain database-portable across H2 and PostgreSQL.

## 6. Frontend Design

The existing page is upgraded from a V0 search page to a V1 workbench:

- repository sidebar remains
- workspace tabs: `Search`, `Ask`, `Review`, `MCP`, `Eval`
- right/lower panels show evidence, trace, tool audit, and metrics
- controls remain dense and utilitarian for repeated developer use

P7 avoids introducing a complex component tree. The page can stay single-file if that keeps the closure practical, but UI state must cover the V1 demo path.

## 7. Testing Plan

| Test | Expected Result |
| --- | --- |
| Evaluation API integration | Import small repo, run `all`, persist metrics and results |
| Strategy expansion | `all` produces three metric groups |
| Hit/MRR coverage | Known query hits expected Java file |
| List/get APIs | Return summary and full result |
| Frontend build | TypeScript and Next.js production build pass |

Final verification:

```powershell
& ..\scripts\use-java.ps1 21; mvn test
npm run build
```

## 8. Acceptance Criteria

- V1 has P7 detailed design before implementation.
- Evaluation APIs are implemented and tested.
- Evaluation metrics persist and can be displayed by frontend.
- Frontend exposes Search, Ask, Review, MCP, and Eval workbench paths.
- Java V1 release docs describe launch, demo, APIs, resume bullets, and known tradeoffs.
- Backend and frontend verification pass.
