"use client";

import type { CatalogItem, IntegrationJobStatus } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  AlertCircle,
  BookOpenText,
  Check,
  CheckCircle2,
  Code2,
  FileSearch,
  Hammer,
  PackageCheck,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

type Props = {
  recentTools: CatalogItem[];
  jobStatuses: Array<{ jobId: string; status: IntegrationJobStatus }>;
};

const pipelineSteps = [
  { key: "discovery", label: "Discovery", detail: "Find auth and endpoints", color: "bg-[color:var(--thinking)]", icon: FileSearch },
  { key: "reader", label: "Reader", detail: "Extract docs into a spec", color: "bg-[color:var(--read)]", icon: BookOpenText },
  { key: "codegen", label: "Codegen", detail: "Build the adapter", color: "bg-[color:var(--edit)]", icon: Code2 },
  { key: "test_fix", label: "Test/fix", detail: "Run checks and repair", color: "bg-[color:var(--gold)]", icon: Hammer },
  { key: "publish", label: "Publish", detail: "Register the tool", color: "bg-[color:var(--grep)]", icon: PackageCheck },
] satisfies Array<{
  key: string;
  label: string;
  detail: string;
  color: string;
  icon: LucideIcon;
}>;

type StepState = "done" | "current" | "pending" | "failed";

function normalizeStage(stage?: string | null) {
  const value = (stage ?? "queued").toLowerCase().replace(/[\s-]/g, "_");
  if (!value || value === "queued") return "queued";
  if (value.includes("discover")) return "discovery";
  if (value.includes("reader") || value === "read") return "reader";
  if (value.includes("codegen") || value.includes("code")) return "codegen";
  if (value.includes("test") || value.includes("fix")) return "test_fix";
  if (value.includes("publish")) return "publish";
  return value;
}

function statusValue(status: IntegrationJobStatus) {
  return status.status.toLowerCase();
}

function activeStageIndex(status: IntegrationJobStatus) {
  if (statusValue(status) === "complete") return pipelineSteps.length - 1;
  const stage = normalizeStage(status.current_stage);
  return pipelineSteps.findIndex((step) => step.key === stage);
}

function stepState(index: number, status: IntegrationJobStatus): StepState {
  const activeIndex = activeStageIndex(status);
  const state = statusValue(status);

  if (state === "complete") return "done";
  if (state === "failed") {
    if (activeIndex < 0) return index === 0 ? "failed" : "pending";
    if (index < activeIndex) return "done";
    return index === activeIndex ? "failed" : "pending";
  }
  if (activeIndex < 0) return "pending";
  if (index < activeIndex) return "done";
  return index === activeIndex ? "current" : "pending";
}

function progressFor(status: IntegrationJobStatus) {
  const state = statusValue(status);
  const activeIndex = activeStageIndex(status);
  if (state === "complete") return 100;
  if (activeIndex < 0) return state === "queued" ? 6 : 12;

  const stepOffset = state === "failed" ? 0.55 : 0.4;
  return Math.min(96, Math.round(((activeIndex + stepOffset) / pipelineSteps.length) * 100));
}

function shortJobId(jobId: string) {
  return jobId.length > 18 ? `${jobId.slice(0, 8)}...${jobId.slice(-6)}` : jobId;
}

function stageSummary(status: IntegrationJobStatus) {
  const state = statusValue(status);
  const index = activeStageIndex(status);
  const label = index >= 0 ? pipelineSteps[index].label : "Queued";
  if (state === "complete") return "Tool published to the catalog.";
  if (state === "failed") return index >= 0 ? `Pipeline stopped during ${label}.` : "Pipeline stopped before the first stage.";
  if (state === "queued") return "Waiting for the integrator to pick up the request.";
  return `${label} is running now.`;
}

function stepCaption(state: StepState) {
  if (state === "done") return "complete";
  if (state === "current") return "running now";
  if (state === "failed") return "needs attention";
  return "waiting";
}

function stepCircleClass(step: (typeof pipelineSteps)[number], state: StepState) {
  if (state === "done") return "border-[rgba(38,37,30,0.22)] bg-[color:var(--text)] text-[color:var(--surface-light)]";
  if (state === "current") return `${step.color} border-[rgba(38,37,30,0.18)] text-[color:var(--text)] shadow-[rgba(0,0,0,0.08)_0_4px_12px]`;
  if (state === "failed") return "border-[rgba(207,45,86,0.24)] bg-[rgba(207,45,86,0.1)] text-[color:var(--error)]";
  return "border-[rgba(38,37,30,0.1)] bg-[color:var(--surface-strong)] text-[color:var(--text-soft)]";
}

