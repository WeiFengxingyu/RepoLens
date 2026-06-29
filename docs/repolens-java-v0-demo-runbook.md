# RepoLens-Java V0 Demo Runbook

## 1. Scope

This runbook is for the RepoLens-Java V0 demo loop:

```text
local repository import
  -> scanner
  -> Java parser
  -> chunk builder
  -> Lucene BM25 index
  -> evidence retrieval
  -> Next.js workbench display
```

V0 does not include QA generation, PR review, multi-agent review, MCP tools, vector search, graph expansion, authentication, or multi-user permissions.

## 2. Environment

Required local tools:

```text
Java 21
Maven 3.9+
Node.js 20+
npm
```

Use the project Java switcher before backend commands:

```powershell
cd F:\Desktop\agent\RepoLens
.\scripts\use-java.ps1 21
```

Expected Java:

```text
Microsoft OpenJDK 21.0.11
```

## 3. Backend

Start the Java backend:

```powershell
cd F:\Desktop\agent\RepoLens
.\scripts\dev-backend-java.ps1
```

Backend URL:

```text
http://localhost:8080
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8080/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## 4. Frontend

Start the Next.js workbench in another PowerShell window:

```powershell
cd F:\Desktop\agent\RepoLens
.\scripts\dev-frontend.ps1
```

Frontend URL:

```text
http://localhost:3000
```

The frontend defaults to:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

Override if needed:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8080"
npm run dev
```

## 5. UI Demo Flow

1. Open `http://localhost:3000`.
2. In `Local path`, enter a local Java repository path.
3. Click `Import`.
4. Confirm the selected repository status becomes `ready`.
5. Check the metrics:
   - Files
   - Parsed
   - Skipped
   - Chunks
   - Relations
6. Check `Languages`.
7. Check `Index Status`, especially `Current step` and `Indexed`.
8. In `Evidence`, search for a method, route, annotation, or class name.
9. Confirm evidence cards show:
   - file path and line range
   - symbol name
   - `BM25`
   - score
   - snippet
   - route / annotations when available

Suggested queries:

```text
RepositoryApplicationService
LuceneIndexService
GetMapping getUser
scanner chunk builder
```

## 6. API Smoke

Use this if you want to validate backend behavior without the browser.

```powershell
$repoPath = "F:\Desktop\agent\RepoLens\backend-java"

$repo = Invoke-RestMethod `
  -Uri "http://localhost:8080/api/repositories" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{
    source = $repoPath
    name = "backend-java"
  } | ConvertTo-Json)

$repo
```

Retrieve evidence:

```powershell
$result = Invoke-RestMethod `
  -Uri "http://localhost:8080/api/repositories/$($repo.id)/retrieve" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{
    query = "RepositoryApplicationService LuceneIndexService"
    top_k = 5
    use_bm25 = $true
    use_vector = $false
    use_graph = $false
  } | ConvertTo-Json)

$result.evidences | Select-Object file_path,start_line,end_line,symbol_name,source,score -First 5
```

## 7. Tests

Backend:

```powershell
cd F:\Desktop\agent\RepoLens
.\scripts\use-java.ps1 21
cd backend-java
mvn test
```

Expected:

```text
Tests run: 21, Failures: 0, Errors: 0, Skipped: 0
```

Frontend:

```powershell
cd F:\Desktop\agent\RepoLens\frontend
npm run build
```

Expected:

```text
Compiled successfully
Linting and checking validity of types
```

## 8. Runtime Files

V0 local runtime files are ignored by git:

```text
.repolens-java/
.m2/
target/
```

Default H2 database:

```text
backend-java/.repolens-java/db/repolens.mv.db
```

Default Lucene index root:

```text
backend-java/.repolens-java/indexes/lucene/{repositoryId}
```

## 9. Known Limits

- V0 scans local directories only. Git clone is not implemented.
- V0 uses synchronous import. Large repositories may block the request.
- V0 uses H2 by default. PostgreSQL is prepared as a runtime dependency but not required for this demo.
- V0 retrieves with Lucene BM25 only.
- Vector and graph toggles are API-compatible placeholders.
- JavaParser extracts Java symbols without full type solving.
- Class chunks can be large for large classes.
- No authentication, authorization, tenant isolation, or audit UI.
- No source file viewer or syntax highlighting yet.

## 10. Interview Talk Track

Use this concise explanation:

```text
RepoLens-Java V0 is a Java 21 + Spring Boot code-retrieval workbench.
It imports a local repository, filters files with a scanner, parses Java symbols with JavaParser,
builds method/class/config chunks, writes them to relational storage, indexes chunks into Lucene BM25,
and exposes an Evidence API consumed by a Next.js workbench.
The V0 intentionally keeps vector search, graph expansion, PR review, and multi-agent workflows out of scope,
so the minimum retrieval loop is independently testable and stable before V1 expansion.
```
