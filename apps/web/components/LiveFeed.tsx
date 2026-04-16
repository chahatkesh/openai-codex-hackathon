"use client";

import type { CatalogItem, IntegrationJobStatus } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Sparkles } from "lucide-react";

type Props = {
  recentTools: CatalogItem[];
  jobStatuses: Array<{ jobId: string; status: IntegrationJobStatus }>;
};

export function LiveFeed({ recentTools, jobStatuses }: Props) {
  return (
    <section className="space-y-6">
      <AnimatePresence>
        {jobStatuses.map(({ jobId, status }) => (
          <motion.article 
            key={jobId} 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="group relative overflow-hidden rounded-2xl border border-sky-400/20 bg-gradient-to-r from-sky-500/10 to-[color:var(--surface)] p-5 shadow-lg shadow-sky-500/5 mix-blend-plus-lighter"
          >
            <div className="absolute inset-y-0 left-0 w-1 bg-sky-400 rounded-l-2xl animate-pulse"></div>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-sky-500/20 p-2 text-sky-400">
                  <Activity size={18} className="animate-spin-slow" />
                </div>
                <div>
                  <h3 className="text-sm font-bold tracking-wide text-sky-100">Job: {jobId.slice(0, 8)}</h3>
                  <p className="mt-1 flex items-center gap-1.5 text-xs font-medium text-sky-200/80">
                    <span className="uppercase tracking-widest text-[10px] text-sky-400">Stage</span>
                    {status.current_stage ?? "queued"}
                  </p>
                </div>
              </div>
              <StatusBadge status={status.status} />
            </div>
            
            {status.error_log && (
              <div className="mt-4 rounded-xl bg-red-500/10 border border-red-500/20 p-3 text-xs text-red-200 backdrop-blur-md">
                <p className="font-mono">{status.error_log}</p>
              </div>
            )}
          </motion.article>
        ))}

        {recentTools.map((tool) => (
          <motion.article 
            key={tool.id} 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="group relative rounded-2xl border border-teal-500/15 bg-teal-500/5 p-5 shadow-md shadow-teal-500/5 hover:bg-teal-500/10 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-sm font-bold text-slate-100">{tool.name}</h3>
                  <span className="flex items-center gap-1 rounded-full bg-teal-400/20 px-2 py-0.5 text-[10px] font-black uppercase tracking-wider text-teal-300">
                    <Sparkles size={10} className="text-teal-400" /> New
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed font-medium">{tool.description}</p>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-teal-500/10 flex items-center text-[10px] font-bold uppercase tracking-wider text-teal-200">
              Provider // <span className="ml-1 text-slate-300">{tool.provider}</span>
            </div>
          </motion.article>
        ))}
      </AnimatePresence>
      
      {!jobStatuses.length && !recentTools.length && (
         <div className="flex flex-col items-center justify-center py-12 px-4 rounded-2xl border border-white/5 bg-[color:var(--surface)] text-slate-400 text-center">
            <Activity className="h-8 w-8 mb-3 opacity-20" />
            <p className="text-sm font-medium">No live activity.</p>
         </div>
      )}
    </section>
  );
}
