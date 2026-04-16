"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LiveFeed } from "@/components/LiveFeed";
import {
  EndpointUnavailableError,
  getJobStatus,
  getRecentJobs,
  getRecentTools,
  type CatalogItem,
  type IntegrationJobStatus,
} from "@/lib/api";
import { addTrackedJobId, getTrackedJobIds } from "@/lib/jobs";

type JobFeed = { jobId: string; status: IntegrationJobStatus };

export default function FeedPage() {
  const [recentTools, setRecentTools] = useState<CatalogItem[]>([]);
  const [jobs, setJobs] = useState<JobFeed[]>([]);
  const [recentError, setRecentError] = useState<string | null>(null);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    let cancelled = false;
    let loading = false;

    const load = async () => {
      if (loading) return;
      loading = true;
      setIsRefreshing(true);

      try {
        try {
          const tools = await getRecentTools();
          if (!cancelled) {
            setRecentTools(tools);
            setRecentError(null);
          }
        } catch (error) {
          if (!cancelled) {
            if (error instanceof EndpointUnavailableError) {
              setRecentError("Recent tools endpoint is not ready yet. Showing integration jobs only.");
            } else {
              setRecentError("Could not load recent tools.");
            }
          }
        }

        let recentJobs: JobFeed[] = [];
        try {
          const serverJobs = await getRecentJobs(20);
          recentJobs = serverJobs.flatMap((j) => {
            const id = j.job_id ?? j.id;
            if (!id) return [];
            addTrackedJobId(id);
            return [{ jobId: id, status: j }];
          });
          if (!cancelled) setJobsError(null);
        } catch {
          // Non-fatal: local tracked IDs still render when available.
        }

        const jobIds = getTrackedJobIds();
        if (!jobIds.length && !recentJobs.length) {
          if (!cancelled) {
            setJobs([]);
            setLastUpdated(new Date());
          }
          return;
        }

        const recentById = new Map(recentJobs.map((job) => [job.jobId, job]));
        const trackedOnlyIds = jobIds.filter((jobId) => !recentById.has(jobId));

        if (!trackedOnlyIds.length) {
          if (!cancelled) {
            setJobs(recentJobs);
            setLastUpdated(new Date());
          }
          return;
        }

        try {
          const trackedStatuses = await Promise.all(
            trackedOnlyIds.map(async (jobId) => ({
              jobId,
              status: await getJobStatus(jobId),
            })),
          );
          if (!cancelled) {
            setJobs([...recentJobs, ...trackedStatuses].slice(0, 20));
            setJobsError(null);
            setLastUpdated(new Date());
          }
        } catch {
          if (!cancelled) {
            setJobs(recentJobs);
            setJobsError("Integration status endpoint unavailable. Tracked job cards will resume automatically.");
            setLastUpdated(new Date());
          }
        }
      } finally {
        loading = false;
        if (!cancelled) {
          setIsRefreshing(false);
        }
      }
    };

    load();
    const timer = window.setInterval(load, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <section className="space-y-6 pb-12">
      <header className="surface-card-light p-6 sm:p-8">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="eyebrow">Live integration feed</p>
            <h1 className="section-title mt-3 text-[color:var(--text)]">Pipeline activity</h1>
            <p className="body-serif mt-2 max-w-2xl">
              Follow tool requests as they move through discovery, reading, codegen, testing, and publish.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="pill bg-[rgba(31,138,101,0.1)] text-[color:var(--success)]">
              <span className={`h-1.5 w-1.5 rounded-full bg-current ${isRefreshing ? "animate-ping" : ""}`} aria-hidden="true" />
              Polling every 3s
            </span>
            <span className="pill">{jobs.length} jobs</span>
            <span className="pill">{recentTools.length} new tools</span>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t table-rule pt-4">
          <p className="text-sm text-[color:var(--text-muted)]">
            {lastUpdated ? `Last updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}` : "Preparing live status..."}
          </p>
          <Link href="/integrate" className="button-warm">
            Request a tool
          </Link>
        </div>
      </header>

      {recentError ? <p className="surface-card-light p-3 text-sm text-[color:var(--gold)]">{recentError}</p> : null}
      {jobsError ? <p className="surface-card-light p-3 text-sm text-[color:var(--gold)]">{jobsError}</p> : null}

      <LiveFeed recentTools={recentTools} jobStatuses={jobs} />
    </section>
  );
}
