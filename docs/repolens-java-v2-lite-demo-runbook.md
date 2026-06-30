# RepoLens-Java V2-Lite Demo Runbook

## 1. Demo Scope

This runbook demonstrates the Java V2-Lite path:

```text
Repository import
  -> ReviewHub organization/project
  -> repository binding
  -> review ruleset
  -> fixture webhook
  -> REVIEW_CHANGE_REQUEST job
  -> change request review
  -> quota/audit/job observability
```

## 2. Start Backend

```powershell
cd F:\Desktop\agent\RepoLens\backend-java
& ..\scripts\use-java.ps1 21
mvn spring-boot:run "-Dspring-boot.run.profiles=v2-lite"
```

Default backend URL:

```text
http://localhost:8080
```

## 3. Start Frontend

```powershell
cd F:\Desktop\agent\RepoLens\frontend
npm run dev
```

Default frontend URL:

```text
http://localhost:3000
```

Open the workbench and select the `V2-Lite` tab.

## 4. Import Repository

Use the left-side repository form:

```text
F:\Desktop\agent\RepoLens\backend-java
```

Wait until the repository status is `ready`.

## 5. Create ReviewHub Objects

In the `V2-Lite` tab:

1. Create organization:

```text
name: RepoLens Demo Org
plan: team
owner: local-owner
```

2. Create project:

```text
name: RepoLens ReviewHub
```

3. Bind repository:

```text
provider: fixture-github
external_repo_id: fixture/repolens-java
webhook_secret: empty
```

4. Create ruleset:

```json
{
  "block_permit_all": true,
  "min_severity": "medium",
  "require_tests_for_security": true
}
```

## 6. Trigger Webhook

Use the Webhook panel:

```text
provider: fixture-github
external_repo_id: fixture/repolens-java
change_url: fixture://github/repolens-java/1
commit_sha: demo-sha
sender: demo-user
```

Expected result:

- Webhook returns a `REVIEW_CHANGE_REQUEST` job.
- Quota `webhook_review` increases by 1.
- Job can be refreshed until `SUCCEEDED`.
- `result_ref` contains `change_request:{id};review_task:{id}`.
- Audit includes `QUOTA_CONSUMED`.

## 7. Optional API Smoke

Create organization:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8080/api/organizations `
  -ContentType "application/json" `
  -Body '{"name":"RepoLens Demo Org","plan_name":"team","owner_user_id":"local-owner"}'
```

List jobs:

```powershell
Invoke-RestMethod -Uri http://localhost:8080/api/jobs?limit=10
```

List audit logs:

```powershell
Invoke-RestMethod -Uri http://localhost:8080/api/audit-logs?limit=20
```

Actuator health:

```powershell
Invoke-RestMethod -Uri http://localhost:8080/actuator/health
```

## 8. Verification Commands

Backend:

```powershell
cd F:\Desktop\agent\RepoLens\backend-java
& ..\scripts\use-java.ps1 21
mvn test
```

Frontend:

```powershell
cd F:\Desktop\agent\RepoLens\frontend
npm run build
```

## 9. Known Boundaries

- V2-Lite uses local worker and local concurrency adapters.
- RabbitMQ and Redis adapters are reserved for V2 full.
- Webhook fixture is local-first; public webhook callback hosting is out of Lite scope.
- Prometheus/Grafana are documented as upgrade targets; V2-Lite exposes Actuator, Job, Quota, and Audit views instead.
