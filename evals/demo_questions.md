# RepoLens Demo Questions

These demo questions are used for Phase 5 walkthroughs. They are paired with
the synthetic demo repositories in `evals/demo_repos/` and intentionally avoid
real customer code or secrets.

## Demo Flow

1. Import `evals/demo_repos/python_service` and wait until the repository status is ready.
2. Import `evals/demo_repos/ts_webapp` and wait until the repository status is ready.
3. Run location and architecture questions from the Ask Panel.
4. Open the Evidence Panel to show file paths, line ranges, snippets, and scores.
5. Open the Trace Panel to show planner, retrieval, reviewer, verifier, and writer traces.
6. Paste the review diff into the Review Panel and inspect risks, suggested tests, citations, and tool calls.
7. Run Evaluation Panel with the three retrieval strategies after the demo repos are indexed.

## Questions

| ID | Category | Repository | Question | Expected Answer Focus | Screenshot Target |
| --- | --- | --- | --- | --- | --- |
| demo-arch-001 | architecture | python_demo | Describe the request flow from the task creation API route to service, repository, and audit logging. | `app/api/tasks.py`, `TaskService`, `TaskRepository`, `AuditLogger`, API -> service -> repository -> audit flow. | ask-trace-panel |
| demo-loc-001 | location | python_demo | Where is repository import implemented and which scanner/chunking modules does it call? | `RepositoryImportService.import_repository`, `scan_repository`, `build_chunks`, import status fields. | evidence-panel |
| demo-exp-001 | explanation | python_demo | Explain how invoice totals handle line items, tax, and discount validation. | `calculate_invoice_total`, `LineItem.total`, non-negative discount, subtotal + tax - discount. | ask-trace-panel |
| demo-impact-001 | impact | python_demo | If token expiration changes from `<= now` to `< now`, what behavior and tests are affected? | Boundary behavior in `validate_access_token`, expired-at-now token, auth tests and Review risk. | review-panel |
| demo-review-001 | review | python_demo | Review the discount validation removal in `app/billing/invoices.py`. | Negative discount risk, total inflation/undercharging, add billing boundary tests. | review-panel |
| demo-arch-002 | architecture | ts_demo | Describe the frontend data flow from DashboardPage to RepositoryList and the repository API client. | `DashboardPage`, `RepositoryList`, `fetchRepositories`, page -> component -> API client. | ask-trace-panel |
| demo-loc-002 | location | ts_demo | Where are evidence cards displayed and how is score precision rendered? | `EvidencePanel`, `evidence.score.toFixed(3)`, snippet/source display. | evidence-panel |
| demo-exp-002 | explanation | ts_demo | Explain how `useEvaluation` manages loading, result, and error state. | `loading`, `error`, `result`, `runEvaluation`, success/error state transitions. | evaluation-panel |
| demo-impact-002 | impact | ts_demo | What breaks if invalid persisted workspace JSON throws instead of falling back to default state? | `restoreWorkspaceState`, localStorage fallback, dashboard startup resilience. | ask-trace-panel |
| demo-review-002 | review | ts_demo | Review the empty diff guard change in `ReviewPanel`. | Whitespace diff submission, disabled button condition, `diff.trim()`, suggested UI test. | review-panel |

## Review Diffs

### demo-review-001

```diff
diff --git a/app/billing/invoices.py b/app/billing/invoices.py
--- a/app/billing/invoices.py
+++ b/app/billing/invoices.py
@@ -15,7 +15,7 @@ def calculate_invoice_total(items: list[LineItem], discount: Decimal) -> Decimal:
-    discount = max(discount, Decimal("0"))
+    discount = discount
     subtotal = sum(item.total for item in items)
     tax = subtotal * Decimal("0.08")
     return subtotal + tax - discount
```

### demo-review-002

```diff
diff --git a/src/components/review-panel.tsx b/src/components/review-panel.tsx
--- a/src/components/review-panel.tsx
+++ b/src/components/review-panel.tsx
@@ -9,7 +9,7 @@ export function ReviewPanel() {
   const [status, setStatus] = useState("idle");
 
   async function submitReview() {
-    if (!diff.trim()) return;
+    if (!diff) return;
     setStatus("loading");
     await createReview({ diff });
     setStatus("submitted");
```

## Screenshot Mapping

| Screenshot Target | Use With Questions |
| --- | --- |
| repository-status | Import both demo repos before asking questions. |
| evidence-panel | `demo-loc-001`, `demo-loc-002` |
| ask-trace-panel | `demo-arch-001`, `demo-exp-001`, `demo-arch-002`, `demo-impact-002` |
| review-panel | `demo-impact-001`, `demo-review-001`, `demo-review-002` |
| evaluation-panel | `demo-exp-002` plus the Phase 5 Evaluation Panel run |
