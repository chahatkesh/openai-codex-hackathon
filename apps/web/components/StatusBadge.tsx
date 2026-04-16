"use client";

import type { ToolStatus } from "@/lib/api";
import { motion } from "framer-motion";

type Props = {
  status: ToolStatus | string;
};

const STYLE_BY_STATUS: Record<string, string> = {
  live: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.1)]",
  pending_credentials: "bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_10px_rgba(245,158,11,0.1)]",
  deprecated: "bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_10px_rgba(244,63,94,0.1)]",
  integrating: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20 shadow-[0_0_10px_rgba(99,102,241,0.1)]",
  failed: "bg-red-500/10 text-red-400 border-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.1)]",
};

export function StatusBadge({ status }: Props) {
  const style = STYLE_BY_STATUS[status] ?? "bg-slate-500/10 text-slate-400 border-slate-500/20";

  return (
    <motion.span 
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest backdrop-blur-sm ${style}`}
    >
      <span className="relative flex h-1.5 w-1.5">
        {status === "live" || status === "integrating" ? (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 bg-current" />
        ) : null}
        <span className="relative inline-flex h-full w-full rounded-full bg-current" />
      </span>
      {status.replaceAll("_", " ")}
    </motion.span>
  );
}
