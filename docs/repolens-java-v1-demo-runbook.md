# RepoLens-Java V1 Demo Runbook

## Goal

Run a repeatable local demo for the Java Edition V1 workbench:

1. import a local Java repository
2. run hybrid retrieval
3. ask a grounded code question
4. review a pasted diff
5. inspect MCP tools and audit
6. run evaluation metrics

## Start Backend

```powershell
cd F:\Desktop\agent\RepoLens\backend-java
& ..\scripts\use-java.ps1 21
mvn spring-boot:run
```

Backend URL:

```text
http://localhost:8080
```

## Start Frontend

```powershell
cd F:\Desktop\agent\RepoLens\frontend
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

## Demo Repository

Use any local Java/Spring Boot repository. For a self-demo, import the current Java backend:

```text
F:\Desktop\agent\RepoLens\backend-java
```

## Demo Path

1. Open the Workbench.
2. Import the repository path.
3. Confirm repository status is `ready`.
4. In `Search`, query:

```text
RepositoryApplicationService index task retrieval
```

5. In `Ask`, ask:

```text
Where is repository import and indexing started?
```

6. In `Review`, paste a small diff that changes authentication, token, or null handling.
7. In `MCP`, refresh tools and audits, then call `repolens.search` through the workbench.
8. In `Eval`, run:

```text
evals/datasets/repolens_java_v1_eval.jsonl
```

Map `java_demo` to the imported repository id.

## Acceptance Proof

The demo is successful when:

- evidence includes file path, line range, symbol, source, and score
- Ask returns answer, citations, confidence, and trace steps
- Review returns risk level, risks, suggested tests, citations, markdown, tool calls, and traces
- MCP audit shows permission decision, input hash, output hash, latency, and client/session
- Eval shows strategy metrics for `vector_only`, `bm25_vector`, and `bm25_vector_graph`
