"use client";

import type { ToolStatus } from "@/lib/api";
import { motion } from "framer-motion";

type Props = {
  status: ToolStatus | string;
};

const STYLE_BY_STATUS: Record<string, string> = {
  live: "bg-[rgba(31,138,101,0.12)] text-[color:var(--success)] border-[rgba(31,138,101,0.2)]",
  pending_credentials: "bg-[rgba(192,133,50,0.12)] text-[color:var(--gold)] border-[rgba(192,133,50,0.22)]",
  deprecated: "bg-[rgba(207,45,86,0.1)] text-[color:var(--error)] border-[rgba(207,45,86,0.2)]",
  integrating: "bg-[rgba(159,187,224,0.28)] text-[color:var(--text)] border-[rgba(38,37,30,0.12)]",
  queued: "bg-[rgba(223,168,143,0.26)] text-[color:var(--text)] border-[rgba(38,37,30,0.12)]",
  running: "bg-[rgba(159,201,162,0.28)] text-[color:var(--text)] border-[rgba(38,37,30,0.12)]",
  complete: "bg-[rgba(31,138,101,0.12)] text-[color:var(--success)] border-[rgba(31,138,101,0.2)]",
  failed: "bg-[rgba(207,45,86,0.1)] text-[color:var(--error)] border-[rgba(207,45,86,0.2)]",
};

export function StatusBadge({ status }: Props) {
  const style = STYLE_BY_STATUS[status] ?? "bg-[color:var(--surface-strong)] text-[color:var(--text-muted)] border-[rgba(38,37,30,0.1)]";
  const active = status === "live" || status === "integrating" || status === "running";

  return (
    <motion.span
      layout
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs leading-none ${style}`}
    >
      <span className="relative flex h-1.5 w-1.5" aria-hidden="true">
        {active ? <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-current opacity-50" /> : null}
        <span className="relative inline-flex h-full w-full rounded-full bg-current" />
      </span>
      {status.replaceAll("_", " ")}
    </motion.span>
  );
}
