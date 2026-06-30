"use client";

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import {
  bindRepositoryToProject,
  createOrganization,
  createProject,
  createReviewRuleset,
  getJob,
  listAuditLogs,
  listJobs,
  listOrganizations,
  listProjectBindings,
  listProjectQuota,
  listProjects,
  listReviewRulesets,
  listWorkers,
  triggerWebhookReview
} from "@/lib/api";
import type {
  AuditLogResponse,
  JobResponse,
  OrganizationResponse,
  ProjectResponse,
  QuotaBucketResponse,
  RepositoryBindingResponse,
  RepositoryDetail,
  ReviewRulesetResponse,
  WebhookJobResponse,
  WorkerResponse
} from "@/types/workbench";

type AsyncState = "idle" | "running" | "ready" | "empty" | "failed";

type V2LitePanelProps = {
  selectedRepository: RepositoryDetail | null;
  topK: number;
  useBm25: boolean;
  useVector: boolean;
  useGraph: boolean;
};

const defaultRules = `{
  "block_permit_all": true,
  "min_severity": "medium",
  "require_tests_for_security": true
}`;

export function V2LitePanel({
  selectedRepository,
  topK,
  useBm25,
  useVector,
  useGraph
}: V2LitePanelProps) {
  const [organizations, setOrganizations] = useState<OrganizationResponse[]>([]);
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [bindings, setBindings] = useState<RepositoryBindingResponse[]>([]);
  const [rulesets, setRulesets] = useState<ReviewRulesetResponse[]>([]);
  const [quotas, setQuotas] = useState<QuotaBucketResponse[]>([]);
  const [audits, setAudits] = useState<AuditLogResponse[]>([]);
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [workers, setWorkers] = useState<WorkerResponse[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobResponse | null>(null);
  const [webhookResult, setWebhookResult] = useState<WebhookJobResponse | null>(null);

  const [organizationId, setOrganizationId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [organizationName, setOrganizationName] = useState("RepoLens Demo Org");
  const [planName, setPlanName] = useState("team");
  const [ownerUserId, setOwnerUserId] = useState("local-owner");
  const [projectName, setProjectName] = useState("RepoLens ReviewHub");

  const [provider, setProvider] = useState("fixture-github");
  const [externalRepoId, setExternalRepoId] = useState("fixture/repolens-java");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [rulesetName, setRulesetName] = useState("Strict Security Review");
  const [rulesJson, setRulesJson] = useState(defaultRules);
  const [changeUrl, setChangeUrl] = useState("fixture://github/repolens-java/1");
  const [commitSha, setCommitSha] = useState("demo-sha");
  const [sender, setSender] = useState("demo-user");

  const [state, setState] = useState<AsyncState>("idle");
  const [error, setError] = useState<string | null>(null);

  const repositoryReady = selectedRepository?.status === "ready";
  const activeBinding = useMemo(
    () => bindings.find((binding) => binding.repository_id === selectedRepository?.id) ?? bindings[0],
    [bindings, selectedRepository]
  );

  useEffect(() => {
    void refreshAll();
  }, []);

  async function refreshAll(nextOrganizationId?: string, nextProjectId?: string, nextJobId?: string) {
    setState("running");
    setError(null);
    try {
      const [organizationItems, jobItems, workerItems, auditItems] = await Promise.all([
        listOrganizations(50),
        listJobs(30),
        listWorkers(),
        listAuditLogs(50)
      ]);
      setOrganizations(organizationItems);
      setJobs(jobItems);
      setWorkers(workerItems);
      setAudits(auditItems);

      const resolvedOrganizationId =
        nextOrganizationId || organizationId || organizationItems[0]?.id || "";
      setOrganizationId(resolvedOrganizationId);

      let projectItems: ProjectResponse[] = [];
      if (resolvedOrganizationId) {
        projectItems = await listProjects(resolvedOrganizationId);
      }
      setProjects(projectItems);

      const resolvedProjectId =
        nextProjectId ||
        (projectItems.some((project) => project.id === projectId) ? projectId : projectItems[0]?.id) ||
        "";
      setProjectId(resolvedProjectId);

      if (resolvedProjectId) {
        const [bindingItems, rulesetItems, quotaItems] = await Promise.all([
          listProjectBindings(resolvedProjectId),
          listReviewRulesets(resolvedProjectId),
          listProjectQuota(resolvedProjectId)
        ]);
        setBindings(bindingItems);
        setRulesets(rulesetItems);
        setQuotas(quotaItems);
      } else {
        setBindings([]);
        setRulesets([]);
        setQuotas([]);
      }

      const resolvedJobId = nextJobId || webhookResult?.job.id || jobItems[0]?.id;
      if (resolvedJobId) {
        setSelectedJob(await getJob(resolvedJobId));
      } else {
        setSelectedJob(null);
      }
      setState(organizationItems.length || jobItems.length || auditItems.length ? "ready" : "empty");
    } catch (refreshError) {
      setState("failed");
      setError(refreshError instanceof Error ? refreshError.message : "Unable to load V2-Lite data.");
    }
  }

  async function handleCreateOrganization(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("running");
    setError(null);
    try {
      const created = await createOrganization({
        name: organizationName.trim(),
        plan_name: planName.trim() || "team",
        owner_user_id: ownerUserId.trim() || "local-owner"
      });
      await refreshAll(created.id);
      setState("ready");
    } catch (createError) {
      setState("failed");
      setError(createError instanceof Error ? createError.message : "Organization creation failed.");
    }
  }

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organizationId) {
      setError("Create or select an organization first.");
      return;
    }
    setState("running");
    setError(null);
    try {
      const created = await createProject(organizationId, { name: projectName.trim() });
      await refreshAll(organizationId, created.id);
      setState("ready");
    } catch (createError) {
      setState("failed");
      setError(createError instanceof Error ? createError.message : "Project creation failed.");
    }
  }

  async function handleBindRepository(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectId || !selectedRepository) {
      setError("Select a project and ready repository first.");
      return;
    }
    setState("running");
    setError(null);
    try {
      await bindRepositoryToProject(projectId, selectedRepository.id, {
        provider: provider.trim(),
        external_repo_id: externalRepoId.trim(),
        webhook_secret: webhookSecret.trim() || undefined
      });
      await refreshAll(organizationId, projectId);
      setState("ready");
    } catch (bindError) {
      setState("failed");
      setError(bindError instanceof Error ? bindError.message : "Repository binding failed.");
    }
  }

  async function handleCreateRuleset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectId) {
      setError("Create or select a project first.");
      return;
    }
    setState("running");
    setError(null);
    try {
      const parsedRules = JSON.parse(rulesJson) as Record<string, unknown>;
      await createReviewRuleset(projectId, {
        name: rulesetName.trim(),
        enabled: true,
        rules: parsedRules
      });
      await refreshAll(organizationId, projectId);
      setState("ready");
    } catch (rulesetError) {
      setState("failed");
      setError(rulesetError instanceof Error ? rulesetError.message : "Ruleset creation failed.");
    }
  }

  async function handleTriggerWebhook(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("running");
    setError(null);
    try {
      const response = await triggerWebhookReview(provider.trim(), {
        external_repo_id: externalRepoId.trim(),
        change_url: changeUrl.trim(),
        event: "pull_request",
        action: "opened",
        commit_sha: commitSha.trim() || "demo-sha",
        sender: sender.trim() || "demo-user",
        top_k: topK,
        use_bm25: useBm25,
        use_vector: useVector,
        use_graph: useGraph,
        run_static_check: true
      });
      setWebhookResult(response);
      await refreshAll(organizationId, response.project_id, response.job.id);
      setState("ready");
    } catch (webhookError) {
      setState("failed");
      setError(webhookError instanceof Error ? webhookError.message : "Webhook trigger failed.");
    }
  }

  async function handleRefreshJob(jobId: string) {
    setState("running");
    setError(null);
    try {
      setSelectedJob(await getJob(jobId));
      const [jobItems, workerItems] = await Promise.all([listJobs(30), listWorkers()]);
      setJobs(jobItems);
      setWorkers(workerItems);
      setState("ready");
    } catch (jobError) {
      setState("failed");
      setError(jobError instanceof Error ? jobError.message : "Job refresh failed.");
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <section className="rounded-md border border-line bg-surface p-4">
          <ResultHeader title="ReviewHub Setup" status={state} detail={selectedRepository?.name ?? "no repository"} />
          {error ? <Alert tone="red" message={error} /> : null}
          {!repositoryReady ? <Alert tone="amber" message="Select a ready repository before binding or triggering webhook." /> : null}

          <form className="mt-4 grid gap-3 md:grid-cols-3" onSubmit={handleCreateOrganization}>
            <TextInput label="Organization" value={organizationName} onChange={setOrganizationName} />
            <TextInput label="Plan" value={planName} onChange={setPlanName} />
            <TextInput label="Owner" value={ownerUserId} onChange={setOwnerUserId} />
            <div className="md:col-span-3">
              <RunButton disabled={state === "running"}>{state === "running" ? "Working" : "Create Organization"}</RunButton>
            </div>
          </form>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <SelectBox
              label="Organization"
              value={organizationId}
              items={organizations.map((item) => ({ label: item.name, value: item.id }))}
              onChange={(value) => {
                setOrganizationId(value);
                void refreshAll(value, "");
              }}
            />
            <SelectBox
              label="Project"
              value={projectId}
              items={projects.map((item) => ({ label: item.name, value: item.id }))}
              onChange={(value) => {
                setProjectId(value);
                void refreshAll(organizationId, value);
              }}
            />
          </div>

          <form className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={handleCreateProject}>
            <TextInput label="Project name" value={projectName} onChange={setProjectName} />
            <div className="self-end">
              <RunButton disabled={!organizationId || state === "running"}>Create Project</RunButton>
            </div>
          </form>

          <form className="mt-4 grid gap-3 md:grid-cols-3" onSubmit={handleBindRepository}>
            <TextInput label="Provider" value={provider} onChange={setProvider} />
            <TextInput label="External repo" value={externalRepoId} onChange={setExternalRepoId} />
            <TextInput label="Webhook secret" value={webhookSecret} onChange={setWebhookSecret} />
            <div className="md:col-span-3">
              <RunButton disabled={!repositoryReady || !projectId || state === "running"}>Bind Repository</RunButton>
            </div>
          </form>

          <form className="mt-4 flex flex-col gap-3" onSubmit={handleCreateRuleset}>
            <TextInput label="Ruleset" value={rulesetName} onChange={setRulesetName} />
            <textarea
              className="min-h-32 rounded-md border border-line bg-white px-3 py-2 font-mono text-xs leading-5 outline-none focus:border-ink"
              value={rulesJson}
              onChange={(event) => setRulesJson(event.target.value)}
            />
            <RunButton disabled={!projectId || state === "running"}>Create Ruleset</RunButton>
          </form>
        </section>

        <section className="rounded-md border border-line bg-surface p-4">
          <ResultHeader title="Webhook" status={webhookResult?.idempotent_replay ? "replay" : state} detail={activeBinding?.id ?? "unbound"} />
          <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={handleTriggerWebhook}>
            <TextInput label="Provider" value={provider} onChange={setProvider} />
            <TextInput label="External repo" value={externalRepoId} onChange={setExternalRepoId} />
            <TextInput label="Change URL" value={changeUrl} onChange={setChangeUrl} />
            <TextInput label="Commit SHA" value={commitSha} onChange={setCommitSha} />
            <TextInput label="Sender" value={sender} onChange={setSender} />
            <div className="self-end">
              <RunButton disabled={!repositoryReady || !activeBinding || state === "running"}>
                {state === "running" ? "Triggering" : "Trigger Webhook"}
              </RunButton>
            </div>
          </form>

          {webhookResult ? (
            <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
              <InfoItem label="Job" value={webhookResult.job.id} />
              <InfoItem label="Status" value={webhookResult.job.status} />
              <InfoItem label="Ruleset" value={webhookResult.ruleset_id ?? "-"} />
              <InfoItem label="Replay" value={webhookResult.idempotent_replay ? "yes" : "no"} />
              <div className="md:col-span-2">
                <InfoItem label="Idempotency" value={webhookResult.idempotency_key} />
              </div>
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState label="No webhook event" />
            </div>
          )}
        </section>
      </div>

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-md border border-line bg-surface p-4">
          <ResultHeader title="Async Job" status={selectedJob?.status ?? "-"} detail={selectedJob?.job_type ?? "-"} />
          {selectedJob ? (
            <div className="mt-4 flex flex-col gap-3">
              <div className="grid gap-3 md:grid-cols-2">
                <InfoItem label="Job ID" value={selectedJob.id} />
                <InfoItem label="Created by" value={selectedJob.created_by ?? "-"} />
                <InfoItem label="Result" value={selectedJob.result_ref ?? "-"} />
                <InfoItem label="Updated" value={formatDate(selectedJob.updated_at)} />
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  className="rounded-md border border-line bg-white px-3 py-2 text-sm font-medium text-ink"
                  onClick={() => void handleRefreshJob(selectedJob.id)}
                  type="button"
                >
                  Refresh Job
                </button>
              </div>
              <JobAttemptList attempts={selectedJob.attempts} />
              <JobEventList events={selectedJob.events} />
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState label="No job selected" />
            </div>
          )}
        </section>

        <section className="rounded-md border border-line bg-surface p-4">
          <ResultHeader title="Governance" status={`${quotas.length} quota`} detail={`${audits.length} audit`} />
          <div className="mt-4 flex flex-col gap-3">
            <QuotaList quotas={quotas} />
            <WorkerList workers={workers} />
          </div>
        </section>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <EntityList
          title="Bindings"
          empty="No bindings"
          items={bindings.map((binding) => ({
            id: binding.id,
            title: `${binding.provider} / ${binding.external_repo_id}`,
            detail: `${binding.repository_id} / ${binding.enabled ? "enabled" : "disabled"}`
          }))}
        />
        <EntityList
          title="Rulesets"
          empty="No rulesets"
          items={rulesets.map((ruleset) => ({
            id: ruleset.id,
            title: ruleset.name,
            detail: `${ruleset.enabled ? "enabled" : "disabled"} / ${jsonSummary(ruleset.rules)}`
          }))}
        />
        <AuditLogList audits={audits} />
      </section>

      <section className="rounded-md border border-line bg-surface p-4">
        <ResultHeader title="Recent Jobs" status={`${jobs.length} jobs`} />
        <div className="mt-4 grid gap-2">
          {jobs.length ? (
            jobs.slice(0, 8).map((job) => (
              <button
                key={job.id}
                className="rounded-md border border-line bg-white p-3 text-left text-sm"
                onClick={() => void handleRefreshJob(job.id)}
                type="button"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium">{job.job_type}</span>
                  <span className="text-xs text-muted">{job.status}</span>
                </div>
                <div className="mt-1 break-all text-xs text-muted">{job.id}</div>
              </button>
            ))
          ) : (
            <EmptyState label="No jobs" />
          )}
        </div>
      </section>
    </section>
  );
}

