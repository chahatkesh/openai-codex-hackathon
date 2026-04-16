"use client";

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

  useEffect(() => {
    const load = async () => {
      try {
        setRecentTools(await getRecentTools());
        setRecentError(null);
      } catch (error) {
        if (error instanceof EndpointUnavailableError) {
          setRecentError("Recent tools endpoint is not ready yet. Showing integration jobs only.");
        } else {
          setRecentError("Could not load recent tools.");
        }
      }

      try {
        const serverJobs = await getRecentJobs(20);
        serverJobs.forEach((j) => {
          const id = j.job_id ?? j.id;
          if (id) addTrackedJobId(id);
        });
        setJobsError(null);
      } catch {
        // Non-fatal: local tracked IDs still render when available.
      }

      const jobIds = getTrackedJobIds();
      if (!jobIds.length) {
        setJobs([]);
        return;
      }

      try {
        const statuses = await Promise.all(
          jobIds.map(async (jobId) => ({
            jobId,
            status: await getJobStatus(jobId),
          })),
        );
        setJobs(statuses);
        setJobsError(null);
      } catch {
        setJobsError("Integration status endpoint unavailable. Tracked job cards will resume automatically.");
      }
    };

    load();
    const timer = window.setInterval(load, 5000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <section className="space-y-6 pb-12">
      <header className="surface-card-light p-6">
        <p className="eyebrow">Live integration feed</p>
        <h1 className="section-title mt-3 text-[color:var(--text)]">Feed</h1>
        <p className="body-serif mt-2 max-w-2xl">Watch recently published tools and tracked pipeline jobs move from request to catalog.</p>
      </header>

      {recentError ? <p className="surface-card-light p-3 text-sm text-[color:var(--gold)]">{recentError}</p> : null}
      {jobsError ? <p className="surface-card-light p-3 text-sm text-[color:var(--gold)]">{jobsError}</p> : null}

      <LiveFeed recentTools={recentTools} jobStatuses={jobs} />

      {!recentTools.length && !jobs.length ? (
        <p className="surface-card-light p-4 text-sm text-[color:var(--text-muted)]">No live events yet. Trigger an integration to populate this feed.</p>
      ) : null}
    </section>
  );
}
