"use client";

import { useEffect, useState } from "react";
import { LiveFeed } from "@/components/LiveFeed";
import { EndpointUnavailableError, getJobStatus, getRecentJobs, getRecentTools, type CatalogItem, type IntegrationJobStatus } from "@/lib/api";
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

      // Merge localStorage job IDs with server-side recent jobs
      try {
        const serverJobs = await getRecentJobs(20);
        // Track server-side job IDs in localStorage so they survive tab refreshes
        serverJobs.forEach((j) => {
          const id = j.job_id ?? j.id;
          if (id) addTrackedJobId(id);
        });
        setJobsError(null);
      } catch {
        // Non-fatal — fall through to localStorage-only path
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
    <section className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold text-white">Live Feed</h1>
        <p className="mt-2 text-sm text-[color:var(--text-muted)]">
          Timeline of recently published tools and tracked integration jobs.
        </p>
      </header>

      {recentError ? <p className="text-sm text-amber-200">{recentError}</p> : null}
      {jobsError ? <p className="text-sm text-amber-200">{jobsError}</p> : null}

      <LiveFeed recentTools={recentTools} jobStatuses={jobs} />

      {!recentTools.length && !jobs.length ? (
        <p className="rounded-xl border border-white/10 bg-[color:var(--surface)] p-4 text-sm text-[color:var(--text-muted)]">
          No live events yet. Trigger an integration to populate this feed.
        </p>
      ) : null}
    </section>
  );
}