function TextInput({
  label,
  value,
  onChange
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block text-xs font-medium uppercase text-muted">
      {label}
      <input
        className="mt-2 w-full rounded-md border border-line bg-white px-3 py-2 text-sm normal-case outline-none focus:border-ink"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function SelectBox({
  label,
  value,
  items,
  onChange
}: {
  label: string;
  value: string;
  items: Array<{ label: string; value: string }>;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block text-xs font-medium uppercase text-muted">
      {label}
      <select
        className="mt-2 w-full rounded-md border border-line bg-white px-3 py-2 text-sm normal-case outline-none focus:border-ink"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">-</option>
        {items.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function ResultHeader({ title, status, detail }: { title: string; status: string; detail?: string }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-2">
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="text-xs text-muted">
        {status}
        {detail ? ` / ${detail}` : ""}
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 border-b border-line pb-2">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-1 truncate text-sm font-medium">{value}</div>
    </div>
  );
}

function RunButton({ children, disabled }: { children: string; disabled?: boolean }) {
  return (
    <button
      className="min-h-10 rounded-md bg-ink px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-muted"
      disabled={disabled}
      type="submit"
    >
      {children}
    </button>
  );
}

function Alert({ message, tone }: { message: string; tone: "red" | "amber" }) {
  const className =
    tone === "red"
      ? "border-red-200 bg-red-50 text-red-800"
      : "border-amber-200 bg-amber-50 text-amber-800";
  return <div className={`mt-4 rounded-md border px-3 py-2 text-sm ${className}`}>{message}</div>;
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-md border border-dashed border-line px-3 py-6 text-center text-sm text-muted">
      {label}
    </div>
  );
}

function EntityList({
  title,
  empty,
  items
}: {
  title: string;
  empty: string;
  items: Array<{ id: string; title: string; detail: string }>;
}) {
  return (
    <section className="rounded-md border border-line bg-surface p-4">
      <ResultHeader title={title} status={`${items.length}`} />
      <div className="mt-4 flex flex-col gap-2">
        {items.length ? (
          items.map((item) => (
            <div key={item.id} className="rounded-md border border-line bg-white p-3 text-sm">
              <div className="break-all font-medium">{item.title}</div>
              <div className="mt-1 break-all text-xs text-muted">{item.detail}</div>
            </div>
          ))
        ) : (
          <EmptyState label={empty} />
        )}
      </div>
    </section>
  );
}

function QuotaList({ quotas }: { quotas: QuotaBucketResponse[] }) {
  if (!quotas.length) {
    return <EmptyState label="No quota records" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {quotas.slice(0, 4).map((quota) => (
        <div key={quota.id} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium">{quota.quota_type}</span>
            <span className="text-xs text-muted">{quota.used_count} / {quota.limit_count}</span>
          </div>
          <div className="mt-1 text-xs text-muted">{formatDate(quota.window_start)} - {formatDate(quota.window_end)}</div>
        </div>
      ))}
    </div>
  );
}

function WorkerList({ workers }: { workers: WorkerResponse[] }) {
  if (!workers.length) {
    return <EmptyState label="No worker heartbeat" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {workers.slice(0, 4).map((worker) => (
        <div key={worker.worker_id} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium">{worker.worker_id}</span>
            <span className="text-xs text-muted">{worker.status}</span>
          </div>
          <div className="mt-1 break-all text-xs text-muted">{worker.current_job_id ?? "-"}</div>
        </div>
      ))}
    </div>
  );
}

function JobAttemptList({ attempts }: { attempts: JobResponse["attempts"] }) {
  if (!attempts.length) {
    return <EmptyState label="No attempts" />;
  }
  return (
    <div className="flex flex-col gap-2">
      {attempts.map((attempt) => (
        <div key={attempt.id} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium">Attempt {attempt.attempt_no}</span>
            <span className="text-xs text-muted">{attempt.status} / {attempt.worker_id}</span>
          </div>
          {attempt.error_message ? <div className="mt-1 text-xs text-red-700">{attempt.error_message}</div> : null}
        </div>
      ))}
    </div>
  );
}

function JobEventList({ events }: { events: JobResponse["events"] }) {
  if (!events.length) {
    return <EmptyState label="No events" />;
  }
  return (
    <div className="flex max-h-72 flex-col gap-2 overflow-auto">
      {events.map((event) => (
        <div key={event.id} className="rounded-md border border-line bg-white p-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium">{event.event_type}</span>
            <span className="text-xs text-muted">{formatDate(event.created_at)}</span>
          </div>
          <div className="mt-1 text-xs text-muted">{event.message ?? "-"}</div>
        </div>
      ))}
    </div>
  );
}

function AuditLogList({ audits }: { audits: AuditLogResponse[] }) {
  return (
    <section className="rounded-md border border-line bg-surface p-4">
      <ResultHeader title="Audit" status={`${audits.length}`} />
      <div className="mt-4 flex max-h-96 flex-col gap-2 overflow-auto">
        {audits.length ? (
          audits.slice(0, 12).map((audit) => (
            <div key={audit.id} className="rounded-md border border-line bg-white p-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium">{audit.action}</span>
                <span className="text-xs text-muted">{audit.actor ?? "system"}</span>
              </div>
              <div className="mt-1 break-all text-xs text-muted">{audit.scope_type}:{audit.scope_id}</div>
            </div>
          ))
        ) : (
          <EmptyState label="No audit records" />
        )}
      </div>
    </section>
  );
}

function jsonSummary(value: Record<string, unknown>): string {
  const keys = Object.keys(value);
  return keys.length ? keys.slice(0, 3).join(", ") : "-";
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}
