"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DocsUrlForm } from "@/components/DocsUrlForm";
import { StatusBadge } from "@/components/StatusBadge";
import { EndpointUnavailableError, getJobStatus, triggerIntegration, type IntegrationJobStatus } from "@/lib/api";
import { addTrackedJobId } from "@/lib/jobs";

const pipeline = [
  { name: "Discovery", note: "Locate auth, endpoints, and operation shape", tone: "bg-[color:var(--thinking)]" },
  { name: "Reader", note: "Extract schemas and examples from docs", tone: "bg-[color:var(--read)]" },
  { name: "Codegen", note: "Create deterministic adapter and tests", tone: "bg-[color:var(--edit)]" },
  { name: "Publish", note: "Register the tool for tools/list", tone: "bg-[color:var(--grep)]" },
];

export default function IntegratePage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<IntegrationJobStatus | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    if (jobStatus?.status === "complete" || jobStatus?.status === "failed") return;

    const poll = async () => {
      try {
        const next = await getJobStatus(jobId);
        setJobStatus(next);
        setError(null);
      } catch {
        setError("Integration status endpoint unavailable. Polling will continue.");
      }
    };

    poll();
    const timer = window.setInterval(poll, 3000);
    return () => window.clearInterval(timer);
  }, [jobId, jobStatus?.status]);

  async function onSubmit(payload: { docsUrl: string; toolName?: string }) {
    setSubmitting(true);
    try {
      const created = await triggerIntegration(payload.docsUrl, payload.toolName);
      const createdJobId = created.job_id ?? created.id;
      if (!createdJobId) {
        setError("Integration endpoint responded without a job ID.");
        return;
      }
      setJobId(createdJobId);
      setJobStatus(created);
      addTrackedJobId(createdJobId);
      setError(null);
    } catch (err) {
      if (err instanceof EndpointUnavailableError) {
        setError("`/api/integrate` is not available yet. This page remains usable and will retry on next submission.");
      } else {
        setError("Could not trigger integration. Please retry.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-6 pb-12">
      <header className="surface-card-light p-6">
        <p className="eyebrow">Request a tool</p>
        <h1 className="section-title mt-3 text-[color:var(--text)]">Request a tool</h1>
        <p className="body-serif mt-2 max-w-2xl">
          Paste API docs, suggest a tool name, and queue the bounded pipeline that moves a missing capability into the catalog.
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          <span className="pill">Docs only</span>
          <span className="pill">No credential collection</span>
          <span className="pill">Visible in live feed</span>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <DocsUrlForm onSubmit={onSubmit} disabled={submitting} />

        <aside className="surface-card p-5">
          <p className="eyebrow">Pipeline stages</p>
          <div className="mt-5 space-y-4">
            {pipeline.map((step, index) => (
              <div key={step.name} className="flex gap-3">
                <span className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${step.tone} mono-text text-xs text-[color:var(--text)]`}>
                  {index + 1}
                </span>
                <div className="border-b table-rule pb-4 last:border-b-0 last:pb-0">
                  <p className="text-sm text-[color:var(--text)]">{step.name}</p>
                  <p className="mt-1 text-sm leading-relaxed text-[color:var(--text-muted)]">{step.note}</p>
                </div>
              </div>
            ))}
          </div>
        </aside>
      </div>

      <p className="text-xs text-[color:var(--text-muted)]">
        If integration endpoints are unavailable, this screen keeps rendering and surfaces a non-blocking fallback state.
      </p>

      {error ? <p className="surface-card-light p-3 text-sm text-[color:var(--gold)]">{error}</p> : null}

      {jobId && jobStatus ? (
        <article className="surface-card-light p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="eyebrow">Tracked job</p>
              <h2 className="title-small mt-1 break-all text-[color:var(--text)]">{jobId}</h2>
            </div>
            <StatusBadge status={jobStatus.status} />
          </div>
          <p className="mt-3 text-sm text-[color:var(--text-muted)]">Current stage: {jobStatus.current_stage ?? "queued"}</p>
          {jobStatus.error_log ? <p className="mono-panel mt-3 overflow-x-auto p-3 text-xs text-[color:var(--error)]">{jobStatus.error_log}</p> : null}
          {jobStatus.status === "complete" ? (
            <p className="mt-4 text-sm text-[color:var(--success)]">
              Tool published.{" "}
              <Link href="/catalog" className="warm-link underline">
                View in catalog.
              </Link>
            </p>
          ) : jobStatus.status !== "failed" ? (
            <p className="mt-4 text-sm text-[color:var(--text-muted)]">
              This job is now tracked in the{" "}
              <Link href="/feed" className="warm-link underline">
                live feed.
              </Link>
            </p>
          ) : null}
        </article>
      ) : null}
    </section>
  );
}
