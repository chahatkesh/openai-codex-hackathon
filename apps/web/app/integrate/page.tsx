"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DocsUrlForm } from "@/components/DocsUrlForm";
import { StatusBadge } from "@/components/StatusBadge";
import { EndpointUnavailableError, getJobStatus, triggerIntegration, type IntegrationJobStatus } from "@/lib/api";
import { addTrackedJobId } from "@/lib/jobs";

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
    <section className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold text-white">Integrate New API</h1>
        <p className="mt-2 text-sm text-[color:var(--text-muted)]">
          Paste documentation URL, queue a pipeline job, and monitor progress from discovery to publish.
        </p>
      </header>

      <DocsUrlForm onSubmit={onSubmit} disabled={submitting} />
      <p className="text-xs text-[color:var(--text-muted)]">
        Resilient mode: if integration endpoints are unavailable, this screen keeps rendering and surfaces a
        non-blocking fallback state.
      </p>

      {error ? <p className="text-sm text-amber-200">{error}</p> : null}

      {jobId && jobStatus ? (
        <article className="rounded-xl border border-white/10 bg-[color:var(--surface)] p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-white">Job {jobId}</h2>
            <StatusBadge status={jobStatus.status} />
          </div>
          <p className="mt-2 text-sm text-[color:var(--text-muted)]">
            Current stage: {jobStatus.current_stage ?? "queued"}
          </p>
          {jobStatus.error_log ? <p className="mt-2 text-sm text-rose-300">{jobStatus.error_log}</p> : null}
          {jobStatus.status === "complete" ? (
            <p className="mt-4 text-sm text-emerald-300">
              Tool published. <Link href="/catalog" className="underline">View in catalog.</Link>
            </p>
          ) : null}
        </article>
      ) : null}
    </section>
  );
}
