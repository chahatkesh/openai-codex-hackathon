"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, BookOpenText, Code2, PackageCheck, Search } from "lucide-react";
import { DocsUrlForm } from "@/components/DocsUrlForm";
import { StatusBadge } from "@/components/StatusBadge";
import { EndpointUnavailableError, getJobStatus, triggerIntegration, type IntegrationJobStatus } from "@/lib/api";
import { addTrackedJobId } from "@/lib/jobs";

const pipeline = [
  { name: "Discovery", note: "Locate auth, endpoints, and operation shape", tone: "bg-[color:var(--thinking)]", icon: Search },
  { name: "Reader", note: "Extract schemas and examples from docs", tone: "bg-[color:var(--read)]", icon: BookOpenText },
  { name: "Codegen", note: "Build a deterministic adapter", tone: "bg-[color:var(--edit)]", icon: Code2 },
  { name: "Publish", note: "Register the tool for tools/list", tone: "bg-[color:var(--grep)]", icon: PackageCheck },
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
      <header className="surface-card-light p-6 sm:p-8">
        <p className="eyebrow">Integration pipeline</p>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="section-title text-[color:var(--text)]">Request a tool</h1>
            <p className="body-serif mt-2 max-w-2xl">
              Paste API docs, suggest a tool name, and queue the bounded pipeline that moves a missing capability into the catalog.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="pill">Docs only</span>
            <span className="pill">No credential collection</span>
            <span className="pill">Visible in live feed</span>
          </div>
        </div>
      </header>

      {error ? (
        <p className="surface-card-light px-4 py-3 text-sm text-[color:var(--gold)]">{error}</p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1fr_0.72fr]">
        <DocsUrlForm onSubmit={onSubmit} disabled={submitting} />

        <aside className="surface-card-light p-5">
          <p className="eyebrow">Pipeline stages</p>
          <ol className="mt-4 space-y-0" aria-label="Integration pipeline stages">
            {pipeline.map((step, index) => {
              const Icon = step.icon;
              const isLast = index === pipeline.length - 1;
              return (
                <li key={step.name} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${step.tone}`} aria-hidden="true">
                      <Icon size={13} />
                    </span>
                    {!isLast && <span className="my-1 w-px flex-1 bg-[color:var(--surface-strong)]" aria-hidden="true" />}
                  </div>
                  <div className={`min-w-0 pb-4 ${isLast ? "" : ""}`}>
                    <p className="text-sm text-[color:var(--text)]">{step.name}</p>
                    <p className="mt-0.5 text-xs leading-relaxed text-[color:var(--text-muted)]">{step.note}</p>
                  </div>
                </li>
              );
            })}
          </ol>
          <p className="mt-1 text-xs leading-relaxed text-[color:var(--text-soft)]">
            No credentials are collected. After publish the tool appears in the catalog and tools/list.
          </p>
        </aside>
      </div>

      {jobId && jobStatus ? (
        <article className="surface-card-light p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="eyebrow">Tracked job</p>
              <p className="mono-text mt-1.5 break-all text-xs text-[color:var(--text)]">{jobId}</p>
            </div>
            <StatusBadge status={jobStatus.status} />
          </div>

          <div className="mt-3 flex items-center gap-2 text-xs text-[color:var(--text-muted)]">
            <span className="mono-text text-[0.65rem] text-[color:var(--text-soft)]">stage</span>
            <span className="mono-text text-[color:var(--accent)]">{jobStatus.current_stage ?? "queued"}</span>
          </div>

          {jobStatus.error_log ? (
            <div className="mono-panel mt-3 overflow-x-auto p-3 text-xs text-[color:var(--error)]">{jobStatus.error_log}</div>
          ) : null}

          {jobStatus.status === "complete" ? (
            <p className="mt-4 flex items-center gap-1.5 text-sm text-[color:var(--success)]">
              Tool published.
              <Link href="/catalog" className="inline-flex items-center gap-1 underline hover:opacity-75">
                View in catalog <ArrowRight size={12} />
              </Link>
            </p>
          ) : jobStatus.status !== "failed" ? (
            <p className="mt-4 text-sm text-[color:var(--text-muted)]">
              Tracking in the{" "}
              <Link href="/feed" className="underline hover:text-[color:var(--text)]">
                live feed
              </Link>
              .
            </p>
          ) : null}
        </article>
      ) : null}
    </section>
  );
}
