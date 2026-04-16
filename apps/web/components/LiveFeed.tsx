"use client";

import type { CatalogItem, IntegrationJobStatus } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { AnimatePresence, motion } from "framer-motion";
import { Activity, CheckCircle2, FileSearch, Radio, Sparkles, Wrench } from "lucide-react";

type Props = {
  recentTools: CatalogItem[];
  jobStatuses: Array<{ jobId: string; status: IntegrationJobStatus }>;
};

const pipelineSteps = [
  { label: "Discovery", color: "bg-[color:var(--thinking)]", icon: FileSearch },
  { label: "Reader", color: "bg-[color:var(--read)]", icon: Radio },
  { label: "Codegen", color: "bg-[color:var(--edit)]", icon: Activity },
  { label: "Test_fix", color: "bg-[color:var(--gold)]", icon: Wrench },
  { label: "Publish", color: "bg-[color:var(--grep)]", icon: CheckCircle2 },
];

export function LiveFeed({ recentTools, jobStatuses }: Props) {
  return (
    <section className="space-y-4">
      <AnimatePresence>
        {jobStatuses.map(({ jobId, status }) => (
          <motion.article
            key={jobId}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.98 }}
            className="surface-card-light p-5"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="eyebrow">Pipeline job</p>
                <h3 className="title-small mt-1 break-all text-[color:var(--text)]">{jobId}</h3>
              </div>
              <StatusBadge status={status.status} />
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-5">
              {pipelineSteps.map((step) => {
                const Icon = step.icon;
                const active = (status.current_stage ?? "queued").toLowerCase().includes(step.label.toLowerCase());
                return (
                  <div key={step.label} className="flex items-center gap-3">
                    <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${step.color} text-[color:var(--text)]`}>
                      <Icon size={14} />
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm text-[color:var(--text)]">{step.label}</p>
                      <p className="text-xs text-[color:var(--text-muted)]">{active ? "current" : "ready"}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            {status.error_log ? (
              <div className="mono-panel mt-4 overflow-x-auto p-3 text-xs text-[color:var(--error)]">{status.error_log}</div>
            ) : null}
          </motion.article>
        ))}

        {recentTools.map((tool) => (
          <motion.article
            key={tool.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="surface-card p-5 transition-colors hover:bg-[color:var(--surface-strong)]"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <h3 className="title-small break-words text-[color:var(--text)]">{tool.name}</h3>
                  <span className="pill bg-[rgba(245,78,0,0.1)] text-[color:var(--accent)]">
                    <Sparkles size={12} />
                    New
                  </span>
                </div>
                <p className="body-serif">{tool.description}</p>
              </div>
              <StatusBadge status={tool.status} />
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2 border-t table-rule pt-4">
              <span className="pill">{tool.provider}</span>
              <span className="pill">{tool.category ?? "other"}</span>
              <span className="pill bg-[color:var(--surface-light)]">{tool.cost_per_call} credits</span>
            </div>
          </motion.article>
        ))}
      </AnimatePresence>

      {!jobStatuses.length && !recentTools.length ? (
        <div className="surface-card-light flex flex-col items-center justify-center px-4 py-12 text-center text-[color:var(--text-muted)]">
          <Activity className="mb-3 h-8 w-8 text-[color:var(--text-soft)]" />
          <p className="text-sm">No live activity yet.</p>
        </div>
      ) : null}
    </section>
  );
}