function formattedTime(value?: string | null) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function PipelineJobCard({ jobId, status }: { jobId: string; status: IntegrationJobStatus }) {
  const title = status.requested_tool_name || "Integration request";
  const state = statusValue(status);
  const progress = progressFor(status);
  const active = state === "running";
  const createdAt = formattedTime(status.created_at);
  const completedAt = formattedTime(status.completed_at);

  return (
    <motion.article
      key={jobId}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98 }}
      className="surface-card-light px-5 py-4 sm:px-6"
      aria-live={active ? "polite" : "off"}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-2">
            <h3 className="title-small break-all text-[color:var(--text)]">{title}</h3>
            <span className="mono-text shrink-0 rounded px-1.5 py-0.5 text-[0.65rem] bg-[color:var(--surface-strong)] text-[color:var(--text-soft)]">
              {shortJobId(jobId)}
            </span>
          </div>
          <p className="mt-1 text-xs leading-relaxed text-[color:var(--text-muted)]">{stageSummary(status)}</p>
        </div>
        <div className="shrink-0 pt-0.5">
          <StatusBadge status={status.status} />
        </div>
      </div>

      {/* Stepper with animated track */}
      <div
        className="relative mt-5"
        role="progressbar"
        aria-label={`${title} pipeline progress`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progress}
      >
        {/* Background track */}
        <div className="absolute top-3 left-[10%] right-[10%] h-px bg-[color:var(--surface-strong)]" aria-hidden="true" />
        {/* Active track */}
        <motion.div
          className={`absolute top-3 left-[10%] right-[10%] h-px origin-left ${
            state === "failed" ? "bg-[color:var(--error)]" : "bg-[color:var(--text-soft)]"
          }`}
          initial={false}
          animate={{ scaleX: progress / 100 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          aria-hidden="true"
        />
        {/* Step nodes */}
        <div className="relative grid grid-cols-5">
          {pipelineSteps.map((step, index) => {
            const Icon = step.icon;
            const itemState = stepState(index, status);
            return (
              <div key={step.key} className="flex flex-col items-center gap-1.5">
                <motion.span
                  initial={false}
                  animate={itemState === "current" ? { scale: [1, 1.1, 1] } : { scale: 1 }}
                  transition={itemState === "current" ? { duration: 1.6, repeat: Infinity, ease: "easeInOut" } : undefined}
                  className={`flex h-6 w-6 items-center justify-center rounded-full border ${stepCircleClass(step, itemState)}`}
                  aria-hidden="true"
                >
                  {itemState === "done" ? <Check size={10} /> : itemState === "failed" ? <AlertCircle size={10} /> : <Icon size={10} />}
                </motion.span>
                <div className="text-center">
                  <p
                    className={`text-[0.65rem] leading-tight ${
                      itemState === "pending" ? "text-[color:var(--text-soft)]" : "text-[color:var(--text-muted)]"
                    }`}
                  >
                    {step.label}
                  </p>
                  <p className="mono-text mt-0.5 text-[0.58rem] uppercase text-[color:var(--text-soft)]">
                    {stepCaption(itemState)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer meta */}
      {(status.docs_url || createdAt || completedAt) && (
        <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-[color:var(--border)] pt-3 text-[0.68rem] text-[color:var(--text-soft)]">
          {status.docs_url ? (
            <a
              href={status.docs_url}
              target="_blank"
              rel="noreferrer"
              className="max-w-[22rem] truncate transition-colors hover:text-[color:var(--text-muted)]"
            >
              {status.docs_url}
            </a>
          ) : null}
          {createdAt ? <span>Queued {createdAt}</span> : null}
          {completedAt ? <span>Completed {completedAt}</span> : null}
        </div>
      )}

      {status.error_log ? (
        <div className="mono-panel mt-3 overflow-x-auto p-3 text-xs text-[color:var(--error)]">{status.error_log}</div>
      ) : null}
    </motion.article>
  );
}

function EmptyState({ title, body, icon: Icon }: { title: string; body: string; icon: LucideIcon }) {
  return (
    <div className="surface-card-light flex min-h-44 flex-col justify-center p-6 text-[color:var(--text-muted)]">
      <Icon className="mb-3 h-8 w-8 text-[color:var(--text-soft)]" />
      <p className="text-sm text-[color:var(--text)]">{title}</p>
      <p className="mt-1 text-sm leading-relaxed">{body}</p>
    </div>
  );
}

export function LiveFeed({ recentTools, jobStatuses }: Props) {
  return (
    <section className="grid gap-6 xl:grid-cols-[1.6fr_0.4fr]">
      <div className="space-y-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="eyebrow">Pipeline jobs</p>
            <p className="mt-1 text-sm text-[color:var(--text-muted)]">Live task state from the integration pipeline.</p>
          </div>
          <span className="pill">{jobStatuses.length} tracked</span>
        </div>

        <AnimatePresence>
          {jobStatuses.map(({ jobId, status }) => (
            <PipelineJobCard key={jobId} jobId={jobId} status={status} />
          ))}
        </AnimatePresence>

        {!jobStatuses.length ? (
          <EmptyState title="No pipeline jobs yet." body="Request a tool to watch the bounded pipeline run here." icon={Activity} />
        ) : null}
      </div>

      <aside className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <p className="eyebrow">Published tools</p>
          <span className="pill">{recentTools.length}</span>
        </div>

        <AnimatePresence>
          {recentTools.map((tool) => (
            <motion.article
              key={tool.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="surface-card px-4 py-3 transition-colors hover:bg-[color:var(--surface-strong)]"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="mono-text truncate text-xs font-medium text-[color:var(--text)]">{tool.name}</p>
                  <p className="mt-0.5 truncate text-[0.68rem] text-[color:var(--text-soft)]">{tool.provider} · {tool.category ?? "other"}</p>
                </div>
                <StatusBadge status={tool.status} />
              </div>
              <p className="mt-2 line-clamp-2 text-[0.7rem] leading-relaxed text-[color:var(--text-muted)]">{tool.description}</p>
              <div className="mt-2 flex items-center gap-1.5 border-t border-[color:var(--border)] pt-2">
                <Sparkles size={10} className="shrink-0 text-[color:var(--accent)]" />
                <span className="mono-text text-[0.6rem] text-[color:var(--text-soft)]">{tool.cost_per_call} credits</span>
              </div>
            </motion.article>
          ))}
        </AnimatePresence>

        {!recentTools.length ? (
          <EmptyState title="No published tools yet." body="Completed jobs will land here after publish." icon={CheckCircle2} />
        ) : null}
      </aside>
    </section>
  );
}
